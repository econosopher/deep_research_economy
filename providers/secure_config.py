"""
Secure configuration management with encrypted API keys
"""

import os
import json
import base64
import getpass
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Dict, Optional


class SecureConfig:
    """Secure configuration manager with encrypted API key storage."""
    
    def __init__(self, config_dir: Optional[str] = None):
        """Initialize secure configuration."""
        self.config_dir = Path(config_dir or os.path.expanduser("~/.economy_json_builder"))
        self.config_dir.mkdir(exist_ok=True)
        
        self.config_file = self.config_dir / "config.json"
        self.key_file = self.config_dir / ".key"
        self.encrypted_file = self.config_dir / ".credentials"
        
        self._encryption_key = self._get_or_create_key()
        self._fernet = Fernet(self._encryption_key)
    
    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key based on machine ID."""
        if self.key_file.exists():
            return self.key_file.read_bytes()
        
        # Generate a unique key based on machine characteristics
        machine_id = self._get_machine_id()
        
        # Derive key from machine ID
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'economy_json_builder_salt',
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(machine_id.encode()))
        
        # Save key
        self.key_file.write_bytes(key)
        self.key_file.chmod(0o600)  # Read/write for owner only
        
        return key
    
    def _get_machine_id(self) -> str:
        """Generate a machine-specific ID."""
        import platform
        import uuid
        
        # Combine various machine characteristics
        machine_info = [
            platform.node(),
            platform.system(),
            platform.machine(),
            str(uuid.getnode())  # MAC address
        ]
        
        return "-".join(machine_info)
    
    def get_api_key(self, provider: str, prompt_if_missing: bool = True) -> Optional[str]:
        """Get API key for a provider, prompting if needed."""
        # First check environment variables
        env_mapping = {
            'claude': 'ANTHROPIC_API_KEY',
            'gemini': 'GOOGLE_API_KEY',
            'openai': 'OPENAI_API_KEY'
        }
        
        env_var = env_mapping.get(provider.lower())
        if env_var and env_var in os.environ:
            return os.environ[env_var]
        
        # Check encrypted storage
        credentials = self._load_credentials()
        key_name = f"{provider.lower()}_api_key"
        
        if key_name in credentials:
            return credentials[key_name]
        
        # Prompt for key if missing and allowed
        if prompt_if_missing:
            print(f"\nNo API key found for {provider}.")
            return self.set_api_key(provider)
        
        return None
    
    def set_api_key(self, provider: str, api_key: Optional[str] = None) -> Optional[str]:
        """Set API key for a provider."""
        if api_key is None:
            # Prompt for API key
            print(f"\nSetting up {provider} API key")
            print("Your API key will be encrypted and stored locally.")
            
            if provider.lower() == 'claude':
                print("Get your API key from: https://console.anthropic.com/")
            elif provider.lower() == 'gemini':
                print("Get your API key from: https://makersuite.google.com/app/apikey")
            
            api_key = getpass.getpass(f"Enter your {provider} API key: ").strip()
            
            if not api_key:
                print("No API key provided.")
                return None
        
        # Validate key format (basic check)
        if provider.lower() == 'claude' and not api_key.startswith('sk-ant-'):
            print("Warning: Claude API keys typically start with 'sk-ant-'")
            confirm = input("Continue anyway? (y/n): ").lower()
            if confirm != 'y':
                return None
        
        # Save encrypted
        credentials = self._load_credentials()
        key_name = f"{provider.lower()}_api_key"
        credentials[key_name] = api_key
        self._save_credentials(credentials)
        
        print(f"✓ {provider} API key saved securely.")
        return api_key
    
    def remove_api_key(self, provider: str) -> bool:
        """Remove API key for a provider."""
        credentials = self._load_credentials()
        key_name = f"{provider.lower()}_api_key"
        
        if key_name in credentials:
            del credentials[key_name]
            self._save_credentials(credentials)
            print(f"✓ {provider} API key removed.")
            return True
        
        print(f"No {provider} API key found.")
        return False
    
    def list_providers(self) -> Dict[str, bool]:
        """List all providers and whether they have API keys configured."""
        credentials = self._load_credentials()
        providers = ['claude', 'gemini', 'openai']
        
        result = {}
        for provider in providers:
            key_name = f"{provider}_api_key"
            env_var = f"{provider.upper()}_API_KEY"
            if provider == 'claude':
                env_var = 'ANTHROPIC_API_KEY'
            
            has_key = (
                key_name in credentials or
                env_var in os.environ
            )
            result[provider] = has_key
        
        return result
    
    def _load_credentials(self) -> Dict[str, str]:
        """Load and decrypt credentials."""
        if not self.encrypted_file.exists():
            return {}
        
        try:
            encrypted_data = self.encrypted_file.read_bytes()
            decrypted_data = self._fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            print(f"Warning: Could not load credentials: {e}")
            return {}
    
    def _save_credentials(self, credentials: Dict[str, str]) -> None:
        """Encrypt and save credentials."""
        data = json.dumps(credentials).encode()
        encrypted_data = self._fernet.encrypt(data)
        
        self.encrypted_file.write_bytes(encrypted_data)
        self.encrypted_file.chmod(0o600)  # Read/write for owner only
    
    def get_config(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get non-sensitive configuration value."""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                return config.get(key, default)
        return default
    
    def set_config(self, key: str, value: str) -> None:
        """Set non-sensitive configuration value."""
        config = {}
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                config = json.load(f)
        
        config[key] = value
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def export_config_template(self, path: str) -> None:
        """Export a template configuration file for sharing."""
        template = {
            "DEFAULT_PROVIDER": self.get_config("DEFAULT_PROVIDER", "claude"),
            "REPO_PATH": self.get_config("REPO_PATH", "/path/to/economy-flow-plugin"),
            "_comment": "API keys should be set using 'economy_json_builder --setup' command"
        }
        
        with open(path, 'w') as f:
            json.dump(template, f, indent=2)
        
        print(f"Configuration template exported to: {path}")


