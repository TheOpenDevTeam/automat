"""Global search page — search across all tools, settings, and activity log."""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from automat.ui.page_base import PageWidget
from automat.core.activity_log import search_events, get_recent_events


class SearchPage(PageWidget):
    def __init__(self, app):
        super().__init__(app)
        self.build()

    def build(self):
        tr = self.app.i18n.tr
        self.header("search", tr("search_title"), tr("search_subtitle"))

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(tr("search_placeholder"))
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setFixedHeight(36)
        self.search_input.textChanged.connect(self._on_search)
        self.content_layout.addWidget(self.search_input)

        self.result_tabs = QTabWidget()
        self.content_layout.addWidget(self.result_tabs, 1)

        self.pages_list = QListWidget()
        self.pages_list.itemDoubleClicked.connect(self._go_to_page)
        self.result_tabs.addTab(self.pages_list, tr("search_pages"))

        self.events_list = QListWidget()
        self.result_tabs.addTab(self.events_list, tr("search_events"))

        self.settings_list = QListWidget()
        self.result_tabs.addTab(self.settings_list, tr("search_settings"))

        self._all_pages = []
        self._build_page_index()

    def _build_page_index(self):
        tr = self.app.i18n.tr
        from automat.app import PAGES
        for icon, trans_key, key, cls in PAGES:
            if key and trans_key:
                label = tr(trans_key)
                self._all_pages.append((key, label.lower()))
                self.pages_list.addItem(f"{label}  [{key}]")

    def _on_search(self, query: str):
        q = query.strip().lower()
        self.pages_list.clear()
        self.events_list.clear()
        self.settings_list.clear()

        if not q:
            for key, label in self._all_pages:
                self.pages_list.addItem(f"{label}  [{key}]")
            return

        for key, label in self._all_pages:
            if q in label or q in key:
                self.pages_list.addItem(f"{label}  [{key}]")

        events = search_events(q, limit=30)
        if events:
            for ev in events:
                ico = {"convert": "\u2194", "send": "\u2191", "hash": "#",
                        "schedule": "\u29d6", "fileop": "\U0001f4c1",
                        "error": "\u2716"}.get(ev["event"], "\u25cf")
                ts = ev["ts"][11:16] if len(ev["ts"]) > 16 else ev["ts"]
                detail = ev["detail"][:60] or ev["event"]
                self.events_list.addItem(f"{ico} [{ev['status']}] {detail}  [{ts}]")

        tr = self.app.i18n.tr
        settings_keywords = {
            "theme": ("settings_theme", "page_settings"),
            "тема": ("settings_theme", "page_settings"),
            "language": ("settings_language", "page_settings"),
            "язык": ("settings_language", "page_settings"),
            "proxy": ("settings_proxy", "page_settings"),
            "прокси": ("settings_proxy", "page_settings"),
            "font": ("settings_font", "page_settings"),
            "шрифт": ("settings_font", "page_settings"),
        }
        for kw, (trans_key, page_key) in settings_keywords.items():
            if q in kw:
                self.settings_list.addItem(f"{tr(trans_key)}  [{page_key}]")

    def _go_to_page(self, item):
        text = item.text()
        if "[" in text:
            key = text.split("[")[-1].rstrip("]")
            self.app.show_page(key)
