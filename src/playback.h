#pragma once
#include <vector>
#include <cstdint>

struct EventPacket {
	uint64_t timestamp;
	uint8_t event;
	std::vector<uint8_t> payload;
};