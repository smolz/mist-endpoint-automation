# 🤖 Mist Report Automation Setup Guide

This guide will help you set up automated Mist endpoint reporting with Telegram notifications, change detection, cleanup, and health monitoring.

## 📋 Prerequisites

### Required Python Packages
```bash
pip3 install requests pandas python-telegram-bot configparser schedule openpyxl cryptography
```

> **Note for Windows Users:** On Windows, you may need to use `python` instead of `python3` and `pip` instead of `pip3` in all commands throughout this guide.

### Files Needed
- `mist_endpoint_report.py` (your enhanced main script)
- `mist_automation.py` (the automation wrapper)
- `config_encryption.py` (encryption module)

### Files Created During Setup
- `mist_config.ini` (your Mist API configuration) 
- `automation_config.ini` (automation settings)

## 🔧 Setup Steps

### 1. Create Telegram Bot

1. **Create a new bot:**
   - Message @BotFather on Telegram
   - Send `/newbot`
   - Choose a name and username for your bot
   - Save the **bot token** you receive

2. **Get your Chat ID:**
   - Message @userinfobot on Telegram
   - It will reply with your **chat ID**
   - Or message your new bot, then visit: `https://api.telegram.org/bot<BOT_TOKEN>/getUpdates`

### 2. Create Mist API Configuration

Before setting up automation, you need to configure your Mist API credentials:

```bash
# Create the Mist API configuration file
python3 mist_endpoint_report.py --create-config

# This creates: Resources/mist_config.ini
```

**Or create `Resources/mist_config.ini` manually:**

```ini
[mist]
api_token = your_mist_api_token_here
org_id = your_organization_id_here
base_url = https://api.mist.com
theme = default
days = 7
```

**To get your Mist API credentials:**

