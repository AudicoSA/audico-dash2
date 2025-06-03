
"""
Google Cloud Storage client for handling file operations.

Provides functionality to list, download, and manage files in the
audicopricelistingest bucket.
"""

import logging
from typing import List, Optional, Tuple
from pathlib import Path
import tempfile
import os

from google.cloud import storage
from google.cloud.exceptions import NotFound, GoogleCloudError

from .config import config

logger = logging.getLogger(__name__)

class GCSClient:
    """Google Cloud Storage client for pricelist file management."""
    
    def __init__(self):
        """Initialize GCS client with service account credentials."""
        try:
            # Set credentials environment variable
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.google_application_credentials
            
            self.client = storage.Client(project=config.google_cloud_project_id)
            self.bucket = self.client.bucket(config.gcs_bucket_name)
            
            logger.info(f"Initialized GCS client for bucket: {config.gcs_bucket_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize GCS client: {e}")
            raise
    
    def list_unprocessed_files(self, file_extensions: List[str] = None) -> List[str]:
        """
        List unprocessed files in the bucket.
        
        Args:
            file_extensions: List of file extensions to filter (e.g., ['.pdf', '.xlsx'])
            
        Returns:
            List of file names that haven't been processed
        """
        if file_extensions is None:
            file_extensions = ['.pdf', '.xlsx', '.xls']
        
        try:
            # Get all files in the bucket (excluding processed and error folders)
            blobs = self.bucket.list_blobs()
            unprocessed_files = []
            
            for blob in blobs:
                # Skip files in processed or error folders
                if (blob.name.startswith(config.gcs_processed_folder) or 
                    blob.name.startswith(config.gcs_error_folder)):
                    continue
                
                # Check file extension
                file_path = Path(blob.name)
                if file_path.suffix.lower() in file_extensions:
                    unprocessed_files.append(blob.name)
            
            logger.info(f"Found {len(unprocessed_files)} unprocessed files")
            return unprocessed_files
            
        except Exception as e:
            logger.error(f"Failed to list unprocessed files: {e}")
            raise
    
    def download_file(self, file_name: str) -> Tuple[str, str]:
        """
        Download a file from GCS to a temporary location.
        
        Args:
            file_name: Name of the file in the bucket
            
        Returns:
            Tuple of (local_file_path, gcs_uri)
        """
        try:
            blob = self.bucket.blob(file_name)
            
            if not blob.exists():
                raise NotFound(f"File not found in bucket: {file_name}")
            
            # Create temporary file
            file_extension = Path(file_name).suffix
            temp_file = tempfile.NamedTemporaryFile(
                delete=False, 
                suffix=file_extension,
                prefix="audico_pricelist_"
            )
            
            # Download file
            blob.download_to_filename(temp_file.name)
            gcs_uri = f"gs://{config.gcs_bucket_name}/{file_name}"
            
            logger.info(f"Downloaded file {file_name} to {temp_file.name}")
            return temp_file.name, gcs_uri
            
        except Exception as e:
            logger.error(f"Failed to download file {file_name}: {e}")
            raise
    
    def move_file_to_processed(self, file_name: str) -> None:
        """
        Move a file to the processed folder.
        
        Args:
            file_name: Name of the file to move
        """
        try:
            source_blob = self.bucket.blob(file_name)
            destination_name = f"{config.gcs_processed_folder}{file_name}"
            
            # Copy to processed folder
            destination_blob = self.bucket.copy_blob(source_blob, self.bucket, destination_name)
            
            # Delete original file
            source_blob.delete()
            
            logger.info(f"Moved file {file_name} to processed folder")
            
        except Exception as e:
            logger.error(f"Failed to move file {file_name} to processed folder: {e}")
            raise
    
    def move_file_to_error(self, file_name: str, error_message: str = None) -> None:
        """
        Move a file to the error folder with optional error metadata.
        
        Args:
            file_name: Name of the file to move
            error_message: Optional error message to store as metadata
        """
        try:
            source_blob = self.bucket.blob(file_name)
            destination_name = f"{config.gcs_error_folder}{file_name}"
            
            # Copy to error folder
            destination_blob = self.bucket.copy_blob(source_blob, self.bucket, destination_name)
            
            # Add error metadata if provided
            if error_message:
                destination_blob.metadata = {'error_message': error_message}
                destination_blob.patch()
            
            # Delete original file
            source_blob.delete()
            
            logger.warning(f"Moved file {file_name} to error folder: {error_message}")
            
        except Exception as e:
            logger.error(f"Failed to move file {file_name} to error folder: {e}")
            raise
    
    def cleanup_temp_file(self, file_path: str) -> None:
        """
        Clean up temporary downloaded file.
        
        Args:
            file_path: Path to the temporary file
        """
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                logger.debug(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temporary file {file_path}: {e}")
    
    def get_file_info(self, file_name: str) -> dict:
        """
        Get metadata information about a file.
        
        Args:
            file_name: Name of the file
            
        Returns:
            Dictionary with file metadata
        """
        try:
            blob = self.bucket.blob(file_name)
            blob.reload()
            
            return {
                'name': blob.name,
                'size': blob.size,
                'content_type': blob.content_type,
                'created': blob.time_created,
                'updated': blob.updated,
                'md5_hash': blob.md5_hash,
                'etag': blob.etag
            }
            
        except Exception as e:
            logger.error(f"Failed to get file info for {file_name}: {e}")
            raise
