"""
calibrates and default values for Odrive and handles interfacing between Odrive and python code
"""

import odrive
import odrive.utils as ut
try:
    import constants as c
except:
    import sailbot.constants as c
from time import sleep
import sys
import traceback


class Odrive():
    def __init__(self, calibrate = False):
        print("Start")
        self.od = odrive.find_any()
        self.setConstants()
        

        if calibrate:
            print("calibrating")
            self.reboot()
            self.axis0.requested_state = 3
            self.axis1.requested_state = 3
            sleep(15)
            ut.dump_errors(self.od)
            #CALIBRATION = 3, can be avoided, see how to in list of axisStates
            
            # self.axis0.motor.config.pre_calibrated = False
            # sleep(.1)
            # self.axis0.requested_state = 4
            # sleep(10)
            # ut.dump_errors(self.od)
            # self.axis0.motor.config.pre_calibrated = True
            # try:
            #     self.od.save_configuration()
            # except:
            #     #an exception will be thrown, this is expected
            #     pass

            # self.od = odrive.find_any()
            # self.setConstants()
            
            # self.axis0.requested_state = 2
            # ut.dump_errors(self.od)
            # sleep(1)
            # self.axis0.requested_state = 7
            # sleep(15)

        

        #self.reboot()

        self.axis0.requested_state = 8
        self.axis1.requested_state = 8 
        ut.dump_errors(self.od)
        sleep(.1)

    def reboot(self):
        try:
            self.od.reboot()
            pass
        except:
            #error is expected
            pass
        sleep(2)
        self.od = odrive.find_any()
        self.setConstants()

    def setConstants(self):
        self.KVRating = c.config['ODRIVE']['motorKV']
        #self.od.config.brake_resistance = c.config['CONSTANTS']['odrivebreakresistor']

        self.axis0 = self.od.axis0
        self.mo0 = self.axis0.motor
        self.enc0 = self.axis0.encoder

        self.axis0.controller.config.enable_overspeed_error = False
        self.enc0.config.cpr = c.config['ODRIVE']['odriveEncoderCPR0']
        self.od.axis0.motor.config.pole_pairs = c.config['ODRIVE']['odrivepolepairs0']
        self.od.axis0.motor.config.torque_constant = 1 # read the getting started guide on this, to be changed later
        self.od.axis0.motor.config.motor_type = 0
        
        self.axis0.controller.config.vel_limit = c.config['ODRIVE']['velLimit0']
        self.axis0.controller.config.pos_gain = c.config['ODRIVE']['posGain0']
        self.axis0.controller.config.vel_gain = c.config['ODRIVE']['velGain0']
        self.axis0.controller.config.vel_integrator_gain = c.config['ODRIVE']['velIntegratorGain0']
        self.current0 = c.config['ODRIVE']['currentLimit']
        
        

        self.axis1 = self.od.axis1
        self.mo1 = self.axis1.motor
        self.enc1 = self.axis1.encoder

        self.axis1.controller.config.enable_overspeed_error = False
        self.enc1.config.cpr = c.config['ODRIVE']['odriveEncoderCPR1']
        self.od.axis1.motor.config.pole_pairs = c.config['ODRIVE']['odrivepolepairs1']
        self.od.axis1.motor.config.torque_constant = 1 # read the getting started guide on this, to be changed later
        self.od.axis1.motor.config.motor_type = 0
        
        self.axis1.controller.config.vel_limit = c.config['ODRIVE']['velLimit1']
        self.axis1.controller.config.pos_gain = c.config['ODRIVE']['posGain1']
        self.axis1.controller.config.vel_gain = c.config['ODRIVE']['velGain1']
        self.axis1.controller.config.vel_integrator_gain = c.config['ODRIVE']['velIntegratorGain1']
        self.current1 = c.config['ODRIVE']['currentLimit']
        
        



    @property
    def pos(self):
        return (self.pos0, self.pos1)

    @pos.setter
    def pos(self, value):
        # sets both motor's position to value
        self.pos0 = value
        self.pos1 = value

    def posSet(self, axis, value):
        # sets 'axis' motor to value
        # 'axis' is axis0 or axis1 object
        #print(F"odrive posSet {value}")
        if axis == self.axis0:
            try:
                self.axis0.controller.input_pos = value
            except Exception as e:
                print(F"Error setting axis0 to {value}")
            #print(F"set axis 0 to {value}")
        elif axis == self.axis1:
            try:
                self.axis1.controller.input_pos = value
            except Exception as e:
                print(F"Error setting axis1 to {value}")
            #print(F"set axis 1 to {value}")

    @property
    def vel(self):
        return (self.vel0, self.vel1)

    @vel.setter
    def vel(self, value):
        self.vel0 = value
        self.vel1 = value

    def velSet(self, axis, value):
        if axis == self.axis0:
            self.vel0 = value
        elif axis == self.axis1:
            self.vel1 = value

    @property
    def torque(self):
        #this will change current drawn
        return 8.27 * getDrawnCurrent / self.KVRating

    def torqueSet(self, axis, value):
        if axis == self.axis0:
            self.torque0 = value
        elif axis == self.axis1:
            self.torque1 = value

    @property
    def current(self):
        return (self.current0, self.current1)

    @current.setter
    def current(self, value):
        self.current0 = value
        self.current1 = value

    def currentSet(self, axis, value):
        #this will change torque!!!
        if axis == self.axis0:
            self.current0 = value
        elif axis == self.axis1:
            self.current1 = value

    def getDemandedCurrent(self):
        return (self.getDemandedCurrent0(), self.getDemandedCurrent1())
        
    @property
    def pos0(self):
        return self.axis0.encoder.pos_estimate

    @pos0.setter
    def pos0(self, value):
        self.axis0.controller.input_pos = value

    @property
    def vel0(self):
        return self.axis0.controller.config.vel_limit
        #return self.axis0.controller.input_vel

    @vel0.setter
    def vel0(self, value):
        self.axis0.controller.config.vel_limit = value

    @property
    def torque0(self):
        #this will change current drawn
        return self.axis0.controller.input_torque

    @torque0.setter
    def torque0(self, value):
        self.axis0.controller.input_torque = value

    @property
    def current0(self):
        return self.mo0.config.current_lim

    @current0.setter
    def current0(self, value):
        #this will change torque!!!
        #self.torque = (8.27 * value / self.KVRAting)
        #print(F"Warning: Changing the current limit will affect the torque")
        if float(value) > 65:
            raise Exception("Motor current limit should not be raised this high without verifying the motor can handle it")
        self.mo0.config.current_lim = value

    def getDemandedCurrent0(self):
        return self.axis0.motor.current_control.Iq_setpoint



    @property
    def pos1(self):
        return self.axis1.encoder.pos_estimate

    @pos1.setter
    def pos1(self, value):
        self.axis1.controller.input_pos = value

    @property
    def vel1(self):
        return self.axis0.controller.config.vel_limit

    @vel1.setter
    def vel1(self, value):
        self.axis1.controller.config.vel_limit =  value

    @property
    def torque1(self):
        #this will change current drawn
        return 8.27 * getDrawnCurrent / self.KVRating

    @torque1.setter
    def torque1(self, value):
        self.axis1.controller.input_torque = value

    @property
    def current1(self):
        return self.mo1.config.current_lim

    @current1.setter
    def current1(self, value):
        #this will change torque!!!
        #self.torque = (8.27 * value / self.KVRAting)
        #print(F"Warning: Changing the current limit will affect the torque")
        if float(value) > 65:
            raise Exception("Motor current limit should not be raised this high without verifying the motor can handle it")
        self.mo1.config.current_lim = value

    def getDemandedCurrent1(self):
        return self.axis1.motor.current_control.Iq_setpoint

