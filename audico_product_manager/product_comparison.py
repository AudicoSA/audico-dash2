

"""
Enhanced Product Comparison Logic for Audico Product Manager.

This module provides intelligent product matching between parsed pricelist data
and existing OpenCart products using multiple matching strategies with improved
audio equipment specific search terms and fuzzy matching.
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
    """Enhanced product comparison with intelligent matching for audio equipment."""
    
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
        
        # Enhanced matching thresholds for audio equipment
        self.fuzzy_threshold = 0.75  # Lowered for better audio equipment matching
        self.partial_threshold = 0.55  # Lowered for better partial matches
        
        # Enhanced model extraction patterns for audio equipment
        self.model_extraction_patterns = [
            # Denon specific patterns
            r'(AVR[X]?[-_]?[A-Z]?\d{3,4}[A-Z]*[BT]*)',  # AVR-X1800H, AVRX-580BT
            r'(AVC[-_][A-Z]?\d{3,4}[A-Z]*)',  # AVC-X3800H
            # General audio patterns
            r'([A-Z]{2,}-[A-Z0-9]{3,})',  # AVR-S540H, QSC-K12
            r'([A-Z]{3,}\d{3,}[A-Z]*)',   # AVR540H, SM150PRO
            r'([A-Z]+[-_]\d+[-_]?[A-Z]*)', # AUD-XM-2000, SM-150-PRO
            r'(\b[A-Z]{2,}\d{2,}\b)',     # XM2000, SM150
            # Professional audio patterns
            r'([A-Z]+\d+[A-Z]*[-_]?[A-Z]*)', # SM58, Beta57A
            r'([A-Z]{2,}[-_]?\d{2,}[-_]?[A-Z]*)', # QSC-K12, JBL-EON615
        ]
        
        # Expanded audio equipment search terms
        self.audio_search_terms = [
            "", "Denon", "AKG", "Audio", "Speaker", "Amplifier", "Receiver", "DJ", "Polk", "Alpha",
            # Audio brands
            "JBL", "QSC", "Yamaha", "Pioneer", "Sony", "Marantz", "Onkyo", "Harman", "Shure",
            "Sennheiser", "Audio-Technica", "Behringer", "Mackie", "PreSonus", "Focusrite",
            # Product categories
            "Microphone", "Headphones", "Subwoofer", "Monitor", "Mixer", "Interface", "Preamp",
            "Turntable", "CDJ", "Controller", "Synthesizer", "Keyboard", "Studio", "Live",
            # Audio terms
            "Channel", "Wireless", "Bluetooth", "USB", "XLR", "TRS", "Phantom", "Condenser",
            "Dynamic", "Ribbon", "Cardioid", "Omnidirectional", "Shotgun", "Lavalier",
            # AV terms
            "HDMI", "4K", "8K", "Dolby", "DTS", "Atmos", "Surround", "Theater", "Cinema",
            "Streaming", "Network", "WiFi", "Ethernet", "Optical", "Coaxial", "Analog"
        ]
    
    def load_existing_products(self, force_reload: bool = False) -> bool:
        """
        Load existing products from OpenCart with enhanced audio equipment search.
        
        Args:
            force_reload: Force reload even if already loaded
            
        Returns:
            bool: True if products loaded successfully
        """
        if self.existing_products_loaded and not force_reload:
            return True
        
        try:
            self.logger.info("Loading existing products from OpenCart with enhanced audio search...")
            
            # Test connection first
            if not self.opencart_client.test_connection():
                self.logger.warning("OpenCart connection failed, using enhanced mock data for testing")
                self.existing_products = self._get_enhanced_mock_products()
                self.existing_products_loaded = True
                return True
            
            # Fetch products using expanded audio equipment search terms
            all_products = []
            seen_product_ids = set()
            
            for term in self.audio_search_terms:
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
                return True
            else:
                self.logger.warning("No products found in OpenCart, using enhanced mock data")
                self.existing_products = self._get_enhanced_mock_products()
                self.existing_products_loaded = True
                return True
            
        except Exception as e:
            self.logger.error(f"Error loading existing products: {str(e)}")
            # Fallback to enhanced mock data for testing
            self.logger.info("Using enhanced mock data as fallback")
            self.existing_products = self._get_enhanced_mock_products()
            self.existing_products_loaded = True
            return True
    
    def _get_enhanced_mock_products(self) -> List[Dict[str, Any]]:
        """
        Get enhanced mock products for testing with more audio equipment variety.
        
        Returns:
            List[Dict[str, Any]]: Enhanced mock product data
        """
        return [
            # Denon AV Receivers
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
            },
            {
                'product_id': '6',
                'name': 'Denon AVRX-580BT 5.2 Channel AV Receiver',
                'model': 'AVRX-580BT',
                'sku': 'DENON-AVRX-580BT',
                'price': '7999.00',
                'description': 'Denon AVRX-580BT 5.2 Channel AV Receiver with Bluetooth'
            },
            {
                'product_id': '7',
                'name': 'Denon AVC-X3800H 9.2 Channel AV Processor',
                'model': 'AVC-X3800H',
                'sku': 'DENON-AVC-X3800H',
                'price': '45999.00',
                'description': 'Denon AVC-X3800H 9.2 Channel AV Processor Premium'
            },
            # Professional Audio Equipment
            {
                'product_id': '8',
                'name': 'Shure SM58 Dynamic Microphone',
                'model': 'SM58',
                'sku': 'SHURE-SM58',
                'price': '1899.00',
                'description': 'Shure SM58 Professional Dynamic Vocal Microphone'
            },
            {
                'product_id': '9',
                'name': 'AKG C414 XLS Condenser Microphone',
                'model': 'C414-XLS',
                'sku': 'AKG-C414-XLS',
                'price': '15999.00',
                'description': 'AKG C414 XLS Large Diaphragm Condenser Microphone'
            },
            {
                'product_id': '10',
                'name': 'QSC K12.2 Active Speaker',
                'model': 'K12.2',
                'sku': 'QSC-K12.2',
                'price': '12999.00',
                'description': 'QSC K12.2 2000W 12-inch Powered Speaker'
            },
            # DJ Equipment
            {
                'product_id': '11',
                'name': 'Pioneer CDJ-3000 Professional DJ Player',
                'model': 'CDJ-3000',
                'sku': 'PIONEER-CDJ-3000',
                'price': '35999.00',
                'description': 'Pioneer CDJ-3000 Professional Multi Player'
            },
            {
                'product_id': '12',
                'name': 'Pioneer DJM-900NXS2 DJ Mixer',
                'model': 'DJM-900NXS2',
                'sku': 'PIONEER-DJM-900NXS2',
                'price': '28999.00',
                'description': 'Pioneer DJM-900NXS2 4-Channel Professional DJ Mixer'
            }
        ]
    
    def normalize_text(self, text: str) -> str:
        """
        Enhanced text normalization for audio equipment.
        
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
        
        # Audio equipment specific normalizations
        audio_normalizations = {
            r'\bch\b': 'channel',
            r'\bch\.': 'channel',
            r'\bamp\b': 'amplifier',
            r'\brec\b': 'receiver',
            r'\bspeaker\b': 'speaker',
            r'\bsub\b': 'subwoofer',
            r'\bbt\b': 'bluetooth',
            r'\bwifi\b': 'wifi',
            r'\bhdmi\b': 'hdmi',
            r'\b4k\b': '4k',
            r'\b8k\b': '8k',
            r'\bav\s+receiver\b': 'av receiver',
            r'\bhome\s+theater\b': 'home theater',
            r'\bsurround\s+sound\b': 'surround sound'
        }
        
        for pattern, replacement in audio_normalizations.items():
            text = re.sub(pattern, replacement, text)
        
        # Remove extra whitespace and special characters
        text = re.sub(r'[^\w\s-]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def extract_model_number(self, text: str) -> Optional[str]:
        """
        Enhanced model number extraction for audio equipment.
        
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
                model = match.group(1)
                # Validate model length and format
                if len(model) >= 3 and re.search(r'[A-Z].*\d|^\d.*[A-Z]', model):
                    return model
        
        return None
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Enhanced similarity calculation with audio equipment specific weighting.
        
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
        base_similarity = SequenceMatcher(None, norm_text1, norm_text2).ratio()
        
        # Boost similarity for audio equipment specific terms
        audio_terms = ['receiver', 'amplifier', 'speaker', 'microphone', 'channel', 'dolby', 'dts', 'hdmi']
        common_audio_terms = sum(1 for term in audio_terms if term in norm_text1 and term in norm_text2)
        
        # Apply boost for common audio terms
        if common_audio_terms > 0:
            boost = min(0.1, common_audio_terms * 0.03)  # Max 10% boost
            base_similarity = min(1.0, base_similarity + boost)
        
        return base_similarity
    
    def calculate_confidence_score(self, match_type: MatchType, similarity: float, 
                                 parsed_product: Dict[str, Any], existing_product: Dict[str, Any]) -> float:
        """
        Calculate enhanced confidence score with audio equipment specific factors.
        
        Args:
            match_type: Type of match found
            similarity: Base similarity score
            parsed_product: Parsed product data
            existing_product: Existing product data
            
        Returns:
            float: Enhanced confidence score
        """
        base_confidence = similarity
        
        # Match type bonuses
        match_bonuses = {
            MatchType.EXACT_SKU: 1.0,
            MatchType.EXACT_MODEL: 0.95,
            MatchType.MODEL_EXTRACTED: 0.9,
            MatchType.FUZZY_NAME: similarity,
            MatchType.PARTIAL_MATCH: similarity * 0.8,
            MatchType.NO_MATCH: 0.0
        }
        
        confidence = match_bonuses.get(match_type, similarity)
        
        # Additional confidence factors for audio equipment
        parsed_name = parsed_product.get('name', '').lower()
        existing_name = existing_product.get('name', '').lower()
        
        # Manufacturer consistency bonus
        parsed_manufacturer = parsed_product.get('manufacturer', '').lower()
        if parsed_manufacturer and parsed_manufacturer in existing_name:
            confidence = min(1.0, confidence + 0.05)
        
        # Audio category consistency bonus
        audio_categories = ['receiver', 'amplifier', 'speaker', 'microphone', 'mixer', 'player']
        for category in audio_categories:
            if category in parsed_name and category in existing_name:
                confidence = min(1.0, confidence + 0.03)
                break
        
        # Channel configuration consistency bonus
        parsed_channels = re.search(r'(\d+\.?\d*)\s*ch', parsed_name)
        existing_channels = re.search(r'(\d+\.?\d*)\s*ch', existing_name)
        if parsed_channels and existing_channels and parsed_channels.group(1) == existing_channels.group(1):
            confidence = min(1.0, confidence + 0.05)
        
        return confidence
    
    def find_best_match(self, parsed_product: Dict[str, Any]) -> ProductMatch:
        """
        Find the best match for a parsed product with enhanced audio equipment matching.
        
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
        
        # ENHANCED: Search for specific product model/name if not found in pre-loaded products
        specific_search_products = []
        search_terms = []
        
        # Add specific search terms from the parsed product
        if parsed_model and len(parsed_model.strip()) > 2:
            search_terms.append(parsed_model.strip())
        if parsed_sku and len(parsed_sku.strip()) > 2:
            search_terms.append(parsed_sku.strip())
        
        # Extract model numbers from name for additional searches
        extracted_model = self.extract_model_number(parsed_name)
        if extracted_model and extracted_model not in search_terms:
            search_terms.append(extracted_model)
        
        # Perform specific searches for this product
        for search_term in search_terms:
            try:
                self.logger.info(f"Searching OpenCart for specific term: '{search_term}'")
                products = self.opencart_client.search_products(search_term)
                if products:
                    self.logger.info(f"Found {len(products)} products for '{search_term}'")
                    for product in products:
                        # Avoid duplicates by checking product_id
                        product_id = product.get('product_id')
                        if not any(p.get('product_id') == product_id for p in specific_search_products):
                            specific_search_products.append(product)
                else:
                    self.logger.info(f"No products found for '{search_term}'")
            except Exception as e:
                self.logger.warning(f"Error searching for '{search_term}': {str(e)}")
        
        # Combine pre-loaded products with specific search results
        all_products_to_check = list(self.existing_products)
        for product in specific_search_products:
            # Avoid duplicates
            product_id = product.get('product_id')
            if not any(p.get('product_id') == product_id for p in all_products_to_check):
                all_products_to_check.append(product)
        
        self.logger.info(f"Checking against {len(all_products_to_check)} total products ({len(self.existing_products)} pre-loaded + {len(specific_search_products)} from specific search)")
        
        for existing_product in all_products_to_check:
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
            
            # 3. Enhanced model extraction and comparison
            elif parsed_model or existing_model:
                parsed_extracted = self.extract_model_number(parsed_name) or self.extract_model_number(parsed_model)
                existing_extracted = self.extract_model_number(existing_name) or self.extract_model_number(existing_model)
                
                if parsed_extracted and existing_extracted:
                    if self.normalize_text(parsed_extracted) == self.normalize_text(existing_extracted):
                        match_info['match_type'] = MatchType.MODEL_EXTRACTED
                        match_info['total_score'] = 0.9
                        match_info['scores']['model_extracted'] = 1.0
                        self.logger.debug(f"Extracted model match: {parsed_extracted} == {existing_extracted}")
            
            # 4. Enhanced fuzzy name matching
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
            
            # Calculate enhanced confidence score
            if match_info['total_score'] > 0:
                enhanced_confidence = self.calculate_confidence_score(
                    match_info['match_type'], match_info['total_score'], 
                    parsed_product, existing_product
                )
                match_info['total_score'] = enhanced_confidence
            
            debug_matches.append(match_info)
            
            # Update best match
            if match_info['total_score'] > best_score:
                best_score = match_info['total_score']
                best_match = existing_product
                best_match_type = match_info['match_type']
        
        # Determine confidence level with adjusted thresholds
        if best_score >= 0.85:  # Lowered from 0.9
            confidence_level = MatchConfidence.HIGH
        elif best_score >= 0.65:  # Lowered from 0.7
            confidence_level = MatchConfidence.MEDIUM
        elif best_score >= 0.45:  # Lowered from 0.5
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
        Enhanced price parsing for various formats.
        
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
        Determine what action to take for a product with enhanced logic.
        
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
        
        # If high confidence match found, update (lowered threshold)
        if existing_product and score >= 0.7:  # Lowered from 0.8
            return 'update'
        
        # If medium confidence match, update (lowered threshold)
        if existing_product and score >= 0.5:  # Lowered from 0.6
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
        
        # Check for match quality issues (adjusted thresholds)
        if existing_product:
            if score < 0.7:  # Lowered from 0.8
                issues.append(f'Low match confidence ({score:.1%})')
            
            # Check for significant price differences
            existing_price = self._parse_price(existing_product.get('price', 0))
            if parsed_price and existing_price:
                price_diff_percent = abs(parsed_price - existing_price) / existing_price
                if price_diff_percent > 0.25:  # Increased from 20% to 25%
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
        self.logger.info(f"Starting enhanced comparison of {len(parsed_products)} parsed products")
        
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
