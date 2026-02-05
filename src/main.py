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

if sys.platform == "darwin":
	import platform_macos
elif sys.platform == "win32":
	pass
else:
	pass