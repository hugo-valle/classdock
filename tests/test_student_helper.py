"""
Tests for Student Update Helper functionality.

Tests cover:
- Student repository status checking
- Individual student assistance
- Batch processing
- Conflict resolution
- Configuration validation
- Git operations
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from classdock.assignments.student_helper import (
    StudentUpdateHelper,
    OperationResult,
    UpdateResult,
    StudentStatus,
    BatchSummary
)
from classdock.config.global_config import GlobalConfig


@pytest.fixture
def mock_config():
    """Mock global configuration."""
    config = GlobalConfig()
    config.github_organization = "test-org"
    config.assignment_name = "test-assignment"
    config.template_repo_url = "https://github.com/test-org/template-repo"
    config.classroom_repo_url = "https://github.com/test-org/classroom-repo"
    config.assignment_file = "test.py"
    return config


@pytest.fixture
def student_helper(mock_config):
    """Student helper instance with mocked config."""
    with patch('classdock.assignments.student_helper.get_global_config', return_value=mock_config):
        helper = StudentUpdateHelper(auto_confirm=True)
        return helper


@pytest.fixture
def temp_repo_file():
    """Temporary file with repository URLs."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("https://github.com/test-org/test-assignment-student1\n")
        f.write("https://github.com/test-org/test-assignment-student2\n")
        f.write("# Comment line\n")
        f.write("https://github.com/test-org/test-assignment-student3\n")
        temp_file = Path(f.name)

    yield temp_file

    # Cleanup
    if temp_file.exists():
        temp_file.unlink()


