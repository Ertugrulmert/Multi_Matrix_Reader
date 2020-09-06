# -*- coding: utf-8 -*-
"""
Created on Wed Sep  2 21:29:41 2020

@author: User
"""

import numpy as np
import cv2
import time







def processFrame(frame):
    
    image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    blurred = cv2.medianBlur(image,7)

    gaussian = cv2.adaptiveThreshold(blurred,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,\
            cv2.THRESH_BINARY,11,2)
        
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT,(10,10))
    opened = cv2.morphologyEx(gaussian, cv2.MORPH_OPEN, kernel)
     
    edged = cv2.Canny( cv2.medianBlur(opened ,5) , 5, 100)

    kernel2 = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    closed = cv2.morphologyEx(edged, cv2.MORPH_CLOSE, kernel2)
    
    #adding contours
    
    contours, hierarchy = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    approx_cnts = []
    image_coloured = frame.copy()
    
    for cnt in contours:
        epsilon = 0.05*cv2.arcLength(cnt,True)
        approx = cv2.approxPolyDP(cnt,epsilon,True)
        #approx = cv2.convexHull(cnt)
        
        image_coloured = cv2.drawContours(image_coloured, [approx], 0, (70,255,70), 3)
    
    
    # lines = cv2.HoughLinesP(closed, 1, np.pi/180, 20, np.array([]), 200, 100)
    # image_coloured = frame.copy()
    # for line in lines:
    #     for x1, y1, x2, y2 in line:
    #         cv2.line(image_coloured, (x1, y1), (x2, y2), (100, 20, 200), 3)
    
    
    
    return gaussian
        







cap = cv2.VideoCapture(0)

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


        