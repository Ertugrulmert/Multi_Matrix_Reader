import cv2, threading, time, sys
from datetime import date

from PyQt5   import QtCore, QtWidgets, QtGui, QtMultimedia

from mainWindowUI import Ui_MainWindow

from Modules import Camera, Worker, showLogin
from database import dataBase
from frameProcessor import frameProcessor

       
class MainWindow(QtWidgets.QMainWindow, QtCore.QObject):
    
    """
    The majority of the GUI functionality of the program is within MainWindow.
    Connects signals and slots between various GUI elements and the processor,
    the camera, user inputs and the database.
    
    ...


    Signals
    ---------
    
    requestFrame : QtCore.pyqtSignal(bool,bool,tuple)
        requests a new frame to be processed by the Worker object in a seperate thread
        
    setThreadCamera : QtCore.pyqtSignal(Camera)
        provides a copy of the current caemra to the thread doing processing and fame capturing
    
    Attributes
    ----------
    
    camera : Camera
        The camera selected for frame capture
        
    database : dataBase
        Object working as an interface for PostgreSQL databases
        
    processing : bool
        Flag to determine if the frame should be processed or directly displayed
        
    resetProcess : bool
        Flag to determine if the processor should be reset. When the processor is reset,
        the previosly detected boxes it stores in its instance variable are deleted.
        Reset is used when camera is moved or objects under the camera are to be
        rearranged.
        
    autoScale : tuple of 2 ints
        The factor by which each frame is resized automatically by the GUI functions,
        when ROI is drawn, if the coordinates of the original frame and the displayed image do not match,
        discrepancies occur. To avoid this, autoScale keeps track of transformations and
        makes sure ROI can be mapped correctly to the original image.
        
    codeList : list of string
        Stores the decoded datamtrix codes since the beginning of the program
        When the processor is reset, this list is not affected, it receives updates
        from a temporary list. When codes are sent to the database, this list is used.
        Codes can accumulate from subsequent sessions with different sets of boxes.
        
    tempList : list of string
        Stores the decoded datamtrix codes for each session between the Start and Stop
        commands from the Start button. Used to update codeList when session is stopped.
        This list is wiped out when the processor is reset.
        
        
    ui : Ui_MainWindow
        UI Description automatically generated by Qt Designer
        - later modified to make several changes 
        
    thread1 : QtCore.QThread
        Thread where the worker object is placed. 
        Computationally heavy operations are carried out in this thread   
    
    worker : Worker
        Contains camera and image processing function calls
        Computationally heavy operations are placed here ot be moved to antoher thread
        so that the GUI thread will function normally
    
    Methods
    ----------
    closeEvent(self,event)
        Modified to stop the worker and thread
    
    updateList(self,newList)
         Updates the list UI and the temporary list of the session given a list 
         received from a signal
    
    settingsBox(self)
        Opens the camera settings UI 
    
    toggleProcessing(self)
        Determines if the processor should work, updates UI accordingly
    
    resetProcessor(self)
        Resets the processor object, deleting the boxes and matrix codes retrieved
        in the last Start/Stop session
    
    successUpdate(self,success)
        Updates UI to show if all matrices have been decoded successfully
    
    drawFrame(self,img,scaling_factor)
        Draws the QImage (processed frame) sent from the worker, updates the
        ROI and  requests a new frame after completion
    
    showResolutions(self)
        Adds the available resolutions to the UI (as MenuBar Actions)
    
    prepCamera(self)
        Adds the available cameras to the UI (as MenuBar Actions) and connects
        actions to setCamera
    
    setCamera(self,cameraInfo,i)
        Inıtializes the camera and available resolutions
    
    insert_todays_data(self)
        Saves the codes accumulated since the program started in the table 
        corresponding to the current day (table format: "day_dd_mm_yy")
    
    delete_todays_data(self)
        Deletes the table corresponding to the current day (table format: "day_dd_mm_yy")
    
    display_tables(self)
        Retrieves the names of the tables in the database and displays them
        in a popup window. When a table name is doubleclicked, display_items
        will be called.
    
    display_items(self, item)
        Displays the data inside a table given a table name
        
    login(self)
        Creates the login QDialog to log into a PostgreSQL database
    
    login_result(self,login_success)
        Displays a popup notifying the user 
        if login to database was successful or not
    
    insert_result(self,insert_success)
        Displays a popup notifying the user 
        if insertion of data to database was successful or not
    
    alert(self,errorString)
        Notifies the user of errors occured in database processes.
    """
    
    
    
    requestFrame = QtCore.pyqtSignal(bool,bool,tuple)
    setThreadCamera = QtCore.pyqtSignal(Camera)
    
    def __init__(self):
        super().__init__()
        
    
        self.camera = None
        self.database = dataBase()
        #initially the system is not processing frames
        self.processing = False
        self.resetProcess = False
        self.autoScale = (1,1)
        
        #Lists to store matrix codes
        self.codeList = []
        self.tempList = []
        
        #Setting up the UI
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        #worker is responsible for most computationaly heavy tasks
        #Worker and its thread are initialised
        self.thread1 = QtCore.QThread(parent=self)
        self.worker = Worker()
        self.worker.moveToThread(self.thread1)
        self.thread1.start()
        
        # SIGNAL - SLOT CONNECTIONS
        
        #worker signals
        self.worker.frameReady.connect(self.drawFrame)
        self.worker.updateList.connect(self.updateList)
        self.worker.successUpdate.connect(self.successUpdate)
        
        #ui signals
            #buttons
        self.ui.startButton.clicked.connect(self.toggleProcessing)
        self.ui.resetDetectButton.clicked.connect(self.resetProcessor) 
        self.ui.ROIButton.clicked.connect(self.ui.streamLabel.toggleROI)
            #Menus and Actions
        self.ui.camSelectMenu.aboutToShow.connect(self.prepCamera)
        self.ui.camResolutionMenu.aboutToShow.connect(self.showResolutions)     
        self.ui.actionCamera_Settings.triggered.connect(self.settingsBox)
        
        self.ui.actionLogin.triggered.connect(self.login)
        self.ui.actionUpload.triggered.connect(self.insert_todays_data)
        self.ui.actionDelete.triggered.connect(self.delete_todays_data)
        self.ui.actionDisplay.triggered.connect(self.display_tables)
        
        
        #custom defined signals
        self.requestFrame.connect(self.worker.getNewFrame)
        self.setThreadCamera.connect(self.worker.setCamera)
        
        #database signals
        self.database.DB_error.connect(self.alert)
        self.database.could_connect.connect(self.login_result)
        self.database.DB_inserted.connect(self.insert_result)
        
    
    @QtCore.pyqtSlot()
    def closeEvent(self,event):  
        """
        Modified to stop the worker and thread

        """
        if self.camera is not None: 
            self.camera.close()
            self.camera = None

            if self.thread1 is not None and self.thread1.isRunning():
                 self.worker.stop()
                 self.thread1.quit()
                 self.thread1.wait()
        event.accept() 
        
           
    @QtCore.pyqtSlot(list)    
    def updateList(self,newList):
        """
        Updates the list UI and the temporary list of the session given a list 
        received from a signal

        Parameters
        ----------
        newList : list of str
            matrix codes decoded in the last round of processing

        Returns
        -------
        None.

        """
        self.ui.listWidget.clear()
        #List on GUI shows both temporarly list and the list that collects items
        #throughout the program runtime
        self.ui.listWidget.addItems(self.codeList)
        self.ui.listWidget.addItems(self.tempList)
        #temporary code list updated
        self.tempList = newList.copy()
        
    @QtCore.pyqtSlot()
    def settingsBox(self):
        """
        Opens the camera settings UI 

        Returns
        -------
        None.

        """
        #checking if camera is usable
        if self.camera is not None and self.camera.isReady():
            self.camera.open_settings_dialog()
            
    def toggleProcessing(self): 
        """
        Determines if the processor should work, updates UI accordingly

        Returns
        -------
        None.

        """
        self.processing = not self.processing
        #if started processing now
        if self.processing:
            self.ui.startButton.setText("Stop")
            self.ui.successLabel.setText("PROCESSING")
            self.ui.successLabel.setStyleSheet("")
        #if stopped processing now
        else: 
            self.ui.startButton.setText("Start")
            self.ui.successLabel.setText("READY")
            self.ui.successLabel.setStyleSheet("")
            
            self.codeList.extend(self.tempList)
            self.tempList = []
            
    def resetProcessor(self):
        """
        Resets the processor object, deleting the boxes and matrix codes retrieved
        in the last Start/Stop session

        Returns
        -------
        None.

        """
        self.resetProcess = True
        #temporary list of codes is cleared upon reset
        self.tempList = []
        
    @QtCore.pyqtSlot(bool)
    def successUpdate(self,success):
        """
        Updates UI to show if all matrices have been decoded successfully

        Parameters
        ----------
        success : bool
            Flag that represents successful decoding

        Returns
        -------
        None.

        """
        if success:
            self.ui.successLabel.setText("SUCCESS")
            self.ui.successLabel.setStyleSheet("background-color: lightgreen") 
        else:
            self.ui.successLabel.setText("PROCESSING")
            self.ui.successLabel.setStyleSheet("")
                    
    @QtCore.pyqtSlot(QtGui.QImage,float)            
    def drawFrame(self,img,scaling_factor):
        """
        Draws the QImage (processed frame) sent from the worker, updates the
        ROI and  requests a new frame after completion

        Parameters
        ----------
        img : QImage
            Image to be displayed, given from a signal emitted by worker
        scaling_factor : float
            If the image was downSized, this factor will be used for ROI calibration

        Returns
        -------
        None.

        """
        #real size is the reference to determine how the image was trasformed
        #upon display on theGUI
        realsize = (img.height(),img.width())
        pix = QtGui.QPixmap.fromImage(img)
              
        try:
            #displaying the image on the label
            self.ui.streamLabel.setPixmap(pix) 
            #getting the size of the displayed image to see if the image size changes 
            scaledsize = pix.rect()
            #factor calcualted to calibrate ROI location
            self.autoScale =( scaledsize.height()/realsize[0]/scaling_factor , scaledsize.width()/realsize[1]/scaling_factor )
            #ROI obtained from coordinates on label
            self.ROI = self.ui.streamLabel.getROI()
            #ROI transformed accroding to trasformations that the original iamge went through
            self.ROI = ( int(self.ROI[0]*self.autoScale[0]) , int(self.ROI[1]*self.autoScale[1]) ,\
                       int(self.ROI[2]*self.autoScale[0])  , int(self.ROI[3]*self.autoScale[1]) )
            #transformed ROI is used in processing 
            self.requestFrame.emit(self.processing,self.resetProcess,self.ROI)
            self.resetProcess = False
            
        except:
            print("Drawing Exception")
            print(sys.exc_info()[0], "occurred.")
            time.sleep(0.5)
    
        
            
    def showResolutions(self):
        """
        Adds the available resolutions to the UI (as MenuBar Actions)

        Returns
        -------
        None.

        """
        if self.camera is not None and self.camera.isReady():
            #available resolutions retreived from camera
            cameraResList = self.camera.get_available_resolutions()
            self.ui.camResolutionMenu.clear()
            
            for i in range(len(cameraResList)):
                #listing the available resolutions in a Menu
                resAction = self.ui.camResolutionMenu.addAction("Resolution %d" % i)
                resAction.setText(cameraResList[i])
                resAction.setCheckable(True)
                #resolution will change when a menu item is selected
                resAction.triggered.connect( lambda chk, i=i: self.worker.setCameraResolution(i) )
                
            self.update()
    
            
        
    @QtCore.pyqtSlot()
    def prepCamera(self):
        """
        Adds the available cameras to the UI (as MenuBar Actions) and connects
        actions to setCamera

        Returns
        -------
        None.

        """
        #finding available cameras
        cameraInfos = QtMultimedia.QCameraInfo.availableCameras()
        self.ui.camSelectMenu.clear()
        
        for i in range(len(cameraInfos)):
            #adding available cameras to menu for camera selection
            camAction = self.ui.camSelectMenu.addAction("Camera %d" % i)
            camAction.setText(cameraInfos[i].description())
            camAction.setCheckable(True)
            camAction.triggered.connect( lambda chk, i=i: self.setCamera(cameraInfos[i],i) )
            
        self.update()
       
    @QtCore.pyqtSlot()
    def setCamera(self,cameraInfo,i):
        """
        Inıtializes the camera and available resolutions

        Parameters
        ----------
        cameraInfo : TYPE
            DESCRIPTION.
        i : int
            index of selected camera in the list of available cameras

        Returns
        -------
        None.

        """
        #if a camera is already working, it is stopped before a new one beigns
        if self.camera is not None: 
            self.camera.close()
            self.camera = None
        
        #QCamera only used to retrieve available camera resolutions
        #Otherwise OpenCV's camera system is used for frame capturing
        #"Unsupported Media Type" will be written in the log when QCamera is used 
        #This will not affect the functionality of the program
        tempCam = QtMultimedia.QCamera(cameraInfo)
        tempCam.load()
        #initialising camera
        self.camera = Camera(i)
        #storing the resolutions found by QCamera in the camera object
        self.camera.set_available_resolutions(tempCam.supportedViewfinderResolutions())
        #QCamera is destroyed
        tempCam.unload()
        

        
        if self.camera.initialize():
            #Camera obejct is sent to the worker in teh other thread
            self.setThreadCamera.emit(self.camera)
            
            #Camera related GUI ıotions enabled
            self.ui.camResolutionMenu.setEnabled(True)
            self.ui.actionCamera_Settings.setEnabled(True)
            self.ui.successLabel.setText("READY")
            
            self.ROI = self.ui.streamLabel.getROI()
            #First frame is retreived
            self.requestFrame.emit(self.processing,self.resetProcess,self.ROI)
            
            self.resetProcess = False
            
            
            
    @QtCore.pyqtSlot()    
    def insert_todays_data(self):
        """
        Saves the codes accumulated since the program started in the table 
        corresponding to the current day (table format: "day_dd_mm_yy")

        Returns
        -------
        None.

        """
        #retrieving the date andmatting in a database compatible way for
        today = date.today()
        # dd/mm/YY
        today = today.strftime("%d_%m_%Y")
        #forming the table name
        table_name = "day_"+today
        self.database.insert_list(table_name, self.codeList)
        
    @QtCore.pyqtSlot()    
    def delete_todays_data(self):
        """
        Deletes the table corresponding to the current day (table format: "day_dd_mm_yy")

        Returns
        -------
        None.

        """
        #retrieving the date andmatting in a database compatible way for
        today = date.today()
        # dd/mm/YY
        today = today.strftime("%d_%m_%Y")
        #forming the table name
        table_name = "day_"+today
        self.database.delete_table(table_name)
        
    @QtCore.pyqtSlot()         
    def display_tables(self):
        """
        Retrieves the names of the tables in the database and displays them
        in a popup window. When a table name is doubleclicked, display_items
        will be called.

        Returns
        -------
        None.

        """
        displayDialog = QtWidgets.QDialog(self)
        #deleting the question mark of the dialog
        displayDialog.setWindowFlags(displayDialog.windowFlags()
                            ^ QtCore.Qt.WindowContextHelpButtonHint)

        #List creation
        codeListWidget = QtWidgets.QListWidget()
        tempList = self.database.get_tables()
        #converting table names to string
        tempList = [''.join(name) for name in tempList]
        codeListWidget.addItems(tempList)
        #when table names are clicked, a new popup will display the table data
        codeListWidget.itemDoubleClicked.connect(self.display_items)
        codeListWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)
        displayDialog.setWindowTitle('Database Tables')

        layout = QtWidgets.QVBoxLayout(displayDialog)
        
        layout.addWidget( codeListWidget)
        displayDialog.setLayout(layout)

        ###lock resize
        displayDialog.setSizeGripEnabled(False)
       
        displayDialog.exec_()
        
    @QtCore.pyqtSlot(QtWidgets.QListWidgetItem )         
    def display_items(self, item):
        """
        Displays the data inside a table given a table name

        Parameters
        ----------
        item : QtWidgets.QListWidgetItem
            The title of a table from the PostgreSQL database

        Returns
        -------
        None.

        """
        displayDialog = QtWidgets.QDialog(self)
        #deleting the question mark of the dialog
        displayDialog.setWindowFlags(displayDialog.windowFlags()
                            ^ QtCore.Qt.WindowContextHelpButtonHint)


        codeListWidget = QtWidgets.QListWidget()

        codeListWidget.addItems(self.database.get_data(item.text()))
        codeListWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)
        
        displayDialog.setWindowTitle(item.text())

        layout = QtWidgets.QVBoxLayout(displayDialog)

        layout.addWidget( codeListWidget)
        displayDialog.setLayout(layout)

        ###lock resize
        displayDialog.setSizeGripEnabled(False)      
        displayDialog.exec_()
        

        
        
    @QtCore.pyqtSlot() 
    def login(self):
        """
        Creates the login QDialog to log into a PostgreSQL database

        Returns
        -------
        None.

        """
        loginDialog = showLogin(self)
        #logging into the database
        loginDialog.loginSignal.connect(self.database.login)
        loginDialog.show()
        
    @QtCore.pyqtSlot(bool)     
    def login_result(self,login_success):
        """
        Displays a popup notifying the user 
        if login to database was successful or not

        Parameters
        ----------
        login_success : bool
            whether database login was successful or not

        Returns
        -------
        None.

        """
        
        msg = QtWidgets.QMessageBox()
        if login_success:
            msg.setWindowTitle("Login Successful")
            msg.setText("Entered login credentials are correct.")
            self.ui.actionUpload.setEnabled(True)
            self.ui.actionDelete.setEnabled(True)
            self.ui.actionDisplay.setEnabled(True)
        else:
            msg.setWindowTitle("Login Failed")
            msg.setText("Wrong credentials entered.")
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg.exec_() 
        
        
    @QtCore.pyqtSlot(bool)     
    def insert_result(self,insert_success):
        """
        Displays a popup notifying the user 
        if insertion of data to database was successful or not

        Parameters
        ----------
        insert_success : bool
            Whether data insertion was successful or not

        Returns
        -------
        None.

        """
        
        msg = QtWidgets.QMessageBox()
        if insert_success:
            msg.setWindowTitle("Data Update Successful")
            msg.setText("New codes were succesfully saved.")
        else:
            msg.setWindowTitle("Data Update Failed")
            msg.setText("New codes could not be saved.")
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg.exec_() 
        

    @QtCore.pyqtSlot(str)     
    def alert(self,errorString):
        """
        Notifies the user of errors occured in database processes.

        Parameters
        ----------
        errorString : str
            Describes an error that occured

        Returns
        -------
        None.

        """
        
        err = QtWidgets.QErrorMessage(self)
        err.showMessage(errorString)
        
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle("Error Occured")
        msg.setText(errorString)
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg.exec_()
          
        
    
                  