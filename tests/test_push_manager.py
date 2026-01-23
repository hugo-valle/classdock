"""
Test suite for the ClassroomPushManager class.

Tests template to classroom repository push functionality including validation,
git operations, remote management, and complete workflow execution.
"""

import pytest
import subprocess
from unittest.mock import Mock, patch, call
from pathlib import Path

from classdock.assignments.push_manager import (
    ClassroomPushManager, PushResult, GitCommitInfo, RepositoryState,
    PushValidationResult
)
from classdock.config import GlobalConfig


class TestGitCommitInfo:
    """Test GitCommitInfo utility class."""

    @patch('classdock.assignments.push_manager.subprocess.run')
    def test_from_hash_success(self, mock_subprocess):
        """Test creating GitCommitInfo from valid hash."""
        mock_result = Mock()
        mock_result.stdout = "abc123def456\nabc123d\nFix assignment bug\nJohn Doe\nMon Oct 4 10:00:00 2025"
        mock_subprocess.return_value = mock_result

        commit_info = GitCommitInfo.from_hash("abc123def456")

        assert commit_info.hash == "abc123def456"
        assert commit_info.short_hash == "abc123d"
        assert commit_info.message == "Fix assignment bug"
        assert commit_info.author == "John Doe"
        assert commit_info.date == "Mon Oct 4 10:00:00 2025"

    @patch('classdock.assignments.push_manager.subprocess.run')
    def test_from_hash_failure(self, mock_subprocess):
        """Test creating GitCommitInfo when git command fails."""
        mock_subprocess.side_effect = subprocess.CalledProcessError(
            1, 'git show')

        commit_info = GitCommitInfo.from_hash("abc123def456")

        assert commit_info.hash == "abc123def456"
        assert commit_info.short_hash == "abc123de"
        assert commit_info.message == "Unknown"
        assert commit_info.author == "Unknown"
        assert commit_info.date == "Unknown"

    def test_from_hash_short_hash(self):
        """Test creating GitCommitInfo from short hash."""
        with patch('classdock.assignments.push_manager.subprocess.run') as mock_subprocess:
            mock_subprocess.side_effect = subprocess.CalledProcessError(
                1, 'git show')

            commit_info = GitCommitInfo.from_hash("abc123")

            assert commit_info.hash == "abc123"
            assert commit_info.short_hash == "abc123"


