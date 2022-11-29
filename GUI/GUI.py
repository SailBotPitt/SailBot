from re import A
import sys
from PyQt5.QtWidgets import *
from PyQt5 import QtCore

from PyQt5.QtCore import *  # pyqtSlot, QTimer, Qt,
import PyQt5.QtGui as QtGui
from PyQt5.QtGui import QPainter, QColor, QPen, QKeySequence
import keyboard

import PodSixNet
from PodSixNet.Connection import connection, ConnectionListener
from PodSixNet.Channel import Channel
from PodSixNet.Server import Server

from threading import Thread
from time import sleep

from inputs import get_gamepad

import math

import serial

#TODO:
#add mode section along with fields for needed inputted variables (ex buoy coords for search)
#add subsections

def degreesToRadians(degrees):
    return degrees * math.pi / 180;


def distanceInMBetweenEarthCoordinates(lat1, lon1, lat2, lon2):
    earthRadiusKm = 6371;

    dLat = degreesToRadians(lat2 - lat1);
    dLon = degreesToRadians(lon2 - lon1);

    lat1 = degreesToRadians(lat1);
    lat2 = degreesToRadians(lat2);

    a = math.sin(dLat / 2) * math.sin(dLat / 2) + math.sin(dLon / 2) * math.sin(dLon / 2) * math.cos(lat1) * math.cos(lat2);
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a));
    return earthRadiusKm * c * 1000;


def computeNewCoordinate(lat, lon, d_lat, d_lon):
    """
    finds the gps coordinate that is x meters from given coordinate
    """
    earthRadiusKm = 6371;

    d_lat /= 1000
    d_lon /= 1000

    new_lat = lat + (d_lat / earthRadiusKm) * (180 / math.pi)
    new_lon = lon + (d_lon / earthRadiusKm) * (180 / math.pi) / math.cos(lat * math.pi / 180)

    return (new_lat, new_lon)


def angleBetweenCoordinates(lat1, lon1, lat2, lon2):
    theta1 = degreesToRadians(lat1)
    theta2 = degreesToRadians(lat2)
    delta1 = degreesToRadians(lat2 - lat1)
    delta2 = degreesToRadians(lon2 - lon1)

    y = math.sin(delta2) * math.cos(theta2)
    x = math.cos(theta1) * math.sin(theta2) - math.sin(theta1) * math.cos(theta2) * math.cos(delta2)
    brng = math.atan(y / x)
    brng *= 180 / math.pi

    brng = (brng + 360) % 360

    return brng


class ClientChannel(Channel):

    def Network(self, data):  # Whenever the client does connection.Send(mydata), the Network() method will be called.
        print(str(data))
        BOAT_DATA.message = str(data)

        if data['action'] == 'quit':
            close_app()

        # if the action is an attribute of BOAT_DATA then set the value of that attribute to the value in data
        elif hasattr(BOAT_DATA, data['action']):
            setattr(BOAT_DATA, data['action'], data['value'])

        # refreshes the screen with new boat data
        if DATA_REFRESH:
            DATA_REFRESH()


class MyServer(Server):
    """
	The GUI is setup to act as a server, the client is the boat
	"""
    channelClass = ClientChannel

    # Set channelClass to the channel class created above.

    def __init__(self, *args, **kwargs):
        Server.__init__(self, *args, **kwargs)
        self.channels = []  # clients (boats) connected to the server

    # the channels is an array due to potential disconnects and reconects of the boat, this will store them all

    def Connected(self, channel, addr):
        print(channel, "Connected")
        self.channels.append(channel)

    def send_data(self, data):
        if ARDUINO:
            ARDUINO.send(data)
        for client in self.channels:
            client.Send(data)

    def send_once(self, data, index=0):
        if ARDUINO:
            ARDUINO.send(data)
        if len(self.channels) > 0:
            self.channels[-1].Send(data)
# sends data to most recently connected client (last element in the array)


