import os
from pathlib import Path

APP_NAME = "AUTOMAT"
APP_VERSION = "1.0"
APP_TITLE = "AUTOMAT — Task Automation Manager"
ORG_NAME = "Auxo"

DATA_DIR = Path(os.getenv("APPDATA", Path.home())) / "Automat"
DATA_DIR.mkdir(parents=True, exist_ok=True)
SETTINGS_FILE = str(DATA_DIR / "settings.json")
TASKS_FILE = str(DATA_DIR / "tasks.json")

UI_FONT = "Segoe UI"

PROXY_DEFAULTS = {"host": "", "port": "", "user": "", "pass": ""}


def load_proxy(settings_data: dict) -> dict | None:
    p = settings_data.get("proxy", {})
    if p and p.get("host"):
        proxy_url = f"http://{p.get('user', '')}:{p.get('pass', '')}@{p['host']}:{p.get('port', '')}" if p.get('user') else f"http://{p['host']}:{p.get('port', '')}"
        if p.get('user'):
            proxy_url = f"http://{p['user']}:{p['pass']}@{p['host']}:{p['port']}"
        else:
            proxy_url = f"http://{p['host']}:{p['port']}"
        return {"http": proxy_url, "https": proxy_url}
    return None


ACCENT = "#4f8ef7"
ACCENT2 = "#a855f7"
GREEN = "#22d3a5"
YELLOW = "#f5c842"
RED = "#f74f4f"

