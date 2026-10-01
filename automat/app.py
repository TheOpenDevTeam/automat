"""
Main application window — builds the entire UI layout, manages pages,
handles keyboard shortcuts, theme switching, and the sidebar toggle.
Refactored: God object decomposed into ThemeManager, CalcManager, ClockManager.
"""

import sys
import os
import json
from pathlib import Path

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from automat.config import APP_NAME, APP_VERSION, SETTINGS_FILE, DATA_DIR, RED
from automat.i18n import I18n
from automat.ui.widgets import SidebarButton
from automat.ui.icons import get as icon_get

from automat.core.theme_manager import ThemeManager
from automat.core.calc_manager import CalcManager
from automat.core.clock_manager import ClockManager
from automat.core import json_io

from automat.ui.pages.dash import DashPage
from automat.ui.pages.convert_pro import ConvertProPage
from automat.ui.pages.bulk import BulkSendPage
from automat.ui.pages.telegram_page import TelegramPage
from automat.ui.pages.hash_page import HashPage
from automat.ui.pages.datagen import DataGenPage
from automat.ui.pages.cleandata import CleanDataPage
from automat.ui.pages.fileops import FileOpsPage
from automat.ui.pages.cron_scheduler import CronSchedulerPage
from automat.ui.pages.text_tools import TextToolsPage
from automat.ui.pages.settings import SettingsPage
from automat.ui.pages.ssh_client import SSHClientPage
from automat.ui.pages.git_tools import GitToolsPage
from automat.ui.pages.api_tools import ApiToolsPage
from automat.ui.pages.sys_monitor import SysMonitorPage
from automat.ui.pages.snippets import SnippetsPage
from automat.ui.pages.extra_tools import ExtraToolsPage
from automat.ui.pages.clipboard_page import ClipboardPage
from automat.ui.pages.search_page import SearchPage
from automat.ui.pages.history_page import HistoryPage
from automat.ui.pages.theme_builder import ThemeBuilderPage


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
    ("tools",     "page_tools",    "tools",    ExtraToolsPage),
    ("clipboard", "page_clipboard","clipboard",ClipboardPage),
    ("",          None,            None,       None),  # separator
    ("search",    "page_search",   "search",   SearchPage),
    ("history",   "page_history",  "history",  HistoryPage),
    ("",          None,            None,       None),  # separator
    ("ssh",       "page_ssh",      "ssh",      SSHClientPage),
    ("git",       "page_git",      "git",      GitToolsPage),
    ("api",       "page_api",      "api",      ApiToolsPage),
    ("sysmon",    "page_sysmon",   "sysmon",   SysMonitorPage),
    ("snippets",  "page_snippets", "snippets", SnippetsPage),
    ("",          None,            None,       None),  # separator
    ("theme_builder", "page_theme_builder", "theme_builder", ThemeBuilderPage),
    ("settings",  "page_settings", "settings", SettingsPage),
]

SECTION_KEYS = {"ssh": "sidebar_new", "settings": "sidebar_system"}
_PAGE_KEY_BY_INDEX = [p[2] for p in PAGES if p[2] is not None]

BOOKMARKS_FILE = str(Path(os.getenv("APPDATA", Path.home())) / "Automat" / "bookmarks.json")


