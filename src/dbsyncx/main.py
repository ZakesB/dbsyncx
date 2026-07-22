from dbsyncx.backup import create_backup_manager
import typer
from typing import Optional, List
from .config import (
    init_config,
    load_config,
    get_database_url,
    resolve_config_path,
)
from .sync import pull_db, push_db, dump_db, restore_db
from .exceptions import DbSyncXError
from .utils import format_bytes, require_config, success, error, info
from .adapters import get_adapter
from . import __version__

app = typer.Typer(help="dbsyncx - Database sync tool")
backup_app = typer.Typer(help="Manage backups")

app.add_typer(
    backup_app,
    name="backup",
)


def _validate_tables(tables: Optional[List[str]]) -> Optional[List[str]]:
    if not tables:
        return None

    cleaned = [table.strip() for table in tables]
    empty_tables = [table for table in cleaned if not table]
    if empty_tables:
        raise DbSyncXError("Table names cannot be empty")

    return cleaned


def _confirmation_scope(schema_only: bool, tables: Optional[List[str]]) -> str:
    scope = []

    if schema_only:
        scope.append("schema only")

    if tables:
        scope.append(f"tables: {', '.join(tables)}")

    return f" ({'; '.join(scope)})" if scope else ""

@app.callback()
def main(
    ctx: typer.Context,
    config: Optional[str] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to config file",
    ),
):
    """
    Global CLI options (applies to all commands)
    """
    try:
        config_path = resolve_config_path(config)
        ctx.obj = {
            "config": load_config(config_path),
            "config_path": config_path,
        }
    except Exception:
        # Allow commands like 'init' to run without config
        ctx.obj = {
            "config": None,
            "config_path": None,
        }

@app.command()
def version():
    typer.echo(f"dbsyncx is at version {__version__}")


@app.command()
def init(ctx: typer.Context):
    try:
        init_config()
        success("Initialized config at .dbsyncx/config.yaml")
    except DbSyncXError as e:
        error(str(e))
        raise typer.Exit(1)


@app.command()
def pull(
    ctx: typer.Context,
    source: str,
    target: str,
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate without executing"),
    schema_only: bool = typer.Option(False, "--schema-only", help="Sync schema objects only"),
    table: Optional[List[str]] = typer.Option(None, "--table", "-t", help="Limit sync to a table. Repeat for multiple tables."),
):
    try:
        config = require_config(ctx)

        tables = _validate_tables(table)

        if not force and not dry_run:
            confirm = typer.confirm(
                f"This will overwrite '{target}'{_confirmation_scope(schema_only, tables)}. Continue?"
            )
            if not confirm:
                typer.echo("Cancelled")
                raise typer.Exit()

        pull_db(config, source, target, dry_run=dry_run, schema_only=schema_only, tables=tables)

    except DbSyncXError as e:
        error(str(e))
        raise typer.Exit(1)


@app.command()
def push(
    ctx: typer.Context,
    source: str,
    target: str,
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate without executing"),
    schema_only: bool = typer.Option(False, "--schema-only", help="Sync schema objects only"),
    table: Optional[List[str]] = typer.Option(None, "--table", "-t", help="Limit sync to a table. Repeat for multiple tables."),
):
    try:
        config = require_config(ctx)

        tables = _validate_tables(table)

        if not force and not dry_run:
            confirm = typer.confirm(
                f"This will overwrite '{target}'{_confirmation_scope(schema_only, tables)}. Continue?"
            )
            if not confirm:
                typer.echo("Cancelled")
                raise typer.Exit()

        push_db(config, source, target, dry_run=dry_run, schema_only=schema_only, tables=tables)

    except DbSyncXError as e:
        error(str(e))
        raise typer.Exit(1)


@app.command()
def status(ctx: typer.Context, name: str):
    try:
        config = require_config(ctx)

        url = get_database_url(config, name)
        adapter = get_adapter(url)

        if adapter.test_connection(url):
            success("Connection successful")
        else:
            error("Connection failed")
            raise typer.Exit(1)

    except DbSyncXError as e:
        error(str(e))
        raise typer.Exit(1)

@app.command()
def dump(
    ctx: typer.Context,
    name: str,
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file"
    ),
    dry_run: bool = typer.Option(False, "--dry-run"),
    schema_only: bool = typer.Option(False, "--schema-only", help="Dump schema objects only"),
    table: Optional[List[str]] = typer.Option(None, "--table", "-t", help="Limit dump to a table. Repeat for multiple tables."),
):
    """
    Dump database to file (backup)
    """
    try:
        config = require_config(ctx)

        tables = _validate_tables(table)
        dump_db(config, name, output=output, dry_run=dry_run, schema_only=schema_only, tables=tables)

    except DbSyncXError as e:
        error(str(e))
        raise typer.Exit(1)