class TestStudentUpdateHelper:
    """Test student update helper functionality."""

    def test_initialization(self, student_helper):
        """Test helper initialization."""
        assert student_helper is not None
        assert student_helper.auto_confirm is True
        assert student_helper.branch == "main"
        assert student_helper.temp_dir.exists()

    def test_validate_configuration_success(self, student_helper):
        """Test successful configuration validation."""
        assert student_helper.validate_configuration() is True

    def test_validate_configuration_missing_config(self):
        """Test configuration validation with missing config."""
        with patch('classdock.assignments.student_helper.get_global_config', return_value=None):
            helper = StudentUpdateHelper()
            assert helper.validate_configuration() is False

    def test_extract_student_name(self, student_helper):
        """Test student name extraction from URL."""
        test_cases = [
            ("https://github.com/test-org/test-assignment-student123", "student123"),
            ("https://github.com/test-org/test-assignment-alice-smith.git", "alice-smith"),
            ("https://github.com/test-org/unknown-format", "unknown"),
        ]

        for repo_url, expected in test_cases:
            result = student_helper.extract_student_name(repo_url)
            assert result == expected

    def test_validate_repo_url_valid(self, student_helper):
        """Test repository URL validation with valid URL."""
        valid_url = "https://github.com/test-org/test-assignment-student123"
        assert student_helper.validate_repo_url(valid_url) is True

    def test_validate_repo_url_invalid(self, student_helper):
        """Test repository URL validation with invalid URL."""
        invalid_url = "https://github.com/wrong-org/wrong-assignment-student123"
        assert student_helper.validate_repo_url(invalid_url) is False

    def test_confirm_action_auto_confirm(self, student_helper):
        """Test action confirmation with auto-confirm enabled."""
        assert student_helper.confirm_action("Test prompt?") is True

    def test_confirm_action_manual_confirm(self, mock_config):
        """Test action confirmation with manual confirmation."""
        with patch('classdock.assignments.student_helper.get_global_config', return_value=mock_config):
            helper = StudentUpdateHelper(auto_confirm=False)

            with patch('typer.confirm', return_value=True):
                assert helper.confirm_action("Test prompt?") is True

            with patch('typer.confirm', return_value=False):
                assert helper.confirm_action("Test prompt?") is False

    @patch('subprocess.run')
    def test_check_repo_access_success(self, mock_run, student_helper):
        """Test successful repository access check."""
        mock_run.return_value.returncode = 0

        result = student_helper.check_repo_access(
            "https://github.com/test-org/test-repo")
        assert result is True

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[:2] == ['git', 'ls-remote']

    @patch('subprocess.run')
    def test_check_repo_access_failure(self, mock_run, student_helper):
        """Test failed repository access check."""
        mock_run.return_value.returncode = 1

        result = student_helper.check_repo_access(
            "https://github.com/test-org/nonexistent")
        assert result is False

    @patch('subprocess.run')
    def test_get_remote_commit_success(self, mock_run, student_helper):
        """Test successful remote commit retrieval."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "abc123def456\trefs/heads/main\n"

        result = student_helper.get_remote_commit(
            "https://github.com/test-org/test-repo")
        assert result == "abc123def456"

    @patch('subprocess.run')
    def test_get_remote_commit_failure(self, mock_run, student_helper):
        """Test failed remote commit retrieval."""
        mock_run.return_value.returncode = 1

        result = student_helper.get_remote_commit(
            "https://github.com/test-org/nonexistent")
        assert result is None

    @patch('classdock.assignments.student_helper.StudentUpdateHelper.check_repo_access')
    @patch('classdock.assignments.student_helper.StudentUpdateHelper.get_remote_commit')
    def test_check_student_status_accessible(self, mock_get_commit, mock_check_access, student_helper):
        """Test student status check for accessible repository."""
        mock_check_access.return_value = True
        mock_get_commit.side_effect = [
            "student123", "template456", "classroom789"]

        repo_url = "https://github.com/test-org/test-assignment-student123"
        status = student_helper.check_student_status(repo_url)

        assert status.student_name == "student123"
        assert status.accessible is True
        assert status.student_commit == "student123"
        assert status.template_commit == "template456"
        assert status.classroom_commit == "classroom789"
        assert status.needs_update is True  # Different commits

    @patch('classdock.assignments.student_helper.StudentUpdateHelper.check_repo_access')
    def test_check_student_status_not_accessible(self, mock_check_access, student_helper):
        """Test student status check for inaccessible repository."""
        mock_check_access.return_value = False

        repo_url = "https://github.com/test-org/test-assignment-student123"
        status = student_helper.check_student_status(repo_url)

        assert status.student_name == "student123"
        assert status.accessible is False
        assert status.needs_update is False
        assert "Cannot access" in status.error_message

    @patch('classdock.assignments.student_helper.StudentUpdateHelper.check_repo_access')
    @patch('classdock.assignments.student_helper.StudentUpdateHelper.get_remote_commit')
    def test_check_student_status_up_to_date(self, mock_get_commit, mock_check_access, student_helper):
        """Test student status check for up-to-date repository."""
        mock_check_access.return_value = True
        mock_get_commit.side_effect = [
            "same123", "same123", "same123"]  # Same commits

        repo_url = "https://github.com/test-org/test-assignment-student123"
        status = student_helper.check_student_status(repo_url)

        assert status.accessible is True
        assert status.needs_update is False

    @patch('classdock.assignments.student_helper.StudentUpdateHelper.check_repo_access')
    def test_check_classroom_ready_success(self, mock_check_access, student_helper):
        """Test successful classroom readiness check."""
        mock_check_access.return_value = True

        with patch('classdock.assignments.student_helper.StudentUpdateHelper.get_remote_commit') as mock_get_commit:
            mock_get_commit.side_effect = [
                "same123", "same123"]  # Same commits

            result = student_helper.check_classroom_ready()
            assert result is True

    @patch('classdock.assignments.student_helper.StudentUpdateHelper.check_repo_access')
    def test_check_classroom_ready_not_accessible(self, mock_check_access, student_helper):
        """Test classroom readiness check with inaccessible repository."""
        mock_check_access.return_value = False

        result = student_helper.check_classroom_ready()
        assert result is False

    def test_check_classroom_ready_no_config(self):
        """Test classroom readiness check with no configuration."""
        with patch('classdock.assignments.student_helper.get_global_config', return_value=None):
            helper = StudentUpdateHelper()
            result = helper.check_classroom_ready()
            assert result is False

    @patch('subprocess.run')
    @patch('os.chdir')
    @patch('shutil.rmtree')
    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.exists')
    def test_help_single_student_success(self, mock_exists, mock_mkdir, mock_rmtree, mock_chdir, mock_run, student_helper):
        """Test successful single student help."""
        # Setup mocks
        mock_exists.return_value = False  # Work dir doesn't exist
        mock_run.side_effect = [
            Mock(returncode=0),  # git clone
            Mock(returncode=0),  # git remote add
            Mock(returncode=0),  # git fetch
            Mock(returncode=0),  # git checkout -b backup
            Mock(returncode=0),  # git checkout main
            Mock(returncode=0),  # git merge
            Mock(returncode=0),  # git push origin main
            Mock(returncode=0),  # git push origin backup
        ]

        with patch('classdock.assignments.student_helper.StudentUpdateHelper.check_student_status') as mock_status:
            mock_status.return_value = StudentStatus(
                student_name="student123",
                repo_url="https://github.com/test-org/test-assignment-student123",
                accessible=True,
                needs_update=True
            )

            with patch('classdock.assignments.student_helper.StudentUpdateHelper.validate_repo_url', return_value=True):
                repo_url = "https://github.com/test-org/test-assignment-student123"
                result = student_helper.help_single_student(repo_url)

                assert result.student_name == "student123"
                assert result.result == OperationResult.SUCCESS
                assert "successfully" in result.message.lower()

    @patch('classdock.assignments.student_helper.StudentUpdateHelper.check_student_status')
    def test_help_single_student_up_to_date(self, mock_status, student_helper):
        """Test single student help when already up to date."""
        mock_status.return_value = StudentStatus(
            student_name="student123",
            repo_url="https://github.com/test-org/test-assignment-student123",
            accessible=True,
            needs_update=False
        )

        with patch('classdock.assignments.student_helper.StudentUpdateHelper.validate_repo_url', return_value=True):
            repo_url = "https://github.com/test-org/test-assignment-student123"
            result = student_helper.help_single_student(repo_url)

            assert result.result == OperationResult.UP_TO_DATE

    @patch('classdock.assignments.student_helper.StudentUpdateHelper.check_student_status')
    def test_help_single_student_not_accessible(self, mock_status, student_helper):
        """Test single student help when repository is not accessible."""
        mock_status.return_value = StudentStatus(
            student_name="student123",
            repo_url="https://github.com/test-org/test-assignment-student123",
            accessible=False,
            needs_update=False,
            error_message="Access denied"
        )

        with patch('classdock.assignments.student_helper.StudentUpdateHelper.validate_repo_url', return_value=True):
            repo_url = "https://github.com/test-org/test-assignment-student123"
            result = student_helper.help_single_student(repo_url)

            assert result.result == OperationResult.ACCESS_ERROR
            assert "Access denied" in result.message

    def test_batch_help_students_file_not_found(self, student_helper):
        """Test batch processing with non-existent file."""
        nonexistent_file = Path("/nonexistent/file.txt")

        with pytest.raises(FileNotFoundError):
            student_helper.batch_help_students(nonexistent_file)

    def test_batch_help_students_empty_file(self, student_helper):
        """Test batch processing with empty file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("# Only comments\n")
            f.write("\n")
            temp_file = Path(f.name)

        try:
            with pytest.raises(ValueError, match="No valid repository URLs"):
                student_helper.batch_help_students(temp_file)
        finally:
            temp_file.unlink()

    @patch('classdock.assignments.student_helper.StudentUpdateHelper.help_single_student')
    @patch('classdock.assignments.student_helper.StudentUpdateHelper.check_student_status')
    def test_batch_help_students_success(self, mock_status, mock_help, student_helper, temp_repo_file):
        """Test successful batch processing."""
        # Mock status checks
        mock_status.side_effect = [
            StudentStatus("student1", "url1", True, True),
            StudentStatus("student2", "url2", True, False),  # Up to date
            StudentStatus("student3", "url3", False, False),  # Not accessible
        ]

        # Mock help results
        mock_help.return_value = UpdateResult(
            "student1", "url1", OperationResult.SUCCESS, "Updated")

        summary = student_helper.batch_help_students(temp_repo_file)

        assert summary.total_processed == 3
        assert summary.successful == 1
        assert summary.up_to_date == 1
        assert summary.errors == 1
        assert len(summary.results) == 3

    def test_generate_student_instructions(self, student_helper):
        """Test student instruction generation."""
        repo_url = "https://github.com/test-org/test-assignment-student123"
        instructions = student_helper.generate_student_instructions(repo_url)

        assert "student123" in instructions
        assert "git add" in instructions
        assert "git commit" in instructions
        assert "git merge" in instructions
        assert "OPTION 1" in instructions
        assert "OPTION 2" in instructions

    @patch('shutil.rmtree')
    @patch('pathlib.Path.exists')
    def test_cleanup(self, mock_exists, mock_rmtree, student_helper):
        """Test cleanup functionality."""
        # Mock path exists to return True
        mock_exists.return_value = True

        # Call cleanup
        student_helper.cleanup()

        # Verify cleanup was called
        mock_rmtree.assert_called_once()

    def test_display_student_status(self, student_helper, capsys):
        """Test student status display."""
        status = StudentStatus(
            student_name="student123",
            repo_url="https://github.com/test-org/test-assignment-student123",
            accessible=True,
            needs_update=True,
            student_commit="abc123",
            template_commit="def456",
            classroom_commit="ghi789"
        )

        student_helper.display_student_status(status)
        # Just verify no exceptions are raised
        assert True

    def test_display_batch_summary(self, student_helper):
        """Test batch summary display."""
        results = [
            UpdateResult("student1", "url1",
                         OperationResult.SUCCESS, "Updated"),
            UpdateResult("student2", "url2",
                         OperationResult.UP_TO_DATE, "Current"),
            UpdateResult("student3", "url3",
                         OperationResult.ACCESS_ERROR, "No access"),
        ]

        summary = BatchSummary(
            total_processed=3,
            successful=1,
            up_to_date=1,
            errors=1,
            results=results
        )

        student_helper.display_batch_summary(summary)
        # Just verify no exceptions are raised
        assert True


