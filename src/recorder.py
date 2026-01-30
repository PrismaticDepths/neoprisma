import os, sys

if getattr(sys, "frozen", False):
    BASE = sys._MEIPASS
else:
    BASE = os.path.dirname(__file__)

SRC = os.path.join(BASE, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

import pynput, time, struct
MAJOR_FMT_VERSION = 1 # ONLY CHANGE WHEN YOU MAKE BREAKING CHANGES THAT WOULD CRASH AN OLDER VERSION OF THE PLAYBACK ENGINE. ALSO CHANGE THE NUMBER IN THE PLAYBACK SECTION TOO LOL
# MAJOR_FMT_VERSION MUST BE UNDER 256 (or 255 maybe i forgot) OR THE C++ PLAYBACK CODE MIGHT BREAK
FILE_HEADER_ID = b'<NEOPRISMA>' # DO NOT CHANGE THIS

class Events: # DO NOT MODIFY EXISTING ENUMS SINCE THAT WOULD DEFINITELY BREAK OLD RECORDINGS, ALSO PROBABLY BUMP MAJOR_FMT_VERSION WHEN DOING THIS
	# !! Duplicated in playback.h
	KEY_DOWN = 10
	KEY_UP = 11
	MOUSE_DOWN = 20
	MOUSE_UP = 21
	MOUSE_MOVE_ABSOLUTE = 22
	MOUSE_MOVE_RELATIVE = 23
	MOUSE_SCROLL = 24
	MOUSE_DRAG = 25

#USES LITTLE ENDIAN IF YOU CANT ALREADY TELL
#HEADER: EVENT TIMESTAMP, EVENT TYPE
#HEADER: UINT64, UINT8,
FILE_HEADER_FMT = "<11sB" #char[4],UINT8 should be set to NPRM
EVENT_HEADER_FMT = "<QB" #UINT64,UINT8, PROBABLY DONT CHANGE THIS ONE EITHER BY THE WAY
PAYLOAD_FMTS = { # !! hardcoded + duplicated in playback.cpp
Events.KEY_DOWN:"H", #UINT16
Events.KEY_UP:"H", #UINT16
Events.MOUSE_DOWN:"BHH", #UINT8,UINT16,UINT16
Events.MOUSE_UP:"BHH", #UINT8,UINT16,UINT16
Events.MOUSE_MOVE_ABSOLUTE:"HH", #UINT16,UINT16
Events.MOUSE_MOVE_RELATIVE:"hh", #INT16,INT16
Events.MOUSE_SCROLL:"HHhh", #UINT16,UINT16,INT16,INT16
Events.MOUSE_DRAG:"BHH", #UINT8,UINT16,UINT16
}

# toggle recording is ctrl f7
# so we want to avoid it
# toggle playing recordings is ctrl f9 also avoid that
# ctrl f8 is fine since that will toggle the autoclicker


class OneShotRecorder:
	def __init__(self):

		self.keysdown = set()
		self.clicks = []
		self.starting_time = 0
		self.buffer = bytearray()
		self.buffer.extend(struct.pack(FILE_HEADER_FMT,FILE_HEADER_ID,MAJOR_FMT_VERSION)) # Add the file header
		self.kb_listener = pynput.keyboard.Listener(on_press=self.captured_key_press,on_release=self.captured_key_release)
		self.mouse_listener = pynput.mouse.Listener(on_move=self.captured_mouse_move,on_click=self.captured_mouse_click,on_scroll=self.captured_mouse_scroll)

	def log_event(self,timestamp,event,*payload):
		self.buffer.extend(struct.pack(EVENT_HEADER_FMT+PAYLOAD_FMTS[event],timestamp,event,*payload))

	def captured_key_press(self,key:pynput.keyboard.Key|pynput.keyboard.KeyCode):
		t=time.perf_counter_ns()-self.starting_time
		vk = key.vk if isinstance(key,pynput.keyboard.KeyCode) else key.value.vk
		if 59 in self.keysdown and vk in [101,41]: return
		self.keysdown.add(vk)
		self.log_event(t,Events.KEY_DOWN,vk)

	def captured_key_release(self,key:pynput.keyboard.Key|pynput.keyboard.KeyCode):
		t=time.perf_counter_ns()-self.starting_time
		vk = key.vk if isinstance(key,pynput.keyboard.KeyCode) else key.value.vk
		if 59 in self.keysdown and vk in [101,41]: return
		try: self.keysdown.discard(vk)
		except Exception: pass
		self.log_event(t,Events.KEY_UP,vk)

	def captured_mouse_click(self,x,y,button,pressed):
		t=time.perf_counter_ns()-self.starting_time
		b = list(pynput.mouse.Button).index(button)
		self.log_event(t,Events.MOUSE_DOWN if pressed else Events.MOUSE_UP,b,int(x),int(y))
		if pressed: self.clicks.append(b) 
		else:
			try: self.clicks.remove(b)
			except Exception: pass

	def captured_mouse_move(self,x,y):
		t=time.perf_counter_ns()-self.starting_time
		if len(self.clicks)!=0:
			self.log_event(t,Events.MOUSE_DRAG,self.clicks[-1],int(x),int(y))
		else:
			self.log_event(t,Events.MOUSE_MOVE_ABSOLUTE,int(x),int(y))

	def captured_mouse_scroll(self,x,y,dx,dy):
		t=time.perf_counter_ns()-self.starting_time
		self.log_event(t,Events.MOUSE_SCROLL,int(x),int(y),int(dx),int(dy))

	def start(self):
		try:
			assert self.starting_time == 0
			self.starting_time = time.perf_counter_ns()
			self.kb_listener.start()
			self.mouse_listener.start()
		except Exception:
			raise RuntimeError("Failed to initialize & start keyboard/mouse listeners.")

	def stop(self):
		self.kb_listener.stop()
		self.mouse_listener.stop()