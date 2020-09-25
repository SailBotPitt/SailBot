import constants as C

from windvane import windVane
from GPS import gps 
from drivers import driver
#from transceiver import arduino
from time import sleep

class boat:

    def __init__(self):

        self.gps = gps()
        self.windvane = windVane()
        self.drivers = driver()
        #self.arduino = arduino(C.ARDU_PORT)

        self.currentTarget = None # (longitude, latitude) tuple
        self.targets = [] # holds (longitude, latitude) tuples

    def move(self):
        if self.gps.distanceTo(currentTarget) < C.ACCEPTABLE_RANGE and len(self.targets) > 0:
            #next target

            if (False):#check if next target would involve no-go-zone, if so set current target to another point for zig-zag path
                pass

            else:
                self.currentTarget = self.targets.pop(0)

        else:
            #move towards target
            self.adjustSail()
            self.adjustRudder()
            
    def adjustSail(self):
        if self.currentTarget or True:
            windDir = self.windvane.angle
            if windDir > 180:
                windDir = 180 - (windDir - 180)
            targetAngle = max(min(windDir / 2, 90), 3)
            print(targetAngle , self.windvane.angle)
            self.drivers.sail.set(targetAngle)
        else:
            #move sail to home position
            self.drivers.sail.set(0)
            
    def adjustRudder(self):
        if self.currentTarget:
            #adjust rudder for best wind
            angleTo = gps.angleTo(self.currentTarget)
            d_angle = angleTo - gps.track_angle_deg

            if d_angle > 180: d_angle -= 180

            self.drivers.rudder.set(d_angle)
            
        else:
            #move sail to home position
            self.drivers.rudder.set(0)

    def readMessages(self):
        msgs = self.arduino.read()

        for msg in msgs:
            ary = msg.split(' ')
            if len(ary) > 1:
                if ary[0] == 'sail': self.drivers.sail.set(float(ary[1]))
                elif ary[0] == 'rudder': self.drivers.rudder.set(float(ary[1]))
                elif ary[0] == 'mode': print("TODO: add Modes")

b = boat()

while True:
    b.adjustSail()
    sleep(1)
