import typer


def success(msg: str):
    typer.echo(typer.style(f"✔ {msg}", fg="green"))


def error(msg: str):
    typer.echo(typer.style(f"✖ {msg}", fg="red"), err=True)


def info(msg: str):
    typer.echo(typer.style(f"• {msg}", fg="blue"))

def confirm_action(message: str) -> bool:
    return typer.confirm(message)

def require_config(ctx: typer.Context):
    config = ctx.obj["config"]

    if not config:
        error("Config not found. Run: dbsyncx init")
        raise typer.Exit(1)

    return config