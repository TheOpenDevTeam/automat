from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import json, time
from automat.ui.page_base import PageWidget
from automat.ui.widgets import LogPanel, ProgressBar
from automat.core.activity_log import log, EVENT_SEND, STATUS_OK, STATUS_ERROR
from automat.core.worker import run_in_background
from automat.config import load_proxy

try:
    import requests
except ImportError:
    requests = None


class BulkSendPage(PageWidget):
    def __init__(self, app):
        super().__init__(app)
        self._running = False
        self._worker = None
        self.build()

    def build(self):
        tr = self.app.i18n.tr
        self.header("bulk", tr("bulk_title"), tr("bulk_subtitle"))

        outer = QHBoxLayout()
        self.content_layout.addLayout(outer)

        left, inner_left, ll = self.card(tr("bulk_params_card"))
        outer.addWidget(left)

        ll.addWidget(QLabel("URL:"))
        self.url = QLineEdit("http://localhost:8000/api")
        ll.addWidget(self.url)
        ll.addWidget(QLabel(tr("bulk_method")))
        self.method = QComboBox()
        self.method.addItems(["POST", "GET", "PUT", "DELETE"])
        ll.addWidget(self.method)
        ll.addWidget(QLabel(tr("bulk_json_data")))
        self.data_text = QPlainTextEdit()
        self.data_text.setPlaceholderText('[{"key": "value"}, ...]')
        self.data_text.setMaximumHeight(200)
        ll.addWidget(self.data_text)
        ll.addWidget(QLabel(tr("bulk_delay")))
        self.delay = QLineEdit("0.5")
        ll.addWidget(self.delay)

        right, inner_right, rl = self.card(tr("bulk_stats_card"))
        outer.addWidget(right, 1)
        self.total_lbl = QLabel(tr("bulk_total"))
        self.sent_lbl = QLabel(tr("bulk_sent"))
        self.fail_lbl = QLabel(tr("bulk_failed"))
        self.time_lbl = QLabel(tr("bulk_time"))
        for lbl in (self.total_lbl, self.sent_lbl, self.fail_lbl, self.time_lbl):
            lbl.setObjectName("bulk_stat")
            rl.addWidget(lbl)
        self.progress = ProgressBar()
        rl.addWidget(self.progress)

        btn_row = QHBoxLayout()
        self.start_btn = QPushButton(tr("bulk_start"))
        self.start_btn.setObjectName("accent")
        self.start_btn.clicked.connect(self._start)
        btn_row.addWidget(self.start_btn)
        self.stop_btn = QPushButton(tr("bulk_stop"))
        self.stop_btn.setObjectName("danger")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop)
        btn_row.addWidget(self.stop_btn)
        load_btn = QPushButton(tr("bulk_load"))
        load_btn.clicked.connect(self._load_data)
        btn_row.addWidget(load_btn)
        self.content_layout.addLayout(btn_row)
        self.log_panel = LogPanel()
        self.content_layout.addWidget(self.log_panel)

    def _load_data(self):
        fp, _ = QFileDialog.getOpenFileName(self, "JSON/CSV", "", "JSON (*.json);;CSV (*.csv)")
        if fp:
            with open(fp, encoding="utf-8", errors="ignore") as f:
                self.data_text.setPlainText(f.read())
            self.log_panel.write(f"Loaded {fp}", "ok")

    def _start(self):
        if not requests:
            self.log_panel.write(self.app.i18n.tr("bulk_no_requests"), "err")
            return
        self._running = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        url = self.url.text()
        method = self.method.currentText().lower()
        delay = float(self.delay.text() or 0.5)
        try:
            data = json.loads(self.data_text.toPlainText())
            if isinstance(data, dict):
                data = [data]
        except Exception:
            data = [{"data": self.data_text.toPlainText()}]
        proxies = load_proxy(self.app.settings_data)

        self._worker = run_in_background(
            self._run_bg, data, url, method, delay, proxies,
            on_result=self._on_done,
            on_error=lambda e: self.log_panel.write(f"Error: {e}", "err"),
        )

    def _stop(self):
        self._running = False
        self.log_panel.write(self.app.i18n.tr("bulk_stopping"), "warn")

    def _run_bg(self, data, url, method, delay, proxies):
        total = len(data)
        sent = failed = 0
        start = time.time()
        tr = self.app.i18n.tr

        for i, item in enumerate(data):
            if not self._running:
                break
            try:
                r = requests.request(method, url, json=item, timeout=10, proxies=proxies)
                if r.ok:
                    sent += 1
                    self._safe_log(f"[{i+1}/{total}] OK {r.status_code}", "ok")
                else:
                    failed += 1
                    self._safe_log(f"[{i+1}/{total}] FAIL {r.status_code}", "err")
            except Exception as e:
                failed += 1
                self._safe_log(f"[{i+1}/{total}] ERROR {e}", "err")
            self._safe_update(sent, failed, total, start)
            time.sleep(delay)

        return {"sent": sent, "failed": failed, "total": total, "method": method, "url": url}

    def _safe_log(self, msg, tag):
        QTimer.singleShot(0, lambda m=msg, t=tag: self.log_panel.write(m, t))

    def _safe_update(self, sent, failed, total, start):
        elapsed = time.time() - start
        tr = self.app.i18n.tr
        def _do():
            self.sent_lbl.setText(tr("bulk_sent_fmt", sent=sent))
            self.fail_lbl.setText(tr("bulk_failed_fmt", failed=failed))
            self.time_lbl.setText(tr("bulk_time_fmt", time=elapsed))
            self.progress.setValue(int((sent + failed) / total * 100) if total > 0 else 0)
        QTimer.singleShot(0, _do)

    def _on_done(self, result):
        self._running = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        sent = result["sent"]
        total = result["total"]
        failed = result["failed"]
        self.log_panel.write(
            f"Done: {sent}/{total}",
            "ok" if failed == 0 else "warn")
        log(EVENT_SEND, STATUS_OK, f"{result['method'].upper()} {result['url']}", sent)
        if failed:
            log(EVENT_SEND, STATUS_ERROR, str(failed), failed)
