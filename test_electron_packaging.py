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
