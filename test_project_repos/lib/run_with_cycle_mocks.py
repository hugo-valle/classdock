#!/usr/bin/env python3
"""
Mock Runner for Cycle-Collaborator Command Testing

This script patches CycleCollaboratorManager methods to simulate various collaborator
cycling scenarios without making actual GitHub API calls. It supports testing both
user-present (remove and re-add) and user-absent (add only) scenarios.

Usage:
    SCENARIO=user_present poetry run python run_with_cycle_mocks.py [CLI args]
    SCENARIO=user_absent poetry run python run_with_cycle_mocks.py [CLI args]

Environment Variables:
    SCENARIO: One of [user_present, user_absent]
"""

import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add classroom_pilot to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def mock_user_present_scenario():
    """
    Mock scenario where collaborator IS present in repository.

    Simulates: cycle_single_repository() removes then re-adds the user
    """

    def mock_cycle_single(self, repo_url: str, force: bool = False):
        """Mock successful remove and re-add operation."""
        return (True, 'Removed and re-added collaborator student1')

    return mock_cycle_single


def mock_user_absent_scenario():
    """
    Mock scenario where collaborator IS NOT present in repository.

    Simulates: cycle_single_repository() adds the user
    """

    def mock_cycle_single(self, repo_url: str, force: bool = False):
        """Mock successful add operation."""
        return (True, 'Added collaborator student1')

    return mock_cycle_single


def run_cli_with_mocks(scenario: str):
    """
    Run the classroom-pilot CLI with appropriate mocks for the given scenario.

    Args:
        scenario: The test scenario (user_present, user_absent)

    Returns:
        Exit code from the CLI execution
    """
    # Get CLI arguments (everything after the script name)
    cli_args = sys.argv[1:]

    # Import CLI after path is set
    from classdock.cli import app
    import typer.testing

    runner = typer.testing.CliRunner()

    # Apply appropriate mocks based on scenario
    if scenario == "user_present":
        mock_cycle = mock_user_present_scenario()
        with patch('classdock.assignments.cycle_collaborator.CycleCollaboratorManager.cycle_single_repository', mock_cycle):
            result = runner.invoke(
                app, ["repos", "cycle-collaborator"] + cli_args)

    elif scenario == "user_absent":
        mock_cycle = mock_user_absent_scenario()
        with patch('classdock.assignments.cycle_collaborator.CycleCollaboratorManager.cycle_single_repository', mock_cycle):
            result = runner.invoke(
                app, ["repos", "cycle-collaborator"] + cli_args)

    else:
        print(f"ERROR: Unknown scenario '{scenario}'", file=sys.stderr)
        print("Valid scenarios: user_present, user_absent", file=sys.stderr)
        return 1

    # Print CLI output
    print(result.stdout, end='')

    # Return CLI exit code
    return result.exit_code


def main():
    """Main entry point."""
    scenario = os.environ.get('SCENARIO')

    if not scenario:
        print("ERROR: SCENARIO environment variable required", file=sys.stderr)
        print("Valid scenarios: user_present, user_absent", file=sys.stderr)
        return 1

    exit_code = run_cli_with_mocks(scenario)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
