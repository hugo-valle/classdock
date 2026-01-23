"""
Workspace paths and configuration discovery utilities.
"""

from pathlib import Path
from typing import Optional, List
from .logger import get_logger

logger = get_logger("paths")


class PathManager:
    """Manage workspace paths and configuration discovery."""

    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path or Path.cwd()

    def find_config_file(self, filename: str = "assignment.conf") -> Optional[Path]:
        """
        Find configuration file by searching up the directory tree.

        Args:
            filename: Configuration filename to search for

        Returns:
            Path to config file if found, None otherwise
        """
        current = self.base_path.resolve()

        while current != current.parent:
            config_path = current / filename
            if config_path.exists():
                logger.debug(f"Found config file: {config_path}")
                return config_path
            current = current.parent

        logger.debug(f"Config file '{filename}' not found")
        return None

    def get_workspace_root(self) -> Path:
        """
        Get the workspace root directory.

        Looks for indicators like .git, pyproject.toml, or assignment.conf
        """
        current = self.base_path.resolve()

        while current != current.parent:
            # Check for common workspace indicators
            indicators = ['.git', 'pyproject.toml',
                          'assignment.conf', '.gitignore']

            if any((current / indicator).exists() for indicator in indicators):
                logger.debug(f"Found workspace root: {current}")
                return current

            current = current.parent

        # Fallback to current directory
        logger.debug(
            f"Using current directory as workspace root: {self.base_path}")
        return self.base_path

    def ensure_output_directory(self, output_dir: str = "tools/generated") -> Path:
        """
        Ensure output directory exists and return its path.

        Args:
            output_dir: Relative path to output directory

        Returns:
            Path to output directory
        """
        workspace_root = self.get_workspace_root()
        output_path = workspace_root / output_dir

        output_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Output directory: {output_path}")

        return output_path

    def get_script_directory(self) -> Path:
        """Get the directory containing classdock scripts."""
        # Find the classdock package directory
        current = Path(__file__).parent
        while current.name != "classdock" and current != current.parent:
            current = current.parent

        return current / "scripts"

    def list_assignment_files(self, extensions: Optional[List[str]] = None) -> List[Path]:
        """
        List potential assignment files in the workspace.

        Args:
            extensions: List of file extensions to search for

        Returns:
            List of paths to potential assignment files
        """
        if extensions is None:
            extensions = ['.ipynb', '.py', '.cpp', '.java',
                          '.sql', '.md', '.html', '.js', '.ts']

        workspace_root = self.get_workspace_root()
        assignment_files = []

        for ext in extensions:
            assignment_files.extend(workspace_root.glob(f"**/*{ext}"))

        # Filter out common non-assignment directories
        exclude_patterns = ['.git', '__pycache__',
                            'node_modules', '.venv', 'venv']

        filtered_files = []
        for file_path in assignment_files:
            if not any(pattern in str(file_path) for pattern in exclude_patterns):
                filtered_files.append(file_path)

        logger.debug(f"Found {len(filtered_files)} potential assignment files")
        return filtered_files

    def get_relative_path(self, file_path: Path) -> str:
        """Get relative path from workspace root."""
        workspace_root = self.get_workspace_root()
        try:
            return str(file_path.relative_to(workspace_root))
        except ValueError:
            # If file is not under workspace root, return absolute path
            return str(file_path.resolve())
