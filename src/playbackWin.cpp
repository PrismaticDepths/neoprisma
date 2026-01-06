#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <cstdint>
#include <iostream>
#include <vector>
#include <cstring>
#include <string>
#include <optional>
#include <thread>
#include <chrono>
// #include <ApplicationServices/ApplicationServices.h> this is macos only. making this for windows!
#include "playback.h"
#include <windows.h>
namespace py = pybind11;


constexpr uint8_t MAJOR_FMT_VERSION = 1; // CHANGE IF YOU ALSO CHANGE THIS VARIABLE IN recorder.py
constexpr uint8_t EARLIEST_SUPPORTED_FMT_VERSION = 1; // LEAVE THIS ALONE UNLESS YOU MAKE BREAKING CHANGES AND CANT READ OLDER STUFF SOMEHOW
constexpr char FILE_HEADER_ID[4] = {'N','P','R','M'}; // DONT CHANGE THIS ONE

constexpr size_t sizeof_uint8_t = sizeof(uint8_t);
constexpr size_t sizeof_uint16_t = sizeof(uint16_t);
constexpr size_t sizeof_int16_t = sizeof(int16_t);
constexpr size_t sizeof_uint64_t = sizeof(uint64_t);


void setDPIAwareness() {
	SetProcessDPIAware();
}
void keyStatus(uint16_t vk_code, bool status) {
	/* macos version.
		
	CGEventRef keyStroke = CGEventCreateKeyboardEvent(NULL, (CGKeyCode)vk_code, status);
	CGEventPost(kCGHIDEventTap, keyStroke);
	CFRelease(keyStroke);

	*/
	// windows version
	INPUT inputs[1] = {};
	ZeroMemory(inputs, sizeof(inputs));
	inputs[0].type = INPUT_KEYBOARD;
	inputs[0].ki.wVk = vk_code;
		
	if(!status) {
		inputs[0].ki.dwFlags = KEYEVENTF_KEYUP;
	}
	else {
		inputs[0].ki.dwFlags = 0;
	}
		
	SendInput(ARRAYSIZE(inputs), inputs, sizeof(INPUT));
}

void moveMouseAbsolute(uint16_t x, uint16_t y) {
	
	/*macos version
	CGPoint destination = CGPointMake(x, y);
	CGEventRef motion = CGEventCreateMouseEvent(NULL,kCGEventMouseMoved,destination,kCGMouseButtonLeft);
	CGEventPost(kCGHIDEventTap, motion);
	CFRelease(motion);
	*/
	// windows version
	INPUT input;
	ZeroMemory(&input, sizeof(INPUT));
	input.type = INPUT_MOUSE;

	input.mi.dx = (static_cast<long>(x*65535))/ (GetSystemMetrics(SM_CXSCREEN) - 1); // size of length of primary monitor
	input.mi.dy = (static_cast<long>(y*65535))/ (GetSystemMetrics(SM_CYSCREEN) - 1); // size of width of primary monitor

	input.mi.dwFlags = MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE;

	SendInput(1, &input, sizeof(INPUT));



}

