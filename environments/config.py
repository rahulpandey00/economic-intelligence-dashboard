"""
Environment configuration for the Economic Dashboard.
Determines the current environment and provides environment-specific settings.
"""

import os
from functools import lru_cache
from typing import Dict, Any

# Environment names
ENV_DEVELOPMENT = 'development'
ENV_PRODUCTION = 'production'

# Default environment
DEFAULT_ENV = ENV_DEVELOPMENT


def get_environment() -> str:
    """
    Get the current environment name.
    
    Set via DASHBOARD_ENV environment variable.
    Valid values: 'development', 'production'
    Defaults to 'development' if not set.
    """
    env = os.getenv('DASHBOARD_ENV', DEFAULT_ENV).lower()
    if env in ['prod', 'production']:
        return ENV_PRODUCTION
    elif env in ['dev', 'development']:
        return ENV_DEVELOPMENT
    else:
        # Default to development for unknown values
        return ENV_DEVELOPMENT


def is_production() -> bool:
    """Check if running in production environment."""
    return get_environment() == ENV_PRODUCTION


def is_development() -> bool:
    """Check if running in development environment."""
    return get_environment() == ENV_DEVELOPMENT


# Cache configurations by environment name to avoid rebuilding dictionaries
@lru_cache(maxsize=2)
def _build_config(env_name: str) -> Dict[str, Any]:
    """Build and cache configuration for the specified environment."""
    if env_name == ENV_PRODUCTION:
        return {
            'env_name': ENV_PRODUCTION,
            'debug': False,
            'log_level': 'WARNING',
            'cache_expiry_hours': 24,
            'rate_limit_delay': 0.5,
            'show_debug_info': False,
            'enable_experimental_features': False,
            'api_timeout_seconds': 30,
            'max_retries': 3,
            'data_refresh_interval_hours': 24,
        }
    else:  # development
        return {
            'env_name': ENV_DEVELOPMENT,
            'debug': True,
            'log_level': 'DEBUG',
            'cache_expiry_hours': 1,  # Shorter cache for development
            'rate_limit_delay': 0.1,  # Faster for development
            'show_debug_info': True,
            'enable_experimental_features': True,
            'api_timeout_seconds': 60,  # Longer timeout for debugging
            'max_retries': 1,
            'data_refresh_interval_hours': 1,
        }


def get_env_config() -> Dict[str, Any]:
    """
    Get environment-specific configuration.
    
    Returns a dictionary with settings appropriate for the current environment.
    Configuration is cached per environment for performance.
    """
    return _build_config(get_environment())


def get_config_value(key: str, default: Any = None) -> Any:
    """
    Get a specific configuration value for the current environment.
    
    Args:
        key: Configuration key to retrieve
        default: Default value if key is not found
    
    Returns:
        The configuration value or default
    """
    return get_env_config().get(key, default)