def server_update():
    global RUN_THREAD, DATA_REFRESH, BOAT_DATA, ARDUINO  # global boolean var to stop the tread from anywhere
    while RUN_THREAD:  # repeatedly pumps the server

        if ARDUINO:
            message = str(ARDUINO.read())[2:-5]
            if message.split(' ', 1)[0] == 'cfg':
                BOAT_DATA.config.append(message.split(' ', 1)[1])
                BOAT_DATA.configChanged = True
                if DATA_REFRESH:
                    DATA_REFRESH()
            
            elif message.split(' ', 1)[0] == 'DATA:':
                datalist = message.split(' ', 1)[1].split(', ')
                for i in range(8):
                    if datalist[i] == "N/a":
                        datalist[i] = None

                BOAT_DATA.gps = ( int(datalist[0]), int(datalist[1]) )  #should this be a float?
                BOAT_DATA.rudder_pos = datalist[2]
                BOAT_DATA.sail_pos = datalist[3]
                BOAT_DATA.boat_orient = datalist[4]
                BOAT_DATA.wind_speed = datalist[5]
                BOAT_DATA.wind_dir = datalist[6]
                BOAT_DATA.battery = datalist[7]

                if DATA_REFRESH:
                    DATA_REFRESH()

            elif message:
                print(message.split(' ', 1)[0])
                BOAT_DATA.message = message

                if DATA_REFRESH:
                    DATA_REFRESH()

        if SERVER:
            SERVER.Pump()  # removing Network data from buffer and running the Network function of ClientChannel object

        sleep(.1)  # saves resources by waiting a fraction of a second between pumps


def ArrLineEdit(obj, r, names):
    arr = []
    for y in range(math.ceil(r/2)):
        for x in range(2):
            if y*2+x >= r: continue

            #print("names:", y*2+x)
            consl_temp = QLineEdit()

            label_temp = QLabel(names[y*2+x])
            label_temp.setFrameStyle(QFrame.Panel)
            label_temp.setMaximumHeight(40)

            obj.layout.addWidget(label_temp, y,x*2)
            obj.layout.addWidget(consl_temp, y,x*2+1)
            #print("label:", y,x*2)
            #print("consl:", y,x*2+1)
            arr.append(consl_temp)
    return arr


class boat_data:
    """
	Stores all of the boat information in one object
	"""

    def __init__(self):
        self.gps = (0, 0)   #should this be a float?
        self.gps_points = [(.01, .01), (0, -.01)]
        self.rudder_pos = None
        self.sail_pos = None
        self.boat_orient = None
        self.wind_speed = None
        self.wind_dir = None
        self.battery = None

        self.message = None

        self.config = []
        self.configChanged = False


class mainWindow(QMainWindow):
    """
	Main window od the GUI, only has one child widget (tab widget)
	"""

    def __init__(self):
        super(mainWindow, self).__init__()

        self.setWindowTitle('Sailbot')
        self.resize(800, 600)

        self.tabs = tabWidget(self)
        self.setCentralWidget(self.tabs)

        self.show()


