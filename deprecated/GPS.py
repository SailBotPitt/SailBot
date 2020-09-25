#https://learn.adafruit.com/adafruit-ultimate-gps/circuitpython-parsing
import time
import board
import busio
from time import sleep
from threading import Thread
 
import adafruit_gps

class gps():

    def __init__(self):

        # a slightly higher timeout (GPS modules typically update once a second).
        # These are the defaults you should use for the GPS FeatherWing.
        # For other boards set RX = GPS module TX, and TX = GPS module RX pins.
        #self.uart = busio.UART(board.TX, board.RX, baudrate=9600, timeout=10)
        #

        # for a computer, use the pyserial library for uart access
        import serial
        self.uart = serial.Serial("/dev/ttyS0", baudrate=9600, timeout=10)
        self.gps = adafruit_gps.GPS(self.uart, debug=False) 

        # Turn on the basic GGA and RMC info (what you typically want)
        self.gps.send_command(b'PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')
        # Turn on just minimum info (RMC only, location):
        #gps.send_command(b'PMTK314,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')
        # Turn off everything:
        #gps.send_command(b'PMTK314,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')
        # Turn on everything (not all of it is parsed!)
        #gps.send_command(b'PMTK314,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0')

        # Set update rate to once a second (1hz) which is what you typically want.
        self.gps.send_command(b'PMTK220,1000')
        # Or decrease to once every two seconds by doubling the millisecond value.
        # Be sure to also increase your UART timeout above!
        #gps.send_command(b'PMTK220,2000')
        # You can also speed up the rate, but don't go too fast or else you can lose
        # data during parsing.  This would be twice a second (2hz, 500ms delay):
        #gps.send_command(b'PMTK220,500')

        pump_thread = Thread(target=self.run)# creates a Thread running an infinite loop pumping server
        pump_thread.start()

    def __getattribute__(self, name):
        """
        if an attempt is made to access an attribute that does not exist, it will then attempt to get the attribute from gps object
        this means that rather than using gps_object.gps.longitude, it is possible to use gps_object.longitude
        """
        try:
            return self.gps.__getattribute__(name) 
        except:
            return super().__getattribute__(name)

    def run(self):
        while True:
            self.update()

    def update(print_info = False):
        self.gps.update()

        if gps.has_fix:

            if print_info:

                print('Fix timestamp: {}/{}/{} {:02}:{:02}:{:02}'.format(
                    gps.timestamp_utc.tm_mon,   # Grab parts of the time from the
                    gps.timestamp_utc.tm_mday,  # struct_time object that holds
                    gps.timestamp_utc.tm_year,  # the fix time.  Note you might
                    gps.timestamp_utc.tm_hour,  # not get all data like year, day,
                    gps.timestamp_utc.tm_min,   # month!
                    gps.timestamp_utc.tm_sec))

                print('Latitude: {0:.6f} degrees'.format(gps.latitude))
                print('Longitude: {0:.6f} degrees'.format(gps.longitude))
                print('Fix quality: {}'.format(gps.fix_quality))
                # Some attributes beyond latitude, longitude and timestamp are optional
                # and might not be present.  Check if they're None before trying to use!
                if gps.satellites is not None:
                    print('# satellites: {}'.format(gps.satellites))
                if gps.altitude_m is not None:
                    print('Altitude: {} meters'.format(gps.altitude_m))
                if gps.speed_knots is not None:
                    print('Speed: {} knots'.format(gps.speed_knots))
                if gps.track_angle_deg is not None:
                    print('Track angle: {} degrees'.format(gps.track_angle_deg))
                if gps.horizontal_dilution is not None:
                    print('Horizontal dilution: {}'.format(gps.horizontal_dilution))
                if gps.height_geoid is not None:
                    print('Height geo ID: {} meters'.format(gps.height_geoid))
                    
        else:
            print("no fix")
            
if __name__ == "__main__":
    g = gps()
    sleep(10)
 
