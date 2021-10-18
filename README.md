# Multi Matrix Reader
 
This repository contains a python based desktop application that aims to streamline stock-taking and transactions at facilities processing large quantities of drug boxes or other small sized boxes identifiable with data matrices.  

The application requires live camera footage from a USB 3.0 camera. Drug boxes are placed on a platform with a preferably dark surface as detection is significantly more robust with black or dark background textures. The camera is placed approximately one meter above the platform, although camera properties are adjustable to work better with other distances from the platform. Using the camera footage, the desktop application detects multiple drug boxes placed on the platform at a time and decodes their data matrices. 

## Setup Used in Tests:

<p float="left">
  <img src="/readme_images/platform_view1.jpg" width="200"/>
  <img src="/readme_images/platform_view2.jpg" width="200"/> 
</p>

## Camera Used in Tests:

<p float="left">
  <img src="/readme_images/platform_view1.jpg" width="200"/>
 
  <p align="left">
The only hardware required for the project other than a computer was a sufficiently high resolution camera.Two USB 3.0 cameras by e-con Systems were used during development, one with a maximum resolution of 1080p and another with 4K. Given that the software would be used to detect at least 10 drug boxes at the same time and read their data matrix codes effectively, after experimenting with different setups to mimic real-life use, the 1080p camera was deemed insufficient for the use case. The 4K camera was used at 2.8K resolution with success and any higher resolution did not improve results considerably and slowed down processing. Unless the software is to be supported by more powerful hardware, 2.8K would be the optimal use setting.
   </p>
   
</p>






