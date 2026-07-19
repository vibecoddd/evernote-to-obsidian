"""Static contract checks for the Electron Python-sidecar packaging files."""

from __future__ import annotations

import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent


# These are every Electron/macOS documentation entry point that presents an npm
# command to a developer. Historical macOS documents remain in scope because
# they retain actionable quick-reference commands; no prose-only exclusion is
# needed because the matcher recognizes complete npm invocations, not words.
ELECTRON_NPM_COMMAND_ENTRY_POINTS = (
    "README.md",
    "ELECTRON_CLIENT.md",
    "MACOS_CLIENT.md",
    "docs/superpowers/plans/2026-07-18-electron-desktop-client.md",
    "docs/superpowers/specs/2026-07-18-electron-desktop-client-design.md",
    "docs/superpowers/plans/2026-07-18-macos-client.md",
    "docs/superpowers/specs/2026-07-18-macos-client-design.md",
)

# Match only executable npm forms used by this project, rather than incidental
# mentions of "npm" or unsupported command-like prose.
NPM_COMMAND_PATTERN = re.compile(
    r"\bnpm[ \t]+(?:"
    r"(?:install|ci)(?=$|\s)"
    r"|test(?=$|\s)(?:[ \t]+(?:--[^\s`]*|-[^\s`]+))*(?=$|\s)"
    r"|exec[ \t]+(?!-)[^\s`]+(?=$|\s)"
    r"|run[ \t]+[A-Za-z0-9][A-Za-z0-9:._-]*(?=$|\s)"
    r")"
)


def read_project_file(relative_path: str) -> str:
    return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")


def documented_npm_commands(documentation: str) -> list[re.Match[str]]:
    """Return every supported npm invocation shown in an Electron doc."""
    return list(NPM_COMMAND_PATTERN.finditer(documentation))


def test_documented_npm_commands_only_matches_supported_executable_forms():
    documentation = """
    npm install --ignore-scripts
    npm ci
    npm test -- --run
    npm run build
    npm run build:renderer
    npm run build:electron
    npm run package:mac
    npm run package:win
    npm run package:current
    npm run dev:renderer
    npm exec electron-builder -- --mac
    npm build
    npm package:mac
    npm exec
    npm run
    npm command
    """

    assert [match.group(0) for match in documented_npm_commands(documentation)] == [
        "npm install",
        "npm ci",
        "npm test -- --run",
        "npm run build",
        "npm run build:renderer",
        "npm run build:electron",
        "npm run package:mac",
        "npm run package:win",
        "npm run package:current",
        "npm run dev:renderer",
        "npm exec electron-builder",
    ]


def test_documented_npm_commands_rejects_incomplete_or_nonterminal_forms():
    for command in (
        "npm exec -- --mac",
        "npm test:frontend",
        "npm run",
        "npm run build:renderer!",
        "npm install:all",
        "npm ci:clean",
    ):
        assert documented_npm_commands(command) == [], command


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
        assert "scripts/run_python_build.cjs" in package["scripts"][command]


def test_package_manifest_uses_node_launcher_instead_of_bare_python():
    package = json.loads(read_project_file("package.json"))
    launcher = read_project_file("scripts/run_python_build.cjs")

    for command in ("package:mac", "package:win", "package:current"):
        script = package["scripts"][command]
        assert script.startswith("node scripts/run_python_build.cjs")
        assert not script.startswith("python ")
        assert "scripts/build_electron_app.py" not in script

    assert "build_electron_app.py" in launcher
    assert ".venv" in launcher
    assert "python3" in launcher
    assert "sys.version_info" in launcher


def test_electron_runtime_package_is_dev_dependency_only():
    package = json.loads(read_project_file("package.json"))
    lockfile = json.loads(read_project_file("package-lock.json"))

    assert "electron" not in package["dependencies"]
    assert package["devDependencies"]["electron"] == "43.1.1"
    assert "electron" not in lockfile["packages"][""]["dependencies"]
    assert lockfile["packages"][""]["devDependencies"]["electron"] == "43.1.1"


def test_electron_type_script_output_matches_package_entrypoint():
    package = json.loads(read_project_file("package.json"))
    tsconfig = json.loads(read_project_file("tsconfig.electron.json"))

    assert package["main"] == "dist-electron/main.js"
    assert tsconfig["compilerOptions"]["outDir"] == "dist-electron"
    assert tsconfig["compilerOptions"]["rootDir"] == "electron"
    assert "electron/main.ts" in tsconfig["include"]
    assert "electron/preload.ts" in tsconfig["include"]
    assert "electron/main.test.ts" not in tsconfig["include"]


def test_vite_renderer_uses_relative_assets_for_file_url_packaging():
    config = read_project_file("vite.config.ts")

    assert 'base: "./"' in config


def test_electron_build_script_cleans_stale_output_before_compile():
    package = json.loads(read_project_file("package.json"))
    cleaner = read_project_file("scripts/clean_dist_electron.cjs")

    assert package["scripts"]["build:electron"].startswith(
        "node scripts/clean_dist_electron.cjs && "
    )
    assert "dist-electron" in cleaner
    assert "rmSync" in cleaner
    assert "recursive: true" in cleaner
    assert "force: true" in cleaner


def test_manifest_and_docs_define_a_clean_checkout_electron_launch_flow():
    package = json.loads(read_project_file("package.json"))
    documentation = read_project_file("ELECTRON_CLIENT.md")

    assert package["engines"]["node"] == ">=22.12.0"
    assert "Node.js >=22.12.0" in documentation
    assert "npm 的 engine 警告不足以" in documentation
    assert "发布打包必须使用 Node 22.12+" in documentation
    assert package["main"] == "dist-electron/main.js"
    assert package["scripts"]["build:renderer"] == "vite build --config vite.config.ts"
    assert "tsc -p tsconfig.electron.json" in package["scripts"]["build:electron"]
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


def test_every_documented_electron_npm_command_requires_supported_node_first():
    prerequisite = "Node.js >=22.12.0"
    npm_warning_caveat = "npm 的 engine 警告不足以"

    for relative_path in ELECTRON_NPM_COMMAND_ENTRY_POINTS:
        documentation = read_project_file(relative_path)
        npm_commands = documented_npm_commands(documentation)
        assert prerequisite in documentation, relative_path
        assert npm_warning_caveat in documentation, relative_path

        for npm_command in npm_commands:
            command_offset = npm_command.start()
            prior_documentation = documentation[:command_offset]
            command = npm_command.group(0)
            assert prerequisite in prior_documentation, f"{relative_path}: {command}"
            assert npm_warning_caveat in prior_documentation, f"{relative_path}: {command}"


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
