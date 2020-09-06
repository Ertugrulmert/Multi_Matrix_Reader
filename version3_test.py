import numpy as np
import matplotlib.pyplot as plt
import cv2
import argparse
import os
import itertools as it
import math
import shapely
from shapely.geometry import Polygon,box
import time

area_threshold = 50*50
aspect_ratio_threshold = 7
adjacency_threshold = 0.5


def removeDuplicates(boxes):
    i=0
    while i < len(boxes):
        poly1 = Polygon(boxes[i])
        j = i+1
        while j < len(boxes):
            poly2 = Polygon(boxes[j])
            if poly1.equals(poly2) or poly1.almost_equals(poly2, decimal=-1): del boxes[j]
                
            else: j += 1
        i +=1
    return boxes
def processFrame(image_coloured):
    image = cv2.cvtColor(image_coloured, cv2.COLOR_BGR2GRAY)
    image_h, image_w =image.shape
    
    blur = cv2.GaussianBlur(image,(5,5),0)
    ret3,th3 = cv2.threshold(blur,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)

    v = np.median(th3)
    sigma = 0.33
    
    #---- Apply automatic Canny edge detection using the computed median----
    
    lower = int(max(0, (1.0 - sigma) * v))
    upper = int(min(255, (1.0 + sigma) * v))
    edged = cv2.Canny(th3, lower, upper)
    
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    closed = cv2.morphologyEx(edged, cv2.MORPH_CLOSE, kernel)
    
    area_threshold = 50*50
    aspect_ratio_threshold = 7
    adjacency_threshold = 0.5
    
    contours, hierarchy = cv2.findContours(closed, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
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
                
                #SHAPE INTERACTIONS----------------------------------------------------------------------------------- 
    
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
    
    rect_img = image_coloured.copy()
    
    
    cv2.drawContours(rect_img, boxes, -1, (100,30,100), 5)
    
    return rect_img
    
    
url = 'http://192.168.0.21:8080/video'

cap = cv2.VideoCapture(url)

while(True):
    # Capture frame-by-frame
    ret, frame = cap.read()

    t1 = time.time()
    frame = processFrame(frame)
    t2 = time.time()
    print("time diff : ", t2-t1)
    # Display the resulting frame
    
    imS = cv2.resize(frame, (1440, 960)) 
    
    
    cv2.imshow('frame',imS)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()
