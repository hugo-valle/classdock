"""
Template to Classroom Repository Push Manager.

This module provides Python-based template repository synchronization
handling with GitHub Classroom repositories.
"""

import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple

from ..config import GlobalConfig
from ..utils import get_logger

logger = get_logger("assignments.push_manager")


class PushResult(Enum):
    """Results of push operations."""
    SUCCESS = "success"
    UP_TO_DATE = "up_to_date"
    CANCELLED = "cancelled"
    REPOSITORY_ERROR = "repository_error"
    CONFIGURATION_ERROR = "configuration_error"
    GIT_ERROR = "git_error"
    PERMISSION_ERROR = "permission_error"
    NETWORK_ERROR = "network_error"


@dataclass
class GitCommitInfo:
    """Information about a git commit."""
    hash: str
    short_hash: str
    message: str
    author: str
    date: str

    @classmethod
    def from_hash(cls, commit_hash: str) -> 'GitCommitInfo':
        """Create GitCommitInfo from commit hash."""
        try:
            # Get commit information
            result = subprocess.run([
                'git', 'show', '--format=%H%n%h%n%s%n%an%n%ad', '--no-patch', commit_hash
            ], capture_output=True, text=True, check=True)

            lines = result.stdout.strip().split('\n')
            return cls(
                hash=lines[0],
                short_hash=lines[1],
                message=lines[2],
                author=lines[3],
                date=lines[4]
            )
        except Exception:
            return cls(
                hash=commit_hash,
                short_hash=commit_hash[:8] if len(
                    commit_hash) >= 8 else commit_hash,
                message="Unknown",
                author="Unknown",
                date="Unknown"
            )


@dataclass
class RepositoryState:
    """State information about git repositories."""
    local_commit: GitCommitInfo
    classroom_commit: Optional[GitCommitInfo]
    is_in_sync: bool
    files_changed: List[str]
    force_required: bool


@dataclass
class PushValidationResult:
    """Result of push validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]

    @property
    def has_errors(self) -> bool:
        """Check if validation has errors."""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if validation has warnings."""
        return len(self.warnings) > 0