class tabWidget(QWidget):
    def __init__(self, parent):
        super(QWidget, self).__init__(parent)  # calls QWidget.init (parent class of tabWidget)
        self.layout = QVBoxLayout(self)  # lines items up vertically, not relevent as theres only one item (tabWidget)
        self.setFont(QtGui.QFont('SansSerif', 13))

        # Initialize tab screen
        self.tabs = QTabWidget()

        # consoles
        self.consolelast = ["", ""]  # console, console2
        self.KeyCmd_up    = QShortcut(QKeySequence('up')   , self).activated.connect(lambda: self.ConsoleFancy())
        self.KeyCmd_enter = QShortcut(QKeySequence('Return'), self).activated.connect(lambda: self.commit_message())

        # init tabs
        self.tab1()  # main
        self.tab2()  #previous mode selection
        self.tab3()  # manual
        self.tab4()  # config

        # used for animation of wind
        self.paint_counter = 0
        self.scale = 6000

        # consoles
        # self.consolelast = ["",""]

        # Add tabs to widget
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

    def tab1(self):
        self.tab1 = QWidget()
        self.tabs.addTab(self.tab1, "Boat Info")

        self.tab1.layout = QGridLayout(self)

        # Mode viewer - TT  ==================================

        # self.ttGroupBox = QGroupBox()
        # self.ttGroupBox.layout = QHBoxLayout()

        self.ttlabel = QLabel("Curr Mode: Manual")
        self.ttlabel.setFrameStyle(QFrame.Panel)
        # self.ttlabel.setStyleSheet("border: 1px solid blue;")
        self.ttlabel.setMaximumHeight(40)
        # self.ttlabel.setMaximumWidth(175)

        self.tab1.layout.addWidget(self.ttlabel, 0, 0, 1, 2)

        # Console Box - TL  ===================================
        self.topLeftGroupBox = QGroupBox("Data")
        self.topLeftGroupBox.layout = QVBoxLayout()

        self.gps_lbl = QLabel()
        self.rudder_pos_lbl = QLabel()
        self.sail_pos_lbl = QLabel()
        self.boat_orient_lbl = QLabel()
        self.wind_speed_lbl = QLabel()
        self.wind_dir_lbl = QLabel()
        self.battery_lbl = QLabel()

        self.topLeftGroupBox.layout.addWidget(self.gps_lbl)
        self.topLeftGroupBox.layout.addWidget(self.rudder_pos_lbl)
        self.topLeftGroupBox.layout.addWidget(self.sail_pos_lbl)
        self.topLeftGroupBox.layout.addWidget(self.boat_orient_lbl)
        self.topLeftGroupBox.layout.addWidget(self.wind_speed_lbl)
        self.topLeftGroupBox.layout.addWidget(self.wind_dir_lbl)
        self.topLeftGroupBox.layout.addWidget(self.battery_lbl)

        self.topLeftGroupBox.layout.addStretch(1)
        self.topLeftGroupBox.setLayout(self.topLeftGroupBox.layout)
        self.tab1.layout.addWidget(self.topLeftGroupBox, 1, 0, 1, 2)

        # Console Box - TR  ===================================
        self.topRightGroupBox = QGroupBox("Map")
        self.topRightGroupBox.layout = QGridLayout()

        # img and img_lbl is for the picture of the boat and wind
        self.img = QtGui.QPixmap(300, 300)  # drawing surface
        self.img_lbl = QLabel()  # label to hold the drawing surface
        self.img_lbl.setPixmap(self.img)
        # self.img_lbl.setFixedSize(400, 300)

        self.incBtn = QPushButton('+')
        self.incBtn.setMaximumWidth(125)
        self.incBtn.clicked.connect(self.increase_scale)

        self.decBtn = QPushButton('-')
        self.decBtn.setMaximumWidth(125)
        self.decBtn.clicked.connect(self.decrease_scale)

        self.topRightGroupBox.layout.addWidget(self.img_lbl, 0, 0, 1, 2)
        self.topRightGroupBox.layout.addWidget(self.incBtn, 1, 0)
        self.topRightGroupBox.layout.addWidget(self.decBtn, 1, 1)

        self.topRightGroupBox.layout.setColumnStretch(0, 0)
        self.topRightGroupBox.setLayout(self.topRightGroupBox.layout)
        self.tab1.layout.addWidget(self.topRightGroupBox, 1, 2, 1, 2)

        # Console Box - BL  ===================================
        self.botLeftGroupBox = QGroupBox("Console")
        self.botLeftGroupBox.layout = QVBoxLayout()

        self.message_box = QTextEdit()  # stores all recived data

        self.message_box.setReadOnly(True)
        self.message_box.setLineWrapMode(QTextEdit.NoWrap)
        self.message_box.setMinimumHeight(145)
        # self.message_box.setEnabled(False)

        self.console = QLineEdit()  # entry box for sending messages to boat
        #self.console.editingFinished.connect(lambda: self.commit_message(self.console))

        global DATA_REFRESH
        DATA_REFRESH = self.data_refresh
        self.data_refresh()

        self.botLeftGroupBox.layout.addWidget(self.message_box)
        self.botLeftGroupBox.layout.addWidget(self.console)

        self.botLeftGroupBox.layout.addStretch(1)
        self.botLeftGroupBox.setLayout(self.botLeftGroupBox.layout)
        self.tab1.layout.addWidget(self.botLeftGroupBox, 6, 0, 3, 3)

        self.Act_test = QAction()

        # Mode Box - BR  ===================================
        self.botRightGroupBox = QGroupBox("Mode")
        self.botRightGroupBox.layout = QVBoxLayout()

        # previous for method had issue with Btn objects always having the info of the last
        self.Btn = QPushButton('\n\nEMERGENCY\nMANUAL\nCONTROL\n\n')
        self.Btn.clicked.connect(lambda: self.ModeButton(0, 'Manual'))
        #self.botRightGroupBox.layout.addWidget(self.Btn0)
        '''
        self.Btn1 = QPushButton('Collision Avoidance')
        self.Btn1.clicked.connect(lambda: self.ModeButton(1, 'Collision Avoidance'))
        self.botRightGroupBox.layout.addWidget(self.Btn1)

        self.Btn2 = QPushButton('Precision Navigation')
        self.Btn2.clicked.connect(lambda: self.ModeButton(2, 'Precision Navigation'))
        self.botRightGroupBox.layout.addWidget(self.Btn2)

        self.Btn3 = QPushButton('Endurance')
        self.Btn3.clicked.connect(lambda: self.ModeButton(3, 'Endurance'))
        self.botRightGroupBox.layout.addWidget(self.Btn3)

        self.Btn4 = QPushButton('Station Keeping')
        self.Btn4.clicked.connect(lambda: self.ModeButton(4, 'Station Keeping'))
        self.botRightGroupBox.layout.addWidget(self.Btn4)

        self.Btn5 = QPushButton('Search')
        self.Btn5.clicked.connect(lambda: self.ModeButton(5, 'Search'))
        self.botRightGroupBox.layout.addWidget(self.Btn5)
        '''

        #self.botRightGroupBox.layout.addStretch(1)
        #self.botRightGroupBox.setLayout(self.botRightGroupBox.layout)
        #self.tab1.layout.addWidget(self.botRightGroupBox, 6, 3, 3, 1)
        self.tab1.layout.addWidget(self.Btn, 6, 3, 3, 1)

        # dont need on main tab
        '''#Mode Box - BR2  ===================================
		self.botRight2GroupBox = QGroupBox("Config")
		self.botRight2GroupBox.layout = QVBoxLayout()

		self.fetch = QPushButton('Fetch Config')
		self.fetch.setMaximumWidth(175)
		self.fetch.clicked.connect(self.fetchConfig)

		self.refresh = QPushButton('Refresh Config')
		self.refresh.setMaximumWidth(175)
		self.refresh.clicked.connect(self.refreshConfig)

		self.publish = QPushButton('Publish Config')
		self.publish.setMaximumWidth(175)
		self.publish.clicked.connect(self.publishConfig)

		self.botRight2GroupBox.layout.addWidget(self.refresh)
		self.botRight2GroupBox.layout.addWidget(self.fetch)
		self.botRight2GroupBox.layout.addWidget(self.publish)

		self.botRight2GroupBox.layout.addStretch(1)
		self.botRight2GroupBox.setLayout(self.botRight2GroupBox.layout)
		self.tab1.layout.addWidget(self.botRight2GroupBox, 6, 3, 1, 1)
		'''

        # fin
        self.tab1.setLayout(self.tab1.layout)


    def tab2(self):
        self.tab2 = QWidget()
        self.tabs.addTab(self.tab2, "Set Mode")
        self.tab2.layout = QGridLayout(self)

        self.tab_EVENTS = QTabWidget()

        self.tab_CA()
        self.tab_PN()
        self.tab_EN()
        self.tab_SK()
        self.tab_SR()


        #ModeBox1
        self.ModeBox1 = QGroupBox("")
        self.ModeBox1.layout = QVBoxLayout()

        #ModeBox2
        self.ModeBox2 = QGroupBox("")
        self.ModeBox2.layout = QVBoxLayout()

        # previous for method had issue with Btn objects always having the info of the last
        self.Btn0 = QPushButton('Manual Only')
        self.Btn0.clicked.connect(lambda: self.ModeButton(0, 'Manual'))
        self.ModeBox1.layout.addWidget(self.Btn0)

        self.Btn1 = QPushButton('Collision Avoidance')
        self.Btn1.clicked.connect(lambda: self.ModeButton(1, 'Collision Avoidance'))
        self.ModeBox1.layout.addWidget(self.Btn1)

        self.Btn2 = QPushButton('Precision Navigation')
        self.Btn2.clicked.connect(lambda: self.ModeButton(2, 'Precision Navigation'))
        self.ModeBox1.layout.addWidget(self.Btn2)

        self.Btn3 = QPushButton('Endurance')
        self.Btn3.clicked.connect(lambda: self.ModeButton(3, 'Endurance'))
        self.ModeBox2.layout.addWidget(self.Btn3)

        self.Btn4 = QPushButton('Station Keeping')
        self.Btn4.clicked.connect(lambda: self.ModeButton(4, 'Station Keeping'))
        self.ModeBox2.layout.addWidget(self.Btn4)

        self.Btn5 = QPushButton('Search')
        self.Btn5.clicked.connect(lambda: self.ModeButton(5, 'Search'))
        self.ModeBox2.layout.addWidget(self.Btn5)

        self.ModeBox1.setLayout(self.ModeBox1.layout)
        self.tab2.layout.addWidget(self.ModeBox1, 0, 0)
        self.ModeBox2.setLayout(self.ModeBox2.layout)
        self.tab2.layout.addWidget(self.ModeBox2, 0, 1)

        self.tab2.layout.addWidget(self.tab_EVENTS, 1,0,2,2)


        self.tab2.setLayout(self.tab2.layout)

    def tab3(self):
        """
		Incomplete, mostly just formated labels and boxes
		"""

        self.tab3 = QWidget()
        self.tabs.addTab(self.tab3, "Manual Control")
        self.tab3.layout = QGridLayout(self)

        self.console2 = QLineEdit()
        #self.console2.editingFinished.connect(lambda: self.commit_message(self.console2))

        self.img_lbl2 = QLabel()
        self.img_lbl2.setPixmap(self.img)

        self.cam_img = QtGui.QPixmap(300, 300)
        self.cam_lbl = QLabel()
        self.cam_lbl.setPixmap(self.cam_img)

        self.toggleBtn = QPushButton('Toggle Manual Control : Disabled')
        self.toggleBtn.clicked.connect(self.toggleManual)

        self.tooltip = QLabel("A, D to adjust Sail Position. L_Arrow, R_Arrow to adjust Rudder Position")

        self.tab3.layout.addWidget(self.img_lbl2, 0, 1, 1, 1)
        self.tab3.layout.addWidget(self.cam_lbl, 0, 0, 1, 1)
        self.tab3.layout.addWidget(self.toggleBtn, 1, 0, 1, 1)

        self.tab3.layout.addWidget(self.tooltip, 2, 0, 1, 2)

        self.tab3.layout.addWidget(self.console2, 20, 0, 1, 2)

        self.tab3.setLayout(self.tab3.layout)

    def tab4(self):
        self.tab4 = QWidget()
        self.tabs.addTab(self.tab4, "Boat Config")
        self.configNextline = 0
        self.configLines = []

        self.tab4.layout = QGridLayout(self)

        self.fetch = QPushButton('Fetch Config')
        self.fetch.setMaximumWidth(175)
        self.fetch.clicked.connect(self.fetchConfig)
        self.refresh = QPushButton('Refresh Config')
        self.refresh.setMaximumWidth(175)
        self.refresh.clicked.connect(self.refreshConfig)
        self.publish = QPushButton('Publish Config')
        self.publish.setMaximumWidth(175)
        self.publish.clicked.connect(self.publishConfig)
        self.tab4.layout.addWidget(self.refresh, self.configNextline, 1)
        self.tab4.layout.addWidget(self.fetch, self.configNextline, 0)
        self.tab4.layout.addWidget(self.publish, self.configNextline, 2)
        self.configNextline += 1

        # self.configVals = (('example1 = 000 = 00'), ('example2 = abc'), ('example3 = 123'))
        # self.addConfigLine(self.configVals[1])
        # self.addConfigLine(self.configVals[2])
        # self.addConfigLine(self.configVals[0])

        self.tab4.setLayout(self.tab4.layout)


    def tab_CA(self):
        self.tab_CA = QWidget()
        self.tab_EVENTS.addTab(self.tab_CA, "Collis Avoid")
        self.tab_CA.layout = QGridLayout(self)

        names = ['Buoy x1', 'Buoy y1', 'Buoy x2', 'Buoy y2', 'Buoy x3', 'Buoy y3', 'Buoy x4', 'Buoy y4']
        self.CA_BX = []
        self.CA_BX = ArrLineEdit(self.tab_CA,8,names)
        #ArrName(self.tab_CA,8,names)

        self.tab_CA.setLayout(self.tab_CA.layout)

    def tab_PN(self):
        self.tab_PN = QWidget()
        self.tab_EVENTS.addTab(self.tab_PN, "Prec Nav")
        self.tab_PN.layout = QGridLayout(self)

        names = ['Buoy x1', 'Buoy y1', 'Buoy x2', 'Buoy y2', 'Buoy x3', 'Buoy y3', 'Buoy x4', 'Buoy y4']
        self.PN_BX = ArrLineEdit(self.tab_PN,8,names)

        self.tab_PN.setLayout(self.tab_PN.layout)

    def tab_EN(self):
        self.tab_EN = QWidget()
        self.tab_EVENTS.addTab(self.tab_EN, "Endur")
        self.tab_EN.layout = QGridLayout(self)

        names = ['Buoy x1', 'Buoy y1', 'Buoy x2', 'Buoy y2', 'Buoy x3', 'Buoy y3', 'Buoy x4', 'Buoy y4']
        self.EN_BX = ArrLineEdit(self.tab_EN,8,names)


        self.tab_EN.setLayout(self.tab_EN.layout)

    def tab_SK(self):
        self.tab_SK = QWidget()
        self.tab_EVENTS.addTab(self.tab_SK, "Stat Keep")
        self.tab_SK.layout = QGridLayout(self)

        names = ['Buoy x1', 'Buoy y1', 'Buoy x2', 'Buoy y2']
        self.SK_BX = ArrLineEdit(self.tab_SK,4,names)


        self.tab_SK.setLayout(self.tab_SK.layout)

    def tab_SR(self):
        self.tab_SR = QWidget()
        self.tab_EVENTS.addTab(self.tab_SR, "Search")
        self.tab_SR.layout = QGridLayout(self)

        names = ['Buoy x', 'Buoy y', 'radius']
        self.SR_BX = ArrLineEdit(self.tab_SR,3,names)


        self.tab_SR.setLayout(self.tab_SR.layout)


    def fetchConfig(self):
        ARDUINO.send("get config")
        BOAT_DATA.config = []
        for lbl, dataBox in self.configLines:
            lbl.setEnabled(False)
            dataBox.setEnabled(False)

    def refreshConfig(self):
        if BOAT_DATA.configChanged:
            for line in BOAT_DATA.config:
                found = False
                for lbl, dataBox in self.configLines:
                    if line.split(' : ', 1)[0] == lbl.text():
                        lbl.setEnabled(True)
                        dataBox.setEnabled(True)
                        dataBox.setText(line.split(' : ', 1)[1])
                        found = True

                if found == False:
                    self.addConfigLine(line)

    def publishConfig(self):

        for line in BOAT_DATA.config:
            text, val = line.split(' : ', 1)
            for lbl, dataBox in self.configLines:
                if text == lbl.text():
                    if dataBox.text() != val:
                        ARDUINO.send(F'{text} : {dataBox.text()}')
                    break

    def addConfigLine(self, text):
        name, val = text.split(' : ', 1)
        lbl = QLabel(name)
        lbl.setMaximumWidth(100)
        dataBox = QLineEdit()
        dataBox.setText(val)
        self.configLines.append((lbl, dataBox))

        self.tab4.layout.addWidget(lbl, self.configNextline, 0)
        self.tab4.layout.addWidget(dataBox, self.configNextline, 1)
        self.configNextline += 1

        self.tab4.setLayout(self.tab4.layout)

    def commit_message(self):
        """
		called whenever a enter is pressed when console widget is targeted
		retrives data from textbox and sends a message to clients
		message must be formated as such [action] [value] ; ex) "test 123"
		message can also be a one word command for the GUI,
		if the message is one word and not a keyword then it is ignored
		"""
        num = self.tabs.currentIndex()

        if num == 0:
            textBox = self.console
        else:
            num = 1
            textBox = self.console2

        text = textBox.text()
        if text != "":
            self.consolelast[num] = text

        # print("last:\t", self.consolelast[0], ", ", self.consolelast[1])

        if ARDUINO:
            ARDUINO.send(text)

            textBox.setText('')
            return

        arry = text.split(' ')
        if len(arry) > 1 and SERVER:
            data = {"action": arry[0], 'value': str(arry[1])}
            SERVER.send_once(data)

        # one word keywords for local commands
        else:
            if text == 'terminate':
                close_app()

            elif text.startswith('ARDU_'):

                text = text.split('_')

                if text[1] == "INIT":
                    # try:
                    make_arduino(str(text[2]))
            # except TypeError:
            # 	print("ARDU_INIT requires a COM port index")
            # except:
            # 	print("unable to create ARDUINO object")

        textBox.setText('')

    def increase_scale(self):
        self.scale += 100

    def decrease_scale(self):
        self.scale -= 100

    def paintEvent(self, event):
        # called every frame, draws images used for data visualization
        qp = QPainter()
        qp.begin(self.img)
        qp.fillRect(0, 0, 300, 300, QColor("#000000"))
        self.draw_boat(event, qp)
        self.draw_wind(event, qp)
        self.draw_points(event, qp)
        qp.end()

        self.img_lbl.setPixmap(self.img)
        self.img_lbl2.setPixmap(self.img)

    def draw_points(self, event, qp):

        center = 150
        qp.setPen(QPen(QColor(255, 255, 255), 10))

        for lat, lon in BOAT_DATA.gps_points:
            # dist = distanceInMBetweenEarthCoordinates(BOAT_DATA.gps[0], BOAT_DATA.gps[1], lat, lon)
            # angle = angleBetweenCoordinates(BOAT_DATA.gps[0], BOAT_DATA.gps[1], lat, lon)

            dx = BOAT_DATA.gps[0] - lat
            dy = BOAT_DATA.gps[1] - lon

            qp.drawPoint(center + dx * self.scale, center + dy * self.scale)

    def draw_boat(self, event, qp):

        center = 150

        L = self.scale / 300  # length of line
        spacer = 30  # angle between arms of boat hulls in degrees

        angle = float(BOAT_DATA.boat_orient) if BOAT_DATA.boat_orient else 0

        # DRAW HULL
        x1 = math.cos(math.radians(angle - spacer)) * L
        y1 = math.sin(math.radians(angle - spacer)) * L

        x2 = math.cos(math.radians(angle + spacer)) * L
        y2 = math.sin(math.radians(angle + spacer)) * L

        qp.setPen(QPen(QColor(255, 100, 0), 4))

        qp.drawLine(center, center, center + x1, center + y1)
        qp.drawLine(center, center, center + x2, center + y2)

        # DRAW SAIL
        angle = float(BOAT_DATA.boat_orient) if BOAT_DATA.boat_orient else 0
        angle += float(BOAT_DATA.sail_pos) if BOAT_DATA.sail_pos else 0

        x2 = math.cos(math.radians(angle)) * L
        y2 = math.sin(math.radians(angle)) * L

        qp.setPen(QPen(QColor(255, 255, 255), 4))

        qp.drawLine(center, center, center + x2, center + y2)

    def draw_wind(self, event, qp):
        qp.setPen(QPen(QColor(0, 0, 255), 2))
        max_L = 425  # length of lines for wind
        self.paint_counter += .05
        if self.paint_counter > 150:
            self.paint_counter = -150
        theta = float(BOAT_DATA.wind_dir) if BOAT_DATA.wind_dir else 0

        c1 = 150 + self.paint_counter * math.sin(math.radians(theta))
        c2 = 150 + self.paint_counter * math.cos(math.radians(theta))

        for i in range(-300, 300, 60):
            x1 = (math.cos(math.radians(-theta)) * max_L + (c1 + i))
            y1 = (math.sin(math.radians(-theta)) * max_L + (c2 + i))

            x2 = (math.cos(math.radians(-theta + 180)) * max_L + (c1 + i))
            y2 = (math.sin(math.radians(-theta + 180)) * max_L + (c2 + i))

            qp.drawLine(x1, y1, x2, y2)

    def toggleManual(self):
        global MANUAL

        if MANUAL == False:
            self.toggleBtn.setText('Toggle Manual Control : Enabled')
            MANUAL = True
        else:
            self.toggleBtn.setText('Toggle Manual Control : Disabled')
            MANUAL = False

    def ModeButton(self, data, name):
        global MANUAL
        self.ttlabel.setText("Curr Mode: " + name)
        temp_str = "mode "+str(data)

        if data == 0:
            self.tabs.setCurrentIndex(2)
            self.toggleBtn.setText('Toggle Manual Control : Enabled')  # prevent abuse when switching between other buttons
            MANUAL = True
            SERVER.send_data("mode "+str(data))
            return
        else:
            self.tabs.setCurrentIndex(1)
            self.tab_EVENTS.setCurrentIndex(data-1)
            self.toggleBtn.setText('Toggle Manual Control : Disabled')
            MANUAL = False

            temp_arr = []
            if data == 1:
                temp_arr = self.CA_BX
            elif data == 2:
                temp_arr = self.PN_BX
            elif data == 3:
                temp_arr = self.EN_BX
            elif data == 4:
                temp_arr = self.SK_BX
            elif data == 5:
                temp_arr = self.SR_BX
            else:
                print("ERR: Selecting arr")
                return
            try:
                for i in range(len(temp_arr)):
                    text = temp_arr[i].text()
                    if text == "":
                        print("ERR: Field not filled out:",i)
                        return
                    else:
                        temp_str += " "+str(float(text))
                #temp_str = temp_str[:-1]
            except:
                print("mode str val error")
                return

        #print(temp_str)
        SERVER.send_data(temp_str)

    def ConsoleFancy(self):
        num = self.tabs.currentIndex()

        if num == 0:
            temp = self.console.text()
            self.console.setText(self.consolelast[num])
            self.consolelast[num] = temp
        else:
            num = 1
            temp = self.console2.text()
            self.console2.setText(self.consolelast[num])
            self.consolelast[num] = temp

    def data_refresh(self):
        """
		refreshes labels with new data from BOAT_DATA object
		"""
        self.gps_lbl.setText("GPS: " + str(BOAT_DATA.gps))
        self.rudder_pos_lbl.setText("Rudder Position: " + str(BOAT_DATA.rudder_pos))
        self.sail_pos_lbl.setText("Sail Position: " + str(BOAT_DATA.sail_pos))
        self.boat_orient_lbl.setText("Boat Orientation: " + str(BOAT_DATA.boat_orient))
        self.wind_speed_lbl.setText("Wind Speed: " + str(BOAT_DATA.wind_speed))
        self.wind_dir_lbl.setText("Wind Direction: " + str(BOAT_DATA.wind_dir))
        self.battery_lbl.setText("Battery: " + str(BOAT_DATA.battery) +"%")

        if BOAT_DATA.message:
            self.message_box.append(BOAT_DATA.message)
            sleep(.1)
            sb = self.message_box.verticalScrollBar()
            sb.setValue(sb.maximum())

            BOAT_DATA.message = None

        if hasattr(self, 'R_pos_lbl'):
            self.R_pos_lbl.setText("Rudder Position: " + str(BOAT_DATA.rudder_pos))
            self.S_pos_lbl.setText("Sail Position: " + str(BOAT_DATA.sail_pos))

    @pyqtSlot()
    def on_click(self):
        # dont worry about this
        print("\n")
        for currentQTableWidgetItem in self.tableWidget.selectedItems():
            print(currentQTableWidgetItem.row(), currentQTableWidgetItem.column(), currentQTableWidgetItem.text())


