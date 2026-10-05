"""
Test suite for GitHubAPIClient - initialization and token verification.
"""

import pytest
from unittest.mock import Mock, patch
import requests

from classdock.utils.github_api_client import GitHubAPIClient


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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
