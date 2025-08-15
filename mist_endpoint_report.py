#!/usr/bin/env python3
"""
Enhanced Mist Endpoint Report Generator

This script:
1. Pulls all User MACs from the Mist API
2. Pulls NAC Clients data for the last N days (configurable)
3. Combines the data to create a comprehensive endpoint report
4. Outputs the results to HTML, CSV, JSON, and Excel formats
5. Supports configuration files and enhanced filtering
6. Supports encrypted configuration files
7. Enhanced HTML reports with filtering, search, and statistics

Requirements:
pip3 install requests pandas openpyxl configparser cryptography

Usage:
python3 mist_endpoint_report.py
python3 mist_endpoint_report.py --token YOUR_TOKEN --org-id YOUR_ORG_ID
python3 mist_endpoint_report.py --days 14 --theme sunset --format html,csv
python3 mist_endpoint_report.py --config Resources/mist_config.ini
python3 mist_endpoint_report.py --encrypt-config
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import json
import sys
import argparse
import os
import configparser
from typing import List, Dict, Optional
from functools import wraps
from pathlib import Path

# Import encryption module
try:
    from config_encryption import ConfigEncryption
    ENCRYPTION_AVAILABLE = True
except ImportError:
    ENCRYPTION_AVAILABLE = False

def timer(func):
    """Decorator to time function execution"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"⏱️ {func.__name__} completed in {elapsed:.2f} seconds")
        return result
    return wrapper

def normalize_mac_address(mac: str) -> str:
    """Normalize MAC address to a consistent format (uppercase, no separators)"""
    if not mac:
        return ""
    
    # Remove common separators and convert to uppercase
    normalized = mac.replace(":", "").replace("-", "").replace(".", "").upper().strip()
    
    # Validate MAC address length (should be 12 hex characters)
    if len(normalized) == 12 and all(c in '0123456789ABCDEF' for c in normalized):
        return normalized
    
    return ""  # Return empty string for invalid MACs

def format_timestamp(timestamp: Optional[float]) -> str:
    """Convert Unix timestamp to readable format"""
    if not timestamp:
        return "Never"
    
    try:
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%b %d, %Y %I:%M:%S %p")
    except (ValueError, TypeError):
        return "Invalid Date"

def load_config(config_file: str = None) -> Dict:
    """Load configuration from file (with encryption support)"""
    # Default to Resources directory if no path specified
    if config_file is None:
        config_file = Path("Resources") / "mist_config.ini"
    elif not Path(config_file).parent.name:  # If no directory specified
        config_file = Path("Resources") / config_file
    
    # Check if this is an encrypted file
    if str(config_file).endswith('.enc'):
        return load_encrypted_config(config_file)
    
    # Try encrypted version first if regular file requested
    encrypted_file = Path(str(config_file) + '.enc')
    if encrypted_file.exists():
        return load_encrypted_config(encrypted_file)
    
    # Try regular config files
    config_files = [config_file]
    if config_file != Path("Resources") / "mist_config.ini":
        config_files.append(Path("Resources") / "mist_config.ini")
    config_files.extend([Path('mist_config.ini'), Path('config.ini')])  # Legacy fallbacks
    
    config = configparser.ConfigParser()
    config_data = {}
    
    for conf_file in config_files:
        if conf_file.exists():
            print(f"📋 Loading configuration from: {conf_file}")
            config.read(conf_file)
            if 'mist' in config:
                config_data = {
                    'api_token': config.get('mist', 'api_token', fallback=None),
                    'org_id': config.get('mist', 'org_id', fallback=None),
                    'base_url': config.get('mist', 'base_url', fallback='https://api.mist.com'),
                    'theme': config.get('mist', 'theme', fallback='default'),
                    'days': config.getint('mist', 'days', fallback=7)
                }
                break
    
    return config_data

def load_encrypted_config(encrypted_file: Path) -> Dict:
    """Load encrypted configuration file"""
    if not ENCRYPTION_AVAILABLE:
        raise ImportError("Encryption not available. Install cryptography: pip3 install cryptography")
    
    try:
        # Check for key file
        key_file = Path("Resources") / "encryption.key"
        if key_file.exists():
            print("🔑 Using encryption key file")
            encryptor = ConfigEncryption(key_file=str(key_file))
        else:
            print("🔐 Using password-based encryption")
            encryptor = ConfigEncryption()
        
        config = encryptor.load_encrypted_config(str(encrypted_file))
        
        print(f"🔓 Loaded encrypted configuration from: {encrypted_file}")
        
        if 'mist' in config:
            return {
                'api_token': config.get('mist', 'api_token', fallback=None),
                'org_id': config.get('mist', 'org_id', fallback=None),
                'base_url': config.get('mist', 'base_url', fallback='https://api.mist.com'),
                'theme': config.get('mist', 'theme', fallback='default'),
                'days': config.getint('mist', 'days', fallback=7)
            }
        else:
            return {}
            
    except Exception as e:
        print(f"❌ Failed to load encrypted config: {e}")
        raise

def create_sample_config():
    """Create a sample configuration file"""
    # Ensure Resources directory exists
    resources_dir = Path("Resources")
    resources_dir.mkdir(exist_ok=True)
    print(f"📁 Created directory: {resources_dir}")
    
    config = configparser.ConfigParser()
    config['mist'] = {
        'api_token': 'your_api_token_here',
        'org_id': 'your_org_id_here',
        'base_url': 'https://api.mist.com',
        'theme': 'default',
        'days': '7'
    }
    
    config_path = resources_dir / 'mist_config.ini'
    with open(config_path, 'w') as f:
        config.write(f)
    
    print(f"📁 Created sample configuration file: {config_path}")
    print("   Edit this file with your credentials, then optionally encrypt it:")
    print(f"   python3 config_encryption.py --encrypt {config_path}")

