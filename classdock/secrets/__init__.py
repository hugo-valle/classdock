"""
Secrets and token management package.

This package handles:
- GitHub token management
- Repository secrets configuration
- Student repository secret deployment
- Token validation and rotation
"""

from .manager import SecretsManager

__all__ = ["SecretsManager"]
