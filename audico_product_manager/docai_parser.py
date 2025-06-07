
import logging
import re
import os
import json
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from google.cloud import documentai
import PyPDF2
import io

from openai import OpenAI

try:
    from audico_product_manager.config import config
except ImportError:
    try:
        from .config import config
    except ImportError:
        try:
            from config import config
        except ImportError:
            class FallbackConfig:
                google_cloud_project_id = os.getenv('GOOGLE_CLOUD_PROJECT_ID', 'your-project-id')
                google_cloud_location = os.getenv('GOOGLE_CLOUD_LOCATION', 'us')
                google_cloud_processor_id = os.getenv('GOOGLE_CLOUD_PROCESSOR_ID', 'mock-processor-for-demo')
                openai_api_key = os.getenv('OPENAI_API_KEY')
                openai_client = None
                default_manufacturer = os.getenv('DEFAULT_MANUFACTURER', 'Audico')
            config = FallbackConfig()

@dataclass
class ProductData:
    name: str
    model: str
    price: str
    description: Optional[str] = None
    category: Optional[str] = None
    manufacturer: Optional[str] = None
    specifications: Optional[Dict[str, str]] = None
    confidence: Optional[float] = None
    online_store_name: Optional[str] = None

class DocumentAIParser:
    def __init__(self, project_id: Optional[str] = None, location: Optional[str] = None, 
                 processor_id: Optional[str] = None, openai_api_key: Optional[str] = None):
        self.project_id = project_id or getattr(config, 'google_cloud_project_id', os.getenv('GOOGLE_CLOUD_PROJECT_ID', 'your-project-id'))
        self.location = location or getattr(config, 'google_cloud_location', os.getenv('GOOGLE_CLOUD_LOCATION', 'us'))
        self.processor_id = processor_id or getattr(config, 'google_cloud_processor_id', os.getenv('GOOGLE_CLOUD_PROCESSOR_ID', 'mock-processor-for-demo'))
        self.logger = logging.getLogger(__name__)
        self.openai_client = None
        self._initialize_openai_client(openai_api_key)
        self.documentai_client = None
        self._initialize_documentai_client()
        
        # Enhanced model extraction patterns for audio equipment
        self.denon_model_patterns = [
            # Denon AVR patterns: AVRX-580BT, AVR-X1800H, AVC-X3800H
            r'\b(AVR[X]?[-_]?[A-Z]?\d{3,4}[A-Z]*[BT]*)\b',
            r'\b(AVC[-_][A-Z]?\d{3,4}[A-Z]*)\b',
            # General audio equipment patterns
            r'\b([A-Z]{2,4}[-_]\d{3,4}[A-Z]*)\b',
            r'\b([A-Z]{3,}\d{3,}[A-Z]*)\b',
            # Professional audio patterns
            r'\b([A-Z]+\d+[A-Z]*[-_]?[A-Z]*)\b',
            # DJ/Pro equipment patterns
            r'\b([A-Z]{2,}[-_]?\d{2,}[-_]?[A-Z]*)\b'
        ]
        
        # Price extraction patterns for old vs new RRP
        self.price_patterns = [
            # New RRP / Old RRP patterns
            r'(?:New\s+RRP|RRP)\s*[:\-]?\s*R?\s*([0-9,]+\.?\d*)',
            r'(?:Old\s+RRP|Previous\s+RRP)\s*[:\-]?\s*R?\s*([0-9,]+\.?\d*)',
            # Standard price patterns
            r'R\s*([0-9,]+\.?\d*)',
            r'\$\s*([0-9,]+\.?\d*)',
            r'(?:Price|Cost)\s*[:\-]?\s*R?\s*([0-9,]+\.?\d*)',
            # Table price patterns
            r'\b([0-9,]+\.?\d*)\s*(?:ZAR|R)\b',
            r'\b([0-9,]+\.?\d*)\s*$'  # Price at end of line
        ]

    def _initialize_openai_client(self, api_key: Optional[str] = None):
        try:
            openai_key = (
                api_key or 
                getattr(config, 'openai_api_key', None) or 
                os.getenv('OPENAI_API_KEY')
            )
            if openai_key:
                self.openai_client = OpenAI(api_key=openai_key)
                self.logger.info("✅ OpenAI client initialized successfully")
                print("🤖 OpenAI GPT-4 integration enabled for intelligent document parsing")
            else:
                self.logger.warning("⚠️ OpenAI API key not found. OpenAI parsing will be disabled.")
                print("⚠️ OpenAI API key not found. Will use fallback parsing methods.")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize OpenAI client: {str(e)}")
            print(f"❌ OpenAI initialization failed: {str(e)}")
            self.openai_client = None

    def _initialize_documentai_client(self):
        try:
            self.documentai_client = documentai.DocumentProcessorServiceClient()
            self.logger.info("✅ Document AI client initialized successfully")
            print("📄 Google Cloud Document AI integration enabled")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Document AI client: {str(e)}")
            print(f"⚠️ Document AI unavailable: {str(e)}")

    def _get_processor_name(self) -> str:
        return f"projects/{self.project_id}/locations/{self.location}/processors/{self.processor_id}"

    def extract_denon_model(self, text: str) -> Optional[str]:
        """Extract Denon model numbers using enhanced patterns."""
        if not text:
            return None
        
        # Clean text for better matching
        clean_text = re.sub(r'\s+', ' ', text.upper())
        
        for pattern in self.denon_model_patterns:
            matches = re.findall(pattern, clean_text)
            if matches:
                # Return the first valid match
                for match in matches:
                    if len(match) >= 4:  # Minimum model length
                        return match.strip()
        
        return None

    def extract_price_with_context(self, text: str) -> Dict[str, Optional[str]]:
        """Extract prices with context (new RRP vs old RRP)."""
        prices = {
            'new_rrp': None,
            'old_rrp': None,
            'current_price': None
        }
        
        # Look for new RRP
        new_rrp_pattern = r'(?:New\s+RRP|Current\s+RRP|RRP)\s*[:\-]?\s*R?\s*([0-9,]+\.?\d*)'
        new_match = re.search(new_rrp_pattern, text, re.IGNORECASE)
        if new_match:
            prices['new_rrp'] = new_match.group(1).replace(',', '')
        
        # Look for old RRP
        old_rrp_pattern = r'(?:Old\s+RRP|Previous\s+RRP|Was)\s*[:\-]?\s*R?\s*([0-9,]+\.?\d*)'
        old_match = re.search(old_rrp_pattern, text, re.IGNORECASE)
        if old_match:
            prices['old_rrp'] = old_match.group(1).replace(',', '')
        
        # Look for general price if no specific RRP found
        if not prices['new_rrp'] and not prices['old_rrp']:
            for pattern in self.price_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    prices['current_price'] = match.group(1).replace(',', '')
                    break
        
        return prices

    def normalize_product_name(self, name: str, model: str = None, manufacturer: str = None) -> str:
        """Normalize product names for audio equipment."""
        if not name:
            return ""
        
        normalized = name.strip()
        
        # Audio equipment specific normalizations
        audio_normalizations = {
            r'\bCh\b': 'Channel',
            r'\bCh\.': 'Channel',
            r'\bAmp\b': 'Amplifier',
            r'\bRec\b': 'Receiver',
            r'\bSpeaker\b': 'Speaker',
            r'\bSub\b': 'Subwoofer',
            r'\bBT\b': 'Bluetooth',
            r'\bWiFi\b': 'Wi-Fi',
            r'\bHDMI\b': 'HDMI',
            r'\b4K\b': '4K',
            r'\b8K\b': '8K',
            r'\bDolby\s+Atmos\b': 'Dolby Atmos',
            r'\bDTS\b': 'DTS',
            r'\bAV\s+Receiver\b': 'AV Receiver',
            r'\bHome\s+Theater\b': 'Home Theater',
            r'\bSurround\s+Sound\b': 'Surround Sound'
        }
        
        for pattern, replacement in audio_normalizations.items():
            normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
        
        # Remove duplicate manufacturer/model if already in name
        if manufacturer and normalized.lower().startswith(manufacturer.lower()):
            normalized = normalized[len(manufacturer):].strip()
        
        if model and normalized.lower().startswith(model.lower()):
            normalized = normalized[len(model):].strip()
        
        # Clean up extra whitespace and punctuation
        normalized = re.sub(r'\s+', ' ', normalized)
        normalized = re.sub(r'^[-\s]+|[-\s]+$', '', normalized)
        
        return normalized.strip()

    def parse_document(self, document_content: bytes, mime_type: str) -> List[ProductData]:
        try:
            print(f"\n🔍 Starting enhanced document parsing (MIME type: {mime_type})")
            raw_text = self._extract_raw_text(document_content, mime_type)
            if not raw_text or len(raw_text.strip()) < 50:
                self.logger.warning("Insufficient text extracted from document")
                print("⚠️ Insufficient text content found in document")
                return []
            print(f"📝 Extracted {len(raw_text)} characters of text from document")
            
            if self.openai_client:
                try:
                    print("🤖 Attempting OpenAI GPT-4 intelligent parsing...")
                    products = self._parse_with_gpt4(raw_text)
                    if products:
                        self.logger.info(f"Successfully extracted {len(products)} products using OpenAI GPT-4")
                        print(f"✅ Enhanced OpenAI GPT-4 successfully extracted {len(products)} products")
                        return products
                except Exception as e:
                    self.logger.error(f"OpenAI parsing failed: {str(e)}")
            
            if self.documentai_client and self.processor_id != 'mock-processor-for-demo':
                try:
                    print("📄 Attempting Google Cloud Document AI parsing...")
                    products = self._parse_with_documentai(document_content, mime_type)
                    if products:
                        print(f"✅ Document AI successfully extracted {len(products)} products")
                        return products
                except Exception as e:
                    self.logger.error(f"Document AI parsing failed: {str(e)}")
            
            print("🔧 Using enhanced fallback regex-based parsing...")
            products = self._parse_text_fallback_enhanced(raw_text)
            if products:
                print(f"✅ Enhanced regex fallback successfully extracted {len(products)} products")
            else:
                print("❌ No products could be extracted using any method")
            return products
        except Exception as e:
            self.logger.error(f"Error parsing document: {str(e)}")
            print(f"❌ Document parsing error: {str(e)}")
            return []

    def _extract_raw_text(self, document_content: bytes, mime_type: str) -> str:
        try:
            if mime_type == 'application/pdf':
                return self._extract_pdf_text(document_content)
            elif mime_type.startswith('text/'):
                return document_content.decode('utf-8')
            else:
                self.logger.warning(f"Unsupported mime type: {mime_type}")
                return ""
        except Exception as e:
            self.logger.error(f"Error extracting raw text: {str(e)}")
            return ""

    def _extract_pdf_text(self, pdf_content: bytes) -> str:
        try:
            pdf_file = io.BytesIO(pdf_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            full_text = ""
            for page in pdf_reader.pages:
                full_text += page.extract_text() + "\n"
            self.logger.info(f"Extracted {len(full_text)} characters from PDF")
            return full_text
        except Exception as e:
            self.logger.error(f"Error extracting PDF text: {str(e)}")
            return ""

    def _generate_online_store_name_ai(self, name: str, model: str, manufacturer: Optional[str]) -> Optional[str]:
        """Use OpenAI to generate a concise store-friendly name."""
        if not self.openai_client:
            return None

        try:
            prompt = (
                "Create a short, SEO-friendly product name for an online audio equipment store. "
                "Start with the manufacturer and model followed by a brief descriptor. "
                "Limit to about 12 words. Focus on audio/AV equipment terminology.\n"
                f"Manufacturer: {manufacturer}\nModel: {model}\nDescription: {name}"
            )
            response = self.openai_client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": "You are a product naming assistant for audio equipment."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=32,
            )
            ai_name = response.choices[0].message.content.strip()
            return ai_name
        except Exception as e:
            self.logger.warning(f"AI name generation failed: {str(e)}")
            return None

    def _make_online_store_name(self, name: str, model: str, manufacturer: Optional[str]) -> str:
        """Construct a clean, searchable product name for the online store."""
        # First try using OpenAI for a polished name
        ai_name = self._generate_online_store_name_ai(name, model, manufacturer)
        if ai_name:
            return ai_name

        # Normalize the base name
        base = self.normalize_product_name(name, model, manufacturer)
        
        # Build the final name
        parts = [p.strip() for p in [manufacturer, model, base] if p]
        store_name = " ".join(parts)
        return store_name

    def _price_to_rands(self, price: str) -> str:
        price = re.sub(r'[\$£€]', '', price).strip()
        price = price.replace(',', '')
        try:
            if price:
                amount = float(price)
                return f"R{amount:,.0f}" if amount.is_integer() else f"R{amount:,.2f}"
        except Exception:
            if not price.startswith('R'):
                return f"R{price}"
        if not price.startswith('R'):
            return f"R{price}"
        return price

    def _parse_with_gpt4(self, raw_text: str) -> List[ProductData]:
        try:
            prompt = self._create_enhanced_gpt4_prompt(raw_text)
            response = self._call_openai_with_retries(prompt)
            if not response:
                return []
            products_data = self._parse_gpt4_response(response)
            products = []
            for product_dict in products_data:
                try:
                    sku_value = product_dict.get('sku') or product_dict.get('model', '')
                    manufacturer = product_dict.get('manufacturer') or config.default_manufacturer
                    
                    # Enhanced model extraction
                    if not sku_value:
                        sku_value = self.extract_denon_model(product_dict.get('name', ''))
                    
                    product = ProductData(
                        name=self.normalize_product_name(product_dict.get('name', ''), sku_value, manufacturer),
                        model=sku_value,
                        price=self._price_to_rands(str(product_dict.get('price', '0.00'))),
                        description=product_dict.get('description'),
                        category=product_dict.get('category'),
                        manufacturer=manufacturer,
                        specifications=product_dict.get('specifications'),
                        confidence=product_dict.get('confidence', 0.9),
                        online_store_name=self._make_online_store_name(product_dict.get('name', ''), sku_value, manufacturer)
                    )
                    if product.name and product.model:
                        products.append(product)
                except Exception as e:
                    self.logger.warning(f"Error creating product from GPT-4 response: {str(e)}")
            return products
        except Exception as e:
            self.logger.error(f"Error in GPT-4 parsing: {str(e)}")
            return []

    def _create_enhanced_gpt4_prompt(self, raw_text: str) -> str:
        prompt = f"""
You are an expert at extracting structured product information from audio equipment price lists, product catalogs, and technical documents. Your task is to identify and extract ALL audio/AV products with their complete details.

CRITICAL REQUIREMENTS:
1. Extract EVERY audio/AV product found in the document - do not skip any items
2. Each product MUST have both a name and SKU/model number to be included
3. Focus on audio equipment: receivers, amplifiers, speakers, DJ equipment, microphones, etc.
4. SKU codes for audio equipment typically follow patterns like: AVR-X1800H, AVRX-580BT, AVC-X3800H, SM58, QSC-K12.2, etc.
5. Handle price variations: "New RRP", "Old RRP", "Was", "Now" pricing
6. Prices must be in clean numeric format (e.g., "299.99" not "$ 299 . 99")
7. Look for products in tables, lists, paragraphs, and any structured data

AUDIO EQUIPMENT SPECIFIC PATTERNS:
- Denon models: AVR-X1800H, AVRX-580BT, AVC-X3800H
- Channel configurations: 5.1, 7.2, 9.2 Channel
- Audio features: Dolby Atmos, DTS, HDMI, 4K, 8K, Bluetooth
- Product types: AV Receiver, Amplifier, Speaker, Subwoofer, Microphone

EXTRACTION FIELDS (return as JSON array):
- "sku": Product SKU/model code (string, REQUIRED)
- "name": Full product name (string, REQUIRED)
- "description": Detailed product description (string)
- "price": Numeric price value - prefer "New RRP" over "Old RRP" (string)
- "category": Product type (e.g., "AV Receiver", "Speaker") (string)
- "manufacturer": Brand/manufacturer name (e.g., "Denon", "AKG") (string)
- "specifications": Technical specs as key-value pairs (object)
- "confidence": Extraction confidence 0.0-1.0 (float)

RETURN FORMAT: Valid JSON array only, no explanations or additional text.

TEXT TO PROCESS:
{raw_text[:4000]}"""
        return prompt

    def _call_openai_with_retries(self, prompt: str, max_retries: int = 3) -> Optional[str]:
        for attempt in range(max_retries):
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert data extraction assistant specializing in audio equipment. Always return valid JSON."
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    temperature=0.1,
                    max_tokens=4000,
                    response_format={"type": "json_object"}
                )
                return response.choices[0].message.content
            except Exception as e:
                self.logger.warning(f"OpenAI API call attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
        return None

    def _parse_gpt4_response(self, response_content: str) -> List[Dict[str, Any]]:
        try:
            data = json.loads(response_content)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                if 'products' in data:
                    return data['products']
                elif 'items' in data:
                    return data['items']
                else:
                    return [data]
            else:
                return []
        except json.JSONDecodeError:
            return []

    def _parse_with_documentai(self, document_content: bytes, mime_type: str) -> List[ProductData]:
        request = documentai.ProcessRequest(
            name=self._get_processor_name(),
            raw_document=documentai.RawDocument(
                content=document_content,
                mime_type=mime_type
            )
        )
        result = self.documentai_client.process_document(request=request)
        document = result.document
        products = self._extract_products_from_document(document)
        return products

    def _parse_text_fallback_enhanced(self, text: str) -> List[ProductData]:
        """Enhanced fallback parsing with audio equipment specific patterns."""
        products = []
        text = re.sub(r'\s+', ' ', text)
        
        # Enhanced patterns for audio equipment
        patterns = [
            # Denon specific pattern
            r'(?P<name>[\w\.\-\s]+(?:Denon|AVR|AVC)[\w\.\-\s]*?)[\s|,]+(?P<model>AVR[X]?[-_]?[A-Z]?\d{3,4}[A-Z]*[BT]*|AVC[-_][A-Z]?\d{3,4}[A-Z]*)[\s|,]+.*?R?\s*(?P<price>[0-9,]+\.?\d*)',
            # General audio equipment pattern
            r'(?P<name>[\w\.\-\s]+(?:Channel|Receiver|Amplifier|Speaker)[\w\.\-\s]*?)[\s|,]+(?P<model>[A-Z0-9\-]{4,})[\s|,]+.*?R?\s*(?P<price>[0-9,]+\.?\d*)',
            # Generic pattern
            r'(?P<name>[\w\.\-\s]+)[\s|,]+(?P<model>[A-Z0-9\-]{4,})[\s|,]+.*?R?\s*(?P<price>[0-9,]+\.?\d*)'
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                name = match.group('name').strip()
                model = match.group('model').strip()
                price = match.group('price').replace(',', '').strip()
                
                # Enhanced model extraction
                extracted_model = self.extract_denon_model(name) or model
                
                # Skip if invalid
                if len(name) < 3 or len(extracted_model) < 3:
                    continue
                
                manufacturer = config.default_manufacturer
                
                # Detect manufacturer from name
                if 'denon' in name.lower():
                    manufacturer = 'Denon'
                elif 'akg' in name.lower():
                    manufacturer = 'AKG'
                elif 'polk' in name.lower():
                    manufacturer = 'Polk Audio'
                
                normalized_name = self.normalize_product_name(name, extracted_model, manufacturer)
                online_store_name = self._make_online_store_name(normalized_name, extracted_model, manufacturer)
                
                product = ProductData(
                    name=normalized_name,
                    model=extracted_model,
                    price=self._price_to_rands(price),
                    manufacturer=manufacturer,
                    online_store_name=online_store_name,
                    confidence=0.7  # Lower confidence for fallback parsing
                )
                products.append(product)
        
        return products

    def _extract_products_from_document(self, document: documentai.Document) -> List[ProductData]:
        products = []
        # Temporary variables to collect entity information
        name = ""
        model = ""
        price = ""
        manufacturer = ""
        try:
            entities = document.entities
            for entity in entities:
                entity_type = entity.type_
                entity_text = entity.text_anchor.content if entity.text_anchor else ""
                confidence = entity.confidence
                if entity_type.lower() in ['product_name', 'name', 'title']:
                    name = entity_text
                elif entity_type.lower() in ['model', 'sku', 'part_number']:
                    model = entity_text
                elif entity_type.lower() in ['price', 'cost', 'amount']:
                    price = entity_text
                elif entity_type.lower() in ['manufacturer', 'brand', 'make']:
                    manufacturer = entity_text
                else:
                    continue
                if name and model:
                    # Enhanced model extraction
                    extracted_model = self.extract_denon_model(name) or model
                    normalized_name = self.normalize_product_name(name, extracted_model, manufacturer)
                    
                    product = ProductData(
                        name=normalized_name,
                        model=extracted_model,
                        price=self._price_to_rands(price) if price else None,
                        manufacturer=manufacturer,
                        online_store_name=self._make_online_store_name(normalized_name, extracted_model, manufacturer)
                    )
                    products.append(product)
                    name = model = price = manufacturer = ""
        except Exception as e:
            self.logger.error(f"Error extracting products from document: {str(e)}")
        return products

    def parse_file(self, file_path: str) -> List[ProductData]:
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            if file_path.lower().endswith('.pdf'):
                mime_type = 'application/pdf'
            elif file_path.lower().endswith('.txt'):
                mime_type = 'text/plain'
            else:
                mime_type = 'application/octet-stream'
            return self.parse_document(content, mime_type)
        except Exception as e:
            self.logger.error(f"Error parsing file {file_path}: {str(e)}")
            return []

    def products_to_dict(self, products: List[ProductData]) -> List[Dict[str, Any]]:
        return [asdict(product) for product in products]

    def test_connection(self) -> bool:
        try:
            if self.openai_client:
                self.openai_client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=5
                )
                return True
            if self.documentai_client and self.processor_id != 'mock-processor-for-demo':
                processor_name = self._get_processor_name()
                self.documentai_client.get_processor(name=processor_name)
                return True
            return True
        except Exception:
            return False

# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    parser = DocumentAIParser()
    if parser.test_connection():
        print("\n✅ Enhanced parser initialized successfully and ready to process documents")
    else:
        print("\n❌ Parser initialization failed")
    # Example:
    # products = parser.parse_file("path/to/your/document.pdf")
    # for product in products:
    #     print(f"{product.online_store_name} | {product.model} | {product.price} | Valid")
