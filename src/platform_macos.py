import os, sys

if getattr(sys, "frozen", False):
	BASE = sys._MEIPASS
else:
	BASE = os.path.dirname(__file__)

SRC = os.path.join(BASE, "src")
if SRC not in sys.path:
	sys.path.insert(0, SRC)

import objc, CoreFoundation
objc.registerCFSignature("CFStringRef", b"^{__CFString=}", CoreFoundation.CFStringGetTypeID(), "NSString")

import playback
import recorder
import globalconfwizard
import pynput
import requests
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
	QDoubleSpinBox,
	QSlider,
	QPushButton,
	QVBoxLayout,
	QHBoxLayout
)
from resources import resource_path
import version
__version__ = version.__version__

def latest():
	url = f"https://api.github.com/repos/prismaticdepths/neoprisma/releases/latest"
	try:
		resp = requests.get(url, timeout=5)
		resp.raise_for_status()
		data = resp.json()
		tag = data.get("tag_name")
		if tag:
			return tag
		return "0.0.0"
	except requests.RequestException:
		return "0.0.0"

def version_dif(inp):

	current = __version__.split(".")
	latest = inp.split(".")
	for i in range(3):
		if latest[i] > current[i]: 
			return True, inp
		elif latest[i] < current[i]:
			return False, inp
	return False, inp

class Emitter(QObject):
	error = pyqtSignal(str)

