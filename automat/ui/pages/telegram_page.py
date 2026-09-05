from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import threading, json, time, csv
from config import ACCENT, ACCENT2, GREEN, YELLOW, RED
from ui.page_base import PageWidget
from ui.widgets import LogPanel, ProgressBar, ValidatedLineEdit
from core.activity_log import log, EVENT_SEND, STATUS_OK, STATUS_ERROR
from config import load_proxy
from util import safe

try:
    import requests
except ImportError:
    requests = None


class TelegramPage(PageWidget):
    def __init__(self, app):
        super().__init__(app)
        self.stop_flag = False
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

        self.stats = {"total": QLabel(tr("telegram_total")), "sent": QLabel(tr("telegram_sent")),
                       "failed": QLabel(tr("telegram_failed")), "time": QLabel(tr("telegram_time"))}
        for lbl in self.stats.values():
            lbl.setObjectName("bulk_stat")
        stats_row = QHBoxLayout()
        for lbl in self.stats.values():
            stats_row.addWidget(lbl)
        self.content_layout.addLayout(stats_row)

        self.progress = ProgressBar()
        self.content_layout.addWidget(self.progress)

        btn_row = QHBoxLayout()
        for txt, obj, fn in [(tr("telegram_start"), "accent", self._start),
                              (tr("telegram_stop"), "danger", self._stop),
                              (tr("telegram_export"), None, self._export)]:
            b = QPushButton(txt)
            if obj:
                b.setObjectName(obj)
            b.clicked.connect(fn)
            btn_row.addWidget(b)
        self.content_layout.addLayout(btn_row)
        self.log_panel = LogPanel()
        self.content_layout.addWidget(self.log_panel)
        self.results = []

    def _test_bot(self):
        if not requests:
            self.log_panel.write("✗ requests не установлен", "err")
            return
        proxies = load_proxy(self.app.settings_data) if hasattr(self, 'app') and self.app else None
        try:
            r = requests.get(f"https://api.telegram.org/bot{self.token.text()}/getMe", timeout=5, proxies=proxies)
            data = r.json()
            if data.get("ok"):
                self.log_panel.write(f"✓ Бот: @{data['result']['username']}", "ok")
            else:
                self.log_panel.write(f"✗ {data.get('description')}", "err")
        except Exception as e:
            self.log_panel.write(f"✗ {e}", "err")

    def _start(self):
        self.stop_flag = False
        threading.Thread(target=self._run, daemon=True).start()

    def _stop(self):
        self.stop_flag = True

    def _run(self):
        if not requests:
            self.log_panel.write("✗ requests не установлен", "err")
            return
        token = self.token.text()
        ids = [i.strip() for i in self.recipients.toPlainText().splitlines() if i.strip()]
        msg_tpl = self.message.toPlainText()
        delay = float(self.delay.text() or 1.0)
        retries = int(self.retries.text() or 2)
        total, sent, failed = len(ids), 0, 0
        proxies = load_proxy(self.app.settings_data) if hasattr(self, 'app') and self.app else None
        start = time.time()
        safe(self.stats["total"].setText, self.app.i18n.tr("telegram_total_fmt", total=total))
        self.results = []

        for i, chat_id in enumerate(ids):
            if self.stop_flag:
                break
            ok = False
            for _ in range(retries + 1):
                try:
                    r = requests.post(
                        f"https://api.telegram.org/bot{token}/sendMessage",
                        json={"chat_id": chat_id, "text": msg_tpl, "parse_mode": "HTML"},
                        timeout=10, proxies=proxies)
                    if r.json().get("ok"):
                        sent += 1
                        ok = True
                        safe(self.log_panel.write, f"[{i+1}/{total}] \u2713 {chat_id}", "ok")
                        self.results.append({"id": chat_id, "status": "ok"})
                        break
                except Exception as e:
                    if _ < retries:
                        time.sleep(1)
            if not ok:
                failed += 1
                safe(self.log_panel.write, f"[{i+1}/{total}] \u2717 {chat_id}", "err")
                self.results.append({"id": chat_id, "status": "fail"})
            safe(self.stats["sent"].setText, self.app.i18n.tr("telegram_sent_fmt", sent=sent))
            safe(self.stats["failed"].setText, self.app.i18n.tr("telegram_failed_fmt", failed=failed))
            safe(self.stats["time"].setText, self.app.i18n.tr("telegram_time_fmt", time=time.time()-start))
            safe(self.progress.setValue, int((i + 1) / total * 100))
            time.sleep(delay)

        safe(self.log_panel.write, f"\u2713 {sent}/{total}", "ok" if failed == 0 else "warn")
        log(EVENT_SEND, STATUS_OK, "Telegram", sent)
        if failed:
            log(EVENT_SEND, STATUS_ERROR, str(failed), failed)

    def _export(self):
        if not self.results:
            QMessageBox.warning(self, self.app.i18n.tr("telegram_no_data_title"), self.app.i18n.tr("telegram_no_data_msg"))
            return
        fp, _ = QFileDialog.getSaveFileName(self, self.app.i18n.tr("telegram_save"), "", "JSON (*.json);;CSV (*.csv)")
        if fp:
            with open(fp, "w", encoding="utf-8") as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            self.log_panel.write(f"✓ Сохранено: {fp}", "ok")