void mouseButtonStatus(uint16_t button, uint16_t x, uint16_t y, bool status) {
	
	INPUT input;
	ZeroMemory(&input, sizeof(INPUT));
	input.type = INPUT_MOUSE;

	input.mi.dx = (static_cast<long>(x*65535))/ ( GetSystemMetrics(SM_CXSCREEN) - 1 ); // size of length of primary monitor
	input.mi.dy = (static_cast<long>(y*65535))/ ( GetSystemMetrics(SM_CYSCREEN) - 1); // size of width of primary monitor
	input.mi.dwFlags = MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE;
	switch (button) {
		case 1:
			if (status)
				input.mi.dwFlags |= MOUSEEVENTF_LEFTDOWN;
			else
				input.mi.dwFlags |= MOUSEEVENTF_LEFTUP;
			break;
		case 2:
			if (status)
				input.mi.dwFlags |= MOUSEEVENTF_RIGHTDOWN;
			else
				input.mi.dwFlags |= MOUSEEVENTF_RIGHTUP;
			break;
		case 3:
			if (status)
				input.mi.dwFlags |= MOUSEEVENTF_MIDDLEDOWN;
			else
				input.mi.dwFlags |= MOUSEEVENTF_MIDDLEUP;
			break;
		default:
			// Windows does not support arbitrary mouse buttons
			return;
	}
	SendInput(1, &input, sizeof(INPUT));


	// below is macos version.
	/*
	CGPoint destination = CGPointMake(x, y);
	CGEventType statusEvent;
	CGMouseButton mouseButton;

	switch (button) {
		case 1:
			if (status) {
				statusEvent = kCGEventLeftMouseDown;
			} else {
				statusEvent = kCGEventLeftMouseUp;
			}
			mouseButton = kCGMouseButtonLeft;
			break;
		case 2:
			if (status) {
				statusEvent = kCGEventRightMouseDown;
			} else {
				statusEvent = kCGEventRightMouseUp;
			}
			mouseButton = kCGMouseButtonRight;
			break;
		case 3:
			if (status) {
				statusEvent = kCGEventOtherMouseDown;
			} else {
				statusEvent = kCGEventOtherMouseUp;
			}
			mouseButton = kCGMouseButtonCenter;
			break;
		default:
			if (status) {
				statusEvent = kCGEventOtherMouseDown;
			} else {
				statusEvent = kCGEventOtherMouseUp;
			}
			mouseButton = (CGMouseButton)button;
			break;
	}

	CGEventRef click = CGEventCreateMouseEvent(NULL,statusEvent,destination,mouseButton);
	if (button > 2) {
		CGEventSetIntegerValueField(click, kCGMouseEventButtonNumber, button);
	}
	CGEventPost(kCGHIDEventTap,click);
	CFRelease(click);  
	*/
}

std::pair<bool, uint8_t> ensureValidHeaders(std::vector<uint8_t>& e_bytearray) {
	uint8_t version = 0;
	if (e_bytearray.size() < 5 || std::memcmp(e_bytearray.data(),FILE_HEADER_ID,4) != 0) {
		return {false, version};
	} else {
		std::memcpy(&version,e_bytearray.data()+4,sizeof(version));
		if (version < EARLIEST_SUPPORTED_FMT_VERSION || version > MAJOR_FMT_VERSION) {
			return {false, version};
		} else {
			return {true,version};
		}
	} 
}

std::pair<std::vector<EventPacket>, std::string> CompileEventArray(std::vector<uint8_t>& e_bytearray) {
	std::pair<bool, uint8_t> headerInfo = ensureValidHeaders(e_bytearray);
	std::vector<EventPacket> eventList;
	if (!headerInfo.first) {
		std::cerr << "nprisma: bad fileheader, found version " << int(headerInfo.second) << std::endl;
		return {eventList,"Failed to parse event array: Bad file header or incompatible version."}; 
	}
	for (size_t cur = 5; cur < e_bytearray.size();) {
		EventPacket e;
		std::memcpy(&e.timestamp, e_bytearray.data()+cur, sizeof_uint64_t);
		cur += sizeof_uint64_t;
		std::memcpy(&e.event, e_bytearray.data()+cur, sizeof_uint8_t);
		cur += sizeof_uint8_t;
		uint16_t x;
		uint16_t y;
		switch (e.event) {
			case Events::KEY_DOWN:
			case Events::KEY_UP:
				uint16_t vk;
				std::memcpy(&vk, e_bytearray.data()+cur, sizeof_uint16_t);
				cur += sizeof_uint16_t;
				e.payload.push_back(static_cast<int>(vk));
				break;

			case Events::MOUSE_DOWN:
			case Events::MOUSE_UP:
				uint8_t button;
				std::memcpy(&button, e_bytearray.data()+cur, sizeof_uint8_t);
				cur += sizeof_uint8_t;
				std::memcpy(&x, e_bytearray.data()+cur, sizeof_uint16_t);
				cur += sizeof_uint16_t;
				std::memcpy(&y, e_bytearray.data()+cur, sizeof_uint16_t);
				cur += sizeof_uint16_t;
				e.payload.push_back(static_cast<int>(button));
				e.payload.push_back(static_cast<int>(x));
				e.payload.push_back(static_cast<int>(y));
				break;

			case Events::MOUSE_ABS_MOVE:

				std::memcpy(&x, e_bytearray.data()+cur, sizeof_uint16_t);
				cur += sizeof_uint16_t;
				std::memcpy(&y, e_bytearray.data()+cur, sizeof_uint16_t);
				cur += sizeof_uint16_t;
				e.payload.push_back(static_cast<int>(x));
				e.payload.push_back(static_cast<int>(y));
				break;

			case Events::MOUSE_REL_MOVE:
				break; // TO BE IMPLEMENTED LATER

			case Events::MOUSE_SCROLL:
				int16_t dx;
				int16_t dy;
				std::memcpy(&x, e_bytearray.data()+cur, sizeof_uint16_t);
				cur += sizeof_uint16_t;
				std::memcpy(&y, e_bytearray.data()+cur, sizeof_uint16_t);
				cur += sizeof_uint16_t;
				std::memcpy(&dx, e_bytearray.data()+cur, sizeof_int16_t);
				cur += sizeof_int16_t;
				std::memcpy(&dy, e_bytearray.data()+cur, sizeof_int16_t);
				cur += sizeof_int16_t;
				e.payload.push_back(static_cast<int>(x));
				e.payload.push_back(static_cast<int>(y));
				e.payload.push_back(static_cast<int>(dx));
				e.payload.push_back(static_cast<int>(dy));
				break;

			default:
				break;
		}
		eventList.push_back(e);
	}
	return {eventList,""};
}

