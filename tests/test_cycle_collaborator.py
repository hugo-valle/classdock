"""
Comprehensive test suite for classdock.assignments.cycle_collaborator module.

This test suite provides complete coverage for the CycleCollaboratorManager class,
including unit tests for individual methods, integration tests for cycling workflows,
error handling scenarios, and batch processing operations.
"""

import json
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

from classdock.assignments.cycle_collaborator import (
    CycleCollaboratorManager,
    AccessStatus,
    CycleResult,
    RepositoryStatus,
    CycleOperation,
    BatchSummary
)


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    config = Mock()
    config.github_organization = "test-org"
    config.assignment_name = "assignment1"
    return config


@pytest.fixture
def cycle_manager(mock_config):
    """Create CycleCollaboratorManager instance with mocked dependencies."""
    with patch('classdock.assignments.cycle_collaborator.load_global_config') as mock_load_config:
        mock_load_config.return_value = mock_config
        manager = CycleCollaboratorManager(auto_confirm=True)
        return manager


class TestCycleCollaboratorManager:
    """Test cases for CycleCollaboratorManager class."""

    def test_initialization(self, mock_config):
        """Test manager initialization."""
        with patch('classdock.assignments.cycle_collaborator.load_global_config') as mock_load_config:
            mock_load_config.return_value = mock_config

            manager = CycleCollaboratorManager(auto_confirm=True)

            assert manager.auto_confirm is True
            assert manager.github_organization == "test-org"
            assert manager.assignment_prefix == "assignment1"

    @patch('subprocess.run')
    def test_validate_configuration_success(self, mock_run, cycle_manager):
        """Test successful configuration validation."""
        # Mock successful auth check
        mock_run.return_value = Mock(returncode=0)

        result = cycle_manager.validate_configuration()

        assert result is True
        mock_run.assert_called_once_with(
            ['gh', 'auth', 'status'],
            capture_output=True,
            text=True,
            check=True
        )

    @patch('subprocess.run')
    def test_validate_configuration_no_auth(self, mock_run, cycle_manager):
        """Test configuration validation with no GitHub auth."""
        # Mock failed auth check
        mock_run.side_effect = subprocess.CalledProcessError(
            1, 'gh auth status')

        result = cycle_manager.validate_configuration()

        assert result is False

    def test_validate_configuration_no_organization(self, cycle_manager):
        """Test configuration validation with missing organization."""
        cycle_manager.github_organization = None

        result = cycle_manager.validate_configuration()

        assert result is False

    def test_parse_repository_url_https(self, cycle_manager):
        """Test parsing HTTPS repository URLs."""
        test_cases = [
            ("https://github.com/owner/repo", ("owner", "repo")),
            ("https://github.com/owner/repo.git", ("owner", "repo")),
            ("https://github.com/owner/repo/", ("owner", "repo")),
            ("https://github.com/test-org/assignment1-student",
             ("test-org", "assignment1-student")),
        ]

        for url, expected in test_cases:
            result = cycle_manager._parse_repository_url(url)
            assert result == expected

    def test_parse_repository_url_ssh(self, cycle_manager):
        """Test parsing SSH repository URLs."""
        test_cases = [
            ("git@github.com:owner/repo", ("owner", "repo")),
            ("git@github.com:owner/repo.git", ("owner", "repo")),
        ]

        for url, expected in test_cases:
            result = cycle_manager._parse_repository_url(url)
            assert result == expected

    def test_parse_repository_url_invalid(self, cycle_manager):
        """Test parsing invalid repository URLs."""
        invalid_urls = [
            "not-a-url",
            "https://gitlab.com/owner/repo",
            "https://github.com/owner",
            "",
        ]

        for url in invalid_urls:
            with pytest.raises(ValueError):
                cycle_manager._parse_repository_url(url)

    @patch('subprocess.run')
    def test_check_repository_accessibility_success(self, mock_run, cycle_manager):
        """Test successful repository accessibility check."""
        mock_run.return_value = Mock(returncode=0)

        result = cycle_manager._check_repository_accessibility("owner", "repo")

        assert result is True
        mock_run.assert_called_once_with(
            ['gh', 'repo', 'view', 'owner/repo'],
            capture_output=True,
            text=True,
            check=True
        )

    @patch('subprocess.run')
    def test_check_repository_accessibility_failure(self, mock_run, cycle_manager):
        """Test repository accessibility check failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, 'gh repo view')

        result = cycle_manager._check_repository_accessibility("owner", "repo")

        assert result is False

    @patch('subprocess.run')
    def test_check_collaborator_access_success(self, mock_run, cycle_manager):
        """Test successful collaborator access check."""
        mock_run.return_value = Mock(returncode=0)

        result = cycle_manager._check_collaborator_access(
            "owner", "repo", "user")

        assert result is True
        mock_run.assert_called_once_with(
            ['gh', 'api', 'repos/owner/repo/collaborators/user'],
            capture_output=True,
            text=True,
            check=True
        )

    @patch('subprocess.run')
    def test_check_collaborator_access_failure(self, mock_run, cycle_manager):
        """Test collaborator access check failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, 'gh api')

        result = cycle_manager._check_collaborator_access(
            "owner", "repo", "user")

        assert result is False

    @patch('subprocess.run')
    def test_check_pending_invitations_with_pending(self, mock_run, cycle_manager):
        """Test pending invitations check with pending invitation."""
        mock_response = json.dumps([
            {"invitee": {"login": "user"}, "id": 123},
            {"invitee": {"login": "other"}, "id": 124}
        ])
        mock_run.return_value = Mock(stdout=mock_response, returncode=0)

        result = cycle_manager._check_pending_invitations(
            "owner", "repo", "user")

        assert result is True

    @patch('subprocess.run')
    def test_check_pending_invitations_no_pending(self, mock_run, cycle_manager):
        """Test pending invitations check with no pending invitation."""
        mock_response = json.dumps([
            {"invitee": {"login": "other"}, "id": 124}
        ])
        mock_run.return_value = Mock(stdout=mock_response, returncode=0)

        result = cycle_manager._check_pending_invitations(
            "owner", "repo", "user")

        assert result is False

    @patch('subprocess.run')
    def test_check_pending_invitations_api_failure(self, mock_run, cycle_manager):
        """Test pending invitations check with API failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, 'gh api')

        result = cycle_manager._check_pending_invitations(
            "owner", "repo", "user")

        assert result is False

    def test_check_repository_status_ok(self, cycle_manager):
        """Test repository status check for working repository."""
        with patch.object(cycle_manager, '_check_repository_accessibility', return_value=True), \
                patch.object(cycle_manager, '_check_collaborator_access', return_value=True), \
                patch.object(cycle_manager, '_check_pending_invitations', return_value=False):

            status = cycle_manager.check_repository_status(
                "https://github.com/owner/repo", "user"
            )

            assert status.accessible is True
            assert status.has_collaborator_access is True
            assert status.has_pending_invitation is False
            assert status.access_status == AccessStatus.OK
            assert status.needs_cycling is False

    def test_check_repository_status_corrupted(self, cycle_manager):
        """Test repository status check for corrupted repository."""
        with patch.object(cycle_manager, '_check_repository_accessibility', return_value=True), \
                patch.object(cycle_manager, '_check_collaborator_access', return_value=False), \
                patch.object(cycle_manager, '_check_pending_invitations', return_value=False):

            status = cycle_manager.check_repository_status(
                "https://github.com/owner/repo", "user"
            )

            assert status.accessible is True
            assert status.has_collaborator_access is False
            assert status.has_pending_invitation is False
            assert status.access_status == AccessStatus.CORRUPTED
            assert status.needs_cycling is True

    def test_check_repository_status_not_found(self, cycle_manager):
        """Test repository status check for non-existent repository."""
        with patch.object(cycle_manager, '_check_repository_accessibility', return_value=False):

            status = cycle_manager.check_repository_status(
                "https://github.com/owner/repo", "user"
            )

            assert status.accessible is False
            assert status.access_status == AccessStatus.NOT_FOUND
            assert status.needs_cycling is False

    def test_check_repository_status_invalid_url(self, cycle_manager):
        """Test repository status check with invalid URL."""
        status = cycle_manager.check_repository_status("invalid-url", "user")

        assert status.accessible is False
        assert status.access_status == AccessStatus.UNKNOWN_ERROR
        assert status.needs_cycling is False
        assert "Invalid GitHub repository URL" in status.error_message

    @patch('subprocess.run')
    def test_remove_collaborator_success(self, mock_run, cycle_manager):
        """Test successful collaborator removal."""
        mock_run.return_value = Mock(returncode=0)

        result = cycle_manager._remove_collaborator("owner", "repo", "user")

        assert result is True
        mock_run.assert_called_once_with(
            ['gh', 'api', 'repos/owner/repo/collaborators/user', '--method', 'DELETE'],
            capture_output=True,
            text=True,
            check=True
        )

    @patch('subprocess.run')
    def test_remove_collaborator_failure(self, mock_run, cycle_manager):
        """Test collaborator removal failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, 'gh api')

        result = cycle_manager._remove_collaborator("owner", "repo", "user")

        assert result is False

    @patch('subprocess.run')
    def test_add_collaborator_success(self, mock_run, cycle_manager):
        """Test successful collaborator addition."""
        mock_run.return_value = Mock(returncode=0)

        result = cycle_manager._add_collaborator(
            "owner", "repo", "user", "write")

        assert result is True
        mock_run.assert_called_once_with([
            'gh', 'api', 'repos/owner/repo/collaborators/user',
            '--method', 'PUT',
            '--field', 'permission=write'
        ], capture_output=True, text=True, check=True)

    @patch('subprocess.run')
    def test_add_collaborator_failure(self, mock_run, cycle_manager):
        """Test collaborator addition failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, 'gh api')

        result = cycle_manager._add_collaborator(
            "owner", "repo", "user", "write")

        assert result is False

    def test_cycle_single_repository_already_ok(self, cycle_manager):
        """Test cycling when repository access is already OK."""
        mock_status = RepositoryStatus(
            repo_url="https://github.com/owner/repo",
            username="user",
            accessible=True,
            has_collaborator_access=True,
            has_pending_invitation=False,
            access_status=AccessStatus.OK,
            needs_cycling=False
        )

        with patch.object(cycle_manager, 'check_repository_status', return_value=mock_status):
            result = cycle_manager.cycle_single_repository(
                "https://github.com/owner/repo", "user"
            )

            assert result.result == CycleResult.SKIPPED
            assert "already correct" in result.message
            assert len(result.actions_taken) == 0

    def test_cycle_single_repository_force_mode(self, cycle_manager):
        """Test cycling with force mode enabled."""
        mock_status = RepositoryStatus(
            repo_url="https://github.com/owner/repo",
            username="user",
            accessible=True,
            has_collaborator_access=True,
            has_pending_invitation=False,
            access_status=AccessStatus.OK,
            needs_cycling=False
        )

        with patch.object(cycle_manager, 'check_repository_status', return_value=mock_status), \
                patch.object(cycle_manager, '_remove_collaborator', return_value=True), \
                patch.object(cycle_manager, '_add_collaborator', return_value=True):

            result = cycle_manager.cycle_single_repository(
                "https://github.com/owner/repo", "user", force=True
            )

            assert result.result == CycleResult.SUCCESS
            assert len(result.actions_taken) == 2
            assert "Removed existing collaborator access" in result.actions_taken
            assert "Added user as collaborator" in result.actions_taken[1]

    def test_cycle_single_repository_corrupted_access(self, cycle_manager):
        """Test cycling when repository access is corrupted."""
        mock_status = RepositoryStatus(
            repo_url="https://github.com/owner/repo",
            username="user",
            accessible=True,
            has_collaborator_access=False,
            has_pending_invitation=False,
            access_status=AccessStatus.CORRUPTED,
            needs_cycling=True
        )

        with patch.object(cycle_manager, 'check_repository_status', return_value=mock_status), \
                patch.object(cycle_manager, '_add_collaborator', return_value=True):

            result = cycle_manager.cycle_single_repository(
                "https://github.com/owner/repo", "user"
            )

            assert result.result == CycleResult.SUCCESS
            assert len(result.actions_taken) == 1
            assert "Added user as collaborator" in result.actions_taken[0]

    def test_cycle_single_repository_not_accessible(self, cycle_manager):
        """Test cycling when repository is not accessible."""
        mock_status = RepositoryStatus(
            repo_url="https://github.com/owner/repo",
            username="user",
            accessible=False,
            has_collaborator_access=False,
            has_pending_invitation=False,
            access_status=AccessStatus.NOT_FOUND,
            needs_cycling=False,
            error_message="Repository not found"
        )

        with patch.object(cycle_manager, 'check_repository_status', return_value=mock_status):
            result = cycle_manager.cycle_single_repository(
                "https://github.com/owner/repo", "user"
            )

            assert result.result == CycleResult.FAILED
            assert "Repository not accessible" in result.message
            assert result.error == "Repository not found"

    def test_cycle_single_repository_remove_failure(self, cycle_manager):
        """Test cycling when removing collaborator fails."""
        mock_status = RepositoryStatus(
            repo_url="https://github.com/owner/repo",
            username="user",
            accessible=True,
            has_collaborator_access=True,
            has_pending_invitation=False,
            access_status=AccessStatus.OK,
            needs_cycling=False
        )

        with patch.object(cycle_manager, 'check_repository_status', return_value=mock_status), \
                patch.object(cycle_manager, '_remove_collaborator', return_value=False):

            result = cycle_manager.cycle_single_repository(
                "https://github.com/owner/repo", "user", force=True
            )

            assert result.result == CycleResult.FAILED
            assert "Failed to remove existing collaborator access" in result.message

    def test_cycle_single_repository_add_failure(self, cycle_manager):
        """Test cycling when adding collaborator fails."""
        mock_status = RepositoryStatus(
            repo_url="https://github.com/owner/repo",
            username="user",
            accessible=True,
            has_collaborator_access=False,
            has_pending_invitation=False,
            access_status=AccessStatus.CORRUPTED,
            needs_cycling=True
        )

        with patch.object(cycle_manager, 'check_repository_status', return_value=mock_status), \
                patch.object(cycle_manager, '_add_collaborator', return_value=False):

            result = cycle_manager.cycle_single_repository(
                "https://github.com/owner/repo", "user"
            )

            assert result.result == CycleResult.FAILED
            assert "Failed to add user as collaborator" in result.message

    @patch('time.sleep')
    def test_cycle_multiple_repositories(self, mock_sleep, cycle_manager):
        """Test cycling multiple repositories."""
        repo_urls = [
            "https://github.com/owner/repo1",
            "https://github.com/owner/repo2"
        ]

        mock_result1 = CycleOperation(
            repo_url=repo_urls[0],
            username="user",
            result=CycleResult.SUCCESS,
            message="Success",
            actions_taken=["Added user"]
        )

        mock_result2 = CycleOperation(
            repo_url=repo_urls[1],
            username="user",
            result=CycleResult.SKIPPED,
            message="Already OK",
            actions_taken=[]
        )

        with patch.object(cycle_manager, 'cycle_single_repository', side_effect=[mock_result1, mock_result2]):
            results = cycle_manager.cycle_multiple_repositories(
                repo_urls, "user")

            assert len(results) == 2
            assert results[0].result == CycleResult.SUCCESS
            assert results[1].result == CycleResult.SKIPPED
            assert mock_sleep.call_count == 2  # Sleep between operations

    def test_extract_username_from_repo_url_with_prefix(self, cycle_manager):
        """Test username extraction from repository URL with assignment prefix."""
        test_cases = [
            ("https://github.com/org/assignment1-student123", "student123"),
            ("https://github.com/org/assignment1-user", "user"),
        ]

        for repo_url, expected in test_cases:
            result = cycle_manager._extract_username_from_repo_url(repo_url)
            assert result == expected

    def test_extract_username_from_repo_url_fallback(self, cycle_manager):
        """Test username extraction fallback to last dash segment."""
        cycle_manager.assignment_prefix = None

        result = cycle_manager._extract_username_from_repo_url(
            "https://github.com/org/some-repo-username"
        )
        assert result == "username"

    def test_extract_username_from_repo_url_no_dash(self, cycle_manager):
        """Test username extraction when no dash is present."""
        cycle_manager.assignment_prefix = None

        result = cycle_manager._extract_username_from_repo_url(
            "https://github.com/org/username"
        )
        assert result is None

    def test_batch_cycle_from_file_repo_url_mode(self, cycle_manager, tmp_path):
        """Test batch cycling from file in repository URL mode."""
        # Create test batch file
        batch_file = tmp_path / "repos.txt"
        batch_file.write_text(
            "https://github.com/org/assignment1-student1\n"
            "https://github.com/org/assignment1-student2\n"
            "# Comment line\n"
            "\n"  # Empty line
        )

        mock_result1 = CycleOperation(
            repo_url="https://github.com/org/assignment1-student1",
            username="student1",
            result=CycleResult.SUCCESS,
            message="Success",
            actions_taken=["Added user"]
        )

        mock_result2 = CycleOperation(
            repo_url="https://github.com/org/assignment1-student2",
            username="student2",
            result=CycleResult.SKIPPED,
            message="Already OK",
            actions_taken=[]
        )

        with patch.object(cycle_manager, 'cycle_single_repository', side_effect=[mock_result1, mock_result2]):
            summary = cycle_manager.batch_cycle_from_file(
                batch_file, repo_url_mode=True)

            assert summary.total_repositories == 2
            assert summary.successful_operations == 1
            assert summary.skipped_operations == 1
            assert summary.failed_operations == 0
            assert len(summary.errors) == 0

    def test_batch_cycle_from_file_username_mode(self, cycle_manager, tmp_path):
        """Test batch cycling from file in username mode."""
        # Create test batch file
        batch_file = tmp_path / "usernames.txt"
        batch_file.write_text(
            "student1\n"
            "student2\n"
        )

        mock_result1 = CycleOperation(
            repo_url="https://github.com/test-org/assignment1-student1",
            username="student1",
            result=CycleResult.SUCCESS,
            message="Success",
            actions_taken=["Added user"]
        )

        mock_result2 = CycleOperation(
            repo_url="https://github.com/test-org/assignment1-student2",
            username="student2",
            result=CycleResult.SKIPPED,
            message="Already OK",
            actions_taken=[]
        )

        with patch.object(cycle_manager, 'cycle_single_repository', side_effect=[mock_result1, mock_result2]):
            summary = cycle_manager.batch_cycle_from_file(
                batch_file, repo_url_mode=False)

            assert summary.total_repositories == 2
            assert summary.successful_operations == 1
            assert summary.skipped_operations == 1
            assert summary.failed_operations == 0

    def test_batch_cycle_from_file_no_prefix(self, cycle_manager, tmp_path):
        """Test batch cycling from file in username mode without assignment prefix."""
        cycle_manager.assignment_prefix = None

        batch_file = tmp_path / "usernames.txt"
        batch_file.write_text("student1\n")

        summary = cycle_manager.batch_cycle_from_file(
            batch_file, repo_url_mode=False)

        assert summary.total_repositories == 0
        assert len(summary.errors) == 1
        assert "Assignment prefix not configured" in summary.errors[0]

    def test_batch_cycle_from_file_not_found(self, cycle_manager):
        """Test batch cycling with non-existent file."""
        with pytest.raises(FileNotFoundError):
            cycle_manager.batch_cycle_from_file(Path("nonexistent.txt"))

    def test_batch_cycle_from_file_empty(self, cycle_manager, tmp_path):
        """Test batch cycling from empty file."""
        batch_file = tmp_path / "empty.txt"
        batch_file.write_text("")

        summary = cycle_manager.batch_cycle_from_file(batch_file)

        assert summary.total_repositories == 0
        assert len(summary.errors) == 1
        assert "No valid entries found" in summary.errors[0]

    def test_display_repository_status(self, cycle_manager, capsys):
        """Test displaying repository status."""
        status = RepositoryStatus(
            repo_url="https://github.com/owner/repo",
            username="user",
            accessible=True,
            has_collaborator_access=True,
            has_pending_invitation=False,
            access_status=AccessStatus.OK,
            needs_cycling=False
        )

        cycle_manager.display_repository_status(status)

        captured = capsys.readouterr()
        assert "Repository Status" in captured.out
        assert "✅ Yes" in captured.out
        assert "✅ OK" in captured.out

    def test_display_cycle_result(self, cycle_manager, capsys):
        """Test displaying cycle operation result."""
        result = CycleOperation(
            repo_url="https://github.com/owner/repo",
            username="user",
            result=CycleResult.SUCCESS,
            message="Successfully cycled",
            actions_taken=["Removed collaborator", "Added collaborator"]
        )

        cycle_manager.display_cycle_result(result)

        captured = capsys.readouterr()
        assert "Cycle Operation Result" in captured.out
        assert "✅ SUCCESS" in captured.out
        assert "Removed collaborator" in captured.out
        assert "Added collaborator" in captured.out

    def test_display_batch_summary(self, cycle_manager, capsys):
        """Test displaying batch operation summary."""
        summary = BatchSummary(
            total_repositories=5,
            successful_operations=3,
            skipped_operations=1,
            failed_operations=1,
            repositories_fixed=3,
            repositories_already_ok=1,
            errors=["Error 1", "Error 2"]
        )

        cycle_manager.display_batch_summary(summary)

        captured = capsys.readouterr()
        assert "Batch Operation Summary" in captured.out
        assert "Total Repositories: 5" in captured.out
        assert "Successful Operations: 3" in captured.out
        assert "Error 1" in captured.out
        assert "Error 2" in captured.out
