"""
Test suite for the CronManager class.

Tests cron job management functionality including installation, removal,
status checking, validation, and error handling.
"""

import pytest
import subprocess
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
from datetime import datetime

from classdock.automation.cron_manager import (
    CronManager, CronJob, CronJobType, CronOperationResult,
    CronValidationResult, CronStatus
)
from classdock.config import GlobalConfig


class TestCronManager:
    """Test the CronManager class initialization and basic functionality."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock GlobalConfig for testing."""
        config = Mock(spec=GlobalConfig)
        return config

    @pytest.fixture
    def cron_manager(self, mock_config):
        """Create a CronManager instance for testing."""
        return CronManager(mock_config)

    def test_init_with_config(self, mock_config):
        """Test CronManager initialization with config."""
        manager = CronManager(mock_config)

        assert manager.global_config == mock_config
        assert isinstance(manager.default_schedules, dict)
        assert len(manager.default_schedules) == 5
        assert manager.cron_comment_prefix == "# GitHub Classroom Assignment Auto"

    def test_init_without_config(self):
        """Test CronManager initialization without config."""
        with patch('classdock.automation.cron_manager.GlobalConfig') as mock_global_config:
            manager = CronManager()
            mock_global_config.assert_called_once()

    def test_default_schedules(self, cron_manager):
        """Test default schedule configuration."""
        schedules = cron_manager.default_schedules

        assert schedules[CronJobType.SYNC] == "0 */4 * * *"
        assert schedules[CronJobType.SECRETS] == "0 2 * * *"
        assert schedules[CronJobType.CYCLE] == "0 6 * * 0"
        assert schedules[CronJobType.DISCOVER] == "0 1 * * *"
        assert schedules[CronJobType.ASSIST] == "0 3 * * 0"

    def test_get_cron_script_path(self, cron_manager):
        """Test cron script path resolution."""
        script_path = cron_manager._get_cron_script_path()

        assert isinstance(script_path, Path)
        assert script_path.exists()  # Should be current working directory

    def test_get_log_file_path(self, cron_manager):
        """Test log file path resolution."""
        log_path = cron_manager._get_log_file_path()

        assert isinstance(log_path, Path)
        assert log_path.name == "cron-workflow.log"
        assert "tools/generated" in str(log_path)

    def test_get_assignment_config_path(self, cron_manager):
        """Test assignment config path resolution."""
        config_path = cron_manager._get_assignment_config_path()

        assert isinstance(config_path, Path)
        assert config_path.name == "assignment.conf"


