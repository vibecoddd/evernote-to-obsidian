#!/usr/bin/env python3
"""Build the Python desktop sidecar with the active Python environment."""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path


def pyinstaller_command() -> list[str]:
    configured = os.environ.get("PYINSTALLER")
    if configured:
        return shlex.split(configured)
    return [sys.executable, "-m", "PyInstaller"]


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    command = [
        *pyinstaller_command(),
        "--noconfirm",
        "--clean",
        "--distpath",
        str(project_root / "dist" / "backend"),
        "--workpath",
        str(project_root / "build" / "backend"),
        str(project_root / "packaging" / "backend" / "evernote_backend.spec"),
    ]
    return subprocess.run(command, cwd=project_root, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
