from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from automat.config import ACCENT, ACCENT2, GREEN, RED, YELLOW


class Toast(QWidget):
    def __init__(self, parent, message, color=GREEN, duration=2500):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setObjectName("toast")
        self.setStyleSheet(
            f"QFrame#toast {{ border: 1px solid {color}; border-left: 4px solid {color}; border-radius: 10px; }}"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        self.lbl = QLabel(message)
        self.lbl.setObjectName("toast_label")
        self.lbl.setWordWrap(True)
        layout.addWidget(self.lbl)
        self.adjustSize()
        pw, ph = parent.width(), parent.height()
        px, py = parent.x(), parent.y()
        w, h = 340, self.height()
        x = px + pw - w - 24
        y = py + ph - h - 80
        self.setGeometry(x, y, w, h)
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(250)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.start()
        QTimer.singleShot(duration, self._fade_out)

    def _fade_out(self):
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(250)
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)
        self.anim.finished.connect(self.close)
        self.anim.start()


class LogPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        header = QLabel("LOG")
        header.setObjectName("log_header")
        layout.addWidget(header)
        self.log = QPlainTextEdit()
        self.log.setObjectName("log_area")
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(500)
        layout.addWidget(self.log)
        self._dark_colors = {"ok": GREEN, "err": RED, "warn": YELLOW, "info": ACCENT}
        self._light_colors = {"ok": "#1a7f4a", "err": "#c5221f", "warn": "#9a6700", "info": "#1a5fb4"}

    def write(self, msg, tag="ok"):
        ts = QDateTime.currentDateTime().toString("HH:mm:ss")
        try:
            from automat.ui.icons import is_dark
            dark = is_dark()
        except Exception:
            dark = True
        colors = self._dark_colors if dark else self._light_colors
        color = colors.get(tag, colors["info"])
        self.log.appendHtml(f'<span style="color: {color};">[{ts}] {msg}</span>')

    def clear(self):
        self.log.clear()


class SidebarButton(QPushButton):
    def __init__(self, icon, text, parent=None):
        super().__init__(f"  {text}", parent)
        self.setIcon(icon)
        self.setIconSize(QSize(20, 20))
        self.setCheckable(True)
        self.setObjectName("sidebar_btn")
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(36)


class ProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRange(0, 100)
        self.setValue(0)
        self.setFixedHeight(8)
        self.setTextVisible(False)


class SkeletonBlock(QFrame):
    """Animated placeholder block that shows while content is loading."""
    def __init__(self, width=80, height=20, rounded=6, parent=None):
        super().__init__(parent)
        self.setFixedSize(width, height)
        self._offset_val = 0.0
        self._offset = 0
        self._anim = QPropertyAnimation(self, b"_offset")
        self._anim.setDuration(1500)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setLoopCount(-1)
        self._anim_started = False

    def showEvent(self, event):
        if not self._anim_started:
            self._anim.start()
            self._anim_started = True
        super().showEvent(event)

    def hideEvent(self, event):
        if self._anim.state() == QPropertyAnimation.Running:
            self._anim.pause()
        super().hideEvent(event)

    @pyqtProperty(float)
    def _offset(self):
        return self._offset_val

    @_offset.setter
    def _offset(self, val):
        self._offset_val = val
        self.update()

    def paintEvent(self, event):
        from automat.ui.icons import is_dark as _icons_dark
        try:
            dark = _icons_dark()
        except Exception:
            dark = True
        base = QColor("#35383e") if dark else QColor("#e2e5ea")
        hi = QColor("#4a4f57") if dark else QColor("#c9cfd8")
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        phase = getattr(self, "_offset_val", 0.0)
        grad = QLinearGradient(0, 0, w, 0)
        grad.setColorAt(max(0, phase - 0.4), base)
        grad.setColorAt(phase, hi)
        grad.setColorAt(min(1, phase + 0.4), base)
        p.setBrush(QBrush(grad))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(0, 0, w, h, 6, 6)
        p.end()


class ValidatedLineEdit(QLineEdit):
    """QLineEdit with inline validation and visual feedback via QSS."""

    _VALID_ATTR = "inputState"

    def __init__(self, validator=None, placeholder="", parent=None):
        super().__init__(parent)
        self._validator_fn = validator
        self._has_interacted = False
        self.setProperty(self._VALID_ATTR, True)
        self.setPlaceholderText(placeholder)
        self.textChanged.connect(self._on_text_changed)
        self.editingFinished.connect(self._on_editing_finished)

    def set_validator_fn(self, fn):
        self._validator_fn = fn
        self._refresh()

    def is_valid(self):
        if not self._validator_fn:
            return True
        return self._validator_fn(self.text())

    def _refresh(self):
        valid = self._has_interacted and self.is_valid()
        self.setProperty(self._VALID_ATTR, valid)
        self.style().unpolish(self)
        self.style().polish(self)
        if self._has_interacted and not self.is_valid():
            self.setToolTip("Invalid value")
        else:
            self.setToolTip("")

    def _on_text_changed(self, text):
        if not self._has_interacted:
            return
        self._refresh()

    def _on_editing_finished(self):
        self._has_interacted = True
        self._refresh()
