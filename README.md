# Mist Automation Project

A comprehensive automation system for generating Mist endpoint reports with Telegram notifications, configuration encryption, and advanced scheduling capabilities.

## Features

- **Enhanced Endpoint Reporting**: Pull User MACs and NAC Clients data from Mist API
- **Multiple Output Formats**: HTML, CSV, JSON, and Excel reports with customizable themes
- **Configuration Encryption**: Secure storage of API tokens and sensitive configuration
- **Telegram Notifications**: Automated notifications for report success, failures, and changes
- **Historical Tracking**: SQLite database for tracking report history and system health
- **Scheduling Support**: Built-in scheduling for automated report generation
- **Advanced Filtering**: Filter reports by site, connection type, and date ranges
- **Interactive HTML Reports**: Sortable tables with statistics dashboard

## Requirements

```bash
pip install requests pandas openpyxl configparser cryptography python-telegram-bot schedule
```

## Project Structure

```
├── mist_automation.py          # Main automation wrapper with Telegram notifications
├── mist_endpoint_report.py     # Core Mist API report generator
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
python3.13 mist_automation.py --setup
python3.13 mist_endpoint_report.py --create-config
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
python3.13 mist_automation.py --create-key

# Encrypt configuration files
python3.13 mist_automation.py --encrypt-configs
```

### 4. Test Integration

```bash
# Test Telegram notifications
python3.13 mist_automation.py --test-telegram

# Generate a test report
python3.13 mist_automation.py --run
```

## Usage

### Basic Report Generation

```bash
# Generate report with default settings
python3.13 mist_endpoint_report.py

# Generate report with command line options
python3.13 mist_endpoint_report.py --days 14 --theme sunset --format html,csv,json

# Filter by site or connection type
python3.13 mist_endpoint_report.py --site SITE_ID --connection-type wireless
```

### Automation Features

```bash
# Run single report with automation features
python3.13 mist_automation.py --run

# View system health
python3.13 mist_automation.py --health

# Manual cleanup of old files
python3.13 mist_automation.py --cleanup
```

### Configuration Management

```bash
# Encrypt existing configurations
python3.13 mist_automation.py --encrypt-configs

# Decrypt for editing (remember to re-encrypt!)
python3.13 mist_automation.py --decrypt-configs

# Create new encryption key
python3.13 mist_automation.py --create-key
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

## Report Themes

Available themes for HTML reports:

- **default**: Clean blue theme
- **sunset**: Orange/red gradient
- **ocean**: Deep blue theme
- **forest**: Green nature theme
- **dark**: Dark mode theme
- **corporate**: Professional blue theme

## Output Formats

- **HTML**: Interactive web report with sorting and statistics
- **CSV**: Raw data for spreadsheet analysis
- **JSON**: Structured data with metadata and statistics
- **Excel**: Multi-sheet workbook with data and breakdowns

## Security Features

### Configuration Encryption

The project supports two encryption methods:

1. **Key File Based** (Recommended for automation)
   ```bash
   python3.13 mist_automation.py --create-key
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

- **Success Reports**: Statistics and completion notifications
- **Error Alerts**: Failure notifications with details
- **Change Alerts**: Significant changes in endpoint counts

## Database Schema

The SQLite database tracks:

- **reports**: Report metadata, statistics, and success status
- **health_log**: System health and performance metrics

## Error Handling

- Comprehensive logging to `Logs/mist_automation.log`
- Automatic retry mechanisms for API calls
- Graceful handling of rate limits and timeouts
- Health monitoring and alerting

## Environment Variables

Optional environment variables:

- `MIST_CONFIG_PASSWORD`: Password for encrypted configs
- Configure in your shell or automation system

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
- Ensure cryptography library is installed: `pip install cryptography`
- Verify encryption key file exists and is readable

**Telegram Errors**
- Test bot connection with `--test-telegram`
- Verify bot token and chat ID are correct

**Missing Data**
- Check date range (--days parameter)
- Verify site filters are correct
- Ensure NAC is enabled in Mist configuration

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