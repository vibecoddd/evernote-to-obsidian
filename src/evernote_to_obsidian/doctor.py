from __future__ import annotations

import shutil
import socket
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class DoctorCheck:
    name: str
    status: str
    message: str
    details: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass
class DoctorReport:
    checks: list[DoctorCheck]

    @property
    def ok(self) -> bool:
        return all(check.status != "error" for check in self.checks)

    def to_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "checks": [check.to_dict() for check in self.checks],
        }


def run_doctor(
    vault_path: str | Path | None = None,
    app_data_dir: str | Path | None = None,
    evernote_command: str = "evernote-backup",
) -> DoctorReport:
    app_data_check = _write_check("app_data_write", Path(app_data_dir or Path.home() / ".evernote2obsidian"))
    if app_data_dir is None and app_data_check.status == "error":
        app_data_check.status = "warning"
    checks = [
        _python_version(),
        app_data_check,
    ]
    if vault_path:
        checks.append(_write_check("vault_write", Path(vault_path)))
        checks.append(_disk_space(Path(vault_path)))
        checks.append(_path_length(Path(vault_path)))
    else:
        checks.append(DoctorCheck("vault_write", "warning", "Vault path was not provided"))
        checks.append(DoctorCheck("disk_space", "warning", "Vault path was not provided"))
        checks.append(DoctorCheck("path_length", "warning", "Vault path was not provided"))
    checks.append(_web_port())
    checks.append(_command_check(evernote_command))
    return DoctorReport(checks)


def _python_version() -> DoctorCheck:
    version = sys.version_info
    ok = version >= (3, 10)
    return DoctorCheck(
        "python_version",
        "ok" if ok else "error",
        f"Python {version.major}.{version.minor}.{version.micro}",
    )


def _write_check(name: str, path: Path) -> DoctorCheck:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".evernote2obsidian-write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return DoctorCheck(name, "ok", f"Writable: {path}")
    except OSError as exc:
        return DoctorCheck(name, "error", f"Not writable: {path}", {"error": str(exc)})


def _disk_space(path: Path) -> DoctorCheck:
    try:
        path.mkdir(parents=True, exist_ok=True)
        usage = shutil.disk_usage(path)
        free_mb = usage.free // (1024 * 1024)
        status = "ok" if free_mb >= 100 else "warning"
        return DoctorCheck("disk_space", status, f"{free_mb} MB free", {"free_bytes": usage.free})
    except OSError as exc:
        return DoctorCheck("disk_space", "error", "Unable to inspect disk space", {"error": str(exc)})


def _path_length(path: Path) -> DoctorCheck:
    try:
        path.mkdir(parents=True, exist_ok=True)
        long_name = "a" * 120
        probe = path / f"{long_name}.tmp"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return DoctorCheck("path_length", "ok", "Long path probe succeeded")
    except OSError as exc:
        return DoctorCheck("path_length", "warning", "Long path probe failed", {"error": str(exc)})


def _web_port() -> DoctorCheck:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        return DoctorCheck("web_port", "ok", f"Available local port: {port}", {"port": port})
    except OSError as exc:
        return DoctorCheck("web_port", "warning", "Unable to bind local Web port", {"error": str(exc)})


def _command_check(command: str) -> DoctorCheck:
    path = shutil.which(command)
    if path:
        return DoctorCheck("evernote_backup_command", "ok", f"Found {command}", {"path": path})
    return DoctorCheck(
        "evernote_backup_command",
        "warning",
        f"{command} is not available in PATH; packaged releases should include it",
    )
