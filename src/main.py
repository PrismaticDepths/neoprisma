import playback
import recorder
import pynput
import copy
from threading import Thread


class Main:

	def __init__(self):
		self.recorder = recorder.OneShotRecorder()
		self.arr = bytearray()
		self.state_recording = False
		self.state_playback = False
		self.state_autoclicker = False

		with pynput.keyboard.GlobalHotKeys({
		'<ctrl>+<f7>': self.toggle_recording,
		'<ctrl>+<f9>': self.toggle_playback,
		'<ctrl>+<f8>': self.toggle_autoclicker}) as h:
			h.join()

	def toggle_recording(self):
		if self.state_playback or self.state_autoclicker: return
		print('rec:', not self.state_recording)
		if self.state_recording: self.recorder.stop()
		self.arr = copy.deepcopy(self.recorder.buffer)
		self.recorder = recorder.OneShotRecorder()
		if self.state_recording: 
			self.state_recording = False
		else: 
			self.state_recording = True
			self.recorder.start()

	def toggle_playback(self):
		if self.state_recording or self.state_autoclicker: return
		if self.state_playback: 
			playback.abortPlayback()
			self.state_playback = False
		else:
			self.state_playback = True
			playback.resetAbortPlayback()
			def inner():
				while self.state_playback:
					try:
						playback.CompileAndPlay(self.arr)
					except KeyboardInterrupt: 
						break
			t = Thread(target=inner)
			t.start()
	


	def toggle_autoclicker(self):
		if self.state_recording or self.playback: return

m = Main()