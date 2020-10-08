from PyQt5 import QtWidgets,QtCore,QtGui
from PyQt5.QtCore import QRect, Qt
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen
import cv2, sys
from frameProcessor import frameProcessor

class Camera:
    """
    Combines simple camera operations of cv2 operations with an available resolutions
    list. 

    ...

        
    Attributes
    ----------
    cam_num : int
        index of the camera in the list of available cameras
        
    cap : cv2.VideoCapture
        VideoCapture object for camera operations and frame capture
    
    availableResolutions : list of QSize object
        List of available resolutions obtained from a QCamera
        Each QSize object represents a resolution with its widht and height
        attributes.
        
    isPaused : bool
        Flag to pause the frame capture


    Methods
    -------
    initialize(self)
        Initializes video capture.
        
    isReady(self)
        Returns whether the camera is ready to be used.
   
    captureFrame(self)
        Returns whether frame was succesfully captured.
        
    get_resolution(self)
        Returns index of the current camera resolution in the list of available camera resolutions.
        
    set_resolution(self,resIndex)
        Sets camera resolution .
    
    pause_cam(self)
        Pauses frame capture.
    resume_cam(self)
        Resumes frame capture.
    
    open_settings_dialog(self)
        Opens the default camera setttings dialog of DirectShow driver.
    
    set_available_resolutions(self,resList)
        Sets the list of available resolutions.
    
    get_available_resolutions(self)
        Gets the list of available resolutions.
    
    close(self)
        Stops frame capture and connection to the camera
    
    """    
    
    def __init__(self, cam_num):
        """
        Parameters
        ----------
        cam_num : int
            index of the camera in the list of available cameras

        """
        self.cam_num = cam_num
        self.cap = None
        self.availableResolutions = []
        self.isPaused = False
    
    def initialize(self):
        """
        Initializes video capture
        Returns
        -------
        bool
            whether video capture is working
        """

        print("initialize camera")
        self.cap = cv2.VideoCapture(self.cam_num+ cv2.CAP_DSHOW)
        return self.cap.isOpened()
    
    def isReady(self):
        """
        Returns
        -------
        bool
            whether the camera is ready to be used.

        """
        if self.cap is not None and  self.cap.isOpened() and not self.isPaused:
            return True
        return False
    
    def captureFrame(self):
        """
        Returns
        -------
        bool
            whether frame was succesfully captured
        np.ndarray
            frame captured by camera

        """
        if self.cap is not None and self.cap.isOpened() and not self.isPaused:
            return self.cap.read()
        else: return None,None

    #RESOLUTION
            
    def get_resolution(self):
        """
        Returns
        -------
        int
            index of the current camera resolution in the list of available camera resolutions
        """
        return self.cap.get(cv2.CAP_PROP_FRAME_WIDTH), self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT)
    def set_resolution(self,resIndex):
        """
        Parameters
        ----------
        resIndex : int
            index of the wanted camera resolution in the list of available camera resolutions
        Returns
        -------
        None.

        """
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.availableResolutions[resIndex].width())
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.availableResolutions[resIndex].height())
       
    """setters for camera pausing"""
    def pause_cam(self): self.isPaused = True
    def resume_cam(self): self.isPaused = False
 
    def open_settings_dialog(self):
        """
        Opens the default camera setttings dialog of DirectShow driver
        Returns
        -------
        None.
        
        """
        self.cap.set(cv2.CAP_PROP_SETTINGS, 0)
    
    def set_available_resolutions(self,resList):
        """
        Parameters
        ----------
        resList : list of QSize object
            List of available resolutions obtained from a QCamera
            Each QSize object represents a resolution with its widht and height
            attributes. 

        Returns
        -------
        None.

        """
        self.availableResolutions =resList
    def get_available_resolutions(self):
        """
        Returns
        -------
        list of string
            Returns the list of available resolutions formatted for display

        """
        return [ str(res.width())+'x'+str(res.height())  for res in self.availableResolutions]
    
    
    def __str__(self):
        return 'Camera'
    
    def close(self):
        """
        Stops frame capture and connection to the camera

        Returns
        -------
        None.

        """
        self.pause_cam()
        if self.cap.isOpened():
            self.cap.release()
        
