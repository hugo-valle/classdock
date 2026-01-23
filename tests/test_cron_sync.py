"""
Test suite for the CronSyncManager class.

Tests automated workflow cron job functionality including step execution,
logging, error handling, and environment validation.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from datetime import datetime

from classdock.automation.cron_sync import (
    CronSyncManager, WorkflowStep, CronSyncResult, StepResult,
    CronSyncExecutionResult
)
from classdock.config import GlobalConfig


class TestWorkflowStep:
    """Test WorkflowStep enum functionality."""

    def test_workflow_step_values(self):
        """Test all workflow step values are correct."""
        assert WorkflowStep.SYNC.value == "sync"
        assert WorkflowStep.DISCOVER.value == "discover"
        assert WorkflowStep.SECRETS.value == "secrets"
        assert WorkflowStep.ASSIST.value == "assist"
        assert WorkflowStep.CYCLE.value == "cycle"

    def test_workflow_step_from_string(self):
        """Test creating WorkflowStep from string values."""
        assert WorkflowStep("sync") == WorkflowStep.SYNC
        assert WorkflowStep("discover") == WorkflowStep.DISCOVER
        assert WorkflowStep("secrets") == WorkflowStep.SECRETS
        assert WorkflowStep("assist") == WorkflowStep.ASSIST
        assert WorkflowStep("cycle") == WorkflowStep.CYCLE

    def test_workflow_step_invalid(self):
        """Test invalid workflow step raises ValueError."""
        with pytest.raises(ValueError):
            WorkflowStep("invalid")


class TestStepResult:
    """Test StepResult dataclass functionality."""

    def test_step_result_creation(self):
        """Test creating StepResult with all fields."""
        result = StepResult(
            step=WorkflowStep.SYNC,
            success=True,
            exit_code=0,
            message="Step completed successfully",
            execution_time=1.5
        )

        assert result.step == WorkflowStep.SYNC
        assert result.success is True
        assert result.exit_code == 0
        assert result.message == "Step completed successfully"
        assert result.execution_time == 1.5


class TestCronSyncExecutionResult:
    """Test CronSyncExecutionResult dataclass functionality."""

    def test_execution_result_creation(self):
        """Test creating CronSyncExecutionResult with all fields."""
        step_results = [
            StepResult(WorkflowStep.SYNC, True, 0, "Success", 1.0),
            StepResult(WorkflowStep.SECRETS, False, 1, "Failed", 0.5)
        ]

        result = CronSyncExecutionResult(
            overall_result=CronSyncResult.PARTIAL_FAILURE,
            steps_executed=step_results,
            total_execution_time=2.5,
            log_file_path="/path/to/log",
            error_summary="Some steps failed"
        )

        assert result.overall_result == CronSyncResult.PARTIAL_FAILURE
        assert len(result.steps_executed) == 2
        assert result.total_execution_time == 2.5
        assert result.log_file_path == "/path/to/log"
        assert result.error_summary == "Some steps failed"


class TestCronSyncManager:
    """Test the CronSyncManager class initialization and basic functionality."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock GlobalConfig for testing."""
        config = Mock(spec=GlobalConfig)
        return config

    @pytest.fixture
    def temp_assignment_root(self, tmp_path):
        """Create a temporary assignment root directory."""
        # Create a git directory to simulate git repository
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        return tmp_path

    @pytest.fixture
    def cron_manager(self, mock_config, temp_assignment_root):
        """Create a CronSyncManager instance for testing."""
        return CronSyncManager(mock_config, temp_assignment_root)

    def test_init_with_config(self, mock_config, temp_assignment_root):
        """Test CronSyncManager initialization with config."""
        manager = CronSyncManager(mock_config, temp_assignment_root)

        assert manager.global_config == mock_config
        assert manager.assignment_root == temp_assignment_root
        assert manager.log_dir == temp_assignment_root / "tools" / "generated"
        assert manager.log_file == manager.log_dir / "cron-workflow.log"

    def test_init_without_config(self):
        """Test CronSyncManager initialization without config."""
        with patch('classdock.automation.cron_sync.GlobalConfig') as mock_global_config:
            manager = CronSyncManager()
            mock_global_config.assert_called_once()
            assert manager.assignment_root == Path.cwd()

    def test_log_size_limit_constant(self, cron_manager):
        """Test log size limit constant."""
        assert cron_manager.LOG_SIZE_LIMIT == 10 * 1024 * 1024  # 10MB


