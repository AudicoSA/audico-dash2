

"""
Enhanced Orchestrator for Audico Product Manager.

This module coordinates the entire product processing workflow,
from document parsing (including Excel) to OpenCart synchronization.
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
    from audico_product_manager.excel_parser import ExcelParser
    from audico_product_manager.opencart_client import OpenCartAPIClient
    from audico_product_manager.product_logic import ProductSynchronizer, ProductSyncResult
    from audico_product_manager.store_name_generator import StoreNameGenerator
    from audico_product_manager.enhanced_product_comparison import EnhancedProductComparator
except ImportError:
    try:
        from .config import config
        from .gcs_client import GCSClient
        from .docai_parser import DocumentAIParser, ProductData
        from .excel_parser import ExcelParser
        from .opencart_client import OpenCartAPIClient
        from .product_logic import ProductSynchronizer, ProductSyncResult
        from .store_name_generator import StoreNameGenerator
        from .enhanced_product_comparison import EnhancedProductComparator
    except ImportError:
        from config import config
        from gcs_client import GCSClient
        from docai_parser import DocumentAIParser, ProductData
        from excel_parser import ExcelParser
        from opencart_client import OpenCartAPIClient
        from product_logic import ProductSynchronizer, ProductSyncResult
        from store_name_generator import StoreNameGenerator
        from enhanced_product_comparison import EnhancedProductComparator


class ProductProcessingOrchestrator:
    """Enhanced orchestrator with Excel support for the complete product processing workflow."""
    
    def __init__(self):
        """Initialize the orchestrator with all required clients."""
        self.logger = logging.getLogger(__name__)
        
        # Initialize clients with graceful error handling
        try:
            self.gcs_client = GCSClient()
        except Exception as e:
            self.logger.warning(f"GCS client initialization failed: {str(e)[:100]}... - GCS features will be disabled")
            self.gcs_client = None
            
        self.docai_parser = DocumentAIParser()
        self.excel_parser = ExcelParser()
        self.opencart_client = OpenCartAPIClient()
        self.product_synchronizer = ProductSynchronizer(self.opencart_client)
        
        # Initialize new enhanced components
        self.store_name_generator = StoreNameGenerator()
        self.enhanced_comparator = EnhancedProductComparator(self.opencart_client, self.store_name_generator)
        
        self.logger.info("Enhanced Product Processing Orchestrator initialized with GPT-4 store naming and improved matching")
    
    def process_document_from_gcs(self, gcs_file_path: str) -> Dict[str, Any]:
        """
        Process a document from Google Cloud Storage with Excel support.
        
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
            'file_type': self._detect_file_type(gcs_file_path),
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
            
            # Parse document based on file type
            products_data = self._parse_document_enhanced(local_file_path)
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
        Process a local document file with Excel support.
        
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
            'file_type': self._detect_file_type(file_path),
            'products_found': 0,
            'products_processed': 0,
            'sync_results': [],
            'error_message': None
        }
        
        try:
            # Parse document based on file type
            products_data = self._parse_document_enhanced(file_path)
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
    
    def process_local_document_enhanced(self, file_path: str) -> Dict[str, Any]:
        """
        Process a local document file with enhanced GPT-4 store naming and improved matching.
        
        Args:
            file_path: Path to the local document file
            
        Returns:
            Dict[str, Any]: Processing results with enhanced matching details
        """
        self.logger.info(f"Starting enhanced processing of local document: {file_path}")
        
        result = {
            'success': False,
            'file_path': file_path,
            'timestamp': datetime.now().isoformat(),
            'file_type': self._detect_file_type(file_path),
            'products_found': 0,
            'products_processed': 0,
            'enhanced_matches': [],
            'store_names_generated': [],
            'error_message': None,
            'processing_summary': {}
        }
        
        try:
            # Step 1: Parse document based on file type (existing functionality)
            self.logger.info("Step 1: Extracting raw product data...")
            products_data = self._parse_document_enhanced(file_path)
            result['products_found'] = len(products_data)
            
            if not products_data:
                result['error_message'] = "No products found in document"
                return result
            
            # Step 2: Generate store-friendly names using GPT-4
            self.logger.info("Step 2: Generating store-friendly names with GPT-4...")
            products_data = self.store_name_generator.batch_generate_store_names(products_data)
            
            # Collect generated store names for result
            result['store_names_generated'] = [
                {
                    'original_name': product.name,
                    'model': product.model,
                    'store_name': getattr(product, 'online_store_name', None)
                }
                for product in products_data
            ]
            
            # Step 3: Enhanced product comparison using both raw and store names
            self.logger.info("Step 3: Performing enhanced product comparison...")
            enhanced_matches = self.enhanced_comparator.batch_compare_products(products_data)
            
            # Convert enhanced matches to serializable format
            result['enhanced_matches'] = [
                {
                    'parsed_product_name': match.parsed_product.get('name', ''),
                    'parsed_product_model': match.parsed_product.get('model', ''),
                    'store_name_used': match.store_name_used,
                    'existing_product_name': match.existing_product.get('name', '') if match.existing_product else None,
                    'existing_product_id': match.existing_product.get('product_id', '') if match.existing_product else None,
                    'match_type': match.match_type.value,
                    'confidence_score': match.confidence_score,
                    'confidence_level': match.confidence_level.value,
                    'action': match.action,
                    'issues': match.issues,
                    'price_change': match.price_change
                }
                for match in enhanced_matches
            ]
            
            # Step 4: Synchronize products (if needed)
            successful_matches = [match for match in enhanced_matches if match.action in ['create', 'update']]
            if successful_matches:
                self.logger.info(f"Step 4: Synchronizing {len(successful_matches)} products with OpenCart...")
                # Convert enhanced matches back to ProductData for synchronization
                products_to_sync = []
                for match in successful_matches:
                    if hasattr(match.parsed_product, '__dict__'):
                        # If it's already a ProductData object
                        products_to_sync.append(match.parsed_product)
                    else:
                        # Convert dict back to ProductData
                        product_dict = match.parsed_product
                        product_data = ProductData(
                            name=product_dict.get('name', ''),
                            model=product_dict.get('model', ''),
                            price=product_dict.get('price', ''),
                            description=product_dict.get('description', ''),
                            category=product_dict.get('category', ''),
                            manufacturer=product_dict.get('manufacturer', ''),
                            specifications=product_dict.get('specifications', {}),
                            confidence=product_dict.get('confidence', 0.0),
                            online_store_name=match.store_name_used
                        )
                        products_to_sync.append(product_data)
                
                sync_results = self._synchronize_products(products_to_sync)
                result['sync_results'] = [
                    {
                        'action': sr.action.value,
                        'product_id': sr.opencart_product_id,
                        'error': sr.error_message
                    }
                    for sr in sync_results
                ]
                
                successful_syncs = sum(1 for sr in sync_results if sr.action.value in ['create', 'update'])
                result['products_processed'] = successful_syncs
                result['success'] = successful_syncs > 0
            else:
                result['sync_results'] = []
                result['products_processed'] = 0
                result['success'] = True  # Processing was successful even if no syncing needed
            
            # Generate processing summary
            result['processing_summary'] = self._generate_processing_summary(enhanced_matches)
            
            if not result['success'] and result['products_processed'] == 0:
                result['error_message'] = "No products successfully processed"
            
        except Exception as e:
            self.logger.error(f"Error in enhanced processing of document {file_path}: {str(e)}")
            result['error_message'] = str(e)
        
        return result
    
    def _generate_processing_summary(self, enhanced_matches) -> Dict[str, Any]:
        """
        Generate a summary of the enhanced processing results.
        
        Args:
            enhanced_matches: List of enhanced match results
            
        Returns:
            Dict[str, Any]: Processing summary
        """
        if not enhanced_matches:
            return {}
        
        total = len(enhanced_matches)
        
        # Count by match type
        match_type_counts = {}
        confidence_counts = {}
        action_counts = {}
        
        for match in enhanced_matches:
            match_type_counts[match.match_type.value] = match_type_counts.get(match.match_type.value, 0) + 1
            confidence_counts[match.confidence_level.value] = confidence_counts.get(match.confidence_level.value, 0) + 1
            action_counts[match.action] = action_counts.get(match.action, 0) + 1
        
        # Calculate success metrics
        high_confidence = confidence_counts.get('high', 0)
        medium_confidence = confidence_counts.get('medium', 0)
        success_rate = ((high_confidence + medium_confidence) / total) * 100 if total > 0 else 0
        
        return {
            'total_products': total,
            'match_types': match_type_counts,
            'confidence_levels': confidence_counts,
            'actions': action_counts,
            'success_rate_percent': round(success_rate, 1),
            'high_confidence_matches': high_confidence,
            'medium_confidence_matches': medium_confidence,
            'store_names_generated': sum(1 for match in enhanced_matches if match.store_name_used)
        }
    
    def _detect_file_type(self, file_path: str) -> str:
        """
        Detect file type based on extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            str: File type ('pdf', 'excel', 'image', 'text', 'unknown')
        """
        file_extension = Path(file_path).suffix.lower()
        
        if file_extension == '.pdf':
            return 'pdf'
        elif file_extension in ['.xlsx', '.xls', '.xlsm']:
            return 'excel'
        elif file_extension in ['.png', '.jpg', '.jpeg', '.tiff', '.tif']:
            return 'image'
        elif file_extension in ['.txt', '.csv']:
            return 'text'
        else:
            return 'unknown'
    
    def _parse_document_enhanced(self, file_path: str) -> List[ProductData]:
        """
        Parse document using the appropriate parser based on file type.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            List[ProductData]: List of extracted product data
        """
        file_type = self._detect_file_type(file_path)
        
        try:
            if file_type == 'excel':
                self.logger.info(f"Using Excel parser for file: {file_path}")
                products_data = self.excel_parser.parse_excel_file(file_path)
                self.logger.info(f"Excel parser extracted {len(products_data)} products")
                return products_data
            
            elif file_type in ['pdf', 'image', 'text']:
                self.logger.info(f"Using Document AI parser for {file_type} file: {file_path}")
                
                # Read document content
                with open(file_path, 'rb') as f:
                    document_content = f.read()
                
                # Determine MIME type
                mime_type_map = {
                    'pdf': 'application/pdf',
                    'image': self._get_image_mime_type(file_path),
                    'text': 'text/plain'
                }
                
                mime_type = mime_type_map.get(file_type, 'application/pdf')
                
                # Parse document
                products_data = self.docai_parser.parse_document(document_content, mime_type)
                self.logger.info(f"Document AI parser extracted {len(products_data)} products")
                return products_data
            
            else:
                self.logger.warning(f"Unsupported file type: {file_type} for file: {file_path}")
                return []
            
        except Exception as e:
            self.logger.error(f"Error parsing document {file_path}: {str(e)}")
            return []
    
    def _get_image_mime_type(self, file_path: str) -> str:
        """
        Get MIME type for image files.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            str: MIME type
        """
        file_extension = Path(file_path).suffix.lower()
        mime_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.tiff': 'image/tiff',
            '.tif': 'image/tiff'
        }
        return mime_types.get(file_extension, 'image/jpeg')
    
    def _download_document(self, gcs_file_path: str) -> Optional[str]:
        """
        Download document from GCS to local temporary file.
        
        Args:
            gcs_file_path: Path to the document in GCS
            
        Returns:
            str: Local file path or None if download failed
        """
        if self.gcs_client is None:
            self.logger.error("GCS client not available - cannot download document")
            return None
            
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
        if self.gcs_client is None:
            self.logger.warning("GCS client not available - skipping file move to processed folder")
            return True  # Return True to not block processing
            
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
        if self.gcs_client is None:
            self.logger.warning("GCS client not available - skipping file move to error folder")
            return True  # Return True to not block processing
            
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
        Test connections to all external services including Excel parser.
        
        Returns:
            Dict[str, bool]: Connection test results
        """
        results = {
            'gcs': False,
            'document_ai': False,
            'excel_parser': False,
            'opencart': False
        }
        
        try:
            if self.gcs_client is not None:
                results['gcs'] = self.gcs_client.test_connection()
            else:
                self.logger.warning("GCS client not available - skipping connection test")
                results['gcs'] = False
        except Exception as e:
            self.logger.error(f"GCS connection test failed: {str(e)}")
        
        try:
            results['document_ai'] = self.docai_parser.test_connection()
        except Exception as e:
            self.logger.error(f"Document AI connection test failed: {str(e)}")
        
        try:
            # Test Excel parser by checking if pandas and openpyxl are available
            import pandas as pd
            import openpyxl
            results['excel_parser'] = True
            self.logger.info("Excel parser dependencies available")
        except ImportError as e:
            self.logger.error(f"Excel parser dependencies missing: {str(e)}")
            results['excel_parser'] = False
        
        try:
            results['opencart'] = self.opencart_client.test_connection()
        except Exception as e:
            self.logger.error(f"OpenCart connection test failed: {str(e)}")
        
        return results
    
    def get_supported_file_types(self) -> Dict[str, List[str]]:
        """
        Get supported file types for each parser.
        
        Returns:
            Dict[str, List[str]]: Supported file types by parser
        """
        return {
            'document_ai': ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.tif', '.txt'],
            'excel_parser': self.excel_parser.get_supported_formats()
        }
