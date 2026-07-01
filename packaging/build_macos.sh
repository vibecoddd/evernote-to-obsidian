#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"
SPEC_PATH="${SPEC_PATH:-packaging/pyinstaller-evernote2obsidian.spec}"

"$PYTHON_BIN" -m pip install -r requirements-dev.txt
"$PYTHON_BIN" -m PyInstaller --clean --noconfirm "$SPEC_PATH"
"$PYTHON_BIN" packaging/smoke_test.py

echo "macOS bundle built under dist/evernote2obsidian"
