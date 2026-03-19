"""
Configuration loader for economy flow providers
"""

import os
from pathlib import Path
from typing import Dict, Optional

GEMINI_ENV_VARS = (
    'GEMINI_DEEP_RESEARCH_API_KEY',
    'GEMINI_API_KEY',
    'GOOGLE_API_KEY',
)
ENV_FILES = (
    Path('/Users/phillip/Documents/vibe_coding_projects/.env'),
    Path('/Users/phillip/Documents/secrets/global.env'),
    Path.home() / '.api_keys',
)


def _is_placeholder(value: Optional[str]) -> bool:
    if not value:
        return True
    normalized = value.strip().lower()
    return (
        not normalized or
        normalized.startswith('your_') or
        'placeholder' in normalized
    )


def _load_from_env_files(*keys: str) -> Dict[str, str]:
    values: Dict[str, str] = {}
    remaining = set(keys)

    for env_file in ENV_FILES:
        if not env_file.exists() or not remaining:
            continue

        for raw_line in env_file.read_text().splitlines():
            line = raw_line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key in remaining and not _is_placeholder(value):
                values[key] = value
                remaining.remove(key)

    return values


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
            'GEMINI_DEEP_RESEARCH_API_KEY',
            'GEMINI_API_KEY',
            'GOOGLE_API_KEY',
            'OPENAI_API_KEY',
            'DEFAULT_PROVIDER',
            'REPO_PATH'
        ]
        
        for var in env_vars:
            if var in os.environ:
                config[var] = os.environ[var]

        file_values = _load_from_env_files(*env_vars)
        for key, value in file_values.items():
            config.setdefault(key, value)
        
        return config
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a configuration value."""
        return self.config.get(key, default)
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for a specific provider."""
        key_mapping = {
            'claude': 'ANTHROPIC_API_KEY',
            'gemini': GEMINI_ENV_VARS,
            'openai': 'OPENAI_API_KEY'
        }
        
        api_key_var = key_mapping.get(provider.lower())
        if isinstance(api_key_var, tuple):
            for candidate in api_key_var:
                api_key = self.get(candidate)
                if not _is_placeholder(api_key):
                    return api_key
        elif api_key_var:
            api_key = self.get(api_key_var)
            if not _is_placeholder(api_key):
                return api_key
        
        return None
    
    def validate_provider(self, provider: str) -> bool:
        """Check if a provider has valid configuration."""
        api_key = self.get_api_key(provider)
        return api_key is not None and len(api_key) > 0