DARK_STYLE = """
QMainWindow, QWidget { background-color: #0b0f1a; color: #e2e8f0; font-family: "Segoe UI"; }
QFrame#header { background-color: #0f1525; border: none; border-bottom: 1px solid #1e2745; }
QFrame#sidebar { background-color: #0d1220; border: none; border-right: 1px solid #1a2140; }
QFrame#card { background-color: #131a2e; border: 1px solid #1e2745; border-radius: 10px; }
QFrame#card:hover { border: 1px solid #4f8ef7; }
QFrame#card_accent { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #131a2e, stop:1 #162040); border: 1px solid #1e2745; border-radius: 10px; }
QPushButton { background-color: #1a2340; color: #e2e8f0; border: 1px solid #2a3555; border-radius: 8px; padding: 8px 16px; font-family: "Segoe UI"; font-size: 10pt; }
QPushButton:hover { background-color: #243050; border: 1px solid #4f8ef7; }
QPushButton:pressed { background-color: #2a3555; }
QPushButton#accent { background-color: #4f8ef7; color: white; border: none; font-weight: bold; padding: 8px 16px; min-height: 20px; min-width: 60px; }
QPushButton#accent:hover { background-color: #3b7de6; }
QPushButton#accent2 { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f8ef7, stop:1 #a855f7); color: white; border: none; font-weight: bold; padding: 8px 16px; min-height: 20px; min-width: 60px; }
QPushButton#accent2:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3b7de6, stop:1 #9333ea); }
QPushButton#success { background-color: #22d3a5; color: #0b0f1a; border: none; font-weight: bold; padding: 8px 16px; min-height: 20px; min-width: 60px; }
QPushButton#success:hover { background-color: #1bbd92; }
QPushButton#danger { background-color: #f74f4f; color: white; border: none; font-weight: bold; padding: 8px 16px; min-height: 20px; min-width: 60px; }
QPushButton#danger:hover { background-color: #e04040; }
QPushButton#sidebar_btn { background-color: transparent; color: #8899b0; border: none; text-align: left; padding: 10px 16px; border-radius: 0; font-family: "Segoe UI"; font-size: 10pt; border-left: 3px solid transparent; }
QPushButton#sidebar_btn:hover { background-color: #131a2e; color: #e2e8f0; }
QPushButton#sidebar_btn:checked { background-color: #131a2e; color: #ffffff; border-left: 3px solid #4f8ef7; }
QPushButton#icon_btn { background-color: transparent; color: #8899b0; border: 1px solid #2a3555; border-radius: 8px; padding: 6px; font-size: 14pt; min-width: 36px; min-height: 36px; }
QLabel#sidebar_section { color: #5a6a8a; font-family: "Segoe UI"; font-size: 8pt; font-weight: bold; padding: 10px 16px 6px; letter-spacing: 1px; }
QPushButton#icon_btn:hover { background-color: #1a2340; color: #e2e8f0; border: 1px solid #4f8ef7; }
QLabel { color: #e2e8f0; font-family: "Segoe UI"; }
QLabel#header_title { font-size: 18pt; font-weight: bold; color: #ffffff; letter-spacing: 1px; }
QLabel#text_muted { color: #7c8db0; font-size: 9pt; }
QLabel#text_secondary { color: #94a3b8; }
QLabel#stat_value { font-size: 26pt; font-weight: bold; color: #ffffff; }
QLabel#stat_label { color: #94a3b8; font-size: 9pt; }
QLabel#stat_today { color: #7c8db0; font-size: 8pt; }
QLineEdit { background-color: #1a2340; color: #e2e8f0; border: 1px solid #2a3555; border-radius: 8px; padding: 8px 12px; font-family: "Segoe UI"; font-size: 10pt; }
QLineEdit:focus { border: 1px solid #4f8ef7; }
QLineEdit[inputState="false"] { border: 1px solid #f74f4f; }
QTextEdit, QPlainTextEdit { background-color: #0b0f1a; color: #e2e8f0; border: 1px solid #2a3555; border-radius: 8px; font-family: "Consolas"; font-size: 10pt; padding: 8px; }
QComboBox { background-color: #1a2340; color: #e2e8f0; border: 1px solid #2a3555; border-radius: 8px; padding: 8px 12px; font-family: "Segoe UI"; font-size: 10pt; }
QComboBox:hover { border: 1px solid #4f8ef7; }
QComboBox::drop-down { border: none; width: 32px; border-left: 1px solid #2a3555; }
QComboBox::down-arrow { image: none; }
QComboBox QAbstractItemView { background-color: #1a2340; color: #e2e8f0; selection-background-color: #2a3555; selection-color: #e2e8f0; border: 1px solid #2a3555; border-radius: 8px; }
QCheckBox { color: #94a3b8; font-family: "Segoe UI"; spacing: 8px; font-size: 10pt; }
QCheckBox::indicator { width: 18px; height: 18px; border-radius: 4px; border: 1px solid #2a3555; background-color: #1a2340; }
QCheckBox::indicator:checked { background-color: #4f8ef7; border: 1px solid #4f8ef7; }
QRadioButton { color: #94a3b8; font-family: "Segoe UI"; spacing: 8px; font-size: 10pt; }
QRadioButton::indicator { width: 18px; height: 18px; border-radius: 9px; border: 1px solid #2a3555; background-color: #1a2340; }
QRadioButton::indicator:checked { background-color: #4f8ef7; border: 1px solid #4f8ef7; }
QTabWidget::pane { border: 1px solid #2a3555; background-color: #0b0f1a; border-radius: 10px; }
QTabBar::tab { background-color: #0d1220; color: #94a3b8; padding: 10px 20px; font-family: "Segoe UI"; font-size: 10pt; border: none; border-top-left-radius: 8px; border-top-right-radius: 8px; margin-right: 2px; }
QTabBar::tab:selected { background-color: #131a2e; color: #e2e8f0; border-bottom: 2px solid #4f8ef7; }
QTabBar::tab:hover { background-color: #1a2340; color: #e2e8f0; }
QScrollArea { border: none; }
QScrollBar:vertical { width: 6px; background: transparent; }
QScrollBar::handle:vertical { background: #2a3555; border-radius: 3px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #4f8ef7; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QProgressBar { background-color: #1a2340; border: none; border-radius: 4px; height: 8px; text-align: center; font-size: 8pt; }
QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f8ef7, stop:1 #a855f7); border-radius: 4px; }
QTreeWidget, QTreeView { background-color: #1a2340; color: #e2e8f0; border: 1px solid #2a3555; border-radius: 10px; font-family: "Segoe UI"; font-size: 10pt; }
QTreeWidget::item:hover { background-color: #243050; }
QTreeWidget::item:selected { background-color: #4f8ef7; }
QHeaderView::section { background-color: #0d1220; color: #94a3b8; padding: 8px; border: none; font-family: "Segoe UI"; font-weight: bold; }
QListWidget { background-color: #131a2e; color: #e2e8f0; border: 1px solid #2a3555; border-radius: 10px; font-family: "Segoe UI"; font-size: 10pt; padding: 4px; }
QListWidget::item { padding: 6px 10px; border-radius: 6px; }
QListWidget::item:hover { background-color: #1a2340; }
QListWidget::item:selected { background-color: #4f8ef7; }
QSplitter::handle { background-color: #2a3555; }
QStatusBar { background-color: #0d1220; color: #94a3b8; font-family: "Segoe UI"; font-size: 9pt; border-top: 1px solid #1e2745; }
QMenuBar { background-color: #0d1220; color: #e2e8f0; border-bottom: 1px solid #1e2745; }
QMenuBar::item:selected { background-color: #1a2340; }
QMenu { background-color: #131a2e; color: #e2e8f0; border: 1px solid #2a3555; border-radius: 10px; padding: 4px; }
QMenu::item { padding: 8px 24px; border-radius: 6px; }
QMenu::item:selected { background-color: #1a2340; }
QGroupBox { border: 1px solid #2a3555; border-radius: 10px; margin-top: 14px; padding-top: 14px; font-family: "Segoe UI"; color: #94a3b8; font-size: 10pt; }
QGroupBox::title { subcontrol-origin: margin; padding: 2px 10px; }
QFontComboBox { background-color: #1a2340; color: #e2e8f0; border: 1px solid #2a3555; border-radius: 8px; padding: 8px 12px; font-family: "Segoe UI"; font-size: 10pt; }
QFrame#sidebar_separator { margin: 8px 12px; }
QLabel#hint_label { font-family: 'Segoe UI'; font-size: 8pt; padding: 0 8px; }
QLabel#clock_label { font-family: 'Segoe UI'; font-size: 10pt; padding: 0 12px; color: #94a3b8; }
QLabel#status_text { font-family: 'Segoe UI'; font-size: 9pt; padding: 0 8px; color: #94a3b8; }
QLineEdit#calc_input { border-radius: 4px; padding: 0 6px; font-family: 'Consolas'; font-size: 9pt; min-width: 180px; min-height: 20px; }
QLabel#status_info { font-family: 'Segoe UI'; font-size: 9pt; padding: 0 8px; color: #7c8db0; }
QLabel#terminal_output { font-family: Courier New; font-size: 9pt; background-color: #0a0a0a; color: #22d3a5; }
QLabel#page_header_title { font-size: 22pt; font-weight: bold; font-family: 'Segoe UI'; letter-spacing: 0.5px; }
QLabel#page_header_subtitle { color: #7c8db0; font-size: 9pt; }
QFrame#page_header_separator { margin: 4px 0 8px 0; }
QLabel#card_title { color: #94a3b8; font-family: 'Segoe UI'; font-size: 10pt; font-weight: bold; letter-spacing: 0.5px; }
QFrame#card_separator { color: #2a3555; margin: 2px 0 6px 0; }
QLabel#labeled_row_label { color: #94a3b8; font-family: 'Segoe UI'; font-size: 10pt; min-width: 120px; }
QFrame#toast { background-color: rgba(13, 18, 32, 220); }
QLabel#toast_label { color: #e2e8f0; font-family: 'Segoe UI'; font-size: 10pt; background: transparent; }
QLabel#log_header { color: #94a3b8; font-family: 'Segoe UI'; font-size: 9pt; font-weight: bold; padding: 4px 0; letter-spacing: 1px; }
QPlainTextEdit#log_area { background-color: #0b0f1a; color: #94a3b8; border: 1px solid #2a3555; border-radius: 8px; font-family: Consolas; font-size: 9pt; padding: 8px; }
QLabel#stat_icon { font-size: 28pt; color: #4f8ef7; }
QPushButton#dash_action_btn { color: white; border: none; border-radius: 8px; padding: 12px; font-family: 'Segoe UI'; font-weight: bold; font-size: 10pt; background-color: #4f8ef7; }
QPushButton#dash_action_btn:hover { opacity: 0.85; }
QChart#dash_chart { background-color: #131a2e; title-color: #94a3b8; }
QLabel#sys_value { color: #e2e8f0; font-family: 'Segoe UI'; font-size: 10pt; font-weight: bold; }
QLabel#sysmon_warning { color: #eab308; font-size: 12pt; padding: 40px; }
QLabel#sysmon_big_value { font-size: 28pt; font-weight: bold; color: #4f8ef7; }
QLabel#sysmon_detail { color: #94a3b8; font-family: 'Segoe UI'; font-size: 9pt; }
QChart#sysmon_chart { background-color: #131a2e; plot-area-color: #0f1525; legend-label-color: #e2e8f0; }
QPlainTextEdit#api_response { font-family: Courier New; font-size: 9pt; }
QLabel#api_status { color: #eab308; }
QLabel#api_status[status_color="#22d3a5"] { color: #22d3a5; }
QLabel#api_status[status_color="#f74f4f"] { color: #f74f4f; }
QPlainTextEdit#fmt_editor { font-family: Consolas; font-size: 10pt; }
QLabel#fmt_status { color: #94a3b8; font-family: 'Segoe UI'; font-size: 9pt; padding: 2px 0; }
QLabel#fmt_status[status_color="#22d3a5"] { color: #22d3a5; }
QLabel#fmt_status[status_color="#f74f4f"] { color: #f74f4f; }
QLabel#fmt_status[status_color="#eab308"] { color: #eab308; }
QLabel#conn_status { color: #94a3b8; font-weight: bold; }
QLabel#conn_status[conn_state="connected"] { color: #22d3a5; }
QLabel#conn_status[conn_state="disconnected"] { color: #f74f4f; }
QLabel#regex_status { color: #94a3b8; }
QLabel#regex_status[status_color="ok"] { color: #22d3a5; }
QLabel#bulk_stat { font-family: Consolas; font-size: 10pt; color: #e8ecf4; }
QPlainTextEdit#code_output { font-family: Courier New; font-size: 9pt; }
QPlainTextEdit#code_editor { font-family: Courier New; font-size: 10pt; }
"""

