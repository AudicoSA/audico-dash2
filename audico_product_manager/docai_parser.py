
"""
Google Cloud Document AI parser for extracting product data from pricelists.

Handles PDF and Excel file parsing using Document AI Form Parser to extract
structured product information including names, prices, and descriptions.
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal, InvalidOperation

from google.cloud import documentai_v1 as documentai
from google.cloud.exceptions import GoogleCloudError

from .config import config

logger = logging.getLogger(__name__)

class ProductData:
    """Data class for product information."""
    
    def __init__(self, name: str = "", price: str = "", description: str = "", 
                 sku: str = "", category: str = "", specifications: Dict[str, str] = None):
        self.name = name.strip()
        self.price = price.strip()
        self.description = description.strip()
        self.sku = sku.strip()
        self.category = category.strip()
        self.specifications = specifications or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert product data to dictionary."""
        return {
            'name': self.name,
            'price': self.price,
            'description': self.description,
            'sku': self.sku,
            'category': self.category,
            'specifications': self.specifications
        }
    
    def is_valid(self) -> bool:
        """Check if product data has minimum required fields."""
        return bool(self.name and self.price)
    
    def clean_price(self) -> Optional[Decimal]:
        """Extract and clean price value."""
        if not self.price:
            return None
        
        # Remove currency symbols and whitespace
        price_clean = re.sub(r'[^\d.,]', '', self.price)
        
        # Handle different decimal separators
        if ',' in price_clean and '.' in price_clean:
            # Assume comma is thousands separator
            price_clean = price_clean.replace(',', '')
        elif ',' in price_clean:
            # Assume comma is decimal separator
            price_clean = price_clean.replace(',', '.')
        
        try:
            return Decimal(price_clean)
        except (InvalidOperation, ValueError):
            logger.warning(f"Could not parse price: {self.price}")
            return None

