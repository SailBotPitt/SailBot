from curses import KEY_B2
import constants as c
import logging
import math
import time

try:
    from windvane import windVane
    from GPS import gps
    from compass import compass
    #import GPS
    from camera import camera

    from drivers import driver
    from transceiver import arduino

    from boatMain import boat
except Exception as e:
    print("Failed to import some modules, if this is not a simulation fix this before continuing")
    print(F"Exception raised: {e}")
from datetime import date, datetime
from threading import Thread
from time import sleep



class events(boat):

    def __init__(self):
        self.MESSAGE = None

        print("init")


    def event_NL(self):
        # Nice loop to put in event functions
        #   - sends data about boat
        #   - reads messages and returns bool
        #     if need to stop doing the command (0:no, 1:YES STOP)
        ret = False

        # READ MESSAGE SECTION =========
        self.MESSAGE = self.arduino.readData() #update read
        print("events:", self.MESSAGE)
            # for msg in msgs:
        try:
            for msg in self.MESSAGE:
                ary = msg.split(" ")
                if len(ary) > 0:
                    if ary[0] == 'sail' or ary[0] == "S":
                        ret = True

                    elif ary[0] == 'rudder' or ary[0] == "R":
                        ret = True

                    elif ary[0] == 'mode' and ary[1] == 0:
                        ret = True
        except Exception as e:
            logging.info(f"failed to read command {self.MESSAGE}")
            print(f"message error: {e}")
        
        boat.readMessages(self.MESSAGE) #override message to make faster

        # SEND MESSAGE SECTION =========
        boat.sendData()

        return ret


    def testloop(self, inp):
        t_inp = input("inputs: ")
        t_arr = t_inp.split(" ")
        if inp == "CA":
            self.Collision_Avoidance(t_arr)
        elif inp == "PN":
            self.Percision_Navigation(t_arr)
        elif inp == "E":
            self.Endurance(t_arr)
        elif inp == "SK":
            self.Station_Keeping(t_arr)
        elif inp == "S":
            self.Search(t_arr)
        else:
            print("nah")


    #include in automation event code's main loop:
        #self.readmessages to see if it switches modes or RC commands, returning/break if another mode is true
        #self.sendData() to export data

    #inputs: B1,B2,B3,B4 long/lat
    #arr: [B1x,B1y, etc] (boat.event_arr)
    def Collision_Avoidance(self):
        print("Collision_Avoidance moment")

        while(True):
            #main running
                #blah blah blah


            if self.event_NL(): return  #checks if mode has switched, exits func if so



    #inputs: B1,B2,B3,B4 long/lat
    #arr: [B1x,B1y, etc] (boat.event_arr)
    def Percision_Navigation(self):
        print("Percision_Navigation moment")

        while(True):
            #main running
                #blah blah blah


            if self.event_NL(): return  #checks if mode has switched, exits func if so



    #inputs: B1,B2,B3,B4 long/lat
    #arr: [B1x,B1y, etc] (boat.event_arr)
    def Endurance(self):
        print("Endurance moment")
        
        gps.updategps()
        print(gps.latitude)

        while(True):
            #main running
                #blah blah blah


            if self.event_NL(): return  #checks if mode has switched, exits func if so



    #inputs: B1,B2,B3,B4 long/lat
    #TL,TR,BL,BR
    #arr: [B1x,B1y, etc] (boat.event_arr)
    def Station_Keeping(self):          #Jonah
        print("Station_Keeping moment")
        #Challenge	Goal:
            #To	demonstrate	the	ability	of the boat to remain close to one position and respond to time-based commands.	
        #Description:
            #The boat will enter a 40 x 40m box and attempt to stay inside the box for 5 minutes.
            #It must then exit within 30 seconds to avoid a penalty.
        #Scoring:
            #10	pts	max.
            #2 pts per minute within the box during the 5 minute test (the boat may exit and reenter multiple times).
            #2 pts per minute will be deducted for time within the box after 5½ minutes.	
            #The final score will be reduced by 50% if any RC is preformed from the start of the 5 minute event	until the boat’s final exit.
            #The final score will be to X.X precision
        #assumptions: (based on guidelines)
            #front is upstream


        #see SK_perc_guide() notes on calculating go-to points
        #running:
        #1.) wait till fall behind 80%
        #2.) sail to 90%, until at 90%
        #3.) set sail flat
        #4.) if behind 75%, go to step 2, repeat
        #5.) GTFO (find&sail to best point) after time limit
            #DO NOT JUST DROP SAIL
                #how we won event first time was dropping sail
                #and floating from front to end for total of 5 minute duration travel
        time_perc = 5*60 * (70/100) #time to leave, 5 minute limit * %


        type_arr =   [ 0, 0, 0, 1]
        wanted_arr = [80,75,90,90]
        cool_arr = self.SK_perc_guide(wanted_arr,type_arr,boat.event_arr)
        del type_arr, wanted_arr
            #(0,1)80-line,      (2,3)75-line,
            #(4,5)90-line,      (6,7)90-point,

            #[always auto put on end]:
            #(8,9)Left-line,  (10,11)Right-line
            #(10,11)Back-line
            #(12) mid m line for line check

        start = True#; moving = False
        targ_x = None; targ_y = None
            #gotoGPS just sets it on course, not till it goes there
        #=== main running ===
        #line check is a long process, so instead of checking both
        #DEPRICATED:uses mutual exclusion so not continiously moving to same point (moving bool)
            #gotoGPS just sets it on course, not till it goes there

        #time calc
        start_time = time.time()

        while(True):
            #return checks
            curr_time = time.time()
            if curr_time - start_time >= time_perc:
                #find best point to leave:
                if targ_x == None: targ_x, targ_y = self.cart_perimiter_scan(cool_arr[-7:-1])    #i thought the name sounded cool

                #TODO: when to stop????
                    #using past line depending
                    #using side/back-line that the shortest on intersected at and using SK_line_check with front instead of back
                        #return another var in cart_perimiter_scan, str, ("B","L","R")
                        #or si (var from cart_perimiter_scan)
                    #maybe break to go to another loop after this one, checking it doesnt crash?
                    #[!!!!!]might also just not have too as: as soon as you leave after the timelimit, the event is over and we can switch to manual
                boat.goToGPS(targ_x,targ_y)
                '''
                stall = False
                while(not self.SK_line_check(uhh_idk_something)): stall=True
                '''
            if self.event_NL(): return  #checks if mode has switched, exits func if so


            #beginning set up
            if start: #and not(moving):
                #if not moving and behind 80%
                if self.SK_line_check(cool_arr[0:1], cool_arr[-3:]):
                    start = False; #moving = True
                    boat.goToGPS(cool_arr[6],cool_arr[7])  #go to 90

            #majority sail
            elif not(start): #and not(moving):
                #if not moving and behind 75% and sail back
                if self.SK_line_check(cool_arr[2:3], cool_arr[-3:]):
                    #moving = True
                    boat.goToGPS(cool_arr[6],cool_arr[7])  #go to 90
            
                #if past or at 90% (redundence reduction)
                elif not(self.SK_line_check(cool_arr[4:5], cool_arr[-3:])):
                    #moving = False
                    boat.adjustSail(90)  #loosen sail, do nuthin

    #give %-line of box and other lines(details in SK)
    def SK_perc_guide(self,inp_arr,type_arr,buoy_arr):
        #calc front/back/sides mid point
        #find the parameter lat/long value per percent
        #calc line 75%/80%/90% (give long, if lat) towards front between them
            #input an array of wanted %'s, return array with matching x/y's (in own array, array of arrays)
                #saves on calc times
            #https://www.desmos.com/calculator/wud5cve4bq
                #go with s scaling
                    #1.)find midpoints
                    #2.)between mid1, mid3: perc scale x/y's
                    #works no matter rotation of boat
                #last in inp_arr returns x/y point that is % way of the box
                    #rest is m/b's
                #add m/b of back line, at end of ret_arr
                #add m of front/back midpoint line, at end of ret_arr
                #0: m/b, 1: x/y

        ret_arr = []
        mid_arr=[], m_arr=[], b_arr=[]

        # midpoints ==========================
        #   (12,13,34,24);(front,left,back,right)
        #   02,04,46,26
        a = [0, 2, 0, 4, 4, 6, 2, 6]    #optimizing code with for rather then long ass list
        # 0,1, 2,3, 4,5, 6,7
        for i in range(4):  # 0,1,2,3
            #TODO: remove nice variables: just fill in and make two lines (optimization)
            j1 = a[i*2]  # 0 - 0 - 4 - 2
            k1 = j1 +1  # 1 - 1 - 5 - 3
            j2 = a[(i*2) +1]  # 2 - 4 - 6 - 6  next over in "a"
            k2 = j2 +1  # 3 - 5 - 7 - 7

            p = (buoy_arr[j1] + buoy_arr[j2])/2  # 0+1/2: j1,j2
            mid_arr.append(p)   #p
            mid_arr.append(self.SK_f(p, buoy_arr[j1], buoy_arr[k1], buoy_arr[j2], buoy_arr[k2]))    #p,j1,k1,j2,k2
        
        
        '''# m's and b's ==========================
        #   dont wanna just delete cause dont wanna rewrite if somehow need them
        #   (mid13,mid24; 1,2; 3,4; mid12,mid34)
        m_arr.append(self.SK_m(mid_arr[2], mid_arr[3], mid_arr[6], mid_arr[7]))  # mid13 - mid24 (2,4)  m2
        #m_arr.append(self.SK_m(buoy_arr[0], buoy_arr[1], buoy_arr[2], buoy_arr[3]))  # 1 - 2            front
        m_arr.append(self.SK_m(buoy_arr[4], buoy_arr[5], buoy_arr[6], buoy_arr[7]))  # 3 - 4            back
        #m_arr.append(self.SK_m(mid_arr[0], mid_arr[1], mid_arr[4], mid_arr[5]))  # mid12 - mid34 (1,3)  down center

        b_arr.append(self.SK_v(mid_arr[2], mid_arr[3], mid_arr[6], mid_arr[7]))  # mid13 - mid24 (2,4)
        #b_arr.append(self.SK_v(buoy_arr[0], buoy_arr[1], buoy_arr[2], buoy_arr[3]))  # 1 - 2
        b_arr.append(self.SK_v(buoy_arr[4], buoy_arr[5], buoy_arr[6], buoy_arr[7]))  # 3 - 4
        #b_arr.append(self.SK_v(mid_arr[0], mid_arr[1], mid_arr[4], mid_arr[5]))  # mid12 - mid34 (1,3)


        #front/back mid line for facing use
        m_arr.append(self.SK_m(mid_arr[0],mid_arr[1],mid_arr[4],mid_arr[5]))'''
        m2 = self.SK_m(mid_arr[2], mid_arr[3], mid_arr[6], mid_arr[7])
        
        #newline: s-scale
        for i in range(len(inp_arr)):
            perc = inp_arr[i]/100
            x = perc*mid_arr[0] + (1-perc)*mid_arr[4]
            y = perc*mid_arr[1] + (1-perc)*mid_arr[5]

            if type_arr[i] == 1: #x/y
                ret_arr.append(x)
                ret_arr.append(y)
                continue
            else:
                ret_arr.append( m2[0] )      #m
                ret_arr.append( y-m2[0]*x )  #b

        #sides-line for cart_perimiter_scan
        ret_arr.append( self.SK_m(buoy_arr[0], buoy_arr[1], buoy_arr[4], buoy_arr[5]) ) #m buoy1,buoy3
        ret_arr.append( self.SK_v(buoy_arr[0], buoy_arr[1], buoy_arr[4], buoy_arr[5]) ) #b buoy1,buoy3
        ret_arr.append( self.SK_v(buoy_arr[2], buoy_arr[3], buoy_arr[6], buoy_arr[7]) ) #m buoy2,buoy4
        ret_arr.append( self.SK_v(buoy_arr[2], buoy_arr[3], buoy_arr[6], buoy_arr[7]) ) #b buoy2,buoy4

        #back-line, m of middle-line(linecheck)
        '''ret_arr.append(m_arr[1])
        ret_arr.append(b_arr[1])
        ret_arr.append(m_arr[2])
        #ret_arr.append(b_arr[2])'''
        ret_arr.append( self.SK_m(buoy_arr[4], buoy_arr[5], buoy_arr[6], buoy_arr[7]) )
        ret_arr.append( self.SK_v(buoy_arr[4], buoy_arr[5], buoy_arr[6], buoy_arr[7]) )
        ret_arr.append( self.SK_m(mid_arr[0],mid_arr[1],mid_arr[4],mid_arr[5]) )

        return ret_arr

    #if past line
    def SK_line_check(self,Tarr,Barr):
        #TRUE: BEHIND LINE
        #FALSE: AT OR PAST LINE

        #Ix/y:  current location of boat
        #       boat.gps.longitude, boat.gps.latitude
        #Tarr:  m/b compare line
        #arr:   m/b Back line,

        Fa=0;Fb=0;Fc=0  #temp sets
        #check if sideways =========================
        #input x/y as Buoy x/y's to func
        gps.updategps()
        if abs(Barr[3]) < 1: #Barr is secretly the mid m line shhhhhhh (LOOK AT ME)
            #sideways  -------------------
            #x=(y-b)/m
            Fa= (boat.gps.latitude-Tarr[1])/Tarr[0]
            Fb= boat.gps.longitude
            Fc= (boat.gps.latitude-Barr[1])/Barr[0]
        else:
            #rightways  -------------------
            #y=mx+b
            Fa= Tarr[0]*boat.gps.longitude +Tarr[1]
            Fb= boat.gps.latitude
            Fc= Barr[0]*boat.gps.longitude +Barr[1]

        if Fa > Fc: #upright
            if Fa >= Fb: return False   #past or equal
            else: return True           #behind
        else: #upside down
            if Fa <= Fb: return False   #past or equal
            else: return True           #behind
    
    #find best point of run to leave box
    def cart_perimiter_scan(self,arr):
        #see what mid point closest (Left,Back,Right)
            #cartesian with rand radius
                #find point at perimeter at -45 or 125 (left,right) degrees (LDeg,RDeg line)
                #find m/b of both
                #x = r × cos( θ )
                #y = r × sin( θ );  r=5(doesnt matter)
            #take I() of LDeg,LSide; LDeg,BSide; RDeg,RSide; RDeg,BSide
                #find closest, sail to

        #arr: back-line,left-line,right-line (m,b's) 01,23,45
            #find x,y's of degrees at best run points left and right
            
        gps.updategps()
        lat = boat.gps.latitude, long=boat.gps.longitude
        t = math.pi/180
        o = windVane.position
        lx = 5*math.cos(135 *t+o*t)+lat
        ly = 5*math.sin(135 *t+o*t)+long
        rx = 5*math.cos(-135*t+o*t)+lat
        ry = 5*math.sin(-135*t+o*t)+long
            #into m,b's
        lm = self.SK_m(lx,ly,lat,long)
        lb = self.SK_v(lx,ly,lat,long)
        rm = self.SK_m(rx,ry,lat,long)
        rb = self.SK_v(rx,ry,lat,long)
        #del t,o,lx,ly,rx,ry

            #find intersects of LDeg,LSide; LDeg,BSide; RDeg,RSide; RDeg,BSide
        t_arr=[]
        t_arr.append( self.SK_I(lm,lb,arr[2],arr[3]) )  #x1(0)
        t_arr.append( lm*t_arr[0]+lb )  #y1(1)
        t_arr.append( self.SK_I(lm,lb,arr[0],arr[1]) )  #x2(2)
        t_arr.append( lm*t_arr[2]+lb )  #y2(3)
        t_arr.append( self.SK_I(rm,rb,arr[4],arr[5]) )  #x3(4)
        t_arr.append( rm*t_arr[4]+rb )  #y3(5)
        t_arr.append( self.SK_I(rm,rb,arr[0],arr[1]) )  #x4(6)
        t_arr.append( rm*t_arr[6]+rb )  #y4(7)

            #use distance equation and find closest
        sd = self.SK_d(t_arr[0],t_arr[1],lat,long)
        si = -1
        for i in range(3):
            a = self.SK_d(t_arr[2*(i+1)],t_arr[(2*i)+3],lat,long) #skip 0,1
            if a<sd:    sd=a;si=i
        return t_arr[si+1],t_arr[si+2]


    def SK_f(self,x,a1,b1,a2,b2): return self.SK_m(a1,b1,a2,b2)*x + self.SK_v(a1,b1,a2,b2)  #f(x)=mx+b
    def SK_m(self,a1,b1,a2,b2): return (b2-b1)/(a2-a1)                                      #m: slope between two lines
    def SK_v(self,a1,b1,a2,b2): return b1-(self.SK_m(a1,b1,a2,b2)*a1)                       #b: +y between two lines
    def SK_I(self,M1,V1,M2,V2): return (V2-V1)/(M1-M2)                                      #find x-cord intersect between two lines
    def SK_d(self,a1,b1,a2,b2): return math.sqrt((a2-a1)**2 + (b2-b1)**2)                   #find distance between two points



    #inputs: B1 long/lat, Radius (boat.event_arr)
    def Search(self):
        #make in boatMain along with mode switch, attach buoy coords and radius in ary
        #will need to redo GUI then ://////
        arr = self.SR_pattern(boat.gps.latitude, boat.gps.longitude, boat.event_arr[0], boat.event_arr[1], boat.event_arr[2])

        while(True):
            #main running
                #blah blah blah


            if self.event_NL(): return  #checks if mode has switched, exits func if so
        
    
    def SR_pattern(self, gps_lat, gps_long, buoy_lat, buoy_long, radius):
        #find five coords via search pattern
        #in realtion to current pos and buoy rad center pos

        a = gps_lat - buoy_lat
        b = gps_long - buoy_long
        ang = math.atan(b/a)
        ang *= 180/math.pi

        if(a<0):    ang += 180

        tar_angs = [ang,ang+72,ang-72,ang-(72*3),ang-(72*2)]
        tarx = [0] * 5
        tary = [0] * 5

        for i in range(0,5):
            tarx[i] =  buoy_lat  + radius*math.cos( tar_angs[i] * (math.pi/180) )
            tary[i] =  buoy_long + radius*math.sin( tar_angs[i] * (math.pi/180) )
        
        arr = [tarx,tary]
        return arr

        

if __name__ == "__main__":
    eevee = events()
    while True:
        inp = input("Mode Test: ") # Taking input from user
        eevee.testloop(inp)

