
"""
Product comparison and synchronization logic.

Handles the business logic for comparing parsed products with existing
OpenCart products and determining what actions need to be taken.
"""

import logging
from typing import List, Dict, Any, Tuple, Optional, Set
from decimal import Decimal, InvalidOperation
from difflib import SequenceMatcher
import re

from .docai_parser import ProductData
from .opencart_client import OpenCartProduct, OpenCartAPIClient
from .config import config

logger = logging.getLogger(__name__)

class ProductAction:
    """Represents an action to be taken on a product."""
    
    CREATE = "create"
    UPDATE = "update"
    SKIP = "skip"
    ERROR = "error"
    
    def __init__(self, action: str, parsed_product: ProductData, 
                 existing_product: Optional[OpenCartProduct] = None,
                 reason: str = "", changes: Dict[str, Any] = None):
        self.action = action
        self.parsed_product = parsed_product
        self.existing_product = existing_product
        self.reason = reason
        self.changes = changes or {}
    
    def __str__(self):
        return f"ProductAction({self.action}: {self.parsed_product.name} - {self.reason})"

class ProductMatcher:
    """Handles product matching logic between parsed and existing products."""
    
    def __init__(self, similarity_threshold: float = 0.8):
        """
        Initialize product matcher.
        
        Args:
            similarity_threshold: Minimum similarity score for name matching (0.0-1.0)
        """
        self.similarity_threshold = similarity_threshold
    
    def find_matching_product(self, parsed_product: ProductData, 
                            existing_products: List[OpenCartProduct]) -> Optional[OpenCartProduct]:
        """
        Find the best matching existing product for a parsed product.
        
        Args:
            parsed_product: Product data from parsed document
            existing_products: List of existing OpenCart products
            
        Returns:
            Best matching OpenCart product or None
        """
        best_match = None
        best_score = 0.0
        
        for existing_product in existing_products:
            score = self._calculate_match_score(parsed_product, existing_product)
            
            if score > best_score and score >= self.similarity_threshold:
                best_score = score
                best_match = existing_product
        
        if best_match:
            logger.debug(f"Found match for '{parsed_product.name}' -> '{best_match.name}' (score: {best_score:.2f})")
        
        return best_match
    
    def _calculate_match_score(self, parsed_product: ProductData, 
                             existing_product: OpenCartProduct) -> float:
        """
        Calculate similarity score between parsed and existing product.
        
        Args:
            parsed_product: Product data from parsed document
            existing_product: Existing OpenCart product
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        scores = []
        
        # Name similarity (highest weight)
        name_score = self._calculate_string_similarity(
            parsed_product.name, existing_product.name
        )
        scores.append(name_score * 0.6)
        
        # SKU similarity (if available)
        if parsed_product.sku and existing_product.sku:
            sku_score = self._calculate_string_similarity(
                parsed_product.sku, existing_product.sku
            )
            scores.append(sku_score * 0.3)
        
        # Model similarity (if available)
        if existing_product.model:
            model_score = self._calculate_string_similarity(
                parsed_product.name, existing_product.model
            )
            scores.append(model_score * 0.1)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate similarity between two strings.
        
        Args:
            str1: First string
            str2: Second string
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not str1 or not str2:
            return 0.0
        
        # Normalize strings
        str1_norm = self._normalize_string(str1)
        str2_norm = self._normalize_string(str2)
        
        # Calculate sequence similarity
        return SequenceMatcher(None, str1_norm, str2_norm).ratio()
    
    def _normalize_string(self, text: str) -> str:
        """
        Normalize string for comparison.
        
        Args:
            text: Input text
            
        Returns:
            Normalized text
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove common punctuation
        text = re.sub(r'[^\w\s]', '', text)
        
        return text

