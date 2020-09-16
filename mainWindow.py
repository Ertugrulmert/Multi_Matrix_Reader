import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui     import *
from PyQt5.QtCore    import *
from PyQt5    import QtCore, QtMultimedia, QtWidgets

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
        
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.ui.camSelectMenu.aboutToShow.connect(self.prepCamera)
        
        #self.ui.actionSelect_Camera.triggered.connect(self.prepCamera)
        self.ui.actionCamera_Settings.triggered.connect(self.settingsBox)
        
        self.ui.resetDetectButton.clicked.connect(self.resetProcessor)
        
    def closeEvent(self,event):
        self.camera.stop()
        self.camera.unload()
        event.accept() 
        
        
    @QtCore.pyqtSlot()
    def settingsBox(self):
        self.SettingsDialog = SettingsDialog()
        self.setSettingsParams()
        
        self.SettingsDialog.show()
        print(self.camera)
        print(self.SettingsDialog.ui.brightnessSlider)
        
        self.SettingsDialog.ui.defaultResetButton.clicked.connect(self.camera.reset_properties)
        
        self.SettingsDialog.ui.brightnessSlider.valueChanged.connect(self.updateBrightness)
        self.SettingsDialog.ui.gammaSlider.valueChanged.connect(self.updateGamma)
        self.SettingsDialog.ui.sharpnessSlider.valueChanged.connect(self.updateSharpness)
        self.SettingsDialog.ui.panSlider.valueChanged.connect(self.updatePan)
        self.SettingsDialog.ui.tiltSlider.valueChanged.connect(self.updateTilt)
    @QtCore.pyqtSlot()        
    def updateBrightness(self): self.camera.set_brightness(int(self.SettingsDialog.ui.brightnessSlider.tickPosition()))
    @QtCore.pyqtSlot()
    def updateGamma(self): self.camera.set_gamma(int(self.SettingsDialog.ui.gammaSlider.tickPosition()))
    @QtCore.pyqtSlot()
    def updateSharpness(self): self.camera.set_sharpness(int(self.SettingsDialog.ui.sharpnessSlider.tickPosition()))
    @QtCore.pyqtSlot()
    def updatePan(self): self.camera.set_pan(int(self.SettingsDialog.ui.panSlider.tickPosition()))
    @QtCore.pyqtSlot()
    def updateTilt(self): self.camera.set_tilt(int(self.SettingsDialog.ui.tiltSlider.tickPosition()))
        
    def setSettingsParams(self):
        self.SettingsDialog.ui.brightnessSlider.setValue(self.camera.get_brightness())
        self.SettingsDialog.ui.gammaSlider.setValue(self.camera.get_gamma())
        self.SettingsDialog.ui.panSlider.setValue(self.camera.get_pan())
        self.SettingsDialog.ui.tiltSlider.setValue(self.camera.get_tilt())
        self.SettingsDialog.ui.sharpnessSlider.setValue(self.camera.get_sharpness())
        
    @QtCore.pyqtSlot()
    def prepCamera(self):
        
        cameraInfos = QtMultimedia.QCameraInfo.availableCameras()
        self.ui.camSelectMenu.clear()
        
        for i in range(len(cameraInfos)):
            camAction = self.ui.camSelectMenu.addAction("Camera %d" % i)
            camAction.setText(cameraInfos[i].description())
            camAction.setCheckable(True)
            camAction.triggered.connect( lambda chk, i=i: self.setCamera(cameraInfos[i]) )
            
        self.update()
        #self.ui.camSelectMenu.triggered.connect
       
    @QtCore.pyqtSlot()
    def setCamera(self,cameraInfo):
        
        self.camera = QtMultimedia.QCamera(cameraInfo)
        self.camera.setViewfinder(self.ui.streamView)
        self.camera.setCaptureMode(QtMultimedia.QCamera.CaptureViewfinder)
        self.camera.error.connect(lambda: self.alert(self.my_webcam.errorString()))
        self.camera.start()
        self.ui.actionCamera_Settings.setEnabled(True)
        
    def alert(self,errorString):
        
        err = QErrorMessage(self)
        err.showMessage(errorString)
        
        msg = QMessageBox()
        msg.setWindowTitle("Connection Error")
        msg.setText("Camera disconnected.")
        msg.setIcon(QMessageBox.Critical)
        msg.setStandardButtons(QMessageBox.Ok)
        x = msg.exec_()
          
    @QtCore.pyqtSlot()
    def resetProcessor(self):
        self.processor.reset()
        
        
        

if __name__ == '__main__':
    
    
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())