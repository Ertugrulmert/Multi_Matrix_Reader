# -*- coding: utf-8 -*-
"""
Created on Mon Sep 14 11:08:04 2020

@author: User
"""

import time
import numpy as np
import matplotlib.pyplot as plt
import cv2
import argparse
import os
import itertools as it
import math
import shapely
from shapely.geometry import Polygon,box
from shapely.affinity import translate
from pylibdmtx.pylibdmtx import decode




class frameProcessor:
    
    """
    The class used to carry out all image processing, pattern recognition 
    tasks requried for datamatrix and box detection

    ...

    Attributes
    ----------
    
    BOX DETECTION THRESHOLDS
    
    area_threshold : int
        As the minimum theoretical size of a decodable datamtrix is 10x10 pixels, 
        minimum box is theorized to have 3 times the vertice lengths 
        of such a matrix
        
    aspect_ratio_threshold : int
        to discard false detections with unexpectedly disproportionate vertices
        (that would not be boxes found in real applications )
    
    adjacency_threshold : float
        this threshold is used to eliminate detected boxes that are almost touching
        in some cases, different faces of a box are detected seperately,
        this threshold discards those cases
        defined as the fraction of the shortest vertice among all vertices of two boxes 
        if the distance between two boxes is smaller than 
        adjacency_threshold times shortest vertice, smaller box is discarded


    DATAMATRIX DETECTION PARAMETERS
      
    min_matrix_size : float
        the minimum size of a matrix as a fraction of the box it was detected in
    
    irregularity_threshold : float
        here irregularity describes how different a polygon is from a rectangle
    
    aspect_margin : float
        datamatrices are ideally square shaped, havinga na spect ratio of 1
        this margin defines how close to a rectangle our matrix box can be 
        since in some cases, words and numbers written nexxt to a matrix 
        can alter the box shape, a margin is given
    
    
    boxMargin : float
        to avoid the detection of the outer box as the matrix box itself, 
        matrix has to be samller than this fraction of the outer box area

    
    matrix_margin : float
        manually added margin to the vertices of the detected matrix box
        to make sure no significant pixel of the original matrix 
        is accidentally cut out
        
    Instance Attributes
    -------
    
    frame : np.ndarray (initially empty list)
        the frame to be processed
    
    image_h, image_w : int
        the height and width of the frame
        
    ROI : tuple of 4
        ROI = ( x0,y0,x1,y1 ) represents the coordinates of the two opposite
        corners of the selected region of interest
        (0,0,0,0) by default, ROI not used unless a valid ROI is entered
         
    decoded_matrices : list of int
        the list of datamatrix codes decoded in the current round of processing
    
    already_detected : list of contour object pairs
        contains the contours representing boxes and matrix boxes for properly
        decoded matrices
        (not only the ones detected in the last round but all previos rounds)
        
    not_detected : list of contour object pairs
        contains the contours representing boxes and matrix boxes for which
        decoding failed
        
    autoLowerRes : bool
        determines if frame resolution should autmatically be lowered if 
        the frame resolution is higer than 1080p
        
        
    allDetected : bool
        whether all box detections are successful


    Methods
    -------
        
    reset()  
        Resets the accumulated datamatrices and boxes located previously.
        
    process(self,frame)
        Combines all sub-tasks of the class, outputs both detected datamatrix
        code list and new frame with all boxes drawn.
        
    drawNewFrame(self)
        Draws new frame with detected boxes.
        
    downSize(frame)
        Lowers the resolution of a frame to limit it to 1080p at maximum.
        
    preProcessFrame(self,frame)
        Filters the frame seperately for box detection and matrix decoding,
        detects contours to be analyzed by boxDetection
        
    boxDetection(self, contours)
        Using thresholds and logic operations, classifies given contours as
        boxes, outputs detected boxes
        
    processMatrices(self, matrix_thresholded, matrix_detect_frame, boxes)
        Detects and decodes datamatrices given detected boxes and preprocessed
        frames
        
    removeDuplicates(self,boxes)
        removes duplicated boxes in case the same boxes are detected again
    """    
    
    
     
    #CLASS ATTRIBUTES

    #BOX DETECTION THRESHOLDS
    

    area_threshold = 30*30
    aspect_ratio_threshold = 7
    adjacency_threshold = 0.05

    #DATAMATRIX DETECTION PARAMETERS

    min_matrix_size = 0.01
    irregularity_threshold = 0.2
    aspect_margin = 0.3
    boxMargin = 0.8
    matrix_margin = 0.2
    
    def __init__(self):
         """
        Initialises instance variables

        """
         #INSTANCE ATTRIBUTES INITIALISED
         
         self.frame = []
         self.image_h, self.image_w = 0,0
         self.ROI = (0,0,0,0)
         
         self.decoded_matrices, self.already_detected, self.not_detected = [],[],[]
         
         self.autoLowerRes = True
         self.allDetected = False
         
     
    def reset(self):
         """
         Resets the accumulated datamatrices and boxes located previously.
         """
        
         self.frame = []
         self.image_h, self.image_w = 0,0
         self.ROI = (0,0,0,0)
         
         self.decoded_matrices, self.already_detected = [],[]
         self.allDetected = False
                      
    
    def process(self,frame, ROI = (0,0,0,0)):
        
        """
        Combines all sub-tasks of the class, outputs both detected datamatrix
        code list and new frame with all boxes drawn.
        
        Parameters
        ----------
        frame : np.ndarray
            frame to be processed
            
        ROI : tuple
            opposite corner coordinates of the rectangular region of interest
            (0,0,0,0) by default, meaning it is not used by default
            
        Returns
        -------
        np.ndarray
            resulting frame with detected boxes
            
        list of str
            list of decoded matrix codes
        """
        
        self.frame = frame
        self.not_detected = []
        self.allDetected = False
        
        
        x0,y0,x1,y1 = ROI
        
        #checking if a valid ROI was entered 
        if x1 and y1 and x1<frame.shape[1] and y1<frame.shape[0] and (x1-x0) and (y1-y0):
            
            #only the part of the frame lying inside the ROI will be processed
            #afterwards, new frame will still be drawn using the entire frame
            
            self.ROI = ROI
            self.image_h, self.image_w = ROI[3]-ROI[1],ROI[2]-ROI[0]
            tempframe = frame[y0:y1,x0:x1]
            
            #PREPROCESSING
            matrix_thresholded, matrix_detect_frame, box_contours = self.preProcessFrame(tempframe)
            
            #BOX DETECTION
            boxes = self.boxDetection(box_contours )
            
        else:
            #ROI and frame vertices set to default
            self.ROI = (0,0,0,0)
            self.image_h, self.image_w, _ =frame.shape
            
            #PREPROCESSING
            matrix_thresholded, matrix_detect_frame, box_contours = self.preProcessFrame(frame)
            
            #BOX DETECTION
            boxes = self.boxDetection(box_contours )
        

        #MATRIX DETECTION AND DECODING
        self.processMatrices(matrix_thresholded, matrix_detect_frame, boxes)
        
        
        # DRAW DETECTED BOXES ON FRAME
        self.drawNewFrame()
        
        return self.frame, self.decoded_matrices
        

            
            
    def drawNewFrame(self):
        
        """"
        Draws new frame with detected boxes. Frame drawn in place, 
        on the instance variable "frame"
        
        Returns
        -------
        None.
        """
        
        margin = 5
        fontSize = 1
        font = cv2.FONT_HERSHEY_SIMPLEX
        #print("proc roi",self.ROI)
        # green boxes are for properly decoded matrices and their boxes
        for green_box in self.already_detected:
            
            #draw datamatrix outline
            cv2.drawContours(self.frame, [green_box[1]], -1,(50,105,50),fontSize*3)
            
            cv2.putText(self.frame,'Decoding Successful',( green_box[1][0][0]-margin,green_box[1][0][1]-margin*10), font, fontSize, (50,170,50), 3, cv2.LINE_AA)
            
            #cv2.putText(self.frame, str(green_box[2]) ,(green_box[1][0][0]-margin,green_box[1][0][1]-margin), font, fontSize, (50,170,50), 3, cv2.LINE_AA)
            
            cv2.drawContours(self.frame, [green_box[0]], -1, (50,205,50), fontSize*3)
            
        # red boxes are for failed matrix detection or decoding
        for red_box in self.not_detected:
            
            cv2.drawContours(self.frame, [red_box[0]], -1, (0,70,255), fontSize*3) 
            cv2.putText(self.frame,'Decoding Failed',(red_box[0][0][0]-margin,red_box[0][0][1]-margin), font, fontSize, (0,70,255), 3, cv2.LINE_AA)
            
            if len(red_box[1]):
                #if matrix box was detected but the matrix could not be decoded
                cv2.drawContours(self.frame, [red_box[1]], -1,(0,100,255), fontSize*3)
                
        if not len(self.not_detected): self.allDetected = True
        
        cv2.rectangle(self.frame, (self.ROI[0],self.ROI[1]), (self.ROI[2],self.ROI[3]), (0,70,255), 3)
            
             
    def isAllDetected(self): 
        """
        Returns
        -------
        bool 
            whether all box detections resulted in correct matrix decoding
        """
        return self.allDetected
                
    
    def downSize(frame):
        """
        Lowers the resolution of a frame to limit it to 1080p at maximum.
        
        Returns
        -------
        np.ndarray 
            frame downsized to limit its width to 1920 pixels
            
        float
            factor used to resize frame, later used calibrations in other functions
        """

        scaling_factor = 1920/frame.shape[1]
    
        width = int(frame.shape[1] * scaling_factor)
        height = int(frame.shape[0] * scaling_factor)
        dim = (width, height)

        return cv2.resize(frame, dim ),scaling_factor

              
        
    def preProcessFrame(self,frame):
        
        """
        Filters the frame seperately for box detection and matrix decoding,
        detects contours to be analyzed by boxDetection
        
        Parameters
        ----------
        frame : np.ndarray
            frame to be processed
            
        Returns
        -------
        np.ndarray
            frame processed for optimal matrix decoding
            
        np.ndarray
            frame processed for optimal matrix detection
            
        list of contour
            contour: np.ndarray of integer tuples for coordinate pairs
            contour :[(x0,y0),(x1,y1),(x2,y2)...]
            list of the contours found 
        """
        
        #frame is processed twice, once for box detection, once for datamatrix decoding and detection.
        #the two tasks require different processing
        
        #frame turned to grayscale
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        #blurring helps to eliminate noise and lower number of faulty contour
        #detections later on
        blur = cv2.GaussianBlur(image,(5,5),0)
        
                #THRESHOLDING
    
        #Thresholding for box detection
        _,box_thresholded = cv2.threshold(blur,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        
        #Thresholding for DataMatrix decoding
        matrix_thresholded = cv2.adaptiveThreshold(image,255,cv2.ADAPTIVE_THRESH_MEAN_C,cv2.THRESH_BINARY,35,2)
    
                #EDGE DETECTION
        #Applying Canny edge detection with median - only for box detection    
        sigma = 0.33        
        v_1 = np.median(box_thresholded)  
    
        lower1 = int(max(0, (1.0 - sigma) * v_1))
        upper1 = int(min(255, (1.0 + sigma) * v_1))
        edged1 = cv2.Canny(box_thresholded, lower1, upper1)
     
                #MORPHOLOGICAL OPERATIONS
                
        #for box contour detection
        kernel1 = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 10))
        closed1 = cv2.morphologyEx(edged1, cv2.MORPH_CLOSE, kernel1)
        
        #for matrix detection
        kernel2 = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        matrix_detect_frame = cv2.morphologyEx(matrix_thresholded, cv2.MORPH_OPEN, kernel2)
        
        # finding contours for box detection             
        box_contours, _ = cv2.findContours(closed1, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        
        return matrix_thresholded, matrix_detect_frame, box_contours
    



    def boxDetection(self, contours):
        
        """
        Using thresholds and logic operations, classifies given contours as
        boxes, outputs detected boxes
        
        Parameters
        ----------
        contours : list of contours
            list of the contours to be processed
            
        Returns
        -------
        list of contour
            list of box contours, each contour is a np.ndarray of of four corner coordinate tuples 
        """
        
        rects = []
        boxes = []
        
        
        for i in range(len(contours)):
            approx = cv2.convexHull(contours[i])
            
            contArea = cv2.contourArea(approx)
            
            #AREA THRESHOLD
            if contArea > self.area_threshold :
                
                rect = cv2.minAreaRect(approx)
                (x1,y1),(w1,h1),_ = rect
                
                rectArea = w1*h1
                
                #ASPECT RATIO MEASUREMENT
                aspect_ratio = w1/h1
                
                if 1/self.aspect_ratio_threshold < aspect_ratio < self.aspect_ratio_threshold :
                    
                    #BOX INTERACTIONS--------------------------------------------
        
                    box = cv2.boxPoints(rect)
                    box = np.int0(box) 
                    boxPoly1 = Polygon(box)
                    
                    addRect = True
                    
                    j=0
                    
                    #discard previously detected boxes
                    if len(self.already_detected):
                        for old_box in self.already_detected:
                            if Polygon(old_box[0]).intersects(translate(boxPoly1,self.ROI[0],self.ROI[1])):
                                addRect = False
                                break
                                                       
                            
                    while addRect and j < len(rects):
                        (x2,y2),(w2,h2),_ = rects[j]
        
                        boxPoly2 = Polygon(boxes[j])
                        
                        #CHECK FOR DUPLICATES AND SHAPES AT EDGES OF FRAME
                        if boxPoly1.almost_equals(boxPoly2, decimal=0) or boxPoly1.equals(boxPoly2) \
                        or not boxPoly1.within(Polygon([(1,1),(1,self.image_h-1),(self.image_w-1,self.image_h-1),(self.image_w-1,1)])):
                            addRect = False
                            break     
                        
                        #FIND SHAPES CONTAINED IN SHAPES
                        elif boxPoly1.contains(boxPoly2):
                            del rects[j]
                            del boxes[j]                        
                        elif boxPoly1.within(boxPoly2):
                            addRect = False
                            break
                        
                        #FIND SHAPES CROSSING, TOUCHING OR IN CLOSE PROXIMITY (DETERMINED BY THRESHOLD)
                        elif boxPoly1.crosses(boxPoly2) \
                        or boxPoly1.touches(boxPoly2) \
                        or boxPoly1.distance(boxPoly2) < min(w1,h1,w2,h2)*self.adjacency_threshold :
        
                            rectArea2 = w2*h2
                           
                            if rectArea <= rectArea2:       
                                addRect = False
                                break 
                            else:    
                                del rects[j]
                                del boxes[j]
                        else: 
                            j+=1
                                                  
                    if addRect:
                        rects.append(rect)
                        boxes.append(box)
                        
                        
        return boxes
    


    
    def processMatrices(self, matrix_thresholded, matrix_detect_frame, boxes):
        """
        Detects and decodes datamatrices given detected boxes and preprocessed
        frames
        
        Parameters
        ----------
        matrix_thresholded : np.ndarray
            frame processed for optimal matrix decoding
            
        matrix_detect_fram : np.ndarray
            frame processed for optimal matrix detection
            
        boxes: list of contour
            contour: np.ndarray of integer tuples for coordinate pairs
            contour :[(x0,y0),(x1,y1),(x2,y2)...]
            list of the contours found 
            
        Returns
        -------
        None
        
        Modifies instance variables instead of returning the results
        
        """
        for box in boxes:
            
            #comprised of two parts: 1-Matrix Candidate Detection
            #                        2-Attempting to Decode Matrices
            
            decoded = False
            x,y,w,h = cv2.boundingRect(box)
            
            #Polygon class used for measuring interactions between geometrical shapes
            boxPoly = Polygon(box)
            boxArea = boxPoly.area
            box2 = []
            
            #-------------Matrix Candidate Detection--------------------------
            
            matrix_rotated = []
            #finding contours within the boxes, these contours are matrix candidates 
            matrix_contours, _= cv2.findContours(matrix_detect_frame[y:y+h,x:x+w], cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
            
            for contour in  matrix_contours:
                contour = cv2.convexHull(contour) 
                contArea = cv2.contourArea(contour)
            
                #AREA THRESHOLD
                if  self.boxMargin*boxArea >contArea > self.min_matrix_size*boxArea :
                
                    #IRREGULARITY (NON-RECTANGULARITY) MEASUREMENT
                    irregularity = 0
                    aspect_ratio = 0
                    
                    #converting contour to a rectangle
                    rect = cv2.minAreaRect(contour)
                    (x1,y1),(w1,h1),_ = rect
                
                    rectArea = w1*h1
                    
                    #finding how much the contour deviates from the expected
                    #shape, in terms of rectangularity and ratio of edges
                    
                    #IRREGULARITY (NON-RECTANGULARITY) MEASUREMENT
                    irregularity = abs(rectArea-contArea)/rectArea
                
                    #ASPECT RATIO MEASUREMENT
                    aspect_ratio = w1/h1
                
                    #aspect ratio threshold is given as a fractional margin smaller than 1
                    if irregularity < self.irregularity_threshold \
                    and 1-self.aspect_margin < aspect_ratio < 1+self.aspect_margin :
                        matrix_rotated.append(rect)
            
            #removing duplicated matrix boxes
            matrix_rotated = self.removeDuplicates(matrix_rotated)   
    
                     
            #-----------------------Attempting to Decode Matrices------------------------------
            
           
            for mat_box in matrix_rotated:  
                
                #adding margins to box vertices to make sure no matrix data 
                #is left out
                w2 = int(mat_box[1][0]*(1+self.matrix_margin)) 
                h2 = int(mat_box[1][1]*(1+self.matrix_margin))
                
                mat_box = ((mat_box[0][0]+x,mat_box[0][1]+y),( w2, h2 ),mat_box[2])
                
                box2 = np.int0( cv2.boxPoints(mat_box) )
                
                # one last check for faulty detection of outer box itself as a matrix
                if not boxPoly.contains(Polygon(box2)): box2 = []
                else:
        
                    straight_box = np.array([[0, h2-1], [0, 0],[w2-1, 0], [w2-1, h2-1]], dtype="float32")
            
                    #perspective transformation matrix
                    transform = cv2.getPerspectiveTransform( box2.astype("float32"), straight_box)
            
                    # warp the rotated rectangle 
                    warped = cv2.warpPerspective(matrix_thresholded, transform, (w2, h2))
                    
                    ta = time.time()
                    temp_result = decode(  warped )

                    
                    #if decoding successful
                    if len(temp_result):   
                        
                        #locations of boxes translated if they are found within a ROI,
                        #so that they can be drawn at the right coordinates on the original image
                        
                        newbox = np.array( [(x+self.ROI[0],y+self.ROI[1]) for [x,y] in box] )
                        newbox2 = np.array( [[x+self.ROI[0],y+self.ROI[1]] for [x,y] in box2] )
                        
                        #boxes with properly decoded matrices saved in instance variable
                        self.already_detected.append([newbox,newbox2,temp_result[0].data])
                        self.decoded_matrices.append(str(temp_result[0].data))
                        
                        decoded = True          
                        break
            
            if not decoded:
                #locations of boxes translated if they are found within a ROI,
                #so that they can be drawn at the right coordinates on the original image
                
                newbox = np.array( [(x+self.ROI[0],y+self.ROI[1]) for [x,y] in box] )
                newbox2 = np.array( [ [x+self.ROI[0],y+self.ROI[1]] for [x,y] in box2] )
                #boxes without properly decoded matrices saved in instance variable
                self.not_detected.append([newbox,newbox2])
                
#---------------------------------------------------------------------------------------------------------------
            
    def removeDuplicates(self,boxes):
        """
        removes duplicated boxes in case the same boxes are detected again
        
        Parameters
        ----------
        boxes : list of contours
            list of the box contours to be processed, 
            each contour is a np.ndarray of of four corner coordinate tuples 
            
        Returns
        -------
        list of contour
            list of box contours without duplicates, 
            each contour is a np.ndarray of of four corner coordinate tuples 
        """
        i=0
        while i < len(boxes):
            points1 = cv2.boxPoints(boxes[i])
            points1 = np.int0(points1) 
            #Polygon class used to determine shapes that are too similar to be seperate objects
            poly1 = Polygon(points1)
    
            j = i+1
            while j < len(boxes):
        
                points2 = cv2.boxPoints(boxes[j])
                points2 = np.int0(points2) 
                poly2 = Polygon( points2 )
                #almost equals function is the simiarty measure
                if poly1.equals(poly2) or poly1.almost_equals(poly2, decimal=-1):
                    del boxes[j]
                else: j += 1
            i +=1
        return boxes
    

