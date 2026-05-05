from __future__ import annotations

import json
import sys
from getpass import getpass
from pathlib import Path

import click

from .doctor import run_doctor
from .evernote_backup import EvernoteBackupSource
from .runner import MigrationRunner


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--app-data", type=click.Path(file_okay=False, path_type=Path), default=None)
@click.pass_context
def cli(ctx: click.Context, app_data: Path | None) -> None:
    """Evernote/Yinxiang to Obsidian migration tool."""
    ctx.obj = {"app_data": app_data}


@cli.command()
@click.option("--vault", type=click.Path(file_okay=False, path_type=Path), required=True)
@click.option("--username", required=True)
@click.option("--password", default=None)
@click.option("--backend", default="china", show_default=True)
@click.option("--task-id", default=None)
@click.option("--dry-run", is_flag=True)
@click.pass_context
def migrate(
    ctx: click.Context,
    vault: Path,
    username: str,
    password: str | None,
    backend: str,
    task_id: str | None,
    dry_run: bool,
) -> None:
    """Sync Yinxiang account data and migrate it into an Obsidian vault."""
    app_data = ctx.obj["app_data"]
    work_dir = _task_work_dir(app_data, task_id)
    export_dir = work_dir / "enex"
    password = password if password is not None else getpass("Password: ")
    source = EvernoteBackupSource(backend=backend, work_dir=work_dir, dry_run=dry_run)
    enex_files = source.sync_and_export(username, password, export_dir)
    if dry_run:
        click.echo("Dry run commands:")
        for command in source.commands:
            click.echo(command.command)
        return
    state = MigrationRunner(app_data_dir=app_data).import_enex(enex_files, vault, task_id=task_id)
    click.echo(f"Task {state.task_id} completed: {state.stats.converted_notes} notes converted")


@cli.command("import-enex")
@click.argument("files", type=click.Path(exists=True, dir_okay=False, path_type=Path), nargs=-1, required=True)
@click.option("--vault", type=click.Path(file_okay=False, path_type=Path), required=True)
@click.option("--task-id", default=None)
@click.pass_context
def import_enex(ctx: click.Context, files: tuple[Path, ...], vault: Path, task_id: str | None) -> None:
    """Import local ENEX files into an Obsidian vault."""
    state = MigrationRunner(app_data_dir=ctx.obj["app_data"]).import_enex(
        list(files),
        vault_path=vault,
        task_id=task_id,
    )
    click.echo(f"Task {state.task_id} completed: {state.stats.converted_notes} notes converted")
    click.echo(f"Vault: {state.vault_path}")


@cli.command()
@click.option("--username", required=True)
@click.option("--password", default=None)
@click.option("--backend", default="china", show_default=True)
@click.option("--output", type=click.Path(file_okay=False, path_type=Path), default=None)
@click.option("--dry-run", is_flag=True)
@click.pass_context
def sync(
    ctx: click.Context,
    username: str,
    password: str | None,
    backend: str,
    output: Path | None,
    dry_run: bool,
) -> None:
    """Sync account data and export ENEX without writing an Obsidian vault."""
    app_data = ctx.obj["app_data"]
    work_dir = _task_work_dir(app_data, None)
    output_dir = output or work_dir / "enex"
    password = password if password is not None else ("" if dry_run else getpass("Password: "))
    source = EvernoteBackupSource(backend=backend, work_dir=work_dir, dry_run=dry_run)
    source.sync_and_export(username, password, output_dir)
    if dry_run:
        click.echo("Dry run commands:")
    else:
        click.echo(f"Exported ENEX files to {output_dir}")
    for command in source.commands:
        click.echo(command.command)


@cli.command()
@click.argument("task_id")
@click.pass_context
def resume(ctx: click.Context, task_id: str) -> None:
    """Resume an interrupted migration task."""
    state = MigrationRunner(app_data_dir=ctx.obj["app_data"]).resume(task_id)
    click.echo(f"Task {state.task_id} {state.status}: {state.stats.converted_notes} notes converted")


@cli.command()
@click.argument("task_id")
@click.option("--json", "as_json", is_flag=True)
@click.pass_context
def report(ctx: click.Context, task_id: str, as_json: bool) -> None:
    """Show a task report."""
    payload = MigrationRunner(app_data_dir=ctx.obj["app_data"]).report(task_id)
    if as_json:
        click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        click.echo(f"Task {payload['task_id']}: {payload['status']} ({payload['phase']})")
        click.echo(f"Converted notes: {payload['stats']['converted_notes']}")


@cli.command()
@click.option("--vault", type=click.Path(file_okay=False, path_type=Path), default=None)
@click.option("--evernote-command", default="evernote-backup", show_default=True)
@click.option("--json", "as_json", is_flag=True)
@click.pass_context
def doctor(ctx: click.Context, vault: Path | None, evernote_command: str, as_json: bool) -> None:
    """Check local environment readiness."""
    payload = run_doctor(
        vault_path=vault,
        app_data_dir=ctx.obj["app_data"],
        evernote_command=evernote_command,
    )
    if as_json:
        click.echo(json.dumps(payload.to_dict(), ensure_ascii=False, indent=2))
        return
    for check in payload.checks:
        click.echo(f"[{check.status}] {check.name}: {check.message}")


@cli.command()
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", type=int, default=0, show_default=True)
@click.pass_context
def web(ctx: click.Context, host: str, port: int) -> None:
    """Start the local Web interface."""
    from .web import main as web_main

    web_main(app_data=ctx.obj["app_data"], host=host, port=port)


def _task_work_dir(app_data: Path | None, task_id: str | None) -> Path:
    root = app_data or (Path.home() / ".evernote2obsidian")
    return root / "tasks" / (task_id or "sync")


def main(argv: list[str] | None = None) -> int:
    try:
        cli.main(args=argv, prog_name="evernote2obsidian", standalone_mode=False)
        return 0
    except click.ClickException as exc:
        exc.show()
        return exc.exit_code


if __name__ == "__main__":
    sys.exit(main())

