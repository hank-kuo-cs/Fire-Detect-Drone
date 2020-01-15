from PIL import Image
from PIL import ImageTk
import Tkinter as tki
from Tkinter import Toplevel, Scale
import threading
import datetime
import cv2
import os
import time
import platform
import requests
import json
import numpy as np
from tello_control_ui import TelloUI

STATE_INIT = 0
STATE_PATROL = 1
STATE_CORRECT = 2
STATE_LOCATING = 3
STATE_SEARCH = 4
STATE_FINISH = 5

SIZE_L = 200
SIZE_H = 300




class FireDetect:
	"""Wrapper class to enable the fire detection."""

	def __init__(self, tello, outputpath):
		self.vplayer = TelloUI(tello, outputpath)

		self.partrolDistance = 0.0 #accumulated distance in patrol mode

		self.state = STATE_INIT  #Finite state machine

		self.fireCount = 0
		self.searchCount = 0
		self.box = []

		# start the Tkinter mainloop
		self.Thread = threading.Thread(target = self.main_loop)
		self.Thread.daemon = True
		self.Thread.start()


	def main_loop(self):

		while not self.isEventFinish():
			if self.state is STATE_INIT:
				#Do something init state should do
				#self.Takeoff()
				self.vplayer.tello.takeoff()
				time.sleep(7)
				self.state = STATE_PATROL
			
			elif self.state is STATE_PATROL:
				#Do patrol
				isFinish = self.patrol()
				if isFinish:
					self.state = STATE_FINISH

				elif self.detectFire():
					#send message
					self.fireCount = 0
					self.apiUpdate()
					self.state = STATE_CORRECT

				print("STATE_PATROL")

			elif self.state is STATE_CORRECT:
				#correct position
				print("STATE_CORRECT")
				self.detectFire()

				bbox = list(self.box)
				
				MVcmd = self.correct(bbox)

				print('box =', bbox)
				print('MVcmd =', MVcmd)
				# if not MVcmd:
				# 	self.state = STATE_LOCATING
				if not MVcmd:
					pass
				elif MVcmd[0]:
					self.correctR(MVcmd[0])
				elif MVcmd[1]:
					self.correctT(MVcmd[1])
				else:
					self.state = STATE_LOCATING

				# self.state = STATE_LOCATING


			elif self.state is STATE_LOCATING:
				#Do tracking
				print("STATE_LOCATING")
				isFinish = self.locate()

				if isFinish:
					self.state = STATE_SEARCH


			elif self.state is STATE_SEARCH:
				#Do tracking
				print("STATE_SEARCH")
				isFinish = self.search()
				if isFinish:
					self.state = STATE_LOCATING


			elif self.state is STATE_FINISH:
				print("STATE_FINISH")
				if self.land() == 'ok':
					return

			time.sleep(1.5)
			print('MainLoop')
			print(type(self.vplayer.frame))


	def patrol(self):
		#Do partrol and return finish or not. Ture means finish, False mean need continue.
		MaxDist = 5
		response = self.vplayer.telloMoveForward(self.vplayer.distance)
		print 'forward %f' % self.partrolDistance
		if response == 'ok':
			self.partrolDistance += self.vplayer.distance
			if(self.partrolDistance > MaxDist):
				return True

		return False


	def detectFire(self):
		#Detect and return exist fire or not. Ture means exist fire.
		self.fireCount = 0
		box = np.array([0.0, 0.0, 0.0, 0.0])

		for i in range(3):
			image = cv2.cvtColor(self.vplayer.frame, cv2.COLOR_RGB2BGR)
			data = self.apiDetect(image)
			if data['is_fire']:
				self.fireCount += 1
				box += np.array(data['box'])

		if self.fireCount > 1:
			self.box = box / self.fireCount
			return True

		else:
			return False

	def locate(self):
		#1.Call server API first.
		#2.Circle the fire zone./move right until the fire is out of sight.
		self.vplayer.telloMoveRight(0.2)

		is_fire = self.detectFire()
		if not is_fire:
			return True

		box_center_x = (self.box[0] + self.box[2]) / 2
		print('shape =', self.vplayer.frame.shape)
		x_interval = self.vplayer.frame.shape[1] / 3
		if box_center_x < x_interval:
			return True

		return False


	def search(self):
		#Circle the fire zone./CCW rotate to search the fire.
		self.vplayer.telloCCW(7)
		is_fire = self.detectFire()

		self.searchCount += 1

		if self.searchCount > 5 and not is_fire:
			return True

		if not is_fire:
			return False

		box_center_x = (self.box[0] + self.box[2]) / 2
		x_interval = self.vplayer.frame.shape[1] / 3
		if box_center_x > x_interval * 2:
			return True

		self.searchCount = 0
		return False

	def correctR(self, R):
		if R == 2:
			self.vplayer.telloCW(5)
		elif R == 1:
			self.vplayer.telloCCW(5)
		return

	def correctT(self, T):
		if T == 1:
			self.vplayer.telloMoveForward(0.2)
		elif T == 2:
			self.vplayer.telloMoveBackward(0.1)
		return

	def correct(self, bbox):
		r = []
		if not bbox:
			return r
		width = bbox[2] - bbox[0]
		height = bbox[3] - bbox[1]
		size = width

		# 1 for left; 2 for right
		if(bbox[0] > 320 and bbox[2] < 960):
			r.append(0)
		elif(bbox[2] < 640):
			r.append(1)
		elif(bbox[0] > 640):
			r.append(2)

		
		# 1 for forward; 2 for backward
		if(size > SIZE_L and size < SIZE_H):
			r.append(0)
		elif(size < SIZE_L):
			r.append(1)
		elif(size > SIZE_H):
			r.append(2)

		return r


	def apiDetect(self, image):
		
		image = cv2.pyrDown(image)
		image = cv2.pyrDown(image)

		data = json.dumps(image.tolist(), separators=(',', ':'), sort_keys=True, indent=4)
		resp = requests.post(url='http://localhost:10008/api/v1/fire/detect', json={'image': data})
		resp_data = json.loads(resp.content)['data']
		resp_data['box'] = list(np.array(resp_data['box'], dtype=np.float) * 4)

		print(resp_data)
		return resp_data

	def apiUpdate(self):
		while True:
			image = cv2.cvtColor(self.vplayer.frame, cv2.COLOR_RGB2BGR)
			resp_data = self.apiDetect(image)
			if not resp_data['is_fire']:
				pass
			else:
				img_r1 = cv2.pyrDown(image)
				red = (0, 0, 255)
		        box = resp_data['box']
		        left, top, right, bottom = int(box[0] / 2), int(box[1] / 2), int(box[2] / 2), int(box[3] / 2)

		        img_r1 = cv2.rectangle(img_r1, (left, top), (right, bottom), red, 4)
		        img_r1 = cv2.putText(img_r1, 'Fire', (left, top - 10), cv2.FONT_HERSHEY_COMPLEX, 1.2, red, 1)

		        data = json.dumps(img_r1.tolist(), separators=(',', ':'), sort_keys=True, indent=4)
		        resp = requests.post(url='http://localhost:10008/api/v1/fire/upload', json={'is_fire': True, 'image': data})
		        break

	def land(self):
		#Drone land. Turn 'OK' or 'FALSE'
		return self.vplayer.tello.land()

	def telloTakeOff(self):
		return self.vplayer.tello.takeoff()

	def telloLanding(self):
		return self.vplayer.tello.land()

	def telloCW(self, degree):
		return self.vplayer.tello.rotate_cw(degree)

	def telloCCW(self, degree):
		return self.vplayer.tello.rotate_ccw(degree)

	def telloMoveForward(self, distance):
		return self.vplayer.tello.move_forward(distance)

	def telloMoveBackward(self, distance):
		return self.vplayer.tello.move_backward(distance)

	def telloMoveLeft(self, distance):
		return self.vplayer.tello.move_left(distance)

	def telloMoveRight(self, distance):
		return self.vplayer.tello.move_right(distance)

	def telloUp(self, dist):
		return self.vplayer.tello.move_up(dist)

	def telloDown(self, dist):
		return self.vplayer.tello.move_down(dist)

	def isEventFinish(self): #Return Ture means finish
		return self.vplayer.stopEvent.is_set()

