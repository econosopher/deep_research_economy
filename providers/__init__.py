"""
Economy Flow Providers Package (with lazy-loading)
"""

from typing import Dict

from .base_provider import BaseEconomyProvider
from .config import Config

__all__ = [
    'BaseEconomyProvider',
    'Config',
    'get_provider',
    'PROVIDERS'
]

# Provider registry (module path strings to enable lazy import)
PROVIDERS: Dict[str, str] = {
    'claude': 'providers.claude_provider.ClaudeProvider',
    'gemini': 'providers.gemini_provider.GeminiProvider',
}

def _import_class(path: str):
    module_path, class_name = path.rsplit('.', 1)
    module = __import__(module_path, fromlist=[class_name])
    return getattr(module, class_name)

def get_provider(provider_name: str, api_key: str, **kwargs) -> BaseEconomyProvider:
    """Get a provider instance by name (lazy-load implementation).

    Args:
        provider_name: Name of the provider (claude, gemini)
        api_key: API key for the provider
        **kwargs: Additional arguments for the provider (e.g., model_name for Gemini)
    """
    key = provider_name.lower()
    if key not in PROVIDERS:
        raise ValueError(f"Unknown provider: {provider_name}. Available: {list(PROVIDERS.keys())}")

    provider_class = _import_class(PROVIDERS[key])

    # For Gemini, allow extra kwargs like model_name, depth, required_categories
    if key == 'gemini':
        return provider_class(api_key, **kwargs)
    return provider_class(api_key)
