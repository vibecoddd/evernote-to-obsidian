# macOS 客户端 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为现有印象笔记到 Obsidian 迁移工具增加一个可双击启动、可由 PyInstaller 打包为独立 macOS `.app` 的桌面客户端。

**Architecture:** 新增 `macos_app.py` 作为桌面入口，在 loopback 动态端口上以 daemon 线程启动现有 `WebMigrator`，等待首页可用后交给 PyWebView 显示。PyInstaller spec 显式收集 `templates/`、`static/`、`src/` 和运行时隐藏导入；迁移业务和 Web API 不复制到桌面层。

**Tech Stack:** Python 3.12+, Flask/Flask-SocketIO, PyWebView, PyInstaller, pytest, macOS WebKit.

## Global Constraints

- 客户端只监听 `127.0.0.1`，不得使用 `0.0.0.0` 或允许局域网访问。
- 客户端必须选择动态空闲端口，不得依赖固定的 5000 端口。
- 用户运行 `.app` 时不需要预装 Python 或手动启动 Flask 服务。
- 不改变现有迁移算法和 Web API 的业务语义。
- 每个生产代码行为都必须先有一个观察到失败的测试；配置文件和构建脚本可按配置例外处理。
- 不修改用户已有的 `欢迎使用Obsidian.md` 工作区改动。

---

### Task 1: 添加桌面运行依赖与可测试的运行时辅助函数

**Files:**
- Create: `test_macos_app.py`
- Create: `macos_app.py`
- Modify: `requirements.txt:10-13`

**Interfaces:**
- Produces `get_resource_root() -> pathlib.Path`.
- Produces `find_free_port(host: str = "127.0.0.1") -> int`.
- Produces `wait_for_server(url: str, timeout: float = 10.0, interval: float = 0.1, opener=urllib.request.urlopen) -> None`.
- Raises `StartupError` when readiness polling reaches its deadline or receives an HTTP status other than 200.

- [ ] **Step 1: Write the failing tests for resource roots and port selection**

```python
# test_macos_app.py
from pathlib import Path
import socket

import macos_app


def test_resource_root_uses_project_directory_when_not_frozen(monkeypatch):
    monkeypatch.delattr(macos_app.sys, "_MEIPASS", raising=False)

    assert macos_app.get_resource_root() == Path(macos_app.__file__).resolve().parent


def test_resource_root_uses_pyinstaller_directory_when_frozen(monkeypatch, tmp_path):
    monkeypatch.setattr(macos_app.sys, "_MEIPASS", str(tmp_path), raising=False)

    assert macos_app.get_resource_root() == tmp_path


def test_find_free_port_returns_loopback_port():
    port = macos_app.find_free_port()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", port))
        assert probe.getsockname()[1] == port
```

- [ ] **Step 2: Run the focused tests to verify they fail for the missing module**

Run: `.venv/bin/pytest -q test_macos_app.py`

Expected: FAIL with `ModuleNotFoundError: No module named 'macos_app'`.

- [ ] **Step 3: Write the failing readiness tests**

```python
class FakeResponse:
    def __init__(self, status=200):
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def test_wait_for_server_retries_until_http_200():
    responses = [OSError("not ready"), FakeResponse(200)]
    sleeps = []

    def opener(_url, timeout):
        value = responses.pop(0)
        if isinstance(value, Exception):
            raise value
        return value

    macos_app.wait_for_server(
        "http://127.0.0.1:43123/",
        timeout=1,
        interval=0.01,
        opener=opener,
        sleep=sleeps.append,
        clock=iter([0.0, 0.1, 0.2]).__next__,
    )

    assert sleeps == [0.01]


def test_wait_for_server_raises_startup_error_after_deadline():
    def opener(_url, timeout):
        raise OSError("connection refused")

    times = iter([0.0, 0.5, 1.1])

    try:
        macos_app.wait_for_server(
            "http://127.0.0.1:43123/",
            timeout=1,
            interval=0.01,
            opener=opener,
            sleep=lambda _seconds: None,
            clock=times.__next__,
        )
    except macos_app.StartupError as error:
        assert "127.0.0.1:43123" in str(error)
    else:
        raise AssertionError("wait_for_server should time out")
```

- [ ] **Step 4: Run the readiness tests to verify the failure is about the missing behavior**

Run: `.venv/bin/pytest -q test_macos_app.py`

Expected: FAIL with `AttributeError` for `wait_for_server` and `StartupError` not yet being defined.

- [ ] **Step 5: Implement the minimal runtime helpers**

