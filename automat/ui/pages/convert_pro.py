"""
File conversion page — Excel↔PDF, PDF→Word, Images→PDF, CSV↔Excel.
Fixed: Worker pattern, confirmation dialog, thread-safety.
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os
from automat.config import ACCENT, GREEN, RED
from automat.ui.page_base import PageWidget
from automat.ui.widgets import LogPanel, ProgressBar, ValidatedLineEdit
from automat.core.activity_log import log, EVENT_CONVERT, STATUS_OK, STATUS_ERROR
from automat.core.worker import run_in_background

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

try:
    from openpyxl import load_workbook, Workbook
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

try:
    from pdf2docx import Converter
    HAS_PDF2DOCX = True
except ImportError:
    HAS_PDF2DOCX = False

try:
    from docx2pdf import convert as w2p
    HAS_DOCX2PDF = True
except ImportError:
    HAS_DOCX2PDF = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False


class ConvertProPage(PageWidget):
    def __init__(self, app):
        super().__init__(app)
        self.files = []
        self.stop_flag = False
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
        browse_out.setToolTip("Select input files")
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
        btn_tips = ["Add individual files", "Add all files from folder", "Clear file list"]
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
        convert_btn.setToolTip("Start conversion")
        convert_btn.clicked.connect(self._convert)
        btn_row2.addWidget(convert_btn)
        stop_btn = QPushButton("\u23f9 " + self.app.i18n.tr("bulk_stop"))
        stop_btn.setObjectName("danger")
        stop_btn.setToolTip("Stop conversion")
        stop_btn.clicked.connect(self._stop)
        btn_row2.addWidget(stop_btn)
        self.content_layout.addLayout(btn_row2)
        self.log_panel = LogPanel()
        self.content_layout.addWidget(self.log_panel)

    def _browse_out(self):
        d = QFileDialog.getExistingDirectory(self, "Output folder")
        if d:
            self.out_path.setText(d)

    def _add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select files")
        for f in files:
            self.files.append(f)
            self.file_list.addItem(os.path.basename(f))

    def _add_folder(self):
        d = QFileDialog.getExistingDirectory(self, "Folder with files")
        if d:
            for f in os.listdir(d):
                fp = os.path.join(d, f)
                if os.path.isfile(fp):
                    self.files.append(fp)
                    self.file_list.addItem(f)

    def _clear(self):
        self.files.clear()
        self.file_list.clear()

    def _convert(self):
        if not self.files:
            QMessageBox.warning(self, "Error", "No files selected")
            return
        if not self.out_path.text():
            QMessageBox.warning(self, "Error", "Select output folder")
            return
        # Confirmation dialog for batch operation
        reply = QMessageBox.question(
            self, "Confirm",
            f"Convert {len(self.files)} file(s)?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        self.stop_flag = False
        self.progress.setValue(0)
        run_in_background(
            self._run,
            on_result=self._on_done,
            on_error=lambda e: self.log_panel.write(f"\u2717 {e}", "err"),
        )

    def _stop(self):
        self.stop_flag = True
        self.log_panel.write("Stopping...", "warn")

    def _on_done(self, _):
        self.progress.setValue(100)

    def _run(self):
        from automat.util import safe
        out = self.out_path.text()
        conv = self.conv_type.currentText()
        total = len(self.files)
        for i, f in enumerate(self.files):
            if self.stop_flag:
                break
            safe(self.progress.setValue, int((i + 1) / total * 100))
            safe(self.log_panel.write, f"[{i+1}/{total}] {os.path.basename(f)}", "info")
            try:
                ext = os.path.splitext(f)[1].lower()
                name = os.path.splitext(os.path.basename(f))[0]
                dst = os.path.join(out, name)
                if "Excel \u2192 PDF" in conv and ext in (".xlsx", ".xls"):
                    if not HAS_OPENPYXL or not HAS_REPORTLAB:
                        safe(self.log_panel.write, "\u2717 install: pip install reportlab openpyxl", "err")
                        continue
                    wb = load_workbook(f)
                    ws = wb.active
                    cv = canvas.Canvas(dst + ".pdf", pagesize=A4)
                    y = 800
                    for row in ws.iter_rows(values_only=True):
                        cv.drawString(40, y, "  ".join(str(cell or "") for cell in row))
                        y -= 20
                    cv.save()
                elif "PDF \u2192 Word" in conv and ext == ".pdf":
                    if not HAS_PDF2DOCX:
                        safe(self.log_panel.write, "\u2717 install: pip install pdf2docx", "err")
                        continue
                    cv = Converter(f)
                    cv.convert(dst + ".docx")
                    cv.close()
                elif "Word \u2192 PDF" in conv and ext == ".docx":
                    if not HAS_DOCX2PDF:
                        safe(self.log_panel.write, "\u2717 install: pip install docx2pdf", "err")
                        continue
                    w2p(f, dst + ".pdf")
                elif "Images \u2192 PDF" in conv and ext in (".png", ".jpg", ".jpeg", ".bmp"):
                    if not HAS_PIL:
                        safe(self.log_panel.write, "\u2717 install: pip install Pillow", "err")
                        continue
                    img = Image.open(f).convert("RGB")
                    img.save(dst + ".pdf")
                elif "PDF \u2192 TXT" in conv and ext == ".pdf":
                    if not HAS_PDFPLUMBER:
                        safe(self.log_panel.write, "\u2717 install: pip install pdfplumber", "err")
                        continue
                    with pdfplumber.open(f) as pdf:
                        text = "\n".join(p.extract_text() or "" for p in pdf.pages)
                    with open(dst + ".txt", "w", encoding="utf-8") as tf:
                        tf.write(text)
                elif "CSV \u2192 Excel" in conv and ext == ".csv":
                    if not HAS_OPENPYXL:
                        safe(self.log_panel.write, "\u2717 install: pip install openpyxl", "err")
                        continue
                    wb = Workbook()
                    ws = wb.active
                    with open(f, encoding="utf-8") as cf:
                        for row in csv.reader(cf):
                            ws.append(row)
                    wb.save(dst + ".xlsx")
                elif "Excel \u2192 CSV" in conv and ext in (".xlsx", ".xls"):
                    if not HAS_OPENPYXL:
                        safe(self.log_panel.write, "\u2717 install: pip install openpyxl", "err")
                        continue
                    wb = load_workbook(f)
                    ws = wb.active
                    with open(dst + ".csv", "w", newline="", encoding="utf-8") as cf:
                        w = csv.writer(cf)
                        for row in ws.iter_rows(values_only=True):
                            w.writerow(row)
                safe(self.log_panel.write, f"\u2713 {os.path.basename(f)}", "ok")
                log(EVENT_CONVERT, STATUS_OK, conv, 1)
            except Exception as e:
                safe(self.log_panel.write, f"\u2717 {os.path.basename(f)}: {e}", "err")
                log(EVENT_CONVERT, STATUS_ERROR, str(e), 1)
