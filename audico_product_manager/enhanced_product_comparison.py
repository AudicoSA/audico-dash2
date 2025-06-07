
"""
Enhanced Product Comparison Logic with Store Name Generation and Improved Matching.

This module provides intelligent product matching between parsed pricelist data
and existing OpenCart products using GPT-4 generated store names and fuzzy matching.
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from difflib import SequenceMatcher
import unicodedata

try:
    import rapidfuzz
    from rapidfuzz import fuzz, process
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False
    logging.warning("rapidfuzz not available, falling back to difflib")

try:
    from audico_product_manager.docai_parser import ProductData
    from audico_product_manager.opencart_client import OpenCartAPIClient
    from audico_product_manager.config import config
    from audico_product_manager.store_name_generator import StoreNameGenerator
except ImportError:
    try:
        from .docai_parser import ProductData
        from .opencart_client import OpenCartAPIClient
        from .config import config
        from .store_name_generator import StoreNameGenerator
    except ImportError:
        from docai_parser import ProductData
        from opencart_client import OpenCartAPIClient
        from config import config
        from store_name_generator import StoreNameGenerator


class MatchType(Enum):
    """Types of product matches."""
    EXACT_SKU = "exact_sku"
    EXACT_MODEL = "exact_model"
    STORE_NAME_MATCH = "store_name_match"
    FUZZY_NAME = "fuzzy_name"
    MODEL_EXTRACTED = "model_extracted"
    PARTIAL_MATCH = "partial_match"
    NO_MATCH = "no_match"


class MatchConfidence(Enum):
    """Confidence levels for matches."""
    HIGH = "high"      # 85-100%
    MEDIUM = "medium"  # 65-84%
    LOW = "low"        # 45-64%
    NONE = "none"      # <45%


@dataclass
class EnhancedProductMatch:
    """Represents a match between parsed and existing products with enhanced features."""
    parsed_product: Dict[str, Any]
    existing_product: Optional[Dict[str, Any]]
    match_type: MatchType
    confidence_score: float
    confidence_level: MatchConfidence
    action: str  # 'create', 'update', 'skip'
    issues: List[str]
    price_change: Optional[float] = None
    store_name_used: Optional[str] = None
    debug_info: Dict[str, Any] = None


class EnhancedProductComparator:
    """Enhanced product comparison with GPT-4 store names and improved fuzzy matching."""
    
    def __init__(self, opencart_client: OpenCartAPIClient, store_name_generator: Optional[StoreNameGenerator] = None):
        """
        Initialize the enhanced product comparator.
        
        Args:
            opencart_client: OpenCart API client instance
            store_name_generator: Store name generator instance (optional)
        """
        self.opencart_client = opencart_client
        self.store_name_generator = store_name_generator or StoreNameGenerator()
        self.logger = logging.getLogger(__name__)
        self.existing_products = []
        self.existing_products_loaded = False
        
        # Enhanced matching thresholds
        self.exact_threshold = 0.95
        self.high_threshold = 0.85
        self.medium_threshold = 0.65
        self.low_threshold = 0.45
        
        # Enhanced model extraction patterns
        self.model_extraction_patterns = [
            # Denon specific patterns
            r'(AVR[X]?[-_]?[A-Z]?\d{3,4}[A-Z]*[BT]*)',  # AVR-X1800H, AVRX-580BT
            r'(AVC[-_][A-Z]?\d{3,4}[A-Z]*)',  # AVC-X3800H
            # General audio patterns with decimal support
            r'([A-Z]{1,3}\d{1,3}\.?\d*[A-Z]*)',  # K12.2, SM58, C414
            r'([A-Z]{2,}[-_][A-Z0-9\.]{3,})',  # AVR-S540H, QSC-K12.2
            r'([A-Z]{3,}\d{3,}[A-Z]*)',   # AVR540H, SM150PRO
            r'([A-Z]+[-_]\d+\.?\d*[-_]?[A-Z]*)', # AUD-XM-2000, K12.2
            r'(\b[A-Z]{2,}\d{2,}\.?\d*[A-Z]*\b)',     # XM2000, K12.2, SM150
            # Professional audio patterns
            r'([A-Z]+\d+[A-Z]*[-_]?[A-Z]*)', # SM58, Beta57A
            r'([A-Z]{2,}[-_]?\d{2,}\.?\d*[-_]?[A-Z]*)', # QSC-K12.2, JBL-EON615
            # CDJ and DJ equipment
            r'(CDJ[-_]?\d{3,4}[A-Z]*)', # CDJ-3000, CDJ3000
            # AKG patterns
            r'(C\d{3}[-_]?[A-Z]*)', # C414-XLS, C414
        ]
        
        # Enhanced search terms for OpenCart API
        self.audio_search_terms = [
            "", "Denon", "AKG", "Audio", "Speaker", "Amplifier", "Receiver", "DJ", "Polk", "Alpha",
            "JBL", "QSC", "Yamaha", "Pioneer", "Sony", "Marantz", "Onkyo", "Harman", "Shure",
            "Sennheiser", "Audio-Technica", "Behringer", "Mackie", "PreSonus", "Focusrite",
            "Microphone", "Headphones", "Subwoofer", "Monitor", "Mixer", "Interface", "Preamp",
            "Turntable", "CDJ", "Controller", "Synthesizer", "Keyboard", "Studio", "Live",
            "Channel", "Wireless", "Bluetooth", "USB", "XLR", "TRS", "Phantom", "Condenser",
            "Dynamic", "Ribbon", "Cardioid", "Omnidirectional", "Shotgun", "Lavalier",
            "HDMI", "4K", "8K", "Dolby", "DTS", "Atmos", "Surround", "Theater", "Cinema"
        ]
    
    def load_existing_products(self, force_reload: bool = False) -> bool:
        """
        Load existing products from OpenCart with enhanced search.
        
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
                self.logger.warning("OpenCart connection failed, using enhanced mock data")
                self.existing_products = self._get_enhanced_mock_products()
                self.existing_products_loaded = True
                return True
            
            # Fetch products using multiple search terms
            all_products = []
            seen_product_ids = set()
            
            for term in self.audio_search_terms:
                try:
                    products = self.opencart_client.search_products(term)
                    if products:
                        for product in products:
                            product_id = product.get('product_id')
                            if product_id and product_id not in seen_product_ids:
                                all_products.append(product)
                                seen_product_ids.add(product_id)
                        self.logger.debug(f"Search term '{term}': found {len(products)} products")
                except Exception as e:
                    self.logger.warning(f"Error searching for term '{term}': {str(e)}")
                    continue
            
            if all_products:
                self.logger.info(f"Successfully loaded {len(all_products)} unique products from OpenCart")
                self.existing_products = all_products
                self.existing_products_loaded = True
                return True
            else:
                self.logger.warning("No products found in OpenCart, using mock data")
                self.existing_products = self._get_enhanced_mock_products()
                self.existing_products_loaded = True
                return True
            
        except Exception as e:
            self.logger.error(f"Error loading existing products: {str(e)}")
            self.existing_products = self._get_enhanced_mock_products()
            self.existing_products_loaded = True
            return True
    
    def _get_enhanced_mock_products(self) -> List[Dict[str, Any]]:
        """Get enhanced mock products for testing."""
        return [
            {
                'product_id': '1',
                'name': 'Denon AVR-X580BT - 5 Channel Home Theatre Amplifier 130W per Channel 8K',
                'model': 'AVR-X580BT',
                'sku': 'DENON-AVR-X580BT',
                'price': '7999.00',
                'description': 'Denon AVR-X580BT 5.2 Channel AV Receiver with Bluetooth and 8K support'
            },
            {
                'product_id': '2',
                'name': 'Denon AVR-S540H - 5.2 Channel AV Receiver with HEOS',
                'model': 'AVR-S540H',
                'sku': 'DENON-AVR-S540H',
                'price': '8999.00',
                'description': 'Denon AVR-S540H 5.2 Channel AV Receiver with HEOS Built-in'
            },
            {
                'product_id': '3',
                'name': 'Denon AVR-X1800H - 7.2 Channel AV Receiver with Dolby Atmos',
                'model': 'AVR-X1800H',
                'sku': 'DENON-AVR-X1800H',
                'price': '18999.00',
                'description': 'Denon AVR-X1800H 7.2 Channel AV Receiver with Dolby Atmos'
            },
            {
                'product_id': '4',
                'name': 'Shure SM58 - Dynamic Vocal Microphone',
                'model': 'SM58',
                'sku': 'SHURE-SM58',
                'price': '1899.00',
                'description': 'Shure SM58 Professional Dynamic Vocal Microphone'
            },
            {
                'product_id': '5',
                'name': 'QSC K12.2 - 2000W 12-inch Powered Speaker',
                'model': 'K12.2',
                'sku': 'QSC-K12.2',
                'price': '12999.00',
                'description': 'QSC K12.2 2000W 12-inch Powered Speaker'
            }
        ]
    
    def normalize_text(self, text: str) -> str:
        """Enhanced text normalization for audio equipment."""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove accents and special characters
        text = unicodedata.normalize('NFKD', text)
        text = ''.join(c for c in text if not unicodedata.combining(c))
        
        # Audio equipment specific normalizations
        normalizations = {
            r'\bch\b': 'channel',
            r'\bch\.': 'channel',
            r'\bamp\b': 'amplifier',
            r'\brec\b': 'receiver',
            r'\bbt\b': 'bluetooth',
            r'\bwifi\b': 'wifi',
            r'\bhdmi\b': 'hdmi',
            r'\b4k\b': '4k',
            r'\b8k\b': '8k',
            r'\bav\s+receiver\b': 'av receiver',
            r'\bhome\s+theater\b': 'home theater',
            r'\bhome\s+theatre\b': 'home theater',
            r'\bsurround\s+sound\b': 'surround sound'
        }
        
        for pattern, replacement in normalizations.items():
            text = re.sub(pattern, replacement, text)
        
        # Remove extra whitespace and special characters
        text = re.sub(r'[^\w\s-]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def calculate_fuzzy_similarity(self, text1: str, text2: str) -> float:
        """Calculate fuzzy similarity using rapidfuzz or fallback to difflib."""
        if not text1 or not text2:
            return 0.0
        
        # Normalize both texts
        norm_text1 = self.normalize_text(text1)
        norm_text2 = self.normalize_text(text2)
        
        if RAPIDFUZZ_AVAILABLE:
            # Use rapidfuzz for better performance and accuracy
            ratio = fuzz.ratio(norm_text1, norm_text2) / 100.0
            token_sort_ratio = fuzz.token_sort_ratio(norm_text1, norm_text2) / 100.0
            token_set_ratio = fuzz.token_set_ratio(norm_text1, norm_text2) / 100.0
            
            # Use the best score
            similarity = max(ratio, token_sort_ratio, token_set_ratio)
        else:
            # Fallback to difflib
            similarity = SequenceMatcher(None, norm_text1, norm_text2).ratio()
        
        # Boost similarity for audio equipment specific terms
        audio_terms = ['receiver', 'amplifier', 'speaker', 'microphone', 'channel', 'dolby', 'dts', 'hdmi']
        common_audio_terms = sum(1 for term in audio_terms if term in norm_text1 and term in norm_text2)
        
        if common_audio_terms > 0:
            boost = min(0.1, common_audio_terms * 0.03)
            similarity = min(1.0, similarity + boost)
        
        return similarity
    
    def extract_model_number(self, text: str) -> Optional[str]:
        """Enhanced model number extraction."""
        if not text:
            return None
        
        for pattern in self.model_extraction_patterns:
            match = re.search(pattern, text.upper())
            if match:
                model = match.group(1)
                if len(model) >= 3 and re.search(r'[A-Z].*\d|^\d.*[A-Z]', model):
                    return model
        
        return None
    
    def find_best_match_enhanced(self, product_data: ProductData) -> EnhancedProductMatch:
        """
        Find the best match for a product using enhanced matching with store names.
        
        Args:
            product_data: Product data from extraction
            
        Returns:
            EnhancedProductMatch: Enhanced match result
        """
        if not self.existing_products_loaded:
            self.load_existing_products()
        
        # Generate store-friendly name
        store_name = self.store_name_generator.generate_store_name(product_data)
        product_data.online_store_name = store_name
        
        # Prepare search data
        parsed_name = product_data.name or ""
        parsed_model = product_data.model or ""
        parsed_sku = getattr(product_data, 'sku', '') or ""
        parsed_price = self._parse_price(product_data.price)
        
        best_match = None
        best_score = 0.0
        best_match_type = MatchType.NO_MATCH
        debug_matches = []
        
        self.logger.debug(f"Finding enhanced match for: {parsed_name}")
        self.logger.debug(f"Generated store name: {store_name}")
        
        for existing_product in self.existing_products:
            existing_name = existing_product.get('name', '')
            existing_model = existing_product.get('model', '')
            existing_sku = existing_product.get('sku', '')
            
            match_info = {
                'existing_product': existing_product,
                'scores': {},
                'match_type': MatchType.NO_MATCH,
                'total_score': 0.0
            }
            
            # 1. Exact SKU match (highest priority)
            if parsed_sku and existing_sku:
                sku_similarity = self.calculate_fuzzy_similarity(parsed_sku, existing_sku)
                match_info['scores']['sku'] = sku_similarity
                if sku_similarity >= self.exact_threshold:
                    match_info['match_type'] = MatchType.EXACT_SKU
                    match_info['total_score'] = sku_similarity
            
            # 2. Exact model match
            if match_info['total_score'] < self.exact_threshold and parsed_model and existing_model:
                model_similarity = self.calculate_fuzzy_similarity(parsed_model, existing_model)
                match_info['scores']['model'] = model_similarity
                if model_similarity >= self.exact_threshold:
                    match_info['match_type'] = MatchType.EXACT_MODEL
                    match_info['total_score'] = model_similarity
            
            # 3. Store name matching (new enhanced feature)
            if match_info['total_score'] < self.high_threshold and store_name:
                store_name_similarity = self.calculate_fuzzy_similarity(store_name, existing_name)
                match_info['scores']['store_name'] = store_name_similarity
                if store_name_similarity >= self.high_threshold:
                    match_info['match_type'] = MatchType.STORE_NAME_MATCH
                    match_info['total_score'] = store_name_similarity
            
            # 4. Model extraction and comparison
            if match_info['total_score'] < self.high_threshold:
                parsed_extracted = self.extract_model_number(parsed_name) or self.extract_model_number(parsed_model)
                existing_extracted = self.extract_model_number(existing_name) or self.extract_model_number(existing_model)
                
                if parsed_extracted and existing_extracted:
                    extracted_similarity = self.calculate_fuzzy_similarity(parsed_extracted, existing_extracted)
                    match_info['scores']['model_extracted'] = extracted_similarity
                    if extracted_similarity >= self.high_threshold:
                        match_info['match_type'] = MatchType.MODEL_EXTRACTED
                        match_info['total_score'] = extracted_similarity
            
            # 5. Fuzzy name matching
            if match_info['total_score'] < self.medium_threshold:
                name_similarity = self.calculate_fuzzy_similarity(parsed_name, existing_name)
                match_info['scores']['name_similarity'] = name_similarity
                
                if name_similarity >= self.medium_threshold:
                    match_info['match_type'] = MatchType.FUZZY_NAME
                    match_info['total_score'] = name_similarity
                elif name_similarity >= self.low_threshold:
                    match_info['match_type'] = MatchType.PARTIAL_MATCH
                    match_info['total_score'] = name_similarity
            
            debug_matches.append(match_info)
            
            # Update best match
            if match_info['total_score'] > best_score:
                best_score = match_info['total_score']
                best_match = existing_product
                best_match_type = match_info['match_type']
        
        # Determine confidence level
        if best_score >= self.high_threshold:
            confidence_level = MatchConfidence.HIGH
        elif best_score >= self.medium_threshold:
            confidence_level = MatchConfidence.MEDIUM
        elif best_score >= self.low_threshold:
            confidence_level = MatchConfidence.LOW
        else:
            confidence_level = MatchConfidence.NONE
        
        # Determine action with enhanced logic
        action = self._determine_action_enhanced(best_match, best_score, product_data)
        
        # Calculate price change
        price_change = None
        if best_match and parsed_price:
            existing_price = self._parse_price(best_match.get('price', 0))
            if existing_price:
                price_change = parsed_price - existing_price
        
        # Identify issues
        issues = self._identify_issues_enhanced(product_data, best_match, best_score)
        
        # Create debug info
        debug_info = {
            'total_products_checked': len(self.existing_products),
            'best_score': best_score,
            'store_name_generated': store_name,
            'top_matches': debug_matches[:3],
            'model_extraction': {
                'parsed': self.extract_model_number(parsed_name) or self.extract_model_number(parsed_model),
                'existing': self.extract_model_number(best_match.get('name', '')) if best_match else None
            }
        }
        
        return EnhancedProductMatch(
            parsed_product=product_data.__dict__ if hasattr(product_data, '__dict__') else product_data,
            existing_product=best_match,
            match_type=best_match_type,
            confidence_score=best_score,
            confidence_level=confidence_level,
            action=action,
            issues=issues,
            price_change=price_change,
            store_name_used=store_name,
            debug_info=debug_info
        )
    
    def _parse_price(self, price_value: Any) -> Optional[float]:
        """Enhanced price parsing."""
        if not price_value:
            return None
        
        try:
            price_str = str(price_value)
            cleaned = re.sub(r'[R$€£¥₹₽¢₦₨₪₫₡₵₲₴₸₼₾₿\s]', '', price_str)
            cleaned = re.sub(r'[^\d.,]', '', cleaned)
            
            if not cleaned:
                return None
            
            if ',' in cleaned and '.' in cleaned:
                cleaned = cleaned.replace(',', '')
            elif ',' in cleaned:
                parts = cleaned.split(',')
                if len(parts) == 2 and len(parts[1]) <= 2:
                    cleaned = cleaned.replace(',', '.')
                else:
                    cleaned = cleaned.replace(',', '')
            
            return float(cleaned)
            
        except (ValueError, TypeError):
            self.logger.warning(f"Could not parse price: {price_value}")
            return None
    
    def _determine_action_enhanced(self, existing_product: Optional[Dict], score: float, product_data: ProductData) -> str:
        """Determine action with enhanced logic."""
        # Check for invalid data
        if not product_data.name or not product_data.model:
            return 'skip'
        
        parsed_price = self._parse_price(product_data.price)
        if not parsed_price or parsed_price <= 0:
            return 'skip'
        
        # Enhanced thresholds for actions
        if existing_product and score >= self.medium_threshold:  # 65% threshold
            return 'update'
        
        # Create new product if no good match found
        return 'create'
    
    def _identify_issues_enhanced(self, product_data: ProductData, existing_product: Optional[Dict], score: float) -> List[str]:
        """Identify issues with enhanced logic."""
        issues = []
        
        # Check for missing data
        if not product_data.name:
            issues.append('Missing product name')
        if not product_data.model:
            issues.append('Missing product model')
        
        parsed_price = self._parse_price(product_data.price)
        if not parsed_price or parsed_price <= 0:
            issues.append('Invalid or missing price')
        
        # Check match quality
        if existing_product:
            if score < self.medium_threshold:
                issues.append(f'Low confidence match ({score:.2f})')
            
            # Check for significant price differences
            if parsed_price:
                existing_price = self._parse_price(existing_product.get('price', 0))
                if existing_price:
                    price_diff_percent = abs(parsed_price - existing_price) / existing_price
                    if price_diff_percent > 0.2:  # 20% difference
                        issues.append(f'Significant price difference ({price_diff_percent:.1%})')
        
        return issues
    
    def batch_compare_products(self, products_data: List[ProductData]) -> List[EnhancedProductMatch]:
        """
        Compare a batch of products with enhanced matching.
        
        Args:
            products_data: List of product data to compare
            
        Returns:
            List[EnhancedProductMatch]: List of enhanced match results
        """
        self.logger.info(f"Starting enhanced batch comparison for {len(products_data)} products")
        
        # Ensure existing products are loaded
        self.load_existing_products()
        
        # Generate store names for all products first
        self.logger.info("Generating store names for all products...")
        products_data = self.store_name_generator.batch_generate_store_names(products_data)
        
        # Compare each product
        matches = []
        for i, product_data in enumerate(products_data):
            try:
                self.logger.debug(f"Comparing product {i+1}/{len(products_data)}: {product_data.name}")
                match = self.find_best_match_enhanced(product_data)
                matches.append(match)
                
                self.logger.info(f"Product {i+1}: {match.match_type.value} match with {match.confidence_score:.2f} confidence")
                
            except Exception as e:
                self.logger.error(f"Error comparing product {i+1}: {str(e)}")
                # Create error match
                error_match = EnhancedProductMatch(
                    parsed_product=product_data.__dict__ if hasattr(product_data, '__dict__') else product_data,
                    existing_product=None,
                    match_type=MatchType.NO_MATCH,
                    confidence_score=0.0,
                    confidence_level=MatchConfidence.NONE,
                    action='skip',
                    issues=[f'Comparison error: {str(e)}'],
                    store_name_used=getattr(product_data, 'online_store_name', None)
                )
                matches.append(error_match)
        
        # Log summary
        self._log_comparison_summary(matches)
        
        return matches
    
    def _log_comparison_summary(self, matches: List[EnhancedProductMatch]) -> None:
        """Log summary of comparison results."""
        total = len(matches)
        if total == 0:
            return
        
        # Count by match type
        match_type_counts = {}
        confidence_counts = {}
        action_counts = {}
        
        for match in matches:
            match_type_counts[match.match_type.value] = match_type_counts.get(match.match_type.value, 0) + 1
            confidence_counts[match.confidence_level.value] = confidence_counts.get(match.confidence_level.value, 0) + 1
            action_counts[match.action] = action_counts.get(match.action, 0) + 1
        
        self.logger.info("=== Enhanced Comparison Summary ===")
        self.logger.info(f"Total products compared: {total}")
        self.logger.info(f"Match types: {match_type_counts}")
        self.logger.info(f"Confidence levels: {confidence_counts}")
        self.logger.info(f"Actions: {action_counts}")
        
        # Calculate success rate
        successful_matches = sum(1 for match in matches if match.confidence_level in [MatchConfidence.HIGH, MatchConfidence.MEDIUM])
        success_rate = (successful_matches / total) * 100
        self.logger.info(f"Success rate (High/Medium confidence): {success_rate:.1f}%")
