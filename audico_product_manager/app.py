
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import tempfile
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import requests
import json
import logging
from datetime import datetime
import base64

# Use absolute import that works when running directly
try:
    from audico_product_manager.opencart_client import OpenCartAPIClient
    from audico_product_manager.docai_parser import DocumentAIParser
    from audico_product_manager.product_comparison import ProductComparator
except ImportError:
    from opencart_client import OpenCartAPIClient
    from docai_parser import DocumentAIParser
    from product_comparison import ProductComparator

# Load environment variables from .env
load_dotenv()

# Configure file upload
UPLOAD_FOLDER = '/tmp/audico_uploads'
ALLOWED_EXTENSIONS = {'pdf', 'txt'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize clients
opencart_client = None
docai_parser = None
product_comparator = None

def get_opencart_client():
    """Get or create OpenCart client instance."""
    global opencart_client
    if opencart_client is None:
        opencart_client = OpenCartAPIClient()
    return opencart_client

def get_docai_parser():
    """Get or create Document AI parser instance."""
    global docai_parser
    if docai_parser is None:
        docai_parser = DocumentAIParser()
    return docai_parser

def get_product_comparator():
    """Get or create Product Comparator instance."""
    global product_comparator
    if product_comparator is None:
        product_comparator = ProductComparator(get_opencart_client())
    return product_comparator

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    """Home endpoint."""
    return jsonify({
        'message': 'Audico Product Manager API',
        'version': '1.0.0',
        'status': 'running'
    })

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/test-connection')
def test_connection():
    """Test OpenCart API connection."""
    try:
        client = get_opencart_client()
        success = client.test_connection()
        
        return jsonify({
            'success': success,
            'message': 'Connection successful' if success else 'Connection failed',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Connection test error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Connection test failed: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/categories')
def get_categories():
    """Get all categories from OpenCart."""
    try:
        client = get_opencart_client()
        categories = client.get_categories()
        
        return jsonify({
            'success': True,
            'data': categories,
            'count': len(categories) if categories else 0
        })
    except Exception as e:
        logger.error(f"Error getting categories: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to get categories: {str(e)}'
        }), 500

@app.route('/products')
def get_products():
    """Get products from OpenCart."""
    try:
        limit = request.args.get('limit', 100, type=int)
        page = request.args.get('page', 1, type=int)
        
        client = get_opencart_client()
        products = client.get_products(limit=limit, page=page)
        
        return jsonify({
            'success': True,
            'data': products,
            'count': len(products) if products else 0,
            'page': page,
            'limit': limit
        })
    except Exception as e:
        logger.error(f"Error getting products: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to get products: {str(e)}'
        }), 500

@app.route('/products', methods=['POST'])
def create_product():
    """Create a new product in OpenCart."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        # Validate required fields
        required_fields = ['name', 'model', 'price']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                'success': False,
                'message': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        client = get_opencart_client()
        
        # Create OpenCart product from data
        from opencart_client import OpenCartProduct
        product = OpenCartProduct(
            name=data['name'],
            model=data['model'],
            price=float(data['price']),
            description=data.get('description', ''),
            categories=data.get('categories', []),
            manufacturer_id=data.get('manufacturer_id', 0),
            status=data.get('status', 1),
            stock_status_id=data.get('stock_status_id', 7),
            quantity=data.get('quantity', 100)
        )
        
        result = client.create_product(product)
        
        if result:
            return jsonify({
                'success': True,
                'data': result,
                'message': 'Product created successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to create product'
            }), 500
            
    except Exception as e:
        logger.error(f"Error creating product: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to create product: {str(e)}'
        }), 500

@app.route('/api/products/compare', methods=['POST'])
def compare_products():
    """Compare parsed products with existing OpenCart products."""
    try:
        data = request.get_json()
        
        if not data or 'products' not in data:
            return jsonify({
                'success': False,
                'message': 'No products data provided'
            }), 400
        
        parsed_products = data['products']
        
        if not isinstance(parsed_products, list):
            return jsonify({
                'success': False,
                'message': 'Products data must be a list'
            }), 400
        
        logger.info(f"Starting product comparison for {len(parsed_products)} products")
        
        # Get product comparator
        comparator = get_product_comparator()
        
        # Perform comparison
        matches = comparator.compare_products(parsed_products)
        
        # Generate summary
        summary = comparator.get_comparison_summary(matches)
        
        # Helper function to serialize enum values
        def serialize_enum(value):
            if hasattr(value, 'value'):
                return value.value
            return str(value)
        
        # Convert matches to JSON-serializable format
        comparison_results = []
        for match in matches:
            result = {
                'id': f"match_{len(comparison_results)}",
                'parsedProduct': {
                    'name': str(match.parsed_product.get('name', '')),
                    'sku': str(match.parsed_product.get('sku', '') or match.parsed_product.get('model', '')),
                    'price': float(match.parsed_product.get('price', 0)),
                    'description': str(match.parsed_product.get('description', '')),
                    'model': str(match.parsed_product.get('model', ''))
                },
                'existingProduct': None,
                'matchType': serialize_enum(match.match_type),
                'similarity': int(match.confidence_score * 100),
                'action': str(match.action),
                'priceChange': float(match.price_change) if match.price_change is not None else None,
                'issues': [str(issue) for issue in match.issues],
                'confidenceLevel': serialize_enum(match.confidence_level),
                'debugInfo': match.debug_info
            }
            
            if match.existing_product:
                # Use the comparator's price parsing method for existing product price
                existing_price = comparator._parse_price(match.existing_product.get('price', 0)) or 0.0
                result['existingProduct'] = {
                    'name': match.existing_product.get('name', ''),
                    'sku': match.existing_product.get('sku', '') or match.existing_product.get('model', ''),
                    'price': existing_price,
                    'description': match.existing_product.get('description', ''),
                    'id': match.existing_product.get('product_id', ''),
                    'model': match.existing_product.get('model', '')
                }
            
            comparison_results.append(result)
        
        logger.info(f"Comparison completed. Summary: {summary}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully compared {len(parsed_products)} products',
            'data': {
                'results': comparison_results,
                'summary': summary,
                'total_products': len(parsed_products),
                'existing_products_count': len(comparator.existing_products)
            }
        })
        
    except Exception as e:
        logger.error(f"Error in product comparison: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Product comparison failed: {str(e)}'
        }), 500

@app.route('/api/products/reload-existing', methods=['POST'])
def reload_existing_products():
    """Force reload of existing products from OpenCart."""
    try:
        comparator = get_product_comparator()
        success = comparator.load_existing_products(force_reload=True)
        
        return jsonify({
            'success': success,
            'message': f'Successfully reloaded {len(comparator.existing_products)} existing products' if success else 'Failed to reload products',
            'products_count': len(comparator.existing_products)
        })
        
    except Exception as e:
        logger.error(f"Error reloading existing products: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to reload existing products: {str(e)}'
        }), 500

@app.route('/api/pricelist/upload', methods=['POST'])
def upload_pricelist():
    """Upload and process a pricelist PDF."""
    try:
        # Check if file is present in request
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No file provided'
            }), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'No file selected'
            }), 400
        
        # Check if file type is allowed
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'message': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        file.save(file_path)
        logger.info(f"File saved: {file_path}")
        
        try:
            # Process the file with Document AI
            parser = get_docai_parser()
            products = parser.parse_file(file_path)
            
            # Convert to dictionaries for JSON response
            products_dict = parser.products_to_dict(products)
            
            # Clean up temporary file
            os.remove(file_path)
            
            return jsonify({
                'success': True,
                'message': f'Successfully processed {len(products)} products from {filename}',
                'data': {
                    'filename': filename,
                    'products_count': len(products),
                    'products': products_dict
                }
            })
            
        except Exception as processing_error:
            # Clean up temporary file on error
            if os.path.exists(file_path):
                os.remove(file_path)
            
            logger.error(f"Error processing file: {str(processing_error)}")
            return jsonify({
                'success': False,
                'message': f'Error processing file: {str(processing_error)}'
            }), 500
            
    except Exception as e:
        logger.error(f"Error in upload endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Upload failed: {str(e)}'
        }), 500

@app.route('/api/pricelist/test-parser', methods=['GET'])
def test_parser():
    """Test the Document AI parser connection."""
    try:
        parser = get_docai_parser()
        connection_ok = parser.test_connection()
        
        return jsonify({
            'success': connection_ok,
            'message': 'Parser connection successful' if connection_ok else 'Parser connection failed',
            'parser_type': 'Document AI' if parser.processor_id != 'mock-processor-for-demo' else 'Fallback PDF Parser',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error testing parser: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Parser test failed: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/pricelist/process-text', methods=['POST'])
def process_text():
    """Process text content directly (for testing)."""
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({
                'success': False,
                'message': 'No text content provided'
            }), 400
        
        text_content = data['text']
        
        # Process the text with Document AI parser
        parser = get_docai_parser()
        products = parser._parse_text_fallback(text_content)
        
        # Convert to dictionaries for JSON response
        products_dict = parser.products_to_dict(products)
        
        return jsonify({
            'success': True,
            'message': f'Successfully processed {len(products)} products from text',
            'data': {
                'products_count': len(products),
                'products': products_dict
            }
        })
        
    except Exception as e:
        logger.error(f"Error processing text: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Text processing failed: {str(e)}'
        }), 500

@app.route('/api/pricelist/bulk-create', methods=['POST'])
def bulk_create_products():
    """Create multiple products in OpenCart from parsed pricelist data."""
    try:
        data = request.get_json()
        
        if not data or 'products' not in data:
            return jsonify({
                'success': False,
                'message': 'No products data provided'
            }), 400
        
        products_data = data['products']
        
        if not isinstance(products_data, list):
            return jsonify({
                'success': False,
                'message': 'Products data must be a list'
            }), 400
        
        client = get_opencart_client()
        created_products = []
        failed_products = []
        
        for product_data in products_data:
            try:
                # Create OpenCart product from parsed data
                from opencart_client import OpenCartProduct
                
                # Map parsed data to OpenCart product format
                opencart_product = OpenCartProduct(
                    name=product_data.get('name', ''),
                    model=product_data.get('model', ''),
                    price=float(str(product_data.get('price', '0')).replace(',', '').replace('$', '').replace('€', '').replace('£', '') or 0),
                    description=product_data.get('description', ''),
                    categories=[],  # You might want to map categories
                    manufacturer_id=0,  # You might want to map manufacturers
                    status=1,
                    stock_status_id=7,
                    quantity=100
                )
                
                result = client.create_product(opencart_product)
                
                if result:
                    created_products.append({
                        'model': product_data.get('model'),
                        'name': product_data.get('name'),
                        'opencart_id': result.get('product_id') if isinstance(result, dict) else None
                    })
                else:
                    failed_products.append({
                        'model': product_data.get('model'),
                        'name': product_data.get('name'),
                        'error': 'Failed to create in OpenCart'
                    })
                    
            except Exception as product_error:
                failed_products.append({
                    'model': product_data.get('model', 'Unknown'),
                    'name': product_data.get('name', 'Unknown'),
                    'error': str(product_error)
                })
        
        return jsonify({
            'success': True,
            'message': f'Processed {len(products_data)} products. Created: {len(created_products)}, Failed: {len(failed_products)}',
            'data': {
                'total_processed': len(products_data),
                'created_count': len(created_products),
                'failed_count': len(failed_products),
                'created_products': created_products,
                'failed_products': failed_products
            }
        })
        
    except Exception as e:
        logger.error(f"Error in bulk create: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Bulk create failed: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
