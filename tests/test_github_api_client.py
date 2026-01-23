"""
Test suite for GitHubAPIClient - GitHub Classroom API integration.

This module tests the GitHubAPIClient class that provides GitHub Classroom API
integration with intelligent fallback mechanism for URL parsing.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from dataclasses import dataclass

from classdock.utils.github_api_client import (
    GitHubAPIClient,
    ClassroomInfo,
    AssignmentInfo
)
from classdock.utils.github_exceptions import GitHubAPIError


class TestDataClasses:
    """Test the data classes used for API responses."""

    def test_classroom_info_creation(self):
        """Test ClassroomInfo dataclass creation."""
        classroom = ClassroomInfo(
            id=12345,
            name="Test Classroom",
            url="https://classroom.github.com/classrooms/12345-test",
            organization="test-org"
        )

        assert classroom.id == 12345
        assert classroom.name == "Test Classroom"
        assert classroom.url == "https://classroom.github.com/classrooms/12345-test"
        assert classroom.organization == "test-org"

    def test_assignment_info_creation(self):
        """Test AssignmentInfo dataclass creation."""
        assignment = AssignmentInfo(
            id=67890,
            title="Test Assignment",
            classroom_id=12345,
            invite_link="https://classroom.github.com/assignment-invitations/test",
            organization="test-org"
        )

        assert assignment.id == 67890
        assert assignment.title == "Test Assignment"
        assert assignment.classroom_id == 12345
        assert assignment.invite_link == "https://classroom.github.com/assignment-invitations/test"
        assert assignment.organization == "test-org"


class TestGitHubAPIClientInitialization:
    """Test GitHubAPIClient initialization and basic configuration."""

    def test_init_with_token_parameter(self):
        """Test initialization with token parameter."""
        client = GitHubAPIClient(token="test_token")
        assert client.token == "test_token"
        assert client.base_url == "https://api.github.com"
        assert client.headers["Authorization"] == "token test_token"

    def test_init_with_environment_variable(self):
        """Test initialization with GITHUB_TOKEN environment variable."""
        with patch.dict('os.environ', {'GITHUB_TOKEN': 'env_token'}):
            client = GitHubAPIClient()
            assert client.token == "env_token"

    def test_init_without_token_raises_error(self):
        """Test initialization without token raises ValueError."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="GitHub token is required"):
                GitHubAPIClient()

    def test_custom_base_url(self):
        """Test initialization with custom GitHub API endpoint."""
        # Note: Current implementation uses fixed base_url
        # This test verifies the client uses the correct default
        client = GitHubAPIClient(token="test_token")
        assert client.base_url == "https://api.github.com"


class TestGitHubAPIClientTokenVerification:
    """Test token verification functionality."""

    @patch('requests.get')
    def test_verify_token_success(self, mock_get):
        """Test successful token verification."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"login": "testuser"}
        mock_get.return_value = mock_response

        client = GitHubAPIClient(token="valid_token")
        result = client.verify_token()

        assert result is True
        mock_get.assert_called_once_with(
            "https://api.github.com/user",
            headers=client.headers,
            timeout=10  # GitHubAPIClient includes timeout
        )

    @patch('requests.get')
    def test_verify_token_invalid(self, mock_get):
        """Test token verification with invalid token."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        client = GitHubAPIClient(token="invalid_token")
        result = client.verify_token()

        assert result is False

    @patch('requests.get')
    def test_verify_token_network_error(self, mock_get):
        """Test token verification with network error."""
        mock_get.side_effect = requests.RequestException("Network error")

        client = GitHubAPIClient(token="test_token")
        result = client.verify_token()

        assert result is False


