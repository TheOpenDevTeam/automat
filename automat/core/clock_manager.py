"""
ClockManager — updates a QLabel with the current time every second.
Extracted from AutomatApp._tick.
"""

import datetime
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QLabel


class ClockManager:
    """Manages a clock label that updates every second."""

    def __init__(self, label: QLabel, fmt: str = "%d.%m.%Y  %H:%M:%S"):
        self._label = label
        self._fmt = fmt
        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000)
        self._tick()

    def _tick(self):
        self._label.setText(datetime.datetime.now().strftime(self._fmt))

    def stop(self):
        self._timer.stop()

    def start(self):
        self._timer.start(1000)