def printCurrent(drv):
    while True:
        print(abs(drv.getDemandedCurrent0()))
        sleep(.5)

if __name__ == '__main__':
    import threading
    #print(c.config.keys())
    #print(sys.argv)
    print("Run as sudo if on rasp pi, will otherwise not work")
    if len(sys.argv) < 2 or sys.argv[1] != '0':
        try:
            #odrive.find_any().reboot()
            #sleep(2)
            pass
        except:
            pass
        
        
        drv = Odrive(calibrate=False)
    
        

    else:
        drv = Odrive()

    
    # for i in range(1):
    #     drv.pos0 = 5
    #     drv.pos1 = 5
    #     sleep(3)
    #     drv.pos0 = 0
    #     drv.pos1 = 0
    #     sleep(3)
    # ut.dump_errors(drv.od)

    #drv.reboot()




    # from threading import Thread
    # from time import sleep
    # pump_thread = Thread(target=printCurrent, args=[drv])
    # pump_thread.start()
    p0_offset = 0
    p1_offset = 0
    while True:
        try:
            while True:
                string = input("  > Enter Input:")

                if string == "calibrate":
                    # print("rebooting")
                    # drv.reboot()
                    drv = Odrive(calibrate=True)

                elif string.startswith("pi0") or string.startswith("PI0"):
                    if len(string.split(' ')) == 1:
                        print(drv.axis0.controller.config.pos_gain)
                    else:
                        val = float(string.split(' ')[1])
                        print(drv.axis0.controller.config.pos_gain, "->", val)
                        drv.axis0.controller.config.pos_gain = val

                elif string.startswith("pi1") or string.startswith("PI1"):
                    if len(string.split(' ')) == 1:
                        print(drv.axis1.controller.config.pos_gain)
                    else:
                        val = float(string.split(' ')[1])
                        print(drv.axis1.controller.config.pos_gain, "->", val)
                        drv.axis1.controller.config.pos_gain = val
                
                elif string.lower().startswith("p0"):
                    if len(string.split(' ')) == 1:
                        print(drv.pos0 + p0_offset)
                    else:
                        val = float(string.split(' ')[1])
                        print(drv.pos0 + p0_offset, "->", val)
                        drv.pos0 = val + p0_offset

                elif string.lower().startswith("pr"):
                    if len(string.split(' ')) == 1:
                        print(drv.pos0 + p0_offset)
                    else:
                        val = float(string.split(' ')[1])
                        print(drv.pos0 + p0_offset, "->", val, "(resetting to 0 in 1 sec)")
                        drv.pos0 = val + p0_offset
                        lastRudderMoveVal = val

                        def rudderReset(*args):
                            sleep(1)
                            drv.pos0 = p0_offset

                        threading.Thread(target=rudderReset).start()

                elif string.lower().startswith("z"):
                    print(drv.pos0 + p0_offset, "->", lastRudderMoveVal, "(resetting to 0 in 1 sec)")
                    drv.pos0 = lastRudderMoveVal + p0_offset

                    def rudderReset(*args):
                            sleep(1)
                            drv.pos0 = p0_offset

                    threading.Thread(target=rudderReset).start()

                elif string.lower().startswith("ps"):
                    if len(string.split(' ')) == 1:
                        print(drv.pos1 + p1_offset)
                    else:
                        val = float(string.split(' ')[1])
                        print(drv.pos1 + p1_offset, "->", val)
                        drv.pos1 = val + p1_offset

                elif string.lower().startswith("or"):
                    # val = float(string.split(' ')[1])
                    p0_offset = drv.pos0 + p0_offset
                    print("offset is", p0_offset)

                elif string.lower().startswith("os"):
                    # val = float(string.split(' ')[1])
                    p1_offset = drv.pos0 + p0_offset
                    print("offset is", p0_offset)

                elif string[0] == "v" or string[0] == 'V':
                    if len(string) == 1:
                        print(drv.vel)
                    else:
                        val = float(string[1:])
                        print(drv.vel, "->", val)
                        drv.vel = val

                elif string[0] == "c" or string[0] == 'C':
                    if len(string) == 1:
                        print(F"{drv.getDemandedCurrent()} [{drv.current}]")
                    else:
                        val = float(string[1:])
                        print(drv.current, "->", val)
                        drv.current = val

                elif string.lower().startswith("d0"):
                    if len(string.split(' ')) == 1:
                        print(drv.axis0.controller.config.vel_integrator_gain)
                    else:
                        val = float(string.split(' ')[1])
                        print(drv.axis0.controller.config.vel_integrator_gain, "->", val)
                        drv.axis0.controller.config.vel_integrator_gain = val

                elif string.lower().startswith("d1"):
                    if len(string.split(' ')) == 1:
                        print(drv.axis1.controller.config.vel_integrator_gain)
                    else:
                        val = float(string.split(' ')[1])
                        print(drv.axis1.controller.config.vel_integrator_gain, "->", val)
                        drv.axis1.controller.config.vel_integrator_gain = val

                elif string.lower().startswith("i0"):
                    if len(string.split(' ')) == 1:
                        print(drv.axis0.controller.config.vel_gain)
                    else:
                        val = float(string.split(' ')[1])
                        print(drv.axis0.controller.config.vel_gain, "->", val)
                        drv.axis0.controller.config.vel_gain = val

                elif string.lower().startswith("i1"):
                    if len(string.split(' ')) == 1:
                        print(drv.axis1.controller.config.vel_gain)
                    else:
                        val = float(string.split(' ')[1])
                        print(drv.axis1.controller.config.vel_gain, "->", val)
                        drv.axis1.controller.config.vel_gain = val

                elif string == "reset":
                    print("rebooting")
                    drv.reboot()
                    drv = Odrive(calibrate=False)

                

                elif string[0] == "e" or string[0] == 'E':
                    ut.dump_errors(drv.od)


                


                else:
                    val = float(string)
                    drv.pos0 = val
                    drv.pos1 = val
        except KeyboardInterrupt as e:
            ut.dump_errors(drv.od)
            break
        except Exception as e:
            print(F"Error: {e}")
            print(traceback.format_exc())

    print('done')
       
