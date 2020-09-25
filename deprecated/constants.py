import gzip, pickle


def __getattr__(name):
    global DATA
    return DATA.__getattribute__(name)

def set(name, value):
    setattr(DATA, name, value)
    save()

def save():
    global DATA
    with gzip.open('boatConsts.pickle', 'wb') as file:
        pickle.dump(DATA, file)

def load():
    global DATA
    with gzip.open('boatConsts.pickle', 'rb') as file:
        DATA = pickle.load(file)

class data:
    def __init__(self):
        
        self.SAIL_SERVO_MIN = 2550
        self.SAIL_SERVO_MAX = 6750
        
        self.SAIL_ANGLE_MIN = 0
        self.SAIL_ANGLE_MAX = 90
        

        self.RUDDER_SERVO_MIN= 2500
        self.RUDDER_SERVO_CTR = 4850
        self.RUDDER_SERVO_MAX= 7000

        self.RUDDER_ANGLE_MIN = -45
        self.RUDDER_ANGLE_MAX = 45

        self.SAIL_MIN_ANGLE = 0
        self.SAIL_MAX_ANGLE = 90

        self.SAIL_MIN = 2550
        self.SAIL_MAX = 6750

        self.BAUDRATE = 115200

        self.ARDU_PORT = "/dev/ttyACM0"
        self.ARDU_PORT2 = "/dev/ttyACM1"
        self.RECEIVE_BUFFER_SIZE = 2048

        self.NO_GO_ANGLE = 45

        self.ACCEPTABLE_RANGE = .000005 
        # the maximum acceptable distance between a goal coord and boat gps reading before considering the goal reached
        # 1 degree latitude is approx 69mi/111km ------ .000001 = 1.1m
        # 1 degree longitude is approx 60 * 1852m * cos(latitude)
if __name__ == '__main__':
    DATA = data()
    save()
else:
    try:
        load()
    except:
        print("Failed to load file, continuing with default constants")
        DATA = data()
        save()
    



