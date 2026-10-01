"""Operation history page — timeline with filtering, pagination and export."""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os
from automat.config import DATA_DIR
from automat.ui.page_base import PageWidget
from automat.core.activity_log import (
    get_all_events_paginated, get_event_stats_by_type,
    export_csv, export_json, clear_all_events,
    get_totals, EVENT_CONVERT, EVENT_SEND, EVENT_HASH,
    EVENT_SCHEDULE, EVENT_FILEOP, EVENT_CLEAN, EVENT_DATAGEN, EVENT_TEXT,
)
from automat.core.worker import run_in_background

EVENT_ICONS = {
    "convert": "\u2194", "send": "\u2191", "hash": "#",
    "schedule": "\u29d6", "fileop": "\U0001f4c1",
    "clean": "\U0001f9f9", "datagen": "\u2699", "text": "\U0001f4dd",
}

EVENT_KEYS = {
    "convert": "history_convert", "send": "history_send",
    "hash": "history_hash", "schedule": "history_schedule",
    "fileop": "history_fileop", "clean": "history_clean",
    "datagen": "history_datagen", "text": "history_text",
}

PAGE_SIZE = 50


class HistoryPage(PageWidget):
    def __init__(self, app):
        super().__init__(app)
        self._page = 0
        self._total_count = 0
        self._current_filter = None
        self.build()
        self._load_stats()
        self._load_page()

    def build(self):
        tr = self.app.i18n.tr
        self.header("history", tr("history_title"), tr("history_subtitle"))

        toolbar = QHBoxLayout()

        filter_label = QLabel(tr("history_filter"))
        toolbar.addWidget(filter_label)

        self.filter_combo = QComboBox()
        self.filter_combo.addItem(tr("history_all"), None)
        for ev_key, i18n_key in EVENT_KEYS.items():
            self.filter_combo.addItem(tr(i18n_key), ev_key)
        self.filter_combo.currentIndexChanged.connect(self._on_filter_changed)
        self.filter_combo.setFixedWidth(160)
        toolbar.addWidget(self.filter_combo)

        toolbar.addStretch()

        self.stats_label = QLabel("")
        self.stats_label.setObjectName("text_muted")
        toolbar.addWidget(self.stats_label)

        self.export_csv_btn = QPushButton(tr("history_export_csv"))
        self.export_csv_btn.clicked.connect(self._export_csv)
        toolbar.addWidget(self.export_csv_btn)

        self.export_json_btn = QPushButton(tr("history_export_json"))
        self.export_json_btn.clicked.connect(self._export_json)
        toolbar.addWidget(self.export_json_btn)

        self.clear_btn = QPushButton(tr("history_clear"))
        self.clear_btn.setObjectName("danger")
        self.clear_btn.clicked.connect(self._clear_history)
        toolbar.addWidget(self.clear_btn)

        self.content_layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            tr("history_id"), tr("history_event"),
            tr("history_status"), tr("history_detail"), tr("history_time")
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setSortingEnabled(False)
        self.content_layout.addWidget(self.table, 1)

        nav = QHBoxLayout()
        self.prev_btn = QPushButton("\u25c0")
        self.prev_btn.setFixedSize(30, 30)
        self.prev_btn.clicked.connect(self._prev_page)
        nav.addWidget(self.prev_btn)

        self.page_label = QLabel("")
        self.page_label.setAlignment(Qt.AlignCenter)
        nav.addWidget(self.page_label)

        self.next_btn = QPushButton("\u25b6")
        self.next_btn.setFixedSize(30, 30)
        self.next_btn.clicked.connect(self._next_page)
        nav.addWidget(self.next_btn)

        nav.addStretch()
        self.content_layout.addLayout(nav)

    def _on_filter_changed(self, idx):
        self._current_filter = self.filter_combo.currentData()
        self._page = 0
        self._load_page()

    def _load_page(self):
        offset = self._page * PAGE_SIZE
        run_in_background(
            get_all_events_paginated,
            offset, PAGE_SIZE, self._current_filter,
            on_result=self._apply_page,
        )

    def _apply_page(self, events):
        tr = self.app.i18n.tr
        self.table.setRowCount(len(events))

        for i, ev in enumerate(events):
            ico = EVENT_ICONS.get(ev["event"], "\u25cf")
            i18n_key = EVENT_KEYS.get(ev["event"])
            event_label = tr(i18n_key) if i18n_key else ev["event"]

            self.table.setItem(i, 0, QTableWidgetItem(str(ev["id"])))

            event_item = QTableWidgetItem(f"{ico} {event_label}")
            self.table.setItem(i, 1, event_item)

            status_item = QTableWidgetItem(ev["status"])
            self.table.setItem(i, 2, status_item)

            detail = ev["detail"][:80] if ev["detail"] else ""
            self.table.setItem(i, 3, QTableWidgetItem(detail))

            ts_short = ev["ts"][11:19] if len(ev["ts"]) > 16 else ev["ts"]
            self.table.setItem(i, 4, QTableWidgetItem(ts_short))

        self.table.resizeColumnsToContents()
        self.table.setColumnWidth(1, 180)
        self.table.setColumnWidth(3, 300)

        self.prev_btn.setEnabled(self._page > 0)
        total_pages = max(1, (self._total_count + PAGE_SIZE - 1) // PAGE_SIZE)
        self.next_btn.setEnabled(self._page < total_pages - 1)
        self.page_label.setText(tr("history_page", current=self._page + 1, total=total_pages))

    def _load_stats(self):
        run_in_background(get_totals, on_result=self._apply_stats)

    def _apply_stats(self, totals):
        tr = self.app.i18n.tr
        total = sum(totals.values())
        self.stats_label.setText(tr("history_total", n=total))
        self._total_count = total

    def _prev_page(self):
        if self._page > 0:
            self._page -= 1
            self._load_page()

    def _next_page(self):
        self._page += 1
        self._load_page()

    def _export_csv(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", str(DATA_DIR / "activity_export.csv"),
            "CSV Files (*.csv)")
        if filepath:
            run_in_background(export_csv, filepath, on_result=lambda ok: self._on_export(ok, filepath))

    def _export_json(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export JSON", str(DATA_DIR / "activity_export.json"),
            "JSON Files (*.json)")
        if filepath:
            run_in_background(export_json, filepath, on_result=lambda ok: self._on_export(ok, filepath))

    def _on_export(self, ok, filepath):
        if ok:
            tr = self.app.i18n.tr
            msg = tr("history_exported", path=os.path.basename(filepath))
            if hasattr(self.app, 'toast'):
                self.app.toast(msg, GREEN)
            self._load_stats()
            self._load_page()

    def _clear_history(self):
        tr = self.app.i18n.tr
        reply = QMessageBox.question(
            self, tr("history_clear"), tr("history_clear_confirm"),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            run_in_background(clear_all_events, on_result=self._on_clear)

    def _on_clear(self, ok):
        if ok:
            tr = self.app.i18n.tr
            if hasattr(self.app, 'toast'):
                self.app.toast(tr("history_cleared"), GREEN)
            self._page = 0
            self._load_stats()
            self._load_page()
