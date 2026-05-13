"""Cross-platform process manager for the resvg render server daemon.

Mirrors svan2d.server.playwright.process_manager but for the resvg server.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import psutil

from svan2d.core.logger import get_logger

logger = get_logger()


class ProcessManager:
    """Manages the resvg render server as a background daemon process."""

    def __init__(
        self,
        pid_file: Path | None = None,
        log_file: Path | None = None,
        host: str = "localhost",
        port: int = 4100,
    ):
        svan2d_dir = Path.home() / ".svan2d"
        svan2d_dir.mkdir(exist_ok=True)

        self.pid_file = pid_file or svan2d_dir / "resvg-server.pid"
        self.log_file = log_file or svan2d_dir / "resvg-server.log"
        self.host = host
        self.port = port

    def is_running(self) -> bool:
        pid = self._read_pid()
        if pid is None:
            return False

        try:
            process = psutil.Process(pid)
            cmdline = " ".join(process.cmdline()).lower()
            return "resvg" in cmdline and "render" in cmdline
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            self._remove_pid_file()
            return False

    def start(self) -> bool:
        if self.is_running():
            logger.info("Resvg server is already running")
            return False

        logger.info(f"Starting resvg server on {self.host}:{self.port}")

        try:
            python_exe = sys.executable
            cmd = [
                python_exe,
                "-m",
                "uvicorn",
                "svan2d.server.resvg.render_server:app",
                "--host",
                self.host,
                "--port",
                str(self.port),
                "--log-level",
                "info",
            ]
            log_fd = open(self.log_file, "a")
            env = os.environ.copy()

            if sys.platform == "win32":
                CREATE_NEW_PROCESS_GROUP = 0x00000200
                DETACHED_PROCESS = 0x00000008
                process = subprocess.Popen(
                    cmd,
                    stdout=log_fd,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL,
                    env=env,
                    creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
                )
            else:
                process = subprocess.Popen(
                    cmd,
                    stdout=log_fd,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL,
                    env=env,
                    start_new_session=True,
                )

            self._write_pid(process.pid)
            time.sleep(2)
            if not self.is_running():
                raise RuntimeError("Server process died immediately after start")

            logger.info(f"Resvg server started with PID {process.pid}")
            return True

        except Exception as e:
            logger.error(f"Failed to start resvg server: {e}")
            self._remove_pid_file()
            raise

    def stop(self) -> bool:
        pid = self._read_pid()
        if pid is None:
            logger.info("Resvg server is not running")
            return False

        try:
            process = psutil.Process(pid)
            logger.info(f"Stopping resvg server (PID {pid})")
            process.terminate()

            try:
                process.wait(timeout=10)
            except psutil.TimeoutExpired:
                logger.warning("Graceful shutdown timeout, forcing kill")
                process.kill()
                process.wait(timeout=5)

            self._remove_pid_file()
            logger.info("Resvg server stopped")
            return True

        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.warning(f"Process not found or access denied: {e}")
            self._remove_pid_file()
            return False

    def restart(self) -> bool:
        self.stop()
        time.sleep(1)
        return self.start()

    def status(self) -> dict[str, Any]:
        pid = self._read_pid()
        if pid is None or not self.is_running():
            return {
                "running": False,
                "pid": None,
                "uptime_seconds": None,
                "memory_mb": None,
            }

        try:
            process = psutil.Process(pid)
            uptime = time.time() - process.create_time()
            memory_mb = process.memory_info().rss / (1024 * 1024)
            return {
                "running": True,
                "pid": pid,
                "uptime_seconds": uptime,
                "memory_mb": memory_mb,
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            self._remove_pid_file()
            return {
                "running": False,
                "pid": None,
                "uptime_seconds": None,
                "memory_mb": None,
            }

    def get_logs(self, lines: int = 50) -> str:
        if not self.log_file.exists():
            return "No log file found"

        try:
            with open(self.log_file, "r") as f:
                all_lines = f.readlines()
                return "".join(all_lines[-lines:])
        except Exception as e:
            return f"Error reading log file: {e}"

    def _read_pid(self) -> int | None:
        if not self.pid_file.exists():
            return None

        try:
            with open(self.pid_file, "r") as f:
                return int(f.read().strip())
        except (ValueError, IOError):
            return None

    def _write_pid(self, pid: int):
        with open(self.pid_file, "w") as f:
            f.write(str(pid))

    def _remove_pid_file(self):
        if self.pid_file.exists():
            self.pid_file.unlink()
