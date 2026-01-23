"""
Utility functions module for ClassDock.

This module provides logging utilities, URL validation, file manipulation helpers,
and other common operations used throughout the package.

Note: This module is being migrated to the utils/ package for better organization.
"""

import os
import re
from pathlib import Path
from typing import Optional, List, Union
from urllib.parse import urlparse

# Import from new utils package
from .utils.logger import get_logger

# Initialize logger
logger = get_logger("utils")


def validate_github_url(
    url: str,
    custom_hosts: Optional[Union[List[str], str]] = None,
    config: Optional[dict] = None
) -> bool:
    """
    Validate GitHub URL format with support for custom GitHub hosts.

    Args:
        url: URL to validate
        custom_hosts: Optional list of custom GitHub hosts or single host string
        config: Optional configuration dict to check for GITHUB_HOSTS

    Returns:
        True if valid GitHub URL, False otherwise

    Environment Variables:
        GITHUB_HOSTS: Comma-separated list of custom GitHub hosts
    """
    if not url:
        return False

    try:
        parsed = urlparse(url)

        # Check if it's a valid URL
        if not parsed.scheme or not parsed.netloc:
            return False

        # Build list of valid GitHub hosts
        github_patterns = [
            r'^github\.com$',
            r'^.*\.github\.com$',
            r'^classroom\.github\.com$',
        ]

        # Add custom hosts from various sources
        custom_host_sources = []

        # 1. From function parameter
        if custom_hosts:
            if isinstance(custom_hosts, str):
                custom_host_sources.extend(
                    [h.strip() for h in custom_hosts.split(',') if h.strip()])
            elif isinstance(custom_hosts, list):
                custom_host_sources.extend(
                    [h.strip() for h in custom_hosts if h and h.strip()])

        # 2. From config parameter
        if config and 'GITHUB_HOSTS' in config:
            hosts_config = config['GITHUB_HOSTS']
            if isinstance(hosts_config, str):
                custom_host_sources.extend(
                    [h.strip() for h in hosts_config.split(',') if h.strip()])
            elif isinstance(hosts_config, list):
                custom_host_sources.extend(
                    [h.strip() for h in hosts_config if h and h.strip()])

        # 3. From environment variable
        env_hosts = os.getenv('GITHUB_HOSTS')
        if env_hosts:
            custom_host_sources.extend(
                [h.strip() for h in env_hosts.split(',') if h.strip()])

        # Add custom hosts as exact patterns
        for host in custom_host_sources:
            if host:
                # Escape special regex characters and create exact match pattern
                escaped_host = re.escape(host)
                github_patterns.append(f'^{escaped_host}$')

        # Check against all patterns
        for pattern in github_patterns:
            if re.match(pattern, parsed.netloc):
                return True

        return False

    except Exception:
        return False


def validate_file_path(path: str) -> bool:
    """
    Validate file path exists and is readable.

    Args:
        path: File path to validate

    Returns:
        True if valid and readable, False otherwise
    """
    try:
        file_path = Path(path)
        return file_path.exists() and file_path.is_file()
    except Exception:
        return False


def validate_directory_path(path: str) -> bool:
    """
    Validate directory path exists and is accessible.

    Args:
        path: Directory path to validate

    Returns:
        True if valid and accessible, False otherwise
    """
    try:
        dir_path = Path(path)
        return dir_path.exists() and dir_path.is_dir()
    except Exception:
        return False


def safe_path_join(*parts: str) -> Path:
    """
    Safely join path parts preventing directory traversal.

    Args:
        *parts: Path parts to join

    Returns:
        Safe Path object
    """
    # Remove any path traversal attempts
    safe_parts = []
    for part in parts:
        # Remove dangerous path components
        clean_part = str(part).replace('..', '').replace('~', '')
        safe_parts.append(clean_part)

    return Path(*safe_parts)


def create_output_directory(base_path: str, assignment_name: str) -> Path:
    """
    Create output directory for assignment operations.

    Args:
        base_path: Base directory path
        assignment_name: Assignment name for subdirectory

    Returns:
        Created directory path

    Raises:
        OSError: If directory creation fails
    """
    output_dir = safe_path_join(base_path, assignment_name)

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Created output directory: {output_dir}")
        return output_dir
    except OSError as e:
        logger.error(f"Failed to create output directory {output_dir}: {e}")
        raise


def parse_bash_array(array_string: str) -> list:
    """
    Parse bash-style array string into Python list.

    Args:
        array_string: Bash array string like '("item1" "item2")'

    Returns:
        List of parsed items
    """
    if not array_string:
        return []

    # Remove outer parentheses
    array_string = array_string.strip()
    if array_string.startswith('(') and array_string.endswith(')'):
        array_string = array_string[1:-1]

    # Extract quoted items
    items = re.findall(r'"([^"]*)"', array_string)

    # If no quoted items found, split by whitespace
    if not items:
        items = array_string.split()

    return items


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def check_github_cli() -> bool:
    """
    Check if GitHub CLI is installed and authenticated.

    Returns:
        True if GitHub CLI is available and authenticated, False otherwise
    """
    try:
        import subprocess

        # Check if gh command exists
        result = subprocess.run(
            ['gh', '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            logger.warning("GitHub CLI (gh) is not installed")
            return False

        # Check if authenticated
        result = subprocess.run(
            ['gh', 'auth', 'status'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            logger.warning(
                "GitHub CLI is not authenticated. Run 'gh auth login'")
            return False

        logger.debug("GitHub CLI is available and authenticated")
        return True

    except subprocess.TimeoutExpired:
        logger.warning("GitHub CLI check timed out")
        return False
    except Exception as e:
        logger.warning(f"Error checking GitHub CLI: {e}")
        return False


def get_git_root() -> Optional[Path]:
    """
    Get the root directory of the current Git repository.

    Returns:
        Path to Git root directory, or None if not in a Git repository
    """
    try:
        import subprocess

        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            return Path(result.stdout.strip())
        else:
            return None

    except Exception:
        return None


def ensure_git_repository() -> bool:
    """
    Ensure current directory is a Git repository.

    Returns:
        True if in a Git repository, False otherwise
    """
    git_root = get_git_root()
    if git_root is None:
        logger.error(
            "Not in a Git repository. Please run from a Git repository.")
        return False

    logger.debug(f"Git repository root: {git_root}")
    return True


def shell_escape(arg: str) -> str:
    """
    Escape shell argument to prevent injection.

    Args:
        arg: Argument to escape

    Returns:
        Escaped argument safe for shell execution
    """
    import shlex
    return shlex.quote(str(arg))


def get_script_dir() -> Path:
    """
    Get the directory containing the current script.

    Returns:
        Path to the directory containing the script
    """
    return Path(__file__).parent


def get_repo_root() -> Path:
    """
    Get the repository root directory.

    Returns:
        Path to the repository root
    """
    # Try to get git root first
    git_root = get_git_root()
    if git_root:
        return git_root

    # Fallback: navigate up from script directory
    current = Path(__file__).parent
    while current != current.parent:
        if (current / '.git').exists() or (current / 'pyproject.toml').exists():
            return current
        current = current.parent

    # Final fallback: use parent of script directory
    return Path(__file__).parent.parent
