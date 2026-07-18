import threading


def test_default_web_routes_remain_available():
    from web_app import WebMigrator

    client = WebMigrator().app.test_client()

    for route in ("/", "/config", "/migrate", "/results"):
        assert client.get(route).status_code == 200


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
    migrator.cancel_events["known"] = threading.Event()
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
    migrator.cancel_events[task_id] = threading.Event()
    migrator.cancel_events[task_id].set()

    migrator._run_migration_task(task_id, Config())

    assert migrator.active_migrations[task_id]["status"] == "cancelled"
    assert any(name == "migration_cancelled" and data["task_id"] == task_id and data["result"]["status"] == "cancelled" and room == task_id for name, data, room in emitted)


def test_start_export_registers_cancellation_event(monkeypatch, tmp_path):
    import web_app
    from web_app import WebMigrator

    class NoopThread:
        def __init__(self, **kwargs):
            pass

        daemon = False

        def start(self):
            pass

    monkeypatch.setattr(web_app.threading, "Thread", NoopThread)
    monkeypatch.setattr(web_app.uuid, "uuid4", lambda: "export-task")
    migrator = WebMigrator()

    response = migrator.app.test_client().post("/api/start_export", json={
        "output": {"enex_directory": str(tmp_path)},
    })

    assert response.status_code == 200
    assert migrator.cancel_events["export-task"].is_set() is False


def test_export_task_stops_before_export_when_already_cancelled(monkeypatch):
    from config import Config
    from web_app import WebMigrator

    class Exporter:
        def __init__(self, config):
            pass

        def check_dependencies(self):
            raise AssertionError("cancelled task must not check dependencies")

    monkeypatch.setattr("evernote_exporter.EvernoteExporter", Exporter)
    migrator = WebMigrator()
    emitted = []
    migrator.socketio.emit = lambda name, data, room: emitted.append((name, data, room))
    task_id = "cancelled-export"
    migrator.cancel_events[task_id] = threading.Event()
    migrator.cancel_events[task_id].set()

    migrator._run_export_task(task_id, Config())

    assert migrator.active_migrations[task_id]["status"] == "cancelled"
    assert ("export_cancelled", {"task_id": task_id}, task_id) in emitted


def test_export_task_preserves_created_files_when_cancelled_after_export(monkeypatch, tmp_path):
    from config import Config
    from web_app import WebMigrator

    output = tmp_path / "notes.enex"
    migrator = WebMigrator()
    task_id = "post-export-cancel"
    cancel_event = threading.Event()
    migrator.cancel_events[task_id] = cancel_event
    emitted = []
    migrator.socketio.emit = lambda name, data, room: emitted.append((name, data, room))

    class Exporter:
        def __init__(self, config):
            pass

        def check_dependencies(self):
            return True

        def export_notes(self):
            output.write_text("already exported", encoding="utf-8")
            cancel_event.set()
            return [str(output)]

    monkeypatch.setattr("evernote_exporter.EvernoteExporter", Exporter)

    migrator._run_export_task(task_id, Config())

    assert output.read_text(encoding="utf-8") == "already exported"
    assert migrator.active_migrations[task_id]["status"] == "cancelled"
    assert ("export_completed",) not in [(name,) for name, _, _ in emitted]
    assert ("export_cancelled", {"task_id": task_id}, task_id) in emitted


def test_migration_terminal_state_and_event_include_handler_statistics(monkeypatch):
    import web_app
    from config import Config
    from web_app import WebMigrator

    class Handler:
        def __init__(self, *args):
            self.stats = {
                "total_notes": 2,
                "converted_notes": 1,
                "skipped_notes": 1,
                "total_attachments": 3,
                "errors": ["/vault/failed.md"],
            }

        def run_migration(self):
            return True

    monkeypatch.setattr(web_app, "WebMigrationHandler", Handler)
    migrator = WebMigrator()
    emitted = []
    migrator.socketio.emit = lambda name, data, room: emitted.append((name, data, room))

    migrator._run_migration_task("statistics-task", Config())

    result = migrator.active_migrations["statistics-task"]
    assert result["stats"] == {
        "total_notes": 2,
        "converted_notes": 1,
        "skipped_notes": 1,
        "total_attachments": 3,
        "errors": ["/vault/failed.md"],
    }
    assert ("migration_completed", {"task_id": "statistics-task", "success": True, "result": result}, "statistics-task") in emitted


def test_conversion_records_each_failed_note_path_in_task_statistics(monkeypatch):
    from config import Config
    from web_app import WebMigrationHandler

    class Note:
        attachments = []

    class Parser:
        def parse_file(self, _path):
            return [Note()], "Notebook"

    class Converter:
        def __init__(self, _config):
            pass

        def convert_note(self, _note):
            return "# note"

    class Organizer:
        def __init__(self, _config):
            pass

        def organize_notes(self, notes, _notebook):
            return [(notes[0], "/vault/failed.md")]

        def create_directory_structure(self, _notes):
            pass

        def save_note(self, *_args):
            raise OSError("disk full")

        def create_index_file(self, *_args):
            pass

    monkeypatch.setattr("enex_parser.ENEXParser", Parser)
    monkeypatch.setattr("markdown_converter.MarkdownConverter", Converter)
    monkeypatch.setattr("file_organizer.FileOrganizer", Organizer)
    active = {"failed-note-task": {"stats": {"errors": []}}}
    emitted = []
    handler = WebMigrationHandler("failed-note-task", type("Socket", (), {"emit": lambda *_args, **_kwargs: emitted.append(_args)})(), active)
    config = Config()
    config.config_data = {"input": {"enex_files": ["/exports/notes.enex"]}}
    handler.config = config

    assert handler._step_convert_to_markdown() is False
    assert handler.stats["errors"] == ["/vault/failed.md"]
    assert active["failed-note-task"]["stats"]["errors"] == ["/vault/failed.md"]
