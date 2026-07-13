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
from .utils import success, error
from .adapters import get_adapter
from . import __version__

app = typer.Typer(help="dbsyncx - Database sync tool")


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
        config = ctx.obj["config"]
        if not config:
            error("Config not found. Run: dbsyncx init")
            raise typer.Exit(1)

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
        config = ctx.obj["config"]
        if not config:
            error("Config not found. Run: dbsyncx init")
            raise typer.Exit(1)

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
        config = ctx.obj["config"]
        if not config:
            error("Config not found. Run: dbsyncx init")
            raise typer.Exit(1)

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
        config = ctx.obj["config"]
        if not config:
            error("Config not found. Run: dbsyncx init")
            raise typer.Exit(1)

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
        config = ctx.obj["config"]
        if not config:
            error("Config not found. Run: dbsyncx init")
            raise typer.Exit(1)

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
