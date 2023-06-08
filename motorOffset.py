"""
hadles turning motors using Odrive/Stepper driver 
"""

import board
import busio
#import adafruit_pca9685 as pcaLib
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
try:
    import constants as c
except:
    import sailbot.constants as c

from threading import Thread
from RPi import GPIO
from time import sleep



class motorOffset(Node):
    def __init__(self):
        super().__init__('motorOffset')

        self.pub = self.create_publisher(String, 'driver', 10)

    def rudderOffset(self, value):
        dataStr = String()
        dataStr.data = F"(driverOffset:rudder:{value})"
        self.pub.publish(dataStr)

    def sailOffset(self, value):
        dataStr = String()
        dataStr.data = F"(driverOffset:sail:{value})"
        self.pub.publish(dataStr)


def main(args = None):
    rclpy.init(args=args)
    offsetter = motorOffset()
    while True:
        try:
            cmd = input("> ")
            cmd = cmd.split(' ')
            if len(cmd) == 2:
                if cmd[0] == 's':
                    value = float(cmd[1])
                    offsetter.sailOffset(value)

                if cmd[0] == 'r':
                    value = float(cmd[1])
                    offsetter.rudderOffset(value)
        except KeyboardInterrupt as e:
            break
        except Exception as e:
            print(F"error: {e}")
    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    print("Destroying driver node")
    drv.destroy_node()
    rclpy.shutdown()

