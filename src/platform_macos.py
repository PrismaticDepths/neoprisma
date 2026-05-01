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


try:
	import version
except Exception:
	__version__ = "0.0.0"
else:
	__version__ = version.__version__

def crash(headline="Neoprisma encountered an error and has to crash.",detail="No short details available.",error_msg="",exit_code=1):
	from PyQt6.QtWidgets import (
		QApplication,
		QMessageBox
	)
	import os,sys,traceback,platform,time
	app = QApplication.instance()
	if app is None: app = QApplication(sys.argv)
	box = QMessageBox()
	box.setIcon(QMessageBox.Icon.Critical)
	box.setText(headline)
	box.setInformativeText(f"Please report this issue to the developers!\n\nYou can press \"Show Details...\" to see the full crash report. Include the entire crash log if you file a bug report.\nPressing \"Abort\" or closing the crash dialog will terminate this process.")
	box.setDetailedText(f"""--- Crash Summary ---
Report generated in file: `{__name__}`
Crash headline: {headline}
Shorthand crash detail: {detail}
Neoprisma version: {__version__}
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

import pynput
import requests
import copy
import traceback
import time
from threading import Thread
from PyQt6.QtGui import QAction,QIcon
from PyQt6.QtCore import QObject,pyqtSignal, QTimer, Qt, QEvent,QPoint
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
	QMenuBar,
	QSizePolicy,
	QScrollArea,
	QToolTip
)



from resources import resource_path
try:
	import playback
	import recorder
	import globalconfwizard
	# Extensions
	import ext_scripting_macos
	#import ext_editor_macos
	from globalconfwizard import CNVKeyset,CNVString,CNVType,CNVBoolean,CNVInteger,CNVFloat
except Exception:
	crash("Failed to start Neoprisma!","Fatal error while importing components of the app in seperate Python modules/files.",exit_code=70)

MASTER_STYLESHEET = """
	QWidget {
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

	QPushButton:pressed {
		background-color: #1A1A1A;
		border: 1px solid #222222;
	}

	QLineEdit, QTextEdit, QPlainTextEdit {
		background-color: #1A1A1A;
		border: 1px solid #2A2A2A;
		border-radius: 1px;
		padding: 5px;
		color: #FFFFFF;
	}

	QLineEdit:focus {
		border: 1px solid #555555;
	}

	/*QCheckBox::indicator {
		width: 16px;
		height: 16px;
		background-color: #1A1A1A;
		border: 2px solid #444444;
		border-radius: 4px;
	}

	QCheckBox::indicator:checked {
		background-color: #00B467;
	}*/

	QCheckBox::indicator {
    	width: 16px;
   		height: 16px;
	}


	QScrollBar:vertical {
		border: none;
		background: #121212;
		width: 8px;
	}

	QScrollBar::handle:vertical {
		background: #333333;
		min-height: 20px;
		border-radius: 4px;
	}

	QScrollBar::handle:vertical:hover {
		background: #444444;
	}
	QScrollBar:horizontal {
		border: none;
		background: #121212;
		width: 8px;
	}

	QScrollBar::handle:horizontal {
		background: #333333;
		min-height: 20px;
		border-radius: 4px;
	}

	QScrollBar::handle:horizontal:hover {
		background: #444444;
	}

	QLabel#heading {
		color: #FFFFFF;
		font-weight: bold;
		font-size: 16px;
	}
	QLabel#script-status-long {
		color: #BDBDBD;
		font-size: 8px;
	}
	QPushButton#info-popup {
		border-radius: 8px;
		background-color: #535353;
		border: 1px solid #000000;
		width: 16px;
   		height: 16px;
		margin: 0;
        padding: 0;
	}
	QPushButton:pressed#info-popup {
	}
	QPushButton:hover#info-popup {
	}
	QPushButton#status-red {
		border-radius: 8px;
		background-color: #FF0000;
		border: 1px solid #000000;
		width: 16px;
   		height: 16px;
		margin: 0;
        padding: 0;
	}
	QPushButton:pressed#status-red {
	}
	QPushButton:hover#status-red {
	}
	QPushButton#status-green {
		border-radius: 8px;
		background-color: #32FF64;
		border: 1px solid #000000;
		width: 16px;
   		height: 16px;
		margin: 0;
        padding: 0;
	}
	QPushButton:pressed#status-green {
	}
	QPushButton:hover#status-green {
	}
	QPushButton#status-yellow {
		border-radius: 8px;
		background-color: #FFFA05;
		border: 1px solid #000000;
		width: 16px;
   		height: 16px;
		margin: 0;
        padding: 0;
	}
	QPushButton:pressed#status-yellow {
	}
	QPushButton:hover#status-yellow {
	}
	
