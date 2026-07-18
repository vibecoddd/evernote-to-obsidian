from __future__ import annotations

import socket
import sys
import time
import urllib.request
from pathlib import Path
from typing import Callable


class StartupError(RuntimeError):
    """Raised when the embedded Web service cannot become ready."""


def get_resource_root() -> Path:
    frozen_root = getattr(sys, "_MEIPASS", None)
    if frozen_root:
        return Path(frozen_root)
    return Path(__file__).resolve().parent


def find_free_port(host: str = "127.0.0.1") -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


def wait_for_server(
    url: str,
    timeout: float = 10.0,
    interval: float = 0.1,
    opener: Callable = urllib.request.urlopen,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> None:
    deadline = clock() + timeout
    last_error: Exception | None = None

    while clock() < deadline:
        try:
            with opener(url, timeout=interval) as response:
                if response.status == 200:
                    return
                last_error = StartupError(
                    f"Embedded Web service returned HTTP {response.status}"
                )
        except Exception as error:
            last_error = error
        sleep(interval)

    detail = f": {last_error}" if last_error else ""
    raise StartupError(f"Embedded Web service did not become ready at {url}{detail}")
