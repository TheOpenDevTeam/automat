"""
Data Cleaner page — duplicates, spaces, phone normalization.
Fixed: undo/redo support via history stack.
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import csv, json, re
from automat.config import ACCENT, GREEN, RED
from automat.ui.page_base import PageWidget
from automat.ui.widgets import LogPanel, ProgressBar
from automat.core.activity_log import log, EVENT_CLEAN, STATUS_OK
from automat.core.worker import run_in_background
from automat.util import safe


class CleanDataPage(PageWidget):
    def __init__(self, app):
        super().__init__(app)
        self.data = []
        self.orig_data = []
        self._undo_stack = []
        self._redo_stack = []
        self.build()

    def _push_undo(self):
        """Save current data state to undo stack before modifying."""
        if self.data:
            self._undo_stack.append([dict(r) for r in self.data])
            self._redo_stack.clear()
            if len(self._undo_stack) > 50:
                self._undo_stack.pop(0)

    def _undo(self):
        if not self._undo_stack:
            return
        self._redo_stack.append([dict(r) for r in self.data])
        self.data = self._undo_stack.pop()
        self._show_preview(self.data)
        self.log_panel.write(f"↩ Undo: {len(self.data)} rows", "info")

    def _redo(self):
        if not self._redo_stack:
            return
        self._undo_stack.append([dict(r) for r in self.data])
        self.data = self._redo_stack.pop()
        self._show_preview(self.data)
        self.log_panel.write(f"↪ Redo: {len(self.data)} rows", "info")

    def build(self):
        tr = self.app.i18n.tr
        self.header("cleandata", tr("cleandata_title"), tr("cleandata_subtitle"))

        outer = QHBoxLayout()
        self.content_layout.addLayout(outer)

        left, inner_left, ll = self.card(tr("cleandata_ops_card"))
        outer.addWidget(left)
        load_btn = QPushButton(tr("cleandata_load_btn"))
        load_btn.setObjectName("accent")
        load_btn.clicked.connect(self._load)
        ll.addWidget(load_btn)

        undo_redo_row = QHBoxLayout()
        undo_btn = QPushButton("\u21a9 Undo")
        undo_btn.clicked.connect(self._undo)
        undo_redo_row.addWidget(undo_btn)
        redo_btn = QPushButton("\u21aa Redo")
        redo_btn.clicked.connect(self._redo)
        undo_redo_row.addWidget(redo_btn)
        ll.addLayout(undo_redo_row)

        self.ops = {}
        for key in ["cleandata_rm_duplicates", "cleandata_rm_empty", "cleandata_trim",
                     "cleandata_email_lower", "cleandata_normalize_phones"]:
            cb = QCheckBox(tr(key))
            cb.setChecked(True)
            self.ops[key] = cb
            ll.addWidget(cb)
        clean_btn = QPushButton(tr("cleandata_clean_btn"))
        clean_btn.setObjectName("success")
        clean_btn.clicked.connect(self._clean)
        ll.addWidget(clean_btn)
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setObjectName("card_separator")
        ll.addWidget(sep2)
        for key, fn in [("cleandata_del_col", self._del_col),
                         ("cleandata_sort_col", self._sort_col)]:
            b = QPushButton(tr(key))
            b.setObjectName("accent2")
            b.clicked.connect(fn)
            ll.addWidget(b)
        self.progress = ProgressBar()
        ll.addWidget(self.progress)
        self.log_panel = LogPanel()
        ll.addWidget(self.log_panel)

        right, inner_right, rl = self.card(tr("cleandata_result_card"))
        outer.addWidget(right, 1)
        self.preview = QTableWidget()
        rl.addWidget(self.preview)
        save_row = QHBoxLayout()
        for fmt in ["CSV", "JSON"]:
            b = QPushButton(tr("cleandata_save_fmt", fmt=fmt))
            b.clicked.connect(lambda checked, f=fmt: self._save(f))
            save_row.addWidget(b)
        rl.addLayout(save_row)

    def _load(self):
        fp, _ = QFileDialog.getOpenFileName(self, "CSV/JSON", "", "CSV (*.csv);;JSON (*.json)")
        if not fp:
            return
        try:
            if fp.endswith(".csv"):
                with open(fp, encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    self.data = list(reader)
            else:
                with open(fp, encoding="utf-8") as f:
                    self.data = json.load(f)
            self.orig_data = [dict(r) for r in self.data]
            self._undo_stack.clear()
            self._redo_stack.clear()
            self._show_preview(self.data)
            self.log_panel.write(f"OK Loaded {len(self.data)} rows", "ok")
        except Exception as e:
            QMessageBox.critical(self, self.app.i18n.tr("cleandata_error"), str(e))

    def _show_preview(self, data):
        if not data:
            return
        headers = list(data[0].keys())
        self.preview.setColumnCount(len(headers))
        self.preview.setHorizontalHeaderLabels(headers)
        self.preview.setRowCount(min(len(data), 100))
        for i, row in enumerate(data[:100]):
            for j, h in enumerate(headers):
                self.preview.setItem(i, j, QTableWidgetItem(str(row.get(h, ""))))

    def _clean(self):
        if not self.data:
            QMessageBox.warning(self, self.app.i18n.tr("cleandata_error"),
                                self.app.i18n.tr("cleandata_load_data_first"))
            return
        self._push_undo()
        run_in_background(
            self._run,
            on_result=self._show_result,
            on_error=lambda e: self.log_panel.write(f"Error: {e}", "err"),
        )

    def _run(self):
        data = [dict(r) for r in self.data]
        steps = [k for k, v in self.ops.items() if v.isChecked()]
        total_steps = len(steps)

        for idx, key in enumerate(steps):
            before = len(data)
            if key == "cleandata_rm_duplicates":
                seen = set()
                new = []
                for r in data:
                    t = tuple(r.items())
                    if t not in seen:
                        seen.add(t)
                        new.append(r)
                data = new
                safe(self.log_panel.write, f"OK Duplicates removed: {before - len(data)}", "ok")
            elif key == "cleandata_rm_empty":
                data = [r for r in data if any(
                    str(v).strip() for v in r.values()
                )]
                safe(self.log_panel.write, f"OK Empty rows removed: -{before - len(data)}", "ok")
            elif key == "cleandata_trim":
                for r in data:
                    for k, v in r.items():
                        if isinstance(v, str):
                            r[k] = v.strip()
            elif key == "cleandata_email_lower":
                for r in data:
                    for k in r:
                        if "email" in k.lower():
                            r[k] = r[k].lower()
            elif key == "cleandata_normalize_phones":
                for r in data:
                    for k in r:
                        if any(w in k.lower() for w in ["phone", "tel", "mobile", "telephone"]):
                            num = re.sub(r"\D", "", str(r[k]))
                            if len(num) == 10:
                                r[k] = f"+7{num}"
                            elif len(num) == 11:
                                r[k] = f"+7{num[1:]}"
                            elif len(num) == 7:
                                r[k] = f"+7495{num}"
            safe(self.progress.setValue, int((idx + 1) / total_steps * 100) if total_steps > 0 else 0)

        self.data = data
        log(EVENT_CLEAN, STATUS_OK, f"{len(data)} rows", len(data))
        return len(data)

    def _show_result(self, count):
        self._show_preview(self.data)
        self.log_panel.write(f"OK Done: {len(self.orig_data)} -> {count} rows", "ok")

    def _save(self, fmt):
        if not self.data:
            return
        fp, _ = QFileDialog.getSaveFileName(self, self.app.i18n.tr("cleandata_save_dialog"),
                                             "", f"{fmt} (*.{fmt.lower()})")
        if fp:
            try:
                if fmt == "CSV":
                    with open(fp, "w", newline="", encoding="utf-8") as f:
                        w = csv.DictWriter(f, fieldnames=self.data[0].keys())
                        w.writeheader()
                        w.writerows(self.data)
                else:
                    with open(fp, "w", encoding="utf-8") as f:
                        json.dump(self.data, f, ensure_ascii=False, indent=2)
                self.log_panel.write(f"OK Saved: {fp}", "ok")
            except Exception as e:
                self.log_panel.write(f"Error: {e}", "err")

    def _del_col(self):
        if not self.data:
            QMessageBox.warning(self, self.app.i18n.tr("cleandata_error"),
                                self.app.i18n.tr("cleandata_load_data_first"))
            return
        col, ok = QInputDialog.getItem(self, self.app.i18n.tr("cleandata_del_col_title"),
                                        self.app.i18n.tr("cleandata_del_col_label"),
                                        list(self.data[0].keys()), False)
        if ok and col:
            self._push_undo()
            for r in self.data:
                r.pop(col, None)
            self._show_preview(self.data)
            self.log_panel.write(f"OK Column '{col}' deleted", "ok")

    def _sort_col(self):
        if not self.data:
            QMessageBox.warning(self, self.app.i18n.tr("cleandata_error"),
                                self.app.i18n.tr("cleandata_load_data_first"))
            return
        col, ok = QInputDialog.getItem(self, self.app.i18n.tr("cleandata_sort_title"),
                                        self.app.i18n.tr("cleandata_sort_label"),
                                        list(self.data[0].keys()), False)
        if ok and col:
            self._push_undo()
            self.data.sort(key=lambda r: str(r.get(col, "")))
            self._show_preview(self.data)
            self.log_panel.write(f"OK Sorted by '{col}'", "ok")
