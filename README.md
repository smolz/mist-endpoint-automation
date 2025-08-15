# Mist Automation Project

A comprehensive automation system for generating Mist endpoint reports with IP address tracking, Telegram notifications, configuration encryption, and advanced scheduling capabilities.

## Features

- **Enhanced Endpoint Reporting**: Pull User MACs and NAC Clients data from Mist API with IP address tracking
- **IP Address Visibility**: Track last known IP addresses for network troubleshooting and analysis
- **Multiple Output Formats**: HTML, CSV, JSON, and Excel reports with customizable themes
- **Configuration Encryption**: Secure storage of API tokens and sensitive configuration
- **Telegram Notifications**: Automated notifications for report success, failures, and changes
- **Historical Tracking**: SQLite database for tracking report history and system health
- **Configurable Python Execution**: Support for multiple Python versions and environments
- **Scheduling Support**: Built-in scheduling for automated report generation
- **Advanced Filtering**: Filter reports by site, connection type, and date ranges
- **Interactive HTML Reports**: Sortable tables with statistics dashboard, real-time filtering, and IP address coverage

## Requirements

```bash
pip3 install requests pandas openpyxl configparser cryptography python-telegram-bot schedule
```

> **Note for Windows Users:** On Windows, you may need to use `python` instead of `python3` and `pip` instead of `pip3` in all commands.

## Project Structure

```
├── mist_automation.py          # Main automation wrapper with Telegram notifications
├── mist_endpoint_report.py     # Core Mist API report generator with IP address support
├── config_encryption.py       # Configuration file encryption module
├── Resources/                  # Configuration and encrypted files
│   ├── mist_config.ini.enc    # Encrypted Mist API configuration
│   ├── automation_config.ini.enc # Encrypted automation settings
│   ├── encryption.key         # Encryption key file
│   └── mist_history.db        # Historical tracking database
├── Reports/                    # Generated reports
├── Logs/                      # Application logs
└── Archive/                   # Archived files
```

## Quick Start

### 1. Initial Setup

Create sample configuration files:

```bash
python3 mist_automation.py --setup
python3 mist_endpoint_report.py --create-config
```

### 2. Configure API Credentials

Edit the generated configuration files with your Mist API credentials:

- **API Token**: Get from Mist Portal → Organization → API Tokens
- **Organization ID**: Found in your Mist portal URL after `org_id=`
- **Telegram Bot Token**: Get from @BotFather on Telegram
- **Chat ID**: Get from @userinfobot on Telegram

### 3. Encrypt Configuration (Recommended)

```bash
# Create encryption key
python3 mist_automation.py --create-key

# Encrypt configuration files
python3 mist_automation.py --encrypt-configs
```

### 4. Test Integration

```bash
# Test Telegram notifications
python3 mist_automation.py --test-telegram

# Generate a test report
python3 mist_automation.py --run
```

## Usage

### Basic Report Generation

```bash
# Generate report with default settings (includes IP addresses)
python3 mist_endpoint_report.py

# Generate report with command line options
python3 mist_endpoint_report.py --days 14 --theme sunset --format html,csv,json

# Filter by site or connection type
python3 mist_endpoint_report.py --site SITE_ID --connection-type wireless
```

### Automation Features

```bash
# Run single report with automation features
python3 mist_automation.py --run

# View system health
python3 mist_automation.py --health

# Manual cleanup of old files
python3 mist_automation.py --cleanup

# Use specific Python version (especially useful on macOS)
python3 mist_automation.py --python python3.13 --run
```

### Configuration Management

```bash
# Encrypt existing configurations
python3 mist_automation.py --encrypt-configs

# Decrypt for editing (remember to re-encrypt!)
python3 mist_automation.py --decrypt-configs

# Create new encryption key
python3 mist_automation.py --create-key
```

## Configuration Files

### Mist API Configuration (`Resources/mist_config.ini`)

```ini
[mist]
api_token = your_api_token_here
org_id = your_org_id_here
base_url = https://api.mist.com
theme = default
days = 7
```

