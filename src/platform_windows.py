""" # License
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
	EXEPATH = os.path.dirname(sys.executable)
	BASE = sys._MEIPASS
else:
	EXEPATH = ""
	BASE = os.path.dirname(__file__)

SRC = os.path.join(BASE, "src")
if SRC not in sys.path:
	sys.path.insert(0, SRC)

try:
	import version
except Exception:
	crash_later = True
else: 
	__version__ = version.__version__
	crash_later = False

def crash(headline="Neoprisma encountered an error and has to crash.", detail="No short details available.", error_msg="", exit_code=1):
	from PyQt6.QtWidgets import (
		QApplication,
		QMessageBox
	)
	import os, sys, traceback, platform, time
	app = QApplication.instance()
	if app is None: app = QApplication(sys.argv)
	box = QMessageBox()
	box.setIcon(QMessageBox.Icon.Critical)
	box.setText(headline)
	box.setInformativeText("Please report this issue to the developers!\n\nYou can press \"Show Details...\" to see the full crash report. Include the entire crash log if you file a bug report.\nPressing \"Abort\" or closing the crash dialog will terminate this process.")
	box.setDetailedText(f"""--- Crash Summary ---
Report generated in file: `{__name__}`
Crash headline: {headline}
Shorthand crash detail: {detail}
Neoprisma version: {__version__ if not crash_later else 'Unknown'}
Time of crash: {time.asctime(time.localtime())}
Platform: {platform.platform()}
Exit code: {exit_code}
--- Traceback ---
{error_msg if error_msg != "" else traceback.format_exc()}""")
	box.addButton(QMessageBox.StandardButton.Abort)
	box.setStyleSheet("""QWidget {
		background-color: #303030;
		color: #DEDEDE;
		font-size: 13px;
	}

	QPushButton {
		background-color: #535353;
		border: 0px solid #000000;
		border-radius: 6px;
		padding: 4px 8px;
		color: #E0E0E0;
	}

	QPushButton:hover {
		background-color: #404046;
		border: 1px solid #444444;
		color: #FFFFFF;
	}
	QLineEdit, QTextEdit, QPlainTextEdit {
		background-color: #1A1A1A;
		font-family: 'Courier New', monospace;
		font-size: 10pt;
		border: 1px solid #2A2A2A;
		border-radius: 1px;
		text-align: left;
		padding: 5px;
		color: #FFFFFF;
	}""")
	box.setWindowTitle("Neoprisma Crash Info")
	print(error_msg if error_msg != "" else traceback.format_exc())
	box.exec()
	sys.exit(exit_code)

def exception_hook(exctype, value, tb):
	import traceback
	error_msg = "".join(traceback.format_exception(exctype, value, tb))
	crash(error_msg=error_msg)

sys.excepthook = exception_hook

if crash_later: crash("Missing version file! Please reinstall Neoprisma.")

import pynput
import requests
import copy
import traceback
import time
from threading import Thread
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, Qt
from PyQt6.QtWidgets import (
	QApplication,
	QSystemTrayIcon,
	QMenu, 
	QFileDialog, 
	QMessageBox, 
	QWidget, 
	QLabel,
	QPushButton,
	QVBoxLayout,
	QHBoxLayout,
	QScrollArea,
)

from utils import resource_path

try:
	import playback, recorder
except Exception:
	crash("Failed to start Neoprisma!", "Fatal error while importing components of the app in separate Python modules/files.", exit_code=70)

import globalconfwizard
from globalconfwizard import CNVKeyset, CNVString, CNVBoolean, CNVInteger, CNVFloat, CNVPoint2D
from constants import *

CN_CONFIGURATION_DEFAULTS = {
	"DOC": CNVString("NEOPRISMA CONFIGURATION DATA"),
	"VERSION": CNVInteger(2),
	"KEYBIND_TOGGLE_RECORD": CNVKeyset(set([162, 118])),  # Ctrl + F7
	"KEYBIND_TOGGLE_AUTOCLICK": CNVKeyset(set([162, 119])),  # Ctrl + F8
	"KEYBIND_TOGGLE_PLAYBACK": CNVKeyset(set([162, 120])),  # Ctrl + F9
	"RELEASE_CHANNEL": CNVString("stable"),
	"ABORT_PLAYBACK_ON_INPUT": CNVBoolean(False, description="Stops playback immediately upon any user input.", category="Playback"),
	"HIDE_APP_ICON": CNVBoolean(False, description="Hides dock/taskbar icon when no windows are open.", category="General"),
	"USE_MOUSE_WARPING": CNVBoolean(False, description="Move the mouse instantly without emitting movement events.", category="Playback"),
	"DELAY_BEFORE_PLAYBACK": CNVFloat(0, description="Delay in seconds before playback starts.", smin=0, smax=60, category="Playback"),
	"COMPENSATE_AUTOCLICKER_DRIFT": CNVBoolean(True, description="Adjusts delay to compensate OS drift.", category="Autoclicking"),
	"LOCK_AUTOCLICK_TO_POINT": CNVBoolean(False, "Autoclick at a specific point on-screen.", category="Autoclicking"),
	"AUTOCLICK_TARGET": CNVPoint2D([0, 0], description="Target coordinates if lock point is active.", category="Autoclicking"),
	"HOOK_KEYPRESS_EVENTS": CNVBoolean(True, description="Allows scripts to read keypresses.", category="Scripts"),
	"HOOK_MOUSE_EVENTS": CNVBoolean(True, description="Allows scripts to read mouse movement.", category="Scripts"),
	"LIMIT_PLAYBACK_LOOPS": CNVBoolean(False, description="Limit amount of playback loops.", category="Playback"),
	"MAX_PLAYBACK_LOOPS": CNVInteger(1, description="Maximum playback loop count.", category="Playback", smin=1, smax=1000000),
}

def latest():
	url = "https://api.github.com/repos/prismaticdepths/neoprisma/releases/latest"
	try:
		resp = requests.get(url, timeout=5)
		resp.raise_for_status()
		data = resp.json()
		return data.get("tag_name", "0.0.0")
	except requests.RequestException:
		return "0.0.0"

def version_dif(inp):
	current = __version__.split(".")
	latest_ver = inp.split(".")
	for i in range(3):
		if int(latest_ver[i]) > int(current[i]): 
			return True, inp
		elif int(latest_ver[i]) < int(current[i]):
			return False, inp
	return False, inp

class Emitter(QObject):
	error = pyqtSignal(str)

class Main(QObject):

	def __init__(self):
		super().__init__()
		
		self.app = QApplication.instance()
		if self.app is None: self.app = QApplication(sys.argv)
		self.app.setStyleSheet(MASTER_STYLESHEET)
		self.app.setQuitOnLastWindowClosed(False)

		QTimer.singleShot(0, self.init_input_devices)

		self.arr = bytearray(b"<NEOPRISMA>\x01")
		self.compiled_arr = []

		self.state_recording = False
		self.state_playback = False
		self.state_autoclicker = False

		self.timestamp_multiplier = 1
		self.recording_hotkey = False
		self.hotkey_record_buffer = set()
		self.hotkey_lookup = {}
		self.hotkey_edit_label = "" 
		self.windows_open = 0
		self.cps = (1 / 100)
		self.keysdown = set()
		self.hotkeys = {
			"KEYBIND_TOGGLE_RECORD": set(),
			"KEYBIND_TOGGLE_PLAYBACK": set(),
			"KEYBIND_TOGGLE_AUTOCLICK": set()
		}

		config_path = os.path.expanduser("~/.neoprisma")
		self.conf_data = copy.deepcopy(CN_CONFIGURATION_DEFAULTS)
		if os.path.exists(config_path):
			try:
				conf_data = globalconfwizard.unpack(config_path)
			except Exception:
				globalconfwizard.pack(config_path, self.conf_data)
			else:
				for key, value in conf_data.items():
					if key in self.conf_data:
						self.conf_data[key] = value
		else:
			globalconfwizard.pack(config_path, self.conf_data)

		for key in self.conf_data.keys():
			if key.startswith("KEYBIND"):
				self.hotkeys[key] = self.conf_data[key].get_value()

		self.rebuild_hotkey_lookup()
		self.update_available, self.latest_version = version_dif(latest())

		self.error_emitter = Emitter()
		self.error_emitter.error.connect(lambda msg: QMessageBox.critical(None, "Neoprisma Error", msg, QMessageBox.StandardButton.Ok))

		# Tray icons
		self.icon_static = QIcon(resource_path("assets/neoprisma-static.png"))
		self.icon_rec = QIcon(resource_path("assets/neoprisma-rec.png"))
		self.icon_play = QIcon(resource_path("assets/neoprisma-play.png"))
		self.icon_auto = QIcon(resource_path("assets/neoprisma-ac.png"))

		self.tray = QSystemTrayIcon()
		self.tray.setIcon(self.icon_static)
		self.tray.setVisible(True)

		self.menu = QMenu()
		self.filemenu = QMenu("File")

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
		self.quitaction = QAction("Quit")
		self.quitaction.triggered.connect(self.shutdown)

		self.filemenu.addActions([self.load_widget, self.save_widget])
		self.menu.addMenu(self.filemenu)
		self.menu.addActions([self.toggle_rec_widget, self.toggle_play_widget, self.toggle_auto_widget, self.conf_widget, self.quitaction])

		# Settings UI
		self.settingsw = QWidget()
		self.settingsw_layout = QVBoxLayout()
		self.settingsw.setLayout(self.settingsw_layout)
		self.settingsw.setWindowTitle("Settings")

		self.settingsw_scroll = QScrollArea()
		self.settingsw_scroll.setWidgetResizable(True)
		self.settingsw_scroll.setWidget(self.settingsw)
		self.settingsw_scroll.setWindowTitle("Settings")

		self.settingsw_label_hkheader = QLabel("Hotkeys", self.settingsw) 
		self.settingsw_label_hkheader.setStyleSheet("font-weight: bold; color: white;")
		self.settingsw_label_hkheader.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.settingsw_layout.addWidget(self.settingsw_label_hkheader)

		self.settingsw_hk_layout = QVBoxLayout()
		self.settingsw_hk_rec_layout = QHBoxLayout()
		self.settingsw_hk_rec = QPushButton("Edit RECORD hotkey", self.settingsw)
		self.settingsw_hk_rec_disp = QLabel(" + ".join([self.vk_to_name(i) for i in self.hotkeys["KEYBIND_TOGGLE_RECORD"]]))
		self.settingsw_hk_rec_disp.setAlignment(Qt.AlignmentFlag.AlignRight)
		self.settingsw_hk_rec_layout.addWidget(self.settingsw_hk_rec)
		self.settingsw_hk_rec_layout.addWidget(self.settingsw_hk_rec_disp)

		self.settingsw_hk_play_layout = QHBoxLayout()
		self.settingsw_hk_play = QPushButton("Edit PLAYBACK hotkey", self.settingsw)
		self.settingsw_hk_play_disp = QLabel(" + ".join([self.vk_to_name(i) for i in self.hotkeys["KEYBIND_TOGGLE_PLAYBACK"]]))
		self.settingsw_hk_play_disp.setAlignment(Qt.AlignmentFlag.AlignRight)
		self.settingsw_hk_play_layout.addWidget(self.settingsw_hk_play)
		self.settingsw_hk_play_layout.addWidget(self.settingsw_hk_play_disp)

		self.settingsw_hk_auto_layout = QHBoxLayout()
		self.settingsw_hk_auto = QPushButton("Edit AUTOCLICK hotkey", self.settingsw)
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
		self.settingsw_layout.addLayout(self.settingsw_hk_layout)

		self.settingsw_save = QPushButton("Save configurations", self.settingsw)
		self.settingsw_save.clicked.connect(self.save_configurations)
		self.settingsw_layout.addWidget(self.settingsw_save)

		self.tray.setContextMenu(self.menu)
		self.auto_thread = None

	def shutdown(self):
		self.app.quit()

	def rebuild_hotkey_lookup(self):
		self.hotkey_lookup.clear()
		self.hotkey_lookup[frozenset(self.hotkeys["KEYBIND_TOGGLE_RECORD"])] = self.toggle_recording
		self.hotkey_lookup[frozenset(self.hotkeys["KEYBIND_TOGGLE_PLAYBACK"])] = self.toggle_playback
		self.hotkey_lookup[frozenset(self.hotkeys["KEYBIND_TOGGLE_AUTOCLICK"])] = self.toggle_autoclicker

	def settingsw_popup(self):
		self.settingsw_scroll.show()
		self.settingsw.show()
		self.settingsw.activateWindow()

	def save_configurations(self):
		globalconfwizard.pack(os.path.expanduser("~/.neoprisma"), self.conf_data)

	def set_hk(self, hk):
		if self.recording_hotkey and self.hotkey_edit_label != hk: return
		self.recording_hotkey = not self.recording_hotkey
		if self.recording_hotkey:
			self.hotkey_record_buffer = set()
			self.hotkey_edit_label = hk
		else:
			if len(self.hotkey_record_buffer) > 0:
				self.hotkeys[hk] = copy.deepcopy(self.hotkey_record_buffer)
				self.rebuild_hotkey_lookup()
				if hk == "KEYBIND_TOGGLE_RECORD": self.recorder.update_hk(self.hotkeys[hk])
				if hk.startswith("KEYBIND"): 
					self.conf_data[hk].set_value(self.hotkeys[hk])

	def vk_to_name(self, vk):
		try:
			key_obj = pynput.keyboard.KeyCode.from_vk(vk)
			if key_obj in pynput.keyboard.Key:
				return pynput.keyboard.Key(key_obj).name
			if hasattr(key_obj, 'char') and key_obj.char:
				return key_obj.char
		except Exception:
			pass
		return f"VK_{vk}"

	def listener_hotkeysv2_handlekeypress(self, key, injected=False):
		try:
			if injected or (key is None): return False
			vk = key.vk if isinstance(key, pynput.keyboard.KeyCode) else (key.value.vk if hasattr(key.value, 'vk') else None)
			if vk is None: return False
			self.keysdown.add(vk)

			if self.state_playback and self.conf_data["ABORT_PLAYBACK_ON_INPUT"].real_value: 
				self.toggle_playback()
				return False

			if self.recording_hotkey and len(self.hotkey_record_buffer) < MAX_HOTKEY_LEN:
				self.hotkey_record_buffer.add(vk)
				return False
			
			if len(self.keysdown) > MAX_HOTKEY_LEN or self.settingsw.isActiveWindow(): return False

			trigger = self.hotkey_lookup.get(frozenset(self.keysdown))
			if trigger: 
				trigger()
				return True
		except Exception:
			self.error_emitter.error.emit(traceback.format_exc())

	def listener_hotkeysv2_handlekeyrelease(self, key, injected=False):
		if injected: return
		vk = key.vk if isinstance(key, pynput.keyboard.KeyCode) else (key.value.vk if hasattr(key.value, 'vk') else None)
		if vk: self.keysdown.discard(vk)

	def init_input_devices(self):
		try:
			self.keyboard_listener = pynput.keyboard.Listener(
				on_press=self.master_on_press,
				on_release=self.master_on_release,
				suppress=False,
			)
			self.mouse_listener = pynput.mouse.Listener(
				on_move=self.master_on_move,
				on_click=self.master_on_click,
				on_scroll=self.master_on_scroll,
			)
			self.recorder = recorder.OneShotRecorder()
			self.m_simulator = pynput.mouse.Controller()
			
			self.keyboard_listener.start()
			self.keyboard_listener.wait()
			self.mouse_listener.start()
			self.mouse_listener.wait()
		except Exception:
			crash(headline="An error occurred while initializing recording/playback infrastructure.", detail="Could not initialize input devices.")

	def master_on_press(self, key, injected=False):
		t = time.perf_counter_ns() - self.recorder.starting_time
		if injected: return
		triggered_hotkey = self.listener_hotkeysv2_handlekeypress(key, injected)
		if triggered_hotkey: return
		if self.recorder.running: self.recorder.captured_key_press(key, t, injected)

	def master_on_release(self, key, injected=False):
		t = time.perf_counter_ns() - self.recorder.starting_time
		if injected: return
		self.listener_hotkeysv2_handlekeyrelease(key, injected)
		if self.recorder.running: self.recorder.captured_key_release(key, t, injected)

	def master_on_move(self, x, y, injected=False):
		t = time.perf_counter_ns() - self.recorder.starting_time
		if injected: return
		if self.recorder.running: self.recorder.captured_mouse_move(x, y, t)

	def master_on_click(self, x, y, button, pressed, injected=False):
		t = time.perf_counter_ns() - self.recorder.starting_time
		if injected: return
		if self.recorder.running: self.recorder.captured_mouse_click(x, y, button, pressed, t)

	def master_on_scroll(self, x, y, dx, dy, injected=False):
		t = time.perf_counter_ns() - self.recorder.starting_time
		if injected: return
		if self.recorder.running: self.recorder.captured_mouse_scroll(x, y, dx, dy, t)

	def toggle_recording(self):
		try:
			if self.state_playback or self.state_autoclicker: return
			if self.state_recording:
				self.recorder.stop()
				self.arr = copy.deepcopy(self.recorder.buffer)
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
					except Exception:
						self.error_emitter.error.emit(traceback.format_exc())
						self.tray.setIcon(self.icon_static)
						playback.abortPlayback()
						self.state_playback = False
						return

					time.sleep(self.conf_data["DELAY_BEFORE_PLAYBACK"].real_value)
					if not self.state_playback: return
					count = 0
					while self.state_playback:
						try:
							if (count >= self.conf_data["MAX_PLAYBACK_LOOPS"].real_value) and self.conf_data["LIMIT_PLAYBACK_LOOPS"].real_value:
								self.tray.setIcon(self.icon_static)
								self.state_playback = False
								break
							playback.PlayEventList(self.compiled_arr, self.timestamp_multiplier, self.conf_data["USE_MOUSE_WARPING"].real_value)
							count += 1
						except Exception:
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
				self.auto_thread = Thread(target=self._INNER_toggle_autoclicker_simple)
				self.auto_thread.start()
		except Exception:
			self.error_emitter.error.emit(traceback.format_exc())

	def _INNER_toggle_autoclicker_simple(self):
		while self.state_autoclicker:
			playback.mouseButtonStatus(1, True)
			time.sleep(0)
			playback.mouseButtonStatus(1, False)
			time.sleep(self.cps)

	def load(self):
		try:
			file, _ = QFileDialog.getOpenFileName(None, "Select a recording to load", "", filter="Recordings (*.neop);;All Files (*)")
			if file:
				with open(file, "rb") as fstream:
					dat = bytearray(fstream.read())
					playback.CompileEventArray(dat)
					self.arr = bytearray(dat)
		except Exception:
			self.error_emitter.error.emit(traceback.format_exc())

	def save(self):
		try:
			file, _ = QFileDialog.getSaveFileName(None, "Select a location to save your recording", "", filter="Recordings (*.neop)")
			if file:
				with open(file, "wb") as fstream:
					fstream.write(self.arr)
		except Exception:
			self.error_emitter.error.emit(traceback.format_exc())

try:
	m = Main()
except Exception:
	crash(headline="Failed to start Neoprisma!", detail="Uncaught exception in `Main` class initialization.", exit_code=70)

sys.exit(m.app.exec())