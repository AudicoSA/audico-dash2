
# Troubleshooting Guide

## Common Issues and Solutions

### Python Environment Issues

#### Issue: "Python is not recognized as an internal or external command"
**Solution:**
1. Install Python from https://python.org
2. During installation, check "Add Python to PATH"
3. Restart command prompt/VS Code
4. Verify with `python --version`

#### Issue: "pip is not recognized"
**Solution:**
1. Reinstall Python with "Add to PATH" option
2. Or manually add Python Scripts folder to PATH
3. Use `python -m pip` instead of `pip`

#### Issue: Virtual environment creation fails
**Solution:**
```bash
# Try alternative methods
python -m venv venv
# or
py -m venv venv
# or
python3 -m venv venv
```

#### Issue: Permission denied when installing packages
**Solution:**
1. Run command prompt as Administrator
2. Or use `--user` flag: `pip install --user package_name`
3. Check antivirus software blocking installation

### Node.js and Dashboard Issues

#### Issue: "node is not recognized"
**Solution:**
1. Install Node.js from https://nodejs.org
2. Choose LTS version (18+)
3. Restart command prompt/VS Code
4. Verify with `node --version`

#### Issue: npm install fails with permission errors
**Solution:**
```bash
# Clear npm cache
npm cache clean --force

# Use different registry
npm install --registry https://registry.npmjs.org/

# Run as administrator (Windows)
```

#### Issue: Dashboard won't start on port 3000
**Solution:**
1. Check if port is in use: `netstat -ano | findstr :3000`
2. Kill process using port: `taskkill /PID <process_id> /F`
3. Or use different port: `npm run dev -- -p 3001`

#### Issue: "Module not found" errors in dashboard
**Solution:**
```bash
# Delete node_modules and reinstall
rmdir /s node_modules
del package-lock.json
npm install
```

### Google Cloud Configuration Issues

#### Issue: "Application Default Credentials not found"
**Solution:**
1. Verify `GOOGLE_APPLICATION_CREDENTIALS` path in .env
2. Use absolute path: `C:\path\to\service-account-key.json`
3. Check file permissions and existence
4. Verify service account has required roles

#### Issue: "Permission denied" for Google Cloud Storage
**Solution:**
1. Check service account roles:
   - Storage Object Admin
   - Storage Object Creator
2. Verify bucket exists and is accessible
3. Check bucket permissions

#### Issue: Document AI processor not found
**Solution:**
1. Verify processor ID in .env file
2. Check processor is in same project
3. Ensure Document AI API is enabled
4. Verify service account has Document AI API User role

### OpenCart Integration Issues

#### Issue: "Connection refused" to OpenCart API
**Solution:**
1. Verify OpenCart URL is correct and accessible
2. Check if REST API extension is installed and enabled
3. Verify API credentials are correct
4. Check firewall/security settings

#### Issue: "Unauthorized" API responses
**Solution:**
1. Verify API username and key in .env
2. Check API user permissions in OpenCart admin
3. Ensure API is enabled for your IP address
4. Verify SSL certificate if using HTTPS

#### Issue: Products not creating/updating in OpenCart
**Solution:**
1. Check OpenCart logs for errors
2. Verify product data format
3. Test with dry-run mode first
4. Check required fields are present

### File Processing Issues

#### Issue: "File not found" errors
**Solution:**
1. Check file path is correct
2. Verify file permissions
3. Ensure file is not locked by another process
4. Use absolute paths instead of relative

#### Issue: Large files causing memory errors
**Solution:**
1. Increase system memory
2. Process files in smaller batches
3. Check `MAX_FILE_SIZE` configuration
4. Monitor memory usage during processing

#### Issue: PDF parsing fails
**Solution:**
1. Verify PDF is not password protected
2. Check PDF is not corrupted
3. Try with different PDF files
4. Check Document AI processor configuration

### Network and Connectivity Issues

#### Issue: SSL certificate errors
**Solution:**
1. Update certificates: `pip install --upgrade certifi`
2. Check system date/time
3. Verify network proxy settings
4. Use `--trusted-host` for pip if needed

#### Issue: Timeout errors
**Solution:**
1. Increase timeout values in configuration
2. Check network connectivity
3. Verify firewall settings
4. Test with smaller files first

