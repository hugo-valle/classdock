"""
Global configuration manager for ClassDock.

This module provides centralized configuration management by parsing assignment.conf
once and making all configuration variables globally available to all commands.
"""

from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass

from ..utils import logger


@dataclass
class SecretsConfig:
    """Configuration for a single secret."""
    name: str
    description: str
    # Optional - if None, uses centralized token
    token_file: Optional[str] = None
    max_age_days: int = 90
    validate_format: bool = True

    def uses_centralized_token(self) -> bool:
        """Check if this secret should use the centralized token system."""
        return self.token_file is None or self.token_file.strip() == ""


@dataclass
class GlobalConfig:
    """Global configuration container for all ClassDock settings."""

    # Assignment Information
    classroom_url: Optional[str] = None
    classroom_repo_url: Optional[str] = None
    template_repo_url: Optional[str] = None
    github_organization: Optional[str] = None
    assignment_name: Optional[str] = None
    assignment_file: Optional[str] = None  # For backward compatibility
    # New: supports files, patterns, and folders
    student_files: List[str] = None

    # Secret Management
    secrets_config: List[SecretsConfig] = None
    instructor_token_file: str = "instructor_token.txt"

    # Workflow Configuration
    step_sync_template: bool = True
    step_discover_repos: bool = True
    step_manage_secrets: bool = True
    step_assist_students: bool = False

    # Advanced Configuration
    output_dir: str = "tools/generated"
    exclude_instructor_repos: bool = True
    include_template_repo: bool = False
    default_dry_run: bool = False
    log_level: str = "INFO"
    skip_confirmations: bool = False

    # Raw configuration dictionary for backward compatibility
    raw_config: Dict[str, str] = None

    def __post_init__(self):
        if self.secrets_config is None:
            self.secrets_config = []
        if self.raw_config is None:
            self.raw_config = {}
        if self.student_files is None:
            self.student_files = []

    def get_student_files(self) -> List[str]:
        """
        Get all student files to protect during template updates.

        Returns:
            List of file patterns, file paths, and folder paths to protect.
            Supports backward compatibility with assignment_file.
        """
        files = []

        # Add files from new student_files configuration
        if self.student_files:
            files.extend(self.student_files)

        # Add legacy assignment_file for backward compatibility
        elif self.assignment_file and self.assignment_file not in files:
            files.append(self.assignment_file)

        # Default fallback
        if not files:
            files = ["assignment.ipynb"]

        return files


