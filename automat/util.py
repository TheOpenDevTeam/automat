"""Utility functions for AUTOMAT."""

import logging
import threading

from PyQt5.QtCore import QCoreApplication, QObject, QTimer, pyqtSignal, pyqtSlot

LOG = logging.getLogger("automat.util")


class _Marshaller(QObject):
    """Delivers a callable to the thread that owns this object.

    Emitting a signal from another thread with an Auto connection queues the
    call onto the owner's event loop, which is exactly what cross-thread UI
    updates need.

    The slot MUST be decorated with @pyqtSlot: without it PyQt cannot tell
    which QObject is the receiver, falls back to a direct call, and the
    update runs on the worker thread instead of the GUI thread.
    """

    _invoke_requested = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self._invoke_requested.connect(self._invoke)

    @pyqtSlot(object)
    def _invoke(self, func):
        try:
            func()
        except Exception as e:
            LOG.debug("safe() call failed: %s", e)


_marshaller = None
_marshaller_lock = threading.Lock()


def _get_marshaller() -> _Marshaller:
    global _marshaller
    if _marshaller is None:
        with _marshaller_lock:
            if _marshaller is None:
                m = _Marshaller()
                app = QCoreApplication.instance()
                if app is not None:
                    # Pin to the GUI thread even if this helper is first
                    # touched from a worker.
                    m.moveToThread(app.thread())
                _marshaller = m
    return _marshaller


def safe(func, *args, **kwargs):
    """Run *func* on the GUI thread. Never raises.

    Historically this used `QTimer.singleShot(0, ...)`. That silently never
    fires when called from a QThreadPool worker, because the worker thread has
    no event loop — so every background progress/log update was dropped. The
    signal marshaller works from any thread.
    """
    _get_marshaller()._invoke_requested.emit(
        lambda: func(*args, **kwargs)
    )


def schedule(func, *args, **kwargs):
    """Run *func* on the GUI thread after 0 ms (legacy one-shot behaviour)."""
    def _call():
        try:
            func(*args, **kwargs)
        except Exception as e:
            LOG.debug("schedule() call failed: %s", e)
    QTimer.singleShot(0, _call)
