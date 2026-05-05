from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from . import __version__
from .models import TaskStats, utc_now_iso
from .paths import tasks_dir


PHASES = (
    "created",
    "auth_ready",
    "synced",
    "exported",
    "parsed",
    "written",
    "verified",
    "completed",
    "failed",
)


@dataclass
class TaskState:
    task_id: str
    source_mode: str
    vault_path: Path
    app_data_dir: Path
    phase: str = "created"
    status: str = "running"
    enex_files: list[str] = field(default_factory=list)
    written_files: list[str] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    stats: TaskStats = field(default_factory=TaskStats)
    phase_history: list[dict[str, str]] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)
    versions: dict[str, str] = field(default_factory=lambda: {"tool": __version__})

    @property
    def task_dir(self) -> Path:
        return self.app_data_dir / "tasks" / self.task_id

    @property
    def state_path(self) -> Path:
        return self.task_dir / "state.json"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["vault_path"] = str(self.vault_path)
        data["app_data_dir"] = str(self.app_data_dir)
        data["stats"] = self.stats.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskState":
        return cls(
            task_id=data["task_id"],
            source_mode=data["source_mode"],
            vault_path=Path(data["vault_path"]),
            app_data_dir=Path(data["app_data_dir"]),
            phase=data.get("phase", "created"),
            status=data.get("status", "running"),
            enex_files=list(data.get("enex_files", [])),
            written_files=list(data.get("written_files", [])),
            errors=list(data.get("errors", [])),
            warnings=list(data.get("warnings", [])),
            stats=TaskStats.from_dict(data.get("stats")),
            phase_history=list(data.get("phase_history", [])),
            created_at=data.get("created_at", utc_now_iso()),
            updated_at=data.get("updated_at", utc_now_iso()),
            versions=dict(data.get("versions", {"tool": __version__})),
        )


class TaskStateStore:
    def __init__(self, app_data_root: str | Path):
        self.app_data_dir = Path(app_data_root).expanduser().resolve()
        self.tasks_dir = tasks_dir(self.app_data_dir)
        self.tasks_dir.mkdir(parents=True, exist_ok=True)

    def create(
        self,
        source_mode: str,
        vault_path: str | Path,
        task_id: str | None = None,
    ) -> TaskState:
        task_id = task_id or uuid.uuid4().hex
        state = TaskState(
            task_id=task_id,
            source_mode=source_mode,
            vault_path=Path(vault_path).expanduser().resolve(),
            app_data_dir=self.app_data_dir,
        )
        state.task_dir.mkdir(parents=True, exist_ok=True)
        self.save(state)
        return state

    def load(self, task_id: str) -> TaskState:
        path = self.tasks_dir / task_id / "state.json"
        with path.open("r", encoding="utf-8") as handle:
            return TaskState.from_dict(json.load(handle))

    def save(self, state: TaskState) -> None:
        state.updated_at = utc_now_iso()
        state.task_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = state.state_path.with_suffix(".json.tmp")
        tmp_path.write_text(
            json.dumps(state.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp_path.replace(state.state_path)

    def transition(self, state: TaskState, phase: str, message: str = "") -> TaskState:
        if phase not in PHASES:
            raise ValueError(f"Unknown task phase: {phase}")
        state.phase = phase
        state.status = "failed" if phase == "failed" else ("completed" if phase == "completed" else "running")
        state.phase_history.append(
            {
                "phase": phase,
                "message": message,
                "created_at": utc_now_iso(),
            }
        )
        self.save(state)
        return state

