# Neoprisma / nprisma

Neoprisma is a fast, clean, and reliable autoclicker & macro for MacOS (hopefully coming to Windows soon).
It is the successor to Prism's Autoclicker 4.0.

| | nprisma | prism's autoclicker |
| - | - | - |
| Autoclick | <ul><li>- [x] Customisable delay, only left click. </li></ul> | <ul><li>- [x] LMB, RMB, and most keys. Customizable delay. </li></ul> |
| Tasks | <ul><li>- [x] Keyboard, mouse, including mouse drag events. Adjustable playback speed. </li></ul> | <ul><li>- [x] Supports saving/loading to files, recording, and playback. </li></ul> |
| Interface | <ul><li>- [x] QT based System tray UI. </li></ul> | <ul><li>- [x] Very simple GUI using TkInter. No tray UI. </li></ul> |
| Easy Installation | <ul><li>- [x] Only a recent python release & git should be needed. The install script does the rest. Also checks for new versions automatically and can update itself. </li></ul> | <ul><li>- [ ] Had prebuilt binaries, but required manual de-quarantining. Currently requires a full manual build. </li></ul> |

## Installation

Neoprisma can be built and installed with its dedicated installer script.\
Support for installation via Homebrew is planned to be added soon.

You may inspect `install.sh` in the stable branch of this repository to make sure the code you are about to run is trustworthy.

```bash
curl -fsSL https://raw.githubusercontent.com/PrismaticDepths/neoprisma/stable/install.sh | $SHELL
```

*Once the install finishes, grant Neoprisma "Input Monitoring" and "Accessibility" permissions in System Settings.*

> Please note that you will need to install Python, pip, and Apple's Command Line Tools as a prerequisite for installing neoprisma. Pip is usually bundled with Python. If you have already installed these in the past, you may skip this step.
>
> - Official downloads for Python: https://www.python.org/downloads/
> - See this page for info on the Command Line Tools: https://developer.apple.com/documentation/xcode/installing-the-command-line-tools/

## Hotkeys / Usage

Hotkeys are configurable in the settings menu.

You can reset hotkeys and other configuration data by deleting the hidden file named `.neoprisma` in your home directory. To show hidden files, you can use the keyboard shortcut `<cmd>+<shift>+<.>` in Finder.

All default hotkeys are in the range of `<ctrl>+<fn>+<f7-f9>` (or `<ctrl>+<f7-f9>` if you have configured the function keys to need fn to do their special action)

`<ctrl><fn><f7>` - toggle recording\
`<ctrl><fn><f8>` - toggle autoclicker\
`<ctrl><fn><f9>` - toggle playback

## Known Issues

Hotkeys used to toggle recording are written into recordings. Neoprisma has safeguards to prevent any hotkeys contained in recordings from activating anything within itself, however if a hotkey in a recording conflicts with a hotkey from a different app, there is no guarantee that said app will ignore it. I plan to address this later.

## Performance

CPU usage does not seem to be excessive, nor does battery usage.
This is somewhat surprising considering that Neoprisma isn't optimized for either, and mostly optimized for accurate playback.

When testing with a recording of Geometry Dash gameplay (Stereo Madness), Neoprisma didn't do the best, getting as far as the middle of the first ship section after several tries.

Setting the process priority to 20 may help.
