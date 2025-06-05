
"""
Product logic and synchronization for Audico Product Manager.

This module handles the business logic for product processing, including
data transformation, validation, and synchronization with OpenCart.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re
from decimal import Decimal, InvalidOperation

# Use absolute imports that work when running directly
try:
    from audico_product_manager.docai_parser import ProductData
    from audico_product_manager.opencart_client import OpenCartProduct, OpenCartAPIClient
    from audico_product_manager.config import config
except ImportError:
    try:
        from .docai_parser import ProductData
        from .opencart_client import OpenCartProduct, OpenCartAPIClient
        from .config import config
    except ImportError:
        from docai_parser import ProductData
        from opencart_client import OpenCartProduct, OpenCartAPIClient
        from config import config


class ProductAction(Enum):
    """Enumeration of possible product actions."""
    CREATE = "create"
    UPDATE = "update"
    SKIP = "skip"
    ERROR = "error"


@dataclass
class ProductSyncResult:
    """Result of a product synchronization operation."""
    action: ProductAction
    product_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    opencart_product_id: Optional[int] = None


class ProductSynchronizer:
    """Handles product synchronization between parsed data and OpenCart."""
    
    def __init__(self, opencart_client: OpenCartAPIClient):
        """
        Initialize the product synchronizer.
        
        Args:
            opencart_client: OpenCart API client instance
        """
        self.opencart_client = opencart_client
        self.logger = logging.getLogger(__name__)
        
        # Cache for categories and manufacturers
        self._categories_cache = None
        self._manufacturers_cache = None
    
    def _get_categories(self) -> Dict[str, int]:
        """
        Get categories from OpenCart and cache them.
        
        Returns:
            Dict[str, int]: Mapping of category names to IDs
        """
        if self._categories_cache is None:
            categories = self.opencart_client.get_categories()
            if categories:
                self._categories_cache = {
                    cat.get('name', '').lower(): int(cat.get('category_id', 0))
                    for cat in categories
                    if cat.get('name') and cat.get('category_id')
                }
            else:
                self._categories_cache = {}
        
        return self._categories_cache
    
    def _get_manufacturers(self) -> Dict[str, int]:
        """
        Get manufacturers from OpenCart and cache them.
        
        Returns:
            Dict[str, int]: Mapping of manufacturer names to IDs
        """
        if self._manufacturers_cache is None:
            manufacturers = self.opencart_client.get_manufacturers()
            if manufacturers:
                self._manufacturers_cache = {
                    mfr.get('name', '').lower(): int(mfr.get('manufacturer_id', 0))
                    for mfr in manufacturers
                    if mfr.get('name') and mfr.get('manufacturer_id')
                }
            else:
                self._manufacturers_cache = {}
        
        return self._manufacturers_cache
    
    def _clean_price(self, price_str: str) -> Optional[float]:
        """
        Clean and convert price string to float.
        
        Args:
            price_str: Price string from parsed data
            
        Returns:
            float: Cleaned price or None if invalid
        """
        if not price_str:
            return None
        
        try:
            # Remove currency symbols and whitespace
            cleaned = re.sub(r'[^\d.,]', '', str(price_str))
            
            # Handle different decimal separators
            if ',' in cleaned and '.' in cleaned:
                # Assume comma is thousands separator if both present
                cleaned = cleaned.replace(',', '')
            elif ',' in cleaned:
                # Check if comma is decimal separator
                parts = cleaned.split(',')
                if len(parts) == 2 and len(parts[1]) <= 2:
                    cleaned = cleaned.replace(',', '.')
                else:
                    cleaned = cleaned.replace(',', '')
            
            return float(cleaned)
            
        except (ValueError, InvalidOperation):
            self.logger.warning(f"Could not parse price: {price_str}")
            return None
    
    def _generate_seo_url(self, name: str, model: str) -> str:
        """
        Generate SEO-friendly URL from product name and model.
        
        Args:
            name: Product name
            model: Product model
            
        Returns:
            str: SEO-friendly URL
        """
        # Combine name and model
        text = f"{name} {model}".lower()
        
        # Remove special characters and replace spaces with hyphens
        seo_url = re.sub(r'[^a-z0-9\s-]', '', text)
        seo_url = re.sub(r'\s+', '-', seo_url)
        seo_url = re.sub(r'-+', '-', seo_url)
        seo_url = seo_url.strip('-')
        
        return seo_url
    
    def _find_category_id(self, category_name: str) -> Optional[int]:
        """
        Find category ID by name, with fallback to target category.
        
        Args:
            category_name: Category name to search for
            
        Returns:
            int: Category ID or None if not found
        """
        categories = self._get_categories()
        
        # Try exact match first
        category_id = categories.get(category_name.lower())
        if category_id:
            return category_id
        
        # Try target category from config
        target_category_id = categories.get(config.target_category.lower())
        if target_category_id:
            self.logger.info(f"Using target category '{config.target_category}' for product")
            return target_category_id
        
        # Create target category if it doesn't exist
        self.logger.info(f"Creating target category: {config.target_category}")
        result = self.opencart_client.create_category(
            name=config.target_category,
            description=f"Auto-created category for {config.target_category} products"
        )
        
        if result and 'category_id' in result:
            category_id = int(result['category_id'])
            # Update cache
            self._categories_cache[config.target_category.lower()] = category_id
            return category_id
        
        return None
    
    def _find_manufacturer_id(self, manufacturer_name: str) -> int:
        """
        Find manufacturer ID by name, with fallback to default.
        
        Args:
            manufacturer_name: Manufacturer name to search for
            
        Returns:
            int: Manufacturer ID
        """
        manufacturers = self._get_manufacturers()
        
        # Try exact match first
        manufacturer_id = manufacturers.get(manufacturer_name.lower())
        if manufacturer_id:
            return manufacturer_id
        
        # Try default manufacturer
        default_manufacturer_id = manufacturers.get(config.default_manufacturer.lower())
        if default_manufacturer_id:
            return default_manufacturer_id
        
        # Return 0 if no manufacturer found
        return 0
    
    def convert_to_opencart_product(self, product_data: ProductData) -> Optional[OpenCartProduct]:
        """
        Convert parsed product data to OpenCart product format.
        
        Args:
            product_data: Parsed product data
            
        Returns:
            OpenCartProduct: Converted product or None if conversion failed
        """
        try:
            # Clean and validate price
            price = self._clean_price(product_data.price)
            if price is None or price <= 0:
                self.logger.error(f"Invalid price for product {product_data.name}: {product_data.price}")
                return None
            
            # Find category ID
            category_id = self._find_category_id(product_data.category or config.target_category)
            categories = [category_id] if category_id else []
            
            # Find manufacturer ID
            manufacturer_id = self._find_manufacturer_id(product_data.manufacturer or config.default_manufacturer)
            
            # Generate SEO URL
            seo_url = self._generate_seo_url(product_data.name, product_data.model)
            
            # Create OpenCart product
            opencart_product = OpenCartProduct(
                name=product_data.name,
                model=product_data.model,
                price=price,
                description=product_data.description or f"{product_data.name} - {product_data.model}",
                sku=product_data.model,
                categories=categories,
                manufacturer_id=manufacturer_id,
                status=int(config.default_status),
                stock_status_id=int(config.default_stock_status),
                quantity=100,  # Default quantity
                seo_url=seo_url,
                meta_title=product_data.name,
                meta_description=f"{product_data.name} - {product_data.model}",
                tag=f"{product_data.name},{product_data.model},{product_data.category or config.target_category}"
            )
            
            return opencart_product
            
        except Exception as e:
            self.logger.error(f"Error converting product data: {str(e)}")
            return None
    
    def sync_product(self, product_data: ProductData) -> ProductSyncResult:
        """
        Synchronize a single product with OpenCart.
        
        Args:
            product_data: Parsed product data
            
        Returns:
            ProductSyncResult: Result of the synchronization
        """
        try:
            # Convert to OpenCart product format
            opencart_product = self.convert_to_opencart_product(product_data)
            if not opencart_product:
                return ProductSyncResult(
                    action=ProductAction.ERROR,
                    error_message="Failed to convert product data"
                )
            
            # Check if product already exists
            existing_product = self.opencart_client.get_product_by_model(opencart_product.model)
            
            if existing_product:
                # Update existing product
                product_id = existing_product.get('product_id')
                result = self.opencart_client.update_product(product_id, opencart_product)
                
                if result:
                    return ProductSyncResult(
                        action=ProductAction.UPDATE,
                        product_data=result,
                        opencart_product_id=product_id
                    )
                else:
                    return ProductSyncResult(
                        action=ProductAction.ERROR,
                        error_message="Failed to update existing product"
                    )
            else:
                # Create new product
                result = self.opencart_client.create_product(opencart_product)
                
                if result:
                    product_id = result.get('product_id')
                    return ProductSyncResult(
                        action=ProductAction.CREATE,
                        product_data=result,
                        opencart_product_id=product_id
                    )
                else:
                    return ProductSyncResult(
                        action=ProductAction.ERROR,
                        error_message="Failed to create new product"
                    )
                    
        except Exception as e:
            self.logger.error(f"Error syncing product {product_data.name}: {str(e)}")
            return ProductSyncResult(
                action=ProductAction.ERROR,
                error_message=str(e)
            )
    
    def sync_products_batch(self, products_data: List[ProductData]) -> List[ProductSyncResult]:
        """
        Synchronize a batch of products with OpenCart.
        
        Args:
            products_data: List of parsed product data
            
        Returns:
            List[ProductSyncResult]: Results of the synchronization
        """
        results = []
        
        for i, product_data in enumerate(products_data):
            self.logger.info(f"Syncing product {i+1}/{len(products_data)}: {product_data.name}")
            
            result = self.sync_product(product_data)
            results.append(result)
            
            # Log result
            if result.action == ProductAction.CREATE:
                self.logger.info(f"Created product: {product_data.name}")
            elif result.action == ProductAction.UPDATE:
                self.logger.info(f"Updated product: {product_data.name}")
            elif result.action == ProductAction.ERROR:
                self.logger.error(f"Error with product {product_data.name}: {result.error_message}")
        
        return results
    
    def get_sync_summary(self, results: List[ProductSyncResult]) -> Dict[str, Any]:
        """
        Generate a summary of synchronization results.
        
        Args:
            results: List of sync results
            
        Returns:
            Dict[str, Any]: Summary statistics
        """
        summary = {
            'total': len(results),
            'created': 0,
            'updated': 0,
            'errors': 0,
            'skipped': 0,
            'error_messages': []
        }
        
        for result in results:
            if result.action == ProductAction.CREATE:
                summary['created'] += 1
            elif result.action == ProductAction.UPDATE:
                summary['updated'] += 1
            elif result.action == ProductAction.ERROR:
                summary['errors'] += 1
                if result.error_message:
                    summary['error_messages'].append(result.error_message)
            elif result.action == ProductAction.SKIP:
                summary['skipped'] += 1
        
        return summary
