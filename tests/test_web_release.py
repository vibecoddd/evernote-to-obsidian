import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from evernote_to_obsidian.web import create_app


FIXTURE = Path(__file__).parent / "fixtures" / "sample_complex.enex"


def test_web_pages_and_doctor_api_render(tmp_path):
    app, _socketio = create_app(app_data_dir=tmp_path / "app")
    client = app.test_client()

    assert client.get("/").status_code == 200
    assert client.get("/migrate").status_code == 200

    doctor = client.get(f"/api/doctor?vault_path={tmp_path / 'vault'}")

    assert doctor.status_code == 200
    assert doctor.get_json()["ok"] is True


def test_web_import_enex_status_and_report(tmp_path):
    app, _socketio = create_app(app_data_dir=tmp_path / "app")
    client = app.test_client()
    vault = tmp_path / "vault"

    response = client.post(
        "/api/import_enex",
        data={
            "vault_path": str(vault),
            "task_id": "web-001",
            "enex_files": (io.BytesIO(FIXTURE.read_bytes()), "sample_complex.enex"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["task_id"] == "web-001"

    status = client.get("/api/migration_status/web-001").get_json()
    assert status["status"] == "completed"
    assert status["stats"]["converted_notes"] == 2
    assert (vault / "Work Notes").exists()

    report = client.get("/api/report/web-001").get_json()
    assert report["task_id"] == "web-001"
    assert report["stats"]["total_attachments"] == 1