@app.command()
def restore(
    ctx: typer.Context,
    name: str,
    input_file: str = typer.Argument(..., help="Dump file created by dbsyncx dump or pg_dump -Fc"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate without executing"),
    schema_only: bool = typer.Option(False, "--schema-only", help="Restore schema objects only"),
    table: Optional[List[str]] = typer.Option(None, "--table", "-t", help="Limit restore to a table. Repeat for multiple tables."),
):
    """
    Restore database from a dump file.
    """
    try:
        config = require_config(ctx)

        tables = _validate_tables(table)

        if not force and not dry_run:
            confirm = typer.confirm(
                f"This will overwrite '{name}' from '{input_file}'{_confirmation_scope(schema_only, tables)}. Continue?"
            )
            if not confirm:
                typer.echo("Cancelled")
                raise typer.Exit()

        restore_db(config, name, input_file, dry_run=dry_run, schema_only=schema_only, tables=tables)

    except DbSyncXError as e:
        error(str(e))
        raise typer.Exit(1)

# Below commands are for backup management lifecycle
@backup_app.command("list")
def backup_list(ctx: typer.Context):
    """
    List available backups
    """

    try:
        config = require_config(ctx)
        manager = create_backup_manager(config)
        backups = manager.list_backups()

        if not backups:
            info("No backups found.")
            return

        for backup in backups:
            typer.echo(
                f"{backup.metadata.id} "
                f"{backup.filename} "
                f"{backup.metadata.created_at}"
            )

    except DbSyncXError as e:
        error(str(e))
        raise typer.Exit(1)

@backup_app.command("info")
def backup_info(
    ctx: typer.Context,
    backup_id: str = typer.Argument(..., help="Backup ID"),
):
    """
    Show backup information.
    """
    try:
        config = require_config(ctx)
        manager = create_backup_manager(config)
        backup = manager.get_backup(backup_id)

        if backup is None:
            error(f"Backup '{backup_id}' not found.")
            raise typer.Exit(1)

        typer.echo(f"ID         : {backup.metadata.id}")
        typer.echo(f"Database   : {backup.metadata.database}")
        typer.echo(f"Provider   : {backup.provider}")
        typer.echo(f"Filename   : {backup.filename}")
        typer.echo(f"Location   : {backup.location}")

        if backup.path:
            typer.echo(f"Path       : {backup.path}")

        typer.echo(f'Created At : {backup.metadata.created_at.strftime("%Y-%m-%d %H:%M:%S")}')
        typer.echo(f"Size       : {format_bytes(backup.metadata.size)}")

        if backup.metadata.duration is not None:
            typer.echo(f"Duration   : {backup.metadata.duration:.2f}s")

        if backup.metadata.checksum:
            typer.echo(f"Checksum   : {backup.metadata.checksum}")

        if backup.metadata.db_version:
            typer.echo(f"DB Version : {backup.metadata.db_version}")

        if backup.metadata.tool_version:
            typer.echo(f"dbsyncx    : {backup.metadata.tool_version}")

    except DbSyncXError as e:
        error(str(e))
        raise typer.Exit(1)

@backup_app.command("delete")
def backup_delete(
    ctx: typer.Context,
    backup_id: str = typer.Argument(..., help="Backup ID"),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Skip confirmation",
    ),
):
    """
    Delete a backup.
    """
    try:
        config = require_config(ctx)
        manager = create_backup_manager(config)
        backup = manager.get_backup(backup_id)

        if backup is None:
            error(f"Backup '{backup_id}' not found.")
            raise typer.Exit(1)

        if not force:
            confirm = typer.confirm(
                f"Delete backup '{backup.metadata.id}'?"
            )

            if not confirm:
                typer.echo("Cancelled")
                raise typer.Exit()

        manager.delete_backup(backup_id)

        success(f"Deleted backup '{backup_id}'")

    except DbSyncXError as e:
        error(str(e))
        raise typer.Exit(1)

@backup_app.command("prune")
def backup_prune(ctx: typer.Context):
    """
    Remove backups according to the configured retention policy.
    """
    try:
        config = require_config(ctx)
        manager = create_backup_manager(config)
        manager.prune()

        success("Backup pruning completed.")

    except DbSyncXError as e:
        error(str(e))
        raise typer.Exit(1)