class TestGitHubAPIClientClassroomListing:
    """Test classroom listing functionality."""

    @patch('requests.get')
    def test_list_classrooms_success(self, mock_get):
        """Test successful classroom listing."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": 12345,
                "name": "Test Classroom",
                "url": "https://classroom.github.com/classrooms/12345-test",
                "organization": {"login": "test-org"}
            },
            {
                "id": 67890,
                "name": "Another Classroom",
                "url": "https://classroom.github.com/classrooms/67890-another",
                "organization": {"login": "another-org"}
            }
        ]
        mock_get.return_value = mock_response

        client = GitHubAPIClient(token="test_token")
        classrooms = client.list_classrooms()

        assert len(classrooms) == 2

        assert classrooms[0].id == 12345
        assert classrooms[0].name == "Test Classroom"
        assert classrooms[0].organization == "test-org"

        assert classrooms[1].id == 67890
        assert classrooms[1].name == "Another Classroom"
        assert classrooms[1].organization == "another-org"

    @patch('requests.get')
    def test_list_classrooms_empty_response(self, mock_get):
        """Test classroom listing with empty response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        client = GitHubAPIClient(token="test_token")
        classrooms = client.list_classrooms()

        assert len(classrooms) == 0

    @patch('requests.get')
    def test_list_classrooms_missing_organization(self, mock_get):
        """Test classroom listing with missing organization data."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": 12345,
                "name": "Test Classroom",
                "url": "https://classroom.github.com/classrooms/12345-test"
                # Missing organization field
            }
        ]
        mock_get.return_value = mock_response

        client = GitHubAPIClient(token="test_token")
        classrooms = client.list_classrooms()

        assert len(classrooms) == 1
        # Should default to empty string
        assert classrooms[0].organization == ""


class TestGitHubAPIClientURLExtraction:
    """Test the main URL extraction functionality."""

    def test_extract_classroom_data_from_url_success(self):
        """Test successful classroom data extraction from URL."""
        client = GitHubAPIClient(token="test_token")

        # Mock the list_classrooms method
        mock_classrooms = [
            ClassroomInfo(
                id=225080578,
                name="SOC CS3550 Fall 25",
                url="https://classroom.github.com/classrooms/225080578-soc-cs3550-f25",
                organization="real-org-name"
            )
        ]

        with patch.object(client, 'list_classrooms', return_value=mock_classrooms), \
                patch.object(client, 'list_classroom_assignments', return_value=[]):

            test_url = "https://classroom.github.com/classrooms/225080578-soc-cs3550-f25/assignments/project3"
            result = client.extract_classroom_data_from_url(test_url)

            assert result['success'] is True
            assert result['organization'] == "real-org-name"
            assert result['assignment_name'] == "project3"
            assert result['classroom_id'] == "225080578"
            assert result['classroom_name'] == "SOC CS3550 Fall 25"

    def test_extract_classroom_data_no_matching_classroom(self):
        """Test URL extraction when no matching classroom is found."""
        client = GitHubAPIClient(token="test_token")

        # Mock empty classroom list
        with patch.object(client, 'list_classrooms', return_value=[]):

            test_url = "https://classroom.github.com/classrooms/225080578-soc-cs3550-f25/assignments/project3"
            result = client.extract_classroom_data_from_url(test_url)

            assert result['success'] is False
            assert "No classroom found matching" in result['error']

    def test_extract_classroom_data_invalid_url_format(self):
        """Test URL extraction with invalid URL format."""
        client = GitHubAPIClient(token="test_token")

        test_url = "https://invalid-url.com/not-a-classroom"
        result = client.extract_classroom_data_from_url(test_url)

        assert result['success'] is False
        assert "Invalid classroom URL format" in result['error']

    def test_extract_classroom_data_with_assignment_match(self):
        """Test URL extraction with matching assignment."""
        client = GitHubAPIClient(token="test_token")

        # Mock classroom and assignment data
        mock_classrooms = [
            ClassroomInfo(
                id=225080578,
                name="SOC CS3550 Fall 25",
                url="https://classroom.github.com/classrooms/225080578-soc-cs3550-f25",
                organization="real-org-name"
            )
        ]

        mock_assignments = [
            AssignmentInfo(
                id=12345,
                title="project3",
                classroom_id=225080578,
                invite_link="https://classroom.github.com/assignment-invitations/test",
                organization="real-org-name"
            )
        ]

        with patch.object(client, 'list_classrooms', return_value=mock_classrooms), \
                patch.object(client, 'list_classroom_assignments', return_value=mock_assignments):

            test_url = "https://classroom.github.com/classrooms/225080578-soc-cs3550-f25/assignments/project3"
            result = client.extract_classroom_data_from_url(test_url)

            assert result['success'] is True
            assert result['assignment_id'] == "12345"
            assert result['invite_link'] == "https://classroom.github.com/assignment-invitations/test"


class TestGitHubAPIClientIntegration:
    """Test integration scenarios and error handling."""

    def test_api_request_failure(self):
        """Test handling of API request failures."""
        client = GitHubAPIClient(token="test_token")

        with patch.object(client, 'list_classrooms', side_effect=requests.RequestException("API Error")):

            test_url = "https://classroom.github.com/classrooms/225080578-soc-cs3550-f25/assignments/project3"
            result = client.extract_classroom_data_from_url(test_url)

            assert result['success'] is False
            # Error message is passed through
            assert "API Error" in result['error']

    def test_partial_classroom_data(self):
        """Test handling of partial classroom data from API."""
        client = GitHubAPIClient(token="test_token")

        # Mock classroom with minimal data
        mock_classrooms = [
            ClassroomInfo(
                id=225080578,
                name="",  # Empty name
                url="https://classroom.github.com/classrooms/225080578-soc-cs3550-f25",
                organization="real-org-name"
            )
        ]

        with patch.object(client, 'list_classrooms', return_value=mock_classrooms), \
                patch.object(client, 'list_classroom_assignments', return_value=[]):

            test_url = "https://classroom.github.com/classrooms/225080578-soc-cs3550-f25/assignments/project3"
            result = client.extract_classroom_data_from_url(test_url)

            assert result['success'] is True
            assert result['organization'] == "real-org-name"
            # Should handle empty name gracefully
            assert result['classroom_name'] == ""


class TestOrganizationValidation:
    """Test the organization validation logic."""

    def test_classroom_name_detection_numeric_patterns(self):
        """Test detection of numeric classroom name patterns."""
        # Should be detected as classroom names
        assert GitHubAPIClient.is_likely_classroom_name(
            "225080578-soc-cs3550-f25") is True
        assert GitHubAPIClient.is_likely_classroom_name(
            "12345-programming-course") is True
        assert GitHubAPIClient.is_likely_classroom_name(
            "999999-test-class") is True

    def test_classroom_name_detection_academic_patterns(self):
        """Test detection of academic term patterns."""
        # Should be detected as classroom names
        assert GitHubAPIClient.is_likely_classroom_name(
            "cs101-fall2024") is True
        assert GitHubAPIClient.is_likely_classroom_name(
            "spring2024-math101") is True
        assert GitHubAPIClient.is_likely_classroom_name(
            "cs3550_fall_2024") is True
        assert GitHubAPIClient.is_likely_classroom_name(
            "course-2024-spring") is True

    def test_classroom_name_detection_course_patterns(self):
        """Test detection of course code patterns."""
        # Should be detected as classroom names
        assert GitHubAPIClient.is_likely_classroom_name("cs101-intro") is True
        assert GitHubAPIClient.is_likely_classroom_name(
            "math3550-calculus") is True
        assert GitHubAPIClient.is_likely_classroom_name(
            "soc-cs3550-f25") is True

    def test_real_organization_detection(self):
        """Test that real organization names are not flagged."""
        # Should NOT be detected as classroom names
        assert GitHubAPIClient.is_likely_classroom_name("github") is False
        assert GitHubAPIClient.is_likely_classroom_name("microsoft") is False
        assert GitHubAPIClient.is_likely_classroom_name("python-org") is False
        assert GitHubAPIClient.is_likely_classroom_name(
            "open-source-project") is False
        assert GitHubAPIClient.is_likely_classroom_name(
            "classdock") is False
        assert GitHubAPIClient.is_likely_classroom_name(
            "my-awesome-project") is False

    def test_edge_cases(self):
        """Test edge cases and special inputs."""
        assert GitHubAPIClient.is_likely_classroom_name("") is False
        assert GitHubAPIClient.is_likely_classroom_name("a") is False
        assert GitHubAPIClient.is_likely_classroom_name("123") is False


class TestEnhancedAPIIntegration:
    """Test the enhanced API integration modes."""

    @patch('os.getenv')
    @patch('classdock.assignments.setup.print_status')
    @patch('classdock.assignments.setup.logger')
    @patch('classdock.assignments.setup.URLParser.validate_classroom_url')
    def test_api_mode_always(self, mock_validate, mock_logger, mock_print_status, mock_getenv):
        """Test CLASSROOM_API_MODE=always forces API usage."""
        from classdock.assignments.setup import AssignmentSetup

        # Mock environment variable
        def getenv_side_effect(key, default=None):
            if key == 'CLASSROOM_API_MODE':
                return 'always'
            return default
        mock_getenv.side_effect = getenv_side_effect

        mock_validate.return_value = True

        with patch('classdock.utils.github_api_client.GitHubAPIClient') as mock_api_client_class:
            mock_api_client = Mock()
            mock_api_client.verify_token.return_value = True
            mock_api_client.extract_classroom_data_from_url.return_value = {
                'success': True,
                'organization': 'real-github-org',
                'assignment_name': 'project3',
                'classroom_name': 'Test Classroom',
                'classroom_id': '12345'
            }
            mock_api_client_class.return_value = mock_api_client

            setup = AssignmentSetup()
            setup.url_parser.parse_classroom_url.return_value = {
                'organization': 'normal-org',  # Looks like real org
                'assignment_name': 'project3'
            }

            test_url = "https://classroom.github.com/classrooms/12345-test/assignments/project3"
            result = setup._populate_from_url(test_url)

            # Should use API even though URL parsing looks good
            assert result is True
            assert setup.config_values['GITHUB_ORGANIZATION'] == 'real-github-org'
            mock_api_client.verify_token.assert_called_once()

    @patch('os.getenv')
    @patch('classdock.assignments.setup.URLParser.validate_classroom_url')
    def test_api_mode_never(self, mock_validate, mock_getenv):
        """Test CLASSROOM_API_MODE=never skips API usage."""
        from classdock.assignments.setup import AssignmentSetup

        # Mock environment variable
        def getenv_side_effect(key, default=None):
            if key == 'CLASSROOM_API_MODE':
                return 'never'
            return default
        mock_getenv.side_effect = getenv_side_effect

        mock_validate.return_value = True

        setup = AssignmentSetup()
        setup.url_parser.parse_classroom_url.return_value = {
            'organization': '225080578-soc-cs3550-f25',  # Looks like classroom name
            'assignment_name': 'project3'
        }

        test_url = "https://classroom.github.com/classrooms/225080578-soc-cs3550-f25/assignments/project3"

        with patch('classdock.assignments.setup.logger'):
            result = setup._populate_from_url(test_url)

        # Should use URL parsing result without API validation
        assert result is True
        # URLParser returns 'organization' field as 'soc-cs3550-f25', not the full classroom_id
        assert setup.config_values['GITHUB_ORGANIZATION'] == 'soc-cs3550-f25'

    @patch('os.getenv')
    @patch('classdock.assignments.setup.print_status')
    @patch('classdock.assignments.setup.logger')
    @patch('classdock.assignments.setup.URLParser.validate_classroom_url')
    def test_api_mode_auto_with_classroom_name(self, mock_validate, mock_logger, mock_print_status, mock_getenv):
        """Test CLASSROOM_API_MODE=auto triggers API when org looks like classroom name."""
        from classdock.assignments.setup import AssignmentSetup

        # Mock environment variable (auto is default)
        def getenv_side_effect(key, default=None):
            if key == 'CLASSROOM_API_MODE':
                return 'auto'
            return default
        mock_getenv.side_effect = getenv_side_effect

        mock_validate.return_value = True

        with patch('classdock.utils.github_api_client.GitHubAPIClient') as mock_api_client_class:
            mock_api_client = Mock()
            mock_api_client.verify_token.return_value = True
            mock_api_client.extract_classroom_data_from_url.return_value = {
                'success': True,
                'organization': 'real-github-org',
                'assignment_name': 'project3',
                'classroom_name': 'SOC CS3550 Fall 25',
                'classroom_id': '225080578'
            }
            mock_api_client_class.return_value = mock_api_client

            setup = AssignmentSetup()
            setup.url_parser.parse_classroom_url.return_value = {
                'organization': '225080578-soc-cs3550-f25',  # Looks like classroom name
                'assignment_name': 'project3'
            }

            test_url = "https://classroom.github.com/classrooms/225080578-soc-cs3550-f25/assignments/project3"
            result = setup._populate_from_url(test_url)

            # Should use API because organization looks like classroom name
            assert result is True
            assert setup.config_values['GITHUB_ORGANIZATION'] == 'real-github-org'
            mock_api_client.verify_token.assert_called_once()


class TestAssignmentSetupIntegration:
    """Test integration with AssignmentSetup._populate_from_url method."""

    @patch('classdock.assignments.setup.print_status')
    @patch('classdock.assignments.setup.logger')
    @patch('classdock.assignments.setup.URLParser.validate_classroom_url')
    def test_api_fallback_integration(self, mock_validate, mock_logger, mock_print_status):
        """Test that AssignmentSetup uses API fallback when URL parsing is insufficient."""
        from classdock.assignments.setup import AssignmentSetup

        # Setup mocks
        mock_validate.return_value = True

        # Mock the GitHubAPIClient at the module level where it's imported
        with patch('classdock.utils.github_api_client.GitHubAPIClient') as mock_api_client_class:
            mock_api_client = Mock()
            mock_api_client.verify_token.return_value = True
            mock_api_client.extract_classroom_data_from_url.return_value = {
                'success': True,
                'organization': 'real-github-org',
                'assignment_name': 'project3',
                'classroom_name': 'SOC CS3550 Fall 25',
                'classroom_id': '225080578'
            }
            mock_api_client_class.return_value = mock_api_client

            # Create setup instance and mock URL parser to return classroom name as org
            setup = AssignmentSetup()
            setup.url_parser.parse_classroom_url.return_value = {
                'organization': '',  # Empty organization triggers API fallback
                'assignment_name': 'project3'
            }

            # Test the integration
            test_url = "https://classroom.github.com/classrooms/225080578-soc-cs3550-f25/assignments/project3"

            result = setup._populate_from_url(test_url)

            # Should succeed and use API-extracted organization
            assert result is True
            assert setup.config_values['GITHUB_ORGANIZATION'] == 'real-github-org'
            assert setup.config_values['ASSIGNMENT_NAME'] == 'project3'
            assert setup.config_values['CLASSROOM_URL'] == test_url

            # Verify API client was called
            mock_api_client.verify_token.assert_called_once()
            mock_api_client.extract_classroom_data_from_url.assert_called_once_with(
                test_url)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
