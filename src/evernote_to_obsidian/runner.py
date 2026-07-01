from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Callable

import yaml

from .enex import ENEXParser
from .events import ProgressEvent
from .paths import app_data_dir as default_app_data_dir
from .reports import write_task_reports
from .state import TaskState, TaskStateStore
from .writer import ObsidianWriter, WriteResult


ProgressCallback = Callable[[ProgressEvent], None]


class MigrationRunner:
    def __init__(self, app_data_dir: str | Path | None = None):
        self.app_data_dir = (
            Path(app_data_dir).expanduser().resolve() if app_data_dir else default_app_data_dir()
        )
        self.store = TaskStateStore(self.app_data_dir)

    def import_enex(
        self,
        enex_files: list[str | Path],
        vault_path: str | Path,
        task_id: str | None = None,
        progress_callback: ProgressCallback | None = None,
    ) -> TaskState:
        state = self.store.create("import_enex", vault_path=vault_path, task_id=task_id)
        state.enex_files = [str(Path(path).expanduser().resolve()) for path in enex_files]
        self.store.save(state)
        return self._run_import_state(state, progress_callback)

    def resume(self, task_id: str, progress_callback: ProgressCallback | None = None) -> TaskState:
        state = self.store.load(task_id)
        if state.phase == "completed":
            return state
        if not state.enex_files:
            raise ValueError(f"Task {task_id} has no ENEX inventory to resume")
        return self._run_import_state(state, progress_callback)

    def report(self, task_id: str) -> dict[str, object]:
        state = self.store.load(task_id)
        report_path = state.task_dir / "reports" / "report.json"
        if not report_path.exists():
            write_task_reports(state)
        import json

        return json.loads(report_path.read_text(encoding="utf-8"))

    def _run_import_state(
        self,
        state: TaskState,
        progress_callback: ProgressCallback | None,
    ) -> TaskState:
        parser = ENEXParser()
        writer = ObsidianWriter(state.vault_path)

        if state.phase not in {"parsed", "written", "verified", "completed"}:
            self._transition(state, "parsed", "Parsed ENEX inventory", 35, progress_callback)

        for enex_file in state.enex_files:
            enex_path = Path(enex_file).expanduser().resolve()
            enex_key = str(enex_path)
            if enex_key in state.processed_enex_files:
                continue

            notebook = parser.notebook_name(enex_path)
            result = writer.write_notes(
                parser.iter_notes(enex_path, notebook_name=notebook),
                notebook,
                task_id=state.task_id,
                source_enex=enex_key,
                skip_note_ids=state.processed_note_ids,
                on_note_written=lambda note_result: self._checkpoint_note(state, note_result),
            )
            state.stats.total_notes += result.stats.total_notes
            state.stats.skipped_notes += result.stats.skipped_notes
            state.warnings.extend(result.warnings)
            state.errors.extend(result.errors)
            if not result.errors:
                state.processed_enex_files.append(enex_key)
            self.store.save(state)

        writer.write_indexes_from_results(state.note_results)
        self._transition(state, "written", "Wrote Obsidian vault files", 75, progress_callback)

        self._verify_output(state)
        self._transition(state, "verified", "Verified output files", 90, progress_callback)
        self._transition(state, "completed", "Migration completed", 100, progress_callback)
        write_task_reports(state)
        return state

    def _merge_result(self, aggregate: WriteResult, result: WriteResult) -> None:
        aggregate.stats.converted_notes += result.stats.converted_notes
        aggregate.stats.skipped_notes += result.stats.skipped_notes
        aggregate.stats.total_attachments += result.stats.total_attachments
        aggregate.written_files.extend(result.written_files)
        aggregate.warnings.extend(result.warnings)
        aggregate.errors.extend(result.errors)

    def _checkpoint_note(self, state: TaskState, note_result: dict[str, object]) -> None:
        note_id = str(note_result.get("note_id") or "")
        path = str(note_result.get("path") or "")
        if note_id and note_id not in state.processed_note_ids:
            state.processed_note_ids.append(note_id)
        if path and path not in state.written_files:
            state.written_files.append(path)
        state.note_results = [
            existing for existing in state.note_results if existing.get("note_id") != note_id
        ]
        state.note_results.append(dict(note_result))
        state.stats.converted_notes = len(state.note_results)
        state.stats.total_attachments = sum(
            len(note.get("attachments", [])) for note in state.note_results
        )
        self.store.save(state)

    def _verify_output(self, state: TaskState) -> None:
        errors: list[str] = []
        missing = [path for path in state.written_files if not (state.vault_path / path).exists()]
        if missing:
            errors.append(f"Missing written output files: {missing}")

        attachments_checked = 0
        for note_result in state.note_results:
            rel_path = str(note_result.get("path") or "")
            note_path = state.vault_path / rel_path
            if not note_path.exists():
                errors.append(f"Missing note file: {rel_path}")
                continue
            try:
                markdown = note_path.read_text(encoding="utf-8")
                self._parse_frontmatter(markdown, rel_path)
            except Exception as exc:
                errors.append(f"Invalid frontmatter in {rel_path}: {exc}")
                continue

            for attachment in note_result.get("attachments", []):
                attachment_rel = str(attachment.get("path") or "")
                attachment_path = state.vault_path / attachment_rel
                attachments_checked += 1
                if not attachment_path.exists():
                    errors.append(f"Missing attachment: {attachment_rel}")
                    continue
                expected_hash = attachment.get("hash")
                if expected_hash:
                    actual_hash = hashlib.md5(attachment_path.read_bytes()).hexdigest()
                    if actual_hash != expected_hash:
                        errors.append(f"Attachment hash mismatch: {attachment_rel}")
                if attachment_rel and attachment_rel not in markdown:
                    errors.append(f"Missing attachment link in {rel_path}: {attachment_rel}")

        converted_notes = len({note.get("note_id") or note.get("path") for note in state.note_results})
        if state.stats.converted_notes != converted_notes:
            errors.append(
                f"Converted note count mismatch: stats={state.stats.converted_notes}, verified={converted_notes}"
            )
        if state.stats.total_attachments != attachments_checked:
            errors.append(
                "Attachment count mismatch: "
                f"stats={state.stats.total_attachments}, verified={attachments_checked}"
            )
        if errors:
            raise RuntimeError("; ".join(errors))

        state.verification = {
            "notes_checked": converted_notes,
            "attachments_checked": attachments_checked,
            "frontmatter_checked": converted_notes,
        }

    def _parse_frontmatter(self, markdown: str, rel_path: str) -> dict[str, object]:
        if not markdown.startswith("---\n"):
            raise ValueError("missing opening delimiter")
        match = re.match(r"^---\n(.*?)\n---\n", markdown, flags=re.DOTALL)
        if not match:
            raise ValueError("missing closing delimiter")
        data = yaml.safe_load(match.group(1))
        if not isinstance(data, dict):
            raise ValueError(f"frontmatter is not a mapping in {rel_path}")
        return data

    def _transition(
        self,
        state: TaskState,
        phase: str,
        message: str,
        progress: int,
        progress_callback: ProgressCallback | None,
    ) -> None:
        self.store.transition(state, phase, message)
        if progress_callback:
            progress_callback(
                ProgressEvent(
                    task_id=state.task_id,
                    phase=phase,
                    progress=progress,
                    message=message,
                )
            )
