"""
Tests for SecretsService with force_update functionality.

This module tests the SecretsService class and its integration with
the force_update parameter for forcing secret updates.
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from classdock.services.secrets_service import SecretsService
from classdock.config.global_config import SecretsConfig


class TestSecretsService:
    """Test the SecretsService class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = SecretsService(dry_run=False, verbose=False)

    @patch('classdock.services.secrets_service.get_global_config')
    @patch('classdock.secrets.github_secrets.GitHubSecretsManager')
    def test_add_secrets_without_force_update(self, mock_manager_class, mock_get_config):
        """Test adding secrets without force_update (default behavior)."""
        # Mock global config
        mock_config = MagicMock()
        mock_config.secrets_config = [
            SecretsConfig(
                name="INSTRUCTOR_TESTS_TOKEN",
                description="Test token",
                validate_format=False,
                token_file=None
            )
        ]
        mock_get_config.return_value = mock_config

        # Mock secrets manager
        mock_manager = MagicMock()
        mock_manager.add_secrets_from_global_config.return_value = True
        mock_manager_class.return_value = mock_manager

        # Call without force_update
        success, message = self.service.add_secrets(
            repo_urls=["https://github.com/org/repo1"]
        )

        # Verify
        assert success is True
        assert "completed successfully" in message.lower()

        # Verify force_update=False was passed (default)
        mock_manager.add_secrets_from_global_config.assert_called_once_with(
            repo_urls=["https://github.com/org/repo1"],
            force_update=False
        )

    @patch('classdock.services.secrets_service.get_global_config')
    @patch('classdock.secrets.github_secrets.GitHubSecretsManager')
    def test_add_secrets_with_force_update_true(self, mock_manager_class, mock_get_config):
        """Test adding secrets with force_update=True."""
        # Mock global config
        mock_config = MagicMock()
        mock_config.secrets_config = [
            SecretsConfig(
                name="INSTRUCTOR_TESTS_TOKEN",
                description="Test token",
                validate_format=False,
                token_file=None
            )
        ]
        mock_get_config.return_value = mock_config

        # Mock secrets manager
        mock_manager = MagicMock()
        mock_manager.add_secrets_from_global_config.return_value = True
        mock_manager_class.return_value = mock_manager

        # Call with force_update=True
        success, message = self.service.add_secrets(
            repo_urls=["https://github.com/org/repo1"],
            force_update=True
        )

        # Verify
        assert success is True
        assert "completed successfully" in message.lower()

        # Verify force_update=True was passed
        mock_manager.add_secrets_from_global_config.assert_called_once_with(
            repo_urls=["https://github.com/org/repo1"],
            force_update=True
        )

    @patch('classdock.services.secrets_service.get_global_config')
    @patch('classdock.secrets.github_secrets.GitHubSecretsManager')
    def test_add_secrets_force_update_with_multiple_repos(self, mock_manager_class, mock_get_config):
        """Test force_update with multiple repositories."""
        # Mock global config
        mock_config = MagicMock()
        mock_config.secrets_config = [
            SecretsConfig(
                name="INSTRUCTOR_TESTS_TOKEN",
                description="Test token",
                validate_format=False,
                token_file=None
            )
        ]
        mock_get_config.return_value = mock_config

        # Mock secrets manager
        mock_manager = MagicMock()
        mock_manager.add_secrets_from_global_config.return_value = True
        mock_manager_class.return_value = mock_manager

        # Call with multiple repos and force_update
        repo_urls = [
            "https://github.com/org/repo1",
            "https://github.com/org/repo2",
            "https://github.com/org/repo3"
        ]
        success, message = self.service.add_secrets(
            repo_urls=repo_urls,
            force_update=True
        )

        # Verify
        assert success is True
        mock_manager.add_secrets_from_global_config.assert_called_once_with(
            repo_urls=repo_urls,
            force_update=True
        )

    @patch('classdock.services.secrets_service.get_global_config')
    def test_add_secrets_no_config(self, mock_get_config):
        """Test behavior when no global config is available."""
        mock_get_config.return_value = None

        success, message = self.service.add_secrets(force_update=True)

        assert success is False
        assert "not loaded" in message.lower()

    @patch('classdock.services.secrets_service.get_global_config')
    def test_add_secrets_no_secrets_config(self, mock_get_config):
        """Test behavior when no secrets are configured."""
        mock_config = MagicMock()
        mock_config.secrets_config = None
        mock_get_config.return_value = mock_config

        success, message = self.service.add_secrets(force_update=True)

        assert success is False
        assert "no secrets" in message.lower()

    @patch('classdock.services.secrets_service.get_global_config')
    @patch('classdock.secrets.github_secrets.GitHubSecretsManager')
    def test_add_secrets_manager_fails_with_force_update(self, mock_manager_class, mock_get_config):
        """Test handling when secrets manager fails with force_update."""
        # Mock global config
        mock_config = MagicMock()
        mock_config.secrets_config = [
            SecretsConfig(
                name="INSTRUCTOR_TESTS_TOKEN",
                description="Test token",
                validate_format=False,
                token_file=None
            )
        ]
        mock_get_config.return_value = mock_config

        # Mock secrets manager to fail
        mock_manager = MagicMock()
        mock_manager.add_secrets_from_global_config.return_value = False
        mock_manager_class.return_value = mock_manager

        success, message = self.service.add_secrets(force_update=True)

        assert success is False
        assert "failed" in message.lower()

    def test_add_secrets_dry_run_with_force_update(self):
        """Test dry run mode with force_update flag."""
        service = SecretsService(dry_run=True, verbose=False)

        # Dry run should short-circuit before force_update matters
        success, message = service.add_secrets(
            repo_urls=["https://github.com/org/repo1"],
            force_update=True
        )

        assert success is True
        assert "DRY RUN" in message


