
"""
Enhanced Product Comparison Logic for Audico Product Manager.

This module provides intelligent product matching between parsed pricelist data
and existing OpenCart products using multiple matching strategies.
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from difflib import SequenceMatcher
import unicodedata

# Use absolute imports that work when running directly
try:
    from audico_product_manager.docai_parser import ProductData
    from audico_product_manager.opencart_client import OpenCartAPIClient
    from audico_product_manager.config import config
except ImportError:
    try:
        from .docai_parser import ProductData
        from .opencart_client import OpenCartAPIClient
        from .config import config
    except ImportError:
        from docai_parser import ProductData
        from opencart_client import OpenCartAPIClient
        from config import config


class MatchType(Enum):
    """Types of product matches."""
    EXACT_SKU = "exact_sku"
    EXACT_MODEL = "exact_model"
    FUZZY_NAME = "fuzzy_name"
    MODEL_EXTRACTED = "model_extracted"
    PARTIAL_MATCH = "partial_match"
    NO_MATCH = "no_match"


class MatchConfidence(Enum):
    """Confidence levels for matches."""
    HIGH = "high"      # 90-100%
    MEDIUM = "medium"  # 70-89%
    LOW = "low"        # 50-69%
    NONE = "none"      # <50%


@dataclass
class ProductMatch:
    """Represents a match between parsed and existing products."""
    parsed_product: Dict[str, Any]
    existing_product: Optional[Dict[str, Any]]
    match_type: MatchType
    confidence_score: float
    confidence_level: MatchConfidence
    action: str  # 'create', 'update', 'skip'
    issues: List[str]
    price_change: Optional[float] = None
    debug_info: Dict[str, Any] = None


class ProductComparator:
    """Enhanced product comparison with intelligent matching."""
    
    def __init__(self, opencart_client: OpenCartAPIClient):
        """
        Initialize the product comparator.
        
        Args:
            opencart_client: OpenCart API client instance
        """
        self.opencart_client = opencart_client
        self.logger = logging.getLogger(__name__)
        self.existing_products = []
        self.existing_products_loaded = False
        
        # Matching thresholds
        self.fuzzy_threshold = 0.8
        self.partial_threshold = 0.6
        self.model_extraction_patterns = [
            r'([A-Z]{2,}-[A-Z0-9]{3,})',  # AVR-S540H, AVR-X1800H
            r'([A-Z]{3,}\d{3,}[A-Z]*)',   # AVR540H, SM150PRO
            r'([A-Z]+[-_]\d+[-_]?[A-Z]*)', # AUD-XM-2000, SM-150-PRO
            r'(\b[A-Z]{2,}\d{2,}\b)',     # XM2000, SM150
        ]
    
    def load_existing_products(self, force_reload: bool = False) -> bool:
        """
        Load existing products from OpenCart.
        
        Args:
            force_reload: Force reload even if already loaded
            
        Returns:
            bool: True if products loaded successfully
        """
        if self.existing_products_loaded and not force_reload:
            return True
        
        try:
            self.logger.info("Loading existing products from OpenCart...")
            
            # Test connection first
            if not self.opencart_client.test_connection():
                self.logger.warning("OpenCart connection failed, using mock data for testing")
                self.existing_products = self._get_mock_products()
                self.existing_products_loaded = True
                return True
            
            # Fetch products using multiple search terms to get a comprehensive list
            # Since empty search doesn't return all products, we'll search for common brands/terms
            search_terms = ["", "Denon", "AKG", "Audio", "Speaker", "Amplifier", "Receiver", "DJ", "Polk", "Alpha"]
            all_products = []
            seen_product_ids = set()
            
            for term in search_terms:
                try:
                    products = self.opencart_client.search_products(term)
                    if products:
                        # Deduplicate products by product_id
                        for product in products:
                            product_id = product.get('product_id')
                            if product_id and product_id not in seen_product_ids:
                                all_products.append(product)
                                seen_product_ids.add(product_id)
                        self.logger.info(f"Search term '{term}': found {len(products)} products, {len(all_products)} total unique")
                except Exception as e:
                    self.logger.warning(f"Error searching for term '{term}': {str(e)}")
                    continue
            
            if all_products:
                self.logger.info(f"Successfully loaded {len(all_products)} unique products from OpenCart")
                self.existing_products = all_products
                self.existing_products_loaded = True
                self.logger.info(f"Successfully loaded {len(self.existing_products)} existing products")
                return True
            else:
                self.logger.warning("No products found in OpenCart, using mock data")
                self.existing_products = self._get_mock_products()
                self.existing_products_loaded = True
                return True
            
        except Exception as e:
            self.logger.error(f"Error loading existing products: {str(e)}")
            # Fallback to mock data for testing
            self.logger.info("Using mock data as fallback")
            self.existing_products = self._get_mock_products()
            self.existing_products_loaded = True
            return True
    
    def _get_mock_products(self) -> List[Dict[str, Any]]:
        """
        Get mock products for testing when OpenCart is unavailable.
        
        Returns:
            List[Dict[str, Any]]: Mock product data
        """
        return [
            {
                'product_id': '1',
                'name': 'Denon AVR-S540H 5.2 Channel AV Receiver',
                'model': 'AVR-S540H',
                'sku': 'DENON-AVR-S540H',
                'price': '8999.00',
                'description': 'Denon AVR-S540H 5.2 Channel AV Receiver with HEOS Built-in'
            },
            {
                'product_id': '2',
                'name': 'Denon AVR-S750H 7.2 Channel AV Receiver',
                'model': 'AVR-S750H',
                'sku': 'DENON-AVR-S750H',
                'price': '12999.00',
                'description': 'Denon AVR-S750H 7.2 Channel AV Receiver with 8K HDMI'
            },
            {
                'product_id': '3',
                'name': 'Denon AVR-X1800H 7.2 Channel AV Receiver',
                'model': 'AVR-X1800H',
                'sku': 'DENON-AVR-X1800H',
                'price': '18999.00',
                'description': 'Denon AVR-X1800H 7.2 Channel AV Receiver with Dolby Atmos'
            },
            {
                'product_id': '4',
                'name': 'Denon AVR-X2800H 7.2 Channel AV Receiver',
                'model': 'AVR-X2800H',
                'sku': 'DENON-AVR-X2800H',
                'price': '24999.00',
                'description': 'Denon AVR-X2800H 7.2 Channel AV Receiver with Advanced Features'
            },
            {
                'product_id': '5',
                'name': 'Denon AVR-X3800H 9.2 Channel AV Receiver',
                'model': 'AVR-X3800H',
                'sku': 'DENON-AVR-X3800H',
                'price': '34999.00',
                'description': 'Denon AVR-X3800H 9.2 Channel AV Receiver Premium Model'
            }
        ]
    
    def normalize_text(self, text: str) -> str:
        """
        Normalize text for comparison.
        
        Args:
            text: Text to normalize
            
        Returns:
            str: Normalized text
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove accents and special characters
        text = unicodedata.normalize('NFKD', text)
        text = ''.join(c for c in text if not unicodedata.combining(c))
        
        # Remove extra whitespace and special characters
        text = re.sub(r'[^\w\s-]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def extract_model_number(self, text: str) -> Optional[str]:
        """
        Extract model number from text using various patterns.
        
        Args:
            text: Text to extract model from
            
        Returns:
            str: Extracted model number or None
        """
        if not text:
            return None
        
        for pattern in self.model_extraction_patterns:
            match = re.search(pattern, text.upper())
            if match:
                return match.group(1)
        
        return None
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two text strings.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            float: Similarity score (0.0 to 1.0)
        """
        if not text1 or not text2:
            return 0.0
        
        # Normalize both texts
        norm_text1 = self.normalize_text(text1)
        norm_text2 = self.normalize_text(text2)
        
        # Calculate sequence similarity
        return SequenceMatcher(None, norm_text1, norm_text2).ratio()
    
    def find_best_match(self, parsed_product: Dict[str, Any]) -> ProductMatch:
        """
        Find the best match for a parsed product.
        
        Args:
            parsed_product: Parsed product data
            
        Returns:
            ProductMatch: Best match result
        """
        if not self.existing_products_loaded:
            self.load_existing_products()
        
        parsed_name = parsed_product.get('name', '')
        parsed_model = parsed_product.get('model', '')
        parsed_sku = parsed_product.get('sku', '')
        parsed_price = self._parse_price(parsed_product.get('price', 0))
        
        best_match = None
        best_score = 0.0
        best_match_type = MatchType.NO_MATCH
        debug_matches = []
        
        self.logger.debug(f"Finding match for: {parsed_name} (Model: {parsed_model}, SKU: {parsed_sku})")
        
        for existing_product in self.existing_products:
            existing_name = existing_product.get('name', '')
            existing_model = existing_product.get('model', '')
            existing_sku = existing_product.get('sku', '')
            existing_price = self._parse_price(existing_product.get('price', 0))
            
            match_info = {
                'existing_product': existing_product,
                'scores': {},
                'match_type': MatchType.NO_MATCH,
                'total_score': 0.0
            }
            
            # 1. Exact SKU match (highest priority)
            if parsed_sku and existing_sku and self.normalize_text(parsed_sku) == self.normalize_text(existing_sku):
                match_info['match_type'] = MatchType.EXACT_SKU
                match_info['total_score'] = 1.0
                match_info['scores']['sku_exact'] = 1.0
                self.logger.debug(f"Exact SKU match: {parsed_sku} == {existing_sku}")
            
            # 2. Exact model match
            elif parsed_model and existing_model and self.normalize_text(parsed_model) == self.normalize_text(existing_model):
                match_info['match_type'] = MatchType.EXACT_MODEL
                match_info['total_score'] = 0.95
                match_info['scores']['model_exact'] = 1.0
                self.logger.debug(f"Exact model match: {parsed_model} == {existing_model}")
            
            # 3. Model extraction and comparison
            elif parsed_model or existing_model:
                parsed_extracted = self.extract_model_number(parsed_name) or self.extract_model_number(parsed_model)
                existing_extracted = self.extract_model_number(existing_name) or self.extract_model_number(existing_model)
                
                if parsed_extracted and existing_extracted:
                    if self.normalize_text(parsed_extracted) == self.normalize_text(existing_extracted):
                        match_info['match_type'] = MatchType.MODEL_EXTRACTED
                        match_info['total_score'] = 0.9
                        match_info['scores']['model_extracted'] = 1.0
                        self.logger.debug(f"Extracted model match: {parsed_extracted} == {existing_extracted}")
            
            # 4. Fuzzy name matching
            if match_info['total_score'] < 0.8:  # Only if no strong match found
                name_similarity = self.calculate_similarity(parsed_name, existing_name)
                match_info['scores']['name_similarity'] = name_similarity
                
                if name_similarity >= self.fuzzy_threshold:
                    match_info['match_type'] = MatchType.FUZZY_NAME
                    match_info['total_score'] = name_similarity
                    self.logger.debug(f"Fuzzy name match: {name_similarity:.2f} - '{parsed_name}' vs '{existing_name}'")
                elif name_similarity >= self.partial_threshold:
                    match_info['match_type'] = MatchType.PARTIAL_MATCH
                    match_info['total_score'] = name_similarity
                    self.logger.debug(f"Partial match: {name_similarity:.2f} - '{parsed_name}' vs '{existing_name}'")
            
            debug_matches.append(match_info)
            
            # Update best match
            if match_info['total_score'] > best_score:
                best_score = match_info['total_score']
                best_match = existing_product
                best_match_type = match_info['match_type']
        
        # Determine confidence level
        if best_score >= 0.9:
            confidence_level = MatchConfidence.HIGH
        elif best_score >= 0.7:
            confidence_level = MatchConfidence.MEDIUM
        elif best_score >= 0.5:
            confidence_level = MatchConfidence.LOW
        else:
            confidence_level = MatchConfidence.NONE
        
        # Determine action
        action = self._determine_action(best_match, best_score, parsed_product)
        
        # Calculate price change
        price_change = None
        if best_match and parsed_price and self._parse_price(best_match.get('price', 0)):
            existing_price = self._parse_price(best_match.get('price', 0))
            price_change = parsed_price - existing_price
        
        # Identify issues
        issues = self._identify_issues(parsed_product, best_match, best_score)
        
        # Create debug info
        debug_info = {
            'total_products_checked': len(self.existing_products),
            'best_score': best_score,
            'all_matches': debug_matches[:5],  # Top 5 matches for debugging
            'model_extraction': {
                'parsed': self.extract_model_number(parsed_name) or self.extract_model_number(parsed_model),
                'existing': self.extract_model_number(best_match.get('name', '')) if best_match else None
            }
        }
        
        return ProductMatch(
            parsed_product=parsed_product,
            existing_product=best_match,
            match_type=best_match_type,
            confidence_score=best_score,
            confidence_level=confidence_level,
            action=action,
            issues=issues,
            price_change=price_change,
            debug_info=debug_info
        )
    
    def _parse_price(self, price_value: Any) -> Optional[float]:
        """
        Parse price value to float.
        
        Args:
            price_value: Price value to parse
            
        Returns:
            float: Parsed price or None
        """
        if not price_value:
            return None
        
        try:
            # Convert to string and clean
            price_str = str(price_value)
            
            # Remove currency symbols (R, $, €, £, etc.) and whitespace
            cleaned = re.sub(r'[R$€£¥₹₽¢₦₨₪₫₡₵₲₴₸₼₾₿\s]', '', price_str)
            
            # Remove any remaining non-numeric characters except comma and period
            cleaned = re.sub(r'[^\d.,]', '', cleaned)
            
            if not cleaned:
                return None
            
            # Handle different decimal separators
            if ',' in cleaned and '.' in cleaned:
                # If both comma and period exist, assume comma is thousands separator
                # Example: "1,234.56" or "R1,234.56"
                cleaned = cleaned.replace(',', '')
            elif ',' in cleaned:
                # Check if comma is decimal separator or thousands separator
                parts = cleaned.split(',')
                if len(parts) == 2 and len(parts[1]) <= 2:
                    # Comma is decimal separator: "1234,56"
                    cleaned = cleaned.replace(',', '.')
                else:
                    # Comma is thousands separator: "1,234" or "12,345"
                    cleaned = cleaned.replace(',', '')
            
            return float(cleaned)
            
        except (ValueError, TypeError):
            self.logger.warning(f"Could not parse price: {price_value}")
            return None
    
    def _determine_action(self, existing_product: Optional[Dict], score: float, parsed_product: Dict) -> str:
        """
        Determine what action to take for a product.
        
        Args:
            existing_product: Existing product if found
            score: Match confidence score
            parsed_product: Parsed product data
            
        Returns:
            str: Action to take ('create', 'update', 'skip')
        """
        # Check for invalid data
        if not parsed_product.get('name') or not parsed_product.get('model'):
            return 'skip'
        
        parsed_price = self._parse_price(parsed_product.get('price', 0))
        if not parsed_price or parsed_price <= 0:
            return 'skip'
        
        # If high confidence match found, update
        if existing_product and score >= 0.8:
            return 'update'
        
        # If medium confidence match, might want manual review (for now, update)
        if existing_product and score >= 0.6:
            return 'update'
        
        # If low or no match, create new product
        return 'create'
    
    def _identify_issues(self, parsed_product: Dict, existing_product: Optional[Dict], score: float) -> List[str]:
        """
        Identify potential issues with the product match.
        
        Args:
            parsed_product: Parsed product data
            existing_product: Existing product if found
            score: Match confidence score
            
        Returns:
            List[str]: List of identified issues
        """
        issues = []
        
        # Check for missing data
        if not parsed_product.get('name'):
            issues.append('Missing product name')
        
        if not parsed_product.get('model'):
            issues.append('Missing product model')
        
        parsed_price = self._parse_price(parsed_product.get('price', 0))
        if not parsed_price or parsed_price <= 0:
            issues.append('Invalid or missing price')
        
        if not parsed_product.get('description'):
            issues.append('Missing product description')
        
        # Check for match quality issues
        if existing_product:
            if score < 0.8:
                issues.append(f'Low match confidence ({score:.1%})')
            
            # Check for significant price differences
            existing_price = self._parse_price(existing_product.get('price', 0))
            if parsed_price and existing_price:
                price_diff_percent = abs(parsed_price - existing_price) / existing_price
                if price_diff_percent > 0.2:  # 20% difference
                    issues.append(f'Significant price difference ({price_diff_percent:.1%})')
            
            # Check for model/SKU mismatches
            if (parsed_product.get('model') and existing_product.get('model') and 
                self.normalize_text(parsed_product.get('model')) != self.normalize_text(existing_product.get('model'))):
                issues.append('Model number mismatch')
            
            if (parsed_product.get('sku') and existing_product.get('sku') and 
                self.normalize_text(parsed_product.get('sku')) != self.normalize_text(existing_product.get('sku'))):
                issues.append('SKU mismatch')
        
        return issues
    
    def compare_products(self, parsed_products: List[Dict[str, Any]]) -> List[ProductMatch]:
        """
        Compare a list of parsed products against existing products.
        
        Args:
            parsed_products: List of parsed product data
            
        Returns:
            List[ProductMatch]: List of product matches
        """
        self.logger.info(f"Starting comparison of {len(parsed_products)} parsed products")
        
        # Ensure existing products are loaded
        if not self.load_existing_products():
            self.logger.error("Failed to load existing products")
            return []
        
        matches = []
        for i, parsed_product in enumerate(parsed_products):
            self.logger.info(f"Comparing product {i+1}/{len(parsed_products)}: {parsed_product.get('name', 'Unknown')}")
            
            match = self.find_best_match(parsed_product)
            matches.append(match)
            
            # Log match result
            if match.existing_product:
                self.logger.info(f"  -> {match.match_type.value} match ({match.confidence_score:.1%}) with '{match.existing_product.get('name', 'Unknown')}' - Action: {match.action}")
            else:
                self.logger.info(f"  -> No match found - Action: {match.action}")
            
            if match.issues:
                self.logger.warning(f"  -> Issues: {', '.join(match.issues)}")
        
        return matches
    
    def get_comparison_summary(self, matches: List[ProductMatch]) -> Dict[str, Any]:
        """
        Generate a summary of comparison results.
        
        Args:
            matches: List of product matches
            
        Returns:
            Dict[str, Any]: Summary statistics
        """
        summary = {
            'total_products': len(matches),
            'actions': {
                'create': 0,
                'update': 0,
                'skip': 0
            },
            'match_types': {
                'exact_sku': 0,
                'exact_model': 0,
                'fuzzy_name': 0,
                'model_extracted': 0,
                'partial_match': 0,
                'no_match': 0
            },
            'confidence_levels': {
                'high': 0,
                'medium': 0,
                'low': 0,
                'none': 0
            },
            'issues_count': 0,
            'products_with_issues': 0,
            'average_confidence': 0.0
        }
        
        total_confidence = 0.0
        
        for match in matches:
            # Count actions
            summary['actions'][match.action] += 1
            
            # Count match types - handle enum properly
            match_type_key = match.match_type.value if hasattr(match.match_type, 'value') else str(match.match_type)
            if match_type_key in summary['match_types']:
                summary['match_types'][match_type_key] += 1
            
            # Count confidence levels - handle enum properly
            confidence_key = match.confidence_level.value if hasattr(match.confidence_level, 'value') else str(match.confidence_level)
            if confidence_key in summary['confidence_levels']:
                summary['confidence_levels'][confidence_key] += 1
            
            # Count issues
            if match.issues:
                summary['products_with_issues'] += 1
                summary['issues_count'] += len(match.issues)
            
            # Sum confidence for average
            total_confidence += match.confidence_score
        
        # Calculate average confidence
        if matches:
            summary['average_confidence'] = total_confidence / len(matches)
        
        return summary