class TestEnvironmentValidation:
    """Test environment validation functionality."""

    @pytest.fixture
    def cron_manager(self, tmp_path):
        """Create cron manager with temp directory."""
        config = Mock(spec=GlobalConfig)
        return CronSyncManager(config, tmp_path)

    def test_validate_environment_success(self, cron_manager, tmp_path):
        """Test successful environment validation."""
        # Create git directory
        (tmp_path / ".git").mkdir()

        valid, message = cron_manager.validate_environment()

        assert valid
        assert "successful" in message.lower()

    def test_validate_environment_no_git(self, cron_manager):
        """Test environment validation when not in git repository."""
        valid, message = cron_manager.validate_environment()

        assert not valid
        assert "Not in a git repository" in message

    def test_validate_environment_missing_assignment_root(self, tmp_path):
        """Test environment validation with missing assignment root."""
        config = Mock(spec=GlobalConfig)
        nonexistent_path = tmp_path / "nonexistent"
        manager = CronSyncManager(config, nonexistent_path)

        valid, message = manager.validate_environment()

        assert not valid
        assert "Not in a git repository" in message

    def test_validate_environment_log_directory_creation(self, tmp_path):
        """Test log directory creation during validation."""
        config = Mock(spec=GlobalConfig)
        manager = CronSyncManager(config, tmp_path)

        # Create git directory
        (tmp_path / ".git").mkdir()

        # Ensure log directory doesn't exist initially
        log_dir = tmp_path / "tools" / "generated"
        if log_dir.exists():
            import shutil
            shutil.rmtree(log_dir)

        valid, message = manager.validate_environment()

        assert valid
        assert log_dir.exists()


class TestStepValidation:
    """Test workflow step validation functionality."""

    @pytest.fixture
    def cron_manager(self, tmp_path):
        """Create cron manager for testing."""
        config = Mock(spec=GlobalConfig)
        return CronSyncManager(config, tmp_path)

    def test_validate_steps_empty_list(self, cron_manager):
        """Test validating empty steps list defaults to sync."""
        valid, steps, message = cron_manager.validate_steps([])

        assert valid
        assert steps == [WorkflowStep.SYNC]
        assert "default sync step" in message

    def test_validate_steps_valid_single(self, cron_manager):
        """Test validating single valid step."""
        valid, steps, message = cron_manager.validate_steps(["secrets"])

        assert valid
        assert steps == [WorkflowStep.SECRETS]
        assert "Validated 1 steps" in message

    def test_validate_steps_valid_multiple(self, cron_manager):
        """Test validating multiple valid steps."""
        valid, steps, message = cron_manager.validate_steps(
            ["sync", "secrets", "cycle"])

        assert valid
        assert steps == [WorkflowStep.SYNC,
                         WorkflowStep.SECRETS, WorkflowStep.CYCLE]
        assert "Validated 3 steps" in message

    def test_validate_steps_case_insensitive(self, cron_manager):
        """Test step validation is case insensitive."""
        valid, steps, message = cron_manager.validate_steps(
            ["SYNC", "Secrets", "cYcLe"])

        assert valid
        assert steps == [WorkflowStep.SYNC,
                         WorkflowStep.SECRETS, WorkflowStep.CYCLE]

    def test_validate_steps_invalid_single(self, cron_manager):
        """Test validating invalid step."""
        valid, steps, message = cron_manager.validate_steps(["invalid"])

        assert not valid
        assert steps == []
        assert "Invalid step names: ['invalid']" in message
        assert "Valid steps are:" in message

    def test_validate_steps_mixed_valid_invalid(self, cron_manager):
        """Test validating mix of valid and invalid steps."""
        valid, steps, message = cron_manager.validate_steps(
            ["sync", "invalid", "secrets", "bad"])

        assert not valid
        assert steps == []
        assert "Invalid step names: ['invalid', 'bad']" in message