class TestClassroomPushManager:
    """Test the ClassroomPushManager class initialization and basic functionality."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock GlobalConfig for testing."""
        config = Mock(spec=GlobalConfig)
        config.assignment_file = "assignment.py"
        config.classroom_repo_url = "https://github.com/org/classroom-repo"
        return config

    @pytest.fixture
    def temp_assignment_root(self, tmp_path):
        """Create a temporary assignment root directory."""
        return tmp_path

    @pytest.fixture
    def push_manager(self, mock_config, temp_assignment_root):
        """Create a ClassroomPushManager instance for testing."""
        return ClassroomPushManager(mock_config, temp_assignment_root)

    def test_init_with_config(self, mock_config, temp_assignment_root):
        """Test ClassroomPushManager initialization with config."""
        manager = ClassroomPushManager(mock_config, temp_assignment_root)

        assert manager.global_config == mock_config
        assert manager.assignment_root == temp_assignment_root
        assert manager.classroom_remote == "classroom"
        assert manager.branch == "main"

    def test_init_without_config(self):
        """Test ClassroomPushManager initialization without config."""
        with patch('classdock.assignments.push_manager.GlobalConfig') as mock_global_config:
            manager = ClassroomPushManager()
            mock_global_config.assert_called_once()
            assert manager.assignment_root == Path.cwd()

    @patch('classdock.assignments.push_manager.subprocess.run')
    def test_run_git_command_success(self, mock_subprocess, push_manager):
        """Test successful git command execution."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "git output"
        mock_subprocess.return_value = mock_result

        result = push_manager._run_git_command(['status'])

        assert result == mock_result
        mock_subprocess.assert_called_once_with(
            ['git', 'status'],
            cwd=push_manager.assignment_root,
            capture_output=True,
            text=True,
            check=True,
            timeout=30
        )

    @patch('classdock.assignments.push_manager.subprocess.run')
    def test_run_git_command_failure(self, mock_subprocess, push_manager):
        """Test git command execution with failure."""
        mock_subprocess.side_effect = subprocess.CalledProcessError(
            1, ['git', 'status'], stderr="fatal: not a git repository"
        )

        with pytest.raises(subprocess.CalledProcessError):
            push_manager._run_git_command(['status'])

    @patch('classdock.assignments.push_manager.subprocess.run')
    def test_run_git_command_timeout(self, mock_subprocess, push_manager):
        """Test git command execution with timeout."""
        mock_subprocess.side_effect = subprocess.TimeoutExpired(
            ['git', 'status'], 30)

        with pytest.raises(subprocess.TimeoutExpired):
            push_manager._run_git_command(['status'])


class TestRepositoryValidation:
    """Test repository validation functionality."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock config for testing."""
        config = Mock(spec=GlobalConfig)
        config.assignment_file = "assignment.py"
        config.classroom_repo_url = "https://github.com/org/classroom-repo"
        return config

    @pytest.fixture
    def push_manager(self, mock_config, tmp_path):
        """Create push manager with temp directory."""
        return ClassroomPushManager(mock_config, tmp_path)

    def test_validate_repository_success(self, push_manager, tmp_path):
        """Test successful repository validation."""
        # Create git directory and assignment file
        (tmp_path / ".git").mkdir()
        (tmp_path / "assignment.py").touch()

        result = push_manager.validate_repository()

        assert result.is_valid
        assert not result.has_errors

    def test_validate_repository_not_git(self, push_manager):
        """Test repository validation when not in git repository."""
        result = push_manager.validate_repository()

        assert not result.is_valid
        assert result.has_errors
        assert any("Not in a git repository" in error for error in result.errors)

    def test_validate_repository_missing_assignment_file(self, push_manager, tmp_path):
        """Test repository validation with missing assignment file."""
        (tmp_path / ".git").mkdir()

        result = push_manager.validate_repository()

        assert not result.is_valid
        assert any(
            "Assignment file not found" in error for error in result.errors)

    def test_validate_repository_no_classroom_url(self, tmp_path):
        """Test repository validation without classroom URL."""
        config = Mock(spec=GlobalConfig)
        config.assignment_file = "assignment.py"
        config.classroom_repo_url = None

        manager = ClassroomPushManager(config, tmp_path)
        (tmp_path / ".git").mkdir()
        (tmp_path / "assignment.py").touch()

        result = manager.validate_repository()

        assert not result.is_valid
        assert any(
            "CLASSROOM_REPO_URL is not set" in error for error in result.errors)

    def test_validate_repository_auto_detect_assignment_file(self, tmp_path):
        """Test automatic detection of assignment file."""
        config = Mock(spec=GlobalConfig)
        config.assignment_file = None
        config.classroom_repo_url = "https://github.com/org/repo"

        manager = ClassroomPushManager(config, tmp_path)
        (tmp_path / ".git").mkdir()
        (tmp_path / "assignment.ipynb").touch()

        result = manager.validate_repository()

        assert result.is_valid
        assert result.has_warnings
        assert any(
            "Using detected assignment file" in warning for warning in result.warnings)

    @patch('classdock.assignments.push_manager.ClassroomPushManager._run_git_command')
    def test_check_working_tree_clean_success(self, mock_git, push_manager):
        """Test working tree check when clean."""
        mock_result = Mock()
        mock_result.stdout = ""
        mock_git.return_value = mock_result

        result = push_manager.check_working_tree_clean()

        assert result.is_valid
        assert not result.has_errors

    @patch('classdock.assignments.push_manager.ClassroomPushManager._run_git_command')
    def test_check_working_tree_dirty(self, mock_git, push_manager):
        """Test working tree check with uncommitted changes."""
        # First call returns uncommitted changes
        mock_result1 = Mock()
        mock_result1.stdout = "M file1.py\n?? file2.py"

        # Second call returns status details
        mock_result2 = Mock()
        mock_result2.stdout = "M  file1.py\n?? file2.py"

        mock_git.side_effect = [mock_result1, mock_result2]

        result = push_manager.check_working_tree_clean()

        assert not result.is_valid
        assert result.has_errors
        assert any("uncommitted changes" in error for error in result.errors)

    @patch('classdock.assignments.push_manager.ClassroomPushManager._run_git_command')
    def test_check_working_tree_git_error(self, mock_git, push_manager):
        """Test working tree check with git error."""
        mock_git.side_effect = subprocess.CalledProcessError(1, 'git status')

        result = push_manager.check_working_tree_clean()

        assert not result.is_valid
        assert result.has_errors


