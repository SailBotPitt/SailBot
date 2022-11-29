import boatMain, boatMath
import pygame
import math
from math import pi, sin, cos
from time import sleep
from random import randint

class virtualBoat(boatMain.boat):
    def __init__(self):
        self.currentTarget = None
        self.manualControl = False
        self.cycleTargets = False
        self.compass = virtualCompass(self)
        self.gps = virtualGPS()
        self.windvane = virtualWindvane()
        self.drivers = virtualDriver()
        self.vel = 0

class virtualCompass():

    def __init__(self, parent):
        self.angleVal=0
        self.parent = parent

    @property
    def angle(self):
        return self.angleVal

    @angle.setter
    def angle(self, value):
        self.parent.windvane.angle = value % 360
        self.angleVal = value % 360

class virtualGPS():
    def __init__(self):
        self.latitude =  0
        self.longitude = 0
        self.track_angle_deg = 0

    def updategps(self):
        drawBoat()

class virtualWindvane():
    def __init__(self):
        self.angle = 0
        self.noGoMin = 330
        self.noGoMax = 30

class virtualDriver():
    def __init__(self):
        self.rudder = virtualRudder()
        self.sail = virtualSail()

class virtualSail():
    def __init__(self):
        self.angle = 0

    def set(self, angle):
        self.angle = angle

class virtualRudder():
    def __init__(self):
        self.angle = 0
    
    def set(self, angle):
        self.angle = angle
        drawBoat()

def polarToRect(r, theta, offset=(0,0)):
    x = r * cos(degreesToRadians(theta)) + offset[0]
    y = r * sin(degreesToRadians(theta)) + offset[1]
    return(x,y)

def degreesToRadians(degrees):
  return degrees * pi / 180

def radiansToDegrees(rads):
  return rads * 180 / pi

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

def map(x, min1, max1, min2, max2):
    x = min(max(x, min1), max1)
    return min2 + (max2-min2)*((x-min1)/(max1-min1))

def angleBetweenCoordinates(lat1, long1, lat2, long2):
    dy = lat2 - lat1
    dx = math.cos(pi/180*lat1)*(long2 - long1)
    return radiansToDegrees(math.atan2(dy, dx)) 

