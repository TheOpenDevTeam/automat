"""
Dashboard page — real activity overview with stat cards, quick actions,
recent events feed, 7-day chart, and real-time system info.
"""

import sys
import time
import platform

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtChart import QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis

from config import ACCENT, ACCENT2, GREEN, YELLOW, RED
from ui.page_base import PageWidget
from ui.widgets import SkeletonBlock
from core.activity_log import (
    get_totals,
    get_today_totals,
    get_recent_events,
    get_stats_by_day,
    get_error_count,
    get_success_rate,
)
from core.worker import run_in_background

try:
    import psutil as _psutil
except ImportError:
    _psutil = None

_EVENT_ICONS = {
    "convert": "\u2699",
    "download": "\u2b07",
    "upload": "\u2b06",
    "file_op": "\U0001f4c1",
    "schedule": "\U0001f552",
    "error": "\u2716",
    "search": "\U0001f50d",
    "telegram": "\U0001f4e8",
    "user_action": "\u2694",
}

StartTime = time.time()


class DashPage(PageWidget):
    """Main dashboard with stats, recent activity, chart, and system info."""

    def __init__(self, app):
        super().__init__(app)
        self.stat_labels = {}
        self._skeletons = {}
        self.build()

    def build(self):
        tr = self.app.i18n.tr

        grid = QGridLayout()
        grid.setSpacing(10)
        grid.setContentsMargins(0, 0, 0, 0)
        self.content_layout.addLayout(grid)

        # Row 0: stat cards
        stats = [
            ("convert", "\u2194", tr("dash_conversions"), ACCENT),
            ("send", "\u2191", tr("dash_sends"), ACCENT2),
            ("hash", "#", tr("dash_hashes"), GREEN),
            ("schedule", "\u29d6", tr("dash_tasks"), YELLOW),
        ]
        for i, (key, ico, lbl, clr) in enumerate(stats):
            card, inner, inner_layout = self.card()
            grid.addWidget(card, 0, i)

            icon_lbl = QLabel(ico)
            icon_lbl.setObjectName("stat_icon")
            icon_lbl.setProperty("icon_color", clr)
            icon_lbl.setAlignment(Qt.AlignCenter)
            inner_layout.addWidget(icon_lbl)

            val = QLabel("\u2014")
            val.setObjectName("stat_value")
            val.setAlignment(Qt.AlignCenter)
            val.hide()
            inner_layout.addWidget(val)

            sk_val = SkeletonBlock(80, 36, 6)
            inner_layout.addWidget(sk_val)

            name = QLabel(lbl)
            name.setObjectName("stat_label")
            name.setAlignment(Qt.AlignCenter)
            inner_layout.addWidget(name)

            today = QLabel(tr("dash_today", n="\u2014"))
            today.setObjectName("stat_today")
            today.setAlignment(Qt.AlignCenter)
            today.hide()
            inner_layout.addWidget(today)

            sk_today = SkeletonBlock(100, 16, 4)
            inner_layout.addWidget(sk_today)

            self.stat_labels[key] = (val, today, sk_val, sk_today)

        # Row 1, col 0-1: quick action buttons
        card2, _inner2, layout2 = self.card(f"  {tr('dash_quick_actions')}")
        grid.addWidget(card2, 1, 0, 1, 2)
        actions = QGridLayout()
        actions.setSpacing(8)
        layout2.addLayout(actions)
        colors = [ACCENT, ACCENT2, GREEN, YELLOW]
        pages = ["convert", "bulk", "telegram", "cron"]
        for i, txt in enumerate([tr('dash_convert'), tr('dash_bulk'),
                                  tr('dash_telegram'), tr('dash_cron')]):
            btn = QPushButton(txt)
            btn.setObjectName("dash_action_btn")
            btn.setProperty("action_color", colors[i])
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, p=pages[i]: self.app.show_page(p))
            actions.addWidget(btn, i // 2, i % 2)

        # Row 1, col 2-3: recent events feed
        card3, _inner3, layout3 = self.card(f"  {tr('dash_recent')}")
        grid.addWidget(card3, 1, 2, 1, 2)
        self.feed = QListWidget()
        layout3.addWidget(self.feed)

        # Row 2, col 0-1: activity chart
        card4, _inner4, layout4 = self.card(f"  {tr('dash_chart')}")
        grid.addWidget(card4, 2, 0, 1, 2)
        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        self.chart = QChart()
        self.chart.setObjectName("dash_chart")
        self.chart_view.setChart(self.chart)
        layout4.addWidget(self.chart_view)

        # Row 2, col 2-3: system info
        card5, _inner5, layout5 = self.card(f"  {tr('dash_system')}")
        grid.addWidget(card5, 2, 2, 1, 2)
        self.sys_grid = QGridLayout()
        self.sys_grid.setSpacing(8)
        layout5.addLayout(self.sys_grid)

        self._sys_skeleton_widgets = []
        sys_skeleton_names = ["Python:", "CPU:", "RAM:", "Success:", "Errors:"]
        for i, name in enumerate(sys_skeleton_names):
            kl = QLabel(name)
            kl.setObjectName("sys_label")
            self.sys_grid.addWidget(kl, i, 0)
            sk = SkeletonBlock(80, 18, 4)
            self.sys_grid.addWidget(sk, i, 1)
            self._sys_skeleton_widgets.append(sk)

        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 2)
        grid.setRowStretch(2, 2)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)
        grid.setColumnStretch(3, 1)

        QTimer.singleShot(300, self.refresh)

    def refresh(self):
        run_in_background(
            self._load_data,
            on_result=self._apply,
            on_error=lambda e: print(f"Dashboard load error: {e}"),
        )

    def _load_data(self):
        return {
            "totals": get_totals(),
            "today": get_today_totals(),
            "events": get_recent_events(25),
            "chart": get_stats_by_day(7),
            "errors": get_error_count(7),
            "rate": get_success_rate(),
        }

    def _apply(self, data):
        tr = self.app.i18n.tr
        totals = data["totals"]
        today = data["today"]
        events = data["events"]
        chart = data["chart"]
        errors = data["errors"]
        rate = data["rate"]

        for key, (val_lbl, today_lbl, sk_val, sk_today) in self.stat_labels.items():
            val_lbl.setText(str(totals.get(key, 0)))
            val_lbl.show()
            sk_val.hide()
            today_lbl.setText(tr("dash_today", n=today.get(key, 0)))
            today_lbl.show()
            sk_today.hide()

        self.feed.clear()
        if not events:
            self.feed.addItem(tr("dash_no_events"))
        else:
            for ev in events:
                ico = _EVENT_ICONS.get(ev["event"], "\u25cf")
                ts = ev["ts"][11:16]
                detail = ev["detail"][:40] or ev["event"]
                self.feed.addItem(f"{ico} {detail}  [{ts}]")

        self.chart.removeAllSeries()
        if chart:
            bar_set = QBarSet("Activity")
            bar_set.setColor(QColor(ACCENT))
            categories = []
            for entry in chart:
                bar_set.append(entry["total"])
                categories.append(entry["date"][5:])
            series = QBarSeries()
            series.append(bar_set)
            self.chart.addSeries(series)

            axis_x = QBarCategoryAxis()
            axis_x.append(categories)
            self.chart.addAxis(axis_x, Qt.AlignBottom)
            series.attachAxis(axis_x)

            axis_y = QValueAxis()
            self.chart.addAxis(axis_y, Qt.AlignLeft)
            series.attachAxis(axis_y)

        self._clear_grid(self.sys_grid)

        if _psutil:
            cpu = f"{_psutil.cpu_percent(interval=None):.0f}%"
            ram = _psutil.virtual_memory()
            ram_pct = f"{ram.percent:.0f}%  ({ram.used // (1024**2)} / {ram.total // (1024**2)} MB)"
            disk = _psutil.disk_usage("/")
            disk_pct = f"{disk.percent:.0f}%  ({disk.used // (1024**3):.1f} / {disk.total // (1024**3):.1f} GB)"
            net = _psutil.net_io_counters()
            net_str = f"\u2b07 {net.bytes_recv // (1024**2)} MB  \u2b06 {net.bytes_sent // (1024**2)} MB"
            uptime_sec = int(time.time() - _psutil.boot_time())
        else:
            cpu = "\u2014"
            ram_pct = "\u2014"
            disk_pct = "\u2014"
            net_str = "\u2014"
            uptime_sec = int(time.time() - StartTime)

        python_ver = sys.version.split()[0]
        os_info = f"{platform.system()} {platform.release()}"
        rate_color = GREEN if rate >= 0.9 else (YELLOW if rate >= 0.7 else RED)

        days = uptime_sec // 86400
        hours = (uptime_sec % 86400) // 3600
        mins = (uptime_sec % 3600) // 60
        uptime_str = f"{days}d {hours}h {mins}m" if days else f"{hours}h {mins}m"

        sys_items = [
            ("OS", os_info, None),
            ("Python", python_ver, None),
            (tr("dash_cpu"), cpu, None),
            (tr("dash_ram"), ram_pct, None),
            ("Disk", disk_pct, None),
            ("Network", net_str, None),
            ("Uptime", uptime_str, None),
            (tr("dash_success"), f"{rate * 100:.0f}%", rate_color),
            (tr("dash_errors"), str(errors), None),
        ]

        for i, (label, value, color) in enumerate(sys_items):
            kl = QLabel(f"{label}:")
            kl.setObjectName("sys_label")
            self.sys_grid.addWidget(kl, i, 0)
            vl = QLabel(value)
            vl.setObjectName("sys_value")
            if color:
                vl.setProperty("val_color", color)
            self.sys_grid.addWidget(vl, i, 1)

    def _clear_grid(self, grid: QGridLayout):
        while grid.count():
            item = grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