### Automation Configuration (`Resources/automation_config.ini`)

```ini
[telegram]
bot_token = YOUR_BOT_TOKEN_HERE
chat_id = YOUR_CHAT_ID_HERE
send_success_reports = true
send_error_alerts = true
send_change_alerts = true

[mist]
script_path = ./mist_endpoint_report.py
config_path = Resources/mist_config.ini
python_executable = python3
output_formats = html,json
theme = default

[reports]
directory = Reports
keep_days = 30

[database]
path = mist_history.db
keep_days = 90

[scheduling]
enabled = true
daily_time = 06:00
cleanup_time = 02:00
```

## Python Version Configuration

The system supports configurable Python execution, essential for environments with multiple Python versions (especially macOS):

### Configuration Methods (in order of priority):

1. **Command Line Override**:
   ```bash
   python3 mist_automation.py --python python3.13 --run
   ```

2. **Environment Variable**:
   ```bash
   export MIST_PYTHON_EXECUTABLE=python3.13
   python3 mist_automation.py --run
   ```

3. **Configuration File**:
   ```ini
   [mist]
   python_executable = python3.13
   ```

4. **Auto-Detection**: System automatically detects best available Python

### Platform-Specific Notes:

- **macOS**: Often requires specific version (e.g., `python3.13`)
- **Linux**: Usually `python3` works fine
- **Windows**: May need `python` instead of `python3`

## Report Themes

Available themes for HTML reports:

- **default**: Clean blue theme
- **sunset**: Orange/red gradient
- **ocean**: Deep blue theme
- **forest**: Green nature theme
- **dark**: Dark mode theme
- **corporate**: Professional blue theme

## Output Formats

- **HTML**: Interactive web report with sorting, filtering, IP address tracking, and statistics
- **CSV**: Raw data for spreadsheet analysis including IP addresses
- **JSON**: Structured data with metadata, statistics, and IP address information
- **Excel**: Multi-sheet workbook with data, breakdowns, and IP address coverage metrics

## Enhanced HTML Features with IP Address Support

The HTML reports now include:

- **Real-time search filtering**: Find devices instantly by any field including IP address
- **Quick filter buttons**: "Show Never Seen", "Show With IP", "Show All"
- **IP address tracking**: Last known IP address for each device with special formatting
- **Enhanced statistics**: IP address coverage percentage and device counts
- **Filter statistics**: Shows "X of Y endpoints" with IP coverage info
- **Enhanced CSV download**: Exports only filtered results with IP data
- **Material Design Icons**: Professional network-specific icons including IP indicators
- **Performance info section**: Detailed statistics, breakdowns, and IP address insights

### New IP Address Features

- **🌐 IP Address Column**: Shows last known IP address for each device
- **IP Address Filtering**: "Show With IP" button to view only devices with IP data
- **Smart IP Sorting**: Intelligent numeric sorting for IP addresses
- **Coverage Statistics**: Track percentage of devices with IP address data
- **Network Troubleshooting**: Correlate devices with their network assignments

## Security Features

### Configuration Encryption

The project supports two encryption methods:

1. **Key File Based** (Recommended for automation)
   ```bash
   python3 mist_automation.py --create-key
   ```

2. **Password Based** (Interactive use)
   - Uses PBKDF2 with 100,000 iterations
   - Prompts for password when needed

### Security Best Practices

- Configuration files are encrypted by default
- Temporary decrypted files are securely overwritten
- File permissions are set to 600 (owner read/write only)
- API tokens are never logged or displayed

## Telegram Integration

### Bot Setup

1. Create bot with @BotFather on Telegram
2. Get your chat ID from @userinfobot
3. Configure in `automation_config.ini`
4. Test with `--test-telegram`

### Notification Types

- **Success Reports**: Statistics, IP address coverage, and completion notifications
- **Error Alerts**: Failure notifications with details
- **Change Alerts**: Significant changes in endpoint counts or IP assignments