class TestCronValidation:
    """Test cron validation functionality."""

    @pytest.fixture
    def cron_manager(self):
        """Create a CronManager instance for testing."""
        return CronManager()

    def test_validate_cron_schedule_valid(self, cron_manager):
        """Test validation of valid cron schedules."""
        valid_schedules = [
            "0 */4 * * *",      # Every 4 hours
            "0 2 * * *",        # Daily at 2 AM
            "0 6 * * 0",        # Weekly on Sunday at 6 AM
            "*/15 * * * *",     # Every 15 minutes
            "0 9-17 * * 1-5",   # Business hours weekdays
            "0,30 * * * *",     # On the hour and half hour
        ]

        for schedule in valid_schedules:
            result = cron_manager.validate_cron_schedule(schedule)
            assert result.is_valid, f"Schedule '{schedule}' should be valid"
            assert not result.has_errors

    def test_validate_cron_schedule_invalid(self, cron_manager):
        """Test validation of invalid cron schedules."""
        invalid_schedules = [
            "0 */4 * *",        # Missing field
            "60 2 * * *",       # Invalid minute (>59)
            "0 25 * * *",       # Invalid hour (>23)
            "0 2 32 * *",       # Invalid day (>31)
            "0 2 * 13 *",       # Invalid month (>12)
            "0 2 * * 8",        # Invalid weekday (>7)
            "invalid 2 * * *",  # Non-numeric minute
        ]

        for schedule in invalid_schedules:
            result = cron_manager.validate_cron_schedule(schedule)
            assert not result.is_valid, f"Schedule '{schedule}' should be invalid"
            assert result.has_errors

    def test_validate_cron_field_star(self, cron_manager):
        """Test cron field validation with star wildcard."""
        # Star should be valid for most fields
        assert cron_manager._validate_cron_field("*", 0, 23, allow_star=True)
        assert not cron_manager._validate_cron_field(
            "*", 0, 23, allow_star=False)

    def test_validate_cron_field_step(self, cron_manager):
        """Test cron field validation with step values."""
        assert cron_manager._validate_cron_field("*/4", 0, 23)
        assert cron_manager._validate_cron_field("*/1", 0, 59)
        assert not cron_manager._validate_cron_field("*/25", 0, 23)
        assert not cron_manager._validate_cron_field("*/abc", 0, 23)

    def test_validate_cron_field_range(self, cron_manager):
        """Test cron field validation with range values."""
        assert cron_manager._validate_cron_field("9-17", 0, 23)
        assert cron_manager._validate_cron_field("1-5", 0, 7)
        assert not cron_manager._validate_cron_field(
            "10-5", 0, 23)  # Invalid range
        assert not cron_manager._validate_cron_field(
            "25-30", 0, 23)  # Out of bounds

    def test_validate_cron_field_list(self, cron_manager):
        """Test cron field validation with list values."""
        assert cron_manager._validate_cron_field("0,30", 0, 59)
        assert cron_manager._validate_cron_field("1,3,5", 0, 7)
        assert not cron_manager._validate_cron_field(
            "0,60", 0, 59)  # Out of bounds
        assert not cron_manager._validate_cron_field(
            "a,b", 0, 23)   # Non-numeric

    def test_validate_cron_field_single(self, cron_manager):
        """Test cron field validation with single values."""
        assert cron_manager._validate_cron_field("15", 0, 59)
        assert cron_manager._validate_cron_field("0", 0, 23)
        assert not cron_manager._validate_cron_field(
            "60", 0, 59)  # Out of bounds
        assert not cron_manager._validate_cron_field(
            "abc", 0, 23)  # Non-numeric

    def test_validate_steps_valid(self, cron_manager):
        """Test validation of valid workflow steps."""
        valid_step_combinations = [
            ["sync"],
            ["secrets"],
            ["sync", "secrets"],
            ["sync", "discover", "secrets"],
            ["cycle"],
            ["assist"]
        ]

        for steps in valid_step_combinations:
            result = cron_manager.validate_steps(steps)
            assert result.is_valid, f"Steps {steps} should be valid"
            assert not result.has_errors

    def test_validate_steps_invalid(self, cron_manager):
        """Test validation of invalid workflow steps."""
        invalid_step_combinations = [
            [],                     # Empty list
            ["invalid_step"],       # Invalid step name
            ["sync", "invalid"],    # Mix of valid and invalid
            ["SYNC"],              # Wrong case
        ]

        for steps in invalid_step_combinations:
            result = cron_manager.validate_steps(steps)
            assert not result.is_valid, f"Steps {steps} should be invalid"
            assert result.has_errors

    @patch('classdock.automation.cron_manager.Path.exists')
    @patch('os.access')
    @patch('subprocess.run')
    def test_validate_prerequisites_success(self, mock_subprocess, mock_access, mock_exists, cron_manager):
        """Test successful prerequisite validation."""
        # Mock all files exist and are accessible
        mock_exists.return_value = True
        mock_access.return_value = True
        mock_subprocess.return_value = Mock(returncode=0)

        result = cron_manager.validate_prerequisites()

        assert result.is_valid
        assert not result.has_errors

    @patch('classdock.automation.cron_manager.Path.exists')
    def test_validate_prerequisites_missing_script(self, mock_exists, cron_manager):
        """Test prerequisite validation with missing working directory."""
        mock_exists.side_effect = lambda: False  # Directory doesn't exist

        result = cron_manager.validate_prerequisites()

        assert not result.is_valid
        assert result.has_errors
        assert any(
            "Working directory not found" in error for error in result.errors)

    @patch('classdock.automation.cron_manager.Path.exists')
    def test_validate_prerequisites_valid(self, mock_exists, cron_manager):
        """Test prerequisite validation with valid setup."""
        mock_exists.return_value = True  # Directory exists

        result = cron_manager.validate_prerequisites()

        assert result.is_valid


