#!/usr/bin/env python3
"""
Configuration File Encryption Module

This module provides encryption/decryption for sensitive configuration files
using AES-256 encryption with password-based key derivation.

Requirements:
pip install cryptography

Usage:
    from config_encryption import ConfigEncryption
    
    # Initialize with password
    encryptor = ConfigEncryption()
    
    # Encrypt a config file
    encryptor.encrypt_config_file('Resources/mist_config.ini')
    
    # Decrypt and load config
    config = encryptor.load_encrypted_config('Resources/mist_config.ini.enc')
    
    # Or use with context manager for auto-cleanup
    with ConfigEncryption() as enc:
        config = enc.load_encrypted_config('config.ini.enc')
"""

import os
import sys
import getpass
import hashlib
import base64
import configparser
from typing import Dict, Optional
from pathlib import Path
import tempfile
import atexit
import signal

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
except ImportError:
    print("❌ Error: cryptography library not found")
    print("📦 Install with: pip3.13 install cryptography")
    sys.exit(1)

class ConfigEncryption:
    """Handle encryption and decryption of configuration files"""
    
    def __init__(self, password: str = None, key_file: str = None):
        """
        Initialize encryption handler
        
        Args:
            password: Master password for encryption (will prompt if not provided)
            key_file: Path to key file (alternative to password)
        """
        self.temp_files = []  # Track temporary decrypted files for cleanup
        self.key_file = key_file
        self.password = password
        self._setup_cleanup()
    
    def _setup_cleanup(self):
        """Setup cleanup handlers for temporary files"""
        atexit.register(self._cleanup_temp_files)
        signal.signal(signal.SIGTERM, self._signal_cleanup)
        signal.signal(signal.SIGINT, self._signal_cleanup)
    
    def _signal_cleanup(self, signum, frame):
        """Handle cleanup on signal"""
        self._cleanup_temp_files()
        sys.exit(0)
    
    def _cleanup_temp_files(self):
        """Clean up temporary decrypted files"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    # Overwrite with random data before deletion (security)
                    file_size = os.path.getsize(temp_file)
                    with open(temp_file, 'wb') as f:
                        f.write(os.urandom(file_size))
                    os.remove(temp_file)
            except Exception as e:
                print(f"⚠️ Warning: Could not securely delete {temp_file}: {e}")
        self.temp_files.clear()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup"""
        self._cleanup_temp_files()
    
    def _get_password(self) -> str:
        """Get encryption password from user or environment"""
        if self.password:
            return self.password
        
        # Try environment variable first
        env_password = os.environ.get('MIST_CONFIG_PASSWORD')
        if env_password:
            print("🔑 Using password from MIST_CONFIG_PASSWORD environment variable")
            return env_password
        
        # Prompt user for password
        print("🔐 Configuration files are encrypted")
        password = getpass.getpass("🔑 Enter master password: ").strip()
        
        if not password:
            raise ValueError("Password is required for encrypted configuration")
        
        return password
    
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password using PBKDF2"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,  # High iteration count for security
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def _generate_key_from_file(self) -> bytes:
        """Generate encryption key from key file"""
        if not self.key_file or not os.path.exists(self.key_file):
            raise FileNotFoundError(f"Key file not found: {self.key_file}")
        
        with open(self.key_file, 'rb') as f:
            key_data = f.read()
        
        # Use SHA-256 hash of key file content as key
        key_hash = hashlib.sha256(key_data).digest()
        return base64.urlsafe_b64encode(key_hash)
    
    def create_key_file(self, key_file_path: str) -> None:
        """Create a random key file for encryption"""
        key_dir = os.path.dirname(key_file_path)
        if key_dir and not os.path.exists(key_dir):
            os.makedirs(key_dir)
        
        # Generate random key
        random_key = os.urandom(64)  # 512-bit random key
        
        with open(key_file_path, 'wb') as f:
            f.write(random_key)
        
        # Set restrictive permissions
        os.chmod(key_file_path, 0o600)
        
        print(f"🔑 Created encryption key file: {key_file_path}")
        print("⚠️ Keep this file secure - it's needed to decrypt your configs!")
    
    def encrypt_config_file(self, config_path: str, output_path: str = None) -> str:
        """
        Encrypt a configuration file
        
        Args:
            config_path: Path to plaintext config file
            output_path: Path for encrypted file (default: config_path + '.enc')
            
        Returns:
            Path to encrypted file
        """
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        if output_path is None:
            output_path = config_path + '.enc'
        
        # Read plaintext config
        with open(config_path, 'rb') as f:
            plaintext_data = f.read()
        
        # Get encryption key
        if self.key_file:
            key = self._generate_key_from_file()
            salt = b''  # No salt needed for key file approach
        else:
            password = self._get_password()
            salt = os.urandom(16)  # 128-bit salt
            key = self._derive_key(password, salt)
        
        # Encrypt data
        fernet = Fernet(key)
        encrypted_data = fernet.encrypt(plaintext_data)
        
        # Save encrypted file with salt (if using password)
        with open(output_path, 'wb') as f:
            if not self.key_file:
                f.write(salt)  # Write salt first
            f.write(encrypted_data)
        
        # Set restrictive permissions
        os.chmod(output_path, 0o600)
        
        print(f"🔒 Encrypted configuration: {config_path} → {output_path}")
        
        # Optionally remove plaintext file
        response = input(f"🗑️ Delete plaintext file {config_path}? (y/N): ").strip().lower()
        if response in ['y', 'yes']:
            # Securely overwrite before deletion
            file_size = os.path.getsize(config_path)
            with open(config_path, 'wb') as f:
                f.write(os.urandom(file_size))
            os.remove(config_path)
            print(f"🗑️ Deleted plaintext file: {config_path}")
        
        return output_path
    
    def decrypt_config_file(self, encrypted_path: str, output_path: str = None) -> str:
        """
        Decrypt a configuration file
        
        Args:
            encrypted_path: Path to encrypted config file
            output_path: Path for decrypted file (default: remove .enc extension)
            
        Returns:
            Path to decrypted file
        """
        if not os.path.exists(encrypted_path):
            raise FileNotFoundError(f"Encrypted file not found: {encrypted_path}")
        
        if output_path is None:
            if encrypted_path.endswith('.enc'):
                output_path = encrypted_path[:-4]  # Remove .enc extension
            else:
                output_path = encrypted_path + '.dec'
        
        # Read encrypted file
        with open(encrypted_path, 'rb') as f:
            file_data = f.read()
        
        # Extract salt and encrypted data
        if self.key_file:
            key = self._generate_key_from_file()
            encrypted_data = file_data
        else:
            password = self._get_password()
            salt = file_data[:16]  # First 16 bytes are salt
            encrypted_data = file_data[16:]  # Rest is encrypted data
            key = self._derive_key(password, salt)
        
        # Decrypt data
        try:
            fernet = Fernet(key)
            plaintext_data = fernet.decrypt(encrypted_data)
        except Exception as e:
            raise ValueError("Decryption failed - incorrect password or corrupted file") from e
        
        # Save decrypted file
        with open(output_path, 'wb') as f:
            f.write(plaintext_data)
        
        # Set restrictive permissions
        os.chmod(output_path, 0o600)
        
        print(f"🔓 Decrypted configuration: {encrypted_path} → {output_path}")
        return output_path
    
    def load_encrypted_config(self, encrypted_path: str) -> configparser.ConfigParser:
        """
        Load and parse an encrypted configuration file
        
        Args:
            encrypted_path: Path to encrypted config file
            
        Returns:
            Parsed ConfigParser object
        """
        # Create temporary file for decrypted content
        with tempfile.NamedTemporaryFile(mode='w+b', delete=False, suffix='.ini') as temp_file:
            temp_path = temp_file.name
        
        # Track for cleanup
        self.temp_files.append(temp_path)
        
        try:
            # Decrypt to temporary file
            self.decrypt_config_file(encrypted_path, temp_path)
            
            # Parse configuration
            config = configparser.ConfigParser()
            config.read(temp_path)
            
            return config
            
        except Exception as e:
            # Clean up on error
            if temp_path in self.temp_files:
                self.temp_files.remove(temp_path)
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise e
    
    def get_config_dict(self, encrypted_path: str, section: str = None) -> Dict:
        """
        Load encrypted config and return as dictionary
        
        Args:
            encrypted_path: Path to encrypted config file
            section: Specific section to return (if None, returns all sections)
            
        Returns:
            Configuration as dictionary
        """
        config = self.load_encrypted_config(encrypted_path)
        
        if section:
            if section not in config:
                raise ValueError(f"Section '{section}' not found in configuration")
            return dict(config[section])
        else:
            # Return all sections
            result = {}
            for section_name in config.sections():
                result[section_name] = dict(config[section_name])
            return result

