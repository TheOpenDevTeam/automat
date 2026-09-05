"""
ThemeManager — handles dark/light theme switching, QSS loading,
and icon recoloring. Extracted from AutomatApp.
"""

import json
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from ui.icons import set_theme as icons_set_theme


class ThemeManager:
    """Manages application theme (dark/light) with persistence."""

    def __init__(self, settings: dict, settings_file: str):
        self._settings = settings
        self._settings_file = settings_file
        self._current = settings.get("theme", "dark")
        self._qss_cache: dict[str, str] = {}
        self._load_qss()

    @property
    def current(self) -> str:
        return self._current

    @property
    def is_dark(self) -> bool:
        return self._current == "dark"

    def toggle(self) -> str:
        """Switch theme and return the new theme name."""
        self._current = "light" if self._current == "dark" else "dark"
        self._apply()
        self._persist()
        return self._current

    def apply(self):
        """Apply the current theme on startup."""
        self._apply()

    def _apply(self):
        app = QApplication.instance()
        if app:
            app.setStyleSheet(self._qss_cache.get(self._current, ""))
            icons_set_theme(self._current == "dark")

    def _load_qss(self):
        """Load QSS from embedded strings (fallback) or files."""
        from config import DARK_STYLE, LIGHT_STYLE
        self._qss_cache["dark"] = DARK_STYLE
        self._qss_cache["light"] = LIGHT_STYLE

    def _persist(self):
        self._settings["theme"] = self._current
        try:
            with open(self._settings_file, "w") as f:
                json.dump(self._settings, f, indent=2)
        except Exception:
            pass