class AutomatApp(QMainWindow):
    """Top-level window — thin orchestrator delegating to managers."""

    def __init__(self):
        super().__init__()

        self._pages = {}
        self._current_key = None

        # Sidebar state
        self._sidebar_btns = []
        self._section_labels = []
        self._sidebar_trans = []
        self._sidebar_icon_names = []
        self._btn_group = QButtonGroup()
        self._btn_group.setExclusive(True)
        self._sidebar_collapsed = False
        self._nav_history = []
        self._nav_index = -1
        self._sidebar_full_width = 200
        self._sidebar_min_width = 48

        # Bookmarks
        self._bookmarks = self._load_bookmarks()

        # Load persisted settings
        self.settings_data = self._load_settings()
        self.i18n = I18n(self.settings_data.get("lang", "ru"))

        # Delegate to managers
        self.theme_mgr = ThemeManager(self.settings_data, SETTINGS_FILE)
        self.theme_mgr.apply()

        self.setWindowTitle(self.i18n.tr("app_title"))
        self.setMinimumSize(900, 600)
        self.resize(1280, 800)

        # Enable drag & drop
        self.setAcceptDrops(True)

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
        data = json_io.load_json(SETTINGS_FILE, {"theme": "dark", "lang": "ru"})
        if not isinstance(data, dict):
            return {"theme": "dark", "lang": "ru"}
        return data

    def _save_settings(self):
        self.settings_data["geometry"] = {
            "x": self.x(), "y": self.y(),
            "w": self.width(), "h": self.height(),
        }
        self.settings_data["last_page"] = self._current_key or "dash"
        sizes = self.splitter.sizes()
        if len(sizes) == 2:
            self.settings_data["splitter"] = sizes
        if not json_io.save_json(SETTINGS_FILE, self.settings_data):
            print("Error saving settings")

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

    def apply_theme(self):
        """Apply current theme to QSS, icons, calc and all open pages."""
        self.theme_mgr.apply()
        self.theme_btn.setText("\U0001f319" if self.theme_mgr.is_dark else "\u2600\ufe0f")
        self._refresh_icons()
        if hasattr(self, "calc_result"):
            self._paint_calc_result(self.calc_result.text() or "", "muted")
        for page in self._pages.values():
            if hasattr(page, "refresh_theme"):
                try:
                    page.refresh_theme()
                except Exception:
                    pass

    def _toggle_theme(self):
        self.theme_mgr.toggle()
        self.apply_theme()
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
        header.setFixedHeight(52)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 6, 16, 6)

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

        self.back_btn = QPushButton("\u25c0")
        self.back_btn.setFixedSize(30, 30)
        self.back_btn.setObjectName("icon_btn")
        self.back_btn.setToolTip(self.i18n.tr("nav_back"))
        self.back_btn.clicked.connect(self.go_back)
        h_layout.addWidget(self.back_btn)

        self.fwd_btn = QPushButton("\u25b6")
        self.fwd_btn.setFixedSize(30, 30)
        self.fwd_btn.setObjectName("icon_btn")
        self.fwd_btn.setToolTip(self.i18n.tr("nav_forward"))
        self.fwd_btn.clicked.connect(self.go_forward)
        h_layout.addWidget(self.fwd_btn)

        self.palette_btn = QPushButton("\u2315")
        self.palette_btn.setFixedSize(30, 30)
        self.palette_btn.setObjectName("icon_btn")
        self.palette_btn.setToolTip("Ctrl+K")
        self.palette_btn.clicked.connect(self._show_palette)
        h_layout.addWidget(self.palette_btn)

        hint = QLabel("Ctrl+K")
        hint.setObjectName("hint_label")
        h_layout.addWidget(hint)

        self.bookmark_btn = QPushButton("\u2606")
        self.bookmark_btn.setFixedSize(30, 30)
        self.bookmark_btn.setObjectName("icon_btn")
        self.bookmark_btn.setToolTip(self.i18n.tr("bookmark_add"))
        self.bookmark_btn.clicked.connect(self._show_bookmarks_menu)
        h_layout.addWidget(self.bookmark_btn)

        self.theme_btn = QPushButton(
            "\U0001f319" if self.theme_mgr.is_dark else "\u2600\ufe0f"
        )
        self.theme_btn.setFixedSize(30, 30)
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
        calc_label.setObjectName("calc_sep")
        status_bar.addPermanentWidget(calc_label)

        self.calc_input = QLineEdit()
        self.calc_input.setPlaceholderText(self.i18n.tr("calc_placeholder"))
        self.calc_input.setObjectName("calc_input")
        self.calc_input.setFixedWidth(220)
        self.calc_input.setFixedHeight(24)
        self.calc_input.returnPressed.connect(self._eval_calc)
        status_bar.addPermanentWidget(self.calc_input)

        self.calc_result = QLabel("")
        self._paint_calc_result("", "muted")
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

        if mod == Qt.ControlModifier and key == Qt.Key_K:
            self._show_palette()
            return

        if mod == Qt.ControlModifier and key == Qt.Key_B:
            self._toggle_sidebar()
            return

        if mod == (Qt.ControlModifier | Qt.ShiftModifier) and key == Qt.Key_T:
            self._toggle_theme()
            return

        if key == Qt.Key_F1:
            self._show_shortcuts()
            return

        if mod == Qt.AltModifier and key == Qt.Key_Left:
            self.go_back()
            return

        if mod == Qt.AltModifier and key == Qt.Key_Right:
            self.go_forward()
            return

        if mod == (Qt.ControlModifier | Qt.ShiftModifier) and key == Qt.Key_F:
            self.show_page("search")
            return

        if mod == (Qt.ControlModifier | Qt.ShiftModifier) and key == Qt.Key_H:
            self.show_page("history")
            return

        if mod == Qt.ControlModifier and key == Qt.Key_D:
            self._show_bookmarks_menu()
            return

        if mod == (Qt.ControlModifier | Qt.ShiftModifier) and key == Qt.Key_E:
            self._export_settings()
            return

        if mod == (Qt.ControlModifier | Qt.ShiftModifier) and key == Qt.Key_I:
            self._import_settings()
            return

        if mod == Qt.ControlModifier and key == Qt.Key_U:
            self._check_updates()
            return

        super().keyPressEvent(event)

    # ------------------------------------------------------------------
    # Quick calculator (delegated to CalcManager)
    # ------------------------------------------------------------------

    def _calc_palette(self):
        dark = self.theme_mgr.is_dark
        return {
            "muted": "#7d838d" if dark else "#6b7280",
            "ok": "#2e7bd6" if dark else "#1f6fd6",
            "err": "#cf4444",
        }

    def _paint_calc_result(self, text, state="muted"):
        colors = self._calc_palette()
        self.calc_result.setText(text)
        self.calc_result.setStyleSheet(
            "font-family: 'Consolas'; font-size: 9pt; "
            f"color: {colors.get(state, colors['muted'])}; padding: 0 4px; min-width: 60px;"
        )

    def _eval_calc(self):
        text = self.calc_input.text().strip()
        if not text:
            return
        try:
            result = CalcManager.evaluate(text)
            result_str = f"{result:g}" if isinstance(result, float) else str(result)
            self._paint_calc_result(f"  = {result_str}", "ok")
            self.calc_input.selectAll()
        except Exception:
            self._paint_calc_result(f"  {self.i18n.tr('calc_invalid')}", "err")
            self.calc_input.selectAll()

    # ------------------------------------------------------------------
    # Page navigation
    # ------------------------------------------------------------------

    def _clear_page_cache(self):
        for key, page in list(self._pages.items()):
            try:
                if hasattr(page, 'scheduler') and page.scheduler is not None:
                    try:
                        page.scheduler.shutdown(wait=False)
                    except Exception:
                        pass
                self.workspace.removeWidget(page)
                page.deleteLater()
            except Exception:
                pass
        self._pages.clear()
        self._current_key = None

    def show_page(self, key: str, record: bool = True):
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
            try:
                idx = _PAGE_KEY_BY_INDEX.index(key)
                if 0 <= idx < len(self._sidebar_btns):
                    self._sidebar_btns[idx].setChecked(True)
            except Exception:
                pass

        if record and key:
            if not self._nav_history or self._nav_history[self._nav_index] != key:
                self._nav_history = self._nav_history[:self._nav_index + 1]
                self._nav_history.append(key)
                self._nav_index = len(self._nav_history) - 1
                if len(self._nav_history) > 50:
                    self._nav_history.pop(0)
                    self._nav_index -= 1

        names = {k: n for _, n, k, _ in PAGES if k}
        self.status_text.setText(f"  {self.i18n.tr(names.get(key, ''))}")
        self._update_nav_buttons()
        self._update_bookmark_icon()

    def _update_nav_buttons(self):
        if hasattr(self, "back_btn"):
            self.back_btn.setEnabled(self._nav_index > 0)
            self.fwd_btn.setEnabled(self._nav_index < len(self._nav_history) - 1)

    def _update_bookmark_icon(self):
        if hasattr(self, "bookmark_btn") and self._current_key:
            is_bookmarked = self._current_key in self._bookmarks
            self.bookmark_btn.setText("\u2605" if is_bookmarked else "\u2606")
            self.bookmark_btn.setToolTip(
                self.i18n.tr("bookmark_remove" if is_bookmarked else "bookmark_add"))

    def go_back(self):
        if self._nav_index > 0:
            self._nav_index -= 1
            self.show_page(self._nav_history[self._nav_index], record=False)

    def go_forward(self):
        if self._nav_index < len(self._nav_history) - 1:
            self._nav_index += 1
            self.show_page(self._nav_history[self._nav_index], record=False)

    def _show_palette(self):
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QListWidget
        tr = self.i18n.tr
        dlg = QDialog(self)
        dlg.setWindowTitle(tr("palette_title"))
        dlg.setMinimumWidth(420)
        lay = QVBoxLayout(dlg)
        search = QLineEdit()
        search.setPlaceholderText(tr("palette_placeholder"))
        lay.addWidget(search)
        lst = QListWidget()
        lay.addWidget(lst)
        names = [(k, tr(n)) for _, n, k, _ in PAGES if k]
        items = dict(names)

        def refresh():
            q = search.text().strip().lower()
            lst.clear()
            for k, label in names:
                if not q or q in label.lower() or q in k.lower():
                    lst.addItem(f"{label}  [{k}]")

        def goto(item=None):
            row = lst.currentRow()
            if row < 0:
                return
            text = lst.item(row).text()
            k = text.split("[")[-1].rstrip("]")
            dlg.accept()
            self.show_page(k)

        search.textChanged.connect(refresh)
        lst.itemDoubleClicked.connect(goto)
        lst.itemActivated.connect(goto)
        search.returnPressed.connect(goto)
        refresh()
        lst.setCurrentRow(0)
        search.setFocus()
        dlg.exec_()

    def _show_shortcuts(self):
        from PyQt5.QtWidgets import QMessageBox
        tr = self.i18n.tr
        rows = [
            ("Ctrl+K", tr("palette_title")),
            ("Ctrl+1..9", tr("shortcuts_pages")),
            ("Ctrl+T", tr("toggle_theme")),
            ("Ctrl+B", tr("shortcuts_sidebar")),
            ("Alt+Left / Alt+Right", tr("shortcuts_history")),
            ("Ctrl+S", tr("shortcuts_save")),
            ("Ctrl+Shift+F", tr("search_title")),
            ("Ctrl+Shift+H", tr("history_title")),
            ("Ctrl+D", tr("bookmark_add")),
            ("Ctrl+Shift+E", tr("settings_export_title")),
            ("Ctrl+Shift+I", tr("settings_import_title")),
            ("Ctrl+U", tr("auto_update_check")),
            ("F1", tr("shortcuts_title")),
        ]
        text = "\n".join(f"{k}  —  {v}" for k, v in rows)
        QMessageBox.information(self, tr("shortcuts_title"), text)

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

    # ------------------------------------------------------------------
    # Toast notifications
    # ------------------------------------------------------------------

    def toast(self, message, color="#2f9e68", duration=2500):
        from automat.ui.widgets import Toast
        Toast(self, message, color, duration).show()

    # ------------------------------------------------------------------
    # Drag & Drop
    # ------------------------------------------------------------------

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if not urls:
            return
        paths = [u.toLocalFile() for u in urls]
        exts = {Path(p).suffix.lower() for p in paths}
        tr = self.i18n.tr
        n = len(paths)

        pdf_exts = {".pdf"}
        img_exts = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
        office_exts = {".xlsx", ".xls", ".docx", ".doc", ".csv"}
        text_exts = {".txt", ".md", ".json", ".xml", ".yaml", ".yml"}

        if exts & pdf_exts:
            self.show_page("convert")
            self.toast(tr("drag_converted", n=n))
        elif exts & img_exts:
            self.show_page("convert")
            self.toast(tr("drag_images", n=n))
        elif exts & office_exts:
            self.show_page("convert")
            self.toast(tr("drag_office", n=n))
        elif exts & text_exts:
            self.show_page("text")
            self.toast(tr("drag_text", n=n))
        else:
            self.show_page("fileops")
            self.toast(tr("drag_files", n=n))

    # ------------------------------------------------------------------
    # Bookmarks
    # ------------------------------------------------------------------

    def _load_bookmarks(self) -> list:
        data = json_io.load_json(BOOKMARKS_FILE, [])
        return data if isinstance(data, list) else []

    def _save_bookmarks(self):
        json_io.save_json(BOOKMARKS_FILE, self._bookmarks)

    def _toggle_bookmark(self):
        if self._current_key and self._current_key != "bookmarks":
            if self._current_key in self._bookmarks:
                self._bookmarks.remove(self._current_key)
                self.toast(self.i18n.tr("bookmark_remove"))
            else:
                self._bookmarks.append(self._current_key)
                self.toast(self.i18n.tr("bookmark_add"))
            self._save_bookmarks()

    def _show_bookmarks_menu(self):
        tr = self.i18n.tr
        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu { background-color: #2c2f34; color: #e8eaed; border: 1px solid #454a52; "
            "border-radius: 3px; padding: 4px; }"
            "QMenu::item { padding: 6px 20px; border-radius: 3px; }"
            "QMenu::item:selected { background-color: #35383e; }"
        )

        if not self._bookmarks:
            action = menu.addAction(tr("bookmark_empty"))
            action.setEnabled(False)
        else:
            for key in self._bookmarks:
                icon_name = None
                label = key
                for icon, trans_key, k, cls in PAGES:
                    if k == key:
                        icon_name = icon
                        if trans_key:
                            label = tr(trans_key)
                        break
                if icon_name:
                    ico = icon_get(icon_name, 16)
                    action = menu.addAction(ico, label)
                    action.setData(key)

        menu.addSeparator()
        add_action = menu.addAction(f"\u2606 {tr('bookmark_add')}")
        add_action.setData("__toggle__")

        action = menu.exec_(self.bookmark_btn.mapToGlobal(
            QPoint(0, self.bookmark_btn.height())))
        if action:
            data = action.data()
            if data == "__toggle__":
                self._toggle_bookmark()
            elif data:
                self.show_page(data)

    # ------------------------------------------------------------------
    # Settings Export/Import
    # ------------------------------------------------------------------

    def _export_settings(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self, self.i18n.tr("settings_export_title"),
            str(DATA_DIR / "settings_backup.json"),
            "JSON Files (*.json)")
        if filepath:
            try:
                data = {
                    "settings": self.settings_data,
                    "bookmarks": self._bookmarks,
                    "version": APP_VERSION,
                }
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                self.toast(self.i18n.tr("settings_exported", path=os.path.basename(filepath)))
            except Exception as e:
                QMessageBox.warning(self, self.i18n.tr("settings_error"), str(e))

    def _import_settings(self):
        tr = self.i18n
        reply = QMessageBox.question(
            self, tr("settings_import_title"), tr("settings_import_confirm"),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        filepath, _ = QFileDialog.getOpenFileName(
            self, tr("settings_import_title"), str(DATA_DIR),
            "JSON Files (*.json)")
        if filepath:
            try:
                with open(filepath, encoding="utf-8") as f:
                    data = json.load(f)
                if not isinstance(data, dict):
                    raise ValueError("not a settings export")
                if "settings" in data:
                    self.settings_data.update(data["settings"])
                    json_io.save_json(SETTINGS_FILE, self.settings_data)
                if "bookmarks" in data:
                    self._bookmarks = data["bookmarks"]
                    self._save_bookmarks()
                self.toast(tr("settings_imported"))
            except Exception as e:
                QMessageBox.warning(self, tr("settings_import_error"), str(e))

    # ------------------------------------------------------------------
    # Auto-update check
    # ------------------------------------------------------------------

    def _check_updates(self):
        from automat.core.worker import run_in_background
        tr = self.i18n
        self.toast(tr("auto_update_checking"))

        def _fetch():
            try:
                import requests
                r = requests.get(
                    "https://api.github.com/repos/TheOpenDevTeam/automat/releases/latest",
                    timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    tag = data.get("tag_name", "")
                    html_url = data.get("html_url", "")
                    return {"ok": True, "version": tag, "url": html_url}
            except Exception:
                pass
            return {"ok": False}

        def _on_result(data):
            if data.get("ok") and data.get("version"):
                latest = data["version"].lstrip("v")
                current = APP_VERSION
                if latest != current:
                    reply = QMessageBox.information(
                        self, tr("auto_update_title"),
                        f"{tr('auto_update_available', version=latest)}\n\n"
                        f"{tr('auto_update_current', version=current)}",
                        QMessageBox.Open | QMessageBox.Ok,
                        QMessageBox.Ok)
                    if reply == QMessageBox.Open:
                        import webbrowser
                        webbrowser.open(data["url"])
                else:
                    self.toast(tr("auto_update_uptodate"))
            else:
                self.toast(tr("auto_update_error"), RED)

        run_in_background(_fetch, on_result=_on_result)
