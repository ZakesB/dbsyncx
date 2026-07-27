from abc import ABC, abstractmethod
from typing import List

from dbsyncx.backup.models import Backup



class StorageProvider(ABC):
    """
    Abstract base class for all storage providers.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Returns the name of the storage provider.
        """
        raise NotImplementedError
    
    @abstractmethod
    def upload_backup(self, backup: Backup) -> None:
        """
        Uploads a backup to the storage provider.
        """
        raise NotImplementedError
    
    @abstractmethod
    def download_backup(self, backup: Backup) -> None:
        """
        Downloads a backup from the storage provider.
        """
        raise NotImplementedError
    
    @abstractmethod
    def exists(self, backup: Backup) -> bool:
        """
        Checks if a backup exists in the storage provider.
        """
        raise NotImplementedError
    
    @abstractmethod
    def delete_backup(self, backup: Backup) -> None:
        """
        Deletes a backup from the storage provider.
        """
        raise NotImplementedError