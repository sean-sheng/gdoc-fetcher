"""Google Drive API client for uploading files."""
import mimetypes
from pathlib import Path
from typing import Dict, Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError


class DriveClient:
    """Client for Google Drive API."""

    def __init__(self, token: str):
        """
        Initialize Drive API client.

        Args:
            token: OAuth access token
        """
        credentials = Credentials(token=token)
        self.service = build('drive', 'v3', credentials=credentials)

    def upload_image(self, local_path: str, name: Optional[str] = None) -> str:
        """
        Upload image to Google Drive and return shareable URL.

        Args:
            local_path: Path to local image file
            name: Optional custom name (default: use filename)

        Returns:
            Shareable URL for the uploaded image

        Raises:
            FileNotFoundError: If local file doesn't exist
            ValueError: If file is not a supported image type
            HttpError: If upload fails
        """
        path = Path(local_path)
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {local_path}")

        # Use provided name or filename
        file_name = name or path.name

        # Detect MIME type
        mime_type, _ = mimetypes.guess_type(local_path)
        if not mime_type or not mime_type.startswith('image/'):
            raise ValueError(f"File is not a supported image type: {local_path}")

        # Prepare file metadata
        file_metadata = {
            'name': file_name,
            'mimeType': mime_type
        }

        # Create media upload
        media = MediaFileUpload(
            local_path,
            mimetype=mime_type,
            resumable=True
        )

        try:
            # Upload file
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink, webContentLink'
            ).execute()

            file_id = file['id']

            # Make file publicly accessible
            self._make_public(file_id)

            # Return direct link for embedding
            # Use webContentLink for direct download URL
            return file.get('webContentLink', f"https://drive.google.com/uc?id={file_id}")

        except HttpError as e:
            if e.resp.status == 403:
                raise ValueError("Permission denied. Check Drive API is enabled and authenticated.")
            elif e.resp.status == 404:
                raise ValueError("Drive API not found. Ensure Drive API is enabled in your project.")
            else:
                raise

    def _make_public(self, file_id: str):
        """
        Make file publicly accessible with link.

        Args:
            file_id: Google Drive file ID
        """
        permission = {
            'type': 'anyone',
            'role': 'reader'
        }

        try:
            self.service.permissions().create(
                fileId=file_id,
                body=permission
            ).execute()
        except HttpError:
            # If permission fails, continue anyway
            # The file will still be accessible to the uploader
            pass

    def batch_upload_images(self, image_paths: Dict[str, str]) -> Dict[str, str]:
        """
        Upload multiple images in batch.

        Args:
            image_paths: Dict mapping local paths to custom names (or None)

        Returns:
            Dict mapping local paths to uploaded URLs

        Note:
            Failed uploads will be skipped with a warning.
            Returns partial results if some uploads fail.
        """
        results = {}

        for local_path, name in image_paths.items():
            try:
                url = self.upload_image(local_path, name)
                results[local_path] = url
            except (FileNotFoundError, ValueError, HttpError) as e:
                # Log error but continue with other files
                print(f"Warning: Failed to upload {local_path}: {e}")
                continue

        return results
