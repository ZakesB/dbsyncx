from pathlib import Path
from .base import StorageProvider
from typing import List
from dbsyncx.backup.models import Backup



class LocalStorageProvider(StorageProvider):
    """
    Local storage provider for managing backups on the local filesystem.
    """
    name = "local"

    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def upload_backup(self, backup: Backup) -> None:
        # For local storage, uploading is not needed as the backup is already on the local filesystem.
        # I could implement a method to store the backup to a different location if needed.
        pass

    def download_backup(self, backup: Backup) -> None:
        # For local storage, downloading is not needed as the backup is already on the local filesystem.
        # I could implement a method to copy the backup to a different location if needed.
        pass

    def exists(self, backup: Backup) -> bool:
        return backup.path.exists() if backup.path else False

    def delete_backup(self, backup: Backup) -> None:
        if backup.path and backup.path.exists():
            backup.path.unlink()