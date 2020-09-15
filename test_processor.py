
from frameProcessor import frameProcessor
import ssl
import urllib.request
import cv2

#CAMERA LOOP
cap = cv2.VideoCapture(0,cv2.CAP_DSHOW)

#cap.set(cv2.CAP_PROP_SETTINGS,0.0)
cap.set(4, 2880)

cap.set(3, 2160)
cap.set(27, 133)
cap.set(22, 100)
cap.set(20, 30)
cap.set(33, 79)
cap.set(34, 0)


#out = cv2.VideoWriter('results.avi',cv2.VideoWriter_fourcc(*'MJPG'), 5, (int(cap.get(3)),int(cap.get(4))))

#-------------------------------------------

processor = frameProcessor()
decoded = []
while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
   
    if not ret:
        continue  
    
    newFrame,decoded = processor.process(frame)
    
    
    cv2.namedWindow("window", cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty("window",cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)
    cv2.imshow("window", newFrame)
    
    if cv2.waitKey(1) & 0xFF == ord('r'):
        print("r pressed")
        processor.reset()
    elif cv2.waitKey(1) & 0xFF == ord('q'):
        print("q pressed")
        break


# When everything done, release the capture


cap.release()
cv2.destroyAllWindows()
#out.release()