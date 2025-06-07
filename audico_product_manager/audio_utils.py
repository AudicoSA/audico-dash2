#!/usr/bin/env python3
"""
Audio Equipment Utilities for Enhanced Product Name Processing.
Provides domain-specific patterns, brand recognition, and text normalization.
"""

import re
from typing import Dict, List, Optional, Set

# Comprehensive audio equipment brand database
AUDIO_BRANDS = {
    'denon': ['denon'],
    'marantz': ['marantz'],
    'akg': ['akg'],
    'polk': ['polk', 'polk audio'],
    'qsc': ['qsc'],
    'shure': ['shure'],
    'yamaha': ['yamaha'],
    'pioneer': ['pioneer', 'pioneer dj'],
    'jbl': ['jbl'],
    'bose': ['bose'],
    'sennheiser': ['sennheiser'],
    'audio_technica': ['audio-technica', 'audio technica'],
    'mackie': ['mackie'],
    'behringer': ['behringer'],
    'focal': ['focal'],
    'klipsch': ['klipsch'],
    'kef': ['kef'],
    'bowers_wilkins': ['b&w', 'bowers & wilkins', 'bowers and wilkins'],
    'martin_logan': ['martin logan', 'martinlogan'],
    'definitive': ['definitive technology', 'definitive'],
    'svs': ['svs'],
    'rel': ['rel'],
    'paradigm': ['paradigm'],
    'monitor_audio': ['monitor audio'],
    'wharfedale': ['wharfedale'],
    'elac': ['elac'],
    'emotiva': ['emotiva'],
    'anthem': ['anthem'],
    'arcam': ['arcam'],
    'cambridge': ['cambridge audio', 'cambridge'],
    'nad': ['nad'],
    'rotel': ['rotel'],
    'onkyo': ['onkyo'],
    'integra': ['integra'],
    'sony': ['sony'],
    'lg': ['lg'],
    'samsung': ['samsung']
}

# Enhanced model extraction patterns for audio equipment
AUDIO_MODEL_PATTERNS = [
    # AVR patterns (Denon, Marantz, etc.) - Most specific first
    r'\b(AVR[-_]?X\d{3,4}[A-Z]*)\b',      # AVR-X1800H, AVRX580BT
    r'\b(AVR[-_]?S\d{3,4}[A-Z]*)\b',      # AVR-S540H, AVRS750H
    r'\b(AVR[-_]?\d{3,4}[A-Z]*)\b',       # AVR1800, AVR540
    r'\b(SR\d{4}[A-Z]*)\b',               # SR5015, SR6015 (Marantz)
    r'\b(NR\d{4}[A-Z]*)\b',               # NR1711, NR1510 (Marantz)
    
    # Microphone patterns (Shure, AKG, etc.)
    r'\b(SM\d{2,3}[A-Z]*)\b',             # SM58, SM57, SM150PRO
    r'\b(BETA\d{2,3}[A-Z]*)\b',           # BETA58A, BETA87A
    r'\b(KSM\d{2,3}[A-Z]*)\b',            # KSM32, KSM44A
    r'\b(C\d{3,4}[A-Z]*)\b',              # C414, C451B (AKG)
    r'\b(D\d{2,3}[A-Z]*)\b',              # D5, D112 (AKG)
    r'\b(AT\d{4}[A-Z]*)\b',               # AT4040, AT2020 (Audio-Technica)
    
    # Speaker patterns (QSC, JBL, etc.)
    r'\b(K\d{1,2}\.?\d*[A-Z]*)\b',        # K12.2, K8.2, K10, KW181
    r'\b(KW\d{3}[A-Z]*)\b',               # KW181, KW153 (QSC)
    r'\b(CP\d{1,2}[A-Z]*)\b',             # CP12, CP8 (QSC)
    r'\b(EON\d{3}[A-Z]*)\b',              # EON615, EON612 (JBL)
    r'\b(PRX\d{3}[A-Z]*)\b',              # PRX815, PRX412M (JBL)
    r'\b(SRX\d{3}[A-Z]*)\b',              # SRX815P, SRX828SP (JBL)
    r'\b(VRX\d{3}[A-Z]*)\b',              # VRX932LA, VRX915M (JBL)
    
    # Amplifier patterns
    r'\b(PL[AI]?\d{3,4}[A-Z]*)\b',        # PLA4.2, PLI4800 (QSC)
    r'\b(GX\d{1}[A-Z]*)\b',               # GX3, GX5, GX7 (QSC)
    r'\b(DCA\d{4}[A-Z]*)\b',              # DCA1222, DCA1824 (QSC)
    r'\b(CX\d{3}[A-Z]*)\b',               # CX254, CX404 (QSC)
    
    # Mixer patterns
    r'\b(MG\d{1,2}[A-Z]*)\b',             # MG10XU, MG16XU (Yamaha)
    r'\b(X32[A-Z]*)\b',                   # X32, X32RACK (Behringer)
    r'\b(M32[A-Z]*)\b',                   # M32, M32R (Midas)
    r'\b(QU[-_]?\d{2}[A-Z]*)\b',          # QU-16, QU-24 (Allen & Heath)
    
    # DJ Equipment patterns
    r'\b(CDJ[-_]?\d{4}[A-Z]*)\b',         # CDJ-3000, CDJ2000NXS2 (Pioneer)
    r'\b(DJM[-_]?\d{3,4}[A-Z]*)\b',       # DJM-900NXS2, DJM750MK2 (Pioneer)
    r'\b(PLX[-_]?\d{4}[A-Z]*)\b',         # PLX-1000, PLX500 (Pioneer)
    
    # Special patterns with complex separators
    r'\b([A-Z]{2,4}[-_][A-Z0-9]{2,}[-_][A-Z0-9]{2,})\b',  # LUM-820-IP-BM style
    r'\b([A-Z]{3,}_[A-Z0-9]{3,})\b',      # Underscore patterns
    
    # General alphanumeric patterns (less specific, lower priority)
    r'\b([A-Z]{2,4}[-_]?\d{3,4}[-_]?[A-Z]*)\b',  # General pattern
    r'\b([A-Z]+\d{2,4}[A-Z]*)\b',         # Compact pattern
]