class TestSecretsServiceIntegration:
    """Integration tests for SecretsService with force_update."""

    @patch('classdock.services.secrets_service.get_global_config')
    @patch('classdock.secrets.github_secrets.GitHubSecretsManager')
    def test_force_update_workflow(self, mock_manager_class, mock_get_config):
        """Test complete workflow with force_update parameter."""
        # Setup
        mock_config = MagicMock()
        mock_config.secrets_config = [
            SecretsConfig(
                name="INSTRUCTOR_TESTS_TOKEN",
                description="Token for tests",
                validate_format=False,
                token_file=None
            ),
            SecretsConfig(
                name="API_KEY",
                description="API key",
                validate_format=False,
                token_file=None
            )
        ]
        mock_get_config.return_value = mock_config

        mock_manager = MagicMock()
        mock_manager.add_secrets_from_global_config.return_value = True
        mock_manager_class.return_value = mock_manager

        service = SecretsService(dry_run=False, verbose=True)

        # Execute - first without force
        success1, message1 = service.add_secrets(
            repo_urls=["https://github.com/org/repo1"],
            force_update=False
        )

        # Execute - then with force
        success2, message2 = service.add_secrets(
            repo_urls=["https://github.com/org/repo1"],
            force_update=True
        )

        # Verify both succeeded
        assert success1 is True
        assert success2 is True

        # Verify both calls were made with correct parameters
        calls = mock_manager.add_secrets_from_global_config.call_args_list
        assert len(calls) == 2
        assert calls[0].kwargs['force_update'] is False
        assert calls[1].kwargs['force_update'] is True

    @patch('classdock.services.secrets_service.get_global_config')
    @patch('classdock.secrets.github_secrets.GitHubSecretsManager')
    def test_force_update_parameter_propagation(self, mock_manager_class, mock_get_config):
        """Test that force_update parameter properly propagates through layers."""
        # Mock config
        mock_config = MagicMock()
        mock_config.secrets_config = [
            SecretsConfig(
                name="TEST_TOKEN",
                description="Test",
                validate_format=False,
                token_file=None
            )
        ]
        mock_get_config.return_value = mock_config

        # Mock manager
        mock_manager = MagicMock()
        mock_manager.add_secrets_from_global_config.return_value = True
        mock_manager_class.return_value = mock_manager

        service = SecretsService()

        # Test with explicit False
        service.add_secrets(force_update=False)
        call_args = mock_manager.add_secrets_from_global_config.call_args
        assert call_args.kwargs['force_update'] is False

        # Test with explicit True
        service.add_secrets(force_update=True)
        call_args = mock_manager.add_secrets_from_global_config.call_args
        assert call_args.kwargs['force_update'] is True
