"""Theme Builder page — create, edit, import/export custom themes."""

import json
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from automat.config import DATA_DIR
from automat.ui.page_base import PageWidget
from automat.core.worker import run_in_background
from automat.core import json_io

THEMES_DIR = DATA_DIR / "themes"
THEMES_DIR.mkdir(parents=True, exist_ok=True)


def _build_qss(bg, surface, accent, text):
    muted = _blend(text, bg, 0.5)
    border = _blend(text, bg, 0.8)
    return f"""
QMainWindow, QWidget {{ background-color: {bg}; color: {text}; font-family: "Segoe UI"; font-size: 9pt; }}
QFrame#header {{ background-color: {surface}; border: none; border-bottom: 1px solid {border}; }}
QFrame#sidebar {{ background-color: {surface}; border: none; border-right: 1px solid {border}; }}
QFrame#card {{ background-color: {surface}; border: 1px solid {border}; border-radius: 4px; }}
QPushButton {{ background-color: {_blend(text, bg, 0.12)}; color: {text}; border: 1px solid {_blend(text, bg, 0.2)}; border-radius: 3px; padding: 5px 12px; font-family: "Segoe UI"; font-size: 9pt; }}
QPushButton:hover {{ background-color: {_blend(text, bg, 0.18)}; }}
QPushButton:pressed {{ background-color: {surface}; }}
QPushButton#accent {{ background-color: {accent}; color: white; border: 1px solid {accent}; padding: 5px 12px; min-height: 18px; min-width: 60px; }}
QPushButton#accent:hover {{ background-color: {_darken(accent)}; border: 1px solid {_darken(accent)}; }}
QPushButton#sidebar_btn {{ background-color: transparent; color: {muted}; border: none; text-align: left; padding: 7px 12px; border-radius: 0; font-family: "Segoe UI"; font-size: 9pt; border-left: 2px solid transparent; }}
QPushButton#sidebar_btn:hover {{ background-color: {surface}; color: {text}; }}
QPushButton#sidebar_btn:checked {{ background-color: {_blend(text, bg, 0.1)}; color: {text}; border-left: 2px solid {accent}; }}
QLineEdit {{ background-color: {_blend(text, bg, 0.06)}; color: {text}; border: 1px solid {_blend(text, bg, 0.2)}; border-radius: 3px; padding: 6px 10px; font-family: "Segoe UI"; font-size: 9pt; }}
QLineEdit:focus {{ border: 1px solid {accent}; }}
QTextEdit, QPlainTextEdit {{ background-color: {_blend(text, bg, 0.06)}; color: {text}; border: 1px solid {_blend(text, bg, 0.2)}; border-radius: 3px; font-family: "Consolas"; font-size: 10pt; padding: 6px; }}
QComboBox {{ background-color: {_blend(text, bg, 0.12)}; color: {text}; border: 1px solid {_blend(text, bg, 0.2)}; border-radius: 3px; padding: 6px 10px; font-family: "Segoe UI"; font-size: 9pt; }}
QComboBox QAbstractItemView {{ background-color: {surface}; color: {text}; selection-background-color: {accent}; selection-color: white; border: 1px solid {_blend(text, bg, 0.2)}; }}
QTabWidget::pane {{ border: 1px solid {border}; background-color: {bg}; border-radius: 3px; }}
QTabBar::tab {{ background-color: {surface}; color: {muted}; padding: 7px 14px; font-family: "Segoe UI"; font-size: 9pt; border: none; border-bottom: 2px solid transparent; margin-right: 1px; }}
QTabBar::tab:selected {{ background-color: {bg}; color: {text}; border-bottom: 2px solid {accent}; }}
QScrollBar:vertical {{ width: 10px; background: transparent; }}
QScrollBar::handle:vertical {{ background: {_blend(text, bg, 0.2)}; border-radius: 4px; min-height: 30px; }}
QStatusBar {{ background-color: {surface}; color: {muted}; font-family: "Segoe UI"; font-size: 9pt; border-top: 1px solid {border}; }}
QTableWidget {{ background-color: {surface}; color: {text}; border: 1px solid {border}; border-radius: 3px; gridline-color: {border}; selection-background-color: {accent}; selection-color: white; font-family: "Segoe UI"; font-size: 9pt; }}
QToolTip {{ background-color: {_blend(text, bg, 0.15)}; color: {text}; border: 1px solid {_blend(text, bg, 0.3)}; border-radius: 4px; padding: 4px 8px; font-family: "Segoe UI"; font-size: 9pt; }}
QDialog {{ background-color: {bg}; }}
"""