## Database Schema

The SQLite database tracks:

- **reports**: Report metadata, statistics, IP address coverage, and success status
- **health_log**: System health and performance metrics

## Error Handling

- Comprehensive logging to `Logs/mist_automation.log`
- Automatic retry mechanisms for API calls
- Graceful handling of rate limits and timeouts
- Health monitoring and alerting

## Environment Variables

Optional environment variables:

- `MIST_CONFIG_PASSWORD`: Password for encrypted configs
- `MIST_PYTHON_EXECUTABLE`: Python executable to use for scripts

## Development

### Adding New Features

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Update documentation
5. Submit pull request

### API Rate Limiting

The system includes built-in rate limiting:
- 0.2 second delays between requests
- Paginated API calls with safety limits
- Automatic timeout handling

## Troubleshooting

### Common Issues

**Authentication Errors**
- Verify API token is valid and has proper permissions
- Check organization ID format (UUID)

**Encryption Errors**
- Ensure cryptography library is installed: `pip3 install cryptography`
- Verify encryption key file exists and is readable

**Telegram Errors**
- Test bot connection with `--test-telegram`
- Verify bot token and chat ID are correct

**Python Version Issues**
- Configure specific Python version in `automation_config.ini`
- Use `--python` command line override for testing
- Set `MIST_PYTHON_EXECUTABLE` environment variable
- On macOS, specify exact Python version (e.g., `python3.13`)

**Missing Data**
- Check date range (--days parameter)
- Verify site filters are correct
- Ensure NAC is enabled in Mist configuration

**IP Address Issues**
- IP addresses come from NAC clients data - devices must have connected to appear
- Increase lookback period with `--days` for more IP address coverage
- Check that devices are actually authenticating through NAC

### Logs

Check application logs for detailed error information:
```bash
tail -f Logs/mist_automation.log
```

## License

This project is provided as-is for educational and operational use. Please ensure compliance with your organization's security policies when handling API credentials.

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review application logs
3. Verify configuration settings
4. Test individual components separately

## Changelog

### Version 2.2 - IP Address Support
- **NEW**: Added IP address tracking and reporting from NAC clients data
- **NEW**: Enhanced HTML reports with IP address column and filtering
- **NEW**: IP address coverage statistics and metrics
- **NEW**: "Show With IP" filter button for quick IP address analysis
- **NEW**: Smart IP address sorting in HTML reports
- **NEW**: IP address data in all output formats (HTML, CSV, JSON, Excel)
- **Enhanced**: Statistics now include IP address coverage percentages
- **Enhanced**: Telegram notifications include IP address coverage info
- **Enhanced**: Database tracking includes IP address metrics

### Version 2.1
- Added configurable Python execution for multi-version environments
- Enhanced HTML reports with real-time filtering and Material Design icons
- Improved macOS compatibility with Python version detection
- Added environment variable support for Python executable
- Better error handling and user feedback

### Version 2.0
- Added configuration encryption
- Telegram notification system
- Historical tracking database
- Enhanced HTML reports with themes
- Comprehensive error handling
- Security improvements

### Version 1.0
- Basic Mist API integration
- HTML and CSV report generation
- Command line interface

## Business Value

### Network Visibility
- **Complete endpoint inventory** with User MACs and active NAC clients
- **IP address tracking** for network troubleshooting and planning
- **Connection type analysis** (wireless vs wired)
- **Authentication compliance** monitoring

### Operational Efficiency
- **Automated reporting** with Telegram notifications
- **Historical trending** for capacity planning
- **Security monitoring** for rogue device detection
- **Multi-format outputs** for different stakeholders

### Network Security
- **Device accountability** with MAC and IP correlation
- **Authentication monitoring** with policy rule tracking
- **Change detection** for unexpected network modifications
- **Compliance reporting** for security audits

This enhanced system now provides comprehensive network endpoint visibility including IP address tracking, making it an essential tool for network administrators, security teams, and IT operations.