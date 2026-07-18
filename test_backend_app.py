def test_healthz_returns_status():
    from web_app import WebMigrator

    response = WebMigrator().app.test_client().get("/api/healthz")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_backend_entry_uses_loopback(monkeypatch):
    import backend_app

    calls = []
    fake = type("M", (), {"run": lambda self, **kwargs: calls.append(kwargs)})()
    monkeypatch.setattr(backend_app, "WebMigrator", lambda: fake)

    backend_app.run_backend(43123)

    assert calls[0] == {
        "host": "127.0.0.1",
        "port": 43123,
        "debug": False,
        "allow_unsafe_werkzeug": True,
    }


def test_preflight_endpoint_uses_contract_status_codes(tmp_path):
    from web_app import WebMigrator

    enex_file = tmp_path / "notes.enex"
    enex_file.write_text("<en-export />", encoding="utf-8")
    vault = tmp_path / "vault"
    vault.mkdir()
    client = WebMigrator().app.test_client()

    success = client.post("/api/preflight", json={
        "source_mode": "enex",
        "input": {"enex_files": [str(enex_file)]},
        "output": {"obsidian_vault": str(vault)},
    })
    invalid = client.post("/api/preflight", json={"source_mode": "enex"})

    assert success.status_code == 200
    assert success.get_json()["ok"] is True
    assert invalid.status_code == 422
    assert invalid.get_json()["ok"] is False


def test_cancel_endpoint_sets_known_task_event_and_rejects_unknown_task():
    from web_app import WebMigrator

    migrator = WebMigrator()
    migrator.active_migrations["known"] = {"status": "running"}
    migrator.cancel_events["known"] = __import__("threading").Event()
    client = migrator.app.test_client()

    cancelling = client.post("/api/cancel_migration/known")
    unknown = client.post("/api/cancel_migration/missing")

    assert cancelling.status_code == 200
    assert cancelling.get_json() == {"task_id": "known", "status": "cancelling"}
    assert migrator.cancel_events["known"].is_set()
    assert unknown.status_code == 404
    assert unknown.get_json()["status"] == "not_found"


def test_cancelled_task_emits_cancelled_event_before_major_steps():
    from config import Config
    from web_app import WebMigrator

    migrator = WebMigrator()
    emitted = []
    migrator.socketio.emit = lambda name, data, room: emitted.append((name, data, room))
    task_id = "cancelled-task"
    migrator.cancel_events[task_id] = __import__("threading").Event()
    migrator.cancel_events[task_id].set()

    migrator._run_migration_task(task_id, Config())

    assert migrator.active_migrations[task_id]["status"] == "cancelled"
    assert ("migration_cancelled", {"task_id": task_id}, task_id) in emitted
