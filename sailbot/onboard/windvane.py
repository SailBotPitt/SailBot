from RPi import GPIO
from time import sleep
from threading import Thread, Lock
from queue import Queue
class windVane():

    def __init__(self):

        self.stepsPerRev = 512

        self.clk = 17
        self.dt = 18
    
        self.q = Queue(0)
    
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.clk, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
        GPIO.setup(self.dt, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)

        self.counter = 0
        self.clkLastState = GPIO.input(self.clk)
        pump_thread = Thread(target=self.run)
        pump_thread.start()
        
        pump_thread2 = Thread(target=self.flush_queue)
        pump_thread2.start()
        

    def map(self, x, min1, max1, min2, max2):
        x = min(max(x, min1), max1)
        return min2 + (max2-min2)*((x-min1)/(max1-min1))

    @property
    def angle(self):
        counter = self.counter
        while (counter < 0):
            counter += self.stepsPerRev

        counter = counter % self.stepsPerRev
        return self.map(counter, 0, self.stepsPerRev-1, 0, 359)

    def flush_queue(self):
        while True:
            self.counter += self.q.get()

    def run(self):
        try:
            while True:
                self.update()

        finally:
            GPIO.cleanup()

    def update(self):
        clkState = GPIO.input(self.clk)
        dtState = GPIO.input(self.dt)
        if clkState != self.clkLastState:

            if dtState != clkState:

                self.q.put_nowait(1)
            else:
                self.q.put_nowait(-1)

            self.clkLastState = clkState

if __name__ == '__main__':
    wv = windVane()
    while True:
        sleep(.1)
        print(F"Angle {wv.angle}")
