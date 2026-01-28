# NeoPrisma / nprisma

NeoPrisma is a fast, clean, and reliable autoclicker & macro for MacOS (hopefully coming to Windows soon).
It is the successor to Prism's Autoclicker 4.0.

| | nprisma | prism's autoclicker |
| - | - | - |
| Autoclick | <ul><li>- [x] Fixed at ~900CPS & left click </li></ul> | <ul><li>- [x] Supports autoclicking LMB, RMB, and most keys. </li></ul> |
| Tasks | <ul><li>- [x] Full support, including mouse drag events. </li></ul> | <ul><li>- [x] Supports saving/loading to files, recording, and playback. </li></ul> |
| Interface | <ul><li>- [x] Minimal system tray UI. </li></ul> | <ul><li>- [x] Very simple GUI using TkInter. </li></ul> |

## Installation

Neoprisma can be build and installed with its dedicated installer script.\
Support for installation via Homebrew is planned to be added soon.

> Please note that you will still need to install Python, pip, and Apple's Command Line Tools as a prerequisite for installing neoprisma. Pip is usually bundled with Python. If you have already installed these in the past, you may skip this step.
>
> - Official downloads for Python: https://www.python.org/downloads/
> - See this page for info on the Command Line Tools: https://developer.apple.com/documentation/xcode/installing-the-command-line-tools/

You may inspect `install.sh` in this repository to make sure the code you are about to run is trustworthy.\
If you are satisfied, execute the following in your terminal:

```bash
curl -fsSL https://raw.githubusercontent.com/PrismaticDepths/neoprisma/main/install.sh | bash
```

This will:

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

## Hotkeys

All hotkeys are in the range of `<ctrl>+<fn>+<f7-f9>` (or `<ctrl>+<f7-f9>` if you have configured the function keys to need fn to do their special action)

`<f7>` - toggle recording\
`<f8>` - toggle autoclicker\
`<f9>` - toggle playback\

## Known Issues

Pynput will sometimes crash due to a bug within the library, causing hotkeys to be unresponsive. Additionally, the program will sometimes get `trace trap`'d by the OS for no apparent reason when you toggle recording on. However, neoprisma is still much more stable than prism's autoclicker.

When ran as an app, Neoprisma currently fails as soon as recording is toggled on. This is due to extremely tight security regulations from MacOS, and the app is forcibly killed by the operating system with no way to catch or stop the termination. I am working on fixing this, but it might be a while.

A workaround to this is running the executable file inside the app bundle using your terminal. In Dinder, navigate to the installed neoprisma app (likely at `~/Applications/neoprisma`) and click "Show Contents". Open the "Contents" folder and then the "MacOS" folder and run the executable file you see. After granting your terminal accessibility and input monitoring permissons, you should be able to use neoprisma.

## Performance

CPU usage does not seem to be excessive, nor does battery usage.
This is somewhat surprising considering that neoprisma isn't optimized for either, and mostly optimized for accurate playback.

When testing with a recording of Geometry Dash gameplay, neoprisma didn't do the best, getting as far as the middle of the Stereo Madness ship section after several tries.

Setting the process priority to 20 may help.