#### Issue: Rate limiting errors
**Solution:**
1. Implement exponential backoff
2. Reduce concurrent requests
3. Check API rate limits
4. Add delays between requests

### VS Code Integration Issues

#### Issue: Python interpreter not found in VS Code
**Solution:**
1. Open Command Palette (Ctrl+Shift+P)
2. Type "Python: Select Interpreter"
3. Choose the virtual environment interpreter
4. Path should be: `.\venv\Scripts\python.exe`

#### Issue: Terminal not activating virtual environment
**Solution:**
1. Set default terminal to Command Prompt
2. Or manually activate: `venv\Scripts\activate.bat`
3. Check execution policy: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

#### Issue: Extensions not working properly
**Solution:**
1. Reload VS Code window
2. Update extensions to latest versions
3. Check extension compatibility
4. Disable conflicting extensions

### Performance Issues

#### Issue: Slow file processing
**Solution:**
1. Increase worker threads in configuration
2. Process files in smaller batches
3. Check system resources (CPU, memory)
4. Optimize file sizes before processing

#### Issue: Dashboard loading slowly
**Solution:**
1. Build for production: `npm run build`
2. Check network tab in browser dev tools
3. Optimize images and assets
4. Enable compression in Next.js config

#### Issue: High memory usage
**Solution:**
1. Monitor memory usage with Task Manager
2. Reduce batch sizes
3. Implement garbage collection
4. Check for memory leaks

### Logging and Debugging

#### Issue: No logs appearing
**Solution:**
1. Check log level configuration
2. Verify log file permissions
3. Check log directory exists
4. Enable console logging for debugging

#### Issue: Unclear error messages
**Solution:**
1. Enable debug mode: `DEBUG=true`
2. Increase log level to DEBUG
3. Check full stack traces
4. Use verbose logging options

### Data and Currency Issues

#### Issue: Currency not displaying as Rands (R)
**Solution:**
1. Verify currency replacement was successful
2. Check template files for hardcoded $ symbols
3. Clear browser cache
4. Restart dashboard after changes

#### Issue: Price formatting issues
**Solution:**
1. Check number formatting in code
2. Verify decimal places configuration
3. Test with different price values
4. Check locale settings

## Diagnostic Commands

### System Information
```bash
# Check Python version and location
python --version
where python

# Check Node.js version and location
node --version
where node

# Check npm version
npm --version

# Check installed Python packages
pip list

# Check installed Node packages
npm list
```

### Network Diagnostics
```bash
# Test Google Cloud connectivity
ping storage.googleapis.com

# Test OpenCart connectivity
ping your-store.com

# Check port availability
netstat -ano | findstr :3000
netstat -ano | findstr :8000
```

### File System Diagnostics
```bash
# Check file permissions
icacls filename.txt

# Check disk space
dir C:\ /-c

# Check environment variables
echo %PATH%
set | findstr GOOGLE
```

## Getting Additional Help

### Log Collection
When reporting issues, collect the following logs:
1. Python application logs: `audico_product_manager/logs/`
2. Dashboard logs: `audico_dashboard/app/dev.log`
3. VS Code output panel logs
4. Windows Event Viewer logs (if system-related)

### System Information
Include the following system information:
- Windows version: `winver`
- Python version: `python --version`
- Node.js version: `node --version`
- Available memory and disk space
- Antivirus software in use

### Error Reporting Template
```
**Issue Description:**
Brief description of the problem

**Steps to Reproduce:**
1. Step one
2. Step two
3. Step three

**Expected Behavior:**
What should happen

**Actual Behavior:**
What actually happens

**Error Messages:**
Full error messages and stack traces

**System Information:**
- Windows version:
- Python version:
- Node.js version:
- VS Code version:

**Configuration:**
- Relevant .env variables (without sensitive data)
- Custom configuration changes
```

### Emergency Recovery

#### Complete System Reset
If the system is completely broken:
1. Delete virtual environment: `rmdir /s venv`
2. Delete node_modules: `rmdir /s node_modules`
3. Re-run setup scripts
4. Restore configuration from backup

#### Configuration Backup
Always keep backups of:
- `.env` files (without sensitive data)
- Custom configuration files
- Working system state
- Important log files

---

For issues not covered in this guide, check the system logs and consider running the system in debug mode for more detailed error information.
