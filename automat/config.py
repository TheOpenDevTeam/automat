import os
from dataclasses import dataclass
from pathlib import Path

APP_NAME = "AUTOMAT"
APP_TITLE = "AUTOMAT — Task Automation Manager"
ORG_NAME = "Auxo"


def _app_version() -> str:
    """Single source of truth for the version: installed dist metadata,
    with a fallback for plain source checkouts."""
    try:
        from importlib.metadata import version
        return version("automat")
    except Exception:
        return "1.0.0"


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


# ── Legacy color constants (kept for backward compatibility) ───────────
ACCENT = "#2e7bd6"
ACCENT2 = "#5b7fa6"
GREEN = "#2f9e68"
YELLOW = "#b7791f"
RED = "#cf4444"


# ── Design system: color palettes ──────────────────────────────────────
@dataclass
class Palette:
    """Named color tokens for a single theme. Changing a token here
    updates every QSS rule that references it."""
    bg_main: str
    bg_header: str
    bg_sidebar: str
    bg_card: str
    bg_button: str
    bg_button_hover: str
    bg_button_pressed: str
    bg_button_disabled: str
    bg_input: str
    border_main: str
    border_button: str
    border_hover: str
    border_focus: str
    text_main: str
    text_muted: str
    text_secondary: str
    text_tertiary: str
    text_white: str
    accent: str
    accent_hover: str
    accent2: str
    accent2_hover: str
    success: str
    success_hover: str
    danger: str
    danger_hover: str
    selection: str
    scrollbar_handle: str
    scrollbar_handle_hover: str


DARK_PALETTE = Palette(
    bg_main="#232529", bg_header="#26282d", bg_sidebar="#26282d",
    bg_card="#2c2f34", bg_button="#35383e", bg_button_hover="#3d4148",
    bg_button_pressed="#2a2d32", bg_button_disabled="#2c2f34",
    bg_input="#1f2125",
    border_main="#3a3d43", border_button="#454a52", border_hover="#555b64",
    border_focus="#2e7bd6",
    text_main="#e8eaed", text_muted="#b5bac2", text_secondary="#9aa0a8",
    text_tertiary="#7d838d", text_white="#ffffff",
    accent="#2e7bd6", accent_hover="#2a6fc2",
    accent2="#3d4b5c", accent2_hover="#46566a",
    success="#2f9e68", success_hover="#2a8f5e",
    danger="#cf4444", danger_hover="#bd3d3d",
    selection="#2e7bd6",
    scrollbar_handle="#5a6069", scrollbar_handle_hover="#555b64",
)

LIGHT_PALETTE = Palette(
    bg_main="#f2f3f5", bg_header="#ffffff", bg_sidebar="#e9ebee",
    bg_card="#ffffff", bg_button="#ffffff", bg_button_hover="#eef0f3",
    bg_button_pressed="#dfe3e9", bg_button_disabled="#f2f3f5",
    bg_input="#ffffff",
    border_main="#dde0e5", border_button="#d0d4da", border_hover="#b9bfc8",
    border_focus="#1f6fd6",
    text_main="#1f2937", text_muted="#4b5563", text_secondary="#5b6470",
    text_tertiary="#6b7280", text_white="#ffffff",
    accent="#1f6fd6", accent_hover="#1b63c0",
    accent2="#5b6b7c", accent2_hover="#4f5e6e",
    success="#1e9e6a", success_hover="#1b8d5f",
    danger="#cf4444", danger_hover="#bd3d3d",
    selection="#1f6fd6",
    scrollbar_handle="#a8aeb8", scrollbar_handle_hover="#9aa0a8",
)


