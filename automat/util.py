from PyQt5.QtCore import QTimer


def safe(func, *args, **kwargs):
    QTimer.singleShot(0, lambda: func(*args, **kwargs))
