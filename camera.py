"""
Interface for camera
"""
import cv2
from time import time
import logging
import math
import keyboard
import numpy as np
import picamera
import io

import constants as c
try:
    from GPS import gps
    from compass import compass
except ImportError as e:
    print("Failed to import some modules, if this is not a simulation fix this before continuing")
    print(f"Exception raised: {e}")
    
try:
    from cameraServos import CameraServos
except ImportError as e:
    print("Failed to import some modules, if this is not a simulation fix this before continuing")
    print(f"Exception raised: {e}")
    
from objectDetection import ObjectDetection
    
class Frame():
    """
    Image with context metadata
    
    Attributes:
        - img (np.ndarray): the RGB image taken
        - time: the UTC time at which the image was captured
        - gps: the position of the boat at time of capture
        - pitch: the camera's pitch angle at time of capture
        - yaw: the camera's yaw angle at time of capture
        - detections: a list of buoy Detections
            - initially empty! must call objectDetection.analyze(Frame.img) to populate
    """
    def __init__(self, img=None, time=None, gps=None, pitch=None, yaw=None, detections=[]):
        self.img = img
        self.time = time
        self.gps = gps
        self.pitch = pitch
        self.yaw = yaw
        self.detections = detections
            
        
class Camera():
    """
    Drivers and interface for camera
    
    Attributes:
        - servos (CameraServo): interface to control camera servos
            - servos.pitch and servos.yaw will always have the immediate camera position
            - pitch and yaw can be modified to move the physical servos 
    
    Functions:
        - capture(): Takes a picture
        - survey(): Takes a panorama
    """
    def __init__(self):
        
        int(c.config["CAMERA"]["source"])
        self._cap = cv2.VideoCapture("device=/dev/video0")
        self.servos = CameraServos()
    
    def __del__(self):
        self._cap.release()
        
    def capture(self, context=True, show=False, detect=False) -> Frame:
        """Takes a single picture from camera
        Args:
            - context (bool): whether to include time, gps, and camera angle in return Frame
            - show (bool): whether to show the image that is captured
            - detect (bool): whether to detect buoys within the image
        Returns:
            - The captured image stored as a Frame object
        """
        
        ## TEST THIS V
        stream = io.BytesIO()

        #Get the picture (low resolution, so it should be quite fast)
        #Here you can also specify other parameters (e.g.:rotate the image)
        with picamera.PiCamera() as camera:
            camera.resolution = (320, 240)
            camera.capture(stream, format='jpeg')

        #Convert the picture into a numpy array
        buff = np.fromstring(stream.getvalue(), dtype=np.uint8)

        #Now creates an OpenCV image
        image = cv2.imdecode(buff, 1)
        
        ## TEST THIS ^
        img, time, gps, pitch, yaw = None, None, None, None, None
        
        ret, img = self._cap.read()
        if not ret:
            raise RuntimeError("No camera feed detected")
        
        if show:
            cv2.imshow(img)
            
        if context:
            time, gps, pitch, yaw = self.__get_context()
            
        if detect:
            object_detection = ObjectDetection()
            detections = object_detection.analyze(img)
        
        return Frame(img=img, time=time, gps=gps, pitch=pitch, yaw=yaw, detections=detections)            
        
    def survey(self, num_images=3, pitch=70, servo_range=180, context=True, show=False) -> list[Frame]:
        """Takes a horizontal panaroma over the camera's field of view
            - Maximum boat FoV is ~242.2 degrees (not tested)
        # Args:
            - num_images (int): how many images to take across FoV
                - Picamera2 lens covers an FoV of 62.2 degrees horizontal and 48.8 vertical
                
            - pitch (int): fixed camera pitch angle
                - must be between 0 and 180 degrees: 0 points straight down, 180 points straight up
                
            - servo_range (int): the allowed range of motion for camera servos, always centered
                - must be between 0 and 180 degrees: 0 means servo is fixed to center, 180 is full servo range of motion
                - ex. a range of 90 degrees limits servo movement to between 45-135 degrees for a total boat FoV of 152.2 degrees
                
            - context (bool): whether to include time, gps and camera angle of captured images
            
            - show (bool): whether to show each image as captured
            
        # Returns:
            - A list of the captured images stored as Frame objects
        """
        
        images: list[Frame] = []
        servo_step = servo_range / num_images
        MIN_ANGLE = int(c.config(["CAMERASERVOS"]["min_angle"]))
        MAX_ANGLE = int(c.config(["CAMERASERVOS"]["max_angle"]))
        
        # Move camera to desired pitch
        self.servos.pitch = pitch
        
        if self.servos.yaw <= 90: 
            # Survey left -> right when camera is facing left or center
            for self.servos.yaw in range(MIN_ANGLE, MAX_ANGLE, servo_step):
                images.append(self.capture(context=context, show=show))
        else:
            # Survey right -> left when camera is facing right
            for self.servos.yaw in range(MAX_ANGLE, MIN_ANGLE, servo_step):
                images.append(self.capture(context=context, show=show))
        
        return images

    # TODO:
    def track(self):
        """Centers camera on a detected buoy and attempts to keep it in frame"""
        img = self.capture(context=True, )
    
    def __get_context(self):
        """Helper method to get and format metadata for images"""
        time = time()
        gps.updategps() # TODO: replace with ROS subscriber
        gps = (gps.longitude, gps.latitude)
        pitch = self.servos.pitch
        yaw = self.servos.yaw
        
        return time, gps, pitch, yaw
    
class CameraTester(Camera):
    def __init__(self):
        super().__init__()
        
    def freemove(self):
        while True:
            print(f"Pitch: {self.servos.pitch} Yaw: {self.servos.yaw}\n")
            if keyboard.is_pressed("enter"):
                self.capture(context=False, show=True)
            elif keyboard.is_pressed("space"):
                self.servos.reset()
            elif keyboard.is_pressed("up arrow"):
                self.servos.pitch = self.servos.pitch + 1
            elif keyboard.is_pressed("down arrow"):
                self.servos.pitch = self.servos.pitch - 1
            elif keyboard.is_pressed("left arrow"):
                self.servos.yaw = self.servos.yaw - 1
            elif keyboard.is_pressed("right arrow"):
                self.servos.yaw = self.servos.yaw + 1


if __name__ == "__main__":
    cam = CameraTester()
    while True:
        print('''
=============================
Accepted Command info:
[0] freemove(): free control movement wise with continuous capture feed for demonstration purposes
[1] survey(): go far left,right,center looking for buoy whole time detect() - 3 set points in x axis
[2] track(): follow object
-----------------------------''')
        inp = input("Command Test: ")
        
        if inp == "0":
            cam.freemove()
        if inp == "1":
            cam.survey()
        else:
            print("nah...")
            raise Exception("invalid command selection")