def _qss(p: Palette) -> str:
    """Build a QSS string from a palette. All color values come from
    the palette tokens so a single change propagates everywhere."""
    warn = YELLOW  # theme-independent
    err = RED      # theme-independent
    return f"""
QMainWindow, QWidget {{ background-color: {p.bg_main}; color: {p.text_main}; font-family: "Segoe UI"; font-size: 9pt; }}
QFrame#header {{ background-color: {p.bg_header}; border: none; border-bottom: 1px solid {p.border_main}; }}
QFrame#sidebar {{ background-color: {p.bg_sidebar}; border: none; border-right: 1px solid {p.border_main}; }}
QFrame#card {{ background-color: {p.bg_card}; border: 1px solid {p.border_main}; border-radius: 4px; }}
QFrame#card_accent {{ background-color: {p.bg_card}; border: 1px solid {p.border_main}; border-radius: 4px; }}
QPushButton {{ background-color: {p.bg_button}; color: {p.text_main}; border: 1px solid {p.border_button}; border-radius: 3px; padding: 5px 12px; font-family: "Segoe UI"; font-size: 9pt; }}
QPushButton:hover {{ background-color: {p.bg_button_hover}; border: 1px solid {p.border_hover}; }}
QPushButton:pressed {{ background-color: {p.bg_button_pressed}; border: 1px solid {p.border_button}; }}
QPushButton:disabled {{ background-color: {p.bg_button_disabled}; color: {p.text_tertiary}; border: 1px solid {p.border_main}; }}
QPushButton:focus {{ border: 1px solid {p.border_focus}; }}
QPushButton#accent {{ background-color: {p.accent}; color: {p.text_white}; border: 1px solid {p.accent}; padding: 5px 12px; min-height: 18px; min-width: 60px; }}
QPushButton#accent:hover {{ background-color: {p.accent_hover}; border: 1px solid {p.accent_hover}; }}
QPushButton#accent2 {{ background-color: {p.accent2}; color: {p.text_white}; border: 1px solid {p.accent2}; padding: 5px 12px; min-height: 18px; min-width: 60px; }}
QPushButton#accent2:hover {{ background-color: {p.accent2_hover}; }}
QPushButton#success {{ background-color: {p.success}; color: {p.text_white}; border: 1px solid {p.success}; padding: 5px 12px; min-height: 18px; min-width: 60px; }}
QPushButton#success:hover {{ background-color: {p.success_hover}; }}
QPushButton#danger {{ background-color: {p.danger}; color: {p.text_white}; border: 1px solid {p.danger}; padding: 5px 12px; min-height: 18px; min-width: 60px; }}
QPushButton#danger:hover {{ background-color: {p.danger_hover}; }}
QPushButton#sidebar_btn {{ background-color: transparent; color: {p.text_muted}; border: none; text-align: left; padding: 7px 12px; border-radius: 0; font-family: "Segoe UI"; font-size: 9pt; border-left: 2px solid transparent; }}
QPushButton#sidebar_btn:hover {{ background-color: {p.bg_card}; color: {p.text_white}; }}
QPushButton#sidebar_btn:checked {{ background-color: {p.bg_button}; color: {p.text_white}; border-left: 2px solid {p.accent}; }}
QPushButton#icon_btn {{ background-color: transparent; color: {p.text_muted}; border: 1px solid {p.border_button}; border-radius: 3px; padding: 4px; font-size: 11pt; min-width: 30px; min-height: 30px; }}
QLabel#sidebar_section {{ color: {p.text_tertiary}; font-family: "Segoe UI"; font-size: 8pt; font-weight: normal; letter-spacing: 0.5px; padding: 8px 12px 4px; }}
QPushButton#icon_btn:hover {{ background-color: {p.bg_button}; color: {p.text_white}; }}
QLabel {{ color: {p.text_main}; background: transparent; font-family: "Segoe UI"; }}
QLabel#header_title {{ font-size: 12pt; font-weight: normal; color: {p.text_white}; letter-spacing: 1px; }}
QLabel#text_muted {{ color: {p.text_secondary}; font-size: 9pt; }}
QLabel#text_secondary {{ color: {p.text_muted}; }}
QLabel#stat_value {{ font-size: 18pt; font-weight: normal; color: {p.text_white}; font-family: 'Segoe UI'; }}
QLabel#stat_label {{ color: {p.text_muted}; font-size: 9pt; }}
QLabel#stat_today {{ color: {p.text_tertiary}; font-size: 8pt; }}
QLineEdit {{ background-color: {p.bg_input}; color: {p.text_main}; border: 1px solid {p.border_button}; border-radius: 3px; padding: 6px 10px; font-family: "Segoe UI"; font-size: 9pt; selection-background-color: {p.selection}; }}
QLineEdit:focus {{ border: 1px solid {p.border_focus}; }}
QLineEdit[inputState="false"] {{ border: 1px solid {p.danger}; }}
QTextEdit, QPlainTextEdit {{ background-color: {p.bg_input}; color: {p.text_main}; border: 1px solid {p.border_button}; border-radius: 3px; font-family: "Consolas"; font-size: 10pt; padding: 6px; selection-background-color: {p.selection}; }}
QComboBox {{ background-color: {p.bg_button}; color: {p.text_main}; border: 1px solid {p.border_button}; border-radius: 3px; padding: 6px 10px; font-family: "Segoe UI"; font-size: 9pt; }}
QComboBox:hover {{ border: 1px solid {p.border_hover}; }}
QComboBox:focus {{ border: 1px solid {p.border_focus}; }}
QComboBox::drop-down {{ border: none; width: 28px; }}
QComboBox QAbstractItemView {{ background-color: {p.bg_card}; color: {p.text_main}; selection-background-color: {p.selection}; selection-color: {p.text_white}; border: 1px solid {p.border_button}; border-radius: 3px; }}
QCheckBox {{ color: {p.text_muted}; background: transparent; font-family: "Segoe UI"; spacing: 8px; font-size: 9pt; }}
QCheckBox::indicator {{ width: 15px; height: 15px; border-radius: 2px; border: 1px solid {p.border_hover}; background-color: {p.bg_input}; }}
QCheckBox::indicator:checked {{ background-color: {p.accent}; border: 1px solid {p.accent}; }}
QRadioButton {{ color: {p.text_muted}; background: transparent; font-family: "Segoe UI"; spacing: 8px; font-size: 9pt; }}
QRadioButton::indicator {{ width: 15px; height: 15px; border-radius: 8px; border: 1px solid {p.border_hover}; background-color: {p.bg_input}; }}
QRadioButton::indicator:checked {{ background-color: {p.accent}; border: 1px solid {p.accent}; }}
QTabWidget::pane {{ border: 1px solid {p.border_main}; background-color: {p.bg_main}; border-radius: 3px; }}
QTabBar::tab {{ background-color: {p.bg_header}; color: {p.text_secondary}; padding: 7px 14px; font-family: "Segoe UI"; font-size: 9pt; border: none; border-bottom: 2px solid transparent; margin-right: 1px; }}
QTabBar::tab:selected {{ background-color: {p.bg_card}; color: {p.text_white}; border-bottom: 2px solid {p.accent}; }}
QTabBar::tab:hover {{ background-color: {p.bg_button}; color: {p.text_main}; }}
QScrollArea {{ border: none; }}
QScrollBar:vertical {{ width: 10px; background: transparent; }}
QScrollBar::handle:vertical {{ background: {p.scrollbar_handle}; border-radius: 4px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {p.scrollbar_handle_hover}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QProgressBar {{ background-color: {p.bg_button}; border: none; border-radius: 2px; height: 6px; text-align: center; font-size: 8pt; }}
QProgressBar::chunk {{ background-color: {p.accent}; border-radius: 2px; }}
QTreeWidget, QTreeView {{ background-color: {p.bg_card}; color: {p.text_main}; border: 1px solid {p.border_main}; border-radius: 3px; font-family: "Segoe UI"; font-size: 9pt; }}
QTreeWidget::item:hover {{ background-color: {p.bg_button}; }}
QTreeWidget::item:selected {{ background-color: {p.accent}; color: {p.text_white}; }}
QHeaderView::section {{ background-color: {p.bg_header}; color: {p.text_secondary}; padding: 7px 6px; border: none; border-bottom: 1px solid {p.border_main}; border-right: 1px solid {p.border_main}; font-family: "Segoe UI"; font-size: 9pt; font-weight: normal; }}
QListWidget {{ background-color: {p.bg_card}; color: {p.text_main}; border: 1px solid {p.border_main}; border-radius: 3px; font-family: "Segoe UI"; font-size: 9pt; padding: 4px; }}
QListWidget::item {{ padding: 5px 8px; border-radius: 2px; }}
QListWidget::item:hover {{ background-color: {p.bg_button}; }}
QListWidget::item:selected {{ background-color: {p.accent}; color: {p.text_white}; }}
QSplitter::handle {{ background-color: {p.border_main}; }}
QStatusBar {{ background-color: {p.bg_header}; color: {p.text_secondary}; font-family: "Segoe UI"; font-size: 9pt; border-top: 1px solid {p.border_main}; }}
QMenuBar {{ background-color: {p.bg_header}; color: {p.text_main}; border-bottom: 1px solid {p.border_main}; }}
QMenuBar::item {{ padding: 4px 10px; background: transparent; }}
QMenuBar::item:selected {{ background-color: {p.bg_button}; }}
QMenu {{ background-color: {p.bg_card}; color: {p.text_main}; border: 1px solid {p.border_button}; border-radius: 3px; padding: 4px; }}
QMenu::item {{ padding: 6px 20px; border-radius: 3px; }}
QMenu::item:selected {{ background-color: {p.bg_button}; }}
QGroupBox {{ border: 1px solid {p.border_main}; border-radius: 3px; margin-top: 12px; padding-top: 12px; font-family: "Segoe UI"; color: {p.text_muted}; font-size: 9pt; }}
QGroupBox::title {{ subcontrol-origin: margin; padding: 2px 8px; }}
QFontComboBox {{ background-color: {p.bg_button}; color: {p.text_main}; border: 1px solid {p.border_button}; border-radius: 3px; padding: 6px 10px; font-family: "Segoe UI"; font-size: 9pt; }}
QFrame#sidebar_separator {{ margin: 6px 12px; }}
QLabel#hint_label {{ font-family: 'Segoe UI'; font-size: 8pt; padding: 0 8px; color: {p.text_tertiary}; }}
QLabel#clock_label {{ font-family: 'Segoe UI'; font-size: 9pt; padding: 0 12px; color: {p.text_secondary}; }}
QLabel#status_text {{ font-family: 'Segoe UI'; font-size: 9pt; padding: 0 8px; color: {p.text_secondary}; }}
QLineEdit#calc_input {{ border-radius: 3px; padding: 2px 6px; font-family: 'Consolas'; font-size: 9pt; min-width: 180px; min-height: 20px; }}
QLabel#status_info {{ font-family: 'Segoe UI'; font-size: 9pt; padding: 0 8px; color: {p.text_tertiary}; }}
QPlainTextEdit#terminal_output {{ font-family: Courier New; font-size: 9pt; background-color: #1a1c1f; color: #7fd6a2; }}
QLabel#page_header_title {{ font-size: 13pt; font-weight: normal; font-family: 'Segoe UI'; color: {p.text_white}; }}
QLabel#page_header_subtitle {{ color: {p.text_tertiary}; font-size: 9pt; }}
QFrame#page_header_separator {{ margin: 4px 0 8px 0; }}
QLabel#card_title {{ color: {p.text_muted}; font-family: 'Segoe UI'; font-size: 9pt; font-weight: normal; text-transform: uppercase; letter-spacing: 0.5px; }}
QFrame#card_separator {{ color: {p.border_main}; margin: 2px 0 6px 0; }}
QLabel#labeled_row_label {{ color: {p.text_muted}; font-family: 'Segoe UI'; font-size: 9pt; min-width: 120px; }}
QFrame#toast {{ background-color: rgba(44, 47, 52, 230); border: 1px solid {p.border_button}; border-radius: 3px; }}
QLabel#toast_label {{ color: {p.text_main}; font-family: 'Segoe UI'; font-size: 9pt; background: transparent; }}
QLabel#log_header {{ color: {p.text_secondary}; font-family: 'Segoe UI'; font-size: 9pt; font-weight: normal; letter-spacing: 0.5px; padding: 4px 0; }}
QPlainTextEdit#log_area {{ background-color: {p.bg_input}; color: {p.text_muted}; border: 1px solid {p.border_main}; border-radius: 3px; font-family: Consolas; font-size: 9pt; padding: 6px; }}
QLabel#stat_icon {{ font-size: 22pt; color: {p.text_tertiary}; }}
QLabel#sys_label {{ color: {p.text_secondary}; font-size: 9pt; }}
QLabel#stat_label_mono {{ font-family: Consolas; font-size: 10pt; color: {p.text_muted}; }}
QLabel#match_count {{ color: {p.text_secondary}; font-size: 9pt; }}
QPlainTextEdit#text_editor {{ font-family: Consolas; font-size: 10pt; }}
QPushButton#dash_action_btn {{ color: {p.text_white}; border: 1px solid {p.accent}; border-radius: 3px; padding: 9px 10px; font-family: 'Segoe UI'; font-size: 9pt; background-color: {p.accent}; }}
QPushButton#dash_action_btn:hover {{ background-color: {p.accent_hover}; }}
QChart#dash_chart {{ background-color: {p.bg_card}; }}
QLabel#sys_value {{ color: {p.text_main}; font-family: 'Segoe UI'; font-size: 9pt; font-weight: normal; }}
QLabel#sysmon_warning {{ color: {warn}; font-size: 11pt; padding: 40px; }}
QLabel#sysmon_big_value {{ font-size: 18pt; font-weight: normal; color: {p.text_main}; }}
QLabel#sysmon_detail {{ color: {p.text_secondary}; font-family: 'Segoe UI'; font-size: 9pt; }}
QChart#sysmon_chart {{ background-color: {p.bg_card}; }}
QPlainTextEdit#api_response {{ font-family: Courier New; font-size: 9pt; }}
QLabel#api_status {{ color: #b7791f; }}
QLabel#api_status[status_color="#2f9e68"] {{ color: {p.success}; }}
QLabel#api_status[status_color="#cf4444"] {{ color: {p.danger}; }}
QLabel#api_status[status_color="#22d3a5"] {{ color: {p.success}; }}
QLabel#api_status[status_color="#f74f4f"] {{ color: {p.danger}; }}
QLabel#api_status[status_color="#b7791f"] {{ color: #b7791f; }}
QPlainTextEdit#fmt_editor {{ font-family: Consolas; font-size: 10pt; }}
QLabel#fmt_status {{ color: {p.text_secondary}; font-family: 'Segoe UI'; font-size: 9pt; padding: 2px 0; }}
QLabel#fmt_status[status_color="#2f9e68"] {{ color: {p.success}; }}
QLabel#fmt_status[status_color="#cf4444"] {{ color: {p.danger}; }}
QLabel#fmt_status[status_color="#b7791f"] {{ color: #b7791f; }}
QLabel#fmt_status[status_color="#22d3a5"] {{ color: {p.success}; }}
QLabel#fmt_status[status_color="#f74f4f"] {{ color: {p.danger}; }}
QLabel#fmt_status[status_color="#eab308"] {{ color: #b7791f; }}
QLabel#conn_status {{ color: {p.text_secondary}; font-weight: normal; }}
QLabel#conn_status[conn_state="connected"] {{ color: {p.success}; }}
QLabel#conn_status[conn_state="disconnected"] {{ color: {p.danger}; }}
QLabel#regex_status {{ color: {p.text_secondary}; }}
QLabel#regex_status[status_color="ok"] {{ color: {p.success}; }}
QLabel#bulk_stat {{ font-family: Consolas; font-size: 10pt; color: {p.text_main}; }}
QPlainTextEdit#code_output {{ font-family: Courier New; font-size: 9pt; }}
QPlainTextEdit#code_editor {{ font-family: Courier New; font-size: 10pt; }}
QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit, QDateTimeEdit {{ background-color: {p.bg_input}; color: {p.text_main}; border: 1px solid {p.border_button}; border-radius: 3px; padding: 6px 10px; font-family: "Segoe UI"; font-size: 9pt; selection-background-color: {p.selection}; }}
QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus, QTimeEdit:focus, QDateTimeEdit:focus {{ border: 1px solid {p.border_focus}; }}
QSpinBox::up-button, QSpinBox::down-button, QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{ width: 20px; border: none; background: transparent; }}
QTableWidget, QTableView {{ background-color: {p.bg_card}; color: {p.text_main}; border: 1px solid {p.border_main}; border-radius: 3px; gridline-color: {p.border_main}; selection-background-color: {p.selection}; selection-color: {p.text_white}; font-family: "Segoe UI"; font-size: 9pt; alternate-background-color: {p.bg_button}; }}
QTableWidget::item:selected, QTableView::item:selected {{ background-color: {p.selection}; color: {p.text_white}; }}
QTableCornerButton::section {{ background-color: {p.bg_header}; border: none; }}
QScrollBar:horizontal {{ height: 10px; background: transparent; }}
QScrollBar::handle:horizontal {{ background: {p.scrollbar_handle}; border-radius: 4px; min-width: 30px; }}
QScrollBar::handle:horizontal:hover {{ background: {p.scrollbar_handle_hover}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
QToolTip {{ background-color: {p.bg_button}; color: {p.text_main}; border: 1px solid {p.border_hover}; border-radius: 3px; padding: 4px 8px; font-family: "Segoe UI"; font-size: 9pt; }}
QLabel#calc_sep {{ color: {p.text_tertiary}; font-weight: bold; padding: 0 2px; }}
QDialog {{ background-color: {p.bg_main}; border-radius: 4px; }}
"""


DARK_STYLE = _qss(DARK_PALETTE)
LIGHT_STYLE = _qss(LIGHT_PALETTE)
