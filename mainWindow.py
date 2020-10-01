import cv2, threading, time, sys

from PyQt5   import QtCore, QtWidgets, QtGui, QtMultimedia

from mainWindowUI import Ui_MainWindow

from Modules import Camera
from frameProcessor import frameProcessor


# class SettingsDialog(QDialog):
#     def __init__(self):
#         super().__init__()
#         self.ui = Ui_camSettingsDialog()
#         self.ui.setupUi(self)
#         self.ui.okButton.clicked.connect(self.close)
        

class Worker(QtCore.QObject):
    #getFrame = QtCore.pyqtSignal()
    frameReady = QtCore.pyqtSignal(QtGui.QImage,float)
    updateList = QtCore.pyqtSignal(list)
    successUpdate = QtCore.pyqtSignal(bool)
    QtCore.pyqtSignal(list)
    
    
    
    def __init__(self, parent=None):
        super(Worker, self).__init__(parent)
        
        self.processor = frameProcessor()
        self.camera = None
        self.processing = False
        self.resetProcess = False
        self.img = None
        self.threadactive = True
        self.ROI = (0,0,0,0)
        
        
    def setCamera(self,camera):
        self.camera = camera
        
    @QtCore.pyqtSlot(int)    
    def setCameraResolution(self,i):
        self.camera.pause_cam()
        self.camera.set_resolution(i)
        self.camera.resume_cam()
        
        
    @QtCore.pyqtSlot(bool,bool,tuple)    
    def getNewFrame(self,processing,resetProcess,ROI):
        self.processing = processing
        self.resetProcess = resetProcess
        self.ROI = ROI
        scaling_factor = 1
        while self.threadactive and self.camera is not None:
            
            if not self.camera.isReady():
                continue
            
            ret ,frame= self.camera.captureFrame()
            if not ret:
                continue
            if self.resetProcess: 
                self.processor.reset()
                self.resetProcess = False
                
            if self.processing: 
                frame = self.processFrame(frame)
            
            if  frame.shape[1] > 1920 :
                frame,scaling_factor = frameProcessor.downSize(frame)
            
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.img = QtGui.QImage(frame, frame.shape[1], frame.shape[0], QtGui.QImage.Format_RGB888)
            break
        
        self.frameReady.emit(self.img,scaling_factor)
        
            
    def processFrame(self,frame):
        if self.threadactive and self.processor is not None:
            
            # try:
            frame, matrices = self.processor.process(frame,self.ROI)
            self.updateList.emit(matrices)
            # except:
            #     print("Processor Exception")  
            #     print(sys.exc_info()[0], "occurred.")
            #     self.processing = False
            #     return
        
            if self.processor.isAllDetected():
                self.successUpdate.emit(True)
            else: 
                self.successUpdate.emit(False)
            return frame
    
    def stop(self):
        self.threadactive = False
        self.camera.close()
    
        
