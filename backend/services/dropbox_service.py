import os
import dropbox
from dropbox.exceptions import AuthError, ApiError
from dropbox.files import WriteMode
from fastapi import HTTPException
from typing import Tuple
import uuid
from datetime import datetime
import requests

class DropboxService:
    def __init__(self):
        """Initialize Dropbox service with credentials from environment variables"""
        self.app_key = os.getenv('DROPBOX_APP_KEY')
        self.app_secret = os.getenv('DROPBOX_APP_SECRET')
        self.refresh_token = os.getenv('DROPBOX_REFRESH_TOKEN')
        self.access_token = None
        self.is_available = False
        self.dbx = None
        
        if not self.refresh_token:
            print("⚠️  Dropbox refresh token not found in environment variables")
            return
        
        try:
            # Get fresh access token using refresh token
            self._refresh_access_token()
            if self.access_token:
                # Initialize Dropbox client with fresh access token
                self.dbx = dropbox.Dropbox(self.access_token)
                self._check_credentials()
        except Exception as e:
            print(f"⚠️  Dropbox initialization failed: {e}")
            self.dbx = None

    def _refresh_access_token(self):
        """Get a fresh access token using the refresh token"""
        try:
            response = requests.post('https://api.dropbox.com/oauth2/token', data={
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token,
                'client_id': self.app_key,
                'client_secret': self.app_secret
            })
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data['access_token']
                print("✅ Dropbox access token refreshed successfully")
                return True
            else:
                print(f"⚠️  Failed to refresh Dropbox token: {response.text}")
                return False
                
        except Exception as e:
            print(f"⚠️  Error refreshing Dropbox token: {e}")
            return False

    def _check_credentials(self):
        """Check if Dropbox credentials are valid"""
        try:
            self.dbx.users_get_current_account()
            self.is_available = True
            print("✅ Dropbox client initialized successfully")
        except AuthError as e:
            print(f"⚠️  Dropbox authentication failed: {e}")
            print("⚠️  Trying to refresh access token...")
            if self._refresh_access_token():
                # Reinitialize client with new token
                self.dbx = dropbox.Dropbox(self.access_token)
                try:
                    self.dbx.users_get_current_account()
                    self.is_available = True
                    print("✅ Dropbox client re-initialized successfully with refreshed token")
                except AuthError:
                    print("⚠️  Image upload feature will be disabled. Text notes will still work.")
                    self.is_available = False
            else:
                print("⚠️  Image upload feature will be disabled. Text notes will still work.")
                self.is_available = False

    def _retry_with_refresh(self, method_name: str, *args, **kwargs):
        """Retry a Dropbox API call with token refresh if needed"""
        if not self.dbx:
            raise HTTPException(status_code=503, detail="Dropbox client is not initialized")

        method = getattr(self.dbx, method_name, None)
        if not callable(method):
            raise HTTPException(status_code=500, detail=f"Dropbox API method '{method_name}' is unavailable")

        try:
            return method(*args, **kwargs)
        except AuthError as e:
            print(f"⚠️  Dropbox auth error, attempting token refresh: {e}")
            if not self._refresh_access_token():
                raise HTTPException(status_code=503, detail="Failed to refresh Dropbox credentials")

            # Recreate the client with the new token and retry the same method
            self.dbx = dropbox.Dropbox(self.access_token)
            method = getattr(self.dbx, method_name, None)
            if not callable(method):
                raise HTTPException(status_code=500, detail=f"Dropbox API method '{method_name}' is unavailable after refresh")
            try:
                return method(*args, **kwargs)
            except AuthError as refresh_error:
                raise HTTPException(status_code=503, detail="Dropbox authentication failed after refreshing credentials") from refresh_error

    def upload_image(self, file_content: bytes, filename: str, user_id: str) -> Tuple[str, str]:
        """
        Upload image to Dropbox and get a shareable link
        
        Args:
            file_content: The file's binary content
            filename: Original filename
            user_id: User ID for organizing files
            
        Returns:
            Tuple of (shareable_url, dropbox_path)
        """
        if not self.is_available or not self.dbx:
            raise HTTPException(
                status_code=503, 
                detail="Dropbox service is not available. Please contact administrator to refresh Dropbox credentials."
            )
            
        try:
            # Create a unique filename
            file_extension = os.path.splitext(filename)[1].lower()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_filename = f"{timestamp}_{uuid.uuid4().hex[:8]}{file_extension}"
            
            # Define Dropbox path: /Apps/NoteEmbellisher/{user_id}/{unique_filename}
            dropbox_path = f"/{user_id}/{unique_filename}"
            
            # Upload file with retry on auth failure
            self._retry_with_refresh("files_upload", file_content, dropbox_path, mode=WriteMode('add'))
            
            # Create a shareable link with retry on auth failure
            sharing_settings = self._retry_with_refresh("sharing_create_shared_link_with_settings", dropbox_path)
            
            # Modify URL for direct access
            shareable_url = sharing_settings.url.replace("?dl=0", "?raw=1")
            
            return shareable_url, dropbox_path
            
        except ApiError as e:
            print(f"Error uploading to Dropbox: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to upload image to Dropbox: {e}")

    def download_image_for_ocr(self, dropbox_path: str) -> bytes:
        """
        Download image from Dropbox for OCR processing
        
        Args:
            dropbox_path: The Dropbox file path
            
        Returns:
            File content as bytes
        """
        if not self.is_available or not self.dbx:
            raise HTTPException(
                status_code=503, 
                detail="Dropbox service is not available."
            )
            
        try:
            _, res = self._retry_with_refresh("files_download", path=dropbox_path)
            return res.content
            
        except ApiError as e:
            print(f"Error downloading from Dropbox: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to download image from Dropbox: {e}")

    def delete_image(self, dropbox_path: str) -> bool:
        """
        Delete image from Dropbox
        
        Args:
            dropbox_path: The Dropbox file path
            
        Returns:
            True if successful
        """
        if not self.is_available or not self.dbx:
            print("⚠️  Dropbox service not available, skipping deletion")
            return False
            
        try:
            self._retry_with_refresh("files_delete_v2", dropbox_path)
            return True
        except ApiError as e:
            print(f"Error deleting from Dropbox: {e}")
            return False

    def validate_file_type(self, filename: str, content_type: str) -> bool:
        """Validate if the file type is allowed"""
        allowed_extensions = {'.png', '.jpg', '.jpeg', '.pdf'}
        allowed_mime_types = {'image/png', 'image/jpeg', 'image/jpg', 'application/pdf'}
        
        file_extension = os.path.splitext(filename)[1].lower()
        
        return (file_extension in allowed_extensions and content_type in allowed_mime_types)

# Create a global instance
dropbox_service = DropboxService()
