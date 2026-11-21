"""
File conversion page — UI layer only.
Business logic lives in automat.core.converter.Converter.
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os
from automat.config import APP_NAME
from automat.ui.page_base import PageWidget
from automat.ui.widgets import LogPanel, ProgressBar, ValidatedLineEdit
from automat.core.activity_log import log, EVENT_CONVERT, STATUS_OK, STATUS_ERROR
from automat.core.worker import run_in_background
from automat.core.converter import Converter


class ConvertProPage(PageWidget):
    def __init__(self, app):
        super().__init__(app)
        self.files = []
        self.stop_flag = False
        self.converter = Converter()
        self.build()

    def build(self):
        tr = self.app.i18n.tr
        self.header("convert", tr("convert_title"), tr("convert_subtitle"))

        outer = QHBoxLayout()
        self.content_layout.addLayout(outer)

        left, inner_left, ll = self.card(tr("convert_type_card"))
        left.setMinimumWidth(220)
        outer.addWidget(left)
        self.conv_type = QComboBox()
        self.conv_type.addItems([
            "Excel \u2192 PDF", "PDF \u2192 Word", "Word \u2192 PDF",
            "Images \u2192 PDF", "PDF \u2192 TXT", "CSV \u2192 Excel",
            "Excel \u2192 CSV",
        ])
        self.conv_type.setMinimumWidth(200)
        ll.addWidget(self.conv_type)
        ll.addWidget(QLabel(tr("convert_out_folder")))
        self.out_path = ValidatedLineEdit(placeholder=tr("convert_out_placeholder"))
        self.out_path.set_validator_fn(lambda p: os.path.isdir(p) if p else False)
        ll.addWidget(self.out_path)
        browse_out = QPushButton(tr("convert_browse"))
        browse_out.setObjectName("accent")
        browse_out.setToolTip(tr("convert_browse_out_tip"))
        browse_out.clicked.connect(self._browse_out)
        ll.addWidget(browse_out)
        self.overwrite = QCheckBox(tr("convert_overwrite"))
        self.overwrite.setChecked(True)
        ll.addWidget(self.overwrite)
        self.progress = ProgressBar()
        ll.addWidget(self.progress)

        right, inner_right, rl = self.card(tr("convert_files_card"))
        outer.addWidget(right, 1)
        self.file_list = QListWidget()
        rl.addWidget(self.file_list)
        btn_row = QHBoxLayout()
        btn_tips = [tr("convert_add_tip"), tr("convert_add_folder_tip"), tr("convert_clear_tip")]
        for (txt, fn), tip in zip([
            (tr("convert_add"), self._add_files),
            (tr("convert_add_folder"), self._add_folder),
            (tr("convert_clear"), self._clear),
        ], btn_tips):
            b = QPushButton(txt)
            b.setToolTip(tip)
            b.clicked.connect(fn)
            btn_row.addWidget(b)
        rl.addLayout(btn_row)

        btn_row2 = QHBoxLayout()
        convert_btn = QPushButton(tr("convert_convert_btn"))
        convert_btn.setObjectName("accent")
        convert_btn.setToolTip(tr("convert_run_tip"))
        convert_btn.clicked.connect(self._convert)
        btn_row2.addWidget(convert_btn)
        stop_btn = QPushButton("\u23f9 " + self.app.i18n.tr("bulk_stop"))
        stop_btn.setObjectName("danger")
        stop_btn.setToolTip(tr("convert_stop_tip"))
        stop_btn.clicked.connect(self._stop)
        btn_row2.addWidget(stop_btn)
        self.content_layout.addLayout(btn_row2)
        self.log_panel = LogPanel()
        self.content_layout.addWidget(self.log_panel)

    def _browse_out(self):
        d = QFileDialog.getExistingDirectory(self, self.app.i18n.tr("convert_out_folder"))
        if d:
            self.out_path.setText(d)

    def _add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, self.app.i18n.tr("convert_add"))
        self._add_paths(files)

    def _add_paths(self, paths):
        added = 0
        for f in paths:
            if os.path.isfile(f) and f not in self.files:
                self.files.append(f)
                self.file_list.addItem(os.path.basename(f))
                added += 1
        if added and hasattr(self.app, "toast"):
            self.app.toast(f"+{added}")

    def accept_dropped_paths(self, paths):
        self._add_paths(paths)

    def _add_folder(self):
        d = QFileDialog.getExistingDirectory(self, self.app.i18n.tr("convert_add_folder"))
        if d:
            self._add_paths([os.path.join(d, f) for f in os.listdir(d)])

    def _clear(self):
        self.files.clear()
        self.file_list.clear()

    def _convert(self):
        if not self.files:
            QMessageBox.warning(self, APP_NAME, self.app.i18n.tr("convert_no_files"))
            return
        if not self.out_path.text():
            QMessageBox.warning(self, APP_NAME, self.app.i18n.tr("convert_no_out"))
            return
        reply = QMessageBox.question(
            self, APP_NAME,
            self.app.i18n.tr("convert_confirm", n=len(self.files)),
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        self.stop_flag = False
        self.converter.stop_flag = False
        self.progress.setValue(0)
        run_in_background(
            self._run,
            on_result=self._on_done,
            on_error=lambda e: self.log_panel.write(f"\u2717 {e}", "err"),
        )

    def _stop(self):
        self.stop_flag = True
        self.converter.stop()
        self.log_panel.write(self.app.i18n.tr("convert_stopping"), "warn")

    def _on_done(self, _):
        self.progress.setValue(100)

    def _run(self):
        from automat.util import safe
        tr = self.app.i18n.tr
        out = self.out_path.text()
        conv = self.conv_type.currentText()

        def on_progress(pct):
            safe(self.progress.setValue, int(pct))

        def on_log(msg, tag):
            safe(self.log_panel.write, msg, tag)

        def on_error(msg):
            safe(self.log_panel.write, f"\u2717 {msg}", "err")

        results = self.converter.convert_files(
            self.files, conv, out,
            on_progress=on_progress,
            on_log=on_log,
            on_error=on_error,
        )

        for r in results:
            if r.ok:
                log(EVENT_CONVERT, STATUS_OK, conv, 1)
            else:
                log(EVENT_CONVERT, STATUS_ERROR, r.error or "", 1)
