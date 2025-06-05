
"""
Google Cloud Storage client for Audico Product Manager.

This module provides functionality for interacting with Google Cloud Storage,
including file upload, download, and management operations.
"""

import os
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
from google.cloud import storage
from google.api_core import exceptions as gcs_exceptions

# Use absolute import that works when running directly
try:
    from audico_product_manager.config import config
except ImportError:
    try:
        from .config import config
    except ImportError:
        from config import config


class GCSClient:
    """Client for interacting with Google Cloud Storage."""
    
    def __init__(self, bucket_name: Optional[str] = None, credentials_path: Optional[str] = None):
        """
        Initialize the GCS client.
        
        Args:
            bucket_name: Name of the GCS bucket
            credentials_path: Path to the service account credentials file
        """
        self.bucket_name = bucket_name or config.gcs_bucket_name
        self.credentials_path = credentials_path or config.google_application_credentials
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize the client
        self.client = None
        self.bucket = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Google Cloud Storage client."""
        try:
            # Set the credentials environment variable if not already set
            if self.credentials_path and os.path.exists(self.credentials_path):
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.credentials_path
            
            # Initialize the client
            self.client = storage.Client()
            self.bucket = self.client.bucket(self.bucket_name)
            
            self.logger.info(f"Successfully initialized GCS client for bucket: {self.bucket_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize GCS client: {str(e)}")
            raise
    
    def upload_file(self, local_file_path: str, gcs_file_path: str, 
                   content_type: Optional[str] = None) -> bool:
        """
        Upload a file to Google Cloud Storage.
        
        Args:
            local_file_path: Path to the local file
            gcs_file_path: Destination path in GCS
            content_type: MIME type of the file
            
        Returns:
            bool: True if upload successful, False otherwise
        """
        try:
            blob = self.bucket.blob(gcs_file_path)
            
            # Set content type if provided
            if content_type:
                blob.content_type = content_type
            
            # Upload the file
            blob.upload_from_filename(local_file_path)
            
            self.logger.info(f"Successfully uploaded {local_file_path} to gs://{self.bucket_name}/{gcs_file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to upload {local_file_path}: {str(e)}")
            return False
    
    def download_file(self, gcs_file_path: str, local_file_path: str) -> bool:
        """
        Download a file from Google Cloud Storage.
        
        Args:
            gcs_file_path: Path to the file in GCS
            local_file_path: Destination path for the downloaded file
            
        Returns:
            bool: True if download successful, False otherwise
        """
        try:
            blob = self.bucket.blob(gcs_file_path)
            
            # Create local directory if it doesn't exist
            local_dir = os.path.dirname(local_file_path)
            if local_dir:
                os.makedirs(local_dir, exist_ok=True)
            
            # Download the file
            blob.download_to_filename(local_file_path)
            
            self.logger.info(f"Successfully downloaded gs://{self.bucket_name}/{gcs_file_path} to {local_file_path}")
            return True
            
        except gcs_exceptions.NotFound:
            self.logger.error(f"File not found: gs://{self.bucket_name}/{gcs_file_path}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to download {gcs_file_path}: {str(e)}")
            return False
    
    def list_files(self, prefix: str = '', delimiter: str = None) -> List[str]:
        """
        List files in the GCS bucket.
        
        Args:
            prefix: Prefix to filter files
            delimiter: Delimiter for hierarchical listing
            
        Returns:
            List[str]: List of file paths
        """
        try:
            blobs = self.client.list_blobs(
                self.bucket_name, 
                prefix=prefix, 
                delimiter=delimiter
            )
            
            file_paths = [blob.name for blob in blobs]
            self.logger.info(f"Found {len(file_paths)} files with prefix '{prefix}'")
            return file_paths
            
        except Exception as e:
            self.logger.error(f"Failed to list files: {str(e)}")
            return []
    
    def file_exists(self, gcs_file_path: str) -> bool:
        """
        Check if a file exists in GCS.
        
        Args:
            gcs_file_path: Path to the file in GCS
            
        Returns:
            bool: True if file exists, False otherwise
        """
        try:
            blob = self.bucket.blob(gcs_file_path)
            return blob.exists()
            
        except Exception as e:
            self.logger.error(f"Error checking file existence: {str(e)}")
            return False
    
    def delete_file(self, gcs_file_path: str) -> bool:
        """
        Delete a file from GCS.
        
        Args:
            gcs_file_path: Path to the file in GCS
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        try:
            blob = self.bucket.blob(gcs_file_path)
            blob.delete()
            
            self.logger.info(f"Successfully deleted gs://{self.bucket_name}/{gcs_file_path}")
            return True
            
        except gcs_exceptions.NotFound:
            self.logger.warning(f"File not found for deletion: gs://{self.bucket_name}/{gcs_file_path}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to delete {gcs_file_path}: {str(e)}")
            return False
    
    def move_file(self, source_path: str, destination_path: str) -> bool:
        """
        Move a file within the GCS bucket.
        
        Args:
            source_path: Source file path in GCS
            destination_path: Destination file path in GCS
            
        Returns:
            bool: True if move successful, False otherwise
        """
        try:
            source_blob = self.bucket.blob(source_path)
            destination_blob = self.bucket.blob(destination_path)
            
            # Copy the file
            destination_blob.rewrite(source_blob)
            
            # Delete the original
            source_blob.delete()
            
            self.logger.info(f"Successfully moved gs://{self.bucket_name}/{source_path} to gs://{self.bucket_name}/{destination_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to move {source_path} to {destination_path}: {str(e)}")
            return False
    
    def get_file_metadata(self, gcs_file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a file in GCS.
        
        Args:
            gcs_file_path: Path to the file in GCS
            
        Returns:
            Dict[str, Any]: File metadata or None if file not found
        """
        try:
            blob = self.bucket.blob(gcs_file_path)
            blob.reload()
            
            metadata = {
                'name': blob.name,
                'size': blob.size,
                'content_type': blob.content_type,
                'created': blob.time_created,
                'updated': blob.updated,
                'md5_hash': blob.md5_hash,
                'etag': blob.etag
            }
            
            return metadata
            
        except gcs_exceptions.NotFound:
            self.logger.error(f"File not found: gs://{self.bucket_name}/{gcs_file_path}")
            return None
        except Exception as e:
            self.logger.error(f"Failed to get metadata for {gcs_file_path}: {str(e)}")
            return None
    
    def test_connection(self) -> bool:
        """
        Test the connection to Google Cloud Storage.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Try to access bucket metadata
            self.bucket.reload()
            self.logger.info(f"Successfully connected to GCS bucket: {self.bucket_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"GCS connection test failed: {str(e)}")
            return False
