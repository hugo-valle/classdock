"""
Shared utilities for ClassDock.

This package provides logging, git operations, path management, and other common utilities.
"""

from .logger import setup_logging, get_logger, logger
from .git import GitManager
from .paths import PathManager
from .ui_components import Colors, print_colored, print_error, print_success
from .input_handlers import InputHandler, Validators, URLParser
from .file_operations import FileManager

__all__ = [
    'setup_logging', 'get_logger', 'logger',
    'GitManager', 'PathManager',
    'Colors', 'print_colored', 'print_error', 'print_success',
    'InputHandler', 'Validators', 'URLParser',
    'FileManager'
]
