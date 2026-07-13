from pathlib import Path

import pytest

from dbsyncx.config import DEFAULT_CONFIG, load_config, resolve_config_path


def test_default_config():
    assert "databases" in DEFAULT_CONFIG


def test_load_config_reads_resolved_path(tmp_path):
    config_path = tmp_path / "custom.yaml"
    config_path.write_text(
        "project_id: test\n"
        "databases:\n"
        "  local:\n"
        "    url: postgresql://localhost/local\n"
    )

    config = load_config(config_path)

    assert config["project_id"] == "test"
    assert config["databases"]["local"]["url"] == "postgresql://localhost/local"


def test_resolve_config_path_prefers_cli_path(tmp_path):
    config_path = tmp_path / "custom.yaml"
    config_path.write_text("databases: {}\n")

    assert resolve_config_path(str(config_path)) == config_path


def test_resolve_config_path_uses_env(monkeypatch, tmp_path):
    config_path = tmp_path / "env.yaml"
    config_path.write_text("databases: {}\n")
    monkeypatch.setenv("DBSYNCX_CONFIG", str(config_path))

    assert resolve_config_path() == config_path


def test_resolve_config_path_finds_local_yaml(monkeypatch, tmp_path):
    config_dir = tmp_path / ".dbsyncx"
    config_dir.mkdir()
    config_path = config_dir / "config.yaml"
    config_path.write_text("databases: {}\n")
    monkeypatch.chdir(tmp_path)

    assert resolve_config_path() == Path.cwd() / ".dbsyncx" / "config.yaml"


def test_resolve_config_path_finds_local_yml(monkeypatch, tmp_path):
    config_dir = tmp_path / ".dbsyncx"
    config_dir.mkdir()
    config_path = config_dir / "config.yml"
    config_path.write_text("databases: {}\n")
    monkeypatch.chdir(tmp_path)

    assert resolve_config_path() == Path.cwd() / ".dbsyncx" / "config.yml"


def test_resolve_config_path_missing(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DBSYNCX_CONFIG", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")

    with pytest.raises(FileNotFoundError):
        resolve_config_path()
