"""
Roster management module for ClassDock.

This module provides SQLite-based roster management capabilities including:
- Student enrollment tracking
- Assignment management
- GitHub username linking
- CSV import/export
- Repository synchronization
"""

from .models import Student, Assignment, StudentAssignment
from .manager import RosterManager
from .importer import RosterImporter

__all__ = [
    'Student',
    'Assignment',
    'StudentAssignment',
    'RosterManager',
    'RosterImporter',
]
