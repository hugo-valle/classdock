"""
Configuration management module for ClassDock.

This module handles loading and validation of configuration files, supporting 
the existing .conf format used in assignment.conf with bash-style variable 
assignments and arrays.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

from .utils import logger, validate_github_url


class Configuration:
    """
    Configuration class that validates required fields and provides 
    backward compatibility with existing bash configuration format.
    """

    def __init__(self, config_data: Optional[Dict[str, Any]] = None):
        """Initialize configuration with optional config data."""
        self.data = config_data or {}
        self._validate_configuration()

    @classmethod
    def load(cls, config_file: Optional[Path] = None) -> 'Configuration':
        """
        Load configuration from file or default location.

        Args:
            config_file: Optional path to configuration file

        Returns:
            Configuration instance

        Raises:
            FileNotFoundError: If configuration file doesn't exist
            ValueError: If configuration is invalid
        """
        if config_file is None:
            # Look for assignment.conf in current directory
            config_file = Path("assignment.conf")
            if not config_file.exists():
                # Look for assignment-example.conf as fallback
                config_file = Path("assignment-example.conf")
        else:
            # Convert string to Path if needed
            config_file = Path(config_file)

        if not config_file.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {config_file}")

        logger.debug(f"Loading configuration from: {config_file}")

        config_data = cls._parse_conf_file(config_file)
        return cls(config_data)

    @staticmethod
    def _parse_conf_file(config_file: Path) -> Dict[str, Any]:
        """
        Parse bash-style configuration file.

        Supports:
        - Variable assignments: VAR="value"
        - Array assignments: ARRAY=("item1" "item2")
        - Comments starting with #
        - Environment variable expansion
        """
        config_data = {}

        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Remove comments
        lines = []
        for line in content.split('\n'):
            # Remove inline comments but preserve URLs with # in them
            if '#' in line and not re.search(r'https?://[^\s]*#', line):
                line = line.split('#')[0]
            lines.append(line.strip())

        content = '\n'.join(lines)

        # Parse variable assignments (including multi-line arrays)
        var_pattern = r'^([A-Z_][A-Z0-9_]*)\s*=\s*(.*)$'

        i = 0
        while i < len(lines):
            line = lines[i]
            if not line or line.startswith('#'):
                i += 1
                continue

            match = re.match(var_pattern, line)
            if match:
                var_name, var_value = match.groups()

                # Check if this is the start of a multi-line array
                if var_value.strip().startswith('(') and not var_value.strip().endswith(')'):
                    # Multi-line array - collect all lines until closing )
                    array_lines = [var_value]
                    i += 1
                    while i < len(lines):
                        array_lines.append(lines[i])
                        if lines[i].strip().endswith(')'):
                            break
                        i += 1

                    # Join the array lines and parse as single array
                    var_value = ' '.join(array_lines)

                # Handle array values (both single-line and multi-line)
                array_pattern = r'^\s*\(\s*(.*?)\s*\)\s*$'
                array_match = re.match(array_pattern, var_value, re.DOTALL)
                if array_match:
                    # Parse array elements using combined regex approach
                    array_content = array_match.group(1)

                    # Combined regex to match both quoted and unquoted elements
                    # This pattern matches:
                    # - "quoted strings" with potential escapes
                    # - 'single quoted strings'
                    # - unquoted_words (no spaces, until next quote or end)
                    element_pattern = r'''
                        (?:
                            "([^"\\]*(?:\\.[^"\\]*)*)"    # Double quoted strings with escape support
                            |'([^']*)'                     # Single quoted strings
                            |([^\s"']+)                    # Unquoted words (no spaces)
                        )
                    '''

                    # Find all matches and flatten the groups
                    matches = re.findall(
                        element_pattern, array_content, re.VERBOSE)
                    elements = []

                    for match_groups in matches:
                        # Each match returns a tuple of groups, flatten to get the actual value
                        element = next(
                            (group for group in match_groups if group), '')
                        if element:
                            # Handle escape sequences in double-quoted strings
                            if match_groups[0]:  # Double quoted
                                element = element.replace(
                                    '\\"', '"').replace('\\\\', '\\')
                            elements.append(element)

                    config_data[var_name] = elements
                else:
                    # Handle regular string values
                    # Remove surrounding quotes
                    var_value = var_value.strip()
                    if var_value.startswith('"') and var_value.endswith('"'):
                        var_value = var_value[1:-1]
                    elif var_value.startswith("'") and var_value.endswith("'"):
                        var_value = var_value[1:-1]

                    # Expand environment variables
                    var_value = os.path.expandvars(var_value)
                    config_data[var_name] = var_value

            i += 1

        return config_data

    def _validate_configuration(self) -> None:
        """
        Validate required configuration fields.

        Raises:
            ValueError: If required fields are missing or invalid
        """
        required_fields = [
            'CLASSROOM_URL',
            'TEMPLATE_REPO_URL',
            'GITHUB_ORGANIZATION',
        ]

        missing_fields = []
        for field in required_fields:
            if field not in self.data or not self.data[field]:
                missing_fields.append(field)

        if missing_fields:
            raise ValueError(
                f"Missing required configuration fields: {missing_fields}")

        # Validate URLs (pass config to support custom GitHub hosts)
        if not validate_github_url(self.data['CLASSROOM_URL'], config=self.data):
            raise ValueError(
                f"Invalid CLASSROOM_URL: {self.data['CLASSROOM_URL']}")

        if not validate_github_url(self.data['TEMPLATE_REPO_URL'], config=self.data):
            raise ValueError(
                f"Invalid TEMPLATE_REPO_URL: {self.data['TEMPLATE_REPO_URL']}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with optional default."""
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        self.data[key] = value

    @property
    def classroom_url(self) -> str:
        """Get classroom URL."""
        return self.data['CLASSROOM_URL']

    @property
    def template_repo_url(self) -> str:
        """Get template repository URL."""
        return self.data['TEMPLATE_REPO_URL']

    @property
    def github_organization(self) -> str:
        """Get GitHub organization."""
        return self.data['GITHUB_ORGANIZATION']

    @property
    def secrets(self) -> List[str]:
        """Get list of secrets to manage."""
        return self.data.get('SECRETS', [])

    @property
    def assignment_name(self) -> str:
        """Extract assignment name from classroom URL."""
        if hasattr(self, '_assignment_name'):
            return self._assignment_name

        # Extract from URL pattern: https://classroom.github.com/a/assignment-name
        parsed = urlparse(self.classroom_url)
        path_parts = parsed.path.strip('/').split('/')

        if len(path_parts) >= 2 and path_parts[0] == 'a':
            self._assignment_name = path_parts[1]
        else:
            # Fallback to extracting from template repo URL
            repo_parsed = urlparse(self.template_repo_url)
            repo_parts = repo_parsed.path.strip('/').split('/')
            if len(repo_parts) >= 2:
                self._assignment_name = repo_parts[1].replace('.git', '')
            else:
                self._assignment_name = 'assignment'

        return self._assignment_name

    def to_env_dict(self) -> Dict[str, str]:
        """
        Export configuration as environment variables for system compatibility.

        Returns:
            Dictionary of environment variables
        """
        env_dict = {}

        for key, value in self.data.items():
            if isinstance(value, list):
                # Convert arrays to bash array format
                env_dict[key] = ' '.join(f'"{item}"' for item in value)
            else:
                env_dict[key] = str(value)

        # Add derived values
        env_dict['ASSIGNMENT_NAME'] = self.assignment_name

        return env_dict

    def __repr__(self) -> str:
        """String representation of configuration."""
        return f"Configuration(assignment={self.assignment_name}, org={self.github_organization})"
