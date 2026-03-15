<div align="center">

  <img src="src/assets/preview.png" alt="App Icon">

  <h1>Neoprisma</h1>

  <p>
    Lightweight macro & autoclick utility for MacOS
  </p>

  <p>
    <img src="https://img.shields.io/badge/license-GPLv3.0-blue?style=flat" alt="License">
    <img alt="GitHub top language" src="https://img.shields.io/github/languages/top/prismaticdepths/neoprisma?style=flat">
    <img alt="GitHub language count" src="https://img.shields.io/github/languages/count/prismaticdepths/neoprisma">
    <img alt="GitHub Actions Workflow Status" src="https://img.shields.io/github/actions/workflow/status/prismaticdepths/neoprisma/.github%2Fworkflows%2Fbuild.yml">
    <img alt="GitHub Repo stars" src="https://img.shields.io/github/stars/prismaticdepths/neoprisma?style=flat&color=yellow">
    <img alt="GitHub Tag" src="https://img.shields.io/github/v/tag/prismaticdepths/neoprisma">
  </p>

</div>

# Neoprisma / nprisma

Neoprisma is a simple, reliable, and open source autoclicker/macro utility for MacOS

For too long, sketchy, malware-infected TinyTask versions have ruled the internet in terms of automation. Neoprisma changes that.\
Neoprisma is open-source, so you can actually see the code you are running, meaning no more trusting random blobs you can't see the internals of. Additionally, the app works on Mac!\
Ironically, only MacOS is currently supported, however cross-platform support is a future goal. Neoprisma is an active project, and updates are released very frequently.

## Features

* ✅ Record & play back any keyboard and mouse inputs
* ✅ Save recordings to files and load them anytime
* ✅ Autoclick at high speeds 
* ✅ Fully configurable hotkeys
* ✅ Adjustable playback speeds

## Roadmap

| Feature | Done | Description |
| - | - | - |
| Autoclick | <ul><li>- [ ] </li></ul> | Delay can be adjusted, but only left clicking is supported. | 
| Tasks/Macros | <ul><li>- [x] </li></ul> | Record nearly any sequence of keyboard and mouse inputs. Adjustable playback speed. Tasks can be saved and loaded from files.  |
| Scripting/Full automation | <ul><li>- [ ] </li></ul> | Planned. |
| Interface | <ul><li>- [x] </li></ul> | Primarily system tray based, but has normal UI too. Features automatic update prompting, and dedicated settings window. Icon auto-hides from the dock. |
| Hotkeys | <ul><li>- [x] </li></ul> | Highly configurable. Bugs are still present, however they will be worked out sooner than later. |
| Installer | <ul><li>- [x] </li></ul> | Build from source or download precompiled bundles. The installer will do everything for you with helpful visuals along the way. |

## Installation

Neoprisma can be built from source or installed with its dedicated installer script.\
*Once the install finishes, grant Neoprisma "Input Monitoring" and "Accessibility" permissions in System Settings.*

Before running, inspect `install.sh` in the stable branch of this repository to make sure the code you are about to run is trustworthy. Only proceed if you are satisfied.

Install prebuilt bundle (recommended):
```bash
curl -fsSL https://raw.githubusercontent.com/PrismaticDepths/neoprisma/stable/install.sh | $SHELL
```


Build from source:
```bash
curl -fsSL https://raw.githubusercontent.com/PrismaticDepths/neoprisma/stable/install.sh | $SHELL -s  -- -s
```

### Installer Flags

```
-b BUILD_DIR (Set a different build directory. Absolute paths are recommended.)
-i INSTALL_DIR (Set a different install directory. Absolute paths are recommended.)
-r BRANCH (Clone from a different branch if building from source, such as 'main'.)
-y (Runs in non-interactive mode and automatically accepts all prompts)
-s (Build from source and do not attempt to download a bundle)
---
Example:
curl -fsSL https://raw.githubusercontent.com/PrismaticDepths/neoprisma/stable/install.sh | $SHELL -s  -- -s -y -r main
This would build from source, skip any prompts, and build from the main branch instead of the stable one.
```


### Caveats

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

Hotkeys used to toggle recording are written into recordings. Neoprisma has safeguards to prevent any hotkeys contained in recordings from activating anything within itself, however if a hotkey in a recording conflicts with a hotkey from a different app, there is no guarantee that said app will ignore it. I plan to address this later, and also add suppression so that hotkeys won't also go to other apps when you trigger them.

Hotkeys sometimes become unresponsive. The only solution I have found to this is to spam all of the hotkeys. \
Alternatively, the "Abort Playback On Input" setting can be used, which will stop playback if you press a key. The apps own inputs should not trigger this.
You can also use the command-tab switcher to go to Neoprisma and quit it with `<command>+<q>` if you need.


## Performance

When idle, CPU usage and RAM are very low. However, CPU usage spikes upon mouse movement and keyboard activity, to about 10% of a single core (tested on an M3 Pro). Neoprisma isn't actually optimized for either, and mostly optimized for accurate playback, however there is room to improve here and hence this will probably be improved someday.

When testing with a recording of Geometry Dash gameplay (Stereo Madness), Neoprisma didn't do the best, getting as far as the middle of the first ship section after several tries. This was with an early version of Neoprisma; I have yet to see if there is any difference on later versions.

Setting the process priority to 20 may help.

## Acknowledgements

Thank you to @xbytz for helping to port the majority of the C++ portion of the app to Windows.