void PlayEventList(std::vector<EventPacket> eventList) {
	auto start = std::chrono::high_resolution_clock::now();
	uint64_t lastTimestamp = 0;
	for (EventPacket e : eventList) {
		uint64_t deltaNs = e.timestamp - lastTimestamp;
		auto insertTime = start + std::chrono::nanoseconds(e.timestamp);
		lastTimestamp = e.timestamp;
		std::this_thread::sleep_for(std::chrono::nanoseconds(deltaNs)-std::chrono::nanoseconds(200));
		std::function<void()> func;
		switch (e.event) {
			case Events::KEY_DOWN:
				func = [e]() -> void { keyStatus(e.payload.front(),true); };
				break;
			case Events::KEY_UP:
				func = [e]() -> void { keyStatus(e.payload.front(),false); };
				break;
			case Events::MOUSE_ABS_MOVE:
				func = [e]() -> void { moveMouseAbsolute(e.payload.at(0),e.payload.at(1)); };
				break;
			case Events::MOUSE_DOWN:
				func = [e]() -> void { mouseButtonStatus(e.payload.at(0),e.payload.at(1),e.payload.at(2),true); };
				break;
			case Events::MOUSE_UP:
				func = [e]() -> void { mouseButtonStatus(e.payload.at(0),e.payload.at(1),e.payload.at(2),false); };
				break;
			case Events::MOUSE_SCROLL:
				//func = [e]() -> void { mouseScroll(e.payload.at(0),e.payload.at(1),e.payload.at(2),e.payload.at(3)); };
				//break;
				return;
		}
		while (std::chrono::high_resolution_clock::now() < insertTime) {
			// intentionally do nothing
		}
		func();
	}
	
}

void CompileAndPlay(std::vector<uint8_t>& e_bytearray) {
	auto l = CompileEventArray(e_bytearray);
	PlayEventList(l.first);
}

PYBIND11_MODULE(playback, m) {
    m.def("CompileEventArray", &CompileEventArray, "i mean it just kind like parses the event array idk");
	m.def("PlayEventList", &PlayEventList, "i mean it just kind like plays the thingy if you know what i mean");
	m.def("CompileAndPlay", &CompileAndPlay, "i mean it just kind like plays the thingy with less intervention needed if you know what i mean");
	m.def("setDPIAwareness", &setDPIAwareness, "Sets the process DPI awareness to handle high-DPI displays correctly on Windows.");
}