from pathlib import Path

from dbsyncx.backup.catalog import BackupCatalog
from dbsyncx.backup.manager import BackupManager
from dbsyncx.backup.retention import retention_policy_from_config
from dbsyncx.storage.registry import StorageRegistry


def create_backup_manager(config) -> BackupManager:
    backup_config = config["backup"]

    _cls = StorageRegistry.get_provider(
        backup_config["provider"]
    )

    provider = _cls.from_config(backup_config)

    catalog = BackupCatalog(
        Path(backup_config["directory"]) / backup_config["catalog"]
    )

    return BackupManager(
        catalog=catalog,
        provider=provider,
        retention_policy=retention_policy_from_config(backup_config.get("retention")),
    )