#     /\           | |     (_)              / ____|
#    /  \   _ __ __| |_   _ _ _ __   ___   | |     ___  _ __ ___  ___
#   / /\ \ | '__/ _` | | | | | '_ \ / _ \  | |    / _ \| '_ ` _ \/ __|
#  / ____ \| | | (_| | |_| | | | | | (_) | | |___| (_) | | | | | \__ \
# /_/    \_\_|  \__,_|\__,_|_|_| |_|\___/   \_____\___/|_| |_| |_|___/

class arduino:

    def __init__(self, port_num):
        try:
            self.ser1 = serial.Serial(port= 'COM' + port_num, baudrate = 115200, timeout=.1)
        except:
            print("Error Connecting to COM" + port_num)

    def send(self, data):
        print(data)
        self.ser1.write(str(data).encode())
        #print('done')

    def read(self):
        message = self.ser1.readline()
        print(message)
        return message


def close_app():
    app.quit()
    sys.exit()

    # attempts to close app, if  causes the app to crash,
    # this is important because if you just close the window the app keeps running in the console
    # to truly close it you have to press control-break or similar in the console
    # and the break key is like wayyy at the top of the keayboard and hard to press
    end_program()


def map(value, istart, istop, ostart, ostop):
    return ostart + (ostop - ostart) * ((value - istart) / (istop - istart));


