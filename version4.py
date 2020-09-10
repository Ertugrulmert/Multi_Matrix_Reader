# -*- coding: utf-8 -*-
"""
Created on Wed Sep  2 21:29:41 2020

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

#BOX DETECTION PARAMETERS
area_threshold = 50*50
aspect_ratio_threshold = 7
adjacency_threshold = 0.5

#DATAMATRIX DETECTION PARAMETERS
min_matrix_size = 10*10
irregularity_threshold = 0.1
aspect_margin = 0.1
boxMargin = 0.5

#-------------------------------------------------------------------------------------------------------------------------

def removeDuplicates(boxes):
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

##-------------------------------------------------------------------------------------------------------------------------

def findMatrices(boxImage):
    matrix_rotated = []
    matrix_contours, _= cv2.findContours(boxImage, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    
    for contour in  matrix_contours:
        contour = cv2.convexHull(contour) 
        contArea = cv2.contourArea(contour)
    
        #AREA THRESHOLD
        if  boxMargin*boxImage.size >contArea > min_matrix_size :
        
            #IRREGULARITY (NON-RECTANGULARITY) MEASUREMENT
            irregularity = 0
            aspect_ratio = 0
    
            rect = cv2.minAreaRect(contour)
            (x1,y1),(w1,h1),_ = rect
        
            rectArea = w1*h1

            irregularity = abs(rectArea-contArea)/rectArea
        
            #ASPECT RATIO MEASUREMENT
            aspect_ratio = w1/h1
        
            if irregularity < irregularity_threshold and 1-aspect_margin < aspect_ratio < 1+aspect_margin :
                matrix_rotated.append(rect)
    
    matrix_rotated = removeDuplicates(matrix_rotated)   
    print(len(matrix_rotated))

    return matrix_rotated


##------------------------------------------------------------------------------------------------------------------------

def processFrame(image):
    #frame is processed twice, once for box detection, once for datamatrix decoding and detection.
    #the two tasks require different processing
    
    
    #median blur helps to eliminate salt&pepper noise - if it lowers DataMatrix decoding accuracy, it can be changed or eliminated.
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
            
    kernel1 = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    closed1 = cv2.morphologyEx(edged1, cv2.MORPH_CLOSE, kernel1)

    kernel2 = cv2.getStructuringElement(cv2.MORPH_RECT, (4, 4))
    matrix_detect_frame = cv2.morphologyEx(matrix_thresholded, cv2.MORPH_OPEN, kernel2)
    
            # ADDING CONTOURS
            
    box_contours, _ = cv2.findContours(closed1, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    
    return matrix_thresholded, matrix_detect_frame, box_contours


##---------------------------------------------------------------------------------
        
def boxDetection(contours,area_threshold,aspect_ratio_threshold,irregularity_threshold,adjacency_threshold,image_h, image_w):
    rects = []
    boxes = []
    
    
    for i in range(len(contours)):
        approx = cv2.convexHull(contours[i])
        
        contArea = cv2.contourArea(approx)
        
        #AREA THRESHOLD
        if contArea > area_threshold :
            
            rect = cv2.minAreaRect(approx)
            (x1,y1),(w1,h1),_ = rect
            
            rectArea = w1*h1
            
            #ASPECT RATIO MEASUREMENT
            aspect_ratio = w1/h1
            
            if 1/aspect_ratio_threshold < aspect_ratio < aspect_ratio_threshold :
                
                #SHAPE INTERACTIONS--------------------------------------------
    
                box = cv2.boxPoints(rect)
                box = np.int0(box) 
                boxPoly1 = Polygon(box)
                
                addRect = True
                
                j=0
                while j < len(rects):
                    (x2,y2),(w2,h2),_ = rects[j]
    
                    boxPoly2 = Polygon(boxes[j])
                    
                    #CHECK FOR DUPLICATES AND SHAPES AT EDGES OF FRAME
                    if boxPoly1.almost_equals(boxPoly2, decimal=0) or boxPoly1.equals(boxPoly2) \
                    or not boxPoly1.within(Polygon([(1,1),(1,image_h-2),(image_w-2,image_h-2),(image_w-2,1)])):
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
                    or boxPoly1.distance(boxPoly2) < min(w1,h1,w2,h2)*adjacency_threshold :
    
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


##--------------------------------------------------------------------------------------------------------------
def findMatrices(boxImage):
    matrix_rotated = []
    matrix_contours, _= cv2.findContours(boxImage, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    
    for contour in  matrix_contours:
        contour = cv2.convexHull(contour) 
        contArea = cv2.contourArea(contour)
    
        #AREA THRESHOLD
        if  boxMargin*boxImage.size >contArea > min_matrix_size :
        
            #IRREGULARITY (NON-RECTANGULARITY) MEASUREMENT
            irregularity = 0
            aspect_ratio = 0
    
            rect = cv2.minAreaRect(contour)
            (x1,y1),(w1,h1),_ = rect
        
            rectArea = w1*h1

            irregularity = abs(rectArea-contArea)/rectArea
        
            #ASPECT RATIO MEASUREMENT
            aspect_ratio = w1/h1
        
            if irregularity < irregularity_threshold and 1-aspect_margin < aspect_ratio < 1+aspect_margin :
                matrix_rotated.append(rect)
    
    matrix_rotated = removeDuplicates(matrix_rotated)   
    print(len(matrix_rotated))

    return matrix_rotated

##---------------------------------------------------------------------------------------------------------------

def processMatrices(frame, matrix_thresholded, matrix_detect_frame, boxes):
    font = cv2.FONT_HERSHEY_SIMPLEX
    margin = 20
    
    for box in boxes:
        result = []
        x,y,w,h = cv2.boundingRect(box)
        box2 = []
        
        matrix_boxes=findMatrices( matrix_detect_frame[y:y+h,x:x+w])
        
        #we use the adaptive thresholded image for increased decoding accuracy
        for mat_box in matrix_boxes:     
    
            w2 = int(mat_box[1][0]) + margin
            h2 = int(mat_box[1][1]) + margin
            
            mat_box = ((mat_box[0][0]+x,mat_box[0][1]+y),( w2, h2 ),mat_box[2])
            
            box2 = np.int0( cv2.boxPoints(mat_box) )
    
            straight_box = np.array([[0, h2-1], [0, 0],[w2-1, 0], [w2-1, h2-1]], dtype="float32")
    
            #perspective transformation matrix
            transform = cv2.getPerspectiveTransform( box2.astype("float32"), straight_box)
    
            # warp the rotated rectangle 
            warped = cv2.warpPerspective(matrix_thresholded, transform, (w2, h2))
            
            temp_result = decode(  warped )
            
            if len(temp_result):           
                result = temp_result[0]            
                break
        
        if not len(result):
            cv2.drawContours(frame, [box], -1, (0,70,255), 4) 
            cv2.putText(frame,'Decoding Failed',(box[1][0],box[1][1]), font, 1, (0,70,255), 2, cv2.LINE_AA)
            if len(box2):
                cv2.drawContours(frame, [box2], -1,(0,70,255),4)
        
        else:
            print("decoded: ", result.data)
            #print("coor:  ",x2,y2,w2,h2)
            print("bounding rect: ",x,y,w,h)
            
            cv2.drawContours(frame, [box2], -1,(50,105,50),4)
            
            cv2.putText(frame,'Decoding Succesful',(x-margin,y-margin*5), font, 1, (50,170,50), 2, cv2.LINE_AA)
            cv2.putText(frame, str(result.data) ,(x-margin,y-margin), font, 1, (50,170,50), 2, cv2.LINE_AA)
            
            cv2.drawContours(frame, [box], -1, (50,205,50), 4) 
            
    return frame
        

##---------------------------------------------------------------------------------

#CAMERA LOOP
cap = cv2.VideoCapture(0)
background_sub = cv2.createBackgroundSubtractorMOG2()

#cap.set(4, 4096)

#cap.set(3, 2160)

#out = cv2.VideoWriter('C:/Users/User/Desktop/results/output.avi',cv2.VideoWriter_fourcc('M','J','P','G'), 10, (int(cap.get(3)),int(cap.get(4))))

#-------------------------------------------

update_background = False
mask = []

while(True):
    # Capture frame-by-frame
    ret, frame = cap.read()
   
    if not ret:
        continue
    if not update_background and cv2.waitKey(1) & 0xFF == ord('b'):
        update_background = True
    
    if frame is not None:
        #print(frame.shape)
        #print("frame")
        
            
        t1 = time.time()
    
        image_h, image_w, _ =frame.shape
        
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        masked = []
        
        if update_background:
            background_sub.apply(image,image,-1)
            update_background = False
            
        else:
            background_sub.apply(image,image,0)
        

        
        matrix_thresholded, matrix_detect_frame, box_contours = processFrame(image)
        
        boxes = boxDetection( box_contours, area_threshold, aspect_ratio_threshold, \
                                 irregularity_threshold, adjacency_threshold, image_h, image_w  )
                 
        
        newFrame = processMatrices( frame, matrix_thresholded, matrix_detect_frame, boxes )
        
        t2 = time.time()
        print("time diff : ", t2-t1)
        # Display the resulting frame
        

        cv2.imshow("window", image)
        #out.write(newFrame)


    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
        

# When everything done, release the capture


cap.release()
#out.release()
cv2.destroyAllWindows()

cv2.destroyAllWindows()
