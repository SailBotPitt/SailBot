from messages_pb2 import *
import constants as C

class arduino:

	def __init__(self, port_num):
		self.ser1 = serial.Serial('COM'+port_num, C.BAUDRATE) 


	def send(self, data):
		self.ser1.write(str(data).encode())

	def read(self):
		message = self.ser1.readline()

		pbm = BaseToBoat.parseFromString(message)

		case = pbm.WhichOneOf('command')
		if case == 'rudder' :
			result = ["rudder " + pbm.RudderCommand.position]
		elif case == 'sail' :
			result = ["sail " + pbm.SailCommand.position]
		elif case == 'skipper' :
			result = ["sail " + pbm.SkipperCommand.sailPosition, "rudder " + pbm._SkipperCommand.rudderPosition]
		elif case == 'mode' :
			result = ["mode " + pbm.Mode.mode]

		return result

