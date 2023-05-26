"""
hadles turning motors using Odrive/Stepper driver 
"""

import board
import busio
#import adafruit_pca9685 as pcaLibf
try:
    import constants as c
    import stepper
    from Odrive import Odrive
    from windvane import windVane
except:
    import sailbot.constants as c
    import sailbot.stepper as stepper
    from sailbot.Odrive import Odrive
    from sailbot.windvane import windVane

from threading import Thread
from RPi import GPIOs
from time import sleep


# define type of motor that is being used
USE_ODRIVE_SAIL = True
USE_STEPPER_SAIL = False

USE_ODRIVE_RUDDER = True
USE_STEPPER_RUDDER = False
        
if False: # The two wiring configurations, both defined here for easy switching
    SAIL_DIR_PIN = 17 
    SAIL_PUL_PIN = 4 
    RUDDER_DIR_PIN = 22 
    RUDDER_PUL_PIN = 27 
else:
    SAIL_DIR_PIN = 22
    SAIL_PUL_PIN = 27
    RUDDER_DIR_PIN = 17
    RUDDER_PUL_PIN = 4

class obj_sail:
            
    def __init__(self, auto = False):
        self.autoAdjust = auto
        self.current = 0
        if USE_STEPPER_SAIL:
            self.step = stepper.stepperDriver(SAIL_DIR_PIN, SAIL_PUL_PIN)
        if USE_ODRIVE_SAIL:
            self.odriveAxis = DRV.axis1

    def map(self, x, min1, max1, min2, max2):
        # converts value x, which ranges from min1-max1, to a corresponding value ranging from min2-max2
        # ex: map(0.3, 0, 1, 0, 100) returns 30
        # ex: map(70, 0, 100, 0, 1) returns .7
        x = min(max(x, min1), max1)
        return min2 + (max2-min2)*((x-min1)/(max1-min1))

    def set(self, degrees):
        print(F"setting sail: {degrees}")
        degrees = float(degrees)

        if USE_STEPPER_SAIL:
            self.steps = int(400/360 * (self.current-degrees) ) * 15
            
            if degrees < self.current:
                self.step.turn(False, self.steps)
            else:
                self.step.turn(True, -self.steps)

        if USE_ODRIVE_SAIL:
            val = self.map(degrees, 0, 90, 0, float(c.config['ODRIVE']['odriveSailRotations']))
            DRV.posSet(self.odriveAxis, val)
        self.current = degrees
    
    def autoAdjustSail(self):
        while True:
            if self.autoAdjust == True:
                windDir = self.windvane.angle
                if windDir > 180:
                    windDir = 180 - (windDir - 180)
                targetAngle = max(min(windDir / 2, 90), 3)
                self.set(targetAngle)

                
class obj_rudder:
    # 800 steps = 360 degrees
    #between -45 and 45 degrees
    def __init__(self):
        self.current = 0
        if USE_STEPPER_RUDDER:
            self.step = stepper.stepperDriver(RUDDER_DIR_PIN, RUDDER_PUL_PIN)
        if USE_ODRIVE_RUDDER:
            self.odriveAxis = DRV.axis0

    def map(self, x, min1, max1, min2, max2, enforce_limits = True):
        # converts value x, which ranges from min1-max1, to a corresponding value ranging from min2-max2
        # ex: map(0.3, 0, 1, 0, 100) returns 30
        # ex: map(70, 0, 100, 0, 1) returns .7
        if enforce_limits:
            x = min(max(x, min1), max1)
        return min2 + (max2-min2)*((x-min1)/(max1-min1))
    
    def set(self, degrees):
        print(F"setting rudder: {degrees}")
        degrees = float(degrees)
        
        if USE_STEPPER_RUDDER:
            maxAngle = 30
            if degrees > maxAngle:
                degrees = maxAngle
            elif degrees < -maxAngle:
                degrees = -maxAngle
            self.steps = int(400/360 * (self.current-degrees) ) * 50
            
            if degrees < self.current:
                self.step.turn(True, self.steps)
            else:
                self.step.turn(False, -self.steps)

        if USE_ODRIVE_RUDDER:
            val = self.map(degrees, float(c.config['CONSTANTS']['rudder_angle_min']), float(c.config['CONSTANTS']['rudder_angle_max']), -float(c.config['ODRIVE']['odriveRudderRotations'])/2, float(c.config['ODRIVE']['odriveRudderRotations'])/2)
            DRV.posSet(self.odriveAxis, val)
            #print(F"set rudder to {val} {degrees}")

        self.current = degrees

class driver():

    def __init__(self, calibrateOdrive = True):
        super().__init__('driver')
        global DRV
        if USE_ODRIVE_SAIL or USE_ODRIVE_RUDDER:
            DRV = Odrive(calibrate=calibrateOdrive)
            pass
        self.sail = obj_sail()
        self.rudder = obj_rudder()

if __name__ == "__main__":
    #manually control motors with commands 'sail {value}' and 'rudder {value}'
    drive = driver()

    while True:
        string = input("  > Enter Input:")
        
        if string == "quit":
            break
        
        arr = string.split(" ")
        
        if arr[0] == "sail":
            val = int(arr[1])
            drive.sail.set(val)
            
            
        elif arr[0] == "rudder" or arr[0] == 'r':
              drive.rudder.set(int(arr[1]))
              
        elif arr[0] == "stepper" or arr[0] == 's':
            stepper = stepperMotor()
            stepper.step(int(arr[1]))
