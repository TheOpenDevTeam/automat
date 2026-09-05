"""
Text Tools page — text transformation, search/replace, word statistics,
and a dedicated regular expression tester with live matching.
Fixed: undo/redo preserved for all transforms via cursor operations.
"""

import re
import collections

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from config import ACCENT, ACCENT2, GREEN, YELLOW, RED
from ui.page_base import PageWidget
from core.activity_log import log, EVENT_TEXT, STATUS_OK


class TextToolsPage(PageWidget):
    """Text editor with transformations, search/replace, stats, and regex tester."""

    def __init__(self, app):
        super().__init__(app)
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
            ("UPPER", lambda: self._transform(str.upper)),
            ("lower", lambda: self._transform(str.lower)),
            ("Title", lambda: self._transform(str.title)),
            ("Strip", lambda: self._transform(str.strip)),
            ("Sort\u2191", lambda: self._sort(True)),
            ("Sort\u2193", lambda: self._sort(False)),
            ("Dedup", self._dedup),
            ("Reverse", self._reverse),
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
        find_btn.setToolTip("Find & Replace")
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
        self.editor.setPlaceholderText("Paste or type text here...")
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
        load_btn.setToolTip("Load text from file")
        load_btn.clicked.connect(self._load_file)
        rl.addWidget(load_btn)
        save_btn = QPushButton(tr("text_save"))
        save_btn.setToolTip("Save text to file")
        save_btn.clicked.connect(self._save_file)
        rl.addWidget(save_btn)

        tabs.addTab(w, tr("text_editor_tab"))

    def _replace_content(self, new_text: str):
        """Replace all editor content while preserving undo history."""
        cursor = self.editor.textCursor()
        cursor.beginEditBlock()
        cursor.select(QTextCursor.Document)
        cursor.insertText(new_text)
        cursor.endEditBlock()

    def _transform(self, func):
        text = self.editor.toPlainText()
        self._replace_content(func(text))

    def _sort(self, asc):
        lines = self.editor.toPlainText().splitlines()
        lines.sort(reverse=not asc)
        self._replace_content("\n".join(lines))

    def _dedup(self):
        seen = []
        for line in self.editor.toPlainText().splitlines():
            if line not in seen:
                seen.append(line)
        self._replace_content("\n".join(seen))

    def _reverse(self):
        self._replace_content(self.editor.toPlainText()[::-1])

    def _find(self):
        text = self.find_text.text()
        if not text:
            return
        content = self.editor.toPlainText()
        flags = re.IGNORECASE if not self.regex_cb.isChecked() else 0
        if self.regex_cb.isChecked():
            try:
                pattern = re.compile(text, flags)
                matches = pattern.findall(content)
            except re.error:
                return
        else:
            pattern = re.compile(re.escape(text), flags)
            matches = pattern.findall(content)
        count = len(matches)
        self.editor.setExtraSelections([])
        if count == 0:
            return
        selections = []
        for m in pattern.finditer(content):
            sel = QTextEdit.ExtraSelection()
            sel.cursor = self.editor.textCursor()
            sel.cursor.setPosition(m.start())
            sel.cursor.setPosition(m.end(), QTextCursor.KeepAnchor)
            sel.format.setBackground(QColor(ACCENT + "55"))
            selections.append(sel)
        self.editor.setExtraSelections(selections)

    def _replace(self):
        find_text = self.find_text.text()
        replace_text = self.replace_text.text()
        if not find_text:
            return
        content = self.editor.toPlainText()
        flags = re.IGNORECASE if not self.regex_cb.isChecked() else 0
        if self.regex_cb.isChecked():
            try:
                result = re.sub(find_text, replace_text, content, flags=flags)
            except re.error:
                return
        else:
            result = content.replace(find_text, replace_text)
        self._replace_content(result)

    def _update_stats(self):
        text = self.editor.toPlainText()
        chars = len(text)
        words = len(text.split()) if text.strip() else 0
        lines = text.count("\n") + (1 if text else 0)
        unique = len(set(text.split())) if text.strip() else 0
        if hasattr(self, 'stats_labels'):
            self.stats_labels["Chars"].setText(f"{self.app.i18n.tr('text_chars_label')}: {chars}")
            self.stats_labels["Words"].setText(f"{self.app.i18n.tr('text_words_label')}: {words}")
            self.stats_labels["Lines"].setText(f"{self.app.i18n.tr('text_lines_label')}: {lines}")
            self.stats_labels["Unique words"].setText(f"{self.app.i18n.tr('text_unique_words_label')}: {unique}")
            counter = collections.Counter(text.split())
            self.word_stats.clear()
            for word, count in counter.most_common(20):
                self.word_stats.addItem(f"{word}: {count}")

    def _load_file(self):
        fp, _ = QFileDialog.getOpenFileName(self, self.app.i18n.tr("text_load"), "", "Text (*.txt);;All files (*.*)")
        if fp:
            with open(fp, encoding="utf-8", errors="ignore") as f:
                self.editor.setPlainText(f.read())

    def _save_file(self):
        fp, _ = QFileDialog.getSaveFileName(self, self.app.i18n.tr("text_save"), "", "Text (*.txt);;All files (*.*)")
        if fp:
            with open(fp, "w", encoding="utf-8") as f:
                f.write(self.editor.toPlainText())

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

        if not pattern:
            self.regex_status.setText(tr("text_pattern_prompt"))
            self.match_count.setText(tr("text_matches_label"))
            return

        flags = 0
        if self.flag_ignorecase.isChecked():
            flags |= re.IGNORECASE
        if self.flag_multiline.isChecked():
            flags |= re.MULTILINE
        if self.flag_dotall.isChecked():
            flags |= re.DOTALL

        try:
            compiled = re.compile(pattern, flags)
        except re.error as e:
            self.regex_status.setText(f"Invalid regex: {e}")
            self.match_count.setText(tr("text_matches_label"))
            return

        if not test_text:
            self.regex_status.setText(tr("text_enter_test_text"))
            self.match_count.setText(tr("text_matches_label"))
            return

        matches = list(compiled.finditer(test_text))
        match_count = len(matches)
        self.match_count.setText(f"Matches: {match_count}")

        if match_count == 0:
            self.regex_status.setText(tr("text_no_matches"))
            self.regex_output.setPlainText(tr("text_no_matches"))
            return

        self.regex_status.setText(f"Found {match_count} match(es)")
        self.regex_status.setProperty("status_color", "ok")
        self.regex_status.style().unpolish(self.regex_status)
        self.regex_status.style().polish(self.regex_status)

        lines = []
        for idx, m in enumerate(matches, 1):
            start, end = m.start(), m.end()
            matched_text = m.group(0)
            lines.append(f"Match #{idx}  [pos {start}\u2013{end}]: {matched_text!r}")
            if m.lastindex and m.lastindex > 0:
                if m.groupdict():
                    for name, val in m.groupdict().items():
                        if val is not None:
                            lines.append(f"  [{name}] = {val!r}")
                for g in range(1, m.lastindex + 1):
                    gname = compiled.groupindex.get(g, f"group {g}")
                    if isinstance(gname, int):
                        lines.append(f"  group {gname}: {m.group(g)!r}")
            lines.append("")

        self.regex_output.setPlainText("\n".join(lines))

        extra_selections = []
        for m in matches:
            sel = QTextEdit.ExtraSelection()
            sel.cursor = self.regex_input.textCursor()
            sel.cursor.setPosition(m.start())
            sel.cursor.setPosition(m.end(), QTextCursor.KeepAnchor)
            sel.format.setBackground(QColor(ACCENT + "55"))
            sel.format.setForeground(QColor("#ffffff"))
            extra_selections.append(sel)
        self.regex_input.setExtraSelections(extra_selections)
