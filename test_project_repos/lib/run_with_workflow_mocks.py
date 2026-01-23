#!/usr/bin/env python3
"""
Mock Runner for Update and Push Command Testing

This script patches StudentUpdateHelper and ClassroomPushManager methods to simulate
various workflow scenarios without making actual operations. It supports testing
success and failure paths for update and push commands.

Usage:
    COMMAND=update SCENARIO=success poetry run python run_with_workflow_mocks.py [CLI args]
    COMMAND=update SCENARIO=failure poetry run python run_with_workflow_mocks.py [CLI args]
    COMMAND=push SCENARIO=success poetry run python run_with_workflow_mocks.py [CLI args]
    COMMAND=push SCENARIO=failure poetry run python run_with_workflow_mocks.py [CLI args]

Environment Variables:
    COMMAND: One of [update, push]
    SCENARIO: One of [success, failure]
"""

import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add classroom_pilot to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def mock_update_success():
    """Mock successful update workflow."""

    def mock_execute_update_workflow(self, auto_confirm: bool = False, verbose: bool = False):
        """Mock successful update workflow execution."""
        return (True, "Update completed successfully")

    return mock_execute_update_workflow


def mock_update_failure():
    """Mock failed update workflow."""

    def mock_execute_update_workflow(self, auto_confirm: bool = False, verbose: bool = False):
        """Mock failed update workflow execution."""
        return (False, "Update failed: Configuration validation error")

    return mock_execute_update_workflow


def mock_push_success():
    """Mock successful push workflow."""

    def mock_execute_push_workflow(self, force: bool = False, interactive: bool = False):
        """Mock successful push workflow execution."""
        from classdock.assignments.push_manager import PushResult
        return (PushResult.SUCCESS, "Push completed successfully")

    return mock_execute_push_workflow


def mock_push_failure():
    """Mock failed push workflow."""

    def mock_execute_push_workflow(self, force: bool = False, interactive: bool = False):
        """Mock failed push workflow execution."""
        from classdock.assignments.push_manager import PushResult
        return (PushResult.FAILED, "Push failed: Missing classroom repository")

    return mock_execute_push_workflow


def run_cli_with_mocks(command: str, scenario: str):
    """
    Run the classroom-pilot CLI with appropriate mocks for the given command and scenario.

    Args:
        command: The command to run (update, push)
        scenario: The test scenario (success, failure)

    Returns:
        Exit code from the CLI execution
    """
    # Get CLI arguments (everything after the script name)
    cli_args = sys.argv[1:]

    # Import CLI after path is set
    from classdock.cli import app
    import typer.testing

    runner = typer.testing.CliRunner()

    # Apply appropriate mocks based on command and scenario
    if command == "update":
        if scenario == "success":
            mock_func = mock_update_success()
            with patch('classdock.assignments.student_helper.StudentUpdateHelper.execute_update_workflow', mock_func):
                result = runner.invoke(app, ["repos", "update"] + cli_args)
        elif scenario == "failure":
            mock_func = mock_update_failure()
            with patch('classdock.assignments.student_helper.StudentUpdateHelper.execute_update_workflow', mock_func):
                result = runner.invoke(app, ["repos", "update"] + cli_args)
        else:
            print(
                f"ERROR: Unknown scenario '{scenario}' for update command", file=sys.stderr)
            return 1

    elif command == "push":
        if scenario == "success":
            mock_func = mock_push_success()
            with patch('classdock.assignments.push_manager.ClassroomPushManager.execute_push_workflow', mock_func):
                result = runner.invoke(app, ["repos", "push"] + cli_args)
        elif scenario == "failure":
            mock_func = mock_push_failure()
            with patch('classdock.assignments.push_manager.ClassroomPushManager.execute_push_workflow', mock_func):
                result = runner.invoke(app, ["repos", "push"] + cli_args)
        else:
            print(
                f"ERROR: Unknown scenario '{scenario}' for push command", file=sys.stderr)
            return 1

    else:
        print(f"ERROR: Unknown command '{command}'", file=sys.stderr)
        print("Valid commands: update, push", file=sys.stderr)
        return 1

    # Print CLI output
    print(result.stdout, end='')

    # Return CLI exit code
    return result.exit_code


def main():
    """Main entry point."""
    command = os.environ.get('COMMAND')
    scenario = os.environ.get('SCENARIO')

    if not command:
        print("ERROR: COMMAND environment variable required", file=sys.stderr)
        print("Valid commands: update, push", file=sys.stderr)
        return 1

    if not scenario:
        print("ERROR: SCENARIO environment variable required", file=sys.stderr)
        print("Valid scenarios: success, failure", file=sys.stderr)
        return 1

    exit_code = run_cli_with_mocks(command, scenario)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
