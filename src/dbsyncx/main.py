import typer

from .config import init_config, load_config, get_database_url
from .sync import pull_db, push_db, dump_db
from .exceptions import DbSyncXError
from .utils import success, error
from .adapters import get_adapter
from . import __version__

app = typer.Typer(help="dbsyncx - Database sync tool")


@app.command()
def version():
    typer.echo(f"dbsyncx is at version {__version__}")


@app.command()
def init():
    try:
        init_config()
        success("Initialized config at .dbsyncx/config.yaml")
    except DbSyncXError as e:
        error(str(e))


@app.command()
def pull(
    source: str,
    target: str,
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate without executing"),
):
    try:
        config = load_config()

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
    source: str,
    target: str,
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate without executing"),
):
    try:
        config = load_config()

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
def status(name: str):
    try:
        config = load_config()
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
    name: str,
    output: str = typer.Option(None, "--output", "-o", help="Output file"),
    dry_run: bool = typer.Option(False, "--dry-run"),
):
    """
    Dump database to file (backup)
    """
    try:
        config = load_config()
        dump_db(config, name, output=output, dry_run=dry_run)

    except DbSyncXError as e:
        error(str(e))
        raise typer.Exit(1)