import os
import sys
from PyQt5 import QtCore, uic, QtWidgets
from PyQt5.QtCore import QTimer, QDate, QTime, Qt, QObject, QThread, pyqtSignal, QMutex
from PyQt5.QtGui import QImage, QPixmap
import resources_rc

import module_control as ct
import module_findDistance as fd
import module_image as im

import cv2
from pypylon import pylon
import numpy as np
import time
import warnings
warnings.filterwarnings('ignore', 'The iteration is not making good progress')


# Define function to import external files when using PyInstaller.
def resource_path(relative_path):
	""" Get absolute path to resource, works for dev and for PyInstaller """
	try:
		# PyInstaller creates a temp folder and stores path in _MEIPASS
		base_path = sys._MEIPASS
	except Exception:
		base_path = os.path.abspath(".")

	return os.path.join(base_path, relative_path)

Form_Home, QtBaseClass = uic.loadUiType(resource_path("Homepage.ui"))
Form_Main, QtBaseClass = uic.loadUiType(resource_path("Mainpage.ui"))

Form_Dialog_start, QDialogClass = uic.loadUiType(resource_path("Dialog_start.ui"))
Form_Dialog_after_start, QDialogClass = uic.loadUiType(resource_path("Dialog_after_start.ui"))
Form_Dialog_stop, QDialogClass = uic.loadUiType(resource_path("Dialog_stop.ui"))
Form_Dialog_after_stop, QDialogClass = uic.loadUiType(resource_path("Dialog_after_stop.ui")) 
Form_Dialog_after_after_stop, QDialogClass = uic.loadUiType(resource_path("Dialog_after_after_stop.ui")) 


