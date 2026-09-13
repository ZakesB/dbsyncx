"""Google Drive storage provider for database backup files."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

from dbsyncx.exceptions import DbSyncXError
from dbsyncx.storage.base import StorageProvider

if TYPE_CHECKING:
    from dbsyncx.backup.models import Backup


DRIVE_SCOPE = "https://www.googleapis.com/auth/drive.file"


class GoogleDriveStorageProvider(StorageProvider):
    """Store backup files in a Google Drive folder.

    Authentication supports either an OAuth desktop-client JSON file or a
    service-account JSON key.  OAuth access tokens are persisted locally so
    the browser authorization flow only occurs when required.
    """

    name = "gdrive"

    def __init__(
        self,
        base_path: Path,
        credentials_file: str,
        token_file: Optional[str] = None,
        folder_id: Optional[str] = None,
        folder_name: str = "dbsyncx-backups",
        client: Any = None,
        media_upload_factory: Optional[Callable[..., Any]] = None,
    ):
        self.base_path = Path(base_path)
        self.credentials_file = Path(credentials_file)
        self.token_file = Path(token_file) if token_file else Path(".dbsyncx/google-drive-token.json")
        self.folder_id = folder_id
        self.folder_name = folder_name
        self._client = client
        self._media_upload_factory = media_upload_factory

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "GoogleDriveStorageProvider":
        credentials_file = config.get("credentials_file")
        if not credentials_file:
            raise DbSyncXError(
                "Google Drive backups require backup.credentials_file. "
                "See the Google Drive configuration in the README."
            )
        return cls(
            base_path=Path(config["directory"]),
            credentials_file=credentials_file,
            token_file=config.get("token_file"),
            folder_id=config.get("folder_id"),
            folder_name=config.get("folder_name", "dbsyncx-backups"),
        )

    def _get_client(self):
        if self._client is not None:
            return self._client

        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google.oauth2 import service_account
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
        except ImportError as exc:
            raise DbSyncXError(
                "Google Drive support is not installed. Run: pip install 'dbsyncx[gdrive]'"
            ) from exc

        if not self.credentials_file.exists():
            raise DbSyncXError(
                f"Google Drive credentials file not found: {self.credentials_file}"
            )

        try:
            import json

            with self.credentials_file.open(encoding="utf-8") as file:
                credential_type = json.load(file).get("type")

            if credential_type == "service_account":
                credentials = service_account.Credentials.from_service_account_file(
                    str(self.credentials_file), scopes=[DRIVE_SCOPE]
                )
            else:
                credentials = None
                if self.token_file.exists():
                    credentials = Credentials.from_authorized_user_file(
                        str(self.token_file), [DRIVE_SCOPE]
                    )
                if credentials and credentials.expired and credentials.refresh_token:
                    credentials.refresh(Request())
                if not credentials or not credentials.valid:
                    credentials = InstalledAppFlow.from_client_secrets_file(
                        str(self.credentials_file), [DRIVE_SCOPE]
                    ).run_local_server(port=0)
                self.token_file.parent.mkdir(parents=True, exist_ok=True)
                self.token_file.write_text(credentials.to_json(), encoding="utf-8")
        except Exception as exc:
            raise DbSyncXError(f"Google Drive authentication failed: {exc}") from exc

        self._client = build("drive", "v3", credentials=credentials, cache_discovery=False)
        return self._client

    def _get_folder_id(self) -> str:
        if self.folder_id:
            return self.folder_id

        escaped_folder_name = self.folder_name.replace("'", "\\'")
        query = (
            "mimeType = 'application/vnd.google-apps.folder' "
            f"and name = '{escaped_folder_name}' "
            "and trashed = false"
        )
        response = self._get_client().files().list(
            q=query, spaces="drive", fields="files(id, name)", pageSize=1
        ).execute()
        files = response.get("files", [])
        if files:
            self.folder_id = files[0]["id"]
            return self.folder_id

        response = self._get_client().files().create(
            body={"name": self.folder_name, "mimeType": "application/vnd.google-apps.folder"},
            fields="id",
        ).execute()
        self.folder_id = response["id"]
        return self.folder_id

    def _media_upload(self, path: Path):
        if self._media_upload_factory:
            return self._media_upload_factory(str(path), resumable=True)
        try:
            from googleapiclient.http import MediaFileUpload
        except ImportError as exc:
            raise DbSyncXError(
                "Google Drive support is not installed. Run: pip install 'dbsyncx[gdrive]'"
            ) from exc
        return MediaFileUpload(str(path), resumable=True)

    def upload_backup(self, backup: Backup) -> None:
        if not backup.path or not Path(backup.path).is_file():
            raise DbSyncXError("Cannot upload backup: local dump file was not found.")

        path = Path(backup.path)
        try:
            uploaded = self._get_client().files().create(
                body={
                    "name": Path(backup.filename).name,
                    "parents": [self._get_folder_id()],
                    "appProperties": {"dbsyncx_backup_id": backup.metadata.id},
                },
                media_body=self._media_upload(path),
                fields="id, webViewLink",
            ).execute()
            backup.location = uploaded["id"]
        except DbSyncXError:
            raise
        except Exception as exc:
            raise DbSyncXError(f"Google Drive upload failed: {exc}") from exc

    def download_backup(self, backup: Backup) -> None:
        if not backup.location:
            raise DbSyncXError("Cannot download backup: its Google Drive file ID is missing.")
        destination = Path(backup.path) if backup.path else self.base_path / Path(backup.filename).name
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            from googleapiclient.http import MediaIoBaseDownload

            request = self._get_client().files().get_media(fileId=backup.location)
            with destination.open("wb") as output:
                downloader = MediaIoBaseDownload(output, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()
            backup.path = destination
        except ImportError as exc:
            raise DbSyncXError(
                "Google Drive support is not installed. Run: pip install 'dbsyncx[gdrive]'"
            ) from exc
        except Exception as exc:
            raise DbSyncXError(f"Google Drive download failed: {exc}") from exc

    def exists(self, backup: Backup) -> bool:
        if not backup.location:
            return False
        try:
            self._get_client().files().get(fileId=backup.location, fields="id").execute()
            return True
        except Exception:
            return False

    def delete_backup(self, backup: Backup) -> None:
        if not backup.location:
            return
        try:
            self._get_client().files().delete(fileId=backup.location).execute()
        except Exception as exc:
            raise DbSyncXError(f"Google Drive deletion failed: {exc}") from exc