"""

MACOS_VK_MAP = {
	0: 'a', 11: 'b', 8: 'c', 2: 'd', 14: 'e', 3: 'f', 5: 'g', 4: 'h', 34: 'i',
	38: 'j', 40: 'k', 37: 'l', 46: 'm', 45: 'n', 31: 'o', 35: 'p', 12: 'q',
	15: 'r', 1: 's', 17: 't', 32: 'u', 9: 'v', 13: 'w', 7: 'x', 16: 'y', 6: 'z',
	29: '0', 18: '1', 19: '2', 20: '3', 21: '4', 23: '5', 22: '6', 26: '7', 28: '8', 25: '9',
	49: 'space', 36: 'newline', 48: 'tab',
	24: '=', 27: '-', 33: '[', 30: ']', 42: '\\', 41: ';', 39: "'", 43: ',', 47: '.', 44: '/', 50: '`'
}

CN_CONFIGURATION_DEFAULTS = {
	"DOC":CNVString("NEOPRISMA CONFIGURATION DATA"),
	"VERSION":CNVInteger(2),
	"KEYBIND_TOGGLE_RECORD":CNVKeyset(set([59,98])),
	"KEYBIND_TOGGLE_AUTOCLICK":CNVKeyset(set([59,100])),
	"KEYBIND_TOGGLE_PLAYBACK":CNVKeyset(set([59,101])),
	"RELEASE_CHANNEL":CNVString("stable"),
	"ABORT_PLAYBACK_ON_INPUT":CNVBoolean(False,description="Stops playback immediately upon any\nuser generated (authentic) keyboard input.",category="Playback"),
	"HIDE_APP_ICON":CNVBoolean(True,description="If no UI elements (like this settings window) are open,\nhides the app icon from the dock and excludes from the command-tab switcher.",category="General"),
	"USE_MOUSE_WARPING":CNVBoolean(False,description="Move the mouse instantly without emitting mouse movement events.\nCan fix issues with some video games.",category="Playback"),
	"DELAY_BEFORE_PLAYBACK":CNVFloat(0,description="After playback is triggered, wait the specified number of seconds\nbefore actually starting playback.",smin=0,smax=60,category="Playback"),
	"COMPENSATE_AUTOCLICKER_DRIFT":CNVBoolean(True,description="Intelligently adjusts autoclicker delay to compensate for drift and overhead added by the OS.\nIncreases CPS, but also raises CPU usage.",category="Autoclicking"),
	"HOOK_KEYPRESS_EVENTS":CNVBoolean(True,description="Allows userscripts to log keypresses and receive keypress data. Also uses more CPU.",category="Scripts"),
	"HOOK_MOUSE_EVENTS":CNVBoolean(True,description="Allows userscripts to log mouse movement and clicks and receive mouse data. Also uses more CPU.",category="Scripts")
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
		self.app.setStyleSheet(MASTER_STYLESHEET)

		try: # force the "about" pane to appear on the left of the system menu bar
			import AppKit
			AppKit.NSApp.setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)
			self.app.setApplicationName("neoprisma")
			self.menu_bar = QMenuBar(None) 
			self.about_action = QAction("About Neoprisma", None)
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
		self.cps = (1/100)
		self.keysdown = set()
		self.hotkeys = {
			"KEYBIND_TOGGLE_RECORD": set(),
			"KEYBIND_TOGGLE_PLAYBACK": set(),
			"KEYBIND_TOGGLE_AUTOCLICK": set()
		}
		self.conf_data=copy.deepcopy(CN_CONFIGURATION_DEFAULTS)
		if os.path.exists(os.path.expanduser("~/.neoprisma")):
			try:
				conf_data=globalconfwizard.unpack(os.path.expanduser("~/.neoprisma")) # Try unpacking the config
			except RuntimeError as e: # Handle cases where the file might be outdated and need migration
				if str(e).strip().startswith("NO_VERSION"):

					conf_data=copy.deepcopy(CN_CONFIGURATION_DEFAULTS) # Since we don't have the real unpacked version, grab the default values

					with open(os.path.expanduser("~/.neoprisma"),"r") as cfile: # Legacy unpack function
						for line in cfile.readlines():
							key=line.split("%")[0].strip().upper()
							val=line.split("%")[1].strip()
							conf_data[key].set_value_from_packed(val)

					for key,value in conf_data.items(): # Inefficiently copy the values with the same mechanism normally used
						self.conf_data[key]=value
					globalconfwizard.pack(os.path.expanduser("~/.neoprisma"),self.conf_data) # Write the migrated configuration file

				elif str(e).strip().startswith("LOW_VERSION"):
					pass # migrate to updated version, if there were a new one now
			except Exception as e: # Handle exceptions not intentionally raised
				QMessageBox.warning(None,"Error","Your configuration file appears to be corrupted; please delete hidden file '~/.neoprisma' to reset configurations. Neoprisma will now crash.")
				raise # Exit "gracefully" and show crash details
			else: # part of the try catch logic, not an if-then-else statement
				for key,value in conf_data.items(): # If everything goes right, load the configurations
					self.conf_data[key]=value 
					self.conf_data[key].description=CN_CONFIGURATION_DEFAULTS[key].description
					self.conf_data[key].category=CN_CONFIGURATION_DEFAULTS[key].category
		else: # Generate new configurations if no file is found
			self.conf_data=copy.deepcopy(CN_CONFIGURATION_DEFAULTS)
			globalconfwizard.pack(os.path.expanduser("~/.neoprisma"),self.conf_data)

		for key in self.conf_data.keys():
			if key.startswith("KEYBIND"):
				self.hotkeys[key] = self.conf_data[key].get_value()

		self.rebuild_hotkey_lookup()

		self.update_available, self.latest_version = version_dif(latest())

		self.error_emitter = Emitter()
		self.error_emitter.error.connect(lambda msg: QMessageBox.critical(None,"neoprisma: an error occured",msg,QMessageBox.StandardButton.Ok))

		self.app.setQuitOnLastWindowClosed(False)

		self.icon_static = QIcon(resource_path("assets/neoprisma-static.png"))
		self.icon_rec = QIcon(resource_path("assets/neoprisma-rec.png"))
		self.icon_play = QIcon(resource_path("assets/neoprisma-play.png"))
		self.icon_auto = QIcon(resource_path("assets/neoprisma-ac.png"))

		self.tray = QSystemTrayIcon()
		self.tray.setIcon(self.icon_static)
		self.tray.setVisible(True)

		self.script_ext=ext_scripting_macos.Runner()

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

		self.scrextaction = QAction("Scripts")
		self.scrextaction.triggered.connect(self.script_ext.mainw.show)
		self.menu.addAction(self.scrextaction)

		self.settingsw = QWidget()
		
		self.settingsw_layout = QVBoxLayout()
		self.settingsw.setLayout(self.settingsw_layout)
		self.settingsw.setWindowTitle("Settings")

		self.settingsw_scroll = QScrollArea()
		self.settingsw_scroll.setWidgetResizable(True)
		self.settingsw_scroll.setWidget(self.settingsw)
		self.settingsw_scroll.setBaseSize(300,500)

		self.settingsw_label_hkheader = QLabel("Hotkeys",self.settingsw)
		self.settingsw_label_hkheader.setStyleSheet("font-weight: bold; color: white;")
		self.settingsw_label_hkheader.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.settingsw_layout.addWidget(self.settingsw_label_hkheader)

		self.settingsw_label = QLabel("Hotkeys are disabled while this window is active.",self.settingsw)
		self.settingsw_label.setStyleSheet("color: gray;")
		self.settingsw_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.settingsw_layout.addWidget(self.settingsw_label)
		
		self.settingsw_layout.addSpacing(10)

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
		self.settingsw_hk_rec.setCursor(Qt.CursorShape.PointingHandCursor)
		self.settingsw_hk_play.setCursor(Qt.CursorShape.PointingHandCursor)
		self.settingsw_hk_auto.setCursor(Qt.CursorShape.PointingHandCursor)
		self.settingsw_hk_rec.clicked.connect(lambda: self.set_hk("KEYBIND_TOGGLE_RECORD"))
		self.settingsw_hk_play.clicked.connect(lambda: self.set_hk("KEYBIND_TOGGLE_PLAYBACK"))
		self.settingsw_hk_auto.clicked.connect(lambda: self.set_hk("KEYBIND_TOGGLE_AUTOCLICK"))
		self.settingsw_hk_layout.addLayout(self.settingsw_hk_rec_layout)
		self.settingsw_hk_layout.addLayout(self.settingsw_hk_play_layout)
		self.settingsw_hk_layout.addLayout(self.settingsw_hk_auto_layout)
		self.settingsw_hk_layout.setSpacing(2)
		self.settingsw_hk_layout.setContentsMargins(0, 0, 0, 0)
		self.settingsw_layout.addLayout(self.settingsw_hk_layout)


		self.settingsw_layout.addSpacing(10)
		self.settingsw_label_speedheader = QLabel("Speed Adjust",self.settingsw)
		self.settingsw_label_speedheader.setStyleSheet("font-weight: bold; color: white;")
		self.settingsw_label_speedheader.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.settingsw_layout.addWidget(self.settingsw_label_speedheader)
		self.settingsw_layout.addSpacing(10)

		self.settingsw_speededit = QWidget()
		self.settingsw_speededit_layout = QHBoxLayout()
		self.settingsw_speededit.setLayout(self.settingsw_speededit_layout)
		self.settingsw_speededit_input = QDoubleSpinBox()
		self.settingsw_speededit_input.setRange(0.01,100)
		self.settingsw_speededit_input.setValue(1)
		self.settingsw_speededit_input.valueChanged.connect(self.upd_speed)
		self.settingsw_speededit_label = QLabel("Playback Speed Multiplier",self.settingsw_speededit)
		self.settingsw_speededit_layout.addWidget(self.settingsw_speededit_label)
		self.settingsw_speededit_layout.addWidget(self.settingsw_speededit_input,alignment=Qt.AlignmentFlag.AlignRight)
		self.settingsw_speededit_layout.setContentsMargins(0, 0, 0, 0)
		self.settingsw_cpsedit = QWidget()
		self.settingsw_cpsedit_layout = QHBoxLayout()
		self.settingsw_cpsedit.setLayout(self.settingsw_cpsedit_layout)
		self.settingsw_cpsedit_input = QDoubleSpinBox()
		self.settingsw_cpsedit_input.setRange(0.01,2200)
		self.settingsw_cpsedit_input.setValue(100)
		self.settingsw_cpsedit_input.valueChanged.connect(self.upd_cps)
		self.settingsw_cpsedit_label = QLabel("Autoclick Target Clicks/Second",self.settingsw_cpsedit)
		self.settingsw_cpsedit_layout.addWidget(self.settingsw_cpsedit_label)
		self.settingsw_cpsedit_layout.addWidget(self.settingsw_cpsedit_input,alignment=Qt.AlignmentFlag.AlignRight)
		self.settingsw_cpsedit_layout.setContentsMargins(0, 0, 0, 0)
		self.settingsw_layout.addWidget(self.settingsw_cpsedit)
		self.settingsw_layout.addWidget(self.settingsw_speededit)

		def add_conf_bool(key,value):
				tmp=QWidget()
				tmplayout=QHBoxLayout()
				tmp.setLayout(tmplayout)
				nice_label = key.strip().replace("_"," ").title()
				tmp1=QLabel(nice_label,tmp)
				tmp1.setAlignment(Qt.AlignmentFlag.AlignLeft)
				tmp2=QCheckBox()
				tmp2.setChecked(value.real_value)
				tmp2.checkStateChanged.connect(lambda t: self.conf_data[key].set_value(False if t==Qt.CheckState.Unchecked else True))
				tmplayout.addWidget(tmp1)
				if self.conf_data[key].description != "":
					tmp3 = QPushButton("?",tmp)
					tmp3.setObjectName("info-popup")
					tmp3.setFixedSize(16, 16)
					tmp3.setCursor(Qt.CursorShape.PointingHandCursor)
					def show_info():
						pos = tmp3.mapToGlobal(QPoint(0, -5))
						QToolTip.showText(pos, self.conf_data[key].description, tmp3)
					tmp3.clicked.connect(show_info)
					tmplayout.addWidget(tmp3,alignment=Qt.AlignmentFlag.AlignLeft)

				tmplayout.addWidget(tmp2,alignment=Qt.AlignmentFlag.AlignRight)
				tmplayout.setContentsMargins(0, 0, 0, 0)
				return tmp

		def add_conf_num(key,value):
				tmp=QWidget()
				tmplayout=QHBoxLayout()
				tmp.setLayout(tmplayout)
				nice_label = key.strip().replace("_"," ").title()
				tmp1=QLabel(nice_label,tmp)
				tmp1.setAlignment(Qt.AlignmentFlag.AlignLeft)
				tmp2=QDoubleSpinBox()
				tmp2.setMinimum(0)
				tmp2.setValue(value.real_value)
				tmp2.valueChanged.connect(lambda t: self.conf_data[key].set_value(int(t) if self.conf_data[key].name=="int" else float(t)))
				if self.conf_data[key].name=="int": tmp2.setSingleStep(1)
				if self.conf_data[key].smin: tmp2.setMinimum(self.conf_data[key].smin)
				if self.conf_data[key].smax: tmp2.setMaximum(self.conf_data[key].smax)
				tmplayout.addWidget(tmp1)
				if self.conf_data[key].description != "":
					tmp3 = QPushButton("?",tmp)
					tmp3.setObjectName("info-popup")
					tmp3.setFixedSize(16, 16)
					tmp3.setCursor(Qt.CursorShape.PointingHandCursor)
					def show_info():
						pos = tmp3.mapToGlobal(QPoint(0, -5))
						QToolTip.showText(pos, self.conf_data[key].description, tmp3)
					tmp3.clicked.connect(show_info)
					tmplayout.addWidget(tmp3,alignment=Qt.AlignmentFlag.AlignLeft)

				tmplayout.addWidget(tmp2,alignment=Qt.AlignmentFlag.AlignRight)
				tmplayout.setContentsMargins(0, 0, 0, 0)
				return tmp
		
		headers = set()
		headers_dictionary = {}

		for key,value in self.conf_data.items():
			if value.name == "keyset": continue
			headers.add(value.category)
			if value.category not in headers_dictionary.keys():
				headers_dictionary[value.category] = []
			headers_dictionary[value.category].append(key)
		
		def add_header(cat):
			self.settingsw_layout.addSpacing(10)
			cat_label = QLabel(cat,self.settingsw)
			cat_label.setStyleSheet("font-weight: bold; color: white;")
			cat_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
			self.settingsw_layout.addWidget(cat_label)
			self.settingsw_layout.addSpacing(10)

			cat_layout = QVBoxLayout()
			cat_layout.setContentsMargins(0, 0, 0, 0)
			cat_layout.setSpacing(1)
			return cat_layout
		
		for cat in headers:
			cat_layout = add_header(cat)
			for key in headers_dictionary[cat]:
				value = self.conf_data[key]
				if key=="VERSION": continue
				if value.name == "bool":
					cat_layout.addWidget(add_conf_bool(key,value))
				if value.name in ["int","float"]:
					cat_layout.addWidget(add_conf_num(key,value))
			self.settingsw_layout.addLayout(cat_layout)


		self.settingsw_layout.setSpacing(4)
		self.settingsw_hk_layout.setContentsMargins(0, 0, 0, 0)

		self.settingsw_layout.addSpacing(15)

		self.settingsw_save = QPushButton("Save configurations",self.settingsw)
		self.settingsw_save.setCursor(Qt.CursorShape.PointingHandCursor)
		self.settingsw_save.clicked.connect(self.save_configurations)
		self.settingsw_layout.addWidget(self.settingsw_save)

		self.settingsw_layout.addSpacing(8)

		self.settingsw.closeEvent = self.anyw_close
		self.settingsw_scroll.closeEvent = self.anyw_close

		self.tray.setContextMenu(self.menu)

		self.run_workers = True
		self.auto_thread = None

		QTimer.singleShot(0,self.start_hotkeys)
		QTimer.singleShot(0,self.init_recorder_and_simulator)

		if not self.conf_data["HIDE_APP_ICON"].real_value: self.anyw_open()
		
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
		dismiss_button.setCursor(Qt.CursorShape.PointingHandCursor)
		update_button.setCursor(Qt.CursorShape.PointingHandCursor)
		footl.addWidget(update_button)
		footl.addWidget(dismiss_button)
		winl.addLayout(footl)

		def close_window():
			win.close()
			win.destroy()
		def update():
			win.close()
			win.destroy()
			run_updater()
			self.shutdown()

		dismiss_button.clicked.connect(close_window)
		update_button.clicked.connect(update)

		win.closeEvent = self.anyw_close

		self.anyw_open()
		win.show()
		win.activateWindow()
		win.raise_()

	def settingsw_popup(self):
		self.anyw_open()
		self.settingsw_scroll.show()
		self.settingsw.show()
		self.settingsw.activateWindow()
		self.settingsw.raise_()
		self.settingsw_scroll.raise_()

	def anyw_open(self):
		import AppKit
		AppKit.NSApp.setActivationPolicy_(AppKit.NSApplicationActivationPolicyRegular)

	def anyw_close(self, event:QEvent):
		if not self.conf_data["HIDE_APP_ICON"].real_value:
			event.accept()
			return
		import AppKit
		AppKit.NSApp.setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)
		event.accept()

	def upd_speed(self,x):
		if x == 0: return
		self.timestamp_multiplier=1/x

	def upd_cps(self,x):
		if x == 0: return
		self.cps = (1/x)

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
					self.conf_data[hk].set_value(self.hotkeys[hk])

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

			if self.state_playback and self.conf_data["ABORT_PLAYBACK_ON_INPUT"].real_value: 
				self.toggle_playback()
				return

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

			if self.conf_data["HOOK_KEYPRESS_EVENTS"].real_value: self.script_ext.kit._signal_keystatus(vk,True)

		except Exception:
			self.error_emitter.error.emit(traceback.format_exc())

	def listener_hotkeysv2_handlekeyrelease(self,key:pynput.keyboard.Key|pynput.keyboard.KeyCode,injected=False): # this is a very long name too
		if injected==True: return
		vk = key.vk if isinstance(key,pynput.keyboard.KeyCode) else key.value.vk
		self.keysdown.discard(vk)
		if self.conf_data["HOOK_KEYPRESS_EVENTS"].real_value: 
			self.script_ext.kit._signal_keystatus(vk,False)

	def init_recorder_and_simulator(self):
		try:
			self.recorder=recorder.OneShotRecorder()
			self.m_simulator = pynput.mouse.Controller()
		except Exception:
			self.anyw_open()
			crash(headline="An error occured while initializing recording/playback infastructure.",detail="Could not initialize recorder.OneShotRecorder or pynput.mouse.Controller.")

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
			self.anyw_open()
			crash(headline="An error occured while initializing recording/playback infastructure.",detail="Could not start the hotkey listener.")

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
					time.sleep(self.conf_data["DELAY_BEFORE_PLAYBACK"].real_value)
					if not self.state_playback: return
					while self.state_playback:
						try:
							print(self.compiled_arr)
							playback.PlayEventList(self.compiled_arr,self.timestamp_multiplier,self.conf_data["USE_MOUSE_WARPING"].real_value)
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
				self.auto_thread = Thread(target=self._INNER_toggle_autoclicker_intelligent if self.conf_data["COMPENSATE_AUTOCLICKER_DRIFT"].real_value else self._INNER_toggle_autoclicker_simple )
				self.auto_thread.start()
				
		except Exception:
			self.error_emitter.error.emit(traceback.format_exc())
			
	def _INNER_toggle_autoclicker_simple(self):
		while self.state_autoclicker:
			playback.mouseButtonStatus(1,True)
			time.sleep(0)
			playback.mouseButtonStatus(1,False)
			time.sleep(self.cps)
	def _INNER_toggle_autoclicker_intelligent(self):
		
		added_delay = 0
		total = 0
		counter = 0
		multiplier=1
		t=time.time()
		while self.state_autoclicker:
			counter+=1
			last_timestamp = time.time()
			playback.mouseButtonStatus(1,True)
			time.sleep(0)
			playback.mouseButtonStatus(1,False)
			time.sleep(max(0,(self.cps)*multiplier))
			t=time.time()
			total+=(t-last_timestamp)
			#added_delay = min(0,(self.cps*multiplier)-(t-last_timestamp))
			if total/counter > self.cps: 
				multiplier-=0.001
			elif (total/counter)+0.001 < self.cps:
				multiplier+=0.001
			#print("New added delay:",added_delay,"Resulting delay:",self.cps+added_delay,"Average actual delay:",total/counter,"mult:",multiplier)

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

try:
	m = Main()
except Exception:
	crash(headline="Failed to start Neoprisma!",detail="Uncaught exception in `Main` class initialization.",exit_code=70)
sys.exit(m.app.exec())
