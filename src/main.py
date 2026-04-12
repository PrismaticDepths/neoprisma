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
	BASE = sys._MEIPASS
else:
	BASE = os.path.dirname(__file__)
SRC = os.path.join(BASE, "src")
if SRC not in sys.path:
	sys.path.insert(0, SRC)

from upstreampatches import pynput_313
pynput_313()

def crash(headline="Neoprisma encountered an error and has to crash.",detail="Entrypoint hook triggered.",error_msg="",exit_code=1):
	from PyQt6.QtWidgets import (
		QApplication,
		QMessageBox
	)
	import traceback
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
Neoprisma version: Not available
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

if sys.platform == "darwin":
	import platform_macos
elif sys.platform == "win32":
	pass
else:
	pass
