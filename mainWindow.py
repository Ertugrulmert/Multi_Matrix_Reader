import sys,cv2, threading
from PyQt5.QtWidgets import *
from PyQt5.QtGui     import *
from PyQt5.QtCore    import *
from PyQt5    import QtCore, QtWidgets, QtGui, QtMultimedia, QtMultimediaWidgets

from mainWindowUI import Ui_MainWindow
from camSettingsUI import Ui_camSettingsDialog

from Modules import Camera
from frameProcessor import frameProcessor


class SettingsDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_camSettingsDialog()
        self.ui.setupUi(self)
        self.ui.okButton.clicked.connect(self.close)
        


        
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.processor = frameProcessor()
        self.camera = None
        
        self.processing = False
        self.resetProcess = False
        self.threadpool = QThreadPool()
        
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.ui.camSelectMenu.aboutToShow.connect(self.prepCamera)
        
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
            self.updateList(matrices)
            self.drawFrame(frame)
            # processorThread = ProcessorThread(self.processor.process(frame))
            # processorThread.signals.newFrame.connect(self.drawFrame)
            # processorThread.signals.matrixList.connect(self.updateList)
            # processorThread.signals.finished.connect(self.getNewFrame)
            # self.threadpool.start(processorThread)
    @QtCore.pyqtSlot()    
    def updateList(self,newList):
        self.ui.listWidget.clear()
        self.ui.listWidget.addItems(newList)
        
        
    def getNewFrame(self):
        while self.camera is not None and self.camera.isReady():
            ret ,frame= self.camera.captureFrame()
            if not ret:
                continue
            if self.resetProcess: self.processor.reset()
                
            if self.processing: self.processFrame(frame)
            else: self.drawFrame(frame)

            # captureThread = CaptureThread(self.camera)
            
            # print("thread built")
            # if self.processing: captureThread.frameSignal.connect(self.processFrame)
            # else: captureThread.frameSignal.connect(self.drawFrame)
            # self.threadpool.start(captureThread)
            # print("thread started")
            
    @QtCore.pyqtSlot()            
    def drawFrame(self,frame):

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = QtGui.QImage(frame, frame.shape[1], frame.shape[0], QtGui.QImage.Format_RGB888)
        pix = QtGui.QPixmap.fromImage(img)
        self.ui.streamLabel.setPixmap(pix)  
        self.getNewFrame()
        
        
        
    @QtCore.pyqtSlot()
    def settingsBox(self):
        self.SettingsDialog = SettingsDialog()
        self.setSettingsParams()
        
        self.SettingsDialog.show()
        
        self.SettingsDialog.ui.defaultResetButton.clicked.connect(self.camera.reset_properties)
        
        self.SettingsDialog.ui.brightnessSlider.sliderReleased.connect(self.updateBrightness)
        self.SettingsDialog.ui.gammaSlider.valueChanged.connect(self.updateGamma)
        self.SettingsDialog.ui.sharpnessSlider.valueChanged.connect(self.updateSharpness)
        self.SettingsDialog.ui.panSlider.valueChanged.connect(self.updatePan)
        self.SettingsDialog.ui.tiltSlider.valueChanged.connect(self.updateTilt)
    @QtCore.pyqtSlot()        
    def updateBrightness(self):
        self.camera.set_brightness(int(self.SettingsDialog.ui.brightnessSlider.tickPosition()))
        self.SettingsDialog.ui.brightnessSlider.setValue(int(self.camera.get_brightness()))
    @QtCore.pyqtSlot()
    def updateGamma(self):
        self.camera.set_gamma(int(self.SettingsDialog.ui.gammaSlider.tickPosition()))
        self.SettingsDialog.ui.gammaSlider.setValue(int(self.camera.get_gamma()))
    @QtCore.pyqtSlot()
    def updateSharpness(self):
        self.camera.set_sharpness(int(self.SettingsDialog.ui.sharpnessSlider.tickPosition()))
    @QtCore.pyqtSlot()
    def updatePan(self):
        self.camera.set_pan(int(self.SettingsDialog.ui.panSlider.tickPosition()))
        self.SettingsDialog.ui.panSlider.setValue(int(self.camera.get_pan()))
    @QtCore.pyqtSlot()
    def updateTilt(self):
        self.camera.set_tilt(int(self.SettingsDialog.ui.tiltSlider.tickPosition()))
        self.SettingsDialog.ui.tiltSlider.setValue(int(self.camera.get_tilt()))
        self.SettingsDialog.ui.sharpnessSlider.setValue(int(self.camera.get_sharpness()))
        
    def setSettingsParams(self):
        self.SettingsDialog.ui.brightnessSlider.setValue(int(self.camera.get_brightness()))
        self.SettingsDialog.ui.gammaSlider.setValue(int(self.camera.get_gamma()))
        self.SettingsDialog.ui.panSlider.setValue(int(self.camera.get_pan()))
        self.SettingsDialog.ui.tiltSlider.setValue(int(self.camera.get_tilt()))
        self.SettingsDialog.ui.sharpnessSlider.setValue(int(self.camera.get_sharpness()))
        self.SettingsDialog.ui.resolutionBox.clear()
        self.SettingsDialog.ui.resolutionBox.addItems(self.camera.get_available_resolutions())
        
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
        
        #QCamera only used to retrieve available camera resolutions
        tempCam = QtMultimedia.QCamera(cameraInfo)
        tempCam.load()
        
        self.camera = Camera(i)
        self.camera.set_available_resolutions(tempCam.supportedViewfinderResolutions())
        tempCam.unload()
        
        if self.camera.initialize():
            th = threading.Thread(target=self.getNewFrame)
            th.start()
            self.ui.actionCamera_Settings.setEnabled(True)

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