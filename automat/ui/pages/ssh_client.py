"""
SSH Client page — remote server access with command execution.
Fixed: thread-safety for QMessageBox, uses Worker pattern.
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from config import ACCENT, GREEN, RED
from ui.page_base import PageWidget
from ui.widgets import LogPanel
from core.worker import run_in_background
from util import safe

try:
    import paramiko
    HAS_PARAMIKO = True
except ImportError:
    HAS_PARAMIKO = False


class SSHClientPage(PageWidget):
    def __init__(self, app):
        super().__init__(app)
        self.connected = False
        self.client = None
        self.build()

    def build(self):
        tr = self.app.i18n.tr
        self.header("ssh", tr("ssh_title"), tr("ssh_subtitle"))

        outer = QHBoxLayout()
        self.content_layout.addLayout(outer)

        left, inner_left, ll = self.card(tr("ssh_connect_card"))
        outer.addWidget(left)
        ll.addWidget(QLabel(tr("ssh_host")))
        self.host = QLineEdit("localhost")
        self.host.setPlaceholderText("Hostname or IP")
        ll.addWidget(self.host)
        ll.addWidget(QLabel(tr("ssh_port")))
        self.port = QSpinBox()
        self.port.setRange(1, 65535)
        self.port.setValue(22)
        ll.addWidget(self.port)
        ll.addWidget(QLabel(tr("ssh_user")))
        self.user = QLineEdit("root")
        self.user.setPlaceholderText("Username")
        ll.addWidget(self.user)
        ll.addWidget(QLabel(tr("ssh_password")))
        self.password = QLineEdit()
        self.password.setPlaceholderText("Password (optional)")
        self.password.setEchoMode(QLineEdit.Password)
        ll.addWidget(self.password)
        self.key_file = QLineEdit()
        self.key_file.setPlaceholderText(tr("ssh_key_placeholder"))
        ll.addWidget(self.key_file)
        key_btn = QPushButton(tr("ssh_key_browse"))
        key_btn.clicked.connect(lambda: self.key_file.setText(
            QFileDialog.getOpenFileName(self, "SSH Key")[0]
        ))
        ll.addWidget(key_btn)
        self.connect_btn = QPushButton(tr("ssh_connect"))
        self.connect_btn.setObjectName("accent")
        self.connect_btn.setToolTip("Connect to SSH server")
        self.connect_btn.clicked.connect(self._toggle_connect)
        ll.addWidget(self.connect_btn)
        self.conn_status = QLabel(tr("ssh_not_connected"))
        self.conn_status.setObjectName("conn_status")
        ll.addWidget(self.conn_status)

        right, inner_right, rl = self.card(tr("ssh_terminal_card"))
        outer.addWidget(right, 1)
        rl.addWidget(QLabel(tr("ssh_cmd_placeholder")))
        cmd_row = QHBoxLayout()
        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText(tr("ssh_cmd_placeholder"))
        self.cmd_input.returnPressed.connect(self._exec_cmd)
        cmd_row.addWidget(self.cmd_input)
        exec_btn = QPushButton(tr("ssh_exec"))
        exec_btn.setObjectName("accent")
        exec_btn.clicked.connect(self._exec_cmd)
        cmd_row.addWidget(exec_btn)
        rl.addLayout(cmd_row)

        predef_row = QHBoxLayout()
        cmd_tips = ["List files with details", "Print working directory", "Show current user",
                     "Disk usage", "Memory usage", "System uptime"]
        for cmd, tip in zip(["ls -la", "pwd", "whoami", "df -h", "free -m", "uptime"], cmd_tips):
            b = QPushButton(cmd)
            b.setToolTip(tip)
            b.clicked.connect(lambda checked, c=cmd: self._quick_cmd(c))
            predef_row.addWidget(b)
        rl.addLayout(predef_row)

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setObjectName("terminal_output")
        rl.addWidget(self.output, 1)

        self.log_panel = LogPanel()
        self.content_layout.addWidget(self.log_panel)

    def _toggle_connect(self):
        if self.connected:
            self._disconnect()
        else:
            # Run connection in background thread
            run_in_background(
                self._connect_task,
                on_result=self._on_connect_result,
                on_error=self._on_connect_error,
            )

    def _connect_task(self):
        """Background task — may show QMessageBox via safe()."""
        tr = self.app.i18n.tr
        if not HAS_PARAMIKO:
            raise RuntimeError(tr("ssh_no_paramiko"))

        # Show confirmation dialog on the main thread and wait for result
        result = [None]
        event = QEventLoop()

        def ask_user():
            reply = QMessageBox.question(
                self, tr("ssh_confirm_title"), tr("ssh_confirm_msg"),
                QMessageBox.Yes | QMessageBox.No
            )
            result[0] = reply
            event.quit()

        QTimer.singleShot(0, ask_user)
        event.exec_()

        if result[0] != QMessageBox.Yes:
            return None

        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.WarningPolicy())
        kwargs = {
            "hostname": self.host.text(),
            "port": self.port.value(),
            "username": self.user.text(),
            "timeout": 10,
        }
        if self.password.text():
            kwargs["password"] = self.password.text()
        if self.key_file.text():
            kwargs["key_filename"] = self.key_file.text()
        self.client.connect(**kwargs)
        self.connected = True
        return self.host.text()

    def _on_connect_result(self, host):
        tr = self.app.i18n.tr
        self.conn_status.setText(tr("ssh_connected"))
        self.conn_status.setProperty("conn_state", "connected")
        self.conn_status.style().unpolish(self.conn_status)
        self.conn_status.style().polish(self.conn_status)
        self.connect_btn.setText(tr("ssh_disconnect"))
        self.log_panel.write(tr("ssh_connected_to", host=host), "ok")

    def _on_connect_error(self, error):
        self.log_panel.write(f"\u2717 {error}", "err")

    def _disconnect(self):
        tr = self.app.i18n.tr
        if self.client:
            self.client.close()
        self.connected = False
        self.conn_status.setText(tr("ssh_not_connected"))
        self.conn_status.setProperty("conn_state", "disconnected")
        self.conn_status.style().unpolish(self.conn_status)
        self.conn_status.style().polish(self.conn_status)
        self.connect_btn.setText(tr("ssh_connect"))
        self.log_panel.write(tr("ssh_disconnected"), "warn")

    def _exec_cmd(self):
        if not self.connected or not self.client:
            self.log_panel.write(self.app.i18n.tr("ssh_no_connection"), "err")
            return
        cmd = self.cmd_input.text()
        run_in_background(
            self._run_cmd,
            cmd,
            on_result=lambda _: None,
            on_error=lambda e: self.log_panel.write(f"\u2717 {e}", "err"),
        )

    def _quick_cmd(self, cmd):
        self.cmd_input.setText(cmd)
        self._exec_cmd()

    def _run_cmd(self, cmd):
        stdin, stdout, stderr = self.client.exec_command(cmd, timeout=10)
        out = stdout.read().decode("utf-8", errors="ignore")
        err = stderr.read().decode("utf-8", errors="ignore")
        result = out + err
        safe(self.output.appendPlainText, f"$ {cmd}")
        safe(self.output.appendPlainText, result)
        safe(self.log_panel.write, f"\u2713 {cmd}", "ok")
