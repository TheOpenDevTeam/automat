from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import json, csv
from automat.ui.page_base import PageWidget
from automat.ui.widgets import LogPanel, ProgressBar, ValidatedLineEdit
from automat.core.activity_log import log, EVENT_SEND, STATUS_OK, STATUS_ERROR
from automat.core.worker import run_in_background
from automat.config import load_proxy

try:
    import requests
except ImportError:
    requests = None


class TelegramPage(PageWidget):
    def __init__(self, app):
        super().__init__(app)
        self._running = False
        self._worker = None
        self.results = []
        self.build()

    def build(self):
        tr = self.app.i18n.tr
        self.header("telegram", tr("telegram_title"), tr("telegram_subtitle"))

        outer = QHBoxLayout()
        self.content_layout.addLayout(outer)

        left, inner_left, ll = self.card(tr("telegram_settings_card"))
        outer.addWidget(left)
        ll.addWidget(QLabel("Bot Token:"))
        self.token = ValidatedLineEdit(
            validator=lambda t: len(t) > 10 and ":" in t,
            placeholder="1234567890:ABCdef..."
        )
        self.token.setEchoMode(QLineEdit.Password)
        ll.addWidget(self.token)
        test_btn = QPushButton(tr("telegram_test_bot"))
        test_btn.clicked.connect(self._test_bot)
        ll.addWidget(test_btn)
        ll.addWidget(QLabel(tr("telegram_delay")))
        self.delay = ValidatedLineEdit(
            validator=lambda v: v.replace(".", "", 1).isdigit() and float(v) >= 0,
            placeholder="1.0"
        )
        ll.addWidget(self.delay)
        ll.addWidget(QLabel(tr("telegram_retries")))
        self.retries = ValidatedLineEdit(
            validator=lambda v: v.isdigit() and int(v) >= 0,
            placeholder="2"
        )
        ll.addWidget(self.retries)

        right, inner_right, rl = self.card(tr("telegram_message_card"))
        outer.addWidget(right, 1)
        rl.addWidget(QLabel(tr("telegram_recipients")))
        self.recipients = QPlainTextEdit()
        self.recipients.setPlaceholderText("123456789\n987654321\n@username")
        self.recipients.setMaximumHeight(120)
        rl.addWidget(self.recipients)
        rl.addWidget(QLabel(tr("telegram_message_text")))
        self.message = QPlainTextEdit()
        self.message.setPlaceholderText(tr("telegram_message_placeholder"))
        rl.addWidget(self.message)

        self.stats = {
            "total": QLabel(tr("telegram_total")),
            "sent": QLabel(tr("telegram_sent")),
            "failed": QLabel(tr("telegram_failed")),
            "time": QLabel(tr("telegram_time")),
        }
        for lbl in self.stats.values():
            lbl.setObjectName("bulk_stat")
        stats_row = QHBoxLayout()
        for lbl in self.stats.values():
            stats_row.addWidget(lbl)
        self.content_layout.addLayout(stats_row)

        self.progress = ProgressBar()
        self.content_layout.addWidget(self.progress)

        btn_row = QHBoxLayout()
        self.start_btn = QPushButton(tr("telegram_start"))
        self.start_btn.setObjectName("accent")
        self.start_btn.clicked.connect(self._start)
        btn_row.addWidget(self.start_btn)
        self.stop_btn = QPushButton(tr("telegram_stop"))
        self.stop_btn.setObjectName("danger")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop)
        btn_row.addWidget(self.stop_btn)
        export_btn = QPushButton(tr("telegram_export"))
        export_btn.clicked.connect(self._export)
        btn_row.addWidget(export_btn)
        self.content_layout.addLayout(btn_row)
        self.log_panel = LogPanel()
        self.content_layout.addWidget(self.log_panel)

    def _test_bot(self):
        if not requests:
            self.log_panel.write(self.app.i18n.tr("telegram_no_requests"), "err")
            return
        proxies = load_proxy(self.app.settings_data)
        try:
            r = requests.get(f"https://api.telegram.org/bot{self.token.text()}/getMe",
                             timeout=5, proxies=proxies)
            data = r.json()
            if data.get("ok"):
                self.log_panel.write(f"Bot: @{data['result']['username']}", "ok")
            else:
                self.log_panel.write(f"Error: {data.get('description')}", "err")
        except Exception as e:
            self.log_panel.write(f"Error: {e}", "err")

    def _start(self):
        if not requests:
            self.log_panel.write(self.app.i18n.tr("telegram_no_requests"), "err")
            return
        self._running = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        token = self.token.text()
        ids = [i.strip() for i in self.recipients.toPlainText().splitlines() if i.strip()]
        msg_tpl = self.message.toPlainText()
        delay = float(self.delay.text() or 1.0)
        retries = int(self.retries.text() or 2)
        proxies = load_proxy(self.app.settings_data)

        self._worker = run_in_background(
            self._run_bg, token, ids, msg_tpl, delay, retries, proxies,
            on_result=self._on_done,
            on_error=lambda e: self.log_panel.write(f"Error: {e}", "err"),
        )

    def _stop(self):
        self._running = False

    def _run_bg(self, token, ids, msg_tpl, delay, retries, proxies):
        import time as _time
        total, sent, failed = len(ids), 0, 0
        start = _time.time()
        tr = self.app.i18n.tr
        self.results = []

        for i, chat_id in enumerate(ids):
            if not self._running:
                break
            ok = False
            for attempt in range(retries + 1):
                try:
                    r = requests.post(
                        f"https://api.telegram.org/bot{token}/sendMessage",
                        json={"chat_id": chat_id, "text": msg_tpl, "parse_mode": "HTML"},
                        timeout=10, proxies=proxies)
                    if r.json().get("ok"):
                        sent += 1
                        ok = True
                        self._safe_log(f"[{i+1}/{total}] OK {chat_id}", "ok")
                        self.results.append({"id": chat_id, "status": "ok"})
                        break
                except Exception:
                    if attempt < retries:
                        _time.sleep(1)
            if not ok:
                failed += 1
                self._safe_log(f"[{i+1}/{total}] FAIL {chat_id}", "err")
                self.results.append({"id": chat_id, "status": "fail"})
            self._safe_stats(sent, failed, total, start)
            self._safe_progress(i + 1, total)
            _time.sleep(delay)

        return {"sent": sent, "failed": failed, "total": total}

    def _safe_log(self, msg, tag):
        QTimer.singleShot(0, lambda m=msg, t=tag: self.log_panel.write(m, t))

    def _safe_stats(self, sent, failed, total, start):
        tr = self.app.i18n.tr
        elapsed = __import__("time").time() - start
        def _do():
            self.stats["total"].setText(tr("telegram_total_fmt", total=total))
            self.stats["sent"].setText(tr("telegram_sent_fmt", sent=sent))
            self.stats["failed"].setText(tr("telegram_failed_fmt", failed=failed))
            self.stats["time"].setText(tr("telegram_time_fmt", time=elapsed))
        QTimer.singleShot(0, _do)

    def _safe_progress(self, current, total):
        pct = int(current / total * 100) if total > 0 else 0
        QTimer.singleShot(0, lambda p=pct: self.progress.setValue(p))

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
        log(EVENT_SEND, STATUS_OK, "Telegram", sent)
        if failed:
            log(EVENT_SEND, STATUS_ERROR, str(failed), failed)

    def _export(self):
        if not self.results:
            QMessageBox.warning(self, self.app.i18n.tr("telegram_no_data_title"),
                                self.app.i18n.tr("telegram_no_data_msg"))
            return
        fp, selected_filter = QFileDialog.getSaveFileName(
            self, self.app.i18n.tr("telegram_save"), "",
            "JSON (*.json);;CSV (*.csv)")
        if fp:
            try:
                if selected_filter and "CSV" in selected_filter:
                    if not fp.endswith(".csv"):
                        fp += ".csv"
                    with open(fp, "w", newline="", encoding="utf-8") as f:
                        writer = csv.DictWriter(f, fieldnames=["id", "status"])
                        writer.writeheader()
                        writer.writerows(self.results)
                else:
                    if not fp.endswith(".json"):
                        fp += ".json"
                    with open(fp, "w", encoding="utf-8") as f:
                        json.dump(self.results, f, ensure_ascii=False, indent=2)
                self.log_panel.write(f"Saved: {fp}", "ok")
            except Exception as e:
                self.log_panel.write(f"Error: {e}", "err")
