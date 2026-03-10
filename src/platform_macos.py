""" 
Neoprisma Copyright (C) 2026 PrismaticDepths <prismaticdepths@gmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>
"""

import os, sys

if getattr(sys, "frozen", False):
	EXEPATH = os.path.dirname(os.path.dirname(os.path.dirname(sys.executable)))
	BASE = sys._MEIPASS
else:
	EXEPATH = ""
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
from threading import Thread
from PyQt6.QtGui import QAction,QIcon
from PyQt6.QtCore import QObject,pyqtSignal, QTimer, Qt
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
	QHBoxLayout,
	QMenuBar
)
from resources import resource_path
import version
__version__ = version.__version__

MACOS_VK_MAP = {
	0: 'a', 11: 'b', 8: 'c', 2: 'd', 14: 'e', 3: 'f', 5: 'g', 4: 'h', 34: 'i',
	38: 'j', 40: 'k', 37: 'l', 46: 'm', 45: 'n', 31: 'o', 35: 'p', 12: 'q',
	15: 'r', 1: 's', 17: 't', 32: 'u', 9: 'v', 13: 'w', 7: 'x', 16: 'y', 6: 'z',
	29: '0', 18: '1', 19: '2', 20: '3', 21: '4', 23: '5', 22: '6', 26: '7', 28: '8', 25: '9',
	49: 'space', 36: 'newline', 48: 'tab',
	24: '=', 27: '-', 33: '[', 30: ']', 42: '\\', 41: ';', 39: "'", 43: ',', 47: '.', 44: '/', 50: '`'
}

CONFIGURATION_DEFAULTS = {
	"DOC":"NEOPRISMA CONFIGURATION DATA",
	"KEYBIND_TOGGLE_RECORD":"59 98",
	"KEYBIND_TOGGLE_AUTOCLICK":"59 100",
	"KEYBIND_TOGGLE_PLAYBACK":"59 101",
	"RELEASE_CHANNEL":"stable"
}

MAX_HOTKEY_LEN = 5

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
		if int(latest[i]) > int(current[i]): 
			return True, inp
		elif int(latest[i]) < int(current[i]):
			return False, inp
	return False, inp

def run_updater():

	import tempfile
	import os
	import sys
	import subprocess

	command = f"#!/bin/zsh\ncurl -fsSL https://raw.githubusercontent.com/PrismaticDepths/neoprisma/stable/install.sh | $SHELL {'-s -- -i '+os.path.dirname(EXEPATH) if EXEPATH != '' else ''}; open -a neoprisma"
	with tempfile.NamedTemporaryFile(suffix=".command",delete=False,mode="w") as f:
		f.write(command)
		tmpath=f.name
	os.chmod(tmpath, 0o755)
	subprocess.Popen(["open", tmpath])

class Emitter(QObject):
	error = pyqtSignal(str)

