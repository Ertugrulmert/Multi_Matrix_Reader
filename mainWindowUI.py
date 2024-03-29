
# Form implementation generated from reading ui file 'mainWindowUI.ui'
#
# Created by: PyQt5 UI code generator 5.15.0
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets,QtMultimedia, QtMultimediaWidgets

from Modules import LabelwROI

class Ui_MainWindow(object):
    """ UI Description automatically generated by Qt Designer
    - later modified to make several changes"""
    
    
    def setupUi(self, MainWindow):
        
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(2223, 1660)
        
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
    
        
        # FRAME FOR BUTTONS AND LIST
        self.leftFrame = QtWidgets.QFrame(self.centralwidget)
        
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(30)
        sizePolicy.setHeightForWidth(self.leftFrame.sizePolicy().hasHeightForWidth())
        self.leftFrame.setSizePolicy(sizePolicy)
        self.leftFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.leftFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.leftFrame.setObjectName("leftFrame")
        
        #LAYOUT FOR LEFT FRAME
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.leftFrame)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        
        #FRAME FOR BUTTONS
        self.buttonFrame = QtWidgets.QFrame(self.leftFrame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.buttonFrame.sizePolicy().hasHeightForWidth())
        self.buttonFrame.setSizePolicy(sizePolicy)
        self.buttonFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.buttonFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.buttonFrame.setObjectName("buttonFrame")
        
        #LAYOUT FOR BUTTONS
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout(self.buttonFrame)
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        
        #START BUTTON
        self.startButton = QtWidgets.QPushButton(self.buttonFrame)
        self.startButton.setEnabled(True)
        self.startButton.setObjectName("startButton")
        self.horizontalLayout_5.addWidget(self.startButton)
        
        #RESET DETECTION BUTTON
        self.resetDetectButton = QtWidgets.QPushButton(self.buttonFrame)
        self.resetDetectButton.setObjectName("resetDetectButton")
        self.horizontalLayout_5.addWidget(self.resetDetectButton)
        self.verticalLayout_2.addWidget(self.buttonFrame)
        
        #SELECT ROI BUTTON
        self.ROIButton = QtWidgets.QPushButton(self.buttonFrame)
        self.ROIButton.setObjectName("ROIButton")
        self.horizontalLayout_5.addWidget(self.ROIButton)
        self.verticalLayout_2.addWidget(self.buttonFrame)
        
        #SETTING UP LIST AREA
        self.scrollArea = QtWidgets.QScrollArea(self.leftFrame)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 449, 1355))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.scrollAreaWidgetContents)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        
        #LISTVIEW
        self.listWidget = QtWidgets.QListWidget(self.scrollAreaWidgetContents)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.listWidget.sizePolicy().hasHeightForWidth())
        self.listWidget.setSizePolicy(sizePolicy)
        self.listWidget.setObjectName("listWidget")
        
        #ADDING COMPONENTS
        self.horizontalLayout_3.addWidget(self.listWidget)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout_2.addWidget(self.scrollArea)
        self.horizontalLayout.addWidget(self.leftFrame)
        
        
        self.rightFrame = QtWidgets.QFrame(self.centralwidget)
        self.verticalLayout_1 = QtWidgets.QVBoxLayout(self.rightFrame)
        self.verticalLayout_1.setObjectName("verticalLayout_1")
        
        
        
        self.successLabel = QtWidgets.QLabel(self.rightFrame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.successLabel.sizePolicy().hasHeightForWidth())
        self.successLabel.setSizePolicy(sizePolicy)
        self.successLabel.setObjectName("successLabel")
        self.successLabel.setFont(QtGui.QFont("Arial", 20, QtGui.QFont.Bold))
        self.successLabel.setAlignment(QtCore.Qt.AlignCenter)
        
        #VIDEO STREAMING AREA 
        self.streamLabel = LabelwROI(self.rightFrame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.streamLabel.sizePolicy().hasHeightForWidth())
        self.streamLabel.setSizePolicy(sizePolicy)
        self.streamLabel.setObjectName("streamLabel")
        self.streamLabel.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        
        self.verticalLayout_1.addWidget(self.successLabel)
        self.verticalLayout_1.addWidget(self.streamLabel)
        self.horizontalLayout.addWidget(self.rightFrame)
        
        
        
        MainWindow.setCentralWidget(self.centralwidget)
        
        #MENU BAR
        
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 2223, 47))
        self.menubar.setObjectName("menubar")
        
        #CAMERA MENU
        self.camSelectMenu = QtWidgets.QMenu(self.menubar)
        self.camSelectMenu.setObjectName("camSelectMenu")
        
        #RESOLUTION MENU
        self.camResolutionMenu = QtWidgets.QMenu(self.menubar)
        self.camResolutionMenu.setObjectName("camResolutionMenu")
        self.camResolutionMenu.setEnabled(False)
        
        
        MainWindow.setMenuBar(self.menubar)
        
        
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        

        
        #CAMERA SETTINGS OPTION
        self.actionCamera_Settings = QtWidgets.QAction(MainWindow)
        self.actionCamera_Settings.setEnabled(False)
        self.actionCamera_Settings.setObjectName("actionCamera_Settings")
        
        
        #DATABASE MENU
        self.dataBaseMenu = QtWidgets.QMenu(self.menubar)
        self.dataBaseMenu.setObjectName("dataBaseMenu")
        
        self.actionLogin = QtWidgets.QAction(MainWindow)
        self.actionLogin.setObjectName("Login")
        
        self.actionDisplay = QtWidgets.QAction(MainWindow)
        self.actionDisplay.setEnabled(False)
        self.actionDisplay.setObjectName("Display")
        
        self.actionUpload = QtWidgets.QAction(MainWindow)
        self.actionUpload.setEnabled(False)
        self.actionUpload.setObjectName("Upload")
        
        self.actionDelete = QtWidgets.QAction(MainWindow)
        self.actionDelete.setEnabled(False)
        self.actionDelete.setObjectName("Delete_Today")
        
        #ADDING COMPONENTS        
        self.dataBaseMenu.addAction(self.actionLogin)
        self.dataBaseMenu.addAction(self.actionDisplay )
        self.dataBaseMenu.addAction(self.actionUpload)
        self.dataBaseMenu.addAction(self.actionDelete)
        
        self.menubar.addAction(self.camSelectMenu.menuAction())
        self.menubar.addAction(self.camResolutionMenu.menuAction())
        self.menubar.addAction(self.actionCamera_Settings)
        self.menubar.addAction(self.dataBaseMenu.menuAction())

        self.retranslateUi(MainWindow)
        
        
        
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.startButton.setText(_translate("MainWindow", "Start"))
        self.resetDetectButton.setText(_translate("MainWindow", "Reset Detection"))
        self.ROIButton.setText(_translate("MainWindow", "ROI Selection"))
        self.camSelectMenu.setTitle(_translate("MainWindow", "Select Camera"))
        self.camResolutionMenu.setTitle(_translate("MainWindow", "Select Resolution"))
        self.dataBaseMenu.setTitle(_translate("MainWindow", "Database"))
        self.actionCamera_Settings.setText(_translate("MainWindow", "Camera Settings"))
        self.successLabel.setText(_translate("MainWindow", "No Camera Selected"))
        
        self.actionLogin.setText(_translate("MainWindow", "Login"))
        self.actionDisplay.setText(_translate("MainWindow", "Display Tables"))
        self.actionUpload.setText(_translate("MainWindow", "Upload Data"))
        self.actionDelete.setText(_translate("MainWindow", "Delete Today's Data"))

