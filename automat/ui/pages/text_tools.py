"""
Text Tools page — UI layer only.
Business logic lives in automat.core.text_processor.TextProcessor.
"""

import os

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from automat.ui.page_base import PageWidget
from automat.core.activity_log import log, EVENT_TEXT, STATUS_OK
from automat.core.text_processor import TextProcessor

# Read at most this much of a dropped file so a huge log can't freeze the GUI.
DROP_READ_LIMIT = 5 * 1024 * 1024

# Warn above this size when loading a file into the editor.
LARGE_FILE_WARN = 50 * 1024 * 1024  # 50 MB


class TextToolsPage(PageWidget):
    """Text editor with transformations, search/replace, stats, and regex tester."""

    def __init__(self, app):
        super().__init__(app)
        self.processor = TextProcessor()
        self.build()

    def build(self):
        tr = lambda k: self.app.i18n.tr(k)
        self.header("text", tr("text_title"), tr("text_subtitle"))

        tabs = QTabWidget()
        self.content_layout.addWidget(tabs)
        self._build_editor(tabs)
        self._build_regex(tabs)

    # ------------------------------------------------------------------
    # Editor tab — transform, find/replace, stats
    # ------------------------------------------------------------------

    def _build_editor(self, tabs):
        tr = self.app.i18n.tr
        w = QWidget()
        outer = QHBoxLayout(w)

        left, inner_left, ll = self.card(tr("text_tools_card"))
        outer.addWidget(left)

        tool_bar = QHBoxLayout()
        tooltips = [
            "Convert to UPPERCASE", "Convert to lowercase",
            "Convert to Title Case", "Remove leading/trailing whitespace",
            "Sort lines ascending", "Sort lines descending",
            "Remove duplicate lines", "Reverse line order",
        ]
        for (txt, fn), tip in zip([
            ("UPPER", lambda: self._apply_transform(str.upper)),
            ("lower", lambda: self._apply_transform(str.lower)),
            ("Title", lambda: self._apply_transform(str.title)),
            ("Strip", lambda: self._apply_transform(str.strip)),
            ("Sort\u2191", lambda: self._sort_lines(True)),
            ("Sort\u2193", lambda: self._sort_lines(False)),
            ("Dedup", self._dedup_lines),
            ("Reverse", self._reverse_text),
        ], tooltips):
            b = QPushButton(txt)
            b.setMinimumWidth(52)
            b.setToolTip(tip)
            b.clicked.connect(fn)
            tool_bar.addWidget(b)

        undo_btn = QPushButton("\u21a9")
        undo_btn.setFixedWidth(36)
        undo_btn.setToolTip("Ctrl+Z")
        undo_btn.clicked.connect(self.editor.undo if hasattr(self, 'editor') else lambda: None)
        tool_bar.addWidget(undo_btn)
        redo_btn = QPushButton("\u21aa")
        redo_btn.setFixedWidth(36)
        redo_btn.setToolTip("Ctrl+Y")
        redo_btn.clicked.connect(self.editor.redo if hasattr(self, 'editor') else lambda: None)
        tool_bar.addWidget(redo_btn)

        ll.addLayout(tool_bar)

        ll.addWidget(QLabel(tr("text_find_label")))
        find_row = QHBoxLayout()
        self.find_text = QLineEdit()
        self.find_text.setPlaceholderText(tr("text_find_placeholder"))
        find_row.addWidget(self.find_text)
        self.regex_cb = QCheckBox(tr("text_regex"))
        find_row.addWidget(self.regex_cb)
        find_btn = QPushButton("\U0001f50d")
        find_btn.setToolTip(tr("text_find_replace_tip"))
        find_btn.clicked.connect(self._find)
        find_row.addWidget(find_btn)
        replace_btn = QPushButton(tr("text_replace_all"))
        replace_btn.setObjectName("accent")
        replace_btn.clicked.connect(self._replace)
        find_row.addWidget(replace_btn)
        ll.addLayout(find_row)

        self.replace_text = QLineEdit()
        self.replace_text.setPlaceholderText(tr("text_replace_placeholder"))
        ll.addWidget(self.replace_text)

        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText(tr("text_editor_ph"))
        self.editor.setObjectName("text_editor")
        self.editor.setTabStopDistance(
            QFontMetricsF(self.editor.font()).horizontalAdvance(' ') * 4
        )
        self.editor.textChanged.connect(self._update_stats)
        ll.addWidget(self.editor, 1)

        # Wire undo/redo buttons now that editor exists
        undo_btn.clicked.disconnect()
        undo_btn.clicked.connect(self.editor.undo)
        redo_btn.clicked.disconnect()
        redo_btn.clicked.connect(self.editor.redo)

        # Right panel: statistics
        right, inner_right, rl = self.card(tr("text_stats_card"))
        outer.addWidget(right)
        self.stats_labels = {}
        stats_config = [
            ("Chars", tr("text_chars_label")),
            ("Words", tr("text_words_label")),
            ("Lines", tr("text_lines_label")),
            ("Unique words", tr("text_unique_words_label")),
        ]
        for key, label_text in stats_config:
            lbl = QLabel(f"{label_text}: 0")
            lbl.setObjectName("stat_label_mono")
            rl.addWidget(lbl)
            self.stats_labels[key] = lbl

        rl.addWidget(QLabel(tr("text_top_words")))
        self.word_stats = QListWidget()
        rl.addWidget(self.word_stats)

        load_btn = QPushButton(tr("text_load"))
        load_btn.setToolTip(tr("text_load"))
        load_btn.clicked.connect(self._load_file)
        rl.addWidget(load_btn)
        save_btn = QPushButton(tr("text_save"))
        save_btn.setToolTip(tr("text_save"))
        save_btn.clicked.connect(self._save_file)
        rl.addWidget(save_btn)

        tabs.addTab(w, tr("text_editor_tab"))

    # ------------------------------------------------------------------
    # Text transformations (delegated to TextProcessor)
    # ------------------------------------------------------------------

    def _replace_content(self, new_text: str):
        """Replace all editor content while preserving undo history."""
        cursor = self.editor.textCursor()
        cursor.beginEditBlock()
        cursor.select(QTextCursor.Document)
        cursor.insertText(new_text)
        cursor.endEditBlock()

    def _apply_transform(self, func):
        text = self.editor.toPlainText()
        self._replace_content(self.processor.transform(text, func))

    def _sort_lines(self, asc):
        text = self.editor.toPlainText()
        self._replace_content(self.processor.sort_lines(text, asc))

    def _dedup_lines(self):
        text = self.editor.toPlainText()
        self._replace_content(self.processor.dedup_lines(text))

    def _reverse_text(self):
        text = self.editor.toPlainText()
        self._replace_content(self.processor.reverse_text(text))

    # ------------------------------------------------------------------
    # Find / Replace
    # ------------------------------------------------------------------

    def _find(self):
        text = self.find_text.text()
        if not text:
            return
        content = self.editor.toPlainText()
        result = self.processor.find(
            content, text,
            regex=self.regex_cb.isChecked(),
            ignore_case=not self.regex_cb.isChecked(),
        )
        self.editor.setExtraSelections([])
        if result.count == 0:
            return
        selections = []
        for start, end in result.matches:
            sel = QTextEdit.ExtraSelection()
            sel.cursor = self.editor.textCursor()
            sel.cursor.setPosition(start)
            sel.cursor.setPosition(end, QTextCursor.KeepAnchor)
            sel.format.setBackground(QColor(80, 130, 220, 60))
            selections.append(sel)
        self.editor.setExtraSelections(selections)

    def _replace(self):
        find_text = self.find_text.text()
        replace_text = self.replace_text.text()
        if not find_text:
            return
        content = self.editor.toPlainText()
        result = self.processor.replace(
            content, find_text, replace_text,
            regex=self.regex_cb.isChecked(),
            ignore_case=not self.regex_cb.isChecked(),
        )
        self._replace_content(result)

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def _update_stats(self):
        text = self.editor.toPlainText()
        stats = self.processor.stats(text)
        tr = self.app.i18n.tr
        self.stats_labels["Chars"].setText(f"{tr('text_chars_label')}: {stats.chars}")
        self.stats_labels["Words"].setText(f"{tr('text_words_label')}: {stats.words}")
        self.stats_labels["Lines"].setText(f"{tr('text_lines_label')}: {stats.lines}")
        self.stats_labels["Unique words"].setText(f"{tr('text_unique_words_label')}: {stats.unique_words}")
        self.word_stats.clear()
        for word, count in stats.top_words:
            self.word_stats.addItem(f"{word}: {count}")

    # ------------------------------------------------------------------
    # File load / save
    # ------------------------------------------------------------------

    def _load_file(self):
        fp, _ = QFileDialog.getOpenFileName(
            self, self.app.i18n.tr("text_load"), "",
            "Text (*.txt);;All files (*.*)")
        if fp:
            self._load_path(fp)

    def _load_path(self, fp):
        try:
            file_size = os.path.getsize(fp)
            if file_size > LARGE_FILE_WARN:
                from PyQt5.QtWidgets import QMessageBox
                reply = QMessageBox.warning(
                    self, self.app.i18n.tr("common_error"),
                    f"File is {file_size / 1024 / 1024:.1f} MB. "
                    f"Only the first {DROP_READ_LIMIT / 1024 / 1024:.0f} MB will be loaded. Continue?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )
                if reply != QMessageBox.Yes:
                    return False
            with open(fp, encoding="utf-8", errors="ignore") as f:
                self._replace_content(f.read(DROP_READ_LIMIT))
            log(EVENT_TEXT, STATUS_OK, fp, 1)
            return True
        except Exception as e:
            QMessageBox.warning(self, self.app.i18n.tr("common_error"), str(e))
            return False

    def accept_dropped_paths(self, paths):
        loaded = 0
        for p in paths:
            if os.path.isfile(p) and self._load_path(p):
                loaded += 1
                break  # the editor holds a single document
        if loaded and hasattr(self.app, "toast"):
            self.app.toast(f"+1")

    def _save_file(self):
        fp, _ = QFileDialog.getSaveFileName(
            self, self.app.i18n.tr("text_save"), "",
            "Text (*.txt);;All files (*.*)")
        if fp:
            try:
                with open(fp, "w", encoding="utf-8") as f:
                    f.write(self.editor.toPlainText())
            except Exception as e:
                QMessageBox.warning(self, self.app.i18n.tr("common_error"), str(e))

    # ------------------------------------------------------------------
    # Regex Tester tab
    # ------------------------------------------------------------------

    def _build_regex(self, tabs):
        tr = self.app.i18n.tr
        w = QWidget()
        l = QVBoxLayout(w)

        l.addWidget(QLabel(tr("text_pattern_label")))
        pattern_row = QHBoxLayout()
        self.regex_pattern = QLineEdit()
        self.regex_pattern.setPlaceholderText(r"\b\w+@\w+\.\w+\b")
        self.regex_pattern.textChanged.connect(self._run_regex)
        pattern_row.addWidget(self.regex_pattern, 1)

        self.flag_ignorecase = QCheckBox(tr("text_flag_ignorecase"))
        self.flag_ignorecase.toggled.connect(self._run_regex)
        pattern_row.addWidget(self.flag_ignorecase)
        self.flag_multiline = QCheckBox(tr("text_flag_multiline"))
        self.flag_multiline.toggled.connect(self._run_regex)
        pattern_row.addWidget(self.flag_multiline)
        self.flag_dotall = QCheckBox(tr("text_flag_dotall"))
        self.flag_dotall.toggled.connect(self._run_regex)
        pattern_row.addWidget(self.flag_dotall)
        l.addLayout(pattern_row)

        info_row = QHBoxLayout()
        self.regex_status = QLabel(tr("text_pattern_prompt"))
        self.regex_status.setObjectName("regex_status")
        info_row.addWidget(self.regex_status, 1)
        self.match_count = QLabel(tr("text_matches_label"))
        self.match_count.setObjectName("match_count")
        info_row.addWidget(self.match_count)
        l.addLayout(info_row)

        l.addWidget(QLabel(tr("text_test_string_label")))
        self.regex_input = QPlainTextEdit()
        self.regex_input.setPlaceholderText(tr("text_test_placeholder"))
        self.regex_input.textChanged.connect(self._run_regex)
        l.addWidget(self.regex_input, 1)

        l.addWidget(QLabel(tr("text_results_label")))
        self.regex_output = QPlainTextEdit()
        self.regex_output.setReadOnly(True)
        l.addWidget(self.regex_output, 1)

        tabs.addTab(w, tr("text_regex_tab"))

    def _run_regex(self):
        tr = self.app.i18n.tr
        pattern = self.regex_pattern.text()
        test_text = self.regex_input.toPlainText()
        self.regex_output.clear()

        flags = 0
        if self.flag_ignorecase.isChecked():
            flags |= re.IGNORECASE
        if self.flag_multiline.isChecked():
            flags |= re.MULTILINE
        if self.flag_dotall.isChecked():
            flags |= re.DOTALL

        status, output, count, _positions = self.processor.run_regex(
            pattern, test_text, flags)

        if not pattern:
            self.regex_status.setText(tr("text_pattern_prompt"))
            self.match_count.setText(tr("text_matches_label"))
            return

        if status.startswith("Invalid regex"):
            self.regex_status.setText(status)
            self.match_count.setText(tr("text_matches_label"))
            return

        if not test_text:
            self.regex_status.setText(tr("text_enter_test_text"))
            self.match_count.setText(tr("text_matches_label"))
            return

        self.match_count.setText(f"Matches: {count}")

        if count == 0:
            self.regex_status.setText(tr("text_no_matches"))
            self.regex_output.setPlainText(tr("text_no_matches"))
            return

        self.regex_status.setText(status)
        self.regex_status.setProperty("status_color", "ok")
        self.regex_status.style().unpolish(self.regex_status)
        self.regex_status.style().polish(self.regex_status)

        self.regex_output.setPlainText(output)

        # Highlight matches in the input
        # (positions are available from processor but we re-compute for highlighting)
        extra_selections = []
        import re as _re
        try:
            compiled = _re.compile(pattern, flags)
            for m in compiled.finditer(test_text):
                sel = QTextEdit.ExtraSelection()
                sel.cursor = self.regex_input.textCursor()
                sel.cursor.setPosition(m.start())
                sel.cursor.setPosition(m.end(), QTextCursor.KeepAnchor)
                sel.format.setBackground(QColor(80, 130, 220, 60))
                extra_selections.append(sel)
        except _re.error:
            pass
        self.regex_input.setExtraSelections(extra_selections)
