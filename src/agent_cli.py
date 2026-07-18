#!/usr/bin/env python3
"""Non-interactive CLI adapter for Codex, Claude Code and shell automation."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Sequence, Tuple

from config import Config
from evernote2obsidian import EvernoteToObsidianConverter
from unified_migrator import UnifiedMigrator


VERSION = "0.1.0"


def _result(
    command: str,
    mode: str,
    inputs: Sequence[str],
    output: Optional[str],
    success: bool,
    stats: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
) -> Dict[str, Any]:
    """Build the stable result shape shared by both subcommands."""
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
    """Convert dates and paths in legacy statistics to JSON-safe values."""
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _add_common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--config", "-c", type=Path, help="YAML配置文件路径"
    )
    parser.add_argument(
        "--json", action="store_true", help="只输出一个JSON结果对象"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="启用详细日志"
    )


def build_parser() -> argparse.ArgumentParser:
    """Create the public argparse parser."""
    parser = argparse.ArgumentParser(
        prog="evernote-to-obsidian",
        description="将印象笔记ENEX文件迁移到Obsidian库",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {VERSION}"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    convert = subparsers.add_parser(
        "convert", help="转换已有ENEX文件，不执行Evernote登录"
    )
    _add_common_options(convert)
    convert.add_argument(
        "--input", "-i", type=Path, required=True,
        help="ENEX文件或包含ENEX文件的目录",
    )
    convert.add_argument(
        "--output", "-o", type=Path, required=True,
        help="Obsidian库目录",
    )
    convert.add_argument(
        "--preview", action="store_true", help="只分析输入，不写入输出"
    )
    convert.add_argument(
        "--reset", action="store_true", help="重置目标库的同步状态后退出"
    )

    migrate = subparsers.add_parser(
        "migrate", help="导出Evernote并完成完整迁移"
    )
    _add_common_options(migrate)
    migrate.add_argument(
        "--output", "-o", type=Path, help="覆盖配置中的Obsidian库目录"
    )
    migrate.add_argument(
        "--no-open", action="store_true",
        help="迁移完成后不自动打开Obsidian",
    )

    return parser


def _load_config(config_path: Optional[Path]) -> Config:
    """Load a YAML configuration and validate that the path exists first."""
    if config_path is not None and not config_path.is_file():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    return Config(str(config_path) if config_path is not None else None)


def _resolve_input(input_path: Path) -> Tuple[Path, Sequence[str]]:
    """Validate an input path and return normalized paths for reporting."""
    resolved = input_path.expanduser().resolve()
    if resolved.is_file():
        if resolved.suffix.lower() != ".enex":
            raise ValueError(f"输入文件必须是.enex文件: {resolved}")
        return resolved, [str(resolved)]

    if resolved.is_dir():
        files = sorted(
            path for path in resolved.glob("*.enex") if path.is_file()
        )
        return resolved, [str(path.resolve()) for path in files]

    raise FileNotFoundError(f"输入路径不存在: {resolved}")


def run_convert(args: argparse.Namespace) -> Dict[str, Any]:
    """Run the existing ENEX converter with deterministic CLI overrides."""
    input_path, input_files = _resolve_input(args.input)
    output_path = args.output.expanduser().resolve()
    config = _load_config(args.config)

    if input_path.is_file():
        config.set("input.enex_files", [str(input_path)])
        config.set("input.input_directory", "")
    else:
        config.set("input.enex_files", [])
        config.set("input.input_directory", str(input_path))
    config.set("output.obsidian_vault", str(output_path))
    if args.verbose:
        config.set("logging.level", "DEBUG")
    if args.json:
        config.set("logging.console", False)

    converter = EvernoteToObsidianConverter(config=config)
    if args.reset:
        converter.sync_manager.reset_sync_state()
        return _result(
            "convert", "reset", input_files, str(output_path), True,
            {"reset": True},
        )

    success, stats = converter.run(preview=args.preview)
    return _result(
        "convert",
        "preview" if args.preview else "convert",
        input_files,
        str(output_path),
        success,
        stats,
        None if success else "ENEX转换失败或没有可转换的笔记",
    )


def _credentials_from_config_or_env(config: Config) -> Tuple[str, str]:
    """Resolve credentials without ever prompting on the agent CLI path."""
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


def run_migrate(args: argparse.Namespace) -> Dict[str, Any]:
    """Run the complete migration without interactive prompts."""
    config = _load_config(args.config)
    username, password = _credentials_from_config_or_env(config)
    config.set(
        "evernote_credentials", {"username": username, "password": password}
    )

    if args.output is not None:
        config.set(
            "output.obsidian_vault", str(args.output.expanduser().resolve())
        )
    output = config.get("output.obsidian_vault")
    if not output:
        raise ValueError("必须通过--output或配置文件指定Obsidian库路径")

    config.set("migration.auto_open_obsidian", not args.no_open)
    if args.verbose:
        config.set("logging.level", "DEBUG")
    if args.json:
        config.set("logging.console", False)

    migrator = UnifiedMigrator()
    migrator.config = config
    success = migrator.run_migration()
    return _result(
        "migrate",
        "migrate",
        [],
        str(Path(output).expanduser().resolve()),
        success,
        migrator.stats,
        None if success else "完整迁移失败",
    )


def _dispatch(args: argparse.Namespace) -> Dict[str, Any]:
    if args.command == "convert":
        return run_convert(args)
    if args.command == "migrate":
        return run_migrate(args)
    raise ValueError(f"不支持的命令: {args.command}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point returning a shell-friendly status code."""
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
            args.command, "interrupted", [], None, False, error="用户中断操作"
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
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    elif not result["success"]:
        print(f"❌ {result['error'] or '命令失败'}", file=sys.stderr)

    return 0 if result["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
