"""
Repository Fetcher for GitHub Classroom Student Repositories.

This module handles:
- Student repository discovery via GitHub API integration
- Repository cloning and synchronization with progress tracking
- Template repository management and synchronization
- Git operations and batch processing capabilities
- Authentication and error handling for GitHub operations
"""

from pathlib import Path
from typing import List, Dict, Optional
import subprocess
import os
from dataclasses import dataclass

try:
    from github import Github, GithubException
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False

from ..utils import get_logger, GitManager, PathManager
from ..utils.github_exceptions import (
    GitHubAuthenticationError, GitHubDiscoveryError,
    github_api_retry
)
from ..config import ConfigLoader

logger = get_logger("repos.fetch")


@dataclass
class RepositoryInfo:
    """Information about a discovered repository."""
    name: str
    url: str
    clone_url: str
    is_template: bool = False
    is_student_repo: bool = False
    student_identifier: Optional[str] = None


@dataclass
class FetchResult:
    """Result of repository fetch operation."""
    repository: RepositoryInfo
    success: bool
    local_path: Optional[Path] = None
    error_message: Optional[str] = None
    was_cloned: bool = False
    was_updated: bool = False


class RepositoryFetcher:
    """
    RepositoryFetcher handles comprehensive GitHub Classroom repository operations.

    This class provides methods for discovering student repositories through GitHub API,
    filtering repositories by assignment patterns, batch fetching with progress tracking,
    and managing template repository synchronization. It supports both authenticated
    GitHub API access and fallback to command-line operations.

    Args:
        config_path (Path): Path to the assignment configuration file.
                          Defaults to "assignment.conf" in current directory.

    Attributes:
        config_loader (ConfigLoader): Configuration loader instance.
        config (dict): Loaded configuration values.
        git_manager (GitManager): Git operations manager.
        path_manager (PathManager): Path management utilities.
        github_client (Github): GitHub API client (if authenticated).

    Methods:
        authenticate_github():
            Establishes authenticated connection to GitHub API.

        discover_repositories(assignment_prefix, organization):
            Discovers student repositories matching assignment pattern.

        fetch_repositories(repo_info_list):
            Batch fetches multiple repositories with progress tracking.

        fetch_single_repository(repo_info):
            Fetches a single repository with detailed result information.

        sync_template_repository():
            Synchronizes changes from template repository to student repos.

        update_repositories():
            Updates all local repositories with latest changes.

        filter_student_repositories(repositories, assignment_prefix):
            Filters repositories to identify student submissions.
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize repository fetcher with configuration and API setup.

        Args:
            config_path (Optional[Path]): Path to configuration file.
                                        If None, uses PathManager to find config.
        """
        self.config_loader = ConfigLoader(config_path)
        self.config = self.config_loader.load()
        self.git_manager = GitManager()
        self.path_manager = PathManager()
        self.github_client: Optional['Github'] = None

        # Initialize GitHub client if possible
        try:
            self.authenticate_github()
        except GitHubAuthenticationError as e:
            logger.warning(f"GitHub API authentication failed: {e}")
            logger.info(
                "Will fall back to command-line operations when needed")

    def authenticate_github(self) -> bool:
        """
        Authenticate with GitHub API using available credentials.

        Attempts authentication using GitHub token from environment variables
        or configuration. Supports GITHUB_TOKEN, GITHUB_ACCESS_TOKEN, and
        configuration-based token specification.

        Returns:
            bool: True if authentication successful, False otherwise.

        Raises:
            GitHubAuthenticationError: If PyGithub is not available or authentication fails.
        """
        if not GITHUB_AVAILABLE:
            raise GitHubAuthenticationError(
                "PyGithub library not available. Install with: pip install PyGithub")

        # Try multiple token sources
        token_sources = [
            os.getenv('GITHUB_TOKEN'),
            os.getenv('GITHUB_ACCESS_TOKEN'),
            self.config.get('GITHUB_TOKEN'),
            self.config.get('GITHUB_ACCESS_TOKEN')
        ]

        for token in token_sources:
            if token:
                try:
                    self.github_client = Github(token)
                    # Test authentication by getting user info
                    user = self.github_client.get_user()
                    logger.info(
                        f"Successfully authenticated as GitHub user: {user.login}")
                    return True
                except GithubException as e:
                    logger.warning(
                        f"GitHub authentication failed with token: {e}")
                    continue

        raise GitHubAuthenticationError(
            "No valid GitHub token found in environment or configuration")

    def discover_repositories(self, assignment_prefix: str = None, organization: str = None) -> List[RepositoryInfo]:
        """
        Discover student repositories from GitHub organization using API or CLI fallback.

        Searches the specified GitHub organization for repositories matching the
        assignment prefix pattern. Filters results to identify student repositories,
        template repositories, and instructor repositories based on naming conventions.

        Args:
            assignment_prefix (str, optional): Repository prefix pattern to search for.
                                             If None, uses ASSIGNMENT_NAME from config.
            organization (str, optional): GitHub organization to search.
                                        If None, uses GITHUB_ORGANIZATION from config.

        Returns:
            List[RepositoryInfo]: List of discovered repository information objects.

        Raises:
            GitHubDiscoveryError: If discovery fails or required parameters missing.

        Example:
            >>> fetcher = RepositoryFetcher()
            >>> repos = fetcher.discover_repositories("python-basics", "my-classroom")
            >>> for repo in repos:
            ...     print(f"Found: {repo.name} ({'student' if repo.is_student_repo else 'other'})")
        """
        # Get parameters from config if not provided
        if not assignment_prefix:
            assignment_prefix = self.config.get('ASSIGNMENT_NAME')
            if not assignment_prefix:
                # Try to extract from template repo URL
                template_url = self.config.get('TEMPLATE_REPO_URL')
                if template_url:
                    assignment_prefix = template_url.split(
                        '/')[-1].replace('.git', '').replace('-template', '')

        if not organization:
            organization = self.config.get('GITHUB_ORGANIZATION')

        if not assignment_prefix or not organization:
            raise GitHubDiscoveryError(
                f"Missing required parameters: assignment_prefix='{assignment_prefix}', "
                f"organization='{organization}'. Check configuration.",
                assignment_prefix=assignment_prefix,
                organization=organization
            )

        logger.info(
            f"Discovering repositories with prefix '{assignment_prefix}' in organization '{organization}'")

        try:
            if self.github_client:
                return self._discover_via_api(assignment_prefix, organization)
            else:
                return self._discover_via_cli(assignment_prefix, organization)
        except Exception as e:
            logger.error(f"Repository discovery failed: {e}")
            raise GitHubDiscoveryError(
                f"Failed to discover repositories: {e}",
                assignment_prefix=assignment_prefix,
                organization=organization,
                original_error=e
            )

    @github_api_retry(max_attempts=2, base_delay=1.0)
    def _discover_via_api(self, assignment_prefix: str, organization: str) -> List[RepositoryInfo]:
        """Discover repositories using GitHub API."""
        logger.info("Using GitHub API for repository discovery")

        try:
            org = self.github_client.get_organization(organization)
            repositories = []

            # Get all repositories from organization
            for repo in org.get_repos():
                if assignment_prefix in repo.name:
                    repo_info = RepositoryInfo(
                        name=repo.name,
                        url=repo.html_url,
                        clone_url=repo.clone_url,
                        is_template=repo.name.endswith('-template'),
                        is_student_repo=self._is_student_repository(
                            repo.name, assignment_prefix),
                        student_identifier=self._extract_student_identifier(
                            repo.name, assignment_prefix)
                    )
                    repositories.append(repo_info)
                    logger.debug(f"Found repository: {repo.name}")

            logger.info(f"Discovered {len(repositories)} repositories via API")
            return repositories

        except GithubException as e:
            logger.error(f"GitHub API error: {e}")
            raise GitHubDiscoveryError(
                f"GitHub API error: {e}",
                assignment_prefix=assignment_prefix,
                organization=organization,
                original_error=e
            )

    def _discover_via_cli(self, assignment_prefix: str, organization: str) -> List[RepositoryInfo]:
        """Discover repositories using GitHub CLI fallback."""
        logger.info("Using GitHub CLI for repository discovery")

        try:
            # Use gh CLI to list repositories
            cmd = ['gh', 'repo', 'list', organization, '--limit', '1000']
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True)

            repositories = []
            for line in result.stdout.strip().split('\n'):
                if not line or assignment_prefix not in line:
                    continue

                # Parse gh output: "org/repo-name   description   visibility"
                parts = line.split('\t')
                if len(parts) < 1:
                    continue

                repo_full_name = parts[0]
                repo_name = repo_full_name.split('/')[-1]

                repo_info = RepositoryInfo(
                    name=repo_name,
                    url=f"https://github.com/{repo_full_name}",
                    clone_url=f"https://github.com/{repo_full_name}.git",
                    is_template=repo_name.endswith('-template'),
                    is_student_repo=self._is_student_repository(
                        repo_name, assignment_prefix),
                    student_identifier=self._extract_student_identifier(
                        repo_name, assignment_prefix)
                )
                repositories.append(repo_info)
                logger.debug(f"Found repository: {repo_name}")

            logger.info(f"Discovered {len(repositories)} repositories via CLI")
            return repositories

        except subprocess.CalledProcessError as e:
            logger.error(f"GitHub CLI error: {e}")
            raise GitHubDiscoveryError(
                f"GitHub CLI error: {e}",
                assignment_prefix=assignment_prefix,
                organization=organization,
                original_error=e
            )
        except FileNotFoundError:
            raise GitHubDiscoveryError(
                "GitHub CLI (gh) not found. Please install GitHub CLI or configure API access.",
                assignment_prefix=assignment_prefix,
                organization=organization
            )

    def _is_student_repository(self, repo_name: str, assignment_prefix: str) -> bool:
        """Check if repository name indicates a student submission."""
        # Student repos follow pattern: assignment-prefix-student-identifier
        if not repo_name.startswith(f"{assignment_prefix}-"):
            return False

        # Exclude template and instructor repositories
        if repo_name.endswith('-template') or 'instructor' in repo_name.lower():
            return False

        # Exclude classroom template copies
        if 'classroom' in repo_name.lower() and 'template' in repo_name.lower():
            return False

        return True

    def _extract_student_identifier(self, repo_name: str, assignment_prefix: str) -> Optional[str]:
        """Extract student identifier from repository name."""
        if not self._is_student_repository(repo_name, assignment_prefix):
            return None

        # Remove assignment prefix and return remainder
        prefix_with_dash = f"{assignment_prefix}-"
        if repo_name.startswith(prefix_with_dash):
            return repo_name[len(prefix_with_dash):]

        return None

    def fetch_repositories(self, repo_info_list: List[RepositoryInfo],
                           target_directory: str = "student-repos") -> List[FetchResult]:
        """
        Fetch multiple repositories with comprehensive progress tracking and error handling.

        Performs batch fetching of repositories with detailed result tracking for each
        operation. Handles both cloning new repositories and updating existing ones.
        Provides comprehensive error handling and logging for each repository operation.

        Args:
            repo_info_list (List[RepositoryInfo]): List of repositories to fetch.
            target_directory (str): Target directory name for cloned repositories.
                                   Defaults to "student-repos".

        Returns:
            List[FetchResult]: List of detailed fetch results for each repository.

        Example:
            >>> repositories = fetcher.discover_repositories("python-basics", "my-org")
            >>> results = fetcher.fetch_repositories(repositories)
            >>> successful = [r for r in results if r.success]
            >>> print(f"Successfully fetched {len(successful)}/{len(results)} repositories")
        """
        logger.info(
            f"Starting batch fetch of {len(repo_info_list)} repositories")

        results = []
        success_count = 0

        for i, repo_info in enumerate(repo_info_list, 1):
            logger.info(
                f"[{i}/{len(repo_info_list)}] Processing {repo_info.name}")

            try:
                result = self.fetch_single_repository(
                    repo_info, target_directory)
                results.append(result)

                if result.success:
                    success_count += 1
                    status = "cloned" if result.was_cloned else "updated"
                    logger.info(f"✓ Successfully {status} {repo_info.name}")
                else:
                    logger.error(
                        f"✗ Failed to fetch {repo_info.name}: {result.error_message}")

            except Exception as e:
                logger.error(f"✗ Exception fetching {repo_info.name}: {e}")
                results.append(FetchResult(
                    repository=repo_info,
                    success=False,
                    error_message=str(e)
                ))

        logger.info(
            f"Batch fetch completed: {success_count}/{len(repo_info_list)} successful")
        return results

    def fetch_single_repository(self, repo_info: RepositoryInfo,
                                target_directory: str = "student-repos") -> FetchResult:
        """
        Fetch a single repository with detailed result tracking.

        Handles both cloning new repositories and updating existing ones.
        Provides comprehensive error handling and detailed result information
        including local paths, operation types, and error messages.

        Args:
            repo_info (RepositoryInfo): Repository information to fetch.
            target_directory (str): Target directory for cloned repository.

        Returns:
            FetchResult: Detailed result of the fetch operation.

        Example:
            >>> repo = RepositoryInfo(name="python-basics-student1", 
            ...                      url="https://github.com/org/python-basics-student1",
            ...                      clone_url="https://github.com/org/python-basics-student1.git")
            >>> result = fetcher.fetch_single_repository(repo)
            >>> if result.success:
            ...     print(f"Repository saved to: {result.local_path}")
        """
        logger.debug(f"Fetching repository: {repo_info.name}")

        try:
            # Determine local path
            local_path = self.path_manager.ensure_output_directory(
                target_directory) / repo_info.name

            if local_path.exists() and (local_path / ".git").exists():
                # Repository exists, pull latest changes
                logger.debug(
                    f"Repository {repo_info.name} exists, updating...")
                git_manager = GitManager(local_path)
                success = git_manager.pull_repo()

                return FetchResult(
                    repository=repo_info,
                    success=success,
                    local_path=local_path,
                    was_updated=success,
                    error_message=None if success else "Git pull operation failed"
                )
            else:
                # Clone repository
                logger.debug(f"Cloning repository {repo_info.name}...")
                success = self.git_manager.clone_repo(
                    repo_info.clone_url, local_path)

                return FetchResult(
                    repository=repo_info,
                    success=success,
                    local_path=local_path if success else None,
                    was_cloned=success,
                    error_message=None if success else "Git clone operation failed"
                )

        except Exception as e:
            logger.error(f"Error fetching repository {repo_info.name}: {e}")
            return FetchResult(
                repository=repo_info,
                success=False,
                error_message=str(e)
            )

    def sync_template_repository(self) -> bool:
        """
        Synchronize changes from template repository to student repositories.

        Implements template repository synchronization by fetching the latest
        template changes and providing mechanisms to apply them to student
        repositories. This is useful for distributing updates, fixes, or
        additional materials to all student repositories.

        Returns:
            bool: True if template synchronization successful, False otherwise.

        Raises:
            GitHubDiscoveryError: If template repository configuration is missing.

        Example:
            >>> fetcher = RepositoryFetcher()
            >>> success = fetcher.sync_template_repository()
            >>> if success:
            ...     print("Template repository synchronized successfully")
        """
        logger.info("Synchronizing template repository")

        try:
            template_repo_url = self.config.get("TEMPLATE_REPO_URL")
            if not template_repo_url:
                logger.error(
                    "No template repository URL configured (TEMPLATE_REPO_URL)")
                return False

            # Extract template repository name
            template_name = template_repo_url.split(
                "/")[-1].replace(".git", "")
            template_path = self.path_manager.ensure_output_directory(
                "templates") / template_name

            # Fetch template repository
            if template_path.exists() and (template_path / ".git").exists():
                # Update existing template
                git_manager = GitManager(template_path)
                success = git_manager.pull_repo()
                if success:
                    logger.info(
                        f"Template repository updated at: {template_path}")
                else:
                    logger.error("Failed to update template repository")
                return success
            else:
                # Clone template repository
                success = self.git_manager.clone_repo(
                    template_repo_url, template_path)
                if success:
                    logger.info(
                        f"Template repository cloned to: {template_path}")
                else:
                    logger.error("Failed to clone template repository")
                return success

        except Exception as e:
            logger.error(f"Template sync failed: {e}")
            return False

    def update_repositories(self, target_directory: str = "student-repos") -> Dict[str, bool]:
        """
        Update all local repositories with latest changes from remote.

        Scans the specified directory for Git repositories and attempts to
        pull the latest changes from their remote origins. Provides detailed
        logging and result tracking for each repository.

        Args:
            target_directory (str): Directory containing repositories to update.
                                  Defaults to "student-repos".

        Returns:
            Dict[str, bool]: Dictionary mapping repository names to update success status.

        Example:
            >>> fetcher = RepositoryFetcher()
            >>> results = fetcher.update_repositories()
            >>> failed_updates = [name for name, success in results.items() if not success]
            >>> if failed_updates:
            ...     print(f"Failed to update: {', '.join(failed_updates)}")
        """
        logger.info(f"Updating all repositories in {target_directory}")

        results = {}
        repo_dir = self.path_manager.ensure_output_directory(target_directory)

        if not repo_dir.exists():
            logger.warning(f"Repository directory does not exist: {repo_dir}")
            return results

        # Find all Git repositories in the directory
        git_repos = []
        for item in repo_dir.iterdir():
            if item.is_dir() and (item / ".git").exists():
                git_repos.append(item)

        if not git_repos:
            logger.info("No Git repositories found to update")
            return results

        logger.info(f"Found {len(git_repos)} repositories to update")

        for i, repo_path in enumerate(git_repos, 1):
            repo_name = repo_path.name
            logger.info(f"[{i}/{len(git_repos)}] Updating {repo_name}")

            try:
                git_manager = GitManager(repo_path)
                success = git_manager.pull_repo()
                results[repo_name] = success

                if success:
                    logger.info(f"✓ Successfully updated {repo_name}")
                else:
                    logger.error(f"✗ Failed to update {repo_name}")

            except Exception as e:
                logger.error(f"✗ Exception updating {repo_name}: {e}")
                results[repo_name] = False

        success_count = sum(1 for success in results.values() if success)
        logger.info(
            f"Repository updates completed: {success_count}/{len(results)} successful")
        return results

    def filter_student_repositories(self, repositories: List[RepositoryInfo],
                                    assignment_prefix: str,
                                    include_template: bool = False,
                                    exclude_instructor: bool = True) -> List[RepositoryInfo]:
        """
        Filter repositories to identify student submissions based on naming patterns.

        Applies filtering logic to identify student repositories while optionally
        including or excluding template and instructor repositories based on
        specified criteria.

        Args:
            repositories (List[RepositoryInfo]): List of repositories to filter.
            assignment_prefix (str): Assignment prefix to match against.
            include_template (bool): Whether to include template repositories.
                                   Defaults to False.
            exclude_instructor (bool): Whether to exclude instructor repositories.
                                     Defaults to True.

        Returns:
            List[RepositoryInfo]: Filtered list of repositories matching criteria.

        Example:
            >>> all_repos = fetcher.discover_repositories("python-basics", "my-org")
            >>> student_repos = fetcher.filter_student_repositories(
            ...     all_repos, "python-basics", exclude_instructor=True
            ... )
            >>> print(f"Found {len(student_repos)} student repositories")
        """
        filtered = []

        for repo in repositories:
            # Include template repositories if requested
            if repo.is_template and include_template:
                filtered.append(repo)
                continue

            # Exclude instructor repositories if requested
            if exclude_instructor and 'instructor' in repo.name.lower():
                continue

            # Include student repositories
            if repo.is_student_repo:
                filtered.append(repo)

        logger.info(
            f"Filtered {len(filtered)} repositories from {len(repositories)} total")
        return filtered

    def get_repository_summary(self, repositories: List[RepositoryInfo]) -> Dict[str, int]:
        """
        Generate summary statistics for a list of repositories.

        Args:
            repositories (List[RepositoryInfo]): List of repositories to summarize.

        Returns:
            Dict[str, int]: Dictionary containing count statistics.
        """
        summary = {
            'total': len(repositories),
            'student_repos': sum(1 for r in repositories if r.is_student_repo),
            'template_repos': sum(1 for r in repositories if r.is_template),
            'other_repos': 0
        }
        summary['other_repos'] = summary['total'] - \
            summary['student_repos'] - summary['template_repos']
        return summary

    def fetch_all_repositories(self, verbose: bool = False) -> bool:
        """
        Discover and fetch all student repositories for the configured assignment.

        This is the main entry point that combines repository discovery and fetching
        into a single operation. It uses the configuration to determine the assignment
        prefix and organization, then discovers and fetches all matching repositories.

        Args:
            verbose (bool): Enable verbose logging output.

        Returns:
            bool: True if at least one repository was successfully fetched, False otherwise.

        Example:
            >>> fetcher = RepositoryFetcher(config_path="assignment.conf")
            >>> success = fetcher.fetch_all_repositories(verbose=True)
            >>> if success:
            ...     print("Repositories fetched successfully")
        """
        try:
            # Get assignment prefix and organization from config
            assignment_prefix = self.config.get('ASSIGNMENT_NAME')
            organization = self.config.get('GITHUB_ORGANIZATION')

            if not assignment_prefix or not organization:
                logger.error(
                    "Missing ASSIGNMENT_NAME or GITHUB_ORGANIZATION in configuration")
                return False

            # Discover repositories
            logger.info(
                f"Discovering repositories for assignment: {assignment_prefix}")
            all_repositories = self.discover_repositories(
                assignment_prefix=assignment_prefix,
                organization=organization
            )

            if not all_repositories:
                logger.warning("No repositories found to fetch")
                return False

            # Filter to only student repositories (exclude templates and instructor repos)
            student_repositories = self.filter_student_repositories(
                all_repositories,
                assignment_prefix,
                include_template=False,
                exclude_instructor=True
            )

            if not student_repositories:
                logger.warning("No student repositories found to fetch")
                return False

            logger.info(
                f"Found {len(student_repositories)} student repositories to fetch "
                f"(filtered from {len(all_repositories)} total)"
            )

            # Fetch only student repositories
            results = self.fetch_repositories(student_repositories)

            # Check if any were successful
            successful = [r for r in results if r.success]

            if not successful:
                logger.error("Failed to fetch any repositories")
                return False

            logger.info(
                f"Successfully fetched {len(successful)}/{len(results)} repositories")

            # Write repository URLs to student-repos.txt
            self._write_repository_list(student_repositories)

            # Update .gitignore to exclude student-repos/ and student-repos.txt
            self._update_gitignore()

            return True

        except Exception as e:
            logger.error(f"Failed to fetch repositories: {e}")
            return False

    def _write_repository_list(self, repositories: List[RepositoryInfo]) -> None:
        """
        Write repository URLs to student-repos.txt file.

        Args:
            repositories: List of repositories to write to file.
        """
        try:
            output_file = Path.cwd() / "student-repos.txt"

            with open(output_file, 'w') as f:
                for repo in repositories:
                    if repo.is_student_repo:  # Only write student repositories
                        f.write(f"{repo.url}\n")

            logger.info(f"✅ Created repository list: {output_file}")
            student_count = sum(1 for r in repositories if r.is_student_repo)
            logger.info(f"   Listed {student_count} student repository URLs")

        except Exception as e:
            logger.warning(f"Failed to write student-repos.txt: {e}")

    def _update_gitignore(self) -> None:
        """
        Update .gitignore to exclude student-repos/ directory and student-repos.txt file.
        """
        try:
            gitignore_path = Path.cwd() / ".gitignore"

            # Read existing .gitignore content
            existing_lines = []
            if gitignore_path.exists():
                with open(gitignore_path, 'r') as f:
                    existing_lines = f.read().splitlines()

            # Check if entries already exist
            entries_to_add = []
            if "student-repos/" not in existing_lines:
                entries_to_add.append("student-repos/")
            if "student-repos.txt" not in existing_lines:
                entries_to_add.append("student-repos.txt")

            # Add entries if needed
            if entries_to_add:
                with open(gitignore_path, 'a') as f:
                    if existing_lines and not existing_lines[-1].strip() == "":
                        # Add blank line if file doesn't end with one
                        f.write("\n")
                    f.write(
                        "# GitHub Classroom student repositories (auto-generated)\n")
                    for entry in entries_to_add:
                        f.write(f"{entry}\n")

                logger.info(
                    f"✅ Updated .gitignore with: {', '.join(entries_to_add)}")
            else:
                logger.debug(
                    ".gitignore already contains student-repos entries")

        except Exception as e:
            logger.warning(f"Failed to update .gitignore: {e}")