class TestCronOperations:
    """Test cron job operations (install, remove, status)."""

    @pytest.fixture
    def cron_manager(self):
        """Create a CronManager instance for testing."""
        return CronManager()

    def test_get_default_schedule_single_step(self, cron_manager):
        """Test getting default schedule for single step."""
        assert cron_manager.get_default_schedule(["sync"]) == "0 */4 * * *"
        assert cron_manager.get_default_schedule(["secrets"]) == "0 2 * * *"
        assert cron_manager.get_default_schedule(["cycle"]) == "0 6 * * 0"

    def test_get_default_schedule_multiple_steps(self, cron_manager):
        """Test getting default schedule for multiple steps."""
        result = cron_manager.get_default_schedule(["sync", "secrets"])
        assert result == "0 1 * * *"  # Daily at 1 AM for multiple steps

    def test_get_cron_comment(self, cron_manager):
        """Test cron comment generation with assignment identifier."""
        comment = cron_manager._get_cron_comment(["sync"])
        # Comment now includes assignment identifier (directory name: classdock)
        assert comment == "# GitHub Classroom Assignment Auto-classdock-sync"

        comment = cron_manager._get_cron_comment(["sync", "secrets"])
        assert comment == "# GitHub Classroom Assignment Auto-classdock-sync-secrets"

    def test_get_cron_command(self, cron_manager):
        """Test cron command generation."""
        command = cron_manager._get_cron_command(["sync"])

        assert "python -m classdock automation cron-sync" in command
        assert "sync" in command
        assert ">/dev/null 2>&1" in command

    @patch('classdock.automation.cron_manager.subprocess.run')
    def test_get_current_crontab_exists(self, mock_subprocess, cron_manager):
        """Test getting current crontab when it exists."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "# Test crontab\n0 0 * * * /test/command\n"
        mock_subprocess.return_value = mock_result

        result = cron_manager._get_current_crontab()

        assert result == "# Test crontab\n0 0 * * * /test/command\n"
        mock_subprocess.assert_called_once_with(
            ["crontab", "-l"], capture_output=True, text=True, timeout=10
        )

    @patch('classdock.automation.cron_manager.subprocess.run')
    def test_get_current_crontab_not_exists(self, mock_subprocess, cron_manager):
        """Test getting current crontab when it doesn't exist."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_subprocess.return_value = mock_result

        result = cron_manager._get_current_crontab()

        assert result is None

    @patch('classdock.automation.cron_manager.subprocess.run')
    def test_get_current_crontab_exception(self, mock_subprocess, cron_manager):
        """Test getting current crontab with exception."""
        mock_subprocess.side_effect = subprocess.TimeoutExpired(
            ["crontab", "-l"], 10)

        result = cron_manager._get_current_crontab()

        assert result is None

    @patch('tempfile.NamedTemporaryFile')
    @patch('classdock.automation.cron_manager.subprocess.run')
    @patch('os.unlink')
    def test_set_crontab_success(self, mock_unlink, mock_subprocess, mock_tempfile, cron_manager):
        """Test successfully setting crontab."""
        # Mock temporary file
        mock_file = Mock()
        mock_file.name = "/tmp/test.cron"
        mock_file.__enter__ = Mock(return_value=mock_file)
        mock_file.__exit__ = Mock(return_value=None)
        mock_tempfile.return_value = mock_file

        # Mock successful subprocess
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        result = cron_manager._set_crontab("test crontab content")

        assert result is True
        mock_file.write.assert_called_once_with("test crontab content")
        mock_subprocess.assert_called_once_with(
            ["crontab", "/tmp/test.cron"], capture_output=True, text=True, timeout=10
        )
        mock_unlink.assert_called_once_with("/tmp/test.cron")

    @patch('tempfile.NamedTemporaryFile')
    @patch('classdock.automation.cron_manager.subprocess.run')
    def test_set_crontab_failure(self, mock_subprocess, mock_tempfile, cron_manager):
        """Test setting crontab with failure."""
        # Mock temporary file
        mock_file = Mock()
        mock_file.name = "/tmp/test.cron"
        mock_file.__enter__ = Mock(return_value=mock_file)
        mock_file.__exit__ = Mock(return_value=None)
        mock_tempfile.return_value = mock_file

        # Mock failed subprocess
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Permission denied"
        mock_subprocess.return_value = mock_result

        result = cron_manager._set_crontab("test crontab content")

        assert result is False

    @patch('classdock.automation.cron_manager.CronManager._get_current_crontab')
    def test_job_exists_true(self, mock_get_crontab, cron_manager):
        """Test checking if job exists when it does."""
        mock_get_crontab.return_value = (
            "# GitHub Classroom Assignment Auto-classdock-sync\n"
            "0 */4 * * * python -m classdock automation cron-sync\n"
        )

        result = cron_manager.job_exists(["sync"])
        assert result is True

    @patch('classdock.automation.cron_manager.CronManager._get_current_crontab')
    def test_job_exists_false(self, mock_get_crontab, cron_manager):
        """Test checking if job exists when it doesn't."""
        mock_get_crontab.return_value = (
            "# Other cron job\n"
            "0 0 * * * /other/command\n"
        )

        result = cron_manager.job_exists(["sync"])
        assert result is False

    @patch('classdock.automation.cron_manager.CronManager._get_current_crontab')
    def test_job_exists_no_crontab(self, mock_get_crontab, cron_manager):
        """Test checking if job exists when no crontab exists."""
        mock_get_crontab.return_value = None

        result = cron_manager.job_exists(["sync"])
        assert result is False


