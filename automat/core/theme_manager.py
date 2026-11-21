"""
ThemeManager — handles dark/light theme switching, QSS loading,
icon recoloring, and custom user themes.
"""

import json
from PyQt5.QtWidgets import QApplication
from automat.ui import icons
from automat.ui.icons import set_theme as icons_set_theme


# Arrow colour that matches the text colour of each built-in theme.
_THEME_ARROW_COLOR = {"dark": "#b5bac2", "light": "#5b6470"}


class ThemeManager:
    """Manages application theme (dark/light/custom) with persistence."""

    def __init__(self, settings: dict, settings_file: str):
        self._settings = settings
        self._settings_file = settings_file
        self._current = settings.get("theme", "dark")
        if self._current not in ("dark", "light"):
            self._current = "dark"
        self._custom_qss = None
        self._custom_dark = True
        custom = settings.get("custom_qss")
        if isinstance(custom, str) and custom.strip():
            self._custom_qss = custom
            self._custom_dark = bool(settings.get("custom_dark", True))
        self._qss_cache = {}
        self._load_qss()

    @property
    def current(self) -> str:
        return self._current

    @property
    def is_dark(self) -> bool:
        if self._custom_qss:
            return self._custom_dark
        return self._current == "dark"

    @property
    def is_custom(self) -> bool:
        return bool(self._custom_qss)

    def set_theme(self, name: str) -> str:
        """Switch to a built-in theme by name and persist the choice."""
        if name not in ("dark", "light"):
            name = "dark"
        self._current = name
        self._custom_qss = None
        self._settings.pop("custom_qss", None)
        self._settings.pop("custom_dark", None)
        self._apply()
        self._persist()
        return self._current

    def toggle(self) -> str:
        """Switch theme and return the new theme name."""
        if self._custom_qss:
            # Leave the custom theme for the built-in one with opposite brightness.
            target = "light" if self._custom_dark else "dark"
        else:
            target = "light" if self._current == "dark" else "dark"
        return self.set_theme(target)

    def apply(self):
        """Apply the current theme on startup."""
        self._apply()

    def apply_custom(self, qss: str, dark: bool = None, arrow_color: str = None):
        """Apply a custom QSS theme.

        `dark` decides icon recolouring (otherwise the current theme is kept),
        `arrow_color` lets the custom theme match its own text colour.
        """
        if dark is None:
            dark = self.is_dark
        self._custom_qss = qss
        self._custom_dark = bool(dark)
        self._settings["custom_qss"] = qss
        self._settings["custom_dark"] = self._custom_dark
        app = QApplication.instance()
        if app:
            app.setStyleSheet(qss + self._arrows(arrow_color, dark))
            icons_set_theme(self._custom_dark)
        self._persist()

    def _arrows(self, color=None, dark=None) -> str:
        if color is None:
            color = _THEME_ARROW_COLOR["dark" if dark else "light"]
        return icons.arrow_qss(color)

    def _apply(self):
        app = QApplication.instance()
        if app:
            if self._custom_qss:
                app.setStyleSheet(
                    self._custom_qss + self._arrows(None, self._custom_dark))
            else:
                app.setStyleSheet(self._qss_cache.get(self._current, ""))
            icons_set_theme(self.is_dark)

    def _load_qss(self):
        """Load QSS from embedded strings (fallback) or files."""
        from automat.config import DARK_STYLE, LIGHT_STYLE
        for name, style in (("dark", DARK_STYLE), ("light", LIGHT_STYLE)):
            self._qss_cache[name] = style + self._arrows(
                _THEME_ARROW_COLOR[name], name == "dark")

    def _persist(self):
        self._settings["theme"] = self._current
        try:
            from automat.core import json_io
            json_io.save_json(self._settings_file, self._settings)
        except Exception:
            try:
                with open(self._settings_file, "w", encoding="utf-8") as f:
                    json.dump(self._settings, f, indent=2, ensure_ascii=False)
            except Exception:
                pass
