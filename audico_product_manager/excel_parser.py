
"""
Excel Parser for Audico Product Manager.

This module provides functionality to parse Excel price lists and extract
product information in a format compatible with the existing workflow.
"""

import logging
import re
import os
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
import pandas as pd
from pathlib import Path

try:
    from audico_product_manager.docai_parser import ProductData
    from audico_product_manager.config import config
except ImportError:
    try:
        from .docai_parser import ProductData
        from .config import config
    except ImportError:
        from docai_parser import ProductData
        from config import config


class ExcelParser:
    """Parser for Excel price lists and product catalogs."""
    
    def __init__(self):
        """Initialize the Excel parser."""
        self.logger = logging.getLogger(__name__)
        
        # Common column name mappings for product data
        self.column_mappings = {
            'name': ['name', 'product_name', 'product', 'description', 'item', 'title'],
            'model': ['model', 'sku', 'part_number', 'item_code', 'product_code', 'model_number'],
            'price': ['price', 'cost', 'amount', 'rrp', 'new_rrp', 'current_price', 'selling_price'],
            'old_price': ['old_price', 'old_rrp', 'previous_price', 'was_price', 'original_price'],
            'manufacturer': ['manufacturer', 'brand', 'make', 'supplier', 'vendor'],
            'category': ['category', 'type', 'product_type', 'class', 'group'],
            'description': ['description', 'details', 'specs', 'specifications', 'notes']
        }
        
        # Audio equipment specific model patterns
        self.audio_model_patterns = [
            r'\b(AVR[X]?[-_]?[A-Z]?\d{3,4}[A-Z]*[BT]*)\b',  # Denon AVR patterns
            r'\b(AVC[-_][A-Z]?\d{3,4}[A-Z]*)\b',  # Denon AVC patterns
            r'\b([A-Z]{2,4}[-_]\d{3,4}[A-Z]*)\b',  # General audio patterns
            r'\b([A-Z]{3,}\d{3,}[A-Z]*)\b',  # Professional audio
            r'\b([A-Z]+\d+[A-Z]*[-_]?[A-Z]*)\b',  # DJ/Pro equipment
        ]
    
    def parse_excel_file(self, file_path: str, sheet_name: Union[str, int] = 0) -> List[ProductData]:
        """
        Parse an Excel file and extract product data.
        
        Args:
            file_path: Path to the Excel file
            sheet_name: Sheet name or index to parse (default: first sheet)
            
        Returns:
            List[ProductData]: List of extracted product data
        """
        try:
            self.logger.info(f"Starting Excel parsing: {file_path}")
            
            # Check if file exists
            if not os.path.exists(file_path):
                self.logger.error(f"Excel file not found: {file_path}")
                return []
            
            # Read Excel file
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')
                self.logger.info(f"Successfully loaded Excel file with {len(df)} rows and {len(df.columns)} columns")
            except Exception as e:
                self.logger.error(f"Error reading Excel file: {str(e)}")
                return []
            
            # Clean and prepare dataframe
            df = self._clean_dataframe(df)
            
            # Map columns to standard names
            column_map = self._map_columns(df.columns.tolist())
            self.logger.info(f"Column mapping: {column_map}")
            
            # Extract products
            products = self._extract_products_from_dataframe(df, column_map)
            
            self.logger.info(f"Successfully extracted {len(products)} products from Excel file")
            return products
            
        except Exception as e:
            self.logger.error(f"Error parsing Excel file {file_path}: {str(e)}")
            return []
    
    def parse_prices(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse Excel file and return product data as dictionaries.
        
        Args:
            file_path: Path to the Excel file
            
        Returns:
            List[Dict[str, Any]]: List of product data dictionaries
        """
        products = self.parse_excel_file(file_path)
        return [asdict(product) for product in products]
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and prepare the dataframe for processing.
        
        Args:
            df: Raw dataframe from Excel
            
        Returns:
            pd.DataFrame: Cleaned dataframe
        """
        # Remove completely empty rows and columns
        df = df.dropna(how='all').dropna(axis=1, how='all')
        
        # Clean column names
        df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
        
        # Remove rows where all important columns are empty
        important_cols = ['name', 'product', 'model', 'sku', 'price', 'cost']
        existing_important_cols = [col for col in important_cols if col in df.columns]
        if existing_important_cols:
            df = df.dropna(subset=existing_important_cols, how='all')
        
        # Fill NaN values with empty strings for text columns
        text_columns = df.select_dtypes(include=['object']).columns
        df[text_columns] = df[text_columns].fillna('')
        
        # Convert numeric columns
        numeric_columns = df.select_dtypes(include=['number']).columns
        df[numeric_columns] = df[numeric_columns].fillna(0)
        
        self.logger.info(f"Cleaned dataframe: {len(df)} rows, {len(df.columns)} columns")
        return df
    
    def _map_columns(self, columns: List[str]) -> Dict[str, str]:
        """
        Map Excel columns to standard product data fields.
        
        Args:
            columns: List of column names from Excel
            
        Returns:
            Dict[str, str]: Mapping of standard field names to Excel column names
        """
        column_map = {}
        
        for standard_field, possible_names in self.column_mappings.items():
            for col in columns:
                col_clean = col.lower().strip().replace(' ', '_')
                if any(name in col_clean for name in possible_names):
                    column_map[standard_field] = col
                    break
        
        # If no direct mapping found, try fuzzy matching
        if not column_map.get('name'):
            # Look for the first text column that might contain product names
            for col in columns:
                if any(keyword in col.lower() for keyword in ['product', 'name', 'item', 'description']):
                    column_map['name'] = col
                    break
        
        if not column_map.get('price'):
            # Look for numeric columns that might contain prices
            for col in columns:
                if any(keyword in col.lower() for keyword in ['price', 'cost', 'amount', 'rrp']):
                    column_map['price'] = col
                    break
        
        return column_map
    
    def _extract_products_from_dataframe(self, df: pd.DataFrame, column_map: Dict[str, str]) -> List[ProductData]:
        """
        Extract product data from the cleaned dataframe.
        
        Args:
            df: Cleaned dataframe
            column_map: Column mapping dictionary
            
        Returns:
            List[ProductData]: List of extracted products
        """
        products = []
        
        for index, row in df.iterrows():
            try:
                # Extract basic product information
                name = self._get_cell_value(row, column_map.get('name', ''))
                model = self._get_cell_value(row, column_map.get('model', ''))
                price = self._get_cell_value(row, column_map.get('price', ''))
                old_price = self._get_cell_value(row, column_map.get('old_price', ''))
                manufacturer = self._get_cell_value(row, column_map.get('manufacturer', ''))
                category = self._get_cell_value(row, column_map.get('category', ''))
                description = self._get_cell_value(row, column_map.get('description', ''))
                
                # Skip rows with insufficient data
                if not name and not model:
                    continue
                
                # Extract model from name if not provided
                if not model and name:
                    extracted_model = self._extract_model_from_text(name)
                    if extracted_model:
                        model = extracted_model
                
                # Skip if still no model
                if not model:
                    self.logger.debug(f"Skipping row {index}: No model found")
                    continue
                
                # Parse price
                parsed_price = self._parse_price_value(price)
                if not parsed_price or parsed_price <= 0:
                    # Try old price if current price is invalid
                    parsed_price = self._parse_price_value(old_price)
                
                # Skip if no valid price
                if not parsed_price or parsed_price <= 0:
                    self.logger.debug(f"Skipping row {index}: No valid price found")
                    continue
                
                # Determine manufacturer if not provided
                if not manufacturer:
                    manufacturer = self._detect_manufacturer(name, model)
                
                # Clean and normalize name
                clean_name = self._normalize_product_name(name, model, manufacturer)
                
                # Create product
                product = ProductData(
                    name=clean_name,
                    model=model.strip(),
                    price=self._format_price(parsed_price),
                    description=description.strip() if description else None,
                    category=category.strip() if category else None,
                    manufacturer=manufacturer.strip() if manufacturer else config.default_manufacturer,
                    confidence=0.8,  # Excel parsing confidence
                    online_store_name=self._make_online_store_name(clean_name, model, manufacturer)
                )
                
                products.append(product)
                self.logger.debug(f"Extracted product: {product.name} | {product.model} | {product.price}")
                
            except Exception as e:
                self.logger.warning(f"Error processing row {index}: {str(e)}")
                continue
        
        return products
    
    def _get_cell_value(self, row: pd.Series, column_name: str) -> str:
        """
        Get cell value from row, handling missing columns gracefully.
        
        Args:
            row: Pandas series representing a row
            column_name: Name of the column to extract
            
        Returns:
            str: Cell value as string
        """
        if not column_name or column_name not in row.index:
            return ""
        
        value = row[column_name]
        if pd.isna(value):
            return ""
        
        return str(value).strip()
    
    def _extract_model_from_text(self, text: str) -> Optional[str]:
        """
        Extract model number from text using audio equipment patterns.
        
        Args:
            text: Text to extract model from
            
        Returns:
            str: Extracted model or None
        """
        if not text:
            return None
        
        for pattern in self.audio_model_patterns:
            match = re.search(pattern, text.upper())
            if match:
                model = match.group(1)
                if len(model) >= 3:  # Minimum model length
                    return model
        
        return None
    
    def _parse_price_value(self, price_value: Any) -> Optional[float]:
        """
        Parse price value from Excel cell.
        
        Args:
            price_value: Price value from Excel
            
        Returns:
            float: Parsed price or None
        """
        if not price_value or pd.isna(price_value):
            return None
        
        try:
            # If already a number
            if isinstance(price_value, (int, float)):
                return float(price_value)
            
            # Convert to string and clean
            price_str = str(price_value).strip()
            
            # Remove currency symbols and whitespace
            cleaned = re.sub(r'[R$€£¥₹₽¢₦₨₪₫₡₵₲₴₸₼₾₿\s]', '', price_str)
            
            # Remove any remaining non-numeric characters except comma and period
            cleaned = re.sub(r'[^\d.,]', '', cleaned)
            
            if not cleaned:
                return None
            
            # Handle different decimal separators
            if ',' in cleaned and '.' in cleaned:
                # Both comma and period - assume comma is thousands separator
                cleaned = cleaned.replace(',', '')
            elif ',' in cleaned:
                # Check if comma is decimal separator or thousands separator
                parts = cleaned.split(',')
                if len(parts) == 2 and len(parts[1]) <= 2:
                    # Comma is decimal separator
                    cleaned = cleaned.replace(',', '.')
                else:
                    # Comma is thousands separator
                    cleaned = cleaned.replace(',', '')
            
            return float(cleaned)
            
        except (ValueError, TypeError):
            self.logger.warning(f"Could not parse price: {price_value}")
            return None
    
    def _detect_manufacturer(self, name: str, model: str) -> str:
        """
        Detect manufacturer from product name or model.
        
        Args:
            name: Product name
            model: Product model
            
        Returns:
            str: Detected manufacturer
        """
        text = f"{name} {model}".lower()
        
        # Common audio equipment manufacturers
        manufacturers = {
            'denon': 'Denon',
            'akg': 'AKG',
            'shure': 'Shure',
            'sennheiser': 'Sennheiser',
            'audio-technica': 'Audio-Technica',
            'yamaha': 'Yamaha',
            'pioneer': 'Pioneer',
            'sony': 'Sony',
            'jbl': 'JBL',
            'qsc': 'QSC',
            'behringer': 'Behringer',
            'mackie': 'Mackie',
            'polk': 'Polk Audio',
            'marantz': 'Marantz',
            'onkyo': 'Onkyo',
            'harman': 'Harman Kardon'
        }
        
        for key, manufacturer in manufacturers.items():
            if key in text:
                return manufacturer
        
        return config.default_manufacturer
    
    def _normalize_product_name(self, name: str, model: str, manufacturer: str) -> str:
        """
        Normalize product name for consistency.
        
        Args:
            name: Original product name
            model: Product model
            manufacturer: Product manufacturer
            
        Returns:
            str: Normalized product name
        """
        if not name:
            return ""
        
        normalized = name.strip()
        
        # Remove manufacturer or model if they already appear at the start
        if manufacturer and normalized.lower().startswith(manufacturer.lower()):
            normalized = normalized[len(manufacturer):].strip()
        
        if model and normalized.lower().startswith(model.lower()):
            normalized = normalized[len(model):].strip()
        
        # Audio equipment specific normalizations
        normalizations = {
            r'\bCh\b': 'Channel',
            r'\bCh\.': 'Channel',
            r'\bAmp\b': 'Amplifier',
            r'\bRec\b': 'Receiver',
            r'\bBT\b': 'Bluetooth',
            r'\bWiFi\b': 'Wi-Fi',
            r'\bHDMI\b': 'HDMI',
            r'\b4K\b': '4K',
            r'\b8K\b': '8K'
        }
        
        for pattern, replacement in normalizations.items():
            normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
        
        # Clean up whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _format_price(self, price: float) -> str:
        """
        Format price as Rand currency string.
        
        Args:
            price: Price value
            
        Returns:
            str: Formatted price string
        """
        if price == int(price):
            return f"R{price:,.0f}"
        else:
            return f"R{price:,.2f}"
    
    def _make_online_store_name(self, name: str, model: str, manufacturer: str) -> str:
        """
        Create online store friendly product name.
        
        Args:
            name: Product name
            model: Product model
            manufacturer: Product manufacturer
            
        Returns:
            str: Online store name
        """
        parts = [p.strip() for p in [manufacturer, model, name] if p]
        return " ".join(parts)
    
    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported Excel file formats.
        
        Returns:
            List[str]: List of supported file extensions
        """
        return ['.xlsx', '.xls', '.xlsm']
    
    def validate_excel_file(self, file_path: str) -> bool:
        """
        Validate if the file is a supported Excel format.
        
        Args:
            file_path: Path to the file
            
        Returns:
            bool: True if file is valid Excel format
        """
        if not os.path.exists(file_path):
            return False
        
        file_extension = Path(file_path).suffix.lower()
        return file_extension in self.get_supported_formats()


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    parser = ExcelParser()
    print("✅ Excel parser initialized successfully")
    print(f"Supported formats: {parser.get_supported_formats()}")
    
    # Example:
    # products = parser.parse_excel_file("path/to/your/pricelist.xlsx")
    # for product in products:
    #     print(f"{product.online_store_name} | {product.model} | {product.price}")
