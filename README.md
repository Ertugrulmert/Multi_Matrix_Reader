# Multi Matrix Reader

_Author: Mert Ertuğrul_


_Application developed in 2020 during internship at Karel Electronics_
 
This repository contains a python based desktop application that aims to streamline stock-taking and transactions at facilities processing large quantities of drug boxes or other small sized boxes identifiable with data matrices.  

The application requires live camera footage from a USB 3.0 camera. Drug boxes are placed on a platform with a preferably dark surface as detection is significantly more robust with black or dark background textures. The camera is placed approximately one meter above the platform, although camera properties are adjustable to work better with other distances from the platform. Using the camera footage, the desktop application detects multiple drug boxes placed on the platform at a time and decodes their data matrices. 

## Table of Contents


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

### 1.1 - Pre-processing and Segmentation
    
A series of image processing operations were carried out to make contour detection and data matrix decoding operations work more consistently and fast.
* Thresholding 
* edge detection 
* morphological operations 

were used to prepare the image. The image was processed separately for:
1. drug box detection
2. data matrix detection 
3. data matrix decoding 

The settings or kernels of the operations were changed for each one of these tasks. Various settings and alternative algorithms that are recommended for each step were compared until the best performing ones were determined for final implementation.

#### 1.1.a - Gaussian Blurring

Gaussian filtering is a commonly used way of reducing noise prior to edge detection. It results in the detected edges being more smooth. This operation was only applied for **drug box detection**, as its blurring effect would undermine the data matrix decoding process which requires as high resolution an image as possible.

#### 1.1.b - Thresholding

Two different types of binary thresholding are applied. For **drug box detection**, since the image is bimodal with bright boxes and a dark background, **Otsu’s Binarization** is used to extract the boxes. For **data matrix detection** and **decoding**, **adaptive thresholding** was used with the mean value of a pixel neighbourhood used as the local threshold. Data matrix related operations are applied only within the borders of the already detected drug box contours, thus local thresholding is effective in extracting the print on box covers while global thresholding would not have been as sensitive to the local brightness differences, as can be seen from the Otsu binarized image.
<div>
  <img src="/readme_images/otsu_binarization.png" height="300"/> 
 <img src="/readme_images/adaptive_thresholding.png" height="300"/> 
</div>

  **Left Image:** Box detection image after Otsu’s Binarization, 
  
  **Right Image:** Data matrix image after adaptive thresholding

#### 1.1.c - Edge Detection

Edges are detected on the previously Otsu binarized image using **Canny edge detection**. While this algorithm could have been applied directly to the original image, the results obtained after Otsu binarization were more robust and more likely to give way to closed contours later on in contour detection. When shadows are present for example, first using Otsu binarization helps mitigate wrong edge detections.

Canny edge detection is a commonly used multi-step edge detector composed of Gaussian blurring, obtaining pixel intensity gradient of the image, suppressing all pixels with non-maximum intensity gradient value to obtain thin edges and hysteresis thresholding. The thin (one pixel thick) edges then become candidates for contour detection. The upper and lower bounds for the hysteresis thresholding portion of the algorithm were selected based on the median pixel intensity of the image.

<img src="/readme_images/canny_edge.png" height="300"/> 

**Image:** Box detection image after Canny edge detection

#### 1.1.d - Morphological Operations

In case Canny edge detection results in disconnected line segments instead of closed loops, **morphological closing** is applied to the detected edges to fill the gaps. During my initial tests, contour detection after morphological closing outperformed contour detection on edges directly.

For **data matrix detection**, **morphological opening** is applied to the adaptive thresholded image. Since data matrices are composed of a grid of white and black cells, the opening operation can manage to merge these cells into a black outline of the square data matrix. This prepares the surfaces of the drug boxes for detection of the data matrix contour.

<div>
  <img src="/readme_images/box_detect_morph_opening.png" height="300"/> 
 <img src="/readme_images/matrix_detect_morph_closing.png" height="300"/> 
