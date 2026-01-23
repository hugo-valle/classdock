"""
Git operations and repository management utilities.
"""

import subprocess
from pathlib import Path
from typing import Optional, List, Dict
from .logger import get_logger

logger = get_logger("git")


class GitManager:
    """Handle git operations and repository management."""

    def __init__(self, repo_path: Optional[Path] = None):
        self.repo_path = repo_path or Path.cwd()

    def get_repo_root(self) -> Optional[Path]:
        """Find the git repository root."""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--show-toplevel'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return Path(result.stdout.strip())
        except subprocess.CalledProcessError:
            logger.debug("Not in a git repository")
            return None

    def is_git_repo(self) -> bool:
        """Check if current directory is in a git repository."""
        return self.get_repo_root() is not None

    def get_remote_url(self, remote: str = "origin") -> Optional[str]:
        """Get the URL of a git remote."""
        try:
            result = subprocess.run(
                ['git', 'remote', 'get-url', remote],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            logger.debug(f"Remote '{remote}' not found")
            return None

    def get_current_branch(self) -> Optional[str]:
        """Get the current git branch name."""
        try:
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            logger.debug("Could not determine current branch")
            return None

    def get_status(self) -> Dict[str, List[str]]:
        """Get git status information."""
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )

            status = {
                'modified': [],
                'added': [],
                'deleted': [],
                'untracked': []
            }

            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue

                status_code = line[:2]
                filename = line[3:]

                if status_code.startswith('M'):
                    status['modified'].append(filename)
                elif status_code.startswith('A'):
                    status['added'].append(filename)
                elif status_code.startswith('D'):
                    status['deleted'].append(filename)
                elif status_code.startswith('??'):
                    status['untracked'].append(filename)

            return status

        except subprocess.CalledProcessError:
            logger.error("Failed to get git status")
            return {'modified': [], 'added': [], 'deleted': [], 'untracked': []}

    def clone_repo(self, url: str, destination: Path) -> bool:
        """Clone a repository to the specified destination."""
        try:
            subprocess.run(
                ['git', 'clone', url, str(destination)],
                check=True,
                capture_output=True
            )
            logger.info(f"Successfully cloned {url} to {destination}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to clone {url}: {e}")
            return False

    def pull_repo(self) -> bool:
        """Pull latest changes from origin."""
        try:
            subprocess.run(
                ['git', 'pull'],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
            logger.info("Successfully pulled latest changes")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to pull: {e}")
            return False
