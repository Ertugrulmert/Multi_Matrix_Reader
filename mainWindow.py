import sys,cv2, threading, time
from PyQt5.QtWidgets import *
from PyQt5.QtGui     import *
from PyQt5.QtCore    import *
from PyQt5    import QtCore, QtWidgets, QtGui, QtMultimedia, QtMultimediaWidgets

from mainWindowUI import Ui_MainWindow
from camSettingsUI import Ui_camSettingsDialog

from Modules import Camera
from frameProcessor import frameProcessor


# class SettingsDialog(QDialog):
#     def __init__(self):
#         super().__init__()
#         self.ui = Ui_camSettingsDialog()
#         self.ui.setupUi(self)
#         self.ui.okButton.clicked.connect(self.close)
        


        
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.processor = frameProcessor()
        self.camera = None
        
        self.processing = False
        self.resetProcess = False
        self.thread = None

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.ui.camSelectMenu.aboutToShow.connect(self.prepCamera)
        self.ui.camResolutionMenu.aboutToShow.connect(self.showResolutions)
        
        #self.ui.actionSelect_Camera.triggered.connect(self.prepCamera)
        self.ui.actionCamera_Settings.triggered.connect(self.settingsBox)
        
        self.ui.startButton.clicked.connect(self.toggleProcessing)
        self.ui.resetDetectButton.clicked.connect(self.resetProcessor)
    
    @QtCore.pyqtSlot()
    def closeEvent(self,event):  
        if self.camera is not None: 
            self.camera.close()
            self.camera = None
            self.processing = None
            if self.thread is not None and self.thread.is_alive():
                self.thread.join()
        event.accept() 
        
    @QtCore.pyqtSlot()
    def resetProcessor(self):
        self.resetProcess = True
        
    @QtCore.pyqtSlot()    
    def toggleProcessing(self): self.processing = not self.processing
    
    @QtCore.pyqtSlot() 
    def processFrame(self,frame):
        if self.processor is not None:
            frame, matrices = self.processor.process(frame)
            if self.processor.isAllDetected():
                self.ui.successLabel.setText("SUCCESS")
                self.ui.successLabel.setStyleSheet("background-color: lightgreen") 
            else: self.ui.successLabel.setText("PROCESSING")
            self.updateList(matrices)
            self.drawFrame(frame)

        
    @QtCore.pyqtSlot()    
    def updateList(self,newList):
        self.ui.listWidget.clear()
        self.ui.listWidget.addItems(newList)
        
        
    def getNewFrame(self):
        
        while self.camera is not None:
            
            if not self.camera.isReady():
                continue
            
            ret ,frame= self.camera.captureFrame()
            if not ret:
                continue
            if self.resetProcess: 
                self.processor.reset()
                self.resetProcess = False
                
            if self.processing: self.processFrame(frame)
            else: 
                if  frame.shape[1] > 1920 :
                    frame = frameProcessor.downSize(frame)
                self.drawFrame(frame)

            
                    
    @QtCore.pyqtSlot()            
    def drawFrame(self,frame):
        
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = QtGui.QImage(frame, frame.shape[1], frame.shape[0], QtGui.QImage.Format_RGB888)
        pix = QtGui.QPixmap.fromImage(img)
        self.ui.streamLabel.setPixmap(pix) 
        self.getNewFrame()
    
        
        
        
    @QtCore.pyqtSlot()
    def settingsBox(self):
        if self.camera is not None and self.camera.isReady():
            self.camera.open_settings_dialog()
            
    def showResolutions(self):
        if self.camera is not None and self.camera.isReady():
            cameraResList = self.camera.get_available_resolutions()
            self.ui.camResolutionMenu.clear()
            
            for i in range(len(cameraResList)):
                resAction = self.ui.camResolutionMenu.addAction("Resolution %d" % i)
                resAction.setText(cameraResList[i])
                resAction.setCheckable(True)
                resAction.triggered.connect( lambda chk, i=i: self.setResolution(i) )
                
            self.update()
    
    @QtCore.pyqtSlot()
    def setResolution(self,i):
        self.camera.pause_cam()
        self.camera.set_resolution(i)
        self.camera.resume_cam()
            
        
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
            if self.thread is not None and self.thread.is_alive() : self.thread.join()
        
        #QCamera only used to retrieve available camera resolutions
        tempCam = QtMultimedia.QCamera(cameraInfo)
        tempCam.load()
        
        self.camera = Camera(i)
        self.camera.set_available_resolutions(tempCam.supportedViewfinderResolutions())
        tempCam.unload()
        

        
        if self.camera.initialize():
            self.thread = threading.Thread(target=self.getNewFrame)
            self.thread.start()
            self.ui.camResolutionMenu.setEnabled(True)
            self.ui.actionCamera_Settings.setEnabled(True)
            self.ui.successLabel.setText("READY")

    
        

    @QtCore.pyqtSlot()     
    def alert(self,errorString):
        
        err = QErrorMessage(self)
        err.showMessage(errorString)
        
        msg = QMessageBox()
        msg.setWindowTitle("Connection Error")
        msg.setText("Camera disconnected.")
        msg.setIcon(QMessageBox.Critical)
        msg.setStandardButtons(QMessageBox.Ok)
        x = msg.exec_()
          
        
        
        

if __name__ == '__main__':
    
    
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())