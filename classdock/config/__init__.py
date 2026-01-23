"""
Configuration and environment management for ClassDock.

This package handles configuration loading, validation, environment setup,
and global configuration management.
"""

from .loader import ConfigLoader
from .validator import ConfigValidator
from .generator import ConfigGenerator
from .global_config import (
    GlobalConfig, SecretsConfig, ConfigurationManager,
    load_global_config, get_global_config, get_raw_config, is_config_loaded
)

__all__ = [
    'ConfigLoader', 'ConfigValidator', 'ConfigGenerator',
    'GlobalConfig', 'SecretsConfig', 'ConfigurationManager',
    'load_global_config', 'get_global_config', 'get_raw_config', 'is_config_loaded'
]