def _blend(c1, c2, factor):
    r1, g1, b1 = _hex_to_rgb(c1)
    r2, g2, b2 = _hex_to_rgb(c2)
    r = int(r1 + (r2 - r1) * factor)
    g = int(g1 + (g2 - g1) * factor)
    b = int(b1 + (b2 - b1) * factor)
    return f"#{r:02x}{g:02x}{b:02x}"


def _darken(hex_color, amount=0.15):
    return _blend(hex_color, "#000000", amount)


def _hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


class ColorButton(QPushButton):
    colorChanged = pyqtSignal(str)

    def __init__(self, color="#2e7bd6", parent=None):
        super().__init__(parent)
        self._color = color
        self.setFixedSize(36, 28)
        self.setCursor(Qt.PointingHandCursor)
        self.clicked.connect(self._pick)
        self._update_style()

    def _update_style(self):
        r, g, b = _hex_to_rgb(self._color)
        border = "#555555" if (r * 0.299 + g * 0.587 + b * 0.114) > 128 else "#aaaaaa"
        self.setStyleSheet(
            f"QPushButton {{ background-color: {self._color}; border: 1px solid {border}; "
            f"border-radius: 4px; min-width: 36px; min-height: 28px; }}"
        )

    def _pick(self):
        color = QColorDialog.getColor(QColor(self._color), self)
        if color.isValid():
            self._color = color.name()
            self._update_style()
            self.colorChanged.emit(self._color)

    def color(self):
        return self._color

    def setColor(self, c):
        self._color = c
        self._update_style()


