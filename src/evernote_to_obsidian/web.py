from __future__ import annotations

import secrets
import socket
import threading
import uuid
import webbrowser
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO, join_room
from werkzeug.utils import secure_filename

from .doctor import run_doctor
from .evernote_backup import EvernoteBackupSource
from .runner import MigrationRunner
from .state import TaskStateStore


def create_app(app_data_dir: str | Path | None = None) -> tuple[Flask, SocketIO]:
    project_root = Path(__file__).resolve().parents[2]
    app = Flask(
        __name__,
        template_folder=str(project_root / "templates"),
        static_folder=str(project_root / "static"),
    )
    app.config["SECRET_KEY"] = uuid.uuid4().hex
    app.config["LOCAL_SESSION_TOKEN"] = secrets.token_urlsafe(32)
    app.config["APP_DATA_DIR"] = Path(app_data_dir).expanduser().resolve() if app_data_dir else None
    socketio = SocketIO(app, async_mode="threading")
    active_migrations: dict[str, dict[str, Any]] = {}

    @app.context_processor
    def inject_local_session_token():
        return {"local_session_token": app.config["LOCAL_SESSION_TOKEN"]}

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/config")
    def config_page():
        return render_template("config.html")

    @app.route("/migrate")
    def migrate_page():
        return render_template("migrate.html")

    @app.route("/results")
    def results_page():
        return render_template("results.html")

    @app.route("/api/doctor")
    def api_doctor():
        report = run_doctor(
            vault_path=request.args.get("vault_path") or None,
            app_data_dir=app.config["APP_DATA_DIR"],
            evernote_command=request.args.get("evernote_command", "evernote-backup"),
        )
        return jsonify(report.to_dict())

    @app.route("/api/import_enex", methods=["POST"])
    def api_import_enex():
        guard = _require_local_token(app)
        if guard:
            return guard
        vault_path = request.form.get("vault_path") or request.form.get("outputDirectory")
        if not vault_path:
            return jsonify({"success": False, "error": "vault_path is required"}), 400

        files = request.files.getlist("enex_files")
        if not files:
            return jsonify({"success": False, "error": "No ENEX files uploaded"}), 400

        task_id = _task_id(request.form.get("task_id"))
        upload_dir = _upload_dir(app.config["APP_DATA_DIR"], task_id)
        saved_files: list[Path] = []
        for file_storage in files:
            filename = secure_filename(file_storage.filename or "notes.enex")
            if not filename.endswith(".enex"):
                return jsonify({"success": False, "error": f"Unsupported file: {filename}"}), 400
            path = upload_dir / filename
            file_storage.save(path)
            saved_files.append(path)

        active_migrations[task_id] = {"task_id": task_id, "status": "running", "message": "Upload accepted"}
        thread = threading.Thread(
            target=_run_uploaded_import,
            args=(app, socketio, active_migrations, task_id, saved_files, vault_path),
            daemon=True,
        )
        thread.start()
        return jsonify({"success": True, "task_id": task_id, "message": "Migration started"}), 202

    @app.route("/api/upload_enex", methods=["POST"])
    def api_upload_enex():
        guard = _require_local_token(app)
        if guard:
            return guard
        task_id = _task_id(request.form.get("task_id"))
        upload_dir = _upload_dir(app.config["APP_DATA_DIR"], task_id)
        saved_files: list[str] = []
        for file_storage in request.files.getlist("enex_files"):
            filename = secure_filename(file_storage.filename or "notes.enex")
            if filename.endswith(".enex"):
                path = upload_dir / filename
                file_storage.save(path)
                saved_files.append(str(path))
        if not saved_files:
            return jsonify({"success": False, "error": "No ENEX files uploaded"}), 400
        return jsonify({"success": True, "files": saved_files, "temp_dir": str(upload_dir)})

    @app.route("/api/start_migration", methods=["POST"])
    def api_start_migration():
        guard = _require_local_token(app)
        if guard:
            return guard
        config = request.get_json(silent=True) or {}
        task_id = _task_id(config.get("task_id"))
        active_migrations[task_id] = {"status": "running", "message": "Migration started"}

        thread = threading.Thread(
            target=_run_config_migration,
            args=(app, socketio, active_migrations, task_id, config),
            daemon=True,
        )
        thread.start()
        return jsonify({"success": True, "task_id": task_id, "message": "Migration started"})

    @app.route("/api/migration_status/<task_id>")
    def api_migration_status(task_id: str):
        guard = _require_local_token(app)
        if guard:
            return guard
        if task_id in active_migrations:
            return jsonify(active_migrations[task_id])
        try:
            state = TaskStateStore(_app_data(app)).load(task_id)
            return jsonify(_state_payload(state))
        except Exception:
            return jsonify({"status": "not_found", "message": "Task not found"}), 404

    @app.route("/api/report/<task_id>")
    def api_report(task_id: str):
        guard = _require_local_token(app)
        if guard:
            return guard
        try:
            return jsonify(_runner(app).report(task_id))
        except Exception as exc:
            return jsonify({"error": str(exc)}), 404

    @app.route("/api/tasks")
    def api_tasks():
        guard = _require_local_token(app)
        if guard:
            return guard
        states = TaskStateStore(_app_data(app)).list()
        return jsonify({"tasks": [_state_payload(state) for state in states]})

    @app.route("/api/tasks/<task_id>", methods=["DELETE"])
    def api_delete_task(task_id: str):
        guard = _require_local_token(app)
        if guard:
            return guard
        deleted = TaskStateStore(_app_data(app)).delete(task_id)
        if not deleted:
            return jsonify({"success": False, "error": "Task not found"}), 404
        active_migrations.pop(task_id, None)
        return jsonify({"success": True, "task_id": task_id})

    @socketio.on("join_task")
    def join_task(data):
        task_id = (data or {}).get("task_id")
        token = (data or {}).get("token")
        if task_id and _valid_token(app, token):
            join_room(task_id)

    return app, socketio


