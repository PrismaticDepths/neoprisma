def crash(headline="Neoprisma encountered an error and has to crash.",infotext:str|None=None,crashlog_detail="No short details available.",error_msg="",exit_code=1,ver=""):

	from PyQt6.QtWidgets import (
		QApplication,
		QMessageBox,
		QLAbel
	)
	import os,sys,traceback,platform,time
	app = QApplication.instance()
	if app is None: app = QApplication(sys.argv)
	box = QMessageBox()
	box.setIcon(QMessageBox.Icon.Critical)
	box.setText(headline)
	if infotext is None: 
		box.setInformativeText(f"Please report this issue to the developers!\n\nYou can press \"Show Details...\" to see the full crash report. Include the entire crash log if you file a bug report.\nPressing \"Abort\" or closing the crash dialog will terminate this process.")
	else: box.setInformativeText(infotext)
	box.setDetailedText(f"""--- Crash Summary ---
Report generated in file: `{__name__}`
Crash headline: {headline}
Crash infotext: {"<default>" if infotext is None else infotext}
Shorthand crash detail: {crashlog_detail}
Neoprisma version: {ver}
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

def notice(headline="Notice",infotext="Dialog info text"):

	from PyQt6.QtWidgets import (
		QApplication,
		QMessageBox,
		QLabel
	)
	from PyQt6.QtCore import Qt

	import os,sys
	app = QApplication.instance()
	if app is None: app = QApplication(sys.argv)
	box = QMessageBox()
	box.setIcon(QMessageBox.Icon.Warning)
	box.setText(headline)
	box.setTextFormat(Qt.TextFormat.RichText)
	box.setInformativeText(infotext)
	box.setMouseTracking(True)
	box.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse)
	box.addButton(QMessageBox.StandardButton.Ok)
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
	box.setWindowTitle("Neoprisma")
	for label in box.findChildren(QLabel):
		label.setMouseTracking(True)
		
		label.setOpenExternalLinks(True)
		label.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse)

	box.exec()


def resource_path(relative_path: str) -> str:
	"""Return the absolute path to a resource, works both in dev and in PyInstaller bundle."""
	import os,sys
	if getattr(sys, 'frozen', False):
		base_path = sys._MEIPASS
	else:
		base_path = os.path.dirname(__file__)

	return os.path.join(base_path, relative_path)

def MACOS_fetch_keyboard_layout():
	import plistlib
	from pathlib import Path
	plist_path = Path("~/Library/Preferences/com.apple.HIToolbox.plist").expanduser()	
	if not plist_path.exists(): raise FileNotFoundError
	with open(plist_path, "rb") as f: plist_data = plistlib.load(f)
	selected_sources = plist_data.get("AppleSelectedInputSources", [])
	for source in selected_sources:
		if "KeyboardLayout Name" in source: return source["KeyboardLayout Name"]
	return "Unknown"

def MACOS_fetch_framework(name):
	import ctypes, ctypes.util

	fpath = ctypes.util.find_library(name)
	if fpath is None: raise OSError(f"Could not find framework {name}")
	return ctypes.CDLL(fpath)

def MACOS_is_trusted_Accessibility():
	
	ApplicationServices = MACOS_fetch_framework("ApplicationServices")
	return bool(ApplicationServices.AXIsProcessTrusted())


def MACOS_is_trusted_ListenEvent():
	
	IOKit = MACOS_fetch_framework("IOKit")
	return IOKit.IOHIDCheckAccess(1)==0

