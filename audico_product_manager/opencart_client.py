
"""
OpenCart REST API client for product management.

Provides functionality to interact with OpenCart's custom REST API for
listing, creating, and updating products.
"""

import logging
import requests
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urljoin, urlencode
import base64

from .config import config

logger = logging.getLogger(__name__)

class OpenCartProduct:
    """Data class for OpenCart product information."""
    
    def __init__(self, product_data: Dict[str, Any]):
        """Initialize from OpenCart API response data."""
        self.product_id = product_data.get('product_id')
        self.name = product_data.get('name', '')
        self.model = product_data.get('model', '')
        self.sku = product_data.get('sku', '')
        self.price = product_data.get('price', '0')
        self.description = product_data.get('description', '')
        self.category_id = product_data.get('category_id')
        self.manufacturer_id = product_data.get('manufacturer_id')
        self.status = product_data.get('status', '1')
        self.stock_status_id = product_data.get('stock_status_id', '7')
        self.quantity = product_data.get('quantity', '0')
        self.image = product_data.get('image', '')
        self.date_added = product_data.get('date_added')
        self.date_modified = product_data.get('date_modified')
        self.raw_data = product_data
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API requests."""
        return {
            'name': self.name,
            'model': self.model,
            'sku': self.sku,
            'price': self.price,
            'description': self.description,
            'category_id': self.category_id,
            'manufacturer_id': self.manufacturer_id,
            'status': self.status,
            'stock_status_id': self.stock_status_id,
            'quantity': self.quantity,
            'image': self.image
        }

class OpenCartAPIClient:
    """OpenCart REST API client for product management."""
    
    def __init__(self):
        """Initialize OpenCart API client with authentication."""
        self.base_url = config.opencart_base_url
        self.auth_token = config.opencart_auth_token
        self.session = requests.Session()
        
        # Set up authentication headers
        self.session.headers.update({
            'Authorization': f'Basic {self.auth_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        # Set up retry configuration
        self.max_retries = config.max_retries
        self.retry_delay = config.retry_delay
        
        logger.info("Initialized OpenCart API client")
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, 
                     data: Dict = None) -> Tuple[bool, Dict]:
        """
        Make HTTP request to OpenCart API with retry logic.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            params: URL parameters
            data: Request body data
            
        Returns:
            Tuple of (success, response_data)
        """
        url = urljoin(self.base_url, endpoint)
        
        for attempt in range(self.max_retries + 1):
            try:
                if method.upper() == 'GET':
                    response = self.session.get(url, params=params, timeout=30)
                elif method.upper() == 'POST':
                    response = self.session.post(url, params=params, json=data, timeout=30)
                elif method.upper() == 'PUT':
                    response = self.session.put(url, params=params, json=data, timeout=30)
                elif method.upper() == 'DELETE':
                    response = self.session.delete(url, params=params, timeout=30)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                # Check response status
                if response.status_code == 200:
                    try:
                        return True, response.json()
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON response from {url}")
                        return True, {'message': response.text}
                
                elif response.status_code == 401:
                    logger.error("Authentication failed - check API token")
                    return False, {'error': 'Authentication failed'}
                
                elif response.status_code == 404:
                    logger.warning(f"Endpoint not found: {url}")
                    return False, {'error': 'Endpoint not found'}
                
                elif response.status_code >= 500:
                    logger.warning(f"Server error {response.status_code}, attempt {attempt + 1}")
                    if attempt < self.max_retries:
                        time.sleep(self.retry_delay)
                        continue
                    return False, {'error': f'Server error: {response.status_code}'}
                
                else:
                    logger.warning(f"Unexpected status code {response.status_code}: {response.text}")
                    return False, {'error': f'HTTP {response.status_code}: {response.text}'}
                
            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout, attempt {attempt + 1}")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
                    continue
                return False, {'error': 'Request timeout'}
            
            except requests.exceptions.ConnectionError:
                logger.warning(f"Connection error, attempt {attempt + 1}")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
                    continue
                return False, {'error': 'Connection error'}
            
            except Exception as e:
                logger.error(f"Unexpected error in API request: {e}")
                return False, {'error': str(e)}
        
        return False, {'error': 'Max retries exceeded'}
    
    def search_products(self, search_term: str = "", limit: int = 100, 
                       page: int = 1) -> Tuple[bool, List[OpenCartProduct]]:
        """
        Search for products in OpenCart.
        
        Args:
            search_term: Product name or search term
            limit: Maximum number of results
            page: Page number for pagination
            
        Returns:
            Tuple of (success, list_of_products)
        """
        params = {
            'limit': limit,
            'page': page
        }
        
        if search_term:
            params['search'] = search_term
        
        success, response_data = self._make_request('GET', '/listing', params=params)
        
        if not success:
            return False, []
        
        products = []
        if 'data' in response_data and isinstance(response_data['data'], list):
            for product_data in response_data['data']:
                products.append(OpenCartProduct(product_data))
        elif isinstance(response_data, list):
            for product_data in response_data:
                products.append(OpenCartProduct(product_data))
        
        logger.info(f"Found {len(products)} products for search: '{search_term}'")
        return True, products
    
    def get_product_by_id(self, product_id: str) -> Tuple[bool, Optional[OpenCartProduct]]:
        """
        Get a specific product by ID.
        
        Args:
            product_id: OpenCart product ID
            
        Returns:
            Tuple of (success, product_or_none)
        """
        success, response_data = self._make_request('GET', f'/{product_id}')
        
        if not success:
            return False, None
        
        if 'data' in response_data:
            return True, OpenCartProduct(response_data['data'])
        elif 'product_id' in response_data:
            return True, OpenCartProduct(response_data)
        
        return False, None
    
    def get_product_by_name(self, product_name: str) -> Tuple[bool, Optional[OpenCartProduct]]:
        """
        Get a product by exact name match.
        
        Args:
            product_name: Exact product name to search for
            
        Returns:
            Tuple of (success, product_or_none)
        """
        success, products = self.search_products(search_term=product_name)
        
        if not success:
            return False, None
        
        # Look for exact name match
        for product in products:
            if product.name.lower().strip() == product_name.lower().strip():
                return True, product
        
        return True, None  # No exact match found
    
    def get_product_by_sku(self, sku: str) -> Tuple[bool, Optional[OpenCartProduct]]:
        """
        Get a product by SKU.
        
        Args:
            sku: Product SKU to search for
            
        Returns:
            Tuple of (success, product_or_none)
        """
        success, products = self.search_products(search_term=sku)
        
        if not success:
            return False, None
        
        # Look for exact SKU match
        for product in products:
            if product.sku.lower().strip() == sku.lower().strip():
                return True, product
        
        return True, None  # No exact match found
    
    def create_product(self, product_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Create a new product in OpenCart.
        
        Args:
            product_data: Product data dictionary
            
        Returns:
            Tuple of (success, product_id_or_none)
        """
        # Set default values for required fields
        default_data = {
            'status': config.default_status,
            'stock_status_id': config.default_stock_status,
            'quantity': '0',
            'model': product_data.get('name', '')[:64],  # Use name as model if not provided
            'manufacturer_id': '0',  # Default manufacturer
            'category_id': '0',  # Will be set by category lookup
        }
        
        # Merge with provided data
        final_data = {**default_data, **product_data}
        
        success, response_data = self._make_request('POST', '', data=final_data)
        
        if success:
            product_id = response_data.get('product_id') or response_data.get('data', {}).get('product_id')
            if product_id:
                logger.info(f"Created product: {final_data.get('name')} (ID: {product_id})")
                return True, str(product_id)
        
        logger.error(f"Failed to create product: {response_data}")
        return False, None
    
    def update_product(self, product_id: str, product_data: Dict[str, Any]) -> bool:
        """
        Update an existing product in OpenCart.
        
        Args:
            product_id: OpenCart product ID
            product_data: Updated product data
            
        Returns:
            Success status
        """
        success, response_data = self._make_request('PUT', f'/{product_id}', data=product_data)
        
        if success:
            logger.info(f"Updated product ID: {product_id}")
            return True
        
        logger.error(f"Failed to update product {product_id}: {response_data}")
        return False
    
    def delete_product(self, product_id: str) -> bool:
        """
        Delete a product from OpenCart.
        
        Args:
            product_id: OpenCart product ID
            
        Returns:
            Success status
        """
        success, response_data = self._make_request('DELETE', f'/{product_id}')
        
        if success:
            logger.info(f"Deleted product ID: {product_id}")
            return True
        
        logger.error(f"Failed to delete product {product_id}: {response_data}")
        return False
    
    def get_categories(self) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Get list of product categories.
        
        Returns:
            Tuple of (success, list_of_categories)
        """
        # Note: This endpoint might need to be adjusted based on actual API
        success, response_data = self._make_request('GET', '/categories')
        
        if success and isinstance(response_data, list):
            return True, response_data
        elif success and 'data' in response_data:
            return True, response_data['data']
        
        return False, []
    
    def get_category_id_by_name(self, category_name: str) -> Optional[str]:
        """
        Get category ID by name.
        
        Args:
            category_name: Category name to search for
            
        Returns:
            Category ID or None if not found
        """
        success, categories = self.get_categories()
        
        if not success:
            return None
        
        for category in categories:
            if category.get('name', '').lower() == category_name.lower():
                return str(category.get('category_id'))
        
        return None
    
    def test_connection(self) -> bool:
        """
        Test the API connection and authentication.
        
        Returns:
            True if connection is successful
        """
        try:
            success, response = self.search_products(limit=1)
            if success:
                logger.info("OpenCart API connection test successful")
                return True
            else:
                logger.error(f"OpenCart API connection test failed: {response}")
                return False
        except Exception as e:
            logger.error(f"OpenCart API connection test error: {e}")
            return False
