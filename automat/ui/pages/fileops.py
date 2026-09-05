"""
File Operations page — rename, archive, search, organize by type.
Fixed: undo support for rename and organize operations.
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os, shutil, fnmatch
from config import ACCENT, GREEN, RED
from ui.page_base import PageWidget
from ui.widgets import LogPanel
from core.activity_log import log, EVENT_FILEOP, STATUS_OK, STATUS_ERROR
from core.worker import run_in_background
from util import safe


class FileOpsPage(PageWidget):
    def __init__(self, app):
        super().__init__(app)
        self.tr = self.app.i18n.tr
        self._rename_history = []  # [(old_path, new_path), ...]
        self._organize_history = []  # [(src, dst), ...]
        self.build()

    def build(self):
        tr = self.tr
        self.header("fileops", tr("fileops_title"), tr("fileops_subtitle"))

        tabs = QTabWidget()
        self.content_layout.addWidget(tabs)
        self._build_rename(tabs)
        self._build_archive(tabs)
        self._build_search(tabs)
        self._build_organize(tabs)

    def _build_rename(self, tabs):
        tr = self.tr
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel(tr("fileops_folder")))
        self.ren_path = QLineEdit()
        self.ren_path.setPlaceholderText("Path to folder")
        l.addWidget(self.ren_path)
        browse_btn = QPushButton(tr("fileops_browse"))
        browse_btn.setToolTip("Browse...")
        browse_btn.clicked.connect(lambda: self.ren_path.setText(QFileDialog.getExistingDirectory()))
        l.addWidget(browse_btn)
        l.addWidget(QLabel(tr("fileops_mask")))
        self.ren_mask = QLineEdit("*.*")
        l.addWidget(self.ren_mask)
        l.addWidget(QLabel(tr("fileops_template")))
        self.ren_tpl = QLineEdit("file_{n}{ext}")
        l.addWidget(self.ren_tpl)
        self.ren_preview = QCheckBox(tr("fileops_preview"))
        self.ren_preview.setChecked(True)
        l.addWidget(self.ren_preview)

        btn_row = QHBoxLayout()
        run_btn = QPushButton(tr("fileops_run"))
        run_btn.setObjectName("accent")
        run_btn.setToolTip("Run rename operation")
        run_btn.clicked.connect(self._do_rename)
        btn_row.addWidget(run_btn)
        undo_btn = QPushButton("\u21a9 Undo Rename")
        undo_btn.clicked.connect(self._undo_rename)
        btn_row.addWidget(undo_btn)
        l.addLayout(btn_row)

        self.ren_log = QPlainTextEdit()
        self.ren_log.setReadOnly(True)
        l.addWidget(self.ren_log)
        tabs.addTab(w, tr("fileops_rename"))

    def _do_rename(self):
        tr = self.tr
        path = self.ren_path.text()
        mask = self.ren_mask.text()
        tpl = self.ren_tpl.text()
        preview = self.ren_preview.isChecked()
        if not os.path.isdir(path):
            QMessageBox.warning(self, tr("fileops_error"), tr("fileops_error_folder"))
            return

        if not preview:
            reply = QMessageBox.question(
                self, "Confirm Rename",
                "This will rename files. Continue?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return

        self.ren_log.clear()
        for f in os.listdir(path):
            if fnmatch.fnmatch(f, mask):
                name, ext = os.path.splitext(f)
                nname = tpl.replace("{n}", name).replace("{name}", name).replace("{ext}", ext)
                src = os.path.join(path, f)
                dst = os.path.join(path, nname)
                if preview:
                    self.ren_log.append(f"{f} -> {nname}")
                else:
                    os.rename(src, dst)
                    self._rename_history.append((dst, src))
                    self.ren_log.append(f"OK {f} -> {nname}")
        log(EVENT_FILEOP, STATUS_OK, "rename", 1)

    def _undo_rename(self):
        if not self._rename_history:
            QMessageBox.information(self, "Undo", "Nothing to undo.")
            return
        count = 0
        while self._rename_history:
            new_path, old_path = self._rename_history.pop()
            try:
                if os.path.exists(new_path):
                    os.rename(new_path, old_path)
                    count += 1
            except Exception as e:
                self.ren_log.append(f"Undo error: {e}")
        self.ren_log.append(f"OK Undone {count} renames")

    def _build_archive(self, tabs):
        tr = self.tr
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel(tr("fileops_source")))
        self.arc_src = QLineEdit()
        self.arc_src.setPlaceholderText("Source file path")
        l.addWidget(self.arc_src)
        browse1 = QPushButton(tr("fileops_browse"))
        browse1.setToolTip("Browse...")
        browse1.clicked.connect(lambda: self.arc_src.setText(QFileDialog.getExistingDirectory()))
        l.addWidget(browse1)
        l.addWidget(QLabel(tr("fileops_dest")))
        self.arc_dst = QLineEdit()
        self.arc_dst.setPlaceholderText("Archive output path (.zip)")
        l.addWidget(self.arc_dst)
        l.addWidget(QLabel(tr("fileops_format")))
        self.arc_fmt = QComboBox()
        self.arc_fmt.addItems(["zip", "tar", "gztar", "bztar"])
        l.addWidget(self.arc_fmt)
        row = QHBoxLayout()
        b1 = QPushButton(tr("fileops_archive_btn"))
        b1.setObjectName("accent")
        b1.setToolTip("Create archive")
        b1.clicked.connect(self._do_archive)
        b2 = QPushButton(tr("fileops_extract"))
        b2.setObjectName("accent2")
        b2.setToolTip("Extract archive")
        b2.clicked.connect(self._do_extract)
        row.addWidget(b1)
        row.addWidget(b2)
        l.addLayout(row)
        self.arc_log = QPlainTextEdit()
        self.arc_log.setReadOnly(True)
        l.addWidget(self.arc_log)
        tabs.addTab(w, tr("fileops_archive"))

    def _do_archive(self):
        src = self.arc_src.text()
        dst = self.arc_dst.text()
        fmt = self.arc_fmt.currentText()
        if not src or not dst:
            QMessageBox.warning(self, "Error", "Source and destination required")
            return
        reply = QMessageBox.question(
            self, "Confirm Archive",
            f"Create {fmt} archive from {src}?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        try:
            shutil.make_archive(dst, fmt, src)
            self.arc_log.append(f"OK Archived to {dst}.{fmt}")
        except Exception as e:
            self.arc_log.append(f"Error: {e}")

    def _do_extract(self):
        src = self.arc_src.text()
        dst = self.arc_dst.text()
        if not src or not dst:
            QMessageBox.warning(self, "Error", "Source and destination required")
            return
        try:
            shutil.unpack_archive(src, dst)
            self.arc_log.append(f"OK Extracted to {dst}")
        except Exception as e:
            self.arc_log.append(f"Error: {e}")

    def _build_search(self, tabs):
        tr = self.tr
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel(tr("fileops_folder")))
        self.srch_path = QLineEdit()
        self.srch_path.setPlaceholderText("Root folder to search")
        l.addWidget(self.srch_path)
        browse_btn = QPushButton(tr("fileops_browse"))
        browse_btn.setToolTip("Browse...")
        browse_btn.clicked.connect(lambda: self.srch_path.setText(QFileDialog.getExistingDirectory()))
        l.addWidget(browse_btn)
        l.addWidget(QLabel(tr("fileops_search_mask")))
        self.srch_mask = QLineEdit("*.*")
        l.addWidget(self.srch_mask)
        l.addWidget(QLabel(tr("fileops_search_text")))
        self.srch_text = QLineEdit()
        self.srch_text.setPlaceholderText("Filename or pattern")
        l.addWidget(self.srch_text)
        self.srch_recursive = QCheckBox(tr("fileops_recursive"))
        self.srch_recursive.setChecked(True)
        l.addWidget(self.srch_recursive)
        srch_btn = QPushButton(tr("fileops_search_btn"))
        srch_btn.setObjectName("accent")
        srch_btn.setToolTip("Search files")
        srch_btn.clicked.connect(self._do_search)
        l.addWidget(srch_btn)
        self.srch_results = QListWidget()
        l.addWidget(self.srch_results)
        tabs.addTab(w, tr("fileops_search"))

    def _do_search(self):
        tr = self.tr
        self.srch_results.clear()
        path = self.srch_path.text()
        mask = self.srch_mask.text()
        text = self.srch_text.text()
        recursive = self.srch_recursive.isChecked()
        count = 0
        for root, dirs, files in os.walk(path):
            if not recursive and root != path:
                continue
            for f in files:
                if fnmatch.fnmatch(f, mask):
                    fp = os.path.join(root, f)
                    if text:
                        try:
                            with open(fp, "r", encoding="utf-8", errors="ignore") as fh:
                                if text in fh.read():
                                    self.srch_results.addItem(fp)
                                    count += 1
                        except Exception:
                            pass
                    else:
                        self.srch_results.addItem(fp)
                        count += 1
        self.srch_results.addItem(tr("fileops_found").format(n=count))

    def _build_organize(self, tabs):
        tr = self.tr
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel(tr("fileops_folder_sort")))
        self.org_path = QLineEdit()
        self.org_path.setPlaceholderText("Folder to organize")
        l.addWidget(self.org_path)
        browse_btn = QPushButton(tr("fileops_browse"))
        browse_btn.setToolTip("Browse...")
        browse_btn.clicked.connect(lambda: self.org_path.setText(QFileDialog.getExistingDirectory()))
        l.addWidget(browse_btn)
        self.org_preview = QCheckBox(tr("fileops_preview"))
        self.org_preview.setChecked(True)
        l.addWidget(self.org_preview)

        btn_row = QHBoxLayout()
        org_btn = QPushButton(tr("fileops_sort_btn"))
        org_btn.setObjectName("accent")
        org_btn.setToolTip("Organize files by type")
        org_btn.clicked.connect(self._do_organize)
        btn_row.addWidget(org_btn)
        undo_btn = QPushButton("\u21a9 Undo Organize")
        undo_btn.clicked.connect(self._undo_organize)
        btn_row.addWidget(undo_btn)
        l.addLayout(btn_row)

        self.org_log = QPlainTextEdit()
        self.org_log.setReadOnly(True)
        l.addWidget(self.org_log)
        tabs.addTab(w, tr("fileops_organize"))

    def _do_organize(self):
        tr = self.tr
        path = self.org_path.text()
        preview = self.org_preview.isChecked()
        if not os.path.isdir(path):
            QMessageBox.warning(self, tr("fileops_error"), tr("fileops_error_folder"))
            return

        if not preview:
            reply = QMessageBox.question(
                self, "Confirm Organize",
                "This will move files into subfolders. Continue?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return

        categories = {
            "images": [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg"],
            "docs": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt"],
            "video": [".mp4", ".avi", ".mkv", ".mov", ".wmv"],
            "audio": [".mp3", ".wav", ".flac", ".aac"],
            "code": [".py", ".js", ".ts", ".html", ".css", ".cpp", ".h", ".java", ".sql"],
            "archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
        }
        self.org_log.clear()
        for f in os.listdir(path):
            fp = os.path.join(path, f)
            if not os.path.isfile(fp):
                continue
            ext = os.path.splitext(f)[1].lower()
            dest_dir = "other"
            for cat, exts in categories.items():
                if ext in exts:
                    dest_dir = cat
                    break
            dst = os.path.join(path, dest_dir)
            if preview:
                self.org_log.append(f"{f} -> {dest_dir}/")
            else:
                os.makedirs(dst, exist_ok=True)
                final_dst = os.path.join(dst, f)
                shutil.move(fp, final_dst)
                self._organize_history.append((final_dst, path))
                self.org_log.append(f"OK {f} -> {dest_dir}/")
        log(EVENT_FILEOP, STATUS_OK, "organize", 1)

    def _undo_organize(self):
        if not self._organize_history:
            QMessageBox.information(self, "Undo", "Nothing to undo.")
            return
        count = 0
        while self._organize_history:
            file_path, original_dir = self._organize_history.pop()
            try:
                if os.path.exists(file_path):
                    dst = os.path.join(original_dir, os.path.basename(file_path))
                    shutil.move(file_path, dst)
                    count += 1
            except Exception as e:
                self.org_log.append(f"Undo error: {e}")
        self.org_log.append(f"OK Undone {count} moves")