# Audio equipment synonyms and normalizations
AUDIO_SYNONYMS = {
    'receiver': ['receiver', 'avr', 'av receiver', 'amplifier receiver'],
    'amplifier': ['amplifier', 'amp', 'power amp', 'power amplifier'],
    'speaker': ['speaker', 'loudspeaker', 'monitor', 'studio monitor'],
    'subwoofer': ['subwoofer', 'sub', 'bass speaker', 'woofer'],
    'microphone': ['microphone', 'mic', 'vocal mic', 'instrument mic'],
    'mixer': ['mixer', 'mixing console', 'audio mixer', 'sound mixer'],
    'headphones': ['headphones', 'headphone', 'headset', 'cans'],
    'turntable': ['turntable', 'record player', 'dj turntable'],
    'dj': ['dj', 'disc jockey', 'club', 'professional'],
    'wireless': ['wireless', 'wi-fi', 'wifi', 'bluetooth'],
    'channel': ['channel', 'ch', 'ch.'],
    'watts': ['watts', 'w', 'watt', 'power'],
    '8k': ['8k', '8k uhd', '8k ultra hd'],
    '4k': ['4k', '4k uhd', '4k ultra hd'],
    'dolby': ['dolby', 'dolby atmos', 'dolby digital'],
    'dts': ['dts', 'dts:x', 'dts-hd'],
    'heos': ['heos', 'heos built-in'],
    'airplay': ['airplay', 'airplay 2', 'apple airplay'],
    'home theater': ['home theater', 'home theatre', 'surround sound']
}

# Product type classification patterns
PRODUCT_TYPE_PATTERNS = {
    'AV Receiver': [r'receiver', r'avr', r'av receiver'],
    'Amplifier': [r'amplifier', r'amp', r'power amp'],
    'Speaker': [r'speaker', r'loudspeaker', r'monitor'],
    'Subwoofer': [r'subwoofer', r'sub', r'bass'],
    'Microphone': [r'microphone', r'mic', r'vocal'],
    'Mixer': [r'mixer', r'mixing console', r'console'],
    'Headphones': [r'headphones', r'headphone', r'headset'],
    'Turntable': [r'turntable', r'record player'],
    'DJ Equipment': [r'dj', r'cdj', r'djm'],
    'Cable': [r'cable', r'xlr', r'trs', r'rca'],
    'Stand': [r'stand', r'mount', r'bracket']
}

def extract_audio_model(text: str) -> Optional[str]:
    """Extract audio equipment model using enhanced patterns."""
    if not text:
        return None
    
    # Clean and normalize text
    text = text.upper().strip()
    
    # Try each pattern in order of specificity
    for pattern in AUDIO_MODEL_PATTERNS:
        match = re.search(pattern, text)
        if match:
            model = match.group(1)
            # Clean up the model
            model = re.sub(r'[-_]+', '-', model)  # Normalize separators
            return model
    
    return None

def identify_audio_brand(text: str) -> Optional[str]:
    """Identify audio equipment brand from text."""
    if not text:
        return None
    
    text_lower = text.lower()
    
    for brand_key, brand_variants in AUDIO_BRANDS.items():
        for variant in brand_variants:
            if variant in text_lower:
                # Return proper case brand name
                return brand_key.replace('_', ' ').title()
    
    return None

def classify_product_type(text: str) -> Optional[str]:
    """Classify the product type based on text content."""
    if not text:
        return None
    
    text_lower = text.lower()
    
    for product_type, patterns in PRODUCT_TYPE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return product_type
    
    return None

