import sys
ROS = None
try:
    import constants as c
    import boatMath
    ROS = False
except:
    import sailbot.constants as c
    import sailbot.boatMath as boatMath
    ROS = True
import logging

import math

try:
    # try and load all the sensor libraries
    if not ROS:
        from windvane import windVane
        from GPS import gps
        from compass import compass
        import GPS
        #from camera import camera
        import events #import event,Collision_Avoidance,Percision_Navigation,Endurance,Station_Keeping,Search

        from drivers import driver
        from transceiver import arduino
    else:
        from sailbot.windvane import windVane
        from sailbot.GPS import gps
        from sailbot.compass import compass
        import sailbot.GPS as GPS
        #from camera import camera
        import sailbot.events as events #import event,Collision_Avoidance,Percision_Navigation,Endurance,Station_Keeping,Search

        from sailbot.drivers import driver
        from sailbot.transceiver import arduino

except Exception as e:
    # if libraries fail give error message, and exit if this file is being run directly
    print("Failed to import some modules, if this is not a simulation fix this before continuing")
    print(F"Exception raised: {e}")
    if __name__ == '__main__':
        sys.exit(1)

from datetime import date, datetime
from threading import Thread
from time import sleep
import numpy
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class dummyObject(object):
    pass

class boat(Node):
    
    """
    The overarching class for the entire boat, contains all sensor objects and automation functions
    """
    def __init__(self, calibrateOdrive = True):
        """
        Set everything up and start the main loop
        """
        
        super().__init__('main_subscriber')

        # create sensor objects
        self.gps = dummyObject()
        self.gps.latitude = 0.0
        self.gps.longitude = 0.0
        self.gps.track_angle_deg = 0.0
        self.gps.updateGPS = lambda *args: None #do nothing if this function is called and return None
        self.compass = dummyObject() #compass()
        self.compass.angle = 0.0
        
        self.gps_subscription = self.create_subscription(String, 'GPS', self.ROS_GPSCallback, 10)
        self.compass_subscription = self.create_subscription(String, 'compass', self.ROS_compassCallback, 10)
        
        self.pub = self.create_publisher(String, 'driver', 10)
        #self.windvane = windVane()
        
        # try both of the USB ports the 'arduino' (transciver) may be connected to
        try:
            self.arduino = arduino(c.config['MAIN']['ardu_port'])
            if self.arduino.readData() == "'":
                raise Exception("Could not read arduino")
            else:
                print(self.arduino.readData())
        except:
            self.arduino = arduino(c.config['MAIN']['ardu_port2'])
            if self.arduino.readData() == "'":
                raise Exception("Could not read arduino")


        # Set default values for variables
        self.eevee = None
        self.event_arr = []
        self.manualControl = True   # check RC Mode to change manualControl, and manualControl checks for everything else (faster on memory)
        self.cycleTargets = False
        self.currentTarget = None  # (longitude, latitude) tuple
        self.targets = []  # list of (longitude, latitude) tuples

        # Where we want the sail and rudder to be vs where they currently are
        self.targetSail = 0
        self.currentSail = 0
        self.targetRudder = 0
        self.currentRudder = 0

        tempTarget = False

        self.override = False   #whether to automatically switch to RC when inputting manual commands or prevent the commands
        self.MODE_SETTING = c.config['MODES']['MOD_RC']
        #pump_thread = Thread(target=self.pumpMessages)
        #pump_thread.start()
        self.mainLoop()
        
    def ROS_GPSCallback(self, string):
        if string == "None,None,None":
            self.gps.latitude = None
            self.gps.longitude = None
            self.gps.track_angle_deg = None
            return

        lat, long, trackangle = string.replace("(", "").replace(")", "").split(",")
        self.gps.latitude = float(lat)
        self.gps.longitude = float(long)
        self.gps.track_angle_deg = float(trackangle)

    def ROS_compassCallback(self, string):
        if string == "None,None":
            self.compass.angle = None
            return

        angle = string.replace("(", "").replace(")", "")
        self.compass.angle = float(angle)

        

    def adjustSail(self, angle=None):
        """
        Move the sail to 'angle', angle is value between 0 and 90, 0 being all the way in
        """
        dataStr = String()
        if self.manualControl and angle != None:
            # set sail to angle
            dataStr.data = F"(driver:sail:{angle})"
            self.get_logger().info(dataStr.data)
            self.pub.publish(dataStr)

        elif self.currentTarget or self.manualControl:
            # set sail to optimal angle based on windvane readings
            windDir = self.windvane.angle
            targetAngle = windDir + 35
            dataStr.data = F"(driver:sail:{targetAngle})"
            self.get_logger().info(dataStr.data)
            self.pub.publish(dataStr)
            self.currentSail = targetAngle

        else:
            # move sail to home position
            dataStr.data = F"(driver:sail:{0})"
            self.get_logger().info(dataStr.data)
            self.pub.publish(dataStr)
            self.currentSail = 0
            logging.info('Adjusted sail to home position')

    def adjustRudder(self, angleTo):
        """
        Move the rudder to 'angle', angle is value between -45 and 45
        """
        dataStr = String()
        if self.currentTarget or self.manualControl == True:
            # adjust rudder for best wind
            # angleTo = gps.angleTo(self.currentTarget)

            d_angle = angleTo - self.gps.track_angle_deg

            if d_angle > 180: d_angle -= 180

            dataStr.data = F"(driver:rudder:{d_angle})"
            self.get_logger().info(dataStr.data)
            self.pub.publish(dataStr)

            self.currentRudder = d_angle
            logging.info('Adjusted rudder to: %d', d_angle)

        else:
            # move rudder to home position
            dataStr.data = F"(driver:rudder:{0})"
            self.get_logger().info(dataStr.data)
            self.pub.publish(dataStr)

            self.currentRudder = 0
            logging.info('Adjusted rudder to home position')

    def pumpMessages(self):
        """
        Infinite loop to be run in a thread, once started will run readMessages over and over again
        """
        while True:
            self.readMessages()

    def mainLoop(self):
        """
        Main loop that will run until boat is stopped 
        """
        sailStep = 90
        rudderStep = 90
        while True:
            self.readMessages() # read messages from transceiver   

            if self.manualControl:
                # set sail and rudder to values read from readMessages
                self.adjustSail(self.targetSail)
                self.adjustRudder(self.targetRudder)
                    

            else:  # set mode for automation
                continue # automation code crashes so skip until fixed
                if self.MODE_SETTING == c.config['MODES']['MOD_COLLISION_AVOID']:
                    logging.info("Received message to Automate: COLLISION_AVOIDANCE")
                    self.eevee = events.Collision_Avoidance(self.event_arr)

                elif self.MODE_SETTING == c.config['MODES']['MOD_PRECISION_NAVIGATE']:
                    logging.info("Received message to Automate: PRECISION_NAVIGATE")
                    self.eevee = events.Percision_Navigation(self.event_arr)

                elif self.MODE_SETTING == c.config['MODES']['MOD_ENDURANCE']:
                    logging.info("Received message to Automate: ENDURANCE")
                    self.eevee = events.Endurance(self.event_arr)

                elif self.MODE_SETTING == c.config['MODES']['MOD_STATION_KEEPING']:
                    logging.info("Received message to Automate: STATION_KEEPING")
                    self.eevee = events.Station_Keeping(self.event_arr)

                elif self.MODE_SETTING == c.config['MODES']['MOD_SEARCH']:
                    logging.info("Received message to Automate: SEARCH")
                    self.eevee = events.Search(self.event_arr)

                '''if not self.currentTarget:
                    # if we dont have a target GPS load the next target from the targets list
                    if self.targets != []:
                        self.currentTarget = self.targets.pop(0)
                    else:
                        print('no targets')
                if self.currentTarget: 
                    # go to target if we have one
                    self.goToGPS(self.currentTarget[0], self.currentTarget[1])'''
                try:
                    targ_x,targ_y = self.eevee.next_gps()
                    if targ_x:  #__number__,__number__
                        self.currentTarget[0], self.currentTarget[1] = targ_x,targ_y
                        self.goToGPS(targ_x,targ_y)
                    else:   #None,None
                        self.adjustSail(90)
                except events.eventFinished:
                    #end of event
                    self.eevee = None
                    logging.info("OVERRIDE: Switching to RC")
                    self.MODE_SETTING = c.config['MODES']['MOD_RC']
                    self.manualControl = True



    def sendData(self):
        #GPS:x/y, RudderPos, SailPos, BoatOrientation, Windspd, WindDir, Batt
        #1/2,3,4,5,6,7,8
        totstr = ""
        arr = ["N/a"] * 8

        try:
            arr[0] = F"{self.gps.longitude}"
            arr[1] = F"{self.gps.latitude}"
        except Exception as e:
            logging.info(f"failed to find data: gps, {e}")
            print(f"data error: {e}")

        try:
            if abs(self.currentRudder) >= 10:
                arr[2] = F"{self.currentRudder}"
            else: #format so number is 2 digits
                arr[2] = F"0{self.currentRudder}"
        except Exception as e:
            logging.info(f"failed to find data: rudder, {e}")
            print(f"data error: {e}")

        try:
            if abs(self.currentSail) >= 10:
                arr[3] = F"{self.currentSail}"
            else: #format so number is 2 digits
                arr[3] = F"0{self.currentSail}"
        except Exception as e:
            logging.info(f"failed to find data: sail, {e}")
            print(f"data error: {e}")
        
        try:
            arr[4] = F"{self.compass.angle}"
        except Exception as e:
            logging.info(f"failed to find data: compass, {e}")
            print(f"data error: {e}")

        try:
            #arr[5] = #dont have
            arr[6] = F"{self.windvane.angle}"
        except Exception as e:
            logging.info(f"failed to find data: windvane, {e}")
            print(f"data error: {e}")

        #arr[7] = #dont have

        for i in range(8):
            totstr += arr[i]
            if i<7:
                totstr += ","
        
        self.arduino.send("DATA: " + totstr)

    def readMessages(self, msgOR=None):
        """ 
        Read messages from transceiver
        """
        if msgOR != None:
            msgs = msgOR
        else:
            #msgs = self.arduino.read()[:-3].replace('\n', '')
            msgs = self.arduino.readData()
        #print(msgs)

        try:
            for msg in msgs:
                # print(F"msg {msg[0]}")
                processed = False # to track if we processed the message, if not we can handle an invalid message
                ary = msg.split(" ")
                # print(F"ary: {ary}")
                #make it so you cant do manual commands unless in RC mode to avoid automation undoing work done
                #override is in place to switch to RC if given RC commands if potential accidents may happen
                if len(ary) > 0:
                        # manual adjust sail
                    if ary[0] == 'sail' or ary[0] == "S":
                        if self.override:
                            logging.info("OVERRIDE: Switching to RC")
                            self.MODE_SETTING = c.config['MODES']['MOD_RC']
                            self.manualControl = True

                        if self.manualControl:
                            logging.info(F'Received message to adjust sail to {float(ary[1])}')
                            self.targetSail = float(ary[1])
                            processed = True
                        else:
                            logging.info("Refuse to change sail, not in RC Mode")

                        # manual adjust rudder

                    elif ary[0] == 'rudder' or ary[0] == "R":
                        if self.override:
                            logging.info("OVERRIDE: Switching to RC")
                            self.MODE_SETTING = c.config['MODES']['MOD_RC']
                            self.manualControl = True

                        if self.manualControl: 
                            rudderMidPoint = (float(c.config['CONSTANTS']["rudder_angle_max"]) - float(c.config['CONSTANTS']['rudder_angle_min']))/2
                            halfDeadZone  = float(c.config['CONSTANTS']['ControllerRudderDeadZoneDegs']) / 2

                            # ignore values within the dead zone, ex: if controller is at 1 degree, rudder will still default to 0
                            if float(ary[1]) < rudderMidPoint + halfDeadZone and float(ary[1]) > rudderMidPoint - halfDeadZone:  
                                self.targetRudder = float(rudderMidPoint) - 45 #values read in range from 0:90 instead of -45:45
                            else:
                                self.targetRudder = float(ary[1]) - 45 #values read in range from 0:90 instead of -45:45
                            logging.info(F'Received message to adjust rudder to {float(ary[1])}')
                            processed = True
                        else:
                            logging.info("Refuse to change sail, not in RC Mode")

                    elif str(ary[0]) == 'sailOffset' or ary[0] == 'SO':
                        self.manualControl = True
                        dataStr = String()
                        dataStr.data = F"(driverOffset:sail:{float(ary[1])})"
                        self.get_logger().info(dataStr.data)
                        self.pub.publish(dataStr)

                    elif str(ary[0]) == 'rudderOffset' or ary[0] == 'RO':
                        self.manualControl = True
                        dataStr = String()
                        dataStr.data = F"(driverOffset:rudder:{float(ary[1])})"
                        self.get_logger().info(dataStr.data)
                        self.pub.publish(dataStr)

                    elif ary[0] == 'controlOff':
                        self.manualControl = False
                        self.override = False

                    elif ary[0] == 'override':
                        self.override = not self.override
                        processed = True


                    elif ary[0] == 'mode': # set boats mode to the value specified, command should be formatted : "mode {value}" value is int 1-5
                        try:
                            if int(ary[1]) < 0 or int(ary[1]) > 5:
                                logging.info("Outside mode range")
                            else:
                                logging.info(F'Setting mode to {int(ary[1])}')
                                self.MODE_SETTING = int(ary[1])

                                logging.info(F'Setting event array')
                                self.event_arr = []
                                for i in range(len(ary)-2):
                                    self.event_arr.append(ary[i+2])

                                processed = True
                        except Exception as e:
                            print(F"Error changing mode: {e}")
                            logging.info(F"Error changing mode: {e}")

                        if self.MODE_SETTING == c.config['MODES']['MOD_RC']:
                            logging.info("Setting manual mode to True")
                            self.manualControl = True
                        else:
                            logging.info("Setting manual mode to False")
                            self.manualControl = False


                    elif ary[0] == 'addTarget': # add current GPS to list of targets
                        while self.gps.latitude == None or self.gps.longitude == None:
                            print("no gps")
                            #self.gps.updategps()
                            sleep(.1)
                        target = (self.gps.latitude, self.gps.longitude)
                        logging.info(F"added Target at {target}")
                        self.targets.append(target)
                        print(f"added target, current target list is {self.targets}")
                        processed = True
                    elif ary[0] != '':
                        print(f'unknown command {ary[0]}')
                
                if processed:
                        pass
                        #self.arduino.send("boat probably processed message")

        except Exception as e:
            logging.info(f"failed to read command {msgs}")
            #print(f"message error: {e}")
            x = [letter for letter in msgs]
            #print(ary, msgs, x)
            
    def goBetweenBuoy(self, LeftBuoyPixel, RightBuoyPixel):
        # Both in camera, assuming arguments = none if not in camera
        if LeftBuoyPixel and RightBuoyPixel:
            # Find distance of buoys to center line
            # TODO Add the total camera pixel size to constants (x,y)
            # Thought it only x distance needs to be checked
            distLeft = abs(LeftBuoyPixel[1] - c.cameraPixelSizeX / 2.0)
            distRight = abs(RightBuoyPixel[1] - c.cameraPixelSizeX / 2.0)

            # Check if one is significantly closer to center
            # TODO determine pixel wise what is significantly closer
            if distRight - distLeft > 20:  # Left buoy is closer
                # Turn right
                newCompassAngle = (self.compass.angle + 10) % 360
                self.turnToAngle(newCompassAngle)
            elif distLeft - distRight > 20:  # Right buoy closer
                # Turn left
                newCompassAngle = (self.compass.angle - 10) % 360
                self.turnToAngle(newCompassAngle)
        else:
            # Go to gps
            self.goToGps(self.currentTarget[0], self.currentTarget[1])

    def goToGPS(self, lat, long):
        """  
        Go to GPS coordinates lat, long
        """

        # Get current GPS coordinates, if we can't load info from GPS wait until we can and print error message
        #self.gps.updategps()
        while self.gps.latitude == None or self.gps.longitude == None:
            print("no gps")
            #self.gps.updategps()
            sleep(.1)

        # determine angle we need to turn
        compassAngle = self.compass.angle
        deltaAngle = boatMath.angleToPoint(compassAngle, self.gps.latitude, self.gps.longitude, lat, long)
        targetAngle = (compassAngle + deltaAngle) % 360
        windAngle = self.windvane.angle

        
        if (deltaAngle + windAngle) % 360 < self.windvane.noGoMin and (
                deltaAngle + windAngle) % 360 > self.windvane.noGoMax: # angle is not in no go zone
            self.turnToAngle(targetAngle)
        else: # angle is in no go zone, go to the nearest edge of no go zone
            if (targetAngle - compassAngle) % 360 <= 180:
                # turn left
                self.turnToAngle(self.windvane.noGoMin)
            else:
                # turn right
                self.turnToAngle(self.windvane.noGoMax)

        if abs(boatMath.distanceInMBetweenEarthCoordinates(lat, long, self.gps.latitude, self.gps.longitude)) < int(c.config['CONSTANTS']['reachedGPSThreshhold']):
            # if we are very close to GPS coord
            if self.cycleTargets:
                self.targets.append((lat, long))
            self.currentTarget = None
            self.adjustRudder(0)

    def turnToAngle(self, angle, wait_until_finished = False):
        """
        adjust rudder until the boat is facing compass angle 'angle'
        if wait_until_finished is True the boat will continue to adjust rudder until the boat is facing the right direction
        if wait_until_finished is False the boat will adjust the rudder to an appropriate angle and then return
        """
        leftPositive = -1  # change to negative one if boat is rotating the wrong way
        
        logging.info("starting turnToAngle")
        compassAngle = self.compass.angle
        while abs(compassAngle - angle) > int(c.config['CONSTANTS']['angle_margin_of_error']): # while not facing the right angle
            compassAngle = self.compass.angle

            if ((angle - compassAngle) % 360 <= 180):  # turn Left
                # move rudder to at most 45 degrees
                rudderPos = leftPositive * min(45, 3 * abs(compassAngle - angle))  # /c.rotationSmoothingConst)
                logging.info(F'turning to angle: {angle} from angle: {compassAngle} by turning rudder to {rudderPos}')
                self.adjustRudder(int(rudderPos))
            else: 
                # move rudder to at most -45 degrees
                rudderPos = -1 * leftPositive * min(45, 3 * abs(compassAngle - angle))  # /c.rotationSmoothingConst)
                logging.info(F'turning to angle: {angle} from angle: {compassAngle} by turning rudder to {rudderPos}')
                self.adjustRudder(int(rudderPos))

            if not wait_until_finished:
                break
            


        #print(compassAngle)
        logging.info("finished turnToAngle")


def main(args=None):

    rclpy.init(args=args)

    calibrateOdrive = True
    for arg in sys.argv:
        if arg == "noCal":
            calibrateOdrive = False
    b = boat(calibrateOdrive = calibrateOdrive)
    try:
        b.mainLoop()
        # b.turnToAngle(90)
        # b.goToGPS(40.44368167, -79.9580000)
        print("Cleaning Up")
        b.adjustRudder(0)
        b.adjustSail(0)

        b.destroy_node()
        rclpy.shutdown()

    except KeyboardInterrupt as e:
        print("\n\nEXITING...\n\n")
        b.adjustRudder(0)
        b.adjustSail(0)
        b.destroy_node()
        rclpy.shutdown()
        print("EXITED CLEANLY")

if __name__ == "__main__":
    """
    this is the code that runs if you run this file 
    read in command line args and create boat object
    start mainloop
    when code is stopped return sail and rudder to 0 position
    """
    main()


