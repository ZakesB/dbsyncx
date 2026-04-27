from typer.testing import CliRunner
from dbsyncx.main import app

runner = CliRunner()

def test_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0

def test_init():
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0