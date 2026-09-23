# installer/

Inno Setup script and assets for building the Chalchitra Windows installer.

## Prerequisites

- [Inno Setup 7](https://jrsoftware.org/isdl.php) (32-bit or 64-bit edition both work)
- Python environment with `Pillow` installed (for wizard image generation)

## Build steps

### 1. Build the application first

From the project root:

```bash
source venv/Scripts/activate
pyinstaller --clean --noconfirm Chalchitra.spec
This must succeed before the installer can be compiled — it packages dist/Chalchitra/.

2. Generate the wizard images
bash
python installer/make_wizard_images.py
Produces wizard-large.bmp and wizard-small.bmp in this folder.

3. Compile the installer
Locate ISCC.exe (the Inno Setup compiler). Common paths:

C:\Users\<you>\AppData\Local\Programs\Inno Setup 7\ISCC.exe (per-user install)

C:\Program Files (x86)\Inno Setup 7\ISCC.exe (system install)

Then run:

bash
"/c/Users/<you>/AppData/Local/Programs/Inno Setup 7/ISCC.exe" installer/Chalchitra.iss
Output is written to dist/Chalchitra-Setup-<version>.exe.

Customizing
Version number: edit #define MyAppVersion in Chalchitra.iss

Publisher / URLs: edit the #define block at the top

File associations: extend the .mp4 .mkv entries in [Registry]

Wizard colors / images: edit make_wizard_images.py and rerun

Welcome text / finish text: edit the [Code] section

Notes
The installer is per-user (no admin prompt). Files land in %LOCALAPPDATA%\Programs\Chalchitra\.

The uninstaller preserves user settings in %LOCALAPPDATA%\Chalchitra\.

Upgrade detection uses the AppId GUID in [Setup]. Never change it after the first public release.

text

Now the folder tree:
G:\Chalchitra_app
├── .gitignore
├── LICENSE
├── README.md
├── Chalchitra.spec
├── assets/
│ ├── icon.ico
│ └── fonts/
│ ├── README.md
│ ├── Roboto.ttf
│ └── MaterialSymbolsOutlined.ttf
├── installer/
│ ├── README.md
│ ├── Chalchitra.iss
│ └── make_wizard_images.py
├── libs/
│ └── README.md
└── src/
└── main.py

text

---

## Step 3 — Initialize git and make the first commit

```bash
cd /g/Chalchitra_app

# Initialize the repo with main as the default branch
git init -b main

# (Optional) Set a local identity if you want a different one for this repo
git config user.name "AirSilo"
git config user.email "gbhargov9@gmail.com"

# Stage everything except what .gitignore excludes
git add .

# Sanity check: what's about to be committed?
git status
git ls-files | wc -l
Verify before committing that no large or unwanted files are staged:

bash
git ls-files | grep -E "\.dll|venv|dist/|__pycache__"
That should return nothing. If any of those appear, your .gitignore isn't working — check that the file is named exactly .gitignore (with a leading dot) and is at the project root.

Now commit:

bash
git commit -m "Initial commit: Chalchitra v1.0.0

- Python + PySide6 + python-mpv media player
- Frameless custom UI with mint accent
- Full track/subtitle/HDR control
- Resume, recent files, playlist, geometry persistence
- Inno Setup installer script
- GPL v3 license"