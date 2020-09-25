import math
def convertDegMinToDecDeg (degMin):
    min = 0.0
    decDeg = 0.0
    
    min = math.fmod(degMin, 100.0)
    
    degMin = int(degMin/100)
    decDeg = degMin + (min/60)
    
    return decDeg

print(convertDegMinToDecDeg(40267.6132))
print(convertDegMinToDecDeg(7957.4614))
