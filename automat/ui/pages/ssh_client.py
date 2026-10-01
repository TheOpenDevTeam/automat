"""
SSH Client page — remote server access with command execution.
Fixed: thread-safety for QMessageBox, uses Worker pattern.
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from automat.config import GREEN
from automat.ui.page_base import PageWidget
from automat.ui.widgets import LogPanel
from automat.core.worker import run_in_background
from automat.util import safe

try:
    import paramiko
    HAS_PARAMIKO = True
except ImportError:
    HAS_PARAMIKO = False


class SSHClientPage(PageWidget):
    def __init__(self, app):
        super().__init__(app)
        self.connected = False
        self._connecting = False
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
            return
        if self._connecting:
            return

        tr = self.app.i18n.tr
        if not HAS_PARAMIKO:
            self.log_panel.write(tr("ssh_no_paramiko"), "err")
            return

        # Read the widgets here, on the GUI thread: Qt widgets must never be
        # touched from a worker thread. The worker gets a plain snapshot.
        host = self.host.text().strip()
        if not host:
            self.log_panel.write(tr("ssh_no_host"), "err")
            return

        reply = QMessageBox.question(
            self, tr("ssh_confirm_title"), tr("ssh_confirm_msg"),
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        params = {
            "hostname": host,
            "port": self.port.value(),
            "username": self.user.text().strip(),
            "password": self.password.text(),
            "key_filename": self.key_file.text().strip(),
        }

        self._connecting = True
        self.connect_btn.setEnabled(False)
        self.conn_status.setText(tr("ssh_connecting"))

        run_in_background(
            self._connect_task,
            params,
            on_result=self._on_connect_result,
            on_error=self._on_connect_error,
        )

    def _connect_task(self, params):
        """Background thread — uses only the snapshot, never Qt widgets."""
        if not HAS_PARAMIKO:
            raise RuntimeError("paramiko is not installed")

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.WarningPolicy())
        kwargs = {
            "hostname": params["hostname"],
            "port": params["port"],
            "username": params["username"],
            "timeout": 10,
        }
        if params["password"]:
            kwargs["password"] = params["password"]
        if params["key_filename"]:
            kwargs["key_filename"] = params["key_filename"]
        client.connect(**kwargs)

        self.client = client
        return params["hostname"]

    def _on_connect_result(self, host):
        tr = self.app.i18n.tr
        self.connected = True
        self._connecting = False
        self.conn_status.setText(tr("ssh_connected"))
        self.conn_status.setProperty("conn_state", "connected")
        self.conn_status.style().unpolish(self.conn_status)
        self.conn_status.style().polish(self.conn_status)
        self.connect_btn.setText(tr("ssh_disconnect"))
        self.connect_btn.setEnabled(True)
        self.log_panel.write(tr("ssh_connected_to", host=host), "ok")
        # The secret has been handed to paramiko; do not keep it in the UI.
        self.password.clear()

    def _on_connect_error(self, error):
        tr = self.app.i18n.tr
        self.connected = False
        self._connecting = False
        self.conn_status.setText(tr("ssh_not_connected"))
        self.connect_btn.setEnabled(True)
        self.log_panel.write(f"\u2717 {error}", "err")

    def _disconnect(self):
        tr = self.app.i18n.tr
        client, self.client = self.client, None
        if client:
            try:
                client.close()
            except Exception:
                pass
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
        # Snapshot both in the GUI thread: the client may be closed by
        # _disconnect() while the worker is still running.
        client = self.client
        cmd = self.cmd_input.text()
        if not cmd:
            return
        self.output.appendPlainText(f"$ {cmd}")
        run_in_background(
            self._run_cmd,
            client,
            cmd,
            on_result=lambda _: None,
            on_error=lambda e: self.log_panel.write(f"\u2717 {e}", "err"),
        )

    def _quick_cmd(self, cmd):
        self.cmd_input.setText(cmd)
        self._exec_cmd()

    def _run_cmd(self, client, cmd):
        stdin, stdout, stderr = client.exec_command(cmd, timeout=10)
        out = stdout.read().decode("utf-8", errors="ignore")
        err = stderr.read().decode("utf-8", errors="ignore")
        result = out + err
        safe(self.output.appendPlainText, result)
        safe(self.log_panel.write, f"\u2713 {cmd}", "ok")
