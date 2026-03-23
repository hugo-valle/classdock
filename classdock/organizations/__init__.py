"""
Organizations module for ClassDock.

Provides GitHub organization lifecycle management including:
- Organization creation and listing
- Template repository cloning between organizations
- Local workspace folder management (master folder + semester org folder)
- Interactive setup wizard
- Naming convention validation
"""

from .models import (
    CloneResult,
    Organization,
    SetupResult,
    TemplateRepo,
    WorkspaceFolder,
)
from .validators import OrgNameValidator, ValidationResult

__all__ = [
    "Organization",
    "TemplateRepo",
    "WorkspaceFolder",
    "CloneResult",
    "SetupResult",
    "OrgNameValidator",
    "ValidationResult",
]
