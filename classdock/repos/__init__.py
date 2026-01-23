"""
Repository operations and management package.

This package handles all repository-related operations including:
- Student repository discovery and fetching
- Repository cloning and synchronization
- Collaborator management and permissions
- Template repository operations
"""

from .fetch import RepositoryFetcher
from .collaborator import CollaboratorManager

__all__ = ["RepositoryFetcher", "CollaboratorManager"]

__all__ = ['RepoFetcher', 'RepoUpdater', 'RepoPusher', 'CollaboratorManager']
