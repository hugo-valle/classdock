"""
Tests for AssignmentService token pre-check functionality.

This test suite validates the token pre-check logic added to AssignmentService.setup()
that ensures a GitHub token is available before launching the setup wizard.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from pathlib import Path
import os

from classdock.services.assignment_service import AssignmentService


class TestAssignmentServiceTokenPreCheck:
    """Test token pre-check functionality in AssignmentService.setup()."""

    @patch('classdock.utils.token_manager.GitHubTokenManager')
    @patch('classdock.assignments.setup.AssignmentSetup')
    def test_setup_with_existing_config_token(self, mock_assignment_setup, mock_token_manager_class):
        """Test setup when centralized token config file exists."""
        # Mock token manager
        mock_token_manager = MagicMock()
        mock_config_file = MagicMock()
        mock_config_file.exists.return_value = True
        type(mock_token_manager).config_file = PropertyMock(
            return_value=mock_config_file)
        mock_token_manager._get_token_from_keychain.return_value = None
        mock_token_manager.get_github_token.return_value = "ghp_test_token"
        mock_token_manager_class.return_value = mock_token_manager

        # Mock setup wizard
        mock_wizard = Mock()
        mock_wizard.run_wizard.return_value = True
        mock_assignment_setup.return_value = mock_wizard

        # Test
        service = AssignmentService(dry_run=False)
        success, message = service.setup()

        # Verify
        assert success is True
        assert "successfully" in message.lower()
        mock_token_manager.get_github_token.assert_called_once()
        mock_wizard.run_wizard.assert_called_once()

    @patch('classdock.utils.token_manager.GitHubTokenManager')
    @patch('classdock.assignments.setup.AssignmentSetup')
    def test_setup_with_keychain_token(self, mock_assignment_setup, mock_token_manager_class):
        """Test setup when token exists in system keychain."""
        # Mock token manager
        mock_token_manager = MagicMock()
        mock_config_file = MagicMock()
        mock_config_file.exists.return_value = False
        type(mock_token_manager).config_file = PropertyMock(
            return_value=mock_config_file)
        mock_token_manager._get_token_from_keychain.return_value = "keychain_token"
        mock_token_manager.get_github_token.return_value = "keychain_token"
        mock_token_manager_class.return_value = mock_token_manager

        # Mock setup wizard
        mock_wizard = Mock()
        mock_wizard.run_wizard.return_value = True
        mock_assignment_setup.return_value = mock_wizard

        # Test
        service = AssignmentService(dry_run=False)
        success, message = service.setup()

        # Verify
        assert success is True
        assert "successfully" in message.lower()
        mock_token_manager.get_github_token.assert_called_once()
        mock_wizard.run_wizard.assert_called_once()

    @patch.dict(os.environ, {'GITHUB_TOKEN': 'env_token_value'}, clear=True)
    @patch('classdock.utils.token_manager.GitHubTokenManager')
    @patch('typer.confirm')
    @patch('classdock.assignments.setup.AssignmentSetup')
    def test_setup_with_env_token_import_accepted(self, mock_assignment_setup, mock_confirm, mock_token_manager_class):
        """Test setup when env token exists and user accepts import."""
        # Mock token manager
        mock_token_manager = MagicMock()
        mock_config_file = MagicMock()
        mock_config_file.exists.return_value = False
        type(mock_token_manager).config_file = PropertyMock(
            return_value=mock_config_file)
        mock_token_manager._get_token_from_keychain.return_value = None
        mock_token_manager.get_github_token.return_value = None  # First call fails

        # Mock token verification and storage
        mock_token_info = {
            'token_type': 'classic',
            'scopes': ['repo', 'workflow'],
            'username': 'testuser'
        }
        mock_token_manager._verify_and_get_token_info.return_value = mock_token_info
        mock_token_manager._store_token.return_value = None
        mock_token_manager_class.return_value = mock_token_manager

        # Mock user confirmation - user accepts import
        mock_confirm.return_value = True

        # Mock setup wizard
        mock_wizard = Mock()
        mock_wizard.run_wizard.return_value = True
        mock_assignment_setup.return_value = mock_wizard

        # Test
        service = AssignmentService(dry_run=False)
        success, message = service.setup()

        # Verify
        assert success is True
        assert "successfully" in message.lower()
        mock_token_manager._verify_and_get_token_info.assert_called_once_with(
            'env_token_value')
        mock_token_manager._store_token.assert_called_once()
        mock_wizard.run_wizard.assert_called_once()

    @patch.dict(os.environ, {'GITHUB_TOKEN': 'env_token_value'}, clear=True)
    @patch('classdock.utils.token_manager.GitHubTokenManager')
    @patch('typer.confirm')
    def test_setup_with_env_token_import_declined_no_interactive(self, mock_confirm, mock_token_manager_class):
        """Test setup when env token exists, import declined, no interactive setup."""
        # Mock token manager
        mock_token_manager = MagicMock()
        mock_config_file = MagicMock()
        mock_config_file.exists.return_value = False
        type(mock_token_manager).config_file = PropertyMock(
            return_value=mock_config_file)
        mock_token_manager._get_token_from_keychain.return_value = None
        mock_token_manager.get_github_token.return_value = None
        mock_token_manager_class.return_value = mock_token_manager

        # Mock user confirmation - decline both import and interactive creation
        mock_confirm.side_effect = [False, False]

        # Test
        service = AssignmentService(dry_run=False)
        success, message = service.setup()

        # Verify
        assert success is False
        assert "token" in message.lower()
        assert mock_confirm.call_count == 2

    @patch.dict(os.environ, {'GITHUB_TOKEN': 'env_token_value'}, clear=True)
    @patch('classdock.utils.token_manager.GitHubTokenManager')
    @patch('typer.confirm')
    @patch('classdock.assignments.setup.AssignmentSetup')
    def test_setup_with_env_token_import_declined_with_interactive(self, mock_assignment_setup, mock_confirm, mock_token_manager_class):
        """Test setup when env token exists, import declined, but interactive setup accepted."""
        # Mock token manager
        mock_token_manager = MagicMock()
        mock_config_file = MagicMock()
        mock_config_file.exists.return_value = False
        type(mock_token_manager).config_file = PropertyMock(
            return_value=mock_config_file)
        mock_token_manager._get_token_from_keychain.return_value = None
        mock_token_manager.get_github_token.return_value = None
        mock_token_manager.setup_new_token.return_value = "ghp_interactive_token"
        mock_token_manager_class.return_value = mock_token_manager

        # Mock user confirmation - decline import, accept interactive
        mock_confirm.side_effect = [False, True]

        # Mock setup wizard
        mock_wizard = Mock()
        mock_wizard.run_wizard.return_value = True
        mock_assignment_setup.return_value = mock_wizard

        # Test
        service = AssignmentService(dry_run=False)
        success, message = service.setup()

        # Verify
        assert success is True
        assert "successfully" in message.lower()
        mock_token_manager.setup_new_token.assert_called_once()
        mock_wizard.run_wizard.assert_called_once()

    @patch.dict(os.environ, {}, clear=True)
    @patch('classdock.utils.token_manager.GitHubTokenManager')
    @patch('typer.confirm')
    @patch('classdock.assignments.setup.AssignmentSetup')
    def test_setup_no_token_interactive_creation_accepted(self, mock_assignment_setup, mock_confirm, mock_token_manager_class):
        """Test setup when no token exists and user accepts interactive creation."""
        # Mock token manager
        mock_token_manager = MagicMock()
        mock_config_file = MagicMock()
        mock_config_file.exists.return_value = False
        type(mock_token_manager).config_file = PropertyMock(
            return_value=mock_config_file)
        mock_token_manager._get_token_from_keychain.return_value = None
        mock_token_manager.get_github_token.return_value = None
        mock_token_manager.setup_new_token.return_value = "ghp_new_token"
        mock_token_manager_class.return_value = mock_token_manager

        # Mock user confirmation - accept interactive creation
        mock_confirm.return_value = True

        # Mock setup wizard
        mock_wizard = Mock()
        mock_wizard.run_wizard.return_value = True
        mock_assignment_setup.return_value = mock_wizard

        # Test
        service = AssignmentService(dry_run=False)
        success, message = service.setup()

        # Verify
        assert success is True
        assert "successfully" in message.lower()
        mock_token_manager.setup_new_token.assert_called_once()
        mock_wizard.run_wizard.assert_called_once()

    @patch.dict(os.environ, {}, clear=True)
    @patch('classdock.utils.token_manager.GitHubTokenManager')
    @patch('typer.confirm')
    def test_setup_no_token_interactive_creation_declined(self, mock_confirm, mock_token_manager_class):
        """Test setup when no token exists and user declines interactive creation."""
        # Mock token manager
        mock_token_manager = MagicMock()
        mock_config_file = MagicMock()
        mock_config_file.exists.return_value = False
        type(mock_token_manager).config_file = PropertyMock(
            return_value=mock_config_file)
        mock_token_manager._get_token_from_keychain.return_value = None
        mock_token_manager.get_github_token.return_value = None
        mock_token_manager_class.return_value = mock_token_manager

        # Mock user confirmation - decline interactive creation
        mock_confirm.return_value = False

        # Test
        service = AssignmentService(dry_run=False)
        success, message = service.setup()

        # Verify
        assert success is False
        assert "token" in message.lower()
        assert "configured" in message.lower()

    @patch.dict(os.environ, {}, clear=True)
    @patch('classdock.utils.token_manager.GitHubTokenManager')
    def test_setup_dry_run_no_token(self, mock_token_manager_class):
        """Test setup in dry-run mode when no token exists."""
        # Mock token manager (not actually called in dry-run mode)
        mock_token_manager = MagicMock()
        mock_config_file = MagicMock()
        mock_config_file.exists.return_value = False
        type(mock_token_manager).config_file = PropertyMock(
            return_value=mock_config_file)
        mock_token_manager._get_token_from_keychain.return_value = None
        mock_token_manager.get_github_token.return_value = None
        mock_token_manager_class.return_value = mock_token_manager

        # Test
        service = AssignmentService(dry_run=True)
        success, message = service.setup()

        # Verify - In dry-run mode, we just report what would happen
        assert success is True  # Dry-run always succeeds, just reports what would happen
        assert "DRY RUN" in message
        assert "assignment setup wizard" in message

    @patch.dict(os.environ, {'GITHUB_TOKEN': 'env_token_value'}, clear=True)
    @patch('classdock.utils.token_manager.GitHubTokenManager')
    def test_setup_dry_run_with_env_token_only(self, mock_token_manager_class):
        """Test setup in dry-run mode when only env token exists."""
        # Mock token manager (not actually called in dry-run mode)
        mock_token_manager = MagicMock()
        mock_config_file = MagicMock()
        mock_config_file.exists.return_value = False
        type(mock_token_manager).config_file = PropertyMock(
            return_value=mock_config_file)
        mock_token_manager._get_token_from_keychain.return_value = None
        mock_token_manager.get_github_token.return_value = None
        mock_token_manager_class.return_value = mock_token_manager

        # Test
        service = AssignmentService(dry_run=True)
        success, message = service.setup()

        # Verify - In dry-run mode, we just report what would happen
        assert success is True  # Dry-run always succeeds, just reports what would happen
        assert "DRY RUN" in message
        assert "assignment setup wizard" in message

    @patch.dict(os.environ, {'GITHUB_TOKEN': 'invalid_token'}, clear=True)
    @patch('classdock.utils.token_manager.GitHubTokenManager')
    @patch('typer.confirm')
    @patch('classdock.assignments.setup.AssignmentSetup')
    def test_setup_env_token_verification_fails_interactive_fallback(self, mock_assignment_setup, mock_confirm, mock_token_manager_class):
        """Test setup when env token verification fails and fallback to interactive."""
        # Mock token manager
        mock_token_manager = MagicMock()
        mock_config_file = MagicMock()
        mock_config_file.exists.return_value = False
        type(mock_token_manager).config_file = PropertyMock(
            return_value=mock_config_file)
        mock_token_manager._get_token_from_keychain.return_value = None
        mock_token_manager.get_github_token.return_value = None
        mock_token_manager._verify_and_get_token_info.return_value = None  # Verification fails
        mock_token_manager.setup_new_token.return_value = "ghp_new_token"
        mock_token_manager_class.return_value = mock_token_manager

        # Mock user confirmation - accept import, then accept interactive after failure
        mock_confirm.side_effect = [True, True]

        # Mock setup wizard
        mock_wizard = Mock()
        mock_wizard.run_wizard.return_value = True
        mock_assignment_setup.return_value = mock_wizard

        # Test
        service = AssignmentService(dry_run=False)
        success, message = service.setup()

        # Verify
        assert success is True
        assert "successfully" in message.lower()
        mock_token_manager._verify_and_get_token_info.assert_called_once()
        mock_token_manager.setup_new_token.assert_called_once()
        mock_wizard.run_wizard.assert_called_once()

    @patch.dict(os.environ, {'GITHUB_TOKEN': 'invalid_token'}, clear=True)
    @patch('classdock.utils.token_manager.GitHubTokenManager')
    @patch('typer.confirm')
    def test_setup_env_token_verification_fails_interactive_declined(self, mock_confirm, mock_token_manager_class):
        """Test setup when env token verification fails and interactive declined."""
        # Mock token manager
        mock_token_manager = MagicMock()
        mock_config_file = MagicMock()
        mock_config_file.exists.return_value = False
        type(mock_token_manager).config_file = PropertyMock(
            return_value=mock_config_file)
        mock_token_manager._get_token_from_keychain.return_value = None
        mock_token_manager.get_github_token.return_value = None
        mock_token_manager._verify_and_get_token_info.return_value = None  # Verification fails
        mock_token_manager_class.return_value = mock_token_manager

        # Mock user confirmation - accept import, then decline interactive after failure
        mock_confirm.side_effect = [True, False]

        # Test
        service = AssignmentService(dry_run=False)
        success, message = service.setup()

        # Verify
        assert success is False
        assert "token" in message.lower()
        mock_token_manager._verify_and_get_token_info.assert_called_once()

    @patch.dict(os.environ, {'GITHUB_TOKEN': 'env_token_value'}, clear=True)
    @patch('classdock.utils.token_manager.GitHubTokenManager')
    @patch('typer.confirm')
    def test_setup_env_token_import_storage_error(self, mock_confirm, mock_token_manager_class):
        """Test setup when env token storage fails."""
        # Mock token manager
        mock_token_manager = MagicMock()
        mock_config_file = MagicMock()
        mock_config_file.exists.return_value = False
        type(mock_token_manager).config_file = PropertyMock(
            return_value=mock_config_file)
        mock_token_manager._get_token_from_keychain.return_value = None
        mock_token_manager.get_github_token.return_value = None

        # Mock token verification success but storage failure
        mock_token_info = {'token_type': 'classic',
                           'scopes': ['repo'], 'username': 'testuser'}
        mock_token_manager._verify_and_get_token_info.return_value = mock_token_info
        mock_token_manager._store_token.side_effect = Exception(
            "Storage failed")
        mock_token_manager_class.return_value = mock_token_manager

        # Mock user confirmation - accept import
        mock_confirm.return_value = True

        # Test
        service = AssignmentService(dry_run=False)
        success, message = service.setup()

        # Verify
        assert success is False
        assert "Failed to import" in message
        assert "Storage failed" in message


class TestAssignmentServiceTokenPreCheckWithURL:
    """Test token pre-check functionality with URL parameter."""

    @patch('classdock.utils.token_manager.GitHubTokenManager')
    @patch('classdock.assignments.setup.AssignmentSetup')
    def test_setup_with_url_and_existing_token(self, mock_assignment_setup, mock_token_manager_class):
        """Test setup with URL when token exists."""
        # Mock token manager
        mock_token_manager = MagicMock()
        mock_config_file = MagicMock()
        mock_config_file.exists.return_value = True
        type(mock_token_manager).config_file = PropertyMock(
            return_value=mock_config_file)
        mock_token_manager._get_token_from_keychain.return_value = None
        mock_token_manager.get_github_token.return_value = "ghp_test_token"
        mock_token_manager_class.return_value = mock_token_manager

        # Mock setup wizard
        mock_wizard = Mock()
        mock_wizard.run_wizard_with_url.return_value = True
        mock_assignment_setup.return_value = mock_wizard

        # Test
        service = AssignmentService(dry_run=False)
        url = "https://classroom.github.com/classrooms/123/assignments/test"
        success, message = service.setup(url=url)

        # Verify
        assert success is True
        assert "successfully" in message.lower()
        mock_wizard.run_wizard_with_url.assert_called_once_with(url)

    @patch.dict(os.environ, {}, clear=True)
    @patch('classdock.utils.token_manager.GitHubTokenManager')
    @patch('typer.confirm')
    def test_setup_with_url_no_token_declined(self, mock_confirm, mock_token_manager_class):
        """Test setup with URL when no token and user declines creation."""
        # Mock token manager
        mock_token_manager = MagicMock()
        mock_config_file = MagicMock()
        mock_config_file.exists.return_value = False
        type(mock_token_manager).config_file = PropertyMock(
            return_value=mock_config_file)
        mock_token_manager._get_token_from_keychain.return_value = None
        mock_token_manager.get_github_token.return_value = None
        mock_token_manager_class.return_value = mock_token_manager

        # Mock user confirmation - decline
        mock_confirm.return_value = False

        # Test
        service = AssignmentService(dry_run=False)
        url = "https://classroom.github.com/classrooms/123/assignments/test"
        success, message = service.setup(url=url)

        # Verify - token check happens before URL is processed
        assert success is False
        assert "token" in message.lower()
