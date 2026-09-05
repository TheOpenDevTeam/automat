from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import threading, json, time
from config import ACCENT, ACCENT2, GREEN, YELLOW, RED
from ui.page_base import PageWidget
from ui.widgets import LogPanel, ProgressBar
from core.activity_log import log, EVENT_SEND, STATUS_OK, STATUS_ERROR
from config import load_proxy
from util import safe

try:
    import requests
except ImportError:
    requests = None


class BulkSendPage(PageWidget):
    def __init__(self, app):
        super().__init__(app)
        self.stop_flag = False
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
        self.total_lbl = QLabel(tr("bulk_total")); self.sent_lbl = QLabel(tr("bulk_sent"))
        self.fail_lbl = QLabel(tr("bulk_failed")); self.time_lbl = QLabel(tr("bulk_time"))
        for lbl in (self.total_lbl, self.sent_lbl, self.fail_lbl, self.time_lbl):
            lbl.setObjectName("bulk_stat")
            rl.addWidget(lbl)
        self.progress = ProgressBar()
        rl.addWidget(self.progress)

        btn_row = QHBoxLayout()
        for txt, obj, fn in [(tr("bulk_start"), "accent", self._start),
                             (tr("bulk_stop"), "danger", self._stop),
                             (tr("bulk_load"), None, self._load_data)]:
            b = QPushButton(txt)
            if obj:
                b.setObjectName(obj)
            b.clicked.connect(fn)
            btn_row.addWidget(b)
        self.content_layout.addLayout(btn_row)
        self.log_panel = LogPanel()
        self.content_layout.addWidget(self.log_panel)

    def _load_data(self):
        fp, _ = QFileDialog.getOpenFileName(self, "JSON/CSV", "", "JSON (*.json);;CSV (*.csv)")
        if fp:
            with open(fp, encoding="utf-8") as f:
                self.data_text.setPlainText(f.read())
            self.log_panel.write(f"✓ Загружен {fp}", "ok")

    def _start(self):
        self.stop_flag = False
        threading.Thread(target=self._run, daemon=True).start()

    def _stop(self):
        self.stop_flag = True
        self.log_panel.write("Остановка...", "warn")

    def _run(self):
        if not requests:
            self.log_panel.write("✗ requests не установлен", "err")
            return
        try:
            data = json.loads(self.data_text.toPlainText())
            if isinstance(data, dict):
                data = [data]
        except Exception:
            data = [{"data": self.data_text.toPlainText()}]

        url = self.url.text()
        method = self.method.currentText().lower()
        delay = float(self.delay.text() or 0.5)
        total = len(data)
        sent = failed = 0
        start = time.time()
        proxies = load_proxy(self.app.settings_data) if hasattr(self, 'app') and self.app else None

        safe(self.total_lbl.setText, self.app.i18n.tr("bulk_total_fmt", total=total))
        for i, item in enumerate(data):
            if self.stop_flag:
                break
            try:
                r = requests.request(method, url, json=item, timeout=10, proxies=proxies)
                if r.ok:
                    sent += 1
                    safe(self.log_panel.write, f"[{i+1}/{total}] \u2713 {r.status_code}", "ok")
                else:
                    failed += 1
                    safe(self.log_panel.write, f"[{i+1}/{total}] \u2717 {r.status_code}", "err")
            except Exception as e:
                failed += 1
                safe(self.log_panel.write, f"[{i+1}/{total}] \u2717 {e}", "err")
            safe(self.sent_lbl.setText, self.app.i18n.tr("bulk_sent_fmt", sent=sent))
            safe(self.fail_lbl.setText, self.app.i18n.tr("bulk_failed_fmt", failed=failed))
            safe(self.time_lbl.setText, self.app.i18n.tr("bulk_time_fmt", time=time.time()-start))
            safe(self.progress.setValue, int((i + 1) / total * 100))
            time.sleep(delay)

        safe(self.log_panel.write, f"\u2713 \u0417\u0430\u0432\u0435\u0440\u0448\u0435\u043d\u043e: {sent}/{total}", "ok" if failed == 0 else "warn")
        log(EVENT_SEND, STATUS_OK, f"{method.upper()} {url}", sent)
        if failed:
            log(EVENT_SEND, STATUS_ERROR, str(failed), failed)
