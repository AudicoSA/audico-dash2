
# Configuration Guide

## Overview
This guide covers the detailed configuration of the Audico Product Management System for Windows deployment.

## Environment Configuration

### Python Environment Variables
Create a `.env` file in the `audico_product_manager` directory with the following variables:

```env
# Google Cloud Configuration
GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\service-account-key.json
GOOGLE_CLOUD_PROJECT_ID=your-project-id
DOCUMENT_AI_PROCESSOR_ID=your-processor-id
GCS_BUCKET_NAME=your-bucket-name

# OpenCart Configuration
OPENCART_BASE_URL=https://your-store.com
OPENCART_API_USERNAME=your-api-username
OPENCART_API_KEY=your-api-key

# System Configuration
LOG_LEVEL=INFO
DRY_RUN=false
PRICE_TOLERANCE=0.01
SIMILARITY_THRESHOLD=0.8
```

### Google Cloud Setup

#### 1. Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing one
3. Note the Project ID

#### 2. Enable APIs
Enable the following APIs:
- Document AI API
- Cloud Storage API

#### 3. Create Service Account
1. Go to IAM & Admin → Service Accounts
2. Create a new service account
3. Grant the following roles:
   - Document AI API User
   - Storage Object Admin
4. Create and download JSON key file
5. Save the key file securely and update `GOOGLE_APPLICATION_CREDENTIALS`

#### 4. Create Storage Bucket
1. Go to Cloud Storage
2. Create a new bucket
3. Choose appropriate region and storage class
4. Update `GCS_BUCKET_NAME` in .env

#### 5. Create Document AI Processor
1. Go to Document AI
2. Create a new processor
3. Choose "Form Parser" or "Document OCR"
4. Note the Processor ID
5. Update `DOCUMENT_AI_PROCESSOR_ID` in .env

### OpenCart Configuration

#### 1. Install REST API Extension
1. Download OpenCart REST API extension
2. Install through OpenCart admin panel
3. Enable the extension

#### 2. Create API User
1. Go to System → Users → API
2. Create a new API user
3. Generate API key
4. Set appropriate permissions

#### 3. Configure Store Settings
Update the following in .env:
- `OPENCART_BASE_URL`: Your store's base URL
- `OPENCART_API_USERNAME`: API username
- `OPENCART_API_KEY`: Generated API key

## Dashboard Configuration

### Environment Variables
The dashboard uses the following configuration files:

#### next.config.js
```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
  env: {
    BACKEND_URL: process.env.BACKEND_URL || 'http://localhost:8000',
  },
}

module.exports = nextConfig
```

#### .env.local (optional)
```env
BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=Audico Product Manager
```

## System Configuration

### Logging Configuration
The system uses Python's logging module. Configure in `logging.conf`:

```ini
[loggers]
keys=root,audico

[handlers]
keys=consoleHandler,fileHandler

[formatters]
keys=simpleFormatter

[logger_root]
level=INFO
handlers=consoleHandler

[logger_audico]
level=INFO
handlers=consoleHandler,fileHandler
qualname=audico
propagate=0

[handler_consoleHandler]
class=StreamHandler
level=INFO
formatter=simpleFormatter
args=(sys.stdout,)

[handler_fileHandler]
class=FileHandler
level=INFO
formatter=simpleFormatter
args=('logs/audico.log',)

[formatter_simpleFormatter]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

### Product Matching Configuration
Configure product matching behavior in `config.py`:

```python
# Product matching settings
SIMILARITY_THRESHOLD = 0.8  # Minimum similarity for product matching
PRICE_TOLERANCE = 0.01      # Price comparison tolerance (1%)

# Processing settings
MAX_CONCURRENT_UPLOADS = 5
BATCH_SIZE = 100
RETRY_ATTEMPTS = 3
RETRY_DELAY = 5  # seconds

# Currency settings
DEFAULT_CURRENCY = 'R'  # South African Rands
CURRENCY_SYMBOL = 'R'
```

## Security Configuration

### API Security
1. Use HTTPS for all external API calls
2. Store credentials securely
3. Implement rate limiting
4. Monitor API usage

### File Security
1. Validate uploaded file types
2. Scan files for malware
3. Limit file sizes
4. Use secure file storage

### Network Security
1. Configure firewall rules
2. Use VPN for sensitive operations
3. Monitor network traffic
4. Implement access controls

## Performance Configuration

### Python Performance
```python
# Memory management
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
CHUNK_SIZE = 8192

# Processing optimization
WORKER_THREADS = 4
QUEUE_SIZE = 100
TIMEOUT_SECONDS = 300
```

### Dashboard Performance
```javascript
// Next.js optimization
const nextConfig = {
  experimental: {
    appDir: true,
  },
  images: {
    domains: ['localhost'],
  },
  compress: true,
  poweredByHeader: false,
}
```

## Database Configuration (Optional)
If using a database for caching or logging:

```env
# Database configuration (optional)
DATABASE_URL=sqlite:///audico.db
# or
DATABASE_URL=postgresql://user:password@localhost/audico
```

## Monitoring Configuration

### Health Checks
Configure health check endpoints:

```python
HEALTH_CHECK_ENDPOINTS = {
    'google_cloud': 'https://storage.googleapis.com',
    'opencart': '{OPENCART_BASE_URL}/api',
    'document_ai': 'https://documentai.googleapis.com'
}
```

### Metrics Collection
```python
METRICS_CONFIG = {
    'enabled': True,
    'interval': 60,  # seconds
    'retention': 7,  # days
}
```

## Backup Configuration

### Automated Backups
```python
BACKUP_CONFIG = {
    'enabled': True,
    'schedule': '0 2 * * *',  # Daily at 2 AM
    'retention_days': 30,
    'backup_location': 'C:\\Backups\\Audico'
}
```

## Testing Configuration

### Test Environment
```env
# Test environment variables
TEST_MODE=true
TEST_GCS_BUCKET=audico-test-bucket
TEST_OPENCART_URL=https://test-store.com
```

### Mock Services
Enable mock services for testing:

```python
MOCK_SERVICES = {
    'document_ai': False,
    'gcs': False,
    'opencart': True  # Enable for testing without real store
}
```

## Troubleshooting Configuration

### Debug Mode
```env
DEBUG=true
LOG_LEVEL=DEBUG
VERBOSE_LOGGING=true
```

### Error Reporting
```python
ERROR_REPORTING = {
    'enabled': True,
    'email_notifications': True,
    'slack_webhook': 'https://hooks.slack.com/...',
}
```

---

For additional configuration options, refer to the individual module documentation and the troubleshooting guide.
