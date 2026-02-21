#include <windows.h>
#include <automation.h>

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

	input.mi.dx = (static_cast<long>(x)*65535)/ (GetSystemMetrics(SM_CXSCREEN) - 1); // size of length of primary monitor
	input.mi.dy = (static_cast<long>(y)*65535)/ (GetSystemMetrics(SM_CYSCREEN) - 1); // size of width of primary monitor

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