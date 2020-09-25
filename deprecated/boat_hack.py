import board
import busio
import adafruit_pca9685 as pcaLib
import constants as c
import messages_pb2
import serial
import drivers
from threading import Thread

def map(x, min1, max1, min2, max2):
    x = min(max(x, min1), max1)
    return min2 + (max2-min2)*((x-min1)/(max1-min1))
            
class obj_sail:
            
    servo_min = c.SAIL_SERVO_MIN
    servo_max = c.SAIL_SERVO_MAX
            
    angle_min = c.SAIL_ANGLE_MIN
    angle_max = c.SAIL_ANGLE_MAX
            
    def __init__(self, channel_index):
        self.channel =  pca.channels[channel_index]

    def set(self, degrees):
        try:
            degrees = float(degrees)
            val = map(degrees, self.angle_min, self.angle_max,
                  self.servo_min, self.servo_max)

            self.channel.duty_cycle = int(val)
            return
        except TypeError:
            print("invalid input, degrees param must be a number")
            
class obj_rudder:
            
    servo_min = c.RUDDER_SERVO_MIN
    servo_ctr = c.RUDDER_SERVO_CTR
    servo_max = c.RUDDER_SERVO_MAX
            
    angle_min = c.RUDDER_ANGLE_MIN
    angle_max = c.RUDDER_ANGLE_MAX
    angle_ctr = angle_min + (angle_max - angle_min) / 2
            
    def __init__(self, channel_index):
        self.channel =  pca.channels[channel_index]

    def set(self, degrees):
        try:
            if degrees < self.angle_ctr:
                
                val = map(degrees, self.angle_min, self.angle_ctr,
                      self.servo_min, self.servo_ctr)
            else:
                val = map(degrees, self.angle_ctr, self.angle_max,
                      self.servo_ctr, self.servo_max)


            self.channel.duty_cycle = int(val)
            return
        except TypeError:
            print("invalid input, degrees param must be a number")
    
class arduino:
    def __init__(self):
        #self.ser1 = serial.Serial('COM'+portnum, 9600)
        try:
            self.ser1 = serial.Serial(str(c.ARDU_PORT), c.BAUDRATE)
        except:
            self.ser1 = serial.Serial(str(c.ARDU_PORT2), c.BAUDRATE)
        print(repr(self.ser1))
        
    def send(self, data):
        self.ser1.write(str(data).encode())
        
    def read(self):
        message = self.ser1.readline()
        #message = self.ser1.read(c.RECEIVE_BUFFER_SIZE)
        return message[0:-2]
    
class proto:
    def position_status(self, sailPosition, rudderPosition):
        message = messages_pb2.BoatToBase()
        status = messages_pb2.SailStatus()
        status.sailPosition = sailPosition
        status.rudderPosition = rudderPosition
        message.sails = status
        return message
    
def proto_both(message):
    command = message.skipper
    mSail.set(command.sailPosition)
    mRudder.set(command.rudderPosition)
    
def proto_sail(message):
    command = message.sail
    mSail.set(command.position)
    
def proto_rudder(message):
    command = message.rudder
    mRudder.set(command.position)
    
def proto_mode(message):
    command = message.mode
    
def handle_input():
    sail = 15
    rudder = 0
    drivers.drive.sail.set(sail)
    drivers.drive.rudder.set(rudder)
    while True:
        message = REC.read()
        #commands = {
         #       "sail" : mSail.set,
          #      "rudder" : mRudder.set
           # }
        commands = {
            'skipper' : proto_both,
            'sail' : proto_sail,
            'rudder' : proto_rudder,
            'mode' : proto_mode
        }
        
        if message:
            #ary = message.split(' ')
            
            #cmd = commands[ary.pop(0)]
            #cmd(*ary)
            print(message)
            ary = message.decode().split(" ")
            if ary[0] == "sail":
                sail += int(ary[1])
                
                if sail < 10:
                    sail = 10
                    
                elif sail > 90:
                    sail = 90
                
                print("sail", sail)
            elif ary[0] == "rudder":
                rudder += int(ary[1])
                if rudder < -45:
                    rudder = -45
                elif rudder > 45:
                    rudder = 45
                print("rudder", rudder)

            drivers.drive.sail.set(sail)
            drivers.drive.rudder.set(rudder)
            #proto_message = messages_pb2.BaseToBoat()
            #proto_message.ParseFromString(message)
            #command = proto_message.WhichOneOf('command')
            #commands[command](message)

if __name__ == "__main__":

    i2c = busio.I2C(board.SCL, board.SDA)
    pca = pcaLib.PCA9685(i2c)
    pca.frequency = 50

    mSail = obj_sail(0)
    mRudder = obj_rudder(1)
    
    #arduino class needs com port
    REC = arduino()
    
    pump_thread = Thread(target=handle_input)
    pump_thread.start()
    
    while True:
        pass
        """string = input("  > Enter Input:")
        
        if string == "quit":
            break
        
        arr = string.split(" ")
        
        if arr[0] == "sail":
             # dont set this below 15 for now, the exact min/max seems
             # to be a little off and setting it to 0 is not good
            val = int(arr[1]) if int(arr[1]) >= 15 else 15
            mSail.set(val)
            
        elif arr[0] == "rudder":
              mRudder.set(int(arr[1]))
        
        #handle_input(REC.read())"""


                  
