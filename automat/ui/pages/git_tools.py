"""
Git Integration page — clone, status, pull, push, commit, log, branch.
Fixed: Worker pattern for background git operations.
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import subprocess, os
from config import ACCENT, GREEN, RED
from ui.page_base import PageWidget
from ui.widgets import LogPanel
from core.worker import run_in_background
from util import safe


class GitToolsPage(PageWidget):
    def __init__(self, app):
        super().__init__(app)
        self.build()

    def build(self):
        tr = self.app.i18n.tr
        self.header("git", tr("git_title"), tr("git_subtitle"))

        outer = QHBoxLayout()
        self.content_layout.addLayout(outer)

        left, inner_left, ll = self.card(tr("git_ops_card"))
        outer.addWidget(left)

        ll.addWidget(QLabel(tr("git_repo_path")))
        repo_row = QHBoxLayout()
        self.repo_path = QLineEdit(os.getcwd())
        self.repo_path.setPlaceholderText("Repository path")
        repo_row.addWidget(self.repo_path)
        browse_btn = QPushButton("\u2026")
        browse_btn.setFixedWidth(40)
        browse_btn.setToolTip("Select repository folder")
        browse_btn.clicked.connect(
            lambda: self.repo_path.setText(QFileDialog.getExistingDirectory(self, "Repository"))
        )
        repo_row.addWidget(browse_btn)
        ll.addLayout(repo_row)

        ll.addWidget(QLabel(tr("git_clone_url")))
        self.clone_url = QLineEdit()
        self.clone_url.setPlaceholderText("https://github.com/user/repo.git")
        ll.addWidget(self.clone_url)

        btn_grid = QGridLayout()
        git_tips = ["Clone a remote repository", "Show working tree status",
                     "Pull latest changes", "Push commits to remote",
                     "Show commit log", "List/create branches",
                     "Stage all changes", "Commit staged changes"]
        btns = [
            (0, 0, tr("git_clone"), self._clone, "accent"),
            (0, 1, tr("git_status"), self._status, "accent"),
            (1, 0, tr("git_pull"), self._pull, "accent2"),
            (1, 1, tr("git_push"), self._push, "accent2"),
            (2, 0, tr("git_log"), self._log, None),
            (2, 1, tr("git_branch"), self._branch, None),
            (3, 0, tr("git_add_all"), self._add, None),
            (3, 1, tr("git_commit"), self._commit, "success"),
        ]
        for (row, col, txt, fn, obj), tip in zip(btns, git_tips):
            b = QPushButton(txt)
            if obj:
                b.setObjectName(obj)
            b.setToolTip(tip)
            b.clicked.connect(fn)
            btn_grid.addWidget(b, row, col)
        ll.addLayout(btn_grid)

        ll.addWidget(QLabel(tr("git_commit_msg")))
        self.commit_msg = QLineEdit()
        self.commit_msg.setPlaceholderText(tr("git_commit_placeholder"))
        self.commit_msg.setToolTip("Press Ctrl+Enter to commit")
        ll.addWidget(self.commit_msg)

        right, inner_right, rl = self.card(tr("git_output_card"))
        outer.addWidget(right, 1)
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setObjectName("terminal_output")
        rl.addWidget(self.output, 1)

        self.log_panel = LogPanel()
        self.content_layout.addWidget(self.log_panel)

    def _run_git(self, args):
        try:
            r = subprocess.run(
                ["git"] + args, capture_output=True, text=True,
                cwd=self.repo_path.text(), timeout=30,
            )
            out = r.stdout + r.stderr
            safe(self.output.appendPlainText, f"$ git {' '.join(args)}")
            safe(self.output.appendPlainText, out)
            if r.returncode == 0:
                safe(self.log_panel.write, f"\u2713 git {' '.join(args)}", "ok")
            else:
                safe(self.log_panel.write, f"\u2717 {r.stderr[:100]}", "err")
            return out
        except Exception as e:
            safe(self.output.appendPlainText, str(e))
            safe(self.log_panel.write, str(e), "err")
            return ""

    def _threaded(self, args):
        run_in_background(
            self._run_git, args,
            on_result=lambda _: None,
            on_error=lambda e: safe(self.log_panel.write, str(e), "err"),
        )

    def _clone(self):
        url = self.clone_url.text()
        if url:
            self._threaded(["clone", url])

    def _status(self):
        self._threaded(["status"])

    def _pull(self):
        self._threaded(["pull"])

    def _push(self):
        self._threaded(["push"])

    def _log(self):
        self._threaded(["log", "--oneline", "-20"])

    def _branch(self):
        self._threaded(["branch", "-a"])

    def _add(self):
        self._threaded(["add", "."])

    def _commit(self):
        msg = self.commit_msg.text()
        if not msg:
            QMessageBox.warning(
                self, self.app.i18n.tr("git_error"),
                self.app.i18n.tr("git_enter_msg"),
            )
            return
        self._threaded(["commit", "-m", msg])
