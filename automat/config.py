import os
from pathlib import Path

APP_NAME = "AUTOMAT"
APP_TITLE = "AUTOMAT — Task Automation Manager"
ORG_NAME = "Auxo"


def _app_version() -> str:
    """Single source of truth for the version: installed dist metadata,
    with a fallback for plain source checkouts."""
    try:
        from importlib.metadata import PackageNotFoundError, version
        return version("automat")
    except Exception:
        return "2.0b1"


APP_VERSION = _app_version()

DATA_DIR = Path(os.getenv("APPDATA", Path.home())) / "Automat"
DATA_DIR.mkdir(parents=True, exist_ok=True)
SETTINGS_FILE = str(DATA_DIR / "settings.json")
TASKS_FILE = str(DATA_DIR / "tasks.json")

UI_FONT = "Segoe UI"

PROXY_DEFAULTS = {"host": "", "port": "", "user": "", "pass": ""}


def load_proxy(settings_data):
    p = settings_data.get("proxy", {}) if isinstance(settings_data, dict) else {}
    if p and p.get("host") and p.get("port"):
        if p.get('user'):
            proxy_url = f"http://{p['user']}:{p.get('pass', '')}@{p['host']}:{p['port']}"
        else:
            proxy_url = f"http://{p['host']}:{p['port']}"
        return {"http": proxy_url, "https": proxy_url}
    return None


ACCENT = "#2e7bd6"
ACCENT2 = "#5b7fa6"
GREEN = "#2f9e68"
YELLOW = "#b7791f"
RED = "#cf4444"

