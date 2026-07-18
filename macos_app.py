from __future__ import annotations

import socket
import sys
import time
import urllib.request
import platform
import threading
from multiprocessing import freeze_support
from pathlib import Path
from typing import Any, Callable


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


def start_web_server(migrator: Any, host: str, port: int) -> threading.Thread:
    thread = threading.Thread(
        target=migrator.run,
        kwargs={"host": host, "port": port, "debug": False},
        name="macos-web-server",
        daemon=True,
    )
    thread.start()
    return thread


def create_web_migrator():
    src_dir = get_resource_root() / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

    from web_app import WebMigrator

    return WebMigrator()


def import_webview():
    try:
        import webview
    except ImportError as error:
        raise StartupError(
            "PyWebView is not installed; install requirements.txt before running the macOS client"
        ) from error
    return webview


def run_desktop_app(
    migrator_factory=create_web_migrator,
    webview_module=None,
    readiness=wait_for_server,
) -> None:
    if platform.system() != "Darwin":
        raise StartupError("The macOS desktop client must be run on macOS")

    host = "127.0.0.1"
    port = find_free_port(host)
    migrator = migrator_factory()
    start_web_server(migrator, host, port)

    url = f"http://{host}:{port}/"
    readiness(url)
    webview_module = webview_module or import_webview()
    webview_module.create_window(
        "印象笔记到 Obsidian",
        url,
        width=1120,
        height=780,
        min_size=(800, 600),
        resizable=True,
    )
    webview_module.start()


def main() -> int:
    freeze_support()
    try:
        run_desktop_app()
    except StartupError as error:
        print(f"❌ macOS 客户端启动失败: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
