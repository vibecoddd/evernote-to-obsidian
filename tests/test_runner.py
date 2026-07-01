import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from evernote_to_obsidian.doctor import run_doctor
from evernote_to_obsidian.runner import MigrationRunner
from evernote_to_obsidian.state import TaskStateStore


FIXTURE = Path(__file__).parent / "fixtures" / "sample_complex.enex"


def test_import_enex_creates_resumable_task_and_progress_events(tmp_path):
    events = []
    runner = MigrationRunner(app_data_dir=tmp_path / "app")

    state = runner.import_enex(
        [FIXTURE],
        vault_path=tmp_path / "vault",
        task_id="run-001",
        progress_callback=events.append,
    )

    loaded = TaskStateStore(tmp_path / "app").load("run-001")
    phase_names = [event["phase"] for event in loaded.phase_history]

    assert state.phase == "completed"
    assert loaded.status == "completed"
    assert phase_names == ["parsed", "written", "verified", "completed"]
    assert loaded.stats.total_notes == 2
    assert loaded.stats.converted_notes == 2
    assert loaded.stats.total_attachments == 1
    assert loaded.processed_enex_files == [str(FIXTURE.resolve())]
    assert loaded.processed_note_ids == [
        "11111111-1111-1111-1111-111111111111",
        "22222222-2222-2222-2222-222222222222",
    ]
    assert [note["note_id"] for note in loaded.note_results] == loaded.processed_note_ids
    assert (loaded.task_dir / "reports" / "report.json").exists()
    assert any(event.phase == "written" for event in events)


def test_resume_continues_task_with_existing_enex_inventory(tmp_path):
    store = TaskStateStore(tmp_path / "app")
    state = store.create(
        source_mode="import_enex",
        vault_path=tmp_path / "vault",
        task_id="resume-001",
    )
    state.enex_files = [str(FIXTURE)]
    store.transition(state, "exported", "ENEX files ready")

    resumed = MigrationRunner(app_data_dir=tmp_path / "app").resume("resume-001")

    assert resumed.phase == "completed"
    assert resumed.stats.converted_notes == 2
    assert (tmp_path / "vault" / "Work Notes").exists()


def test_resume_skips_already_checkpointed_notes(tmp_path):
    store = TaskStateStore(tmp_path / "app")
    vault = tmp_path / "vault"
    first_note = vault / "Work Notes" / "Meeting_Plan_ Q1.md"
    first_note.parent.mkdir(parents=True)
    first_note.write_text("---\ntitle: \"Meeting/Plan: Q1?\"\n---\n\nAlready written\n", encoding="utf-8")

    state = store.create(
        source_mode="import_enex",
        vault_path=vault,
        task_id="resume-note-001",
    )
    state.enex_files = [str(FIXTURE.resolve())]
    state.processed_note_ids = ["11111111-1111-1111-1111-111111111111"]
    state.note_results = [
        {
            "note_id": "11111111-1111-1111-1111-111111111111",
            "path": "Work Notes/Meeting_Plan_ Q1.md",
            "attachments": [],
            "source_enex": str(FIXTURE.resolve()),
        }
    ]
    state.written_files = ["Work Notes/Meeting_Plan_ Q1.md"]
    state.stats.total_notes = 1
    state.stats.converted_notes = 1
    store.save(state)

    resumed = MigrationRunner(app_data_dir=tmp_path / "app").resume("resume-note-001")

    assert resumed.status == "completed"
    assert resumed.stats.converted_notes == 2
    assert resumed.processed_note_ids == [
        "11111111-1111-1111-1111-111111111111",
        "22222222-2222-2222-2222-222222222222",
    ]
    assert first_note.read_text(encoding="utf-8").endswith("Already written\n")
    index = (vault / "Work Notes" / "Work Notes_Index.md").read_text(encoding="utf-8")
    assert "[[Meeting_Plan_ Q1]]" in index
    assert "[[Meeting_Plan_ Q1-22222222]]" in index


def test_verification_detects_missing_attachment(tmp_path):
    runner = MigrationRunner(app_data_dir=tmp_path / "app")
    state = runner.import_enex([FIXTURE], vault_path=tmp_path / "vault", task_id="verify-001")
    attachment = (
        tmp_path
        / "vault"
        / "attachments"
        / "11111111-1111-1111-1111-111111111111"
        / "diagram.png"
    )
    attachment.unlink()

    with pytest.raises(RuntimeError, match="Missing attachment"):
        runner._verify_output(state)


def test_doctor_reports_local_environment_without_real_account(tmp_path):
    report = run_doctor(
        vault_path=tmp_path / "vault",
        app_data_dir=tmp_path / "app",
        evernote_command="definitely-missing-evernote-backup",
    )
    checks = {check.name: check for check in report.checks}

    assert "python_version" in checks
    assert "app_data_write" in checks
    assert "vault_write" in checks
    assert "disk_space" in checks
    assert "path_length" in checks
    assert "web_port" in checks
    assert "evernote_backup_command" in checks
    assert checks["evernote_backup_command"].status == "warning"
    assert report.to_dict()["ok"] is True
