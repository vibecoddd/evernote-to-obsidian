from __future__ import annotations

from pathlib import Path
from typing import Callable

from .enex import ENEXParser
from .events import ProgressEvent
from .models import TaskStats
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
        aggregate = WriteResult()

        parsed: list[tuple[list, str]] = []
        for enex_file in state.enex_files:
            notes, notebook = parser.parse_file(enex_file)
            parsed.append((notes, notebook))
            aggregate.stats.total_notes += len(notes)

        self._transition(state, "parsed", "Parsed ENEX files", 35, progress_callback)

        for notes, notebook in parsed:
            result = writer.write_notes(notes, notebook, task_id=state.task_id)
            self._merge_result(aggregate, result)

        state.stats = aggregate.stats
        state.written_files = aggregate.written_files
        state.warnings.extend(aggregate.warnings)
        state.errors.extend(aggregate.errors)
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

    def _verify_output(self, state: TaskState) -> None:
        missing = [path for path in state.written_files if not (state.vault_path / path).exists()]
        if missing:
            raise RuntimeError(f"Missing written output files: {missing}")

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
