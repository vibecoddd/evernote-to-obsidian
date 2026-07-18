#!/usr/bin/env python3
"""Machine-readable CLI adapter for coding agents and shell automation."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import sys
from pathlib import Path
from typing import Any, Optional, Sequence

import yaml

from evernote_to_obsidian import __version__
from evernote_to_obsidian.enex import ENEXParser
from evernote_to_obsidian.evernote_backup import EvernoteBackupSource
from evernote_to_obsidian.paths import app_data_dir
from evernote_to_obsidian.runner import MigrationRunner


def _result(
    command: str,
    mode: str,
    inputs: Sequence[str],
    output: Optional[str],
    success: bool,
    stats: Optional[dict[str, Any]] = None,
    error: Optional[str] = None,
) -> dict[str, Any]:
    return {
        "success": bool(success),
        "command": command,
        "mode": mode,
        "input": list(inputs),
        "output": output,
        "stats": _json_safe(stats or {}),
        "error": error,
    }


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _add_common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", "-c", type=Path, help="YAML配置文件路径")
    parser.add_argument("--app-data", type=Path, help="任务状态目录")
    parser.add_argument("--json", action="store_true", help="只输出一个JSON结果对象")
    parser.add_argument("--verbose", "-v", action="store_true", help="启用详细输出")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="evernote-to-obsidian",
        description="将印象笔记ENEX文件迁移到Obsidian库",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    convert = subparsers.add_parser(
        "convert", help="转换已有ENEX文件，不执行Evernote登录"
    )
    _add_common_options(convert)
    convert.add_argument(
        "--input",
        "-i",
        type=Path,
        required=True,
        help="ENEX文件或包含ENEX文件的目录",
    )
    convert.add_argument(
        "--output",
        "-o",
        type=Path,
        required=True,
        help="Obsidian库目录",
    )
    convert.add_argument("--preview", action="store_true", help="只解析输入，不写入输出")

    migrate = subparsers.add_parser("migrate", help="导出Evernote并完成完整迁移")
    _add_common_options(migrate)
    migrate.add_argument("--output", "-o", type=Path, help="覆盖配置中的Obsidian库目录")
    migrate.add_argument("--backend", default=None, help="Evernote backend, e.g. china")
    migrate.add_argument(
        "--no-open",
        action="store_true",
        help="保留兼容选项；机器模式不会自动打开Obsidian",
    )

    return parser


def run_convert(args: argparse.Namespace) -> dict[str, Any]:
    enex_files = _resolve_input(args.input)
    output_path = args.output.expanduser().resolve()
    input_strings = [str(path) for path in enex_files]

    if args.preview:
        stats = _preview_stats(enex_files)
        return _result("convert", "preview", input_strings, str(output_path), True, stats)

    state = MigrationRunner(app_data_dir=args.app_data).import_enex(enex_files, output_path)
    success = state.status == "completed" and not state.errors
    stats: dict[str, Any] = {
        **state.stats.to_dict(),
        "task_id": state.task_id,
        "task_dir": str(state.task_dir),
        "written_files": list(state.written_files),
        "verification": dict(state.verification),
    }
    error = None if success else "; ".join(str(item) for item in state.errors)
    return _result("convert", "convert", input_strings, str(output_path), success, stats, error)


def run_migrate(args: argparse.Namespace) -> dict[str, Any]:
    config = _load_config(args.config)
    username, password = _credentials_from_config_or_env(config)
    vault_path = _migrate_output_path(args, config)
    backend = args.backend or str(_nested(config, "evernote_backend", default="china"))
    root = app_data_dir(args.app_data)
    work_dir = root / "tasks" / "sync"
    export_dir = work_dir / "enex"

    source = EvernoteBackupSource(backend=backend, work_dir=work_dir)
    enex_files = source.sync_and_export(username, password, export_dir)
    state = MigrationRunner(app_data_dir=root).import_enex(enex_files, vault_path)
    success = state.status == "completed" and not state.errors
    stats: dict[str, Any] = {
        **state.stats.to_dict(),
        "task_id": state.task_id,
        "task_dir": str(state.task_dir),
        "commands": [command.command for command in source.commands],
        "no_open": bool(args.no_open),
    }
    error = None if success else "; ".join(str(item) for item in state.errors)
    return _result(
        "migrate",
        "migrate",
        [str(path) for path in enex_files],
        str(Path(vault_path).expanduser().resolve()),
        success,
        stats,
        error,
    )


def _dispatch(args: argparse.Namespace) -> dict[str, Any]:
    if args.command == "convert":
        return run_convert(args)
    if args.command == "migrate":
        return run_migrate(args)
    raise ValueError(f"不支持的命令: {args.command}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    captured_stdout = io.StringIO()
    captured_stderr = io.StringIO()
    try:
        with contextlib.ExitStack() as stack:
            if args.json:
                stack.enter_context(contextlib.redirect_stdout(captured_stdout))
                stack.enter_context(contextlib.redirect_stderr(captured_stderr))
            result = _dispatch(args)
    except KeyboardInterrupt:
        result = _result(
            getattr(args, "command", "unknown"),
            "interrupted",
            [],
            None,
            False,
            error="用户中断操作",
        )
    except Exception as exc:
        result = _result(
            getattr(args, "command", "unknown"),
            "error",
            [],
            None,
            False,
            error=str(exc),
        )

    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    elif result["success"]:
        print(f"{result['command']} {result['mode']} succeeded")
        if args.verbose:
            print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["error"] or "命令失败", file=sys.stderr)
    return 0 if result["success"] else 1


def _resolve_input(input_path: Path) -> list[Path]:
    resolved = input_path.expanduser().resolve()
    if resolved.is_file():
        if resolved.suffix.lower() != ".enex":
            raise ValueError(f"输入文件必须是.enex文件: {resolved}")
        return [resolved]
    if resolved.is_dir():
        files = sorted(path.resolve() for path in resolved.glob("*.enex") if path.is_file())
        if files:
            return files
        raise ValueError(f"输入目录中没有.enex文件: {resolved}")
    raise FileNotFoundError(f"输入路径不存在: {resolved}")


def _preview_stats(enex_files: Sequence[Path]) -> dict[str, Any]:
    parser = ENEXParser()
    notebooks: dict[str, int] = {}
    total_notes = 0
    total_attachments = 0
    for enex_file in enex_files:
        notebook = parser.notebook_name(enex_file)
        file_notes = 0
        for note in parser.iter_notes(enex_file, notebook_name=notebook):
            file_notes += 1
            total_attachments += len(note.resources)
        total_notes += file_notes
        notebooks[notebook] = notebooks.get(notebook, 0) + file_notes
    return {
        "total_files": len(enex_files),
        "total_notes": total_notes,
        "converted_notes": 0,
        "skipped_notes": 0,
        "total_attachments": total_attachments,
        "notebooks": notebooks,
    }


def _load_config(config_path: Path | None) -> dict[str, Any]:
    if config_path is None:
        return {}
    path = config_path.expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"配置文件不存在: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"配置文件必须是YAML映射: {path}")
    return data


def _credentials_from_config_or_env(config: dict[str, Any]) -> tuple[str, str]:
    configured = config.get("evernote_credentials")
    if isinstance(configured, dict):
        username = configured.get("username")
        password = configured.get("password")
        if username and password:
            return str(username), str(password)

    username = os.environ.get("EVERNOTE_USERNAME")
    password = os.environ.get("EVERNOTE_PASSWORD")
    if username and password:
        return username, password

    raise ValueError(
        "缺少Evernote credentials；请配置evernote_credentials，或设置 "
        "EVERNOTE_USERNAME 和 EVERNOTE_PASSWORD"
    )


def _migrate_output_path(args: argparse.Namespace, config: dict[str, Any]) -> Path:
    output = args.output or _nested(config, "output.obsidian_vault")
    if not output:
        raise ValueError("必须通过--output或配置文件指定Obsidian库路径")
    return Path(str(output)).expanduser().resolve()


def _nested(data: dict[str, Any], dotted_key: str, default: Any = None) -> Any:
    current: Any = data
    for part in dotted_key.split("."):
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current


if __name__ == "__main__":
    sys.exit(main())
