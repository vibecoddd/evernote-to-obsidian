"""Static contract checks for the Electron Python-sidecar packaging files."""

from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent


def read_project_file(relative_path: str) -> str:
    return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")


def test_pyinstaller_spec_builds_the_backend_entry_with_runtime_assets():
    spec = read_project_file("packaging/backend/evernote_backend.spec")

    assert "backend_app.py" in spec
    for asset in ("templates", "static", "src"):
        assert f'project_root / "{asset}"' in spec
    for runtime_package in ("eventlet", "engineio", "socketio"):
        assert runtime_package in spec
    assert 'name="evernote-backend"' in spec
    assert "webview" not in spec.lower()
    assert "BUNDLE(" not in spec


def test_electron_builder_config_packages_renderer_and_backend_for_each_platform():
    config = read_project_file("packaging/electron-builder.yml")

    assert "appId: com.evernote-to-obsidian.migrator" in config
    assert "productName: 印象笔记迁移工具" in config
    assert "dist-electron/**/*" in config
    assert "dist/renderer/**/*" in config
    assert "extraResources:" in config
    assert "from: dist/backend" in config
    assert "to: backend" in config
    assert "target: dmg" in config
    assert "target: nsis" in config
    assert "directories:" in config
    assert "output: release" in config
    assert "files:" in config
    assert "- dist-electron/**/*" in config
    assert "- release/**/*" not in config


def test_backend_build_script_constructs_pyinstaller_command_without_running_it(monkeypatch):
    from scripts import build_backend

    calls: list[tuple[list[str], Path]] = []

    class Result:
        returncode = 0

    def run(command: list[str], *, cwd: Path, check: bool) -> Result:
        calls.append((command, cwd))
        assert check is False
        return Result()

    monkeypatch.delenv("PYINSTALLER", raising=False)
    monkeypatch.setattr(build_backend.subprocess, "run", run)

    assert build_backend.main() == 0
    command, cwd = calls.pop()
    assert command[:3] == [build_backend.sys.executable, "-m", "PyInstaller"]
    assert "--distpath" in command
    assert command[command.index("--distpath") + 1] == str(PROJECT_ROOT / "dist" / "backend")
    assert "--workpath" in command
    assert command[command.index("--workpath") + 1] == str(PROJECT_ROOT / "build" / "backend")
    assert command[-1] == str(PROJECT_ROOT / "packaging" / "backend" / "evernote_backend.spec")
    assert cwd == PROJECT_ROOT


def test_electron_build_script_runs_build_backend_then_builder(monkeypatch):
    from scripts import build_electron_app

    calls: list[list[str]] = []

    class Result:
        returncode = 0

    def run(command: list[str], *, cwd: Path, check: bool) -> Result:
        calls.append(command)
        assert cwd == PROJECT_ROOT
        assert check is False
        return Result()

    monkeypatch.setattr(build_electron_app.subprocess, "run", run)

    assert build_electron_app.main(["--mac"]) == 0
    assert calls == [
        [build_electron_app.npm_command(), "run", "build"],
        [build_electron_app.sys.executable, "scripts/build_backend.py"],
        [
            build_electron_app.npm_command(),
            "exec",
            "electron-builder",
            "--",
            "--config",
            "packaging/electron-builder.yml",
            "--mac",
        ],
    ]


def test_package_manifest_exposes_platform_packaging_commands():
    package = json.loads(read_project_file("package.json"))

    for command in ("package:mac", "package:win", "package:current"):
        assert "scripts/build_electron_app.py" in package["scripts"][command]


def test_manifest_and_docs_define_a_clean_checkout_electron_launch_flow():
    package = json.loads(read_project_file("package.json"))
    documentation = read_project_file("ELECTRON_CLIENT.md")

    assert package["engines"]["node"] == ">=22.12.0"
    assert "Node.js >=22.12.0" in documentation
    assert "npm 的 engine 警告不足以" in documentation
    assert "发布打包必须使用 Node 22.12+" in documentation
    assert package["main"] == "dist-electron/main.js"
    assert package["scripts"]["build:renderer"] == "vite build --config vite.config.ts"
    assert package["scripts"]["build:electron"] == "tsc -p tsconfig.electron.json"
    assert "npm run build:renderer && npm run build:electron" in documentation
    assert "npx electron ." in documentation
    assert "仓库根目录" in documentation
    assert "`npm run dev:renderer` 只启动 Vite renderer 开发服务器" in documentation


def test_readme_documents_electron_platform_packaging_commands():
    readme = read_project_file("README.md")

    assert "Node.js >=22.12.0" in readme
    assert "发布打包必须使用 Node 22.12+" in readme
    for command in ("npm install", "npm run package:mac", "npm run package:win"):
        assert command in readme


def test_electron_client_documentation_covers_task_eight_packaging_contract():
    documentation = read_project_file("ELECTRON_CLIENT.md")

    for topic in (
        "npm install",
        "npm run package:mac",
        "npm run package:win",
        "127.0.0.1",
        "动态端口",
        "Python sidecar",
        "/api/healthz",
        "15 秒",
        "停止 sidecar",
        ".dmg",
        "NSIS",
        "Windows 路径",
        "缺失",
        "签名",
        "公证",
        "不需要 PyWebView",
    ):
        assert topic in documentation
