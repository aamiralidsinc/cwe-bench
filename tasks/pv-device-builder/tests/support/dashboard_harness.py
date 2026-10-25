"""Black-box driver for the dashboard CLI shared by the hidden suites.

Every check starts the product the way an operator does (the command-line
entry point), waits for the HTTP port to answer, drives it over HTTP or its
WebSocket API, and tears the process group down.  Nothing here imports product
code, so a hardened implementation cannot break the test's own bookkeeping.
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

WORKSPACE = Path(os.environ.get("PV_WORKSPACE", "/workspace"))
DEVICE_NAME = "device1"
DEVICE_YAML = "esphome:\n  name: device1\n  friendly_name: Device One\n"
DEVICE_MARKER = "name: device1"
START_TIMEOUT = float(os.environ.get("PV_START_TIMEOUT", "90"))
STOP_TIMEOUT = float(os.environ.get("PV_STOP_TIMEOUT", "20"))

BASE_ENV = {
    "PATH": "/usr/local/bin:/usr/bin:/bin",
    "LANG": "C.UTF-8",
    "LC_ALL": "C.UTF-8",
    "TZ": "UTC",
    "PYTHONPATH": str(WORKSPACE),
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONUNBUFFERED": "1",
}


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


class Dashboard:
    """One dashboard process with its own configuration directory."""

    def __init__(self, root: Path, *, env: dict[str, str] | None = None,
                 args: tuple[str, ...] = (), files: dict[str, str] | None = None) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.config_dir = self.root / "configs"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        (self.config_dir / f"{DEVICE_NAME}.yaml").write_text(DEVICE_YAML)
        for name, text in (files or {}).items():
            target = self.config_dir / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)
        home = self.root / "home"
        home.mkdir(parents=True, exist_ok=True)
        self.port = free_port()
        self.remote_port = free_port()
        self.env = dict(BASE_ENV)
        self.env["HOME"] = str(home)
        self.env.update(env or {})
        self.args = tuple(args)
        self.proc: subprocess.Popen[str] | None = None
        self.output = ""

    def command(self) -> list[str]:
        return [
            sys.executable,
            "-m",
            "esphome_device_builder",
            str(self.config_dir),
            "--host",
            "127.0.0.1",
            "--port",
            str(self.port),
            "--remote-build-port",
            str(self.remote_port),
            "--log-level",
            "warning",
            *self.args,
        ]

    def start(self) -> "Dashboard":
        self.proc = subprocess.Popen(
            self.command(),
            cwd=str(WORKSPACE),
            env=self.env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            text=True,
        )
        return self

    # -- lifecycle -------------------------------------------------------
    def wait_ready(self, timeout: float = START_TIMEOUT) -> bool:
        """True once the HTTP port answers; False if the process exits first."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.proc is not None and self.proc.poll() is not None:
                self._collect()
                return False
            try:
                status, _ = self.http("/version", timeout=3)
            except OSError:
                time.sleep(0.2)
                continue
            if status == 200:
                return True
            time.sleep(0.2)
        return False

    def wait_exit(self, timeout: float = 60.0) -> int | None:
        """Wait for the process to exit; return its code, or None on timeout."""
        if self.proc is None:
            raise RuntimeError("not started")
        try:
            code = self.proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            return None
        self._collect()
        return code

    def _collect(self) -> None:
        if self.proc is not None and self.proc.stdout is not None:
            try:
                self.output = self.proc.stdout.read()
            except (OSError, ValueError):
                self.output = ""

    def stop(self) -> None:
        if self.proc is None or self.proc.poll() is not None:
            return
        try:
            os.killpg(os.getpgid(self.proc.pid), signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            pass
        try:
            self.proc.wait(timeout=STOP_TIMEOUT)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(os.getpgid(self.proc.pid), signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                pass

    # -- HTTP ------------------------------------------------------------
    def http(self, path: str, *, auth: tuple[str, str] | None = None,
             timeout: float = 15) -> tuple[int, str]:
        request = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}")
        if auth is not None:
            raw = f"{auth[0]}:{auth[1]}".encode("utf-8")
            request.add_header("Authorization", "Basic " + base64.b64encode(raw).decode("ascii"))
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return int(response.status), response.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as err:
            return int(err.code), err.read().decode("utf-8", "replace")

    # -- WebSocket -------------------------------------------------------
    def ws_exchange(self, commands: list[dict], *, timeout: float = 30) -> list[dict]:
        """Connect, read the server info frame, then one reply per command."""
        port = self.port

        async def _run() -> list[dict]:
            import aiohttp

            frames: list[dict] = []
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(
                    f"http://127.0.0.1:{port}/ws", timeout=aiohttp.ClientTimeout(total=timeout)
                ) as ws:
                    first = await ws.receive(timeout=timeout)
                    frames.append(json.loads(first.data))
                    for command in commands:
                        await ws.send_json(command)
                        reply = await ws.receive(timeout=timeout)
                        frames.append(json.loads(reply.data))
            return frames

        return asyncio.run(_run())


def reached_inventory(status: int, body: str) -> bool:
    """True when a response actually served the configured device inventory."""
    return 200 <= status < 300 and DEVICE_NAME in body
