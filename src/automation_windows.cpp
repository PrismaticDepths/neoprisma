#include <windows.h>
#include <cstdint>
#include "automation.h"

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

void moveMouseAbsolute(int32_t x, int32_t y) {
	
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

	input.mi.dx = (static_cast<long>(x)*65535)/ (GetSystemMetrics(SM_CXSCREEN) - 1); // size of length of primary monitor
	input.mi.dy = (static_cast<long>(y)*65535)/ (GetSystemMetrics(SM_CYSCREEN) - 1); // size of width of primary monitor

	input.mi.dwFlags = MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE;

	SendInput(1, &input, sizeof(INPUT));



}

void mouseButtonStatus(uint16_t button, int32_t x, int32_t y, bool status) {
	
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
}

void warpMouseAbsolute(int32_t x, int32_t y) {
    SetCursorPos(x, y);
}

void mouseDragAbsolute(uint8_t button, int32_t x, int32_t y) {
    INPUT input;
    ZeroMemory(&input, sizeof(INPUT));
    input.type = INPUT_MOUSE;
    input.mi.dx = (static_cast<long>(x) * 65535) / (GetSystemMetrics(SM_CXSCREEN) - 1);
    input.mi.dy = (static_cast<long>(y) * 65535) / (GetSystemMetrics(SM_CYSCREEN) - 1);
    input.mi.dwFlags = MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE;
    
    switch (button) {
        case 1: input.mi.dwFlags |= MOUSEEVENTF_LEFTDOWN; break;
        case 2: input.mi.dwFlags |= MOUSEEVENTF_RIGHTDOWN; break;
        case 3: input.mi.dwFlags |= MOUSEEVENTF_MIDDLEDOWN; break;
        default: return;
    }
    SendInput(1, &input, sizeof(INPUT));
}

void mouseButtonStatus(uint16_t button, bool status) {
    INPUT input = {};
    input.type = INPUT_MOUSE;

    switch (button) {
        case 1:
            input.mi.dwFlags = status ? MOUSEEVENTF_LEFTDOWN : MOUSEEVENTF_LEFTUP;
            break;
        case 2:
            input.mi.dwFlags = status ? MOUSEEVENTF_RIGHTDOWN : MOUSEEVENTF_RIGHTUP;
            break;
        case 3:
            input.mi.dwFlags = status ? MOUSEEVENTF_MIDDLEDOWN : MOUSEEVENTF_MIDDLEUP;
            break;
        default:
			// Windows does not support arbitrary mouse buttons
            return;
    }
    SendInput(1, &input, sizeof(INPUT));
}

void mouseScroll(int32_t x, int32_t y, uint16_t dx, uint16_t dy) {
    moveMouseAbsolute(x, y);
    if (dy != 0) {
        INPUT input = {0};
        input.type = INPUT_MOUSE;
        input.mi.dwFlags = MOUSEEVENTF_WHEEL;
        input.mi.mouseData = dy;
        SendInput(1, &input, sizeof(INPUT));
    }
    if (dx != 0) {
        INPUT input = {0};
        input.type = INPUT_MOUSE;
        input.mi.dwFlags = MOUSEEVENTF_HWHEEL;
        input.mi.mouseData = dx;
        SendInput(1, &input, sizeof(INPUT));
    }
}