class PimApp(QObject):
	# global counter
	
	cap_signal = pyqtSignal(str)
	dist_signal = pyqtSignal(list) 
	
	def __init__(self):
		super().__init__()
		
		# Create a gui object.
		self.gui = ui()
		self.gui.homepage()
		self.gui.mainpage()
		
		# Show homepage
		self.gui.window_home.show()
		
		# Create new worker threads.
		self.timerThread_datetime()
		self.timerThread_camera_big()
		self.timerThread_camera_small()
		self.move_to_Thread()
		
		# Make any cross object connections.
		self.connectSignals()
	
	def connectSignals(self):
		# Homepage Signals
		self.gui.form_home.lineEdit_targetAmount.returnPressed.connect(self.cal_time)
		self.gui.form_home.startButton.clicked.connect(self.start_button_clicked)
		
		# self.count_signal.connect(self.update_current_amount)
		self.cap_signal.connect(self.camera_process_status)
		self.gui.form_main.playButton.clicked.connect(self.camera_show)
		self.gui.form_main.pauseButton.clicked.connect(self.pause_button_clicked)
		self.gui.form_main.stopButton.clicked.connect(self.stop_button_clicked)
		
	def cal_time(self):
		graftAmount = self.gui.form_home.lineEdit_targetAmount.text()
		opTime = 8.62*int(graftAmount)/3600
		self.gui.form_home.label_opTime.setText("{:.1f}".format(opTime))

	def start_button_clicked(self):	
		self.gui.Dia_Start()
		self.gui.dialog1.show()
		rsp1 = self.gui.dialog1.exec_()
		
		if rsp1 == QDialogClass.Accepted:
			self.gui.Dia_After_Start()
			self.gui.dialog2.show()
			rsp2 = self.gui.dialog2.exec_()
			
			if rsp2 == QDialogClass.Accepted:
				self.gui.window_main.show()
				self.gui.window_home.close()
				HN = self.gui.form_home.lineEdit_HN.text()
				self.gui.form_main.label_HN.setText("<font color='white'>" + HN + "</font>")
				self.TargetAmount = self.gui.form_home.lineEdit_targetAmount.text()
				self.gui.form_main.label_targetAmount.setText("<font color='#55ff7f'>" + self.TargetAmount + "</font>")
				self.TargetAmount_int = int(self.TargetAmount)
				
			else:
				pass
				
		else:
			pass
	
	def timerThread_datetime(self):	
		# set timer for digital clock
		self.timer_datetime = QTimer()
		self.timer_datetime.timeout.connect(self.update_datetime)   #update digital clock using update_datetime function
		self.timer_datetime.start(20) # timeout interval = 20 msec
		
	def timerThread_camera_big(self):
		# set timer for camera
		self.timer_camera_big = QTimer()
		self.timer_camera_big.timeout.connect(self.update_frame_big)
	
	def timerThread_camera_small(self):
		# set timer for camera
		self.timer_camera_small = QTimer()
		self.timer_camera_small.timeout.connect(self.update_frame_small)
	
	# update digital clock 
	def update_datetime(self):
		date_ = QDate.currentDate()
		time_ = QTime.currentTime()
		self.gui.form_main.label_date.setText("<font color='#f8edd4'>" + date_.toString(Qt.ISODate) + "</font>")
		self.gui.form_main.label_time.setText("<font color='#f8edd4'>" + time_.toString() + "</font>")	
	
	# view camera
	def update_frame_big(self):
		
		self.grabResult = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
	
		if self.grabResult.GrabSucceeded():
			# Access the image data
			self.img = self.converter_RGB.Convert(self.grabResult)
			self.image = self.img.GetArray()
			
			# Find distance between target and needle position
			try:
				fdist = fd.FindingDistance(self.image)
				distance = fdist.real_distance
				# send out distance values to control thread
				self.dist_signal.emit(distance)
				
			except:
				print("No distance")
				# pass
			
			# Modify image for gui_window
			self.imp = im.ImageProcessing(self.image, 'BLOB')
			self.show_img = self.imp.img_with_bounding
			
			# get image infos
			height, width, channel = self.show_img.shape
			step = channel * width
			# create QImage from image
			qImg = QImage(self.show_img.data, width, height, step, QImage.Format_RGB888)
			# show image in img_label
			self.gui.form_main.label_bigCam.setPixmap(QPixmap.fromImage(qImg))
			self.gui.form_main.label_bigCam.setScaledContents(True)
			
			'''
			# get image infos
			height, width, channel = self.image.shape
			step = channel * width
			# create QImage from image
			qImg = QImage(self.image.data, width, height, step, QImage.Format_RGB888)
			# show image in img_label
			self.gui.form_main.label_bigCam.setPixmap(QPixmap.fromImage(qImg))
			self.gui.form_main.label_bigCam.setScaledContents(True)
			'''
			
	def update_frame_small(self):	
		
		'''
		# read image in BGR format
		ret2, image2 = self.cap.read()
		# convert image to RGB format
		image2 = cv2.cvtColor(image2, cv2.COLOR_BGR2RGB)
		'''

		im2 = self.imp.roi
		image2 = np.array(im2) 
		# image2 = np.transpose(image2,(1,0,2)).copy()
		
		# get image infos
		height2, width2, channel2 = image2.shape
		step2 = channel2 * width2
		# create QImage from image
		qImg2 = QImage(image2.data, width2, height2, step2, QImage.Format_RGB888)
		# show image in img_label
		self.gui.form_main.label_smallCam.setPixmap(QPixmap.fromImage(qImg2))
		self.gui.form_main.label_smallCam.setScaledContents(True)
		
	def camera_show(self):
		# if timer is stopped
		if not self.timer_camera_big.isActive() and not self.timer_camera_small.isActive():
			
			# start timer
			self.timer_camera_big.start()	# timeout interval = default = 0 msec
			self.timer_camera_small.start()
			
			'''
			### small window
			# create video capture
			self.cap = cv2.VideoCapture(0)				
			self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT,640)  
			self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,480)
			self.cap_signal.emit("Capture(small) Done!")
			'''
			
			### big window
			# conecting to the first available camera and loading its features
			self.camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
			self.camera.Open()
			nodeFile = "daA1920-30uc_22901961.pfs"
			pylon.FeaturePersistence.Load(nodeFile, self.camera.GetNodeMap(), True)
			self.camera.Close()
			
			# Grabing Continusely (video) with minimal delay
			self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly) 
			self.converter_RGB = pylon.ImageFormatConverter()

			# converting to opencv bgr format
			self.converter_RGB.OutputPixelFormat = pylon.PixelType_RGB8packed
			self.converter_RGB.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
			
			'''
			# converting to opencv mono format
			self.converter_mono.OutputPixelFormat = pylon.PixelType_Mono8
			self.converter_mono.OutputPixelFormat = pylon.PixelType_Mono8
			'''
			
			self.cap_signal.emit("Capture Done!")
			
		else:	
			self.cap_signal.emit("Camera has already been in capture mode!")
		
	def camera_process_status(self, result):
		print(result)
	
	def update_current_amount(self, counter):
		self.CurrentAmount = str(counter)
		self.gui.form_main.label_currentAmount.setText("<font color='#ffff00'>" + self.CurrentAmount + "</font>")
		
	def pause_button_clicked(self):
		# stop timer
		self.timer_camera_big.stop()
		self.timer_camera_small.stop()
		
		'''
		### small window
		# release video capture
		self.cap.release()
		'''
		
		### big window
		# Releasing grab result
		self.grabResult.Release()
		# Releasing the resource    
		self.camera.StopGrabbing()
	
	def stop_button_clicked(self):
		# stop timer
		self.timer_camera_big.stop()
		self.timer_camera_small.stop()
		
		'''
		### small window
		# release video capture
		self.cap.release()
		'''
		
		### big window
		# Releasing grab result
		self.grabResult.Release()
		# Releasing the resource    
		self.camera.StopGrabbing()
		
		# Pop-ups each dialog
		self.gui.Dia_Stop()
		self.gui.dialog3.show()
		rsp3 = self.gui.dialog3.exec_()
		
		if rsp3 == QDialogClass.Accepted:			
			self.gui.Dia_After_Stop()
			self.gui.dialog4.show()
			rsp4 = self.gui.dialog4.exec_()
			
			if rsp4 == QDialogClass.Accepted:
				self.gui.Dia_After_After_Stop()
				self.gui.dialog5.show()
				rsp5 = self.gui.dialog5.exec_()
				
				if rsp5 == QtWidgets.QDialog.Accepted:
					time.sleep(1)
					app = QtWidgets.QApplication(sys.argv)
					sys.exit(app.exec_())
				
				else:
					self.camera_show()	
				
			else:
				self.camera_show()
				
		else:
			self.camera_show()
		
	
	def move_to_Thread(self):
		# Create a thread for robotObject. 
		self.objThread3 = QThread()
		self.obj3 = robotObject()
		self.obj3.moveToThread(self.objThread3)
		self.gui.form_main.playButton.clicked.connect(self.obj3.setHome)
		self.dist_signal.connect(self.obj3.robot)
		self.obj3.count_signal.connect(self.update_current_amount)
		self.objThread3.start()
		
