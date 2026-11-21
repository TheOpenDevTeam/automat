"""
Стартовое обучение: что где расположено в AUTOMAT.

Показывается один раз после первой установки (флаг `onboarding_done`
в settings.json). Диалог можно пропустить кнопкой «Пропустить» или
крестиком — флаг всё равно выставляется, повторно открывается из
Настроек («Показать обучение»).
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QWidget,
)
from PyQt5.QtCore import Qt


def _slides(tr):
    """(заголовок, текст) — тексты берутся из i18n, здесь только порядок."""
    return [
        (tr("onboard_1_title"), tr("onboard_1_text")),
        (tr("onboard_2_title"), tr("onboard_2_text")),
        (tr("onboard_3_title"), tr("onboard_3_text")),
        (tr("onboard_4_title"), tr("onboard_4_text")),
        (tr("onboard_5_title"), tr("onboard_5_text")),
    ]


class OnboardingDialog(QDialog):
    def __init__(self, app, parent=None):
        super().__init__(parent or app)
        self.app = app
        tr = app.i18n.tr

        self.setWindowTitle(tr("onboard_title"))
        self.setMinimumSize(520, 380)
        self.setModal(True)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowContextHelpButtonHint
        )

        layout = QVBoxLayout(self)

        self.dots = QLabel()
        self.dots.setAlignment(Qt.AlignCenter)
        self.dots.setObjectName("text_muted")

        self.stack = QStackedWidget()
        for title, text in _slides(tr):
            self.stack.addWidget(self._make_slide(title, text))
        layout.addWidget(self.stack, 1)
        layout.addWidget(self.dots)

        btn_row = QHBoxLayout()
        self.skip_btn = QPushButton(tr("onboard_skip"))
        self.skip_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.skip_btn)
        btn_row.addStretch()
        self.back_btn = QPushButton(f"← {tr('onboard_back')}")
        self.back_btn.clicked.connect(self._back)
        btn_row.addWidget(self.back_btn)
        self.next_btn = QPushButton(f"{tr('onboard_next')} →")
        self.next_btn.setObjectName("accent")
        self.next_btn.clicked.connect(self._next)
        btn_row.addWidget(self.next_btn)
        layout.addLayout(btn_row)

        self.stack.currentChanged.connect(self._refresh)
        self._refresh(0)

    def _make_slide(self, title: str, text: str) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(24, 16, 24, 16)
        lay.setSpacing(12)
        title_lbl = QLabel(title)
        title_lbl.setObjectName("page_header_title")
        title_lbl.setWordWrap(True)
        title_lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(title_lbl)
        body = QLabel(text)
        body.setWordWrap(True)
        body.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        body.setTextFormat(Qt.RichText)
        lay.addWidget(body, 1)
        return page

    def _refresh(self, idx: int):
        total = self.stack.count()
        self.dots.setText("  ".join(
            "●" if i == idx else "○" for i in range(total)
        ))
        self.back_btn.setEnabled(idx > 0)
        tr = self.app.i18n.tr
        if idx >= total - 1:
            self.next_btn.setText(tr("onboard_finish"))
        else:
            self.next_btn.setText(f"{tr('onboard_next')} →")

    def _back(self):
        self.stack.setCurrentIndex(max(0, self.stack.currentIndex() - 1))

    def _next(self):
        idx = self.stack.currentIndex()
        if idx >= self.stack.count() - 1:
            self.accept()
        else:
            self.stack.setCurrentIndex(idx + 1)