class TestRemoteManagement:
    """Test git remote management functionality."""

    @pytest.fixture
    def push_manager(self, tmp_path):
        """Create push manager for testing."""
        config = Mock(spec=GlobalConfig)
        config.classroom_repo_url = "https://github.com/org/classroom-repo"
        return ClassroomPushManager(config, tmp_path)

    @patch('classdock.assignments.push_manager.ClassroomPushManager._run_git_command')
    def test_setup_classroom_remote_new(self, mock_git, push_manager):
        """Test setting up new classroom remote."""
        # Mock remote list (no classroom remote)
        mock_result = Mock()
        mock_result.stdout = "origin\n"
        mock_git.return_value = mock_result

        success, message = push_manager.setup_classroom_remote()

        assert success
        assert "remote configured" in message

        # Verify calls
        expected_calls = [
            call(['remote'], check=False),
            call(['remote', 'add', 'classroom',
                 'https://github.com/org/classroom-repo'])
        ]
        mock_git.assert_has_calls(expected_calls)

    @patch('classdock.assignments.push_manager.ClassroomPushManager._run_git_command')
    def test_setup_classroom_remote_existing(self, mock_git, push_manager):
        """Test updating existing classroom remote."""
        # Mock remote list (has classroom remote)
        mock_result = Mock()
        mock_result.stdout = "origin\nclassroom\n"
        mock_git.return_value = mock_result

        success, message = push_manager.setup_classroom_remote()

        assert success
        assert "remote configured" in message

        # Verify calls
        expected_calls = [
            call(['remote'], check=False),
            call(['remote', 'set-url', 'classroom',
                 'https://github.com/org/classroom-repo'])
        ]
        mock_git.assert_has_calls(expected_calls)

    def test_setup_classroom_remote_no_url(self, tmp_path):
        """Test setting up remote without URL configured."""
        config = Mock(spec=GlobalConfig)
        config.classroom_repo_url = None
        manager = ClassroomPushManager(config, tmp_path)

        success, message = manager.setup_classroom_remote()

        assert not success
        assert "not configured" in message

    @patch('classdock.assignments.push_manager.ClassroomPushManager._run_git_command')
    def test_setup_classroom_remote_git_error(self, mock_git, push_manager):
        """Test setting up remote with git error."""
        mock_git.side_effect = subprocess.CalledProcessError(1, 'git remote')

        success, message = push_manager.setup_classroom_remote()

        assert not success
        assert "Failed to setup" in message

    @patch('classdock.assignments.push_manager.ClassroomPushManager._run_git_command')
    def test_fetch_classroom_repository_success(self, mock_git, push_manager):
        """Test successful fetch of classroom repository."""
        mock_git.return_value = Mock()

        success, message = push_manager.fetch_classroom_repository()

        assert success
        assert "Successfully fetched" in message
        mock_git.assert_called_once_with(['fetch', 'classroom'])

    @patch('classdock.assignments.push_manager.ClassroomPushManager._run_git_command')
    def test_fetch_classroom_repository_empty_repo(self, mock_git, push_manager):
        """Test fetch when classroom repository is empty."""
        error = subprocess.CalledProcessError(1, 'git fetch')
        error.stderr = "fatal: couldn't find remote ref"
        mock_git.side_effect = error

        success, message = push_manager.fetch_classroom_repository()

        assert success  # Empty repo is okay
        assert "empty or newly created" in message

    @patch('classdock.assignments.push_manager.ClassroomPushManager._run_git_command')
    def test_fetch_classroom_repository_error(self, mock_git, push_manager):
        """Test fetch with network error."""
        error = subprocess.CalledProcessError(1, 'git fetch')
        error.stderr = "network error"
        mock_git.side_effect = error

        success, message = push_manager.fetch_classroom_repository()

        assert not success
        assert "Failed to fetch" in message