1. **API Token:**
   - Go to [Mist Portal](https://manage.mist.com)
   - Navigate to **Organization → API Tokens**
   - Click **Create Token**
   - Give it a name (e.g., "Endpoint Reports")
   - **Copy the token** (you won't see it again!)

2. **Organization ID:**
   - In your Mist portal, look at the URL
   - Find the part after `org_id=`
   - Example: `https://manage.mist.com/admin/?org_id=12345678-1234-1234-1234-123456789abc`
   - Your org_id is: `12345678-1234-1234-1234-123456789abc`

3. **Base URL (region-specific):**
   - **US (default):** `https://api.mist.com`
   - **EU:** `https://api.eu.mist.com`
   - **APAC:** `https://api.ac2.mist.com`
   - **Other regions:** Check Mist documentation

**Test your Mist configuration:**
```bash
# Test a basic report to verify credentials
python3 mist_endpoint_report.py --config Resources/mist_config.ini --format html --theme default
```

**🔒 Optional: Encrypt your configuration for security:**
```bash
# Method 1: Password-based encryption (prompted for password)
python3 mist_endpoint_report.py --encrypt-config

# Method 2: Key-file encryption (more secure for automation)
python3 mist_automation.py --create-key
python3 config_encryption.py --encrypt Resources/mist_config.ini --key-file Resources/encryption.key
```

### 3. Create Automation Configuration

```bash
# Create sample automation configuration file
python3 mist_automation.py --setup

# This creates: Resources/automation_config.ini
```

### 4. Edit Automation Configuration

Edit `automation_config.ini` with your actual values:

```ini
[telegram]
bot_token = 1234567890:ABCdefGhIjKlMnOpQrStUvWxYz
chat_id = 123456789
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

### 5. Configure Python Executable (Important for macOS)

The system supports configurable Python execution, which is especially important on macOS where multiple Python versions may be installed:

#### **Method 1: Configuration File (Recommended)**
Edit `Resources/automation_config.ini`:
```ini
[mist]
python_executable = python3.13  # or your specific Python version
```

#### **Method 2: Environment Variable**
```bash
export MIST_PYTHON_EXECUTABLE=python3.13
```

#### **Method 3: Command Line Override**
```bash
python3 mist_automation.py --python python3.13 --run
```

#### **Platform-Specific Notes:**
- **macOS**: Often need specific version like `python3.13` or `/usr/local/bin/python3.13`
- **Linux**: Usually `python3` works fine
- **Windows**: May need `python` instead of `python3`

### 6. Test Integration

```bash
# Test Telegram connection
python3 mist_automation.py --test-telegram

# Should send a test message to your Telegram chat
```

### 7. Test Single Run

```bash
# Run a single automated report
python3 mist_automation.py --run

# Or with specific Python version
python3 mist_automation.py --python python3.13 --run

# This will:
# - Generate a Mist report
# - Compare with previous run
# - Send Telegram notification
# - Store results in database
# - Clean up old files
```

## 🔒 Configuration Encryption

### Why Encrypt Configuration Files?

Your configuration files contain sensitive information:
- **Mist API tokens** - Access to your organization's data
- **Telegram bot tokens** - Control of your notification bot
- **Organization IDs** - Internal identifiers

### Encryption Methods

#### **Method 1: Password-Based Encryption**
```bash
# Encrypt configuration files (you'll be prompted for password)
python3 mist_automation.py --encrypt-configs

# Decrypt for editing
python3 mist_automation.py --decrypt-configs
# Edit files...
# Re-encrypt after editing
python3 mist_automation.py --encrypt-configs
```

#### **Method 2: Key-File Encryption (Recommended for Automation)**
```bash
# Create encryption key file
python3 mist_automation.py --create-key

# Encrypt using key file
python3 config_encryption.py --encrypt Resources/mist_config.ini --key-file Resources/encryption.key
python3 config_encryption.py --encrypt Resources/automation_config.ini --key-file Resources/encryption.key

# The automation will automatically use the key file if present
```

### Environment Variable Support
```bash
# Set password via environment variable (for password-based encryption)
export MIST_CONFIG_PASSWORD="your_secure_password"

# Set Python executable via environment variable
export MIST_PYTHON_EXECUTABLE="python3.13"

python3 mist_automation.py --run
```

### Security Best Practices

1. **Use key-file encryption** for automated systems
2. **Store key files separately** from config files (different servers/locations)
3. **Set restrictive permissions:**
   ```bash
   chmod 600 Resources/encryption.key
   chmod 600 Resources/*.ini.enc
   ```
4. **Don't commit keys to version control** - add to `.gitignore`:
   ```
   Resources/encryption.key
   Resources/*.ini
   Resources/*.ini.enc
   ```
5. **Regularly rotate encryption keys** and API tokens

## 🚀 Usage Options

### Manual Execution
```bash
# Single run with full automation
python3 mist_automation.py --run

# With specific Python version
python3 mist_automation.py --python python3.13 --run

# Manual cleanup
python3 mist_automation.py --cleanup

# Check system health
python3 mist_automation.py --health
```

### Scheduled Automation

The system provides guidance for setting up scheduled automation, but relies on your operating system's built-in scheduling tools:

```bash
# Get scheduling guidance
python3 mist_automation.py --schedule
```

### System Service (Linux)

Create `/etc/systemd/system/mist-automation.service`:

```ini
[Unit]
Description=Mist Endpoint Report Automation
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/your/scripts
Environment=MIST_PYTHON_EXECUTABLE=python3.13
ExecStart=/usr/bin/python3 /path/to/mist_automation.py --run
Restart=on-failure
RestartSec=30

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable mist-automation.service
sudo systemctl start mist-automation.service
sudo systemctl status mist-automation.service
```

### Cron Job (Recommended for Regular Automation)
```bash
# Edit crontab
crontab -e

# Add daily report at 6 AM (using specific Python version)
0 6 * * * cd /path/to/scripts && /usr/local/bin/python3.13 mist_automation.py --run

# Or using environment variable
0 6 * * * cd /path/to/scripts && MIST_PYTHON_EXECUTABLE=python3.13 python3 mist_automation.py --run

# Add cleanup at 2 AM
0 2 * * * cd /path/to/scripts && python3 mist_automation.py --cleanup

# Weekly health check (Mondays at 8 AM)
0 8 * * 1 cd /path/to/scripts && python3 mist_automation.py --health
```

### Windows Task Scheduler

1. Open **Task Scheduler** from Start Menu
2. Click **Create Basic Task**
3. Name: "Mist Endpoint Reports"
4. Trigger: **Daily**
5. Set time (e.g., 6:00 AM)
6. Action: **Start a program**
7. Program: `python` (or `python3`)
8. Arguments: `mist_automation.py --run`
9. Start in: `C:\path\to\your\scripts`

## 📊 Features Overview

### 📱 Telegram Notifications

**Success Reports Include:**
- ⏰ Generation time and duration
- 📈 Device statistics (total, active, compliance)
- 🔌 Connection type breakdown
- 📊 Changes from previous report
- 📄 Key insights and metrics

**Error Alerts Include:**
- 🚨 Failure notification
- ⏰ Timestamp and duration
- ❌ Error details
- 🔧 Action required message

**Health Summaries Include:**
- 📊 24-hour performance stats
- ✅ Success rate percentage
- ⚡ Average execution time
- 🏥 System health status

### 📈 Change Detection

The system tracks:
- **Device count changes** (new/removed devices)
- **Compliance rate changes** (>5% threshold)
- **Activity changes** (devices coming online/offline)
- **Connection type changes** (wireless/wired shifts)

### 🧹 Automated Cleanup

**File Cleanup:**
- Removes old report files (configurable retention)
- Keeps directory organized
- Logs cleanup activity

**Database Cleanup:**
- Purges old health logs
- Maintains historical trends
- Optimizes database size

### 🏥 Health Monitoring

**Tracks:**
- ✅ Report success/failure rates
- ⏱️ Execution duration trends
- 📊 API performance metrics
- 🔍 Error patterns

**Alerts on:**
- Report generation failures
- Slow execution times
- API connectivity issues
- System degradation

## 📂 File Structure

```
your-project/
├── mist_endpoint_report.py      # Main enhanced script
├── mist_automation.py           # Automation wrapper
├── config_encryption.py        # Encryption module
├── Resources/
│   ├── mist_config.ini         # Mist API credentials
│   ├── automation_config.ini   # Automation settings
│   ├── encryption.key          # Encryption key file
│   └── mist_history.db         # SQLite tracking database
├── Logs/
│   └── mist_automation.log     # Log file
└── Reports/                    # Generated reports
    ├── mist_endpoint_report_20241215_060001.html
    ├── mist_endpoint_report_20241215_060001.json
    └── ...
```

## 🔍 Troubleshooting

### Common Issues

**Telegram not working:**
```bash
# Check configuration
python3 mist_automation.py --test-telegram

# Verify bot token and chat ID
# Ensure bot can send messages to your chat
```

**Mist API credentials issues:**
```bash
# Test your Mist configuration first
python3 mist_endpoint_report.py --config Resources/mist_config.ini --format html

# Check API token and org_id in Resources/mist_config.ini
# Verify you're using the correct API endpoint for your region
```

**Python version issues:**
```bash
# Test with specific Python version
python3 mist_automation.py --python python3.13 --run

# Configure in automation_config.ini:
# python_executable = python3.13

# Set environment variable:
# export MIST_PYTHON_EXECUTABLE=python3.13

# Check which Python versions are available:
ls /usr/bin/python*
which python3.13
```

**Report generation fails:**
```bash
# Verify script paths in automation_config.ini
# Check log file: Logs/mist_automation.log
# Ensure correct Python executable is configured
# Test individual components separately
```

**Scheduling not working:**
```bash
# Check scheduler status (for cron):
systemctl status cron  # Linux
launchctl list | grep cron  # macOS

# Verify cron syntax
crontab -l

# Check system service status (if using systemd)
systemctl status mist-automation.service
```

**Encryption errors:**
```bash
# Ensure cryptography is installed
pip3 install cryptography

# Check key file permissions
ls -la Resources/encryption.key

# Test encryption separately
python3 config_encryption.py --encrypt Resources/mist_config.ini
```

### Advanced Troubleshooting

**Database issues:**
```bash
# Check database health
python3 mist_automation.py --health

# Inspect database directly (if needed)
sqlite3 Resources/mist_history.db ".tables"
sqlite3 Resources/mist_history.db "SELECT * FROM health_log ORDER BY timestamp DESC LIMIT 5;"
```

**Network connectivity:**
```bash
# Test Mist API connectivity
curl -H "Authorization: Token YOUR_TOKEN" https://api.mist.com/api/v1/orgs/YOUR_ORG_ID/sites

# Test Telegram API connectivity
curl https://api.telegram.org/botYOUR_BOT_TOKEN/getMe
```

### Log Files

**Main automation log:**
```bash
tail -f Logs/mist_automation.log
```

**Check specific log entries:**
```bash
grep ERROR Logs/mist_automation.log
grep SUCCESS Logs/mist_automation.log
```

**Log rotation (prevent large files):**
```bash
# Add to your cron to rotate logs monthly
0 0 1 * * mv /path/to/Logs/mist_automation.log /path/to/Logs/mist_automation.log.$(date +\%Y\%m) && touch /path/to/Logs/mist_automation.log
```

## 🔐 Security Notes

- **Use encryption** for all configuration files containing sensitive data
- **Store encryption keys separately** from encrypted config files
- **Set restrictive permissions:** `chmod 600 Resources/encryption.key Resources/*.ini.enc`
- **Use environment variables** for passwords in production environments
- **Don't commit sensitive files** to version control (use `.gitignore`)
- **Regularly rotate** API tokens and encryption keys
- **Use key-file encryption** for automated/scheduled operations
- **Monitor access logs** and set up alerts for unusual activity

## 🎯 Advanced Configuration

### Custom Thresholds
Edit `automation_config.ini` to adjust:
- Change detection sensitivity
- Health monitoring thresholds
- Cleanup retention periods
- Notification preferences

### Multiple Environments
Use different config files:
```bash
python3 mist_automation.py --config Resources/production_config.ini --run
python3 mist_automation.py --config Resources/staging_config.ini --run
```

### Integration with Monitoring Systems

The SQLite database can be queried by external monitoring tools:
```sql
-- Check recent failures
SELECT * FROM health_log WHERE status = 'failure' ORDER BY timestamp DESC;

-- Calculate average performance
SELECT AVG(duration_seconds) FROM health_log WHERE timestamp > datetime('now', '-7 days');

-- Check compliance trends
SELECT timestamp, compliance_rate FROM reports ORDER BY timestamp DESC LIMIT 10;
```

### Custom Notification Templates

For advanced users, you can modify the notification messages in `mist_automation.py`:
- Success notification format
- Error alert templates
- Health summary layout
- Add custom metrics or branding

### Performance Optimization

**For large organizations:**
```ini
# In automation_config.ini
[mist]
days = 7  # Reduce lookback period
output_formats = html  # Generate fewer formats

[reports]
keep_days = 14  # Shorter retention period

[database]
keep_days = 30  # Less historical data
```

**For high-frequency reporting:**
```bash
# Use specific Python version for consistency
export MIST_PYTHON_EXECUTABLE=/usr/local/bin/python3.13

# Schedule more frequent cleanup
0 */6 * * * cd /path/to/scripts && python3 mist_automation.py --cleanup
```

## 🌐 Multi-Region Setup

For organizations with multiple Mist regions:

**Create separate configs:**
```bash
# US configuration
cp Resources/mist_config.ini Resources/mist_config_us.ini
# Edit base_url to https://api.mist.com

# EU configuration  
cp Resources/mist_config.ini Resources/mist_config_eu.ini
# Edit base_url to https://api.eu.mist.com

# Schedule separate runs
0 6 * * * cd /path/to/scripts && python3 mist_automation.py --config Resources/automation_config_us.ini --run
0 7 * * * cd /path/to/scripts && python3 mist_automation.py --config Resources/automation_config_eu.ini --run
```

## 📞 Support and Maintenance

### Regular Maintenance Tasks

**Weekly:**
- Review generated reports for insights
- Check system health
- Monitor Telegram notifications

**Monthly:**
- Run manual cleanup
- Review log files
- Check disk space usage
- Verify API token validity

**Quarterly:**
- Rotate API tokens
- Update Python dependencies
- Review and update configuration
- Test disaster recovery procedures

### Getting Help

For issues:
1. Check log files first (`Logs/mist_automation.log`)
2. Verify configuration settings
3. Test individual components separately
4. Review Telegram bot permissions
5. Check network connectivity
6. Consult the troubleshooting section above

### Monitoring Checklist

- [ ] Telegram notifications working
- [ ] Reports generating successfully
- [ ] Database tracking properly
- [ ] Cleanup running regularly
- [ ] Python version configured correctly
- [ ] API credentials valid
- [ ] Encryption working properly
- [ ] Scheduling configured
- [ ] Log files being created
- [ ] Health metrics reasonable

## 🎉 You're Ready!

Once you've completed this setup guide, your Mist automation system will:

✅ **Generate comprehensive endpoint reports**
✅ **Send Telegram notifications**
✅ **Track historical data and trends**
✅ **Automatically clean up old files**
✅ **Monitor system health**
✅ **Protect sensitive configuration data**
✅ **Work reliably across different Python versions**

**Next Steps:**
1. Set up your preferred scheduling method (cron/Task Scheduler)
2. Monitor the first few automated runs
3. Adjust configuration based on your needs
4. Explore the advanced features as you become comfortable

Happy automated reporting! 🎉

---

**Need help?** Check the troubleshooting section or review the detailed User Guide for more information on day-to-day usage and advanced features.