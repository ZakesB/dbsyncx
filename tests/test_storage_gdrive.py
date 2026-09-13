from datetime import datetime
from pathlib import Path

from dbsyncx.backup.models import Backup, BaseMetadataModel
from dbsyncx.storage.gdrive import GoogleDriveStorageProvider
from dbsyncx.storage.registry import StorageRegistry


class _Request:
    def __init__(self, response):
        self.response = response

    def execute(self):
        return self.response


class _Files:
    def __init__(self):
        self.create_calls = []
        self.deleted = []

    def list(self, **kwargs):
        return _Request({"files": []})

    def create(self, **kwargs):
        self.create_calls.append(kwargs)
        return _Request({"id": "folder-id" if len(self.create_calls) == 1 else "backup-id"})

    def get(self, **kwargs):
        return _Request({"id": kwargs["fileId"]})

    def delete(self, **kwargs):
        self.deleted.append(kwargs["fileId"])
        return _Request({})


class _Client:
    def __init__(self):
        self.files_api = _Files()

    def files(self):
        return self.files_api


def _backup(path: Path) -> Backup:
    return Backup(
        metadata=BaseMetadataModel(
            id="backup-1", database="production", created_at=datetime.now(), size=path.stat().st_size
        ),
        filename=path.name,
        provider="gdrive",
        location="",
        path=path,
    )


def test_gdrive_provider_uploads_to_created_folder(tmp_path):
    dump = tmp_path / "production.dump"
    dump.write_bytes(b"backup")
    client = _Client()
    provider = GoogleDriveStorageProvider(
        base_path=tmp_path,
        credentials_file="unused.json",
        client=client,
        media_upload_factory=lambda path, resumable: (path, resumable),
    )
    backup = _backup(dump)

    provider.upload_backup(backup)

    assert backup.location == "backup-id"
    folder_call, upload_call = client.files_api.create_calls
    assert folder_call["body"]["name"] == "dbsyncx-backups"
    assert upload_call["body"]["parents"] == ["folder-id"]
    assert upload_call["body"]["appProperties"] == {"dbsyncx_backup_id": "backup-1"}
    assert upload_call["media_body"] == (str(dump), True)


def test_gdrive_provider_is_registered_and_deletes_remote_file(tmp_path):
    assert StorageRegistry.get_provider("gdrive") is GoogleDriveStorageProvider
    dump = tmp_path / "production.dump"
    dump.write_bytes(b"backup")
    client = _Client()
    provider = GoogleDriveStorageProvider(
        base_path=tmp_path,
        credentials_file="unused.json",
        folder_id="folder-id",
        client=client,
    )
    backup = _backup(dump)
    backup.location = "backup-id"

    assert provider.exists(backup) is True
    provider.delete_backup(backup)
    assert client.files_api.deleted == ["backup-id"]
