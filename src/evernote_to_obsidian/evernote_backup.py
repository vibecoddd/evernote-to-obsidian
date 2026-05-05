from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .errors import redact_secrets


@dataclass
class CommandResult:
    command: str
    returncode: int
    stdout: str = ""
    stderr: str = ""


class EvernoteBackupSource:
    def __init__(
        self,
        command: str = "evernote-backup",
        backend: str = "china",
        work_dir: str | Path | None = None,
        dry_run: bool = False,
    ):
        self.command = command
        self.backend = backend
        self.work_dir = Path(work_dir or ".").expanduser().resolve()
        self.dry_run = dry_run
        self.commands: list[CommandResult] = []

    def init_db(self, username: str, password: str) -> CommandResult:
        return self._run(
            [
                "init-db",
                "--backend",
                self.backend,
                "--user",
                username,
                "--password",
                password,
                "--use-system-ssl-ca",
                "--force",
            ],
            secrets=[password],
        )

    def reauth(self, username: str, password: str) -> CommandResult:
        return self._run(
            [
                "reauth",
                "--backend",
                self.backend,
                "--user",
                username,
                "--password",
                password,
                "--use-system-ssl-ca",
            ],
            secrets=[password],
        )

    def sync(self) -> CommandResult:
        return self._run(
            [
                "sync",
                "--max-download-workers",
                "2",
                "--max-chunk-results",
                "50",
                "--network-retry-count",
                "100",
                "--use-system-ssl-ca",
            ]
        )

    def export(self, output_dir: str | Path) -> tuple[CommandResult, list[Path]]:
        output_path = Path(output_dir).expanduser().resolve()
        output_path.mkdir(parents=True, exist_ok=True)
        result = self._run(["export", str(output_path)])
        return result, sorted(output_path.glob("*.enex"))

    def sync_and_export(self, username: str, password: str, output_dir: str | Path) -> list[Path]:
        self.init_db(username, password)
        self.sync()
        _, enex_files = self.export(output_dir)
        return enex_files

    def _run(self, args: list[str], secrets: list[str] | None = None) -> CommandResult:
        self.work_dir.mkdir(parents=True, exist_ok=True)
        command = [self.command, *args]
        redacted = redact_secrets(command, secrets=secrets)
        if self.dry_run:
            result = CommandResult(command=redacted, returncode=0, stdout="Dry run")
            self.commands.append(result)
            return result

        env = os.environ.copy()
        for key in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
            env.pop(key, None)

        completed = subprocess.run(
            command,
            cwd=str(self.work_dir),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        result = CommandResult(
            command=redacted,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=redact_secrets(completed.stderr, secrets=secrets),
        )
        self.commands.append(result)
        if completed.returncode != 0:
            raise RuntimeError(f"evernote-backup failed: {result.stderr or result.stdout}")
        return result