class TestCronInstallation:
    """Test cron job installation functionality."""

    @pytest.fixture
    def cron_manager(self):
        """Create a CronManager instance for testing."""
        return CronManager()

    @patch('classdock.automation.cron_manager.CronManager.validate_prerequisites')
    @patch('classdock.automation.cron_manager.CronManager.validate_steps')
    @patch('classdock.automation.cron_manager.CronManager.validate_cron_schedule')
    @patch('classdock.automation.cron_manager.CronManager.job_exists')
    @patch('classdock.automation.cron_manager.CronManager._get_current_crontab')
    @patch('classdock.automation.cron_manager.CronManager._set_crontab')
    def test_install_cron_job_success(
        self, mock_set_crontab, mock_get_crontab, mock_job_exists,
        mock_validate_schedule, mock_validate_steps, mock_validate_prereq,
        cron_manager
    ):
        """Test successful cron job installation."""
        # Mock successful validations
        mock_validate_prereq.return_value = CronValidationResult(True, [], [])
        mock_validate_steps.return_value = CronValidationResult(True, [], [])
        mock_validate_schedule.return_value = CronValidationResult(True, [
        ], [])

        # Mock job doesn't exist
        mock_job_exists.return_value = False

        # Mock existing crontab
        mock_get_crontab.return_value = "# Existing entry\n0 0 * * * /existing/command\n"

        # Mock successful crontab update
        mock_set_crontab.return_value = True

        result, message = cron_manager.install_cron_job(
            ["sync"], "0 */4 * * *")

        assert result == CronOperationResult.SUCCESS
        assert "successfully" in message
        mock_set_crontab.assert_called_once()

    @patch('classdock.automation.cron_manager.CronManager.validate_prerequisites')
    def test_install_cron_job_prereq_failure(self, mock_validate_prereq, cron_manager):
        """Test cron job installation with prerequisite validation failure."""
        mock_validate_prereq.return_value = CronValidationResult(
            False, ["Script not found"], []
        )

        result, message = cron_manager.install_cron_job(["sync"])

        assert result == CronOperationResult.VALIDATION_ERROR
        assert "Prerequisites validation failed" in message

    @patch('classdock.automation.cron_manager.CronManager.validate_prerequisites')
    @patch('classdock.automation.cron_manager.CronManager.validate_steps')
    def test_install_cron_job_steps_failure(
        self, mock_validate_steps, mock_validate_prereq, cron_manager
    ):
        """Test cron job installation with steps validation failure."""
        mock_validate_prereq.return_value = CronValidationResult(True, [], [])
        mock_validate_steps.return_value = CronValidationResult(
            False, ["Invalid step"], []
        )

        result, message = cron_manager.install_cron_job(["invalid_step"])

        assert result == CronOperationResult.VALIDATION_ERROR
        assert "Steps validation failed" in message

    @patch('classdock.automation.cron_manager.CronManager.validate_prerequisites')
    @patch('classdock.automation.cron_manager.CronManager.validate_steps')
    @patch('classdock.automation.cron_manager.CronManager.validate_cron_schedule')
    def test_install_cron_job_schedule_failure(
        self, mock_validate_schedule, mock_validate_steps, mock_validate_prereq, cron_manager
    ):
        """Test cron job installation with schedule validation failure."""
        mock_validate_prereq.return_value = CronValidationResult(True, [], [])
        mock_validate_steps.return_value = CronValidationResult(True, [], [])
        mock_validate_schedule.return_value = CronValidationResult(
            False, ["Invalid schedule"], []
        )

        result, message = cron_manager.install_cron_job(
            ["sync"], "invalid schedule")

        assert result == CronOperationResult.VALIDATION_ERROR
        assert "Schedule validation failed" in message

    @patch('classdock.automation.cron_manager.CronManager.validate_prerequisites')
    @patch('classdock.automation.cron_manager.CronManager.validate_steps')
    @patch('classdock.automation.cron_manager.CronManager.validate_cron_schedule')
    @patch('classdock.automation.cron_manager.CronManager.job_exists')
    def test_install_cron_job_already_exists(
        self, mock_job_exists, mock_validate_schedule,
        mock_validate_steps, mock_validate_prereq, cron_manager
    ):
        """Test cron job installation when job already exists."""
        # Mock successful validations
        mock_validate_prereq.return_value = CronValidationResult(True, [], [])
        mock_validate_steps.return_value = CronValidationResult(True, [], [])
        mock_validate_schedule.return_value = CronValidationResult(True, [
        ], [])

        # Mock job exists
        mock_job_exists.return_value = True

        result, message = cron_manager.install_cron_job(["sync"])

        assert result == CronOperationResult.ALREADY_EXISTS
        assert "already exists" in message

    @patch('classdock.automation.cron_manager.CronManager.validate_prerequisites')
    @patch('classdock.automation.cron_manager.CronManager.validate_steps')
    @patch('classdock.automation.cron_manager.CronManager.validate_cron_schedule')
    @patch('classdock.automation.cron_manager.CronManager.job_exists')
    @patch('classdock.automation.cron_manager.CronManager._get_current_crontab')
    @patch('classdock.automation.cron_manager.CronManager._set_crontab')
    def test_install_cron_job_no_existing_crontab(
        self, mock_set_crontab, mock_get_crontab, mock_job_exists,
        mock_validate_schedule, mock_validate_steps, mock_validate_prereq,
        cron_manager
    ):
        """Test cron job installation when no crontab exists."""
        # Mock successful validations
        mock_validate_prereq.return_value = CronValidationResult(True, [], [])
        mock_validate_steps.return_value = CronValidationResult(True, [], [])
        mock_validate_schedule.return_value = CronValidationResult(True, [
        ], [])

        # Mock job doesn't exist
        mock_job_exists.return_value = False

        # Mock no existing crontab
        mock_get_crontab.return_value = None

        # Mock successful crontab creation
        mock_set_crontab.return_value = True

        result, message = cron_manager.install_cron_job(["sync"])

        assert result == CronOperationResult.SUCCESS
        mock_set_crontab.assert_called_once()
        # Verify the new crontab contains our job with assignment identifier
        call_args = mock_set_crontab.call_args[0][0]
        assert "# GitHub Classroom Assignment Auto-classdock-sync" in call_args
        assert "0 */4 * * *" in call_args  # Default schedule for sync