def drawBoat():
    global UPDATE, targetLat, targetLong, TIME_STEP

    for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    targetLat -= .0001
                elif event.key == pygame.K_RIGHT:
                    targetLat += .0001
                elif event.key == pygame.K_UP:
                    targetLong -= .0001
                    pass
                elif event.key == pygame.K_DOWN:
                    targetLong += .0001
                    pass

                elif event.key == pygame.K_a:
                    BOAT.drivers.sail.angle = min(BOAT.drivers.sail.angle+5, 90)

                elif event.key == pygame.K_d:
                    BOAT.drivers.sail.angle = max(BOAT.drivers.sail.angle-5, 0)

                elif event.key == pygame.K_q:
                    BOAT.drivers.rudder.angle = max(-45, BOAT.drivers.rudder.angle-5)

                elif event.key == pygame.K_e:
                    BOAT.drivers.rudder.angle = min(45, BOAT.drivers.rudder.angle+5)
                    
                elif event.key == pygame.K_SPACE:
                    UPDATE = not UPDATE

                elif event.key == pygame.K_MINUS:
                    TIME_STEP *= 1.1

                elif event.key == pygame.K_PLUS:
                    TIME_STEP /= 1.1


    size = (400,400)
    rect_filled = pygame.Surface(size)
    pygame.draw.rect(rect_filled, BLACK, rect_filled.get_rect())   
    screen.blit(rect_filled, (0,0))

    size = (100, 100)
    boat = pygame.Surface(size)


    


    # Hull
    coords = polarToRect(25, (180-BOAT.compass.angle + 15) % 360, (50,50))
    pygame.draw.line(boat, RED, (50, 50), coords)

    coords = polarToRect(25, (180-BOAT.compass.angle - 15) % 360, (50,50))
    pygame.draw.line(boat, RED, (50, 50), coords)

    #Rudder
    coords = polarToRect(25, (180-BOAT.compass.angle) % 360, (50,50))
    coords2 = polarToRect(10, -BOAT.drivers.rudder.angle + (180-BOAT.compass.angle) % 360, coords)
    pygame.draw.line(boat, WHITE, coords, coords2)

    #Sail
    sailAngle = (180-BOAT.compass.angle) + BOAT.drivers.sail.angle if BOAT.compass.angle < 180 else (180-BOAT.compass.angle) - BOAT.drivers.sail.angle
    coords = polarToRect(10, sailAngle, (50,50))
    pygame.draw.line(boat, WHITE, (50,50), coords)

    drawX = map(BOAT.gps.latitude, 40.443, 40.444, 25, 375)
    drawY = map(BOAT.gps.longitude, -79.9585, -79.9575, 25, 375)
    screen.blit(boat, (drawX - 50, drawY - 50))

    circle_filled = pygame.Surface((25,25))
    pygame.draw.circle(circle_filled, WHITE, (10, 10), 10)
    drawX = map(ghostPoint[0], 40.443, 40.444, 25, 375)
    drawY = map(ghostPoint[1], -79.9585, -79.9575, 25, 375)
    screen.blit(circle_filled, (drawX - 10, drawY - 10))

    circle_filled = pygame.Surface((25,25))
    pygame.draw.circle(circle_filled, RED, (10, 10), 10)
    drawX = map(targetLat, 40.443, 40.444, 25, 375)
    drawY = map(targetLong, -79.9585, -79.9575, 25, 375)
    screen.blit(circle_filled, (drawX - 10, drawY - 10))

    font = pygame.font.Font('freesansbold.ttf', 16)
    white = (255, 255, 255)
    text = font.render(F'{"Paused " if not UPDATE else ""} Sail: {BOAT.drivers.sail.angle}, Rudder: {BOAT.drivers.rudder.angle}', True, white)
    textRect = text.get_rect()
    textRect.center = (200, 350)
    screen.blit(text, textRect)


    pygame.display.update()

    if UPDATE:
        dx, dy = polarToRect(BOAT.vel, (180-BOAT.compass.angle) % 360)
        nx, ny = computeNewCoordinate(BOAT.gps.latitude, BOAT.gps.longitude, -dx, -dy)

        windDir = BOAT.windvane.angle
        if windDir > 180:
            windDir = 180 - (windDir - 180)
        optAngle = max(min(windDir / 2, 90), 3)
        #BOAT.drivers.sail.set(optAngle)

        if BOAT.windvane.angle < BOAT.windvane.noGoMin and BOAT.windvane.angle > BOAT.windvane.noGoMax:

            BOAT.vel = min(.05, BOAT.vel + .001) * max((1 -  abs(BOAT.drivers.sail.angle - optAngle)/3000), 0)
        else:
            BOAT.vel = max(BOAT.vel - .0001, 0) * max((1 -  abs(BOAT.drivers.sail.angle - optAngle)/3000), 0)

        BOAT.gps.latitude = nx
        BOAT.gps.longitude = ny

        if BOAT.drivers.rudder.angle > 5:
            BOAT.compass.angle -= BOAT.drivers.rudder.angle / 100

        if BOAT.drivers.rudder.angle < -5:
            BOAT.compass.angle -= BOAT.drivers.rudder.angle / 100


    

    sleep(TIME_STEP)




if __name__ == '__main__':
    TIME_STEP = .005
    UPDATE = False
    BOAT = virtualBoat()
    pygame.init()
    screen = pygame.display.set_mode((400, 400))
    WHITE = pygame.Color(255, 255, 255)
    RED = pygame.Color(255, 0, 0) 
    BLACK = pygame.Color(0, 0, 0) 
    BOAT.gps.latitude, BOAT.gps.longitude = (40.4433, -79.9580000)
    targetLat, targetLong = (40.44368167, -79.9580000)
    ghostPoint = (targetLat, targetLong)
    pygame.key.set_repeat(500,200)
    BOAT.currentTarget = (targetLat, targetLong)
    
    while True:
        if not BOAT.manualControl:
            if BOAT.currentTarget == None:
                BOAT.currentTarget = ghostPoint

            BOAT.goToGPS(BOAT.currentTarget[0], BOAT.currentTarget[1])
            ghostPoint = (targetLat, targetLong)

        else:
            drawBoat()

    
    # while True:
    #     drawBoat()
    #     print(BOAT.compass.angle + boatMath.angleToPoint(BOAT.compass.angle, BOAT.gps.latitude, BOAT.gps.longitude, targetLat, targetLong))
        