class TestRepositoryState:
    """Test repository state analysis functionality."""

    @pytest.fixture
    def push_manager(self, tmp_path):
        """Create push manager for testing."""
        config = Mock(spec=GlobalConfig)
        return ClassroomPushManager(config, tmp_path)

    @patch('classdock.assignments.push_manager.GitCommitInfo.from_hash')
    @patch('classdock.assignments.push_manager.ClassroomPushManager._run_git_command')
    def test_get_repository_state_in_sync(self, mock_git, mock_commit_info, push_manager):
        """Test getting repository state when in sync."""
        # Mock local commit
        local_commit = Mock()
        local_commit.hash = "abc123"

        # Mock classroom commit (same)
        classroom_commit = Mock()
        classroom_commit.hash = "abc123"

        mock_commit_info.side_effect = [local_commit, classroom_commit]

        # Mock git commands
        mock_git.side_effect = [
            Mock(stdout="abc123\n"),  # local rev-parse
            Mock(stdout="abc123\n", returncode=0),  # classroom rev-parse
            Mock(stdout="", returncode=0),  # diff (no changes)
            Mock(returncode=0)  # merge-base (is ancestor)
        ]

        state = push_manager.get_repository_state()

        assert state.is_in_sync
        assert state.local_commit == local_commit
        assert state.classroom_commit == classroom_commit
        assert state.files_changed == []
        assert not state.force_required

    @patch('classdock.assignments.push_manager.GitCommitInfo.from_hash')
    @patch('classdock.assignments.push_manager.ClassroomPushManager._run_git_command')
    def test_get_repository_state_out_of_sync(self, mock_git, mock_commit_info, push_manager):
        """Test getting repository state when out of sync."""
        # Mock local commit
        local_commit = Mock()
        local_commit.hash = "abc123"

        # Mock classroom commit (different)
        classroom_commit = Mock()
        classroom_commit.hash = "def456"

        mock_commit_info.side_effect = [local_commit, classroom_commit]

        # Mock git commands
        mock_git.side_effect = [
            Mock(stdout="abc123\n"),  # local rev-parse
            Mock(stdout="def456\n", returncode=0),  # classroom rev-parse
            Mock(stdout="file1.py\nfile2.py\n",
                 returncode=0),  # diff (changes)
            Mock(returncode=1)  # merge-base (not ancestor, force needed)
        ]

        state = push_manager.get_repository_state()

        assert not state.is_in_sync
        assert state.local_commit == local_commit
        assert state.classroom_commit == classroom_commit
        assert state.files_changed == ["file1.py", "file2.py"]
        assert state.force_required

    @patch('classdock.assignments.push_manager.GitCommitInfo.from_hash')
    @patch('classdock.assignments.push_manager.ClassroomPushManager._run_git_command')
    def test_get_repository_state_no_classroom_commit(self, mock_git, mock_commit_info, push_manager):
        """Test getting repository state when classroom has no commits."""
        # Mock local commit
        local_commit = Mock()
        local_commit.hash = "abc123"

        mock_commit_info.return_value = local_commit

        # Mock git commands
        mock_git.side_effect = [
            Mock(stdout="abc123\n"),  # local rev-parse
            Mock(returncode=1)  # classroom rev-parse (fails)
        ]

        state = push_manager.get_repository_state()

        assert not state.is_in_sync
        assert state.local_commit == local_commit
        assert state.classroom_commit is None
        assert state.files_changed == []
        assert not state.force_required

    def test_show_changes_summary_in_sync(self, push_manager):
        """Test changes summary when repositories are in sync."""
        local_commit = Mock()
        local_commit.short_hash = "abc123"
        local_commit.message = "Latest changes"

        classroom_commit = Mock()
        classroom_commit.short_hash = "abc123"
        classroom_commit.message = "Latest changes"

        state = RepositoryState(
            local_commit=local_commit,
            classroom_commit=classroom_commit,
            is_in_sync=True,
            files_changed=[],
            force_required=False
        )

        summary = push_manager.show_changes_summary(state)

        assert "already in sync" in summary
        assert "abc123" in summary

    def test_show_changes_summary_with_changes(self, push_manager):
        """Test changes summary with file changes."""
        local_commit = Mock()
        local_commit.short_hash = "abc123"
        local_commit.message = "Latest changes"

        classroom_commit = Mock()
        classroom_commit.short_hash = "def456"
        classroom_commit.message = "Old changes"

        state = RepositoryState(
            local_commit=local_commit,
            classroom_commit=classroom_commit,
            is_in_sync=False,
            files_changed=["file1.py", "file2.py", "file3.py"],
            force_required=True
        )

        summary = push_manager.show_changes_summary(state)

        assert "file1.py" in summary
        assert "file2.py" in summary
        assert "Force push will be required" in summary
        assert "3" in summary  # number of files

    def test_show_changes_summary_many_files(self, push_manager):
        """Test changes summary with many files (should truncate)."""
        local_commit = Mock()
        local_commit.short_hash = "abc123"
        local_commit.message = "Latest changes"

        state = RepositoryState(
            local_commit=local_commit,
            classroom_commit=None,
            is_in_sync=False,
            files_changed=[f"file{i}.py" for i in range(15)],  # 15 files
            force_required=False
        )

        summary = push_manager.show_changes_summary(state)

        assert "file0.py" in summary
        assert "file9.py" in summary  # Should show first 10
        assert "and 5 more files" in summary  # Should mention remaining