class TestStudentUpdateHelperIntegration:
    """Integration tests for student update helper."""

    def test_end_to_end_workflow_simulation(self, mock_config):
        """Test end-to-end workflow simulation."""
        with patch('classdock.assignments.student_helper.get_global_config', return_value=mock_config):
            helper = StudentUpdateHelper(auto_confirm=True)

            # Test configuration validation
            assert helper.validate_configuration() is True

            # Test student name extraction
            repo_url = "https://github.com/test-org/test-assignment-alice"
            student_name = helper.extract_student_name(repo_url)
            assert student_name == "alice"

            # Test URL validation
            assert helper.validate_repo_url(repo_url) is True

            # Test instruction generation
            instructions = helper.generate_student_instructions(repo_url)
            assert "alice" in instructions

    @patch('classdock.assignments.student_helper.StudentUpdateHelper.check_repo_access')
    def test_status_check_workflow(self, mock_check_access, mock_config):
        """Test status checking workflow."""
        with patch('classdock.assignments.student_helper.get_global_config', return_value=mock_config):
            helper = StudentUpdateHelper()

            # Mock accessible repository
            mock_check_access.return_value = True

            with patch('classdock.assignments.student_helper.StudentUpdateHelper.get_remote_commit') as mock_get_commit:
                mock_get_commit.side_effect = [
                    "abc123", "abc123", "abc123"]  # Same commits

                repo_url = "https://github.com/test-org/test-assignment-student123"
                status = helper.check_student_status(repo_url)

                assert status.accessible is True
                assert status.needs_update is False

    def test_error_handling(self, mock_config):
        """Test error handling in various scenarios."""
        with patch('classdock.assignments.student_helper.get_global_config', return_value=mock_config):
            helper = StudentUpdateHelper()

            # Test with invalid URL
            invalid_url = "not-a-url"
            assert helper.validate_repo_url(invalid_url) is False

            # Test with missing config fields
            incomplete_config = GlobalConfig()
            incomplete_config.github_organization = "test-org"
            # Missing assignment_name and template_repo_url

            with patch('classdock.assignments.student_helper.get_global_config', return_value=incomplete_config):
                helper_incomplete = StudentUpdateHelper()
                assert helper_incomplete.validate_configuration() is False