class TestLogManagement:
    """Test logging and log management functionality."""

    @pytest.fixture
    def cron_manager(self, tmp_path):
        """Create cron manager for testing."""
        config = Mock(spec=GlobalConfig)
        manager = CronSyncManager(config, tmp_path)
        manager.log_dir.mkdir(parents=True, exist_ok=True)
        return manager

    def test_log_cron_creates_log_entry(self, cron_manager):
        """Test cron logging creates properly formatted log entry."""
        test_message = "Test log message"

        cron_manager.log_cron(test_message)

        assert cron_manager.log_file.exists()
        content = cron_manager.log_file.read_text()
        assert test_message in content
        assert datetime.now().strftime('%Y-%m-%d') in content

    def test_log_cron_multiple_messages(self, cron_manager):
        """Test multiple log messages are appended."""
        messages = ["First message", "Second message", "Third message"]

        for msg in messages:
            cron_manager.log_cron(msg)

        content = cron_manager.log_file.read_text()
        for msg in messages:
            assert msg in content

    def test_rotate_log_if_needed_small_file(self, cron_manager):
        """Test log rotation when file is under size limit."""
        # Create small log file
        cron_manager.log_cron("Small log entry")

        rotated = cron_manager.rotate_log_if_needed()

        assert not rotated
        assert cron_manager.log_file.exists()

    def test_rotate_log_if_needed_large_file(self, cron_manager):
        """Test log rotation when file exceeds size limit."""
        # Create large log file by writing many entries
        large_content = "x" * (cron_manager.LOG_SIZE_LIMIT + 1000)
        cron_manager.log_file.write_text(large_content)

        rotated = cron_manager.rotate_log_if_needed()

        assert rotated
        # Original file should be rotated
        old_log = cron_manager.log_file.with_suffix('.log.old')
        assert old_log.exists()
        # New log should exist with rotation message
        assert cron_manager.log_file.exists()

    def test_rotate_log_replaces_old_backup(self, cron_manager):
        """Test log rotation replaces existing old backup."""
        # Create large log file
        large_content = "x" * (cron_manager.LOG_SIZE_LIMIT + 1000)
        cron_manager.log_file.write_text(large_content)

        # Create existing old backup
        old_log = cron_manager.log_file.with_suffix('.log.old')
        old_log.write_text("old backup content")

        cron_manager.rotate_log_if_needed()

        # Old backup should be replaced with current log content
        assert old_log.exists()
        assert "x" * 1000 in old_log.read_text()  # Contains part of large content

    def test_log_cron_file_error_fallback(self, cron_manager, capsys):
        """Test log_cron fallback to stderr when file writing fails."""
        # Make log file directory read-only to cause write error
        cron_manager.log_dir.chmod(0o444)

        try:
            cron_manager.log_cron("Test message")

            # Should fallback to stderr
            captured = capsys.readouterr()
            assert "LOG ERROR:" in captured.err
            assert "Test message" in captured.err
        finally:
            # Restore permissions
            cron_manager.log_dir.chmod(0o755)


class TestLogUtilities:
    """Test log utility functions."""

    @pytest.fixture
    def cron_manager(self, tmp_path):
        """Create cron manager for testing."""
        config = Mock(spec=GlobalConfig)
        manager = CronSyncManager(config, tmp_path)
        manager.log_dir.mkdir(parents=True, exist_ok=True)
        return manager

    def test_get_log_tail_no_file(self, cron_manager):
        """Test getting log tail when file doesn't exist."""
        lines = cron_manager.get_log_tail()
        assert lines == []

    def test_get_log_tail_with_content(self, cron_manager):
        """Test getting log tail with content."""
        # Create log with multiple lines
        for i in range(10):
            cron_manager.log_cron(f"Log line {i}")

        lines = cron_manager.get_log_tail(5)

        assert len(lines) == 5
        assert "Log line 9" in lines[-1]
        assert "Log line 5" in lines[0]

    def test_get_log_tail_fewer_lines_than_requested(self, cron_manager):
        """Test getting log tail when file has fewer lines than requested."""
        # Create log with only 3 lines
        for i in range(3):
            cron_manager.log_cron(f"Log line {i}")

        lines = cron_manager.get_log_tail(10)

        assert len(lines) == 3

    def test_get_log_stats_no_file(self, cron_manager):
        """Test getting log stats when file doesn't exist."""
        stats = cron_manager.get_log_stats()

        assert stats["exists"] is False
        assert stats["size"] == 0
        assert stats["lines"] == 0
        assert stats["last_modified"] is None

    def test_get_log_stats_with_file(self, cron_manager):
        """Test getting log stats with existing file."""
        # Create log content
        for i in range(5):
            cron_manager.log_cron(f"Log line {i}")

        stats = cron_manager.get_log_stats()

        assert stats["exists"] is True
        assert stats["size"] > 0
        assert stats["size_mb"] >= 0.0
        assert stats["lines"] == 5
        assert stats["last_modified"] is not None
        assert stats["path"] == str(cron_manager.log_file)

    def test_clear_log_success(self, cron_manager):
        """Test successful log clearing."""
        # Create log content
        cron_manager.log_cron("Test content")
        assert cron_manager.log_file.exists()

        success = cron_manager.clear_log()

        assert success
        # File should exist again with clear message
        assert cron_manager.log_file.exists()
        content = cron_manager.log_file.read_text()
        assert "Log file cleared" in content

    def test_clear_log_no_file(self, cron_manager):
        """Test clearing log when file doesn't exist."""
        success = cron_manager.clear_log()

        assert success
        assert cron_manager.log_file.exists()  # Created with clear message


