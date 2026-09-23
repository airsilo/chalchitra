<div align="center">

# Chalchitra

**A minimal, fully offline media player for Windows.**

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Platform: Windows 10+](https://img.shields.io/badge/Platform-Windows%2010%2B-lightgrey.svg)]()
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg)]()

Made by [AirSilo](https://airsilo.space)

</div>

---

## Overview

Chalchitra is a lightweight, privacy-first video player for Windows. It plays almost every popular video format out of the box, works entirely offline, and contains no telemetry, analytics, or network calls of any kind.

Built with **Python**, **PySide6 (Qt 6)**, and **mpv** for playback.

## Features

- **Broad format support** — MP4, MKV, AVI, MOV, WebM, FLV, WMV, M4V, TS, MPG, MPEG, M2TS, OGV, 3GP
- **Hardware-accelerated decoding** via mpv (auto-selected)
- **Frameless custom UI** with mint accent, Roboto + Material Symbols
- **Full track control** — switch audio, video, and subtitle tracks mid-playback
- **Subtitle styling** — font family, size, bold, text color, outline color, outline size, with live preview
- **Load custom fonts** — drop any `.ttf` or `.otf` into Subtitle Settings
- **Audio sync offset** — correct any drift between audio and video (±1 s in 0.1 s steps)
- **Audio channel modes** — Auto, Mono, Stereo, 5.1, 7.1
- **HDR modes** — Auto, On (passthrough), Off (tone-map to SDR)
- **Playback speed** — 0.25× to 4× with one-key cycling
- **Resume position** — remembers where you left off, per file
- **Recent files** — quick access to the last 10 played files
- **Playlist** — multi-file drop, next/prev, jump to item
- **Remember last import folder** — file dialog reopens where you last picked a file
- **Window geometry persistence** — position, size, and maximize state survive restarts
- **Fullscreen with auto-hide** — bars and cursor fade away after 2.2 s idle
- **Drag-and-drop** — drop files onto the window to play
- **Right-click integration** — "Play with Chalchitra" on every video file

## Screenshots

> Screenshots coming soon.

## System requirements

- **Windows 10 or 11 (64-bit only)**
- ~250 MB disk space for the installed app

## Installation

### Option 1 — Installer (recommended)

Download the latest `Chalchitra-Setup-<version>.exe` from the [Releases](https://github.com/airsilo/chalchitra/releases) page.

Double-click and follow the wizard. The installer:

- Places the app in `%LOCALAPPDATA%\Programs\Chalchitra\`
- Adds Start menu and (optionally) desktop shortcuts
- Registers Chalchitra in "Open with" for common video formats
- Adds a "Play with Chalchitra" right-click entry
- Provides a working uninstaller in Settings → Apps

Your settings are preserved between installs and uninstalls. They live in:
%LOCALAPPDATA%\Chalchitra\settings.ini

text

### Option 2 — Portable

Grab `Chalchitra-Portable-<version>.zip` from the same Releases page. Extract anywhere and run `Chalchitra.exe`. No installation, no registry changes.

## Building from source

Requires **Python 3.11+** and **Git**.

### 1. Clone the repository

git clone https://github.com/airsilo/chalchitra.git
cd chalchitra
2. Get the mpv engine
Follow libs/README.md to download libmpv-2.dll and place it in libs/.

3. Set up a virtual environment
Git Bash:

bash
python -m venv venv
source venv/Scripts/activate
PowerShell:

powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
4. Install dependencies
bash
pip install PySide6 python-mpv PyOpenGL Pillow pyinstaller
5. Run from source
bash
python src/main.py
Open a video with File → Open File, Ctrl+O, or drag-and-drop. You can also pass a path directly:

bash
python src/main.py "D:\path\to\video.mkv"
Packaging
Build the standalone app
bash
pyinstaller --clean --noconfirm Chalchitra.spec
Output: dist/Chalchitra/Chalchitra.exe + _internal/ folder.

Build the Windows installer (optional)
Requires Inno Setup 7 — see installer/README.md.

bash
python installer/make_wizard_images.py
"/c/Users/<you>/AppData/Local/Programs/Inno Setup 7/ISCC.exe" installer/Chalchitra.iss
Output: dist/Chalchitra-Setup-<version>.exe.

Keyboard shortcuts
Key	Action
Space	Play / pause
← / →	Seek ∓5 s
↑ / ↓	Seek ±30 s
F	Toggle fullscreen
Esc	Exit fullscreen
M	Mute
+ / -	Volume up / down
A	Cycle audio track
V	Cycle subtitle track
Shift+V	Open subtitle settings
[ / ]	Slow down / speed up
\	Reset speed to 1×
H	Cycle HDR mode
N / P	Next / previous in playlist
Ctrl+O	Open file
Ctrl+Q	Quit
Configuration
All persistent settings live in a single INI file:

text
%LOCALAPPDATA%\Chalchitra\settings.ini
It stores volume, speed, HDR mode, subtitle styling, window geometry, recent files, resume positions, and your last-used import folder. Delete the file to reset everything.

Tech stack
Component	Purpose
PySide6	Qt 6 user interface
python-mpv	Python bindings for libmpv
mpv	Playback engine (embedded as libmpv-2.dll)
Pillow	Icon generation from SVG
Inno Setup	Windows installer
License
Chalchitra is licensed under the GNU General Public License v3.0. See LICENSE for the full text.

You are free to use, modify, and redistribute Chalchitra under the terms of the GPL. If you distribute a modified version, you must make its source code available under the same license.

Because Chalchitra dynamically links against libmpv (licensed under LGPL v2.1+), the two licenses are compatible — GPL v3 applications may link against LGPL libraries.

Credits
Playback engine: the mpv team

Windows builds of libmpv: shinchiro/mpv-winbuild-cmake

UI framework: the Qt Project

Fonts: Roboto and Material Symbols by Google (Apache 2.0)

Contributing
Issues and pull requests are welcome at github.com/airsilo/chalchitra.

Before opening an issue, please check the existing issues to avoid duplicates.

<div align="center">
Made by AirSilo

</div> ```

