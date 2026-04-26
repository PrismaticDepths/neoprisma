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

MACOS_VK_MAP = { # Duplicated - from `platform_macos.py`
	0: 'a', 11: 'b', 8: 'c', 2: 'd', 14: 'e', 3: 'f', 5: 'g', 4: 'h', 34: 'i',
	38: 'j', 40: 'k', 37: 'l', 46: 'm', 45: 'n', 31: 'o', 35: 'p', 12: 'q',
	15: 'r', 1: 's', 17: 't', 32: 'u', 9: 'v', 13: 'w', 7: 'x', 16: 'y', 6: 'z',
	29: '0', 18: '1', 19: '2', 20: '3', 21: '4', 23: '5', 22: '6', 26: '7', 28: '8', 25: '9',
	49: 'space', 36: 'newline', 48: 'tab',
	24: '=', 27: '-', 33: '[', 30: ']', 42: '\\', 41: ';', 39: "'", 43: ',', 47: '.', 44: '/', 50: '`'
}

class NeoprismaScriptingToolkit:

	def __init__(self,playback):
		import copy
		self.playback = playback
		print(dir(self.playback))
		self.extras={}
		self.extras["keyStatus"] = self.playback.keyStatus
		self.extras["moveMouseAbsolute"] = self.playback.moveMouseAbsolute
		self.extras["warpMouseAbsolute"] = self.playback.warpMouseAbsolute
		self.extras["mouseDragAbsolute"] = self.playback.mouseDragAbsolute
		self.extras["mouseButtonStatus"] = self.playback.mouseButtonStatus
		self.extras["mouseScroll"] = self.playback.mouseScroll




def create_runtime(extras=None):
	def attribute_filter(obj, attr_name, is_setting):
		if isinstance(attr_name, str) and attr_name.startswith('_'):
			raise AttributeError("Access to private/internal attributes is denied. This is for security purposes, however if you believe you have found a bug, please report it.")
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

class Runner(QObject):

	def __init__(self):
		super().__init__()

		
		self.mainw = QWidget()
		self.mainw.setBaseSize(500,500)
		self.mainw_layout = QVBoxLayout()
		self.bottom_layout = QHBoxLayout()
		self.mainw.setLayout(self.mainw_layout)
		self.mainw.setWindowTitle("Script Runner")

		self.accept_btn = QPushButton("Accept")
		self.discard_btn = QPushButton("Cancel")

		#self.footer_label = QLabel(f"<a href='https://github.com/PrismaticDepths/neoprisma/releases/tag/{self.latest_version}'>View Release</a>  ❖  <a href='https://github.com/PrismaticDepths/neoprisma/compare/{__version__}...{self.latest_version}'>Full Changelog</a>")
		#self.footer_label.setOpenExternalLinks(True)

		self.mainw_layout.addSpacing(10)

		self.input_box = QTextEdit()
		self.input_box.setStyleSheet("""
		QLineEdit, QTextEdit, QPlainTextEdit {
		font-family: 'Courier New', monospace;
		}""")
		self.mainw_layout.addWidget(self.input_box)

		self.accept_btn.pressed.connect(self.run)

		self.bottom_layout.addWidget(self.accept_btn)
		self.bottom_layout.addWidget(self.discard_btn)

		self.mainw_layout.addLayout(self.bottom_layout)

		import playback
		self.kit = NeoprismaScriptingToolkit(playback)
		self.runtime = create_runtime(extras=self.kit.extras)

	def run(self):

		self.runtime.execute(self.input_box.toPlainText())