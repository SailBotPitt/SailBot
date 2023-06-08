"""
Math functions useful for sailbotting
"""
import math

def degreesToRadians(degrees):
  return degrees * math.pi / 180

def radiansToDegrees(rads):
  return rads * 180 / math.pi

def getCoordinateADistanceAlongAngle(distance, angle):
    print("write function")
    return "lat, long"

def distanceInMBetweenEarthCoordinates(lat1, lon1, lat2, lon2):
  earthRadiusKm = 6371

  dLat = degreesToRadians(lat2-lat1)
  dLon = degreesToRadians(lon2-lon1)

  lat1 = degreesToRadians(lat1)
  lat2 = degreesToRadians(lat2)

  a = math.sin(dLat/2) * math.sin(dLat/2) + math.sin(dLon/2) * math.sin(dLon/2) * math.cos(lat1) * math.cos(lat2)
  c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
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
    #angle (relative to north?) from lat/long1 to lat/long2
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


def calculate_compass_angle(pt1, pt2):
    """Calculates the angle between two gps points"""
    delta_lon = pt2.lon - pt1.lon
    y = math.sin(math.radians(delta_lon)) * math.cos(math.radians(pt2.lat))
    x = math.cos(math.radians(pt1.lat)) * math.sin(math.radians(pt2.lat)) - math.sin(
        math.radians(pt1.lat)) * math.cos(math.radians(pt2.lat)) * math.cos(math.radians(delta_lon))
    angle = math.atan2(y, x)
    angle_deg = math.degrees(angle)
    compass_angle = (angle_deg + 360) % 360
    return compass_angle

def angleToPoint(heading, lat1, long1, lat2, long2):
    phi = math.atan2(long1-long2, lat1-lat2)

    return (360 - (radiansToDegrees(phi) + heading + 180)) % 360

def convertDegMinToDecDeg (degMin):
    min = 0.0
    decDeg = 0.0

    min = math.fmod(degMin, 100.0)

    degMin = int(degMin/100)
    decDeg = degMin + (min/60)

    return decDeg

def convertWindAngle (windAngle):
    # This assumes windAngle is measured from 0 to 360 degrees
    if (windAngle >= 0 and windAngle <= 180):
        tempAngle = (180 - windAngle)*-1
    else:
        tempAngle = windAngle - 180

    # This also assumes the compass is measured from 0 to 360 degrees
    compassAngle = boatCompass + tempAngle # we would need to get the boat compass reading from the compass

    return (compassAngle % 360)