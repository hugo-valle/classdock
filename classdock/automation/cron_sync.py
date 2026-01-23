"""
Automated Workflow Cron Job Manager for GitHub Classroom Assignments.

This module provides automated synchronization and workflow execution designed 
to run as scheduled tasks (cron jobs) for assignment management workflows.

Key capabilities:
- Execute workflow steps (sync, discover, secrets, assist, cycle)
- Comprehensive logging with automatic log rotation
- Configuration validation and error handling
- Support for multiple workflow steps in sequence
- Cron-friendly execution with proper exit codes
- Integration with assignment orchestrator functionality
"""

import sys
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass

from ..config import GlobalConfig
from ..utils import get_logger


class WorkflowStep(Enum):
    """Valid workflow steps for automated execution."""
    SYNC = "sync"
    DISCOVER = "discover"
    SECRETS = "secrets"
    ASSIST = "assist"
    CYCLE = "cycle"


class CronSyncResult(Enum):
    """Results of cron sync execution."""
    SUCCESS = "success"
    PARTIAL_FAILURE = "partial_failure"
    COMPLETE_FAILURE = "complete_failure"
    CONFIGURATION_ERROR = "configuration_error"
    ENVIRONMENT_ERROR = "environment_error"


@dataclass
class StepResult:
    """Result of executing a single workflow step."""
    step: WorkflowStep
    success: bool
    exit_code: int
    message: str
    execution_time: float


@dataclass
class CronSyncExecutionResult:
    """Comprehensive result of cron sync execution."""
    overall_result: CronSyncResult
    steps_executed: List[StepResult]
    total_execution_time: float
    log_file_path: str
    error_summary: Optional[str] = None