# Convenience functions for backward compatibility
class Config:
    """Legacy config wrapper for compatibility."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.secure_config = SecureConfig()
        
        # Migrate from old config if it exists
        self._migrate_old_config(config_path)
    
    def _migrate_old_config(self, old_config_path: Optional[str] = None):
        """Migrate from old plain text config to secure storage."""
        old_path = Path(old_config_path or os.path.expanduser("~/.economy_json_config"))
        
        if old_path.exists():
            print("\nMigrating from old configuration format...")
            
            with open(old_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Migrate API keys
                        if key == 'ANTHROPIC_API_KEY' and value != 'your_claude_api_key_here':
                            self.secure_config.set_api_key('claude', value)
                        elif key == 'GOOGLE_API_KEY' and value != 'your_gemini_api_key_here':
                            self.secure_config.set_api_key('gemini', value)
                        elif key == 'OPENAI_API_KEY' and value != 'your_openai_api_key_here':
                            self.secure_config.set_api_key('openai', value)
                        # Migrate other settings
                        elif key in ['DEFAULT_PROVIDER', 'REPO_PATH']:
                            self.secure_config.set_config(key, value)
            
            # Rename old config to backup
            backup_path = old_path.with_suffix('.backup')
            old_path.rename(backup_path)
            print(f"✓ Old configuration backed up to: {backup_path}")
            print("✓ Migration complete. API keys are now encrypted.")
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get configuration value."""
        return self.secure_config.get_config(key, default)
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for a provider."""
        return self.secure_config.get_api_key(provider, prompt_if_missing=False)
    
    def validate_provider(self, provider: str) -> bool:
        """Check if a provider has valid configuration."""
        api_key = self.get_api_key(provider)
        return api_key is not None and len(api_key) > 0