def setup_encryption_cli():
    """Command-line interface for encryption setup"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Encrypt/decrypt Mist configuration files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --encrypt Resources/mist_config.ini
  %(prog)s --decrypt Resources/mist_config.ini.enc
  %(prog)s --create-key Resources/encryption.key
  %(prog)s --encrypt Resources/mist_config.ini --key-file Resources/encryption.key
        """
    )
    
    parser.add_argument('--encrypt', help='Encrypt a configuration file')
    parser.add_argument('--decrypt', help='Decrypt a configuration file')
    parser.add_argument('--create-key', help='Create a new encryption key file')
    parser.add_argument('--key-file', help='Use key file instead of password')
    parser.add_argument('--output', help='Output file path')
    
    args = parser.parse_args()
    
    try:
        if args.create_key:
            encryptor = ConfigEncryption()
            encryptor.create_key_file(args.create_key)
            
        elif args.encrypt:
            encryptor = ConfigEncryption(key_file=args.key_file)
            output_path = encryptor.encrypt_config_file(args.encrypt, args.output)
            print(f"✅ Successfully encrypted: {output_path}")
            
        elif args.decrypt:
            encryptor = ConfigEncryption(key_file=args.key_file)
            output_path = encryptor.decrypt_config_file(args.decrypt, args.output)
            print(f"✅ Successfully decrypted: {output_path}")
            
        else:
            parser.print_help()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_encryption_cli()