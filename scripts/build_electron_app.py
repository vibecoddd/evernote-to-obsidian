#!/usr/bin/env python3
"""Build renderer, Electron main process, Python sidecar, and installer."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def npm_command() -> str:
    return "npm.cmd" if os.name == "nt" else "npm"


def run(command: list[str], project_root: Path) -> int:
    return subprocess.run(command, cwd=project_root, check=False).returncode


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Package the Electron desktop application.")
    targets = parser.add_mutually_exclusive_group()
    targets.add_argument("--mac", action="store_true")
    targets.add_argument("--win", action="store_true")
    args = parser.parse_args(arguments)

    project_root = Path(__file__).resolve().parents[1]
    npm = npm_command()
    commands = [
        [npm, "run", "build"],
        [sys.executable, "scripts/build_backend.py"],
        [
            npm,
            "exec",
            "electron-builder",
            "--",
            "--config",
            "packaging/electron-builder.yml",
        ],
    ]
    if args.mac:
        commands[-1].append("--mac")
    elif args.win:
        commands[-1].append("--win")

    for command in commands:
        result = run(command, project_root)
        if result:
            return result
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