class ui(QtBaseClass, QDialogClass, Form_Home, Form_Main, Form_Dialog_start, Form_Dialog_after_start):
	
	def __init__(self):
		super().__init__()
		
	def homepage(self):
		self.window_home = QtBaseClass()
		self.form_home = Form_Home()
		self.form_home.setupUi(self.window_home)
	
	def mainpage(self):
		self.window_main = QtBaseClass()
		self.form_main = Form_Main()
		self.form_main.setupUi(self.window_main)
	
	def Dia_Start(self):
		self.dialog1 = QDialogClass()
		self.form_d1 = Form_Dialog_start()
		self.form_d1.setupUi(self.dialog1)
	
	def Dia_After_Start(self):
		self.dialog2 = QDialogClass()
		self.form_d2 = Form_Dialog_after_start()
		self.form_d2.setupUi(self.dialog2)
	
	def Dia_Stop(self):
		self.dialog3 = QDialogClass()
		self.form_d3 = Form_Dialog_stop()
		self.form_d3.setupUi(self.dialog3)
	
	def Dia_After_Stop(self):
		self.dialog4 = QDialogClass()
		self.form_d4 = Form_Dialog_after_stop()
		self.form_d4.setupUi(self.dialog4)
	
	def Dia_After_After_Stop(self):
		self.dialog5 = QDialogClass()
		self.form_d5 = Form_Dialog_after_after_stop()
		self.form_d5.setupUi(self.dialog5)
	
class robotObject(QObject):
	counter = 0
	count_signal = pyqtSignal(int)
	
	def __init__(self):
		super().__init__()

	def setHome(self):
		self.cont_rob = ct.Control()
		dc_port = 'COM18'
		# dc_port = input("COM port for dc motor: ")
		# print(type(dc_port))
		self.serialPort = self.cont_rob.OpenSerialPort(dc_port)
		if self.serialPort == None: sys.exit(1)
		self.cont_rob.setHome(self.serialPort)
	
	def robot(self, distance):
		self.cont_rob.Motors_Control(self.serialPort, distance)
		self.counter = self.counter + 1
		self.count_signal.emit(self.counter)
		
if __name__ == "__main__":
	app = QtWidgets.QApplication(sys.argv)
	window = PimApp()
	sys.exit(app.exec_())

