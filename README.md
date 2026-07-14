# Enhanced Rich Text Notepad

A feature-rich notepad built with **Tkinter** that supports rich text formatting, themes, auto-save, line numbers, and system tray functionality.

## Features

- **Rich Text Support** — Bold, Italic, Underline, Text & Background Colors
- **Custom File Format** — Saves formatting in `.ntd` files (JSON-based)
- **Multiple Themes** — Light, Dark, Solarized Dark
- **Line Numbers** — Toggleable sidebar
- **Syntax Highlighting** — Basic support for Python/Markdown
- **Auto-Save & Backups** — Automatic backups every 30 seconds
- **Zoom In/Out** — Mouse wheel + keyboard support
- **Recent Files** — Quick access to last 8 files
- **Find & Replace** — With regex support
- **Export to HTML**
- **System Tray Icon** — Minimize to tray with right-click menu
- **Auto Indent**
- **Word Wrap Toggle**

## Installation

1. **Clone or download** the project
2. Install required packages:

```bash
pip install pystray pillow

Run the application:

Bashpython notepad.py
Usage

Save files with .ntd extension to preserve formatting
Minimize the window → goes to system tray
Right-click the tray icon for options (Show, New, Save, Quit)
Use Ctrl + Mouse Wheel to zoom
Ctrl + B / I / U for quick formatting

Keyboard Shortcuts









































ShortcutActionCtrl + NNew FileCtrl + OOpen FileCtrl + SSaveCtrl + BBoldCtrl + IItalicCtrl + UUnderlineCtrl + FFind & ReplaceCtrl + Plus / MinusZoom In / Out
Project Structure
text├── notepad.py              # Main application
├── notepad_settings.json   # Saves theme, font, recent files
├── *.ntd                   # Your saved rich text files
└── *_backup_*.ntd          # Auto-generated backups
Requirements

Python 3.6+
Tkinter (usually comes with Python)
pystray
Pillow

Notes

The tray icon uses a built-in generated icon. You can replace create_tray_image() with your own .ico or .png file.
Full multi-tab support is prepared but currently in placeholder mode.