class ProductComparator:
    """Handles product comparison and change detection."""
    
    def __init__(self, price_tolerance: float = 0.01):
        """
        Initialize product comparator.
        
        Args:
            price_tolerance: Tolerance for price comparison (percentage)
        """
        self.price_tolerance = price_tolerance
    
    def compare_products(self, parsed_product: ProductData, 
                        existing_product: OpenCartProduct) -> Dict[str, Any]:
        """
        Compare parsed product with existing product to detect changes.
        
        Args:
            parsed_product: Product data from parsed document
            existing_product: Existing OpenCart product
            
        Returns:
            Dictionary of detected changes
        """
        changes = {}
        
        # Compare name
        if self._strings_differ(parsed_product.name, existing_product.name):
            changes['name'] = {
                'old': existing_product.name,
                'new': parsed_product.name
            }
        
        # Compare price
        parsed_price = parsed_product.clean_price()
        existing_price = self._parse_existing_price(existing_product.price)
        
        if parsed_price and existing_price:
            if self._prices_differ(parsed_price, existing_price):
                changes['price'] = {
                    'old': str(existing_price),
                    'new': str(parsed_price)
                }
        elif parsed_price and not existing_price:
            changes['price'] = {
                'old': existing_product.price,
                'new': str(parsed_price)
            }
        
        # Compare description
        if (parsed_product.description and 
            self._strings_differ(parsed_product.description, existing_product.description)):
            changes['description'] = {
                'old': existing_product.description,
                'new': parsed_product.description
            }
        
        # Compare SKU
        if (parsed_product.sku and 
            self._strings_differ(parsed_product.sku, existing_product.sku)):
            changes['sku'] = {
                'old': existing_product.sku,
                'new': parsed_product.sku
            }
        
        return changes
    
    def _strings_differ(self, str1: str, str2: str) -> bool:
        """Check if two strings are significantly different."""
        if not str1 or not str2:
            return bool(str1) != bool(str2)
        
        # Normalize and compare
        norm1 = str1.strip().lower()
        norm2 = str2.strip().lower()
        
        return norm1 != norm2
    
    def _prices_differ(self, price1: Decimal, price2: Decimal) -> bool:
        """Check if two prices are significantly different."""
        if price1 == price2:
            return False
        
        # Calculate percentage difference
        if price2 == 0:
            return price1 != 0
        
        diff_percentage = abs(price1 - price2) / price2
        return diff_percentage > self.price_tolerance
    
    def _parse_existing_price(self, price_str: str) -> Optional[Decimal]:
        """Parse existing product price string to Decimal."""
        if not price_str:
            return None
        
        try:
            # Remove currency symbols and whitespace
            price_clean = re.sub(r'[^\d.,]', '', str(price_str))
            
            # Handle different decimal separators
            if ',' in price_clean and '.' in price_clean:
                price_clean = price_clean.replace(',', '')
            elif ',' in price_clean:
                price_clean = price_clean.replace(',', '.')
            
            return Decimal(price_clean)
        except (InvalidOperation, ValueError):
            logger.warning(f"Could not parse existing price: {price_str}")
            return None

