import constants as c
import logging
import math
import time

try:
    from windvane import windVane
    from GPS import gps
    from compass import compass
    import GPS
    from camera import camera
    from boatMath import getCoordinateADistanceAlongAngle
    from drivers import driver
    from transceiver import arduino
    import constants
    from boatMain import boat
except Exception as e:
    print("Failed to import some modules, if this is not a simulation fix this before continuing")
    print(F"Exception raised: {e}")
from datetime import date, datetime
from threading import Thread
from time import sleep



class events(boat):

    def __init__(self):
        self.MESSAGE = None
        print("init")
        self.totalError = 0.0
        self.oldError = 0.0
        self.oldTime = time.time()


    def event_NL(self):
        # Nice loop to put in event functions
        #   - sends data about boat
        #   - reads messages and returns bool
        #     if need to stop doing the command (0:no, 1:YES STOP)
        ret = False

        # READ MESSAGE SECTION =========
        self.MESSAGE = self.arduino.readData() #update read
        print("events:", self.MESSAGE)
            # for msg in msgs:
        try:
            for msg in self.MESSAGE:
                ary = msg.split(" ")
                if len(ary) > 0:
                    if ary[0] == 'sail' or ary[0] == "S":
                        ret = True

                    elif ary[0] == 'rudder' or ary[0] == "R":
                        ret = True

                    elif ary[0] == 'mode' and ary[1] == 0:
                        ret = True
        except Exception as e:
            logging.info(f"failed to read command {self.MESSAGE}")
            print(f"message error: {e}")
        
        boat.readMessages(self.MESSAGE) #override message to make faster

        # SEND MESSAGE SECTION =========
        boat.sendData()

        # New PID stuff
        if (time.time() - self.oldTime < 100):  # Only runs every tenth of a second
            # Finds the angle the boat should take
            error = boat.targetAngle - boat.compass.angle  # Finds how far off the boat is from its goal
            self.totalError += error  # Gets the total error to be used for the integral gain
            derivativeError = (error - self.oldError) / (
                        time.time() - self.oldtime)  # Gets the change in error for the derivative portion
            deltaAngle = constants.P * error + constants.I * self.totalError + constants.D * derivativeError  # Finds the angle the boat should be going

            # Translates the angle into lat and log so goToGPS won't ignore it
            boat.currentAngle = getCoordinateADistanceAlongAngle(1000, deltaAngle + boat.compass.angle)

            # Resets the variable
            self.oldTime = time.time()
            self.oldError = error


        return ret


    def testloop(self, inp):
        t_inp = input("inputs: ")
        t_arr = t_inp.split(" ")
        if inp == "CA":
            self.Collision_Avoidance(t_arr)
        elif inp == "PN":
            self.Percision_Navigation(t_arr)
        elif inp == "E":
            self.Endurance(t_arr)
        elif inp == "SK":
            self.Station_Keeping(t_arr)
        elif inp == "S":
            self.Search(t_arr)
        else:
            print("nah")


    #include in automation event code's main loop:
        #self.readmessages to see if it switches modes or RC commands, returning/break if another mode is true
        #self.sendData() to export data

    #inputs: B1,B2,B3,B4 long/lat
    #arr: [B1x,B1y, etc]
    def Collision_Avoidance(self,arr):
        print("Collision_Avoidance moment")

        if self.event_NL(): return

    #inputs: B1,B2,B3,B4 long/lat
    #arr: [B1x,B1y, etc]
    def Percision_Navigation(self,arr):
        print("Percision_Navigation moment")

        if self.event_NL(): return

    #inputs: B1,B2,B3,B4 long/lat
    #arr: [B1x,B1y, etc]
    def Endurance(self,arr):
        print("Endurance moment")

        if self.event_NL(): return

    #inputs: B1,B2 long/lat
    #arr: [B1x,B1y, etc]
    def Station_Keeping(self,arr):
        print("Station_Keeping moment")

        if self.event_NL(): return

    #inputs: B1 long/lat, Radius
    def Search(self,arr):
        #make in boatMain along with mode switch, attach buoy coords and radius in ary
        #will need to redo GUI then ://////
        while(True):
            self.search_pattern(boat.gps.latitude, boat.gps.longitude, arr[0], arr[1], arr[2])

            if self.event_NL(): return
        
    
    def search_pattern(self, gps_lat, gps_long, buoy_lat, buoy_long, radius):
        #find five coords via search pattern
        #in realtion to current pos and buoy rad center pos

        a = gps_lat - buoy_lat
        b = gps_long - buoy_long
        ang = math.atan(b/a)
        ang *= 180/math.pi

        if(a<0):    ang += 180

        tar_angs = [ang,ang+72,ang-72,ang-(72*3),ang-(72*2)]
        tarx = [0] * 5
        tary = [0] * 5

        for i in range(0,5):
            tarx[i] =  buoy_lat  + radius*math.cos( tar_angs[i] * (math.pi/180) )
            tary[i] =  buoy_long + radius*math.sin( tar_angs[i] * (math.pi/180) )
        
        arr = [tarx,tary]
        return arr

        

if __name__ == "__main__":
    eevee = events()
    while True:
        inp = input("Mode Test: ") # Taking input from user
        eevee.testloop(inp)

