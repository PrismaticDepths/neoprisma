# Neoprisma / nprisma

Neoprisma is a fast, clean, and reliable autoclicker & macro for MacOS (hopefully coming to Windows soon).
It is the successor to Prism's Autoclicker 4.0.

## Roadmap

| Feature | Done | Description |
| - | - | - |
| Autoclick | <ul><li>- [ ] </li></ul> | Delay can be adjusted, but only left clicking is supported. | 
| Tasks/Macros | <ul><li>- [x] </li></ul> | Record keyboard and mouse, including mouse drag events. Adjustable playback speed. |
| Scripting/Full automation | <ul><li>- [ ] </li></ul> | Planned. |
| Interface | <ul><li>- [x] </li></ul> | QT based. Interface works fine, though more polish is planned. |
| Hotkeys | <ul><li>- [x] </li></ul> | Configurable. They work, but can get caught in recordings and sometimes get stuck. |
| Installer | <ul><li>- [ ] </li></ul> | Difficulties may arise if your Python install is not well configured. Otherwise, it is smooth sailing. |

## Installation

Neoprisma can be built and installed with its dedicated installer script.\
Support for installation via Homebrew is planned to be added soon.

You may inspect `install.sh` in the stable branch of this repository to make sure the code you are about to run is trustworthy.

```bash
curl -fsSL https://raw.githubusercontent.com/PrismaticDepths/neoprisma/stable/install.sh | $SHELL
```

*Once the install finishes, grant Neoprisma "Input Monitoring" and "Accessibility" permissions in System Settings.*

### Caveats

| Dependencies |
| - |
| You will need to install Python, pip, and Apple's Command Line Tools as a prerequisite for installing neoprisma. Pip is usually bundled with Python. If you have already installed these in the past, you may skip this step. |
| Official downloads for Python: https://www.python.org/downloads/ |
| See this page for info on the Command Line Tools: https://developer.apple.com/documentation/xcode/installing-the-command-line-tools/ |

| Permissions |
| - |
| Neoprisma requires *"Input Monitoring"* and *"Accessibility"* permissions to operate. You must re-grant these permissions every time you install or update Neoprisma. |
| *"Input Monitoring"* allows Neoprisma to monitor keyboard input. This is used for hotkeys, and the recording of tasks. |
| *"Accessibility"* allows, among other things, for Neoprisma to control your mouse and keyboard. This is used for autoclicking and playing back tasks. |
| You can grant these permissions in the "Privacy & Security" section of System Settings. |

## Hotkeys / Usage

Hotkeys are configurable in the settings menu.

| Default Keybind | Action |
| - | - |
|`<ctrl><fn><f7>` | toggle recording |
|`<ctrl><fn><f8>` | toggle autoclicker |
|`<ctrl><fn><f9>` | toggle playback |

You can reset hotkeys and other configuration data by deleting the hidden file named `.neoprisma` in your home directory. To show hidden files, you can use the keyboard shortcut `<cmd>+<shift>+<.>` in Finder.

## Known Issues

Hotkeys used to toggle recording are written into recordings. Neoprisma has safeguards to prevent any hotkeys contained in recordings from activating anything within itself, however if a hotkey in a recording conflicts with a hotkey from a different app, there is no guarantee that said app will ignore it. I plan to address this later.

Hotkeys sometimes become unresponsive. The only solution I have found to this is to spam all of the hotkeys. \
Alternatively, the "Abort Playback On Input" setting can be used, which will stop playback if you press a key. The apps own inputs should not trigger this.
You can also use the command-tab switcher to go to Neoprisma and quit it with `<command>+<q>` if you need.


## Performance

CPU usage does not seem to be excessive, nor does battery usage.
This is somewhat surprising considering that Neoprisma isn't optimized for either, and mostly optimized for accurate playback.

When testing with a recording of Geometry Dash gameplay (Stereo Madness), Neoprisma didn't do the best, getting as far as the middle of the first ship section after several tries.

Setting the process priority to 20 may help.
