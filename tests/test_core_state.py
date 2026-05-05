import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from evernote_to_obsidian.errors import redact_secrets
from evernote_to_obsidian.models import TaskStats
from evernote_to_obsidian.reports import write_task_reports
from evernote_to_obsidian.state import TaskStateStore


def test_task_state_store_round_trips_and_records_phase_history(tmp_path):
    store = TaskStateStore(tmp_path)
    state = store.create(
        source_mode="import_enex",
        vault_path=tmp_path / "vault",
        task_id="task-001",
    )

    assert state.phase == "created"
    assert state.task_dir == tmp_path / "tasks" / "task-001"

    state.enex_files.append("source.enex")
    store.transition(state, "parsed", "Parsed 1 ENEX file")

    loaded = store.load("task-001")

    assert loaded.task_id == "task-001"
    assert loaded.phase == "parsed"
    assert loaded.enex_files == ["source.enex"]
    assert loaded.phase_history[-1]["phase"] == "parsed"
    assert loaded.phase_history[-1]["message"] == "Parsed 1 ENEX file"


def test_redact_secrets_handles_strings_and_command_lists():
    command = [
        "evernote-backup",
        "init-db",
        "--user",
        "user@example.com",
        "--password",
        "secret-password",
    ]

    redacted = redact_secrets(command, secrets=["secret-password"])

    assert "secret-password" not in redacted
    assert "user@example.com" in redacted
    assert "--password [REDACTED]" in redacted


def test_write_task_reports_outputs_json_and_markdown(tmp_path):
    store = TaskStateStore(tmp_path)
    state = store.create(
        source_mode="import_enex",
        vault_path=tmp_path / "vault",
        task_id="task-report",
    )
    state.stats = TaskStats(
        total_notes=2,
        converted_notes=2,
        skipped_notes=0,
        total_attachments=1,
    )
    state.written_files = ["Notebook/First.md", "Notebook/Second.md"]
    state.warnings.append("Filename shortened")
    store.transition(state, "completed", "Migration completed")

    json_path, markdown_path = write_task_reports(state)

    report = json.loads(json_path.read_text(encoding="utf-8"))
    markdown = markdown_path.read_text(encoding="utf-8")

    assert report["task_id"] == "task-report"
    assert report["stats"]["converted_notes"] == 2
    assert "Filename shortened" in report["warnings"]
    assert "# Migration Report: task-report" in markdown
    assert "Notebook/First.md" in markdown
