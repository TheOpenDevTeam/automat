"""
Main application window — builds the entire UI layout, manages pages,
handles keyboard shortcuts, theme switching, and the sidebar toggle.
Refactored: God object decomposed into ThemeManager, CalcManager, ClockManager.
"""

import sys
import json

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from config import APP_NAME, APP_VERSION, SETTINGS_FILE
from i18n import I18n
from ui.widgets import SidebarButton
from ui.icons import get as icon_get

from core.theme_manager import ThemeManager
from core.calc_manager import CalcManager
from core.clock_manager import ClockManager

from ui.pages.dash import DashPage
from ui.pages.convert_pro import ConvertProPage
from ui.pages.bulk import BulkSendPage
from ui.pages.telegram_page import TelegramPage
from ui.pages.hash_page import HashPage
from ui.pages.datagen import DataGenPage
from ui.pages.cleandata import CleanDataPage
from ui.pages.fileops import FileOpsPage
from ui.pages.cron_scheduler import CronSchedulerPage
from ui.pages.text_tools import TextToolsPage
from ui.pages.settings import SettingsPage
from ui.pages.ssh_client import SSHClientPage
from ui.pages.git_tools import GitToolsPage
from ui.pages.api_tools import ApiToolsPage
from ui.pages.sys_monitor import SysMonitorPage
from ui.pages.snippets import SnippetsPage


# Page registry: (icon, translation_key, page_key, page_class)
PAGES = [
    ("dashboard", "page_dash",     "dash",     DashPage),
    ("convert",   "page_convert",  "convert",  ConvertProPage),
    ("bulk",      "page_bulk",     "bulk",     BulkSendPage),
    ("telegram",  "page_telegram", "telegram", TelegramPage),
    ("hash",      "page_hash",     "hash",     HashPage),
    ("datagen",   "page_datagen",  "datagen",  DataGenPage),
    ("cleandata", "page_cleandata","cleandata",CleanDataPage),
    ("fileops",   "page_fileops",  "fileops",  FileOpsPage),
    ("cron",      "page_cron",     "cron",     CronSchedulerPage),
    ("text",      "page_text",     "text",     TextToolsPage),
    ("",          None,            None,       None),  # separator
    ("ssh",       "page_ssh",      "ssh",      SSHClientPage),
    ("git",       "page_git",      "git",      GitToolsPage),
    ("api",       "page_api",      "api",      ApiToolsPage),
    ("sysmon",    "page_sysmon",   "sysmon",   SysMonitorPage),
    ("snippets",  "page_snippets", "snippets", SnippetsPage),
    ("",          None,            None,       None),  # separator
    ("settings",  "page_settings", "settings", SettingsPage),
]

SECTION_KEYS = {"ssh": "sidebar_new", "settings": "sidebar_system"}
_PAGE_KEY_BY_INDEX = [p[2] for p in PAGES if p[2] is not None]


