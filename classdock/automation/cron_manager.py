"""
Cron job management for automated GitHub Classroom workflows.

This module provides Python-based cron job management,
handling cron job installation, removal, status checking, and validation
for automated assignment workflow management.
"""

import subprocess
import tempfile
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple, Union
from datetime import datetime

from ..config import GlobalConfig
from ..utils import get_logger

logger = get_logger("automation.cron_manager")


class CronJobType(Enum):
    """Supported cron job workflow types."""
    SYNC = "sync"
    DISCOVER = "discover"
    SECRETS = "secrets"
    ASSIST = "assist"
    CYCLE = "cycle"


class CronOperationResult(Enum):
    """Results of cron operations."""
    SUCCESS = "success"
    ALREADY_EXISTS = "already_exists"
    NOT_FOUND = "not_found"
    PERMISSION_ERROR = "permission_error"
    VALIDATION_ERROR = "validation_error"
    SYSTEM_ERROR = "system_error"


@dataclass
class CronJob:
    """Represents a single cron job entry."""
    steps: List[str]
    schedule: str
    command: str
    comment: str
    is_active: bool = True

    @property
    def steps_key(self) -> str:
        """Get unique key for the job steps."""
        return "-".join(self.steps)


@dataclass
class CronValidationResult:
    """Result of cron job validation."""
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


@dataclass
class CronStatus:
    """Status information for cron jobs."""
    installed_jobs: List[CronJob]
    total_jobs: int
    log_file_exists: bool
    log_file_path: Optional[Path]
    last_log_activity: Optional[str]

    @property
    def has_jobs(self) -> bool:
        """Check if any jobs are installed."""
        return self.total_jobs > 0


