#https://learn.adafruit.com/adafruit-ultimate-gps/circuitpython-parsing
import time
try:
    import board
    import busio
    import adafruit_gps
except:
    print("Failed to import board, run on Raspberry Pi")
from time import sleep
from threading import Thread
import math
 



def degreesToRadians(degrees):
  return degrees * math.pi / 180

def getCoordinateADistanceAlongAngle(distance, angle):
    print("write function")
    return "lat, long"

def distanceInMBetweenEarthCoordinates(lat1, lon1, lat2, lon2):
  earthRadiusKm = 6371

  dLat = degreesToRadians(lat2-lat1)
  dLon = degreesToRadians(lon2-lon1)

  lat1 = degreesToRadians(lat1)
  lat2 = degreesToRadians(lat2)

  a = math.sin(dLat/2) * math.sin(dLat/2) + math.sin(dLon/2) * math.sin(dLon/2) * math.cos(lat1) * math.cos(lat2); 
  c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a)); 
  return earthRadiusKm * c * 1000

def computeNewCoordinate(lat, lon, d_lat, d_lon):
    """
    finds the gps coordinate that is x meters from given coordinate
    """
    earthRadiusKm = 6371
    
    d_lat /= 1000
    d_lon /= 1000
    
    new_lat = lat + (d_lat / earthRadiusKm) * (180/math.pi)
    new_lon = lon + (d_lon / earthRadiusKm) * (180/math.pi) / math.cos(lat * math.pi/180)
    
    return (new_lat, new_lon)

def angleBetweenCoordinates(lat1, lon1, lat2, lon2):
    theta1 = degreesToRadians(lat1)
    theta2 = degreesToRadians(lat2)
    delta1 = degreesToRadians(lat2 - lat1)
    delta2 = degreesToRadians(lon2 - lon1)
    
    y = math.sin(delta2) * math.cos(theta2)
    x = math.cos(theta1) * math.sin(theta2) - math.sin(theta1)*math.cos(theta2)*math.cos(delta2)
    brng = math.atan(y/x)
    brng *= 180/math.pi
    
    brng = (brng + 360) % 360
    
    return brng

def convertDegMinToDecDeg (degMin):
    min = 0.0
    decDeg = 0.0
    
    min = math.fmod(degMin, 100.0)
    
    degMin = int(degMin/100)
    decDeg = degMin + (min/60)
    
    return decDeg

class gps():

    def __init__(self):

        # a slightly higher timeout (GPS modules typically update once a second).
        # These are the defaults you should use for the GPS FeatherWing.
        # For other boards set RX = GPS module TX, and TX = GPS module RX pins.
        #self.uart = busio.UART(board.TX, board.RX, baudrate=9600, timeout=10)
        #

        # for a computer, use the pyserial library for uart access
        import serial
        #self.uart = serial.Serial("/dev/ttyACM1", baudrate=9600, timeout=10)
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

        #pump_thread = Thread(target=self.run)# creates a Thread running an infinite loop pumping server
        #pump_thread.start()

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
            self.updategps()
            
    def readgps(self):
        timestamp = time.monotonic()
        while True:
            data = self.gps.read(64)
            
            if data is not None:
                data_string = ''.join([chr(b) for b in data])
                print(data_string, end="")
                
                if time.monotonic() - timestamp > 5:
                    self.gps.send_command(b'PMTK605')
                    timestamp = time.monotonic()

    def updategps(self, print_info = True):
        self.gps.update()
        
        if print_info:
            return
            print('Fix timestamp: {}/{}/{} {:02}:{:02}:{:02}'.format(
                self.gps.timestamp_utc.tm_mon,   # Grab parts of the time from the
                self.gps.timestamp_utc.tm_mday,  # struct_time object that holds
                self.gps.timestamp_utc.tm_year,  # the fix time.  Note you might
                self.gps.timestamp_utc.tm_hour,  # not get all data like year, day,
                self.gps.timestamp_utc.tm_min,   # month!
                self.gps.timestamp_utc.tm_sec))

            print('Latitude: {0:.8f} degrees'.format(self.gps.latitude))
            print('Longitude: {0:.8f} degrees'.format(self.gps.longitude))
            print('Lat in decDeg:', convertDegMinToDecDeg(self.gps.latitude) )
            print('long in decDeg:', convertDegMinToDecDeg(self.gps.longitude) )
            print('Fix quality: {}'.format(self.gps.fix_quality))
            # Some attributes beyond latitude, longitude and timestamp are optional
            # and might not be present.  Check if they're None before trying to use!
            if gps.satellites is not None:
                print('# satellites: {}'.format(self.gps.satellites))
            if gps.altitude_m is not None:
                print('Altitude: {} meters'.format(self.gps.altitude_m))
            if gps.speed_knots is not None:
                print('Speed: {} knots'.format(self.gps.speed_knots))
            if gps.track_angle_deg is not None:
                print('Track angle: {} degrees'.format(self.gps.track_angle_deg))
            if gps.horizontal_dilution is not None:
                print('Horizontal dilution: {}'.format(self.gps.horizontal_dilution))
            if gps.height_geoid is not None:
                print('Height geo ID: {} meters'.format(self.gps.height_geoid))

            
if __name__ == "__main__":
    # print(convertDegMinToDecDeg(4026.5666))
    # print(convertDegMinToDecDeg(7957.4877))

    
    # print(angleBetweenCoordinates(40.44277, 79.9581, 40.84277, 80.9581))





    # 40267.5664N, 7957.4877W -> +40 26.5666', -79 57.4878'
    # DDMM.MMMM,(N/S),DDDMM.MMMM,(E/W)
    # deal with nesw cases

    # g = gps()
    # for i in range(10):
    #     g.readgps()
    #     sleep(1)
    
 
