#pragma once

#ifndef AUTOMATION_H
#define AUTOMATION_H

#include <cstdint>

void keyStatus(uint16_t vk_code, bool status);
void moveMouseAbsolute(uint16_t x, uint16_t y);
void mouseDragAbsolute(uint8_t button, uint16_t x, uint16_t y);
void mouseButtonStatus(uint16_t button, uint16_t x, uint16_t y, bool status);
void mouseScroll(uint16_t x, uint16_t y, uint16_t dx, uint16_t dy);

#endif