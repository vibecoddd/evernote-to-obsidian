from __future__ import annotations

import json
from pathlib import Path

from .state import TaskState


def task_report_data(state: TaskState) -> dict[str, object]:
    return {
        "task_id": state.task_id,
        "source_mode": state.source_mode,
        "status": state.status,
        "phase": state.phase,
        "vault_path": str(state.vault_path),
        "task_dir": str(state.task_dir),
        "stats": state.stats.to_dict(),
        "enex_files": state.enex_files,
        "written_files": state.written_files,
        "errors": state.errors,
        "warnings": state.warnings,
        "phase_history": state.phase_history,
        "created_at": state.created_at,
        "updated_at": state.updated_at,
        "versions": state.versions,
    }


def markdown_report(state: TaskState) -> str:
    lines = [
        f"# Migration Report: {state.task_id}",
        "",
        f"- Status: {state.status}",
        f"- Phase: {state.phase}",
        f"- Source mode: {state.source_mode}",
        f"- Vault: `{state.vault_path}`",
        f"- Task cache: `{state.task_dir}`",
        "",
        "## Stats",
        "",
        f"- Total notes: {state.stats.total_notes}",
        f"- Converted notes: {state.stats.converted_notes}",
        f"- Skipped notes: {state.stats.skipped_notes}",
        f"- Attachments: {state.stats.total_attachments}",
        "",
        "## Written Files",
        "",
    ]
    lines.extend(f"- `{file_path}`" for file_path in state.written_files)
    if not state.written_files:
        lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {warning}" for warning in state.warnings)
    if not state.warnings:
        lines.append("- None")
    lines.extend(["", "## Errors", ""])
    lines.extend(f"- {error.get('category', 'runtime')}: {error.get('message', '')}" for error in state.errors)
    if not state.errors:
        lines.append("- None")
    lines.append("")
    return "\n".join(lines)


def write_task_reports(state: TaskState, output_dir: str | Path | None = None) -> tuple[Path, Path]:
    report_dir = Path(output_dir) if output_dir else state.task_dir / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "report.json"
    markdown_path = report_dir / "report.md"
    json_path.write_text(
        json.dumps(task_report_data(state), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    markdown_path.write_text(markdown_report(state), encoding="utf-8")
    return json_path, markdown_path