class AutomatApp(QMainWindow):
    """Top-level window — thin orchestrator delegating to managers."""

    def __init__(self):
        super().__init__()

        self._pages: dict[str, QWidget] = {}
        self._current_key: str | None = None

        # Sidebar state
        self._sidebar_btns: list[QPushButton] = []
        self._section_labels: list[tuple[str, QLabel]] = []
        self._sidebar_trans: list[tuple[QPushButton, str]] = []
        self._sidebar_icon_names: list[str] = []
        self._btn_group = QButtonGroup()
        self._btn_group.setExclusive(True)
        self._sidebar_collapsed = False
        self._sidebar_full_width = 210
        self._sidebar_min_width = 48

        # Load persisted settings
        self.settings_data = self._load_settings()
        self.i18n = I18n(self.settings_data.get("lang", "ru"))

        # Delegate to managers
        self.theme_mgr = ThemeManager(self.settings_data, SETTINGS_FILE)
        self.theme_mgr.apply()

        self.setWindowTitle(self.i18n.tr("app_title"))
        self.setMinimumSize(900, 600)
        self.resize(1280, 800)

        self._build_ui()
        self._restore_geometry()

        # Clock manager — owns the timer
        self.clock_mgr = ClockManager(self.clock)

        self.show_page("dash")
        self._refresh_ui_text()

    # ------------------------------------------------------------------
    # Settings persistence
    # ------------------------------------------------------------------

    def _load_settings(self) -> dict:
        try:
            with open(SETTINGS_FILE) as f:
                return json.load(f)
        except Exception:
            return {"theme": "dark", "lang": "ru"}

    def _save_settings(self):
        try:
            self.settings_data["geometry"] = {
                "x": self.x(), "y": self.y(),
                "w": self.width(), "h": self.height(),
            }
            self.settings_data["last_page"] = self._current_key or "dash"
            sizes = self.splitter.sizes()
            if len(sizes) == 2:
                self.settings_data["splitter"] = sizes
            with open(SETTINGS_FILE, "w") as f:
                json.dump(self.settings_data, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def _restore_geometry(self):
        try:
            g = self.settings_data.get("geometry")
            if g:
                self.setGeometry(g["x"], g["y"], g["w"], g["h"])
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Theme (delegated to ThemeManager)
    # ------------------------------------------------------------------

    def _toggle_theme(self):
        new = self.theme_mgr.toggle()
        self.theme_btn.setText("\U0001f319" if new == "dark" else "\u2600\ufe0f")
        self._refresh_icons()
        self._save_settings()

    def _refresh_icons(self):
        if not hasattr(self, '_header_icon_lbl'):
            return
        self._header_icon_lbl.setPixmap(icon_get("dashboard", 28).pixmap(28, 28))
        for i, btn in enumerate(self._sidebar_btns):
            if i < len(self._sidebar_icon_names):
                btn.setIcon(icon_get(self._sidebar_icon_names[i], 20))

    # ------------------------------------------------------------------
    # UI text refresh
    # ------------------------------------------------------------------

    def _rebuild_ui_text(self):
        tr = self.i18n.tr
        self.setWindowTitle(tr("app_title"))
        self.header_title.setText(tr("header_title"))
        self.header_subtitle.setText(tr("app_subtitle", version=APP_VERSION))
        self.status_text.setText(tr("status_ready"))
        self.status_info.setText(
            tr("status_python", ver=sys.version.split()[0], version=APP_VERSION)
        )
        self.theme_btn.setToolTip(tr("toggle_theme"))
        self.sidebar_toggle.setToolTip(
            tr("sidebar_expand") if self._sidebar_collapsed else tr("sidebar_collapse")
        )
        self.calc_input.setPlaceholderText(tr("calc_placeholder"))
        for section_key, label in self._section_labels:
            label.setText(f"  {tr(section_key)}")
        for btn, trans_key in self._sidebar_trans:
            btn.setText(f"  {tr(trans_key)}")

    def _refresh_ui_text(self):
        self._rebuild_ui_text()
        key = self._current_key
        if key:
            names = {k: n for _, n, k, _ in PAGES if k}
            self.status_text.setText(f"  {self.i18n.tr(names.get(key, ''))}")

    # ------------------------------------------------------------------
    # Main UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self._build_header(main_layout)
        self._build_body(main_layout)
        self._build_status_bar()

    def _build_header(self, parent_layout: QVBoxLayout):
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(60)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 8, 24, 8)

        self._header_icon_lbl = QLabel()
        self._header_icon_lbl.setPixmap(icon_get("dashboard", 28).pixmap(28, 28))
        h_layout.addWidget(self._header_icon_lbl)

        title_box = QVBoxLayout()
        title_box.setSpacing(0)
        self.header_title = QLabel("AUTOMAT")
        self.header_title.setObjectName("header_title")
        title_box.addWidget(self.header_title)
        self.header_subtitle = QLabel("")
        self.header_subtitle.setObjectName("text_muted")
        title_box.addWidget(self.header_subtitle)
        h_layout.addLayout(title_box)
        h_layout.addStretch()

        hint = QLabel("Ctrl+1..9  Ctrl+T")
        hint.setObjectName("text_muted")
        hint.setObjectName("hint_label")
        h_layout.addWidget(hint)

        self.theme_btn = QPushButton(
            "\U0001f319" if self.theme_mgr.is_dark else "\u2600\ufe0f"
        )
        self.theme_btn.setFixedSize(36, 36)
        self.theme_btn.setObjectName("icon_btn")
        self.theme_btn.clicked.connect(self._toggle_theme)
        h_layout.addWidget(self.theme_btn)

        self.clock = QLabel()
        self.clock.setObjectName("clock_label")
        h_layout.addWidget(self.clock)

        parent_layout.addWidget(header)

    def _build_body(self, parent_layout: QVBoxLayout):
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(2)
        self.splitter.setChildrenCollapsible(False)
        self._build_sidebar(self.splitter)
        self._build_workspace(self.splitter)
        saved_sizes = self.settings_data.get("splitter")
        if saved_sizes and len(saved_sizes) == 2:
            self.splitter.setSizes(saved_sizes)
        else:
            self.splitter.setSizes([self._sidebar_full_width, 1280])

        body_layout.addWidget(self.splitter)
        parent_layout.addWidget(body, 1)

    def _build_sidebar(self, parent_layout: QSplitter):
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setMinimumWidth(self._sidebar_min_width)
        self.sidebar.setMaximumWidth(self._sidebar_full_width)
        sb_layout = QVBoxLayout(self.sidebar)
        sb_layout.setContentsMargins(0, 4, 0, 4)
        sb_layout.setSpacing(0)

        self.sidebar_toggle = QPushButton("\u25c0")
        self.sidebar_toggle.setObjectName("icon_btn")
        self.sidebar_toggle.setFixedSize(36, 36)
        self.sidebar_toggle.setCursor(Qt.PointingHandCursor)
        self.sidebar_toggle.clicked.connect(self._toggle_sidebar)
        toggle_row = QHBoxLayout()
        toggle_row.addWidget(self.sidebar_toggle)
        toggle_row.addStretch()
        sb_layout.addLayout(toggle_row)

        self._btn_group = QButtonGroup()
        self._btn_group.setExclusive(True)

        for icon_name, trans_key, key, cls in PAGES:
            if key is None:
                sep = QFrame()
                sep.setFrameShape(QFrame.HLine)
                sep.setObjectName("sidebar_separator")
                sb_layout.addWidget(sep)
                section_key = SECTION_KEYS.get(icon_name, "sidebar_tools")
                lbl = QLabel(f"  {self.i18n.tr(section_key)}")
                lbl.setObjectName("sidebar_section")
                sb_layout.addWidget(lbl)
                self._section_labels.append((section_key, lbl))
                continue

            ico = icon_get(icon_name, 20)
            btn = SidebarButton(ico, self.i18n.tr(trans_key))
            btn.clicked.connect(lambda checked, k=key: self.show_page(k))
            self._btn_group.addButton(btn)
            self._sidebar_btns.append(btn)
            self._sidebar_trans.append((btn, trans_key))
            self._sidebar_icon_names.append(icon_name)
            sb_layout.addWidget(btn)

        sb_layout.addStretch()
        parent_layout.addWidget(self.sidebar)

    def _build_workspace(self, parent_layout: QSplitter):
        self.workspace = QStackedWidget()
        parent_layout.addWidget(self.workspace)

    def _build_status_bar(self):
        status_bar = QStatusBar()
        status_bar.setObjectName("status_bar")

        self.status_text = QLabel("")
        self.status_text.setObjectName("status_text")
        status_bar.addWidget(self.status_text)

        calc_label = QLabel(" = ")
        calc_label.setStyleSheet("font-weight: bold; color: #94a3b8; padding: 0 2px;")
        status_bar.addPermanentWidget(calc_label)

        self.calc_input = QLineEdit()
        self.calc_input.setPlaceholderText(self.i18n.tr("calc_placeholder"))
        self.calc_input.setObjectName("calc_input")
        self.calc_input.setFixedWidth(220)
        self.calc_input.setFixedHeight(24)
        self.calc_input.returnPressed.connect(self._eval_calc)
        status_bar.addPermanentWidget(self.calc_input)

        self.calc_result = QLabel("")
        self.calc_result.setStyleSheet(
            "font-family: 'Consolas'; font-size: 9pt; font-weight: bold; "
            "color: #94a3b8; padding: 0 4px; min-width: 60px;"
        )
        status_bar.addPermanentWidget(self.calc_result)

        self.status_info = QLabel("")
        self.status_info.setObjectName("status_info")
        status_bar.addPermanentWidget(self.status_info)

        self.setStatusBar(status_bar)

    # ------------------------------------------------------------------
    # Collapsible sidebar
    # ------------------------------------------------------------------

    def _toggle_sidebar(self):
        self._sidebar_collapsed = not self._sidebar_collapsed
        start_w = self.sidebar.width()
        target = (
            self._sidebar_min_width if self._sidebar_collapsed else self._sidebar_full_width
        )

        self._anim = QPropertyAnimation(self.sidebar, b"minimumWidth")
        self._anim.setDuration(180)
        self._anim.setStartValue(start_w)
        self._anim.setEndValue(target)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.valueChanged.connect(self._on_sidebar_anim)
        self._anim.finished.connect(self._on_sidebar_anim_finished)

        self._anim2 = QPropertyAnimation(self.sidebar, b"maximumWidth")
        self._anim2.setDuration(180)
        self._anim2.setStartValue(start_w)
        self._anim2.setEndValue(target)
        self._anim2.setEasingCurve(QEasingCurve.OutCubic)

        self._anim.start()
        self._anim2.start()

        self.sidebar_toggle.setText("\u25b6" if self._sidebar_collapsed else "\u25c0")
        tr = self.i18n.tr
        self.sidebar_toggle.setToolTip(
            tr("sidebar_expand") if self._sidebar_collapsed else tr("sidebar_collapse")
        )

    def _on_sidebar_anim(self, value):
        sizes = self.splitter.sizes()
        if len(sizes) == 2:
            sizes[0] = int(value)
            self.splitter.setSizes(sizes)

    def _on_sidebar_anim_finished(self):
        sizes = self.splitter.sizes()
        if len(sizes) == 2:
            target = self._sidebar_min_width if self._sidebar_collapsed else self._sidebar_full_width
            sizes[0] = target
            self.splitter.setSizes(sizes)

    # ------------------------------------------------------------------
    # Keyboard shortcuts
    # ------------------------------------------------------------------

    def keyPressEvent(self, event: QKeyEvent):
        mod = event.modifiers()
        key = event.key()

        if mod == Qt.ControlModifier and Qt.Key_1 <= key <= Qt.Key_9:
            idx = key - Qt.Key_1
            if idx < len(_PAGE_KEY_BY_INDEX):
                self.show_page(_PAGE_KEY_BY_INDEX[idx])
            return

        if mod == Qt.ControlModifier and key == Qt.Key_T:
            self._toggle_theme()
            return

        if mod == Qt.ControlModifier and key == Qt.Key_S:
            self._save_settings()
            return

        super().keyPressEvent(event)

    # ------------------------------------------------------------------
    # Quick calculator (delegated to CalcManager)
    # ------------------------------------------------------------------

    def _eval_calc(self):
        text = self.calc_input.text().strip()
        if not text:
            return
        try:
            result = CalcManager.evaluate(text)
            result_str = f"{result:g}" if isinstance(result, float) else str(result)
            self.calc_result.setText(f"  = {result_str}")
            self.calc_result.setStyleSheet(
                "font-family: 'Consolas'; font-size: 9pt; font-weight: bold; "
                "color: #22d3ee; padding: 0 4px; min-width: 60px;"
            )
            self.calc_input.selectAll()
        except Exception:
            self.calc_result.setText(f"  {self.i18n.tr('calc_invalid')}")
            self.calc_result.setStyleSheet(
                "font-family: 'Consolas'; font-size: 9pt; font-weight: bold; "
                "color: #ef4444; padding: 0 4px; min-width: 60px;"
            )
            self.calc_input.selectAll()

    # ------------------------------------------------------------------
    # Page navigation
    # ------------------------------------------------------------------

    def _clear_page_cache(self):
        for key, page in list(self._pages.items()):
            self.workspace.removeWidget(page)
            page.deleteLater()
        self._pages.clear()
        self._current_key = None

    def show_page(self, key: str):
        if key not in self._pages:
            for icon, name, k, cls in PAGES:
                if k == key:
                    page = cls(self)
                    self._pages[key] = page
                    self.workspace.addWidget(page)
                    break

        widget = self._pages.get(key)
        if widget:
            self.workspace.setCurrentWidget(widget)
            self._current_key = key

        names = {k: n for _, n, k, _ in PAGES if k}
        self.status_text.setText(f"  {self.i18n.tr(names.get(key, ''))}")

    # ------------------------------------------------------------------
    # Window close
    # ------------------------------------------------------------------

    def closeEvent(self, event):
        self._save_settings()
        self.clock_mgr.stop()
        for key, page in self._pages.items():
            if hasattr(page, 'scheduler') and page.scheduler is not None:
                try:
                    page.scheduler.shutdown(wait=False)
                except Exception:
                    pass
        event.accept()
