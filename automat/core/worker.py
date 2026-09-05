"""
Worker pattern for background tasks — replaces裸 threading.Thread usage.
Uses QThreadPool + QRunnable for proper Qt integration.
"""

from PyQt5.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal


class WorkerSignals(QObject):
    """Signals emitted by a Worker."""
    finished = pyqtSignal()
    error = pyqtSignal(str)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)


class Worker(QRunnable):
    """
    Generic worker for running tasks in a background thread.

    Usage:
        worker = Worker(fn=some_function, arg1=val1, arg2=val2)
        worker.signals.result.connect(self.on_result)
        worker.signals.error.connect(self.on_error)
        QThreadPool.globalInstance().start(worker)
    """

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.setAutoDelete(True)

    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.signals.result.emit(result)
        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            self.signals.finished.emit()


def run_in_background(fn, *args, on_result=None, on_error=None, on_finished=None, **kwargs):
    """
    Convenience function — fire and forget or connect signals.

    Usage:
        run_in_background(
            self._fetch_data,
            on_result=self._apply_data,
            on_error=self._show_error,
        )
    """
    worker = Worker(fn, *args, **kwargs)
    if on_result:
        worker.signals.result.connect(on_result)
    if on_error:
        worker.signals.error.connect(on_error)
    if on_finished:
        worker.signals.finished.connect(on_finished)
    QThreadPool.globalInstance().start(worker)
    return worker
