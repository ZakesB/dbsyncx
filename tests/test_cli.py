import re
import os
from contextlib import contextmanager
from tempfile import TemporaryDirectory

from typer.testing import CliRunner
from dbsyncx.main import app

runner = CliRunner()


def _compact_help(output: str) -> str:
    """Remove terminal formatting and wrapping from Rich-rendered CLI help."""
    plain_output = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", output)
    return re.sub(r"\s+", "", plain_output)


@contextmanager
def isolated_filesystem():
    """Use a temporary current directory across supported Typer versions."""
    original_directory = os.getcwd()
    with TemporaryDirectory() as directory:
        os.chdir(directory)
        try:
            yield
        finally:
            os.chdir(original_directory)


def create_config():
    import os

    os.makedirs(".dbsyncx", exist_ok=True)
    with open(".dbsyncx/config.yaml", "w") as f:
        f.write(
            "project_id: test\n"
            "databases:\n"
            "  local:\n"
            "    url: postgresql://localhost/local\n"
            "  production:\n"
            "    url: postgresql://localhost/production\n"
        )


def test_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "1.3.1" in result.output

def test_init():
    with isolated_filesystem():
        result = runner.invoke(app, ["init"])
        assert result.exit_code == 0


def test_push_dry_run():
    with isolated_filesystem():
        create_config()

        result = runner.invoke(app, ["push", "local", "production", "--dry-run"])

        assert result.exit_code == 0
        assert "Dry run complete" in result.output


def test_pull_accepts_schema_only_and_tables(monkeypatch):
    calls = []

    def fake_pull(config, source, target, dry_run=False, schema_only=False, tables=None):
        calls.append(
            {
                "source": source,
                "target": target,
                "dry_run": dry_run,
                "schema_only": schema_only,
                "tables": tables,
            }
        )

    monkeypatch.setattr("dbsyncx.main.pull_db", fake_pull)

    with isolated_filesystem():
        create_config()

        result = runner.invoke(
            app,
            [
                "pull",
                "production",
                "local",
                "--force",
                "--schema-only",
                "--table",
                "public.users",
                "--table",
                "audit_log",
            ],
        )

        assert result.exit_code == 0
        assert calls == [
            {
                "source": "production",
                "target": "local",
                "dry_run": False,
                "schema_only": True,
                "tables": ["public.users", "audit_log"],
            }
        ]


def test_dump_accepts_schema_only_and_tables(monkeypatch):
    calls = []

    def fake_dump(config, name, output=None, dry_run=False, schema_only=False, tables=None):
        calls.append(
            {
                "name": name,
                "output": output,
                "dry_run": dry_run,
                "schema_only": schema_only,
                "tables": tables,
            }
        )

    monkeypatch.setattr("dbsyncx.main.dump_db", fake_dump)

    with isolated_filesystem():
        create_config()

        result = runner.invoke(
            app,
            [
                "dump",
                "production",
                "--output",
                "production.dump",
                "--schema-only",
                "--table",
                "public.users",
            ],
        )

        assert result.exit_code == 0
        assert calls == [
            {
                "name": "production",
                "output": "production.dump",
                "dry_run": False,
                "schema_only": True,
                "tables": ["public.users"],
            }
        ]


def test_restore_command(monkeypatch):
    calls = []

    def fake_restore(config, name, input_file, dry_run=False, schema_only=False, tables=None):
        calls.append(
            {
                "name": name,
                "input_file": input_file,
                "dry_run": dry_run,
                "schema_only": schema_only,
                "tables": tables,
            }
        )

    monkeypatch.setattr("dbsyncx.main.restore_db", fake_restore)

    with isolated_filesystem():
        create_config()

        result = runner.invoke(
            app,
            [
                "restore",
                "local",
                "production.dump",
                "--force",
                "--schema-only",
                "--table",
                "public.users",
            ],
        )

        assert result.exit_code == 0
        assert calls == [
            {
                "name": "local",
                "input_file": "production.dump",
                "dry_run": False,
                "schema_only": True,
                "tables": ["public.users"],
            }
        ]


def test_new_options_are_in_command_help():
    result = runner.invoke(app, ["dump", "--help"])

    assert result.exit_code == 0
    help_output = _compact_help(result.output)
    assert "--schema-only" in help_output
    assert "--table" in help_output
