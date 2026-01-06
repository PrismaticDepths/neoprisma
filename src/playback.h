#pragma once
#include <vector>
#include <cstdint>

struct EventPacket {
	uint64_t timestamp;
	uint8_t event;
	std::vector<int> payload;
};

struct Events {
	static constexpr uint8_t KEY_DOWN = 10;
	static constexpr uint8_t KEY_UP = 11;
	static constexpr uint8_t MOUSE_DOWN = 20;
	static constexpr uint8_t MOUSE_UP = 21;
	static constexpr uint8_t MOUSE_MOVE_ABSOLUTE = 22;
	static constexpr uint8_t MOUSE_MOVE_RELATIVE = 23;
	static constexpr uint8_t MOUSE_ABS_MOVE = 22;
	static constexpr uint8_t MOUSE_REL_MOVE = 23;
	static constexpr uint8_t MOUSE_SCROLL = 24;
	static constexpr uint8_t MOUSE_DRAG = 25;
};