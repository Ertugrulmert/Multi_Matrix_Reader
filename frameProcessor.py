# -*- coding: utf-8 -*-
"""
Created on Mon Sep 14 11:08:04 2020

@author: User
"""

import ssl
import urllib.request



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
        
    setFrame(frame)
        Used to manually set a frame, not used in normal use of processor.
        
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
         
         #INSTANCE ATTRIBUTES INITIALISED
         
         self.frame = []
         self.image_h, self.image_w = 0,0
         
         self.decoded_matrices, self.already_detected, self.not_detected = [],[],[]
         
         self.autoLowerRes = True
         self.allDetected = False
         
     
    def reset(self):
         """Resets the accumulated datamatrices and boxes located previously."""
        
         self.frame = []
         self.image_h, self.image_w = 0,0
         
         self.decoded_matrices, self.already_detected = [],[]
         self.allDetected = False
        
    def setFrame(self,frame):
        """Used to manually set a frame, not used in normal use of processor."""
        
        self.frame = frame
        self.image_h, self.image_w, _ =frame.shape
        
        
    # TODO : ADD FUNCTIONS TO SELECT AND DRAW ROI 
             
    
    def process(self,frame):
        
        """Combines all sub-tasks of the class, outputs both detected datamatrix
        code list and new frame with all boxes drawn."""
        
        #TODO : ERROR HANDLING
        
        self.frame = frame
        self.not_detected = []
        self.allDetected = False

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
        
        """"Draws new frame with detected boxes."""
        
        margin = 5
        fontSize = 1
        font = cv2.FONT_HERSHEY_SIMPLEX
        
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
            
                
        #automatically lower resolution of output frame 
        if self.autoLowerRes and max(self.image_h,self.image_w) > 1921 :
             self.frame = frameProcessor.downSize(self.frame)
             #print(self.frame.shape)
             
    def isAllDetected(self): return self.allDetected
                
    
    def downSize(frame):
        """Lowers the resolution of a frame to limit it to 1080p at maximum."""

        scaling_factor = 1920/frame.shape[1]
    
        width = int(frame.shape[1] * scaling_factor)
        height = int(frame.shape[0] * scaling_factor)
        dim = (width, height)
        print(frame.shape)
        #np.imshow(frame)
        return cv2.resize(frame, dim )

              
        
    def preProcessFrame(self,frame):
        
        """Filters the frame seperately for box detection and matrix decoding,
        detects contours to be analyzed by boxDetection"""
        
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
        
        """Using thresholds and logic operations, classifies given contours as
        boxes, outputs detected boxes"""
        
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
                            if Polygon(old_box[0]).intersects(boxPoly1):
                                addRect = False
                                break
                                                       
                            
                    while addRect and j < len(rects):
                        (x2,y2),(w2,h2),_ = rects[j]
        
                        boxPoly2 = Polygon(boxes[j])
                        
                        #CHECK FOR DUPLICATES AND SHAPES AT EDGES OF FRAME
                        if boxPoly1.almost_equals(boxPoly2, decimal=0) or boxPoly1.equals(boxPoly2) \
                        or not boxPoly1.within(Polygon([(1,1),(1,self.image_h-2),(self.image_w-2,self.image_h-2),(self.image_w-2,1)])):
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
                        #print("RECT: ",rect)
                        
                        
        return boxes
    


    
    def processMatrices(self, matrix_thresholded, matrix_detect_frame, boxes):
        """Detects and decodes datamatrices given detected boxes and preprocessed
        frames"""
        
        for box in boxes:
            
            #comprised of two parts: 1-Matrix Candidate Detection
            #                        2-Attempting to Decode Matrices
            
            decoded = False
            x,y,w,h = cv2.boundingRect(box)
            boxPoly = Polygon(box)
            boxArea = boxPoly.area
            box2 = []
            
            #-------------Matrix Candidate Detection--------------------------
            
            matrix_rotated = []
            matrix_contours, _= cv2.findContours(matrix_detect_frame[y:y+h,x:x+w], cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
            
            for contour in  matrix_contours:
                contour = cv2.convexHull(contour) 
                contArea = cv2.contourArea(contour)
            
                #AREA THRESHOLD
                if  self.boxMargin*boxArea >contArea > self.min_matrix_size*boxArea :
                
                    #IRREGULARITY (NON-RECTANGULARITY) MEASUREMENT
                    irregularity = 0
                    aspect_ratio = 0
            
                    rect = cv2.minAreaRect(contour)
                    (x1,y1),(w1,h1),_ = rect
                
                    rectArea = w1*h1
        
                    irregularity = abs(rectArea-contArea)/rectArea
                
                    #ASPECT RATIO MEASUREMENT
                    aspect_ratio = w1/h1
                
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
                    print("decode time: ",time.time()-ta)
                    print("matrix size: ",warped.shape)
                    
                    #if decoding successful
                    if len(temp_result):       
                        self.already_detected.append([box,box2,temp_result[0].data])
                        self.decoded_matrices.append(str(temp_result[0].data))
                        
                        decoded = True          
                        break
            
            if not decoded:
                self.not_detected.append([box,box2])
                
#---------------------------------------------------------------------------------------------------------------
            
    def removeDuplicates(self,boxes):
        """removes duplicated boxes in case the same boxes are detected again"""
        i=0
        while i < len(boxes):
            points1 = cv2.boxPoints(boxes[i])
            points1 = np.int0(points1) 
            poly1 = Polygon(points1)
    
            j = i+1
            while j < len(boxes):
        
                points2 = cv2.boxPoints(boxes[j])
                points2 = np.int0(points2) 
                poly2 = Polygon( points2 )
                if poly1.equals(poly2) or poly1.almost_equals(poly2, decimal=-1):
                    del boxes[j]
                else: j += 1
            i +=1
        return boxes
    

