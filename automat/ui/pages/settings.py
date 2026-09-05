from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import json
from config import ACCENT, ACCENT2, GREEN, YELLOW, RED, SETTINGS_FILE
from i18n import LANGUAGES
from ui.page_base import PageWidget
from ui.widgets import Toast, ValidatedLineEdit


class SettingsPage(PageWidget):
    def __init__(self, app):
        super().__init__(app)
        self._built = False
        self.build()

    def build(self):
        self._clear_content()
        tr = self.app.i18n.tr

        self.header("settings", tr("settings_title"), tr("settings_subtitle"))

        c1, i1, l1 = self.card(tr("settings_appearance"))
        self.content_layout.addWidget(c1)

        self.theme_combo = QComboBox()
        self.theme_combo.addItem(tr("theme_dark"), "dark")
        self.theme_combo.addItem(tr("theme_light"), "light")
        idx = self.theme_combo.findData(self.app.settings_data.get("theme", "dark"))
        if idx >= 0:
            self.theme_combo.setCurrentIndex(idx)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_change)
        self.labeled_row(l1, tr("settings_theme"), self.theme_combo)

        self.lang_combo = QComboBox()
        lang_names = {"ru": "Русский", "en": "English"}
        for code in LANGUAGES:
            self.lang_combo.addItem(lang_names.get(code, code), code)
        idx = self.lang_combo.findData(self.app.settings_data.get("lang", "ru"))
        if idx >= 0:
            self.lang_combo.setCurrentIndex(idx)
        self.lang_combo.currentIndexChanged.connect(self._on_lang_change)
        self.labeled_row(l1, tr("settings_language"), self.lang_combo)

        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFont("Segoe UI"))
        self.labeled_row(l1, tr("settings_font"), self.font_combo)

        c2, i2, l2 = self.card(tr("settings_proxy"))
        self.content_layout.addWidget(c2)
        self.proxy_host = ValidatedLineEdit(placeholder=tr("settings_proxy_host"))
        l2.addWidget(self.proxy_host)
        self.proxy_port = ValidatedLineEdit(
            validator=lambda v: v.isdigit() if v else True,
            placeholder=tr("settings_proxy_port")
        )
        l2.addWidget(self.proxy_port)
        self.proxy_user = ValidatedLineEdit(placeholder=tr("settings_proxy_user"))
        l2.addWidget(self.proxy_user)
        self.proxy_pass = ValidatedLineEdit(placeholder=tr("settings_proxy_pass"))
        self.proxy_pass.setEchoMode(QLineEdit.Password)
        l2.addWidget(self.proxy_pass)

        c3, i3, l3 = self.card(tr("settings_reset"))
        self.content_layout.addWidget(c3)
        reset_btn = QPushButton(f"  {tr('settings_reset_btn')}")
        reset_btn.setObjectName("danger")
        reset_btn.clicked.connect(self._reset)
        l3.addWidget(reset_btn)
        clear_btn = QPushButton(f"  {tr('settings_clear_log')}")
        clear_btn.clicked.connect(self._clear_log)
        l3.addWidget(clear_btn)

        save_btn = QPushButton(f"  {tr('settings_save')}")
        save_btn.setObjectName("success")
        save_btn.clicked.connect(self._save)
        self.content_layout.addWidget(save_btn)

        self._built = True

    def _clear_content(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            if item.layout():
                self._clear_layout(item.layout())

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            if item.layout():
                self._clear_layout(item.layout())

    def _on_theme_change(self, idx):
        theme = self.theme_combo.currentData()
        self.app.settings_data["theme"] = theme
        self.app._apply_theme()
        self.app.theme_btn.setText("\U0001f319" if theme == "dark" else "\u2600\ufe0f")
        self.app._refresh_icons()

    def _on_lang_change(self, idx):
        lang = self.lang_combo.currentData()
        self.app.settings_data["lang"] = lang
        self.app.i18n.lang = lang
        self.app._clear_page_cache()
        self.app._refresh_ui_text()
        self.build()

    def _save(self):
        s = self.app.settings_data
        s["theme"] = self.theme_combo.currentData()
        s["lang"] = self.lang_combo.currentData()
        s["font"] = self.font_combo.currentFont().family()
        s["proxy"] = {"host": self.proxy_host.text(), "port": self.proxy_port.text(),
                       "user": self.proxy_user.text(), "pass": self.proxy_pass.text()}
        try:
            with open(SETTINGS_FILE, "w") as f:
                json.dump(s, f, indent=2)
            Toast(self.app, f"  {self.app.i18n.tr('settings_saved')}", GREEN)
        except Exception as e:
            QMessageBox.critical(self, self.app.i18n.tr("settings_error"), str(e))

    def _reset(self):
        reply = QMessageBox.question(self, self.app.i18n.tr("settings_reset_title"),
                                      self.app.i18n.tr("settings_reset_confirm"),
                                      QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.app.settings_data = {"theme": "dark", "lang": "ru"}
            idx = self.theme_combo.findData("dark")
            if idx >= 0:
                self.theme_combo.setCurrentIndex(idx)
            idx = self.lang_combo.findData("ru")
            if idx >= 0:
                self.lang_combo.setCurrentIndex(idx)
            self.app.i18n.lang = "ru"
            self.app._refresh_ui_text()
            self.build()
            self._save()

    def _clear_log(self):
        try:
            from core.activity_log import _DB_FILE, _init
            import os
            os.remove(_DB_FILE)
            _init()
            Toast(self.app, f"  {self.app.i18n.tr('settings_cleared')}", GREEN)
        except Exception as e:
            QMessageBox.critical(self, self.app.i18n.tr("settings_error"), str(e))
