
"""
Store Name Generator for Audico Product Manager.

This module provides GPT-4 powered generation of OpenCart-friendly product names
that follow store conventions and improve product matching accuracy.
"""

import logging
import re
from typing import Dict, Any, Optional, List
from openai import OpenAI
import os

try:
    from audico_product_manager.config import config
    from audico_product_manager.docai_parser import ProductData
except ImportError:
    try:
        from .config import config
        from .docai_parser import ProductData
    except ImportError:
        from config import config
        from docai_parser import ProductData


class StoreNameGenerator:
    """Generates OpenCart-friendly product names using GPT-4."""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize the store name generator.
        
        Args:
            openai_api_key: OpenAI API key (optional, will use config/env if not provided)
        """
        self.logger = logging.getLogger(__name__)
        
        # Initialize OpenAI client
        api_key = openai_api_key or getattr(config, 'openai_api_key', None) or os.getenv('OPENAI_API_KEY')
        if not api_key:
            self.logger.warning("No OpenAI API key provided. Store name generation will be disabled.")
            self.openai_client = None
        else:
            self.openai_client = OpenAI(api_key=api_key)
        
        # Store naming patterns and examples
        self.naming_patterns = {
            'av_receiver': 'Brand Model - X.X Channel AV Receiver Description',
            'amplifier': 'Brand Model - Power Amplifier Description',
            'speaker': 'Brand Model - Speaker Type Description',
            'microphone': 'Brand Model - Microphone Type Description',
            'mixer': 'Brand Model - Channel Mixer Description',
            'player': 'Brand Model - Media Player Description',
            'headphones': 'Brand Model - Headphone Type Description',
            'turntable': 'Brand Model - Turntable Description',
            'controller': 'Brand Model - DJ Controller Description',
            'interface': 'Brand Model - Audio Interface Description'
        }
        
        # Brand mappings for consistency
        self.brand_mappings = {
            'denon': 'Denon',
            'akg': 'AKG',
            'shure': 'Shure',
            'pioneer': 'Pioneer',
            'yamaha': 'Yamaha',
            'sony': 'Sony',
            'jbl': 'JBL',
            'qsc': 'QSC',
            'marantz': 'Marantz',
            'onkyo': 'Onkyo',
            'polk': 'Polk Audio',
            'harman': 'Harman Kardon',
            'sennheiser': 'Sennheiser',
            'audio-technica': 'Audio-Technica',
            'behringer': 'Behringer',
            'mackie': 'Mackie',
            'presonus': 'PreSonus',
            'focusrite': 'Focusrite'
        }
    
    def generate_store_name(self, product_data: ProductData) -> str:
        """
        Generate an OpenCart-friendly store name for a product.
        
        Args:
            product_data: Product data from extraction
            
        Returns:
            str: Generated store-friendly name
        """
        if not self.openai_client:
            self.logger.warning("OpenAI client not available, using fallback naming")
            return self._generate_fallback_name(product_data)
        
        try:
            # Prepare context for GPT-4
            context = self._prepare_context(product_data)
            
            # Generate store name using GPT-4
            store_name = self._call_gpt4_for_naming(context)
            
            if store_name:
                self.logger.info(f"Generated store name: '{store_name}' for product: '{product_data.name}'")
                return store_name
            else:
                self.logger.warning("GPT-4 failed to generate name, using fallback")
                return self._generate_fallback_name(product_data)
                
        except Exception as e:
            self.logger.error(f"Error generating store name: {str(e)}")
            return self._generate_fallback_name(product_data)
    
    def _prepare_context(self, product_data: ProductData) -> Dict[str, Any]:
        """
        Prepare context for GPT-4 name generation.
        
        Args:
            product_data: Product data from extraction
            
        Returns:
            Dict[str, Any]: Context for GPT-4
        """
        # Extract key information
        raw_name = product_data.name or ""
        model = product_data.model or ""
        description = product_data.description or ""
        manufacturer = product_data.manufacturer or ""
        
        # Detect product category
        category = self._detect_product_category(raw_name, description)
        
        # Extract brand from various sources
        brand = self._extract_brand(raw_name, model, manufacturer)
        
        # Extract technical specifications
        specs = self._extract_specifications(raw_name, description)
        
        return {
            'raw_name': raw_name,
            'model': model,
            'description': description,
            'manufacturer': manufacturer,
            'detected_category': category,
            'extracted_brand': brand,
            'specifications': specs,
            'naming_pattern': self.naming_patterns.get(category, 'Brand Model - Product Description')
        }
    
    def _detect_product_category(self, name: str, description: str) -> str:
        """
        Detect product category from name and description.
        
        Args:
            name: Product name
            description: Product description
            
        Returns:
            str: Detected category
        """
        text = f"{name} {description}".lower()
        
        # Category detection patterns
        category_patterns = {
            'av_receiver': [r'av\s+receiver', r'a/v\s+receiver', r'home\s+theater\s+receiver', 
                           r'\d+\.\d+\s+ch', r'channel.*receiver', r'surround.*receiver'],
            'amplifier': [r'amplifier', r'amp\b', r'power\s+amp', r'integrated\s+amp'],
            'speaker': [r'speaker', r'monitor', r'subwoofer', r'woofer', r'tweeter'],
            'microphone': [r'microphone', r'mic\b', r'vocal\s+mic', r'condenser', r'dynamic'],
            'mixer': [r'mixer', r'mixing\s+console', r'dj\s+mixer', r'audio\s+mixer'],
            'player': [r'player', r'cdj', r'media\s+player', r'cd\s+player', r'turntable'],
            'headphones': [r'headphone', r'headset', r'earphone', r'in-ear', r'over-ear'],
            'turntable': [r'turntable', r'record\s+player', r'vinyl', r'deck'],
            'controller': [r'controller', r'dj\s+controller', r'midi\s+controller'],
            'interface': [r'interface', r'audio\s+interface', r'usb\s+interface']
        }
        
        for category, patterns in category_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    return category
        
        return 'general'
    
    def _extract_brand(self, name: str, model: str, manufacturer: str) -> str:
        """
        Extract brand from various sources.
        
        Args:
            name: Product name
            model: Product model
            manufacturer: Manufacturer field
            
        Returns:
            str: Extracted brand
        """
        # Check manufacturer field first
        if manufacturer:
            brand_lower = manufacturer.lower().strip()
            if brand_lower in self.brand_mappings:
                return self.brand_mappings[brand_lower]
            return manufacturer.strip()
        
        # Extract from name or model
        text = f"{name} {model}".lower()
        
        for brand_key, brand_name in self.brand_mappings.items():
            if brand_key in text:
                return brand_name
        
        # Try to extract first word as brand
        words = name.split() if name else []
        if words:
            first_word = words[0].strip()
            if len(first_word) > 2 and first_word.isalpha():
                return first_word.title()
        
        return "Unknown Brand"
    
    def _extract_specifications(self, name: str, description: str) -> Dict[str, str]:
        """
        Extract technical specifications from name and description.
        
        Args:
            name: Product name
            description: Product description
            
        Returns:
            Dict[str, str]: Extracted specifications
        """
        text = f"{name} {description}".lower()
        specs = {}
        
        # Channel configuration
        channel_match = re.search(r'(\d+\.?\d*)\s*ch', text)
        if channel_match:
            specs['channels'] = channel_match.group(1) + ' Channel'
        
        # Power rating
        power_match = re.search(r'(\d+)w', text)
        if power_match:
            specs['power'] = power_match.group(1) + 'W'
        
        # Resolution support
        if '8k' in text:
            specs['resolution'] = '8K'
        elif '4k' in text:
            specs['resolution'] = '4K'
        
        # Connectivity
        if 'bluetooth' in text or 'bt' in text:
            specs['connectivity'] = 'Bluetooth'
        if 'wifi' in text:
            specs['connectivity'] = specs.get('connectivity', '') + ' WiFi'
        if 'hdmi' in text:
            specs['connectivity'] = specs.get('connectivity', '') + ' HDMI'
        
        # Audio formats
        if 'dolby' in text:
            specs['audio_format'] = 'Dolby'
        if 'dts' in text:
            specs['audio_format'] = specs.get('audio_format', '') + ' DTS'
        if 'atmos' in text:
            specs['audio_format'] = specs.get('audio_format', '') + ' Atmos'
        
        return specs
    
    def _call_gpt4_for_naming(self, context: Dict[str, Any]) -> Optional[str]:
        """
        Call GPT-4 to generate store-friendly product name.
        
        Args:
            context: Context for name generation
            
        Returns:
            str: Generated name or None if failed
        """
        try:
            # Prepare examples for few-shot learning
            examples = self._get_naming_examples()
            
            # Create prompt
            prompt = f"""You are an expert at creating product names for an audio equipment online store. Your task is to convert technical product specifications into customer-friendly product names that follow consistent naming patterns.

