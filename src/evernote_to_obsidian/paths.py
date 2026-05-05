from __future__ import annotations

import os
from pathlib import Path


APP_DIR_NAME = ".evernote2obsidian"


def app_data_dir(explicit: str | Path | None = None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    env_value = os.environ.get("EVERNOTE2OBSIDIAN_HOME")
    if env_value:
        return Path(env_value).expanduser().resolve()
    return (Path.home() / APP_DIR_NAME).resolve()


def tasks_dir(root: str | Path | None = None) -> Path:
    return app_data_dir(root) / "tasks"


def task_dir(task_id: str, root: str | Path | None = None) -> Path:
    return tasks_dir(root) / task_id

