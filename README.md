# ⚡ AUTOMAT — Task Automation Manager

[![CI](https://github.com/TheOpenDevTeam/automat/actions/workflows/test.yml/badge.svg)](https://github.com/TheOpenDevTeam/automat/actions)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

**AUTOMAT** is a powerful open-source task automation tool with a modern PyQt5 graphical interface. Built by [**OpenDev**](https://github.com/TheOpenDevTeam) — a startup of independent developers creating free and secure open-source applications.

---

## Features

### Built-in tools

| Tool | Description |
|------|-------------|
| **Dashboard** | Real-time activity overview with charts, quick actions, and system stats |
| **File Converter** | Excel↔PDF, PDF→Word, Images→PDF, CSV↔Excel, PDF→TXT |
| **Bulk HTTP Sender** | Send mass POST/GET requests with progress tracking |
| **Telegram Messenger** | Bulk messaging via Bot API with templates |
| **Hash & Encode** | MD5, SHA1/256/512, Base64, URL encode/decode |
| **Data Generator** | Generate JSON, CSV, SQL, XML with custom fields |
| **Data Cleaner** | Remove duplicates, normalize phones/emails, trim whitespace |
| **File Operations** | Rename, archive (zip/tar), search, organize by type |
| **Task Scheduler** | Cron, interval, and one-time tasks via APScheduler |
| **Text Tools** | UPPER/lower/Title transform, sort, dedup, search/replace, word stats |
| **Regex Tester** | Live regex matching with flag toggles and group capture display |

### v1.0 modules

| Tool | Description |
|------|-------------|
| **SSH Client** | Remote server access with command execution and preset commands |
| **Git Integration** | Clone, status, pull, push, commit, log, branch management |
| **API Client** | REST requests with JSON body/headers + JSON/YAML/XML formatter |
| **System Monitor** | Real-time CPU, RAM, Disk monitoring with PyQtChart graphs |
| **Snippets** | Code/template storage with category organization |

### v1.0 features

| Feature | Description |
|---------|-------------|
| **Global Search** | Search across all tools, settings, and activity log (Ctrl+Shift+F) |
| **Operation History** | Full timeline with filtering, pagination, and CSV/JSON export |
| **Custom Theme Builder** | Create, edit, import/export custom color themes with live preview |
| **Bookmarks** | Favorite pages for quick access via sidebar (Ctrl+D) |
| **Drag & Drop** | Drop files on the window — auto-detects type and opens the right tool |
| **Settings Export/Import** | Backup and restore all settings, bookmarks, and preferences (Ctrl+Shift+E/I) |
| **Check for Updates** | One-click update check via GitHub releases API (Ctrl+U) |

### UI / UX

- Dark and light themes with smooth toggle
- Real-time dashboard with activity charts (7-day history)
- Collapsible sidebar with animated transitions
- Quick calculator in the status bar
- Keyboard shortcuts (Ctrl+1..9 for pages, Ctrl+T for theme)
- Toast notification system
- i18n: Russian and English interface
- Window geometry persistence
- Global search (Ctrl+Shift+F)
- Bookmarks system (Ctrl+D)
- Drag & drop file support

---

## Installation

```bash
# Clone the repository
git clone https://github.com/TheOpenDevTeam/automat.git
cd automat

# Install (editable, recommended)
pip install -e .

# Run
python -m automat.main

# Or run the test suite
QT_QPA_PLATFORM=offscreen pytest tests/ -q
```

### System requirements

- **Python**: 3.9+
- **OS**: Windows 10/11, Linux, macOS
- **Dependencies**: PyQt5, requests, psutil, APScheduler, paramiko, openpyxl, Pillow, pdf2docx, reportlab

---

## Project structure

```
automat/
├── core/                  # Business logic layer
│   ├── activity_log.py    # SQLite activity logger + export/search
│   ├── app_logger.py      # Structured logging
│   ├── calc_manager.py    # Calculator logic
│   ├── clipboard_history.py # Clipboard history store + monitor
│   ├── clock_manager.py   # Clock timer
│   ├── db.py              # Shared SQLite plumbing (WAL, retry)
│   ├── json_io.py         # JSON persistence (quarantine, atomic save)
│   ├── theme_manager.py   # Theme switching
│   └── worker.py          # Background task runner
├── ui/
│   ├── pages/             # 22 application pages
│   │   ├── dash.py        # Dashboard
│   │   ├── search_page.py # Global search
│   │   ├── history_page.py# Operation history
│   │   ├── theme_builder.py# Theme builder
│   │   ├── clipboard_page.py # Clipboard history
│   │   ├── extra_tools.py # QR / color picker / curl converter
│   │   └── ...            # Other pages
│   ├── page_base.py       # Base page class
│   ├── widgets.py         # Reusable UI components
│   └── icons.py           # Icon system
├── app.py                 # Main window (QMainWindow)
├── config.py              # QSS themes, colors, app config
├── i18n.py                # i18n system (RU/EN)
├── main.py                # Entry point (`python -m automat.main`)
└── util.py                # GUI-thread marshaller
```

---

## Running tests

```bash
pip install pytest
pytest tests/ -v
```

---

## Building .exe

```bash
pip install pyinstaller
cd automat
pyinstaller --onedir --windowed --name "AUTOMAT" main.py
```

---

## License

This project is licensed under the **GNU General Public License v3.0**. See the [LICENSE](LICENSE) file for details.

---

## Contributing

We welcome contributions! Feel free to:
- Submit pull requests
- Report issues
- Suggest new features
- Improve documentation

---

