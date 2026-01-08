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
constexpr char FILE_HEADER_ID[11] = {'<','N','E','O','P','R','I','S','M','A','>'}; // DONT CHANGE THIS ONE
constexpr uint8_t FILE_HEADER_ID_SIZE = 11;

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

std::pair<bool, uint8_t> ensureValidHeaders(const std::vector<uint8_t>& e_bytearray) {
	uint8_t version = 0;
	if (e_bytearray.size() < FILE_HEADER_ID_SIZE+1 || std::memcmp(e_bytearray.data(),FILE_HEADER_ID,FILE_HEADER_ID_SIZE) != 0) {
		return {false, version};
	} else {
		std::memcpy(&version,e_bytearray.data()+FILE_HEADER_ID_SIZE,sizeof(version));
		if (version < EARLIEST_SUPPORTED_FMT_VERSION || version > MAJOR_FMT_VERSION) {
			return {false, version};
		} else {
			return {true,version};
		}
	} 
}

std::pair<std::vector<EventPacket>, std::string> CompileEventArray(const std::vector<uint8_t>& e_bytearray) {
	std::pair<bool, uint8_t> headerInfo = ensureValidHeaders(e_bytearray);
	std::vector<EventPacket> eventList;
	if (!headerInfo.first) {
		std::cerr << "nprisma: bad fileheader, found version " << int(headerInfo.second) << " (must be >=" << int(EARLIEST_SUPPORTED_FMT_VERSION) << "& <=" << int(MAJOR_FMT_VERSION) << ")" << std::endl;
		if (headerInfo.second == 0) {
			throw std::runtime_error("Incompatible file format (11byte header does not match; not a .neop recording)");
		} else {
			throw std::runtime_error("Incompatible version, file is version " + std::to_string(headerInfo.second) + " (must be >=" + std::to_string(EARLIEST_SUPPORTED_FMT_VERSION) + "&& <=" + std::to_string(MAJOR_FMT_VERSION) + ")" );
		}

		return {eventList,"Failed to parse event array: Bad file header or incompatible version."}; 
	}
	for (size_t cur = FILE_HEADER_ID_SIZE+1; cur < e_bytearray.size();) {
		EventPacket e;
		if (cur + sizeof_uint64_t + sizeof_uint8_t > e_bytearray.size()) { throw std::runtime_error("Corrupt or truncated event array (broken EventPacket header @ "+std::to_string(cur)+")"); }
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
				if (cur + sizeof_uint16_t > e_bytearray.size()) { throw std::runtime_error("Corrupt or truncated event array. (broken EventPacket payload @ index "+std::to_string(cur)+")"); }

				uint16_t vk;
				std::memcpy(&vk, e_bytearray.data()+cur, sizeof_uint16_t);
				cur += sizeof_uint16_t;
				e.payload.push_back(static_cast<int>(vk));
				break;

			case Events::MOUSE_DOWN:
			case Events::MOUSE_UP:
				if (cur + sizeof_uint8_t + sizeof_uint16_t + sizeof_uint16_t > e_bytearray.size()) { throw std::runtime_error("Corrupt or truncated event array. (broken EventPacket payload @ index "+std::to_string(cur)+")"); }
				
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
				if (cur + sizeof_uint16_t + sizeof_uint16_t > e_bytearray.size()) { throw std::runtime_error("Corrupt or truncated event array. (broken EventPacket payload @ index "+std::to_string(cur)+")"); }

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
				if (cur + sizeof_uint16_t + sizeof_uint16_t + sizeof_uint16_t + sizeof_uint16_t > e_bytearray.size()) { throw std::runtime_error("Corrupt or truncated event array. (broken EventPacket payload @ index "+std::to_string(cur)+")"); }

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
				if (cur + sizeof_uint8_t + sizeof_uint16_t + sizeof_uint16_t > e_bytearray.size()) { throw std::runtime_error("Corrupt or truncated event array. (broken EventPacket payload @ index "+std::to_string(cur)+")"); }

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
				throw std::runtime_error("Corrupt or outdated event array. (Unknown event type <"+std::to_string(e.event)+"> encountered @ index "+std::to_string(cur)+")");
				break;
		}
		eventList.push_back(e);
	}
	return {eventList,""};
}

void PlayEventList(const std::vector<EventPacket>& eventList) {
	py::gil_scoped_release release;

	if (n_abort.load(std::memory_order_relaxed)) { return; }
	auto start = std::chrono::steady_clock::now();
	for (const EventPacket& e : eventList) {
		if (n_abort.load(std::memory_order_relaxed)) { return; }
		auto insertTime = start + std::chrono::nanoseconds(e.timestamp);
		while (true) {
			if (n_abort.load(std::memory_order_relaxed)) { return; }
			auto now = std::chrono::steady_clock::now();
			if (now >= insertTime) { break; }
			auto remaining = insertTime - now;
			if (remaining > std::chrono::nanoseconds(200)) {
				std::this_thread::sleep_for(remaining-std::chrono::nanoseconds(200));
			} else {
				std::this_thread::yield();
			}
		}
		switch (e.event) {
			case Events::KEY_DOWN:
				keyStatus(e.payload.front(),true);
				break;
			case Events::KEY_UP:
				keyStatus(e.payload.front(),false);
				break;
			case Events::MOUSE_MOVE_ABSOLUTE:
				moveMouseAbsolute(e.payload.at(0),e.payload.at(1));
				break;
			case Events::MOUSE_DOWN:
				mouseButtonStatus(e.payload.at(0),e.payload.at(1),e.payload.at(2),true);
				break;
			case Events::MOUSE_UP:
				mouseButtonStatus(e.payload.at(0),e.payload.at(1),e.payload.at(2),false);
				break;
			case Events::MOUSE_SCROLL:
				mouseScroll(e.payload.at(0),e.payload.at(1),e.payload.at(2),e.payload.at(3));
				break;
			case Events::MOUSE_DRAG:
				mouseDragAbsolute(e.payload.at(0),e.payload.at(1),e.payload.at(2));
				break;
		}

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
	m.def("abortPlayback", &abortPlayback, "Sets flag n_abort to True, causing a running recording to stop after the current event finishes.");
	m.def("resetAbortPlayback", &resetAbortPlayback, "Sets flag n_abort to False. Allows you to play recordings again.");
	m.def("getAbortStatus", &getAbortStatus, "Returns the value of flag n_abort");
	py::class_<EventPacket>(m, "EventPacket")
        .def(py::init<>()) // Expose the default constructor to allow creation in Python
        .def_readwrite("timestamp", &EventPacket::timestamp)
        .def_readwrite("event", &EventPacket::event)
        .def_readwrite("payload", &EventPacket::payload);
}