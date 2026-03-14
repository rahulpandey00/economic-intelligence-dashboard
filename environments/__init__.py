"""
Environment configuration module for the Economic Dashboard.
Supports development (dev) and production (prod) environments.
"""

from .config import get_environment, is_production, is_development, get_env_config
