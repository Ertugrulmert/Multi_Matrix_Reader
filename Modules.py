# import traceback, sys, time
# import numpy as np
from PyQt5 import QtWidgets
from PyQt5.QtCore import QRect, Qt
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen
# from PyQt5.QtWidgets import QApplication, QPushButton, QMainWindow



import cv2
class Camera:
    
    def __init__(self, cam_num):
        self.cam_num = cam_num
        self.cap = None
        self.availableResolutions = []
        self.isPaused = False
    
    def initialize(self):
        #self.cap = cv2.VideoCapture("/dev/video"+str(self.cam_num+ cv2.CAP_DSHOW))
        print("initialize camera")
        self.cap = cv2.VideoCapture(self.cam_num+ cv2.CAP_DSHOW)
        return self.cap.isOpened()
    
    def isReady(self):
        if self.cap is not None and  self.cap.isOpened() and not self.isPaused:
            return True
        return False
    def captureFrame(self):
        if self.cap is not None and self.cap.isOpened() and not self.isPaused:
            return self.cap.read()
        else: return None,None
    #CAMERA PROPERTIES GETTER-SETTERS
    
    # #BRIGHTNESS
    # def set_brightness(self, value):
    #     self.cap.set(cv2.CAP_PROP_BRIGHTNESS, value)
    #     print("aimed: ",value)
    #     print(self.get_brightness())
        
    # def get_brightness(self):
    #     return self.cap.get(cv2.CAP_PROP_BRIGHTNESS)

    #RESOLUTION
            
    def get_resolution(self):
        return self.cap.get(cv2.CAP_PROP_FRAME_WIDTH), self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT)
    def set_resolution(self,resIndex):
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.availableResolutions[resIndex].width())
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.availableResolutions[resIndex].height())
        
    def pause_cam(self): self.isPaused = True
    def resume_cam(self): self.isPaused = False
    
    # #ZOOM
    
    # def set_zoom(self,zoom):
    #     self.cap.set(cv2.CAP_PROP_ZOOM,zoom)
    # def get_zoom(self):
    #     return self.cap.get(cv2.CAP_PROP_ZOOM)
    
    # #GAMMA
    
    # def set_gamma(self,gamma):
    #     self.cap.set(cv2.CAP_PROP_GAMMA,gamma)
    # def get_gamma(self):
    #     return self.cap.get(cv2.CAP_PROP_GAMMA)
    
    # #PAN
    
    # def set_pan(self,pan):
    #     self.cap.set(cv2.CAP_PROP_PAN,pan)
    # def get_pan(self):
    #     return self.cap.get(cv2.CAP_PROP_PAN)
    
    # #TILT
    
    # def set_tilt(self,tilt):
    #     self.cap.set(cv2.CAP_PROP_TILT,tilt)
    # def get_tilt(self):
    #     return self.cap.get(cv2.CAP_PROP_TILT)   
    
    # #SHARPNESS
    
    # def set_sharpness(self,sharpness):
    #     self.cap.set(cv2.CAP_PROP_SHARPNESS,sharpness)
    # def get_sharpness(self):
    #     return self.cap.get(cv2.CAP_PROP_SHARPNESS)  
    
    def open_settings_dialog(self):
        self.cap.set(cv2.CAP_PROP_SETTINGS, 0)
    
    def set_available_resolutions(self,resList):
        self.availableResolutions =resList
    def get_available_resolutions(self):
        return [ str(res.width())+'x'+str(res.height())  for res in self.availableResolutions]
    
    
    def __str__(self):
        return 'Camera'
    
    def close(self):
        self.pause_cam()
        if self.cap.isOpened():
            self.cap.release()
        
        
 
class LabelwROI(QtWidgets.QLabel):
    x0,y0,x1,y1 = 0,0,0,0
    start = False
    drawROI = False
    # 
    def toggleROI(self): 
        self.drawROI = not self.drawROI
        x0,y0,x1,y1 = 0,0,0,0
        start = False
        
    def getROI(self): 
        if self.drawROI:
            return (self.x0,self.y0,self.x1,self.y1)
        else: return (0,0,0,0)
        
    def waitROI(self):
        return self.start
    
    def mousePressEvent(self,event):
        if self.drawROI:
            self.start = True
            self.x0 = event.x()
            self.y0 = event.y()
         
    def mouseReleaseEvent(self,event):
        self.start = False
        #print(self.x0,self.y0,self.x1,self.y1)
         # 
    def mouseMoveEvent(self,event):
        if self.drawROI and self.start:
            self.x1 = event.x()
            self.y1 = event.y()
            self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.drawROI:
            rect =QRect(self.x0, self.y0, abs(self.x1-self.x0), abs(self.y1-self.y0))
            painter = QPainter(self)
            painter.setPen(QPen(Qt.red,2,Qt.SolidLine))
            painter.drawRect(rect)
        
