import typer


def success(msg: str):
    typer.echo(typer.style(f"✔ {msg}", fg="green"))


def error(msg: str):
    typer.echo(typer.style(f"✖ {msg}", fg="red"), err=True)


def info(msg: str):
    typer.echo(typer.style(f"• {msg}", fg="blue"))

def confirm_action(message: str) -> bool:
    return typer.confirm(message)