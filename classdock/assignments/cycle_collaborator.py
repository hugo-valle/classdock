"""
Cycle Collaborator Management for GitHub Classroom Operations.

This module provides comprehensive collaborator permission cycling to fix GitHub Classroom
access issues. It intelligently detects when cycling is needed and safely restores
student access to their repositories.

Features:
- Intelligent access issue detection
- Safe collaborator permission cycling
- Batch processing for multiple students
- Force mode for manual override
- Comprehensive status reporting
- GitHub API integration with CLI fallback
"""

import json
import re
import subprocess
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple

from ..config.global_config import load_global_config
from ..utils import get_logger

logger = get_logger("assignments.cycle_collaborator")


class AccessStatus(Enum):
    """Repository access status enumeration."""
    OK = "ok"
    CORRUPTED = "corrupted"
    NOT_FOUND = "not_found"
    ACCESS_DENIED = "access_denied"
    UNKNOWN_ERROR = "unknown_error"


class CycleResult(Enum):
    """Collaborator cycling operation result."""
    SUCCESS = "success"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass
class RepositoryStatus:
    """Repository access status information."""
    repo_url: str
    username: str
    accessible: bool
    has_collaborator_access: bool
    has_pending_invitation: bool
    access_status: AccessStatus
    needs_cycling: bool
    error_message: Optional[str] = None


@dataclass
class CycleOperation:
    """Collaborator cycling operation result."""
    repo_url: str
    username: str
    result: CycleResult
    message: str
    actions_taken: List[str]
    error: Optional[str] = None


@dataclass
class BatchSummary:
    """Summary of batch cycling operations."""
    total_repositories: int
    successful_operations: int
    skipped_operations: int
    failed_operations: int
    repositories_fixed: int
    repositories_already_ok: int
    errors: List[str]


