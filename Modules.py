import cv2
class Camera:
    
    def __init__(self, cam_num):
        self.cam_num = cam_num
        self.cap = None
    
    def initialize(self):
        self.cap = cv2.VideoCapture(self.cam_num)
        return self.cap.isOpened()

    def get_frame(self):
        ret, self.last_frame = self.cap.read()
        return self.last_frame
   
    def close_camera(self):
        self.cap.release()
        
    
    #CAMERA PROPERTIES GETTER-SETTERS
    
    #BRIGHTNESS
        
    def set_brightness(self, value):
        self.cap.set(cv2.CAP_PROP_BRIGHTNESS, value)
        
    def get_brightness(self):
        return self.cap.get(cv2.CAP_PROP_BRIGHTNESS)

    #RESOLUTION
    
    def set_resolution(self,width,height):
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        
        if self.cap.get(cv2.CAP_PROP_FRAME_WIDTH) != width \
        and self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT) != height :
            return False
        else: return True
        
    def get_resolution(self):
        return self.cap.get(cv2.CAP_PROP_FRAME_WIDTH), self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT)
    
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
    
    
    
    def __str__(self):
        return 'Camera'