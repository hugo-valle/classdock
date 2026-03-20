"""
ClassDock - Python CLI Package

A comprehensive automation suite for managing Classroom assignments
with advanced workflow orchestration, repository discovery, and secret management capabilities.
"""

from ._version import get_version

__version__ = get_version()
__author__ = "Hugo Valle"
__description__ = "ClassDock - Comprehensive automation suite for managing assignments"

from .bash_wrapper import BashWrapper
from .config import ConfigLoader, ConfigValidator
from .services.assignment_service import AssignmentService
from .services.automation_service import AutomationService
from .services.repos_service import ReposService
from .services.secrets_service import SecretsService
from .utils import get_logger, setup_logging

__all__ = [
    "ConfigLoader",
    "ConfigValidator",
    "setup_logging",
    "get_logger",
    "BashWrapper",
    "AssignmentService",
    "ReposService",
    "SecretsService",
    "AutomationService",
    "__version__",
]
