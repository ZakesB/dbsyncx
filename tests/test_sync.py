from unittest.mock import Mock

from dbsyncx.sync import dump_db, pull_db, push_db, restore_db


CONFIG = {
    "databases": {
        "local": {"url": "postgresql://localhost/local"},
        "production": {"url": "postgresql://localhost/production"},
    }
}


def test_pull_passes_schema_only_and_tables(monkeypatch):
    adapter = Mock()
    monkeypatch.setattr("dbsyncx.sync.get_adapter", lambda url: adapter)

    pull_db(
        CONFIG,
        "production",
        "local",
        schema_only=True,
        tables=["public.users"],
    )

    adapter.dump.assert_called_once()
    adapter.restore.assert_called_once()
    assert adapter.dump.call_args.kwargs == {
        "schema_only": True,
        "tables": ["public.users"],
    }
    assert adapter.restore.call_args.kwargs == {
        "schema_only": True,
        "tables": ["public.users"],
    }


def test_push_dry_run_skips_adapter_operations(monkeypatch):
    adapter = Mock()
    monkeypatch.setattr("dbsyncx.sync.get_adapter", lambda url: adapter)

    push_db(CONFIG, "local", "production", dry_run=True)

    adapter.dump.assert_not_called()
    adapter.restore.assert_not_called()


def test_dump_passes_schema_only_and_tables(monkeypatch):
    adapter = Mock()
    monkeypatch.setattr("dbsyncx.sync.get_adapter", lambda url: adapter)

    dump_db(
        CONFIG,
        "production",
        output="production.dump",
        schema_only=True,
        tables=["public.users", "audit_log"],
    )

    adapter.dump.assert_called_once_with(
        "postgresql://localhost/production",
        "production.dump",
        schema_only=True,
        tables=["public.users", "audit_log"],
    )


def test_restore_passes_schema_only_and_tables(monkeypatch):
    adapter = Mock()
    monkeypatch.setattr("dbsyncx.sync.get_adapter", lambda url: adapter)

    restore_db(
        CONFIG,
        "local",
        "production.dump",
        schema_only=True,
        tables=["public.users"],
    )

    adapter.restore.assert_called_once_with(
        "postgresql://localhost/local",
        "production.dump",
        schema_only=True,
        tables=["public.users"],
    )
