
# Audico Product Management System - Windows Setup Guide

## Overview
The Audico Product Management System is a comprehensive automated solution for processing pricelists and managing product data in OpenCart stores. This package includes both the core Python system and a NextJS testing dashboard.

## System Requirements

### Prerequisites
- **Windows 10/11** (64-bit)
- **Python 3.8+** (Download from https://python.org)
- **Node.js 18+** (Download from https://nodejs.org)
- **VS Code** (Download from https://code.visualstudio.com)
- **Git** (Download from https://git-scm.com)

### Recommended VS Code Extensions
- Python
- Pylance
- ES7+ React/Redux/React-Native snippets
- Tailwind CSS IntelliSense
- Auto Rename Tag
- Bracket Pair Colorizer

## Quick Start

### 1. Extract the Package
Extract the `audico_complete_system.zip` file to your desired location (e.g., `C:\Projects\audico_system\`)

### 2. Open in VS Code
1. Open VS Code
2. File → Open Folder
3. Select the extracted `audico_pkg` folder

### 3. Run Setup Scripts
Open VS Code Terminal (Ctrl+`) and run:

```bash
# Install Python dependencies
.\scripts\install_python.bat

# Install Node.js dependencies and start dashboard
.\scripts\setup_dashboard.bat
```

### 4. Configure Environment
1. Copy `.env.example` to `.env` in the `audico_product_manager` folder
2. Fill in your Google Cloud and OpenCart credentials
3. See Configuration Guide below for details

## Package Structure

```
audico_pkg/
├── audico_product_manager/     # Core Python system
│   ├── *.py                   # Python modules
│   ├── requirements.txt       # Python dependencies
│   ├── .env.example          # Environment template
│   └── README.md             # Core system documentation
├── audico_dashboard/          # NextJS testing dashboard
│   ├── app/                  # Next.js application
│   ├── components/           # React components
│   ├── package.json         # Node.js dependencies
│   └── *.config.*           # Configuration files
├── scripts/                  # Setup and utility scripts
│   ├── install_python.bat   # Python setup script
│   ├── setup_dashboard.bat  # Dashboard setup script
│   └── run_system.bat       # System launcher
├── docs/                    # Documentation
│   ├── configuration.md    # Configuration guide
│   ├── troubleshooting.md  # Troubleshooting guide
│   └── api_reference.md    # API documentation
└── README_WINDOWS.md       # This file
```

## Configuration

### Google Cloud Setup
1. Create a Google Cloud Project
2. Enable Document AI API
3. Create a service account and download JSON key
4. Create a Cloud Storage bucket
5. Update `.env` file with your credentials

### OpenCart Setup
1. Install OpenCart REST API extension
2. Generate API credentials
3. Update `.env` file with store URL and credentials

### Environment Variables
Copy `audico_product_manager/.env.example` to `audico_product_manager/.env` and configure:

```env
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT_ID=audico-pricelists
GOOGLE_CLOUD_LOCATION=us
GOOGLE_CLOUD_PROCESSOR_ID=your-processor-id
GOOGLE_CLOUD_CREDENTIALS_PATH=path/to/service-account-key.json
# Or
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json

# OpenAI Configuration
OPENAI_API_KEY=your-openai-key

# Google Cloud Storage
GCS_BUCKET_NAME=audicopricelistingest
GCS_PROCESSED_FOLDER=processed/
GCS_ERROR_FOLDER=errors/

# OpenCart Configuration
OPENCART_BASE_URL=https://your-store.com/index.php?route=ocrestapi
OPENCART_AUTH_TOKEN=your-opencart-token

# System Configuration
LOG_LEVEL=INFO
DRY_RUN=false
BATCH_SIZE=50
MAX_RETRIES=3
RETRY_DELAY=5
```

## Running the System

### Method 1: Using Scripts
```bash
# Start the complete system
.\scripts\run_system.bat
```

### Method 2: Manual Start
```bash
# Terminal 1: Start Python system
cd audico_product_manager
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python orchestrator.py

# Terminal 2: Start dashboard
cd audico_dashboard\app
npm install
npm run dev
```

### Method 3: VS Code Integration
1. Open the workspace in VS Code
2. Use the integrated terminal
3. Run the Python debugger for the core system
4. Use the NPM scripts panel for the dashboard

## Testing the System

### 1. Dashboard Access
- Open browser to http://localhost:3000
- Navigate through different modules
- Test file uploads and system monitoring

### 2. Core System Testing
```bash
cd audico_product_manager
python -m pytest tests/  # If tests are available
python orchestrator.py --dry-run  # Safe testing mode
```

### 3. Integration Testing
1. Upload a test pricelist through the dashboard
2. Monitor processing in System Monitor
3. Check results in Product Comparison
4. Verify OpenCart integration

## Currency Configuration
The system is configured to use South African Rands (R) as the default currency. All price displays and calculations use the R symbol.

## Development Workflow

### Python Development
1. Activate virtual environment: `venv\Scripts\activate`
2. Install development dependencies: `pip install -r requirements-dev.txt`
3. Run linting: `flake8 .`
4. Run tests: `pytest`

### Dashboard Development
1. Navigate to dashboard: `cd audico_dashboard\app`
2. Install dependencies: `npm install`
3. Start development server: `npm run dev`
4. Build for production: `npm run build`

## Monitoring and Logs

### Log Locations
- Python logs: `audico_product_manager/logs/`
- Dashboard logs: `audico_dashboard/app/dev.log`
- System logs: Check VS Code terminal output

### Monitoring Dashboard
Access the monitoring dashboard at http://localhost:3000/system-monitor to view:
- System status
- Processing logs
- Error reports
- Performance metrics

## Security Considerations

### API Keys and Credentials
- Never commit `.env` files to version control
- Store credentials securely
- Use environment-specific configurations
- Regularly rotate API keys

### Network Security
- Use HTTPS for all external API calls
- Implement proper authentication
- Monitor API usage and rate limits

## Performance Optimization

### Python System
- Use virtual environments
- Monitor memory usage for large files
- Implement proper error handling
- Use logging for debugging

### Dashboard
- Optimize bundle size with `npm run build`
- Use React DevTools for performance profiling
- Implement proper state management
- Monitor network requests

## Backup and Recovery

### Data Backup
- Backup `.env` configuration files
- Export OpenCart product data regularly
- Backup Google Cloud Storage buckets
- Document custom configurations

### System Recovery
- Keep a copy of working configurations
- Document any custom modifications
- Maintain version control for code changes
- Test recovery procedures regularly

## Support and Troubleshooting

### Common Issues
See `docs/troubleshooting.md` for detailed solutions to common problems.

### Getting Help
1. Check the troubleshooting guide
2. Review system logs
3. Test with dry-run mode
4. Verify all credentials and configurations

### Reporting Issues
When reporting issues, include:
- Error messages and stack traces
- System configuration details
- Steps to reproduce the problem
- Log file excerpts

## Version Information
- Core System: v1.0.0
- Dashboard: v1.0.0
- Python: 3.8+
- Node.js: 18+
- Currency: South African Rands (R)

---

For detailed configuration and troubleshooting information, see the additional documentation in the `docs/` folder.
