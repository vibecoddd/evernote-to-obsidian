"""End-to-end smoke checks for the Electron Python sidecar."""

from __future__ import annotations

import json
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent


def find_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def test_desktop_sidecar_starts_on_loopback_healthz_and_exits():
    port = find_loopback_port()
    process = subprocess.Popen(
        [sys.executable, "backend_app.py", "--port", str(port)],
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    health_url = f"http://127.0.0.1:{port}/api/healthz"
    deadline = time.monotonic() + 15
    last_error: Exception | None = None

    try:
        while time.monotonic() < deadline:
            if process.poll() is not None:
                output = process.stdout.read() if process.stdout else ""
                raise AssertionError(
                    f"sidecar exited before health check passed with code "
                    f"{process.returncode}\n{output}"
                )

            try:
                with urllib.request.urlopen(health_url, timeout=0.5) as response:
                    assert response.geturl().startswith("http://127.0.0.1:")
                    assert response.status == 200
                    assert json.loads(response.read().decode("utf-8")) == {
                        "status": "ok"
                    }
                    break
            except (OSError, urllib.error.URLError) as exc:
                last_error = exc
                time.sleep(0.1)
        else:
            output = process.stdout.read() if process.stdout else ""
            raise AssertionError(
                f"sidecar did not pass {health_url} before deadline; "
                f"last error: {last_error}\n{output}"
            )
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)

    assert process.poll() is not None
