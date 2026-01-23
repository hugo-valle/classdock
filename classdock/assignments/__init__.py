"""
Assignment orchestration and management for ClassDock.

This package handles assignment lifecycle operations including setup, orchestration, and management.
"""

from .orchestrator import AssignmentOrchestrator
from .setup import AssignmentSetup
from .manage import AssignmentManager

__all__ = ['AssignmentOrchestrator', 'AssignmentSetup', 'AssignmentManager']
