import io
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from evernote_to_obsidian.web import create_app


FIXTURE = Path(__file__).parent / "fixtures" / "sample_complex.enex"


def _headers(app):
    return {"X-Evernote2Obsidian-Token": app.config["LOCAL_SESSION_TOKEN"]}


def _wait_for_task(client, task_id, headers):
    payload = {}
    for _ in range(80):
        response = client.get(f"/api/migration_status/{task_id}", headers=headers)
        payload = response.get_json()
        if response.status_code == 200 and payload["status"] in {"completed", "failed"}:
            return payload
        time.sleep(0.05)
    raise AssertionError(f"Task {task_id} did not finish: {payload}")


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

    unauthorized = client.post(
        "/api/import_enex",
        data={
            "vault_path": str(vault),
            "task_id": "web-denied",
            "enex_files": (io.BytesIO(FIXTURE.read_bytes()), "sample_complex.enex"),
        },
        content_type="multipart/form-data",
    )

    assert unauthorized.status_code == 403

    response = client.post(
        "/api/import_enex",
        data={
            "vault_path": str(vault),
            "task_id": "web-001",
            "enex_files": (io.BytesIO(FIXTURE.read_bytes()), "sample_complex.enex"),
        },
        content_type="multipart/form-data",
        headers=_headers(app),
    )

    assert response.status_code == 202
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["task_id"] == "web-001"

    status = _wait_for_task(client, "web-001", _headers(app))
    assert status["status"] == "completed"
    assert status["stats"]["converted_notes"] == 2
    assert (vault / "Work Notes").exists()

    report = client.get("/api/report/web-001", headers=_headers(app)).get_json()
    assert report["task_id"] == "web-001"
    assert report["stats"]["total_attachments"] == 1

    tasks = client.get("/api/tasks", headers=_headers(app)).get_json()
    assert [task["task_id"] for task in tasks["tasks"]] == ["web-001"]

    deleted = client.delete("/api/tasks/web-001", headers=_headers(app))
    assert deleted.status_code == 200
    assert deleted.get_json()["success"] is True
    assert not (tmp_path / "app" / "tasks" / "web-001").exists()


def test_web_sensitive_apis_require_local_session_token(tmp_path):
    app, _socketio = create_app(app_data_dir=tmp_path / "app")
    client = app.test_client()

    assert client.get("/api/tasks").status_code == 403
    assert client.get("/api/migration_status/missing").status_code == 403
    assert client.get("/api/report/missing").status_code == 403

    start = client.post(
        "/api/start_migration",
        json={
            "task_id": "web-start-001",
            "input": {"enex_files": [str(FIXTURE)]},
            "output": {"obsidian_vault": str(tmp_path / "vault")},
        },
    )

    assert start.status_code == 403


def test_web_start_migration_uses_server_task_state(tmp_path):
    app, _socketio = create_app(app_data_dir=tmp_path / "app")
    client = app.test_client()
    headers = _headers(app)

    response = client.post(
        "/api/start_migration",
        json={
            "task_id": "web-start-002",
            "input": {"enex_files": [str(FIXTURE)]},
            "output": {"obsidian_vault": str(tmp_path / "vault")},
        },
        headers=headers,
    )

    assert response.status_code == 200
    assert response.get_json()["task_id"] == "web-start-002"

    status = _wait_for_task(client, "web-start-002", headers)

    assert status["status"] == "completed"
    assert status["stats"]["converted_notes"] == 2
    assert client.get("/api/tasks", headers=headers).get_json()["tasks"][0]["task_id"] == "web-start-002"
