import traceback, sys, time
import numpy as np
from PyQt5 import QtCore , QtWidgets, QtGui, QtMultimedia, QtMultimediaWidgets
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QRunnable
from PyQt5.QtWidgets import QApplication, QPushButton, QMainWindow
from PyQt5.QtMultimedia import QCamera, QCameraInfo, QMediaObject, QCameraViewfinderSettings, QCameraImageCapture
from PyQt5.QtMultimediaWidgets import QCameraViewfinder


import cv2
class Camera:
    
    def __init__(self, cam_num):
        self.cam_num = cam_num
        self.cap = None
        self.availableResolutions = []
    
    def initialize(self):
        #self.cap = cv2.VideoCapture("/dev/video"+str(self.cam_num+ cv2.CAP_DSHOW))
        print("initialize camera")
        self.cap = cv2.VideoCapture(self.cam_num+ cv2.CAP_DSHOW)
        return self.cap.isOpened()
    
    def isReady(self):
        if self.cap is not None and  self.cap.isOpened()  :
            return True
        return False
    def captureFrame(self):
        if self.cap is not None and self.cap.isOpened():
            return self.cap.read()
        else: return None,None
    #CAMERA PROPERTIES GETTER-SETTERS
    
    #BRIGHTNESS
    def set_brightness(self, value):
        self.cap.set(cv2.CAP_PROP_BRIGHTNESS, value)
        print("aimed: ",value)
        print(self.get_brightness())
        
    def get_brightness(self):
        return self.cap.get(cv2.CAP_PROP_BRIGHTNESS)

    #RESOLUTION
    def set_resolution(self,width,height):
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        
        if self.cap.get(cv2.CAP_PROP_FRAME_WIDTH) != width \
            and self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT) != height : return False
        else: return True
            
    def get_resolution(self):
        return self.cap.get(cv2.CAP_PROP_FRAME_WIDTH), self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT)
    def set_resolution(self,resIndex):
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.availableResolutions[resIndex].width())
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.availableResolutions[resIndex].height())
    
    #ZOOM
    
    def set_zoom(self,zoom):
        self.cap.set(cv2.CAP_PROP_ZOOM,zoom)
    def get_zoom(self):
        return self.cap.get(cv2.CAP_PROP_ZOOM)
    
    #GAMMA
    
    def set_gamma(self,gamma):
        self.cap.set(cv2.CAP_PROP_GAMMA,gamma)
    def get_gamma(self):
        return self.cap.get(cv2.CAP_PROP_GAMMA)
    
    #PAN
    
    def set_pan(self,pan):
        self.cap.set(cv2.CAP_PROP_PAN,pan)
    def get_pan(self):
        return self.cap.get(cv2.CAP_PROP_PAN)
    
    #TILT
    
    def set_tilt(self,tilt):
        self.cap.set(cv2.CAP_PROP_TILT,tilt)
    def get_tilt(self):
        return self.cap.get(cv2.CAP_PROP_TILT)   
    
    #SHARPNESS
    
    def set_sharpness(self,sharpness):
        self.cap.set(cv2.CAP_PROP_SHARPNESS,sharpness)
    def get_sharpness(self):
        return self.cap.get(cv2.CAP_PROP_SHARPNESS)  
    
    def reset_properties(self):
        self.cap.set(cv2.CAP_PROP_SETTINGS, 0)
    
    def set_available_resolutions(self,resList):
        self.availableResolutions =resList
    def get_available_resolutions(self):
        return [ str(res.width())+'x'+str(res.height())  for res in self.availableResolutions]
    
    
    def __str__(self):
        return 'Camera'
    
    def close(self):
        if self.cap.isOpened():
            self.cap.release()
        
        
 
        
# class ThreadSignals(QObject):
#     '''
#     Defines the signals available from a running worker thread.

#     Supported signals are:

#     finished
#         No data
    
#     error
#         `tuple` (exctype, value, traceback.format_exc() )
    
#     result
#         `object` data returned from processing, anything

#     '''
#     finished = pyqtSignal()
#     error = pyqtSignal(tuple)
#     result = pyqtSignal(object)
#     reset = pyqtSignal()
    
#     matrixList = pyqtSignal(list)
#     newFrame = pyqtSignal(np.ndarray)
        
    
    
    
# class ProcessorThread(QRunnable):


#     def __init__(self, processFunc):
#         super(ProcessorThread, self).__init__()

#         # Store constructor arguments (re-used for processing)
#         self.process = processFunc
#         self.signals = ThreadSignals()    
      

#     @pyqtSlot()
#     def run(self):

        
#         # Retrieve args/kwargs here; and fire processing using them
#         try:
#             print("trying to process frame")
#             newFrame, matrixList = self.process
#         except:
#             traceback.print_exc()
#             exctype, value = sys.exc_info()[:2]
#             self.signals.error.emit((exctype, value, traceback.format_exc()))
#         else:
#             self.signals.newFrame.emit(newFrame)
#             self.signals.matrixList.emit(matrixList)# Return the result of the processing
#         finally:
#             self.signals.finished.emit()  # Done
            
        
# class CaptureThread(QRunnable,QObject):
#     frameSignal = pyqtSignal(object)
#     noFrame = pyqtSignal(bool)
#     def __init__(self, cap):
#         print("init frame")
#         super(CaptureThread, self).__init__()   
#         QObject.__init__(self)
#         self.setAutoDelete(True)
        
#         self.cap = cap
        
#     @pyqtSlot()
#     def run(self):
#         print("trying to capture frame")
#                 # Retrieve args/kwargs here; and fire processing using them
#         #try:
#         hasFrame, frame = self.cap.captureFrame()
        
#         #while hasFrame is not None and not hasFrame:
#         #    hasframe, frame = self.frameFunc
#         # except:
#         #     traceback.print_exc()
#         #     exctype, value = sys.exc_info()[:2]
#         #     self.signals.error.emit((exctype, value, traceback.format_exc()))
#         #else:
#         if hasFrame is not None and not hasFrame:
#             time.sleep(5)
#             hasFrame, frame = self.cap.captureFrame()
#             #self.noFrame.emit()
#         if hasFrame is not None and hasFrame:    
#             self.frameSignal.emit(frame)

            
        
        
        
        