class ClassroomPushManager:
    """Manages pushing template changes to GitHub Classroom repositories."""

    def __init__(self, global_config: Optional[GlobalConfig] = None, assignment_root: Optional[Path] = None):
        """Initialize push manager with configuration."""
        self.global_config = global_config or GlobalConfig()
        self.assignment_root = assignment_root or Path.cwd()

        # Configuration constants
        self.classroom_remote = "classroom"
        self.branch = "main"

    def _run_git_command(self, args: List[str], cwd: Optional[Path] = None,
                         check: bool = True, capture_output: bool = True) -> subprocess.CompletedProcess:
        """Run git command with error handling."""
        try:
            return subprocess.run(
                ['git'] + args,
                cwd=cwd or self.assignment_root,
                capture_output=capture_output,
                text=True,
                check=check,
                timeout=30
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: git {' '.join(args)}")
            logger.error(f"Exit code: {e.returncode}")
            logger.error(f"Stderr: {e.stderr}")
            raise
        except subprocess.TimeoutExpired:
            logger.error(f"Git command timed out: git {' '.join(args)}")
            raise

    def validate_repository(self) -> PushValidationResult:
        """Validate that we're in a proper template repository."""
        errors = []
        warnings = []

        # Check if we're in a git repository
        git_dir = self.assignment_root / ".git"
        if not git_dir.exists():
            errors.append(f"Not in a git repository: {self.assignment_root}")
            return PushValidationResult(False, errors, warnings)

        # Check if assignment file exists
        assignment_file = getattr(self.global_config, 'assignment_file', None)
        if not assignment_file:
            # Try common defaults
            for default_file in ['assignment.ipynb', 'assignment.py', 'README.md']:
                if (self.assignment_root / default_file).exists():
                    assignment_file = default_file
                    warnings.append(
                        f"Using detected assignment file: {assignment_file}")
                    break

        if assignment_file and not (self.assignment_root / assignment_file).exists():
            errors.append(f"Assignment file not found: {assignment_file}")
            errors.append("This doesn't appear to be the template repository")
        elif not assignment_file:
            warnings.append("No assignment file specified in configuration")

        # Check if classroom repository URL is configured
        classroom_url = getattr(self.global_config, 'classroom_repo_url', None)
        if not classroom_url:
            errors.append("CLASSROOM_REPO_URL is not set in configuration")
            errors.append(
                "Please add the GitHub Classroom repository URL to your assignment.conf:")
            errors.append(
                'CLASSROOM_REPO_URL="https://github.com/ORG/classroom-semester-assignment-name"')

        return PushValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def check_working_tree_clean(self) -> PushValidationResult:
        """Check if working tree is clean (no uncommitted changes)."""
        errors = []
        warnings = []

        try:
            # Check for uncommitted changes
            result = self._run_git_command(['status', '--porcelain'])

            if result.stdout.strip():
                errors.append(
                    "You have uncommitted changes in your working directory")
                errors.append(
                    "Please commit or stash your changes before pushing")

                # Show the status
                status_result = self._run_git_command(['status', '--short'])
                if status_result.stdout:
                    errors.append(
                        f"Uncommitted changes:\n{status_result.stdout}")

        except Exception as e:
            errors.append(f"Failed to check working tree status: {e}")

        return PushValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def setup_classroom_remote(self) -> Tuple[bool, str]:
        """Setup or update classroom remote."""
        try:
            classroom_url = getattr(
                self.global_config, 'classroom_repo_url', None)
            if not classroom_url:
                return False, "Classroom repository URL not configured"

            # Check if remote exists
            result = self._run_git_command(['remote'], check=False)
            remotes = result.stdout.strip().split('\n') if result.stdout.strip() else []

            if self.classroom_remote in remotes:
                # Update existing remote URL
                self._run_git_command(
                    ['remote', 'set-url', self.classroom_remote, classroom_url])
                logger.info(f"Updated {self.classroom_remote} remote URL")
            else:
                # Add new remote
                self._run_git_command(
                    ['remote', 'add', self.classroom_remote, classroom_url])
                logger.info(f"Added {self.classroom_remote} remote")

            return True, f"Classroom remote configured: {classroom_url}"

        except Exception as e:
            return False, f"Failed to setup classroom remote: {e}"

    def fetch_classroom_repository(self) -> Tuple[bool, str]:
        """Fetch latest state from classroom repository."""
        try:
            logger.info("Fetching classroom repository state...")
            self._run_git_command(['fetch', self.classroom_remote])
            return True, "Successfully fetched classroom repository"

        except subprocess.CalledProcessError as e:
            if "fatal: couldn't find remote ref" in e.stderr.lower():
                return True, "Classroom repository appears to be empty or newly created"
            return False, f"Failed to fetch classroom repository: {e.stderr}"
        except Exception as e:
            return False, f"Failed to fetch classroom repository: {e}"

    def get_repository_state(self) -> RepositoryState:
        """Get current state comparison between local and classroom repositories."""
        try:
            # Get local commit
            local_result = self._run_git_command(['rev-parse', self.branch])
            local_commit_hash = local_result.stdout.strip()
            local_commit = GitCommitInfo.from_hash(local_commit_hash)

            # Try to get classroom commit
            classroom_commit = None
            try:
                classroom_result = self._run_git_command(
                    ['rev-parse', f'{self.classroom_remote}/{self.branch}'],
                    check=False
                )
                if classroom_result.returncode == 0:
                    classroom_commit_hash = classroom_result.stdout.strip()
                    classroom_commit = GitCommitInfo.from_hash(
                        classroom_commit_hash)
            except Exception:
                pass  # Classroom branch doesn't exist yet

            # Check if repositories are in sync
            is_in_sync = (classroom_commit and
                          local_commit.hash == classroom_commit.hash)

            # Get list of changed files
            files_changed = []
            if classroom_commit:
                try:
                    diff_result = self._run_git_command([
                        'diff', '--name-only',
                        f'{self.classroom_remote}/{self.branch}..{self.branch}'
                    ], check=False)
                    if diff_result.returncode == 0:
                        files_changed = [
                            line.strip() for line in diff_result.stdout.splitlines()
                            if line.strip()
                        ]
                except Exception:
                    pass

            # Check if force push is required
            force_required = False
            if classroom_commit:
                try:
                    # Check if classroom branch is ancestor of local branch
                    merge_base_result = self._run_git_command([
                        'merge-base', '--is-ancestor',
                        f'{self.classroom_remote}/{self.branch}', self.branch
                    ], check=False)
                    force_required = merge_base_result.returncode != 0
                except Exception:
                    force_required = True  # Assume force needed if we can't determine

            return RepositoryState(
                local_commit=local_commit,
                classroom_commit=classroom_commit,
                is_in_sync=is_in_sync,
                files_changed=files_changed,
                force_required=force_required
            )

        except Exception as e:
            logger.error(f"Failed to get repository state: {e}")
            raise

    def show_changes_summary(self, state: RepositoryState) -> str:
        """Generate a summary of changes to be pushed."""
        summary = []

        summary.append("Repository Comparison:")
        summary.append(
            f"  Local commit:     {state.local_commit.short_hash} - {state.local_commit.message}")

        if state.classroom_commit:
            summary.append(
                f"  Classroom commit: {state.classroom_commit.short_hash} - {state.classroom_commit.message}")
        else:
            summary.append(
                "  Classroom commit: none (empty or new repository)")

        if state.is_in_sync:
            summary.append("\n✅ Repositories are already in sync!")
            return "\n".join(summary)

        if state.files_changed:
            summary.append(
                f"\nFiles to be updated ({len(state.files_changed)}):")
            for file_path in state.files_changed[:10]:  # Show first 10 files
                summary.append(f"  - {file_path}")
            if len(state.files_changed) > 10:
                summary.append(
                    f"  ... and {len(state.files_changed) - 10} more files")
        elif not state.classroom_commit:
            summary.append(
                "\n📝 This appears to be the first push to classroom repository")

        if state.force_required:
            summary.append(
                "\n⚠️  Force push will be required (histories have diverged)")

        return "\n".join(summary)

    def push_to_classroom(self, force: bool = False) -> Tuple[PushResult, str]:
        """Push changes to classroom repository."""
        try:
            logger.info("Pushing changes to classroom repository...")

            # Get current state to determine if force is needed
            state = self.get_repository_state()

            # Prepare push arguments
            push_args = [self.classroom_remote, self.branch]
            if force or state.force_required:
                push_args.append('--force')
                logger.warning("Using force push")

            # Execute push
            result = self._run_git_command(['push'] + push_args)

            if result.returncode == 0:
                return PushResult.SUCCESS, "Successfully pushed changes to classroom repository"
            else:
                return PushResult.GIT_ERROR, f"Push failed: {result.stderr}"

        except subprocess.CalledProcessError as e:
            if "permission denied" in e.stderr.lower() or "access denied" in e.stderr.lower():
                return PushResult.PERMISSION_ERROR, f"Permission denied: {e.stderr}"
            elif "network" in e.stderr.lower() or "connection" in e.stderr.lower():
                return PushResult.NETWORK_ERROR, f"Network error: {e.stderr}"
            else:
                return PushResult.GIT_ERROR, f"Git error: {e.stderr}"
        except Exception as e:
            return PushResult.GIT_ERROR, f"Unexpected error: {e}"

    def verify_push(self) -> Tuple[bool, str]:
        """Verify that push was successful by comparing commits."""
        try:
            logger.info("Verifying push was successful...")

            # Fetch latest state
            self._run_git_command(['fetch', self.classroom_remote])

            # Get current state
            state = self.get_repository_state()

            if state.is_in_sync:
                return True, "Verification passed - repositories are now in sync"
            else:
                return False, "Verification failed - commits don't match after push"

        except Exception as e:
            return False, f"Failed to verify push: {e}"

    def get_next_steps_guidance(self) -> str:
        """Generate guidance for next steps after successful push."""
        classroom_url = getattr(
            self.global_config, 'classroom_repo_url', 'N/A')

        guidance = []
        guidance.append("📋 Next Steps:")
        guidance.append("")
        guidance.append("1. Announce the update to students via:")
        guidance.append("   - Course announcement")
        guidance.append("   - Email notification")
        guidance.append("   - Canvas/LMS message")
        guidance.append("")
        guidance.append(
            "2. Direct students to update their repositories using:")
        guidance.append(
            "   - Automated update: classdock assignments update")
        guidance.append("   - Manual process: docs/UPDATE-GUIDE.md")
        guidance.append("")
        guidance.append("3. Monitor for student questions and provide support")
        guidance.append("")
        guidance.append(
            "4. Check that student tests still pass with the updates")
        guidance.append("")
        guidance.append(f"🔗 Classroom repository: {classroom_url}")

        return "\n".join(guidance)

    def execute_push_workflow(self, force: bool = False, interactive: bool = True) -> Tuple[PushResult, str]:
        """Execute the complete push workflow."""
        try:
            # Step 1: Validate repository
            logger.info("Validating repository...")
            repo_validation = self.validate_repository()
            if not repo_validation.is_valid:
                return PushResult.REPOSITORY_ERROR, "\n".join(repo_validation.errors)

            if repo_validation.has_warnings:
                for warning in repo_validation.warnings:
                    logger.warning(warning)

            # Step 2: Check working tree
            logger.info("Checking for uncommitted changes...")
            tree_validation = self.check_working_tree_clean()
            if not tree_validation.is_valid:
                return PushResult.GIT_ERROR, "\n".join(tree_validation.errors)

            # Step 3: Setup classroom remote
            logger.info("Setting up classroom remote...")
            remote_success, remote_message = self.setup_classroom_remote()
            if not remote_success:
                return PushResult.CONFIGURATION_ERROR, remote_message

            # Step 4: Fetch classroom repository
            logger.info("Fetching classroom repository...")
            fetch_success, fetch_message = self.fetch_classroom_repository()
            if not fetch_success:
                return PushResult.NETWORK_ERROR, fetch_message

            # Step 5: Compare repositories
            logger.info("Comparing repositories...")
            state = self.get_repository_state()

            if state.is_in_sync:
                return PushResult.UP_TO_DATE, "Repositories are already in sync - no changes to push"

            # Step 6: Show changes (if interactive)
            changes_summary = self.show_changes_summary(state)
            logger.info(f"Changes to be pushed:\n{changes_summary}")

            # Step 7: Confirm (if interactive and not force)
            if interactive and not force:
                try:
                    response = input(
                        "\nDo you want to push these changes to the classroom repository? [y/N] ")
                    if response.lower() not in ['y', 'yes']:
                        return PushResult.CANCELLED, "Operation cancelled by user"
                except (EOFError, KeyboardInterrupt):
                    return PushResult.CANCELLED, "Operation cancelled by user"

            # Step 8: Push changes
            logger.info("Pushing to classroom repository...")
            push_result, push_message = self.push_to_classroom(force)
            if push_result != PushResult.SUCCESS:
                return push_result, push_message

            # Step 9: Verify push
            logger.info("Verifying push...")
            verify_success, verify_message = self.verify_push()
            if not verify_success:
                return PushResult.GIT_ERROR, verify_message

            # Step 10: Return success with guidance
            success_message = f"{push_message}\n\n{self.get_next_steps_guidance()}"
            return PushResult.SUCCESS, success_message

        except KeyboardInterrupt:
            return PushResult.CANCELLED, "Operation cancelled by user"
        except Exception as e:
            logger.error(f"Unexpected error in push workflow: {e}")
            return PushResult.GIT_ERROR, f"Unexpected error: {e}"
