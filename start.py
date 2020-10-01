import mainWindow,sys
from PyQt5.QtWidgets import QApplication

from numpy import int0,median,array
import cv2
from shapely.geometry import Polygon,box
from pylibdmtx.pylibdmtx import decode

import cv2, threading, time

from PyQt5   import QtCore, QtWidgets, QtGui, QtMultimedia


if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)
else:
    app = QtWidgets.QApplication.instance() 
w = mainWindow.MainWindow()
w.showMaximized()
app.exec_()
