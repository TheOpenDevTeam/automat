from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from automat.ui.page_base import PageWidget
from automat.core import clipboard_history as ch


class ClipboardPage(PageWidget):
    def __init__(self, app):
        super().__init__(app)
        self.tr = self.app.i18n.tr
        ch.ensure_monitoring(QApplication.instance())
        self.build()
        self.refresh()

    def build(self):
        tr = self.tr
        self.header("clipboard", tr("clip_title"), tr("clip_subtitle"))

        outer = QHBoxLayout()
        self.content_layout.addLayout(outer)

        left, _, ll = self.card(tr("clip_list_card"))
        outer.addWidget(left, 1)

        search_row = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText(tr("clip_search"))
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.refresh)
        search_row.addWidget(self.search, 1)
        refresh_btn = QPushButton(tr("clip_refresh"))
        refresh_btn.clicked.connect(self.refresh)
        search_row.addWidget(refresh_btn)
        ll.addLayout(search_row)

        self.list = QListWidget()
        self.list.itemClicked.connect(self._show)
        self.list.itemDoubleClicked.connect(lambda item: self._copy())
        ll.addWidget(self.list, 1)

        btn_row = QHBoxLayout()
        for txt, fn, obj in [(tr("clip_copy"), self._copy, "accent"),
                             (tr("clip_pin"), self._toggle_pin, None),
                             (tr("clip_delete"), self._delete, "danger"),
                             (tr("clip_clear"), self._clear, None)]:
            b = QPushButton(txt)
            if obj:
                b.setObjectName(obj)
            b.clicked.connect(fn)
            btn_row.addWidget(b)
        ll.addLayout(btn_row)

        right, _, rl = self.card(tr("clip_preview_card"))
        outer.addWidget(right, 1)
        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setObjectName("code_output")
        rl.addWidget(self.preview, 1)
        self.meta = QLabel("")
        self.meta.setObjectName("text_muted")
        self.meta.setWordWrap(True)
        rl.addWidget(self.meta)

    def refresh(self, *args):
        tr = self.tr
        q = self.search.text().strip() if hasattr(self, "search") else ""
        self._items = ch.list_clips(q)
        self.list.clear()
        for c in self._items:
            short = c["text"].replace("\n", " ⏎ ")
            if len(short) > 90:
                short = short[:90] + "…"
            prefix = "📌 " if c["pinned"] else ""
            item = QListWidgetItem(prefix + short)
            item.setToolTip(c["ts"])
            item.setData(Qt.UserRole, c["id"])
            self.list.addItem(item)
        self.meta.setText(tr("clip_count", n=len(self._items), total=ch.count()))

    def _current(self):
        item = self.list.currentItem()
        if not item:
            return None
        cid = item.data(Qt.UserRole)
        for c in self._items:
            if c["id"] == cid:
                return c
        return None

    def _show(self, item):
        c = self._current()
        if c:
            self.preview.setPlainText(c["text"])
            self.meta.setText(f"{c['ts']} · {len(c['text'])} chars")

    def _copy(self):
        c = self._current()
        if c:
            QApplication.clipboard().setText(c["text"])

    def _toggle_pin(self):
        c = self._current()
        if c:
            ch.set_pinned(c["id"], not c["pinned"])
            self.refresh()

    def _delete(self):
        c = self._current()
        if c:
            ch.delete(c["id"])
            self.preview.clear()
            self.refresh()

    def _clear(self):
        tr = self.tr
        if QMessageBox.question(self, tr("clip_clear"), tr("clip_clear_confirm")) == QMessageBox.Yes:
            ch.clear(unpinned_only=True)
            self.preview.clear()
            self.refresh()
