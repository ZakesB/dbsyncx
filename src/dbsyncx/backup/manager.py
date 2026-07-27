from typing import List, Optional

from dbsyncx.backup.catalog import BackupCatalog
from dbsyncx.backup.models import Backup
from dbsyncx.storage.base import StorageProvider


class BackupManager:
    """
    Coordinates backup management lifeclycle operations
    """

    def __init__(self, catalog: BackupCatalog, provider: StorageProvider):
        self.catalog = catalog
        self.provider = provider

    def register_backup(self, backup: Backup) -> Backup:
        """
        Register a completed backup.
        """

        self.provider.upload_backup(backup)

        self.catalog.add(backup)
        self.catalog.save()

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
    
    def prune(self) -> None:
        """
        Apply the configured retention policy.
        """
        # TODO: Implement retention policies.
        pass