NAMING PATTERNS:
- AV Receivers: "Brand Model - X.X Channel AV Receiver [Key Features]"
- Amplifiers: "Brand Model - [Power] Amplifier [Type/Features]"
- Speakers: "Brand Model - [Size/Type] Speaker [Features]"
- Microphones: "Brand Model - [Type] Microphone [Features]"
- Other Audio: "Brand Model - [Product Type] [Key Features]"

EXAMPLES:
{examples}

PRODUCT TO NAME:
Raw Name: {context['raw_name']}
Model: {context['model']}
Brand: {context['extracted_brand']}
Category: {context['detected_category']}
Specifications: {context['specifications']}
Description: {context['description']}

REQUIREMENTS:
1. Use the detected brand and model prominently
2. Follow the naming pattern for the product category
3. Include key specifications (channels, power, connectivity)
4. Make it customer-friendly and searchable
5. Keep it concise but descriptive
6. Use proper capitalization and formatting

Generate ONLY the product name, nothing else:"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert product naming specialist for audio equipment stores."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.3
            )
            
            generated_name = response.choices[0].message.content.strip()
            
            # Validate and clean the generated name
            if generated_name and len(generated_name) > 10:
                return self._clean_generated_name(generated_name)
            
            return None
            
        except Exception as e:
            self.logger.error(f"GPT-4 API call failed: {str(e)}")
            return None
    
    def _get_naming_examples(self) -> str:
        """
        Get examples for few-shot learning.
        
        Returns:
            str: Formatted examples
        """
        examples = [
            "Raw: '5.2 Ch. 130W 8K AV Receiver with Bluetooth' Model: 'AVRX-580BT' → 'Denon AVR-X580BT - 5.2 Channel AV Receiver 130W 8K Bluetooth'",
            "Raw: 'SM58 Dynamic Vocal Microphone' Model: 'SM58' → 'Shure SM58 - Dynamic Vocal Microphone'",
            "Raw: 'K12.2 2000W 12-inch Powered Speaker' Model: 'K12.2' → 'QSC K12.2 - 2000W 12-inch Powered Speaker'",
            "Raw: 'CDJ-3000 Professional Multi Player' Model: 'CDJ-3000' → 'Pioneer CDJ-3000 - Professional DJ Media Player'",
            "Raw: 'C414 XLS Large Diaphragm Condenser' Model: 'C414-XLS' → 'AKG C414 XLS - Large Diaphragm Condenser Microphone'"
        ]
        return "\n".join(examples)
    
    def _clean_generated_name(self, name: str) -> str:
        """
        Clean and validate generated name.
        
        Args:
            name: Generated name to clean
            
        Returns:
            str: Cleaned name
        """
        # Remove quotes and extra whitespace
        name = name.strip().strip('"\'')
        
        # Ensure proper capitalization
        name = re.sub(r'\s+', ' ', name)
        
        # Limit length
        if len(name) > 150:
            name = name[:147] + "..."
        
        return name
    
    def _generate_fallback_name(self, product_data: ProductData) -> str:
        """
        Generate fallback name when GPT-4 is not available.
        
        Args:
            product_data: Product data
            
        Returns:
            str: Fallback name
        """
        try:
            # Extract basic components
            brand = self._extract_brand(product_data.name or "", product_data.model or "", product_data.manufacturer or "")
            model = product_data.model or ""
            category = self._detect_product_category(product_data.name or "", product_data.description or "")
            specs = self._extract_specifications(product_data.name or "", product_data.description or "")
            
            # Build fallback name
            parts = []
            
            if brand and brand != "Unknown Brand":
                parts.append(brand)
            
            if model:
                parts.append(model)
            
            # Add category-specific description
            if category == 'av_receiver':
                if specs.get('channels'):
                    parts.append(f"- {specs['channels']} AV Receiver")
                else:
                    parts.append("- AV Receiver")
            elif category == 'amplifier':
                parts.append("- Amplifier")
            elif category == 'speaker':
                parts.append("- Speaker")
            elif category == 'microphone':
                parts.append("- Microphone")
            else:
                parts.append("- Audio Equipment")
            
            # Add key specs
            if specs.get('power'):
                parts.append(specs['power'])
            if specs.get('resolution'):
                parts.append(specs['resolution'])
            if specs.get('connectivity'):
                parts.append(specs['connectivity'])
            
            fallback_name = " ".join(parts)
            
            # Fallback to original name if construction fails
            if len(fallback_name.strip()) < 10:
                fallback_name = product_data.name or f"{brand} {model}" or "Unknown Product"
            
            self.logger.info(f"Generated fallback name: '{fallback_name}'")
            return fallback_name
            
        except Exception as e:
            self.logger.error(f"Error generating fallback name: {str(e)}")
            return product_data.name or "Unknown Product"
    
    def batch_generate_store_names(self, products_data: List[ProductData]) -> List[ProductData]:
        """
        Generate store names for a batch of products.
        
        Args:
            products_data: List of product data
            
        Returns:
            List[ProductData]: Products with generated store names
        """
        self.logger.info(f"Generating store names for {len(products_data)} products")
        
        for product_data in products_data:
            try:
                store_name = self.generate_store_name(product_data)
                product_data.online_store_name = store_name
                self.logger.debug(f"Generated store name for {product_data.model}: {store_name}")
            except Exception as e:
                self.logger.error(f"Error generating store name for {product_data.model}: {str(e)}")
                product_data.online_store_name = product_data.name or "Unknown Product"
        
        return products_data
    
    def test_generation(self) -> bool:
        """
        Test the store name generation functionality.
        
        Returns:
            bool: True if test successful
        """
        try:
            # Create test product data
            test_product = ProductData(
                name="5.2 Ch. 130W 8K AV Receiver with Bluetooth",
                model="AVRX-580BT",
                price="7999.00",
                description="Denon AVRX-580BT 5.2 Channel AV Receiver with Bluetooth connectivity",
                manufacturer="Denon"
            )
            
            # Generate store name
            store_name = self.generate_store_name(test_product)
            
            self.logger.info(f"Test generation successful: '{store_name}'")
            return True
            
        except Exception as e:
            self.logger.error(f"Test generation failed: {str(e)}")
            return False