class TestStudentUpdateHelperExecuteUpdateWorkflow:
    """
    TestStudentUpdateHelperExecuteUpdateWorkflow contains unit tests for the execute_update_workflow
    method added to StudentUpdateHelper. This method is the main entry point for the update
    workflow that validates configuration and checks classroom readiness.

    Test Cases:
    - test_execute_update_workflow_success: Tests successful workflow execution
    - test_execute_update_workflow_with_auto_confirm: Tests auto_confirm parameter handling
    - test_execute_update_workflow_config_validation_failure: Tests config validation failure
    - test_execute_update_workflow_classroom_not_ready: Tests when classroom not ready
    - test_execute_update_workflow_exception_handling: Tests exception handling
    - test_execute_update_workflow_verbose_mode: Tests verbose logging
    """

    def test_execute_update_workflow_success(self, mock_config):
        """
        Test successful execute_update_workflow execution.

        This test verifies that execute_update_workflow correctly:
        - Validates configuration
        - Checks classroom readiness
        - Returns True with success message
        """
        with patch('classdock.assignments.student_helper.get_global_config', return_value=mock_config):
            helper = StudentUpdateHelper(auto_confirm=False)

            with patch.object(helper, 'validate_configuration', return_value=True), \
                    patch.object(helper, 'check_classroom_ready', return_value=True):

                success, message = helper.execute_update_workflow(
                    auto_confirm=True, verbose=False)

                assert success is True
                assert "Update workflow validated successfully" in message
                assert helper.auto_confirm is True

    def test_execute_update_workflow_with_auto_confirm(self, mock_config):
        """
        Test execute_update_workflow with auto_confirm parameter.

        This test verifies that the auto_confirm parameter is properly
        applied to the helper instance.
        """
        with patch('classdock.assignments.student_helper.get_global_config', return_value=mock_config):
            helper = StudentUpdateHelper(auto_confirm=False)

            with patch.object(helper, 'validate_configuration', return_value=True), \
                    patch.object(helper, 'check_classroom_ready', return_value=True):

                success, message = helper.execute_update_workflow(
                    auto_confirm=True, verbose=True)

                assert success is True
                assert helper.auto_confirm is True

    def test_execute_update_workflow_config_validation_failure(self, mock_config):
        """
        Test execute_update_workflow when configuration validation fails.

        This test verifies that execute_update_workflow returns False with
        appropriate error message when configuration validation fails.
        """
        with patch('classdock.assignments.student_helper.get_global_config', return_value=mock_config):
            helper = StudentUpdateHelper(auto_confirm=True)

            with patch.object(helper, 'validate_configuration', return_value=False):
                success, message = helper.execute_update_workflow(
                    auto_confirm=True, verbose=False)

                assert success is False
                assert "Configuration validation failed" in message

    def test_execute_update_workflow_classroom_not_ready(self, mock_config):
        """
        Test execute_update_workflow when classroom repository is not ready.

        This test verifies that execute_update_workflow returns False with
        appropriate error message when classroom is not ready.
        """
        with patch('classdock.assignments.student_helper.get_global_config', return_value=mock_config):
            helper = StudentUpdateHelper(auto_confirm=True)

            with patch.object(helper, 'validate_configuration', return_value=True), \
                    patch.object(helper, 'check_classroom_ready', return_value=False):

                success, message = helper.execute_update_workflow(
                    auto_confirm=True, verbose=False)

                assert success is False
                assert "Classroom repository not ready" in message

    def test_execute_update_workflow_exception_handling(self, mock_config):
        """
        Test execute_update_workflow exception handling.

        This test verifies that execute_update_workflow gracefully handles
        exceptions and returns False with error message.
        """
        with patch('classdock.assignments.student_helper.get_global_config', return_value=mock_config):
            helper = StudentUpdateHelper(auto_confirm=True)

            with patch.object(helper, 'validate_configuration', side_effect=Exception("Unexpected error")):
                success, message = helper.execute_update_workflow(
                    auto_confirm=True, verbose=False)

                assert success is False
                assert "Unexpected error" in message

    def test_execute_update_workflow_verbose_mode(self, mock_config):
        """
        Test execute_update_workflow with verbose mode enabled.

        This test verifies that the verbose parameter is accepted and
        doesn't affect the workflow logic.
        """
        with patch('classdock.assignments.student_helper.get_global_config', return_value=mock_config):
            helper = StudentUpdateHelper(auto_confirm=True)

            with patch.object(helper, 'validate_configuration', return_value=True), \
                    patch.object(helper, 'check_classroom_ready', return_value=True):

                success, message = helper.execute_update_workflow(
                    auto_confirm=True, verbose=True)

                assert success is True
                assert "Update workflow validated successfully" in message

    def test_execute_update_workflow_without_auto_confirm_param(self, mock_config):
        """
        Test execute_update_workflow when auto_confirm=False is provided.

        This test verifies that when auto_confirm=False is provided, the
        existing helper setting is preserved (not overwritten) since the
        implementation only updates auto_confirm when it's truthy.
        """
        with patch('classdock.assignments.student_helper.get_global_config', return_value=mock_config):
            helper = StudentUpdateHelper(auto_confirm=True)
            original_auto_confirm = helper.auto_confirm

            with patch.object(helper, 'validate_configuration', return_value=True), \
                    patch.object(helper, 'check_classroom_ready', return_value=True):

                success, message = helper.execute_update_workflow(
                    auto_confirm=False, verbose=False)

                assert success is True
                # auto_confirm should remain True since False is falsy and doesn't trigger update
                assert helper.auto_confirm is True

    def test_execute_update_workflow_return_type(self, mock_config):
        """
        Test execute_update_workflow return type.

        This test verifies that execute_update_workflow always returns
        a tuple of (bool, str).
        """
        with patch('classdock.assignments.student_helper.get_global_config', return_value=mock_config):
            helper = StudentUpdateHelper(auto_confirm=True)

            with patch.object(helper, 'validate_configuration', return_value=True), \
                    patch.object(helper, 'check_classroom_ready', return_value=True):

                result = helper.execute_update_workflow(
                    auto_confirm=True, verbose=False)

                assert isinstance(result, tuple)
                assert len(result) == 2
                assert isinstance(result[0], bool)
                assert isinstance(result[1], str)
