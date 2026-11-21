from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from automat.config import GREEN, SETTINGS_FILE
from automat.i18n import LANGUAGES
from automat.ui.page_base import PageWidget
from automat.ui.widgets import Toast, ValidatedLineEdit


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
        for code in LANGUAGES:
            self.lang_combo.addItem(tr(f"settings_lang_{code}"), code)
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

        c4, i4, l4 = self.card(tr("auto_update_title"))
        self.content_layout.addWidget(c4)
        export_btn = QPushButton(f"  {tr('settings_export_btn')}")
        export_btn.clicked.connect(self.app._export_settings)
        l4.addWidget(export_btn)
        import_btn = QPushButton(f"  {tr('settings_import_btn')}")
        import_btn.clicked.connect(self.app._import_settings)
        l4.addWidget(import_btn)
        from automat.config import APP_VERSION
        from automat.core import updater as _upd
        ver_lbl = QLabel(tr("auto_update_current", version=APP_VERSION))
        ver_lbl.setObjectName("text_muted")
        l4.addWidget(ver_lbl)
        self.auto_check_box = QCheckBox(tr("auto_update_auto"))
        self.auto_check_box.setChecked(
            _upd.get_update_settings(self.app.settings_data).get("auto_check", True))
        self.auto_check_box.toggled.connect(self._on_auto_check_toggle)
        l4.addWidget(self.auto_check_box)
        last = _upd.get_update_settings(self.app.settings_data).get("last_check") or ""
        self.last_check_lbl = QLabel(
            tr("auto_update_last_check",
               when=last[:16].replace("T", " ") if last else tr("auto_update_never")))
        self.last_check_lbl.setObjectName("text_muted")
        l4.addWidget(self.last_check_lbl)
        update_btn = QPushButton(f"  {tr('auto_update_check')}")
        update_btn.clicked.connect(self.app._check_updates)
        l4.addWidget(update_btn)
        onboard_btn = QPushButton(f"  {tr('settings_show_onboarding')}")
        onboard_btn.clicked.connect(lambda: self.app._show_onboarding(force=True))
        l4.addWidget(onboard_btn)

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
        self.app.theme_mgr.set_theme(theme)
        self.app.apply_theme()
        self.app._save_settings()

    def refresh_theme(self):
        """Keep the combo in sync when the theme changes elsewhere (Ctrl+T)."""
        super().refresh_theme()
        if not hasattr(self, "theme_combo"):
            return
        current = self.app.theme_mgr.current
        idx = self.theme_combo.findData(current)
        if idx >= 0 and idx != self.theme_combo.currentIndex():
            self.theme_combo.blockSignals(True)
            self.theme_combo.setCurrentIndex(idx)
            self.theme_combo.blockSignals(False)

    def _on_lang_change(self, idx):
        lang = self.lang_combo.currentData()
        self.app.settings_data["lang"] = lang
        self.app.i18n.lang = lang
        self.app._clear_page_cache()
        self.app._refresh_ui_text()
        self.build()

    def _on_auto_check_toggle(self, checked: bool):
        from automat.core import updater as _upd
        s = self.app.settings_data
        s["updates"] = {**_upd.get_update_settings(s), "auto_check": bool(checked)}

    def _save(self):
        s = self.app.settings_data
        s["theme"] = self.theme_combo.currentData()
        s["lang"] = self.lang_combo.currentData()
        s["font"] = self.font_combo.currentFont().family()
        s["proxy"] = {"host": self.proxy_host.text(), "port": self.proxy_port.text(),
                       "user": self.proxy_user.text(), "pass": self.proxy_pass.text()}
        if hasattr(self, "auto_check_box"):
            from automat.core import updater as _upd
            s["updates"] = {**_upd.get_update_settings(s),
                            "auto_check": self.auto_check_box.isChecked()}
        try:
            # Atomic write via json_io: a crash mid-write cannot truncate settings.
            from automat.core import json_io
            json_io.save_json(SETTINGS_FILE, s)
            Toast(self.app, f"  {self.app.i18n.tr('settings_saved')}", GREEN)
        except Exception as e:
            QMessageBox.critical(self, self.app.i18n.tr("settings_error"), str(e))

    def _reset(self):
        reply = QMessageBox.question(self, self.app.i18n.tr("settings_reset_title"),
                                      self.app.i18n.tr("settings_reset_confirm"),
                                      QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            # Mutate in place: ThemeManager and other managers hold a
            # reference to this dict.
            self.app.settings_data.clear()
            self.app.settings_data.update({"theme": "dark", "lang": "ru"})
            self.app.theme_mgr.set_theme("dark")
            self.app.i18n.lang = "ru"
            self.app.apply_theme()
            self.app._refresh_ui_text()
            self.build()
            self._save()

    def _clear_log(self):
        try:
            from automat.core.activity_log import _DB_FILE, _init
            from automat.core import db
            db.delete_database(_DB_FILE)
            _init()
            Toast(self.app, f"  {self.app.i18n.tr('settings_cleared')}", GREEN)
        except Exception as e:
            QMessageBox.critical(self, self.app.i18n.tr("settings_error"), str(e))