class TestPushExecution:
    """Test push execution functionality."""

    @pytest.fixture
    def push_manager(self, tmp_path):
        """Create push manager for testing."""
        config = Mock(spec=GlobalConfig)
        return ClassroomPushManager(config, tmp_path)

    @patch('classdock.assignments.push_manager.ClassroomPushManager.get_repository_state')
    @patch('classdock.assignments.push_manager.ClassroomPushManager._run_git_command')
    def test_push_to_classroom_success(self, mock_git, mock_get_state, push_manager):
        """Test successful push to classroom repository."""
        # Mock state
        mock_state = Mock()
        mock_state.force_required = False
        mock_get_state.return_value = mock_state

        # Mock successful push
        mock_result = Mock()
        mock_result.returncode = 0
        mock_git.return_value = mock_result

        result, message = push_manager.push_to_classroom()

        assert result == PushResult.SUCCESS
        assert "Successfully pushed" in message
        mock_git.assert_called_once_with(['push', 'classroom', 'main'])

    @patch('classdock.assignments.push_manager.ClassroomPushManager.get_repository_state')
    @patch('classdock.assignments.push_manager.ClassroomPushManager._run_git_command')
    def test_push_to_classroom_force_required(self, mock_git, mock_get_state, push_manager):
        """Test push when force is required."""
        # Mock state requiring force
        mock_state = Mock()
        mock_state.force_required = True
        mock_get_state.return_value = mock_state

        # Mock successful push
        mock_result = Mock()
        mock_result.returncode = 0
        mock_git.return_value = mock_result

        result, message = push_manager.push_to_classroom()

        assert result == PushResult.SUCCESS
        mock_git.assert_called_once_with(
            ['push', 'classroom', 'main', '--force'])

    @patch('classdock.assignments.push_manager.ClassroomPushManager.get_repository_state')
    @patch('classdock.assignments.push_manager.ClassroomPushManager._run_git_command')
    def test_push_to_classroom_permission_error(self, mock_git, mock_get_state, push_manager):
        """Test push with permission error."""
        mock_state = Mock()
        mock_state.force_required = False
        mock_get_state.return_value = mock_state

        error = subprocess.CalledProcessError(1, 'git push')
        error.stderr = "Permission denied"
        mock_git.side_effect = error

        result, message = push_manager.push_to_classroom()

        assert result == PushResult.PERMISSION_ERROR
        assert "Permission denied" in message

    @patch('classdock.assignments.push_manager.ClassroomPushManager.get_repository_state')
    @patch('classdock.assignments.push_manager.ClassroomPushManager._run_git_command')
    def test_push_to_classroom_network_error(self, mock_git, mock_get_state, push_manager):
        """Test push with network error."""
        mock_state = Mock()
        mock_state.force_required = False
        mock_get_state.return_value = mock_state

        error = subprocess.CalledProcessError(1, 'git push')
        error.stderr = "Network connection failed"
        mock_git.side_effect = error

        result, message = push_manager.push_to_classroom()

        assert result == PushResult.NETWORK_ERROR
        assert "Network error" in message

    @patch('classdock.assignments.push_manager.ClassroomPushManager.get_repository_state')
    @patch('classdock.assignments.push_manager.ClassroomPushManager._run_git_command')
    def test_verify_push_success(self, mock_git, mock_get_state, push_manager):
        """Test successful push verification."""
        # Mock in-sync state after push
        mock_state = Mock()
        mock_state.is_in_sync = True
        mock_get_state.return_value = mock_state

        # Mock fetch
        mock_git.return_value = Mock()

        success, message = push_manager.verify_push()

        assert success
        assert "Verification passed" in message

    @patch('classdock.assignments.push_manager.ClassroomPushManager.get_repository_state')
    @patch('classdock.assignments.push_manager.ClassroomPushManager._run_git_command')
    def test_verify_push_failure(self, mock_git, mock_get_state, push_manager):
        """Test push verification failure."""
        # Mock out-of-sync state after push
        mock_state = Mock()
        mock_state.is_in_sync = False
        mock_get_state.return_value = mock_state

        # Mock fetch
        mock_git.return_value = Mock()

        success, message = push_manager.verify_push()

        assert not success
        assert "Verification failed" in message

    def test_get_next_steps_guidance(self, push_manager):
        """Test generation of next steps guidance."""
        push_manager.global_config.classroom_repo_url = "https://github.com/org/test-repo"

        guidance = push_manager.get_next_steps_guidance()

        assert "Next Steps" in guidance
        assert "Announce the update" in guidance
        assert "Monitor for student questions" in guidance
        assert "https://github.com/org/test-repo" in guidance