class ConfigurationManager:
    """Manages global configuration for ClassDock."""

    def __init__(self):
        self._config: Optional[GlobalConfig] = None
        self._config_file_path: Optional[Path] = None

    def load_config(self, config_file: Optional[str] = None, assignment_root: Optional[Path] = None) -> GlobalConfig:
        """
        Load configuration from assignment.conf file.

        Args:
            config_file: Configuration file name (default: assignment.conf)
            assignment_root: Root directory to look for config file

        Returns:
            GlobalConfig instance with parsed configuration
        """
        if config_file is None:
            config_file = "assignment.conf"

        # Determine config file path
        if assignment_root:
            config_path = assignment_root / config_file
        else:
            config_path = Path.cwd() / config_file

        if not config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}")

        self._config_file_path = config_path
        logger.info(f"Loading configuration from: {config_path}")

        # Parse the configuration file
        raw_config = self._parse_config_file(config_path)

        # Create GlobalConfig instance
        self._config = self._create_global_config(raw_config)

        logger.info("✅ Configuration loaded successfully")
        return self._config

    def _parse_config_file(self, config_path: Path) -> Dict[str, str]:
        """Parse bash-style configuration file."""
        config = {}

        with open(config_path, 'r') as f:
            content = f.read()

        # Remove comments and empty lines
        in_multiline = False
        multiline_content = []
        multiline_key = None

        for line in content.split('\n'):
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue

            # Handle multiline values (like SECRETS_CONFIG)
            if '="' in line and line.count('"') == 1:
                # Start of multiline
                key, value = line.split('="', 1)
                in_multiline = True
                multiline_key = key.strip()
                multiline_content = [value]
                continue
            elif in_multiline:
                if line.endswith('"'):
                    # End of multiline
                    multiline_content.append(line[:-1])
                    config[multiline_key] = '\n'.join(multiline_content)
                    in_multiline = False
                    multiline_content = []
                    multiline_key = None
                else:
                    multiline_content.append(line)
                continue

            # Handle regular key=value pairs
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()

                # Remove inline comments (handle # in values)
                if '#' in value:
                    # Only remove comments if they're not inside quotes
                    if (value.startswith('"') and value.count('"') >= 2) or \
                       (value.startswith("'") and value.count("'") >= 2):
                        # Value is quoted, don't remove # inside quotes
                        pass
                    else:
                        # Remove inline comment
                        value = value.split('#')[0].strip()

                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]

                config[key] = value

        return config

    def _create_global_config(self, raw_config: Dict[str, str]) -> GlobalConfig:
        """Create GlobalConfig instance from raw configuration dictionary."""

        # Parse secrets configuration
        secrets_config = self._parse_secrets_config(
            raw_config.get("SECRETS_CONFIG", ""))

        # Debug logging for boolean parsing
        step_manage_secrets_raw = raw_config.get("STEP_MANAGE_SECRETS", "true")
        step_manage_secrets_parsed = step_manage_secrets_raw.lower() == "true"
        logger.debug(
            f"STEP_MANAGE_SECRETS: raw='{step_manage_secrets_raw}' -> parsed={step_manage_secrets_parsed}")

        # Parse student files configuration (supports multiple formats)
        student_files = []

        # Check for new STUDENT_FILES configuration (comma-separated)
        if raw_config.get("STUDENT_FILES"):
            student_files = [
                f.strip() for f in raw_config["STUDENT_FILES"].split(",") if f.strip()]

        # Check for legacy ASSIGNMENT_FILE (for backward compatibility)
        elif raw_config.get("ASSIGNMENT_FILE"):
            student_files = [raw_config["ASSIGNMENT_FILE"]]

        # Default fallback
        if not student_files:
            student_files = ["assignment.ipynb"]

        config = GlobalConfig(
            # Assignment Information
            classroom_url=raw_config.get("CLASSROOM_URL"),
            classroom_repo_url=raw_config.get("CLASSROOM_REPO_URL"),
            template_repo_url=raw_config.get("TEMPLATE_REPO_URL"),
            github_organization=raw_config.get("GITHUB_ORGANIZATION"),
            assignment_name=raw_config.get("ASSIGNMENT_NAME"),
            assignment_file=raw_config.get("ASSIGNMENT_FILE"),
            student_files=student_files,

            # Secret Management
            secrets_config=secrets_config,
            instructor_token_file=raw_config.get(
                "INSTRUCTOR_TOKEN_FILE", "instructor_token.txt"),

            # Workflow Configuration
            step_sync_template=raw_config.get(
                "STEP_SYNC_TEMPLATE", "true").lower() == "true",
            step_discover_repos=raw_config.get(
                "STEP_DISCOVER_REPOS", "true").lower() == "true",
            step_manage_secrets=step_manage_secrets_parsed,
            step_assist_students=raw_config.get(
                "STEP_ASSIST_STUDENTS", "false").lower() == "true",

            # Advanced Configuration
            output_dir=raw_config.get("OUTPUT_DIR", "tools/generated"),
            exclude_instructor_repos=raw_config.get(
                "EXCLUDE_INSTRUCTOR_REPOS", "true").lower() == "true",
            include_template_repo=raw_config.get(
                "INCLUDE_TEMPLATE_REPO", "false").lower() == "true",
            default_dry_run=raw_config.get(
                "DEFAULT_DRY_RUN", "false").lower() == "true",
            log_level=raw_config.get("LOG_LEVEL", "INFO"),
            skip_confirmations=raw_config.get(
                "SKIP_CONFIRMATIONS", "false").lower() == "true",

            # Raw configuration for backward compatibility
            raw_config=raw_config
        )

        return config

    def _parse_secrets_config(self, secrets_config_str: str) -> List[SecretsConfig]:
        """Parse SECRETS_CONFIG string into SecretsConfig objects.

        See ConfigurationManager._parse_secrets_config in project docs for supported
        formats. The parser accepts the new simplified 3-field format as well
        as legacy file-backed formats for backward compatibility.

        Args:
            secrets_config_str: Multiline string from the SECRETS_CONFIG value.

        Returns:
            List[SecretsConfig]: Parsed secrets configuration objects.
        """

        secrets: List[SecretsConfig] = []

        if not secrets_config_str.strip():
            return secrets

        # Split by lines and process each secret configuration
        lines = [line.strip()
                 for line in secrets_config_str.split('\n') if line.strip()]

        for line in lines:
            if ':' not in line:
                continue

            parts = line.split(':')
            if len(parts) >= 2:
                name = parts[0].strip()
                description = parts[1].strip() if len(parts) > 1 else ""

                # Determine format based on number of parts and content
                if len(parts) == 3:
                    third_part = parts[2].strip()
                    if third_part.lower() in ('true', 'false'):
                        # New simplified format: name:description:validate_format
                        secret = SecretsConfig(
                            name=name,
                            description=description,
                            token_file=None,
                            max_age_days=90,
                            validate_format=third_part.lower() == 'true'
                        )
                    else:
                        # Legacy: name:description:token_file
                        secret = SecretsConfig(
                            name=name,
                            description=description,
                            token_file=third_part,
                            max_age_days=90,
                            validate_format=True
                        )
                elif len(parts) == 4:
                    third_part = parts[2].strip()
                    fourth_part = parts[3].strip()

                    if fourth_part.lower() in ('true', 'false') and third_part.isdigit():
                        # New: name:description:max_age_days:validate_format
                        secret = SecretsConfig(
                            name=name,
                            description=description,
                            token_file=None,
                            max_age_days=int(third_part),
                            validate_format=fourth_part.lower() == 'true'
                        )
                    else:
                        # Legacy: name:description:token_file:max_age_days
                        secret = SecretsConfig(
                            name=name,
                            description=description,
                            token_file=third_part,
                            max_age_days=int(
                                fourth_part) if fourth_part.isdigit() else 90,
                            validate_format=True
                        )
                elif len(parts) >= 5:
                    # Full legacy format: name:description:token_file:max_age_days:validate_format
                    token_file = parts[2].strip() if parts[2].strip() else None
                    max_age = int(parts[3]) if len(
                        parts) > 3 and parts[3].strip().isdigit() else 90
                    validate_flag = parts[4].strip().lower(
                    ) == 'true' if len(parts) > 4 else True
                    secret = SecretsConfig(
                        name=name,
                        description=description,
                        token_file=token_file,
                        max_age_days=max_age,
                        validate_format=validate_flag
                    )
                else:
                    # Minimal: name:description
                    secret = SecretsConfig(
                        name=name,
                        description=description,
                        token_file=None,
                        max_age_days=90,
                        validate_format=True
                    )

                secrets.append(secret)

        return secrets

    def get_config(self) -> Optional[GlobalConfig]:
        """Get the currently loaded configuration."""
        return self._config

    def get_raw_config(self) -> Dict[str, str]:
        """Get raw configuration dictionary for backward compatibility."""
        if self._config:
            return self._config.raw_config
        return {}

    def is_loaded(self) -> bool:
        """Check if configuration is loaded."""
        return self._config is not None

    def get_config_file_path(self) -> Optional[Path]:
        """Get the path to the loaded configuration file."""
        return self._config_file_path

    def validate_config(self) -> bool:
        """Validate that required configuration is present."""
        if not self._config:
            logger.error("No configuration loaded")
            return False

        # Check required fields
        required_fields = [
            ("github_organization", "GITHUB_ORGANIZATION"),
            ("assignment_name", "ASSIGNMENT_NAME"),
        ]

        missing_fields = []
        for field_name, config_name in required_fields:
            if not getattr(self._config, field_name):
                missing_fields.append(config_name)

        if missing_fields:
            logger.error(
                f"Missing required configuration fields: {', '.join(missing_fields)}")
            return False

        return True


# Global configuration manager instance
config_manager = ConfigurationManager()


def get_global_config() -> Optional[GlobalConfig]:
    """Get the global configuration instance."""
    return config_manager.get_config()


def load_global_config(config_file: Optional[str] = None, assignment_root: Optional[Path] = None) -> GlobalConfig:
    """Load global configuration from file."""
    return config_manager.load_config(config_file, assignment_root)


def get_raw_config() -> Dict[str, str]:
    """Get raw configuration dictionary for backward compatibility."""
    return config_manager.get_raw_config()


def is_config_loaded() -> bool:
    """Check if global configuration is loaded."""
    return config_manager.is_loaded()
