from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .markdown import MarkdownConverter
from .models import Note, TaskStats, utc_now_iso


@dataclass
class WriteResult:
    stats: TaskStats = field(default_factory=TaskStats)
    written_files: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)


class ObsidianWriter:
    def __init__(
        self,
        vault_path: str | Path,
        attachment_dir: str = "attachments",
        overwrite_existing: bool = False,
    ):
        self.vault_path = Path(vault_path).expanduser().resolve()
        self.attachment_dir = attachment_dir
        self.overwrite_existing = overwrite_existing
        self.converter = MarkdownConverter()
        self._used_note_paths: set[Path] = set()

    def write_notes(self, notes: list[Note], notebook_name: str, task_id: str) -> WriteResult:
        self.vault_path.mkdir(parents=True, exist_ok=True)
        result = WriteResult()
        result.stats.total_notes = len(notes)
        migrated_at = utc_now_iso()
        notebook_dir = self.vault_path / self._sanitize_component(notebook_name)
        notebook_dir.mkdir(parents=True, exist_ok=True)

        note_entries: list[tuple[Note, str]] = []
        for note in notes:
            try:
                attachment_links, attachment_metadata = self._write_attachments(note)
                markdown = self.converter.convert(
                    note=note,
                    attachment_links=attachment_links,
                    attachment_metadata=attachment_metadata,
                    task_id=task_id,
                    migrated_at=migrated_at,
                )
                note_path = self._note_path(note, notebook_dir)
                note_path.write_text(markdown, encoding="utf-8")
                self._set_timestamps(note_path, note)
                rel_path = note_path.relative_to(self.vault_path).as_posix()
                result.written_files.append(rel_path)
                note_entries.append((note, rel_path))
                result.stats.converted_notes += 1
                result.stats.total_attachments += len(attachment_metadata)
            except Exception as exc:
                result.stats.skipped_notes += 1
                result.errors.append({"message": str(exc), "note": note.title})

        self._write_index(notebook_name, notebook_dir, note_entries)
        self._write_vault_report(task_id, result)
        return result

    def _write_attachments(self, note: Note) -> tuple[dict[str, str], list[dict[str, Any]]]:
        if not note.resources:
            return {}, []
        note_attachment_dir = self.vault_path / self.attachment_dir / self._sanitize_component(note.note_id())
        note_attachment_dir.mkdir(parents=True, exist_ok=True)
        links: dict[str, str] = {}
        metadata: list[dict[str, Any]] = []
        used: set[str] = set()

        for resource in note.resources:
            resource_hash = resource.ensure_hash()
            filename = self._unique_filename(self._sanitize_component(resource.filename), used)
            used.add(filename)
            path = note_attachment_dir / filename
            path.write_bytes(resource.data)
            relative = path.relative_to(self.vault_path).as_posix()
            links[resource_hash] = self._obsidian_link(relative, filename, resource.mime_type)
            metadata.append(
                {
                    "filename": resource.filename,
                    "path": relative,
                    "mime_type": resource.mime_type,
                    "hash": resource_hash,
                    "size": resource.size,
                }
            )
        return links, metadata

    def _note_path(self, note: Note, notebook_dir: Path) -> Path:
        base = self._sanitize_component(note.title or "Untitled Note")
        candidate = notebook_dir / f"{base}.md"
        if self._path_available(candidate):
            self._used_note_paths.add(candidate)
            return candidate

        candidate = notebook_dir / f"{base}-{note.short_id}.md"
        counter = 1
        while not self._path_available(candidate):
            candidate = notebook_dir / f"{base}-{note.short_id}-{counter}.md"
            counter += 1
        self._used_note_paths.add(candidate)
        return candidate

    def _path_available(self, path: Path) -> bool:
        return self.overwrite_existing or (path not in self._used_note_paths and not path.exists())

    def _write_index(self, notebook_name: str, notebook_dir: Path, note_entries: list[tuple[Note, str]]) -> None:
        index_path = notebook_dir / f"{self._sanitize_component(notebook_name)}_Index.md"
        lines = [
            f"# {notebook_name} Index",
            "",
            f"Generated: {utc_now_iso()}",
            f"Total notes: {len(note_entries)}",
            "",
        ]
        for note, rel_path in sorted(note_entries, key=lambda item: item[0].title):
            stem = Path(rel_path).stem
            tag_text = " ".join(f"#{tag}" for tag in note.tags)
            suffix = f" {tag_text}" if tag_text else ""
            lines.append(f"- [[{stem}]] - {note.title}{suffix}")
        index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _write_vault_report(self, task_id: str, result: WriteResult) -> None:
        report_dir = self.vault_path / "migration-reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        data = {
            "task_id": task_id,
            "stats": result.stats.to_dict(),
            "written_files": result.written_files,
            "warnings": result.warnings,
            "errors": result.errors,
        }
        (report_dir / f"{task_id}.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        lines = [
            f"# Migration Report: {task_id}",
            "",
            f"- Total notes: {result.stats.total_notes}",
            f"- Converted notes: {result.stats.converted_notes}",
            f"- Skipped notes: {result.stats.skipped_notes}",
            f"- Attachments: {result.stats.total_attachments}",
            "",
            "## Written Files",
            "",
        ]
        lines.extend(f"- `{path}`" for path in result.written_files)
        (report_dir / f"{task_id}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _obsidian_link(self, relative_path: str, filename: str, mime_type: str) -> str:
        if mime_type.startswith("image/"):
            return f"![[{relative_path}]]"
        return f"[[{relative_path}|{filename}]]"

    def _unique_filename(self, filename: str, used: set[str]) -> str:
        candidate = filename
        stem = Path(filename).stem
        suffix = Path(filename).suffix
        counter = 1
        while candidate in used:
            candidate = f"{stem}-{counter}{suffix}"
            counter += 1
        return candidate

    def _sanitize_component(self, value: str) -> str:
        value = value.strip() or "untitled"
        value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value)
        value = re.sub(r"_+", "_", value).strip(" ._")
        if not value:
            value = "untitled"
        reserved = {
            "CON",
            "PRN",
            "AUX",
            "NUL",
            "COM1",
            "COM2",
            "COM3",
            "COM4",
            "COM5",
            "COM6",
            "COM7",
            "COM8",
            "COM9",
            "LPT1",
            "LPT2",
            "LPT3",
            "LPT4",
            "LPT5",
            "LPT6",
            "LPT7",
            "LPT8",
            "LPT9",
        }
        if value.upper() in reserved:
            value = f"{value}_"
        return value[:120].rstrip(" .") or "untitled"

    def _set_timestamps(self, path: Path, note: Note) -> None:
        timestamp = None
        if note.updated:
            timestamp = note.updated.timestamp()
        elif note.created:
            timestamp = note.created.timestamp()
        if timestamp is not None:
            try:
                os.utime(path, (timestamp, timestamp))
            except OSError:
                pass

