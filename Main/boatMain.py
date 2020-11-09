import constants as C

from windvane import windVane
from GPS import Gps 
from drivers import driver
from transceiver import arduino

class boat:

    def __init__(self):
	
        self.gps = Gps()
        self.windvane = windVane()
        self.drivers = driver(autoSail = False)
        self.arduino = arduino(C.ARDU_PORT)

        self.currentTarget = None # (longitude, latitude) tuple
        self.targets = [] # holds (longitude, latitude) tuples

        noGoZoneDegs = 20

        tempTarget = False

    def move(self):
        if self.gps.distanceTo(currentTarget) < C.ACCEPTABLE_RANGE and len(self.targets) > 0:
            #next target

            targetAngle = TargetAngleRelativeToNorth() #Func doesnt exist yet

            windAngleRelativeToNorth = convertWindAngle(self.windVane.angle)

            if tempTarget == False and targetAngle - windAngleRelativeToNorth < (noGoZoneDegs/2):
                if targetAngle < windAngleRelativeToNorth or abs(targetAngle - 360) < windAngleRelativeToNorth:
                    #newTargetAngle < targetangle
                    newTargetAngle = windAngleRelativeToNorth - (noGoZoneDegs/2 + 10) 
                else:
                    #newTargetAngle > targetAngle
                    newTargetAngle = windAngleRelativeToNorth + (noGoZoneDegs/2 + 10)

                tempTarget = True
                rotateToAngle(newTargetAngle)

            else if tempTarget and targetAngle - windAngleRelativeToNorth > (noGoZoneDegs/2):
                tempTarget = False
                rotateToAngle(targetAngle)

            else if tempTarget == False:
                rotateToAngle(targetAngle)

            # else:
            #     self.currentTarget = self.targets.pop(0)

        else:
            #move towards target
            self.adjustSail()
            self.adjustRudder()
            
    def adjustSail(self):
        if self.currentTarget:
            windDir = self.windvane.angle
            targetAngle = windDir + 35
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

    def sendMessagesToGui(self):
        #Gps data
        coordinates = self.gps.getCoordinates()
        arduino.send(coordinates)

        #Rudder data
        rudd_position = "rudder_pos " + str(self.drivers.rudder.get())
        arduino.send(rudd_position)

        #Sail Position
        sail_position = "sail_pos " + str(self.drivers.sail.get())
        arduino.send(sail_position)

if __name__ == "__main__":

    boat()

