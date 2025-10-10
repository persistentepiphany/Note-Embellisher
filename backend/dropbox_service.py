import os
import dropbox
from dropbox.exceptions import AuthError, ApiError
from dropbox.files import WriteMode
from fastapi import HTTPException
from typing import Tuple
import uuid
from datetime import datetime

class DropboxService:
    def __init__(self):
        """Initialize Dropbox service with credentials from environment variables"""
        self.app_key = os.getenv('DROPBOX_APP_KEY')
        self.app_secret = os.getenv('DROPBOX_APP_SECRET')
        self.access_token = os.getenv('DROPBOX_TOKEN')
        
        if not self.access_token:
            raise ValueError("Dropbox access token not found in environment variables")
        
        # Initialize Dropbox client with access token
        self.dbx = dropbox.Dropbox(self.access_token)
        self._check_credentials()

    def _check_credentials(self):
        """Check if Dropbox credentials are valid"""
        try:
            self.dbx.users_get_current_account()
            print("✅ Dropbox client initialized successfully")
        except AuthError:
            raise HTTPException(status_code=401, detail="Invalid Dropbox credentials")

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
        try:
            # Create a unique filename
            file_extension = os.path.splitext(filename)[1].lower()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_filename = f"{timestamp}_{uuid.uuid4().hex[:8]}{file_extension}"
            
            # Define Dropbox path: /Apps/NoteEmbellisher/{user_id}/{unique_filename}
            dropbox_path = f"/{user_id}/{unique_filename}"
            
            # Upload file
            self.dbx.files_upload(file_content, dropbox_path, mode=WriteMode('add'))
            
            # Create a shareable link
            sharing_settings = self.dbx.sharing_create_shared_link_with_settings(dropbox_path)
            
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
        try:
            _, res = self.dbx.files_download(path=dropbox_path)
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
        try:
            self.dbx.files_delete_v2(dropbox_path)
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
