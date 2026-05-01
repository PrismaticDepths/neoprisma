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

import playback

try:
	import lupa
except ModuleNotFoundError or ImportError:
	raise ImportError("`lupa` library was not found in the runtime. You may be running a development build of Neoprisma; see the project's homepage for download information. [ https://github.com/PrismaticDepths/neoprisma ]")

from pathlib import Path
from PyQt6.QtGui import QAction,QIcon
from PyQt6.QtCore import QObject,pyqtSignal, QTimer, Qt, QThreadPool,QThread
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
	QScrollArea,
	QMenuBar
)

MACOS_VK_MAP = { # Duplicated - from `platform_macos.py`
	0: 'a', 11: 'b', 8: 'c', 2: 'd', 14: 'e', 3: 'f', 5: 'g', 4: 'h', 34: 'i',
	38: 'j', 40: 'k', 37: 'l', 46: 'm', 45: 'n', 31: 'o', 35: 'p', 12: 'q',
	15: 'r', 1: 's', 17: 't', 32: 'u', 9: 'v', 13: 'w', 7: 'x', 16: 'y', 6: 'z',
	29: '0', 18: '1', 19: '2', 20: '3', 21: '4', 23: '5', 22: '6', 26: '7', 28: '8', 25: '9',
	49: 'space', 36: 'newline', 48: 'tab',
	24: '=', 27: '-', 33: '[', 30: ']', 42: '\\', 41: ';', 39: "'", 43: ',', 47: '.', 44: '/', 50: '`'
}



class LuaSignal:
    def __init__(self):
        self._handlers = []

    def connect(self, func):
        if not callable(func):
            raise TypeError("connect() requires a function.")
        self._handlers.append(func)
        # Using a safer way to disconnect in case the handler was already removed
        return {"Disconnect": lambda: self._handlers.remove(func) if func in self._handlers else None}

    def fire(self, *args):
        for handler in self._handlers:
            # We use QThreadPool to ensure the UI thread stays free
            # even if the Lua handler is doing heavy calculations.
            QThreadPool.globalInstance().start(lambda h=handler, a=args: self._execute_handler(h, a))

    def _execute_handler(self, handler, args):
        try:
            handler(*args)
        except Exception as e:
            print(f"Error in Lua event handler: {e}")

class LUA_Keyboard:
	def __init__(self,playback):
		self.onKeyPress = LuaSignal() # args: vk
		self.onKeyRelease = LuaSignal() # args: vk
		self.keyStatus = playback.keyStatus # args: vk, bool
class LUA_Mouse:
	def __init__(self,playback):
		self.onMouseDown = LuaSignal() # args: button
		self.onMouseUp = LuaSignal() # args: button
		self.onMouseMoved = LuaSignal() # args: x,y
		self.moveMouseAbsolute = playback.moveMouseAbsolute
		self.warpMouseAbsolute = playback.warpMouseAbsolute
		self.dragMouseAbsolute = playback.mouseDragAbsolute
		self.mouseButtonStatus = playback.mouseButtonStatus
		self.mouseScroll = playback.mouseScroll # args: x,y,dx,dy

class LUA_Clock:
	def __init__(self):
		import time
		self.time = time.time

class LUA_Neoprisma:
	def __init__(self,playback):
		self.Keyboard = LUA_Keyboard(playback)
		self.Mouse = LUA_Mouse(playback)
		self.Clock = LUA_Clock()
	


class NeoprismaScriptingToolkit:

	def __init__(self,playback):
		import copy
		self.playback = playback
		self.LUA_Neoprisma = LUA_Neoprisma(self.playback)
		self.extras={}
		self.extras["Neoprisma"] = self.LUA_Neoprisma

	def _signal_keystatus(self,vk,status):
		self.LUA_Neoprisma.Keyboard.onKeyPress.fire(vk) if status else self.LUA_Neoprisma.Keyboard.onKeyRelease.fire(vk)
	def _signal_mousestatus(self,button,status):
		self.LUA_Neoprisma.Mouse.onMouseDown.fire(button) if status else self.LUA_Neoprisma.Mouse.onMouseUp.fire(button)
	def _signal_mousemovement(self,x,y):
		self.LUA_Neoprisma.Mouse.onMouseMoved.fire(x,y) 

def create_runtime(extras=None):
	def attribute_filter(obj, attr_name, is_setting):
		if isinstance(attr_name, str) and attr_name.startswith('_'):
			raise AttributeError("Access to private/internal attributes (attributes starting with an underscore, in other words) is denied. This is for security purposes, however if you believe you have found a bug, please report it.")
		return attr_name
	
	runtime = lupa.LuaRuntime(
		register_builtins=False,
		attribute_filter=attribute_filter
	)

	lua_globals = runtime.globals()

	unsafe_globals = ["os", "io", "package", "debug", "require", "module"]
	for name in unsafe_globals:
		lua_globals[name] = None

	lua_globals["math"] = lua_globals.math
	lua_globals["string"] = lua_globals.string
	lua_globals["table"] = lua_globals.table

	lua_globals["print"] = print

	if extras is not None:

		for key,value in extras.items():

			lua_globals[key] = value
	print([k for k,v in lua_globals.items()])
	return runtime

