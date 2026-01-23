"""
Python implementation of add-secrets-to-students functionality.

This module provides a comprehensive Python implementation
for adding secrets to student GitHub repositories using global configuration.
"""

import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests

from ..utils import logger
from ..config.global_config import get_global_config
from ..utils.github_classroom_api import create_classroom_api_client, GitHubClassroomAPIError


class GitHubSecretsManager:
    """Manages GitHub repository secrets using the GitHub API and global configuration."""

    def __init__(self, dry_run: bool = False):
        """
        Initialize the secrets manager using global configuration.

        Args:
            dry_run: If True, show what would be done without executing
        """
        self.dry_run = dry_run
        self.global_config = get_global_config()

        if not self.global_config:
            raise ValueError(
                "Global configuration not loaded. Please run from assignment root directory.")

        self.github_token = self._get_github_token()
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "classdock"
        }

    def _get_github_token(self) -> str:
        """Get GitHub token using the centralized token manager."""
        try:
            from ..utils.token_manager import GitHubTokenManager

            token_manager = GitHubTokenManager()
            token = token_manager.get_github_token()

            if token:
                return token
            else:
                # Fallback to original logic if token manager fails
                logger.warning(
                    "Token manager returned None, trying fallback methods")
                return self._get_github_token_fallback()

        except Exception as e:
            logger.warning(
                f"Error using token manager: {e}, trying fallback methods")
            return self._get_github_token_fallback()

    def _get_github_token_fallback(self) -> str:
        """Fallback GitHub token retrieval from gh CLI or environment."""
        try:
            # Try to get token from gh CLI
            result = subprocess.run(
                ["gh", "auth", "token"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("Could not get GitHub token from gh CLI")
            # Fallback to environment variable
            import os
            token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
            if not token:
                raise ValueError(
                    "No GitHub token found. Please authenticate with 'gh auth login' or set GITHUB_TOKEN")
            return token

    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make authenticated GitHub API request."""
        full_url = f"{self.base_url}{url}" if url.startswith("/") else url

        kwargs.setdefault("headers", {}).update(self.headers)

        if self.dry_run and method.upper() in ["POST", "PUT", "PATCH", "DELETE"]:
            logger.info(f"[DRY RUN] Would {method.upper()} {full_url}")
            # Return a mock response for dry run
            mock_response = requests.Response()
            mock_response.status_code = 200
            mock_response._content = b'{"dry_run": true}'
            return mock_response

        response = requests.request(method, full_url, **kwargs)
        response.raise_for_status()
        return response

    def parse_repo_url(self, repo_url: str) -> Tuple[str, str]:
        """
        Parse GitHub repository URL to extract owner and repo name.

        Args:
            repo_url: GitHub repository URL

        Returns:
            Tuple of (owner, repo_name)
        """
        # Handle different URL formats
        if repo_url.startswith("https://github.com/"):
            # https://github.com/owner/repo or https://github.com/owner/repo.git
            path = urlparse(repo_url).path.strip("/")
            if path.endswith(".git"):
                path = path[:-4]
            parts = path.split("/")
            if len(parts) >= 2:
                return parts[0], parts[1]
        elif "/" in repo_url and not repo_url.startswith("http"):
            # owner/repo format
            parts = repo_url.split("/")
            if len(parts) >= 2:
                return parts[0], parts[1]

        raise ValueError(f"Invalid repository URL format: {repo_url}")

    def check_repo_access(self, owner: str, repo: str) -> bool:
        """Check if repository exists and is accessible."""
        try:
            response = self._make_request("GET", f"/repos/{owner}/{repo}")
            return response.status_code == 200
        except requests.RequestException:
            return False

    def get_repo_public_key(self, owner: str, repo: str) -> Dict[str, str]:
        """Get repository's public key for secret encryption."""
        response = self._make_request(
            "GET", f"/repos/{owner}/{repo}/actions/secrets/public-key")
        return response.json()

    def encrypt_secret(self, public_key: str, secret_value: str) -> str:
        """
        Legacy method - now using GitHub CLI which handles encryption automatically.
        Kept for backward compatibility.
        """
        logger.warning(
            "encrypt_secret method is deprecated - using GitHub CLI instead")
        return secret_value

    def list_repo_secrets(self, owner: str, repo: str) -> List[Dict[str, str]]:
        """List secrets in repository."""
        try:
            response = self._make_request(
                "GET", f"/repos/{owner}/{repo}/actions/secrets")
            return response.json().get("secrets", [])
        except requests.RequestException:
            return []

    def get_secret_info(self, owner: str, repo: str, secret_name: str) -> Optional[Dict[str, str]]:
        """Get information about a specific secret."""
        secrets = self.list_repo_secrets(owner, repo)
        for secret in secrets:
            if secret["name"] == secret_name:
                return secret
        return None

    def secret_needs_update(self, secret_info: Optional[Dict[str, str]], max_age_days: int = 90) -> bool:
        """Determine if secret needs updating based on age."""
        if not secret_info:
            return True  # Secret doesn't exist, needs creation

        # Parse the updated_at timestamp
        try:
            updated_at = datetime.fromisoformat(
                secret_info["updated_at"].replace("Z", "+00:00"))
            age = datetime.now(updated_at.tzinfo) - updated_at
            return age.days > max_age_days
        except (KeyError, ValueError):
            # If we can't determine age, assume it needs update
            return True

    def add_secret_to_repo(
        self,
        owner: str,
        repo: str,
        secret_name: str,
        secret_value: str,
        max_age_days: int = 90,
        force_update: bool = False
    ) -> bool:
        """
        Add or update a secret in a repository using GitHub CLI.

        Args:
            owner: Repository owner
            repo: Repository name
            secret_name: Name of the secret
            secret_value: Value of the secret (will be copied as-is)
            max_age_days: Maximum age before updating
            force_update: Force update regardless of age

        Returns:
            True if successful, False otherwise
        """
        repo_full_name = f"{owner}/{repo}"

        logger.info(
            f"Adding secret '{secret_name}' to repository: {repo_full_name}")

        # Check repository access
        if not self.check_repo_access(owner, repo):
            logger.error(f"Cannot access repository: {repo_full_name}")
            return False

        # Check existing secret
        existing_secret = self.get_secret_info(owner, repo, secret_name)

        if existing_secret and not force_update:
            if not self.secret_needs_update(existing_secret, max_age_days):
                logger.info(
                    f"Secret '{secret_name}' is up to date in {repo_full_name}")
                return True

        try:
            if self.dry_run:
                logger.info(
                    f"[DRY RUN] Would add secret '{secret_name}' to {repo_full_name}")
                logger.info(f"[DRY RUN] Secret value: {secret_value[:10]}...")
                return True

            # Use GitHub CLI to add the secret (it handles encryption automatically)
            cmd = [
                "gh", "secret", "set", secret_name,
                "--repo", repo_full_name,
                "--body", secret_value
            ]

            _result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            action = "Created" if not existing_secret else "Updated"
            logger.info(
                f"✅ {action} secret '{secret_name}' in {repo_full_name}")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(
                f"GitHub CLI error for {repo_full_name}: {e.stderr.strip()}")
            return False
        except Exception as e:
            logger.error(f"Error adding secret to {repo_full_name}: {e}")
            return False

    def validate_token_format(self, token_value: str, skip_validation: bool = False) -> bool:
        """Validate GitHub token format."""
        if skip_validation:
            return True

        if not token_value.startswith("ghp_"):
            logger.error(
                f"Invalid token format. Expected 'ghp_' prefix, got: {token_value[:10]}...")
            return False

        return True

    def get_instructor_token(self, token_file: str = "instructor_token.txt") -> str:
        """Load instructor token from file."""
        token_path = Path(token_file)

        if not token_path.exists():
            raise FileNotFoundError(f"Token file not found: {token_path}")

        token_value = token_path.read_text().strip()

        if not token_value:
            raise ValueError("Token file is empty")

        return token_value

    def process_single_repo(
        self,
        repo_url: str,
        secret_name: str = "INSTRUCTOR_TESTS_TOKEN",
        secret_value: Optional[str] = None,
        max_age_days: int = 90,
        force_update: bool = False,
        skip_validation: bool = False
    ) -> bool:
        """
        Process a single repository.

        Args:
            repo_url: Repository URL to process
            secret_name: Name of the secret to add
            secret_value: Value of the secret. If None, uses centralized token from GitHubTokenManager
            max_age_days: Maximum age before updating secrets
            force_update: Force update regardless of age
            skip_validation: Skip GitHub token format validation

        Returns:
            True if successful, False otherwise
        """
        try:
            # Parse repository URL
            owner, repo = self.parse_repo_url(repo_url)

            # Use centralized token if no explicit secret value provided
            if secret_value is None:
                secret_value = self.github_token
                logger.debug(
                    f"Using centralized GitHub token for secret '{secret_name}'")

            # Validate token format
            if not self.validate_token_format(secret_value, skip_validation):
                return False

            # Add secret to repository
            return self.add_secret_to_repo(
                owner, repo, secret_name, secret_value, max_age_days, force_update
            )

        except Exception as e:
            logger.error(f"Error processing repository {repo_url}: {e}")
            return False

    def process_batch_repos(
        self,
        repo_urls: List[str],
        secret_name: str = "INSTRUCTOR_TESTS_TOKEN",
        secret_value: Optional[str] = None,
        max_age_days: int = 90,
        force_update: bool = False,
        skip_validation: bool = False
    ) -> Dict[str, int]:
        """
        Process multiple repositories.

        Args:
            repo_urls: List of repository URLs to process
            secret_name: Name of the secret to add
            secret_value: Value of the secret. If None, uses centralized token from GitHubTokenManager
            max_age_days: Maximum age before updating secrets
            force_update: Force update regardless of age
            skip_validation: Skip GitHub token format validation

        Returns:
            Dictionary with success and failure counts
        """
        results = {"success": 0, "failed": 0, "total": len(repo_urls)}

        logger.info(f"Processing {len(repo_urls)} repositories")

        for repo_url in repo_urls:
            repo_url = repo_url.strip()
            if not repo_url or repo_url.startswith("#"):
                continue  # Skip empty lines and comments

            if self.process_single_repo(
                repo_url, secret_name, secret_value, max_age_days, force_update, skip_validation
            ):
                results["success"] += 1
            else:
                results["failed"] += 1

        logger.info(
            f"Batch processing complete: {results['success']} success, {results['failed']} failed")
        return results

    def add_secrets_from_global_config(self, repo_urls: Optional[List[str]] = None, force_update: bool = False) -> bool:
        """
        Add secrets to repositories using global configuration.

        Args:
            repo_urls: List of repository URLs (if None, auto-discover from config)
            force_update: Force update secrets even if they already exist and are up to date

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if secrets management is enabled
            if not self.global_config.step_manage_secrets:
                logger.info(
                    "Secret management is disabled (STEP_MANAGE_SECRETS=false)")
                return True

            # Get secrets configuration from global config
            if not self.global_config.secrets_config:
                logger.warning(
                    "No secrets configuration found in global config")
                logger.info("No secrets configuration found - nothing to do")
                return True

            # Auto-discover repositories if not provided
            if repo_urls is None:
                repo_urls = self._discover_repositories()
                if not repo_urls:
                    logger.warning(
                        "No repositories discovered for secrets management")
                    return True

            # Process all configured secrets
            for secret_config in self.global_config.secrets_config:
                logger.info(f"Processing secret: {secret_config.name}")

                # Determine the secret value to use:
                # - If the secret uses centralized token (token_file is None or empty),
                #   use the centralized GitHub token from GitHubTokenManager
                # - Otherwise, read the specified token file (legacy behavior)
                secret_value = None

                if secret_config.uses_centralized_token():
                    # Use centralized token from GitHubTokenManager (already loaded in self.github_token)
                    secret_value = self.github_token
                    logger.debug(
                        f"Using centralized GitHub token for secret '{secret_config.name}'")
                else:
                    # Legacy: read from token file
                    token_file = secret_config.token_file
                    token_path = Path(token_file)
                    if not token_path.exists():
                        logger.warning(f"Token file not found: {token_file}")
                        logger.info(
                            "Create the token file to enable secrets management")
                        if self.dry_run:
                            logger.info(
                                "✅ Dry run: Token file would be required")
                            continue
                        return False

                    try:
                        secret_value = self.get_instructor_token(token_file)
                        logger.debug(
                            f"Loaded secret value from file: {token_file}")
                    except Exception as e:
                        logger.error(
                            f"Failed to read token file {token_file}: {e}")
                        return False

                # Process all repositories for this secret
                results = self.process_batch_repos(
                    repo_urls,
                    secret_config.name,
                    secret_value,
                    secret_config.max_age_days,
                    force_update=force_update,
                    skip_validation=not secret_config.validate_format
                )

                if results["failed"] > 0:
                    logger.error(
                        f"Failed to add {secret_config.name} to some repositories")
                    return False

            logger.info("✅ Successfully added all secrets to repositories")
            return True

        except Exception as e:
            logger.error(f"Error adding secrets from global config: {e}")
            return False

    def _discover_repositories(self) -> List[str]:
        """
        Discover student repositories from GitHub Classroom assignment.

        Returns:
            List of repository URLs
        """
        try:
            # Validate required configuration
            if not self.global_config.classroom_url:
                logger.error(
                    "CLASSROOM_URL not configured - cannot discover repositories")
                return []

            if not self.global_config.github_organization:
                logger.error(
                    "GITHUB_ORGANIZATION not configured - cannot discover repositories")
                return []

            logger.info(
                "Starting repository auto-discovery using GitHub Classroom API")
            logger.info(f"Classroom URL: {self.global_config.classroom_url}")
            logger.info(
                f"Organization: {self.global_config.github_organization}")

            # Create GitHub Classroom API client
            try:
                classroom_api = create_classroom_api_client(self.github_token)
            except Exception as e:
                logger.error(
                    f"Failed to create GitHub Classroom API client: {e}")
                logger.error(
                    "Ensure your GitHub token has classroom scope permissions")
                return []

            # Discover student repositories
            repositories = classroom_api.discover_student_repositories(
                classroom_url=self.global_config.classroom_url,
                github_organization=self.global_config.github_organization,
                exclude_template=self.global_config.exclude_instructor_repos
            )

            if not repositories:
                logger.warning("No student repositories found")
                logger.info("This could be because:")
                logger.info(
                    "  - The assignment has no student submissions yet")
                logger.info(
                    "  - Your GitHub token lacks classroom scope permissions")
                logger.info(
                    "  - The classroom URL or organization is incorrect")
                return []

            logger.info(
                f"✅ Auto-discovered {len(repositories)} student repositories")

            # Log discovered repositories for debugging
            for i, repo_url in enumerate(repositories[:5]):  # Show first 5
                logger.debug(f"  {i+1}. {repo_url}")
            if len(repositories) > 5:
                logger.debug(f"  ... and {len(repositories) - 5} more")

            return repositories

        except GitHubClassroomAPIError as e:
            logger.error(f"GitHub Classroom API error: {e}")
            if e.status_code == 401:
                logger.error(
                    "Authentication failed - check your GitHub token permissions")
            elif e.status_code == 403:
                logger.error(
                    "Access denied - ensure your token has classroom scope")
            elif e.status_code == 404:
                logger.error(
                    "Assignment not found - check CLASSROOM_URL and GITHUB_ORGANIZATION")
            return []
        except Exception as e:
            logger.error(f"Unexpected error during repository discovery: {e}")
            return []


def add_secrets_to_students(
    config: Dict[str, str],
    secret_name: str = "INSTRUCTOR_TESTS_TOKEN",
    token_file: str = "instructor_token.txt",
    repo_urls: Optional[List[str]] = None,
    batch_file: Optional[str] = None,
    max_age_days: int = 90,
    force_update: bool = False,
    skip_validation: bool = False,
    dry_run: bool = False
) -> bool:
    """
    Main function to add secrets to student repositories.

    Args:
        config: Configuration from assignment.conf
        secret_name: Name of the secret to add
        token_file: Path to file containing secret value
        repo_urls: List of repository URLs to process
        batch_file: File containing repository URLs (one per line)
        max_age_days: Maximum age before updating secrets
        force_update: Force update regardless of age
        skip_validation: Skip GitHub token format validation
        dry_run: Show what would be done without executing

    Returns:
        True if all operations successful, False otherwise
    """
    try:
        manager = GitHubSecretsManager(config, dry_run=dry_run)

        # Get secret name from config if not provided
        if secret_name == "INSTRUCTOR_TESTS_TOKEN":
            secret_name = config.get("SECRET_NAME", "INSTRUCTOR_TESTS_TOKEN")

        # Determine which repositories to process
        urls_to_process = []

        if batch_file:
            # Read URLs from file
            batch_path = Path(batch_file)
            if not batch_path.exists():
                logger.error(f"Batch file not found: {batch_file}")
                return False

            with open(batch_path, "r") as f:
                urls_to_process = [
                    line.strip() for line in f if line.strip() and not line.startswith("#")]

        elif repo_urls:
            urls_to_process = repo_urls

        else:
            # Auto-discover from config following the real structure
            logger.info(
                "Processing secrets management from assignment configuration")

            # Check if secrets management is enabled
            if config.get("STEP_MANAGE_SECRETS", "true").lower() == "false":
                logger.info(
                    "Secret management is disabled (STEP_MANAGE_SECRETS=false)")
                return True

            # Parse SECRETS_CONFIG to understand what secrets to manage
            secrets_config = config.get("SECRETS_CONFIG", "").strip()
            if not secrets_config:
                logger.warning("SECRETS_CONFIG not found in configuration")
                logger.info("No secrets configuration found - nothing to do")
                return True

            # Parse the first secret configuration line
            # Format: SECRET_NAME:description:token_file_path:max_age_days:validate_format
            secret_lines = [line.strip()
                            for line in secrets_config.split('\n') if line.strip()]
            if not secret_lines:
                logger.warning(
                    "No secret configurations found in SECRETS_CONFIG")
                return True

            # Parse the first secret config (for now, support one secret)
            secret_config_parts = secret_lines[0].split(':')
            if len(secret_config_parts) >= 3:
                secret_name = secret_config_parts[0].strip()
                token_file = secret_config_parts[2].strip()
                max_age_days = int(secret_config_parts[3]) if len(
                    secret_config_parts) > 3 else 90
                skip_validation = not (secret_config_parts[4].lower(
                ) == "true" if len(secret_config_parts) > 4 else True)
            else:
                logger.error(
                    f"Invalid SECRETS_CONFIG format: {secret_lines[0]}")
                return False

            # Use INSTRUCTOR_TOKEN_FILE if specified
            instructor_token_file = config.get(
                "INSTRUCTOR_TOKEN_FILE", token_file)

            # Get GitHub organization
            github_org = config.get("GITHUB_ORGANIZATION")
            if not github_org:
                logger.error("GITHUB_ORGANIZATION not found in configuration")
                return False

            # Get classroom URL for future repository discovery
            classroom_url = config.get("CLASSROOM_URL")
            if not classroom_url:
                logger.error("CLASSROOM_URL not found in configuration")
                logger.info(
                    "CLASSROOM_URL is required for student repository discovery")
                return False

            logger.info("Configuration validated:")
            logger.info(f"  - Secret: {secret_name}")
            logger.info(f"  - Token file: {instructor_token_file}")
            logger.info(f"  - Organization: {github_org}")
            logger.info(f"  - Classroom URL: {classroom_url}")

            # Validate token file exists
            token_path = Path(instructor_token_file)
            if not token_path.exists():
                logger.warning(
                    f"Instructor token file not found: {instructor_token_file}")
                logger.info(
                    "Create the token file to enable secrets management")
                if dry_run:
                    logger.info("✅ Dry run: Configuration validation complete")
                return True

            # Validate token format
            try:
                token_value = manager.get_instructor_token(
                    instructor_token_file)
                if not manager.validate_token_format(token_value, skip_validation):
                    return False
                logger.info(f"✅ Token file validated: {instructor_token_file}")
            except Exception as e:
                logger.error(f"Token validation failed: {e}")
                return False

            # For now, we don't have specific repositories to process
            # TODO: Implement GitHub Classroom API integration to discover student repositories
            logger.warning(
                "Student repository auto-discovery not yet implemented")
            logger.info(
                "To process specific repositories, provide repo URLs or batch file")

            if dry_run:
                logger.info(
                    "✅ Dry run: Secrets management configuration is ready")
                logger.info(
                    "When repository discovery is implemented, secrets will be added to student repositories")

            return True

        if not urls_to_process:
            logger.warning("No repository URLs to process")
            return True

        # Process repositories
        if len(urls_to_process) == 1:
            # Single repository
            return manager.process_single_repo(
                urls_to_process[0], secret_name, token_file, max_age_days, force_update, skip_validation
            )
        else:
            # Multiple repositories
            results = manager.process_batch_repos(
                urls_to_process, secret_name, token_file, max_age_days, force_update, skip_validation
            )
            return results["failed"] == 0

    except Exception as e:
        logger.error(f"Failed to process secrets: {e}")
        return False