def _run_uploaded_import(
    app: Flask,
    socketio: SocketIO,
    active_migrations: dict[str, dict[str, Any]],
    task_id: str,
    saved_files: list[Path],
    vault_path: str,
) -> None:
    try:
        state = _runner(app).import_enex(
            saved_files,
            vault_path=vault_path,
            task_id=task_id,
            progress_callback=lambda event: _emit_progress(socketio, active_migrations, event),
        )
        payload = _state_payload(state)
        active_migrations[state.task_id] = payload
        socketio.emit(
            "migration_completed",
            {"task_id": state.task_id, "success": True, "result": payload},
            room=state.task_id,
        )
    except Exception as exc:
        active_migrations[task_id] = {"task_id": task_id, "status": "failed", "message": str(exc)}
        socketio.emit("migration_error", {"task_id": task_id, "error": str(exc)}, room=task_id)


def _run_config_migration(
    app: Flask,
    socketio: SocketIO,
    active_migrations: dict[str, dict[str, Any]],
    task_id: str,
    config: dict[str, Any],
) -> None:
    try:
        output = config.get("output", {})
        vault_path = output.get("obsidian_vault")
        if not vault_path:
            raise ValueError("output.obsidian_vault is required")
        enex_files = config.get("input", {}).get("enex_files", [])
        if enex_files:
            state = _runner(app).import_enex(
                [Path(path) for path in enex_files],
                vault_path=vault_path,
                task_id=task_id,
                progress_callback=lambda event: _emit_progress(socketio, active_migrations, event),
            )
        else:
            credentials = config.get("evernote_credentials", {})
            username = credentials.get("username")
            password = credentials.get("password")
            if not username or not password:
                raise ValueError("Evernote username and password are required")
            work_dir = _app_data(app) / "tasks" / task_id / "evernote"
            export_dir = _app_data(app) / "tasks" / task_id / "enex"
            source = EvernoteBackupSource(
                backend=config.get("evernote_backend", "china"),
                work_dir=work_dir,
            )
            synced_files = source.sync_and_export(username, password, export_dir)
            state = _runner(app).import_enex(
                synced_files,
                vault_path=vault_path,
                task_id=task_id,
                progress_callback=lambda event: _emit_progress(socketio, active_migrations, event),
            )
        payload = _state_payload(state)
        active_migrations[task_id] = payload
        socketio.emit("migration_completed", {"task_id": task_id, "success": True, "result": payload}, room=task_id)
    except Exception as exc:
        active_migrations[task_id] = {"status": "failed", "message": str(exc)}
        socketio.emit("migration_error", {"task_id": task_id, "error": str(exc)}, room=task_id)