class ProductSynchronizer:
    """Main class for product synchronization logic."""
    
    def __init__(self, opencart_client: OpenCartAPIClient):
        """
        Initialize product synchronizer.
        
        Args:
            opencart_client: OpenCart API client instance
        """
        self.opencart_client = opencart_client
        self.matcher = ProductMatcher()
        self.comparator = ProductComparator()
        
        # Cache for existing products
        self._existing_products_cache = None
        self._cache_timestamp = None
    
    def analyze_products(self, parsed_products: List[ProductData]) -> List[ProductAction]:
        """
        Analyze parsed products and determine required actions.
        
        Args:
            parsed_products: List of products from parsed documents
            
        Returns:
            List of ProductAction objects
        """
        logger.info(f"Analyzing {len(parsed_products)} parsed products")
        
        # Get existing products
        existing_products = self._get_existing_products()
        if existing_products is None:
            logger.error("Failed to retrieve existing products")
            return [ProductAction(ProductAction.ERROR, product, reason="Failed to retrieve existing products") 
                   for product in parsed_products]
        
        actions = []
        
        for parsed_product in parsed_products:
            try:
                action = self._analyze_single_product(parsed_product, existing_products)
                actions.append(action)
            except Exception as e:
                logger.error(f"Error analyzing product '{parsed_product.name}': {e}")
                actions.append(ProductAction(
                    ProductAction.ERROR, 
                    parsed_product, 
                    reason=f"Analysis error: {e}"
                ))
        
        # Log summary
        action_counts = {}
        for action in actions:
            action_counts[action.action] = action_counts.get(action.action, 0) + 1
        
        logger.info(f"Analysis complete: {action_counts}")
        return actions
    
    def _analyze_single_product(self, parsed_product: ProductData, 
                               existing_products: List[OpenCartProduct]) -> ProductAction:
        """
        Analyze a single parsed product and determine the required action.
        
        Args:
            parsed_product: Product data from parsed document
            existing_products: List of existing OpenCart products
            
        Returns:
            ProductAction object
        """
        # Validate parsed product
        if not parsed_product.is_valid():
            return ProductAction(
                ProductAction.ERROR, 
                parsed_product, 
                reason="Invalid product data (missing name or price)"
            )
        
        # Find matching existing product
        matching_product = self.matcher.find_matching_product(parsed_product, existing_products)
        
        if matching_product:
            # Product exists, check for updates
            changes = self.comparator.compare_products(parsed_product, matching_product)
            
            if changes:
                return ProductAction(
                    ProductAction.UPDATE,
                    parsed_product,
                    matching_product,
                    reason=f"Product needs update: {list(changes.keys())}",
                    changes=changes
                )
            else:
                return ProductAction(
                    ProductAction.SKIP,
                    parsed_product,
                    matching_product,
                    reason="Product is up to date"
                )
        else:
            # New product, needs to be created
            return ProductAction(
                ProductAction.CREATE,
                parsed_product,
                reason="New product not found in OpenCart"
            )
    
    def execute_actions(self, actions: List[ProductAction]) -> Dict[str, int]:
        """
        Execute the determined product actions.
        
        Args:
            actions: List of ProductAction objects to execute
            
        Returns:
            Dictionary with execution statistics
        """
        logger.info(f"Executing {len(actions)} product actions")
        
        stats = {
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0
        }
        
        for action in actions:
            try:
                if action.action == ProductAction.CREATE:
                    success = self._create_product(action)
                    if success:
                        stats['created'] += 1
                    else:
                        stats['errors'] += 1
                
                elif action.action == ProductAction.UPDATE:
                    success = self._update_product(action)
                    if success:
                        stats['updated'] += 1
                    else:
                        stats['errors'] += 1
                
                elif action.action == ProductAction.SKIP:
                    stats['skipped'] += 1
                    logger.debug(f"Skipped product: {action.parsed_product.name}")
                
                else:  # ERROR
                    stats['errors'] += 1
                    logger.error(f"Product error: {action.parsed_product.name} - {action.reason}")
                
            except Exception as e:
                logger.error(f"Error executing action for '{action.parsed_product.name}': {e}")
                stats['errors'] += 1
        
        logger.info(f"Execution complete: {stats}")
        return stats
    
    def _create_product(self, action: ProductAction) -> bool:
        """Create a new product in OpenCart."""
        parsed_product = action.parsed_product
        
        # Prepare product data
        product_data = {
            'name': parsed_product.name,
            'description': parsed_product.description or parsed_product.name,
            'model': parsed_product.sku or parsed_product.name[:64],
            'sku': parsed_product.sku,
            'price': str(parsed_product.clean_price() or '0'),
            'status': config.default_status,
            'stock_status_id': config.default_stock_status,
            'quantity': '0'
        }
        
        # Get category ID for target category
        category_id = self.opencart_client.get_category_id_by_name(config.target_category)
        if category_id:
            product_data['category_id'] = category_id
        
        # Create product
        success, product_id = self.opencart_client.create_product(product_data)
        
        if success:
            logger.info(f"Created product: {parsed_product.name} (ID: {product_id})")
            return True
        else:
            logger.error(f"Failed to create product: {parsed_product.name}")
            return False
    
    def _update_product(self, action: ProductAction) -> bool:
        """Update an existing product in OpenCart."""
        parsed_product = action.parsed_product
        existing_product = action.existing_product
        changes = action.changes
        
        # Prepare update data with only changed fields
        update_data = {}
        
        for field, change in changes.items():
            if field == 'price':
                update_data['price'] = change['new']
            elif field == 'name':
                update_data['name'] = change['new']
            elif field == 'description':
                update_data['description'] = change['new']
            elif field == 'sku':
                update_data['sku'] = change['new']
        
        # Update product
        success = self.opencart_client.update_product(existing_product.product_id, update_data)
        
        if success:
            logger.info(f"Updated product: {existing_product.name} (ID: {existing_product.product_id})")
            return True
        else:
            logger.error(f"Failed to update product: {existing_product.name}")
            return False
    
    def _get_existing_products(self) -> Optional[List[OpenCartProduct]]:
        """Get all existing products from OpenCart with caching."""
        try:
            # Simple caching - in production, consider more sophisticated caching
            success, products = self.opencart_client.search_products(limit=1000)
            
            if success:
                logger.info(f"Retrieved {len(products)} existing products from OpenCart")
                return products
            else:
                logger.error("Failed to retrieve existing products from OpenCart")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving existing products: {e}")
            return None
    
    def get_synchronization_summary(self, actions: List[ProductAction]) -> Dict[str, Any]:
        """
        Generate a summary of the synchronization analysis.
        
        Args:
            actions: List of ProductAction objects
            
        Returns:
            Summary dictionary
        """
        summary = {
            'total_products': len(actions),
            'actions': {
                'create': 0,
                'update': 0,
                'skip': 0,
                'error': 0
            },
            'products_to_create': [],
            'products_to_update': [],
            'products_with_errors': []
        }
        
        for action in actions:
            summary['actions'][action.action] += 1
            
            if action.action == ProductAction.CREATE:
                summary['products_to_create'].append({
                    'name': action.parsed_product.name,
                    'price': str(action.parsed_product.clean_price() or '0'),
                    'sku': action.parsed_product.sku
                })
            
            elif action.action == ProductAction.UPDATE:
                summary['products_to_update'].append({
                    'name': action.parsed_product.name,
                    'existing_id': action.existing_product.product_id,
                    'changes': list(action.changes.keys())
                })
            
            elif action.action == ProductAction.ERROR:
                summary['products_with_errors'].append({
                    'name': action.parsed_product.name,
                    'reason': action.reason
                })
        
        return summary
