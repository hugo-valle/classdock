"""
Enhanced logging setup using rich for better CLI output.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

try:
    from rich.logging import RichHandler
    from rich.console import Console
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Global logger instance
logger = logging.getLogger("classdock")


def setup_logging(verbose: bool = False, log_file: Optional[Path] = None) -> None:
    """
    Set up enhanced logging with rich output.

    Args:
        verbose: Enable verbose (DEBUG) logging
        log_file: Optional log file path
    """
    # Set logging level
    level = logging.DEBUG if verbose else logging.INFO

    # Clear any existing handlers
    logger.handlers.clear()
    logger.setLevel(level)

    # Configure rich handler if available
    if RICH_AVAILABLE:
        console = Console(stderr=True)
        handler = RichHandler(
            console=console,
            show_path=verbose,
            show_time=verbose,
            rich_tracebacks=True,
            markup=True
        )
        formatter = logging.Formatter(
            fmt="%(message)s",
            datefmt="[%X]"
        )
    else:
        # Fallback to standard handler
        handler = logging.StreamHandler(sys.stderr)
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    handler.setFormatter(formatter)
    handler.setLevel(level)
    logger.addHandler(handler)

    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)  # Always debug to file
        logger.addHandler(file_handler)

    # Set level for root logger to prevent duplicate messages
    logging.getLogger().setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module."""
    return logging.getLogger(f"classdock.{name}")
