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
import pynput
import copy
import traceback
import time
import sys
from threading import Thread
from PyQt6.QtGui import QAction,QIcon
from PyQt6.QtCore import QObject,pyqtSignal, QTimer, QMetaObject, Qt
from PyQt6.QtWidgets import QApplication,QSystemTrayIcon,QMenu, QFileDialog, QMessageBox, QWidget
from resources import resource_path


class DummyRecorder:
	buffer = bytearray(b"<NEOPRISMA>\x01")

class Emitter(QObject):
	error = pyqtSignal(str)

class sig(QObject):
	s = pyqtSignal()

from PyQt6.QtCore import QObject, pyqtSignal

class MainThreadInvoker(QObject):
	call_signal = pyqtSignal(object)  # emit a callable

	def __init__(self):
		super().__init__()
		self.call_signal.connect(self._run)

	def _run(self, func):
		# This executes in the main thread
		func()


class Main:

	def __init__(self):

		self.app = QApplication(sys.argv)

		self.arr = bytearray(b"<NEOPRISMA>\x01")
		self.compiled_arr:list[playback.EventPacket] = []
		self.state_recording = False
		self.state_playback = False
		self.state_autoclicker = False
		self.timestamp_multiplier = 1
		self.dummy_recorder = None
		
		self.error_emitter = Emitter()
		self.error_emitter.error.connect(lambda msg: QMessageBox.critical(None,"neoprisma: an error occured",msg if len(msg) <= 300 else msg[:300],QMessageBox.StandardButton.Ok))

		self.signal_toggle_recording = sig()
		self.signal_toggle_playback = sig()
		self.signal_toggle_autoclicker = sig()
		self.signal_toggle_recording.s.connect(self.toggle_recording)
		self.signal_toggle_playback.s.connect(self.toggle_playback)
		self.signal_toggle_autoclicker.s.connect(self.toggle_autoclicker)

		self.thread_helper = MainThreadInvoker()

		self.app.setQuitOnLastWindowClosed(False)

		self.icon_static = QIcon(resource_path("assets/icon.png"))
		self.icon_rec = QIcon(resource_path("assets/cbimage.png"))
		self.icon_play = QIcon(resource_path("assets/cbimage-2.png"))
		self.icon_auto = QIcon(resource_path("assets/icon.png"))

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
		self.conf_widget = QAction("Settings")

		self.menu.addActions([self.toggle_rec_widget,self.toggle_play_widget,self.toggle_auto_widget,self.load_widget,self.save_widget,self.conf_widget])

		# Add a Quit option to the menu.
		quit = QAction("Quit")
		quit.triggered.connect(self.app.quit)
		self.menu.addAction(quit)

		# Add the menu to the tray
		self.tray.setContextMenu(self.menu)

		QTimer.singleShot(0,self.start_hotkeys)
		QTimer.singleShot(0,self.init_dummy_recorder)
		QTimer.singleShot(0,self.init_recorder_and_simulator)
		self.app.exec()

	def init_dummy_recorder(self):
		try:
			self.dummy_recorder = recorder.OneShotRecorder()
		except Exception:
			self.error_emitter.error.emit(traceback.format_exc())

	def init_recorder_and_simulator(self):
			try:
				self.recorder=recorder.OneShotRecorder()
				self.m_simulator = pynput.mouse.Controller()
			except Exception:
				self.error_emitter.error.emit("Could not initialize recorder.OneShotRecorder or pynput.mouse.Controller: "+traceback.format_exc())

	def start_hotkeys(self):
		try:
			self.h = pynput.keyboard.GlobalHotKeys({
			'<ctrl>+<f7>': self._toggle_recording,
			'<ctrl>+<f9>': self._toggle_playback,
			'<ctrl>+<f8>': self._toggle_autoclicker},
			on_error=self.error_emitter.error.emit)
			self.h.start()
		except Exception:
			self.error_emitter.error.emit("Could not start the global hotkey listener: "+traceback.format_exc())

	def _toggle_recording(self):
		#self.signal_toggle_recording.s.emit()
		#QTimer.singleShot(0,self.toggle_recording)
		#QMetaObject.invokeMethod(self.app,self.toggle_recording,Qt.ConnectionType.QueuedConnection)
		self.thread_helper.call_signal.emit(self.toggle_recording)
	def _toggle_playback(self):
		#self.signal_toggle_playback.s.emit()
		#QTimer.singleShot(0,self.toggle_playback)
		#QMetaObject.invokeMethod(self.app,self.toggle_playback,Qt.ConnectionType.QueuedConnection)
		self.thread_helper.call_signal.emit(self.toggle_playback)
	def _toggle_autoclicker(self):
		#self.signal_toggle_autoclicker.s.emit()
		#QTimer.singleShot(0,self.toggle_autoclicker)
		#QMetaObject.invokeMethod(self.app,self.toggle_autoclicker,Qt.ConnectionType.QueuedConnection)
		self.thread_helper.call_signal.emit(self.toggle_autoclicker)
	def toggle_recording(self):
		self.error_emitter.error.emit("R")
		print("received: toggle recording")
		try:
			if self.state_playback or self.state_autoclicker: return
			# print('rec:', not self.state_recording)
			if self.state_recording: 
				self.recorder.stop()
				time.sleep(0.05)
			self.arr = copy.deepcopy(self.recorder.buffer)
		
			self.recorder = copy.deepcopy(self.dummy_recorder)
			self.error_emitter.error.emit("R")
			time.sleep(0)
			if self.state_recording:
				self.tray.setIcon(self.icon_static)
				self.state_recording = False
			else: 
				self.tray.setIcon(self.icon_rec)
				self.state_recording = True
				QTimer.singleShot(0,self.recorder.start)
		except Exception:
			self.error_emitter.error.emit(traceback.format_exc())

	def toggle_playback(self):
		try:
			if self.state_recording or self.state_autoclicker: return
			# print('play:', not self.state_playback)
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