class TestCronRemoval:
    """Test cron job removal functionality."""

    @pytest.fixture
    def cron_manager(self):
        """Create a CronManager instance for testing."""
        return CronManager()

    @patch('classdock.automation.cron_manager.CronManager._get_current_crontab')
    def test_remove_cron_job_no_crontab(self, mock_get_crontab, cron_manager):
        """Test removing cron job when no crontab exists."""
        mock_get_crontab.return_value = None

        result, message = cron_manager.remove_cron_job(["sync"])

        assert result == CronOperationResult.NOT_FOUND
        assert "No crontab exists" in message

    @patch('classdock.automation.cron_manager.CronManager._get_current_crontab')
    @patch('classdock.automation.cron_manager.CronManager._set_crontab')
    def test_remove_cron_job_all_success(self, mock_set_crontab, mock_get_crontab, cron_manager):
        """Test removing all assignment cron jobs successfully."""
        mock_get_crontab.return_value = (
            "# GitHub Classroom Assignment Auto-sync\n"
            "0 */4 * * * /path/to/sync\n"
            "# GitHub Classroom Assignment Auto-secrets\n"
            "0 2 * * * /path/to/secrets\n"
            "# Other job\n"
            "0 0 * * * /other/command\n"
        )
        mock_set_crontab.return_value = True

        result, message = cron_manager.remove_cron_job("all")

        assert result == CronOperationResult.SUCCESS
        assert "All assignment cron jobs removed" in message

        # Verify only non-assignment jobs remain
        call_args = mock_set_crontab.call_args[0][0]
        assert "GitHub Classroom Assignment Auto" not in call_args
        assert "# Other job" in call_args

    @patch('classdock.automation.cron_manager.CronManager._get_current_crontab')
    def test_remove_cron_job_all_not_found(self, mock_get_crontab, cron_manager):
        """Test removing all assignment jobs when none exist."""
        mock_get_crontab.return_value = (
            "# Other job\n"
            "0 0 * * * /other/command\n"
        )

        result, message = cron_manager.remove_cron_job("all")

        assert result == CronOperationResult.NOT_FOUND
        assert "No assignment cron jobs found" in message

    @patch('classdock.automation.cron_manager.CronManager._get_current_crontab')
    @patch('classdock.automation.cron_manager.CronManager._remove_crontab')
    def test_remove_cron_job_all_remove_entire_crontab(
        self, mock_remove_crontab, mock_get_crontab, cron_manager
    ):
        """Test removing all jobs when only assignment jobs exist."""
        mock_get_crontab.return_value = (
            "# GitHub Classroom Assignment Auto-sync\n"
            "0 */4 * * * /path/to/sync\n"
        )
        mock_remove_crontab.return_value = True

        result, message = cron_manager.remove_cron_job("all")

        assert result == CronOperationResult.SUCCESS
        mock_remove_crontab.assert_called_once()

    @patch('classdock.automation.cron_manager.CronManager.job_exists')
    def test_remove_cron_job_specific_not_found(self, mock_job_exists, cron_manager):
        """Test removing specific job when it doesn't exist."""
        mock_job_exists.return_value = False

        result, message = cron_manager.remove_cron_job(["sync"])

        assert result == CronOperationResult.NOT_FOUND
        # Handle both possible error messages: specific job not found vs no crontab exists
        assert "not found" in message or "No crontab exists" in message

    @patch('classdock.automation.cron_manager.CronManager.job_exists')
    @patch('classdock.automation.cron_manager.CronManager._get_current_crontab')
    @patch('classdock.automation.cron_manager.CronManager._set_crontab')
    def test_remove_cron_job_specific_success(
        self, mock_set_crontab, mock_get_crontab, mock_job_exists, cron_manager
    ):
        """Test removing specific job successfully."""
        mock_job_exists.return_value = True
        mock_get_crontab.return_value = (
            "# GitHub Classroom Assignment Auto-classdock-sync\n"
            "0 */4 * * * python -m classdock automation cron-sync 'assignment.conf' sync >/dev/null 2>&1\n"
            "# Other job\n"
            "0 0 * * * /other/command\n"
        )
        mock_set_crontab.return_value = True

        result, message = cron_manager.remove_cron_job(["sync"])

        assert result == CronOperationResult.SUCCESS
        assert "removed successfully" in message

        # Verify sync job is removed but other job remains
        call_args = mock_set_crontab.call_args[0][0]
        assert "Auto-classdock-sync" not in call_args
        assert "# Other job" in call_args


