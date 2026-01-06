#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <cstdint>
#include <iostream>
#include <vector>
#include <atomic>
#include <cstring>
#include <string>
#include <optional>
#include <thread>
#include <chrono>
#include <ApplicationServices/ApplicationServices.h>
#include "playback.h"
namespace py = pybind11;

constexpr uint8_t MAJOR_FMT_VERSION = 1; // CHANGE IF YOU ALSO CHANGE THIS VARIABLE IN recorder.py
constexpr uint8_t EARLIEST_SUPPORTED_FMT_VERSION = 1; // LEAVE THIS ALONE UNLESS YOU MAKE BREAKING CHANGES AND CANT READ OLDER STUFF SOMEHOW
constexpr char FILE_HEADER_ID[4] = {'N','P','R','M'}; // DONT CHANGE THIS ONE

constexpr size_t sizeof_uint8_t = sizeof(uint8_t);
constexpr size_t sizeof_uint16_t = sizeof(uint16_t);
constexpr size_t sizeof_int16_t = sizeof(int16_t);
constexpr size_t sizeof_uint64_t = sizeof(uint64_t);

std::atomic<bool> n_abort{false};

void abortPlayback() {
	n_abort.store(true,std::memory_order_relaxed);
}

void resetAbortPlayback() {
	n_abort.store(false,std::memory_order_relaxed);
}

bool getAbortStatus() {
	return n_abort.load(std::memory_order_relaxed);
}

void keyStatus(uint16_t vk_code, bool status) {
	CGEventRef keyStroke = CGEventCreateKeyboardEvent(NULL, (CGKeyCode)vk_code, status);
	CGEventPost(kCGHIDEventTap, keyStroke);
	CFRelease(keyStroke);
}

void moveMouseAbsolute(uint16_t x, uint16_t y) {
	CGPoint destination = CGPointMake(x, y);
	CGEventRef motion = CGEventCreateMouseEvent(NULL,kCGEventMouseMoved,destination,kCGMouseButtonLeft);
	CGEventPost(kCGHIDEventTap, motion);
	CFRelease(motion);
}

void mouseDragAbsolute(uint8_t button, uint16_t x, uint16_t y) {
	CGPoint destination = CGPointMake(x, y);
	CGMouseButton mouseButton;
	CGEventType dragType;
		switch (button) {
		case 1:
			mouseButton = kCGMouseButtonLeft;
			dragType = kCGEventLeftMouseDragged;
			break;
		case 3:
			mouseButton = kCGMouseButtonRight;
			dragType = kCGEventRightMouseDragged;
			break;
		case 2:
			mouseButton = kCGMouseButtonCenter;
			dragType = kCGEventOtherMouseDragged;
			break;
		default:
			mouseButton = (CGMouseButton)(button-1);
			dragType = kCGEventOtherMouseDragged;
			break;
	}
	CGEventRef motion = CGEventCreateMouseEvent(NULL,dragType,destination,mouseButton);
	CGEventPost(kCGHIDEventTap, motion);
	CFRelease(motion);
}

void mouseButtonStatus(uint16_t button, uint16_t x, uint16_t y, bool status) {
	CGPoint destination = CGPointMake(x, y);
	CGEventType statusEvent;
	CGMouseButton mouseButton;

	std::cout << button << std::endl;

	switch (button) {
		case 1:
			if (status) {
				statusEvent = kCGEventLeftMouseDown;
			} else {
				statusEvent = kCGEventLeftMouseUp;
			}
			mouseButton = kCGMouseButtonLeft;
			break;
		case 3:
			if (status) {
				statusEvent = kCGEventRightMouseDown;
			} else {
				statusEvent = kCGEventRightMouseUp;
			}
			mouseButton = kCGMouseButtonRight;
			break;
		case 2:
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
			mouseButton = (CGMouseButton)(button-1);
			break;
	}

	CGEventRef click = CGEventCreateMouseEvent(NULL,statusEvent,destination,mouseButton);
	if (button > 3 || button == 2) {
		CGEventSetIntegerValueField(click, kCGMouseEventButtonNumber, button);
	}
	CGEventPost(kCGHIDEventTap,click);
	CFRelease(click);  

}

void mouseScroll(uint16_t x, uint16_t y, uint16_t dx, uint16_t dy) {

	CGPoint location = CGPointMake(x,y);
	CGEventRef motion = CGEventCreateScrollWheelEvent(NULL, kCGScrollEventUnitPixel,2,dx,dy);
	CGEventSetLocation(motion,location);
	CGEventPost(kCGHIDEventTap,motion);
	CFRelease(motion);


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
		uint8_t button;
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

			case Events::MOUSE_MOVE_ABSOLUTE:

				std::memcpy(&x, e_bytearray.data()+cur, sizeof_uint16_t);
				cur += sizeof_uint16_t;
				std::memcpy(&y, e_bytearray.data()+cur, sizeof_uint16_t);
				cur += sizeof_uint16_t;
				e.payload.push_back(static_cast<int>(x));
				e.payload.push_back(static_cast<int>(y));
				break;

			case Events::MOUSE_MOVE_RELATIVE:
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

			case Events::MOUSE_DRAG:

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

			default:
				break;
		}
		eventList.push_back(e);
	}
	return {eventList,""};
}

void PlayEventList(std::vector<EventPacket> eventList) {

	if (n_abort.load(std::memory_order_relaxed)) { return; }
	auto start = std::chrono::high_resolution_clock::now();
	uint64_t lastTimestamp = 0;
	for (EventPacket e : eventList) {
		if (n_abort.load(std::memory_order_relaxed)) { return; }
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
			case Events::MOUSE_MOVE_ABSOLUTE:
				func = [e]() -> void { moveMouseAbsolute(e.payload.at(0),e.payload.at(1)); };
				break;
			case Events::MOUSE_DOWN:
				func = [e]() -> void { mouseButtonStatus(e.payload.at(0),e.payload.at(1),e.payload.at(2),true); };
				break;
			case Events::MOUSE_UP:
				func = [e]() -> void { mouseButtonStatus(e.payload.at(0),e.payload.at(1),e.payload.at(2),false); };
				break;
			case Events::MOUSE_SCROLL:
				func = [e]() -> void { mouseScroll(e.payload.at(0),e.payload.at(1),e.payload.at(2),e.payload.at(3)); };
				break;
			case Events::MOUSE_DRAG:
				func = [e]() -> void { mouseDragAbsolute(e.payload.at(0),e.payload.at(1),e.payload.at(2)); };
		}
		while (std::chrono::high_resolution_clock::now() < insertTime) {
			if (n_abort.load(std::memory_order_relaxed)) { return; }
		}
		func();

	}
	
}

void CompileAndPlay(std::vector<uint8_t>& e_bytearray) {
	py::gil_scoped_release release;

	auto l = CompileEventArray(e_bytearray);
	PlayEventList(l.first);
}

PYBIND11_MODULE(playback, m) {
    m.def("CompileEventArray", &CompileEventArray, "i mean it just kind like parses the event array idk");
	m.def("PlayEventList", &PlayEventList, "i mean it just kind like plays the thingy if you know what i mean");
	m.def("CompileAndPlay", &CompileAndPlay, "i mean it just kind like plays the thingy with less intervention needed if you know what i mean");
	m.def("abortPlayback", &abortPlayback, "Sets flag n_abort to True, causing a running recording to stop after the current event finishes.");
	m.def("resetAbortPlayback", &resetAbortPlayback, "Sets flag n_abort to False. Allows you to play recordings again.");
	m.def("getAbortStatus", &getAbortStatus, "Returns the value of flag n_abort");
	
}