class Worker(QtCore.QObject):

    """
    Contains camera and image processing function calls
    Computationally heavy operations are placed here ot be moved to antoher thread
    so that the GUI thread will function normally

    ...
    
    Signals
    ----------
    frameReady : QtCore.pyqtSignal(QtGui.QImage,float)
        Sends the frame to the GUI thread to be displayed
    
    updateList : QtCore.pyqtSignal(list)
        Sends the new decoded matrix codes to the GUI thread
    
    successUpdate : QtCore.pyqtSignal(bool)
        Notifies GUI thread about whether every box has a succesfully decoded matrix

    
    Attributes
    ----------
    
    processor : frameProcessor
        The processor object for image processing, box detection and matrix decoding
        
    camera : Camera 
        The camera object used to capture frames
        
    processing : bool
        Whether the frame will be processed to get boxes and matrix codes
        
    resetProcess : bool
        Whether the processor should be reset 
    
    img : QImage
        Processed frame to be sent to the GUI thread
        
    threadactive : bool
        Flag to tell the functions to stop before the thread is stopped
        
    ROI : tuple of 4
        ROI = ( x0,y0,x1,y1 ) represents the coordinates of the two opposite
        corners of the selected region of interest
        (0,0,0,0) by default, ROI not used unless a valid ROI is entered

    Methods
    -------
    setCamera(self,camera)
        Sets the camera 
    
    setCameraResolution(self,i)
        Works as a slot to set camera resolution to value sent from UI thread
    
    getNewFrame(self,processing,resetProcess,ROI)
        Obtains and processes a new frame
    
    processFrame(self,frame)
        Processes the frame to obtain boxes and datamtrix codes
        
    stop(self)
        Stops the functions of the Worker
    
    """    
    
    #SIGNALS
    frameReady = QtCore.pyqtSignal(QtGui.QImage,float)
    updateList = QtCore.pyqtSignal(list)
    successUpdate = QtCore.pyqtSignal(bool)
    
    
    
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
        """
        Sets the camera 

        Parameters
        ----------
        camera : Camera
            The camera object used to capture frames
            
        Returns
        -------
        None.

        """
        self.camera = camera
        
    @QtCore.pyqtSlot(int)    
    def setCameraResolution(self,i):
        """
        Works as a slot to set camera resolution to value sent from UI thread

        Parameters
        ----------
        i : int
            index of the resolution in the list of available resolutions

        Returns
        -------
        None.

        """
        self.camera.pause_cam()
        self.camera.set_resolution(i)
        self.camera.resume_cam()
        
        
    @QtCore.pyqtSlot(bool,bool,tuple)    
    def getNewFrame(self,processing,resetProcess,ROI):
        """
        Obtains and processes a new frame 

        Parameters
        ----------
        processing : bool
            whether the frame will be processed to get boxes and matrix codes
        resetProcess : bool
            whether the processor should be reset
        ROI : tuple
            ( x0,y0,x1,y1 ) represents the coordinates of the two opposite
            corners of the selected region of interest

        Returns
        -------
        None.

        """
        
        try:
            
            self.processing = processing
            self.resetProcess = resetProcess
            self.ROI = ROI
            scaling_factor = 1
            #if the thread will not be closed
            if self.threadactive:
              
                while  self.camera is not None:
                    
                    #making sure camera is working
                    if not self.camera.isReady():
                        continue
                    #capturing new frame
                    ret ,frame= self.camera.captureFrame()
                    if not ret:
                        continue
                    #resetting the processor to if needed
                    if self.resetProcess: 
                        self.processor.reset()
                        self.resetProcess = False
                    #processing the frame
                    if self.processing: 
                        frame = self.processFrame(frame)
                    #lowering the resolution of the frame if it is above 1920 pixels in width
                    if  frame.shape[1] > 1920 :
                        frame,scaling_factor = frameProcessor.downSize(frame)
                    
                    #color format conversion for GUI display
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    self.img = QtGui.QImage(frame, frame.shape[1], frame.shape[0], QtGui.QImage.Format_RGB888)
                    break
                #sending the resulting image and its scaling factor to GUI thread
                #sclaing factor is needed for calibrating the relative coordinates of mouse clicks on image
                self.frameReady.emit(self.img,scaling_factor)
                
        except Exception as e:
            print( e)
        
            
    def processFrame(self,frame):
        """
        Processes the frame to obtain boxes and datamtrix codes

        Parameters
        ----------
        frame : np.ndarray
            frame to be processed

        Returns
        -------
        frame : np.ndarray
            processed frame

        """
        #checking if the thread will not be closed and processor is available
        if self.threadactive and self.processor is not None:
            
            try:
                #processing
                frame, matrices = self.processor.process(frame,self.ROI)
                #sending the list of decoded datamatrix codes to the GUI thread
                self.updateList.emit(matrices)
            except:
                print("Processor Exception")  
                print(sys.exc_info()[0], "occurred.")
                self.processing = False
                return 
            #if all detected boxes resulted in succesfull matrix decoding, notifyin GUI thread
            if self.processor.isAllDetected():
                self.successUpdate.emit(True)
            else: 
                self.successUpdate.emit(False)
            return frame
    
    def stop(self):
        """
        Stops the functions of the Worker
        
        Returns
        -------
        None.

        """
        self.threadactive = False
        self.processor = None
        self.camera.close()    
        self.camera = None
 
        
