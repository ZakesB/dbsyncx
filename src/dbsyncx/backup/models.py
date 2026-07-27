from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

@dataclass
class BaseMetadataModel:
    """
    Metadata describing a database backup.
    """
    id: str
    database: str
    created_at: datetime
    size: int
    checksum: Optional[str] = None
    duration: Optional[float] = None
    db_version: Optional[str] = None
    tool_version: Optional[str] = None


@dataclass
class Backup:
    """
    Represents a database backup and its storage information.
    """
    metadata: BaseMetadataModel
    filename: str
    provider: str
    location: str
    path: Optional[Path] = None


@dataclass
class RetentionPolicy:
    """
    Represents a retention policy for database backups.
    """
    enable: bool = True
    keep_last: Optional[int] = None
    max_age_days: Optional[int] = None


@dataclass
class BackupResult:
    """
    Represents a database backup restore operation.
    """
    backup: Backup
    uploaded: bool = False
    retained: bool = False