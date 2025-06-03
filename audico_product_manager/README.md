
# Audico Product Manager

Automated product management solution for OpenCart stores using Google Cloud Document AI for parsing pricelists and OpenCart REST API for product synchronization.

## Features

- **Document Parsing**: Automatically parse Excel and PDF pricelists using Google Cloud Document AI Form Parser
- **Product Comparison**: Intelligent matching and comparison of parsed products with existing OpenCart inventory
- **Automated Synchronization**: Create new products and update existing ones based on pricelist data
- **Error Handling**: Comprehensive error handling with retry logic and detailed logging
- **Dry Run Mode**: Analyze changes without executing them
- **Flexible Configuration**: Environment-based configuration management
- **Batch Processing**: Efficient processing of multiple files and products

## Architecture

```
Google Cloud Storage (audicopricelistingest)
    ↓
Document AI Form Parser
    ↓
Product Analysis & Comparison
    ↓
OpenCart REST API Integration
    ↓
Product Creation/Update
```

## Installation

1. **Clone or create the project directory**:
   ```bash
   cd ~/audico_product_manager
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Google Cloud credentials**:
   - Ensure the service account key file is available at `~/Uploads/audico-pricelists-d6dcac3f7c31.json`
   - Or set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your specific configuration
   ```

## Configuration

### Required Environment Variables

- `GOOGLE_CLOUD_PROJECT_ID`: Google Cloud project ID (default: audico-pricelists)
- `GOOGLE_CLOUD_PROCESSOR_ID`: Document AI processor ID (required)
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to service account key file
- `OPENCART_AUTH_TOKEN`: OpenCart API authentication token

### Optional Configuration

- `GCS_BUCKET_NAME`: Google Cloud Storage bucket name (default: audicopricelistingest)
- `TARGET_CATEGORY`: Target product category (default: Load)
- `LOG_LEVEL`: Logging level (default: INFO)
- `BATCH_SIZE`: Processing batch size (default: 50)
- `MAX_RETRIES`: Maximum retry attempts (default: 3)

## Usage

### Command Line Interface

```bash
# Run full pipeline
python -m audico_product_manager.orchestrator

# Dry run (analyze without executing changes)
python -m audico_product_manager.orchestrator --dry-run

# Process specific file
python -m audico_product_manager.orchestrator --specific-file "pricelist.pdf"

# Filter files by name
python -m audico_product_manager.orchestrator --file-filter "2024"

# Test connections
python -m audico_product_manager.orchestrator --test-connections

# Save results to file
python -m audico_product_manager.orchestrator --output-file results.json

# Set log level
python -m audico_product_manager.orchestrator --log-level DEBUG
```

### Python API

```python
from audico_product_manager.orchestrator import ProductManagerOrchestrator

# Initialize orchestrator
orchestrator = ProductManagerOrchestrator()

# Test connections
connections = orchestrator.test_connections()
print(connections)

# Run full pipeline
results = orchestrator.run_full_pipeline(dry_run=True)
print(results)

# Process specific file
file_results = orchestrator.process_specific_file("pricelist.pdf")
print(file_results)
```

## File Processing Workflow

1. **File Discovery**: Scan GCS bucket for unprocessed files (PDF, Excel)
2. **Document Parsing**: Use Document AI to extract structured product data
3. **Product Analysis**: Compare parsed products with existing OpenCart inventory
4. **Action Planning**: Determine required actions (create, update, skip)
5. **Execution**: Execute planned actions via OpenCart API
6. **File Management**: Move processed files to appropriate folders

## Product Matching Logic

The system uses intelligent matching to identify existing products:

- **Name Similarity**: String similarity matching with configurable threshold
- **SKU Matching**: Exact SKU matching when available
- **Model Matching**: Fallback to model field matching
- **Fuzzy Matching**: Handles variations in product names and formatting

## Error Handling

- **Retry Logic**: Automatic retry for transient failures
- **Error Categorization**: Different handling for different error types
- **File Management**: Failed files moved to error folder with metadata
- **Comprehensive Logging**: Detailed logs for debugging and monitoring

## Logging

The system provides comprehensive logging:

- **Console Output**: Real-time progress and status updates
- **File Logging**: Detailed logs saved to `audico_product_manager.log`
- **Structured Logging**: JSON-formatted logs for easy parsing
- **Log Levels**: Configurable verbosity (DEBUG, INFO, WARNING, ERROR)

## Security Considerations

- **Credential Management**: Service account keys stored securely
- **API Authentication**: Basic Auth with secure token handling
- **Environment Variables**: Sensitive configuration via environment variables
- **Access Control**: Minimal required permissions for Google Cloud services

## Monitoring and Maintenance

### Key Metrics to Monitor

- Processing success rate
- Document parsing accuracy
- API response times
- Error rates by category
- File processing volume

### Regular Maintenance Tasks

- Monitor log files for errors
- Review and update product matching rules
- Validate Document AI processor performance
- Update dependencies and security patches
- Backup configuration and credentials

## Troubleshooting

### Common Issues

1. **Authentication Errors**:
   - Verify Google Cloud credentials file exists and is valid
   - Check OpenCart API token is correct
   - Ensure proper IAM permissions

2. **Document Parsing Issues**:
   - Verify Document AI processor ID is correct
   - Check file formats are supported (PDF, Excel)
   - Review Document AI quotas and limits

3. **OpenCart API Issues**:
   - Test API connectivity with `--test-connections`
   - Verify API endpoint URLs are correct
   - Check for API rate limiting

4. **File Processing Errors**:
   - Check GCS bucket permissions
   - Verify file formats and structure
   - Review error logs for specific issues

### Debug Mode

Enable debug logging for detailed troubleshooting:

```bash
python -m audico_product_manager.orchestrator --log-level DEBUG
```

## Development

### Project Structure

```
audico_product_manager/
├── __init__.py              # Package initialization
├── config.py                # Configuration management
├── gcs_client.py            # Google Cloud Storage client
├── docai_parser.py          # Document AI parser
├── opencart_client.py       # OpenCart API client
├── product_logic.py         # Product comparison logic
├── orchestrator.py          # Main orchestration script
├── requirements.txt         # Python dependencies
├── logging.conf             # Logging configuration
├── .env.example             # Environment variables template
└── README.md                # This file
```

### Adding New Features

1. **New Document Types**: Extend `DocumentAIParser` class
2. **Additional APIs**: Create new client classes following existing patterns
3. **Custom Logic**: Extend `ProductSynchronizer` for business-specific rules
4. **New Workflows**: Add methods to `ProductManagerOrchestrator`

### Testing

```bash
# Run tests (when implemented)
pytest tests/

# Test specific components
python -c "from audico_product_manager.opencart_client import OpenCartAPIClient; client = OpenCartAPIClient(); print(client.test_connection())"
```

## Support

For issues and questions:

1. Check the troubleshooting section above
2. Review log files for error details
3. Verify configuration and credentials
4. Test individual components in isolation

## License

This project is proprietary software for Audico online store management.
