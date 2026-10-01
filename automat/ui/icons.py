"""
Vector icon provider — renders embedded SVG icons to QPixmap via QSvgRenderer,
with a QPainter-based fallback for systems without QtSvg.
"""

from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QFont, QBrush
from PyQt5.QtCore import Qt, QByteArray, QRectF

try:
    from PyQt5.QtSvg import QSvgRenderer
    HAS_SVG = True
except ImportError:
    HAS_SVG = False

_COLOR = "#e2e8f0"
_LIGHT_COLOR = "#4f6080"

_SVG_BODIES = {
    "dashboard": (
        '<rect x="3" y="12" width="4" height="9" rx="1"/>'
        '<rect x="10" y="7" width="4" height="14" rx="1"/>'
        '<rect x="17" y="3" width="4" height="18" rx="1"/>'
    ),
    "convert": (
        '<polyline points="17 2 21 6 17 10"/>'
        '<line x1="3" y1="6" x2="21" y2="6"/>'
        '<polyline points="7 22 3 18 7 14"/>'
        '<line x1="21" y1="18" x2="3" y2="18"/>'
    ),
    "bulk": (
        '<line x1="12" y1="2" x2="12" y2="21"/>'
        '<polyline points="8 16 12 21 16 16"/>'
        '<rect x="3" y="21" width="18" height="2" rx="1"/>'
    ),
    "telegram": (
        '<polygon points="21 2 3 10 11 13 18 5 13 15 21 2"/>'
        '<line x1="11" y1="13" x2="15" y2="21"/>'
    ),
    "hash": (
        '<rect x="5" y="11" width="14" height="10" rx="2"/>'
        '<path d="M8 11V7a4 4 0 018 0v4"/>'
        '<circle cx="12" cy="16" r="1.5"/>'
    ),
    "datagen": (
        '<rect x="3" y="3" width="7" height="7" rx="1"/>'
        '<rect x="14" y="3" width="7" height="7" rx="1"/>'
        '<rect x="3" y="14" width="7" height="7" rx="1"/>'
        '<rect x="14" y="14" width="7" height="7" rx="1"/>'
    ),
    "cleandata": (
        '<circle cx="12" cy="12" r="10"/>'
        '<polyline points="8 12 11 15 16 9"/>'
    ),
    "fileops": (
        '<path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/>'
    ),
    "cron": (
        '<circle cx="12" cy="12" r="10"/>'
        '<polyline points="12 6 12 12 16 14"/>'
    ),
    "text": (
        '<polyline points="4 7 4 4 20 4 20 7"/>'
        '<line x1="9" y1="20" x2="15" y2="20"/>'
        '<line x1="12" y1="4" x2="12" y2="20"/>'
    ),
    "ssh": (
        '<polyline points="4 17 10 12 4 7"/>'
        '<line x1="12" y1="19" x2="20" y2="19"/>'
    ),
    "git": (
        '<line x1="6" y1="3" x2="6" y2="15"/>'
        '<circle cx="18" cy="6" r="3"/>'
        '<circle cx="6" cy="18" r="3"/>'
        '<path d="M18 9a9 9 0 01-9 9"/>'
    ),
    "api": (
        '<circle cx="12" cy="12" r="10"/>'
        '<line x1="2" y1="12" x2="22" y2="12"/>'
        '<path d="M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z"/>'
    ),
    "sysmon": (
        '<rect x="2" y="3" width="20" height="14" rx="2"/>'
        '<line x1="8" y1="21" x2="16" y2="21"/>'
        '<line x1="12" y1="17" x2="12" y2="21"/>'
        '<polyline points="6 11 9 8 12 11 15 6 18 9"/>'
    ),
    "snippets": (
        '<rect x="4" y="2" width="16" height="20" rx="2"/>'
        '<line x1="9" y1="6" x2="15" y2="6"/>'
        '<line x1="9" y1="10" x2="15" y2="10"/>'
        '<line x1="9" y1="14" x2="13" y2="14"/>'
    ),
    "settings": (
        '<circle cx="12" cy="12" r="3"/>'
        '<path d="M12 1v2M12 21v2M1 12h2M21 12h2M5.64 5.64l1.41 1.41M16.95 16.95l1.41 1.41M5.64 18.36l1.41-1.41M16.95 7.05l1.41-1.41"/>'
    ),
    "tools": (
        '<path d="M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.76z"/>'
    ),
    "clipboard": (
        '<rect x="8" y="2" width="8" height="4" rx="1"/>'
        '<path d="M16 4h2a2 2 0 012 2v14a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2h2"/>'
        '<line x1="9" y1="12" x2="15" y2="12"/>'
        '<line x1="9" y1="16" x2="13" y2="16"/>'
    ),
}


def _make_svg_icon(name, size=24, color=_COLOR):
    body = _SVG_BODIES.get(name)
    if not body:
        return QIcon()
    svg = (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" '
        f'fill="none" stroke="{color}" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round">'
        f'{body}</svg>'
    )
    if HAS_SVG:
        renderer = QSvgRenderer(QByteArray(svg.encode()))
        pm = QPixmap(size, size)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        renderer.render(p)
        p.end()
        return QIcon(pm)
    return _make_fallback_icon(name, size)


def _make_fallback_icon(name, size=24):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(QColor("#4f8ef7")))
    p.drawRoundedRect(2, 2, size - 4, size - 4, 4, 4)
    p.setPen(QPen(QColor("white"), 0))
    f = QFont("Segoe UI", size // 2, QFont.Bold)
    p.setFont(f)
    p.drawText(QRectF(0, 0, size, size), Qt.AlignCenter, name[0].upper() if name else "?")
    p.end()
    return QIcon(pm)


_cache = {}


def get(name, size=24, color=None):
    if color is None:
        color = _COLOR
    key = (name, size, color)
    if key not in _cache:
        _cache[key] = _make_svg_icon(name, size, color)
    return _cache[key]


def pixmap(name, size=32, color=None):
    if color is None:
        color = _COLOR
    return get(name, size, color).pixmap(size, size)


def all_names():
    return list(_SVG_BODIES.keys())


def set_theme(is_dark: bool):
    """Update the default icon color to match the current theme and clear cache."""
    global _COLOR
    _COLOR = "#e2e8f0" if is_dark else _LIGHT_COLOR
    _cache.clear()


def is_dark() -> bool:
    """Current icon theme flag (True = dark)."""
    return _COLOR == "#e2e8f0"