def _emit_progress(socketio: SocketIO, active_migrations: dict[str, dict[str, Any]], event) -> None:
    step_map = {"parsed": 2, "written": 3, "verified": 4, "completed": 4}
    payload = {
        "task_id": event.task_id,
        "step": step_map.get(event.phase, 1),
        "step_name": event.phase,
        "phase": event.phase,
        "progress": event.progress,
        "message": event.message,
    }
    active_migrations[event.task_id] = {**active_migrations.get(event.task_id, {}), **payload, "status": "running"}
    socketio.emit("migration_progress", payload, room=event.task_id)


def _state_payload(state) -> dict[str, Any]:
    return {
        "task_id": state.task_id,
        "status": state.status,
        "phase": state.phase,
        "progress": 100 if state.status == "completed" else 0,
        "message": state.phase_history[-1]["message"] if state.phase_history else "",
        "start_time": state.created_at,
        "end_time": state.updated_at,
        "vault_path": str(state.vault_path),
        "stats": state.stats.to_dict(),
        "task_dir": str(state.task_dir),
        "report_dir": str(state.task_dir / "reports"),
        "verification": state.verification,
        "errors": state.errors,
        "warnings": state.warnings,
    }


def _runner(app: Flask) -> MigrationRunner:
    return MigrationRunner(app_data_dir=_app_data(app))


def _app_data(app: Flask) -> Path:
    configured = app.config.get("APP_DATA_DIR")
    if configured:
        return Path(configured)
    return Path.home() / ".evernote2obsidian"


def _upload_dir(app_data_dir: Path | None, task_id: str) -> Path:
    root = Path(app_data_dir) if app_data_dir else Path.home() / ".evernote2obsidian"
    path = root / "tasks" / task_id / "uploads"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _require_local_token(app: Flask):
    token = (
        request.headers.get("X-Evernote2Obsidian-Token")
        or request.args.get("token")
        or request.form.get("_token")
    )
    if _valid_token(app, token):
        return None
    return jsonify({"success": False, "error": "Forbidden"}), 403


def _valid_token(app: Flask, token: str | None) -> bool:
    expected = str(app.config.get("LOCAL_SESSION_TOKEN") or "")
    return bool(token and expected and secrets.compare_digest(str(token), expected))


def _task_id(value: str | None) -> str:
    candidate = (value or uuid.uuid4().hex).strip()
    if not candidate or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for char in candidate):
        return uuid.uuid4().hex
    return candidate[:120]


def _available_port(host: str) -> int:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind((host, 0))
            return int(sock.getsockname()[1])
    except OSError:
        return 5000


def main(app_data: str | Path | None = None, host: str = "127.0.0.1", port: int = 0) -> None:
    app, socketio = create_app(app_data_dir=app_data)
    selected_port = port or _available_port(host)
    url = f"http://{host}:{selected_port}"
    try:
        webbrowser.open(url)
    except Exception:
        pass
    print(f"Starting local Web UI at {url}")
    socketio.run(app, host=host, port=selected_port, debug=False, allow_unsafe_werkzeug=True)