</div>

  **Left Image:** Box detection image after morphological opening, 
  
  **Right Image:** Matrix detection image after morphological closing
  

#### 1.1.e - Contour Detection

I opted for OpenCV’s contour detection function. This function implements an algorithm Suzuki & Be introduced in their paper “Topological Structural Analysis of Digitized Binary Images by Border Following.” In this application the function is set to approximate the contours, meaning that it forms simpler contours represented by a shorter list of points. Since the intrinsic shapes we are trying to extract are rectangles, this improves the contours. The obtained contours are kept in a temporary list to be classified.

OpenCV recommends binarizing the image prior to contour detection for better results, which is partly why the previous steps were followed. Another reason is that the previous steps reduce variance in non-edge areas substantially and without them, hundreds more of false contours would be detected that have to be processed later to be classified as false.

<img src="/readme_images/contour_overlay.png" height="300"/> 

**Image:** Original image with detected contours overlayed

### 1.2 - Feature Extraction and Classification

After the contours are obtained, an algorithm is needed to determine whether each contour really represents an underlying drug box. Since boxes are rectangular, the features needed to classify contours are very simple and the classification is simply a set of rules concerning the shape of the contours and their interactions with other contours.
There is a permanent and a temporary list of contours stored by the detector, the contours in the temporary list that satisfy the necessary criteria are added to the permanent list, accumulating over consecutive frames. The permanent list stores boxes detected in the previous frames that had successfully decoded data matrices, if a matrix has already been decoded, the box containing it will not need to be processed again. This speeds up the program considerably since the decoding function is slow and should not be called unless absolutely necessary.

<img align="left" src="/readme_images/boxes_overlay.png" height="300" padding-right:10px/> 

The following procedure is applied to determine which contours represent real drug boxes:

**1.** The **convex hull** of the contours is found.
**2.** The area of the convex hull is used as a feature. – A **minimum area threshold** is applied to eliminate any contours formed purely by noise.
**3.** The **minimum enclosing rectangle** around the convex hull is found.
**4.** The **aspect ratio** of the rectangle is used as a feature. – The aspect ratio is thresholded to determine if it is within the limits of a realistic drug box.

To eliminate misdetections within and near boxes, geometric interactions between boxes need to be inspected. In many cases, a coloured line on a box or a side surface of a box would be detected as a separate box and they would still meet the criteria above, requiring additional measures.The additional measures based on interactions of boxes are as follows:

1. The box is discarded if another box with similar properties and location already exists in the permanent list.
2. The interactions of the new boxes are checked:
    * Duplicates and boxes touching the edges of the frame are removed.
    * Boxes inside other boxes are determined and only the outer boxes are kept.
    * Boxes that are crossing, touching or in close proximity are determined and only the box with larger area is kept.

After this procedure, the remaining boxes are considered to represent real drug boxes. Given these boxes, data matrix candidates contained within them need to be determined. 

For this purpose, another version of the image that was pre-processed specifically for data matrix box detection is used. The process followed for finding the boxes of data matrices is similar to the steps above. The **aspect ratio threshold** is selected as much **stricter**, only taking values close to one since data matrix outlines must be square shaped. Also, an **irregularity threshold** is added to account for detections of granular artifacts remaining after adaptive thresholding. The word irregularity is used to refer to **how different the original contour is from the minimum enclosing rectangle of its convex hull**. The **ratio between the difference of their areas and the area of the rectangle** is used to quantify this feature.

### 1.3 - Data Matrix Decoding

After a viable data matrix candidate is determined in a drug box cover image, the matrix region is put through a **rotation transformation** to increase decoding accuracy. Then the decoding function of the **pylibdmtx** library attempts to decode the matrix. If decoding is successful, the outer and matrix boxes as well as the decoded code are stored in permanent lists.

