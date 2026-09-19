from datetime import datetime, timedelta

import pytest

from dbsyncx.backup.catalog import BackupCatalog
from dbsyncx.backup.manager import BackupManager
from dbsyncx.backup.models import Backup, BaseMetadataModel, RetentionPolicy
from dbsyncx.backup.retention import backups_to_prune, retention_policy_from_config
from dbsyncx.exceptions import ConfigError


class _Provider:
    name = "local"

    def __init__(self):
        self.uploaded = []
        self.deleted = []

    def upload_backup(self, backup):
        self.uploaded.append(backup.metadata.id)

    def delete_backup(self, backup):
        self.deleted.append(backup.metadata.id)


def _backup(backup_id, database, created_at, provider="local"):
    return Backup(
        metadata=BaseMetadataModel(
            id=backup_id,
            database=database,
            created_at=created_at,
            size=1,
        ),
        filename=f"{backup_id}.dump",
        provider=provider,
        location=backup_id,
    )


def test_retention_keeps_recent_and_newest_backups_per_database():
    now = datetime(2026, 9, 18, 12, 0, 0)
    backups = [
        _backup("production-new", "production", now - timedelta(days=1)),
        _backup("production-recent", "production", now - timedelta(days=3)),
        _backup("production-old", "production", now - timedelta(days=10)),
        _backup("reporting-only", "reporting", now - timedelta(days=20)),
    ]

    selected = backups_to_prune(
        backups,
        RetentionPolicy(keep_last=2, max_age_days=7),
        now=now,
    )

    assert [backup.metadata.id for backup in selected] == ["production-old"]


def test_retention_keep_last_prunes_excess_backups_without_an_age_limit():
    now = datetime(2026, 9, 18, 12, 0, 0)
    backups = [
        _backup("new", "production", now - timedelta(hours=1)),
        _backup("old", "production", now - timedelta(hours=2)),
    ]

    selected = backups_to_prune(backups, RetentionPolicy(keep_last=1), now=now)

    assert [backup.metadata.id for backup in selected] == ["old"]


def test_prune_dry_run_does_not_delete_or_change_the_catalog(tmp_path):
    now = datetime.now()
    old = _backup("old", "production", now - timedelta(days=2))
    newest = _backup("new", "production", now - timedelta(days=1))
    other_provider = _backup("remote", "production", now - timedelta(days=3), provider="gdrive")
    catalog = BackupCatalog(tmp_path / "catalog.json")
    for backup in (old, newest, other_provider):
        catalog.add(backup)
    catalog.save()
    provider = _Provider()
    manager = BackupManager(catalog, provider, RetentionPolicy(keep_last=1))

    candidates = manager.prune(dry_run=True)

    assert [backup.metadata.id for backup in candidates] == ["old"]
    assert provider.deleted == []
    assert {backup.metadata.id for backup in catalog.list()} == {"old", "new", "remote"}


def test_prune_deletes_candidates_and_persists_catalog(tmp_path):
    now = datetime.now()
    old = _backup("old", "production", now - timedelta(days=2))
    newest = _backup("new", "production", now - timedelta(days=1))
    catalog_path = tmp_path / "catalog.json"
    catalog = BackupCatalog(catalog_path)
    for backup in (old, newest):
        catalog.add(backup)
    catalog.save()
    provider = _Provider()
    manager = BackupManager(catalog, provider, RetentionPolicy(keep_last=1))

    pruned = manager.prune()

    assert [backup.metadata.id for backup in pruned] == ["old"]
    assert provider.deleted == ["old"]
    reloaded_catalog = BackupCatalog(catalog_path)
    assert [backup.metadata.id for backup in reloaded_catalog.list()] == ["new"]


def test_enabled_policy_prunes_after_registering_a_backup(tmp_path):
    now = datetime.now()
    old = _backup("old", "production", now - timedelta(days=1))
    newest = _backup("new", "production", now)
    catalog = BackupCatalog(tmp_path / "catalog.json")
    catalog.add(old)
    catalog.save()
    provider = _Provider()
    manager = BackupManager(
        catalog,
        provider,
        RetentionPolicy(enabled=True, keep_last=1),
    )

    manager.register_backup(newest)

    assert provider.uploaded == ["new"]
    assert provider.deleted == ["old"]
    assert [backup.metadata.id for backup in catalog.list()] == ["new"]


def test_retention_policy_rejects_invalid_limit_values():
    with pytest.raises(ConfigError, match="keep_last"):
        retention_policy_from_config({"keep_last": -1})

    with pytest.raises(ConfigError, match="max_age_days"):
        retention_policy_from_config({"max_age_days": True})

    with pytest.raises(ConfigError, match="must be a mapping"):
        retention_policy_from_config("keep_last: 7")
