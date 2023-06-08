"""
reads and sends data from the connected USB transceiver
"""
#from messages_pb2 import *
import serial
try:
    import constants as c
except:
    import sailbot.constants as c
import sys
import smbus2 as smbus#,smbus2
import time

I2C_SLAVE_ADDRESS = 0x10

def ConvertStringsToBytes(src):
  converted = []
  for b in src:
    converted.append(ord(b))
  return converted

class arduino:

    def __init__(self, port_num):
        # connect to device on 'port_num'
        self.ser1 = serial.Serial(port_num, c.config['MAIN']['baudrate'], timeout = .5) 
        self.I2Cbus = smbus.SMBus(1)

    def send(self, data):
        #print(data)
        self.ser1.write(str(data).encode())

    def readData(self):
        # get data from transceiver
        self.send("?") # transceiver is programmed to respond to '?' with its data
        msgs = []
        msg = self.read()
        if msg == None or msg == "'":
            time.sleep(.1)
            msg = self.read()
            if msg == None or msg == "'":
                self.send("?")
                msg = self.read()
        # print(msg)
        splits = msg.split(" ")
        if len(splits) >= 7:
            returnList = [F"{splits[0]} {splits[1]}", F"{splits[2]} {splits[3]}"] # rudderOffset (val), sailOffset (val)
        
            mode, offset = self.getModeAndOffset(float(splits[5]), float(splits[7]))

            returnList.append(F"{mode} {offset}")

            return returnList
        else:
            return msg
                
        

    def read(self):
        message = str(self.ser1.readline()).replace("\r\n'", "").replace("b'", "").replace("\\r\\n'", "")
        
        return str(message)

    def getModeAndOffset(self, readModeVal, readOffsetVal):
        modes = { # mappings of the read mode integer to the function that should be used with the offsetValue
            "controlOff" : 0,
            "sailOffset" : 45,
            "rudderOffset" : 90
        }

        bestMode = None
        bestVal = None
        for key, value in modes.items():
            if bestVal == None or abs(readModeVal - value) < bestVal:
                bestMode = key
                bestVal = abs(readModeVal - value)

        if bestMode == "sailOffset":
            offset = self.map(readOffsetVal, 0, 90, -2, 2)

        elif bestMode == "rudderOffset":
            offset = self.map(readOffsetVal, 0, 90, -0.2, 0.2)

        else:
            offset = 0

        return bestMode, offset

    def map(self, x, min1, max1, min2, max2):
        # converts value x, which ranges from min1-max1, to a corresponding value ranging from min2-max2
        # ex: map(0.3, 0, 1, 0, 100) returns 30
        # ex: map(70, 0, 100, 0, 1) returns .7
        x = min(max(x, min1), max1)
        return min2 + (max2-min2)*((x-min1)/(max1-min1))

if __name__ == "__main__":
    print("start")
    try:
        ardu = arduino(c.config['MAIN']['ardu_port'])
        if ardu.read() == "'":
            #print("error:", ardu.readData())
            raise EOFError("could not read arduino data")
    except EOFError:
        try:
            ardu = arduino(c.config['MAIN']['ardu_port2'])
            if ardu.read() == "'":
                #print("error:", ardu.readData())
                raise EOFError("could not read arduino data")
        except EOFError:
            ardu = arduino(c.config['MAIN']['ardu_port3'])
            if ardu.read() == "'":
                #print("error:", ardu.readData())
                raise EOFError("could not read arduino data")
    
    time.sleep(1)
    print("start2")
    while True:
        # print(ardu.read())
        print(ardu.readData())