class MainWindow(QtWidgets.QMainWindow, QtCore.QObject):
    requestFrame = QtCore.pyqtSignal(bool,bool,tuple)
    setThreadCamera = QtCore.pyqtSignal(Camera)
    
    def __init__(self):
        super().__init__()
        self.camera = None
        self.processing = False
        self.resetProcess = False
        self.autoScale = (1,1)
        
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.thread1 = QtCore.QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.thread1)
        self.thread1.start()
        
        self.worker.frameReady.connect(self.drawFrame)
        self.worker.updateList.connect(self.updateList)
        self.worker.successUpdate.connect(self.successUpdate)
        self.ui.startButton.clicked.connect(self.toggleProcessing)
        self.ui.resetDetectButton.clicked.connect(self.resetProcessor)
        
        self.requestFrame.connect(self.worker.getNewFrame)
        self.setThreadCamera.connect(self.worker.setCamera)
      
        self.ui.camSelectMenu.aboutToShow.connect(self.prepCamera)
        self.ui.camResolutionMenu.aboutToShow.connect(self.showResolutions)
        
        self.ui.actionCamera_Settings.triggered.connect(self.settingsBox)
        self.ui.ROIButton.clicked.connect(self.ui.streamLabel.toggleROI)
    
    @QtCore.pyqtSlot()
    def closeEvent(self,event):  
        if self.camera is not None: 
            self.camera.close()
            self.camera = None

            if self.thread1 is not None and self.thread1.isRunning():
                 self.thread1.terminate()
                 self.thread1.wait()
        event.accept() 
        
           
    @QtCore.pyqtSlot(list)    
    def updateList(self,newList):
        self.ui.listWidget.clear()
        self.ui.listWidget.addItems(newList)
        
    @QtCore.pyqtSlot()
    def settingsBox(self):
        if self.camera is not None and self.camera.isReady():
            self.camera.open_settings_dialog()
            
    def toggleProcessing(self): 
        self.processing = not self.processing
        print("toggle",self.processing)
        if not self.processing:
            self.ui.successLabel.setText("PROCESSING")
            self.ui.successLabel.setStyleSheet("")

    def resetProcessor(self):
        self.resetProcess = True
        
    @QtCore.pyqtSlot(bool)
    def successUpdate(self,success):
        if success:
            self.ui.successLabel.setText("SUCCESS")
            self.ui.successLabel.setStyleSheet("background-color: lightgreen") 
        else:
            self.ui.successLabel.setText("PROCESSING")
            self.ui.successLabel.setStyleSheet("")
                    
    @QtCore.pyqtSlot(QtGui.QImage,float)            
    def drawFrame(self,img,scaling_factor):
        
        realsize = (img.height(),img.width())
        pix = QtGui.QPixmap.fromImage(img)
              
        # try:
        self.ui.streamLabel.setPixmap(pix) 
        scaledsize = pix.rect()
        
        self.autoScale =( scaledsize.height()/realsize[0]/scaling_factor , scaledsize.width()/realsize[1]/scaling_factor )
        print(self.autoScale)
        
        self.ROI = self.ui.streamLabel.getROI()
        self.ROI = ( int(self.ROI[0]*self.autoScale[0]) , int(self.ROI[1]*self.autoScale[1]) ,\
                   int(self.ROI[2]*self.autoScale[0])  , int(self.ROI[3]*self.autoScale[1]) )
        self.requestFrame.emit(self.processing,self.resetProcess,self.ROI)
        self.resetProcess = False
            
        # except:
        #     print("Drawing Exception")
        #     print(sys.exc_info()[0], "occurred.")
        #     time.sleep(0.5)
    
        
            
    def showResolutions(self):
        if self.camera is not None and self.camera.isReady():
            cameraResList = self.camera.get_available_resolutions()
            self.ui.camResolutionMenu.clear()
            
            for i in range(len(cameraResList)):
                resAction = self.ui.camResolutionMenu.addAction("Resolution %d" % i)
                resAction.setText(cameraResList[i])
                resAction.setCheckable(True)
                resAction.triggered.connect( lambda chk, i=i: self.worker.setCameraResolution(i) )
                
            self.update()
    
            
        
    @QtCore.pyqtSlot()
    def prepCamera(self):
        
        cameraInfos = QtMultimedia.QCameraInfo.availableCameras()
        self.ui.camSelectMenu.clear()
        
        for i in range(len(cameraInfos)):
            camAction = self.ui.camSelectMenu.addAction("Camera %d" % i)
            camAction.setText(cameraInfos[i].description())
            camAction.setCheckable(True)
            camAction.triggered.connect( lambda chk, i=i: self.setCamera(cameraInfos[i],i) )
            
        self.update()
        #self.ui.camSelectMenu.triggered.connect
       
    @QtCore.pyqtSlot()
    def setCamera(self,cameraInfo,i):
        
        if self.camera is not None: 
            self.camera.close()
            self.camera = None
            #if self.thread is not None and self.thread.is_alive() : self.thread.join()
        
        #QCamera only used to retrieve available camera resolutions
        tempCam = QtMultimedia.QCamera(cameraInfo)
        tempCam.load()
        
        self.camera = Camera(i)
        self.camera.set_available_resolutions(tempCam.supportedViewfinderResolutions())
        tempCam.unload()
        

        
        if self.camera.initialize():
            self.setThreadCamera.emit(self.camera)
            
            # self.thread = threading.Thread(target=self.getNewFrame)
            # self.thread.start()
            
            self.ui.camResolutionMenu.setEnabled(True)
            self.ui.actionCamera_Settings.setEnabled(True)
            self.ui.successLabel.setText("READY")
            
            self.ROI = self.ui.streamLabel.getROI()
            self.requestFrame.emit(self.processing,self.resetProcess,self.ROI)
            
            self.resetProcess = False
    
        

    # @QtCore.pyqtSlot()     
    # def alert(self,errorString):
        
    #     err = QErrorMessage(self)
    #     err.showMessage(errorString)
        
    #     msg = QMessageBox()
    #     msg.setWindowTitle("Connection Error")
    #     msg.setText("Camera disconnected.")
    #     msg.setIcon(QMessageBox.Critical)
    #     msg.setStandardButtons(QMessageBox.Ok)
    #     x = msg.exec_()
          
        
