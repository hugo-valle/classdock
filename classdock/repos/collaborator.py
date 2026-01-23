"""
Repository Collaborator Management for GitHub Classroom Operations.

This module handles:
- Collaborator permission management and access control for student repositories
- Repository access auditing and permission verification
- Automated collaborator cycling for permission issues resolution
- Batch collaborator operations with progress tracking and error handling
- GitHub API authentication and fallback strategies for collaborator management
"""

from pathlib import Path
from typing import List, Dict, Optional
import subprocess

# GitHub API integration with fallback handling
try:
    from github import Github, Repository, GithubException
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False

from ..utils import get_logger, GitManager
from ..utils.github_exceptions import (
    GitHubAuthenticationError, GitHubRepositoryError,
    github_api_retry, github_api_context
)
from ..config import ConfigLoader

logger = get_logger("repos.collaborator")


class CollaboratorManager:
    """
    CollaboratorManager handles comprehensive GitHub repository collaborator operations.

    This class provides methods for managing repository collaborators, handling permission
    cycles, auditing repository access, and performing batch collaborator operations
    across multiple student repositories. It supports both authenticated GitHub API
    access and fallback to command-line operations for reliability.

    Args:
        config_path (Path): Path to the assignment configuration file.
                          Defaults to "assignment.conf" in current directory.

    Attributes:
        config_loader (ConfigLoader): Configuration loader instance.
        config (dict): Loaded configuration values.
        git_manager (GitManager): Git operations manager.
        github_client (Github): GitHub API client (if authenticated).

    Methods:
        add_collaborator(repository_name, username, permission):
            Adds a collaborator to the specified repository with given permissions.

        remove_collaborator(repository_name, username):
            Removes collaborator access from the specified repository.

        cycle_collaborator_permissions(repository_name, username):
            Cycles collaborator permissions to resolve access issues.

        audit_repository_access(repository_name):
            Audits current collaborator access and permissions for repository.

        batch_collaborator_operation(repositories, operation_type):
            Performs batch collaborator operations across multiple repositories.

        verify_collaborator_access(repository_name, username):
            Verifies that collaborator has appropriate access to repository.

        list_repository_collaborators(repository_name):
            Lists all collaborators and their permissions for specified repository.
    """

    def __init__(self, config_path: Path = Path("assignment.conf")):
        """
        Initialize collaborator manager with configuration and API setup.

        Args:
            config_path (Path): Path to configuration file.
                              Defaults to "assignment.conf" in current directory.
        """
        self.config_loader = ConfigLoader(config_path)
        self.config = self.config_loader.load()
        self.git_manager = GitManager()
        self.github_client = None

        # Initialize GitHub API client if available
        if GITHUB_AVAILABLE:
            try:
                self.github_client = self._initialize_github_client()
            except GitHubAuthenticationError as e:
                logger.warning(f"GitHub API initialization failed: {e}")
                self.github_client = None

    def _initialize_github_client(self) -> Optional['Github']:
        """
        Initialize GitHub API client with authentication.

        Returns:
            Github: Authenticated GitHub client instance or None if unavailable.

        Raises:
            GitHubAuthenticationError: If authentication fails.
        """
        if not GITHUB_AVAILABLE:
            logger.warning(
                "PyGithub not available - falling back to CLI operations")
            return None

        tokens = [
            self.config.get('GITHUB_TOKEN'),
            self.config.get('GITHUB_ACCESS_TOKEN'),
        ]

        for token in tokens:
            if not token:
                continue

            try:
                with github_api_context("github_client_initialization"):
                    client = Github(token)
                    # Test authentication by getting user info
                    client.get_user().login
                    logger.info("GitHub API client initialized successfully")
                    return client
            except GithubException as e:
                logger.warning(f"GitHub authentication failed with token: {e}")
                continue

        raise GitHubAuthenticationError(
            "No valid GitHub token found in environment or configuration")

    @github_api_retry(max_attempts=2, base_delay=1.0)
    def list_collaborators(self, repo_name: str) -> List[Dict[str, str]]:
        """
        List collaborators for a repository.

        Args:
            repo_name: Name of the repository (format: owner/repo)

        Returns:
            List[Dict[str, str]]: List of collaborator information dictionaries.

        Raises:
            GitHubRepositoryError: If repository access fails.
        """
        logger.info(f"Listing collaborators for {repo_name}")

        try:
            if self.github_client:
                return self._list_collaborators_via_api(repo_name)
            else:
                return self._list_collaborators_via_cli(repo_name)
        except Exception as e:
            raise GitHubRepositoryError(
                f"Failed to list collaborators for {repo_name}: {e}",
                repository_name=repo_name
            )

    def _list_collaborators_via_api(self, repo_name: str) -> List[Dict[str, str]]:
        """List collaborators using GitHub API."""
        logger.info("Using GitHub API for collaborator listing")

        try:
            repo = self.github_client.get_repo(repo_name)
            collaborators = []

            for collaborator in repo.get_collaborators():
                collaborator_info = {
                    "login": collaborator.login,
                    "permissions": self._get_collaborator_permissions(repo, collaborator),
                    "type": collaborator.type,
                    "site_admin": collaborator.site_admin
                }
                collaborators.append(collaborator_info)

            logger.info(f"Found {len(collaborators)} collaborators via API")
            return collaborators

        except GithubException as e:
            raise GitHubRepositoryError(
                f"GitHub API error listing collaborators: {e}",
                repository_name=repo_name
            )

    def _list_collaborators_via_cli(self, repo_name: str) -> List[Dict[str, str]]:
        """List collaborators using GitHub CLI fallback."""
        logger.info("Using GitHub CLI for collaborator listing")

        try:
            # Use gh CLI to list collaborators
            cmd = ['gh', 'api', f'repos/{repo_name}/collaborators']
            _proc = subprocess.run(
                cmd, capture_output=True, text=True, check=True)

            import json
            collaborators_data = json.loads(_proc.stdout)

            collaborators = []
            for collab in collaborators_data:
                collaborator_info = {
                    "login": collab.get("login", ""),
                    "permissions": collab.get("permissions", {}),
                    "type": collab.get("type", ""),
                    "site_admin": collab.get("site_admin", False)
                }
                collaborators.append(collaborator_info)

            logger.info(f"Found {len(collaborators)} collaborators via CLI")
            return collaborators

        except subprocess.CalledProcessError as e:
            raise GitHubRepositoryError(
                f"GitHub CLI error listing collaborators: {e}",
                repository_name=repo_name
            )

    def _get_collaborator_permissions(self, repo: 'Repository', collaborator) -> Dict[str, bool]:
        """Get detailed permissions for a collaborator."""
        try:
            permissions = repo.get_collaborator_permission(collaborator)
            return {
                "admin": permissions.permission == "admin",
                "maintain": permissions.permission == "maintain",
                "push": permissions.permission in ["admin", "maintain", "push"],
                "triage": permissions.permission in ["admin", "maintain", "push", "triage"],
                "pull": True  # Everyone has pull access if they're a collaborator
            }
        except GithubException:
            # Fallback to basic permissions if detailed access fails
            return {
                "admin": False,
                "maintain": False,
                "push": True,  # Assume push access for collaborators
                "triage": True,
                "pull": True
            }

    @github_api_retry(max_attempts=2, base_delay=1.0)
    def add_collaborator(self, repo_name: str, username: str, permission: str = "push") -> bool:
        """
        Add a collaborator to a repository.

        Args:
            repo_name: Name of the repository (format: owner/repo)
            username: GitHub username to add as collaborator
            permission: Permission level (admin, maintain, push, triage, pull)

        Returns:
            bool: True if collaborator was added successfully.

        Raises:
            GitHubRepositoryError: If adding collaborator fails.
        """
        logger.info(
            f"Adding collaborator {username} to {repo_name} with {permission} permission")

        try:
            if self.github_client:
                return self._add_collaborator_via_api(repo_name, username, permission)
            else:
                return self._add_collaborator_via_cli(repo_name, username, permission)
        except Exception as e:
            raise GitHubRepositoryError(
                f"Failed to add collaborator {username} to {repo_name}: {e}",
                repository_name=repo_name
            )

    def _add_collaborator_via_api(self, repo_name: str, username: str, permission: str) -> bool:
        """Add collaborator using GitHub API."""
        logger.info("Using GitHub API for adding collaborator")

        try:
            repo = self.github_client.get_repo(repo_name)
            user = self.github_client.get_user(username)

            # Add collaborator with specified permission
            repo.add_to_collaborators(user, permission=permission)

            logger.info(
                f"Successfully added {username} to {repo_name} with {permission} permission")
            return True

        except GithubException as e:
            raise GitHubRepositoryError(
                f"GitHub API error adding collaborator: {e}",
                repository_name=repo_name
            )

    def _add_collaborator_via_cli(self, repo_name: str, username: str, permission: str) -> bool:
        """Add collaborator using GitHub CLI fallback."""
        logger.info("Using GitHub CLI for adding collaborator")

        try:
            # Use gh CLI to add collaborator
            cmd = [
                'gh', 'api', f'repos/{repo_name}/collaborators/{username}',
                '--method', 'PUT',
                '--field', f'permission={permission}'
            ]
            subprocess.run(
                cmd, capture_output=True, text=True, check=True)

            logger.info(
                f"Successfully added {username} to {repo_name} via CLI")
            return True

        except subprocess.CalledProcessError as e:
            raise GitHubRepositoryError(
                f"GitHub CLI error adding collaborator: {e}",
                repository_name=repo_name
            )

    @github_api_retry(max_attempts=2, base_delay=1.0)
    def remove_collaborator(self, repo_name: str, username: str) -> bool:
        """
        Remove a collaborator from a repository.

        Args:
            repo_name: Name of the repository (format: owner/repo)
            username: GitHub username to remove

        Returns:
            bool: True if collaborator was removed successfully.

        Raises:
            GitHubRepositoryError: If removing collaborator fails.
        """
        logger.info(f"Removing collaborator {username} from {repo_name}")

        try:
            if self.github_client:
                return self._remove_collaborator_via_api(repo_name, username)
            else:
                return self._remove_collaborator_via_cli(repo_name, username)
        except Exception as e:
            raise GitHubRepositoryError(
                f"Failed to remove collaborator {username} from {repo_name}: {e}",
                repository_name=repo_name
            )

    def _remove_collaborator_via_api(self, repo_name: str, username: str) -> bool:
        """Remove collaborator using GitHub API."""
        logger.info("Using GitHub API for removing collaborator")

        try:
            repo = self.github_client.get_repo(repo_name)
            user = self.github_client.get_user(username)

            # Remove collaborator from repository
            repo.remove_from_collaborators(user)

            logger.info(f"Successfully removed {username} from {repo_name}")
            return True

        except GithubException as e:
            raise GitHubRepositoryError(
                f"GitHub API error removing collaborator: {e}",
                repository_name=repo_name
            )

    def _remove_collaborator_via_cli(self, repo_name: str, username: str) -> bool:
        """Remove collaborator using GitHub CLI fallback."""
        logger.info("Using GitHub CLI for removing collaborator")

        try:
            # Use gh CLI to remove collaborator
            cmd = [
                'gh', 'api', f'repos/{repo_name}/collaborators/{username}',
                '--method', 'DELETE'
            ]
            subprocess.run(
                cmd, capture_output=True, text=True, check=True)

            logger.info(
                f"Successfully removed {username} from {repo_name} via CLI")
            return True

        except subprocess.CalledProcessError as e:
            raise GitHubRepositoryError(
                f"GitHub CLI error removing collaborator: {e}",
                repository_name=repo_name
            )

    def cycle_collaborator_permissions(self, assignment_prefix: str, username: str) -> Dict[str, bool]:
        """Cycle collaborator permissions across assignment repositories."""
        logger.info(
            f"Cycling permissions for {username} on assignment {assignment_prefix}")

        results = {}

        try:
            # TODO: Implement permission cycling logic
            # 1. Find all repositories matching assignment prefix
            # 2. Remove collaborator from all repositories
            # 3. Add collaborator to next repository in cycle

            logger.warning(
                "Permission cycling not yet implemented - using bash wrapper")
            results[assignment_prefix] = True

        except Exception as e:
            logger.error(f"Failed to cycle permissions for {username}: {e}")
            results[assignment_prefix] = False

        return results

    def audit_repository_access(self, assignment_prefix: str) -> Dict[str, List[str]]:
        """Audit collaborator access across assignment repositories."""
        logger.info(f"Auditing access for assignment {assignment_prefix}")

        access_report = {}

        try:
            # TODO: Implement access auditing
            # 1. Find all repositories matching assignment prefix
            # 2. List collaborators for each repository
            # 3. Generate access report

            logger.warning(
                "Access auditing not yet implemented - using bash wrapper")

        except Exception as e:
            logger.error(f"Access audit failed for {assignment_prefix}: {e}")

        return access_report

    def update_repository_permissions(self, repo_name: str, permission_updates: Dict[str, str]) -> Dict[str, bool]:
        """Update permissions for multiple collaborators on a repository."""
        logger.info(
            f"Updating permissions for {len(permission_updates)} collaborators on {repo_name}")

        results = {}

        for username, permission in permission_updates.items():
            try:
                success = self.update_collaborator_permission(
                    repo_name, username, permission)
                results[username] = success

            except GitHubRepositoryError as e:
                logger.error(
                    f"Failed to update permission for {username}: {e}")
                results[username] = False
            except Exception as e:
                logger.error(
                    f"Unexpected error updating permission for {username}: {e}")
                results[username] = False

        return results

    @github_api_retry(max_attempts=2, base_delay=1.0)
    def update_collaborator_permission(self, repo_name: str, username: str, permission: str) -> bool:
        """
        Update permission for a single collaborator.

        Args:
            repo_name: Name of the repository (format: owner/repo)
            username: GitHub username to update
            permission: New permission level (admin, maintain, push, triage, pull)

        Returns:
            bool: True if permission was updated successfully.

        Raises:
            GitHubRepositoryError: If updating permission fails.
        """
        logger.info(
            f"Updating {username} permission to {permission} on {repo_name}")

        try:
            if self.github_client:
                return self._update_permission_via_api(repo_name, username, permission)
            else:
                return self._update_permission_via_cli(repo_name, username, permission)
        except Exception as e:
            raise GitHubRepositoryError(
                f"Failed to update permission for {username} on {repo_name}: {e}",
                repository_name=repo_name
            )

    def _update_permission_via_api(self, repo_name: str, username: str, permission: str) -> bool:
        """Update collaborator permission using GitHub API."""
        logger.info("Using GitHub API for permission update")

        try:
            repo = self.github_client.get_repo(repo_name)
            user = self.github_client.get_user(username)

            # Update collaborator permission (same as adding with new permission)
            repo.add_to_collaborators(user, permission=permission)

            logger.info(
                f"Successfully updated {username} permission to {permission} on {repo_name}")
            return True

        except GithubException as e:
            raise GitHubRepositoryError(
                f"GitHub API error updating permission: {e}",
                repository_name=repo_name
            )

    def _update_permission_via_cli(self, repo_name: str, username: str, permission: str) -> bool:
        """Update collaborator permission using GitHub CLI fallback."""
        logger.info("Using GitHub CLI for permission update")

        try:
            # Use gh CLI to update permission (same as add collaborator)
            cmd = [
                'gh', 'api', f'repos/{repo_name}/collaborators/{username}',
                '--method', 'PUT',
                '--field', f'permission={permission}'
            ]
            _proc = subprocess.run(
                cmd, capture_output=True, text=True, check=True)

            logger.info(
                f"Successfully updated {username} permission to {permission} via CLI")
            return True

        except subprocess.CalledProcessError as e:
            raise GitHubRepositoryError(
                f"GitHub CLI error updating permission: {e}",
                repository_name=repo_name
            )
