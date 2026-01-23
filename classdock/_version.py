"""Version utility for classdock package."""

import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING or sys.version_info >= (3, 8):
    from importlib import metadata
else:
    import importlib_metadata as metadata


def get_version() -> str:
    """
    Get the version from the installed package metadata.

    If the package is not installed (development mode), 
    falls back to reading from pyproject.toml.

    Returns:
        str: The version string
    """
    try:
        # Try to get version from installed package metadata
        return metadata.version("classdock")
    except metadata.PackageNotFoundError:
        # Fallback: read from pyproject.toml for development
        return _read_version_from_pyproject()


def _read_version_from_pyproject() -> str:
    """Read version directly from pyproject.toml file."""
    try:
        # Find pyproject.toml file
        current_dir = Path(__file__).parent
        pyproject_path = current_dir.parent / "pyproject.toml"

        if not pyproject_path.exists():
            return "0.0.0.dev"

        # Read and parse pyproject.toml
        with open(pyproject_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Simple regex to extract version (avoiding external dependencies)
        import re
        match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
        if match:
            return f"{match.group(1)}.dev"
        else:
            return "0.0.0.dev"

    except Exception:
        return "0.0.0.dev"
