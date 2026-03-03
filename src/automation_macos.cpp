#include <ApplicationServices/ApplicationServices.h>
#include <cstdint>
#include "automation.h"

static CGEventSourceRef source = CGEventSourceCreate(kCGEventSourceStateHIDSystemState);

void keyStatus(uint16_t vk_code, bool status) {
	CGEventRef keyStroke = CGEventCreateKeyboardEvent(source, (CGKeyCode)vk_code, status);
	CGEventPost(kCGHIDEventTap, keyStroke);
	CFRelease(keyStroke);
}

void moveMouseAbsolute(uint16_t x, uint16_t y) {
	CGPoint destination = CGPointMake(x, y);
	CGEventRef motion = CGEventCreateMouseEvent(source,kCGEventMouseMoved,destination,kCGMouseButtonLeft);
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
	CGEventRef motion = CGEventCreateMouseEvent(source,dragType,destination,mouseButton);
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

	CGEventRef click = CGEventCreateMouseEvent(source,statusEvent,destination,mouseButton);
	if (button > 3 || button == 2) {
		CGEventSetIntegerValueField(click, kCGMouseEventButtonNumber, button);
	}
	CGEventPost(kCGHIDEventTap,click);
	CFRelease(click);  

}

void mouseScroll(uint16_t x, uint16_t y, uint16_t dx, uint16_t dy) {

	CGPoint location = CGPointMake(x,y);
	CGEventRef motion = CGEventCreateScrollWheelEvent(source, kCGScrollEventUnitPixel,2,dx,dy);
	CGEventSetLocation(motion,location);
	CGEventPost(kCGHIDEventTap,motion);
	CFRelease(motion);

}