```python
# macos_app.py
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
```

- [ ] **Step 6: Add the desktop runtime dependency**

Append this line to `requirements.txt` after the Flask-SocketIO dependencies:

```text
pywebview>=5.4.0
```

- [ ] **Step 7: Run the focused tests to verify they pass**

Run: `.venv/bin/pytest -q test_macos_app.py`

Expected: PASS for the resource-root, port, retry, and timeout tests.

- [ ] **Step 8: Commit the tested runtime helpers**

```bash
git add macos_app.py test_macos_app.py requirements.txt
git commit -m "feat: add macOS desktop runtime helpers"
```

### Task 2: Add the desktop launcher and lifecycle integration

**Files:**
- Modify: `test_macos_app.py`
- Modify: `macos_app.py`

**Interfaces:**
- Produces `start_web_server(migrator, host, port) -> threading.Thread`.
- Produces `run_desktop_app(migrator_factory, webview_module, readiness=wait_for_server) -> None`.
- `run_desktop_app` calls `migrator.run(host="127.0.0.1", port=<dynamic>, debug=False)` and loads `http://127.0.0.1:<dynamic>/`.

- [ ] **Step 1: Write the failing lifecycle test**

```python
class FakeMigrator:
    def __init__(self):
        self.run_calls = []

    def run(self, **kwargs):
        self.run_calls.append(kwargs)


class FakeWebView:
    def __init__(self):
        self.window_calls = []
        self.start_calls = 0

    def create_window(self, title, url, **kwargs):
        self.window_calls.append((title, url, kwargs))
        return object()

    def start(self):
        self.start_calls += 1


def test_run_desktop_app_uses_dynamic_loopback_url(monkeypatch):
    migrator = FakeMigrator()
    webview = FakeWebView()
    readiness_urls = []

    monkeypatch.setattr(macos_app, "find_free_port", lambda: 43123)
    monkeypatch.setattr(
        macos_app,
        "start_web_server",
        lambda instance, host, port: instance.run(host=host, port=port, debug=False),
    )

    macos_app.run_desktop_app(
        migrator_factory=lambda: migrator,
        webview_module=webview,
        readiness=lambda url: readiness_urls.append(url),
    )

    assert migrator.run_calls == [
        {"host": "127.0.0.1", "port": 43123, "debug": False}
    ]
    assert readiness_urls == ["http://127.0.0.1:43123/"]
    assert webview.window_calls[0][1] == "http://127.0.0.1:43123/"
    assert webview.start_calls == 1
```

- [ ] **Step 2: Run the lifecycle test to verify it fails**

Run: `.venv/bin/pytest -q test_macos_app.py::test_run_desktop_app_uses_dynamic_loopback_url`

Expected: FAIL because `start_web_server` and `run_desktop_app` are not yet defined.

- [ ] **Step 3: Implement the launcher functions**

```python
import platform
import threading
from multiprocessing import freeze_support
from typing import Any


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
```

- [ ] **Step 4: Run focused lifecycle and helper tests**

Run: `.venv/bin/pytest -q test_macos_app.py`

Expected: PASS for all desktop launcher unit tests.

- [ ] **Step 5: Run import and syntax checks**

Run: `.venv/bin/python -m py_compile macos_app.py`

Expected: exit code 0 and no syntax errors.

- [ ] **Step 6: Commit the launcher**

```bash
git add macos_app.py test_macos_app.py
git commit -m "feat: launch Flask UI inside macOS window"
```

### Task 3: Add PyInstaller packaging configuration and build command

**Files:**
- Create: `packaging/macos/evernote_to_obsidian.spec`
- Create: `scripts/build_macos_app.py`
- Create: `requirements-macos-build.txt`

**Interfaces:**
- `scripts/build_macos_app.py` exits 0 only on macOS after invoking PyInstaller.
- The spec produces `dist/印象笔记迁移工具.app` and includes `templates/`, `static/`, and `src/` in the application bundle.

- [ ] **Step 1: Add the build-tool dependency file**

Create `requirements-macos-build.txt`:

```text
-r requirements.txt
pyinstaller>=6.10.0
```

- [ ] **Step 2: Write the PyInstaller spec**

Create `packaging/macos/evernote_to_obsidian.spec`:

