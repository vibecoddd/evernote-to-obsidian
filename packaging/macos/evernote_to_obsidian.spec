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
    exclude_binaries=True,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name=app_name,
)
BUNDLE(
    coll,
    name=f"{app_name}.app",
    bundle_identifier="com.evernote-to-obsidian.migrator",
)