class Main(QObject):

	signal_restart = pyqtSignal()

	def __init__(self):
		super().__init__()

		self.app = QApplication(sys.argv)

		self.update_available, self.latest_version = version_dif(latest())

		self.arr = bytearray(b"<NEOPRISMA>\x01")
		self.compiled_arr:list[playback.EventPacket] = []
		self.state_recording = False
		self.state_playback = False
		self.state_autoclicker = False
		self.timestamp_multiplier = 1
		self.cps = 100
		self.keysdown = set()
		self.hotkeys = {
			"KEYBIND_TOGGLE_RECORD": set(),
			"KEYBIND_TOGGLE_PLAYBACK": set(),
			"KEYBIND_TOGGLE_AUTOCLICK": set()
		}

		if os.path.exists(os.path.expanduser("~/.neoprisma")):
			self.conf_data=globalconfwizard.unpack(os.path.expanduser("~/.neoprisma"))
		else:
			self.conf_data={
				"DOC":"NEOPRISMA CONFIGURATION DATA",
				"KEYBIND_TOGGLE_RECORD":"59 98",
				"KEYBIND_TOGGLE_AUTOCLICK":"59 100",
				"KEYBIND_TOGGLE_PLAYBACK":"59 101"
			}
			globalconfwizard.pack(os.path.expanduser("~/.neoprisma"),self.conf_data)

		for key in self.conf_data.keys():
			if key.startswith("KEYBIND"):
				self.hotkeys[key] = set(int(i) for i in self.conf_data[key].split(" "))

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
		self.conf_widget = QAction("Settings")
		self.conf_widget.triggered.connect(self.settingsw_popup)

		self.menu.addActions([self.toggle_rec_widget,self.toggle_play_widget,self.toggle_auto_widget,self.load_widget,self.save_widget,self.conf_widget])

		# Add a Quit option to the menu.
		self.quitaction = QAction("Quit")
		self.quitaction.triggered.connect(self.app.quit)
		self.menu.addAction(self.quitaction)

		self.settingsw = QWidget()
		self.settingsw.setBaseSize(300,500)
		self.settingsw_layout = QVBoxLayout()
		self.settingsw.setLayout(self.settingsw_layout)
		self.settingsw.setWindowTitle("Settings")
		self.settingsw_label = QLabel("Hotkeys are disabled while this window is active.",self.settingsw)
		self.settingsw_layout.addWidget(self.settingsw_label)
		self.settingsw_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
		#self.settingsw_speedslider = QSlider()
		#self.settingsw_speedslider.setRange(0,2)
		#self.settingsw_speedslider.setValue(1)
		#self.settingsw_speedslider.valueChanged.connect()
		self.settingsw_hk_rec = QPushButton("Set RECORD hotkey to currently held keys",self.settingsw)
		self.settingsw_hk_play = QPushButton("Set PLAYBACK hotkey to currently held keys",self.settingsw)
		self.settingsw_hk_auto = QPushButton("Set AUTOCLICK hotkey to currently held keys",self.settingsw)
		self.settingsw_hk_rec.clicked.connect(lambda: self.set_hk("KEYBIND_TOGGLE_RECORD"))
		self.settingsw_hk_play.clicked.connect(lambda: self.set_hk("KEYBIND_TOGGLE_PLAYBACK"))
		self.settingsw_hk_auto.clicked.connect(lambda: self.set_hk("KEYBIND_TOGGLE_AUTOCLICK"))
		self.settingsw_layout.addWidget(self.settingsw_hk_rec)
		self.settingsw_layout.addWidget(self.settingsw_hk_play)
		self.settingsw_layout.addWidget(self.settingsw_hk_auto)

		self.settingsw_speededit = QWidget()
		self.settingsw_speededit_layout = QHBoxLayout()
		self.settingsw_speededit.setLayout(self.settingsw_speededit_layout)
		self.settingsw_speededit_input = QDoubleSpinBox()
		self.settingsw_speededit_input.setRange(0.01,100)
		self.settingsw_speededit_input.setValue(1)
		self.settingsw_speededit_input.valueChanged.connect(self.upd_speed)
		self.settingsw_speededit_label = QLabel("(Playback) Speed multiplier:",self.settingsw_speededit)
		self.settingsw_speededit_layout.addWidget(self.settingsw_speededit_label)
		self.settingsw_speededit_layout.addWidget(self.settingsw_speededit_input)
		self.settingsw_layout.addWidget(self.settingsw_speededit)

		self.settingsw_cpsedit = QWidget()
		self.settingsw_cpsedit_layout = QHBoxLayout()
		self.settingsw_cpsedit.setLayout(self.settingsw_cpsedit_layout)
		self.settingsw_cpsedit_input = QDoubleSpinBox()
		self.settingsw_cpsedit_input.setRange(0.01,2200)
		self.settingsw_cpsedit_input.setValue(100)
		self.settingsw_cpsedit_input.valueChanged.connect(self.upd_cps)
		self.settingsw_cpsedit_label = QLabel("(Autoclick) Target clicks/second:",self.settingsw_cpsedit)
		self.settingsw_cpsedit_layout.addWidget(self.settingsw_cpsedit_label)
		self.settingsw_cpsedit_layout.addWidget(self.settingsw_cpsedit_input)
		self.settingsw_layout.addWidget(self.settingsw_cpsedit)
		self.settingsw_layout.addWidget(self.settingsw_speededit)

		self.settingsw_save = QPushButton("Save configurations",self.settingsw)
		self.settingsw_save.clicked.connect(self.save_configurations)
		self.settingsw_layout.addWidget(self.settingsw_save)
		self.tray.setContextMenu(self.menu)

		self.signal_restart.connect(self.start_hotkeys)

		QTimer.singleShot(0,self.start_hotkeys)
		QTimer.singleShot(0,self.init_recorder_and_simulator)


		self.listener_keepalive = QTimer(self)
		self.listener_keepalive.timeout.connect(self.poll_hotkey_listener_alive)
		self.listener_keepalive.start(20000)

		if self.update_available:
			QTimer.singleShot(0,self.prompt_update)

	def prompt_update(self):

		QMessageBox.information(None,"Update available!",f"A new version of Neoprisma is available.\n\nYou currently have version {__version__}, and a newer version {self.latest_version} is now available for download.\n\nVisit the project's GitHub repository for more information.",QMessageBox.StandardButton.Ok)

	def settingsw_popup(self):
		self.settingsw.show()
		self.settingsw.activateWindow()
		self.settingsw.raise_()

	def upd_speed(self,x):
		if x == 0: return
		self.timestamp_multiplier=1/x
	def upd_cps(self,x):
		if x == 0: return
		self.cps = 1/(2*x)

	def save_configurations(self):
		globalconfwizard.pack(os.path.expanduser("~/.neoprisma"),self.conf_data)

	def set_hk(self,hk):
		if len(self.keysdown) > 0:
			self.hotkeys[hk] = copy.deepcopy(self.keysdown)
			if hk == "KEYBIND_TOGGLE_RECORD": self.recorder.update_hk(self.hotkeys[hk])
			if hk.startswith("KEYBIND"): 
				self.conf_data[hk] = " ".join([str(i) for i in self.keysdown])

	def listener_hotkeysv2_handlekeypress(self,key:pynput.keyboard.Key|pynput.keyboard.KeyCode,i): # this is a very long name
		try:
			if i or key is None: return
			vk = key.vk if isinstance(key,pynput.keyboard.KeyCode) else key.value.vk
			self.keysdown.add(vk)
			if self.settingsw.isActiveWindow(): return
			if self.keysdown == self.hotkeys["KEYBIND_TOGGLE_RECORD"]:
				self.toggle_recording()
			elif self.keysdown == self.hotkeys["KEYBIND_TOGGLE_PLAYBACK"]:
				self.toggle_playback()
			elif self.keysdown == self.hotkeys["KEYBIND_TOGGLE_AUTOCLICK"]:
				self.toggle_autoclicker()
		except Exception:
			self.error_emitter.error.emit(traceback.format_exc())
	def listener_hotkeysv2_handlekeyrelease(self,key:pynput.keyboard.Key|pynput.keyboard.KeyCode,i): # this is a very long name too
		if i: return
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
			if hasattr(self, "h") and self.h:
				self.h.stop()

			self.h = pynput.keyboard.Listener(
				self.listener_hotkeysv2_handlekeypress,
				self.listener_hotkeysv2_handlekeyrelease,
				suppress=False,
			)
			self.h.start()
			self.h.wait()
		except Exception:
			self.error_emitter.error.emit("Could not start the hotkey listener: "+traceback.format_exc())


	def poll_hotkey_listener_alive(self):
		if not self.h.is_alive():
			self.signal_restart.emit()

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
						time.sleep(self.cps)
						playback.mouseButtonStatus(1,int(mpos[0]),int(mpos[1]),False)
						time.sleep(self.cps)
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
m.app.exec()