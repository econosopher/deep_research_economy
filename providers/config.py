"""
Configuration loader for economy flow providers
"""

import os
from pathlib import Path
from typing import Dict, Optional


class Config:
    """Load and manage configuration for economy flow providers."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration from file or environment."""
        self.config_path = config_path or os.path.expanduser("~/.economy_flow_config")
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, str]:
        """Load configuration from file and environment variables."""
        config = {}
        
        # First, try to load from config file
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
        
        # Override with environment variables if they exist
        env_vars = [
            'ANTHROPIC_API_KEY',
            'GOOGLE_API_KEY',
            'OPENAI_API_KEY',
            'DEFAULT_PROVIDER',
            'REPO_PATH'
        ]
        
        for var in env_vars:
            if var in os.environ:
                config[var] = os.environ[var]
        
        return config
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a configuration value."""
        return self.config.get(key, default)
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for a specific provider."""
        key_mapping = {
            'claude': 'ANTHROPIC_API_KEY',
            'gemini': 'GOOGLE_API_KEY',
            'openai': 'OPENAI_API_KEY'
        }
        
        api_key_var = key_mapping.get(provider.lower())
        if api_key_var:
            api_key = self.get(api_key_var)
            if api_key and api_key != f"your_{provider}_api_key_here":
                return api_key
        
        return None
    
    def validate_provider(self, provider: str) -> bool:
        """Check if a provider has valid configuration."""
        api_key = self.get_api_key(provider)
        return api_key is not None and len(api_key) > 0