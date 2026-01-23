"""
Configuration validation for ClassDock.

This module provides validation for configuration values and settings.
"""

import re
from typing import Dict, Any, List, Tuple
from ..utils import get_logger

logger = get_logger("config.validator")


class ConfigValidator:
    """Validate configuration values and settings."""

    @staticmethod
    def validate_github_url(url: str) -> Tuple[bool, str]:
        """
        Validate GitHub URL format.

        Args:
            url: URL to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not url:
            return False, "URL cannot be empty"

        github_pattern = r'^https://github\.com/.+/.+$'
        classroom_pattern = r'^https://classroom\.github\.com/classrooms/.+/assignments/.+$'

        if re.match(github_pattern, url) or re.match(classroom_pattern, url):
            return True, ""
        else:
            return False, "Must be a valid GitHub or GitHub Classroom URL"

    @staticmethod
    def validate_organization(org: str) -> Tuple[bool, str]:
        """
        Validate GitHub organization name.

        Args:
            org: Organization name to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not org:
            return False, "Organization name cannot be empty"

        if re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$', org):
            return True, ""
        else:
            return False, "Organization name must contain only letters, numbers, and hyphens"

    @staticmethod
    def validate_assignment_name(name: str) -> Tuple[bool, str]:
        """
        Validate assignment name.

        Args:
            name: Assignment name to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not name:
            return True, ""  # Allow empty assignment names

        if re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9_-]*[a-zA-Z0-9])?$', name):
            return True, ""
        else:
            return False, "Assignment name must contain only letters, numbers, hyphens, and underscores"

    @staticmethod
    def validate_file_path(file_path: str) -> Tuple[bool, str]:
        """
        Validate file path has proper extension.

        Args:
            file_path: File path to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not file_path:
            return False, "File path cannot be empty"

        valid_extensions = {'.ipynb', '.py', '.cpp', '.sql', '.md', 'asm',
                            '.html', '.js', '.ts', '.java', '.c', '.h', '.hpp', '.txt'}

        if any(file_path.endswith(ext) for ext in valid_extensions):
            return True, ""
        else:
            return False, f"File must have a valid extension: {', '.join(sorted(valid_extensions))}"

    @staticmethod
    def validate_student_files(student_files: str) -> Tuple[bool, str]:
        """
        Validate student files configuration (supports comma-separated files, patterns, and folders).

        Args:
            student_files: Comma-separated list of files, patterns, or folders to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not student_files:
            return False, "Student files cannot be empty"

        # Split by comma and validate each entry
        file_entries = [entry.strip()
                        for entry in student_files.split(',') if entry.strip()]

        if not file_entries:
            return False, "At least one file, pattern, or folder must be specified"

        valid_extensions = {'.ipynb', '.py', '.cpp', '.sql', '.md', '.asm',
                            '.html', '.js', '.ts', '.java', '.c', '.h', '.hpp', '.txt', '.csv', '.json'}

        for entry in file_entries:
            # Check for folders (ending with /)
            if entry.endswith('/'):
                if len(entry) < 2:
                    return False, f"Folder path '{entry}' is too short"
                continue

            # Check for glob patterns (containing wildcards)
            if '*' in entry or '?' in entry or '[' in entry:
                # Basic validation for glob patterns
                if entry.startswith('**/') or entry.endswith('/**'):
                    continue  # Valid recursive patterns
                if any(char in entry for char in ['*', '?']):
                    continue  # Valid glob patterns

            # Check regular files
            if not any(entry.endswith(ext) for ext in valid_extensions):
                return False, f"File '{entry}' must have a valid extension: {', '.join(sorted(valid_extensions))}"

        return True, ""

    @staticmethod
    def validate_required_fields(config: Dict[str, Any]) -> List[str]:
        """
        Validate that all required configuration fields are present.

        Args:
            config: Configuration dictionary to validate

        Returns:
            List of missing required fields
        """
        required_fields = [
            'CLASSROOM_URL',
            'TEMPLATE_REPO_URL',
            'GITHUB_ORGANIZATION'
        ]

        missing_fields = []
        for field in required_fields:
            if field not in config or not config[field]:
                missing_fields.append(field)

        # Check for STUDENT_FILES or ASSIGNMENT_FILE (backward compatibility)
        if not config.get('STUDENT_FILES') and not config.get('ASSIGNMENT_FILE'):
            missing_fields.append('STUDENT_FILES or ASSIGNMENT_FILE')

        return missing_fields

    @staticmethod
    def validate_full_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Perform full configuration validation.

        Args:
            config: Configuration dictionary to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Check required fields
        missing = ConfigValidator.validate_required_fields(config)
        if missing:
            errors.extend(
                [f"Missing required field: {field}" for field in missing])

        # Validate specific fields if present
        if config.get('CLASSROOM_URL'):
            valid, error = ConfigValidator.validate_github_url(
                config['CLASSROOM_URL'])
            if not valid:
                errors.append(f"CLASSROOM_URL: {error}")

        if config.get('TEMPLATE_REPO_URL'):
            valid, error = ConfigValidator.validate_github_url(
                config['TEMPLATE_REPO_URL'])
            if not valid:
                errors.append(f"TEMPLATE_REPO_URL: {error}")

        if config.get('GITHUB_ORGANIZATION'):
            valid, error = ConfigValidator.validate_organization(
                config['GITHUB_ORGANIZATION'])
            if not valid:
                errors.append(f"GITHUB_ORGANIZATION: {error}")

        if config.get('ASSIGNMENT_NAME'):
            valid, error = ConfigValidator.validate_assignment_name(
                config['ASSIGNMENT_NAME'])
            if not valid:
                errors.append(f"ASSIGNMENT_NAME: {error}")

        # Validate new STUDENT_FILES configuration (preferred)
        if config.get('STUDENT_FILES'):
            valid, error = ConfigValidator.validate_student_files(
                config['STUDENT_FILES'])
            if not valid:
                errors.append(f"STUDENT_FILES: {error}")

        # Validate legacy ASSIGNMENT_FILE for backward compatibility
        elif config.get('ASSIGNMENT_FILE'):
            valid, error = ConfigValidator.validate_file_path(
                config['ASSIGNMENT_FILE'])
            if not valid:
                errors.append(f"ASSIGNMENT_FILE: {error}")

        return len(errors) == 0, errors

    def validate_config_file(self, config_path) -> Tuple[bool, List[str]]:
        """
        Validate a configuration file.

        Args:
            config_path: Path to configuration file (Path object or string)

        Returns:
            Tuple of (is_valid: bool, errors: List[str])
        """
        from .loader import ConfigLoader
        from pathlib import Path

        try:
            # Convert to Path object if needed
            path = Path(config_path) if not isinstance(
                config_path, Path) else config_path

            # Check if file exists before loading
            if not path.exists():
                return False, [f"Configuration file not found: {path}"]

            # Load configuration from file with explicit path
            loader = ConfigLoader(config_path=path)
            config_dict = loader.load()

            # Validate the loaded configuration
            return self.validate_full_config(config_dict)

        except Exception as e:
            return False, [f"Failed to load configuration file: {e}"]
