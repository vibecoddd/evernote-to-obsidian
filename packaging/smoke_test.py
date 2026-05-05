from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "sample_complex.enex"


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        print(completed.stdout)
        print(completed.stderr, file=sys.stderr)
        raise SystemExit(completed.returncode)
    return completed


def main() -> int:
    temp_root = Path(tempfile.mkdtemp(prefix="e2o-smoke-"))
    try:
        app_data = temp_root / "app"
        vault = temp_root / "vault"
        python = sys.executable
        cli = [python, "migrate.py", "--app-data", str(app_data)]

        doctor = run(cli + ["doctor", "--vault", str(vault), "--json"])
        doctor_payload = json.loads(doctor.stdout)
        if not doctor_payload["ok"]:
            raise SystemExit("doctor reported fatal errors")

        run(
            cli
            + [
                "import-enex",
                str(FIXTURE),
                "--vault",
                str(vault),
                "--task-id",
                "smoke",
            ]
        )
        report = run(cli + ["report", "smoke", "--json"])
        report_payload = json.loads(report.stdout)
        if report_payload["stats"]["converted_notes"] != 2:
            raise SystemExit("smoke import did not convert 2 notes")
        if not (vault / "Work Notes").exists():
            raise SystemExit("smoke vault missing notebook directory")
        print(f"Smoke test passed: {vault}")
        return 0
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
