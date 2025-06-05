
"""
Configuration management for Audico Product Manager.

Handles environment variables, Google Cloud credentials, OpenAI API, and application settings.
"""

import os
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import openai

# Load environment variables from .env file in the project root
# Get the path to the project root (parent directory of audico_product_manager)
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path)

class Config:
    """Configuration class for managing application settings."""
    
    def __init__(self):
        """Initialize configuration with environment variables and defaults."""
        
        # OpenAI Configuration
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        # Google Cloud Configuration
        self.google_cloud_project_id = os.getenv('GOOGLE_CLOUD_PROJECT_ID', 'audico-pricelists')
        self.google_cloud_location = os.getenv('GOOGLE_CLOUD_LOCATION', 'us')
        # For demo purposes, we'll use a mock processor ID since we don't have create permissions
        self.google_cloud_processor_id = os.getenv('GOOGLE_CLOUD_PROCESSOR_ID', 'mock-processor-for-demo')
        
        # Google Cloud credentials path - prioritize GOOGLE_CLOUD_CREDENTIALS_PATH
        self.google_application_credentials = (
            os.getenv('GOOGLE_CLOUD_CREDENTIALS_PATH') or 
            os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        )
        
        # Set the environment variable for Google Cloud authentication
        if self.google_application_credentials:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.google_application_credentials
        
        # Google Cloud Storage Configuration
        self.gcs_bucket_name = os.getenv('GCS_BUCKET_NAME', 'audicopricelistingest')
        self.gcs_processed_folder = os.getenv('GCS_PROCESSED_FOLDER', 'processed/')
        self.gcs_error_folder = os.getenv('GCS_ERROR_FOLDER', 'errors/')
        
        # OpenCart API Configuration
        self.opencart_base_url = os.getenv(
            'OPENCART_BASE_URL', 
            'https://www.audicoonline.co.za/index.php?route=ocrestapi'
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
        
        # Initialize OpenAI client
        self.openai_client = None
        self._initialize_openai_client()
        
        # Validation
        self._validate_config()
    
    def _initialize_openai_client(self):
        """Initialize the OpenAI client."""
        if self.openai_api_key:
            try:
                self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
                logging.info("Successfully initialized OpenAI client")
            except Exception as e:
                logging.error(f"Failed to initialize OpenAI client: {str(e)}")
                self.openai_client = None
        else:
            logging.warning("No OpenAI API key provided - OpenAI features will be disabled")
            self.openai_client = None
    
    def _validate_config(self):
        """Validate required configuration parameters."""
        required_configs = [
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
        if self.google_application_credentials:
            if not Path(self.google_application_credentials).exists():
                logging.warning(
                    f"Google Cloud credentials file not found: {self.google_application_credentials}. "
                    f"Please ensure the file exists or set GOOGLE_CLOUD_CREDENTIALS_PATH or GOOGLE_APPLICATION_CREDENTIALS environment variable."
                )
        else:
            logging.warning(
                "No Google Cloud credentials path specified. "
                "Please set GOOGLE_CLOUD_CREDENTIALS_PATH or GOOGLE_APPLICATION_CREDENTIALS environment variable."
            )
        
        # Warn if OpenAI API key is missing
        if not self.openai_api_key:
            logging.warning(
                "No OpenAI API key provided. Set OPENAI_API_KEY environment variable to enable intelligent parsing."
            )
    
    def get_document_ai_endpoint(self) -> str:
        """Get the Document AI API endpoint for the configured location."""
        return f"{self.google_cloud_location}-documentai.googleapis.com"
    
    def get_processor_path(self) -> str:
        """Get the full processor path for Document AI."""
        return f"projects/{self.google_cloud_project_id}/locations/{self.google_cloud_location}/processors/{self.google_cloud_processor_id}"

# Global configuration instance
config = Config()
