#!/usr/bin/env python3
"""
Mock Helpers for Repos Commands Testing

This module provides Python-based mocking utilities for testing classdock
repos commands. It uses unittest.mock to patch repository operations and simulate
various scenarios without making actual GitHub API calls or filesystem changes.

Usage:
    Import and call the mock functions before executing CLI commands in tests.
    Each function patches specific methods and returns controlled test data.
"""

import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import List, Dict, Any


def mock_fetch_with_repos_list(repos_list_file: str) -> Dict[str, Any]:
    """
    Mock RepositoryFetcher to simulate reading from a repos list file.

    Args:
        repos_list_file: Path to file containing repository URLs

    Returns:
        Dictionary with mock configuration
    """
    # Read the repos list file
    repos = []
    if Path(repos_list_file).exists():
        with open(repos_list_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    repos.append(line)

    return {
        'repos_count': len(repos),
        'repos': repos,
        'success': len(repos) > 0
    }


def mock_fetch_auto_discovery() -> Dict[str, Any]:
    """
    Mock RepositoryFetcher for auto-discovery variant.

    Returns:
        Dictionary with synthetic repository list
    """
    return {
        'repos_count': 2,
        'repos': [
            'https://github.com/test-org/test-assignment-student1',
            'https://github.com/test-org/test-assignment-student2'
        ],
        'success': True
    }


def mock_fetch_empty_list() -> Dict[str, Any]:
    """
    Mock RepositoryFetcher to simulate empty repository list.

    Returns:
        Dictionary indicating empty list scenario
    """
    return {
        'repos_count': 0,
        'repos': [],
        'success': False,
        'error': 'No repositories found'
    }


def mock_fetch_invalid_urls() -> Dict[str, Any]:
    """
    Mock RepositoryFetcher to simulate invalid URL errors.

    Returns:
        Dictionary indicating invalid URL scenario
    """
    return {
        'repos_count': 0,
        'repos': [],
        'success': False,
        'error': 'GitHubDiscoveryError: Invalid repository URL format in list'
    }


def mock_cycle_collaborator_user_present() -> Dict[str, Any]:
    """
    Mock CycleCollaboratorManager when target user IS present in collaborators.

    Returns:
        Dictionary with remove/re-add operation result
    """
    return {
        'collaborators': [{'login': 'student1', 'permission': 'write'}],
        'operation': 'remove_and_readd',
        'success': True,
        'message': 'Removed and re-added collaborator student1'
    }


def mock_cycle_collaborator_user_absent() -> Dict[str, Any]:
    """
    Mock CycleCollaboratorManager when target user is NOT present.

    Returns:
        Dictionary with add operation result
    """
    return {
        'collaborators': [],
        'operation': 'add',
        'success': True,
        'message': 'Added collaborator student1'
    }


def apply_fetch_mocks(scenario: str, repos_list_file: str = None):
    """
    Apply fetch-related mocks based on scenario.

    Args:
        scenario: One of 'auto_discovery', 'repos_list', 'empty_list', 'invalid_urls'
        repos_list_file: Path to repos list file (for repos_list scenario)
    """
    if scenario == 'auto_discovery':
        mock_data = mock_fetch_auto_discovery()
    elif scenario == 'repos_list':
        mock_data = mock_fetch_with_repos_list(repos_list_file)
    elif scenario == 'empty_list':
        mock_data = mock_fetch_empty_list()
    elif scenario == 'invalid_urls':
        mock_data = mock_fetch_invalid_urls()
    else:
        raise ValueError(f"Unknown scenario: {scenario}")

    # Output mock data as JSON for shell consumption
    print(json.dumps(mock_data))


def apply_cycle_collaborator_mocks(scenario: str):
    """
    Apply cycle-collaborator mocks based on scenario.

    Args:
        scenario: One of 'user_present', 'user_absent'
    """
    if scenario == 'user_present':
        mock_data = mock_cycle_collaborator_user_present()
    elif scenario == 'user_absent':
        mock_data = mock_cycle_collaborator_user_absent()
    else:
        raise ValueError(f"Unknown scenario: {scenario}")

    # Output mock data as JSON for shell consumption
    print(json.dumps(mock_data))


if __name__ == '__main__':
    # CLI interface for shell scripts
    if len(sys.argv) < 3:
        print(
            "Usage: mock_repos_helpers.py <command> <scenario> [args...]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    scenario = sys.argv[2]

    if command == 'fetch':
        repos_list_file = sys.argv[3] if len(sys.argv) > 3 else None
        apply_fetch_mocks(scenario, repos_list_file)
    elif command == 'cycle-collaborator':
        apply_cycle_collaborator_mocks(scenario)
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)
