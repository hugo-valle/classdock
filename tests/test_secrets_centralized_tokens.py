"""
Tests for centralized token integration in SecretsManager.

This module tests the SecretsManager.get_secret_token_value() method and the
integration with the centralized GitHubTokenManager for token retrieval.
"""

import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

from classdock.secrets.manager import SecretsManager
from classdock.config.global_config import SecretsConfig


class TestSecretsManagerCentralizedTokens:
    """Test the SecretsManager centralized token integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = SecretsManager()

    @patch('classdock.utils.token_manager.GitHubTokenManager')
    def test_get_secret_token_value_centralized_token(self, mock_token_manager_class):
        """Test getting token value from centralized token manager."""
        # Mock the GitHubTokenManager
        mock_token_manager = MagicMock()
        mock_token_manager.get_github_token.return_value = "github_pat_test_token_12345"
        mock_token_manager_class.return_value = mock_token_manager

        # Create a secret config that uses centralized tokens
        secret_config = SecretsConfig(
            name="INSTRUCTOR_TESTS_TOKEN",
            description="Token for accessing instructor test repository",
            validate_format=True,
            token_file=None,  # None means use centralized token
            max_age_days=None
        )

        # Get token value
        token_value = self.manager.get_secret_token_value(secret_config)

        # Verify
        assert token_value == "github_pat_test_token_12345"
        mock_token_manager_class.assert_called_once()
        mock_token_manager.get_github_token.assert_called_once()

    @patch('builtins.open', new_callable=mock_open, read_data="file_based_token_12345")
    @patch('pathlib.Path.exists', return_value=True)
    def test_get_secret_token_value_file_based_token(self, mock_exists, mock_file):
        """Test getting token value from file (backward compatibility)."""
        # Create a secret config that uses file-based tokens
        secret_config = SecretsConfig(
            name="OLD_TOKEN",
            description="Old style file-based token",
            validate_format=False,
            token_file="token.txt",  # Non-None means use file-based token
            max_age_days=30
        )

        # Get token value
        token_value = self.manager.get_secret_token_value(secret_config)

        # Verify
        assert token_value == "file_based_token_12345"
        # The code passes a Path object to open, not a string
        mock_file.assert_called_once_with(Path("token.txt"), 'r')

    @patch('builtins.open', side_effect=FileNotFoundError("Token file not found"))
    def test_get_secret_token_value_file_not_found(self, mock_file):
        """Test error handling when token file is not found."""
        secret_config = SecretsConfig(
            name="MISSING_TOKEN",
            description="Token with missing file",
            validate_format=False,
            token_file="missing_token.txt",
            max_age_days=30
        )

        with pytest.raises(FileNotFoundError, match="Token file not found"):
            self.manager.get_secret_token_value(secret_config)

    @patch('classdock.utils.token_manager.GitHubTokenManager')
    def test_get_secret_token_value_centralized_token_error(self, mock_token_manager_class):
        """Test error handling when centralized token retrieval fails."""
        # Mock the GitHubTokenManager to raise an exception
        mock_token_manager = MagicMock()
        mock_token_manager.get_github_token.side_effect = Exception(
            "Token retrieval failed")
        mock_token_manager_class.return_value = mock_token_manager

        secret_config = SecretsConfig(
            name="FAILED_TOKEN",
            description="Token that fails to retrieve",
            validate_format=True,
            token_file=None,
            max_age_days=None
        )

        with pytest.raises(Exception, match="Token retrieval failed"):
            self.manager.get_secret_token_value(secret_config)

    @patch('classdock.secrets.manager.SecretsManager.get_secret_token_value')
    @patch('classdock.config.global_config.get_global_config')
    def test_add_secrets_from_global_config_centralized_tokens(self, mock_get_global_config, mock_get_token_value):
        """Test adding secrets from global config with centralized tokens."""
        # Mock global config
        mock_config = MagicMock()
        mock_config.secrets_config = [
            SecretsConfig(
                name="INSTRUCTOR_TESTS_TOKEN",
                description="Token for accessing instructor test repository",
                validate_format=True,
                token_file=None,
                max_age_days=None
            ),
            SecretsConfig(
                name="API_KEY",
                description="API key for service",
                validate_format=False,
                token_file=None,
                max_age_days=None
            )
        ]
        mock_get_global_config.return_value = mock_config

        # Mock token retrieval
        mock_get_token_value.side_effect = [
            "github_pat_token1", "api_key_value"]

        # Mock repository discovery and deployment
        with patch.object(self.manager, 'find_student_repositories', return_value=["https://github.com/org/repo1"]):
            with patch.object(self.manager, 'add_secrets_to_repository', return_value={"INSTRUCTOR_TESTS_TOKEN": True, "API_KEY": True}):
                result = self.manager.add_secrets_from_global_config()

                # Verify success
                assert result is True

                # Verify token retrieval was called for each secret
                assert mock_get_token_value.call_count == 2

    @patch('classdock.config.global_config.get_global_config')
    def test_add_secrets_from_global_config_no_secrets(self, mock_get_global_config):
        """Test behavior when no secrets are configured."""
        # Mock global config with no secrets
        mock_config = MagicMock()
        mock_config.secrets_config = []
        mock_get_global_config.return_value = mock_config

        result = self.manager.add_secrets_from_global_config()

        # Should return False when no secrets are configured
        assert result is False

    @patch('classdock.config.global_config.get_global_config')
    def test_add_secrets_from_global_config_no_global_config(self, mock_get_global_config):
        """Test behavior when global config is not available."""
        mock_get_global_config.return_value = None

        result = self.manager.add_secrets_from_global_config()

        # Should return False when global config is not available
        assert result is False

    @patch('classdock.secrets.manager.SecretsManager.get_secret_token_value')
    @patch('classdock.config.global_config.get_global_config')
    def test_add_secrets_from_global_config_token_retrieval_failure(self, mock_get_global_config, mock_get_token_value):
        """Test handling of token retrieval failure."""
        # Mock global config
        mock_config = MagicMock()
        mock_config.secrets_config = [
            SecretsConfig(
                name="FAILING_TOKEN",
                description="Token that fails to retrieve",
                validate_format=True,
                token_file=None,
                max_age_days=None
            )
        ]
        mock_get_global_config.return_value = mock_config

        # Mock token retrieval failure
        mock_get_token_value.side_effect = Exception("Token retrieval failed")

        result = self.manager.add_secrets_from_global_config()

        # Should return False when token retrieval fails
        assert result is False

    def test_secrets_config_uses_centralized_token_method(self):
        """Test the uses_centralized_token() method of SecretsConfig."""
        # Test centralized token (token_file is None)
        centralized_config = SecretsConfig(
            name="CENTRALIZED_TOKEN",
            description="Uses centralized token management",
            validate_format=True,
            token_file=None,
            max_age_days=None
        )
        assert centralized_config.uses_centralized_token() is True

        # Test file-based token (token_file is not None)
        file_based_config = SecretsConfig(
            name="FILE_TOKEN",
            description="Uses file-based token",
            validate_format=True,
            token_file="token.txt",
            max_age_days=30
        )
        assert file_based_config.uses_centralized_token() is False

    @patch('classdock.utils.token_manager.GitHubTokenManager')
    def test_integration_new_vs_old_format_token_retrieval(self, mock_token_manager_class):
        """Test that new and old format configs use appropriate token retrieval methods."""
        # Setup mock
        mock_token_manager = MagicMock()
        mock_token_manager.get_github_token.return_value = "centralized_token"
        mock_token_manager_class.return_value = mock_token_manager

        # Test new format (centralized)
        new_config = SecretsConfig(
            name="NEW_TOKEN",
            description="New format token",
            validate_format=True,
            token_file=None,
            max_age_days=None
        )

        token_value = self.manager.get_secret_token_value(new_config)
        assert token_value == "centralized_token"
        mock_token_manager.get_github_token.assert_called_once()

        # Test old format (file-based) - with mock file
        with patch('builtins.open', mock_open(read_data="file_token")):
            with patch('pathlib.Path.exists', return_value=True):
                old_config = SecretsConfig(
                    name="OLD_TOKEN",
                    description="Old format token",
                    validate_format=True,
                    token_file="old_token.txt",
                    max_age_days=30
                )

                token_value = self.manager.get_secret_token_value(old_config)
                assert token_value == "file_token"
