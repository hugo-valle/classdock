"""
Assignment orchestration and management for ClassDock.

This package handles assignment lifecycle operations including setup, orchestration, and management.
"""

from .manage import AssignmentManager
from .orchestrator import AssignmentOrchestrator
from .setup import AssignmentSetup

__all__ = ["AssignmentOrchestrator", "AssignmentSetup", "AssignmentManager"]
