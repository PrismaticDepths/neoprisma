#pragma once

#ifndef AUTOMATION_H
#define AUTOMATION_H

#include <cstdint>

void keyStatus(uint16_t vk_code, bool status);
void moveMouseAbsolute(int32_t x, int32_t y);
void warpMouseAbsolute(int32_t x, int32_t y);
void mouseDragAbsolute(uint8_t button, int32_t x, int32_t y);
void mouseButtonStatus(uint16_t button, int32_t x, int32_t y, bool status);
void mouseButtonStatus(uint16_t button, bool status);
void mouseScroll(int32_t x, int32_t y, uint16_t dx, uint16_t dy);

#endif