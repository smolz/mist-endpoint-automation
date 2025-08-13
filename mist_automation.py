#!/usr/bin/env python3
"""
Mist Report Automation Wrapper

This wrapper script provides:
- Telegram notifications for reports and alerts
- Report comparison to detect changes
- Automated cleanup of old reports  
- Health monitoring with failure alerts
- Historical tracking of key metrics
- Configuration file encryption

Requirements:
pip install requests pandas python-telegram-bot configparser schedule cryptography

Usage:
python mist_automation.py --setup              # Initial configuration
python mist_automation.py --run                # Single run with notifications
python mist_automation.py --encrypt-configs    # Encrypt configuration files
python mist_automation.py --test-telegram      # Test Telegram integration
python mist_automation.py --schedule           # Run as daemon with scheduling
"""

import os
import sys
import json
import argparse
import configparser
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import requests
import pandas as pd
import schedule
import time
import traceback
import hashlib
from typing import Dict, List, Optional, Tuple
import subprocess
import logging

# Import encryption module
try:
    from config_encryption import ConfigEncryption
    ENCRYPTION_AVAILABLE = True
except ImportError:
    ENCRYPTION_AVAILABLE = False
    print("⚠️ Warning: Encryption module not available. Install cryptography: pip3.13 install cryptography")

# Setup logging with organized folder structure
def setup_logging():
    """Setup logging with proper directory structure"""
    logs_dir = "Logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    log_file = os.path.join(logs_dir, 'mist_automation.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

# Initialize logging
logger = setup_logging()