DARK_STYLE = """
QMainWindow, QWidget { background-color: #232529; color: #e8eaed; font-family: "Segoe UI"; font-size: 9pt; }
QFrame#header { background-color: #26282d; border: none; border-bottom: 1px solid #3a3d43; }
QFrame#sidebar { background-color: #26282d; border: none; border-right: 1px solid #3a3d43; }
QFrame#card { background-color: #2c2f34; border: 1px solid #3a3d43; border-radius: 4px; }
QFrame#card_accent { background-color: #2c2f34; border: 1px solid #3a3d43; border-radius: 4px; }
QPushButton { background-color: #35383e; color: #e8eaed; border: 1px solid #454a52; border-radius: 3px; padding: 5px 12px; font-family: "Segoe UI"; font-size: 9pt; }
QPushButton:hover { background-color: #3d4148; border: 1px solid #555b64; }
QPushButton:pressed { background-color: #2a2d32; border: 1px solid #454a52; }
QPushButton:disabled { background-color: #2c2f34; color: #6b7078; border: 1px solid #3a3d43; }
QPushButton:focus { border: 1px solid #2e7bd6; }
QPushButton#accent { background-color: #2e7bd6; color: white; border: 1px solid #2e7bd6; padding: 5px 12px; min-height: 18px; min-width: 60px; }
QPushButton#accent:hover { background-color: #2a6fc2; border: 1px solid #2a6fc2; }
QPushButton#accent2 { background-color: #3d4b5c; color: white; border: 1px solid #4a586c; padding: 5px 12px; min-height: 18px; min-width: 60px; }
QPushButton#accent2:hover { background-color: #46566a; }
QPushButton#success { background-color: #2f9e68; color: white; border: 1px solid #2f9e68; padding: 5px 12px; min-height: 18px; min-width: 60px; }
QPushButton#success:hover { background-color: #2a8f5e; }
QPushButton#danger { background-color: #cf4444; color: white; border: 1px solid #cf4444; padding: 5px 12px; min-height: 18px; min-width: 60px; }
QPushButton#danger:hover { background-color: #bd3d3d; }
QPushButton#sidebar_btn { background-color: transparent; color: #b5bac2; border: none; text-align: left; padding: 7px 12px; border-radius: 0; font-family: "Segoe UI"; font-size: 9pt; border-left: 2px solid transparent; }
QPushButton#sidebar_btn:hover { background-color: #2c2f34; color: #ffffff; }
QPushButton#sidebar_btn:checked { background-color: #32353a; color: #ffffff; border-left: 2px solid #2e7bd6; }
QPushButton#icon_btn { background-color: transparent; color: #b5bac2; border: 1px solid #454a52; border-radius: 3px; padding: 4px; font-size: 11pt; min-width: 30px; min-height: 30px; }
QLabel#sidebar_section { color: #7d838d; font-family: "Segoe UI"; font-size: 8pt; font-weight: normal; letter-spacing: 0.5px; padding: 8px 12px 4px; }
QPushButton#icon_btn:hover { background-color: #35383e; color: #ffffff; }
QLabel { color: #e8eaed; font-family: "Segoe UI"; }
QLabel#header_title { font-size: 12pt; font-weight: normal; color: #ffffff; letter-spacing: 1px; }
QLabel#text_muted { color: #9aa0a8; font-size: 9pt; }
QLabel#text_secondary { color: #b5bac2; }
QLabel#stat_value { font-size: 18pt; font-weight: normal; color: #ffffff; font-family: 'Segoe UI'; }
QLabel#stat_label { color: #b5bac2; font-size: 9pt; }
QLabel#stat_today { color: #7d838d; font-size: 8pt; }
QLineEdit { background-color: #1f2125; color: #e8eaed; border: 1px solid #454a52; border-radius: 3px; padding: 6px 10px; font-family: "Segoe UI"; font-size: 9pt; selection-background-color: #2e7bd6; }
QLineEdit:focus { border: 1px solid #2e7bd6; }
QLineEdit[inputState="false"] { border: 1px solid #cf4444; }
QTextEdit, QPlainTextEdit { background-color: #1f2125; color: #e8eaed; border: 1px solid #454a52; border-radius: 3px; font-family: "Consolas"; font-size: 10pt; padding: 6px; selection-background-color: #2e7bd6; }
QComboBox { background-color: #35383e; color: #e8eaed; border: 1px solid #454a52; border-radius: 3px; padding: 6px 10px; font-family: "Segoe UI"; font-size: 9pt; }
QComboBox:hover { border: 1px solid #555b64; }
QComboBox:focus { border: 1px solid #2e7bd6; }
QComboBox::drop-down { border: none; width: 28px; }
QComboBox::down-arrow { image: none; }
QComboBox QAbstractItemView { background-color: #2c2f34; color: #e8eaed; selection-background-color: #2e7bd6; selection-color: white; border: 1px solid #454a52; border-radius: 3px; }
QCheckBox { color: #b5bac2; font-family: "Segoe UI"; spacing: 8px; font-size: 9pt; }
QCheckBox::indicator { width: 15px; height: 15px; border-radius: 2px; border: 1px solid #555b64; background-color: #1f2125; }
QCheckBox::indicator:checked { background-color: #2e7bd6; border: 1px solid #2e7bd6; }
QRadioButton { color: #b5bac2; font-family: "Segoe UI"; spacing: 8px; font-size: 9pt; }
QRadioButton::indicator { width: 15px; height: 15px; border-radius: 8px; border: 1px solid #555b64; background-color: #1f2125; }
QRadioButton::indicator:checked { background-color: #2e7bd6; border: 1px solid #2e7bd6; }
QTabWidget::pane { border: 1px solid #3a3d43; background-color: #232529; border-radius: 3px; }
QTabBar::tab { background-color: #26282d; color: #9aa0a8; padding: 7px 14px; font-family: "Segoe UI"; font-size: 9pt; border: none; border-bottom: 2px solid transparent; margin-right: 1px; }
QTabBar::tab:selected { background-color: #2c2f34; color: #ffffff; border-bottom: 2px solid #2e7bd6; }
QTabBar::tab:hover { background-color: #35383e; color: #e8eaed; }
QScrollArea { border: none; }
QScrollBar:vertical { width: 10px; background: transparent; }
QScrollBar::handle:vertical { background: #5a6069; border-radius: 4px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #555b64; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QProgressBar { background-color: #35383e; border: none; border-radius: 2px; height: 6px; text-align: center; font-size: 8pt; }
QProgressBar::chunk { background-color: #2e7bd6; border-radius: 2px; }
QTreeWidget, QTreeView { background-color: #2c2f34; color: #e8eaed; border: 1px solid #3a3d43; border-radius: 3px; font-family: "Segoe UI"; font-size: 9pt; }
QTreeWidget::item:hover { background-color: #35383e; }
QTreeWidget::item:selected { background-color: #2e7bd6; color: white; }
QHeaderView::section { background-color: #26282d; color: #9aa0a8; padding: 7px 6px; border: none; border-bottom: 1px solid #3a3d43; border-right: 1px solid #3a3d43; font-family: "Segoe UI"; font-size: 9pt; font-weight: normal; }
QListWidget { background-color: #2c2f34; color: #e8eaed; border: 1px solid #3a3d43; border-radius: 3px; font-family: "Segoe UI"; font-size: 9pt; padding: 4px; }
QListWidget::item { padding: 5px 8px; border-radius: 2px; }
QListWidget::item:hover { background-color: #35383e; }
QListWidget::item:selected { background-color: #2e7bd6; color: white; }
QSplitter::handle { background-color: #3a3d43; }
QStatusBar { background-color: #26282d; color: #9aa0a8; font-family: "Segoe UI"; font-size: 9pt; border-top: 1px solid #3a3d43; }
QMenuBar { background-color: #26282d; color: #e8eaed; border-bottom: 1px solid #3a3d43; }
QMenuBar::item { padding: 4px 10px; background: transparent; }
QMenuBar::item:selected { background-color: #35383e; }
QMenu { background-color: #2c2f34; color: #e8eaed; border: 1px solid #454a52; border-radius: 3px; padding: 4px; }
QMenu::item { padding: 6px 20px; border-radius: 3px; }
QMenu::item:selected { background-color: #35383e; }
QGroupBox { border: 1px solid #3a3d43; border-radius: 3px; margin-top: 12px; padding-top: 12px; font-family: "Segoe UI"; color: #b5bac2; font-size: 9pt; }
QGroupBox::title { subcontrol-origin: margin; padding: 2px 8px; }
QFontComboBox { background-color: #35383e; color: #e8eaed; border: 1px solid #454a52; border-radius: 3px; padding: 6px 10px; font-family: "Segoe UI"; font-size: 9pt; }
QFrame#sidebar_separator { margin: 6px 12px; }
QLabel#hint_label { font-family: 'Segoe UI'; font-size: 8pt; padding: 0 8px; color: #7d838d; }
QLabel#clock_label { font-family: 'Segoe UI'; font-size: 9pt; padding: 0 12px; color: #9aa0a8; }
QLabel#status_text { font-family: 'Segoe UI'; font-size: 9pt; padding: 0 8px; color: #9aa0a8; }
QLineEdit#calc_input { border-radius: 3px; padding: 2px 6px; font-family: 'Consolas'; font-size: 9pt; min-width: 180px; min-height: 20px; }
QLabel#status_info { font-family: 'Segoe UI'; font-size: 9pt; padding: 0 8px; color: #7d838d; }
QLabel#terminal_output { font-family: Courier New; font-size: 9pt; background-color: #1a1c1f; color: #7fd6a2; }
QLabel#page_header_title { font-size: 13pt; font-weight: normal; font-family: 'Segoe UI'; color: #ffffff; }
QLabel#page_header_subtitle { color: #7d838d; font-size: 9pt; }
QFrame#page_header_separator { margin: 4px 0 8px 0; }
QLabel#card_title { color: #b5bac2; font-family: 'Segoe UI'; font-size: 9pt; font-weight: normal; text-transform: uppercase; letter-spacing: 0.5px; }
QFrame#card_separator { color: #3a3d43; margin: 2px 0 6px 0; }
QLabel#labeled_row_label { color: #b5bac2; font-family: 'Segoe UI'; font-size: 9pt; min-width: 120px; }
QFrame#toast { background-color: rgba(44, 47, 52, 230); border: 1px solid #454a52; border-radius: 3px; }
QLabel#toast_label { color: #e8eaed; font-family: 'Segoe UI'; font-size: 9pt; background: transparent; }
QLabel#log_header { color: #9aa0a8; font-family: 'Segoe UI'; font-size: 9pt; font-weight: normal; letter-spacing: 0.5px; padding: 4px 0; }
QPlainTextEdit#log_area { background-color: #1f2125; color: #b5bac2; border: 1px solid #3a3d43; border-radius: 3px; font-family: Consolas; font-size: 9pt; padding: 6px; }
QLabel#stat_icon { font-size: 22pt; color: #7d838d; }
QPushButton#dash_action_btn { color: white; border: 1px solid #2e7bd6; border-radius: 3px; padding: 9px 10px; font-family: 'Segoe UI'; font-size: 9pt; background-color: #2e7bd6; }
QPushButton#dash_action_btn:hover { background-color: #2a6fc2; }
QChart#dash_chart { background-color: #2c2f34; }
QLabel#sys_value { color: #e8eaed; font-family: 'Segoe UI'; font-size: 9pt; font-weight: normal; }
QLabel#sysmon_warning { color: #b7791f; font-size: 11pt; padding: 40px; }
QLabel#sysmon_big_value { font-size: 18pt; font-weight: normal; color: #e8eaed; }
QLabel#sysmon_detail { color: #9aa0a8; font-family: 'Segoe UI'; font-size: 9pt; }
QChart#sysmon_chart { background-color: #2c2f34; }
QPlainTextEdit#api_response { font-family: Courier New; font-size: 9pt; }
QLabel#api_status { color: #b7791f; }
QLabel#api_status[status_color="#2f9e68"] { color: #2f9e68; }
QLabel#api_status[status_color="#cf4444"] { color: #cf4444; }
QLabel#api_status[status_color="#22d3a5"] { color: #2f9e68; }
QLabel#api_status[status_color="#f74f4f"] { color: #cf4444; }
QLabel#api_status[status_color="#b7791f"] { color: #b7791f; }
QPlainTextEdit#fmt_editor { font-family: Consolas; font-size: 10pt; }
QLabel#fmt_status { color: #9aa0a8; font-family: 'Segoe UI'; font-size: 9pt; padding: 2px 0; }
QLabel#fmt_status[status_color="#2f9e68"] { color: #2f9e68; }
QLabel#fmt_status[status_color="#cf4444"] { color: #cf4444; }
QLabel#fmt_status[status_color="#b7791f"] { color: #b7791f; }
QLabel#fmt_status[status_color="#22d3a5"] { color: #2f9e68; }
QLabel#fmt_status[status_color="#f74f4f"] { color: #cf4444; }
QLabel#fmt_status[status_color="#eab308"] { color: #b7791f; }
QLabel#conn_status { color: #9aa0a8; font-weight: normal; }
QLabel#conn_status[conn_state="connected"] { color: #2f9e68; }
QLabel#conn_status[conn_state="disconnected"] { color: #cf4444; }
QLabel#regex_status { color: #9aa0a8; }
QLabel#regex_status[status_color="ok"] { color: #2f9e68; }
QLabel#bulk_stat { font-family: Consolas; font-size: 10pt; color: #e8eaed; }
QPlainTextEdit#code_output { font-family: Courier New; font-size: 9pt; }
QPlainTextEdit#code_editor { font-family: Courier New; font-size: 10pt; }
QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit, QDateTimeEdit { background-color: #1f2125; color: #e8eaed; border: 1px solid #454a52; border-radius: 3px; padding: 6px 10px; font-family: "Segoe UI"; font-size: 9pt; selection-background-color: #2e7bd6; }
QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus, QTimeEdit:focus, QDateTimeEdit:focus { border: 1px solid #2e7bd6; }
QSpinBox::up-button, QSpinBox::down-button, QDoubleSpinBox::up-button, QDoubleSpinBox::down-button { width: 20px; border: none; background: transparent; }
QTableWidget, QTableView { background-color: #2c2f34; color: #e8eaed; border: 1px solid #3a3d43; border-radius: 3px; gridline-color: #3a3d43; selection-background-color: #2e7bd6; selection-color: white; font-family: "Segoe UI"; font-size: 9pt; alternate-background-color: #27292e; }
QTableWidget::item:selected, QTableView::item:selected { background-color: #2e7bd6; color: white; }
QTableCornerButton::section { background-color: #26282d; border: none; }
QScrollBar:horizontal { height: 10px; background: transparent; }
QScrollBar::handle:horizontal { background: #5a6069; border-radius: 4px; min-width: 30px; }
QScrollBar::handle:horizontal:hover { background: #555b64; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QToolTip { background-color: #35383e; color: #e8eaed; border: 1px solid #555b64; border-radius: 3px; padding: 4px 8px; font-family: "Segoe UI"; font-size: 9pt; }
QLabel#calc_sep { color: #7d838d; font-weight: bold; padding: 0 2px; }
QDialog { background-color: #232529; border-radius: 4px; }
"""

