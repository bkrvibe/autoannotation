import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from google.cloud import storage
from app.core.config import settings

class GCSService:
    """Service for interacting with Google Cloud Storage."""
    
    def __init__(self):
        """Initialize the GCS client."""
        # This will automatically use GOOGLE_APPLICATION_CREDENTIALS from env
        self.client = storage.Client()
        self.bucket = self.client.bucket(settings.GCS_BUCKET)
    
    def generate_signed_url_put(self, blob_name: str, content_type: str) -> str:
        """
        Generate a signed URL for uploading a file (PUT).
        Current demo credentials might not support this if purely User Credentials, 
        but Service Accounts do.
        """
        blob = self.bucket.blob(blob_name)
        url = blob.generate_signed_url(
            version="v4",
            expiration=3600, # 1 hour
            method="PUT",
            content_type=content_type
        )
        return url

    def generate_signed_url_get(self, blob_name: str) -> str:
        """Generate a signed URL for reading a file (GET)."""
        blob = self.bucket.blob(blob_name)
        url = blob.generate_signed_url(
            version="v4",
            expiration=3600, # 1 hour
            method="GET",
        )
        return url

    def generate_unique_path(self, original_filename: str, tenant_id: str = "default") -> str:
        """
        Generate a unique GCS path based on timestamp.
        Format: prefix/tenants/{tenant_id}/uploads/{timestamp}/{filename}
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        return f"{settings.GCS_UPLOAD_PREFIX}/tenants/{tenant_id}/uploads/{timestamp}/{original_filename}"
    
    def upload_file(self, local_path: str, gcs_path: Optional[str] = None) -> str:
        """
        Upload a single file to GCS (Server-side).
        """
        local_path = Path(local_path)
        
        if gcs_path is None:
            # Fallback for dev if no tenant specified
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
            gcs_path = f"{settings.GCS_UPLOAD_PREFIX}/uploads/{timestamp}/{local_path.name}"
        
        blob = self.bucket.blob(gcs_path)
        blob.upload_from_filename(str(local_path))
        
        # Return full gs:// URI for Airflow
        return f"gs://{settings.GCS_BUCKET}/{gcs_path}"
    
    def download_file(self, gcs_uri: str, local_path: str) -> str:
        """
        Download a file from GCS to local path.
        """
        # Remove gs://bucket/ prefix if present
        if gcs_uri.startswith("gs://"):
            path_part = gcs_uri.replace(f"gs://{settings.GCS_BUCKET}/", "")
        else:
            path_part = gcs_uri
        
        blob = self.bucket.blob(path_part)
        
        # Ensure directory exists
        local_path_obj = Path(local_path)
        local_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        blob.download_to_filename(str(local_path))
        
        return str(local_path)
