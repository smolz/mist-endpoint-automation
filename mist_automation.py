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
pip3 install requests pandas python-telegram-bot configparser schedule cryptography

Usage:
python3 mist_automation.py --setup              # Initial configuration
python3 mist_automation.py --run                # Single run with notifications
python3 mist_automation.py --encrypt-configs    # Encrypt configuration files
python3 mist_automation.py --test-telegram      # Test Telegram integration
python3 mist_automation.py --schedule           # Run as daemon with scheduling
"""

import os
import sys
import json
import argparse
import configparser
import sqlite3
import shutil
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import subprocess
import logging
import requests
import pandas as pd
import schedule
import time
import traceback

# Import encryption module
try:
    from config_encryption import ConfigEncryption
    ENCRYPTION_AVAILABLE = True
except ImportError:
    ENCRYPTION_AVAILABLE = False
    logging.warning("Encryption module not available. Install cryptography: pip3 install cryptography")

# Setup logging with organized folder structure
def setup_logging():
    """Setup logging with proper directory structure"""
    logs_dir = Path("Logs")
    logs_dir.mkdir(exist_ok=True)
    
    log_file = logs_dir / 'mist_automation.log'
    
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
            logger.info("✅ Telegram message sent successfully")
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
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            resources_dir = Path("Resources")
            resources_dir.mkdir(exist_ok=True)
            db_path = resources_dir / "mist_history.db"
        
        self.db_path = Path(db_path)
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
    
    def store_report(self, stats: Dict, file_path: str, report_hash: str, success: bool, duration: Optional[float] = None):
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
                str(file_path),
                success
            ))
            
            conn.commit()
            conn.close()
            logger.debug("📝 Report data stored in database")
            
        except Exception as e:
            logger.error(f"❌ Failed to store report data: {e}")
    
    def log_health_event(self, status: str, duration: float, error_msg: Optional[str] = None, details: Optional[str] = None):
        """Log health event to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO health_log (timestamp, status, duration_seconds, error_message, details)
                VALUES (?, ?, ?, ?, ?)
            ''', (datetime.now().isoformat(), status, duration, error_msg, details))
            
            conn.commit()
            conn.close()
            logger.debug(f"📈 Health event logged: {status}")
            
        except Exception as e:
            logger.error(f"❌ Failed to log health event: {e}")
    
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
    
    def __init__(self, config_file: Optional[str] = None, python_executable: Optional[str] = None):
        self.setup_directories()
        
        if config_file is None:
            config_file = Path("Resources") / "automation_config.ini"
        elif not Path(config_file).parent.name:
            config_file = Path("Resources") / config_file
        
        self.config_file = Path(config_file)
        self.config = self.load_config()
        
        # Set up Python executable
        self.python_executable = python_executable or self._get_python_executable()
        
        # Initialize components
        self.telegram = None
        telegram_config = self.config.get('telegram', {})
        if telegram_config.get('bot_token') and telegram_config.get('chat_id'):
            self.telegram = TelegramNotifier(
                telegram_config['bot_token'],
                telegram_config['chat_id']
            )
        
        # Set up database
        db_path = self.config.get('database', {}).get('path')
        if db_path and not Path(db_path).parent.name:
            db_path = Path("Resources") / db_path
        
        self.tracker = HistoricalTracker(db_path)
        
        # Set up paths
        self.mist_script = self.config.get('mist', {}).get('script_path', './mist_endpoint_report.py')
        self.reports_dir = Path(self.config.get('reports', {}).get('directory', 'Reports'))
    
    def setup_directories(self):
        """Create necessary directories if they don't exist"""
        directories = [Path('Resources'), Path('Logs'), Path('Reports')]
        for directory in directories:
            directory.mkdir(exist_ok=True)
    
    def _get_python_executable(self) -> str:
        """Get Python executable with multiple override options"""
        
        # 1. Environment variable (highest priority)
        env_python = os.environ.get('MIST_PYTHON_EXECUTABLE')
        if env_python and shutil.which(env_python):
            logger.info(f"🐍 Using Python from MIST_PYTHON_EXECUTABLE: {env_python}")
            return env_python
        
        # 2. Configuration file
        config_python = self.config.get('mist', {}).get('python_executable')
        if config_python and shutil.which(config_python):
            logger.info(f"🐍 Using Python from config: {config_python}")
            return config_python
        
        # 3. Auto-detection
        detected = self._detect_python_executable()
        logger.info(f"🐍 Auto-detected Python: {detected}")
        return detected
    
    def _detect_python_executable(self) -> str:
        """Auto-detect the best Python executable"""
        
        # Current interpreter is usually the best choice
        current = sys.executable
        if current and shutil.which(current):
            return current
        
        # Platform-specific detection
        if sys.platform == "darwin":  # macOS
            candidates = ['python3.13', 'python3.12', 'python3.11', 'python3']
        elif sys.platform.startswith("win"):  # Windows
            candidates = ['python', 'python3', 'py']
        else:  # Linux/Unix
            candidates = ['python3', 'python']
        
        for candidate in candidates:
            if shutil.which(candidate):
                try:
                    # Quick version check
                    result = subprocess.run([candidate, '--version'], 
                                          capture_output=True, text=True, timeout=3)
                    if result.returncode == 0 and 'Python 3.' in result.stdout:
                        return candidate
                except Exception:
                    continue
        
        # Last resort
        return 'python3'
    
    def load_config(self) -> Dict:
        """Load configuration from file (with encryption support)"""
        if not self.config_file.exists():
            encrypted_file = self.config_file.with_suffix('.ini.enc')
            if encrypted_file.exists():
                return self.load_encrypted_config(encrypted_file)
            else:
                logger.warning(f"⚠️ Config file not found: {self.config_file}")
                return {}
        
        config = configparser.ConfigParser()
        config.read(self.config_file)
        
        result = {}
        for section in config.sections():
            result[section] = dict(config[section])
        
        logger.info(f"📋 Loaded configuration from: {self.config_file}")
        return result
    
    def load_encrypted_config(self, encrypted_file: Path) -> Dict:
        """Load encrypted configuration file"""
        if not ENCRYPTION_AVAILABLE:
            raise ImportError("Encryption not available. Install cryptography: pip3 install cryptography")
        
        try:
            key_file = Path("Resources") / "encryption.key"
            if key_file.exists():
                encryptor = ConfigEncryption(key_file=str(key_file))
            else:
                encryptor = ConfigEncryption()
            
            config = encryptor.load_encrypted_config(str(encrypted_file))
            
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
        resources_dir = Path("Resources")
        resources_dir.mkdir(exist_ok=True)
        
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
            'python_executable': 'python3',
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
        
        config_path = resources_dir / "automation_config.ini"
        with open(config_path, 'w') as f:
            config.write(f)
        
        print(f"\n📧 Configuration file created: {config_path}")
        print("📝 Please edit this file with your actual values:")
        print("   1. Get Telegram bot token from @BotFather")
        print("   2. Get your chat ID from @userinfobot")
        print("   3. Update paths and preferences")
        print("   4. Run: python3 mist_automation.py --test-telegram")
        logger.info(f"Sample configuration created: {config_path}")
    
    def test_telegram(self) -> bool:
        """Test Telegram integration"""
        if not self.telegram:
            print("❌ Telegram not configured")
            logger.warning("Telegram not configured")
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
            logger.info("Telegram test completed successfully")
        else:
            print("❌ Telegram test failed. Check your bot token and chat ID.")
            logger.error("Telegram test failed")
        
        return success
    
    def calculate_report_hash(self, report_file: str) -> str:
        """Calculate hash of report file contents for change detection"""
        try:
            if not os.path.exists(report_file):
                return ""
            
            hasher = hashlib.sha256()
            with open(report_file, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate report hash: {e}")
            return str(time.time())  # Fallback to timestamp
    
    def run_mist_report(self) -> Tuple[bool, Dict, str, float]:
        """Run the Mist endpoint report script"""
        start_time = time.time()
        
        try:
            # Get config path, default to encrypted version if available
            mist_config_path = self.config.get('mist', {}).get('config_path', 'Resources/mist_config.ini')
            
            # Check if encrypted version exists and use it
            if Path(mist_config_path + '.enc').exists():
                mist_config_path = mist_config_path + '.enc'
            elif not Path(mist_config_path).exists():
                # Try default locations
                if Path('Resources/mist_config.ini.enc').exists():
                    mist_config_path = 'Resources/mist_config.ini.enc'
                elif Path('Resources/mist_config.ini').exists():
                    mist_config_path = 'Resources/mist_config.ini'
            
            # Build command with configurable Python
            cmd = [
                self.python_executable,  # Use configurable Python
                self.mist_script,
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
            # First try JSON files
            json_files = list(self.reports_dir.glob("mist_endpoint_report_*.json"))
            if json_files:
                latest_json = max(json_files, key=lambda x: x.stat().st_mtime)
                with open(latest_json, 'r') as f:
                    data = json.load(f)
                    return data.get('statistics', {})
            
            # Fallback to CSV files
            csv_files = list(self.reports_dir.glob("mist_endpoint_report_*.csv"))
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
            
            # Count connection types safely
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
            html_files = list(self.reports_dir.glob("mist_endpoint_report_*.html"))
            
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

📌 <b>Connection Types:</b>
🔹 Wireless: {stats.get('by_connection_type', {}).get('wireless', 0)}
🔹 Wired: {stats.get('by_connection_type', {}).get('wired', 0)}
        """
        
        self.telegram.send_message(message)
    
    def send_error_notification(self, error_msg: str, duration: float):
        """Send error notification via Telegram"""
        if not self.telegram or not self.config.get('telegram', {}).get('send_error_alerts', 'false').lower() == 'true':
            return
        
        message = f"""
❌ <b>Mist Endpoint Report - Failed</b>

⏰ <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
⚡ <b>Duration:</b> {duration:.1f}s

🔥 <b>Error:</b>
<code>{error_msg}</code>

Please check the logs for more details.
        """
        
        self.telegram.send_message(message)
    
    def cleanup_old_files(self) -> Tuple[int, int, int]:
        """Clean up old report files and database entries"""
        # Clean up old report files
        keep_days = int(self.config.get('reports', {}).get('keep_days', 30))
        cleaned_files = 0
        
        if self.reports_dir.exists():
            cutoff_date = datetime.now() - timedelta(days=keep_days)
            
            for file_path in self.reports_dir.glob("mist_endpoint_report_*"):
                if file_path.stat().st_mtime < cutoff_date.timestamp():
                    try:
                        file_path.unlink()
                        cleaned_files += 1
                        logger.info(f"🗑️ Deleted old report: {file_path.name}")
                    except Exception as e:
                        logger.error(f"❌ Failed to delete {file_path.name}: {e}")
        
        # Clean up old database entries
        db_keep_days = int(self.config.get('database', {}).get('keep_days', 90))
        reports_deleted = 0
        health_deleted = 0
        
        try:
            conn = sqlite3.connect(self.tracker.db_path)
            cursor = conn.cursor()
            
            cutoff_date = (datetime.now() - timedelta(days=db_keep_days)).isoformat()
            
            cursor.execute('DELETE FROM reports WHERE timestamp < ?', (cutoff_date,))
            reports_deleted = cursor.rowcount
            
            cursor.execute('DELETE FROM health_log WHERE timestamp < ?', (cutoff_date,))
            health_deleted = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            logger.info(f"🧹 Database cleanup: {reports_deleted} reports, {health_deleted} health logs")
            
        except Exception as e:
            logger.error(f"❌ Database cleanup failed: {e}")
        
        return cleaned_files, reports_deleted, health_deleted
    
    def run_single_report(self):
        """Run a single report with full automation features"""
        start_time = time.time()
        logger.info("🚀 Starting automated Mist report generation...")
        
        try:
            # Get previous report for comparison
            previous_report = self.tracker.get_last_report()
            
            # Run the report
            success, stats, report_file, duration = self.run_mist_report()
            
            # Calculate report hash for change detection
            report_hash = self.calculate_report_hash(report_file)
            
            # Log health event
            self.tracker.log_health_event(
                "success" if success else "failure", 
                duration, 
                None if success else "Report generation failed"
            )
            
            # Store results
            self.tracker.store_report(stats, report_file, report_hash, success, duration)
            
            if success:
                # Send success notification
                self.send_success_notification(stats, report_file, duration)
                logger.info("✅ Automated report generation completed successfully")
                print("✅ Mist report completed successfully!")
            else:
                # Send error notification
                self.send_error_notification("Report generation failed", duration)
                logger.error("❌ Automated report generation failed")
                print("❌ Mist report failed. Check logs for details.")
            
            return success
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)
            
            # Log health event for exception
            self.tracker.log_health_event("failure", duration, error_msg)
            
            # Send error notification
            self.send_error_notification(error_msg, duration)
            
            logger.error(f"❌ Automated report generation failed with exception: {e}")
            print(f"❌ Mist report failed: {e}")
            return False

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
  %(prog)s --cleanup               # Clean up old files
  %(prog)s --health                # Show system health
        """
    )
    
    parser.add_argument('--setup', action='store_true', help='Create sample configuration file')
    parser.add_argument('--test-telegram', action='store_true', help='Test Telegram bot integration')
    parser.add_argument('--run', action='store_true', help='Run single report with automation features')
    parser.add_argument('--schedule', action='store_true', help='Start scheduled automation daemon')
    parser.add_argument('--cleanup', action='store_true', help='Run manual cleanup of old files and database')
    parser.add_argument('--health', action='store_true', help='Show health summary')
    parser.add_argument('--config', help='Configuration file path (default: Resources/automation_config.ini)')
    parser.add_argument('--python', help='Python executable to use for running scripts')
    parser.add_argument('--encrypt-configs', action='store_true', help='Encrypt existing configuration files')
    parser.add_argument('--decrypt-configs', action='store_true', help='Decrypt configuration files for editing')
    parser.add_argument('--create-key', action='store_true', help='Create encryption key file')
    
    return parser.parse_args()

def main():
    """Main function"""
    args = parse_command_line_args()
    
    try:
        if args.setup:
            automation = MistAutomation()
            automation.create_sample_config()
            
        elif args.create_key:
            if not ENCRYPTION_AVAILABLE:
                print("❌ Encryption not available. Install cryptography: pip3 install cryptography")
                logger.error("Encryption not available")
                sys.exit(1)
            
            key_file = Path("Resources") / "encryption.key"
            encryptor = ConfigEncryption()
            encryptor.create_key_file(str(key_file))
            print("✅ Encryption key created successfully!")
            logger.info("Encryption key created successfully")
            
        elif args.encrypt_configs:
            if not ENCRYPTION_AVAILABLE:
                print("❌ Encryption not available. Install cryptography: pip3 install cryptography")
                logger.error("Encryption not available")
                sys.exit(1)
            
            config_files = [
                Path("Resources") / "mist_config.ini",
                Path("Resources") / "automation_config.ini"
            ]
            
            key_file = Path("Resources") / "encryption.key"
            if key_file.exists():
                print("🔑 Using encryption key file")
                encryptor = ConfigEncryption(key_file=str(key_file))
            else:
                print("🔐 Using password-based encryption")
                encryptor = ConfigEncryption()
            
            encrypted_count = 0
            for config_file in config_files:
                if config_file.exists():
                    try:
                        print(f"🔒 Encrypting: {config_file}")
                        encryptor.encrypt_config_file(str(config_file))
                        encrypted_count += 1
                        logger.info(f"Encrypted configuration: {config_file}")
                    except Exception as e:
                        print(f"❌ Failed to encrypt {config_file}: {e}")
                        logger.error(f"Failed to encrypt {config_file}: {e}")
                else:
                    print(f"⚠️ Config file not found: {config_file}")
                    logger.warning(f"Config file not found: {config_file}")
            
            if encrypted_count > 0:
                print(f"✅ Encrypted {encrypted_count} configuration files")
                logger.info(f"Encrypted {encrypted_count} configuration files")
            else:
                print("❌ No configuration files were encrypted")
                logger.warning("No configuration files were encrypted")
            
        elif args.decrypt_configs:
            if not ENCRYPTION_AVAILABLE:
                print("❌ Encryption not available. Install cryptography: pip3 install cryptography")
                logger.error("Encryption not available")
                sys.exit(1)
            
            encrypted_files = [
                Path("Resources") / "mist_config.ini.enc",
                Path("Resources") / "automation_config.ini.enc"
            ]
            
            key_file = Path("Resources") / "encryption.key"
            if key_file.exists():
                print("🔑 Using encryption key file")
                encryptor = ConfigEncryption(key_file=str(key_file))
            else:
                print("🔐 Using password-based encryption")
                encryptor = ConfigEncryption()
            
            decrypted_count = 0
            for encrypted_file in encrypted_files:
                if encrypted_file.exists():
                    try:
                        print(f"🔓 Decrypting: {encrypted_file}")
                        encryptor.decrypt_config_file(str(encrypted_file))
                        decrypted_count += 1
                        logger.info(f"Decrypted configuration: {encrypted_file}")
                    except Exception as e:
                        print(f"❌ Failed to decrypt {encrypted_file}: {e}")
                        logger.error(f"Failed to decrypt {encrypted_file}: {e}")
                else:
                    print(f"⚠️ Encrypted file not found: {encrypted_file}")
                    logger.warning(f"Encrypted file not found: {encrypted_file}")
            
            if decrypted_count > 0:
                print(f"✅ Decrypted {decrypted_count} configuration files")
                print("⚠️ Remember to re-encrypt after editing!")
                logger.info(f"Decrypted {decrypted_count} configuration files")
            else:
                print("❌ No encrypted files were found to decrypt")
                logger.warning("No encrypted files were found to decrypt")
        
        else:
            # Initialize automation for other commands
            automation = MistAutomation(args.config, args.python)
            
            if args.test_telegram:
                success = automation.test_telegram()
                sys.exit(0 if success else 1)
                
            elif args.run:
                success = automation.run_single_report()
                sys.exit(0 if success else 1)
                
            elif args.cleanup:
                logger.info("🧹 Starting manual cleanup...")
                print("🧹 Starting cleanup...")
                
                cleaned_files, reports_deleted, health_deleted = automation.cleanup_old_files()
                
                print(f"✅ Cleaned up {cleaned_files} old report files")
                print(f"✅ Cleaned up {reports_deleted} old report entries and {health_deleted} health log entries")
                print("🎉 Cleanup completed!")
                
                logger.info(f"Cleanup completed: {cleaned_files} files, {reports_deleted} reports, {health_deleted} health logs")
                
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
                        status = "Excellent"
                    elif success_rate > 90:
                        print("🟡 System Status: Good")
                        status = "Good"
                    elif success_rate > 75:
                        print("🟠 System Status: Needs Attention")
                        status = "Needs Attention"
                    else:
                        print("🔴 System Status: Critical")
                        status = "Critical"
                    
                    logger.info(f"Health check completed - Status: {status}, Success rate: {success_rate:.1f}%")
                else:
                    print("No health data available for the last 24 hours")
                    logger.info("No health data available for the last 24 hours")
                
            elif args.schedule:
                print("📅 Scheduling functionality would be implemented here")
                print("💡 For now, use cron (Linux/macOS) or Task Scheduler (Windows)")
                print("   Example cron entry:")
                print(f"   0 6 * * * cd {Path.cwd()} && {automation.python_executable} mist_automation.py --run")
                logger.info("Schedule command called - providing manual setup instructions")
                
            else:
                print("No action specified. Use --help for available options.")
                logger.warning("No action specified in command line arguments")
                
    except KeyboardInterrupt:
        print("\n👋 Operation cancelled")
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Unhandled exception: {e}")
        logger.debug(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()