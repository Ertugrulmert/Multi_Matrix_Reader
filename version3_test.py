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
area_threshold = 30*30
aspect_ratio_threshold = 7
adjacency_threshold = 0.05

#DATAMATRIX DETECTION PARAMETERS
min_matrix_size = 0.01
irregularity_threshold = 0.2
aspect_margin = 0.3
boxMargin = 0.8
matrix_margin = 0.2

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



##------------------------------------------------------------------------------------------------------------------------

def processFrame(frame):
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


##---------------------------------------------------------------------------------
        
def boxDetection(already_detected, contours,area_threshold,aspect_ratio_threshold,irregularity_threshold,adjacency_threshold,image_h, image_w):
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
                
                #discard previousl detected boxes
                if len(already_detected):
                    for old_box in already_detected:
                        if Polygon(old_box[0]).intersects(boxPoly1):
                            addRect = False
                            break
                else: print("NONE DETECTED YET")
                        
                        
                        
                while addRect and j < len(rects):
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



##---------------------------------------------------------------------------------------------------------------

def processMatrices(frame, matrix_thresholded, matrix_detect_frame, boxes, detected):
    font = cv2.FONT_HERSHEY_SIMPLEX
    margin = 5
    
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
            if  boxMargin*boxArea >contArea > min_matrix_size*boxArea :
            
                #IRREGULARITY (NON-RECTANGULARITY) MEASUREMENT
                irregularity = 0
                aspect_ratio = 0
        
                rect = cv2.minAreaRect(contour)
                (x1,y1),(w1,h1),_ = rect
            
                rectArea = w1*h1
    
                irregularity = abs(rectArea-contArea)/rectArea
            
                #ASPECT RATIO MEASUREMENT
                aspect_ratio = w1/h1
            
                if irregularity<irregularity_threshold and 1-aspect_margin < aspect_ratio < 1+aspect_margin :
                    matrix_rotated.append(rect)
        
        matrix_rotated = removeDuplicates(matrix_rotated)   
        #print(len(matrix_rotated))

        
        
        
        #-----------------------Attempting to Decode Matrices------------------------------
        
       
        for mat_box in matrix_rotated:  
            
    
            w2 = int(mat_box[1][0]*(1+matrix_margin)) 
            h2 = int(mat_box[1][1]*(1+matrix_margin))
            
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
                
                temp_result = decode(  warped )
                
                if len(temp_result):       
                    detected.append([box,box2,temp_result[0].data])
                    decoded = True          
                    break
        
        if not decoded:
            cv2.drawContours(frame, [box], -1, (0,70,255), 3) 
            cv2.putText(frame,'Decoding Failed',(box[1][0],box[1][1]), font, 1, (0,70,255), 3, cv2.LINE_AA)
            if len(box2):
                cv2.drawContours(frame, [box2], -1,(0,100,255),2)
        
    for det in detected:
        
            print("decoded: ", det[2])
            #print("coor:  ",x2,y2,w2,h2)
            #print("bounding rect: ",x,y,w,h)
            
            #draw datamatrix outline
            cv2.drawContours(frame, [det[1]], -1,(50,105,50),2)
            
            cv2.putText(frame,'Decoding Succesful',( det[1][0][0]-margin,det[1][0][1]-margin*5), font, 1, (50,170,50), 3, cv2.LINE_AA)
            cv2.putText(frame, str(det[2]) ,(det[1][0][0]-margin,det[1][0][1]), font, 1, (50,170,50), 3, cv2.LINE_AA)
            
            cv2.drawContours(frame, [det[0]], -1, (50,205,50), 2) 
            
    return frame, detected
        

##---------------------------------------------------------------------------------

#CAMERA LOOP
cap = cv2.VideoCapture(0,cv2.CAP_DSHOW)

#cap.set(cv2.CAP_PROP_SETTINGS,0.0)
cap.set(4, 1920)

cap.set(3, 1080)
cap.set(27, 133)
cap.set(22, 100)
cap.set(20, 30)
cap.set(33, 79)
cap.set(34, 0)


out = cv2.VideoWriter('result_1920x1080.avi',cv2.VideoWriter_fourcc(*'MJPG'), 5, (int(cap.get(3)),int(cap.get(4))))

#-------------------------------------------

already_detected = []
while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
   
    if not ret:
        continue  
    
    
    
    print(frame.shape)
    print("frame")
    t1 = time.time()
    

    image_h, image_w, _ =frame.shape
    
    matrix_thresholded, matrix_detect_frame, box_contours = processFrame(frame)
    t2 = time.time()

    print("processFrame : ", time.time()-t1)
    boxes = boxDetection( already_detected, box_contours,  area_threshold, aspect_ratio_threshold, \
                             irregularity_threshold, adjacency_threshold, image_h, image_w  )
             
    print("boxDetection : ", time.time()-t2)
    t2 = time.time()
    newFrame, already_detected = processMatrices( frame, matrix_thresholded,matrix_detect_frame, boxes, already_detected )
    print("processMatrices : ", time.time()-t2)
    
    t2 = time.time()
    print("time diff : ", t2-t1)
    # Display the resulting frame
    

    out.write(newFrame)
    
    cv2.namedWindow("window", cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty("window",cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)
    cv2.imshow("window", newFrame)


    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything done, release the capture


cap.release()
cv2.destroyAllWindows()
out.release()