class Main(QObject):

	def __init__(self):
		super().__init__()

		

		self.app = QApplication(sys.argv)

		try: # force the "about" pane to appear on the left of the system menu bar
			import AppKit
			AppKit.NSApp.setActivationPolicy_(AppKit.NSApplicationActivationPolicyRegular)
			self.app.setApplicationName("neoprisma")
			self.menu_bar = QMenuBar(None) 
			self.about_action = QAction("About neoprisma", None)
			self.about_action.setMenuRole(QAction.MenuRole.AboutRole)
			self.about_action.triggered.connect(
				lambda: AppKit.NSApp.orderFrontStandardAboutPanel_(None)
			)
			self.dummy_menu = self.menu_bar.addMenu("App")
			self.dummy_menu.addAction(self.about_action)
		except Exception:
			pass

		self.arr = bytearray(b"<NEOPRISMA>\x01")
		self.compiled_arr:list[playback.EventPacket] = []
		self.state_recording = False
		self.state_playback = False
		self.state_autoclicker = False
		self.timestamp_multiplier = 1
		self.recording_hotkey = False
		self.hotkey_record_buffer = set()
		self.hotkey_lookup = {}
		self.hotkey_edit_label = ""
		self.cps = 1/100
		self.keysdown = set()
		self.hotkeys = {
			"KEYBIND_TOGGLE_RECORD": set(),
			"KEYBIND_TOGGLE_PLAYBACK": set(),
			"KEYBIND_TOGGLE_AUTOCLICK": set()
		}
		self.conf_data=copy.deepcopy(CONFIGURATION_DEFAULTS)
		if os.path.exists(os.path.expanduser("~/.neoprisma")):
			conf_data=globalconfwizard.unpack(os.path.expanduser("~/.neoprisma"))
			for key,value in conf_data.items():
				self.conf_data[key] = value
		else:
			self.conf_data=CONFIGURATION_DEFAULTS
			globalconfwizard.pack(os.path.expanduser("~/.neoprisma"),self.conf_data)

		for key in self.conf_data.keys():
			if key.startswith("KEYBIND"):
				self.hotkeys[key] = set(int(i) for i in self.conf_data[key].split(" "))

		self.rebuild_hotkey_lookup()

		self.update_available, self.latest_version = version_dif(latest())

		self.error_emitter = Emitter()
		self.error_emitter.error.connect(lambda msg: QMessageBox.critical(None,"neoprisma: an error occured",msg if len(msg) <= 350 else msg[:350],QMessageBox.StandardButton.Ok))

		self.app.setQuitOnLastWindowClosed(False)

		self.icon_static = QIcon(resource_path("assets/neoprisma-static.png"))
		self.icon_rec = QIcon(resource_path("assets/neoprisma-rec.png"))
		self.icon_play = QIcon(resource_path("assets/neoprisma-play.png"))
		self.icon_auto = QIcon(resource_path("assets/neoprisma-ac.png"))

		self.tray = QSystemTrayIcon()
		self.tray.setIcon(self.icon_static)
		self.tray.setVisible(True)

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

		self.quitaction = QAction("Quit")
		self.quitaction.triggered.connect(self.shutdown)
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

		self.settingsw_hk_layout = QVBoxLayout()

		self.settingsw_hk_rec_layout = QHBoxLayout()
		self.settingsw_hk_rec = QPushButton("Edit RECORD hotkey",self.settingsw)
		self.settingsw_hk_rec_disp = QLabel(" + ".join([self.vk_to_name(i) for i in self.hotkeys["KEYBIND_TOGGLE_RECORD"]]))
		self.settingsw_hk_rec_disp.setAlignment(Qt.AlignmentFlag.AlignRight)
		self.settingsw_hk_rec_layout.addWidget(self.settingsw_hk_rec)
		self.settingsw_hk_rec_layout.addWidget(self.settingsw_hk_rec_disp)

		self.settingsw_hk_play_layout = QHBoxLayout()
		self.settingsw_hk_play = QPushButton("Edit PLAYBACK hotkey",self.settingsw)
		self.settingsw_hk_play_disp = QLabel(" + ".join([self.vk_to_name(i) for i in self.hotkeys["KEYBIND_TOGGLE_PLAYBACK"]]))
		self.settingsw_hk_play_disp.setAlignment(Qt.AlignmentFlag.AlignRight)
		self.settingsw_hk_play_layout.addWidget(self.settingsw_hk_play)
		self.settingsw_hk_play_layout.addWidget(self.settingsw_hk_play_disp)

		self.settingsw_hk_auto_layout = QHBoxLayout()
		self.settingsw_hk_auto = QPushButton("Edit AUTOCLICK hotkey",self.settingsw)
		self.settingsw_hk_auto_disp = QLabel(" + ".join([self.vk_to_name(i) for i in self.hotkeys["KEYBIND_TOGGLE_AUTOCLICK"]]))
		self.settingsw_hk_auto_disp.setAlignment(Qt.AlignmentFlag.AlignRight)
		self.settingsw_hk_auto_layout.addWidget(self.settingsw_hk_auto)
		self.settingsw_hk_auto_layout.addWidget(self.settingsw_hk_auto_disp)

		self.settingsw_hk_rec.clicked.connect(lambda: self.set_hk("KEYBIND_TOGGLE_RECORD"))
		self.settingsw_hk_play.clicked.connect(lambda: self.set_hk("KEYBIND_TOGGLE_PLAYBACK"))
		self.settingsw_hk_auto.clicked.connect(lambda: self.set_hk("KEYBIND_TOGGLE_AUTOCLICK"))
		self.settingsw_hk_layout.addLayout(self.settingsw_hk_rec_layout)
		self.settingsw_hk_layout.addLayout(self.settingsw_hk_play_layout)
		self.settingsw_hk_layout.addLayout(self.settingsw_hk_auto_layout)
		self.settingsw_hk_layout.setSpacing(1)
		self.settingsw_hk_layout.setContentsMargins(0, 0, 0, 0)
		self.settingsw_layout.addLayout(self.settingsw_hk_layout)

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

		self.settingsw_layout.setSpacing(5)
		self.settingsw_hk_layout.setContentsMargins(0, 0, 0, 0)

		self.settingsw_save = QPushButton("Save configurations",self.settingsw)
		self.settingsw_save.clicked.connect(self.save_configurations)
		self.settingsw_layout.addWidget(self.settingsw_save)

		self.tray.setContextMenu(self.menu)

		self.run_workers = True
		self.auto_thread = None

		QTimer.singleShot(0,self.start_hotkeys)
		QTimer.singleShot(0,self.init_recorder_and_simulator)
		
		if self.update_available:
			QTimer.singleShot(0,self.prompt_update)

	def shutdown(self):
		self.run_workers = False
		self.app.quit()

	def rebuild_hotkey_lookup(self):
		self.hotkey_lookup.clear()
		self.hotkey_lookup[frozenset(self.hotkeys["KEYBIND_TOGGLE_RECORD"])] = self.toggle_recording
		self.hotkey_lookup[frozenset(self.hotkeys["KEYBIND_TOGGLE_PLAYBACK"])] = self.toggle_playback
		self.hotkey_lookup[frozenset(self.hotkeys["KEYBIND_TOGGLE_AUTOCLICK"])] = self.toggle_autoclicker

	def prompt_update(self):

		#QMessageBox.information(None,"Update available!",f"A new version of Neoprisma is available.\n\nYou currently have version {__version__}, and a newer version {self.latest_version} is now available for download.\n\nVisit the project's GitHub repository for more information.",QMessageBox.StandardButton.Ok)
		win=QWidget()

		win.setWindowTitle(f"Installer ({__version__} -> {self.latest_version})")
		winl = QVBoxLayout()
		footl = QHBoxLayout()
		win.setLayout(winl)
		
		header_label = QLabel(f"A new version of Neoprisma is available!\n")
		version_label = QLabel(f"Currently installed: {__version__}\nLatest version: {self.latest_version}")
		footer_label = QLabel(f"<a href='https://github.com/PrismaticDepths/neoprisma/releases/tag/{self.latest_version}'>View Release</a>  ❖  <a href='https://github.com/PrismaticDepths/neoprisma/compare/{__version__}...{self.latest_version}'>Full Changelog</a>")
		footer_label.setOpenExternalLinks(True)
		header_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
		version_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
		footer_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
		dismiss_button = QPushButton("Dismiss")
		update_button = QPushButton("Update")
		winl.addWidget(header_label)
		winl.addWidget(version_label)
		winl.addWidget(footer_label)
		footl.addWidget(update_button)
		footl.addWidget(dismiss_button)
		winl.addLayout(footl)

		def close_window():
			win.destroy()
		def update():
			win.destroy()
			run_updater()
			self.shutdown()

		dismiss_button.clicked.connect(close_window)
		update_button.clicked.connect(update)

		win.show()
		win.activateWindow()
		win.raise_()

	def settingsw_popup(self):
		self.settingsw.show()
		self.settingsw.activateWindow()
		self.settingsw.raise_()

	def upd_speed(self,x):
		if x == 0: return
		self.timestamp_multiplier=1/x

	def upd_cps(self,x):
		if x == 0: return
		self.cps = 1/x

	def save_configurations(self):
		globalconfwizard.pack(os.path.expanduser("~/.neoprisma"),self.conf_data)

	def set_hk(self,hk):
		if self.recording_hotkey and self.hotkey_edit_label != hk: return
		self.recording_hotkey = not self.recording_hotkey
		if self.recording_hotkey:
			self.hotkey_record_buffer = set()
			self.hotkey_edit_label = hk
			if hk == "KEYBIND_TOGGLE_RECORD":
				self.settingsw_hk_rec.setText("[Click to stop listening...]")
				self.settingsw_hk_rec_disp.setText("")
			elif hk == "KEYBIND_TOGGLE_PLAYBACK":
				self.settingsw_hk_play.setText("[Click to stop listening...]")
				self.settingsw_hk_play_disp.setText("")
			elif hk == "KEYBIND_TOGGLE_AUTOCLICK":
				self.settingsw_hk_auto.setText("[Click to stop listening...]")
				self.settingsw_hk_auto_disp.setText("")
		else:
			if hk == "KEYBIND_TOGGLE_RECORD":
				self.settingsw_hk_rec.setText("Edit RECORD hotkey")
			elif hk == "KEYBIND_TOGGLE_PLAYBACK":
				self.settingsw_hk_play.setText("Edit PLAYBACK hotkey")
			elif hk == "KEYBIND_TOGGLE_AUTOCLICK":
				self.settingsw_hk_auto.setText("Edit AUTOCLICK hotkey")
			if len(self.hotkey_record_buffer) > 0:
				self.hotkeys[hk] = copy.deepcopy(self.hotkey_record_buffer)
				self.rebuild_hotkey_lookup()
				if hk == "KEYBIND_TOGGLE_RECORD": self.recorder.update_hk(self.hotkeys[hk])
				if hk.startswith("KEYBIND"): 
					self.conf_data[hk] = " ".join([str(i) for i in self.hotkey_record_buffer])

	def vk_to_name(self,vk):
		if vk == 49: return MACOS_VK_MAP[vk]
		if pynput.keyboard.KeyCode.from_vk(vk) in pynput.keyboard.Key:
			return pynput.keyboard.Key(pynput.keyboard.KeyCode.from_vk(vk)).name
		else:
			try:
				return MACOS_VK_MAP[vk]
			except Exception:
				return f"⍰<{vk}>"

	def listener_hotkeysv2_handlekeypress(self,key:pynput.keyboard.Key|pynput.keyboard.KeyCode,injected=False): # this is a very long name
		# Injected: Whether the event is authentic or software generated. We can detect our own key events with this. Pynput 1.8.0+
		try:
			if (injected==True) or (key is None): return

			vk = key.vk if isinstance(key,pynput.keyboard.KeyCode) else key.value.vk
			self.keysdown.add(vk)

			if self.recording_hotkey and len(self.hotkey_record_buffer) < MAX_HOTKEY_LEN:
				self.hotkey_record_buffer.add(vk)
				text = " + ".join([self.vk_to_name(i) for i in self.hotkey_record_buffer])
				if self.hotkey_edit_label == "KEYBIND_TOGGLE_RECORD":
					self.settingsw_hk_rec_disp.setText(text)
				elif self.hotkey_edit_label == "KEYBIND_TOGGLE_PLAYBACK":
					self.settingsw_hk_play_disp.setText(text)
				elif self.hotkey_edit_label == "KEYBIND_TOGGLE_AUTOCLICK":
					self.settingsw_hk_auto_disp.setText(text)
				return
			
			if (len(self.keysdown) > MAX_HOTKEY_LEN) or (self.settingsw.isActiveWindow()): return

			trigger = self.hotkey_lookup.get(frozenset(self.keysdown))
			if trigger: trigger()

		except Exception:
			self.error_emitter.error.emit(traceback.format_exc())

	def listener_hotkeysv2_handlekeyrelease(self,key:pynput.keyboard.Key|pynput.keyboard.KeyCode,injected=False): # this is a very long name too
		if injected==True: return
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
				on_press=self.listener_hotkeysv2_handlekeypress,
				on_release=self.listener_hotkeysv2_handlekeyrelease,
				suppress=False,
			)
			self.h.start()
		except Exception:
			self.error_emitter.error.emit("Could not start the hotkey listener: "+traceback.format_exc())

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
				self.auto_thread = Thread(target=self._INNER_toggle_autoclicker)
				self.auto_thread.start()
				
		except Exception:
			self.error_emitter.error.emit(traceback.format_exc())
			
	def _INNER_toggle_autoclicker(self):
		while self.state_autoclicker:
			playback.mouseButtonStatus(1,int(self.m_simulator.position[0]),int(self.m_simulator.position[1]),True)
			time.sleep(self.cps)
			playback.mouseButtonStatus(1,int(self.m_simulator.position[0]),int(self.m_simulator.position[1]),False)
			if not self.state_autoclicker: break
			time.sleep(self.cps)

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
sys.exit(m.app.exec())
