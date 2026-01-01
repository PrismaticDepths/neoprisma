#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <cstdint>
#include <iostream>
#include <vector>
#include <ApplicationServices/ApplicationServices.h>
#include "playback.h"
namespace py = pybind11;

constexpr uint8_t MAJOR_FMT_VERSION = 1; // CHANGE IF YOU ALSO CHANGE THIS VARIABLE IN recorder.py
constexpr uint8_t EARLIEST_SUPPORTED_FMT_VERSION = 1; // LEAVE THIS ALONE UNLESS YOU MAKE BREAKING CHANGES AND CANT READ OLDER STUFF SOMEHOW
constexpr char FILE_HEADER_ID[4] = {'N','P','R','M'}; // DONT CHANGE THIS ONE

void keyStatus(uint16_t vk_code, bool status) {
	CGEventRef keyStroke = CGEventCreateKeyboardEvent(NULL, (CGKeyCode)vk_code, status);
	CGEventPost(kCGHIDEventTap, keyStroke);
	CFRelease(keyStroke);
}

std::pair<bool, uint8_t> ensureValidHeaders(std::vector<uint8_t>) {
	// just pretend there is code here
}

void playEventArray(std::vector<uint8_t> e_bytearray) {
	std::pair<bool, uint8> headerInfo = ensureValidHeaders(e_bytearray);
	if (headerInfo.first == false || headerInfo.second < EARLIEST_SUPPORTED_FMT_VERSION || headerInfo.second > MAJOR_FMT_VERSION ) {abort();}
}

PYBIND11_MODULE(playback, m) {
    m.def("hello", &hello, "says hi lol");
}
