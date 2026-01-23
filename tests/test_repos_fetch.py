"""
Comprehensive test suite for classdock.repos.fetch module.

This test suite provides comprehensive coverage for the RepositoryFetcher class,
which handles GitHub Classroom repository operations including discovery, fetching,
and management. The tests include unit tests for individual methods, integration
tests for GitHub API operations, error handling, and comprehensive mocking
scenarios for reliable test execution.

Test Categories:
1. Initialization Tests - Constructor and authentication setup
2. GitHub Authentication Tests - API authentication and token handling
3. Repository Discovery Tests - GitHub API and CLI repository discovery
4. Repository Filtering Tests - Student repository identification and filtering
5. Single Repository Fetch Tests - Individual repository operations
6. Batch Repository Fetch Tests - Multiple repository operations with progress tracking
7. Template Repository Tests - Template repository synchronization
8. Repository Update Tests - Local repository update operations
9. Error Handling Tests - Exception scenarios and graceful failures
10. Integration Tests - End-to-end workflows and API integration

The RepositoryFetcher class provides methods for:
- GitHub API authentication with multiple token sources
- Repository discovery via GitHub API or CLI fallback
- Pattern-based filtering for student repository identification
- Batch fetching with progress tracking and error resilience
- Template repository management and synchronization
- Local repository updates and maintenance
- Comprehensive error handling and logging

All tests use proper mocking to isolate the RepositoryFetcher from external dependencies
including GitHub API calls, file system operations, and subprocess calls, ensuring
test reliability and speed while maintaining comprehensive coverage.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import subprocess

from classdock.repos.fetch import (
    RepositoryFetcher,
    RepositoryInfo,
    FetchResult
)
from classdock.utils.github_exceptions import (
    GitHubAuthenticationError,
    GitHubDiscoveryError
)


class TestRepositoryFetcherInitialization:
    """
    TestRepositoryFetcherInitialization contains unit tests for the RepositoryFetcher class
    initialization and basic setup. It verifies that the constructor properly handles
    configuration loading, component initialization, and GitHub authentication setup.

    Test Cases:
    - test_init_with_config_path: Tests initialization with explicit configuration path
    - test_init_without_config_path: Tests initialization with automatic config discovery
    - test_init_component_setup: Tests proper initialization of internal components
    - test_init_github_authentication_success: Tests successful GitHub authentication during init
    - test_init_github_authentication_failure: Tests graceful handling of authentication failures
    """

    @patch('classdock.repos.fetch.PathManager')
    @patch('classdock.repos.fetch.GitManager')
    @patch('classdock.repos.fetch.ConfigLoader')
    def test_init_with_config_path(self, mock_config_loader, mock_git_manager, mock_path_manager):
        """
        Test RepositoryFetcher initialization with explicit configuration path.

        This test verifies that when a specific configuration file path is provided,
        the RepositoryFetcher correctly initializes all its components and attempts
        GitHub authentication setup.
        """
        config_path = Path("/test/assignment.conf")
        mock_config_instance = Mock()
        mock_config_instance.load.return_value = {
            'GITHUB_ORGANIZATION': 'test-org'}
        mock_config_loader.return_value = mock_config_instance

        with patch.object(RepositoryFetcher, 'authenticate_github', side_effect=GitHubAuthenticationError("Test")):
            fetcher = RepositoryFetcher(config_path)

        mock_config_loader.assert_called_once_with(config_path)
        assert fetcher.config == {'GITHUB_ORGANIZATION': 'test-org'}
        mock_git_manager.assert_called_once()
        mock_path_manager.assert_called_once()

    @patch('classdock.repos.fetch.PathManager')
    @patch('classdock.repos.fetch.GitManager')
    @patch('classdock.repos.fetch.ConfigLoader')
    def test_init_without_config_path(self, mock_config_loader, mock_git_manager, mock_path_manager):
        """
        Test RepositoryFetcher initialization without explicit configuration path.

        This test verifies that when no configuration path is provided, the
        RepositoryFetcher uses ConfigLoader's automatic discovery mechanism.
        """
        mock_config_instance = Mock()
        mock_config_instance.load.return_value = {}
        mock_config_loader.return_value = mock_config_instance

        with patch.object(RepositoryFetcher, 'authenticate_github', side_effect=GitHubAuthenticationError("Test")):
            fetcher = RepositoryFetcher()

        mock_config_loader.assert_called_once_with(None)
        assert hasattr(fetcher, 'git_manager')
        assert hasattr(fetcher, 'path_manager')

    @patch('classdock.repos.fetch.PathManager')
    @patch('classdock.repos.fetch.GitManager')
    @patch('classdock.repos.fetch.ConfigLoader')
    def test_init_component_setup(self, mock_config_loader, mock_git_manager, mock_path_manager):
        """
        Test that RepositoryFetcher properly initializes all required components.

        This test verifies that all internal components (ConfigLoader, GitManager,
        PathManager) are properly instantiated and that the GitHub client is
        initially set to None before authentication.
        """
        mock_config_instance = Mock()
        mock_config_instance.load.return_value = {}
        mock_config_loader.return_value = mock_config_instance

        with patch.object(RepositoryFetcher, 'authenticate_github', side_effect=GitHubAuthenticationError("Test")):
            fetcher = RepositoryFetcher()

        assert fetcher.config_loader == mock_config_loader.return_value
        assert fetcher.git_manager == mock_git_manager.return_value
        assert fetcher.path_manager == mock_path_manager.return_value
        assert fetcher.github_client is None

    @patch('classdock.repos.fetch.PathManager')
    @patch('classdock.repos.fetch.GitManager')
    @patch('classdock.repos.fetch.ConfigLoader')
    def test_init_github_authentication_success(self, mock_config_loader, mock_git_manager, mock_path_manager):
        """
        Test successful GitHub authentication during RepositoryFetcher initialization.

        This test verifies that when GitHub authentication succeeds during initialization,
        the github_client is properly set and no exceptions are raised.
        """
        mock_config_instance = Mock()
        mock_config_instance.load.return_value = {}
        mock_config_loader.return_value = mock_config_instance

        mock_github_client = Mock()
        with patch.object(RepositoryFetcher, 'authenticate_github', return_value=True) as mock_auth:
            with patch('classdock.repos.fetch.GITHUB_AVAILABLE', True):
                fetcher = RepositoryFetcher()

        mock_auth.assert_called_once()

    @patch('classdock.repos.fetch.PathManager')
    @patch('classdock.repos.fetch.GitManager')
    @patch('classdock.repos.fetch.ConfigLoader')
    def test_init_github_authentication_failure(self, mock_config_loader, mock_git_manager, mock_path_manager):
        """
        Test graceful handling of GitHub authentication failure during initialization.

        This test verifies that when GitHub authentication fails during initialization,
        the RepositoryFetcher continues to function and logs appropriate warnings
        without raising exceptions.
        """
        mock_config_instance = Mock()
        mock_config_instance.load.return_value = {}
        mock_config_loader.return_value = mock_config_instance

        with patch.object(RepositoryFetcher, 'authenticate_github', side_effect=GitHubAuthenticationError("No token")):
            fetcher = RepositoryFetcher()

        assert fetcher.github_client is None


class TestRepositoryFetcherAuthentication:
    """
    TestRepositoryFetcherAuthentication contains unit tests for GitHub API authentication
    functionality. It verifies that the authentication process correctly handles various
    token sources, validates credentials, and provides appropriate error handling.

    Test Cases:
    - test_authenticate_github_with_env_token: Tests authentication using environment variables
    - test_authenticate_github_with_config_token: Tests authentication using configuration tokens
    - test_authenticate_github_multiple_sources: Tests token source priority handling
    - test_authenticate_github_no_token: Tests behavior when no tokens are available
    - test_authenticate_github_invalid_token: Tests handling of invalid tokens
    - test_authenticate_github_pygithub_unavailable: Tests behavior when PyGithub is not installed
    """

    def setup_method(self):
        """Set up test fixtures for authentication tests."""
        self.mock_config = {
            'GITHUB_ORGANIZATION': 'test-org',
            'ASSIGNMENT_NAME': 'test-assignment'
        }

    @patch('classdock.repos.fetch.GITHUB_AVAILABLE', True)
    @patch('classdock.repos.fetch.Github')
    @patch('classdock.repos.fetch.PathManager')
    @patch('classdock.repos.fetch.GitManager')
    @patch('classdock.repos.fetch.ConfigLoader')
    @patch('classdock.repos.fetch.os.getenv')
    def test_authenticate_github_with_env_token(self, mock_getenv, mock_config_loader, mock_git_manager,
                                                mock_path_manager, mock_github_class):
        """
        Test GitHub authentication using environment variable token.

        This test verifies that the authenticate_github method correctly retrieves
        tokens from environment variables and successfully authenticates with the
        GitHub API.
        """
        mock_config_instance = Mock()
        mock_config_instance.load.return_value = self.mock_config
        mock_config_loader.return_value = mock_config_instance

        # Mock os.getenv to return our test token for GITHUB_ACCESS_TOKEN
        def mock_getenv_side_effect(key, default=None):
            if key == 'GITHUB_TOKEN':
                return None
            elif key == 'GITHUB_ACCESS_TOKEN':
                return 'test_token'
            return default

        mock_getenv.side_effect = mock_getenv_side_effect

        mock_github_client = Mock()
        mock_user = Mock()
        mock_user.login = "test-user"
        mock_github_client.get_user.return_value = mock_user
        mock_github_class.return_value = mock_github_client

        fetcher = RepositoryFetcher.__new__(RepositoryFetcher)
        fetcher.config_loader = mock_config_instance
        fetcher.config = self.mock_config
        fetcher.git_manager = mock_git_manager.return_value
        fetcher.path_manager = mock_path_manager.return_value
        fetcher.github_client = None

        result = fetcher.authenticate_github()

        assert result is True
        assert fetcher.github_client == mock_github_client
        mock_github_class.assert_called_once_with('test_token')
        mock_github_client.get_user.assert_called_once()

    @patch('classdock.repos.fetch.GITHUB_AVAILABLE', True)
    @patch('classdock.repos.fetch.Github')
    @patch('classdock.repos.fetch.PathManager')
    @patch('classdock.repos.fetch.GitManager')
    @patch('classdock.repos.fetch.ConfigLoader')
    @patch('classdock.repos.fetch.os.getenv')
    def test_authenticate_github_with_config_token(self, mock_getenv, mock_config_loader, mock_git_manager,
                                                   mock_path_manager, mock_github_class):
        """
        Test GitHub authentication using configuration file token.

        This test verifies that when environment variables are not available,
        the authenticate_github method falls back to configuration file tokens.
        """
        config_with_token = {**self.mock_config,
                             'GITHUB_ACCESS_TOKEN': 'config_token'}
        mock_config_instance = Mock()
        mock_config_instance.load.return_value = config_with_token
        mock_config_loader.return_value = mock_config_instance

        # Mock environment variables to return None (no env tokens)
        mock_getenv.return_value = None

        mock_github_client = Mock()
        mock_user = Mock()
        mock_user.login = "test-user"
        mock_github_client.get_user.return_value = mock_user
        mock_github_class.return_value = mock_github_client

        fetcher = RepositoryFetcher.__new__(RepositoryFetcher)
        fetcher.config_loader = mock_config_instance
        fetcher.config = config_with_token
        fetcher.git_manager = mock_git_manager.return_value
        fetcher.path_manager = mock_path_manager.return_value
        fetcher.github_client = None

        result = fetcher.authenticate_github()

        assert result is True
        mock_github_class.assert_called_once_with('config_token')

    @patch('classdock.repos.fetch.GITHUB_AVAILABLE', True)
    @patch('classdock.repos.fetch.Github')
    @patch('classdock.repos.fetch.PathManager')
    @patch('classdock.repos.fetch.GitManager')
    @patch('classdock.repos.fetch.ConfigLoader')
    @patch('classdock.repos.fetch.os.getenv')
    def test_authenticate_github_no_token(self, mock_getenv, mock_config_loader, mock_git_manager,
                                          mock_path_manager, mock_github_class):
        """
        Test GitHub authentication failure when no tokens are available.

        This test verifies that when no authentication tokens are found in any
        source, the authenticate_github method raises appropriate exceptions.
        """
        mock_config_instance = Mock()
        mock_config_instance.load.return_value = self.mock_config
        mock_config_loader.return_value = mock_config_instance

        # Mock environment variables to return None (no tokens)
        mock_getenv.return_value = None

        fetcher = RepositoryFetcher.__new__(RepositoryFetcher)
        fetcher.config_loader = mock_config_instance
        fetcher.config = self.mock_config
        fetcher.git_manager = mock_git_manager.return_value
        fetcher.path_manager = mock_path_manager.return_value
        fetcher.github_client = None

        with pytest.raises(GitHubAuthenticationError, match="No valid GitHub token found"):
            fetcher.authenticate_github()

    @patch('classdock.repos.fetch.GITHUB_AVAILABLE', False)
    @patch('classdock.repos.fetch.PathManager')
    @patch('classdock.repos.fetch.GitManager')
    @patch('classdock.repos.fetch.ConfigLoader')
    def test_authenticate_github_pygithub_unavailable(self, mock_config_loader, mock_git_manager, mock_path_manager):
        """
        Test GitHub authentication when PyGithub library is not available.

        This test verifies that when PyGithub is not installed, the authenticate_github
        method raises appropriate exceptions indicating the missing dependency.
        """
        mock_config_instance = Mock()
        mock_config_instance.load.return_value = self.mock_config
        mock_config_loader.return_value = mock_config_instance

        fetcher = RepositoryFetcher.__new__(RepositoryFetcher)
        fetcher.config_loader = mock_config_instance
        fetcher.config = self.mock_config
        fetcher.git_manager = mock_git_manager.return_value
        fetcher.path_manager = mock_path_manager.return_value
        fetcher.github_client = None

        with pytest.raises(GitHubAuthenticationError, match="PyGithub library not available"):
            fetcher.authenticate_github()


class TestRepositoryFetcherDiscovery:
    """
    TestRepositoryFetcherDiscovery contains unit tests for repository discovery functionality
    through both GitHub API and CLI methods. It verifies that repositories are correctly
    discovered, filtered, and classified based on assignment patterns.

    Test Cases:
    - test_discover_repositories_via_api: Tests API-based repository discovery
    - test_discover_repositories_via_cli: Tests CLI-based repository discovery fallback
    - test_discover_repositories_missing_params: Tests parameter validation
    - test_discover_repositories_config_fallback: Tests configuration parameter resolution
    - test_discover_repositories_api_error: Tests error handling for API failures
    - test_discover_repositories_cli_error: Tests error handling for CLI failures
    """

    def setup_method(self):
        """Set up test fixtures for discovery tests."""
        self.mock_config = {
            'GITHUB_ORGANIZATION': 'test-org',
            'ASSIGNMENT_NAME': 'python-basics',
            'TEMPLATE_REPO_URL': 'https://github.com/test-org/python-basics-template.git'
        }

    @patch('classdock.repos.fetch.PathManager')
    @patch('classdock.repos.fetch.GitManager')
    @patch('classdock.repos.fetch.ConfigLoader')
    def test_discover_repositories_via_api(self, mock_config_loader, mock_git_manager, mock_path_manager):
        """
        Test repository discovery using GitHub API.

        This test verifies that the discover_repositories method correctly uses
        the GitHub API to find repositories matching the assignment pattern
        and properly classifies them as student or template repositories.
        """
        mock_config_instance = Mock()
        mock_config_instance.load.return_value = self.mock_config
        mock_config_loader.return_value = mock_config_instance

        # Create mock GitHub client and organization
        mock_github_client = Mock()
        mock_org = Mock()
        mock_github_client.get_organization.return_value = mock_org

        # Create mock repositories
        mock_repos = []
        repo_data = [
            ('python-basics-student1', False),
            ('python-basics-student2', False),
            ('python-basics-template', True),
            ('other-assignment-student1', False)
        ]

        for repo_name, is_template in repo_data:
            mock_repo = Mock()
            mock_repo.name = repo_name
            mock_repo.html_url = f"https://github.com/test-org/{repo_name}"
            mock_repo.clone_url = f"https://github.com/test-org/{repo_name}.git"
            mock_repos.append(mock_repo)

        mock_org.get_repos.return_value = mock_repos

        fetcher = RepositoryFetcher.__new__(RepositoryFetcher)
        fetcher.config_loader = mock_config_instance
        fetcher.config = self.mock_config
        fetcher.git_manager = mock_git_manager.return_value
        fetcher.path_manager = mock_path_manager.return_value
        fetcher.github_client = mock_github_client

        repositories = fetcher.discover_repositories(
            'python-basics', 'test-org')

        # Only repos with 'python-basics' in name
        assert len(repositories) == 3
        student_repos = [r for r in repositories if r.is_student_repo]
        template_repos = [r for r in repositories if r.is_template]

        assert len(student_repos) == 2
        assert len(template_repos) == 1
        assert 'student1' in student_repos[0].student_identifier
        assert 'student2' in student_repos[1].student_identifier

    @patch('classdock.repos.fetch.subprocess.run')
    @patch('classdock.repos.fetch.PathManager')
    @patch('classdock.repos.fetch.GitManager')
    @patch('classdock.repos.fetch.ConfigLoader')
    def test_discover_repositories_via_cli(self, mock_config_loader, mock_git_manager,
                                           mock_path_manager, mock_subprocess):
        """
        Test repository discovery using GitHub CLI fallback.

        This test verifies that when GitHub API is not available, the
        discover_repositories method falls back to using GitHub CLI
        commands and correctly parses the output.
        """
        mock_config_instance = Mock()
        mock_config_instance.load.return_value = self.mock_config
        mock_config_loader.return_value = mock_config_instance

        # Mock subprocess output
        cli_output = """test-org/python-basics-student1\tStudent repo\tprivate