class DocumentAIParser:
    """Document AI parser for extracting product data from pricelists."""
    
    def __init__(self):
        """Initialize Document AI client."""
        try:
            # Set up client with regional endpoint
            client_options = {"api_endpoint": config.get_document_ai_endpoint()}
            self.client = documentai.DocumentProcessorServiceClient(
                client_options=client_options
            )
            
            logger.info(f"Initialized Document AI client for location: {config.google_cloud_location}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Document AI client: {e}")
            raise
    
    def process_document(self, gcs_uri: str, mime_type: str = None) -> List[ProductData]:
        """
        Process a document from GCS and extract product data.
        
        Args:
            gcs_uri: GCS URI of the document (gs://bucket/file)
            mime_type: MIME type of the document (auto-detected if None)
            
        Returns:
            List of ProductData objects extracted from the document
        """
        try:
            if not config.google_cloud_processor_id:
                raise ValueError("Google Cloud processor ID not configured")
            
            # Auto-detect MIME type if not provided
            if mime_type is None:
                if gcs_uri.lower().endswith('.pdf'):
                    mime_type = "application/pdf"
                elif gcs_uri.lower().endswith(('.xlsx', '.xls')):
                    mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                else:
                    mime_type = "application/pdf"  # Default
            
            # Prepare the document for processing
            raw_document = documentai.RawDocument(
                content=None,  # Using GCS URI instead of content
                mime_type=mime_type,
                gcs_uri=gcs_uri
            )
            
            # Create the process request
            request = documentai.ProcessRequest(
                name=config.get_processor_path(),
                raw_document=raw_document
            )
            
            # Process the document
            logger.info(f"Processing document: {gcs_uri}")
            result = self.client.process_document(request=request)
            document = result.document
            
            # Extract product data
            products = self._extract_products_from_document(document)
            
            logger.info(f"Extracted {len(products)} products from {gcs_uri}")
            return products
            
        except Exception as e:
            logger.error(f"Failed to process document {gcs_uri}: {e}")
            raise
    
    def _extract_products_from_document(self, document: documentai.Document) -> List[ProductData]:
        """
        Extract product data from processed document.
        
        Args:
            document: Processed Document AI document
            
        Returns:
            List of ProductData objects
        """
        products = []
        
        try:
            # Extract from tables (primary method for structured pricelists)
            table_products = self._extract_from_tables(document)
            products.extend(table_products)
            
            # Extract from entities (fallback method)
            if not products:
                entity_products = self._extract_from_entities(document)
                products.extend(entity_products)
            
            # Extract from key-value pairs (additional data)
            kv_products = self._extract_from_key_value_pairs(document)
            products.extend(kv_products)
            
            # Clean and validate products
            valid_products = []
            for product in products:
                if product.is_valid():
                    valid_products.append(product)
                else:
                    logger.debug(f"Skipping invalid product: {product.name}")
            
            return valid_products
            
        except Exception as e:
            logger.error(f"Failed to extract products from document: {e}")
            return []
    
    def _extract_from_tables(self, document: documentai.Document) -> List[ProductData]:
        """Extract product data from tables in the document."""
        products = []
        
        for page in document.pages:
            for table in page.tables:
                # Analyze table structure to identify columns
                header_row = None
                if table.header_rows:
                    header_row = table.header_rows[0]
                
                # Extract column mappings
                column_mapping = self._analyze_table_headers(header_row, document.text)
                
                # Extract data rows
                for row in table.body_rows:
                    product = self._extract_product_from_table_row(
                        row, column_mapping, document.text
                    )
                    if product:
                        products.append(product)
        
        return products
    
    def _analyze_table_headers(self, header_row, document_text: str) -> Dict[int, str]:
        """Analyze table headers to map columns to product fields."""
        column_mapping = {}
        
        if not header_row:
            # Default column mapping for tables without headers
            return {
                0: 'name',
                1: 'price',
                2: 'description',
                3: 'sku'
            }
        
        for i, cell in enumerate(header_row.cells):
            header_text = self._get_text_from_layout(cell.layout, document_text).lower()
            
            # Map common header patterns to product fields
            if any(keyword in header_text for keyword in ['product', 'name', 'item', 'description']):
                column_mapping[i] = 'name'
            elif any(keyword in header_text for keyword in ['price', 'cost', 'amount', 'value']):
                column_mapping[i] = 'price'
            elif any(keyword in header_text for keyword in ['desc', 'detail', 'spec']):
                column_mapping[i] = 'description'
            elif any(keyword in header_text for keyword in ['sku', 'code', 'id', 'part']):
                column_mapping[i] = 'sku'
            elif any(keyword in header_text for keyword in ['category', 'type', 'class']):
                column_mapping[i] = 'category'
        
        return column_mapping
    
    def _extract_product_from_table_row(self, row, column_mapping: Dict[int, str], 
                                      document_text: str) -> Optional[ProductData]:
        """Extract product data from a table row."""
        product_data = {}
        
        for i, cell in enumerate(row.cells):
            cell_text = self._get_text_from_layout(cell.layout, document_text)
            field_name = column_mapping.get(i)
            
            if field_name:
                product_data[field_name] = cell_text
            elif i == 0 and 'name' not in product_data:
                product_data['name'] = cell_text
            elif i == 1 and 'price' not in product_data:
                product_data['price'] = cell_text
        
        if product_data.get('name') or product_data.get('price'):
            return ProductData(**product_data)
        
        return None
    
    def _extract_from_entities(self, document: documentai.Document) -> List[ProductData]:
        """Extract product data from document entities."""
        products = []
        current_product = ProductData()
        
        for entity in document.entities:
            entity_text = entity.mention_text.strip()
            
            if entity.type_ == "price":
                if current_product.name:
                    current_product.price = entity_text
                    products.append(current_product)
                    current_product = ProductData()
                else:
                    current_product.price = entity_text
            
            elif entity.type_ in ["product_name", "organization"]:
                if current_product.price:
                    products.append(current_product)
                current_product = ProductData(name=entity_text)
            
            elif entity.type_ == "quantity":
                current_product.specifications['quantity'] = entity_text
        
        # Add the last product if it has data
        if current_product.name or current_product.price:
            products.append(current_product)
        
        return products
    
    def _extract_from_key_value_pairs(self, document: documentai.Document) -> List[ProductData]:
        """Extract product data from key-value pairs."""
        products = []
        
        for page in document.pages:
            for form_field in page.form_fields:
                field_name = self._get_text_from_layout(
                    form_field.field_name, document.text
                ).lower().strip()
                field_value = self._get_text_from_layout(
                    form_field.field_value, document.text
                ).strip()
                
                # Look for product-related key-value pairs
                if any(keyword in field_name for keyword in ['product', 'item', 'name']):
                    product = ProductData(name=field_value)
                    products.append(product)
                elif any(keyword in field_name for keyword in ['price', 'cost']):
                    if products:
                        products[-1].price = field_value
        
        return products
    
    def _get_text_from_layout(self, layout, document_text: str) -> str:
        """Extract text from a layout element."""
        if not layout or not layout.text_anchor:
            return ""
        
        text = ""
        for segment in layout.text_anchor.text_segments:
            start_index = int(segment.start_index) if segment.start_index else 0
            end_index = int(segment.end_index) if segment.end_index else len(document_text)
            text += document_text[start_index:end_index]
        
        return text.strip()
    
    def get_document_confidence(self, document: documentai.Document) -> float:
        """Calculate overall confidence score for the document."""
        if not document.pages:
            return 0.0
        
        total_confidence = 0.0
        confidence_count = 0
        
        for page in document.pages:
            # Check table confidence
            for table in page.tables:
                if hasattr(table, 'detection_confidence'):
                    total_confidence += table.detection_confidence
                    confidence_count += 1
            
            # Check form field confidence
            for form_field in page.form_fields:
                if hasattr(form_field.field_name, 'confidence'):
                    total_confidence += form_field.field_name.confidence
                    confidence_count += 1
                if hasattr(form_field.field_value, 'confidence'):
                    total_confidence += form_field.field_value.confidence
                    confidence_count += 1
        
        return total_confidence / confidence_count if confidence_count > 0 else 0.0