class CycleCollaboratorManager:
    """
    Manager for cycling collaborator permissions to fix repository access issues.

    This class handles the core functionality of collaborator permission cycling,
    providing intelligent detection of access issues and safe permission cycling.
    """

    def __init__(self, config_path: Optional[Path] = None, auto_confirm: bool = False):
        """
        Initialize the cycle collaborator manager.

        Args:
            config_path: Path to configuration file (defaults to assignment.conf)
            auto_confirm: Whether to skip confirmation prompts
        """
        self.config = load_global_config(config_path)
        self.auto_confirm = auto_confirm
        self.github_organization = self.config.github_organization
        self.assignment_prefix = self.config.assignment_name

    def validate_configuration(self) -> bool:
        """
        Validate that required configuration is available.

        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            if not self.github_organization:
                logger.error("GitHub organization not configured")
                return False

            if not self._check_github_authentication():
                logger.error("GitHub authentication not available")
                return False

            logger.info("Configuration validation passed")
            return True

        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False

    def _check_github_authentication(self) -> bool:
        """Check if GitHub CLI is authenticated."""
        try:
            subprocess.run(
                ['gh', 'auth', 'status'],
                capture_output=True,
                text=True,
                check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def check_repository_status(self, repo_url: str, username: str) -> RepositoryStatus:
        """
        Check the access status of a repository for a specific user.

        Args:
            repo_url: URL of the repository to check
            username: Username to check access for

        Returns:
            RepositoryStatus object with detailed status information
        """
        logger.info(
            f"Checking repository status: {repo_url} for user {username}")

        # Parse repository information
        try:
            owner, repo_name = self._parse_repository_url(repo_url)
        except ValueError as e:
            return RepositoryStatus(
                repo_url=repo_url,
                username=username,
                accessible=False,
                has_collaborator_access=False,
                has_pending_invitation=False,
                access_status=AccessStatus.UNKNOWN_ERROR,
                needs_cycling=False,
                error_message=str(e)
            )

        # Check repository accessibility
        accessible = self._check_repository_accessibility(owner, repo_name)
        if not accessible:
            return RepositoryStatus(
                repo_url=repo_url,
                username=username,
                accessible=False,
                has_collaborator_access=False,
                has_pending_invitation=False,
                access_status=AccessStatus.NOT_FOUND,
                needs_cycling=False,
                error_message="Repository not found or not accessible"
            )

        # Check collaborator access
        has_collaborator_access = self._check_collaborator_access(
            owner, repo_name, username)

        # Check pending invitations
        has_pending_invitation = self._check_pending_invitations(
            owner, repo_name, username)

        # Determine access status and cycling needs
        if has_collaborator_access:
            access_status = AccessStatus.OK
            needs_cycling = False
        elif has_pending_invitation:
            access_status = AccessStatus.CORRUPTED
            needs_cycling = True
        else:
            access_status = AccessStatus.CORRUPTED
            needs_cycling = True

        return RepositoryStatus(
            repo_url=repo_url,
            username=username,
            accessible=accessible,
            has_collaborator_access=has_collaborator_access,
            has_pending_invitation=has_pending_invitation,
            access_status=access_status,
            needs_cycling=needs_cycling
        )

    def _parse_repository_url(self, repo_url: str) -> Tuple[str, str]:
        """
        Parse repository URL to extract owner and repository name.

        Args:
            repo_url: GitHub repository URL

        Returns:
            Tuple of (owner, repository_name)

        Raises:
            ValueError: If URL format is invalid
        """
        # Handle various GitHub URL formats
        patterns = [
            r'https://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$',
            r'git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$',
        ]

        for pattern in patterns:
            match = re.match(pattern, repo_url.strip())
            if match:
                owner, repo_name = match.groups()
                return owner, repo_name

        raise ValueError(f"Invalid GitHub repository URL: {repo_url}")

    def _check_repository_accessibility(self, owner: str, repo_name: str) -> bool:
        """Check if repository exists and is accessible."""
        try:
            subprocess.run(
                ['gh', 'repo', 'view', f'{owner}/{repo_name}'],
                capture_output=True,
                text=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def _check_collaborator_access(self, owner: str, repo_name: str, username: str) -> bool:
        """Check if user is a collaborator on the repository."""
        try:
            subprocess.run(
                ['gh', 'api',
                    f'repos/{owner}/{repo_name}/collaborators/{username}'],
                capture_output=True,
                text=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def _check_pending_invitations(self, owner: str, repo_name: str, username: str) -> bool:
        """Check if user has pending invitations for the repository."""
        try:
            proc = subprocess.run(
                ['gh', 'api', f'repos/{owner}/{repo_name}/invitations'],
                capture_output=True,
                text=True,
                check=True
            )

            invitations = json.loads(proc.stdout)
            for invitation in invitations:
                if invitation.get('invitee', {}).get('login') == username:
                    return True
            return False
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            return False

    def cycle_single_repository(
        self,
        repo_url: str,
        username: str,
        force: bool = False
    ) -> CycleOperation:
        """
        Cycle collaborator permissions for a single repository.

        Args:
            repo_url: URL of the repository
            username: Username to cycle permissions for
            force: Whether to force cycling even if access appears correct

        Returns:
            CycleOperation with result details
        """
        logger.info(
            f"Cycling collaborator permissions: {repo_url} for {username}")

        actions_taken = []

        try:
            # Check current status
            status = self.check_repository_status(repo_url, username)

            if not status.accessible:
                return CycleOperation(
                    repo_url=repo_url,
                    username=username,
                    result=CycleResult.FAILED,
                    message="Repository not accessible",
                    actions_taken=actions_taken,
                    error=status.error_message
                )

            # Determine if cycling is needed
            if not status.needs_cycling and not force:
                return CycleOperation(
                    repo_url=repo_url,
                    username=username,
                    result=CycleResult.SKIPPED,
                    message="Repository access is already correct - no action needed",
                    actions_taken=actions_taken
                )

            # Parse repository info
            owner, repo_name = self._parse_repository_url(repo_url)

            # Remove existing collaborator access if present
            if status.has_collaborator_access:
                success = self._remove_collaborator(owner, repo_name, username)
                if success:
                    actions_taken.append(
                        "Removed existing collaborator access")
                else:
                    return CycleOperation(
                        repo_url=repo_url,
                        username=username,
                        result=CycleResult.FAILED,
                        message="Failed to remove existing collaborator access",
                        actions_taken=actions_taken,
                        error="Remove collaborator operation failed"
                    )

            # Add user back as collaborator with write permissions
            success = self._add_collaborator(
                owner, repo_name, username, "write")
            if success:
                actions_taken.append(
                    "Added user as collaborator with write permission")
                return CycleOperation(
                    repo_url=repo_url,
                    username=username,
                    result=CycleResult.SUCCESS,
                    message="Successfully cycled collaborator permissions - new invitation sent",
                    actions_taken=actions_taken
                )
            else:
                return CycleOperation(
                    repo_url=repo_url,
                    username=username,
                    result=CycleResult.FAILED,
                    message="Failed to add user as collaborator",
                    actions_taken=actions_taken,
                    error="Add collaborator operation failed"
                )

        except Exception as e:
            logger.error(f"Unexpected error cycling permissions: {e}")
            return CycleOperation(
                repo_url=repo_url,
                username=username,
                result=CycleResult.FAILED,
                message=f"Unexpected error: {e}",
                actions_taken=actions_taken,
                error=str(e)
            )

    def _remove_collaborator(self, owner: str, repo_name: str, username: str) -> bool:
        """Remove collaborator from repository."""
        try:
            subprocess.run(
                ['gh', 'api',
                    f'repos/{owner}/{repo_name}/collaborators/{username}', '--method', 'DELETE'],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(
                f"Successfully removed {username} from {owner}/{repo_name}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to remove collaborator: {e}")
            return False

    def _add_collaborator(self, owner: str, repo_name: str, username: str, permission: str = "write") -> bool:
        """Add collaborator to repository with specified permissions."""
        try:
            subprocess.run([
                'gh', 'api', f'repos/{owner}/{repo_name}/collaborators/{username}',
                '--method', 'PUT',
                '--field', f'permission={permission}'
            ], capture_output=True, text=True, check=True)

            logger.info(
                f"Successfully added {username} to {owner}/{repo_name} with {permission} permission")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to add collaborator: {e}")
            return False

    def cycle_multiple_repositories(
        self,
        repo_urls: List[str],
        username: str,
        force: bool = False
    ) -> List[CycleOperation]:
        """
        Cycle collaborator permissions for multiple repositories.

        Args:
            repo_urls: List of repository URLs
            username: Username to cycle permissions for
            force: Whether to force cycling even if access appears correct

        Returns:
            List of CycleOperation results
        """
        logger.info(
            f"Cycling permissions for {username} across {len(repo_urls)} repositories")

        results = []
        for repo_url in repo_urls:
            try:
                result = self.cycle_single_repository(
                    repo_url, username, force)
                results.append(result)

                # Brief delay between operations to avoid rate limiting
                time.sleep(0.5)

            except Exception as e:
                logger.error(f"Failed to process repository {repo_url}: {e}")
                results.append(CycleOperation(
                    repo_url=repo_url,
                    username=username,
                    result=CycleResult.FAILED,
                    message=f"Processing failed: {e}",
                    actions_taken=[],
                    error=str(e)
                ))

        return results

    def batch_cycle_from_file(
        self,
        batch_file_path: Path,
        repo_url_mode: bool = False,
        force: bool = False
    ) -> BatchSummary:
        """
        Process batch cycling operations from a file.

        Args:
            batch_file_path: Path to file containing repository URLs or usernames
            repo_url_mode: If True, file contains repo URLs; if False, contains usernames
            force: Whether to force cycling even if access appears correct

        Returns:
            BatchSummary with operation results
        """
        logger.info(f"Processing batch file: {batch_file_path}")

        if not batch_file_path.exists():
            raise FileNotFoundError(f"Batch file not found: {batch_file_path}")

        # Read and parse batch file
        lines = []
        with open(batch_file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    lines.append(line)

        if not lines:
            logger.warning("No valid entries found in batch file")
            return BatchSummary(
                total_repositories=0,
                successful_operations=0,
                skipped_operations=0,
                failed_operations=0,
                repositories_fixed=0,
                repositories_already_ok=0,
                errors=["No valid entries found in batch file"]
            )

        results = []
        errors = []

        for line in lines:
            try:
                # Auto-detect if line is a URL or username
                is_url = line.startswith('https://') or line.startswith('http://')

                if is_url or repo_url_mode:
                    # Process as repository URL with extracted username
                    repo_url = line
                    username = self._extract_username_from_repo_url(repo_url)
                    if username:
                        result = self.cycle_single_repository(
                            repo_url, username, force)
                        results.append(result)
                    else:
                        errors.append(
                            f"Could not extract username from URL: {repo_url}")
                else:
                    # Process as username with assignment prefix
                    if not self.assignment_prefix:
                        errors.append(
                            "Assignment prefix not configured for username mode")
                        continue

                    username = line
                    repo_url = f"https://github.com/{self.github_organization}/{self.assignment_prefix}-{username}"
                    result = self.cycle_single_repository(
                        repo_url, username, force)
                    results.append(result)
            except Exception as e:
                logger.error(f"Failed to process entry {line}: {e}")
                errors.append(f"Failed to process {line}: {e}")

        # Generate summary
        successful = len(
            [r for r in results if r.result == CycleResult.SUCCESS])
        skipped = len([r for r in results if r.result == CycleResult.SKIPPED])
        failed = len([r for r in results if r.result == CycleResult.FAILED])

        return BatchSummary(
            total_repositories=len(results),
            successful_operations=successful,
            skipped_operations=skipped,
            failed_operations=failed,
            repositories_fixed=successful,
            repositories_already_ok=skipped,
            errors=errors
        )

    def _extract_username_from_repo_url(self, repo_url: str) -> Optional[str]:
        """
        Extract username from repository URL based on common naming patterns.

        Args:
            repo_url: Repository URL

        Returns:
            Extracted username or None if extraction fails
        """
        try:
            owner, repo_name = self._parse_repository_url(repo_url)

            # Try to extract username from repository name
            # Common patterns: assignment-username, assignment1-username, etc.
            if self.assignment_prefix and repo_name.startswith(self.assignment_prefix):
                # Remove assignment prefix and any following dash
                username = repo_name[len(self.assignment_prefix):].lstrip('-')
                if username:
                    return username

            # Fallback: use the part after the last dash
            if '-' in repo_name:
                return repo_name.split('-')[-1]

            return None

        except ValueError:
            return None

    def display_repository_status(self, status: RepositoryStatus) -> None:
        """Display repository status information in a user-friendly format."""
        print("\n=== Repository Status ===")
        print(f"Repository: {status.repo_url}")
        print(f"Student: {status.username}")
        print(f"Accessible: {'✅ Yes' if status.accessible else '❌ No'}")

        if status.accessible:
            print(
                f"Collaborator Access: {'✅ Yes' if status.has_collaborator_access else '❌ No'}")
            print(
                f"Pending Invitation: {'⏳ Yes' if status.has_pending_invitation else '✅ No'}")
            print(
                f"Status: {'✅ OK' if status.access_status == AccessStatus.OK else '🚨 CORRUPTED'}")
            print(
                f"Needs Cycling: {'🔄 Yes' if status.needs_cycling else '✅ No'}")

        if status.error_message:
            print(f"Error: {status.error_message}")

    def display_cycle_result(self, result: CycleOperation) -> None:
        """Display cycle operation result in a user-friendly format."""
        print("\n=== Cycle Operation Result ===")
        print(f"Repository: {result.repo_url}")
        print(f"Student: {result.username}")

        if result.result == CycleResult.SUCCESS:
            print("Result: ✅ SUCCESS")
        elif result.result == CycleResult.SKIPPED:
            print("Result: ⏭️ SKIPPED")
        else:
            print("Result: ❌ FAILED")

        print(f"Message: {result.message}")

        if result.actions_taken:
            print("Actions Taken:")
            for action in result.actions_taken:
                print(f"  • {action}")

        if result.error:
            print(f"Error Details: {result.error}")

    def display_batch_summary(self, summary: BatchSummary) -> None:
        """Display batch operation summary in a user-friendly format."""
        print("\n=== Batch Operation Summary ===")
        print(f"Total Repositories: {summary.total_repositories}")
        print(f"Successful Operations: {summary.successful_operations}")
        print(f"Skipped Operations: {summary.skipped_operations}")
        print(f"Failed Operations: {summary.failed_operations}")
        print(f"Repositories Fixed: {summary.repositories_fixed}")
        print(f"Repositories Already OK: {summary.repositories_already_ok}")

        if summary.errors:
            print(f"\nErrors ({len(summary.errors)}):")
            for error in summary.errors:
                print(f"  • {error}")