class TestWorkflowStepExecution:
    """Test individual workflow step execution."""

    @pytest.fixture
    def cron_manager(self, tmp_path):
        """Create cron manager for testing."""
        config = Mock(spec=GlobalConfig)
        manager = CronSyncManager(config, tmp_path)
        manager.log_dir.mkdir(parents=True, exist_ok=True)
        return manager

    @patch('classdock.automation.cron_sync.time.time')
    def test_execute_workflow_step_success(self, mock_time, cron_manager):
        """Test successful workflow step execution."""
        # Mock time progression
        mock_time.side_effect = [1000.0, 1002.5]  # 2.5 seconds execution

        with patch('classdock.assignments.orchestrator.AssignmentOrchestrator') as mock_orchestrator_class:
            mock_orchestrator = Mock()
            mock_orchestrator.execute_step.return_value = (
                True, "Step completed successfully")
            mock_orchestrator_class.return_value = mock_orchestrator

            result = cron_manager.execute_workflow_step(WorkflowStep.SYNC)

        assert result.step == WorkflowStep.SYNC
        assert result.success is True
        assert result.exit_code == 0
        assert result.message == "Step completed successfully"
        assert result.execution_time == 2.5

    @patch('classdock.automation.cron_sync.time.time')
    def test_execute_workflow_step_failure(self, mock_time, cron_manager):
        """Test workflow step execution failure."""
        mock_time.side_effect = [1000.0, 1001.0]  # 1 second execution

        with patch('classdock.assignments.orchestrator.AssignmentOrchestrator') as mock_orchestrator_class:
            mock_orchestrator = Mock()
            mock_orchestrator.execute_step.return_value = (
                False, "Step failed")
            mock_orchestrator_class.return_value = mock_orchestrator

            result = cron_manager.execute_workflow_step(WorkflowStep.SECRETS)

        assert result.step == WorkflowStep.SECRETS
        assert result.success is False
        assert result.exit_code == 1
        assert result.message == "Step failed"
        assert result.execution_time == 1.0

    @patch('classdock.automation.cron_sync.time.time')
    def test_execute_workflow_step_exception(self, mock_time, cron_manager):
        """Test workflow step execution with exception."""
        mock_time.side_effect = [1000.0, 1000.5]  # 0.5 seconds execution

        with patch('classdock.assignments.orchestrator.AssignmentOrchestrator') as mock_orchestrator_class:
            mock_orchestrator_class.side_effect = Exception("Import error")

            result = cron_manager.execute_workflow_step(WorkflowStep.CYCLE)

        assert result.step == WorkflowStep.CYCLE
        assert result.success is False
        assert result.exit_code == 2
        assert "Exception during step execution" in result.message
        assert result.execution_time == 0.5


