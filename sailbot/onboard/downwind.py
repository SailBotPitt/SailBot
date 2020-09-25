from drivers import driver
from windvane import windVane

def map(x, min1, max1, min2, max2):
        x = min(max(x, min1), max1)
        return min2 + (max2-min2)*((x-min1)/(max1-min1))
    
def downwind ():
    wv = windVane()
    #current = wv.angle
    #drivers = driver(sailAuto = False)
    #print (drivers.sail.autoAdjust)
    while True: #current != 180:
       # print('n')
       #pos = 45*(180-current)/180 #map(current, 0, 360, -45, 45)
       #print(pos, current)
       #drivers.rudder.set(pos)
       current = wv.angle
       print(wv.angle)
        
downwind()