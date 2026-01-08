import playback
import recorder
import pynput
import copy
import traceback
import sys
from threading import Thread
from PyQt6.QtGui import QAction,QIcon
from PyQt6.QtCore import QObject,pyqtSignal
from PyQt6.QtWidgets import QApplication,QSystemTrayIcon,QMenu, QFileDialog, QMessageBox, QWidget

class Emitter(QObject):
	error = pyqtSignal(str)

class Main:

	def __init__(self):
		self.recorder = recorder.OneShotRecorder()
		self.arr = bytearray()
		self.compiled_arr:list[playback.EventPacket] = []
		self.state_recording = False
		self.state_playback = False
		self.state_autoclicker = False
		
		self.error_emitter = Emitter()
		self.error_emitter.error.connect(lambda msg: QMessageBox.critical(None,"neoprisma: an error occured",msg,QMessageBox.StandardButton.Ok))

		self.app = QApplication(sys.argv)
		self.app.setQuitOnLastWindowClosed(False)

		self.icon_static = QIcon("icon.png")
		self.icon_rec = QIcon("cbimage.png")
		self.icon_play = QIcon("cbimage-2.png")
		self.icon_auto = QIcon("icon.png")

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

		h = pynput.keyboard.GlobalHotKeys({
		'<ctrl>+<f7>': self.toggle_recording,
		'<ctrl>+<f9>': self.toggle_playback,
		'<ctrl>+<f8>': self.toggle_autoclicker})

		h.start()
		self.app.exec()

	def toggle_recording(self):
		try:
			if self.state_playback or self.state_autoclicker: return
			print('rec:', not self.state_recording)
			if self.state_recording: self.recorder.stop()
			self.arr = copy.deepcopy(self.recorder.buffer)
			self.recorder = recorder.OneShotRecorder()
			if self.state_recording:
				self.tray.setIcon(self.icon_static)
				self.state_recording = False
			else: 
				self.tray.setIcon(self.icon_rec)
				self.state_recording = True
				self.recorder.start()
		except Exception:
			self.error_emitter.error.emit(traceback.format_exc(250))

	def toggle_playback(self):
		try:
			if self.state_recording or self.state_autoclicker: return
			print('play:', not self.state_playback)
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
					except RuntimeError as e:
						self.error_emitter.error.emit(str(e))
						self.toggle_playback()
					except Exception as e:
						self.error_emitter.error.emit(traceback.format_exc())
						self.toggle_playback()
					while self.state_playback:
						try:
							playback.PlayEventList(self.compiled_arr)
						except Exception as e:
							self.error_emitter.error.emit(traceback.format_exc())
							self.toggle_playback()
							break
				t = Thread(target=inner)
				t.start()
		except Exception:
			self.error_emitter.error.emit(traceback.format_exc())

	def toggle_autoclicker(self):

		try:
			if self.state_recording or self.state_playback: return
			print('auto:', not self.state_autoclicker)
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