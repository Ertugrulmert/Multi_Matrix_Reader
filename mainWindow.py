import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui     import *
from PyQt5.QtCore    import *

from mainWindowUI import Ui_MainWindow
from camSettingsUI import Ui_camSettingsDialog

from Modules import Camera
from frameProcessor import frameProcessor

processor, Camera = None,None

class SettingsDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_camSettingsDialog()
        self.ui.setupUi(self)



        
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
    
    def settingsBox(self):
        self.SettingsDialog = SettingsDialog()
        self.SettingsDialog.show()
        

if __name__ == '__main__':
    
    processor = frameProcessor()
    
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())