"""
Economy Flow Providers Package
"""

from .base_provider import BaseEconomyProvider
from .claude_provider import ClaudeProvider
from .gemini_provider import GeminiProvider
from .config import Config

__all__ = [
    'BaseEconomyProvider',
    'ClaudeProvider', 
    'GeminiProvider',
    'Config'
]

# Provider registry
PROVIDERS = {
    'claude': ClaudeProvider,
    'gemini': GeminiProvider,
}

def get_provider(provider_name: str, api_key: str, **kwargs) -> BaseEconomyProvider:
    """Get a provider instance by name.
    
    Args:
        provider_name: Name of the provider (claude, gemini)
        api_key: API key for the provider
        **kwargs: Additional arguments for the provider (e.g., model_name for Gemini)
    """
    provider_class = PROVIDERS.get(provider_name.lower())
    if not provider_class:
        raise ValueError(f"Unknown provider: {provider_name}. Available: {list(PROVIDERS.keys())}")
    
    # Pass additional kwargs to providers that support them
    if provider_name.lower() == 'gemini' and 'model_name' in kwargs:
        return provider_class(api_key, model_name=kwargs['model_name'])
    
    return provider_class(api_key)