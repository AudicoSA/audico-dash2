
"""
Orchestrator for Audico Product Manager.

This module coordinates the entire product processing workflow,
from document parsing to OpenCart synchronization.
"""

import logging
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

# Use absolute imports that work when running directly
try:
    from audico_product_manager.config import config
    from audico_product_manager.gcs_client import GCSClient
    from audico_product_manager.docai_parser import DocumentAIParser, ProductData
    from audico_product_manager.opencart_client import OpenCartAPIClient
    from audico_product_manager.product_logic import ProductSynchronizer, ProductSyncResult
except ImportError:
    try:
        from .config import config
        from .gcs_client import GCSClient
        from .docai_parser import DocumentAIParser, ProductData
        from .opencart_client import OpenCartAPIClient
        from .product_logic import ProductSynchronizer, ProductSyncResult
    except ImportError:
        from config import config
        from gcs_client import GCSClient
        from docai_parser import DocumentAIParser, ProductData
        from opencart_client import OpenCartAPIClient
        from product_logic import ProductSynchronizer, ProductSyncResult


class ProductProcessingOrchestrator:
    """Orchestrates the complete product processing workflow."""
    
    def __init__(self):
        """Initialize the orchestrator with all required clients."""
        self.logger = logging.getLogger(__name__)
        
        # Initialize clients
        self.gcs_client = GCSClient()
        self.docai_parser = DocumentAIParser()
        self.opencart_client = OpenCartAPIClient()
        self.product_synchronizer = ProductSynchronizer(self.opencart_client)
        
        self.logger.info("Product Processing Orchestrator initialized")
    
    def process_document_from_gcs(self, gcs_file_path: str) -> Dict[str, Any]:
        """
        Process a document from Google Cloud Storage.
        
        Args:
            gcs_file_path: Path to the document in GCS
            
        Returns:
            Dict[str, Any]: Processing results
        """
        self.logger.info(f"Starting processing of document: {gcs_file_path}")
        
        result = {
            'success': False,
            'gcs_file_path': gcs_file_path,
            'timestamp': datetime.now().isoformat(),
            'products_found': 0,
            'products_processed': 0,
            'sync_results': [],
            'error_message': None
        }
        
        try:
            # Download document from GCS
            local_file_path = self._download_document(gcs_file_path)
            if not local_file_path:
                result['error_message'] = "Failed to download document from GCS"
                return result
            
            # Parse document
            products_data = self._parse_document(local_file_path)
            result['products_found'] = len(products_data)
            
            if not products_data:
                result['error_message'] = "No products found in document"
                self._move_to_error_folder(gcs_file_path, "No products found")
                return result
            
            # Synchronize products with OpenCart
            sync_results = self._synchronize_products(products_data)
            result['sync_results'] = [
                {
                    'action': sr.action.value,
                    'product_id': sr.opencart_product_id,
                    'error': sr.error_message
                }
                for sr in sync_results
            ]
            
            # Calculate success metrics
            successful_syncs = sum(1 for sr in sync_results if sr.action.value in ['create', 'update'])
            result['products_processed'] = successful_syncs
            
            # Move document to appropriate folder
            if successful_syncs > 0:
                self._move_to_processed_folder(gcs_file_path)
                result['success'] = True
            else:
                self._move_to_error_folder(gcs_file_path, "No products successfully processed")
                result['error_message'] = "No products successfully processed"
            
            # Clean up local file
            self._cleanup_local_file(local_file_path)
            
        except Exception as e:
            self.logger.error(f"Error processing document {gcs_file_path}: {str(e)}")
            result['error_message'] = str(e)
            self._move_to_error_folder(gcs_file_path, str(e))
        
        return result
    
    def process_local_document(self, file_path: str) -> Dict[str, Any]:
        """
        Process a local document file.
        
        Args:
            file_path: Path to the local document file
            
        Returns:
            Dict[str, Any]: Processing results
        """
        self.logger.info(f"Starting processing of local document: {file_path}")
        
        result = {
            'success': False,
            'file_path': file_path,
            'timestamp': datetime.now().isoformat(),
            'products_found': 0,
            'products_processed': 0,
            'sync_results': [],
            'error_message': None
        }
        
        try:
            # Parse document
            products_data = self._parse_document(file_path)
            result['products_found'] = len(products_data)
            
            if not products_data:
                result['error_message'] = "No products found in document"
                return result
            
            # Synchronize products with OpenCart
            sync_results = self._synchronize_products(products_data)
            result['sync_results'] = [
                {
                    'action': sr.action.value,
                    'product_id': sr.opencart_product_id,
                    'error': sr.error_message
                }
                for sr in sync_results
            ]
            
            # Calculate success metrics
            successful_syncs = sum(1 for sr in sync_results if sr.action.value in ['create', 'update'])
            result['products_processed'] = successful_syncs
            result['success'] = successful_syncs > 0
            
            if not result['success']:
                result['error_message'] = "No products successfully processed"
            
        except Exception as e:
            self.logger.error(f"Error processing local document {file_path}: {str(e)}")
            result['error_message'] = str(e)
        
        return result
    
    def _download_document(self, gcs_file_path: str) -> Optional[str]:
        """
        Download document from GCS to local temporary file.
        
        Args:
            gcs_file_path: Path to the document in GCS
            
        Returns:
            str: Local file path or None if download failed
        """
        try:
            # Create temporary directory
            temp_dir = Path("temp_documents")
            temp_dir.mkdir(exist_ok=True)
            
            # Generate local file path
            file_name = Path(gcs_file_path).name
            local_file_path = temp_dir / file_name
            
            # Download file
            success = self.gcs_client.download_file(gcs_file_path, str(local_file_path))
            
            if success:
                self.logger.info(f"Downloaded document to: {local_file_path}")
                return str(local_file_path)
            else:
                self.logger.error(f"Failed to download document: {gcs_file_path}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error downloading document: {str(e)}")
            return None
    
    def _parse_document(self, file_path: str) -> List[ProductData]:
        """
        Parse document and extract product data.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            List[ProductData]: List of extracted product data
        """
        try:
            # Read document content
            with open(file_path, 'rb') as f:
                document_content = f.read()
            
            # Determine MIME type based on file extension
            file_extension = Path(file_path).suffix.lower()
            mime_type_map = {
                '.pdf': 'application/pdf',
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.tiff': 'image/tiff',
                '.tif': 'image/tiff'
            }
            
            mime_type = mime_type_map.get(file_extension, 'application/pdf')
            
            # Parse document
            products_data = self.docai_parser.parse_document(document_content, mime_type)
            
            self.logger.info(f"Extracted {len(products_data)} products from document")
            return products_data
            
        except Exception as e:
            self.logger.error(f"Error parsing document {file_path}: {str(e)}")
            return []
    
    def _synchronize_products(self, products_data: List[ProductData]) -> List[ProductSyncResult]:
        """
        Synchronize products with OpenCart.
        
        Args:
            products_data: List of product data to synchronize
            
        Returns:
            List[ProductSyncResult]: Synchronization results
        """
        try:
            sync_results = self.product_synchronizer.sync_products_batch(products_data)
            
            # Log summary
            summary = self.product_synchronizer.get_sync_summary(sync_results)
            self.logger.info(f"Sync summary: {summary}")
            
            return sync_results
            
        except Exception as e:
            self.logger.error(f"Error synchronizing products: {str(e)}")
            return []
    
    def _move_to_processed_folder(self, gcs_file_path: str) -> bool:
        """
        Move successfully processed file to processed folder.
        
        Args:
            gcs_file_path: Original file path in GCS
            
        Returns:
            bool: True if move successful, False otherwise
        """
        try:
            file_name = Path(gcs_file_path).name
            processed_path = f"{config.gcs_processed_folder}{file_name}"
            
            success = self.gcs_client.move_file(gcs_file_path, processed_path)
            
            if success:
                self.logger.info(f"Moved processed file to: {processed_path}")
            else:
                self.logger.error(f"Failed to move file to processed folder: {gcs_file_path}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error moving file to processed folder: {str(e)}")
            return False
    
    def _move_to_error_folder(self, gcs_file_path: str, error_reason: str) -> bool:
        """
        Move failed file to error folder.
        
        Args:
            gcs_file_path: Original file path in GCS
            error_reason: Reason for the error
            
        Returns:
            bool: True if move successful, False otherwise
        """
        try:
            file_name = Path(gcs_file_path).name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            error_file_name = f"{timestamp}_{file_name}"
            error_path = f"{config.gcs_error_folder}{error_file_name}"
            
            success = self.gcs_client.move_file(gcs_file_path, error_path)
            
            if success:
                self.logger.info(f"Moved error file to: {error_path} (Reason: {error_reason})")
            else:
                self.logger.error(f"Failed to move file to error folder: {gcs_file_path}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error moving file to error folder: {str(e)}")
            return False
    
    def _cleanup_local_file(self, file_path: str) -> bool:
        """
        Clean up local temporary file.
        
        Args:
            file_path: Path to the local file to clean up
            
        Returns:
            bool: True if cleanup successful, False otherwise
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                self.logger.info(f"Cleaned up local file: {file_path}")
                return True
            return True
            
        except Exception as e:
            self.logger.error(f"Error cleaning up local file {file_path}: {str(e)}")
            return False
    
    def test_all_connections(self) -> Dict[str, bool]:
        """
        Test connections to all external services.
        
        Returns:
            Dict[str, bool]: Connection test results
        """
        results = {
            'gcs': False,
            'document_ai': False,
            'opencart': False
        }
        
        try:
            results['gcs'] = self.gcs_client.test_connection()
        except Exception as e:
            self.logger.error(f"GCS connection test failed: {str(e)}")
        
        try:
            results['document_ai'] = self.docai_parser.test_connection()
        except Exception as e:
            self.logger.error(f"Document AI connection test failed: {str(e)}")
        
        try:
            results['opencart'] = self.opencart_client.test_connection()
        except Exception as e:
            self.logger.error(f"OpenCart connection test failed: {str(e)}")
        
        return results
