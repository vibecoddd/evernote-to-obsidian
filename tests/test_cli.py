import json
import sys
from pathlib import Path

from click.testing import CliRunner

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from evernote_to_obsidian.cli import cli


FIXTURE = Path(__file__).parent / "fixtures" / "sample_complex.enex"


def test_doctor_outputs_json(tmp_path):
    result = CliRunner().invoke(
        cli,
        [
            "--app-data",
            str(tmp_path / "app"),
            "doctor",
            "--vault",
            str(tmp_path / "vault"),
            "--evernote-command",
            "definitely-missing-evernote-backup",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert any(check["name"] == "evernote_backup_command" for check in payload["checks"])


def test_import_enex_and_report_commands(tmp_path):
    runner = CliRunner()
    app_data = tmp_path / "app"
    vault = tmp_path / "vault"

    result = runner.invoke(
        cli,
        [
            "--app-data",
            str(app_data),
            "import-enex",
            str(FIXTURE),
            "--vault",
            str(vault),
            "--task-id",
            "cli-001",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "cli-001" in result.output
    assert (vault / "Work Notes").exists()

    report = runner.invoke(cli, ["--app-data", str(app_data), "report", "cli-001", "--json"])

    assert report.exit_code == 0, report.output
    payload = json.loads(report.output)
    assert payload["task_id"] == "cli-001"
    assert payload["stats"]["converted_notes"] == 2

    cleanup = runner.invoke(cli, ["--app-data", str(app_data), "cleanup", "cli-001", "--yes"])

    assert cleanup.exit_code == 0, cleanup.output
    assert "deleted" in cleanup.output
    assert not (app_data / "tasks" / "cli-001").exists()


def test_sync_dry_run_validates_arguments_without_network(tmp_path):
    result = CliRunner().invoke(
        cli,
        [
            "--app-data",
            str(tmp_path / "app"),
            "sync",
            "--username",
            "user@example.com",
            "--dry-run",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Dry run" in result.output
    assert "--backend china" in result.output


def test_help_includes_release_commands():
    result = CliRunner().invoke(cli, ["--help"])

    assert result.exit_code == 0
    for command in ["migrate", "import-enex", "sync", "resume", "report", "doctor", "cleanup", "web"]:
        assert command in result.output