def parse_command_line_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Generate Enhanced Mist Endpoint Report',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s
  %(prog)s --token YOUR_TOKEN --org-id YOUR_ORG_ID
  %(prog)s --days 14 --theme sunset --format html,csv
  %(prog)s --config Resources/mist_config.ini
  %(prog)s --encrypt-config
        """
    )
    
    parser.add_argument('-t', '--token', help='Mist API token')
    parser.add_argument('-o', '--org-id', help='Organization ID (UUID format)')
    parser.add_argument('-b', '--base-url', default='https://api.mist.com', help='API base URL (default: https://api.mist.com)')
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--days', type=int, default=7, help='Number of days to look back for NAC clients (default: 7)')
    parser.add_argument('--theme', choices=['default', 'sunset', 'ocean', 'forest', 'dark', 'corporate'], default='default', help='Report theme (default: default)')
    parser.add_argument('--site', help='Filter by specific site ID')
    parser.add_argument('--connection-type', choices=['wired', 'wireless'], help='Filter by connection type')
    parser.add_argument('--format', default='html', help='Output formats (comma-separated): html,csv,json,excel (default: html)')
    parser.add_argument('--create-config', action='store_true', help='Create a sample configuration file and exit')
    parser.add_argument('--encrypt-config', action='store_true', help='Encrypt existing configuration file')
    parser.add_argument('--decrypt-config', action='store_true', help='Decrypt configuration file for editing')
    
    return parser.parse_args()

def get_user_input():
    """Get API token and organization ID from user input"""
    import getpass
    
    print("📧 Mist API Configuration")
    print("=" * 50)
    print()
    
    # Get API Token
    print("📋 Please provide your Mist API token:")
    print("   (You can create one at: https://manage.mist.com → Organization → API Tokens)")
    api_token = getpass.getpass("🔑 API Token (input will be hidden): ").strip()
    
    if not api_token:
        print("❌ Error: API token is required")
        sys.exit(1)
    
    print()
    
    # Get Organization ID
    print("🏢 Please provide your organization ID:")
    print("   (Found in your Mist portal URL after 'org_id=')")
    print("   Example: If URL is https://manage.mist.com/admin/?org_id=12345678-1234-1234-1234-123456789abc")
    print("   Then org_id is: 12345678-1234-1234-1234-123456789abc")
    org_id = input("🆔 Organization ID: ").strip()
    
    if not org_id:
        print("❌ Error: Organization ID is required")
        sys.exit(1)
    
    # Validate org_id format (basic UUID check)
    if len(org_id) != 36 or org_id.count('-') != 4:
        print("⚠️ Warning: Organization ID doesn't look like a valid UUID format")
        confirm = input("Continue anyway? (y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            sys.exit(1)
    
    print()
    
    # Get API Base URL (optional)
    print("🌐 API Base URL (optional):")
    print("   Default: https://api.mist.com")
    print("   For other regions, use: https://api.eu.mist.com, https://api.ac2.mist.com, etc.")
    base_url = input("🔗 Base URL (press Enter for default): ").strip()
    
    if not base_url:
        base_url = "https://api.mist.com"
    
    # Remove trailing slash if present
    base_url = base_url.rstrip('/')
    
    print()
    print("✅ Configuration complete!")
    print(f"   Organization ID: {org_id}")
    print(f"   API Endpoint: {base_url}")
    print()
    
    return api_token, org_id, base_url

class MistAPIClient:
    def __init__(self, api_token: str, org_id: str, base_url: str = "https://api.mist.com"):
        """
        Initialize Mist API client
        
        Args:
            api_token: Your Mist API token
            org_id: Your organization ID
            base_url: Mist API base URL (adjust for your region)
        """
        self.api_token = api_token
        self.org_id = org_id
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Token {api_token}',
            'Content-Type': 'application/json'
        })
    
    def _make_request(self, endpoint: str, params: Dict = None) -> List[Dict]:
        """Make paginated API request and return all results"""
        url = f"{self.base_url}/api/v1/orgs/{self.org_id}/{endpoint}"
        all_results = []
        page = 1
        seen_records = set()
        
        while True:
            current_params = params.copy() if params else {}
            current_params.update({'page': page, 'limit': 1000})
            
            print(f"Fetching {endpoint} - page {page} (total so far: {len(all_results)})...")
            
            try:
                response = self.session.get(url, params=current_params)
                response.raise_for_status()
                
                data = response.json()
                
                # Handle different response formats
                if isinstance(data, list):
                    results = data
                    total_count = None
                elif isinstance(data, dict):
                    if 'results' in data:
                        results = data['results']
                        total_count = data.get('total', data.get('count'))
                    elif 'data' in data:
                        results = data['data']
                        total_count = data.get('total', data.get('count'))
                    else:
                        results = [data]
                        total_count = 1
                else:
                    results = []
                    total_count = 0
                
                if not results:
                    print("No more results found")
                    break
                
                # Filter out duplicates
                new_results = []
                for result in results:
                    if 'id' in result:
                        unique_id = result['id']
                    elif 'wcid' in result:
                        unique_id = result['wcid']
                    else:
                        mac = result.get('mac', result.get('device_mac', ''))
                        timestamp = result.get('timestamp', '')
                        unique_id = f"{mac}-{timestamp}"
                    
                    if unique_id not in seen_records:
                        seen_records.add(unique_id)
                        new_results.append(result)
                
                all_results.extend(new_results)
                
                print(f"Retrieved {len(results)} records from page {page} ({len(new_results)} new)")
                
                # Stop conditions
                if len(new_results) == 0:
                    break
                
                if len(results) < current_params['limit']:
                    break
                
                if total_count and len(all_results) >= total_count:
                    break
                
                if page > 50:  # Safety check
                    print(f"⚠️ Safety stop: Reached page {page}")
                    break
                    
                page += 1
                time.sleep(0.2)  # Rate limiting
                
            except requests.exceptions.RequestException as e:
                print(f"Error fetching {endpoint}: {e}")
                break
        
        print(f"✅ Retrieved {len(all_results)} unique records from {endpoint}")
        return all_results

    @timer
    def get_sites(self) -> Dict[str, str]:
        """Get all sites and return a lookup dictionary of site_id -> site_name"""
        sites_data = self._make_request('sites')
        
        site_lookup = {}
        for site in sites_data:
            site_id = site.get('id', '')
            site_name = site.get('name', f'Unknown Site ({site_id[:8]})')
            if site_id:
                site_lookup[site_id] = site_name
        
        print(f"🏢 Retrieved {len(site_lookup)} sites for lookup")
        return site_lookup

    @timer
    def get_user_macs(self) -> List[Dict]:
        """Get all user MACs from the organization"""
        return self._make_request('usermacs/search')
    
    @timer
    def get_nac_clients_last_n_days(self, days: int = 7, site_id: str = None, connection_type: str = None) -> List[Dict]:
        """Get NAC clients from the last N days with optional filtering"""
        end_time = int(time.time())
        start_time = end_time - (days * 24 * 60 * 60)
        
        start_date = datetime.fromtimestamp(start_time).strftime("%Y-%m-%d %H:%M:%S")
        end_date = datetime.fromtimestamp(end_time).strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"📅 Querying NAC clients from {start_date} to {end_date} ({days} days)")
        
        params = {
            'start': start_time,
            'end': end_time
        }
        
        if site_id:
            params['site_id'] = site_id
            print(f"🏢 Filtering by site: {site_id}")
        
        if connection_type:
            params['type'] = connection_type
            print(f"📌 Filtering by connection type: {connection_type}")
        
        return self._make_request('nac_clients/search', params)

def generate_statistics(df: pd.DataFrame) -> Dict:
    """Generate comprehensive statistics from the endpoint data"""
    now = datetime.now()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    
    # Convert Last Seen to datetime for analysis
    def parse_last_seen(date_str):
        if date_str == "Never" or pd.isna(date_str) or date_str == "":
            return None
        try:
            return datetime.strptime(date_str, "%b %d, %Y %I:%M:%S %p")
        except (ValueError, TypeError):
            return None
    
    df_copy = df.copy()
    df_copy['last_seen_dt'] = df_copy['Last Seen'].apply(parse_last_seen)
    
    # Calculate active devices (handle NaT values properly)
    active_24h = 0
    active_7d = 0
    
    for dt in df_copy['last_seen_dt']:
        if dt is not None and not pd.isna(dt):
            if dt >= last_24h:
                active_24h += 1
            if dt >= last_7d:
                active_7d += 1
    
    # Count values safely
    total_devices = len(df)
    never_seen = len(df[df['Last Seen'] == 'Never'])
    with_auth_rules = len(df[df['Matched Auth Policy Rule'] != 'Not Available'])
    
    # Safe value counting for categorical data
    def safe_value_counts(series):
        return series.fillna('Unknown').value_counts().to_dict()
    
    stats = {
        'total_devices': total_devices,
        'active_last_24h': active_24h,
        'active_last_7d': active_7d,
        'never_seen': never_seen,
        'by_auth_type': safe_value_counts(df['Auth Type']),
        'by_site': safe_value_counts(df['Site']),
        'by_connection_type': safe_value_counts(df['Connection Type']),
        'with_auth_rules': with_auth_rules,
        'compliance_rate': (with_auth_rules / total_devices * 100) if total_devices > 0 else 0
    }
    
    return stats

@timer
def create_endpoint_report(user_macs: List[Dict], nac_clients: List[Dict], site_lookup: Dict[str, str]) -> pd.DataFrame:
    """Create the endpoint report by combining user MACs and NAC clients data"""
    
    print(f"📁 Processing {len(user_macs)} user MACs and {len(nac_clients)} NAC client records...")
    
    # Create initial endpoint report from user MACs
    endpoint_data = []
    
    for user_mac in user_macs:
        mac_address = normalize_mac_address(user_mac.get('mac', ''))
        name = user_mac.get('name', '')
        labels = user_mac.get('labels', [])
        description = user_mac.get('notes', '')
        
        if not mac_address:
            continue
        
        endpoint_data.append({
            'Name': name,
            'MAC Address': mac_address,
            'Labels': ', '.join(labels) if labels else '',
            'Description': description,
            'Last Seen': 'Never',
            'Site': 'Unknown',
            'Connection Type': 'Unknown',
            'SSID/Port': 'Not Available',
            'Auth Type': 'Not Available',
            'Matched Auth Policy Rule': 'Not Available'
        })
    
    # Create DataFrame
    df = pd.DataFrame(endpoint_data)
    
    # Create a lookup dictionary for NAC clients by MAC address
    nac_lookup = {}
    
    for client in nac_clients:
        device_mac = normalize_mac_address(client.get('mac', ''))
        timestamp = client.get('timestamp')
        auth_rule = client.get('last_nacrule_name', '')
        client_type = client.get('type', 'unknown')
        
        if not device_mac:
            continue
        
        # Keep the most recent entry for each MAC
        if device_mac not in nac_lookup or (timestamp and timestamp > nac_lookup[device_mac]['timestamp']):
            nac_lookup[device_mac] = {
                'timestamp': timestamp,
                'auth_rule': auth_rule,
                'type': client_type,
                'ssid': client.get('last_ssid', '') if client_type == 'wireless' else '',
                'port_id': client.get('last_port_id', '') if client_type == 'wired' else '',
                'auth_type': client.get('auth_type', ''),
                'site_id': client.get('site_id', '')
            }
    
    print(f"📁 Unique NAC client MACs: {len(nac_lookup)}")
    
    # Update the endpoint report with NAC client data
    matches_found = 0
    for idx, row in df.iterrows():
        mac_address = row['MAC Address']
        
        if mac_address in nac_lookup:
            nac_data = nac_lookup[mac_address]
            df.at[idx, 'Last Seen'] = format_timestamp(nac_data['timestamp'])
            df.at[idx, 'Connection Type'] = nac_data['type'].title()
            df.at[idx, 'Auth Type'] = nac_data['auth_type'].upper() if nac_data['auth_type'] else 'Unknown'
            df.at[idx, 'Matched Auth Policy Rule'] = nac_data['auth_rule'] or 'No Rule Matched'
            
            # Set site name
            site_id = nac_data['site_id']
            df.at[idx, 'Site'] = site_lookup.get(site_id, f'Unknown Site ({site_id[:8]}...)' if site_id else 'No Site')
            
            # Set SSID for wireless or Port for wired
            if nac_data['type'] == 'wireless' and nac_data['ssid']:
                df.at[idx, 'SSID/Port'] = f"SSID: {nac_data['ssid']}"
            elif nac_data['type'] == 'wired' and nac_data['port_id']:
                df.at[idx, 'SSID/Port'] = f"Port: {nac_data['port_id']}"
            else:
                df.at[idx, 'SSID/Port'] = 'Not Available'
            
            matches_found += 1
    
    print(f"✅ Found {matches_found} MAC address matches")
    
    return df

@timer
def export_to_csv(df: pd.DataFrame, filename: str):
    """Export DataFrame to CSV"""
    df.to_csv(filename, index=False)
    print(f"📄 CSV report generated: {filename}")

@timer
def export_to_json(df: pd.DataFrame, filename: str, stats: Dict):
    """Export DataFrame and statistics to JSON"""
    
    # Create a copy of the DataFrame and handle non-serializable data
    df_clean = df.copy()
    
    # Convert any datetime columns to strings and handle NaT/NaN values
    for col in df_clean.columns:
        if df_clean[col].dtype == 'datetime64[ns]':
            df_clean[col] = df_clean[col].dt.strftime('%Y-%m-%d %H:%M:%S').fillna('Never')
        elif df_clean[col].dtype == 'object':
            df_clean[col] = df_clean[col].fillna('')
        elif df_clean[col].dtype in ['float64', 'int64']:
            df_clean[col] = df_clean[col].fillna(0)
    
    # Convert to records and ensure all values are JSON serializable
    endpoints_data = []
    for record in df_clean.to_dict('records'):
        clean_record = {}
        for key, value in record.items():
            if pd.isna(value) or value is pd.NaT:
                clean_record[key] = None
            elif hasattr(value, 'isoformat'):  # datetime objects
                clean_record[key] = value.isoformat()
            else:
                clean_record[key] = value
        endpoints_data.append(clean_record)
    
    # Clean statistics data as well
    clean_stats = {}
    for key, value in stats.items():
        if isinstance(value, dict):
            clean_stats[key] = {k: (v if not pd.isna(v) else 0) for k, v in value.items()}
        elif pd.isna(value):
            clean_stats[key] = 0
        else:
            clean_stats[key] = value
    
    data = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'total_records': len(df),
            'report_type': 'mist_endpoint_report'
        },
        'statistics': clean_stats,
        'endpoints': endpoints_data
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"📄 JSON report generated: {filename}")

@timer
def export_to_excel(df: pd.DataFrame, filename: str, stats: Dict):
    """Export DataFrame to Excel with multiple sheets and formatting"""
    try:
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Main data sheet
            df.to_excel(writer, sheet_name='Endpoint Report', index=False)
            
            # Statistics sheet
            stats_df = pd.DataFrame([
                ['Total Devices', stats['total_devices']],
                ['Active Last 24h', stats['active_last_24h']],
                ['Active Last 7d', stats['active_last_7d']],
                ['Never Seen', stats['never_seen']],
                ['With Auth Rules', stats['with_auth_rules']],
                ['Compliance Rate (%)', f"{stats['compliance_rate']:.1f}"]
            ], columns=['Metric', 'Value'])
            
            stats_df.to_excel(writer, sheet_name='Statistics', index=False)
            
            # Connection Type breakdown
            conn_type_df = pd.DataFrame(list(stats['by_connection_type'].items()), 
                                      columns=['Connection Type', 'Count'])
            conn_type_df.to_excel(writer, sheet_name='Connection Types', index=False)
            
            # Site breakdown
            site_df = pd.DataFrame(list(stats['by_site'].items()), 
                                 columns=['Site', 'Count'])
            site_df.to_excel(writer, sheet_name='Sites', index=False)
            
            # Auth Type breakdown
            auth_df = pd.DataFrame(list(stats['by_auth_type'].items()), 
                                 columns=['Auth Type', 'Count'])
            auth_df.to_excel(writer, sheet_name='Auth Types', index=False)
        
        print(f"📄 Excel report generated: {filename}")
        
    except ImportError:
        print("⚠️ openpyxl not installed. Install with: pip3 install openpyxl")
        print("   Skipping Excel export...")

def generate_html_report(df: pd.DataFrame, output_file: str = 'mist_endpoint_report.html', 
                        color_theme: str = 'default', stats: Dict = None):
    """Generate an enhanced HTML report with advanced filtering and statistics"""
    
    # Define color themes
    themes = {
        'default': {'bg': '#4A90E2', 'accent': '#357ABD'},
        'sunset': {'bg': '#FF6B35', 'accent': '#E55A2B'}, 
        'ocean': {'bg': '#0077BE', 'accent': '#005A8B'},
        'forest': {'bg': '#228B22', 'accent': '#1F7A1F'},
        'dark': {'bg': '#2C3E50', 'accent': '#34495E'},
        'corporate': {'bg': '#1E3A8A', 'accent': '#1E40AF'}
    }
    
    colors = themes.get(color_theme, themes['default'])
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('<!DOCTYPE html>\n')
        f.write('<html lang="en">\n')
        f.write('<head>\n')
        f.write('<meta charset="UTF-8">\n')
        f.write('<meta name="viewport" content="width=device-width, initial-scale=1.0">\n')
        f.write('<title>Enhanced Mist Endpoint Report</title>\n')
        f.write('<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" rel="stylesheet">\n')
        f.write('<style>\n')
        f.write('body { font-family: Arial, sans-serif; margin: 20px; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }\n')
        f.write('.container { max-width: 1400px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }\n')
        f.write('.material-symbols-outlined { vertical-align: middle; margin-right: 6px; font-size: 18px; }\n')
        f.write('.connection-wired { color: #1565c0; }\n')
        f.write('.connection-wireless { color: #2e7d32; }\n')
        f.write('h1 { color: #333; text-align: center; margin-bottom: 10px; }\n')
        f.write('.subtitle { text-align: center; color: #666; margin-bottom: 20px; }\n')
        f.write('.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }\n')
        f.write(f'.stat-card {{ background: linear-gradient(135deg, {colors["bg"]} 0%, {colors["accent"]} 100%); color: white; padding: 15px; border-radius: 8px; text-align: center; }}\n')
        f.write('.stat-number { font-size: 2em; font-weight: bold; margin-bottom: 5px; }\n')
        f.write('.stat-label { font-size: 0.9em; opacity: 0.9; }\n')
        f.write('table { border-collapse: collapse; width: 100%; margin-top: 20px; }\n')
        f.write('th, td { border: 1px solid #ddd; padding: 8px; text-align: left; font-size: 0.9em; }\n')
        f.write(f'th {{ background: {colors["bg"]}; color: white; cursor: pointer; user-select: none; font-weight: bold; }}\n')
        f.write(f'th:hover {{ background: {colors["accent"]}; }}\n')
        f.write('th.sort-asc::after { content: " ▲"; color: #fff; }\n')
        f.write('th.sort-desc::after { content: " ▼"; color: #fff; }\n')
        f.write('tr:nth-child(even) { background-color: #f8f9fa; }\n')
        f.write('tr:hover { background-color: #e8f4fd; }\n')
        f.write('.never-seen { color: #dc3545; font-style: italic; font-weight: bold; }\n')
        f.write('.recently-active { color: #28a745; font-weight: bold; }\n')
        f.write(f'.download-btn {{ background: {colors["bg"]}; color: white; padding: 12px 24px; border: none; border-radius: 6px; cursor: pointer; margin: 10px 5px; font-size: 14px; font-weight: bold; transition: all 0.3s ease; }}\n')
        f.write(f'.download-btn:hover {{ background: {colors["accent"]}; transform: translateY(-1px); box-shadow: 0 4px 8px rgba(0,0,0,0.2); }}\n')
        f.write('.controls { margin: 20px 0; display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }\n')
        f.write('.filter-input { padding: 8px; border-radius: 4px; border: 1px solid #ddd; min-width: 200px; }\n')
        f.write('.performance-info { background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid ' + colors["bg"] + '; }\n')
        f.write('</style>\n')
        
        # Add enhanced JavaScript functionality
        f.write('<script>\n')
        f.write('let originalRows = [];\n\n')
        
        f.write('function initializeTable() {\n')
        f.write('  const tbody = document.querySelector("tbody");\n')
        f.write('  originalRows = Array.from(tbody.querySelectorAll("tr"));\n')
        f.write('}\n\n')
        
        f.write('function sortTable(columnIndex) {\n')
        f.write('  const table = document.querySelector("table");\n')
        f.write('  const tbody = table.querySelector("tbody");\n')
        f.write('  const rows = Array.from(tbody.querySelectorAll("tr"));\n')
        f.write('  const header = table.querySelectorAll("th")[columnIndex];\n')
        f.write('  \n')
        f.write('  table.querySelectorAll("th").forEach(th => {\n')
        f.write('    th.classList.remove("sort-asc", "sort-desc");\n')
        f.write('  });\n')
        f.write('  \n')
        f.write('  const isAscending = !header.dataset.sortDir || header.dataset.sortDir === "desc";\n')
        f.write('  header.dataset.sortDir = isAscending ? "asc" : "desc";\n')
        f.write('  header.classList.add(isAscending ? "sort-asc" : "sort-desc");\n')
        f.write('  \n')
        f.write('  rows.sort((a, b) => {\n')
        f.write('    const aText = a.cells[columnIndex].textContent.trim();\n')
        f.write('    const bText = b.cells[columnIndex].textContent.trim();\n')
        f.write('    \n')
        f.write('    if (aText.includes("Never") && !bText.includes("Never")) return isAscending ? 1 : -1;\n')
        f.write('    if (bText.includes("Never") && !aText.includes("Never")) return isAscending ? -1 : 1;\n')
        f.write('    if (aText.includes("Never") && bText.includes("Never")) return 0;\n')
        f.write('    \n')
        f.write('    if (columnIndex === 4) {\n')  # Last Seen column
        f.write('      const aDate = new Date(aText.replace(/[🟢🟡❌❓]/g, "").trim());\n')
        f.write('      const bDate = new Date(bText.replace(/[🟢🟡❌❓]/g, "").trim());\n')
        f.write('      if (!isNaN(aDate) && !isNaN(bDate)) {\n')
        f.write('        return isAscending ? aDate - bDate : bDate - aDate;\n')
        f.write('      }\n')
        f.write('    }\n')
        f.write('    \n')
        f.write('    const result = aText.localeCompare(bText, undefined, {numeric: true});\n')
        f.write('    return isAscending ? result : -result;\n')
        f.write('  });\n')
        f.write('  \n')
        f.write('  rows.forEach(row => tbody.appendChild(row));\n')
        f.write('}\n\n')
        
        f.write('function filterTable() {\n')
        f.write('  const filterValue = document.getElementById("tableFilter").value.toLowerCase();\n')
        f.write('  const tbody = document.querySelector("tbody");\n')
        f.write('  const rows = tbody.querySelectorAll("tr");\n')
        f.write('  \n')
        f.write('  rows.forEach(row => {\n')
        f.write('    const text = row.textContent.toLowerCase();\n')
        f.write('    row.style.display = text.includes(filterValue) ? "" : "none";\n')
        f.write('  });\n')
        f.write('  \n')
        f.write('  updateFilterStats();\n')
        f.write('}\n\n')
        
        f.write('function updateFilterStats() {\n')
        f.write('  const tbody = document.querySelector("tbody");\n')
        f.write('  const visibleRows = tbody.querySelectorAll("tr:not([style*=\\"display: none\\"])").length;\n')
        f.write('  const totalRows = tbody.querySelectorAll("tr").length;\n')
        f.write('  document.getElementById("filterStats").textContent = `Showing ${visibleRows} of ${totalRows} endpoints`;\n')
        f.write('}\n\n')
        
        f.write('function downloadCSV() {\n')
        f.write('  const table = document.querySelector("table");\n')
        f.write('  const rows = table.querySelectorAll("tr");\n')
        f.write('  let csv = "";\n')
        f.write('  rows.forEach(row => {\n')
        f.write('    if (row.style.display !== "none") {\n')
        f.write('      const cells = row.querySelectorAll("th, td");\n')
        f.write('      const rowData = [];\n')
        f.write('      cells.forEach(cell => {\n')
        f.write('        let cellText = cell.textContent.trim();\n')
        f.write('        cellText = cellText.replace(/[🟢🟡❌❓]/g, "").trim();\n')
        f.write('        if (cellText.includes(",")) {\n')
        f.write('          cellText = "\\"" + cellText.replace(/"/g, "\\"\\"") + "\\"";\n')
        f.write('        }\n')
        f.write('        rowData.push(cellText);\n')
        f.write('      });\n')
        f.write('      csv += rowData.join(",") + "\\n";\n')
        f.write('    }\n')
        f.write('  });\n')
        f.write('  const blob = new Blob([csv], { type: "text/csv" });\n')
        f.write('  const url = window.URL.createObjectURL(blob);\n')
        f.write('  const a = document.createElement("a");\n')
        f.write('  a.href = url;\n')
        f.write('  a.download = "mist_endpoint_report_" + new Date().toISOString().slice(0,19).replace(/[:-]/g, "") + ".csv";\n')
        f.write('  document.body.appendChild(a);\n')
        f.write('  a.click();\n')
        f.write('  document.body.removeChild(a);\n')
        f.write('  window.URL.revokeObjectURL(url);\n')
        f.write('}\n\n')
        
        f.write('function showOnlyNeverSeen() {\n')
        f.write('  const tbody = document.querySelector("tbody");\n')
        f.write('  const rows = tbody.querySelectorAll("tr");\n')
        f.write('  \n')
        f.write('  rows.forEach(row => {\n')
        f.write('    const lastSeenCell = row.cells[4];\n')
        f.write('    const isNeverSeen = lastSeenCell.textContent.includes("Never");\n')
        f.write('    row.style.display = isNeverSeen ? "" : "none";\n')
        f.write('  });\n')
        f.write('  \n')
        f.write('  updateFilterStats();\n')
        f.write('}\n\n')
        
        f.write('function showAll() {\n')
        f.write('  const tbody = document.querySelector("tbody");\n')
        f.write('  const rows = tbody.querySelectorAll("tr");\n')
        f.write('  \n')
        f.write('  rows.forEach(row => {\n')
        f.write('    row.style.display = "";\n')
        f.write('  });\n')
        f.write('  \n')
        f.write('  document.getElementById("tableFilter").value = "";\n')
        f.write('  updateFilterStats();\n')
        f.write('}\n\n')
        
        f.write('window.onload = function() {\n')
        f.write('  initializeTable();\n')
        f.write('  updateFilterStats();\n')
        f.write('};\n')
        f.write('</script>\n')
        f.write('</head>\n')
        f.write('<body>\n')
        f.write('<div class="container">\n')
        f.write('<h1>🌐 Enhanced Mist Endpoint Report</h1>\n')
        f.write(f'<div class="subtitle">Generated on {datetime.now().strftime("%B %d, %Y at %I:%M:%S %p")} - Theme: {color_theme.title()}</div>\n')
        
        # Add statistics cards if available
        if stats:
            f.write('<div class="stats-grid">\n')
            f.write(f'<div class="stat-card"><div class="stat-number">{stats["total_devices"]}</div><div class="stat-label">Total Devices</div></div>\n')
            f.write(f'<div class="stat-card"><div class="stat-number">{stats["active_last_24h"]}</div><div class="stat-label">Active Last 24h</div></div>\n')
            f.write(f'<div class="stat-card"><div class="stat-number">{stats["active_last_7d"]}</div><div class="stat-label">Active Last 7d</div></div>\n')
            f.write(f'<div class="stat-card"><div class="stat-number">{stats["never_seen"]}</div><div class="stat-label">Never Seen</div></div>\n')
            f.write(f'<div class="stat-card"><div class="stat-number">{stats["with_auth_rules"]}</div><div class="stat-label">With Auth Rules</div></div>\n')
            f.write(f'<div class="stat-card"><div class="stat-number">{stats["compliance_rate"]:.1f}%</div><div class="stat-label">Compliance Rate</div></div>\n')
            f.write('</div>\n')
        
        # Add enhanced controls with filtering
        f.write('<div class="controls">\n')
        f.write('<button class="download-btn" onclick="downloadCSV()">📥 Download Filtered CSV</button>\n')
        f.write('<button class="download-btn" onclick="showOnlyNeverSeen()">👻 Show Never Seen</button>\n')
        f.write('<button class="download-btn" onclick="showAll()">🔄 Show All</button>\n')
        f.write('<input type="text" id="tableFilter" class="filter-input" placeholder="🔍 Filter endpoints..." onkeyup="filterTable()">\n')
        f.write('<span id="filterStats" style="margin-left: 10px; color: #666;"></span>\n')
        f.write('</div>\n')
        
        f.write('<table>\n')
        f.write('<thead>\n')
        f.write('<tr>\n')
        f.write('<th onclick="sortTable(0)">Name</th>\n')
        f.write('<th onclick="sortTable(1)">MAC Address</th>\n')
        f.write('<th onclick="sortTable(2)">Labels</th>\n')
        f.write('<th onclick="sortTable(3)">Description</th>\n')
        f.write('<th onclick="sortTable(4)">Last Seen</th>\n')
        f.write('<th onclick="sortTable(5)">Auth Type</th>\n')
        f.write('<th onclick="sortTable(6)">Site</th>\n')
        f.write('<th onclick="sortTable(7)">Connection Type</th>\n')
        f.write('<th onclick="sortTable(8)">SSID/Port</th>\n')
        f.write('<th onclick="sortTable(9)">Matched Auth Policy Rule</th>\n')
        f.write('</tr>\n')
        f.write('</thead>\n')
        f.write('<tbody>\n')
        
        # Determine which entries are recently active
        recent_cutoff = datetime.now() - timedelta(hours=24)
        
        for _, row in df.iterrows():
            f.write('<tr>\n')
            f.write(f'<td>{row["Name"] or "Unnamed Device"}</td>\n')
            f.write(f'<td>{row["MAC Address"]}</td>\n')
            f.write(f'<td>{row["Labels"]}</td>\n')
            f.write(f'<td>{row["Description"] or "No description"}</td>\n')
            
            # Enhanced Last Seen with activity indicators
            last_seen = row['Last Seen']
            if last_seen == 'Never':
                last_seen_class = 'class="never-seen"'
                activity_icon = '❌'
            else:
                try:
                    last_seen_dt = datetime.strptime(last_seen, "%b %d, %Y %I:%M:%S %p")
                    if last_seen_dt >= recent_cutoff:
                        last_seen_class = 'class="recently-active"'
                        activity_icon = '🟢'
                    else:
                        last_seen_class = ''
                        activity_icon = '🟡'
                except:
                    last_seen_class = ''
                    activity_icon = '❓'
            
            f.write(f'<td {last_seen_class}>{activity_icon} {last_seen}</td>\n')
            f.write(f'<td>{row["Auth Type"]}</td>\n')
            f.write(f'<td>🏢 {row["Site"]}</td>\n')
            
            # Add icons for connection types
            conn_type = row["Connection Type"]
            if conn_type.lower() == 'wireless':
                conn_display = f'<span class="material-symbols-outlined connection-wireless">wifi</span>{conn_type}'
            elif conn_type.lower() == 'wired':
                conn_display = f'<span class="material-symbols-outlined connection-wired">lan</span>{conn_type}'
            else:
                conn_display = f'❓ {conn_type}'
            
            f.write(f'<td>{conn_display}</td>\n')
            f.write(f'<td>{row["SSID/Port"]}</td>\n')
            f.write(f'<td>{row["Matched Auth Policy Rule"]}</td>\n')
            f.write('</tr>\n')
        
        f.write('</tbody>\n')
        f.write('</table>\n')
        
        # Add performance info section
        if stats:
            f.write('<div class="performance-info">\n')
            f.write('<h3>📊 Report Details</h3>\n')
            f.write('<p><strong>Coverage:</strong> User MACs database and NAC client activity</p>\n')
            f.write('<p><strong>Activity Indicators:</strong> 🟢 Active (24h) | 🟡 Older | ❌ Never Seen | <span class="material-symbols-outlined connection-wireless">wifi</span> Wireless | <span class="material-symbols-outlined connection-wired">lan</span> Wired</p>\n')
            
            # Connection type breakdown
            conn_types = stats.get('by_connection_type', {})
            conn_summary = ' | '.join([f'{k.title()}: {v}' for k, v in conn_types.items()])
            f.write(f'<p><strong>Connection Types:</strong> {conn_summary} | </p>\n')
            
            # Top sites breakdown  
            sites = stats.get('by_site', {})
            top_sites = sorted(sites.items(), key=lambda x: x[1], reverse=True)[:5]
            sites_summary = ' | '.join([f'{k}: {v}' for k, v in top_sites])
            f.write(f'<p><strong>Top Sites:</strong> {sites_summary} | </p>\n')
            f.write('</div>\n')
        
        f.write('</div>\n')
        f.write('</body>\n')
        f.write('</html>\n')
    
    print(f"📄 Enhanced HTML report generated: {output_file}")

def main():
    """Main function to run the enhanced endpoint report generation"""
    
    # Parse command line arguments
    args = parse_command_line_args()
    
    # Handle special commands
    if args.create_config:
        create_sample_config()
        return
    
    if args.encrypt_config:
        if not ENCRYPTION_AVAILABLE:
            print("❌ Encryption not available. Install cryptography: pip3 install cryptography")
            sys.exit(1)
        
        config_file = Path("Resources") / "mist_config.ini"
        if not config_file.exists():
            print(f"❌ Configuration file not found: {config_file}")
            print("   Create it first with: python3 mist_endpoint_report.py --create-config")
            sys.exit(1)
        
        # Check for key file
        key_file = Path("Resources") / "encryption.key"
        if key_file.exists():
            encryptor = ConfigEncryption(key_file=str(key_file))
        else:
            encryptor = ConfigEncryption()
        
        try:
            encryptor.encrypt_config_file(str(config_file))
            print("✅ Configuration encrypted successfully!")
        except Exception as e:
            print(f"❌ Encryption failed: {e}")
            sys.exit(1)
        return
    
    if args.decrypt_config:
        if not ENCRYPTION_AVAILABLE:
            print("❌ Encryption not available. Install cryptography: pip3 install cryptography")
            sys.exit(1)
        
        encrypted_file = Path("Resources") / "mist_config.ini.enc"
        if not encrypted_file.exists():
            print(f"❌ Encrypted configuration file not found: {encrypted_file}")
            sys.exit(1)
        
        # Check for key file
        key_file = Path("Resources") / "encryption.key"
        if key_file.exists():
            encryptor = ConfigEncryption(key_file=str(key_file))
        else:
            encryptor = ConfigEncryption()
        
        try:
            encryptor.decrypt_config_file(str(encrypted_file))
            print("✅ Configuration decrypted successfully!")
            print("⚠️ Remember to re-encrypt after editing!")
        except Exception as e:
            print(f"❌ Decryption failed: {e}")
            sys.exit(1)
        return

    # Load configuration from file if available
    config_data = load_config(args.config)
    
    # Determine configuration source and values
    if args.token and args.org_id:
        # Use command line arguments (highest priority)
        API_TOKEN = args.token
        ORG_ID = args.org_id
        BASE_URL = args.base_url.rstrip('/')
        THEME = args.theme
        DAYS = args.days
        print("📋 Using command line arguments")
    elif config_data.get('api_token') and config_data.get('org_id'):
        # Use config file values, override with any provided command line args
        API_TOKEN = args.token or config_data['api_token']
        ORG_ID = args.org_id or config_data['org_id']
        BASE_URL = (args.base_url if args.base_url != 'https://api.mist.com' else config_data['base_url']).rstrip('/')
        THEME = args.theme if args.theme != 'default' else config_data.get('theme', 'default')
        DAYS = args.days if args.days != 7 else config_data.get('days', 7)
        print("📋 Using configuration file with command line overrides")
    else:
        # No configuration available - get everything from user input
        API_TOKEN, ORG_ID, BASE_URL = get_user_input()
        THEME = args.theme
        DAYS = args.days
    
    print("🚀 Starting Enhanced Mist Endpoint Report Generation...")
    print(f"📊 Organization ID: {ORG_ID}")
    print(f"🌐 API Endpoint: {BASE_URL}")
    print(f"🎨 Theme: {THEME}")
    print(f"📅 Days to analyze: {DAYS}")
    if args.site:
        print(f"🏢 Site filter: {args.site}")
    if args.connection_type:
        print(f"📌 Connection type filter: {args.connection_type}")
    print()
    
    # Parse output formats
    output_formats = [fmt.strip().lower() for fmt in args.format.split(',')]
    print(f"📄 Output formats: {', '.join(output_formats)}")
    print()
    
    # Initialize API client
    client = MistAPIClient(API_TOKEN, ORG_ID, BASE_URL)
    
    try:
        # Step 1: Get Sites for lookup
        print("🏢 Step 1: Fetching Sites...")
        site_lookup = client.get_sites()
        print()
        
        # Step 2: Get User MACs
        print("📋 Step 2: Fetching User MACs...")
        user_macs = client.get_user_macs()
        print(f"✅ Retrieved {len(user_macs)} user MAC entries")
        print()
        
        # Step 3: Get NAC Clients with filtering
        print(f"🔍 Step 3: Fetching NAC Clients (last {DAYS} days)...")
        nac_clients = client.get_nac_clients_last_n_days(
            days=DAYS, 
            site_id=args.site, 
            connection_type=args.connection_type
        )
        print(f"✅ Retrieved {len(nac_clients)} NAC client records")
        print()
        
        # Step 4: Create combined report
        print("📄 Step 4: Creating endpoint report...")
        df = create_endpoint_report(user_macs, nac_clients, site_lookup)
        print(f"✅ Created report with {len(df)} endpoints")
        print()
        
        # Step 5: Generate statistics
        print("📊 Step 5: Generating statistics...")
        stats = generate_statistics(df)
        print("✅ Statistics generated")
        print()
        
        # Step 6: Create Reports directory
        reports_dir = Path("Reports")
        reports_dir.mkdir(exist_ok=True)
        print(f"📁 Reports directory: {reports_dir}")
        
        # Step 7: Generate reports in requested formats
        print("📄 Step 7: Generating enhanced reports...")
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        for output_format in output_formats:
            if output_format == 'html':
                output_file = reports_dir / f"mist_endpoint_report_{timestamp}.html"
                generate_html_report(df, str(output_file), THEME, stats)
            elif output_format == 'csv':
                output_file = reports_dir / f"mist_endpoint_report_{timestamp}.csv"
                export_to_csv(df, str(output_file))
            elif output_format == 'json':
                output_file = reports_dir / f"mist_endpoint_report_{timestamp}.json"
                export_to_json(df, str(output_file), stats)
            elif output_format == 'excel':
                output_file = reports_dir / f"mist_endpoint_report_{timestamp}.xlsx"
                export_to_excel(df, str(output_file), stats)
            else:
                print(f"⚠️ Unknown format: {output_format}")
        
        print()
        
        # Enhanced Summary with performance metrics
        total_endpoints = len(df)
        active_endpoints = stats['active_last_7d']
        with_auth_rules = stats['with_auth_rules']
        wireless_devices = stats['by_connection_type'].get('Wireless', 0)
        wired_devices = stats['by_connection_type'].get('Wired', 0)
        
        print("📊 Enhanced Report Summary:")
        print(f"   Total Endpoints: {total_endpoints}")
        print(f"   Active (24h): {stats['active_last_24h']}")
        print(f"   Active (7d): {active_endpoints}")
        print(f"   Never Seen: {stats['never_seen']}")
        print(f"   With Auth Rules: {with_auth_rules}")
        print(f"   Wireless Devices: {wireless_devices}")
        print(f"   Wired Devices: {wired_devices}")
        print(f"   Compliance Rate: {stats['compliance_rate']:.1f}%")
        print(f"   Activity Rate (7d): {(active_endpoints/total_endpoints*100):.1f}%" if total_endpoints > 0 else "   Activity Rate: 0%")
        
        # Show top sites
        if stats['by_site']:
            top_sites = sorted(stats['by_site'].items(), key=lambda x: x[1], reverse=True)[:3]
            print(f"   Top Sites: {', '.join([f'{site}: {count}' for site, count in top_sites])}")
        
        print()
        print(f"✅ Enhanced report generation completed!")
        print(f"📁 Reports saved in: {reports_dir}/")
        
    except KeyboardInterrupt:
        print("\n⚠️ Report generation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()