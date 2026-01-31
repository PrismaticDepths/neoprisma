# Neoprisma / nprisma

Neoprisma is a fast, clean, and reliable autoclicker & macro for MacOS (hopefully coming to Windows soon).
It is the successor to Prism's Autoclicker 4.0.

| | nprisma | prism's autoclicker |
| - | - | - |
| Autoclick | <ul><li>- [x] Fixed at ~900CPS & left click </li></ul> | <ul><li>- [x] LMB, RMB, and most keys. Customizable delay. </li></ul> |
| Tasks | <ul><li>- [x] Keyboard, mouse, including mouse drag events. </li></ul> | <ul><li>- [x] Supports saving/loading to files, recording, and playback. </li></ul> |
| Interface | <ul><li>- [x] QT based System tray UI. </li></ul> | <ul><li>- [x] Very simple GUI using TkInter. No tray UI. </li></ul> |
| Easy Installation | <ul><li>- [x] Only a recent python release & git should be needed. The install script does the rest. </li></ul> | <ul><li>- [x] Had prebuilt binaries, but required manual de-quarantining. Currently requires a full manual build. </li></ul> |

## Installation

Neoprisma can be built and installed with its dedicated installer script.\
Support for installation via Homebrew is planned to be added soon.

You may inspect `install.sh` in this repository to make sure the code you are about to run is trustworthy.\
If you are satisfied, execute the following in your terminal:

```bash
curl -fsSL https://raw.githubusercontent.com/PrismaticDepths/neoprisma/main/install.sh | bash
```

Once the install finishes, grant the application "Input Monitoring" and "Accessibility" permissions in System Settings.

> Please note that you will still need to install Python, pip, and Apple's Command Line Tools as a prerequisite for installing neoprisma. Pip is usually bundled with Python. If you have already installed these in the past, you may skip this step.
>
> - Official downloads for Python: https://www.python.org/downloads/
> - See this page for info on the Command Line Tools: https://developer.apple.com/documentation/xcode/installing-the-command-line-tools/

This install script will do the following for you:

1. Ensure all dependencies are installed before running
2. Ask to clean the target build directory (if it already exists)
3. Clone this git repository into the build directory
4. Create a virtual environment and install dependencies from `requirements.txt`
5. Install `pyinstaller`
6. Compile the C++ portions of the app into `.so` binaries
7. Build the program as a `.app` bundle.
8. Move the app into the target installation directory
9. Sign the app's code
10. Clean up after itself (erase the build directory since it is not needed anymore)

## Hotkeys / Usage

All hotkeys are in the range of `<ctrl>+<fn>+<f7-f9>` (or `<ctrl>+<f7-f9>` if you have configured the function keys to need fn to do their special action)

`<ctrl><fn><f7>` - toggle recording\
`<ctrl><fn><f8>` - toggle autoclicker\
`<ctrl><fn><f9>` - toggle playback

## Known Issues

Pynput will sometimes crash due to a bug within the library, causing hotkeys to be unresponsive. Additionally, the program will sometimes get `trace trap`'d by the OS for no apparent reason when you toggle recording on. However, Neoprisma is still much more stable than prism's autoclicker.

Parts of Neoprisma hotkeys can sometimes get caught in recordings. In theory, this should have little to no effect since Neoprisma already blocks activation of recording, playing, or autoclicking if it is already doing one of the three.

The speed of the autoclicking is actually high enough it can sometimes cause real input events to be dropped, resulting in a less responsive keyboard and mouse. I will add customizable speed soon, so this should be less of a problem. Just note that anything over ~1000CPS is a bad idea.

## Performance

CPU usage does not seem to be excessive, nor does battery usage.
This is somewhat surprising considering that Neoprisma isn't optimized for either, and mostly optimized for accurate playback.

When testing with a recording of Geometry Dash gameplay (Stereo Madness), Neoprisma didn't do the best, getting as far as the middle of the first ship section after several tries.

Setting the process priority to 20 may help.