```python
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules


project_root = Path(SPEC).resolve().parents[2]
app_name = "印象笔记迁移工具"
datas = [
    (str(project_root / "templates"), "templates"),
    (str(project_root / "static"), "static"),
    (str(project_root / "src"), "src"),
]
hiddenimports = ["web_app"]
for package in ("eventlet", "engineio", "socketio", "webview"):
    hiddenimports.extend(collect_submodules(package))


a = Analysis(
    [str(project_root / "macos_app.py")],
    pathex=[str(project_root), str(project_root / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)
BUNDLE(
    exe,
    name=f"{app_name}.app",
    bundle_identifier="com.evernote-to-obsidian.migrator",
)
```

- [ ] **Step 3: Write the macOS-only build command**

Create `scripts/build_macos_app.py`:

```python
#!/usr/bin/env python3
from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    if platform.system() != "Darwin":
        print("This build must run on macOS.", file=sys.stderr)
        return 2

    pyinstaller = os.environ.get("PYINSTALLER") or shutil.which("pyinstaller")
    if not pyinstaller:
        candidate = Path(sys.executable).with_name("pyinstaller")
        pyinstaller = str(candidate) if candidate.exists() else None
    if not pyinstaller:
        print(
            "PyInstaller is not installed. Run: python3 -m pip install -r requirements-macos-build.txt",
            file=sys.stderr,
        )
        return 2

    spec = project_root / "packaging" / "macos" / "evernote_to_obsidian.spec"
    result = subprocess.run(
        [pyinstaller, "--noconfirm", "--clean", str(spec)],
        cwd=project_root,
        check=False,
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Install build tools and run the build**

Run: `.venv/bin/pip install -r requirements-macos-build.txt`

Run: `.venv/bin/python scripts/build_macos_app.py`

Expected: PyInstaller exits 0 and creates `dist/印象笔记迁移工具.app`.

- [ ] **Step 5: Inspect the bundle contents**

Run: `test -d 'dist/印象笔记迁移工具.app' && test -f 'dist/印象笔记迁移工具.app/Contents/Info.plist' && find 'dist/印象笔记迁移工具.app/Contents' -maxdepth 3 -type d | rg '/(templates|static|src)$'`

Expected: all three resource directories are present inside the app bundle.

- [ ] **Step 6: Commit packaging files**

```bash
git add packaging/macos/evernote_to_obsidian.spec scripts/build_macos_app.py requirements-macos-build.txt
git commit -m "build: package macOS application with PyInstaller"
```

### Task 4: Document development, build, and verification workflow

**Files:**
- Create: `MACOS_CLIENT.md`
- Modify: `README.md` in the installation and usage sections

- [ ] **Step 1: Document developer installation and local desktop launch**

Add commands that use the project virtual environment:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-macos-build.txt
.venv/bin/python macos_app.py
```

Explain that local launch requires a macOS GUI session and opens the existing migration interface in a native window.

- [ ] **Step 2: Document packaging and artifact location**

Add:

```bash
.venv/bin/python scripts/build_macos_app.py
open "dist/印象笔记迁移工具.app"
```

Document that PyInstaller must be run on the target macOS architecture, that signing/notarization are release-owner steps, and that the application only binds a local loopback service.

- [ ] **Step 3: Add explicit troubleshooting for startup failures**

Document the three supported checks:

```bash
.venv/bin/python -m py_compile macos_app.py
.venv/bin/pytest -q test_macos_app.py
test -d "dist/印象笔记迁移工具.app"
```

Explain the expected messages for missing PyWebView, non-macOS execution, and failed local service readiness.

- [ ] **Step 4: Run documentation and repository checks**

Run: `git diff --check`

Run: `rg -n "macOS|PyWebView|PyInstaller|印象笔记迁移工具.app" README.md MACOS_CLIENT.md`

Expected: no whitespace errors and the documented commands/targets are present.

- [ ] **Step 5: Commit documentation**

```bash
git add README.md MACOS_CLIENT.md
git commit -m "docs: document macOS client workflow"
```

## Final Verification Checklist

- [ ] `.venv/bin/pytest -q test_macos_app.py` passes with zero failures.
- [ ] `.venv/bin/python -m py_compile macos_app.py` exits 0.
- [ ] Existing baseline failures are unchanged and are reported separately from new desktop tests.
- [ ] `scripts/build_macos_app.py` builds on macOS and creates `dist/印象笔记迁移工具.app`.
- [ ] Bundle contains templates, static assets, and src modules.
- [ ] A macOS GUI smoke test opens the home page; if the execution environment has no GUI session, the limitation is reported with the bundle-level evidence instead of claiming GUI success.
- [ ] `git status --short` shows only intentional source changes and the pre-existing user change to `欢迎使用Obsidian.md`.
