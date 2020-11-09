import board
import busio
import adafruit_pca9685 as pcaLib
import constants as c
from threading import Thread
from windvane import windVane
            
class obj_sail:
            
    servo_min = c.SAIL_SERVO_MIN
    servo_max = c.SAIL_SERVO_MAX
            
    angle_min = c.SAIL_ANGLE_MIN
    angle_max = c.SAIL_ANGLE_MAX

    sailPosition = 0 #Keeps track of current sail position
    
            
    def __init__(self, pca, channel_index, auto):
        self.channel =  pca.channels[channel_index]
        self.autoAdjust = auto
        self.windvane = windVane()
        pump_thread2 = Thread(target=self.autoAdjustSail)
        pump_thread2.start()

    def map(self, x, min1, max1, min2, max2):
        x = min(max(x, min1), max1)
        return min2 + (max2-min2)*((x-min1)/(max1-min1))

    def set(self, degrees):
            
        val = self.map(degrees, self.angle_min, self.angle_max,
                  self.servo_min, self.servo_max)

        self.channel.duty_cycle = int(val)
        sailPosition = degrees
        return
    
    def autoAdjustSail(self):
        while True:
            if self.autoAdjust == True:
                windDir = self.windvane.angle
                if windDir > 180:
                    windDir = 180 - (windDir - 180)
                targetAngle = max(min(windDir / 2, 90), 3)
                self.set(targetAngle)

    def get(self):
        return sailPosition


                
class obj_rudder:
            
    servo_min = c.RUDDER_SERVO_MIN
    servo_ctr = c.RUDDER_SERVO_CTR
    servo_max = c.RUDDER_SERVO_MAX
            
    angle_min = c.RUDDER_ANGLE_MIN
    angle_max = c.RUDDER_ANGLE_MAX
    angle_ctr = angle_min + (angle_max - angle_min) / 2

    rudderPosition = 0 #Will keep the current position of rudder
            
    def __init__(self, pca, channel_index):
        self.channel =  pca.channels[channel_index]

    def map(self, x, min1, max1, min2, max2):
        x = min(max(x, min1), max1)
        return min2 + (max2-min2)*((x-min1)/(max1-min1))

    def set(self, degrees):
        if degrees < self.angle_ctr:
            
            val = self.map(degrees, self.angle_min, self.angle_ctr,
                  self.servo_min, self.servo_ctr)
        else:
            val = self.map(degrees, self.angle_ctr, self.angle_max,
                  self.servo_ctr, self.servo_max)


        self.channel.duty_cycle = int(val)
        rudderPosition = degrees
        return

    def get(self):
        return rudderPosition

class driver:

    def __init__(self, sail_channel = 0, rudder_channel = 1, sailAuto = True):
        
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.pca = pcaLib.PCA9685(self.i2c)
        self.pca.frequency = 50

        self.sail = obj_sail(self.pca, sail_channel, sailAuto)
        self.rudder = obj_rudder(self.pca, rudder_channel)
        print('n', sailAuto)

if __name__ == "__main__":
    drive = driver(0, 1)
    drive.sail.autoAdjust = False

    
    while True:
        string = input("  > Enter Input:")
        
        if string == "quit":
            break
        
        arr = string.split(" ")
        
        if arr[0] == "sail":
             # dont set this below 15 for now, the exact min/max seems
             # to be a little off and setting it to 0 is not good
            val = int(arr[1])
            #val = int(arr[1]) if int(arr[1]) >= 15 else 15
            drive.sail.set(val)
            
        elif arr[0] == "rudder":
              drive.rudder.set(int(arr[1]))
              
        