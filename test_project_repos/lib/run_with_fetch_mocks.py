#!/usr/bin/env python3
"""
Mock Runner for Fetch Command Testing

This script patches RepositoryFetcher methods to simulate various fetch scenarios
without making actual GitHub API calls. It supports testing auto-discovery, repos-list,
empty list, and invalid URL scenarios.

Usage:
    SCENARIO=auto_discovery poetry run python run_with_fetch_mocks.py --config path/to/config
    SCENARIO=repos_list REPOS_LIST_FILE=fixtures/repos/student_repos.txt poetry run python run_with_fetch_mocks.py --config path/to/config
    SCENARIO=empty_list poetry run python run_with_fetch_mocks.py --config path/to/config
    SCENARIO=invalid_urls poetry run python run_with_fetch_mocks.py --config path/to/config

Environment Variables:
    SCENARIO: One of [auto_discovery, repos_list, empty_list, invalid_urls]
    REPOS_LIST_FILE: Path to repos list file (required for repos_list scenario)
"""

import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import List

# Add classroom_pilot to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def read_repos_list(file_path: str) -> List[str]:
    """Read repository URLs from a file."""
    repos = []
    if Path(file_path).exists():
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    repos.append(line)
    return repos


def mock_auto_discovery_scenario():
    """Mock auto-discovery scenario: discovers and fetches repositories successfully."""

    def mock_fetch_all_repositories(self, verbose=False):
        """Mock successful auto-discovery and fetch."""
        return True

    return mock_fetch_all_repositories


def mock_repos_list_scenario(repos_list_file: str):
    """Mock repos-list scenario: discovers repos from file and fetches successfully."""
    repos = read_repos_list(repos_list_file)

    def mock_discover_repositories(self, assignment_prefix: str = None, organization: str = None):
        """Mock discovery from repos list file."""
        from classdock.repos.fetch import RepositoryInfo

        # Create RepositoryInfo objects from repos list
        repo_infos = []
        for repo_url in repos:
            # Parse org and repo name from URL
            # Format: https://github.com/org/repo or org/repo
            parts = repo_url.rstrip('/').split('/')
            if len(parts) >= 2:
                org = parts[-2]
                repo = parts[-1]
                repo_infos.append(RepositoryInfo(
                    url=repo_url if repo_url.startswith(
                        'http') else f"https://github.com/{repo_url}",
                    name=repo,
                    clone_url=f"{repo_url if repo_url.startswith('http') else f'https://github.com/{repo_url}'}.git",
                    is_template=False,
                    is_student_repo=True,
                    student_identifier=repo.split(
                        '-')[-1] if '-' in repo else repo
                ))

        return repo_infos

    def mock_fetch_repositories(self, repositories, target_directory: str = "student-repos"):
        """Mock successful fetch of all discovered repos."""
        from classdock.repos.fetch import FetchResult

        # Return list of successful FetchResult objects
        results = []
        for repo in repositories:
            results.append(FetchResult(
                repository=repo,
                success=True,
                was_cloned=True,
                local_path=f"/mock/path/{repo.name}",
                error_message=None
            ))
        return results

    return mock_discover_repositories, mock_fetch_repositories


def mock_empty_list_scenario():
    """Mock empty list scenario: no repositories found."""

    def mock_discover_repositories(self, assignment_prefix: str = None, organization: str = None):
        """Mock discovery returning empty list."""
        return []

    return mock_discover_repositories


def mock_invalid_urls_scenario():
    """Mock invalid URLs scenario: discovery raises error."""

    def mock_discover_repositories(self, assignment_prefix: str = None, organization: str = None):
        """Mock discovery raising error for invalid URLs."""
        from classdock.utils.github_exceptions import GitHubDiscoveryError
        raise GitHubDiscoveryError("Invalid repository URL format in list")

    return mock_discover_repositories


def run_cli_with_mocks(scenario: str, repos_list_file: str = None):
    """
    Run the classroom-pilot CLI with appropriate mocks for the given scenario.

    Args:
        scenario: The test scenario (auto_discovery, repos_list, empty_list, invalid_urls)
        repos_list_file: Path to repos list file (required for repos_list scenario)

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
    if scenario == "auto_discovery":
        mock_func = mock_auto_discovery_scenario()
        with patch('classdock.repos.fetch.RepositoryFetcher.fetch_all_repositories', mock_func):
            result = runner.invoke(app, ["repos", "fetch"] + cli_args)

    elif scenario == "repos_list":
        if not repos_list_file:
            print(
                "ERROR: REPOS_LIST_FILE environment variable required for repos_list scenario", file=sys.stderr)
            return 1

        mock_discover, mock_fetch = mock_repos_list_scenario(repos_list_file)
        with patch('classdock.repos.fetch.RepositoryFetcher.discover_repositories', mock_discover), \
                patch('classdock.repos.fetch.RepositoryFetcher.fetch_repositories', mock_fetch):
            result = runner.invoke(app, ["repos", "fetch"] + cli_args)

    elif scenario == "empty_list":
        mock_discover = mock_empty_list_scenario()
        with patch('classdock.repos.fetch.RepositoryFetcher.discover_repositories', mock_discover):
            # Also need to mock fetch_all_repositories to handle empty discovery
            def mock_fetch_all(self, verbose=False):
                repos = self.discover_repositories(verbose)
                if not repos:
                    return False
                return True

            with patch('classdock.repos.fetch.RepositoryFetcher.fetch_all_repositories', mock_fetch_all):
                result = runner.invoke(app, ["repos", "fetch"] + cli_args)

    elif scenario == "invalid_urls":
        mock_discover = mock_invalid_urls_scenario()
        with patch('classdock.repos.fetch.RepositoryFetcher.discover_repositories', mock_discover):
            result = runner.invoke(app, ["repos", "fetch"] + cli_args)

    else:
        print(f"ERROR: Unknown scenario '{scenario}'", file=sys.stderr)
        print("Valid scenarios: auto_discovery, repos_list, empty_list, invalid_urls", file=sys.stderr)
        return 1

    # Print CLI output
    print(result.stdout, end='')

    # Return CLI exit code
    return result.exit_code


def main():
    """Main entry point."""
    scenario = os.environ.get('SCENARIO')
    repos_list_file = os.environ.get('REPOS_LIST_FILE')

    if not scenario:
        print("ERROR: SCENARIO environment variable required", file=sys.stderr)
        print("Valid scenarios: auto_discovery, repos_list, empty_list, invalid_urls", file=sys.stderr)
        return 1

    exit_code = run_cli_with_mocks(scenario, repos_list_file)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
