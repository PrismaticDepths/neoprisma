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
namespace py = pybind11;


constexpr uint8_t MAJOR_FMT_VERSION = 1; // CHANGE IF YOU ALSO CHANGE THIS VARIABLE IN recorder.py
constexpr uint8_t EARLIEST_SUPPORTED_FMT_VERSION = 1; // LEAVE THIS ALONE UNLESS YOU MAKE BREAKING CHANGES AND CANT READ OLDER STUFF SOMEHOW
constexpr char FILE_HEADER_ID[11] = {'<','N','E','O','P','R','I','S','M','>'}; // DONT CHANGE THIS ONE
cosntexpr uint8_t FILE_HEADER_ID_SIZE = 11;

constexpr size_t sizeof_uint8_t = sizeof(uint8_t);
constexpr size_t sizeof_uint16_t = sizeof(uint16_t);
constexpr size_t sizeof_int16_t = sizeof(int16_t);
constexpr size_t sizeof_uint64_t = sizeof(uint64_t);

std::atomic<bool> n_abort{false};



std::pair<bool, uint8_t> ensureValidHeaders(std::vector<uint8_t>& e_bytearray) {
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
std::pair<std::vector<EventPacket>, std::string> CompileEventArray(std::vector<uint8_t>& e_bytearray) {
	std::pair<bool, uint8_t> headerInfo = ensureValidHeaders(e_bytearray);
	std::vector<EventPacket> eventList;
	if (!headerInfo.first) {
		std::cerr << "nprisma: bad fileheader, found version " << int(headerInfo.second) << " (must be <=" << int(EARLIEST_SUPPORTED_FMT_VERSION) << "& >=" << int(MAJOR_FMT_VERSION) << ")" << std::endl;
		if (headerInfo.second == 0) {
			throw std::runtime_error("Incompatible file format (not a .neop recording)");
		} else {
			throw std::runtime_error("Incompatible version, file is version " + std::to_string(headerInfo.second) + " (must be <=" + std::to_string(EARLIEST_SUPPORTED_FMT_VERSION) + " & >=" + std::to_string(MAJOR_FMT_VERSION) + ")" );
		}

		return {eventList,"Failed to parse event array: Bad file header or incompatible version."}; 
	}
	for (size_t cur = FILE_HEADER_ID_SIZE+1; cur < e_bytearray.size();) {
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
	//m.def("setDPIAwareness", &setDPIAwareness, "Sets the process DPI awareness to handle high-DPI displays correctly on Windows.");
}