"""
Configuration File Loader for the GitHub Classroom Setup Wizard.

This module handles the loading, parsing, and updating of assignment configuration files
in shell variable format. It provides robust parsing capabilities with error handling
and integrates with PathManager for automatic file discovery.
"""

from pathlib import Path
from typing import Dict, Any, Optional
from ..utils import get_logger, PathManager

logger = get_logger("config.loader")


class ConfigLoader:
    """
    ConfigLoader is responsible for loading and parsing configuration files for GitHub Classroom assignments.

    This class provides methods to read configuration files in shell variable format (KEY=value),
    parse their contents while handling comments and various quote styles, retrieve individual
    configuration values with default fallbacks, and update configuration files while preserving
    structure and formatting.

    The loader supports automatic file discovery through PathManager integration, graceful error
    handling for missing or malformed files, and maintains compatibility with shell-style
    configuration formats used throughout the ClassDock system.

    Args:
        config_path (Optional[Path]): The path to the configuration file to load.
                                    If None, PathManager will attempt to locate the file automatically.

    Attributes:
        path_manager (PathManager): PathManager instance for file discovery operations.
        config_path (Path): The resolved path to the configuration file.

    Methods:
        load():
            Loads and parses the configuration file, returning a dictionary of key-value pairs.

        get_value(key, default):
            Retrieves a specific configuration value with optional default fallback.

        update_config(updates):
            Updates the configuration file with new or modified key-value pairs.
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize ConfigLoader with optional configuration file path.

        Creates a new ConfigLoader instance with PathManager integration for
        automatic file discovery when no explicit path is provided. If a
        config_path is specified, it will be used directly; otherwise,
        PathManager.find_config_file() will be called to locate the
        configuration file automatically.

        Args:
            config_path (Optional[Path]): Path to the configuration file to load.
                                        If None, PathManager will attempt to locate
                                        the file automatically in the current workspace.

        Example:
            >>> # Explicit path
            >>> loader = ConfigLoader(Path("assignment.conf"))

            >>> # Automatic discovery
            >>> loader = ConfigLoader()  # Uses PathManager to find config
        """
        self.path_manager = PathManager()
        self.config_path = config_path or self.path_manager.find_config_file()

    def load(self) -> Dict[str, Any]:
        """
        Load and parse configuration from the assigned configuration file.

        Reads the configuration file in shell variable format (KEY=value) and parses
        the contents into a dictionary. Handles comments (lines starting with #),
        empty lines, quoted values (both single and double quotes), and various
        formatting styles commonly found in shell configuration files.

        The parser strips whitespace, removes surrounding quotes from values,
        and ignores malformed lines that don't contain an equals sign. Error
        handling ensures that file access issues or parsing problems return
        an empty dictionary rather than raising exceptions.

        Returns:
            Dict[str, Any]: Dictionary containing configuration key-value pairs.
                          Returns empty dictionary if file doesn't exist or
                          parsing fails.

        Raises:
            Does not raise exceptions - logs errors and returns empty dict on failure.

        Example:
            >>> loader = ConfigLoader(Path("assignment.conf"))
            >>> config = loader.load()
            >>> print(config['CLASSROOM_URL'])
            'https://classroom.github.com/assignment-id'
        """
        if not self.config_path or not self.config_path.exists():
            logger.warning("No configuration file found")
            return {}

        try:
            # Read configuration file (shell format)
            config = {}
            with open(self.config_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue

                    # Parse variable assignments
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"\'')  # Remove quotes
                        config[key] = value

            logger.info(f"Loaded configuration from {self.config_path}")
            return config

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return {}

    def get_value(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a specific configuration value with optional default fallback.

        Loads the configuration file and returns the value associated with the
        specified key. If the key is not found in the configuration, returns
        the provided default value. This method provides a convenient way to
        access individual configuration values without manually parsing the
        entire configuration dictionary.

        Args:
            key (str): The configuration key to retrieve.
            default (Any, optional): The default value to return if the key
                                   is not found. Defaults to None.

        Returns:
            Any: The configuration value associated with the key, or the default
                value if the key is not found. Return type matches the default
                value type when key is missing.

        Example:
            >>> loader = ConfigLoader()
            >>> url = loader.get_value('CLASSROOM_URL', 'https://default.example.com')
            >>> timeout = loader.get_value('TIMEOUT', 30)
        """
        config = self.load()
        return config.get(key, default)

    def update_config(self, updates: Dict[str, Any]) -> bool:
        """
        Update configuration file with new or modified key-value pairs.

        Loads the existing configuration, merges the provided updates with
        existing values, and writes the combined configuration back to the file.
        The method preserves existing configuration entries while adding new
        ones and updating existing ones with new values.

        The output format includes a header comment indicating the file was
        updated by ConfigLoader, followed by all configuration entries in
        KEY="value" format with proper quoting. This ensures compatibility
        with shell-style configuration parsing.

        Args:
            updates (Dict[str, Any]): Dictionary of key-value pairs to add or update
                                    in the configuration file. Keys will be converted
                                    to strings, and values will be quoted in the output.

        Returns:
            bool: True if the configuration file was successfully updated,
                 False if an error occurred during the update process.

        Raises:
            Does not raise exceptions - logs errors and returns False on failure.

        Example:
            >>> loader = ConfigLoader(Path("assignment.conf"))
            >>> success = loader.update_config({
            ...     'CLASSROOM_URL': 'https://classroom.github.com/new-assignment',
            ...     'TIMEOUT': '60'
            ... })
            >>> print(f"Update {'succeeded' if success else 'failed'}")
        """
        if not self.config_path:
            logger.error("No configuration file path available")
            return False

        try:
            # Load existing config
            existing_config = self.load()

            # Merge updates
            existing_config.update(updates)

            # Write back to file
            with open(self.config_path, 'w') as f:
                f.write("# GitHub Classroom Assignment Configuration\n")
                f.write("# Updated by ConfigLoader\n\n")

                for key, value in existing_config.items():
                    f.write(f'{key}="{value}"\n')

            logger.info(f"Updated configuration file: {self.config_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to update configuration: {e}")
            return False
