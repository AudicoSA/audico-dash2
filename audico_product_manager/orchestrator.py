
"""
Main orchestration script for the Audico Product Manager.

Coordinates the entire pipeline: file processing, product parsing,
comparison, and synchronization with OpenCart.
"""

import logging
import argparse
import sys
import json
from pathlib import Path
from typing import List, Dict, Any
import tempfile
import os
from datetime import datetime

from .config import config
from .gcs_client import GCSClient
from .docai_parser import DocumentAIParser, ProductData
from .opencart_client import OpenCartAPIClient
from .product_logic import ProductSynchronizer, ProductAction

# Set up logging
def setup_logging():
    """Configure logging for the application."""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(config.log_file)
        ]
    )
    
    # Set specific logger levels
    logging.getLogger('google.cloud').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

class ProductManagerOrchestrator:
    """Main orchestrator for the product management pipeline."""
    
    def __init__(self):
        """Initialize the orchestrator with all required clients."""
        logger.info("Initializing Audico Product Manager")
        
        try:
            self.gcs_client = GCSClient()
            self.docai_parser = DocumentAIParser()
            self.opencart_client = OpenCartAPIClient()
            self.synchronizer = ProductSynchronizer(self.opencart_client)
            
            logger.info("All clients initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize clients: {e}")
            raise
    
    def run_full_pipeline(self, dry_run: bool = False, file_filter: str = None) -> Dict[str, Any]:
        """
        Run the complete product management pipeline.
        
        Args:
            dry_run: If True, analyze but don't execute changes
            file_filter: Optional filter for specific files
            
        Returns:
            Pipeline execution results
        """
        logger.info(f"Starting full pipeline (dry_run={dry_run})")
        
        results = {
            'start_time': datetime.now().isoformat(),
            'files_processed': 0,
            'products_parsed': 0,
            'actions_analyzed': 0,
            'actions_executed': {},
            'errors': [],
            'files': []
        }
        
        try:
            # Step 1: Get unprocessed files
            logger.info("Step 1: Retrieving unprocessed files from GCS")
            files = self.gcs_client.list_unprocessed_files()
            
            if file_filter:
                files = [f for f in files if file_filter.lower() in f.lower()]
                logger.info(f"Applied file filter '{file_filter}': {len(files)} files")
            
            if not files:
                logger.info("No unprocessed files found")
                return results
            
            logger.info(f"Found {len(files)} files to process")
            
            # Step 2: Process each file
            all_products = []
            for file_name in files:
                try:
                    file_result = self._process_single_file(file_name, dry_run)
                    results['files'].append(file_result)
                    results['files_processed'] += 1
                    
                    if file_result['products']:
                        all_products.extend(file_result['products'])
                    
                except Exception as e:
                    error_msg = f"Error processing file {file_name}: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    
                    # Move file to error folder
                    try:
                        self.gcs_client.move_file_to_error(file_name, str(e))
                    except Exception as move_error:
                        logger.error(f"Failed to move error file: {move_error}")
            
            results['products_parsed'] = len(all_products)
            
            # Step 3: Analyze all products together
            if all_products:
                logger.info(f"Step 3: Analyzing {len(all_products)} products")
                actions = self.synchronizer.analyze_products(all_products)
                results['actions_analyzed'] = len(actions)
                
                # Step 4: Execute actions (if not dry run)
                if not dry_run:
                    logger.info("Step 4: Executing product actions")
                    execution_stats = self.synchronizer.execute_actions(actions)
                    results['actions_executed'] = execution_stats
                else:
                    logger.info("Step 4: Skipped execution (dry run mode)")
                    # Generate summary for dry run
                    summary = self.synchronizer.get_synchronization_summary(actions)
                    results['dry_run_summary'] = summary
            
            results['end_time'] = datetime.now().isoformat()
            results['success'] = True
            
            logger.info(f"Pipeline completed successfully: {results}")
            return results
            
        except Exception as e:
            error_msg = f"Pipeline failed: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            results['success'] = False
            results['end_time'] = datetime.now().isoformat()
            return results
    
    def _process_single_file(self, file_name: str, dry_run: bool) -> Dict[str, Any]:
        """
        Process a single file through the parsing pipeline.
        
        Args:
            file_name: Name of the file to process
            dry_run: If True, don't move files after processing
            
        Returns:
            File processing results
        """
        logger.info(f"Processing file: {file_name}")
        
        file_result = {
            'file_name': file_name,
            'products': [],
            'confidence_score': 0.0,
            'processing_time': None,
            'error': None
        }
        
        temp_file_path = None
        start_time = datetime.now()
        
        try:
            # Download file
            temp_file_path, gcs_uri = self.gcs_client.download_file(file_name)
            
            # Parse document
            logger.info(f"Parsing document: {gcs_uri}")
            products = self.docai_parser.process_document(gcs_uri)
            
            file_result['products'] = products
            file_result['processing_time'] = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"Extracted {len(products)} products from {file_name}")
            
            # Move file to processed folder (if not dry run)
            if not dry_run:
                self.gcs_client.move_file_to_processed(file_name)
            
            return file_result
            
        except Exception as e:
            file_result['error'] = str(e)
            logger.error(f"Error processing file {file_name}: {e}")
            raise
            
        finally:
            # Clean up temporary file
            if temp_file_path:
                self.gcs_client.cleanup_temp_file(temp_file_path)
    
    def test_connections(self) -> Dict[str, bool]:
        """
        Test connections to all external services.
        
        Returns:
            Dictionary with connection test results
        """
        logger.info("Testing connections to external services")
        
        results = {}
        
        # Test Google Cloud Storage
        try:
            files = self.gcs_client.list_unprocessed_files()
            results['gcs'] = True
            logger.info(f"GCS connection successful ({len(files)} files found)")
        except Exception as e:
            results['gcs'] = False
            logger.error(f"GCS connection failed: {e}")
        
        # Test Document AI
        try:
            # We can't easily test Document AI without processing a document
            # So we'll just check if the client initializes
            results['document_ai'] = True
            logger.info("Document AI client initialized successfully")
        except Exception as e:
            results['document_ai'] = False
            logger.error(f"Document AI initialization failed: {e}")
        
        # Test OpenCart API
        try:
            results['opencart'] = self.opencart_client.test_connection()
            if results['opencart']:
                logger.info("OpenCart API connection successful")
            else:
                logger.error("OpenCart API connection failed")
        except Exception as e:
            results['opencart'] = False
            logger.error(f"OpenCart API connection error: {e}")
        
        return results
    
    def process_specific_file(self, file_name: str, dry_run: bool = False) -> Dict[str, Any]:
        """
        Process a specific file by name.
        
        Args:
            file_name: Name of the file to process
            dry_run: If True, analyze but don't execute changes
            
        Returns:
            Processing results
        """
        logger.info(f"Processing specific file: {file_name}")
        
        try:
            # Process the file
            file_result = self._process_single_file(file_name, dry_run)
            
            if file_result['products']:
                # Analyze products
                actions = self.synchronizer.analyze_products(file_result['products'])
                
                if not dry_run:
                    # Execute actions
                    execution_stats = self.synchronizer.execute_actions(actions)
                    file_result['actions_executed'] = execution_stats
                else:
                    # Generate summary for dry run
                    summary = self.synchronizer.get_synchronization_summary(actions)
                    file_result['dry_run_summary'] = summary
            
            return file_result
            
        except Exception as e:
            logger.error(f"Error processing specific file {file_name}: {e}")
            return {
                'file_name': file_name,
                'error': str(e),
                'success': False
            }

