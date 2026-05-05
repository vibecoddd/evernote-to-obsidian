from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


@dataclass
class Resource:
    data: bytes
    mime_type: str
    filename: str
    hash: str | None = None
    width: int | None = None
    height: int | None = None

    @property
    def size(self) -> int:
        return len(self.data)

    def ensure_hash(self) -> str:
        if not self.hash:
            self.hash = hashlib.md5(self.data).hexdigest()
        return self.hash


@dataclass
class Note:
    title: str
    content: str
    created: datetime | None = None
    updated: datetime | None = None
    tags: list[str] = field(default_factory=list)
    notebook: str | None = None
    source_url: str | None = None
    author: str | None = None
    source: str = "Evernote"
    resources: list[Resource] = field(default_factory=list)
    attributes: dict[str, Any] = field(default_factory=dict)
    guid: str | None = None
    content_hash: str | None = None

    def note_id(self) -> str:
        if self.guid:
            return self.guid
        if self.content_hash:
            return self.content_hash
        digest = hashlib.sha256(f"{self.title}\n{self.content}".encode("utf-8")).hexdigest()
        self.content_hash = digest
        return digest

    @property
    def short_id(self) -> str:
        return self.note_id()[:8]


@dataclass
class MigrationConfig:
    vault_path: Path
    app_data_dir: Path
    source_mode: str = "import_enex"
    backend: str = "china"
    attachment_dir: str = "attachments"
    create_indexes: bool = True
    overwrite_existing: bool = False
    link_style: str = "wiki"

    def as_json(self) -> dict[str, Any]:
        data = asdict(self)
        data["vault_path"] = str(self.vault_path)
        data["app_data_dir"] = str(self.app_data_dir)
        return data


@dataclass
class TaskStats:
    total_notes: int = 0
    converted_notes: int = 0
    skipped_notes: int = 0
    total_attachments: int = 0

    def to_dict(self) -> dict[str, int]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "TaskStats":
        data = data or {}
        return cls(
            total_notes=int(data.get("total_notes", 0)),
            converted_notes=int(data.get("converted_notes", 0)),
            skipped_notes=int(data.get("skipped_notes", 0)),
            total_attachments=int(data.get("total_attachments", 0)),
        )

