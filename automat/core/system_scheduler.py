r"""
System scheduler integration — registers recurring tasks with the OS task
scheduler so they run even when AUTOMAT is closed.

Backends:
  Windows  -> schtasks.exe (Task Scheduler)
  Linux    -> systemd user timers (fallback: crontab)
  macOS    -> launchd (placeholder, not implemented)

Usage:

    from automat.core.system_scheduler import system_scheduler

    system_scheduler.register_task("backup", "0 2 * * *",
                                   [sys.executable, r"C:\scripts\backup.py"])
    system_scheduler.unregister_task("backup")
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Optional


@dataclass
class ScheduledTask:
    name: str
    cron: str            # cron expression (min hour day month dow)
    command: list[str]   # executable + args
    enabled: bool = True


class SystemScheduler:
    """Registers tasks with the host OS task scheduler."""

    def __init__(self):
        self._platform = sys.platform

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def register_task(self, name: str, cron: str, command: list[str],
                      enabled: bool = True) -> str:
        """Register a recurring task. Returns an status message."""
        task = ScheduledTask(name=name, cron=cron, command=command,
                             enabled=enabled)
        if self._platform == "win32":
            return self._register_windows(task)
        if self._platform.startswith("linux"):
            return self._register_linux(task)
        if self._platform == "darwin":
            return self._register_macos(task)
        return f"unsupported platform: {self._platform}"

    def unregister_task(self, name: str) -> str:
        """Remove a previously registered task."""
        if self._platform == "win32":
            return self._unregister_windows(name)
        if self._platform.startswith("linux"):
            return self._unregister_linux(name)
        if self._platform == "darwin":
            return self._unregister_macos(name)
        return f"unsupported platform: {self._platform}"

    def list_tasks(self) -> list[str]:
        """Return names of tasks registered with the system scheduler."""
        if self._platform == "win32":
            return self._list_windows()
        if self._platform.startswith("linux"):
            return self._list_linux()
        if self._platform == "darwin":
            return self._list_macos()
        return []

    def is_available(self) -> bool:
        """True if a system scheduler backend is usable on this host."""
        if self._platform == "win32":
            return shutil.which("schtasks") is not None
        if self._platform.startswith("linux"):
            return shutil.which("systemctl") is not None or \
                shutil.which("crontab") is not None
        return False

    # ------------------------------------------------------------------
    # Windows — Task Scheduler via schtasks.exe
    # ------------------------------------------------------------------

    def _register_windows(self, task: ScheduledTask) -> str:
        schtasks = shutil.which("schtasks")
        if not schtasks:
            return "schtasks.exe not found"
        # Build a wrapper batch file that launches the command, so the
        # scheduled task always points at a stable entry point.
        wrapper = self._write_windows_wrapper(task.name, task.command)
        # Convert cron expression to a Windows schedule string.
        schedule = self._cron_to_windows_schedule(task.cron)
        cmd = [
            schtasks, "/Create", "/TN", task.name, "/TR", wrapper,
            "/SC", schedule, "/F",
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            if not task.enabled:
                self.disable_task_windows(task.name)
            return f"registered '{task.name}' with Windows Task Scheduler"
        except subprocess.CalledProcessError as exc:
            return f"failed to register '{task.name}': {exc.stderr.strip()}"

    def _unregister_windows(self, name: str) -> str:
        schtasks = shutil.which("schtasks")
        if not schtasks:
            return "schtasks.exe not found"
        cmd = [schtasks, "/Delete", "/TN", name, "/F"]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return f"removed '{name}' from Windows Task Scheduler"
        except subprocess.CalledProcessError as exc:
            return f"failed to remove '{name}': {exc.stderr.strip()}"

    def disable_task_windows(self, name: str) -> None:
        schtasks = shutil.which("schtasks")
        if not schtasks:
            return
        subprocess.run([schtasks, "/Change", "/TN", name, "/DISABLE"],
                       capture_output=True)

    def _list_windows(self) -> list[str]:
        schtasks = shutil.which("schtasks")
        if not schtasks:
            return []
        try:
            out = subprocess.run(
                [schtasks, "/Query", "/FO", "LIST", "/V"],
                capture_output=True, text=True, check=True).stdout
        except subprocess.CalledProcessError:
            return []
        names = []
        for line in out.splitlines():
            if line.startswith("TaskName:"):
                names.append(line.split(":", 1)[1].strip())
        return names

    def _write_windows_wrapper(self, name: str, command: list[str]) -> str:
        """Create a .bat wrapper in %TEMP% that runs the command."""
        import tempfile
        bat_dir = tempfile.gettempdir()
        bat_path = os.path.join(bat_dir, f"automat_task_{name}.bat")
        # Escape command args for batch.
        args = " ".join(f'"{a}"' for a in command)
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write(f"@echo off\n{args}\n")
        return bat_path

    @staticmethod
    def _cron_to_windows_schedule(cron: str) -> str:
        """Very rough cron -> Windows /SC mapping. Falls back to daily."""
        parts = cron.split()
        if len(parts) < 5:
            return "DAILY"
        minute, hour = parts[0], parts[1]
        if hour == "*" and minute == "*":
            return "MINUTE"
        if minute != "*" and hour != "*":
            return f"DAILY /ST {hour}:{minute}"
        return "DAILY"

    # ------------------------------------------------------------------
    # Linux — systemd user timers (fallback crontab)
    # ------------------------------------------------------------------

    def _register_linux(self, task: ScheduledTask) -> str:
        if shutil.which("systemctl"):
            return self._register_systemd_timer(task)
        if shutil.which("crontab"):
            return self._register_crontab(task)
        return "no systemd or crontab available"

    def _register_systemd_timer(self, task: ScheduledTask) -> str:
        """Create a systemd user service + timer."""
        import tempfile
        unit_dir = os.path.expanduser("~/.config/systemd/user")
        os.makedirs(unit_dir, exist_ok=True)
        service = os.path.join(unit_dir, f"automat-{task.name}.service")
        timer = os.path.join(unit_dir, f"automat-{task.name}.timer")
        cmd = " ".join(f'"{a}"' for a in task.command)
        with open(service, "w", encoding="utf-8") as f:
            f.write(f"[Unit]\nDescription=Automat task {task.name}\n\n"
                    f"[Service]\nType=oneshot\nExecStart={cmd}\n")
        cal = self._cron_to_systemd_calendar(task.cron)
        with open(timer, "w", encoding="utf-8") as f:
            f.write(f"[Unit]\nDescription=Run Automat task {task.name}\n\n"
                    f"[Timer]\nOnCalendar={cal}\nPersistent=true\n\n"
                    f"[Install]\nWantedBy=timers.target\n")
        try:
            subprocess.run(["systemctl", "--user", "daemon-reload"],
                           capture_output=True, check=False)
            subprocess.run(["systemctl", "--user", "enable", "--now",
                            f"automat-{task.name}.timer"],
                           capture_output=True, check=False)
            return f"registered '{task.name}' as systemd user timer"
        except FileNotFoundError:
            return "systemctl not available"

    def _register_crontab(self, task: ScheduledTask) -> str:
        """Append a crontab entry (user crontab)."""
        cmd = " ".join(f'"{a}"' for a in task.command)
        entry = f"{task.cron} {cmd} # automat:{task.name}\n"
        try:
            current = subprocess.run(["crontab", "-l"],
                                     capture_output=True, text=True)
            existing = current.stdout if current.returncode == 0 else ""
            # Remove any previous entry for this task name.
            lines = [l for l in existing.splitlines()
                     if f"# automat:{task.name}" not in l]
            lines.append(entry.rstrip())
            new_crontab = "\n".join(lines) + "\n"
            p = subprocess.run(["crontab", "-"], input=new_crontab,
                               capture_output=True, text=True)
            if p.returncode != 0:
                return f"crontab failed: {p.stderr.strip()}"
            return f"registered '{task.name}' in user crontab"
        except FileNotFoundError:
            return "crontab not available"

    def _unregister_linux(self, name: str) -> str:
        if shutil.which("systemctl"):
            subprocess.run(["systemctl", "--user", "disable", "--now",
                            f"automat-{name}.timer"], capture_output=True)
            for ext in (".service", ".timer"):
                path = os.path.expanduser(
                    f"~/.config/systemd/user/automat-{name}{ext}")
                if os.path.exists(path):
                    os.remove(path)
            subprocess.run(["systemctl", "--user", "daemon-reload"],
                           capture_output=True)
            return f"removed '{name}' systemd timer"
        if shutil.which("crontab"):
            try:
                current = subprocess.run(["crontab", "-l"],
                                         capture_output=True, text=True)
                if current.returncode != 0:
                    return "no crontab to edit"
                lines = [l for l in current.stdout.splitlines()
                         if f"# automat:{name}" not in l]
                p = subprocess.run(["crontab", "-"],
                                   input="\n".join(lines) + "\n",
                                   capture_output=True, text=True)
                if p.returncode != 0:
                    return f"crontab update failed: {p.stderr.strip()}"
                return f"removed '{name}' from crontab"
            except FileNotFoundError:
                return "crontab not available"
        return "no system scheduler available"

    def _list_linux(self) -> list[str]:
        if shutil.which("systemctl"):
            try:
                out = subprocess.run(
                    ["systemctl", "--user", "list-timers", "--all", "--no-legend"],
                    capture_output=True, text=True, check=False).stdout
                names = []
                for line in out.splitlines():
                    if "automat-" in line:
                        parts = line.split()
                        if parts:
                            names.append(parts[0].replace("automat-", ""))
                return names
            except FileNotFoundError:
                pass
        if shutil.which("crontab"):
            try:
                out = subprocess.run(["crontab", "-l"],
                                     capture_output=True, text=True,
                                     check=False).stdout
                names = []
                for line in out.splitlines():
                    if "# automat:" in line:
                        names.append(line.split("# automat:")[1].strip())
                return names
            except FileNotFoundError:
                pass
        return []

    # ------------------------------------------------------------------
    # macOS — placeholder
    # ------------------------------------------------------------------

    def _register_macos(self, task: ScheduledTask) -> str:
        return "macOS launchd integration not implemented"

    def _unregister_macos(self, name: str) -> str:
        return "macOS launchd integration not implemented"

    def _list_macos(self) -> list[str]:
        return []

    @staticmethod
    def _cron_to_systemd_calendar(cron: str) -> str:
        """Rough cron -> systemd OnCalendar mapping."""
        parts = cron.split()
        if len(parts) < 5:
            return "*-*-* *:*:00"
        minute, hour, day, month, dow = parts[:5]
        def star(v): return v == "*"
        def num(v): return v if not star(v) else "*"
        return (f"{num(month)}-{num(day)} {num(hour)}:{num(minute)}:00")


# Singleton instance
system_scheduler = SystemScheduler()
