import pynput, time, struct


class Events: # DO NOT MODIFY EXISTING ENUMS SINCE THAT WOULD BREAK OLD RECORDINGS
	KEY_DOWN = 10
	KEY_UP = 11
	MOUSE_DOWN = 20
	MOUSE_UP = 21
	MOUSE_MOVE_ABSOLUTE = 22
	MOUSE_MOVE_RELATIVE = 23
	MOUSE_SCROLL = 24

#USES LITTLE ENDIAN IF YOU CANT ALREADY TELL
#HEADER: EVENT TIMESTAMP, EVENT TYPE
#HEADER: UINT64, UINT8,
EVENT_HEADER_FMT = "<QB"
PAYLOAD_FMTS = {
Events.KEY_DOWN:"<H", #UINT16
Events.KEY_UP:"<H", #UINT16
Events.MOUSE_DOWN:"<BHH", #UINT8,UINT16,UINT16
Events.MOUSE_UP:"<BHH", #UINT8,UINT16,UINT16
Events.MOUSE_MOVE_ABSOLUTE:"<HH", #UINT16,UINT16
Events.MOUSE_MOVE_RELATIVE:"<hh", #INT16,INT16
Events.MOUSE_SCROLL:"<HHhh", #UINT16,UINT16,INT16,INT16
}

class OneShotRecorder:
	def __init__(self):
		self.starting_time = 0
		self.buffer = bytearray()
		self.kb_listener = pynput.keyboard.Listener(on_press=self.captured_key_press,on_release=self.captured_key_release)
		self.mouse_listener = pynput.mouse.Listener(on_move=self.captured_mouse_move,on_click=self.captured_mouse_click,on_scroll=self.captured_mouse_scroll)

	def log_event(self,timestamp,event,*payload):
		self.buffer.extend(struct.pack(EVENT_HEADER_FMT+PAYLOAD_FMTS[event],timestamp,event,*payload))

	def captured_key_press(self,key:pynput.keyboard.Key|pynput.keyboard.KeyCode):
		t=time.perf_counter_ns()-self.start
		self.log_event(t,Events.KEY_DOWN,key.vk if isinstance(key,pynput.keyboard.KeyCode) else key.value.vk)

	def captured_key_release(self,key:pynput.keyboard.Key|pynput.keyboard.KeyCode):
		t=time.perf_counter_ns()-self.start
		self.log_event(t,Events.KEY_UP,key.vk if isinstance(key,pynput.keyboard.KeyCode) else key.value.vk)

	def captured_mouse_click(self,x,y,button:pynput.mouse.Button,pressed):
		t=time.perf_counter_ns()-self.start
		self.log_event(t,Events.MOUSE_DOWN if pressed else Events.MOUSE_UP,button.value,x,y)

	def captured_mouse_move(self,x,y):
		t=time.perf_counter_ns()-self.start
		self.log_event(t,Events.MOUSE_MOVE_ABSOLUTE,x,y)

	def captured_mouse_scroll(self,x,y,dx,dy):
		t=time.perf_counter_ns()-self.start
		self.log_event(t,Events.MOUSE_SCROLL,x,y,dx,dy)

	def start(self):
		self.start = time.perf_counter_ns()
		kb_listener.start()
		mouse_listener.start()
		# it is threaded soo
		


start = time.perf_counter_ns()
kb_listener.start()
mouse_listener.start()
time.sleep(10)
kb_listener.stop()
mouse_listener.stop()