class TestCronStatus:
    """Test cron job status functionality."""

    @pytest.fixture
    def cron_manager(self):
        """Create a CronManager instance for testing."""
        return CronManager()

    @patch('classdock.automation.cron_manager.CronManager._get_current_crontab')
    @patch('classdock.automation.cron_manager.Path.exists')
    def test_get_cron_status_no_jobs(self, mock_exists, mock_get_crontab, cron_manager):
        """Test getting status when no cron jobs are installed."""
        mock_get_crontab.return_value = None
        mock_exists.return_value = False

        status = cron_manager.get_cron_status()

        assert isinstance(status, CronStatus)
        assert status.total_jobs == 0
        assert not status.has_jobs
        assert not status.log_file_exists
        assert status.log_file_path is None

    @patch('classdock.automation.cron_manager.CronManager._get_current_crontab')
    @patch('classdock.automation.cron_manager.Path.exists')
    def test_get_cron_status_with_jobs(self, mock_exists, mock_get_crontab, cron_manager):
        """Test getting status with installed cron jobs."""
        mock_get_crontab.return_value = (
            "# GitHub Classroom Assignment Auto-sync\n"
            "0 */4 * * * python -m classdock automation cron-sync 'assignment.conf' sync >/dev/null 2>&1\n"
            "# GitHub Classroom Assignment Auto-secrets\n"
            "0 2 * * * python -m classdock automation cron-sync 'assignment.conf' secrets >/dev/null 2>&1\n"
        )
        mock_exists.return_value = False

        status = cron_manager.get_cron_status()

        assert status.total_jobs == 2
        assert status.has_jobs
        assert len(status.installed_jobs) == 2

        # Check first job
        sync_job = status.installed_jobs[0]
        assert sync_job.steps == ["sync"]
        assert sync_job.schedule == "0 */4 * * *"
        assert sync_job.is_active

        # Check second job
        secrets_job = status.installed_jobs[1]
        assert secrets_job.steps == ["secrets"]
        assert secrets_job.schedule == "0 2 * * *"

    @patch('classdock.automation.cron_manager.CronManager._get_current_crontab')
    @patch('classdock.automation.cron_manager.Path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data="Log line 1\nLog line 2\nLog line 3\n")
    def test_get_cron_status_with_log_file(
        self, mock_file, mock_exists, mock_get_crontab, cron_manager
    ):
        """Test getting status with log file present."""
        mock_get_crontab.return_value = None
        mock_exists.return_value = True

        status = cron_manager.get_cron_status()

        assert status.log_file_exists
        assert status.log_file_path == cron_manager.log_file_path
        assert status.last_log_activity == "Log line 1\nLog line 2\nLog line 3"

    @patch('classdock.automation.cron_manager.subprocess.run')
    @patch('classdock.automation.cron_manager.Path.exists')
    @patch('classdock.automation.cron_manager.Path.stat')
    def test_show_logs_success(self, mock_stat, mock_exists, mock_subprocess, cron_manager):
        """Test showing logs successfully."""
        mock_exists.return_value = True
        mock_subprocess.return_value = Mock(
            returncode=0,
            stdout="Recent log entry 1\nRecent log entry 2\n"
        )

        # Mock file stats
        mock_stat_result = Mock()
        mock_stat_result.st_size = 1024
        mock_stat_result.st_mtime = datetime.now().timestamp()
        mock_stat.return_value = mock_stat_result

        success, output = cron_manager.show_logs()

        assert success
        assert "Recent log entry 1" in output
        assert "Recent Workflow Log Entries" in output
        assert "Log File Info" in output
        assert "1.0 KB" in output  # Size formatting

    @patch('classdock.automation.cron_manager.Path.exists')
    def test_show_logs_file_not_found(self, mock_exists, cron_manager):
        """Test showing logs when file doesn't exist."""
        mock_exists.return_value = False

        success, output = cron_manager.show_logs()

        assert not success
        assert "Log file not found" in output

    def test_list_default_schedules(self, cron_manager):
        """Test listing default schedules."""
        output = cron_manager.list_default_schedules()

        assert "Default schedules for workflow steps" in output
        assert "sync" in output
        assert "secrets" in output
        assert "cycle" in output
        assert "0 */4 * * *" in output  # Sync schedule
        assert "0 2 * * *" in output    # Secrets schedule
        assert "Examples:" in output


class TestCronManagerEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def cron_manager(self):
        """Create a CronManager instance for testing."""
        return CronManager()

    @patch('classdock.automation.cron_manager.CronManager.validate_prerequisites')
    @patch('classdock.automation.cron_manager.CronManager.validate_steps')
    @patch('classdock.automation.cron_manager.CronManager.validate_cron_schedule')
    @patch('classdock.automation.cron_manager.CronManager.job_exists')
    @patch('classdock.automation.cron_manager.CronManager._get_current_crontab')
    @patch('classdock.automation.cron_manager.CronManager._set_crontab')
    def test_install_cron_job_permission_error(
        self, mock_set_crontab, mock_get_crontab, mock_job_exists,
        mock_validate_schedule, mock_validate_steps, mock_validate_prereq,
        cron_manager
    ):
        """Test cron job installation with permission error."""
        # Mock successful validations
        mock_validate_prereq.return_value = CronValidationResult(True, [], [])
        mock_validate_steps.return_value = CronValidationResult(True, [], [])
        mock_validate_schedule.return_value = CronValidationResult(True, [
        ], [])
        mock_job_exists.return_value = False
        mock_get_crontab.return_value = ""

        # Mock permission error
        mock_set_crontab.side_effect = PermissionError("Permission denied")

        result, message = cron_manager.install_cron_job(["sync"])

        assert result == CronOperationResult.PERMISSION_ERROR
        assert "Permission denied" in message

    @patch('classdock.automation.cron_manager.CronManager._get_current_crontab')
    def test_remove_cron_job_permission_error(self, mock_get_crontab, cron_manager):
        """Test cron job removal with permission error."""
        mock_get_crontab.side_effect = PermissionError("Permission denied")

        result, message = cron_manager.remove_cron_job(["sync"])

        assert result == CronOperationResult.PERMISSION_ERROR
        assert "Permission denied" in message

    @patch('classdock.automation.cron_manager.subprocess.run')
    @patch('classdock.automation.cron_manager.Path.exists')
    def test_show_logs_subprocess_error(self, mock_exists, mock_subprocess, cron_manager):
        """Test showing logs with subprocess error."""
        mock_exists.return_value = True
        mock_subprocess.return_value = Mock(
            returncode=1,
            stderr="Permission denied"
        )

        success, output = cron_manager.show_logs()

        assert not success
        assert "Failed to read log file" in output
        assert "Permission denied" in output

    def test_cron_validation_result_properties(self):
        """Test CronValidationResult property methods."""
        # Test with errors
        result_with_errors = CronValidationResult(
            False, ["Error 1", "Error 2"], ["Warning 1"]
        )
        assert result_with_errors.has_errors
        assert result_with_errors.has_warnings

        # Test without errors
        result_no_errors = CronValidationResult(True, [], [])
        assert not result_no_errors.has_errors
        assert not result_no_errors.has_warnings

    def test_cron_job_steps_key(self):
        """Test CronJob steps_key property."""
        job = CronJob(
            steps=["sync", "secrets"],
            schedule="0 1 * * *",
            command="/test/command",
            comment="# Test comment"
        )
        assert job.steps_key == "sync-secrets"

    def test_cron_status_has_jobs(self):
        """Test CronStatus has_jobs property."""
        # Test with jobs
        status_with_jobs = CronStatus(
            installed_jobs=[Mock()],
            total_jobs=1,
            log_file_exists=False,
            log_file_path=None,
            last_log_activity=None
        )
        assert status_with_jobs.has_jobs

        # Test without jobs
        status_no_jobs = CronStatus(
            installed_jobs=[],
            total_jobs=0,
            log_file_exists=False,
            log_file_path=None,
            last_log_activity=None
        )
        assert not status_no_jobs.has_jobs
