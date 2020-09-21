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
    
    #CLASS ATTRIBUTES

    #BOX DETECTION PARAMETERS
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
         
         #INSTANCE ATTRIBUTES
         
         self.frame = []
         self.image_h, self.image_w = 0,0
         
         self.decoded_matrices, self.already_detected, self.not_detected = [],[],[]
         
         self.autoLowerRes = True
         
     
    def reset(self):
         self.frame = []
         self.image_h, self.image_w = 0,0
         
         self.decoded_matrices, self.already_detected = [],[]
        
    def setFrame(self,frame):
        self.frame = frame
        self.image_h, self.image_w, _ =frame.shape
             
    
    def process(self,frame):
        
        #THROW ERROR
        
        self.frame = frame
        self.not_detected = []
        

        self.image_h, self.image_w, _ =frame.shape
        
        matrix_thresholded, matrix_detect_frame, box_contours = self.preProcessFrame(frame)
        
        
        boxes = self.boxDetection(box_contours )

        self.processMatrices(matrix_thresholded, matrix_detect_frame, boxes)
        
        
        # Draw new frame
        self.drawNewFrame()
        
        return self.frame, self.decoded_matrices
        
        
    def drawNewFrame(self):
        
        margin = 5
        fontSize = 1
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        for green_box in self.already_detected:
            #print("decoded: ", green_box[2])
            
            #draw datamatrix outline
            cv2.drawContours(self.frame, [green_box[1]], -1,(50,105,50),fontSize*3)
            
            cv2.putText(self.frame,'Decoding Succesful',( green_box[1][0][0]-margin,green_box[1][0][1]-margin*10), font, fontSize, (50,170,50), 3, cv2.LINE_AA)
            
            cv2.putText(self.frame, str(green_box[2]) ,(green_box[1][0][0]-margin,green_box[1][0][1]-margin), font, fontSize, (50,170,50), 3, cv2.LINE_AA)
            
            cv2.drawContours(self.frame, [green_box[0]], -1, (50,205,50), fontSize*3)
            
        for red_box in self.not_detected:
            
            cv2.drawContours(self.frame, [red_box[0]], -1, (0,70,255), fontSize*3) 
            cv2.putText(self.frame,'Decoding Failed',(red_box[0][0][0]-margin,red_box[0][0][1]-margin), font, fontSize, (0,70,255), 3, cv2.LINE_AA)
            if len(red_box[1]):
                cv2.drawContours(self.frame, [red_box[1]], -1,(0,100,255), fontSize*3)
                
        if self.autoLowerRes and max(self.image_h,self.image_w) > 1921 :
             self.frame = frameProcessor.downSize(self.frame)
             print(self.frame.shape)
                
    
    def downSize(frame):

                scaling_factor = 1920/frame.shape[1]
            
                width = int(frame.shape[1] * scaling_factor)
                height = int(frame.shape[0] * scaling_factor)
                dim = (width, height)
                print(frame.shape)
                #np.imshow(frame)
                return cv2.resize(frame, dim )

              
        
    def preProcessFrame(self,frame):
        #frame is processed twice, once for box detection, once for datamatrix decoding and detection.
        #the two tasks require different processing
        
        
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        #blur helps to eliminate noise - if it lowers DataMatrix decoding accuracy, it can be changed or eliminated.
        blur = cv2.GaussianBlur(image,(5,5),0)
        
                #THRESHOLDING
    
        #Thresholding for box detection
        _,box_thresholded = cv2.threshold(blur,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        
        #Thresholding for DataMatrix decoding
        matrix_thresholded = cv2.adaptiveThreshold(image,255,cv2.ADAPTIVE_THRESH_MEAN_C,cv2.THRESH_BINARY,35,2)
    
                #EDGE DETECTION
        sigma = 0.33        
        v_1 = np.median(box_thresholded)  
    
        #Applying Canny edge detection with median - only for box detection
    
        lower1 = int(max(0, (1.0 - sigma) * v_1))
        upper1 = int(min(255, (1.0 + sigma) * v_1))
        edged1 = cv2.Canny(box_thresholded, lower1, upper1)
     
                #MORPHOLOGICAL OPERATIONS
                
        kernel1 = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 10))
        closed1 = cv2.morphologyEx(edged1, cv2.MORPH_CLOSE, kernel1)
    
        kernel2 = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        matrix_detect_frame = cv2.morphologyEx(matrix_thresholded, cv2.MORPH_OPEN, kernel2)
        
                # ADDING CONTOURS
                
        box_contours, _ = cv2.findContours(closed1, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        
        return matrix_thresholded, matrix_detect_frame, box_contours
    
#---------------------------------------------------------------------------------------------------------------------


    def boxDetection(self, contours):
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
                    
                    #SHAPE INTERACTIONS--------------------------------------------
        
                    box = cv2.boxPoints(rect)
                    box = np.int0(box) 
                    boxPoly1 = Polygon(box)
                    
                    addRect = True
                    
                    j=0
                    
                    #discard previousl detected boxes
                    if len(self.already_detected):
                        for old_box in self.already_detected:
                            if Polygon(old_box[0]).intersects(boxPoly1):
                                addRect = False
                                break
                    #else: print("NONE DETECTED YET")
                            
                            
                            
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
                            #print("distance/min(w1,h1,w2,h2) : ",boxPoly1.distance(boxPoly2)/min(w1,h1,w2,h2))
                            j+=1
                                                  
                    if addRect:
                        rects.append(rect)
                        boxes.append(box)
                        #print("RECT: ",rect)
        
                            
                        
        return boxes
    

#------------------------------------------------------------------------------------------------------------------------


    ##---------------------------------------------------------------------------------------------------------------
    
    def processMatrices(self, matrix_thresholded, matrix_detect_frame, boxes):
        
        not_detected = []
        
        for box in boxes:
            
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
            
            matrix_rotated = self.removeDuplicates(matrix_rotated)   
            #print(len(matrix_rotated))
    
                     
            #-----------------------Attempting to Decode Matrices------------------------------
            
           
            for mat_box in matrix_rotated:  
                
        
                w2 = int(mat_box[1][0]*(1+self.matrix_margin)) 
                h2 = int(mat_box[1][1]*(1+self.matrix_margin))
                
                mat_box = ((mat_box[0][0]+x,mat_box[0][1]+y),( w2, h2 ),mat_box[2])
                
                box2 = np.int0( cv2.boxPoints(mat_box) )
                
                # one last check for faulty detection of box itself as a matrix
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
                    
                    if len(temp_result):       
                        self.already_detected.append([box,box2,temp_result[0].data])
                        self.decoded_matrices.append(str(temp_result[0].data))
                        
                        decoded = True          
                        break
            
            if not decoded:
                self.not_detected.append([box,box2])
                
#---------------------------------------------------------------------------------------------------------------
            
    def removeDuplicates(self,boxes):
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
                    print("removed")
                else: j += 1
            i +=1
        return boxes
    