class TestCronSyncExecution:
    """Test complete cron sync workflow execution."""

    @pytest.fixture
    def cron_manager(self, tmp_path):
        """Create cron manager for testing."""
        config = Mock(spec=GlobalConfig)
        manager = CronSyncManager(config, tmp_path)
        # Create git directory
        (tmp_path / ".git").mkdir()
        manager.log_dir.mkdir(parents=True, exist_ok=True)
        return manager

    @patch('classdock.automation.cron_sync.time.time')
    def test_execute_cron_sync_success_all_steps(self, mock_time, cron_manager):
        """Test successful execution of all steps."""
        mock_time.side_effect = [1000.0, 1010.0]  # 10 seconds total

        with patch.object(cron_manager, 'execute_workflow_step') as mock_execute:
            mock_execute.side_effect = [
                StepResult(WorkflowStep.SYNC, True, 0, "Sync success", 2.0),
                StepResult(WorkflowStep.SECRETS, True,
                           0, "Secrets success", 3.0)
            ]

            result = cron_manager.execute_cron_sync(["sync", "secrets"])

        assert result.overall_result == CronSyncResult.SUCCESS
        assert len(result.steps_executed) == 2
        assert result.total_execution_time == 10.0
        assert result.error_summary is None

    @patch('classdock.automation.cron_sync.time.time')
    def test_execute_cron_sync_partial_failure(self, mock_time, cron_manager):
        """Test execution with some step failures."""
        mock_time.side_effect = [1000.0, 1008.0]  # 8 seconds total

        with patch.object(cron_manager, 'execute_workflow_step') as mock_execute:
            mock_execute.side_effect = [
                StepResult(WorkflowStep.SYNC, True, 0, "Sync success", 2.0),
                StepResult(WorkflowStep.SECRETS, False,
                           1, "Secrets failed", 1.0),
                StepResult(WorkflowStep.CYCLE, True, 0, "Cycle success", 3.0)
            ]

            result = cron_manager.execute_cron_sync(
                ["sync", "secrets", "cycle"])

        assert result.overall_result == CronSyncResult.PARTIAL_FAILURE
        assert len(result.steps_executed) == 3
        assert "Failed steps: ['secrets']" in result.error_summary

    @patch('classdock.automation.cron_sync.time.time')
    def test_execute_cron_sync_complete_failure(self, mock_time, cron_manager):
        """Test execution with all step failures."""
        mock_time.side_effect = [1000.0, 1005.0]  # 5 seconds total

        with patch.object(cron_manager, 'execute_workflow_step') as mock_execute:
            mock_execute.side_effect = [
                StepResult(WorkflowStep.SYNC, False, 1, "Sync failed", 2.0),
                StepResult(WorkflowStep.SECRETS, False,
                           1, "Secrets failed", 1.0)
            ]

            result = cron_manager.execute_cron_sync(["sync", "secrets"])

        assert result.overall_result == CronSyncResult.COMPLETE_FAILURE
        assert "Failed steps: ['sync', 'secrets']" in result.error_summary

    def test_execute_cron_sync_environment_error(self, tmp_path):
        """Test execution with environment validation error."""
        config = Mock(spec=GlobalConfig)
        # Don't create git directory to trigger environment error
        manager = CronSyncManager(config, tmp_path)

        result = manager.execute_cron_sync(["sync"])

        assert result.overall_result == CronSyncResult.ENVIRONMENT_ERROR
        assert len(result.steps_executed) == 0
        assert "Not in a git repository" in result.error_summary

    def test_execute_cron_sync_configuration_error(self, cron_manager):
        """Test execution with step validation error."""
        result = cron_manager.execute_cron_sync(["invalid_step"])

        assert result.overall_result == CronSyncResult.CONFIGURATION_ERROR
        assert len(result.steps_executed) == 0
        assert "Invalid step names" in result.error_summary

    @patch('classdock.automation.cron_sync.time.time')
    def test_execute_cron_sync_stop_on_failure(self, mock_time, cron_manager):
        """Test execution with stop on failure enabled."""
        mock_time.side_effect = [1000.0, 1003.0]  # 3 seconds total

        with patch.object(cron_manager, 'execute_workflow_step') as mock_execute:
            mock_execute.side_effect = [
                StepResult(WorkflowStep.SYNC, False, 1, "Sync failed", 1.0)
            ]

            result = cron_manager.execute_cron_sync(
                ["sync", "secrets", "cycle"],
                stop_on_failure=True
            )

        assert result.overall_result == CronSyncResult.COMPLETE_FAILURE
        assert len(result.steps_executed) == 1  # Only first step executed
        assert mock_execute.call_count == 1

    @patch('classdock.automation.cron_sync.time.time')
    def test_execute_cron_sync_default_step(self, mock_time, cron_manager):
        """Test execution with empty steps list defaults to sync."""
        mock_time.side_effect = [1000.0, 1002.0]  # 2 seconds total

        with patch.object(cron_manager, 'execute_workflow_step') as mock_execute:
            mock_execute.return_value = StepResult(
                WorkflowStep.SYNC, True, 0, "Success", 1.0)

            result = cron_manager.execute_cron_sync([])

        assert result.overall_result == CronSyncResult.SUCCESS
        assert len(result.steps_executed) == 1
        assert result.steps_executed[0].step == WorkflowStep.SYNC