def handle_input():
    while RUN_THREAD:

        if MANUAL:

            try:
                events = get_gamepad()
            except:
                global FOUND_GAMEPAD
                if FOUND_GAMEPAD:
                    FOUND_GAMEPAD = False
                    print("No Gamepad found")
                events = []
            for event in events:
                # if not 'ABS' in str(event.code) and not 'SYN_REPORT' in str(event.code):
                # 	print(event.ev_type, event.code, event.state)

                if 'ABS_HAT0X' in str(event.code):
                    val = 5 * event.state
                    if val != 0:
                        SERVER.send_data(F"sail {val}")

                if 'ABS_X' in str(event.code):
                    val = int(map(event.state, -33000, 33000, -45, 45))
                    SERVER.send_data(F"rudder {val}")

                if "BTN" in str(event.code):
                    if 'SOUTH' in str(event.code):
                        SERVER.send_data("sail -90")
                    if 'NORTH' in str(event.code):
                        SERVER.send_data("sail 90")
                    if 'EAST' in str(event.code):
                        SERVER.send_data("toggleAutoSail")

            if keyboard.is_pressed('w') and SERVER:
                val = min((BOAT_DATA.sail_pos + 5), 90) if BOAT_DATA.sail_pos else 5
                SERVER.send_data("sail 5")
                sleep(.25)


            elif keyboard.is_pressed('s') and SERVER:
                val = max((BOAT_DATA.sail_pos - 5), -90) if BOAT_DATA.sail_pos else -5
                SERVER.send_data("sail -5")
                sleep(.25)

            elif keyboard.is_pressed('a') and SERVER:
                val = min((BOAT_DATA.sail_pos + 5), 90) if BOAT_DATA.sail_pos else 5
                SERVER.send_data("rudder 5")
                sleep(.25)


            elif keyboard.is_pressed('d') and SERVER:
                val = max((BOAT_DATA.sail_pos - 5), -90) if BOAT_DATA.sail_pos else -5
                SERVER.send_data("rudder -5")

                sleep(.25)


def make_arduino(com_port):
    global RUN_THREAD, ARDUINO

    ARDUINO = arduino(com_port)

    RUN_THREAD = True
    pump_thread = Thread(target=server_update)  # creates a Thread running an infinite loop pumping server
    pump_thread.start()

    pump_thread2 = Thread(target=handle_input)  # creates a Thread running an infinite loop checking input
    pump_thread2.start()


if __name__ == "__main__":
    DATA_REFRESH = None
    MANUAL = False
    FOUND_GAMEPAD = True

    #print(sys.argv.pop())

    try:
        make_arduino(sys.argv.pop())
        #make_arduino(4)
    except:
        ARDUINO = None
        print("Could not create ARDUINO object, did you include a COM port is args?")
        print("use the following command to add ARDUINO: ARDU_INIT_[COM port]")

    SERVER = MyServer(
        localaddr=('0.0.0.0', 1338))  # creates a server object accepting connections from any IP on port 1337
    BOAT_DATA = boat_data()  # creates BOAT_DATA object and sets it as a global variable

    app = QApplication(sys.argv)
    w = mainWindow()

    sys.exit(app.exec_())