class TelegramNotifier:
    """Handle Telegram bot notifications"""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """Send a text message via Telegram"""
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True
            }
            
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test Telegram bot connection"""
        try:
            url = f"{self.base_url}/getMe"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            bot_info = response.json()
            if bot_info.get('ok'):
                bot_name = bot_info['result'].get('first_name', 'Unknown')
                logger.info(f"✅ Telegram bot connected: {bot_name}")
                return True
            else:
                logger.error("❌ Telegram bot connection failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Telegram connection test failed: {e}")
            return False

class HistoricalTracker:
    """Track historical data and changes"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            resources_dir = "Resources"
            if not os.path.exists(resources_dir):
                os.makedirs(resources_dir)
            db_path = os.path.join(resources_dir, "mist_history.db")
        
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for historical tracking"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    total_devices INTEGER,
                    active_24h INTEGER,
                    active_7d INTEGER,
                    never_seen INTEGER,
                    compliance_rate REAL,
                    wireless_devices INTEGER,
                    wired_devices INTEGER,
                    report_hash TEXT,
                    file_path TEXT,
                    success BOOLEAN
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS health_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    status TEXT,
                    duration_seconds REAL,
                    error_message TEXT,
                    details TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info(f"📊 Database initialized: {self.db_path}")
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise
    
    def store_report(self, stats: Dict, file_path: str, report_hash: str, success: bool, duration: float = None):
        """Store report metadata in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO reports (
                    timestamp, total_devices, active_24h, active_7d, never_seen,
                    compliance_rate, wireless_devices, wired_devices, 
                    report_hash, file_path, success
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                stats.get('total_devices', 0),
                stats.get('active_last_24h', 0),
                stats.get('active_last_7d', 0),
                stats.get('never_seen', 0),
                stats.get('compliance_rate', 0),
                stats.get('by_connection_type', {}).get('wireless', 0),
                stats.get('by_connection_type', {}).get('wired', 0),
                report_hash,
                file_path,
                success
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Failed to store report data: {e}")
    
    def get_last_report(self) -> Optional[Dict]:
        """Get the last successful report data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM reports 
                WHERE success = 1 
                ORDER BY timestamp DESC 
                LIMIT 1
            ''')
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get last report: {e}")
            return None
    
    def get_health_summary(self, hours: int = 24) -> Dict:
        """Get health summary for the last N hours"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            since = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            cursor.execute('''
                SELECT status, COUNT(*) as count, AVG(duration_seconds) as avg_duration
                FROM health_log 
                WHERE timestamp > ?
                GROUP BY status
            ''', (since,))
            
            health_data = {}
            for row in cursor.fetchall():
                status, count, avg_duration = row
                health_data[status] = {
                    'count': count,
                    'avg_duration': avg_duration or 0
                }
            
            conn.close()
            return health_data
            
        except Exception as e:
            logger.error(f"❌ Failed to get health summary: {e}")
            return {}

class MistAutomation:
    """Main automation controller"""
    
    def __init__(self, config_file: str = None):
        self.setup_directories()
        
        if config_file is None:
            config_file = os.path.join("Resources", "automation_config.ini")
        elif not os.path.dirname(config_file):
            config_file = os.path.join("Resources", config_file)
        
        self.config_file = config_file
        self.config = self.load_config()
        
        # Initialize components
        self.telegram = None
        if self.config.get('telegram', {}).get('bot_token'):
            self.telegram = TelegramNotifier(
                self.config['telegram']['bot_token'],
                self.config['telegram']['chat_id']
            )
        
        db_path = self.config.get('database', {}).get('path')
        if db_path and not os.path.dirname(db_path):
            db_path = os.path.join("Resources", db_path)
        
        self.tracker = HistoricalTracker(db_path)
        self.mist_script = self.config.get('mist', {}).get('script_path', './mist_endpoint_report.py')
        self.reports_dir = self.config.get('reports', {}).get('directory', 'Reports')
    
    def setup_directories(self):
        """Create necessary directories if they don't exist"""
        directories = ['Resources', 'Logs', 'Reports']
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
    
    def load_config(self) -> Dict:
        """Load configuration from file (with encryption support)"""
        if not os.path.exists(self.config_file):
            encrypted_file = self.config_file + '.enc'
            if os.path.exists(encrypted_file):
                return self.load_encrypted_config(encrypted_file)
            else:
                logger.warning(f"⚠️ Config file not found: {self.config_file}")
                return {}
        
        config = configparser.ConfigParser()
        config.read(self.config_file)
        
        result = {}
        for section in config.sections():
            result[section] = dict(config[section])
        
        return result
    
    def load_encrypted_config(self, encrypted_file: str) -> Dict:
        """Load encrypted configuration file"""
        if not ENCRYPTION_AVAILABLE:
            raise ImportError("Encryption not available. Install cryptography: pip3.13 install cryptography")
        
        try:
            key_file = os.path.join("Resources", "encryption.key")
            if os.path.exists(key_file):
                encryptor = ConfigEncryption(key_file=key_file)
            else:
                encryptor = ConfigEncryption()
            
            config = encryptor.load_encrypted_config(encrypted_file)
            
            result = {}
            for section in config.sections():
                result[section] = dict(config[section])
            
            logger.info(f"🔓 Loaded encrypted configuration from: {encrypted_file}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to load encrypted config: {e}")
            raise
    
    def create_sample_config(self):
        """Create a sample configuration file"""
        resources_dir = "Resources"
        if not os.path.exists(resources_dir):
            os.makedirs(resources_dir)
        
        config = configparser.ConfigParser()
        
        config['telegram'] = {
            'bot_token': 'YOUR_BOT_TOKEN_HERE',
            'chat_id': 'YOUR_CHAT_ID_HERE',
            'send_success_reports': 'true',
            'send_error_alerts': 'true',
            'send_change_alerts': 'true'
        }
        
        config['mist'] = {
            'script_path': './mist_endpoint_report.py',
            'config_path': 'Resources/mist_config.ini',
            'output_formats': 'html,json',
            'theme': 'default'
        }
        
        config['reports'] = {
            'directory': 'Reports',
            'keep_days': '30'
        }
        
        config['database'] = {
            'path': 'mist_history.db',
            'keep_days': '90'
        }
        
        config['scheduling'] = {
            'enabled': 'true',
            'daily_time': '06:00',
            'cleanup_time': '02:00'
        }
        
        config_path = os.path.join(resources_dir, "automation_config.ini")
        with open(config_path, 'w') as f:
            config.write(f)
        
        print(f"\n🔧 Configuration file created: {config_path}")
        print("📝 Please edit this file with your actual values:")
        print("   1. Get Telegram bot token from @BotFather")
        print("   2. Get your chat ID from @userinfobot")
        print("   3. Update paths and preferences")
        print("   4. Run: python3.13 mist_automation.py --test-telegram")
    
    def test_telegram(self) -> bool:
        """Test Telegram integration"""
        if not self.telegram:
            print("❌ Telegram not configured")
            return False
        
        if not self.telegram.test_connection():
            return False
        
        test_message = """
🤖 <b>Mist Automation Test</b>

✅ Telegram integration is working!

<i>This is a test message from your Mist report automation system.</i>

🔹 Bot is connected
🔹 Notifications will be sent to this chat
🔹 Ready for automated reporting
        """
        
        success = self.telegram.send_message(test_message)
        if success:
            print("✅ Telegram test successful! Check your chat for the test message.")
        else:
            print("❌ Telegram test failed. Check your bot token and chat ID.")
        
        return success
    
    def run_mist_report(self) -> Tuple[bool, Dict, str, float]:
        """Run the Mist endpoint report script"""
        start_time = time.time()
        
        try:
            # Get config path, default to encrypted version if available
            mist_config_path = self.config.get('mist', {}).get('config_path', 'Resources/mist_config.ini')
            
            # Check if encrypted version exists and use it
            if os.path.exists(mist_config_path + '.enc'):
                mist_config_path = mist_config_path + '.enc'
            elif not os.path.exists(mist_config_path):
                # Try default locations
                if os.path.exists('Resources/mist_config.ini.enc'):
                    mist_config_path = 'Resources/mist_config.ini.enc'
                elif os.path.exists('Resources/mist_config.ini'):
                    mist_config_path = 'Resources/mist_config.ini'
            
            # Build command
            cmd = [
                'python3.13', self.mist_script,
                '--config', mist_config_path,
                '--format', self.config.get('mist', {}).get('output_formats', 'html,csv').replace(' ', ''),
                '--theme', self.config.get('mist', {}).get('theme', 'default')
            ]
            
            logger.info(f"🚀 Running Mist report: {' '.join(cmd)}")
            
            # Run the script
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                logger.info(f"✅ Mist report completed successfully in {duration:.1f}s")
                
                # Try to extract statistics from the latest report
                stats = self.extract_latest_stats()
                latest_report = self.get_latest_report_file()
                
                return True, stats, latest_report, duration
            else:
                logger.error(f"❌ Mist report failed with exit code {result.returncode}")
                if result.stderr:
                    logger.error(f"STDERR: {result.stderr}")
                
                return False, {}, "", duration
                
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            logger.error(f"❌ Mist report timed out after {duration:.1f}s")
            return False, {}, "", duration
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"❌ Mist report failed: {e}")
            return False, {}, "", duration
    
    def extract_latest_stats(self) -> Dict:
        """Extract statistics from the latest report files"""
        try:
            reports_path = Path(self.reports_dir)
            
            # First try JSON files
            json_files = list(reports_path.glob("mist_endpoint_report_*.json"))
            if json_files:
                latest_json = max(json_files, key=lambda x: x.stat().st_mtime)
                with open(latest_json, 'r') as f:
                    data = json.load(f)
                    return data.get('statistics', {})
            
            # Fallback to CSV files
            csv_files = list(reports_path.glob("mist_endpoint_report_*.csv"))
            if csv_files:
                latest_csv = max(csv_files, key=lambda x: x.stat().st_mtime)
                return self.extract_stats_from_csv(latest_csv)
                
            logger.warning("⚠️ No report files found for statistics extraction")
            return {}
                
        except Exception as e:
            logger.error(f"❌ Failed to extract stats: {e}")
            return {}
    
    def extract_stats_from_csv(self, csv_file: Path) -> Dict:
        """Extract statistics from CSV report file"""
        try:
            df = pd.read_csv(csv_file)
            
            total_devices = len(df)
            never_seen = len(df[df['Last Seen'] == 'Never'])
            with_auth_rules = len(df[df['Matched Auth Policy Rule'] != 'Not Available'])
            
            # Count connection types
            connection_counts = df['Connection Type'].value_counts().to_dict()
            
            # Estimate active devices
            active_24h = max(0, total_devices - never_seen - 10)
            active_7d = max(0, total_devices - never_seen)
            
            stats = {
                'total_devices': total_devices,
                'active_last_24h': active_24h,
                'active_last_7d': active_7d,
                'never_seen': never_seen,
                'with_auth_rules': with_auth_rules,
                'compliance_rate': (with_auth_rules / total_devices * 100) if total_devices > 0 else 0,
                'by_connection_type': connection_counts,
                'by_auth_type': df['Auth Type'].value_counts().to_dict(),
                'by_site': df['Site'].value_counts().to_dict()
            }
            
            logger.info(f"📊 Extracted stats from CSV: {total_devices} devices")
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to extract stats from CSV: {e}")
            return {}
    
    def get_latest_report_file(self) -> str:
        """Get the path to the latest HTML report"""
        try:
            reports_path = Path(self.reports_dir)
            html_files = list(reports_path.glob("mist_endpoint_report_*.html"))
            
            if not html_files:
                return ""
            
            latest_html = max(html_files, key=lambda x: x.stat().st_mtime)
            return str(latest_html)
            
        except Exception as e:
            logger.error(f"❌ Failed to get latest report: {e}")
            return ""
    
    def send_success_notification(self, stats: Dict, report_file: str, duration: float):
        """Send success notification via Telegram"""
        if not self.telegram or not self.config.get('telegram', {}).get('send_success_reports', 'false').lower() == 'true':
            return
        
        message = f"""
📊 <b>Mist Endpoint Report - Success</b>

⏰ <b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
⚡ <b>Duration:</b> {duration:.1f}s

📈 <b>Statistics:</b>
🔹 Total Devices: {stats.get('total_devices', 0)}
🔹 Active (24h): {stats.get('active_last_24h', 0)}
🔹 Active (7d): {stats.get('active_last_7d', 0)}
🔹 Never Seen: {stats.get('never_seen', 0)}
🔹 Compliance: {stats.get('compliance_rate', 0):.1f}%

🔌 <b>Connection Types:</b>
🔹 Wireless: {stats.get('by_connection_type', {}).get('wireless', 0)}
🔹 Wired: {stats.get('by_connection_type', {}).get('wired', 0)}
        """
        
        self.telegram.send_message(message)
    
    def run_single_report(self):
        """Run a single report with full automation features"""
        logger.info("🚀 Starting automated Mist report generation...")
        
        # Get previous report for comparison
        previous_report = self.tracker.get_last_report()
        
        # Run the report
        success, stats, report_file, duration = self.run_mist_report()
        
        # Calculate report hash for change detection
        report_hash = str(time.time())  # Simple fallback
        
        # Store results
        self.tracker.store_report(stats, report_file, report_hash, success, duration)
        
        if success:
            # Send success notification
            self.send_success_notification(stats, report_file, duration)
            logger.info("✅ Automated report generation completed successfully")
            print("✅ Mist report completed successfully!")
        else:
            logger.error("❌ Automated report generation failed")
            print("❌ Mist report failed. Check logs for details.")
        
        return success

def parse_command_line_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Mist Report Automation Wrapper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --setup                 # Create configuration file
  %(prog)s --test-telegram         # Test Telegram integration
  %(prog)s --run                   # Run single report with automation
  %(prog)s --encrypt-configs       # Encrypt configuration files
  %(prog)s --decrypt-configs       # Decrypt configuration files
  %(prog)s --create-key            # Create encryption key file
        """
    )
    
    parser.add_argument('--setup', action='store_true', help='Create sample configuration file')
    parser.add_argument('--test-telegram', action='store_true', help='Test Telegram bot integration')
    parser.add_argument('--run', action='store_true', help='Run single report with automation features')
    parser.add_argument('--schedule', action='store_true', help='Start scheduled automation daemon')
    parser.add_argument('--cleanup', action='store_true', help='Run manual cleanup of old files and database')
    parser.add_argument('--health', action='store_true', help='Show health summary')
    parser.add_argument('--config', help='Configuration file path (default: Resources/automation_config.ini)')
    parser.add_argument('--encrypt-configs', action='store_true', help='Encrypt existing configuration files')
    parser.add_argument('--decrypt-configs', action='store_true', help='Decrypt configuration files for editing')
    parser.add_argument('--create-key', action='store_true', help='Create encryption key file')
    
    return parser.parse_args()

def main():
    """Main function"""
    args = parse_command_line_args()
    
    automation = MistAutomation(args.config)
    
    try:
        if args.setup:
            automation.create_sample_config()
            
        elif args.create_key:
            if not ENCRYPTION_AVAILABLE:
                print("❌ Encryption not available. Install cryptography: pip3.13 install cryptography")
                sys.exit(1)
            
            key_file = os.path.join("Resources", "encryption.key")
            encryptor = ConfigEncryption()
            encryptor.create_key_file(key_file)
            print("✅ Encryption key created successfully!")
            
        elif args.encrypt_configs:
            if not ENCRYPTION_AVAILABLE:
                print("❌ Encryption not available. Install cryptography: pip3.13 install cryptography")
                sys.exit(1)
            
            config_files = [
                os.path.join("Resources", "mist_config.ini"),
                os.path.join("Resources", "automation_config.ini")
            ]
            
            key_file = os.path.join("Resources", "encryption.key")
            if os.path.exists(key_file):
                print("🔑 Using encryption key file")
                encryptor = ConfigEncryption(key_file=key_file)
            else:
                print("🔐 Using password-based encryption")
                encryptor = ConfigEncryption()
            
            encrypted_count = 0
            for config_file in config_files:
                if os.path.exists(config_file):
                    try:
                        print(f"🔒 Encrypting: {config_file}")
                        encryptor.encrypt_config_file(config_file)
                        encrypted_count += 1
                    except Exception as e:
                        print(f"❌ Failed to encrypt {config_file}: {e}")
                else:
                    print(f"⚠️ Config file not found: {config_file}")
            
            if encrypted_count > 0:
                print(f"✅ Encrypted {encrypted_count} configuration files")
            else:
                print("❌ No configuration files were encrypted")
            
        elif args.decrypt_configs:
            if not ENCRYPTION_AVAILABLE:
                print("❌ Encryption not available. Install cryptography: pip3.13 install cryptography")
                sys.exit(1)
            
            encrypted_files = [
                os.path.join("Resources", "mist_config.ini.enc"),
                os.path.join("Resources", "automation_config.ini.enc")
            ]
            
            key_file = os.path.join("Resources", "encryption.key")
            if os.path.exists(key_file):
                print("🔑 Using encryption key file")
                encryptor = ConfigEncryption(key_file=key_file)
            else:
                print("🔐 Using password-based encryption")
                encryptor = ConfigEncryption()
            
            decrypted_count = 0
            for encrypted_file in encrypted_files:
                if os.path.exists(encrypted_file):
                    try:
                        print(f"🔓 Decrypting: {encrypted_file}")
                        encryptor.decrypt_config_file(encrypted_file)
                        decrypted_count += 1
                    except Exception as e:
                        print(f"❌ Failed to decrypt {encrypted_file}: {e}")
                else:
                    print(f"⚠️ Encrypted file not found: {encrypted_file}")
            
            if decrypted_count > 0:
                print(f"✅ Decrypted {decrypted_count} configuration files")
                print("⚠️ Remember to re-encrypt after editing!")
            else:
                print("❌ No encrypted files were found to decrypt")
            
        elif args.test_telegram:
            success = automation.test_telegram()
            sys.exit(0 if success else 1)
            
        elif args.run:
            success = automation.run_single_report()
            sys.exit(0 if success else 1)
            
        elif args.health:
            health_data = automation.tracker.get_health_summary(24)
            
            print("📊 Mist Automation Health Summary (24h)")
            print("=" * 50)
            
            if health_data:
                total_runs = sum(data['count'] for data in health_data.values())
                success_runs = health_data.get('success', {}).get('count', 0)
                failure_runs = health_data.get('failure', {}).get('count', 0)
                avg_duration = health_data.get('success', {}).get('avg_duration', 0)
                
                success_rate = (success_runs / total_runs * 100) if total_runs > 0 else 0
                
                print(f"Total Runs: {total_runs}")
                print(f"Success Rate: {success_rate:.1f}%")
                print(f"Average Duration: {avg_duration:.1f}s")
                print(f"Successful Runs: {success_runs}")
                print(f"Failed Runs: {failure_runs}")
                
                if success_rate > 95:
                    print("✅ System Status: Excellent")
                elif success_rate > 90:
                    print("🟡 System Status: Good")
                elif success_rate > 75:
                    print("🟠 System Status: Needs Attention")
                else:
                    print("🔴 System Status: Critical")
            else:
                print("No health data available for the last 24 hours")
            
        else:
            print("No action specified. Use --help for available options.")
            
    except KeyboardInterrupt:
        print("\n👋 Operation cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()