class CronManager:
    """Manages cron jobs for automated GitHub Classroom workflows."""

    def __init__(self, global_config: Optional[GlobalConfig] = None):
        """Initialize cron manager with configuration."""
        self.global_config = global_config or GlobalConfig()

        # Default schedules for different workflow types
        self.default_schedules = {
            CronJobType.SYNC: "0 */4 * * *",      # Every 4 hours
            CronJobType.SECRETS: "0 2 * * *",     # Daily at 2 AM
            CronJobType.CYCLE: "0 6 * * 0",       # Weekly on Sunday at 6 AM
            CronJobType.DISCOVER: "0 1 * * *",    # Daily at 1 AM
            CronJobType.ASSIST: "0 3 * * 0"       # Weekly on Sunday at 3 AM
        }

        # Configuration constants
        self.cron_comment_prefix = "# GitHub Classroom Assignment Auto"
        self.cron_script_path = self._get_cron_script_path()
        self.log_file_path = self._get_log_file_path()

    def _get_cron_script_path(self) -> Path:
        """Get path to the Python cron sync command."""
        # Return current working directory since we'll use python -m classdock
        return Path.cwd()

    def _get_log_file_path(self) -> Path:
        """Get path to the cron workflow log file."""
        # Use current working directory + tools/generated
        return Path.cwd() / "tools" / "generated" / "cron-workflow.log"

    def _get_assignment_config_path(self) -> Path:
        """Get path to the assignment configuration file."""
        return Path.cwd() / "assignment.conf"

    def validate_prerequisites(self) -> CronValidationResult:
        """Validate prerequisites for cron job management."""
        errors = []
        warnings = []

        # Check if working directory exists (Python validation)
        if not self.cron_script_path.exists():
            errors.append(
                f"Working directory not found: {self.cron_script_path}")

        # Check if assignment config exists
        assignment_conf = self._get_assignment_config_path()
        if not assignment_conf.exists():
            warnings.append(
                f"Assignment configuration not found: {assignment_conf}")

        # Check cron service availability
        try:
            subprocess.run(
                ["crontab", "-l"],
                capture_output=True,
                text=True,
                timeout=10
            )
            # Command succeeds even if no crontab exists (returns specific error)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            errors.append(
                "Crontab command not available or system cron not running")
        except Exception as e:
            warnings.append(f"Could not verify cron service: {e}")

        # Check log directory writability
        log_dir = self.log_file_path.parent
        if not log_dir.exists():
            try:
                log_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                warnings.append(
                    f"Could not create log directory {log_dir}: {e}")
        elif not os.access(log_dir, os.W_OK):
            warnings.append(f"Log directory not writable: {log_dir}")

        return CronValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def validate_cron_schedule(self, schedule: str) -> CronValidationResult:
        """Validate cron schedule format."""
        errors = []
        warnings = []

        # Basic format validation - should have 5 fields
        fields = schedule.strip().split()
        if len(fields) != 5:
            errors.append(
                f"Invalid cron schedule format: '{schedule}' (expected 5 fields)")
            return CronValidationResult(False, errors, warnings)

        # Validate each field
        minute, hour, day, month, weekday = fields

        # Minute validation (0-59)
        if not self._validate_cron_field(minute, 0, 59):
            errors.append(
                f"Invalid minute field: '{minute}' (must be 0-59 or */n)")

        # Hour validation (0-23)
        if not self._validate_cron_field(hour, 0, 23):
            errors.append(
                f"Invalid hour field: '{hour}' (must be 0-23 or */n)")

        # Day validation (1-31)
        if not self._validate_cron_field(day, 1, 31, allow_star=True):
            errors.append(
                f"Invalid day field: '{day}' (must be 1-31, *, or */n)")

        # Month validation (1-12)
        if not self._validate_cron_field(month, 1, 12, allow_star=True):
            errors.append(
                f"Invalid month field: '{month}' (must be 1-12, *, or */n)")

        # Weekday validation (0-7, where 0 and 7 are Sunday)
        if not self._validate_cron_field(weekday, 0, 7, allow_star=True):
            errors.append(
                f"Invalid weekday field: '{weekday}' (must be 0-7, *, or */n)")

        return CronValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def _validate_cron_field(self, field: str, min_val: int, max_val: int, allow_star: bool = True) -> bool:
        """Validate individual cron field."""
        if field == "*" and allow_star:
            return True

        # Handle step values (*/n)
        if field.startswith("*/"):
            try:
                step = int(field[2:])
                return step > 0 and step <= max_val
            except ValueError:
                return False

        # Handle range values (n-m)
        if "-" in field:
            try:
                start, end = field.split("-", 1)
                start_val = int(start)
                end_val = int(end)
                return (min_val <= start_val <= max_val and
                        min_val <= end_val <= max_val and
                        start_val <= end_val)
            except ValueError:
                return False

        # Handle list values (n,m,o)
        if "," in field:
            try:
                values = [int(v.strip()) for v in field.split(",")]
                return all(min_val <= v <= max_val for v in values)
            except ValueError:
                return False

        # Handle single value
        try:
            value = int(field)
            return min_val <= value <= max_val
        except ValueError:
            return False

    def validate_steps(self, steps: List[str]) -> CronValidationResult:
        """Validate workflow step names."""
        errors = []
        warnings = []

        valid_steps = {job_type.value for job_type in CronJobType}

        for step in steps:
            if step not in valid_steps:
                errors.append(
                    f"Invalid step: '{step}' (valid steps: {', '.join(sorted(valid_steps))})")

        if not steps:
            errors.append("At least one workflow step is required")

        return CronValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def get_default_schedule(self, steps: List[str]) -> str:
        """Get default schedule for given workflow steps."""
        if len(steps) > 1:
            # Multiple steps - use common daily schedule
            return "0 1 * * *"  # Daily at 1 AM

        # Single step - use specific schedule
        step_type = CronJobType(steps[0])
        return self.default_schedules.get(step_type, "0 */4 * * *")

    def _get_cron_comment(self, steps: List[str]) -> str:
        """Generate comment for cron job with assignment context."""
        steps_key = "-".join(steps)

        # Include assignment name to make cron jobs unique per assignment
        assignment_identifier = self._get_assignment_identifier()

        return f"{self.cron_comment_prefix}-{assignment_identifier}-{steps_key}"

    def _get_assignment_identifier(self) -> str:
        """Get unique identifier for the current assignment."""
        # Try to get assignment name from config
        if self.global_config and self.global_config.assignment_name:
            # Sanitize assignment name for use in cron comment
            return self.global_config.assignment_name.replace(" ", "-").replace("/", "-")

        # Fallback to directory name if no assignment name configured
        return Path.cwd().name

    def _get_cron_command(self, steps: List[str]) -> str:
        """Generate command for cron job using Python CLI."""
        steps_str = " ".join(steps)
        config_file = self._get_assignment_config_path()

        # Use python -m classdock automation cron-sync for automation
        # Include --config to ensure correct assignment is targeted
        return f"cd {self.cron_script_path} && python -m classdock automation cron-sync --config {config_file} {steps_str} >/dev/null 2>&1"

    def _get_current_crontab(self) -> Optional[str]:
        """Get current user's crontab content."""
        try:
            result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout
            else:
                # No crontab exists
                return None
        except Exception as e:
            logger.warning(f"Could not read crontab: {e}")
            return None

    def _set_crontab(self, content: str) -> bool:
        """Set user's crontab content."""
        try:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.cron') as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name

            result = subprocess.run(
                ["crontab", temp_file_path],
                capture_output=True,
                text=True,
                timeout=10
            )

            os.unlink(temp_file_path)

            if result.returncode == 0:
                return True
            else:
                logger.error(f"Failed to set crontab: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error setting crontab: {e}")
            return False

    def _remove_crontab(self) -> bool:
        """Remove user's crontab entirely."""
        try:
            result = subprocess.run(
                ["crontab", "-r"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0 or "no crontab" in result.stderr.lower()
        except Exception as e:
            logger.warning(f"Error removing crontab: {e}")
            return True  # Assume success if crontab doesn't exist

    def job_exists(self, steps: List[str]) -> bool:
        """Check if cron job for given steps exists."""
        current_crontab = self._get_current_crontab()
        if not current_crontab:
            return False

        comment = self._get_cron_comment(steps)
        return comment in current_crontab

    def install_cron_job(self, steps: List[str], schedule: Optional[str] = None) -> Tuple[CronOperationResult, str]:
        """Install cron job for specified workflow steps."""
        try:
            # Validate prerequisites
            prereq_validation = self.validate_prerequisites()
            if not prereq_validation.is_valid:
                error_msg = "Prerequisites validation failed: " + \
                    "; ".join(prereq_validation.errors)
                return CronOperationResult.VALIDATION_ERROR, error_msg

            # Validate steps
            steps_validation = self.validate_steps(steps)
            if not steps_validation.is_valid:
                error_msg = "Steps validation failed: " + \
                    "; ".join(steps_validation.errors)
                return CronOperationResult.VALIDATION_ERROR, error_msg

            # Get default schedule if not provided
            if schedule is None:
                schedule = self.get_default_schedule(steps)
                logger.info(f"Using default schedule: {schedule}")

            # Validate schedule
            schedule_validation = self.validate_cron_schedule(schedule)
            if not schedule_validation.is_valid:
                error_msg = "Schedule validation failed: " + \
                    "; ".join(schedule_validation.errors)
                return CronOperationResult.VALIDATION_ERROR, error_msg

            # Check if job already exists
            if self.job_exists(steps):
                return CronOperationResult.ALREADY_EXISTS, f"Cron job for steps '{' '.join(steps)}' already exists"

            # Create cron job entry
            comment = self._get_cron_comment(steps)
            command = self._get_cron_command(steps)
            cron_entry = f"{comment}\n{schedule} {command}"

            # Get current crontab and add new entry
            current_crontab = self._get_current_crontab()
            if current_crontab:
                new_crontab = f"{current_crontab.rstrip()}\n{cron_entry}\n"
            else:
                new_crontab = f"{cron_entry}\n"

            # Set new crontab
            if self._set_crontab(new_crontab):
                success_msg = f"Cron job installed successfully for steps: {' '.join(steps)}"
                logger.info(success_msg)
                return CronOperationResult.SUCCESS, success_msg
            else:
                return CronOperationResult.SYSTEM_ERROR, "Failed to update crontab"

        except PermissionError:
            return CronOperationResult.PERMISSION_ERROR, "Permission denied accessing crontab"
        except Exception as e:
            logger.error(f"Unexpected error installing cron job: {e}")
            return CronOperationResult.SYSTEM_ERROR, f"System error: {e}"

    def remove_cron_job(self, steps: Union[List[str], str]) -> Tuple[CronOperationResult, str]:
        """Remove cron job for specified workflow steps or all jobs."""
        try:
            current_crontab = self._get_current_crontab()
            if not current_crontab:
                return CronOperationResult.NOT_FOUND, "No crontab exists"

            if steps == "all" or (isinstance(steps, list) and len(steps) == 1 and steps[0] == "all"):
                # Remove all assignment-related cron jobs
                lines = current_crontab.splitlines()
                filtered_lines = []

                i = 0
                while i < len(lines):
                    line = lines[i]
                    # If this line is a comment with our prefix, skip it and the next line (command)
                    if self.cron_comment_prefix in line:
                        i += 1  # Skip comment line
                        if i < len(lines):
                            i += 1  # Skip command line too
                    else:
                        filtered_lines.append(line)
                        i += 1

                if len(filtered_lines) == len(lines):
                    return CronOperationResult.NOT_FOUND, "No assignment cron jobs found to remove"

                # Check if there are any non-empty, non-whitespace lines remaining
                non_empty_filtered_lines = [
                    line for line in filtered_lines if line.strip()]

                if non_empty_filtered_lines:
                    new_crontab = "\n".join(filtered_lines) + "\n"
                    if self._set_crontab(new_crontab):
                        return CronOperationResult.SUCCESS, "All assignment cron jobs removed successfully"
                    else:
                        return CronOperationResult.SYSTEM_ERROR, "Failed to update crontab"
                else:
                    # Remove entire crontab if no other entries
                    if self._remove_crontab():
                        return CronOperationResult.SUCCESS, "All assignment cron jobs removed successfully"
                    else:
                        return CronOperationResult.SYSTEM_ERROR, "Failed to remove crontab"

            else:
                # Remove specific cron job
                if isinstance(steps, str):
                    steps = [steps]

                if not self.job_exists(steps):
                    return CronOperationResult.NOT_FOUND, f"Cron job for steps '{' '.join(steps)}' not found"

                comment = self._get_cron_comment(steps)
                command = self._get_cron_command(steps)

                lines = current_crontab.splitlines()
                filtered_lines = [
                    line for line in lines
                    if comment not in line and command not in line
                ]

                if filtered_lines:
                    new_crontab = "\n".join(filtered_lines) + "\n"
                    if self._set_crontab(new_crontab):
                        return CronOperationResult.SUCCESS, f"Cron job for steps '{' '.join(steps)}' removed successfully"
                    else:
                        return CronOperationResult.SYSTEM_ERROR, "Failed to update crontab"
                else:
                    # Remove entire crontab if no other entries
                    if self._remove_crontab():
                        return CronOperationResult.SUCCESS, f"Cron job for steps '{' '.join(steps)}' removed successfully"
                    else:
                        return CronOperationResult.SYSTEM_ERROR, "Failed to remove crontab"

        except PermissionError:
            return CronOperationResult.PERMISSION_ERROR, "Permission denied accessing crontab"
        except Exception as e:
            logger.error(f"Unexpected error removing cron job: {e}")
            return CronOperationResult.SYSTEM_ERROR, f"System error: {e}"

    def get_cron_status(self) -> CronStatus:
        """Get status of installed cron jobs."""
        installed_jobs = []

        current_crontab = self._get_current_crontab()
        if current_crontab:
            lines = current_crontab.splitlines()

            i = 0
            while i < len(lines):
                line = lines[i].strip()

                # Check if this is our comment line
                if line.startswith(self.cron_comment_prefix):
                    # Extract steps from comment
                    comment_parts = line.split("-")
                    if len(comment_parts) > 1:
                        steps_key = comment_parts[-1]
                        steps = steps_key.split("-")

                        # Check if next line is the corresponding command
                        if i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            if next_line and not next_line.startswith("#"):
                                # Parse schedule and command
                                parts = next_line.split(" ", 5)
                                if len(parts) >= 6:
                                    schedule = " ".join(parts[:5])
                                    command = parts[5]

                                    job = CronJob(
                                        steps=steps,
                                        schedule=schedule,
                                        command=command,
                                        comment=line,
                                        is_active=True
                                    )
                                    installed_jobs.append(job)
                                    i += 1  # Skip the command line
                i += 1

        # Check log file
        log_file_exists = self.log_file_path.exists()
        last_log_activity = None

        if log_file_exists:
            try:
                # Get last few lines from log file
                with open(self.log_file_path, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        last_log_activity = "".join(lines[-3:]).strip()
            except Exception as e:
                logger.warning(f"Could not read log file: {e}")

        return CronStatus(
            installed_jobs=installed_jobs,
            total_jobs=len(installed_jobs),
            log_file_exists=log_file_exists,
            log_file_path=self.log_file_path if log_file_exists else None,
            last_log_activity=last_log_activity
        )

    def show_logs(self, lines: int = 30) -> Tuple[bool, str]:
        """Show recent workflow log entries."""
        if not self.log_file_path.exists():
            return False, f"Log file not found: {self.log_file_path}"

        try:
            # Use tail command to get last N lines
            result = subprocess.run(
                ["tail", f"-n{lines}", str(self.log_file_path)],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                output = f"=== Recent Workflow Log Entries ===\n{result.stdout}\n"

                # Add file info
                stat = self.log_file_path.stat()
                file_size = stat.st_size
                if file_size < 1024:
                    size_str = f"{file_size} bytes"
                elif file_size < 1024 * 1024:
                    size_str = f"{file_size / 1024:.1f} KB"
                else:
                    size_str = f"{file_size / (1024 * 1024):.1f} MB"

                mod_time = datetime.fromtimestamp(
                    stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")

                output += "\n=== Log File Info ===\n"
                output += f"File: {self.log_file_path}\n"
                output += f"Size: {size_str}\n"
                output += f"Last modified: {mod_time}\n"

                return True, output
            else:
                return False, f"Failed to read log file: {result.stderr}"

        except Exception as e:
            return False, f"Error reading log file: {e}"

    def list_default_schedules(self) -> str:
        """List default schedules for all workflow steps."""
        output = "Default schedules for workflow steps:\n\n"

        for job_type in CronJobType:
            schedule = self.default_schedules[job_type]
            output += f"  {job_type.value:<10} {schedule}\n"

        output += "\nSchedule format: minute hour day_of_month month day_of_week\n"
        output += "Examples:\n"
        output += "  0 */4 * * *   - Every 4 hours\n"
        output += "  0 2 * * *     - Daily at 2 AM\n"
        output += "  0 6 * * 0     - Weekly on Sunday at 6 AM\n"

        return output
