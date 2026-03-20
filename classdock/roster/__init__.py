"""
Roster management module for ClassDock.

This module provides SQLite-based roster management capabilities including:
- Student enrollment tracking
- Assignment management
- GitHub username linking
- CSV import/export
- Repository synchronization
"""

from .importer import RosterImporter
from .manager import RosterManager
from .models import Assignment, Student, StudentAssignment
from .sync import RosterSynchronizer

__all__ = [
    "Student",
    "Assignment",
    "StudentAssignment",
    "RosterManager",
    "RosterImporter",
    "RosterSynchronizer",
]
