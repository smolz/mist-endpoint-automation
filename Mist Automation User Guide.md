# Mist Automation User Guide

Welcome to the Mist Automation System! This guide will walk you through everything you need to know to set up and use this powerful endpoint reporting tool with comprehensive IP address tracking.

## Table of Contents

- [Mist Automation User Guide](#mist-automation-user-guide)
  - [Table of Contents](#table-of-contents)
  - [What This System Does](#what-this-system-does)
  - [Before You Start](#before-you-start)
    - [What You'll Need](#what-youll-need)
    - [Install Required Software](#install-required-software)
  - [Step-by-Step Setup](#step-by-step-setup)
    - [Step 1: Download and Prepare](#step-1-download-and-prepare)
    - [Step 2: Get Your Mist API Credentials](#step-2-get-your-mist-api-credentials)
    - [Step 3: Set Up Telegram Notifications (Optional)](#step-3-set-up-telegram-notifications-optional)
    - [Step 4: Create Configuration Files](#step-4-create-configuration-files)
    - [Step 5: Configure Your Settings](#step-5-configure-your-settings)
      - [Edit `Resources/mist_config.ini`:](#edit-resourcesmist_configini)
      - [Edit `Resources/automation_config.ini`:](#edit-resourcesautomation_configini)
    - [Step 6: Secure Your Configuration (Highly Recommended)](#step-6-secure-your-configuration-highly-recommended)
    - [Step 7: Test Everything](#step-7-test-everything)
  - [Command Reference](#command-reference)
    - [Main Automation Commands](#main-automation-commands)
      - [`python3 mist_automation.py [options]`](#python3-mist_automationpy-options)
      - [Detailed Main Automation Command Explanations](#detailed-main-automation-command-explanations)
    - [Report Generation Commands](#report-generation-commands)
      - [`python3 mist_endpoint_report.py [options]`](#python3-mist_endpoint_reportpy-options)
    - [Configuration Management Commands](#configuration-management-commands)
      - [`python3 config_encryption.py [options]`](#python3-config_encryptionpy-options)
      - [Detailed Option Explanations](#detailed-option-explanations)
  - [Daily Usage](#daily-usage)
    - [Generating Reports](#generating-reports)
      - [Quick Report (Default Settings)](#quick-report-default-settings)
      - [Custom Report Options](#custom-report-options)
      - [Available Themes](#available-themes)
    - [Using Automation Features](#using-automation-features)
      - [Single Report with Notifications](#single-report-with-notifications)
      - [Check System Health](#check-system-health)
      - [Clean Up Old Files](#clean-up-old-files)
  - [Understanding Your Reports](#understanding-your-reports)
    - [HTML Report Features](#html-report-features)
    - [Understanding the Data](#understanding-the-data)
      - [Connection Types](#connection-types)
      - [Authentication Status](#authentication-status)
      - [Activity Status](#activity-status)
      - [IP Address Information](#ip-address-information)
  - [Configuration Options Explained](#configuration-options-explained)
    - [Mist Configuration Options](#mist-configuration-options)
      - [Option Details:](#option-details)
    - [Automation Configuration Options](#automation-configuration-options)
      - [Telegram Section:](#telegram-section)
      - [Mist Section:](#mist-section)
      - [Reports Section:](#reports-section)
      - [Database Section:](#database-section)
      - [Scheduling Section:](#scheduling-section)
      - [Configuration Best Practices:](#configuration-best-practices)
  - [Maintenance Tasks](#maintenance-tasks)
    - [Weekly Tasks](#weekly-tasks)
    - [Monthly Tasks](#monthly-tasks)
    - [Updating Configuration](#updating-configuration)
  - [Troubleshooting](#troubleshooting)
    - [Common Issues and Solutions](#common-issues-and-solutions)
      - ["Authentication failed" or "Invalid token"](#authentication-failed-or-invalid-token)
      - ["No data found" or empty reports](#no-data-found-or-empty-reports)
      - [Telegram notifications not working](#telegram-notifications-not-working)
      - ["Encryption failed" errors](#encryption-failed-errors)
      - [Reports are empty or missing devices](#reports-are-empty-or-missing-devices)
      - [Low IP address coverage](#low-ip-address-coverage)
      - [Python version issues](#python-version-issues)
    - [Getting Help](#getting-help)
    - [Log Files](#log-files)
  - [Advanced Features](#advanced-features)
    - [Filtering Reports](#filtering-reports)
    - [IP Address Analysis](#ip-address-analysis)
    - [Scheduling (Advanced Users)](#scheduling-advanced-users)
      - [macOS/Linux with cron:](#macoslinux-with-cron)
      - [Windows with Task Scheduler:](#windows-with-task-scheduler)
    - [Multiple Output Formats](#multiple-output-formats)
  - [Security Best Practices](#security-best-practices)
  - [Tips for Better Reports](#tips-for-better-reports)
  - [Getting the Most Value](#getting-the-most-value)
    - [Regular Review Questions](#regular-review-questions)
    - [Using Reports for Security](#using-reports-for-security)
      - [**IP Address Correlation for Security**](#ip-address-correlation-for-security)
      - [**Enhanced Security Monitoring**](#enhanced-security-monitoring)
    - [Network Troubleshooting Workflows](#network-troubleshooting-workflows)
      - [**Device Connectivity Issues**](#device-connectivity-issues)
      - [**DHCP and IP Assignment Problems**](#dhcp-and-ip-assignment-problems)
      - [**Network Policy Compliance**](#network-policy-compliance)
      - [**Performance and Capacity Planning**](#performance-and-capacity-planning)
      - [**When IP Coverage is Low**](#when-ip-coverage-is-low)

## What This System Does

The Mist Automation System helps you:
- 📊 Generate comprehensive reports of all your network endpoints **with IP address tracking**
- 🌐 **Track last known IP addresses for network troubleshooting and planning**
- 🔐 Keep your API credentials secure with encryption
- 📱 Get Telegram notifications when reports complete
- 📈 Track changes and trends over time
- ⏰ Schedule automatic report generation
- 🎨 Create beautiful, interactive HTML reports **with IP address visibility**

## Before You Start

### What You'll Need

1. **Mist API Access**
   - Admin access to your Mist organization
   - Ability to create API tokens

2. **Telegram (Optional but Recommended)**
   - Telegram account for receiving notifications
   - Ability to create a bot

3. **Python Environment**
   - Python 3.8 or newer
   - Terminal/command line access

### Install Required Software

```bash
pip3 install requests pandas openpyxl configparser cryptography python-telegram-bot schedule
```

> **Note for Windows Users:** On Windows, you may need to use `python` instead of `python3` and `pip` instead of `pip3` in all commands throughout this guide.

## Step-by-Step Setup

### Step 1: Download and Prepare

1. Download or clone the project files to your computer
2. Open a terminal and navigate to the project folder
3. Verify the files are there:
   ```bash
   ls
   # You should see: mist_automation.py, mist_endpoint_report.py, config_encryption.py, etc.
   ```

### Step 2: Get Your Mist API Credentials

1. **Log into your Mist Portal**
   - Go to https://manage.mist.com
   - Log in with your admin account

2. **Create an API Token**
   - Click on your organization name
   - Go to **Settings** → **API Tokens**
   - Click **Create Token**
   - Give it a name like "Endpoint Reporting"
   - Select the needed permissions (at minimum: read access to organizations, sites, and clients)
   - **Copy and save the token** - you won't see it again!

3. **Find Your Organization ID**
   - Look at your browser URL
   - Find the part that says `org_id=` followed by a long string
   - Example: `org_id=12345678-1234-1234-1234-123456789abc`
   - **Copy and save this ID**

### Step 3: Set Up Telegram Notifications (Optional)

1. **Create a Telegram Bot**
   - Open Telegram and search for `@BotFather`
   - Send `/start` to BotFather
   - Send `/newbot` and follow the prompts
   - Choose a name like "Mist Reports Bot"
   - **Copy and save the bot token**

2. **Get Your Chat ID**
   - Search for `@userinfobot` in Telegram
   - Send `/start` to this bot
   - It will reply with your user information
   - **Copy and save your Chat ID** (the number)

3. **Start Your Bot**
   - Find your new bot in Telegram
   - Send `/start` to activate it

### Step 4: Create Configuration Files

Run this command to create sample configuration files:

```bash
python3 mist_automation.py --setup
```

This creates two files in the `Resources` folder:
- `mist_config.ini` - Mist API settings
- `automation_config.ini` - Automation and Telegram settings

### Step 5: Configure Your Settings

Edit the configuration files with your information:

#### Edit `Resources/mist_config.ini`:
```ini
[mist]
api_token = YOUR_ACTUAL_API_TOKEN_HERE
org_id = YOUR_ACTUAL_ORG_ID_HERE
base_url = https://api.mist.com
theme = default
days = 7
```

#### Edit `Resources/automation_config.ini`:
```ini
[telegram]
bot_token = YOUR_ACTUAL_BOT_TOKEN_HERE
chat_id = YOUR_ACTUAL_CHAT_ID_HERE
send_success_reports = true
send_error_alerts = true
send_change_alerts = true

[mist]
script_path = ./mist_endpoint_report.py
config_path = Resources/mist_config.ini
python_executable = python3
output_formats = html,csv
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

### Step 6: Secure Your Configuration (Highly Recommended)

Encrypt your configuration files to keep your credentials safe:

```bash
# Create an encryption key
python3 mist_automation.py --create-key

# Encrypt your configuration files
python3 mist_automation.py --encrypt-configs
```

When prompted, choose to delete the plain text files for security.

### Step 7: Test Everything

Test your Telegram setup:
```bash
python3 mist_automation.py --test-telegram
```

Generate your first report:
```bash
python3 mist_automation.py --run
```

## Command Reference

### Main Automation Commands

#### `python3 mist_automation.py [options]`

| Command | Description | Example |
|---------|-------------|---------|
| `--setup` | Creates sample configuration files in Resources/ directory | `python3 mist_automation.py --setup` |
| `--run` | Runs a single report with full automation features including notifications | `python3 mist_automation.py --run` |
| `--test-telegram` | Tests Telegram bot integration and sends test message | `python3 mist_automation.py --test-telegram` |
| `--health` | Shows detailed system health summary for last 24 hours | `python3 mist_automation.py --health` |
| `--cleanup` | Manually cleans up old reports and database entries based on config | `python3 mist_automation.py --cleanup` |
| `--create-key` | Creates a new encryption key file for securing configurations | `python3 mist_automation.py --create-key` |
| `--encrypt-configs` | Encrypts existing configuration files for security | `python3 mist_automation.py --encrypt-configs` |
| `--decrypt-configs` | Decrypts configuration files for editing (remember to re-encrypt!) | `python3 mist_automation.py --decrypt-configs` |
| `--config FILE` | Specifies custom automation config file path | `python3 mist_automation.py --config custom.ini --run` |
| `--python EXECUTABLE` | Python executable to use for running scripts | `python3 mist_automation.py --python python3.13 --run` |

#### Detailed Main Automation Command Explanations

**`--setup`**
- Creates two sample configuration files: `automation_config.ini` and references to `mist_config.ini`
- Places files in the `Resources/` directory (creates if doesn't exist)
- Includes all configuration sections with default values and helpful comments
- Safe to run multiple times - won't overwrite existing files
- Essential first step for any new installation

**`--run`**
- Executes a complete automated report generation cycle with IP address tracking
- Runs the mist_endpoint_report.py script with configured settings
- Sends Telegram notifications based on success/failure including IP coverage data
- Records statistics and performance data in the historical database
- Compares results with previous runs to detect significant changes
- Much more comprehensive than running mist_endpoint_report.py directly
- Recommended for all automated/scheduled operations

**`--test-telegram`**
- Validates your Telegram bot configuration without generating reports
- Tests bot token validity and chat connectivity
- Sends a formatted test message to verify notifications work
- Checks bot permissions and chat accessibility
- Returns clear success/failure status
- Essential for troubleshooting notification issues
- Run this before setting up automation to ensure notifications work

**`--health`**
- Analyzes system performance and reliability over the last 24 hours
- Shows success/failure rates for report generation
- Displays average execution times and performance trends
- Identifies patterns that might indicate system issues
- Provides overall system status rating (Excellent/Good/Needs Attention/Critical)
- Useful for monitoring automated systems and identifying problems early
- Data comes from the historical tracking database

**`--cleanup`**
- Removes old report files based on the `keep_days` setting in configuration
- Purges old database entries beyond the configured retention period
- Prevents disk space issues from accumulating reports over time
- Operates on both the Reports/ directory and the SQLite database
- Shows detailed information about what was cleaned up
- Safe to run manually or include in scheduled maintenance
- Respects configuration settings - won't delete more than intended

**`--create-key`**
- Generates a new 512-bit random encryption key for securing configuration files
- Creates the key file in `Resources/encryption.key` with restrictive permissions (600)
- Uses cryptographically secure random number generation
- Key file method is more secure than password-based encryption for automation
- Required before using `--encrypt-configs` if you want key-file encryption
- Keep this file secure - it's needed to decrypt your configurations

**`--encrypt-configs`**
- Encrypts both `mist_config.ini` and `automation_config.ini` files
- Uses either the encryption key file or prompts for a password
- Creates `.enc` versions and optionally removes plaintext files
- Uses AES-256 encryption with secure key derivation
- Essential for protecting API tokens and sensitive configuration data
- Encrypted files can be used directly by the system - no manual decryption needed

**`--decrypt-configs`**
- Temporarily decrypts configuration files for editing
- Creates plaintext versions of encrypted `.enc` files
- Warns you to re-encrypt after making changes
- Useful for updating API tokens, changing settings, or troubleshooting
- Uses the same encryption key or password used for encryption
- Remember to run `--encrypt-configs` again after editing

**`--config FILE`**
- Overrides the default automation configuration file location
- Useful for testing different configurations or managing multiple environments
- File path can be relative or absolute
- If no directory specified, looks in Resources/ folder
- Automatically detects and uses encrypted versions (.enc files)
- Allows running different automation profiles for different purposes

**`--python EXECUTABLE`**
- Overrides the Python executable used to run the report generation script
- Essential for systems with multiple Python versions (especially macOS)
- Examples: `python3.13`, `python3.12`, `/usr/local/bin/python3`
- Can also be configured in automation_config.ini or via environment variable
- Useful when the default `python3` doesn't work or points to wrong version

### Report Generation Commands

#### `python3 mist_endpoint_report.py [options]`

| Command | Description | Example |
|---------|-------------|---------|
| `--token TOKEN` | Specifies API token (overrides config) | `python3 mist_endpoint_report.py --token abc123` |
| `--org-id ORG_ID` | Specifies organization ID (overrides config) | `python3 mist_endpoint_report.py --org-id uuid-here` |
| `--config FILE` | Uses specific configuration file | `python3 mist_endpoint_report.py --config custom_config.ini` |
| `--days N` | Number of days to look back for NAC data and IP addresses | `python3 mist_endpoint_report.py --days 30` |
| `--theme THEME` | Report visual theme | `python3 mist_endpoint_report.py --theme sunset` |
| `--site SITE_ID` | Filters results to specific site | `python3 mist_endpoint_report.py --site abc-123-def` |
| `--connection-type TYPE` | Filters by connection type (wired/wireless) | `python3 mist_endpoint_report.py --connection-type wireless` |
| `--format FORMATS` | Output formats with IP address data (comma-separated) | `python3 mist_endpoint_report.py --format html,csv,json` |
| `--base-url URL` | API base URL for different regions | `python3 mist_endpoint_report.py --base-url https://api.eu.mist.com` |
| `--create-config` | Creates sample Mist configuration file | `python3 mist_endpoint_report.py --create-config` |
| `--encrypt-config` | Encrypts existing Mist configuration | `python3 mist_endpoint_report.py --encrypt-config` |
| `--decrypt-config` | Decrypts Mist configuration for editing | `python3 mist_endpoint_report.py --decrypt-config` |

### Configuration Management Commands

#### `python3 config_encryption.py [options]`

| Command | Description | Example |
|---------|-------------|---------|
| `--encrypt FILE` | Encrypts a specific configuration file | `python3 config_encryption.py --encrypt config.ini` |
| `--decrypt FILE` | Decrypts a specific configuration file | `python3 config_encryption.py --decrypt config.ini.enc` |
| `--create-key FILE` | Creates encryption key at specified path | `python3 config_encryption.py --create-key mykey.key` |
| `--key-file FILE` | Uses specific key file for encryption | `python3 config_encryption.py --encrypt config.ini --key-file mykey.key` |
| `--output FILE` | Specifies output file path | `python3 config_encryption.py --encrypt config.ini --output encrypted.enc` |

#### Detailed Option Explanations

**Days (`--days N`)**
- Controls how far back to search for NAC client activity and IP address assignments
- Default: 7 days
- Recommended: 7-14 days for active networks, 30+ for less active or better IP coverage
- Higher values = more comprehensive IP data but slower reports
- **IP Impact**: More days = better chance of capturing IP addresses for infrequently connecting devices

**Themes (`--theme THEME`)**
- Changes visual appearance of HTML reports including IP address display
- Available: `default`, `sunset`, `ocean`, `forest`, `dark`, `corporate`
- Affects colors, gradients, and overall styling including IP address formatting
- Choose based on your organization's branding or preference

**Output Formats (`--format FORMATS`)**
- `html`: Interactive web report with sorting, statistics, and IP address filtering
- `csv`: Raw data including IP addresses for spreadsheet analysis
- `json`: Structured data with metadata and IP address information for integration
- `excel`: Multi-sheet workbook with breakdowns and IP address coverage metrics
- Combine multiple formats: `html,csv,json`

**Connection Type Filter (`--connection-type TYPE`)**
- `wireless`: Only WiFi-connected devices (may have different IP assignment patterns)
- `wired`: Only Ethernet-connected devices (typically more stable IP assignments)
- Useful for analyzing specific infrastructure components and IP allocation strategies

**Site Filter (`--site SITE_ID`)**
- Limits report to devices from a specific site
- Get site IDs from Mist portal or previous reports
- Essential for large organizations with multiple locations
- **IP Impact**: Different sites may have different IP ranges/VLANs

**Base URL (`--base-url URL`)**
- Changes API endpoint for different Mist regions
- US: `https://api.mist.com` (default)
- Europe: `https://api.eu.mist.com`
- APAC: `https://api.ac2.mist.com`
- Use region closest to your Mist org for better performance

## Daily Usage

### Generating Reports

#### Quick Report (Default Settings)
```bash
python3 mist_endpoint_report.py
```

#### Custom Report Options
```bash
# Look back 14 days for better IP coverage
python3 mist_endpoint_report.py --days 14

# Use a different theme
python3 mist_endpoint_report.py --theme sunset

# Generate multiple formats with IP data
python3 mist_endpoint_report.py --format html,csv,json,excel

# Filter by connection type to analyze IP patterns
python3 mist_endpoint_report.py --connection-type wireless

# Filter by specific site for targeted IP analysis
python3 mist_endpoint_report.py --site YOUR_SITE_ID
```

#### Available Themes
- `default` - Clean blue theme with professional IP address formatting
- `sunset` - Orange/red gradient with warm IP styling
- `ocean` - Deep blue theme with network-focused design
- `forest` - Green nature theme with organic IP presentation
- `dark` - Dark mode theme with high-contrast IP display
- `corporate` - Professional blue theme optimized for business reports

### Using Automation Features

#### Single Report with Notifications
```bash
python3 mist_automation.py --run
```

#### Check System Health
```bash
python3 mist_automation.py --health
```

#### Clean Up Old Files
```bash
python3 mist_automation.py --cleanup
```

## Understanding Your Reports

### HTML Report Features

When you open an HTML report, you'll see:

1. **Statistics Dashboard** - Key metrics at the top
   - Total devices
   - Active devices (24h and 7d)
   - Never seen devices
   - **Devices with IP addresses**
   - **IP address coverage percentage**
   - Compliance rate

2. **Interactive Table** - Click column headers to sort
   - Device names and MAC addresses
   - **Last known IP addresses with special formatting**
   - Connection type (wireless/wired)
   - Last seen dates with color coding
   - Authentication information
   - Site assignments

3. **Enhanced Filter Options**
   - 🔍 Real-time search filtering (includes IP addresses)
   - 👻 "Show Never Seen" - devices that never connected
   - **🌐 "Show With IP" - devices with IP address data**
   - 🔄 "Show All" - reset all filters

4. **Activity Indicators**
   - 🟢 Green: Active in last 24 hours
   - 🟡 Yellow: Seen within the lookback period
   - ❌ Red: Never seen
   - **🌐 Blue monospace: IP address available**

5. **Download Options** - Export filtered data as CSV from the web interface

### Understanding the Data

#### Connection Types
- **Wireless**: Devices connected via WiFi (may have dynamic IP assignments)
- **Wired**: Devices connected via Ethernet (typically more stable IP assignments)

#### Authentication Status
- Shows how devices authenticated to your network
- Includes matched policy rules
- Helps identify compliance issues
- **IP Correlation**: Authentication success often correlates with IP assignment

#### Activity Status
- **Recently Active**: Connected in last 24 hours (likely to have current IP)
- **Seen Recently**: Connected within your lookback period (may have older IP)
- **Never Seen**: Registered but never connected (no IP address available)

#### IP Address Information

The reports now include **Last IP Address** data for devices that have connected to your network:

**IP Address Sources**
- **NAC Clients Data**: IP addresses come from devices that have authenticated through your NAC system
- **Last Known IP**: Shows the most recent IP address assigned to each device
- **Coverage Depends On**: 
  - NAC being enabled and configured properly
  - Devices actually connecting (not just being registered in User MACs)
  - Your lookback period (--days parameter)
  - DHCP configuration and network policies

**IP Address Coverage Interpretation**
- **High Coverage (80%+)**: Most registered devices are actively connecting and getting IP assignments
- **Medium Coverage (50-80%)**: Some devices may be registered but not connecting regularly
- **Low Coverage (<50%)**: Many devices are registered but haven't connected recently, or NAC/DHCP issues may exist

**Using IP Address Data**
- **Network Troubleshooting**: Correlate device connectivity issues with IP assignments
- **DHCP Analysis**: Understand IP allocation patterns across your network segments
- **Security Monitoring**: Track device movement across IP ranges/VLANs for policy compliance
- **Network Planning**: Analyze IP usage and subnet utilization for capacity planning
- **Policy Validation**: Verify devices are getting IPs from correct VLANs based on their authentication

**IP Address Display**
- **Valid IPs**: Shown in blue monospace font with 🌐 icon
- **Not Available**: Grayed out italic text for devices without IP data
- **Smart Sorting**: IP addresses sort numerically (192.168.1.1 before 192.168.1.10)
- **Search Integration**: Can search by IP address in the filter box

## Configuration Options Explained

### Mist Configuration Options

The `Resources/mist_config.ini` file controls how the system connects to your Mist organization:

```ini
[mist]
api_token = your_api_token_here
org_id = your_org_id_here  
base_url = https://api.mist.com
theme = default
days = 7
```

#### Option Details:

**`api_token`**
- Your Mist API authentication token
- Required for all API calls including NAC clients data for IP addresses
- Keep this secure - it provides access to your network data
- Create in Mist Portal: Organization → API Tokens

**`org_id`**
- UUID of your Mist organization
- Found in your Mist portal URL after `org_id=`
- Must be exact - system cannot guess or auto-detect
- Example: `12345678-1234-1234-1234-123456789abc`

**`base_url`**
- Mist API endpoint URL
- Default: `https://api.mist.com` (US)
- Europe: `https://api.eu.mist.com`
- APAC: `https://api.ac2.mist.com`
- Use region where your Mist org is hosted for optimal performance

**`theme`**
- Default visual theme for HTML reports including IP address styling
- Options: `default`, `sunset`, `ocean`, `forest`, `dark`, `corporate`
- Can be overridden with `--theme` command line option
- Affects colors, styling, and professional appearance including IP formatting

**`days`**
- Default lookback period for NAC client data and IP address collection
- How many days back to search for device activity and IP assignments
- Can be overridden with `--days` command line option
- Balance between completeness and performance
- **IP Impact**: More days = better IP address coverage for infrequently connecting devices

### Automation Configuration Options

The `Resources/automation_config.ini` file controls automation features:

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
output_formats = html,csv
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

#### Telegram Section:

**`bot_token`**
- Token from @BotFather when you created your bot
- Required for sending any Telegram notifications including IP coverage updates
- Keep secure - allows sending messages as your bot

**`chat_id`**
- Your Telegram user ID or group chat ID
- Where notifications will be sent including IP address statistics
- Get from @userinfobot or by messaging your bot

**`send_success_reports`**
- `true`: Send notification when reports complete successfully with IP coverage data
- `false`: Only send error notifications
- Useful to confirm automated runs are working and track IP coverage trends

**`send_error_alerts`**
- `true`: Send notification when reports fail
- `false`: Fail silently (not recommended)
- Critical for monitoring automated systems

**`send_change_alerts`**
- `true`: Send notification when significant changes detected including IP coverage changes
- `false`: Only basic success/failure notifications
- Helps identify network changes, policy modifications, or IP assignment issues

#### Mist Section:

**`script_path`**
- Path to the main report generation script with IP address support
- Usually `./mist_endpoint_report.py`
- Allows using different script versions or locations

**`config_path`**
- Path to Mist API configuration file
- Usually `Resources/mist_config.ini` or `Resources/mist_config.ini.enc`
- System automatically detects encrypted versions

**`python_executable`**
- Python executable to use for running the report generation script
- Default: Uses system auto-detection (usually `python3`)
- Examples: `python3.13`, `python3.12`, `/usr/local/bin/python3`
- Essential for macOS users who need specific Python versions
- Can be overridden with `--python` command line argument or `MIST_PYTHON_EXECUTABLE` environment variable

**`output_formats`**
- Default output formats for automated runs (all include IP address data)
- Comma-separated: `html,csv,json,excel`
- Balances usefulness with storage space
- Consider including `json` for programmatic access to IP data

**`theme`**
- Default theme for automated reports including IP address presentation
- Can be different from manual report theme
- Consider using `corporate` for automated reports for professional IP data display

#### Reports Section:

**`directory`**
- Where generated reports with IP address data are stored
- Default: `Reports`
- System creates this directory if it doesn't exist

**`keep_days`**
- How long to keep old report files including IP address history
- Default: 30 days
- Automatic cleanup prevents disk space issues
- Adjust based on your storage needs and compliance requirements
- **IP Impact**: Longer retention allows for IP address trend analysis

#### Database Section:

**`path`**
- SQLite database file for historical tracking including IP coverage metrics
- Usually stored in `Resources/` directory
- Tracks report statistics, system health, and IP address coverage over time

**`keep_days`**
- How long to keep historical data in database including IP coverage trends
- Default: 90 days (longer than reports for trend analysis)
- Used for health monitoring, change detection, and IP coverage analysis

#### Scheduling Section:

**`enabled`**
- `true`: Enable scheduling features
- `false`: Disable automatic scheduling
- Currently used for documentation - actual scheduling requires external tools

**`daily_time`**
- Preferred time for daily automated reports with IP tracking
- Format: `HH:MM` (24-hour)
- Used when setting up cron jobs or task scheduler

**`cleanup_time`**
- Preferred time for daily cleanup operations
- Usually during low-usage hours (early morning)
- Separate from report generation to avoid conflicts

#### Configuration Best Practices:

1. **Start with Conservative Settings**
   - `days = 7` for initial testing (good IP coverage for active networks)
   - `keep_days = 30` for reports
   - Enable all Telegram notifications initially to monitor IP coverage

2. **Adjust Based on Usage and IP Coverage**
   - Increase `days` for less active networks or better IP coverage
   - Reduce `keep_days` if storage is limited
   - Monitor IP coverage rates and adjust lookback periods accordingly
   - Disable success notifications if too frequent but keep change alerts for IP coverage changes

3. **Security Considerations**
   - Always encrypt configuration files after setup
   - Use restrictive file permissions
   - Regularly rotate API tokens
   - Monitor IP address data for security insights

4. **Performance Tuning**
   - Lower `days` value = faster reports but potentially less IP coverage
   - Fewer output formats = less storage
   - Regular cleanup prevents performance degradation
   - Use correct Python executable for optimal performance

5. **IP Address Optimization**
   - Monitor IP coverage percentages in reports
   - Adjust `days` parameter if IP coverage is consistently low
   - Ensure NAC is properly configured for IP address tracking
   - Consider network infrastructure health if IP coverage drops suddenly

## Maintenance Tasks

### Weekly Tasks
- Review generated reports for security insights and IP address patterns
- Check system health: `python3 mist_automation.py --health`
- Monitor IP address coverage trends
- Review any devices with missing IP addresses

### Monthly Tasks
- Clean up old files: `python3 mist_automation.py --cleanup`
- Review and update configuration if needed
- Analyze IP address allocation patterns for network planning
- Check for devices that consistently lack IP addresses

### Updating Configuration

If you need to change settings:

```bash
# Decrypt configuration files
python3 mist_automation.py --decrypt-configs

# Edit the files in Resources/ folder
# Make your changes

# Re-encrypt the files
python3 mist_automation.py --encrypt-configs
```

## Troubleshooting

### Common Issues and Solutions

#### "Authentication failed" or "Invalid token"
- Check that your API token is correct
- Ensure the token has the necessary permissions (including NAC clients access)
- Verify your organization ID is correct

#### "No data found" or empty reports
- Check your date range (--days parameter)
- Verify devices are actually connecting to your network
- Ensure NAC (Network Access Control) is enabled in Mist

#### Telegram notifications not working
- Test with: `python3 mist_automation.py --test-telegram`
- Verify bot token and chat ID are correct
- Make sure you've sent `/start` to your bot

#### "Encryption failed" errors
- Ensure you have the cryptography library: `pip3 install cryptography`
- Check that you have the encryption key file
- Verify file permissions (should be readable by you)

#### Reports are empty or missing devices
- Increase the lookback period: `--days 30`
- Check if devices are actually in the User MACs database in Mist
- Verify your organization ID includes all sites

#### Low IP address coverage
- **Check NAC Configuration**: Ensure NAC is enabled and properly configured
- **Increase Lookback Period**: Try `--days 14` or `--days 30` for better IP coverage
- **Verify Device Connectivity**: Devices must actually connect to get IP addresses
- **Check Authentication Flow**: Devices need to authenticate through NAC to get IP data
- **Review Network Policies**: Ensure DHCP is working properly in your environment
- **Consider Network Health**: Sudden drops in IP coverage may indicate infrastructure issues

#### Python version issues
- Configure specific Python version in `automation_config.ini`: `python_executable = python3.13`
- Use command line override: `python3 mist_automation.py --python python3.13 --run`
- Set environment variable: `export MIST_PYTHON_EXECUTABLE=python3.13`
- On macOS, you may need to specify the exact Python version installed

### Getting Help

1. **Check the logs**: Look in `Logs/mist_automation.log` for detailed error messages
2. **Test individual components**: Run each script separately to isolate issues
3. **Verify configuration**: Double-check all your API credentials and settings
4. **Check IP coverage**: Low IP coverage may indicate NAC configuration issues

### Log Files

The system creates detailed logs in the `Logs` folder:
- `mist_automation.log` - Main application log including IP address processing
- Check these for error details and troubleshooting information

## Advanced Features

### Filtering Reports

You can filter reports by various criteria to analyze IP address patterns:

```bash
# Only wireless devices (may show different IP allocation patterns)
python3 mist_endpoint_report.py --connection-type wireless

# Only wired devices (typically more stable IP assignments)
python3 mist_endpoint_report.py --connection-type wired

# Specific site only (useful for analyzing site-specific IP ranges)
python3 mist_endpoint_report.py --site abc123-def456-789ghi

# Combine filters for targeted IP analysis
python3 mist_endpoint_report.py --site abc123 --connection-type wireless --days 30
```

### IP Address Analysis

**Using the HTML Interface:**
- Use the "Show With IP" filter to focus on devices with IP data
- Search by IP address or IP range in the filter box
- Sort by IP address column for network analysis
- Export filtered results for further analysis

**Analyzing IP Patterns:**
- Look for devices on unexpected subnets (potential security issues)
- Identify DHCP exhaustion (many devices without recent IPs)
- Monitor guest vs. corporate VLAN assignments
- Track device mobility across IP ranges

### Scheduling (Advanced Users)

The system includes scheduling capabilities, but setting up automation depends on your operating system:

#### macOS/Linux with cron:
```bash
# Edit your crontab
crontab -e

# Add this line for daily 6 AM reports with IP tracking:
0 6 * * * cd /path/to/mist-automation && python3 mist_automation.py --run

# Or with specific Python version:
0 6 * * * cd /path/to/mist-automation && /usr/local/bin/python3.13 mist_automation.py --run
```

#### Windows with Task Scheduler:
- Open Task Scheduler
- Create a basic task
- Set it to run `python3 mist_automation.py --run` daily

### Multiple Output Formats

Generate reports with comprehensive IP address data in multiple formats simultaneously:

```bash
# Generate all formats with IP address data
python3 mist_endpoint_report.py --format html,csv,json,excel

# Focus on data formats for IP analysis
python3 mist_endpoint_report.py --format csv,json

# For network operations presentations
python3 mist_endpoint_report.py --format html,excel --theme corporate
```

**IP Address Data in Each Format:**
- **HTML**: Interactive IP filtering, coverage statistics, and network troubleshooting tools
- **CSV**: Raw IP data for import into network management tools or spreadsheet analysis
- **JSON**: Structured IP data for integration with monitoring systems and automation
- **Excel**: Multi-sheet analysis including IP coverage metrics and subnet breakdowns

## Security Best Practices

1. **Always encrypt your configuration files** - Contains sensitive API tokens
2. **Use secure file permissions** - The system sets these automatically
3. **Regularly rotate your API tokens** - Update them in Mist every few months
4. **Keep your encryption key secure** - Store it safely, it's needed to decrypt configs
5. **Review reports regularly** - Look for unexpected devices or authentication patterns
6. **Monitor IP address assignments** - Unexpected IP assignments may indicate security issues
7. **Use IP data for security analysis** - Correlate MAC addresses with IP assignments for anomaly detection

## Tips for Better Reports

1. **Choose the right lookback period for IP coverage**
   - 7 days: Good for active networks with frequent connections
   - 14-30 days: Better for networks with less frequent usage or to capture more IP data
   - 90+ days: Comprehensive historical view including seasonal device usage patterns

2. **Optimize IP address coverage**
   - Ensure NAC is properly configured and enabled
   - Verify devices are actually connecting, not just registered
   - Consider increasing lookback period if IP coverage is consistently low
   - Check that authentication is working properly across all sites

3. **Use IP address filtering effectively**
   - Use "Show With IP" to focus on actively connecting devices
   - Filter by IP ranges to analyze specific network segments
   - Combine with connection type filters for targeted infrastructure analysis
   - Search by specific IP addresses for troubleshooting

4. **Leverage multiple output formats for IP analysis**
   - HTML for interactive IP address analysis and filtering
   - CSV for IP address analysis in spreadsheets or network management tools
   - JSON for integration with network monitoring systems and automation
   - Excel for comprehensive IP usage reports with multiple analysis sheets

5. **Monitor trends over time**
   - Use the health command to see historical IP coverage patterns
   - Watch for sudden changes in IP coverage (may indicate network issues)
   - Track compliance rate improvements alongside IP assignment success
   - Identify devices that consistently lack IP addresses for follow-up

## Getting the Most Value

### Regular Review Questions

When reviewing your reports, consider these IP-enhanced questions:

- Are there devices that have never connected? (Security concern - no IP history)
- Are authentication rules working as expected? (Check IP assignment correlation)
- Are there unusual patterns in IP assignments or connection types?
- Is the IP address coverage improving or declining over time?
- Are devices connecting from unexpected IP ranges or subnets?
- Are there devices with MAC addresses but no recent IP assignments? (Connectivity issues)
- Are devices getting IP addresses from unexpected VLANs? (Policy/configuration problems)
- Do guest devices properly receive guest VLAN IP addresses?
- Are there authentication failures for devices that have IP assignments? (Potential security issues)

### Using Reports for Security

#### **IP Address Correlation for Security**

- **Rogue Device Detection**: Look for unknown MAC addresses with unexpected IP assignments
- **Network Segmentation Validation**: Verify devices are getting IPs from correct VLANs/subnets
- **Authentication Bypass Detection**: Find devices with IP addresses but no authentication records
- **IP Address Abuse Monitoring**: Track devices that appear on multiple IP ranges inappropriately
- **Policy Compliance**: Ensure corporate devices get corporate IPs and guests get guest IPs

#### **Enhanced Security Monitoring**

- **Identify rogue devices**: Look for unknown MAC addresses, especially those with IP assignments
- **Monitor compliance**: Track authentication rule matches and correlate with IP assignments
- **Detect anomalies**: Unusual IP assignment patterns or new devices in sensitive ranges
- **Audit access**: Review which devices access which parts of your network based on IP data
- **Track device mobility**: Monitor devices moving between different IP ranges/sites

### Network Troubleshooting Workflows

#### **Device Connectivity Issues**
1. **Check Device Status**: Look for device in report - is it registered?
2. **Verify IP Assignment**: Does the device have a recent IP address?
3. **Check Authentication**: Does authentication status match IP allocation?
4. **Validate Network Policy**: Is the device getting IP from expected VLAN/subnet?
5. **Review Timeline**: When did the device last successfully get an IP?

#### **DHCP and IP Assignment Problems**
1. **Analyze IP Coverage**: What percentage of devices have IP addresses?
2. **Identify Patterns**: Are certain device types or sites having IP issues?
3. **Check Subnet Utilization**: Are devices stuck on wrong subnets?
4. **Monitor Exhaustion**: Compare registered devices vs. those with recent IPs
5. **Validate Policies**: Ensure auth policies correctly assign VLAN/IP ranges

#### **Network Policy Compliance**
1. **Guest Network Validation**: Verify guest devices are on guest VLANs (check IP ranges)
2. **Corporate Segmentation**: Ensure corporate devices have corporate IP assignments
3. **IoT Device Management**: Check that IoT devices are properly segmented via IP assignment
4. **Policy Violations**: Monitor for IP/authentication mismatches that indicate policy bypasses

#### **Performance and Capacity Planning**
1. **IP Utilization Analysis**: Track IP assignment patterns for capacity planning
2. **Site Comparison**: Compare IP coverage across different sites
3. **Connection Type Analysis**: Analyze wired vs. wireless IP assignment success rates
4. **Historical Trends**: Use database to track IP coverage changes over time

#### **When IP Coverage is Low**
1. **Check NAC Configuration**: Ensure NAC is enabled and properly configured
2. **Verify Authentication Flow**: Test that devices can successfully authenticate
3. **Review DHCP Settings**: Ensure DHCP servers are properly configured and reachable
4. **Increase Lookback Period**: Try longer time periods to capture infrequent connections
5. **Check Network Infrastructure**: Verify switches, APs, and authentication servers are healthy

This enhanced user guide now provides comprehensive coverage of the IP address features while maintaining all the existing functionality. The IP address tracking significantly enhances the value of the reports for network troubleshooting, security monitoring, and operational planning.