test-org/python-basics-student2\tStudent repo\tprivate
test-org/python-basics-template\tTemplate repo\tpublic
test-org/other-assignment-student1\tOther repo\tprivate"""

        mock_result = Mock()
        mock_result.stdout = cli_output
        mock_subprocess.return_value = mock_result

        fetcher = RepositoryFetcher.__new__(RepositoryFetcher)
        fetcher.config_loader = mock_config_instance
        fetcher.config = self.mock_config
        fetcher.git_manager = mock_git_manager.return_value
        fetcher.path_manager = mock_path_manager.return_value
        fetcher.github_client = None

        repositories = fetcher.discover_repositories(
            'python-basics', 'test-org')

        assert len(repositories) == 3
        mock_subprocess.assert_called_once_with(
            ['gh', 'repo', 'list', 'test-org', '--limit', '1000'],
            capture_output=True, text=True, check=True
        )

    @patch('classdock.repos.fetch.PathManager')
    @patch('classdock.repos.fetch.GitManager')
    @patch('classdock.repos.fetch.ConfigLoader')
    def test_discover_repositories_missing_params(self, mock_config_loader, mock_git_manager, mock_path_manager):
        """
        Test repository discovery with missing required parameters.

        This test verifies that when required parameters (assignment_prefix or organization)
        are missing and cannot be resolved from configuration, appropriate exceptions are raised.
        """
        incomplete_config = {
            'GITHUB_ORGANIZATION': 'test-org'}  # Missing assignment name
        mock_config_instance = Mock()
        mock_config_instance.load.return_value = incomplete_config
        mock_config_loader.return_value = mock_config_instance

        fetcher = RepositoryFetcher.__new__(RepositoryFetcher)
        fetcher.config_loader = mock_config_instance
        fetcher.config = incomplete_config
        fetcher.git_manager = mock_git_manager.return_value
        fetcher.path_manager = mock_path_manager.return_value
        fetcher.github_client = None

        with pytest.raises(GitHubDiscoveryError, match="Missing required parameters"):
            fetcher.discover_repositories()


class TestRepositoryFetcherFiltering:
    """
    TestRepositoryFetcherFiltering contains unit tests for repository filtering and
    classification functionality. It verifies that repositories are correctly
    identified as student repositories, template repositories, or other types
    based on naming patterns and filtering criteria.

    Test Cases:
    - test_is_student_repository: Tests student repository identification
    - test_extract_student_identifier: Tests student identifier extraction
    - test_filter_student_repositories: Tests repository filtering logic
    - test_filter_with_options: Tests filtering with include/exclude options
    - test_get_repository_summary: Tests repository statistics generation
    """

    def setup_method(self):
        """Set up test fixtures for filtering tests."""
        self.repositories = [
            RepositoryInfo("python-basics-student1", "url1",
                           "clone1", False, True, "student1"),
            RepositoryInfo("python-basics-student2", "url2",
                           "clone2", False, True, "student2"),
            RepositoryInfo("python-basics-template", "url3",
                           "clone3", True, False, None),
            RepositoryInfo("python-basics-instructor-tests",
                           "url4", "clone4", False, False, None),
            RepositoryInfo("other-assignment-student1", "url5",
                           "clone5", False, False, None)
        ]

    @patch('classdock.repos.fetch.PathManager')
    @patch('classdock.repos.fetch.GitManager')
    @patch('classdock.repos.fetch.ConfigLoader')
    def test_is_student_repository(self, mock_config_loader, mock_git_manager, mock_path_manager):
        """
        Test student repository identification logic.

        This test verifies that the _is_student_repository method correctly
        identifies repositories as student submissions based on naming patterns
        and excludes template and instructor repositories.
        """
        mock_config_instance = Mock()
        mock_config_instance.load.return_value = {}
        mock_config_loader.return_value = mock_config_instance

        fetcher = RepositoryFetcher.__new__(RepositoryFetcher)
        fetcher.config_loader = mock_config_instance
        fetcher.config = {}
        fetcher.git_manager = mock_git_manager.return_value
        fetcher.path_manager = mock_path_manager.return_value
        fetcher.github_client = None

        # Test student repository identification
        assert fetcher._is_student_repository(
            "python-basics-student1", "python-basics") is True
        assert fetcher._is_student_repository(
            "python-basics-template", "python-basics") is False
        assert fetcher._is_student_repository(
            "python-basics-instructor-tests", "python-basics") is False
        assert fetcher._is_student_repository(
            "other-assignment-student1", "python-basics") is False
        assert fetcher._is_student_repository(
            "python-basics-classroom-template", "python-basics") is False

    @patch('classdock.repos.fetch.PathManager')
    @patch('classdock.repos.fetch.GitManager')
    @patch('classdock.repos.fetch.ConfigLoader')
    def test_extract_student_identifier(self, mock_config_loader, mock_git_manager, mock_path_manager):
        """
        Test student identifier extraction from repository names.

        This test verifies that the _extract_student_identifier method correctly
        extracts student usernames or identifiers from repository names following
        the standard GitHub Classroom naming pattern.
        """
        mock_config_instance = Mock()
        mock_config_instance.load.return_value = {}
        mock_config_loader.return_value = mock_config_instance

        fetcher = RepositoryFetcher.__new__(RepositoryFetcher)
        fetcher.config_loader = mock_config_instance
        fetcher.config = {}
        fetcher.git_manager = mock_git_manager.return_value
        fetcher.path_manager = mock_path_manager.return_value
        fetcher.github_client = None

        # Test student identifier extraction
        assert fetcher._extract_student_identifier(
            "python-basics-student1", "python-basics") == "student1"
        assert fetcher._extract_student_identifier(
            "python-basics-johndoe", "python-basics") == "johndoe"
        assert fetcher._extract_student_identifier(
            "python-basics-template", "python-basics") is None
        assert fetcher._extract_student_identifier(
            "other-assignment-student1", "python-basics") is None

    @patch('classdock.repos.fetch.PathManager')
    @patch('classdock.repos.fetch.GitManager')
    @patch('classdock.repos.fetch.ConfigLoader')
    def test_filter_student_repositories(self, mock_config_loader, mock_git_manager, mock_path_manager):
        """
        Test repository filtering functionality.

        This test verifies that the filter_student_repositories method correctly
        filters a list of repositories to return only those matching specified
        criteria (student repositories, template inclusion/exclusion, etc.).
        """
        mock_config_instance = Mock()
        mock_config_instance.load.return_value = {}
        mock_config_loader.return_value = mock_config_instance

        fetcher = RepositoryFetcher.__new__(RepositoryFetcher)
        fetcher.config_loader = mock_config_instance
        fetcher.config = {}
        fetcher.git_manager = mock_git_manager.return_value
        fetcher.path_manager = mock_path_manager.return_value
        fetcher.github_client = None

        # Test default filtering (students only)
        filtered = fetcher.filter_student_repositories(
            self.repositories, "python-basics")
        assert len(filtered) == 2
        assert all(r.is_student_repo for r in filtered)

        # Test including template
        filtered_with_template = fetcher.filter_student_repositories(
            self.repositories, "python-basics", include_template=True
        )
        assert len(filtered_with_template) == 3
        assert any(r.is_template for r in filtered_with_template)

    @patch('classdock.repos.fetch.PathManager')
    @patch('classdock.repos.fetch.GitManager')
    @patch('classdock.repos.fetch.ConfigLoader')
    def test_get_repository_summary(self, mock_config_loader, mock_git_manager, mock_path_manager):
        """
        Test repository summary statistics generation.

        This test verifies that the get_repository_summary method correctly
        generates statistical summaries of repository collections including
        counts of different repository types.
        """
        mock_config_instance = Mock()
        mock_config_instance.load.return_value = {}
        mock_config_loader.return_value = mock_config_instance

        fetcher = RepositoryFetcher.__new__(RepositoryFetcher)
        fetcher.config_loader = mock_config_instance
        fetcher.config = {}
        fetcher.git_manager = mock_git_manager.return_value
        fetcher.path_manager = mock_path_manager.return_value
        fetcher.github_client = None

        summary = fetcher.get_repository_summary(self.repositories)

        assert summary['total'] == 5
        assert summary['student_repos'] == 2
        assert summary['template_repos'] == 1
        assert summary['other_repos'] == 2


class TestRepositoryFetcherSingleFetch:
    """
    TestRepositoryFetcherSingleFetch contains unit tests for individual repository
    fetching operations. It verifies that single repositories are correctly
    cloned or updated with proper error handling and result tracking.

    Test Cases:
    - test_fetch_single_repository_clone: Tests cloning new repositories
    - test_fetch_single_repository_update: Tests updating existing repositories
    - test_fetch_single_repository_error: Tests error handling during fetch operations
    - test_fetch_single_repository_result_tracking: Tests detailed result information
    """

    def setup_method(self):
        """Set up test fixtures for single fetch tests."""
        self.repo_info = RepositoryInfo(
            name="python-basics-student1",
            url="https://github.com/test-org/python-basics-student1",
            clone_url="https://github.com/test-org/python-basics-student1.git",
            is_student_repo=True,
            student_identifier="student1"
        )

    @patch('classdock.repos.fetch.PathManager')
    @patch('classdock.repos.fetch.GitManager')
    @patch('classdock.repos.fetch.ConfigLoader')
    def test_fetch_single_repository_clone(self, mock_config_loader, mock_git_manager, mock_path_manager):
        """
        Test cloning a new repository.

        This test verifies that when a repository doesn't exist locally,
        the fetch_single_repository method correctly clones it using
        GitManager and returns appropriate result information.
        """
        mock_config_instance = Mock()
        mock_config_instance.load.return_value = {}
        mock_config_loader.return_value = mock_config_instance

        mock_path_manager_instance = Mock()
        mock_local_path = Mock()
        mock_local_path.exists.return_value = False
        mock_local_path.__str__ = Mock(
            return_value="/output/student-repos/python-basics-student1")
        mock_path_manager_instance.ensure_output_directory.return_value = Path(
            "/output/student-repos")
        mock_path_manager.return_value = mock_path_manager_instance

        mock_git_manager_instance = Mock()
        mock_git_manager_instance.clone_repo.return_value = True
        mock_git_manager.return_value = mock_git_manager_instance

        with patch('pathlib.Path') as mock_path_class:
            mock_path_class.return_value = mock_local_path

            fetcher = RepositoryFetcher.__new__(RepositoryFetcher)
            fetcher.config_loader = mock_config_instance
            fetcher.config = {}
            fetcher.git_manager = mock_git_manager_instance
            fetcher.path_manager = mock_path_manager_instance
            fetcher.github_client = None

            result = fetcher.fetch_single_repository(self.repo_info)

        assert result.success is True
        assert result.was_cloned is True
        assert result.was_updated is False
        assert result.repository == self.repo_info
        mock_git_manager_instance.clone_repo.assert_called_once()

    @patch('classdock.repos.fetch.PathManager')
    @patch('classdock.repos.fetch.GitManager')
    @patch('classdock.repos.fetch.ConfigLoader')
    def test_fetch_single_repository_update(self, mock_config_loader, mock_git_manager, mock_path_manager):
        """
        Test updating an existing repository.

        This test verifies that when a repository already exists locally,
        the fetch_single_repository method correctly updates it using
        GitManager and returns appropriate result information.
        """
        mock_config_instance = Mock()
        mock_config_instance.load.return_value = {}
        mock_config_loader.return_value = mock_config_instance

        mock_path_manager_instance = Mock()
        mock_local_path = Mock()
        mock_local_path.exists.return_value = True
        mock_git_subdir = Mock()
        mock_git_subdir.exists.return_value = True
        mock_local_path.__truediv__ = Mock(
            return_value=mock_git_subdir)  # Handle / operator

        # Mock the base directory and its division operation
        mock_base_dir = Mock()
        mock_base_dir.__truediv__ = Mock(
            return_value=mock_local_path)  # base_dir / repo_name
        mock_path_manager_instance.ensure_output_directory.return_value = mock_base_dir
        mock_path_manager.return_value = mock_path_manager_instance

        mock_git_manager_instance = Mock()
        mock_git_manager.return_value = mock_git_manager_instance

        # Mock for the GitManager created for the existing repo
        mock_repo_git_manager = Mock()
        mock_repo_git_manager.pull_repo.return_value = True

        with patch('classdock.repos.fetch.GitManager', return_value=mock_repo_git_manager) as mock_git_class:
            fetcher = RepositoryFetcher.__new__(RepositoryFetcher)
            fetcher.config_loader = mock_config_instance
            fetcher.config = {}
            fetcher.git_manager = mock_git_manager_instance
            fetcher.path_manager = mock_path_manager_instance
            fetcher.github_client = None

            result = fetcher.fetch_single_repository(self.repo_info)

        assert result.success is True
        assert result.was_cloned is False
        assert result.was_updated is True
        assert result.repository == self.repo_info
        mock_repo_git_manager.pull_repo.assert_called_once()


class TestRepositoryFetcherBatchFetch:
    """
    TestRepositoryFetcherBatchFetch contains unit tests for batch repository
    fetching operations. It verifies that multiple repositories are processed
    with proper progress tracking, error handling, and result aggregation.

    Test Cases:
    - test_fetch_repositories_success: Tests successful batch fetching
    - test_fetch_repositories_mixed_results: Tests handling of partial failures
    - test_fetch_repositories_progress_tracking: Tests progress logging and tracking
    - test_fetch_repositories_error_resilience: Tests error isolation in batch operations
    """

    def setup_method(self):
        """Set up test fixtures for batch fetch tests."""
        self.repo_list = [
            RepositoryInfo("repo1", "url1", "clone1", False, True, "student1"),
            RepositoryInfo("repo2", "url2", "clone2", False, True, "student2"),
            RepositoryInfo("repo3", "url3", "clone3", False, True, "student3")
        ]

    @patch('classdock.repos.fetch.PathManager')
    @patch('classdock.repos.fetch.GitManager')
    @patch('classdock.repos.fetch.ConfigLoader')
    def test_fetch_repositories_success(self, mock_config_loader, mock_git_manager, mock_path_manager):
        """
        Test successful batch repository fetching.

        This test verifies that when all repository fetch operations succeed,
        the fetch_repositories method returns successful results for all
        repositories with proper progress tracking.
        """
        mock_config_instance = Mock()
        mock_config_instance.load.return_value = {}
        mock_config_loader.return_value = mock_config_instance

        fetcher = RepositoryFetcher.__new__(RepositoryFetcher)
        fetcher.config_loader = mock_config_instance
        fetcher.config = {}
        fetcher.git_manager = mock_git_manager.return_value
        fetcher.path_manager = mock_path_manager.return_value
        fetcher.github_client = None

        # Mock successful fetch results
        with patch.object(fetcher, 'fetch_single_repository') as mock_fetch:
            mock_fetch.side_effect = [
                FetchResult(repo, True, Path(
                    f"/path/{repo.name}"), None, True, False)
                for repo in self.repo_list
            ]

            results = fetcher.fetch_repositories(self.repo_list)

        assert len(results) == 3
        assert all(r.success for r in results)
        assert mock_fetch.call_count == 3

    @patch('classdock.repos.fetch.PathManager')
    @patch('classdock.repos.fetch.GitManager')
    @patch('classdock.repos.fetch.ConfigLoader')
    def test_fetch_repositories_mixed_results(self, mock_config_loader, mock_git_manager, mock_path_manager):
        """
        Test batch fetching with mixed success and failure results.

        This test verifies that when some repository fetch operations fail,
        the fetch_repositories method continues processing other repositories
        and properly tracks both successful and failed operations.
        """
        mock_config_instance = Mock()
        mock_config_instance.load.return_value = {}
        mock_config_loader.return_value = mock_config_instance

        fetcher = RepositoryFetcher.__new__(RepositoryFetcher)
        fetcher.config_loader = mock_config_instance
        fetcher.config = {}
        fetcher.git_manager = mock_git_manager.return_value
        fetcher.path_manager = mock_path_manager.return_value
        fetcher.github_client = None

        # Mock mixed results (success, failure, success)
        with patch.object(fetcher, 'fetch_single_repository') as mock_fetch:
            mock_fetch.side_effect = [
                FetchResult(self.repo_list[0], True, Path(
                    "/path/repo1"), None, True, False),
                FetchResult(self.repo_list[1], False,
                            None, "Clone failed", False, False),
                FetchResult(self.repo_list[2], True, Path(
                    "/path/repo3"), None, True, False)
            ]

            results = fetcher.fetch_repositories(self.repo_list)

        assert len(results) == 3
        assert results[0].success is True
        assert results[1].success is False
        assert results[2].success is True
        assert "Clone failed" in results[1].error_message


class TestRepositoryFetcherTemplateSync:
    """
    TestRepositoryFetcherTemplateSync contains unit tests for template repository
    synchronization functionality. It verifies that template repositories are
    correctly fetched, updated, and managed for distribution to student repositories.

    Test Cases:
    - test_sync_template_repository_clone: Tests cloning template repositories
    - test_sync_template_repository_update: Tests updating existing template repositories
    - test_sync_template_repository_no_config: Tests behavior with missing template config
    - test_sync_template_repository_error: Tests error handling during template sync
    """

    @patch('classdock.repos.fetch.PathManager')
    @patch('classdock.repos.fetch.GitManager')
    @patch('classdock.repos.fetch.ConfigLoader')
    def test_sync_template_repository_clone(self, mock_config_loader, mock_git_manager, mock_path_manager):
        """
        Test cloning a template repository.

        This test verifies that when a template repository doesn't exist locally,
        the sync_template_repository method correctly clones it from the configured
        template repository URL.
        """
        config_with_template = {
            'TEMPLATE_REPO_URL': 'https://github.com/test-org/python-basics-template.git'
        }
        mock_config_instance = Mock()
        mock_config_instance.load.return_value = config_with_template
        mock_config_loader.return_value = mock_config_instance

        mock_path_manager_instance = Mock()
        mock_template_path = Mock()
        mock_template_path.exists.return_value = False
        mock_base_path = Mock()
        # Handle / operator for base_path / template_name
        mock_base_path.__truediv__ = Mock(return_value=mock_template_path)
        mock_path_manager_instance.ensure_output_directory.return_value = mock_base_path
        mock_path_manager.return_value = mock_path_manager_instance

        mock_git_manager_instance = Mock()
        mock_git_manager_instance.clone_repo.return_value = True
        mock_git_manager.return_value = mock_git_manager_instance

        fetcher = RepositoryFetcher.__new__(RepositoryFetcher)
        fetcher.config_loader = mock_config_instance
        fetcher.config = config_with_template
        fetcher.git_manager = mock_git_manager_instance
        fetcher.path_manager = mock_path_manager_instance
        fetcher.github_client = None

        result = fetcher.sync_template_repository()

        assert result is True
        mock_git_manager_instance.clone_repo.assert_called_once_with(
            'https://github.com/test-org/python-basics-template.git',
            mock_template_path
        )

    @patch('classdock.repos.fetch.PathManager')
    @patch('classdock.repos.fetch.GitManager')
    @patch('classdock.repos.fetch.ConfigLoader')
    def test_sync_template_repository_no_config(self, mock_config_loader, mock_git_manager, mock_path_manager):
        """
        Test template sync behavior with missing template configuration.

        This test verifies that when no template repository URL is configured,
        the sync_template_repository method returns False and logs appropriate
        error messages.
        """
        mock_config_instance = Mock()
        mock_config_instance.load.return_value = {}  # No template config
        mock_config_loader.return_value = mock_config_instance

        fetcher = RepositoryFetcher.__new__(RepositoryFetcher)
        fetcher.config_loader = mock_config_instance
        fetcher.config = {}
        fetcher.git_manager = mock_git_manager.return_value
        fetcher.path_manager = mock_path_manager.return_value
        fetcher.github_client = None

        result = fetcher.sync_template_repository()

        assert result is False


class TestRepositoryFetcherErrorHandling:
    """
    TestRepositoryFetcherErrorHandling contains unit tests for error handling
    and exception scenarios within the RepositoryFetcher class. It verifies
    that various error conditions are handled gracefully with appropriate
    logging and fallback behavior.

    Test Cases:
    - test_discover_repositories_github_api_error: Tests API error handling
    - test_discover_repositories_cli_error: Tests CLI error handling
    - test_fetch_single_repository_git_error: Tests Git operation error handling
    - test_authenticate_github_invalid_token: Tests invalid token handling
    - test_update_repositories_missing_directory: Tests missing directory handling
    """

    @patch('classdock.repos.fetch.PathManager')
    @patch('classdock.repos.fetch.GitManager')
    @patch('classdock.repos.fetch.ConfigLoader')
    def test_discover_repositories_github_api_error(self, mock_config_loader, mock_git_manager, mock_path_manager):
        """
        Test error handling for GitHub API failures during repository discovery.

        This test verifies that when GitHub API calls fail, the discover_repositories
        method raises appropriate exceptions and handles the errors gracefully.
        """
        mock_config_instance = Mock()
        mock_config_instance.load.return_value = {
            'GITHUB_ORGANIZATION': 'test-org',
            'ASSIGNMENT_NAME': 'python-basics'
        }
        mock_config_loader.return_value = mock_config_instance

        mock_github_client = Mock()
        # Mock GitHub exception without importing the actual library
        github_error = Exception("GitHub API Error: 404 Not Found")
        mock_github_client.get_organization.side_effect = github_error

        fetcher = RepositoryFetcher.__new__(RepositoryFetcher)
        fetcher.config_loader = mock_config_instance
        fetcher.config = mock_config_instance.load.return_value
        fetcher.git_manager = mock_git_manager.return_value
        fetcher.path_manager = mock_path_manager.return_value
        fetcher.github_client = mock_github_client

        with pytest.raises(GitHubDiscoveryError):
            fetcher.discover_repositories('python-basics', 'test-org')

    @patch('classdock.repos.fetch.subprocess.run')
    @patch('classdock.repos.fetch.PathManager')
    @patch('classdock.repos.fetch.GitManager')
    @patch('classdock.repos.fetch.ConfigLoader')
    def test_discover_repositories_cli_error(self, mock_config_loader, mock_git_manager,
                                             mock_path_manager, mock_subprocess):
        """
        Test error handling for GitHub CLI failures during repository discovery.

        This test verifies that when GitHub CLI commands fail, the discover_repositories
        method raises appropriate exceptions and handles subprocess errors gracefully.
        """
        mock_config_instance = Mock()
        mock_config_instance.load.return_value = {
            'GITHUB_ORGANIZATION': 'test-org',
            'ASSIGNMENT_NAME': 'python-basics'
        }
        mock_config_loader.return_value = mock_config_instance

        mock_subprocess.side_effect = subprocess.CalledProcessError(1, 'gh')

        fetcher = RepositoryFetcher.__new__(RepositoryFetcher)
        fetcher.config_loader = mock_config_instance
        fetcher.config = mock_config_instance.load.return_value
        fetcher.git_manager = mock_git_manager.return_value
        fetcher.path_manager = mock_path_manager.return_value
        fetcher.github_client = None

        with pytest.raises(GitHubDiscoveryError):
            fetcher.discover_repositories('python-basics', 'test-org')


class TestRepositoryFetcherFetchAllRepositories:
    """
    TestRepositoryFetcherFetchAllRepositories contains unit tests for the fetch_all_repositories
    method added to RepositoryFetcher. This method is the main entry point that combines
    repository discovery and fetching into a single workflow.

    Test Cases:
    - test_fetch_all_repositories_success: Tests successful discovery and fetch workflow
    - test_fetch_all_repositories_missing_config: Tests error when config missing required fields
    - test_fetch_all_repositories_no_repos_found: Tests handling when no repositories discovered
    - test_fetch_all_repositories_all_fetch_failures: Tests when all fetches fail
    - test_fetch_all_repositories_partial_success: Tests partial success scenario
    - test_fetch_all_repositories_exception_handling: Tests exception handling
    """

    @patch('classdock.repos.fetch.PathManager')
    @patch('classdock.repos.fetch.GitManager')
    @patch('classdock.repos.fetch.ConfigLoader')
    def test_fetch_all_repositories_success(self, mock_config_loader, mock_git_manager, mock_path_manager):
        """
        Test successful fetch_all_repositories workflow.

        This test verifies that fetch_all_repositories correctly:
        - Reads configuration for ASSIGNMENT_NAME and GITHUB_ORGANIZATION
        - Calls discover_repositories with correct parameters
        - Calls fetch_repositories with discovered repos
        - Returns True when at least one repository is successfully fetched
        """
        mock_config_instance = Mock()
        mock_config_instance.load.return_value = {
            'ASSIGNMENT_NAME': 'python-basics',
            'GITHUB_ORGANIZATION': 'test-org'
        }
        mock_config_loader.return_value = mock_config_instance

        fetcher = RepositoryFetcher.__new__(RepositoryFetcher)
        fetcher.config_loader = mock_config_instance
        fetcher.config = mock_config_instance.load.return_value
        fetcher.git_manager = mock_git_manager.return_value
        fetcher.path_manager = mock_path_manager.return_value
        fetcher.github_client = None

        # Mock discover_repositories to return test repos
        test_repos = [
            RepositoryInfo(
                name='python-basics-student1',
                url='https://github.com/test-org/python-basics-student1',
                clone_url='https://github.com/test-org/python-basics-student1.git',
                is_student_repo=True,
                student_identifier='student1'
            ),
            RepositoryInfo(
                name='python-basics-student2',
                url='https://github.com/test-org/python-basics-student2',
                clone_url='https://github.com/test-org/python-basics-student2.git',
                is_student_repo=True,
                student_identifier='student2'
            )
        ]

        # Mock fetch_repositories to return successful results
        fetch_results = [
            FetchResult(repository=test_repos[0],
                        success=True, was_cloned=True),
            FetchResult(repository=test_repos[1],
                        success=True, was_cloned=True)
        ]

        with patch.object(fetcher, 'discover_repositories', return_value=test_repos) as mock_discover, \
                patch.object(fetcher, 'fetch_repositories', return_value=fetch_results) as mock_fetch:

            result = fetcher.fetch_all_repositories(verbose=True)

            assert result is True
            mock_discover.assert_called_once_with(
                assignment_prefix='python-basics',
                organization='test-org'
            )
            mock_fetch.assert_called_once_with(test_repos)

    @patch('classdock.repos.fetch.PathManager')
    @patch('classdock.repos.fetch.GitManager')
    @patch('classdock.repos.fetch.ConfigLoader')
    def test_fetch_all_repositories_missing_config(self, mock_config_loader, mock_git_manager, mock_path_manager):
        """
        Test fetch_all_repositories with missing configuration fields.

        This test verifies that fetch_all_repositories returns False and logs
        an error when required configuration fields are missing.
        """
        mock_config_instance = Mock()
        mock_config_instance.load.return_value = {
            'GITHUB_ORGANIZATION': 'test-org'
            # Missing ASSIGNMENT_NAME
        }
        mock_config_loader.return_value = mock_config_instance

        fetcher = RepositoryFetcher.__new__(RepositoryFetcher)
        fetcher.config_loader = mock_config_instance
        fetcher.config = mock_config_instance.load.return_value
        fetcher.git_manager = mock_git_manager.return_value
        fetcher.path_manager = mock_path_manager.return_value
        fetcher.github_client = None

        result = fetcher.fetch_all_repositories(verbose=False)

        assert result is False

    @patch('classdock.repos.fetch.PathManager')
    @patch('classdock.repos.fetch.GitManager')
    @patch('classdock.repos.fetch.ConfigLoader')
    def test_fetch_all_repositories_no_repos_found(self, mock_config_loader, mock_git_manager, mock_path_manager):
        """
        Test fetch_all_repositories when no repositories are discovered.

        This test verifies that fetch_all_repositories returns False and logs
        a warning when discover_repositories returns an empty list.
        """
        mock_config_instance = Mock()
        mock_config_instance.load.return_value = {
            'ASSIGNMENT_NAME': 'python-basics',
            'GITHUB_ORGANIZATION': 'test-org'
        }
        mock_config_loader.return_value = mock_config_instance

        fetcher = RepositoryFetcher.__new__(RepositoryFetcher)
        fetcher.config_loader = mock_config_instance
        fetcher.config = mock_config_instance.load.return_value
        fetcher.git_manager = mock_git_manager.return_value
        fetcher.path_manager = mock_path_manager.return_value
        fetcher.github_client = None

        with patch.object(fetcher, 'discover_repositories', return_value=[]):
            result = fetcher.fetch_all_repositories(verbose=False)

            assert result is False

    @patch('classdock.repos.fetch.PathManager')
    @patch('classdock.repos.fetch.GitManager')
    @patch('classdock.repos.fetch.ConfigLoader')
    def test_fetch_all_repositories_all_fetch_failures(self, mock_config_loader, mock_git_manager, mock_path_manager):
        """
        Test fetch_all_repositories when all repository fetches fail.

        This test verifies that fetch_all_repositories returns False when
        all discovered repositories fail to fetch.
        """
        mock_config_instance = Mock()
        mock_config_instance.load.return_value = {
            'ASSIGNMENT_NAME': 'python-basics',
            'GITHUB_ORGANIZATION': 'test-org'
        }
        mock_config_loader.return_value = mock_config_instance

        fetcher = RepositoryFetcher.__new__(RepositoryFetcher)
        fetcher.config_loader = mock_config_instance
        fetcher.config = mock_config_instance.load.return_value
        fetcher.git_manager = mock_git_manager.return_value
        fetcher.path_manager = mock_path_manager.return_value
        fetcher.github_client = None

        test_repos = [
            RepositoryInfo(
                name='python-basics-student1',
                url='https://github.com/test-org/python-basics-student1',
                clone_url='https://github.com/test-org/python-basics-student1.git',
                is_student_repo=True
            )
        ]

        # All fetches fail
        fetch_results = [
            FetchResult(
                repository=test_repos[0], success=False, error_message="Fetch failed")
        ]

        with patch.object(fetcher, 'discover_repositories', return_value=test_repos), \
                patch.object(fetcher, 'fetch_repositories', return_value=fetch_results):

            result = fetcher.fetch_all_repositories(verbose=False)

            assert result is False

    @patch('classdock.repos.fetch.PathManager')
    @patch('classdock.repos.fetch.GitManager')
    @patch('classdock.repos.fetch.ConfigLoader')
    def test_fetch_all_repositories_partial_success(self, mock_config_loader, mock_git_manager, mock_path_manager):
        """
        Test fetch_all_repositories with partial success.

        This test verifies that fetch_all_repositories returns True when
        at least one repository is successfully fetched, even if others fail.
        """
        mock_config_instance = Mock()
        mock_config_instance.load.return_value = {
            'ASSIGNMENT_NAME': 'python-basics',
            'GITHUB_ORGANIZATION': 'test-org'
        }
        mock_config_loader.return_value = mock_config_instance

        fetcher = RepositoryFetcher.__new__(RepositoryFetcher)
        fetcher.config_loader = mock_config_instance
        fetcher.config = mock_config_instance.load.return_value
        fetcher.git_manager = mock_git_manager.return_value
        fetcher.path_manager = mock_path_manager.return_value
        fetcher.github_client = None

        test_repos = [
            RepositoryInfo(
                name='python-basics-student1',
                url='https://github.com/test-org/python-basics-student1',
                clone_url='https://github.com/test-org/python-basics-student1.git',
                is_student_repo=True
            ),
            RepositoryInfo(
                name='python-basics-student2',
                url='https://github.com/test-org/python-basics-student2',
                clone_url='https://github.com/test-org/python-basics-student2.git',
                is_student_repo=True
            )
        ]

        # One success, one failure
        fetch_results = [
            FetchResult(repository=test_repos[0],
                        success=True, was_cloned=True),
            FetchResult(
                repository=test_repos[1], success=False, error_message="Network error")
        ]

        with patch.object(fetcher, 'discover_repositories', return_value=test_repos), \
                patch.object(fetcher, 'fetch_repositories', return_value=fetch_results):

            result = fetcher.fetch_all_repositories(verbose=False)

            assert result is True

    @patch('classdock.repos.fetch.PathManager')
    @patch('classdock.repos.fetch.GitManager')
    @patch('classdock.repos.fetch.ConfigLoader')
    def test_fetch_all_repositories_exception_handling(self, mock_config_loader, mock_git_manager, mock_path_manager):
        """
        Test fetch_all_repositories exception handling.

        This test verifies that fetch_all_repositories gracefully handles
        exceptions during the workflow and returns False.
        """
        mock_config_instance = Mock()
        mock_config_instance.load.return_value = {
            'ASSIGNMENT_NAME': 'python-basics',
            'GITHUB_ORGANIZATION': 'test-org'
        }
        mock_config_loader.return_value = mock_config_instance

        fetcher = RepositoryFetcher.__new__(RepositoryFetcher)
        fetcher.config_loader = mock_config_instance
        fetcher.config = mock_config_instance.load.return_value
        fetcher.git_manager = mock_git_manager.return_value
        fetcher.path_manager = mock_path_manager.return_value
        fetcher.github_client = None

        with patch.object(fetcher, 'discover_repositories', side_effect=Exception("Unexpected error")):
            result = fetcher.fetch_all_repositories(verbose=False)

            assert result is False


if __name__ == '__main__':
    pytest.main([__file__])
