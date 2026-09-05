"""
Task Scheduler page — cron, interval, and one-time tasks via APScheduler.
Fixed: tasks survive app restart (rescheduled on load).
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import threading, json, subprocess, datetime
from config import ACCENT, GREEN, RED, TASKS_FILE
from ui.page_base import PageWidget
from ui.widgets import LogPanel
from core.activity_log import log, EVENT_SCHEDULE, STATUS_OK, STATUS_ERROR
from core.worker import run_in_background
from config import load_proxy
from util import safe

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.triggers.date import DateTrigger
    HAS_APS = True
except ImportError:
    HAS_APS = False
    BackgroundScheduler = object


class CronSchedulerPage(PageWidget):
    def __init__(self, app):
        super().__init__(app)
        self.tasks = []
        self.scheduler = BackgroundScheduler() if HAS_APS else None
        if HAS_APS:
            self.scheduler.start()
        self.build()
        self._load()

    def build(self):
        tr = self.app.i18n.tr
        self.header("cron", tr("cron_title"), tr("cron_subtitle"))

        outer = QHBoxLayout()
        self.content_layout.addLayout(outer)

        left, inner_left, ll = self.card(tr("cron_new_task_card"))
        outer.addWidget(left)
        ll.addWidget(QLabel(tr("cron_name_label")))
        self.task_name = QLineEdit()
        self.task_name.setPlaceholderText("Task name")
        ll.addWidget(self.task_name)
        ll.addWidget(QLabel(tr("cron_type_label")))
        self.task_type = QComboBox()
        self.task_type.addItems(["script", "http_get", "http_post", "file_backup", "notify"])
        ll.addWidget(self.task_type)
        ll.addWidget(QLabel(tr("cron_path_label")))
        self.task_path = QLineEdit()
        self.task_path.setPlaceholderText("Script path or URL")
        ll.addWidget(self.task_path)
        pick_btn = QPushButton(tr("cron_file_btn"))
        pick_btn.clicked.connect(lambda: self.task_path.setText(
            QFileDialog.getOpenFileName(self, self.app.i18n.tr("cron_file_dialog"))[0]
            or self.task_path.text()
        ))
        ll.addWidget(pick_btn)
        ll.addWidget(QLabel(tr("cron_trigger_label")))
        self.task_trigger = QComboBox()
        self.task_trigger.addItems(["cron", "interval", "once"])
        ll.addWidget(self.task_trigger)
        ll.addWidget(QLabel(tr("cron_cron_label")))
        self.task_cron = QLineEdit("*/5 * * * *")
        ll.addWidget(self.task_cron)
        ll.addWidget(QLabel(tr("cron_interval_label")))
        self.task_interval = QSpinBox()
        self.task_interval.setRange(1, 1440)
        self.task_interval.setValue(60)
        ll.addWidget(self.task_interval)
        add_btn = QPushButton(tr("cron_add_btn"))
        add_btn.setObjectName("success")
        add_btn.clicked.connect(self._add)
        ll.addWidget(add_btn)
        self.log_panel = LogPanel()
        ll.addWidget(self.log_panel)

        right, inner_right, rl = self.card(tr("cron_tasks_card"))
        outer.addWidget(right, 1)
        self.task_table = QTableWidget()
        self.task_table.setColumnCount(5)
        self.task_table.setHorizontalHeaderLabels([
            tr("cron_table_name"), tr("cron_table_type"),
            tr("cron_table_schedule"), tr("cron_table_next_run"),
            tr("cron_table_status"),
        ])
        self.task_table.horizontalHeader().setStretchLastSection(True)
        rl.addWidget(self.task_table)

        btn_row = QHBoxLayout()
        btn_tips = ["Run selected task now", "Pause/Resume task", "Delete selected task"]
        for (txt, obj, fn), tip in zip([
            (tr("cron_run_btn"), "accent", self._run_now),
            (tr("cron_pause_btn"), None, self._pause_task),
            (tr("cron_del_btn"), "danger", self._del_task),
        ], btn_tips):
            b = QPushButton(txt)
            if obj:
                b.setObjectName(obj)
            b.setToolTip(tip)
            b.clicked.connect(fn)
            btn_row.addWidget(b)
        rl.addLayout(btn_row)

    def _schedule_task(self, task):
        """Add a single task to the APScheduler."""
        if not HAS_APS or not self.scheduler:
            return
        job_id = f"task_{task['name']}"
        try:
            existing = self.scheduler.get_job(job_id)
            if existing:
                existing.remove()
        except Exception:
            pass

        if not task.get("enabled", True):
            return

        trigger_type = task.get("trigger", "interval")
        if trigger_type == "cron":
            parts = task.get("cron", "*/5 * * * *").split()
            kwargs = {}
            if len(parts) >= 1:
                kwargs["minute"] = parts[0]
            if len(parts) >= 2:
                kwargs["hour"] = parts[1]
            if len(parts) >= 3:
                kwargs["day"] = parts[2]
            if len(parts) >= 4:
                kwargs["month"] = parts[3]
            if len(parts) >= 5:
                kwargs["day_of_week"] = parts[4]
            trigger = CronTrigger(**kwargs)
        elif trigger_type == "interval":
            trigger = IntervalTrigger(minutes=task.get("interval", 60))
        elif trigger_type == "once":
            trigger = DateTrigger(run_date=datetime.datetime.now() + datetime.timedelta(seconds=5))
        else:
            return

        try:
            self.scheduler.add_job(
                self._run_task, trigger, args=[task],
                id=job_id, name=task["name"], replace_existing=True,
            )
        except Exception as e:
            self.log_panel.write(f"Sched error: {e}", "err")

    def _add(self):
        task = {
            "name": self.task_name.text(),
            "type": self.task_type.currentText(),
            "path": self.task_path.text(),
            "trigger": self.task_trigger.currentText(),
            "cron": self.task_cron.text(),
            "interval": self.task_interval.value(),
            "enabled": True,
        }
        self.tasks.append(task)
        self._schedule_task(task)
        self._refresh()
        self._save()

    def _refresh(self):
        self.task_table.setRowCount(len(self.tasks))
        for i, t in enumerate(self.tasks):
            self.task_table.setItem(i, 0, QTableWidgetItem(t["name"]))
            self.task_table.setItem(i, 1, QTableWidgetItem(t["type"]))
            if t["trigger"] == "cron":
                sched = t["cron"]
            elif t["trigger"] == "interval":
                sched = self.app.i18n.tr("cron_every_n_min", n=t["interval"])
            else:
                sched = self.app.i18n.tr("cron_once")
            self.task_table.setItem(i, 2, QTableWidgetItem(sched))

            next_run = "\u2014"
            if HAS_APS and self.scheduler:
                try:
                    job = self.scheduler.get_job(f"task_{t['name']}")
                    if job and job.next_run_time:
                        next_run = job.next_run_time.strftime("%H:%M:%S")
                except Exception:
                    pass
            self.task_table.setItem(i, 3, QTableWidgetItem(next_run))
            self.task_table.setItem(i, 4, QTableWidgetItem(
                "\u25cf" if t.get("enabled", True) else "\u23f8"
            ))

    def _run_task(self, task):
        proxies = load_proxy(self.app.settings_data) if hasattr(self, 'app') and self.app else None
        try:
            if task["type"] == "script" and task["path"]:
                subprocess.run(["python", task["path"]], timeout=60)
            elif task["type"] in ("http_get", "http_post") and task["path"]:
                import requests
                if task["type"] == "http_get":
                    requests.get(task["path"], timeout=10, proxies=proxies)
                else:
                    requests.post(task["path"], timeout=10, proxies=proxies)
            elif task["type"] == "file_backup" and task["path"]:
                import shutil as _shutil
                dst = task["path"] + f".bak.{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
                _shutil.copy2(task["path"], dst)
            elif task["type"] == "notify":
                safe(self.log_panel.write, f"{task['name']}", "info")
            safe(self.log_panel.write, f"\u2713 {task['name']}", "ok")
            log(EVENT_SCHEDULE, STATUS_OK, task["name"], 1)
        except Exception as e:
            safe(self.log_panel.write, f"\u2717 {task['name']}: {e}", "err")
            log(EVENT_SCHEDULE, STATUS_ERROR, str(e), 1)

    def _run_now(self):
        row = self.task_table.currentRow()
        if row < 0:
            return
        run_in_background(self._run_task, self.tasks[row])

    def _pause_task(self):
        row = self.task_table.currentRow()
        if row < 0:
            return
        self.tasks[row]["enabled"] = not self.tasks[row]["enabled"]
        if self.tasks[row]["enabled"]:
            self._schedule_task(self.tasks[row])
        else:
            if HAS_APS and self.scheduler:
                try:
                    job = self.scheduler.get_job(f"task_{self.tasks[row]['name']}")
                    if job:
                        job.remove()
                except Exception:
                    pass
        self._refresh()
        self._save()

    def _del_task(self):
        row = self.task_table.currentRow()
        if row < 0:
            return
        if HAS_APS and self.scheduler:
            try:
                job = self.scheduler.get_job(f"task_{self.tasks[row]['name']}")
                if job:
                    job.remove()
            except Exception:
                pass
        self.tasks.pop(row)
        self._refresh()
        self._save()

    def _save(self):
        try:
            with open(TASKS_FILE, "w") as f:
                json.dump(self.tasks, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _load(self):
        try:
            with open(TASKS_FILE) as f:
                self.tasks = json.load(f)
                for task in self.tasks:
                    self._schedule_task(task)
                self._refresh()
        except Exception:
            pass