class ScriptStatus:
	def __init__(self,sname,sstatus,num_hooks):
		self.name=sname
		self.status=sstatus
		self.num_hooks = num_hooks
		self.status_layout = QVBoxLayout()
		self.status_layout2 = QHBoxLayout()
		self.status_layout.setContentsMargins(0,0,0,0)
		self.status_layout.setSpacing(2)
		self.script_name=QLabel(self.name)
		self.status_layout.addWidget(self.script_name)
		self.status_long = QLabel(f"{self.status} ({str(self.num_hooks)+" hooks registered" if self.status=="sleeping" else "xx:xx elapsed" if self.status=="running" else "error" if self.status=="interrupted" else ""})")
		self.status_long.setObjectName("script-status-long")
		self.status_layout.addWidget(self.status_long)
		self.status_layout2.addLayout(self.status_layout)
		self.status_button = QPushButton("")
		self.status_button.setObjectName("status-yellow" if self.status=="sleeping" else "status-green" if self.status=="running" else "status-red")
		self.status_button.setFixedSize(16,16)
		self.status_layout2.addWidget(self.status_button)
	def set_name(self,name):
		self.name = name
		self.script_name.setText(self.name)
	def set_status(self,status):
		assert status in ["running","sleeping","interrupted"]
		self.status = status
		self.status_button.setObjectName("status-yellow" if self.status=="sleeping" else "status-green" if self.status=="running" else "status-red")

def ScriptWorker(QObject):
	

class Runner(QObject):

	def __init__(self):
		super().__init__()

		
		self.mainw = QWidget()
		self.mainw.setBaseSize(500,750)
		self.mainw_layout = QVBoxLayout()
		self.mainw.setLayout(self.mainw_layout)
		self.mainw.setWindowTitle("Script Dashboard")
		self.script_view = QVBoxLayout()
		self.script_scroll_content = QWidget(); self.script_scroll_content.setLayout(self.script_view)
		self.script_scroll = QScrollArea(); self.script_scroll.setWidget(self.script_scroll_content); self.script_scroll.setWidgetResizable(True)

		# Set up bottom 4 buttons 

		self.bottom_layout_outer = QVBoxLayout()
		self.bottom_layout_up = QHBoxLayout()
		self.bottom_layout_down = QHBoxLayout()
		self.bottom_layout_outer.setContentsMargins(0,0,0,0)
		self.bottom_layout_up.setContentsMargins(0,0,0,0)
		self.bottom_layout_down.setContentsMargins(0,0,0,0)
		self.bottom_layout_outer.setSpacing(4)
		self.bottom_layout_outer.addLayout(self.bottom_layout_up)
		self.bottom_layout_outer.addLayout(self.bottom_layout_down)

		self.execute_btn = QPushButton("Run New")
		self.execute_btn.released.connect(self.load)
		self.log_btn = QPushButton("Open Log")
		self.bottom_layout_up.addWidget(self.execute_btn)
		self.bottom_layout_up.addWidget(self.log_btn)

		self.terminate_all_btn = QPushButton("Terminate All")
		self.exit_btn = QPushButton("Exit")
		self.bottom_layout_down.addWidget(self.terminate_all_btn)
		self.bottom_layout_down.addWidget(self.exit_btn)

		# Add header

		running_label = QLabel("Script Monitor")
		running_label.setStyleSheet("font-weight: bold; color: white;")
		running_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.mainw_layout.addWidget(running_label)

		#self.accept_btn = QPushButton("Accept")
		#self.discard_btn = QPushButton("Cancel")

		self.mainw_layout.addSpacing(10)

		s=self.make_script_status("wasd-to-arrows.lua","sleeping",4)
		self.script_view.addLayout(s.status_layout2)

		self.mainw_layout.addWidget(self.script_scroll)

		#self.input_box = QTextEdit()
		#self.input_box.setStyleSheet("""
		#QLineEdit, QTextEdit, QPlainTextEdit {
		#font-family: 'Courier New', monospace;
		#}""")
		#self.input_box.setAcceptRichText(False)
		#self.mainw_layout.addWidget(self.input_box)

		#self.accept_btn.pressed.connect(self.run)

		#self.bottom_layout.addWidget(self.accept_btn)
		#self.bottom_layout.addWidget(self.discard_btn)

		self.mainw_layout.addLayout(self.bottom_layout_outer)

		import playback
		self.kit = NeoprismaScriptingToolkit(playback)
		self.runtime = create_runtime(extras=self.kit.extras)



	def make_script_status(self,name,status,num_hooks):

		return ScriptStatus(name,status,num_hooks)

	def run(self,name,text):
		def inner():
			s=self.make_script_status(name,"running",0)
			self.script_view.addLayout(s.status_layout2)
			try:
				self.runtime.execute(text)
			except lupa.LuaError:
				s.set_status("interrupted")
			else:
				s.status_layout2.deleteLater()
		t=QThread()
		

	def load(self):

		try:
			file, _ = QFileDialog.getOpenFileName(None,"Select a script to load",filter="Lua Scripts (*.lua);;All Files (*)")
			with open(file,"r") as fstream:
				dat = fstream.read()
				box = QMessageBox()
				box.setIcon(QMessageBox.Icon.Information)
				box.setText("Do you want to run this script?")
				box.setInformativeText("Make sure this script is safe!\nNeoprisma does its best to sandbox scripts, but malicious code execution is a possibility.\nClick \"Show Details...\" to see the code you are about to run.")
				box.setDetailedText(dat)
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
				box.addButton(QMessageBox.StandardButton.Yes).released.connect(lambda: self.run(Path(file).name,dat))
				box.addButton(QMessageBox.StandardButton.No)
				box.exec()
		except:
			pass

	def save(self):

		try:
			file, _ = QFileDialog.getSaveFileName(None,"Select a location to save your script",filter="Lua Scripts (*.lua)")
			if file == "": return
			else:
				with open(file,"w") as fstream:
					fstream.write(self.input_box.toPlainText())
		except:
			pass