Initially, the running time of the algorithm far exceeded the requirement to create a smooth real-time video feed on the GUI. The primary cause was pylibdmtx working extremely slowly. At that stage, alternative libraries and ways of manually implementing a decoding algorithm were searched. As the pre-processing and classification steps reached their final form, the number of potential matrix candidates that had to be given to pylibdmtx dropped. In addition, the accumulation of previously successfully detected and decoded box and matrices led to new candidate numbers dropping exponentially with each frame after the first frame. As a result, the library could be kept with satisfactory results.

<img src="/readme_images/final_Result.png" height="300"/> 

**Image:** Results with the final algorithm

### 2 - Graphical User Interface Design

All the required functionalities of the application were connected to a graphical user interface designed with **PyQt5** and **Qt Designer**.

* **Menu bar** options for **selecting a camera, setting desired camera resolution and opening a camera settings dialog** were added.
* Once database implementation was complete, various **database functionalities** were also added to be accessible from the menu bar.
* **Start/Stop** button was added to control whether frames should be processed or directly displayed instead. When processing is stopped, the list of codes obtained in the last session of processing are added to the permanent list of codes.
* **Reset Detection** button was necessary to reset the previously detected boxes attribute of the decoder. When the camera is moved or an adjustment is made to the scene it is recording, previously detected boxes will stay in their old places and block new detections so the processor must be refreshed. This only **deletes the decoded codes from the last session** and **not the permanent list**.
* **ROI (Region of Interest) selection** functionality was integrated into both the GUI and the processor code at a later stage. It is used if the user wants to specify that only a certain section of the frame should be processed. After the **“ROI Selection”** button is pressed, the user can draw a rectangular ROI on the displayed image.
* A **list box** displays the data matrix codes identified since the program was started
* The **live camera feed** (processed feed if processing has started) is displayed, successfully detected drug boxes and their data matrix boxes are **highlighted in green**. Boxes with no data matrix boxes identified or with data matrix boxes that could not be decoded are **highlighted in red**.


All computationally heavy operations or operations that needed to run asynchronously from the main thread including capturing new frames from the camera and processing of the frames were moved to a separate thread. These processes communicated with the GUI through signals and slots.

<img src="/readme_images/GUI_before_database.png" height="300"/> 

**Image:** GUI screenshot showing algorithm in work (before database functionality added)

<img src="/readme_images/GUI_with_ROI.png" height="300"/> 

**Image:** GUI screenshot showing ROI selection

<img src="/readme_images/GUI_with_DB.png" height="300"/> 

**Image:** GUI screenshot showing database table access


### 3 - Database Implementation
The database for data matrix codes was implemented in **PostgreSQL**. The data matrix codes collected on a given day are stored in a table for that day. Table titles followed a convention based on the date of table creation, reflecting the stock taking operations of a given day. Functions for adding new codes, deleting tables and reading table data were implemented and connected to the GUI.

### 4 -  Camera Used in Tests:

  <img align="left" src="https://www.e-consystems.com/images/See3CAM/See3CAM_CU135/4K-USB-camera-board_zoom.jpg" width="200"/>

  <em > See3CAM_CU135 – 4K Custom Lens USB 3.0 Camera Board</em>
  
The only hardware required for the project other than a computer was a sufficiently high resolution camera.Two USB 3.0 cameras by e-con Systems were used during development, one with a maximum resolution of 1080p and another with 4K. Given that the software would be used to detect at least 10 drug boxes at the same time and read their data matrix codes effectively, after experimenting with different setups to mimic real-life use, the 1080p camera was deemed insufficient for the use case. The 4K camera was used at 2.8K resolution with success and any higher resolution did not improve results considerably and slowed down processing. Unless the software is to be supported by more powerful hardware, 2.8K would be the optimal use setting.

### 5 - Requirements:
* numpy
* cv2
* matplotlib
* pylibdmtx
* shapely
* PyQt5
   