LIGHT_STYLE = """
QMainWindow, QWidget { background-color: #f1f5f9; color: #1a2533; font-family: "Segoe UI"; }
QFrame#header { background-color: #ffffff; border: none; border-bottom: 1px solid #d0d9e6; }
QFrame#sidebar { background-color: #e8eef5; border: none; border-right: 1px solid #d0d9e6; }
QFrame#card { background-color: #ffffff; border: 1px solid #d0d9e6; border-radius: 10px; }
QFrame#card:hover { border: 1px solid #4f8ef7; }
QFrame#card_accent { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ffffff, stop:1 #f0f4ff); border: 1px solid #d0d9e6; border-radius: 10px; }
QPushButton { background-color: #ffffff; color: #1a2533; border: 1px solid #d0d9e6; border-radius: 8px; padding: 8px 16px; font-family: "Segoe UI"; font-size: 10pt; }
QPushButton:hover { background-color: #e8eef5; border: 1px solid #4f8ef7; }
QPushButton:pressed { background-color: #dce4ef; }
QPushButton#accent { background-color: #4f8ef7; color: white; border: none; font-weight: bold; padding: 8px 16px; min-height: 20px; min-width: 60px; }
QPushButton#accent:hover { background-color: #3b7de6; }
QPushButton#accent2 { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f8ef7, stop:1 #a855f7); color: white; border: none; font-weight: bold; padding: 8px 16px; min-height: 20px; min-width: 60px; }
QPushButton#accent2:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3b7de6, stop:1 #9333ea); }
QPushButton#success { background-color: #22d3a5; color: white; border: none; font-weight: bold; padding: 8px 16px; min-height: 20px; min-width: 60px; }
QPushButton#success:hover { background-color: #1bbd92; }
QPushButton#danger { background-color: #f74f4f; color: white; border: none; font-weight: bold; padding: 8px 16px; min-height: 20px; min-width: 60px; }
QPushButton#danger:hover { background-color: #e04040; }
QPushButton#sidebar_btn { background-color: transparent; color: #4f6080; border: none; text-align: left; padding: 10px 16px; border-radius: 0; font-family: "Segoe UI"; font-size: 10pt; border-left: 3px solid transparent; }
QPushButton#sidebar_btn:hover { background-color: #dce4ef; color: #1a2533; }
QPushButton#sidebar_btn:checked { background-color: #dce4ef; color: #1a2533; border-left: 3px solid #4f8ef7; }
QPushButton#icon_btn { background-color: transparent; color: #5a6a8a; border: 1px solid #d0d9e6; border-radius: 8px; padding: 6px; font-size: 14pt; min-width: 36px; min-height: 36px; }
QLabel#sidebar_section { color: #5a6a8a; font-family: "Segoe UI"; font-size: 8pt; font-weight: bold; padding: 10px 16px 6px; letter-spacing: 1px; }
QPushButton#icon_btn:hover { background-color: #e8eef5; color: #1a2533; }
QLabel { color: #1a2533; font-family: "Segoe UI"; }
QLabel#header_title { font-size: 18pt; font-weight: bold; color: #0b0f1a; letter-spacing: 1px; }
QLabel#text_muted { color: #6b7d9a; font-size: 9pt; }
QLabel#text_secondary { color: #4f6080; }
QLabel#stat_value { font-size: 26pt; font-weight: bold; color: #1a2533; }
QLabel#stat_label { color: #4f6080; font-size: 9pt; }
QLabel#stat_today { color: #6b7d9a; font-size: 8pt; }
QLineEdit { background-color: #ffffff; color: #1a2533; border: 1px solid #d0d9e6; border-radius: 8px; padding: 8px 12px; font-family: "Segoe UI"; font-size: 10pt; }
QLineEdit:focus { border: 1px solid #4f8ef7; }
QLineEdit[inputState="false"] { border: 1px solid #f74f4f; }
QTextEdit, QPlainTextEdit { background-color: #fafcfe; color: #1a2533; border: 1px solid #d0d9e6; border-radius: 8px; font-family: "Consolas"; font-size: 10pt; padding: 8px; }
QComboBox { background-color: #ffffff; color: #1a2533; border: 1px solid #d0d9e6; border-radius: 8px; padding: 8px 12px; font-family: "Segoe UI"; font-size: 10pt; }
QComboBox:hover { border: 1px solid #4f8ef7; }
QComboBox::drop-down { border: none; width: 32px; border-left: 1px solid #d0d9e6; }
QComboBox::down-arrow { image: none; }
QComboBox QAbstractItemView { background-color: #ffffff; color: #1a2533; selection-background-color: #cbd5e1; selection-color: #1a2533; border: 1px solid #d0d9e6; border-radius: 8px; }
QCheckBox { color: #4f6080; font-family: "Segoe UI"; spacing: 8px; font-size: 10pt; }
QCheckBox::indicator { width: 18px; height: 18px; border-radius: 4px; border: 1px solid #d0d9e6; background-color: #ffffff; }
QCheckBox::indicator:checked { background-color: #4f8ef7; border: 1px solid #4f8ef7; }
QRadioButton { color: #4f6080; font-family: "Segoe UI"; spacing: 8px; font-size: 10pt; }
QRadioButton::indicator { width: 18px; height: 18px; border-radius: 9px; border: 1px solid #d0d9e6; background-color: #ffffff; }
QRadioButton::indicator:checked { background-color: #4f8ef7; border: 1px solid #4f8ef7; }
QTabWidget::pane { border: 1px solid #d0d9e6; background-color: #ffffff; border-radius: 10px; }
QTabBar::tab { background-color: #e8eef5; color: #4f6080; padding: 10px 20px; font-family: "Segoe UI"; font-size: 10pt; border: none; border-top-left-radius: 8px; border-top-right-radius: 8px; margin-right: 2px; }
QTabBar::tab:selected { background-color: #ffffff; color: #1a2533; border-bottom: 2px solid #4f8ef7; }
QTabBar::tab:hover { background-color: #dce4ef; color: #1a2533; }
QScrollArea { border: none; }
QScrollBar:vertical { width: 6px; background: transparent; }
QScrollBar::handle:vertical { background: #c8d2e0; border-radius: 3px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #4f8ef7; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QProgressBar { background-color: #dce4ef; border: none; border-radius: 4px; height: 8px; text-align: center; font-size: 8pt; }
QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f8ef7, stop:1 #a855f7); border-radius: 4px; }
QTreeWidget, QTreeView { background-color: #ffffff; color: #1a2533; border: 1px solid #d0d9e6; border-radius: 10px; font-family: "Segoe UI"; font-size: 10pt; }
QTreeWidget::item:hover { background-color: #e8eef5; }
QTreeWidget::item:selected { background-color: #4f8ef7; color: white; }
QHeaderView::section { background-color: #e8eef5; color: #4f6080; padding: 8px; border: none; font-family: "Segoe UI"; font-weight: bold; }
QListWidget { background-color: #ffffff; color: #1a2533; border: 1px solid #d0d9e6; border-radius: 10px; font-family: "Segoe UI"; font-size: 10pt; padding: 4px; }
QListWidget::item { padding: 6px 10px; border-radius: 6px; }
QListWidget::item:hover { background-color: #e8eef5; }
QListWidget::item:selected { background-color: #4f8ef7; color: white; }
QSplitter::handle { background-color: #d0d9e6; }
QStatusBar { background-color: #ffffff; color: #4f6080; font-family: "Segoe UI"; font-size: 9pt; border-top: 1px solid #d0d9e6; }
QMenuBar { background-color: #ffffff; color: #1a2533; border-bottom: 1px solid #d0d9e6; }
QMenuBar::item:selected { background-color: #e8eef5; }
QMenu { background-color: #ffffff; color: #1a2533; border: 1px solid #d0d9e6; border-radius: 10px; padding: 4px; }
QMenu::item { padding: 8px 24px; border-radius: 6px; }
QMenu::item:selected { background-color: #e8eef5; }
QGroupBox { border: 1px solid #d0d9e6; border-radius: 10px; margin-top: 14px; padding-top: 14px; font-family: "Segoe UI"; color: #4f6080; font-size: 10pt; }
QGroupBox::title { subcontrol-origin: margin; padding: 2px 10px; }
QFontComboBox { background-color: #ffffff; color: #1a2533; border: 1px solid #d0d9e6; border-radius: 8px; padding: 8px 12px; font-family: "Segoe UI"; font-size: 10pt; }
QFrame#sidebar_separator { margin: 8px 12px; }
QLabel#hint_label { font-family: 'Segoe UI'; font-size: 8pt; padding: 0 8px; }
QLabel#clock_label { font-family: 'Segoe UI'; font-size: 10pt; padding: 0 12px; color: #4f6080; }
QLabel#status_text { font-family: 'Segoe UI'; font-size: 9pt; padding: 0 8px; color: #4f6080; }
QLineEdit#calc_input { border-radius: 4px; padding: 0 6px; font-family: 'Consolas'; font-size: 9pt; min-width: 180px; min-height: 20px; }
QLabel#status_info { font-family: 'Segoe UI'; font-size: 9pt; padding: 0 8px; color: #6b7d9a; }
QLabel#terminal_output { font-family: Courier New; font-size: 9pt; background-color: #fafcfe; color: #1a7a5a; }
QLabel#page_header_title { font-size: 22pt; font-weight: bold; font-family: 'Segoe UI'; letter-spacing: 0.5px; }
QLabel#page_header_subtitle { color: #6b7d9a; font-size: 9pt; }
QFrame#page_header_separator { margin: 4px 0 8px 0; }
QLabel#card_title { color: #4f6080; font-family: 'Segoe UI'; font-size: 10pt; font-weight: bold; letter-spacing: 0.5px; }
QFrame#card_separator { color: #d0d9e6; margin: 2px 0 6px 0; }
QLabel#labeled_row_label { color: #4f6080; font-family: 'Segoe UI'; font-size: 10pt; min-width: 120px; }
QFrame#toast { background-color: rgba(255, 255, 255, 220); }
QLabel#toast_label { color: #1a2533; font-family: 'Segoe UI'; font-size: 10pt; background: transparent; }
QLabel#log_header { color: #4f6080; font-family: 'Segoe UI'; font-size: 9pt; font-weight: bold; padding: 4px 0; letter-spacing: 1px; }
QPlainTextEdit#log_area { background-color: #fafcfe; color: #4f6080; border: 1px solid #d0d9e6; border-radius: 8px; font-family: Consolas; font-size: 9pt; padding: 8px; }
QLabel#stat_icon { font-size: 28pt; color: #4f8ef7; }
QPushButton#dash_action_btn { color: white; border: none; border-radius: 8px; padding: 12px; font-family: 'Segoe UI'; font-weight: bold; font-size: 10pt; background-color: #4f8ef7; }
QPushButton#dash_action_btn:hover { opacity: 0.85; }
QChart#dash_chart { background-color: #ffffff; title-color: #4f6080; }
QLabel#sys_value { color: #1a2533; font-family: 'Segoe UI'; font-size: 10pt; font-weight: bold; }
QLabel#sysmon_warning { color: #d97706; font-size: 12pt; padding: 40px; }
QLabel#sysmon_big_value { font-size: 28pt; font-weight: bold; color: #4f8ef7; }
QLabel#sysmon_detail { color: #4f6080; font-family: 'Segoe UI'; font-size: 9pt; }
QChart#sysmon_chart { background-color: #ffffff; plot-area-color: #f8fafc; legend-label-color: #1a2533; }
QPlainTextEdit#api_response { font-family: Courier New; font-size: 9pt; }
QLabel#api_status { color: #d97706; }
QLabel#api_status[status_color="#22d3a5"] { color: #16a34a; }
QLabel#api_status[status_color="#f74f4f"] { color: #dc2626; }
QPlainTextEdit#fmt_editor { font-family: Consolas; font-size: 10pt; }
QLabel#fmt_status { color: #4f6080; font-family: 'Segoe UI'; font-size: 9pt; padding: 2px 0; }
QLabel#fmt_status[status_color="#22d3a5"] { color: #16a34a; }
QLabel#fmt_status[status_color="#f74f4f"] { color: #dc2626; }
QLabel#fmt_status[status_color="#eab308"] { color: #d97706; }
QLabel#conn_status { color: #4f6080; font-weight: bold; }
QLabel#conn_status[conn_state="connected"] { color: #16a34a; }
QLabel#conn_status[conn_state="disconnected"] { color: #dc2626; }
QLabel#regex_status { color: #4f6080; }
QLabel#regex_status[status_color="ok"] { color: #16a34a; }
QLabel#bulk_stat { font-family: Consolas; font-size: 10pt; color: #1a2533; }
QPlainTextEdit#code_output { font-family: Courier New; font-size: 9pt; }
QPlainTextEdit#code_editor { font-family: Courier New; font-size: 10pt; }
"""
