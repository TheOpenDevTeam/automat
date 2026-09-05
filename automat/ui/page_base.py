"""
Base page widget — provides scrollable content, card layout, and header.
All styles are handled via objectName + QSS in config.py.
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from ui.icons import pixmap as icon_pixmap


class PageWidget(QWidget):
    def __init__(self, app=None):
        super().__init__()
        self.app = app
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.content = QWidget()
        self.content.setObjectName("page_content")
        self.content.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(32, 28, 32, 28)
        self.content_layout.setSpacing(16)
        self.scroll.setWidget(self.content)
        self.layout.addWidget(self.scroll)

    def header(self, icon_name, title, subtitle=""):
        h_layout = QHBoxLayout()
        icon_lbl = QLabel()
        icon_lbl.setObjectName("page_header_icon")
        pm = icon_pixmap(icon_name, 36)
        icon_lbl.setPixmap(pm)
        icon_lbl.setFixedSize(36, 36)
        h_layout.addWidget(icon_lbl)
        text_layout = QVBoxLayout()
        h = QLabel(title)
        h.setObjectName("page_header_title")
        text_layout.addWidget(h)
        if subtitle:
            s = QLabel(subtitle)
            s.setObjectName("page_header_subtitle")
            text_layout.addWidget(s)
        h_layout.addLayout(text_layout)
        h_layout.addStretch()
        self.content_layout.addLayout(h_layout)
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("page_header_separator")
        self.content_layout.addWidget(sep)

    def card(self, title=""):
        card = QFrame()
        card.setObjectName("card")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(16, 16, 16, 16)
        cl.setSpacing(8)
        if title:
            lbl = QLabel(title)
            lbl.setObjectName("card_title")
            cl.addWidget(lbl)
            sep = QFrame()
            sep.setFrameShape(QFrame.HLine)
            sep.setObjectName("card_separator")
            cl.addWidget(sep)
        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setSpacing(8)
        cl.addWidget(inner)
        return card, inner, inner_layout

    def labeled_row(self, parent_layout, label, widget):
        row = QHBoxLayout()
        lbl = QLabel(label)
        lbl.setObjectName("labeled_row_label")
        row.addWidget(lbl)
        row.addWidget(widget, 1)
        parent_layout.addLayout(row)
