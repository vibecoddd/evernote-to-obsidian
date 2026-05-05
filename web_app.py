#!/usr/bin/env python3
"""Local Web entry point for the release migration tool."""

import sys
from pathlib import Path

src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from evernote_to_obsidian.web import main


if __name__ == "__main__":
    main()

