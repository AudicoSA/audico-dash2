
"""
OpenCart API Client for Audico Product Manager.

This module provides a client for interacting with the OpenCart REST API,
including authentication, product management, and category operations.
"""

import requests
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urljoin, urlencode
import base64
from dotenv import load_dotenv

# Use absolute import that works when running directly
try:
    from audico_product_manager.config import config
except ImportError:
    try:
        from .config import config
    except ImportError:
        from config import config

# Load environment variables
load_dotenv()

class OpenCartProduct:
    """Represents a product in OpenCart with all necessary attributes."""
    
    def __init__(self, name: str, model: str, price: float, **kwargs):
        """
        Initialize an OpenCart product.
        
        Args:
            name: Product name
            model: Product model/SKU
            price: Product price
            **kwargs: Additional product attributes
        """
        self.name = name
        self.model = model
        self.price = price
        
        # Optional attributes with defaults
        self.description = kwargs.get('description', '')
        self.meta_title = kwargs.get('meta_title', name)
        self.meta_description = kwargs.get('meta_description', '')
        self.meta_keyword = kwargs.get('meta_keyword', '')
        self.tag = kwargs.get('tag', '')
        self.sku = kwargs.get('sku', model)
        self.upc = kwargs.get('upc', '')
        self.ean = kwargs.get('ean', '')
        self.jan = kwargs.get('jan', '')
        self.isbn = kwargs.get('isbn', '')
        self.mpn = kwargs.get('mpn', '')
        self.location = kwargs.get('location', '')
        self.quantity = kwargs.get('quantity', 100)
        self.minimum = kwargs.get('minimum', 1)
        self.subtract = kwargs.get('subtract', 1)
        self.stock_status_id = kwargs.get('stock_status_id', 7)  # In Stock
        self.date_available = kwargs.get('date_available', '2023-01-01')
        self.manufacturer_id = kwargs.get('manufacturer_id', 0)
        self.shipping = kwargs.get('shipping', 1)
        self.points = kwargs.get('points', 0)
        self.tax_class_id = kwargs.get('tax_class_id', 0)
        self.weight = kwargs.get('weight', 0.0)
        self.weight_class_id = kwargs.get('weight_class_id', 1)
        self.length = kwargs.get('length', 0.0)
        self.width = kwargs.get('width', 0.0)
        self.height = kwargs.get('height', 0.0)
        self.length_class_id = kwargs.get('length_class_id', 1)
        self.status = kwargs.get('status', 1)  # Enabled
        self.sort_order = kwargs.get('sort_order', 0)
        self.image = kwargs.get('image', '')
        
        # Categories (list of category IDs)
        self.categories = kwargs.get('categories', [])
        
        # Additional images
        self.images = kwargs.get('images', [])
        
        # Product options
        self.options = kwargs.get('options', [])
        
        # Product attributes
        self.attributes = kwargs.get('attributes', [])
        
        # SEO URL
        self.seo_url = kwargs.get('seo_url', '')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the product to a dictionary for API submission."""
        product_data = {
            'name': self.name,
            'model': self.model,
            'price': str(self.price),
            'description': self.description,
            'meta_title': self.meta_title,
            'meta_description': self.meta_description,
            'meta_keyword': self.meta_keyword,
            'tag': self.tag,
            'sku': self.sku,
            'upc': self.upc,
            'ean': self.ean,
            'jan': self.jan,
            'isbn': self.isbn,
            'mpn': self.mpn,
            'location': self.location,
            'quantity': str(self.quantity),
            'minimum': str(self.minimum),
            'subtract': str(self.subtract),
            'stock_status_id': str(self.stock_status_id),
            'date_available': self.date_available,
            'manufacturer_id': str(self.manufacturer_id),
            'shipping': str(self.shipping),
            'points': str(self.points),
            'tax_class_id': str(self.tax_class_id),
            'weight': str(self.weight),
            'weight_class_id': str(self.weight_class_id),
            'length': str(self.length),
            'width': str(self.width),
            'height': str(self.height),
            'length_class_id': str(self.length_class_id),
            'status': str(self.status),
            'sort_order': str(self.sort_order),
            'image': self.image,
        }
        
        # Add categories if specified
        if self.categories:
            product_data['product_category'] = self.categories
        
        # Add additional images if specified
        if self.images:
            product_data['product_image'] = self.images
        
        # Add options if specified
        if self.options:
            product_data['product_option'] = self.options
        
        # Add attributes if specified
        if self.attributes:
            product_data['product_attribute'] = self.attributes
        
        # Add SEO URL if specified
        if self.seo_url:
            product_data['product_seo_url'] = [{'language_id': '1', 'keyword': self.seo_url}]
        
        return product_data


class OpenCartAPIClient:
    """Client for interacting with OpenCart REST API."""
    
    def __init__(self, base_url: Optional[str] = None, auth_token: Optional[str] = None):
        """
        Initialize the OpenCart API client.
        
        Args:
            base_url: OpenCart API base URL
            auth_token: Authentication token for API access
        """
        self.base_url = base_url or config.opencart_base_url
        self.auth_token = auth_token or config.opencart_auth_token
        self.session = requests.Session()
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Set up Basic Auth headers
        self.headers = {
            'Authorization': f'Basic {self.auth_token}',
            'Content-Type': 'application/json'
        }
    
    def search_products(self, search_term: str) -> Optional[List[Dict]]:
        """
        Search for products using the OpenCart API.
        
        Args:
            search_term: Product name or model to search for
            
        Returns:
            List[Dict]: List of matching products or None if request failed
        """
        try:
            # Use the specific endpoint format for audicoonline.co.za
            url = f"https://www.audicoonline.co.za/index.php?route=ocrestapi/product/listing&search={search_term}"
            
            self.logger.info(f"Searching for products with term: {search_term}")
            response = self.session.get(url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                # Extract products from the nested response structure
                if 'data' in data and 'products' in data['data']:
                    products = data['data']['products']
                    self.logger.info(f"Successfully retrieved {len(products)} products")
                    return products
                else:
                    self.logger.warning(f"Unexpected response structure: {list(data.keys())}")
                    return []
            else:
                self.logger.error(f"Product search failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Product search error: {str(e)}")
            return None
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                     params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make an authenticated request to the OpenCart API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            data: Request data for POST/PUT requests
            params: Query parameters
            
        Returns:
            Dict: Response data or None if request failed
        """
        url = urljoin(self.base_url, endpoint)
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, headers=self.headers, params=params)
            elif method.upper() == 'POST':
                response = self.session.post(url, headers=self.headers, json=data)
            elif method.upper() == 'PUT':
                response = self.session.put(url, headers=self.headers, json=data)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, headers=self.headers)
            else:
                self.logger.error(f"Unsupported HTTP method: {method}")
                return None
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                self.logger.error(f"API request failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Request error: {str(e)}")
            return None
    
    def get_categories(self) -> Optional[List[Dict]]:
        """
        Retrieve all categories from OpenCart.
        
        Returns:
            List[Dict]: List of categories or None if request failed
        """
        response = self._make_request('GET', '/categories')
        if response and 'data' in response:
            return response['data']
        return None
    
    def get_category_by_name(self, name: str) -> Optional[Dict]:
        """
        Find a category by name.
        
        Args:
            name: Category name to search for
            
        Returns:
            Dict: Category data or None if not found
        """
        categories = self.get_categories()
        if categories:
            for category in categories:
                if category.get('name', '').lower() == name.lower():
                    return category
        return None
    
    def create_category(self, name: str, description: str = '', parent_id: int = 0) -> Optional[Dict]:
        """
        Create a new category in OpenCart.
        
        Args:
            name: Category name
            description: Category description
            parent_id: Parent category ID (0 for top-level)
            
        Returns:
            Dict: Created category data or None if creation failed
        """
        category_data = {
            'name': name,
            'description': description,
            'parent_id': str(parent_id),
            'status': '1',
            'sort_order': '0'
        }
        
        return self._make_request('POST', '/categories', data=category_data)
    
    def get_products(self, search_term: str = "", limit: int = 100, page: int = 1) -> Optional[List[Dict]]:
        """Retrieve products from OpenCart using search.

        Args:
            search_term: Search term for products (empty string returns all)
            limit: Unused. Reserved for future support of result limiting.
            page: Unused. Placeholder for future pagination support.

        Returns:
            List[Dict]: List of products or None if request failed
        """
        return self.search_products(search_term)
    
    def get_product_by_model(self, model: str) -> Optional[Dict]:
        """
        Find a product by model/SKU.
        
        Args:
            model: Product model/SKU to search for
            
        Returns:
            Dict: Product data or None if not found
        """
        # Search for products using the model as search term
        products = self.search_products(model)
        if products:
            # Look for exact model match first
            for product in products:
                if product.get('model', '').lower() == model.lower():
                    return product
            # If no exact match, return the first result
            return products[0] if products else None
        return None
    
    def create_product(self, product: OpenCartProduct) -> Optional[Dict]:
        """
        Create a new product in OpenCart.
        
        Args:
            product: OpenCartProduct instance
            
        Returns:
            Dict: Created product data or None if creation failed
        """
        product_data = product.to_dict()
        self.logger.info(f"Creating product: {product.name} (Model: {product.model})")
        
        response = self._make_request('POST', '/products', data=product_data)
        if response:
            self.logger.info(f"Successfully created product: {product.name}")
        else:
            self.logger.error(f"Failed to create product: {product.name}")
        
        return response
    
    def update_product(self, product_id: int, product: OpenCartProduct) -> Optional[Dict]:
        """
        Update an existing product in OpenCart.
        
        Args:
            product_id: ID of the product to update
            product: OpenCartProduct instance with updated data
            
        Returns:
            Dict: Updated product data or None if update failed
        """
        product_data = product.to_dict()
        self.logger.info(f"Updating product ID {product_id}: {product.name}")
        
        response = self._make_request('PUT', f'/products/{product_id}', data=product_data)
        if response:
            self.logger.info(f"Successfully updated product: {product.name}")
        else:
            self.logger.error(f"Failed to update product: {product.name}")
        
        return response
    
    def delete_product(self, product_id: int) -> bool:
        """
        Delete a product from OpenCart.
        
        Args:
            product_id: ID of the product to delete
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        self.logger.info(f"Deleting product ID: {product_id}")
        
        response = self._make_request('DELETE', f'/products/{product_id}')
        if response:
            self.logger.info(f"Successfully deleted product ID: {product_id}")
            return True
        else:
            self.logger.error(f"Failed to delete product ID: {product_id}")
            return False
    
    def sync_product(self, product: OpenCartProduct) -> Tuple[bool, Optional[Dict]]:
        """
        Synchronize a product with OpenCart (create or update).
        
        Args:
            product: OpenCartProduct instance
            
        Returns:
            Tuple[bool, Optional[Dict]]: (success, product_data)
        """
        # Check if product already exists
        existing_product = self.get_product_by_model(product.model)
        
        if existing_product:
            # Update existing product
            product_id = existing_product.get('product_id')
            result = self.update_product(product_id, product)
            return result is not None, result
        else:
            # Create new product
            result = self.create_product(product)
            return result is not None, result
    
    def get_manufacturers(self) -> Optional[List[Dict]]:
        """
        Retrieve all manufacturers from OpenCart.
        
        Returns:
            List[Dict]: List of manufacturers or None if request failed
        """
        response = self._make_request('GET', '/manufacturers')
        if response and 'data' in response:
            return response['data']
        return None
    
    def get_manufacturer_by_name(self, name: str) -> Optional[Dict]:
        """
        Find a manufacturer by name.
        
        Args:
            name: Manufacturer name to search for
            
        Returns:
            Dict: Manufacturer data or None if not found
        """
        manufacturers = self.get_manufacturers()
        if manufacturers:
            for manufacturer in manufacturers:
                if manufacturer.get('name', '').lower() == name.lower():
                    return manufacturer
        return None
    
    def test_connection(self) -> bool:
        """
        Test the connection to OpenCart API.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Test with a simple product search
            url = f"https://www.audicoonline.co.za/index.php?route=ocrestapi/product/listing&search=test"
            response = self.session.get(url, headers=self.headers)
            self.logger.info(f"Connection test response: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Connection test failed: {str(e)}")
            return False
