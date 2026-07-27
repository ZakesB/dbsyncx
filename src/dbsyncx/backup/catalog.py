import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Dict, List, Optional

from dbsyncx.backup.models import Backup, BaseMetadataModel



class BackupCatalog:
    """
    Manages the backup catalog.
    """

    def __init__(self, catalog_path: Path):
        self.catalog_path = catalog_path
        self._backups: Dict[str, Backup] = {}

        if self.catalog_path.exists():
            self.load()
    
    def load(self) -> None:
        """
        Load the catalog from disk
        """
        with self.catalog_path.open("r", encoding="utf-8") as fp:
            data = json.load(fp)
        
        self._backups.clear()

        for item in data:
            metadata = item["metadata"]

            backup = Backup(
                metadata=BaseMetadataModel(
                    id=metadata["id"],
                    database=metadata["database"],
                    created_at=datetime.fromisoformat(metadata["created_at"]),
                    size=metadata["size"],
                    checksum=metadata.get("checksum"),
                    duration=metadata.get("duration"),
                    db_version=metadata.get("db_version"),
                    tool_version=metadata.get("tool_version"),
                ),
                filename=item["filename"],
                provider=item["provider"],
                location=item["location"],
                path=Path(item["path"]) if item.get("path") else None,
            )

            self._backups[backup.metadata.id] = backup
    
    def save(self) -> None:
        """
        Persist the catalog
        """
        self.catalog_path.parent.mkdir(parents=True, exist_ok=True)

        backups = []

        for backup in self._backups.values():
            backups.append(
                {
                    "metadata": {
                        "id": backup.metadata.id,
                        "database": backup.metadata.database,
                        "created_at": backup.metadata.created_at.isoformat(),
                        "size": backup.metadata.size,
                        "checksum": backup.metadata.checksum,
                        "duration": backup.metadata.duration,
                        "db_version": backup.metadata.db_version,
                        "tool_version": backup.metadata.tool_version,
                    },
                    "filename": str(backup.filename),
                    "provider": backup.provider,
                    "location": str(backup.location),
                    "path": str(backup.path) if backup.path else None,
                }
            )

        with NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=self.catalog_path.parent,
            delete=False,
        ) as tmp:
            json.dump(backups, tmp, indent=4)
            tmp.flush()

        Path(tmp.name).replace(self.catalog_path)
    
    def add(self, backup: Backup) -> None:
        """
        Add a backup to the catalog
        """

        self._backups[backup.metadata.id] = backup

    def remove(self, backup_id: str) -> None:
        """
        Remove a backup
        """

        self._backups.pop(backup_id, None)

    def get(self, backup_id: str) -> Optional[Backup]:
        """
        Return a backup
        """

        return self._backups.get(backup_id)

    def list(self) -> List[Backup]:
        """
        Return all backups
        """

        return list(self._backups.values())

    def exists(self, backup_id: str) -> bool:
        """
        Return whether a backup exists
        """

        return backup_id in self._backups

    def clear(self) -> None:
        """
        Clear the catalog
        """

        self._backups.clear()