def normalize_audio_text(text: str) -> str:
    """Normalize audio equipment text with domain-specific rules."""
    if not text:
        return ""
    
    # Convert to lowercase for processing
    text = text.lower()
    
    # Normalize common audio terms (avoid repeated replacements)
    for canonical, synonyms in AUDIO_SYNONYMS.items():
        for synonym in synonyms:
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(synonym) + r'\b'
            if synonym != canonical:  # Only replace if different
                text = re.sub(pattern, canonical, text)
    
    # Normalize channel notation
    text = re.sub(r'(\d+)\.(\d+)\s*ch\.?', r'\1.\2 channel', text)
    text = re.sub(r'(\d+)\s*ch\.?', r'\1 channel', text)
    
    # Normalize power notation
    text = re.sub(r'(\d+)\s*w\b', r'\1 watts', text)
    
    # Clean up extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def extract_audio_features(text: str) -> Dict[str, str]:
    """Extract key audio features from product text."""
    features = {}
    
    if not text:
        return features
    
    text_lower = text.lower()
    
    # Extract channel configuration
    channel_match = re.search(r'(\d+)\.?(\d*)\s*ch', text_lower)
    if channel_match:
        main_channels = channel_match.group(1)
        sub_channels = channel_match.group(2) or '0'
        if sub_channels:
            features['channels'] = f"{main_channels}.{sub_channels}"
        else:
            features['channels'] = main_channels
    
    # Extract power rating
    power_match = re.search(r'(\d+)\s*w(?:att)?s?', text_lower)
    if power_match:
        features['power'] = f"{power_match.group(1)}W"
    
    # Extract video capabilities
    if re.search(r'8k', text_lower):
        features['video'] = "8K"
    elif re.search(r'4k', text_lower):
        features['video'] = "4K"
    
    # Extract connectivity features
    connectivity = []
    if re.search(r'bluetooth', text_lower):
        connectivity.append("Bluetooth")
    if re.search(r'wi-?fi', text_lower):
        connectivity.append("Wi-Fi")
    if re.search(r'heos', text_lower):
        connectivity.append("HEOS")
    if re.search(r'airplay', text_lower):
        connectivity.append("AirPlay")
    
    if connectivity:
        features['connectivity'] = connectivity
    
    return features

def create_website_ready_name(name: str, model: str, brand: str = None) -> str:
    """Create a website-ready product name optimized for search and sales."""
    if not name or not model:
        return name or ""
    
    # Extract features
    features = extract_audio_features(name)
    
    # Identify brand if not provided
    if not brand:
        brand = identify_audio_brand(name)
    
    # Classify product type
    product_type = classify_product_type(name)
    
    # Build the website-ready name
    parts = []
    
    # 1. Brand + Model
    if brand:
        parts.append(brand)
    parts.append(model)
    
    # 2. Channel configuration
    if 'channels' in features:
        if '.' in features['channels']:
            parts.append(f"{features['channels']}-Channel")
        else:
            parts.append(f"{features['channels']}-Channel")
    
    # 3. Product type
    if product_type:
        parts.append(product_type)
    
    # 4. Connectivity features with "with"
    if 'connectivity' in features:
        connectivity_list = features['connectivity']
        if len(connectivity_list) == 1:
            parts.append(f"with {connectivity_list[0]}")
        else:
            parts.append(f"with {' & '.join(connectivity_list)}")
    
    # 5. Technical specs with "–" separator
    tech_specs = []
    if 'power' in features:
        tech_specs.append(features['power'])
    if 'video' in features:
        tech_specs.append(features['video'])
    
    if tech_specs:
        parts.append(f"– {' '.join(tech_specs)}")
    
    # 6. Descriptive category suffix
    if product_type == "AV Receiver":
        parts.append("Home Theater Power")
    elif product_type in ["Speaker", "Subwoofer"]:
        parts.append("Professional Audio")
    elif product_type == "Microphone":
        parts.append("Professional Microphone")
    elif product_type == "Mixer":
        parts.append("Audio Mixing Console")
    elif product_type == "DJ Equipment":
        parts.append("Professional DJ Equipment")
    elif product_type == "Amplifier":
        parts.append("Audio Amplifier")
    
    return " ".join(parts)

def enhance_product_data(product_dict: Dict) -> Dict:
    """Enhance product data with audio-specific improvements."""
    enhanced = product_dict.copy()
    
    name = enhanced.get('name', '')
    model = enhanced.get('model', '') or enhanced.get('sku', '')
    
    # Extract model if not present
    if not model and name:
        extracted_model = extract_audio_model(name)
        if extracted_model:
            enhanced['model'] = extracted_model
            enhanced['sku'] = extracted_model
    
    # Identify brand if not present
    if not enhanced.get('manufacturer') and name:
        brand = identify_audio_brand(name)
        if brand:
            enhanced['manufacturer'] = brand
    
    # Classify product type if not present
    if not enhanced.get('category') and name:
        product_type = classify_product_type(name)
        if product_type:
            enhanced['category'] = product_type
    
    # Create website-ready name
    if name and (model or enhanced.get('model')):
        website_name = create_website_ready_name(
            name, 
            model or enhanced.get('model'), 
            enhanced.get('manufacturer')
        )
        enhanced['website_ready_name'] = website_name
    
    # Extract and add features
    features = extract_audio_features(name)
    if features:
        if 'specifications' not in enhanced:
            enhanced['specifications'] = {}
        enhanced['specifications'].update(features)
    
    return enhanced