LIGHT_STYLE = """
QMainWindow, QWidget { background-color: #f2f3f5; color: #1f2937; font-family: "Segoe UI"; font-size: 9pt; }
QFrame#header { background-color: #ffffff; border: none; border-bottom: 1px solid #dde0e5; }
QFrame#sidebar { background-color: #e9ebee; border: none; border-right: 1px solid #dde0e5; }
QFrame#card { background-color: #ffffff; border: 1px solid #dde0e5; border-radius: 4px; }
QFrame#card_accent { background-color: #ffffff; border: 1px solid #dde0e5; border-radius: 4px; }
QPushButton { background-color: #ffffff; color: #1f2937; border: 1px solid #d0d4da; border-radius: 3px; padding: 5px 12px; font-family: "Segoe UI"; font-size: 9pt; }
QPushButton:hover { background-color: #eef0f3; border: 1px solid #b9bfc8; }
QPushButton:pressed { background-color: #dfe3e9; border: 1px solid #b9bfc8; }
QPushButton:disabled { background-color: #f2f3f5; color: #9aa0a8; border: 1px solid #dde0e5; }
QPushButton:focus { border: 1px solid #1f6fd6; }
QPushButton#accent { background-color: #1f6fd6; color: white; border: 1px solid #1f6fd6; padding: 5px 12px; min-height: 18px; min-width: 60px; }
QPushButton#accent:hover { background-color: #1b63c0; border: 1px solid #1b63c0; }
QPushButton#accent2 { background-color: #5b6b7c; color: white; border: 1px solid #5b6b7c; padding: 5px 12px; min-height: 18px; min-width: 60px; }
QPushButton#accent2:hover { background-color: #4f5e6e; }
QPushButton#success { background-color: #1e9e6a; color: white; border: 1px solid #1e9e6a; padding: 5px 12px; min-height: 18px; min-width: 60px; }
QPushButton#success:hover { background-color: #1b8d5f; }
QPushButton#danger { background-color: #cf4444; color: white; border: 1px solid #cf4444; padding: 5px 12px; min-height: 18px; min-width: 60px; }
QPushButton#danger:hover { background-color: #bd3d3d; }
QPushButton#sidebar_btn { background-color: transparent; color: #5b6470; border: none; text-align: left; padding: 7px 12px; border-radius: 0; font-family: "Segoe UI"; font-size: 9pt; border-left: 2px solid transparent; }
QPushButton#sidebar_btn:hover { background-color: #dde0e5; color: #111827; }
QPushButton#sidebar_btn:checked { background-color: #dde0e5; color: #111827; border-left: 2px solid #1f6fd6; }
QPushButton#icon_btn { background-color: transparent; color: #5b6470; border: 1px solid #d0d4da; border-radius: 3px; padding: 4px; font-size: 11pt; min-width: 30px; min-height: 30px; }
QLabel#sidebar_section { color: #7d838d; font-family: "Segoe UI"; font-size: 8pt; font-weight: normal; letter-spacing: 0.5px; padding: 8px 12px 4px; }
QPushButton#icon_btn:hover { background-color: #eef0f3; color: #111827; }
QLabel { color: #1f2937; font-family: "Segoe UI"; }
QLabel#header_title { font-size: 12pt; font-weight: normal; color: #111827; letter-spacing: 1px; }
QLabel#text_muted { color: #6b7280; font-size: 9pt; }
QLabel#text_secondary { color: #4b5563; }
QLabel#stat_value { font-size: 18pt; font-weight: normal; color: #111827; font-family: 'Segoe UI'; }
QLabel#stat_label { color: #4b5563; font-size: 9pt; }
QLabel#stat_today { color: #6b7280; font-size: 8pt; }
QLineEdit { background-color: #ffffff; color: #1f2937; border: 1px solid #d0d4da; border-radius: 3px; padding: 6px 10px; font-family: "Segoe UI"; font-size: 9pt; selection-background-color: #1f6fd6; }
QLineEdit:focus { border: 1px solid #1f6fd6; }
QLineEdit[inputState="false"] { border: 1px solid #cf4444; }
QTextEdit, QPlainTextEdit { background-color: #fbfcfd; color: #1f2937; border: 1px solid #d0d4da; border-radius: 3px; font-family: "Consolas"; font-size: 10pt; padding: 6px; selection-background-color: #1f6fd6; selection-color: white; }
QComboBox { background-color: #ffffff; color: #1f2937; border: 1px solid #d0d4da; border-radius: 3px; padding: 6px 10px; font-family: "Segoe UI"; font-size: 9pt; }
QComboBox:hover { border: 1px solid #b9bfc8; }
QComboBox:focus { border: 1px solid #1f6fd6; }
QComboBox::drop-down { border: none; width: 28px; }
QComboBox::down-arrow { image: none; }
QComboBox QAbstractItemView { background-color: #ffffff; color: #1f2937; selection-background-color: #1f6fd6; selection-color: white; border: 1px solid #d0d4da; border-radius: 3px; }
QCheckBox { color: #4b5563; font-family: "Segoe UI"; spacing: 8px; font-size: 9pt; }
QCheckBox::indicator { width: 15px; height: 15px; border-radius: 2px; border: 1px solid #b9bfc8; background-color: #ffffff; }
QCheckBox::indicator:checked { background-color: #1f6fd6; border: 1px solid #1f6fd6; }
QRadioButton { color: #4b5563; font-family: "Segoe UI"; spacing: 8px; font-size: 9pt; }
QRadioButton::indicator { width: 15px; height: 15px; border-radius: 8px; border: 1px solid #b9bfc8; background-color: #ffffff; }
QRadioButton::indicator:checked { background-color: #1f6fd6; border: 1px solid #1f6fd6; }
QTabWidget::pane { border: 1px solid #dde0e5; background-color: #ffffff; border-radius: 3px; }
QTabBar::tab { background-color: #e9ebee; color: #5b6470; padding: 7px 14px; font-family: "Segoe UI"; font-size: 9pt; border: none; border-bottom: 2px solid transparent; margin-right: 1px; }
QTabBar::tab:selected { background-color: #ffffff; color: #111827; border-bottom: 2px solid #1f6fd6; }
QTabBar::tab:hover { background-color: #dde0e5; color: #111827; }
QScrollArea { border: none; }
QScrollBar:vertical { width: 10px; background: transparent; }
QScrollBar::handle:vertical { background: #a8aeb8; border-radius: 4px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #9aa0a8; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QProgressBar { background-color: #e2e5ea; border: none; border-radius: 2px; height: 6px; text-align: center; font-size: 8pt; }
QProgressBar::chunk { background-color: #1f6fd6; border-radius: 2px; }
QTreeWidget, QTreeView { background-color: #ffffff; color: #1f2937; border: 1px solid #dde0e5; border-radius: 3px; font-family: "Segoe UI"; font-size: 9pt; }
QTreeWidget::item:hover { background-color: #eef0f3; }
QTreeWidget::item:selected { background-color: #1f6fd6; color: white; }
QHeaderView::section { background-color: #e9ebee; color: #5b6470; padding: 7px 6px; border: none; border-bottom: 1px solid #dde0e5; border-right: 1px solid #dde0e5; font-family: "Segoe UI"; font-size: 9pt; font-weight: normal; }
QListWidget { background-color: #ffffff; color: #1f2937; border: 1px solid #dde0e5; border-radius: 3px; font-family: "Segoe UI"; font-size: 9pt; padding: 4px; }
QListWidget::item { padding: 5px 8px; border-radius: 2px; }
QListWidget::item:hover { background-color: #eef0f3; }
QListWidget::item:selected { background-color: #1f6fd6; color: white; }
QSplitter::handle { background-color: #dde0e5; }
QStatusBar { background-color: #ffffff; color: #5b6470; font-family: "Segoe UI"; font-size: 9pt; border-top: 1px solid #dde0e5; }
QMenuBar { background-color: #ffffff; color: #1f2937; border-bottom: 1px solid #dde0e5; }
QMenuBar::item { padding: 4px 10px; background: transparent; }
QMenuBar::item:selected { background-color: #eef0f3; }
QMenu { background-color: #ffffff; color: #1f2937; border: 1px solid #d0d4da; border-radius: 3px; padding: 4px; }
QMenu::item { padding: 6px 20px; border-radius: 3px; }
QMenu::item:selected { background-color: #eef0f3; }
QGroupBox { border: 1px solid #dde0e5; border-radius: 3px; margin-top: 12px; padding-top: 12px; font-family: "Segoe UI"; color: #4b5563; font-size: 9pt; }
QGroupBox::title { subcontrol-origin: margin; padding: 2px 8px; }
QFontComboBox { background-color: #ffffff; color: #1f2937; border: 1px solid #d0d4da; border-radius: 3px; padding: 6px 10px; font-family: "Segoe UI"; font-size: 9pt; }
QFrame#sidebar_separator { margin: 6px 12px; }
QLabel#hint_label { font-family: 'Segoe UI'; font-size: 8pt; padding: 0 8px; color: #7d838d; }
QLabel#clock_label { font-family: 'Segoe UI'; font-size: 9pt; padding: 0 12px; color: #5b6470; }
QLabel#status_text { font-family: 'Segoe UI'; font-size: 9pt; padding: 0 8px; color: #5b6470; }
QLineEdit#calc_input { border-radius: 3px; padding: 2px 6px; font-family: 'Consolas'; font-size: 9pt; min-width: 180px; min-height: 20px; }
QLabel#status_info { font-family: 'Segoe UI'; font-size: 9pt; padding: 0 8px; color: #6b7280; }
QLabel#terminal_output { font-family: Courier New; font-size: 9pt; background-color: #fbfcfd; color: #1e7a4c; }
QLabel#page_header_title { font-size: 13pt; font-weight: normal; font-family: 'Segoe UI'; color: #111827; }
QLabel#page_header_subtitle { color: #6b7280; font-size: 9pt; }
QFrame#page_header_separator { margin: 4px 0 8px 0; }
QLabel#card_title { color: #4b5563; font-family: 'Segoe UI'; font-size: 9pt; font-weight: normal; text-transform: uppercase; letter-spacing: 0.5px; }
QFrame#card_separator { color: #dde0e5; margin: 2px 0 6px 0; }
QLabel#labeled_row_label { color: #4b5563; font-family: 'Segoe UI'; font-size: 9pt; min-width: 120px; }
QFrame#toast { background-color: rgba(255, 255, 255, 235); border: 1px solid #d0d4da; border-radius: 3px; }
QLabel#toast_label { color: #1f2937; font-family: 'Segoe UI'; font-size: 9pt; background: transparent; }
QLabel#log_header { color: #4b5563; font-family: 'Segoe UI'; font-size: 9pt; font-weight: normal; letter-spacing: 0.5px; padding: 4px 0; }
QPlainTextEdit#log_area { background-color: #fbfcfd; color: #4b5563; border: 1px solid #dde0e5; border-radius: 3px; font-family: Consolas; font-size: 9pt; padding: 6px; }
QLabel#stat_icon { font-size: 22pt; color: #9aa0a8; }
QPushButton#dash_action_btn { color: white; border: 1px solid #1f6fd6; border-radius: 3px; padding: 9px 10px; font-family: 'Segoe UI'; font-size: 9pt; background-color: #1f6fd6; }
QPushButton#dash_action_btn:hover { background-color: #1b63c0; }
QChart#dash_chart { background-color: #ffffff; }
QLabel#sys_value { color: #1f2937; font-family: 'Segoe UI'; font-size: 9pt; font-weight: normal; }
QLabel#sysmon_warning { color: #b7791f; font-size: 11pt; padding: 40px; }
QLabel#sysmon_big_value { font-size: 18pt; font-weight: normal; color: #111827; }
QLabel#sysmon_detail { color: #5b6470; font-family: 'Segoe UI'; font-size: 9pt; }
QChart#sysmon_chart { background-color: #ffffff; }
QPlainTextEdit#api_response { font-family: Courier New; font-size: 9pt; }
QLabel#api_status { color: #b7791f; }
QLabel#api_status[status_color="#2f9e68"] { color: #1e9e6a; }
QLabel#api_status[status_color="#cf4444"] { color: #cf4444; }
QLabel#api_status[status_color="#22d3a5"] { color: #1e9e6a; }
QLabel#api_status[status_color="#f74f4f"] { color: #cf4444; }
QLabel#api_status[status_color="#b7791f"] { color: #9a6700; }
QPlainTextEdit#fmt_editor { font-family: Consolas; font-size: 10pt; }
QLabel#fmt_status { color: #5b6470; font-family: 'Segoe UI'; font-size: 9pt; padding: 2px 0; }
QLabel#fmt_status[status_color="#2f9e68"] { color: #1e9e6a; }
QLabel#fmt_status[status_color="#cf4444"] { color: #cf4444; }
QLabel#fmt_status[status_color="#b7791f"] { color: #b7791f; }
QLabel#fmt_status[status_color="#22d3a5"] { color: #1e9e6a; }
QLabel#fmt_status[status_color="#f74f4f"] { color: #cf4444; }
QLabel#fmt_status[status_color="#eab308"] { color: #b7791f; }
QLabel#conn_status { color: #5b6470; font-weight: normal; }
QLabel#conn_status[conn_state="connected"] { color: #1e9e6a; }
QLabel#conn_status[conn_state="disconnected"] { color: #cf4444; }
QLabel#regex_status { color: #5b6470; }
QLabel#regex_status[status_color="ok"] { color: #1e9e6a; }
QLabel#bulk_stat { font-family: Consolas; font-size: 10pt; color: #1f2937; }
QPlainTextEdit#code_output { font-family: Courier New; font-size: 9pt; }
QPlainTextEdit#code_editor { font-family: Courier New; font-size: 10pt; }
QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit, QDateTimeEdit { background-color: #ffffff; color: #1f2937; border: 1px solid #d0d4da; border-radius: 3px; padding: 6px 10px; font-family: "Segoe UI"; font-size: 9pt; selection-background-color: #1f6fd6; selection-color: white; }
QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus, QTimeEdit:focus, QDateTimeEdit:focus { border: 1px solid #1f6fd6; }
QSpinBox::up-button, QSpinBox::down-button, QDoubleSpinBox::up-button, QDoubleSpinBox::down-button { width: 20px; border: none; background: transparent; }
QTableWidget, QTableView { background-color: #ffffff; color: #1f2937; border: 1px solid #dde0e5; border-radius: 3px; gridline-color: #e5e8ec; selection-background-color: #1f6fd6; selection-color: white; font-family: "Segoe UI"; font-size: 9pt; alternate-background-color: #f7f8fa; }
QTableWidget::item:selected, QTableView::item:selected { background-color: #1f6fd6; color: white; }
QTableCornerButton::section { background-color: #e9ebee; border: none; }
QScrollBar:horizontal { height: 10px; background: transparent; }
QScrollBar::handle:horizontal { background: #a8aeb8; border-radius: 4px; min-width: 30px; }
QScrollBar::handle:horizontal:hover { background: #9aa0a8; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QToolTip { background-color: #111827; color: #f9fafb; border: 1px solid #111827; border-radius: 3px; padding: 4px 8px; font-family: "Segoe UI"; font-size: 9pt; }
QLabel#calc_sep { color: #6b7280; font-weight: bold; padding: 0 2px; }
QDialog { background-color: #f2f3f5; border-radius: 4px; }
"""
