#!/usr/bin/env python3
"""CLI entry point for the release migration tool."""

import sys
from pathlib import Path

src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from evernote_to_obsidian.cli import main


if __name__ == "__main__":
    sys.exit(main())
