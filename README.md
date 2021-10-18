# Multi Matrix Reader
 
This repository contains a python based desktop application that aims to streamline stock-taking and transactions at facilities processing large quantities of drug boxes or other small sized boxes identifiable with data matrices.  

The application requires live camera footage from a USB 3.0 camera. Drug boxes are placed on a platform with a preferably dark surface as detection is significantly more robust with black or dark background textures. The camera is placed approximately one meter above the platform, although camera properties are adjustable to work better with other distances from the platform. Using the camera footage, the desktop application detects multiple drug boxes placed on the platform at a time and decodes their data matrices. 

### Setup Used in Tests:

<div>
  <img align="left" src="/readme_images/platform_view1.jpeg" height="300"/>
  <img align="left" src="/readme_images/platform_view2.jpeg" height="300"/> 

 The application requires live camera footage from a USB 3.0 camera. Drug boxes are placed on a platform with a preferably dark surface as detection is significantly more robust with black or dark background textures. The camera is placed approximately one meter above the platform, although camera properties are adjustable to work better with other distances from the platform. Using the camera footage, the desktop application detects multiple drug boxes placed on the platform at a time and decodes their data matrices.

</div>
<br></br>
<br></br>
<br></br>

## Components of the Application

### 1 - Image Analysis and Pattern Recognition
The core of this project was the choice and optimization of the image processing, pattern extraction methods used as well as the rule based classification of extracted features. The methods had to work fast enough to enable each frame coming from the camera to be processed in real time. In other words, the video feed shown in the completed application needed to have sufficiently high fps to appear smooth to the client. Since considerably large (2880×2160) frames had to be processed for the successful decoding of a dozen data matrices from a distance of one meter and due to the decoding library function working slowly, running time was a major restriction in method choice.

The drug boxes needed to be separated from the background and the contours of the boxes needed to be extracted in a robust way. Then, geometric manipulation of the contours provided simple features that were enough to classify them as real drug boxes or not.

#### 1.1 - Pre-processing and Segmentation
    
A series of image processing operations were carried out to make contour detection and data matrix decoding operations work more consistently and fast.
* Thresholding 
* edge detection 
* morphological operations 

were used to prepare the image. The image was processed separately for:
1. drug box detection
2. data matrix detection 
3. data matrix decoding 

The settings or kernels of the operations were changed for each one of these tasks. Various settings and alternative algorithms that are recommended for each step were compared until the best performing ones were determined for final implementation.

##### a.Gaussian Blurring
Gaussian filtering is a commonly used way of reducing noise prior to edge detection. It results in the detected edges being more smooth. This operation was only applied for drug box detection, as its blurring effect would undermine the data matrix decoding process which requires as high resolution an image as possible.

##### b.Thresholding
Two different types of binary thresholding are applied. For drug box detection, since the image is bimodal with bright boxes and a dark background, Otsu’s Binarization is used to extract the boxes. For data matrix detection and decoding, adaptive thresholding with the mean value of a pixel neighbourhood used as the local threshold was used. Data matrix related operations are applied only within the borders of the already detected drug box contours, thus local thresholding is effective in extracting the print on box covers while global thresholding would not have been as sensitive to the local brightness differences, as can be seen from the Otsu binarized image.
<div>

  <img src="/readme_images/platform_view2.jpeg" height="300"/> 
</div>




### Camera Used in Tests:

  <img align="left" src="https://www.e-consystems.com/images/See3CAM/See3CAM_CU135/4K-USB-camera-board_zoom.jpg" width="200"/>

  <em > See3CAM_CU135 – 4K Custom Lens USB 3.0 Camera Board</em>
  
The only hardware required for the project other than a computer was a sufficiently high resolution camera.Two USB 3.0 cameras by e-con Systems were used during development, one with a maximum resolution of 1080p and another with 4K. Given that the software would be used to detect at least 10 drug boxes at the same time and read their data matrix codes effectively, after experimenting with different setups to mimic real-life use, the 1080p camera was deemed insufficient for the use case. The 4K camera was used at 2.8K resolution with success and any higher resolution did not improve results considerably and slowed down processing. Unless the software is to be supported by more powerful hardware, 2.8K would be the optimal use setting.
   