class LabelwROI(QtWidgets.QLabel):
    
    
    """
    Modified QLabel that can draw and return a region of interest (ROI)
    
    ...

    Attributes
    ----------
    x0,y0,x1,y1 : int
        (x0,y0) : the coordinates of the starting point of ROI 
        (x1,y1) : the coordinates of the ending point of ROI 
    
    start : bool
        Flag to enable ROI creation
        
    drawROI : bool
        Flag that True while a ROI is being drawn

    Methods
    ----------
    toggleROI(self)
        Enables/Disables ROI creation
    getROI(self) 
        Returns ROI coordinates
        
    mousePressEvent(self,event)
        Modified to initiate ROI creation
        
    mouseReleaseEvent(self,event)
        Ends ROI creation
        
    mouseMoveEvent(self,event)
        Updates the end point of ROI
        
    paintEvent(self, event)
        Modified to add the ROI onto any drawn QImage
    """
        
        
    x0,y0,x1,y1 = 0,0,0,0
    start = False
    drawROI = False
    # 
    def toggleROI(self): 
        """
        Enables/Disables ROI creation
        """
        self.drawROI = not self.drawROI
        x0,y0,x1,y1 = 0,0,0,0
        self.start = False
        
    def getROI(self): 
        """
        Returns ROI coordinates

        Returns
        -------
        tuple of 4 ints
            (x0,x1,y0,y1) (x0,y0) : the coordinates of the starting point of ROI 
                          (x1,y1) : the coordinates of the ending point of ROI 
        """
        if self.drawROI and not self.start:
            
            if self.pixmap():
                #to make sure the upper left and lower right corners are returned, min and max are used
                #this way, if the ROI is drawn in different directions, the same ROI can be obtained
                return (min(self.x0,self.x1),min(self.y0,self.y1),max(self.x0,self.x1),max(self.y0,self.y1))
        else: return (0,0,0,0)
    
    def mousePressEvent(self,event):
        """
        Modified to initiate ROI creation
        """

        if self.drawROI:
            self.start = True
            self.x0 = event.x()
            self.y0 = event.y()
         
    def mouseReleaseEvent(self,event):
        """ 
        Ends ROI creation
        """
        self.start = False
 
    def mouseMoveEvent(self,event):
        """ 
        Updates the end point of ROI
        """
        
        if self.drawROI and self.start:
            self.x1 = event.x()
            self.y1 = event.y()
            self.update()

    def paintEvent(self, event):
        """
        Modified to add the ROI onto any drawn QImage
        """
        super().paintEvent(event)
        if self.drawROI:
            rect =QRect(min(self.x0,self.x1), min(self.y0,self.y1), abs(self.x1-self.x0), abs(self.y1-self.y0))
            painter = QPainter(self)
            painter.setPen(QPen(Qt.red,2,Qt.SolidLine))
            painter.drawRect(rect)
            
            
        
class showLogin(QtWidgets.QDialog):
    """
    QDialog that asks for and returns database user credentials
    
    ...
    
    Signals
    ----------
    loginSignal : QtCore.pyqtSignal(str,str,str)
        Sends the user credentials to the GUI thread to be passed to the database object

    Methods
    ----------
    accept_and_send(self)
        Emits the login signal if OK button is pressed
    """
    
    loginSignal = QtCore.pyqtSignal(str,str,str)
    def __init__(self, parent):
        QtWidgets.QDialog.__init__(self, parent)
        #delete question mark
        self.setWindowFlags(self.windowFlags()
                            ^ QtCore.Qt.WindowContextHelpButtonHint)
        #Login ,password and database name fields
        self.username = QtWidgets.QLineEdit(self)
        self.password = QtWidgets.QLineEdit(self)
        self.password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.database_name = QtWidgets.QLineEdit(self)
        
        #Setting up the layout 
        loginLayout = QtWidgets.QFormLayout()
        loginLayout.addRow("Username", self.username)
        loginLayout.addRow("Password", self.password)
        loginLayout.addRow("Database", self.database_name)
        self.buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        
        #If OK button is pressed, the custom accept_and_send function will send user credentials to database
        self.buttons.accepted.connect(self.accept_and_send)
        self.buttons.rejected.connect(self.reject)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addLayout(loginLayout)
        self.layout.addWidget( self.buttons)
        self.setLayout(self.layout)

        ### set window title
        self.setWindowTitle('Database Login')
        ###lock resize
        self.setSizeGripEnabled(False)
        self.setFixedSize( self.sizeHint())
    
    def accept_and_send(self):
        self.loginSignal.emit(self.password.text(),self.username.text(),self.database_name.text())
        self.accept()