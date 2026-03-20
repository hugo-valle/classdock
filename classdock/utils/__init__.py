"""
Shared utilities for ClassDock.

This package provides logging, git operations, path management, and other common utilities.
"""

from .file_operations import FileManager
from .git import GitManager
from .input_handlers import InputHandler, URLParser, Validators
from .logger import get_logger, logger, setup_logging
from .paths import PathManager
from .ui_components import Colors, print_colored, print_error, print_success

__all__ = [
    "setup_logging",
    "get_logger",
    "logger",
    "GitManager",
    "PathManager",
    "Colors",
    "print_colored",
    "print_error",
    "print_success",
    "InputHandler",
    "Validators",
    "URLParser",
    "FileManager",
]