class TestWorkflowExecution:
    """Test complete workflow execution."""

    @pytest.fixture
    def push_manager(self, tmp_path):
        """Create push manager for testing."""
        config = Mock(spec=GlobalConfig)
        config.classroom_repo_url = "https://github.com/org/repo"
        return ClassroomPushManager(config, tmp_path)

    @patch('classdock.assignments.push_manager.ClassroomPushManager.verify_push')
    @patch('classdock.assignments.push_manager.ClassroomPushManager.push_to_classroom')
    @patch('classdock.assignments.push_manager.ClassroomPushManager.get_repository_state')
    @patch('classdock.assignments.push_manager.ClassroomPushManager.fetch_classroom_repository')
    @patch('classdock.assignments.push_manager.ClassroomPushManager.setup_classroom_remote')
    @patch('classdock.assignments.push_manager.ClassroomPushManager.check_working_tree_clean')
    @patch('classdock.assignments.push_manager.ClassroomPushManager.validate_repository')
    def test_execute_push_workflow_success(
        self, mock_validate, mock_check_tree, mock_setup_remote, mock_fetch,
        mock_get_state, mock_push, mock_verify, push_manager
    ):
        """Test successful complete workflow execution."""
        # Mock all steps to succeed
        mock_validate.return_value = PushValidationResult(True, [], [])
        mock_check_tree.return_value = PushValidationResult(True, [], [])
        mock_setup_remote.return_value = (True, "Remote configured")
        mock_fetch.return_value = (True, "Fetched successfully")

        # Mock state showing changes needed
        mock_state = Mock()
        mock_state.is_in_sync = False
        mock_get_state.return_value = mock_state

        mock_push.return_value = (PushResult.SUCCESS, "Push successful")
        mock_verify.return_value = (True, "Verification passed")

        with patch('classdock.assignments.push_manager.ClassroomPushManager.show_changes_summary') as mock_summary:
            mock_summary.return_value = "Changes to push"

            result, message = push_manager.execute_push_workflow(
                force=True, interactive=False)

        assert result == PushResult.SUCCESS
        assert "Push successful" in message
        assert "Next Steps" in message

    @patch('classdock.assignments.push_manager.ClassroomPushManager.validate_repository')
    def test_execute_push_workflow_validation_error(self, mock_validate, push_manager):
        """Test workflow with repository validation error."""
        mock_validate.return_value = PushValidationResult(
            False, ["Not a git repo"], [])

        result, message = push_manager.execute_push_workflow()

        assert result == PushResult.REPOSITORY_ERROR
        assert "Not a git repo" in message

    @patch('classdock.assignments.push_manager.ClassroomPushManager.get_repository_state')
    @patch('classdock.assignments.push_manager.ClassroomPushManager.fetch_classroom_repository')
    @patch('classdock.assignments.push_manager.ClassroomPushManager.setup_classroom_remote')
    @patch('classdock.assignments.push_manager.ClassroomPushManager.check_working_tree_clean')
    @patch('classdock.assignments.push_manager.ClassroomPushManager.validate_repository')
    def test_execute_push_workflow_up_to_date(
        self, mock_validate, mock_check_tree, mock_setup_remote, mock_fetch,
        mock_get_state, push_manager
    ):
        """Test workflow when repositories are already up to date."""
        # Mock all validation steps to succeed
        mock_validate.return_value = PushValidationResult(True, [], [])
        mock_check_tree.return_value = PushValidationResult(True, [], [])
        mock_setup_remote.return_value = (True, "Remote configured")
        mock_fetch.return_value = (True, "Fetched successfully")

        # Mock state showing in sync
        mock_state = Mock()
        mock_state.is_in_sync = True
        mock_get_state.return_value = mock_state

        result, message = push_manager.execute_push_workflow()

        assert result == PushResult.UP_TO_DATE
        assert "already in sync" in message

    @patch('classdock.assignments.push_manager.ClassroomPushManager.get_repository_state')
    @patch('classdock.assignments.push_manager.ClassroomPushManager.fetch_classroom_repository')
    @patch('classdock.assignments.push_manager.ClassroomPushManager.setup_classroom_remote')
    @patch('classdock.assignments.push_manager.ClassroomPushManager.check_working_tree_clean')
    @patch('classdock.assignments.push_manager.ClassroomPushManager.validate_repository')
    @patch('builtins.input')
    def test_execute_push_workflow_user_cancellation(
        self, mock_input, mock_validate, mock_check_tree, mock_setup_remote,
        mock_fetch, mock_get_state, push_manager
    ):
        """Test workflow when user cancels operation."""
        # Mock all validation steps to succeed
        mock_validate.return_value = PushValidationResult(True, [], [])
        mock_check_tree.return_value = PushValidationResult(True, [], [])
        mock_setup_remote.return_value = (True, "Remote configured")
        mock_fetch.return_value = (True, "Fetched successfully")

        # Mock state showing changes needed
        mock_state = Mock()
        mock_state.is_in_sync = False
        mock_get_state.return_value = mock_state

        # User says no
        mock_input.return_value = "n"

        with patch('classdock.assignments.push_manager.ClassroomPushManager.show_changes_summary') as mock_summary:
            mock_summary.return_value = "Changes to push"

            result, message = push_manager.execute_push_workflow(
                interactive=True)

        assert result == PushResult.CANCELLED
        assert "cancelled by user" in message

    def test_execute_push_workflow_keyboard_interrupt(self, push_manager):
        """Test workflow with keyboard interrupt."""
        with patch('classdock.assignments.push_manager.ClassroomPushManager.validate_repository') as mock_validate:
            mock_validate.side_effect = KeyboardInterrupt()

            result, message = push_manager.execute_push_workflow()

        assert result == PushResult.CANCELLED
        assert "cancelled by user" in message


class TestPushValidationResult:
    """Test PushValidationResult utility class."""

    def test_has_errors_true(self):
        """Test has_errors property when errors exist."""
        result = PushValidationResult(False, ["Error 1", "Error 2"], [])
        assert result.has_errors

    def test_has_errors_false(self):
        """Test has_errors property when no errors."""
        result = PushValidationResult(True, [], ["Warning 1"])
        assert not result.has_errors

    def test_has_warnings_true(self):
        """Test has_warnings property when warnings exist."""
        result = PushValidationResult(True, [], ["Warning 1", "Warning 2"])
        assert result.has_warnings

    def test_has_warnings_false(self):
        """Test has_warnings property when no warnings."""
        result = PushValidationResult(True, ["Error 1"], [])
        assert not result.has_warnings