class ThemeBuilderPage(PageWidget):
    def __init__(self, app):
        super().__init__(app)
        self._custom_themes = {}
        self.build()
        self._load_themes()

    def build(self):
        tr = self.app.i18n.tr
        self.header("settings", tr("theme_builder_title"), tr("theme_builder_subtitle"))

        outer = QHBoxLayout()
        self.content_layout.addLayout(outer, 1)

        left_col = QVBoxLayout()

        name_card, _, name_layout = self.card(tr("theme_name"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("My Theme")
        name_layout.addWidget(self.name_input)
        left_col.addWidget(name_card)

        colors_card, _, colors_layout = self.card(tr("theme_colors"))
        self.bg_btn = ColorButton("#232529")
        self.surface_btn = ColorButton("#2c2f34")
        self.accent_btn = ColorButton("#2e7bd6")
        self.text_btn = ColorButton("#e8eaed")
        for label, btn in [(tr("theme_bg"), self.bg_btn),
                            (tr("theme_surface"), self.surface_btn),
                            (tr("theme_accent"), self.accent_btn),
                            (tr("theme_text"), self.text_btn)]:
            row = QHBoxLayout()
            row.addWidget(QLabel(label))
            row.addStretch()
            row.addWidget(btn)
            colors_layout.addLayout(row)
            btn.colorChanged.connect(self._update_preview)
        left_col.addWidget(colors_card)

        preview_card, _, preview_layout = self.card(tr("theme_preview"))
        self.preview = QLabel("AUTOMAT v1.0\nDashboard  |  Settings  |  Tools")
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumHeight(120)
        preview_layout.addWidget(self.preview)
        left_col.addWidget(preview_card)

        btn_row = QHBoxLayout()
        save_btn = QPushButton(tr("theme_save"))
        save_btn.setObjectName("accent")
        save_btn.clicked.connect(self._save_theme)
        btn_row.addWidget(save_btn)

        apply_btn = QPushButton(tr("theme_apply"))
        apply_btn.setObjectName("success")
        apply_btn.clicked.connect(self._apply_theme)
        btn_row.addWidget(apply_btn)
        left_col.addLayout(btn_row)

        import_btn = QPushButton(tr("theme_import"))
        import_btn.clicked.connect(self._import_theme)
        left_col.addWidget(import_btn)

        outer.addLayout(left_col, 2)

        right_col = QVBoxLayout()
        themes_card, _, themes_layout = self.card(tr("theme_custom"))
        self.theme_list = QListWidget()
        self.theme_list.currentItemChanged.connect(self._on_theme_selected)
        themes_layout.addWidget(self.theme_list)

        del_row = QHBoxLayout()
        del_btn = QPushButton(tr("theme_delete"))
        del_btn.setObjectName("danger")
        del_btn.clicked.connect(self._delete_theme)
        del_row.addStretch()
        del_row.addWidget(del_btn)
        themes_layout.addLayout(del_row)
        right_col.addWidget(themes_card, 1)

        export_btn = QPushButton(tr("theme_export"))
        export_btn.clicked.connect(self._export_theme)
        right_col.addWidget(export_btn)

        outer.addLayout(right_col, 1)

        self._update_preview()

    def _update_preview(self):
        bg = self.bg_btn.color()
        surface = self.surface_btn.color()
        accent = self.accent_btn.color()
        text = self.text_btn.color()

        self.preview.setStyleSheet(
            f"background-color: {bg}; color: {text}; border: 1px solid {_blend(text, bg, 0.2)}; "
            f"border-radius: 4px; padding: 16px; font-family: 'Segoe UI'; font-size: 10pt;"
        )

    def _save_theme(self):
        tr = self.app.i18n.tr
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, tr("theme_error"), tr("theme_enter_name"))
            return

        theme_data = {
            "name": name,
            "bg": self.bg_btn.color(),
            "surface": self.surface_btn.color(),
            "accent": self.accent_btn.color(),
            "text": self.text_btn.color(),
        }

        filepath = THEMES_DIR / f"{name.lower().replace(' ', '_')}.json"
        json_io.save_json(filepath, theme_data)

        self._custom_themes[name] = theme_data
        self._refresh_list()
        if hasattr(self.app, 'toast'):
            self.app.toast(tr("theme_saved", name=name))

    def _apply_theme(self):
        tr = self.app.i18n.tr
        bg = self.bg_btn.color()
        surface = self.surface_btn.color()
        accent = self.accent_btn.color()
        text = self.text_btn.color()

        qss = _build_qss(bg, surface, accent, text)
        self.app.theme_mgr.apply_custom(qss)
        if hasattr(self.app, 'toast'):
            self.app.toast(tr("theme_applied"))

    def _import_theme(self):
        tr = self.app.i18n.tr
        filepath, _ = QFileDialog.getOpenFileName(
            self, tr("theme_import"), str(DATA_DIR), "JSON Files (*.json)")
        if filepath:
            try:
                with open(filepath) as f:
                    data = json.load(f)
                name = data.get("name", "Imported")
                self._custom_themes[name] = data
                self._refresh_list()
                if hasattr(self.app, 'toast'):
                    self.app.toast(tr("theme_imported"))
            except Exception as e:
                QMessageBox.warning(self, tr("theme_error"), str(e))

    def _export_theme(self):
        tr = self.app.i18n.tr
        item = self.theme_list.currentItem()
        if not item:
            return
        name = item.text()
        theme = self._custom_themes.get(name)
        if not theme:
            return
        filepath, _ = QFileDialog.getSaveFileName(
            self, tr("theme_export"), str(DATA_DIR / f"{name}.json"),
            "JSON Files (*.json)")
        if filepath:
            with open(filepath, "w") as f:
                json.dump(theme, f, indent=2)

    def _delete_theme(self):
        tr = self.app.i18n.tr
        item = self.theme_list.currentItem()
        if not item:
            return
        name = item.text()
        reply = QMessageBox.question(
            self, tr("theme_delete"), tr("theme_delete_confirm", name=name),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            filepath = THEMES_DIR / f"{name.lower().replace(' ', '_')}.json"
            try:
                filepath.unlink()
            except Exception:
                pass
            self._custom_themes.pop(name, None)
            self._refresh_list()
            if hasattr(self.app, 'toast'):
                self.app.toast(tr("theme_deleted"))

    def _on_theme_selected(self, current, prev):
        if current:
            theme = self._custom_themes.get(current.text())
            if theme:
                self.name_input.setText(theme.get("name", ""))
                self.bg_btn.setColor(theme.get("bg", "#232529"))
                self.surface_btn.setColor(theme.get("surface", "#2c2f34"))
                self.accent_btn.setColor(theme.get("accent", "#2e7bd6"))
                self.text_btn.setColor(theme.get("text", "#e8eaed"))
                self._update_preview()

    def _load_themes(self):
        for fp in sorted(THEMES_DIR.glob("*.json")):
            # Per file: one damaged theme must not wipe out all the others.
            data = json_io.load_json(fp, None)
            if isinstance(data, dict) and data.get("name"):
                self._custom_themes[data["name"]] = data
        self._refresh_list()

    def _refresh_list(self):
        self.theme_list.clear()
        for name in sorted(self._custom_themes.keys()):
            self.theme_list.addItem(name)
