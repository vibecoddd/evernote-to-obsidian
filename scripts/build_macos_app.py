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
