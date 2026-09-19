from typing import List, Optional

from dbsyncx.backup.catalog import BackupCatalog
from dbsyncx.backup.models import Backup, RetentionPolicy
from dbsyncx.backup.retention import backups_to_prune
from dbsyncx.storage.base import StorageProvider


class BackupManager:
    """
    Coordinates backup management lifeclycle operations
    """

    def __init__(
        self,
        catalog: BackupCatalog,
        provider: StorageProvider,
        retention_policy: Optional[RetentionPolicy] = None,
    ):
        self.catalog = catalog
        self.provider = provider
        self.retention_policy = retention_policy or RetentionPolicy()

    def register_backup(self, backup: Backup) -> Backup:
        """
        Register a completed backup.
        """

        self.provider.upload_backup(backup)

        self.catalog.add(backup)
        self.catalog.save()

        if self.retention_policy.enabled:
            self.prune()

        return backup

    def list_backups(self) -> List[Backup]:
        """
        Return all backups.
        """

        return self.catalog.list()

    def get_backup(self, backup_id: str) -> Optional[Backup]:
        """
        Return a backup.
        """

        return self.catalog.get(backup_id)

    def delete_backup(self, backup_id: str) -> bool:
        """
        Delete a backup.
        """

        backup = self.catalog.get(backup_id)

        if backup is None:
            return False

        self.provider.delete_backup(backup)

        self.catalog.remove(backup_id)
        self.catalog.save()

        return True
    
    def prune(self, dry_run: bool = False) -> List[Backup]:
        """
        Apply the configured retention policy and return affected backups.

        In dry-run mode, no remote files or catalog entries are changed.
        """
        candidates = backups_to_prune(
            (
                backup
                for backup in self.catalog.list()
                if backup.provider == self.provider.name
            ),
            self.retention_policy,
        )
        if dry_run:
            return candidates

        for backup in candidates:
            self.provider.delete_backup(backup)
            self.catalog.remove(backup.metadata.id)
            self.catalog.save()

        return candidates
