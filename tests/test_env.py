import pytest

from dbsyncx.config import ConfigError, DbSyncXError
from dbsyncx.utils.env import interpolate, interpolate_env


def test_interpolate_required_variable(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/db")

    assert (
        interpolate_env("${DATABASE_URL}")
        == "postgresql://localhost/db"
    )


def test_interpolate_default_value(monkeypatch):
    monkeypatch.delenv("PORT", raising=False)

    assert interpolate_env("${PORT:5432}") == "5432"


def test_interpolate_existing_variable_overrides_default(monkeypatch):
    monkeypatch.setenv("PORT", "6543")

    assert interpolate_env("${PORT:5432}") == "6543"


def test_interpolate_multiple_variables(monkeypatch):
    monkeypatch.setenv("DB_USER", "postgres")
    monkeypatch.setenv("DB_PASSWORD", "secret")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "app")

    value = (
        "postgresql://${DB_USER}:${DB_PASSWORD}"
        "@${DB_HOST}:${DB_PORT}/${DB_NAME}"
    )

    assert (
        interpolate_env(value)
        == "postgresql://postgres:secret@localhost:5432/app"
    )


def test_interpolate_plain_string():
    assert interpolate_env("backups") == "backups"


def test_interpolate_missing_required_variable(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(DbSyncXError, match="DATABASE_URL"):
        interpolate_env("${DATABASE_URL}")


def test_interpolate_dictionary(monkeypatch):
    monkeypatch.setenv("PROJECT_ID", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/db")

    config = {
        "project_id": "${PROJECT_ID}",
        "databases": {
            "production": {
                "url": "${DATABASE_URL}",
            }
        },
    }

    expected = {
        "project_id": "production",
        "databases": {
            "production": {
                "url": "postgresql://localhost/db",
            }
        },
    }

    assert interpolate(config) == expected


def test_interpolate_list(monkeypatch):
    monkeypatch.setenv("TABLE1", "users")
    monkeypatch.setenv("TABLE2", "orders")

    value = [
        "${TABLE1}",
        "${TABLE2}",
    ]

    assert interpolate(value) == [
        "users",
        "orders",
    ]