import os, sys

if getattr(sys, "frozen", False):
	BASE = sys._MEIPASS
else:
	BASE = os.path.dirname(__file__)

SRC = os.path.join(BASE, "src")
if SRC not in sys.path:
	sys.path.insert(0, SRC)

import playback
import recorder
import globalconfwizard
import pynput
import copy
import traceback
import time
import sys
from threading import Thread, Event
from PyQt6.QtGui import QAction,QIcon
from PyQt6.QtCore import QObject,pyqtSignal, QTimer, QMetaObject, Qt, QThread
from PyQt6.QtWidgets import (
	QApplication,
	QSystemTrayIcon,
	QMenu, 
	QFileDialog, 
	QMessageBox, 
	QWidget, 
	QLabel,
	QDial,
	QCheckBox,
	QComboBox,
	QTextEdit,
	QSpinBox,
	QSlider
)
from resources import resource_path


class Emitter(QObject):
	error = pyqtSignal(str)

class Main:

	def __init__(self):

		self.app = QApplication(sys.argv)

		self.arr = bytearray(b"<NEOPRISMA>\x01")
		self.compiled_arr:list[playback.EventPacket] = []
		self.state_recording = False
		self.state_playback = False
		self.state_autoclicker = False
		self.timestamp_multiplier = 1
		self.keysdown = set()
		self.hotkeys = {
			"play": set(),
			"record": set(),
			"auto": set()
		}

		if os.path.exists("~/.neoprisma"):
			conf_data=globalconfwizard.unpack("~/.neoprisma")
		else:
			conf_data={
				"DOC":"NEOPRISMA CONFIGURATION DATA",
				"KEYBIND_TOGGLE_RECORD":"59 98",
				"KEYBIND_TOGGLE_AUTOCLICK":"59 100",
				"KEYBIND_TOGGLE_PLAYBACK":"59 101"
			}
			globalconfwizard.pack("~/.neoprisma",conf_data)
			
		self.hotkeys["play"] = set(int(i) for i in conf_data["KEYBIND_TOGGLE_PLAYBACK"].split(" "))
		self.hotkeys["record"] = set(int(i) for i in conf_data["KEYBIND_TOGGLE_RECORD"].split(" "))
		self.hotkeys["auto"] = set(int(i) for i in conf_data["KEYBIND_TOGGLE_AUTOCLICK"].split(" "))

		self.error_emitter = Emitter()
		self.error_emitter.error.connect(lambda msg: QMessageBox.critical(None,"neoprisma: an error occured",msg if len(msg) <= 300 else msg[:300],QMessageBox.StandardButton.Ok))

		self.app.setQuitOnLastWindowClosed(False)

		self.icon_static = QIcon(resource_path("assets/neoprisma-static.png"))
		self.icon_rec = QIcon(resource_path("assets/neoprisma-rec.png"))
		self.icon_play = QIcon(resource_path("assets/neoprisma-play.png"))
		self.icon_auto = QIcon(resource_path("assets/neoprisma-ac.png"))

		self.tray = QSystemTrayIcon()
		self.tray.setIcon(self.icon_static)
		self.tray.setVisible(True)

		# Create the menu
		self.menu = QMenu()

		self.toggle_rec_widget = QAction("Toggle Recording")
		self.toggle_rec_widget.triggered.connect(self.toggle_recording)
		self.toggle_play_widget = QAction("Toggle Playback")
		self.toggle_play_widget.triggered.connect(self.toggle_playback)
		self.toggle_auto_widget = QAction("Toggle Autoclicker")
		self.toggle_auto_widget.triggered.connect(self.toggle_autoclicker)

		self.load_widget = QAction("Load Recording")
		self.load_widget.triggered.connect(self.load)
		self.save_widget = QAction("Save Recording")
		self.save_widget.triggered.connect(self.save)
		self.conf_widget = QAction("Settings (COMING SOON)")

		self.menu.addActions([self.toggle_rec_widget,self.toggle_play_widget,self.toggle_auto_widget,self.load_widget,self.save_widget,self.conf_widget])

		# Add a Quit option to the menu.
		quit = QAction("Quit")
		quit.triggered.connect(self.app.quit)
		self.menu.addAction(quit)

		self.settingsw = QWidget()
		self.settingsw.setWindowTitle("Settings")
		self.settingsw_label = QLabel("hi",self.settingsw)
		self.settingsw_speedslider = QSlider()
		self.settingsw_speedslider.setRange(0,10)
		self.settingsw_speedslider.setValue(5)
		self.settingsw_speedslider.valueChanged.connect()
		self.settingsw.show()

		# Add the menu to the tray
		self.tray.setContextMenu(self.menu)

		QTimer.singleShot(0,self.start_hotkeys)
		QTimer.singleShot(0,self.init_recorder_and_simulator)
		self.app.exec()

	def listener_hotkeysv2_handlekeypress(self,key:pynput.keyboard.Key|pynput.keyboard.KeyCode): # this is a very long name
		vk = key.vk if isinstance(key,pynput.keyboard.KeyCode) else key.value.vk
		self.keysdown.add(vk)
	def listener_hotkeysv2_handlekeyrelease(self,key:pynput.keyboard.Key|pynput.keyboard.KeyCode): # this is a very long name too
		vk = key.vk if isinstance(key,pynput.keyboard.KeyCode) else key.value.vk
		self.keysdown.discard(vk)


	def init_recorder_and_simulator(self):
			try:
				self.recorder=recorder.OneShotRecorder()
				self.m_simulator = pynput.mouse.Controller()
			except Exception:
				self.error_emitter.error.emit("Could not initialize recorder.OneShotRecorder or pynput.mouse.Controller: "+traceback.format_exc())

	def start_hotkeys(self):
		try:
			self.h = pynput.keyboard.GlobalHotKeys({
			'<ctrl>+<f7>': self.toggle_recording,
			'<ctrl>+<f9>': self.toggle_playback,
			'<ctrl>+<f8>': self.toggle_autoclicker},
			on_error=self.error_emitter.error.emit)
			self.h.start()
		except Exception:
			self.error_emitter.error.emit("Could not start the global hotkey listener: "+traceback.format_exc())

	def toggle_recording(self):
		try:
			if self.state_playback or self.state_autoclicker: return
			if self.state_recording:
				self.recorder.stop()
			self.arr = copy.deepcopy(self.recorder.buffer)
			if self.state_recording:
				self.tray.setIcon(self.icon_static)
				self.state_recording = False
			else: 
				self.state_recording = True
				self.recorder.start()
				self.tray.setIcon(self.icon_rec)
		except Exception:
			self.error_emitter.error.emit(traceback.format_exc())

	def toggle_playback(self):
		try:
			if self.state_recording or self.state_autoclicker: return
			if self.state_playback:
				self.tray.setIcon(self.icon_static)
				playback.abortPlayback()
				self.state_playback = False
			else:
				self.tray.setIcon(self.icon_play)
				self.state_playback = True
				playback.resetAbortPlayback()
				def inner():
					try:
						self.compiled_arr = playback.CompileEventArray(self.arr)[0]
						if len(self.compiled_arr) == 0: 
							self.tray.setIcon(self.icon_static)
							playback.abortPlayback()
							self.state_playback = False
							return
					except RuntimeError as e:
						self.error_emitter.error.emit(str(e))
						self.tray.setIcon(self.icon_static)
						playback.abortPlayback()
						self.state_playback = False
					except Exception as e:
						self.error_emitter.error.emit(traceback.format_exc())
						self.tray.setIcon(self.icon_static)
						playback.abortPlayback()
						self.state_playback = False
					while self.state_playback:
						try:
							playback.PlayEventList(self.compiled_arr,self.timestamp_multiplier)
						except Exception as e:
							self.error_emitter.error.emit(traceback.format_exc())
							self.tray.setIcon(self.icon_static)
							playback.abortPlayback()
							self.state_playback = False
							break
				t = Thread(target=inner)
				t.start()
		except Exception:
			self.error_emitter.error.emit(traceback.format_exc())

	def toggle_autoclicker(self):
		try:
			if self.state_recording or self.state_playback: return
			if self.state_autoclicker:
				self.tray.setIcon(self.icon_static)
				self.state_autoclicker = False
			else:
				self.tray.setIcon(self.icon_auto)
				self.state_autoclicker = True
				def inner():
					while self.state_autoclicker:
						mpos = self.m_simulator.position
						playback.mouseButtonStatus(1,int(mpos[0]),int(mpos[1]),True)
						time.sleep(0.0003)
						playback.mouseButtonStatus(1,int(mpos[0]),int(mpos[1]),False)
						time.sleep(0.0003)
				t = Thread(target=inner)
				t.start()
				

		except Exception:
			self.error_emitter.error.emit(traceback.format_exc())
			
	def load(self):

		try:
			file, _ = QFileDialog.getOpenFileName(None,"Select a recording to load",filter="Recordings (*.neop);;All Files (*)")
			if file == "": return
			else:
				with open(file,"rb") as fstream:
					dat = bytearray(fstream.read())
					try:
						playback.CompileEventArray(dat)
					except RuntimeError as e:
						self.error_emitter.error.emit(str(e))
					else: 
						self.arr = bytearray(dat)
					
		except Exception:
			self.error_emitter.error.emit(traceback.format_exc())

	def save(self):

		try:
			file, _ = QFileDialog.getSaveFileName(None,"Select a location to save your recording",filter="Recordings (*.neop)")
			if file == "": return
			else:
				with open(file,"wb") as fstream:
					fstream.write(self.arr)
		except Exception:
			self.error_emitter.error.emit(traceback.format_exc())


m = Main()