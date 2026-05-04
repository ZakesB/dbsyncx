import typer
from typing import Optional
from .config import (
    init_config,
    load_config,
    get_database_url,
    resolve_config_path,
)
from .sync import pull_db, push_db, dump_db
from .exceptions import DbSyncXError
from .utils import success, error
from .adapters import get_adapter
from . import __version__

app = typer.Typer(help="dbsyncx - Database sync tool")

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
):
    try:
        config = ctx.obj["config"]
        if not config:
            error("Config not found. Run: dbsyncx init")
            raise typer.Exit(1)

        if not force and not dry_run:
            confirm = typer.confirm(
                f"This will overwrite '{target}'. Continue?"
            )
            if not confirm:
                typer.echo("Cancelled")
                raise typer.Exit()

        pull_db(config, source, target, dry_run=dry_run)

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
):
    try:
        config = ctx.obj["config"]
        if not config:
            error("Config not found. Run: dbsyncx init")
            raise typer.Exit(1)

        if not force and not dry_run:
            confirm = typer.confirm(
                f"This will overwrite '{target}'. Continue?"
            )
            if not confirm:
                typer.echo("Cancelled")
                raise typer.Exit()

        push_db(config, source, target, dry_run=dry_run)

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
):
    """
    Dump database to file (backup)
    """
    try:
        config = ctx.obj["config"]
        if not config:
            error("Config not found. Run: dbsyncx init")
            raise typer.Exit(1)

        dump_db(config, name, output=output, dry_run=dry_run)

    except DbSyncXError as e:
        error(str(e))
        raise typer.Exit(1)
