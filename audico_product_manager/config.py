
"""
Configuration management for Audico Product Manager.

Handles environment variables, Google Cloud credentials, and application settings.
"""

import os
import logging
from pathlib import Path
from typing import Optional

class Config:
    """Configuration class for managing application settings."""
    
    def __init__(self):
        """Initialize configuration with environment variables and defaults."""
        
        # Google Cloud Configuration
        self.google_cloud_project_id = os.getenv('GOOGLE_CLOUD_PROJECT_ID', 'audico-pricelists')
        self.google_cloud_location = os.getenv('GOOGLE_CLOUD_LOCATION', 'us')
        self.google_cloud_processor_id = os.getenv('GOOGLE_CLOUD_PROCESSOR_ID')
        self.google_application_credentials = os.getenv(
            'GOOGLE_APPLICATION_CREDENTIALS', 
            '/home/ubuntu/Uploads/audico-pricelists-d6dcac3f7c31.json'
        )
        
        # Google Cloud Storage Configuration
        self.gcs_bucket_name = os.getenv('GCS_BUCKET_NAME', 'audicopricelistingest')
        self.gcs_processed_folder = os.getenv('GCS_PROCESSED_FOLDER', 'processed/')
        self.gcs_error_folder = os.getenv('GCS_ERROR_FOLDER', 'errors/')
        
        # OpenCart API Configuration
        self.opencart_base_url = os.getenv(
            'OPENCART_BASE_URL', 
            'https://www.audicoonline.co.za/index.php?route=ocrestapi/product'
        )
        self.opencart_auth_token = os.getenv(
            'OPENCART_AUTH_TOKEN',
            'b2NyZXN0YXBpX29hdXRoX2NsaWVudDpvY3Jlc3RhcGlfb2F1dGhfc2VjcmV0'
        )
        
        # Product Management Configuration
        self.target_category = os.getenv('TARGET_CATEGORY', 'Load')
        self.default_manufacturer = os.getenv('DEFAULT_MANUFACTURER', 'Audico')
        self.default_status = os.getenv('DEFAULT_STATUS', '1')  # Enabled
        self.default_stock_status = os.getenv('DEFAULT_STOCK_STATUS', '7')  # In Stock
        
        # Processing Configuration
        self.batch_size = int(os.getenv('BATCH_SIZE', '50'))
        self.max_retries = int(os.getenv('MAX_RETRIES', '3'))
        self.retry_delay = int(os.getenv('RETRY_DELAY', '5'))
        
        # Logging Configuration
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.log_file = os.getenv('LOG_FILE', 'audico_product_manager.log')
        
        # Validation
        self._validate_config()
    
    def _validate_config(self):
        """Validate required configuration parameters."""
        required_configs = [
            ('GOOGLE_APPLICATION_CREDENTIALS', self.google_application_credentials),
            ('OPENCART_AUTH_TOKEN', self.opencart_auth_token),
            ('GCS_BUCKET_NAME', self.gcs_bucket_name),
        ]
        
        missing_configs = []
        for name, value in required_configs:
            if not value:
                missing_configs.append(name)
        
        if missing_configs:
            raise ValueError(f"Missing required configuration: {', '.join(missing_configs)}")
        
        # Validate Google Cloud credentials file exists
        if not Path(self.google_application_credentials).exists():
            raise FileNotFoundError(
                f"Google Cloud credentials file not found: {self.google_application_credentials}"
            )
    
    def get_document_ai_endpoint(self) -> str:
        """Get the Document AI API endpoint for the configured location."""
        return f"{self.google_cloud_location}-documentai.googleapis.com"
    
    def get_processor_path(self) -> str:
        """Get the full processor path for Document AI."""
        return f"projects/{self.google_cloud_project_id}/locations/{self.google_cloud_location}/processors/{self.google_cloud_processor_id}"

# Global configuration instance
config = Config()