def main():
    """Main entry point for the command-line interface."""
    parser = argparse.ArgumentParser(
        description="Audico Product Manager - Automated OpenCart Product Management"
    )
    
    parser.add_argument(
        '--dry-run', 
        action='store_true',
        help='Analyze products but do not execute changes'
    )
    
    parser.add_argument(
        '--file-filter',
        type=str,
        help='Filter files by name (case-insensitive substring match)'
    )
    
    parser.add_argument(
        '--specific-file',
        type=str,
        help='Process a specific file by name'
    )
    
    parser.add_argument(
        '--test-connections',
        action='store_true',
        help='Test connections to external services'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Set logging level'
    )
    
    parser.add_argument(
        '--output-file',
        type=str,
        help='Save results to JSON file'
    )
    
    args = parser.parse_args()
    
    # Override log level if specified
    if args.log_level:
        config.log_level = args.log_level
    
    # Set up logging
    setup_logging()
    
    try:
        orchestrator = ProductManagerOrchestrator()
        
        if args.test_connections:
            # Test connections
            results = orchestrator.test_connections()
            print("\nConnection Test Results:")
            for service, status in results.items():
                status_text = "✓ PASS" if status else "✗ FAIL"
                print(f"  {service}: {status_text}")
            
            # Exit with error code if any connection failed
            sys.exit(0 if all(results.values()) else 1)
        
        elif args.specific_file:
            # Process specific file
            results = orchestrator.process_specific_file(args.specific_file, args.dry_run)
        
        else:
            # Run full pipeline
            results = orchestrator.run_full_pipeline(args.dry_run, args.file_filter)
        
        # Output results
        if args.output_file:
            with open(args.output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            logger.info(f"Results saved to {args.output_file}")
        
        # Print summary
        print("\n" + "="*50)
        print("AUDICO PRODUCT MANAGER - EXECUTION SUMMARY")
        print("="*50)
        
        if 'success' in results:
            status = "SUCCESS" if results['success'] else "FAILED"
            print(f"Status: {status}")
        
        if 'files_processed' in results:
            print(f"Files processed: {results['files_processed']}")
        
        if 'products_parsed' in results:
            print(f"Products parsed: {results['products_parsed']}")
        
        if 'actions_executed' in results:
            stats = results['actions_executed']
            print(f"Products created: {stats.get('created', 0)}")
            print(f"Products updated: {stats.get('updated', 0)}")
            print(f"Products skipped: {stats.get('skipped', 0)}")
            print(f"Errors: {stats.get('errors', 0)}")
        
        if 'dry_run_summary' in results:
            summary = results['dry_run_summary']
            print(f"Would create: {summary['actions']['create']} products")
            print(f"Would update: {summary['actions']['update']} products")
            print(f"Would skip: {summary['actions']['skip']} products")
            print(f"Errors: {summary['actions']['error']} products")
        
        if results.get('errors'):
            print(f"\nErrors encountered: {len(results['errors'])}")
            for error in results['errors']:
                print(f"  - {error}")
        
        print("="*50)
        
        # Exit with appropriate code
        if 'success' in results:
            sys.exit(0 if results['success'] else 1)
        else:
            sys.exit(0)
        
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(1)
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
