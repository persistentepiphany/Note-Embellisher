from __future__ import annotations

import os
import secrets
from datetime import datetime, timezone
from typing import Any, Optional, Tuple

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    GOOGLE_DRIVE_LIBS_AVAILABLE = True
except ImportError as e:  # pragma: no cover - optional dependency
    Credentials = Any  # type: ignore
    Flow = Any  # type: ignore
    Request = Any  # type: ignore
    build = Any  # type: ignore
    MediaFileUpload = Any  # type: ignore
    GOOGLE_DRIVE_LIBS_AVAILABLE = False
    _GOOGLE_DRIVE_IMPORT_ERROR = e


class GoogleDriveService:
    """Handles OAuth workflows and uploads to Google Drive."""

    AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
    TOKEN_URI = "https://oauth2.googleapis.com/token"

    def __init__(self) -> None:
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.redirect_uri = os.getenv("GOOGLE_DRIVE_REDIRECT_URI")
        self.success_redirect = os.getenv("GOOGLE_DRIVE_SUCCESS_REDIRECT")
        self.default_folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
        self.scopes = ["https://www.googleapis.com/auth/drive.file"]
        self.is_configured = (
            GOOGLE_DRIVE_LIBS_AVAILABLE
            and bool(self.client_id and self.client_secret and self.redirect_uri)
        )
        if not self.is_configured:
            if not GOOGLE_DRIVE_LIBS_AVAILABLE:
                print(
                    f"Google Drive SDK not available: {_GOOGLE_DRIVE_IMPORT_ERROR}. "
                    "Install google-auth-oauthlib and google-api-python-client to enable uploads."
                )
            else:
                print(
                    "Google Drive service not configured. Set GOOGLE_CLIENT_ID, "
                    "GOOGLE_CLIENT_SECRET, and GOOGLE_DRIVE_REDIRECT_URI."
                )

    # ------------------------------------------------------------------
    # OAuth helpers
    # ------------------------------------------------------------------
    def _client_config(self) -> dict:
        if not self.is_configured:
            raise RuntimeError("Google Drive service not configured")
        return {
            "web": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "auth_uri": self.AUTH_URI,
                "token_uri": self.TOKEN_URI,
                "redirect_uris": [self.redirect_uri],
            }
        }

    def generate_state(self) -> str:
        return secrets.token_urlsafe(32)

    def generate_auth_url(self, state: str) -> Tuple[str, str]:
        """Return the Google OAuth URL and the underlying Flow state."""
        if not self.is_configured:
            raise RuntimeError("Google Drive service not configured")

        flow = Flow.from_client_config(self._client_config(), scopes=self.scopes, state=state)
        flow.redirect_uri = self.redirect_uri
        auth_url, flow_state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
            state=state,
        )
        return auth_url, flow_state

    def exchange_code_for_credentials(self, code: str) -> Any:
        if not self.is_configured:
            raise RuntimeError("Google Drive service not configured")

        flow = Flow.from_client_config(self._client_config(), scopes=self.scopes)
        flow.redirect_uri = self.redirect_uri
        flow.fetch_token(code=code)
        return flow.credentials

    # ------------------------------------------------------------------
    # Credential serialization helpers
    # ------------------------------------------------------------------
    def credentials_to_dict(self, credentials: Any) -> dict:
        return {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes,
            "expiry": credentials.expiry,
            "id_token": getattr(credentials, "id_token", None),
        }

    def build_credentials_from_record(self, record) -> Optional[Any]:
        """Rehydrate google.oauth2.credentials.Credentials from DB record."""
        if not self.is_configured or not record:
            return None
        if not record.refresh_token:
            return None

        creds = Credentials(
            token=record.access_token,
            refresh_token=record.refresh_token,
            token_uri=self.TOKEN_URI,
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=self.scopes,
        )
        if record.token_expiry:
            creds.expiry = record.token_expiry
        return creds

    def refresh_credentials(self, credentials: Any) -> Any:
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        return credentials

    # ------------------------------------------------------------------
    # Upload helpers
    # ------------------------------------------------------------------
    def upload_file(
        self,
    credentials: Any,
        file_path: str,
        mime_type: str,
        drive_filename: Optional[str] = None,
        description: Optional[str] = None,
    ) -> dict:
        if not self.is_configured:
            raise RuntimeError("Google Drive service not configured")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        credentials = self.refresh_credentials(credentials)
        drive_service = build("drive", "v3", credentials=credentials)

        metadata = {
            "name": drive_filename or os.path.basename(file_path),
            "mimeType": mime_type,
        }
        if description:
            metadata["description"] = description
        if self.default_folder_id:
            metadata["parents"] = [self.default_folder_id]

        media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
        result = (
            drive_service.files()
            .create(body=metadata, media_body=media, fields="id, name, webViewLink, webContentLink")
            .execute()
        )
        return result


google_drive_service = GoogleDriveService()