class CronSyncManager:
    """
    Manager for automated workflow cron job execution.

    Provides functionality to execute assignment workflow steps as scheduled
    tasks with comprehensive logging, error handling, and monitoring.
    """

    # Log file size limit (10MB)
    LOG_SIZE_LIMIT = 10 * 1024 * 1024

    def __init__(self, global_config: Optional[GlobalConfig] = None,
                 assignment_root: Optional[Path] = None):
        """
        Initialize the CronSyncManager.

        Args:
            global_config: Global configuration instance
            assignment_root: Root directory of the assignment repository
        """
        self.global_config = global_config or GlobalConfig()
        self.assignment_root = assignment_root or Path.cwd()
        self.logger = get_logger("cron_sync")

        # Set up log file path
        self.log_dir = self.assignment_root / "tools" / "generated"
        self.log_file = self.log_dir / "cron-workflow.log"

        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def validate_environment(self) -> Tuple[bool, str]:
        """
        Validate the execution environment for cron sync.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if we're in a git repository
        git_dir = self.assignment_root / ".git"
        if not git_dir.exists():
            return False, f"Not in a git repository: {self.assignment_root}"

        # Check if assignment root is accessible
        if not self.assignment_root.exists():
            return False, f"Assignment root does not exist: {self.assignment_root}"

        # Check if log directory can be created/accessed
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            if not self.log_dir.exists():
                return False, f"Cannot create log directory: {self.log_dir}"
        except Exception as e:
            return False, f"Log directory setup failed: {e}"

        return True, "Environment validation successful"

    def validate_steps(self, steps: List[str]) -> Tuple[bool, List[WorkflowStep], str]:
        """
        Validate and convert step names to WorkflowStep enums.

        Args:
            steps: List of step names to validate

        Returns:
            Tuple of (is_valid, valid_steps, error_message)
        """
        if not steps:
            # Default to sync step for backward compatibility
            return True, [WorkflowStep.SYNC], "Using default sync step"

        valid_steps = []
        invalid_steps = []

        for step_name in steps:
            try:
                step = WorkflowStep(step_name.lower())
                valid_steps.append(step)
            except ValueError:
                invalid_steps.append(step_name)

        if invalid_steps:
            valid_step_names = [step.value for step in WorkflowStep]
            return False, [], (
                f"Invalid step names: {invalid_steps}. "
                f"Valid steps are: {valid_step_names}"
            )

        return True, valid_steps, f"Validated {len(valid_steps)} steps"

    def rotate_log_if_needed(self) -> bool:
        """
        Rotate log file if it exceeds size limit.

        Returns:
            True if log was rotated, False otherwise
        """
        if not self.log_file.exists():
            return False

        try:
            file_size = self.log_file.stat().st_size
            if file_size > self.LOG_SIZE_LIMIT:
                old_log = self.log_file.with_suffix('.log.old')
                if old_log.exists():
                    old_log.unlink()  # Remove old backup
                self.log_file.rename(old_log)
                self.log_cron("INFO: Log file rotated due to size limit")
                return True
        except Exception as e:
            self.log_cron(f"WARNING: Failed to rotate log file: {e}")

        return False

    def log_cron(self, message: str) -> None:
        """
        Log message to the cron log file with timestamp.

        Args:
            message: Message to log
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}\n"

        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            # Fallback to console if file logging fails
            print(f"LOG ERROR: {e}", file=sys.stderr)
            print(log_entry.strip(), file=sys.stderr)

    def execute_workflow_step(self, step: WorkflowStep, verbose: bool = True) -> StepResult:
        """
        Execute a single workflow step using the assignment orchestrator.

        Args:
            step: Workflow step to execute
            verbose: Enable verbose output

        Returns:
            StepResult with execution details
        """
        start_time = time.time()
        self.log_cron(f"INFO: Executing step: {step.value}")

        try:
            # Import the orchestrator manager
            from ..assignments.orchestrator import AssignmentOrchestrator

            # Initialize orchestrator
            orchestrator = AssignmentOrchestrator(
                self.global_config, self.assignment_root)

            # Execute the specific step
            result, message = orchestrator.execute_step(
                step=step.value,
                auto_confirm=True,  # Equivalent to --yes flag
                verbose=verbose
            )

            execution_time = time.time() - start_time

            if result:
                self.log_cron(
                    f"SUCCESS: Step '{step.value}' completed successfully in {execution_time:.2f}s")
                return StepResult(
                    step=step,
                    success=True,
                    exit_code=0,
                    message=message,
                    execution_time=execution_time
                )
            else:
                self.log_cron(f"ERROR: Step '{step.value}' failed: {message}")
                return StepResult(
                    step=step,
                    success=False,
                    exit_code=1,
                    message=message,
                    execution_time=execution_time
                )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Exception during step execution: {e}"
            self.log_cron(f"ERROR: {error_msg}")

            return StepResult(
                step=step,
                success=False,
                exit_code=2,
                message=error_msg,
                execution_time=execution_time
            )

    def execute_cron_sync(self,
                          steps: List[str],
                          verbose: bool = True,
                          stop_on_failure: bool = False) -> CronSyncExecutionResult:
        """
        Execute the complete cron sync workflow.

        Args:
            steps: List of workflow step names to execute
            verbose: Enable verbose output
            stop_on_failure: Stop execution on first failure

        Returns:
            CronSyncExecutionResult with comprehensive execution details
        """
        start_time = time.time()

        # Rotate log if needed
        self.rotate_log_if_needed()

        self.log_cron("INFO: Starting automated workflow job")
        self.log_cron(f"INFO: Assignment root: {self.assignment_root}")
        self.log_cron(f"INFO: Executing steps: {steps}")

        # Validate environment
        env_valid, env_message = self.validate_environment()
        if not env_valid:
            self.log_cron(
                f"ERROR: Environment validation failed: {env_message}")
            return CronSyncExecutionResult(
                overall_result=CronSyncResult.ENVIRONMENT_ERROR,
                steps_executed=[],
                total_execution_time=time.time() - start_time,
                log_file_path=str(self.log_file),
                error_summary=env_message
            )

        # Validate and parse steps
        steps_valid, workflow_steps, steps_message = self.validate_steps(steps)
        if not steps_valid:
            self.log_cron(f"ERROR: Step validation failed: {steps_message}")
            return CronSyncExecutionResult(
                overall_result=CronSyncResult.CONFIGURATION_ERROR,
                steps_executed=[],
                total_execution_time=time.time() - start_time,
                log_file_path=str(self.log_file),
                error_summary=steps_message
            )

        self.log_cron(f"INFO: {steps_message}")

        # Execute workflow steps
        step_results = []
        overall_success = True

        for step in workflow_steps:
            result = self.execute_workflow_step(step, verbose)
            step_results.append(result)

            if not result.success:
                overall_success = False
                if stop_on_failure:
                    self.log_cron(
                        f"INFO: Stopping execution due to failure in step: {step.value}")
                    break

        # Determine overall result
        if overall_success:
            overall_result = CronSyncResult.SUCCESS
            self.log_cron("SUCCESS: All workflow steps completed successfully")
        elif any(result.success for result in step_results):
            overall_result = CronSyncResult.PARTIAL_FAILURE
            failed_steps = [
                r.step.value for r in step_results if not r.success]
            self.log_cron(
                f"WARNING: Some workflow steps failed: {failed_steps}")
        else:
            overall_result = CronSyncResult.COMPLETE_FAILURE
            self.log_cron("ERROR: All workflow steps failed")

        total_time = time.time() - start_time
        self.log_cron(
            f"INFO: Automated workflow job completed in {total_time:.2f}s")

        # Generate error summary if needed
        error_summary = None
        if overall_result != CronSyncResult.SUCCESS:
            failed_steps = [r for r in step_results if not r.success]
            if failed_steps:
                error_summary = f"Failed steps: {[r.step.value for r in failed_steps]}"

        return CronSyncExecutionResult(
            overall_result=overall_result,
            steps_executed=step_results,
            total_execution_time=total_time,
            log_file_path=str(self.log_file),
            error_summary=error_summary
        )

    def get_log_tail(self, lines: int = 50) -> List[str]:
        """
        Get the last N lines from the cron log file.

        Args:
            lines: Number of lines to retrieve

        Returns:
            List of log lines
        """
        if not self.log_file.exists():
            return []

        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                return [line.rstrip() for line in all_lines[-lines:]]
        except Exception as e:
            self.logger.error(f"Failed to read log file: {e}")
            return [f"Error reading log file: {e}"]

    def get_log_stats(self) -> dict:
        """
        Get statistics about the cron log file.

        Returns:
            Dictionary with log file statistics
        """
        if not self.log_file.exists():
            return {
                "exists": False,
                "size": 0,
                "lines": 0,
                "last_modified": None
            }

        try:
            stat_info = self.log_file.stat()

            # Count lines
            with open(self.log_file, 'r', encoding='utf-8') as f:
                line_count = sum(1 for _ in f)

            return {
                "exists": True,
                "size": stat_info.st_size,
                "size_mb": round(stat_info.st_size / (1024 * 1024), 2),
                "lines": line_count,
                "last_modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                "path": str(self.log_file)
            }
        except Exception as e:
            return {
                "exists": True,
                "error": str(e)
            }

    def clear_log(self) -> bool:
        """
        Clear the cron log file.

        Returns:
            True if successful, False otherwise
        """
        try:
            if self.log_file.exists():
                self.log_file.unlink()
            self.log_cron("INFO: Log file cleared")
            return True
        except Exception as e:
            self.logger.error(f"Failed to clear log file: {e}")
            return False
