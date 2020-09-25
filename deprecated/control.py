#sailbot rudder and sail control
#numbers for the big wet

import board
import busio
import adafruit_pca9685
i2c = busio.I2C(board.SCL, board.SDA)
pca = adafruit_pca9685.PCA9685(i2c)
pca.frequency = 50
sail = pca.channels[0]
rudder = pca.channels[1]

SAIL_SERVO_MIN = 2550
SAIL_SERVO_MAX = 6750
RUDDER_SERVO_MIN = 2500
RUDDER_SERVO_MAX = 7000
RUDDER_SERVO_CTR = 4850

def set_rudder(degrees)
    #TODO find ranges for the rudder
    return

def set_main_sail(degrees)
    ratio = (SAIL_SERVO_MAX - SAIL_SERVO_MIN) / 90
    value = (ratio * degrees) + SAIL_SERVO_MIN
    sail.duty_cycle = value
    return
