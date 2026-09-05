"""
System Monitor page — real-time CPU, RAM, disk, and network graphs
using psutil and PyQtChart.
"""

import datetime

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis, QDateTimeAxis

from config import ACCENT, ACCENT2, GREEN, YELLOW, RED
from ui.page_base import PageWidget

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# Keep 60 data points = 2 minutes of history at 2 s intervals
_HISTORY_SIZE = 60


class SysMonitorPage(PageWidget):
    """Live system resource monitor with time-series charts."""

    def __init__(self, app):
        super().__init__(app)
        self.cpu_history = []
        self.ram_history = []
        self._visible = False
        self.build()
        if HAS_PSUTIL:
            self.timer = QTimer()
            self.timer.timeout.connect(self._update)
            self.timer.start(2000)

    def showEvent(self, event):
        self._visible = True
        super().showEvent(event)

    def hideEvent(self, event):
        self._visible = False
        super().hideEvent(event)

    def build(self):
        tr = self.app.i18n.tr
        self.header("sysmon", tr("sysmon_title"), tr("sysmon_subtitle"))

        if not HAS_PSUTIL:
            lbl = QLabel(tr("sysmon_no_psutil"))
            lbl.setObjectName("sysmon_warning")
            lbl.setAlignment(Qt.AlignCenter)
            self.content_layout.addWidget(lbl)
            return

        stats_grid = QGridLayout()
        stats_grid.setSpacing(10)
        stats_grid.setContentsMargins(0, 0, 0, 0)
        self.content_layout.addLayout(stats_grid)

        # --- CPU card ---
        cpu_card, _cpu_inner, cpu_layout = self.card("CPU")
        stats_grid.addWidget(cpu_card, 0, 0)

        self.cpu_lbl = QLabel("0%")
        self.cpu_lbl.setObjectName("sysmon_big_value")
        self.cpu_lbl.setProperty("accent_color", ACCENT)
        self.cpu_lbl.setAlignment(Qt.AlignCenter)
        cpu_layout.addWidget(self.cpu_lbl)

        self.cpu_count_lbl = QLabel("Cores: \u2014")
        self.cpu_count_lbl.setObjectName("sysmon_detail")
        self.cpu_count_lbl.setAlignment(Qt.AlignCenter)
        cpu_layout.addWidget(self.cpu_count_lbl)

        # --- RAM card ---
        ram_card, _ram_inner, ram_layout = self.card("RAM")
        stats_grid.addWidget(ram_card, 0, 1)

        self.ram_lbl = QLabel("0%")
        self.ram_lbl.setObjectName("sysmon_big_value")
        self.ram_lbl.setProperty("accent_color", ACCENT2)
        self.ram_lbl.setAlignment(Qt.AlignCenter)
        ram_layout.addWidget(self.ram_lbl)

        self.ram_detail_lbl = QLabel("\u2014 / \u2014")
        self.ram_detail_lbl.setObjectName("sysmon_detail")
        self.ram_detail_lbl.setAlignment(Qt.AlignCenter)
        ram_layout.addWidget(self.ram_detail_lbl)

        # --- Disk card ---
        disk_card, _disk_inner, disk_layout = self.card("DISK")
        stats_grid.addWidget(disk_card, 0, 2)

        self.disk_lbl = QLabel("0%")
        self.disk_lbl.setObjectName("sysmon_big_value")
        self.disk_lbl.setProperty("accent_color", GREEN)
        self.disk_lbl.setAlignment(Qt.AlignCenter)
        disk_layout.addWidget(self.disk_lbl)

        self.disk_detail_lbl = QLabel("\u2014 / \u2014")
        self.disk_detail_lbl.setObjectName("sysmon_detail")
        self.disk_detail_lbl.setAlignment(Qt.AlignCenter)
        disk_layout.addWidget(self.disk_detail_lbl)

        # --- Time-series chart (CPU + RAM over the last 2 minutes) ---
        chart_card = QFrame()
        chart_card.setObjectName("card")
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(12, 12, 12, 12)

        chart_title = QLabel(self.app.i18n.tr("sysmon_cpu_ram_chart"))
        chart_title.setObjectName("card_title")
        chart_layout.addWidget(chart_title)

        self.chart = QChart()
        self.chart.setObjectName("sysmon_chart")
        self.chart.legend().setAlignment(Qt.AlignBottom)

        self.cpu_series = QLineSeries()
        self.cpu_series.setName("CPU")
        self.cpu_series.setColor(QColor(ACCENT))
        pen = QPen(QColor(ACCENT))
        pen.setWidth(2)
        self.cpu_series.setPen(pen)

        self.ram_series = QLineSeries()
        self.ram_series.setName("RAM")
        self.ram_series.setColor(QColor(ACCENT2))
        pen2 = QPen(QColor(ACCENT2))
        pen2.setWidth(2)
        self.ram_series.setPen(pen2)

        self.chart.addSeries(self.cpu_series)
        self.chart.addSeries(self.ram_series)

        # Time axis (X)
        self.axis_x = QDateTimeAxis()
        self.axis_x.setFormat("mm:ss")
        self.axis_x.setTickCount(7)
        self.chart.addAxis(self.axis_x, Qt.AlignBottom)
        self.cpu_series.attachAxis(self.axis_x)
        self.ram_series.attachAxis(self.axis_x)

        # Value axis (Y: 0–100 %)
        self.axis_y = QValueAxis()
        self.axis_y.setRange(0, 100)
        self.axis_y.setLabelFormat("%.0f%%")
        self.chart.addAxis(self.axis_y, Qt.AlignLeft)
        self.cpu_series.attachAxis(self.axis_y)
        self.ram_series.attachAxis(self.axis_y)

        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        chart_layout.addWidget(self.chart_view, 1)

        stats_grid.addWidget(chart_card, 1, 0, 1, 3)

        # Stretch: stat cards get 1 part, chart gets 3 parts
        stats_grid.setRowStretch(0, 1)
        stats_grid.setRowStretch(1, 3)
        stats_grid.setColumnStretch(0, 1)
        stats_grid.setColumnStretch(1, 1)
        stats_grid.setColumnStretch(2, 1)

    def _update(self):
        """Called every 2 seconds — refresh all gauges and chart data."""
        if not self._visible:
            return
        try:
            cpu = psutil.cpu_percent(interval=None)
            cpu_count = psutil.cpu_count()
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
        except Exception:
            return

        # --- Update stat cards ---
        self.cpu_lbl.setText(f"{cpu:.0f}%")
        self.cpu_count_lbl.setText(self.app.i18n.tr("sysmon_cores", n=cpu_count))

        self.ram_lbl.setText(f"{ram.percent:.0f}%")
        used_gb = ram.used / (1024 ** 3)
        total_gb = ram.total / (1024 ** 3)
        self.ram_detail_lbl.setText(f"{used_gb:.1f} GB / {total_gb:.1f} GB")

        self.disk_lbl.setText(f"{disk.percent:.0f}%")
        disk_used_gb = disk.used / (1024 ** 3)
        disk_total_gb = disk.total / (1024 ** 3)
        self.disk_detail_lbl.setText(f"{disk_used_gb:.1f} GB / {disk_total_gb:.1f} GB")

        # --- Update time-series chart ---
        now = QDateTime.currentDateTime().toMSecsSinceEpoch()
        self.cpu_series.append(now, cpu)
        self.ram_series.append(now, ram.percent)

        # Trim old data points
        while self.cpu_series.count() > _HISTORY_SIZE:
            self.cpu_series.remove(0)
            self.ram_series.remove(0)

        # Update axis range to show the last 2 minutes
        now_dt = QDateTime.currentDateTime()
        two_min_ago = now_dt.addSecs(-120)
        self.axis_x.setRange(two_min_ago, now_dt)
