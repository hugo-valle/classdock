"""
Tests for config CLI commands (set-token, check-token).

These tests verify the functionality of the config subcommand group
including token management operations.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typer.testing import CliRunner

from classdock.cli import app

VALID_TOKEN_DATA = {
    'scopes': ['repo', 'read:org'],
    'expires_at': '2027-01-01T00:00:00+00:00',
    'token_type': 'fine-grained',
}

VALID_EXPIRATION = {
    'is_expired': False,
    'is_valid': True,
    'expires_at': '2027-01-01T00:00:00+00:00',
    'days_remaining': 74,
    'token_type': 'fine-grained',
}

VALID_SCOPES = {
    'valid': True,
    'scopes': ['repo', 'read:org'],
    'has_repo': True,
    'has_read_org': True,
}


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_token_manager():
    """Mock GitHubTokenManager."""
    with patch('classdock.utils.token_manager.GitHubTokenManager') as mock:
        manager = Mock()
        manager._verify_and_get_token_info.return_value = VALID_TOKEN_DATA
        mock.return_value = manager
        yield manager


class TestConfigSetToken:
    """Tests for 'config set-token' command."""

    def test_set_token_help(self, runner):
        """Test that set-token command shows help."""
        result = runner.invoke(app, ["config", "set-token", "--help"])
        assert result.exit_code == 0
        assert "Update the GitHub Personal Access Token" in result.stdout
        assert "Required token scopes:" in result.stdout
        assert "repo" in result.stdout
        assert "read:org" in result.stdout

    def test_set_token_with_valid_token(self, runner, mock_token_manager):
        """Test setting a valid token with all required scopes."""
        mock_token_manager.save_token.return_value = True

        with patch('classdock.commands.config._check_token_expiration', return_value=VALID_EXPIRATION), \
             patch('classdock.commands.config._validate_token_scopes', return_value=VALID_SCOPES):
            result = runner.invoke(app, [
                "config", "set-token", "ghp_validtoken123456789012345678901234567890"
            ])

        assert result.exit_code == 0
        assert "✅ Token updated successfully!" in result.stdout
        mock_token_manager.save_token.assert_called_once()

    def test_set_token_with_expired_token(self, runner, mock_token_manager):
        """Test setting an expired token fails."""
        expired_info = {
            'is_expired': True,
            'is_valid': False,
            'expires_at': '2025-10-01T00:00:00+00:00',
            'days_remaining': -18,
            'token_type': 'fine-grained',
        }

        with patch('classdock.commands.config._check_token_expiration', return_value=expired_info):
            result = runner.invoke(app, [
                "config", "set-token", "ghp_expiredtoken123456789012345678901234567"
            ])

        assert result.exit_code == 1
        assert "❌ Token has already expired!" in result.stdout
        mock_token_manager.save_token.assert_not_called()

    def test_set_token_with_invalid_token(self, runner, mock_token_manager):
        """Test setting an invalid token fails."""
        mock_token_manager._verify_and_get_token_info.return_value = None

        result = runner.invoke(app, [
            "config", "set-token", "ghp_invalidtoken123456789012345678901234567"
        ])

        assert result.exit_code == 1
        assert "❌ Token validation failed" in result.stdout
        mock_token_manager.save_token.assert_not_called()

    def test_set_token_missing_repo_scope(self, runner, mock_token_manager):
        """Test setting token without repo scope shows warning and prompts user."""
        no_repo_scopes = {
            'valid': True,
            'scopes': ['public_repo'],
            'has_repo': False,
            'has_read_org': False,
        }

        with patch('classdock.commands.config._check_token_expiration', return_value={
            **VALID_EXPIRATION, 'expires_at': None, 'days_remaining': None, 'token_type': 'classic'
        }), \
             patch('classdock.commands.config._validate_token_scopes', return_value=no_repo_scopes):
            result = runner.invoke(app, [
                "config", "set-token", "ghp_limitedscopes123456789012345678901234"
            ], input="n\n")

        assert result.exit_code == 1
        assert "⚠️ Token lacks 'repo' scope" in result.stdout
        assert "Token update cancelled" in result.stdout
        mock_token_manager.save_token.assert_not_called()

    def test_set_token_missing_scopes_with_confirmation(self, runner, mock_token_manager):
        """Test setting token with missing scopes when user confirms."""
        no_repo_scopes = {
            'valid': True,
            'scopes': ['public_repo'],
            'has_repo': False,
            'has_read_org': False,
        }
        mock_token_manager.save_token.return_value = True

        with patch('classdock.commands.config._check_token_expiration', return_value={
            **VALID_EXPIRATION, 'expires_at': None, 'days_remaining': None, 'token_type': 'classic'
        }), \
             patch('classdock.commands.config._validate_token_scopes', return_value=no_repo_scopes):
            result = runner.invoke(app, [
                "config", "set-token", "ghp_limitedscopes123456789012345678901234"
            ], input="y\n")

        assert result.exit_code == 0
        assert "✅ Token updated successfully!" in result.stdout
        mock_token_manager.save_token.assert_called_once()

    def test_set_token_with_force_flag(self, runner, mock_token_manager):
        """Test setting token with --force flag bypasses validation."""
        mock_token_manager.save_token.return_value = True

        result = runner.invoke(app, [
            "config", "set-token", "ghp_anytoken1234567890123456789012345678901",
            "--force"
        ])

        assert result.exit_code == 0
        assert "✅ Token updated successfully!" in result.stdout
        mock_token_manager.save_token.assert_called_once()
        mock_token_manager._verify_and_get_token_info.assert_not_called()

    def test_set_token_invalid_format_with_confirmation(self, runner, mock_token_manager):
        """Test setting token with invalid format shows warning."""
        mock_token_manager.save_token.return_value = True

        with patch('classdock.commands.config._check_token_expiration', return_value={
            **VALID_EXPIRATION, 'expires_at': None, 'days_remaining': None, 'token_type': 'classic'
        }), \
             patch('classdock.commands.config._validate_token_scopes', return_value=VALID_SCOPES):
            result = runner.invoke(app, [
                "config", "set-token", "invalid_format_token123456789012345678"
            ], input="y\n")

        assert result.exit_code == 0
        assert "⚠️ Token doesn't start with 'ghp_' or 'github_pat_'" in result.stdout
        mock_token_manager.save_token.assert_called_once()

    def test_set_token_expiring_soon_warning(self, runner, mock_token_manager):
        """Test setting token that expires soon shows warning."""
        expiring_soon = {
            'is_expired': False,
            'is_valid': True,
            'expires_at': '2026-06-29T00:00:00+00:00',
            'days_remaining': 6,
            'token_type': 'fine-grained',
        }
        mock_token_manager.save_token.return_value = True

        with patch('classdock.commands.config._check_token_expiration', return_value=expiring_soon), \
             patch('classdock.commands.config._validate_token_scopes', return_value=VALID_SCOPES):
            result = runner.invoke(app, [
                "config", "set-token", "ghp_expiringsoon123456789012345678901234"
            ])

        assert result.exit_code == 0
        assert "⚠️ Token expires in 6 days!" in result.stdout
        assert "✅ Token updated successfully!" in result.stdout
        mock_token_manager.save_token.assert_called_once()

    def test_set_token_with_expires_at_parameter(self, runner, mock_token_manager):
        """Test setting token with explicit expiration date."""
        classic_expiration = {
            'is_expired': False,
            'is_valid': True,
            'expires_at': None,
            'days_remaining': None,
            'token_type': 'classic',
        }
        mock_token_manager.save_token.return_value = True

        with patch('classdock.commands.config._check_token_expiration', return_value=classic_expiration), \
             patch('classdock.commands.config._validate_token_scopes', return_value=VALID_SCOPES):
            result = runner.invoke(app, [
                "config", "set-token", "ghp_classictoken123456789012345678901234",
                "--expires-at", "2026-10-19T00:00:00+00:00"
            ])

        assert result.exit_code == 0
        assert "✓ Expiration date set to: 2026-10-19T00:00:00+00:00" in result.stdout
        assert "✅ Token updated successfully!" in result.stdout
        call_args = mock_token_manager.save_token.call_args
        assert call_args[1]['expires_at'] == "2026-10-19T00:00:00+00:00"

    def test_set_token_with_invalid_expires_at_format(self, runner, mock_token_manager):
        """Test setting token with invalid expiration date format."""
        classic_expiration = {
            'is_expired': False,
            'is_valid': True,
            'expires_at': None,
            'days_remaining': None,
            'token_type': 'classic',
        }

        with patch('classdock.commands.config._check_token_expiration', return_value=classic_expiration), \
             patch('classdock.commands.config._validate_token_scopes', return_value=VALID_SCOPES):
            result = runner.invoke(app, [
                "config", "set-token", "ghp_classictoken123456789012345678901234",
                "--expires-at", "invalid-date-format"
            ])

        assert result.exit_code == 1
        assert "❌ Invalid date format" in result.stdout
        assert "Expected ISO format: YYYY-MM-DDTHH:MM:SS+00:00" in result.stdout
        mock_token_manager.save_token.assert_not_called()


class TestConfigCheckToken:
    """Tests for 'config check-token' command."""

    def test_check_token_help(self, runner):
        """Test that check-token command shows help."""
        result = runner.invoke(app, ["config", "check-token", "--help"])
        assert result.exit_code == 0
        assert "Check the current GitHub token status" in result.stdout
        assert "expiration" in result.stdout.lower()
        assert "scopes" in result.stdout.lower()

    def test_check_token_no_token_found(self, runner, mock_token_manager):
        """Test check-token when no token is configured."""
        mock_token_manager.get_github_token.return_value = None

        result = runner.invoke(app, ["config", "check-token"])

        assert result.exit_code == 1
        assert "❌ No GitHub token found!" in result.stdout
        assert "classdock config set-token" in result.stdout

    def test_check_token_valid_with_expiration(self, runner, mock_token_manager):
        """Test check-token with valid token that has expiration."""
        mock_token_manager.get_github_token.return_value = "ghp_valid123"
        expiration = {
            'is_expired': False,
            'is_valid': True,
            'expires_at': '2027-01-01T00:00:00+00:00',
            'days_remaining': 74,
            'token_type': 'fine-grained',
        }
        scopes = {
            'valid': True,
            'scopes': ['repo', 'read:org', 'workflow'],
            'has_repo': True,
            'has_read_org': True,
        }

        with patch('classdock.commands.config._check_token_expiration', return_value=expiration), \
             patch('classdock.commands.config._validate_token_scopes', return_value=scopes):
            result = runner.invoke(app, ["config", "check-token"])

        assert result.exit_code == 0
        assert "📅 Token Expiration:" in result.stdout
        assert "Valid for 74 more days" in result.stdout
        assert "🔐 Token Scopes:" in result.stdout
        assert "repo, read:org, workflow" in result.stdout
        assert "✅ Token is properly configured" in result.stdout

    def test_check_token_expired(self, runner, mock_token_manager):
        """Test check-token with expired token."""
        mock_token_manager.get_github_token.return_value = "ghp_expired123"
        expired = {
            'is_expired': True,
            'is_valid': False,
            'expires_at': '2025-10-17T00:00:00+00:00',
            'days_remaining': -2,
            'token_type': 'expired',
        }

        with patch('classdock.commands.config._check_token_expiration', return_value=expired):
            result = runner.invoke(app, ["config", "check-token"])

        assert result.exit_code == 1
        assert "❌ Token has EXPIRED!" in result.stdout
        assert "October 17, 2025" in result.stdout
        assert "(2 days ago)" in result.stdout
        assert "classdock config set-token" in result.stdout

    def test_check_token_expiring_soon(self, runner, mock_token_manager):
        """Test check-token with token expiring soon."""
        mock_token_manager.get_github_token.return_value = "ghp_expiring123"
        expiring = {
            'is_expired': False,
            'is_valid': True,
            'expires_at': '2026-06-29T00:00:00+00:00',
            'days_remaining': 6,
            'token_type': 'fine-grained',
        }
        scopes = {'valid': True, 'scopes': ['repo', 'read:org'], 'has_repo': True, 'has_read_org': True}

        with patch('classdock.commands.config._check_token_expiration', return_value=expiring), \
             patch('classdock.commands.config._validate_token_scopes', return_value=scopes):
            result = runner.invoke(app, ["config", "check-token"])

        assert result.exit_code == 0
        assert "⚠️ Expires in 6 days" in result.stdout
        assert "Consider generating a new token soon!" in result.stdout

    def test_check_token_classic_no_expiration(self, runner, mock_token_manager):
        """Test check-token with classic token (no expiration)."""
        mock_token_manager.get_github_token.return_value = "ghp_classic123"
        mock_token_manager.config_file.exists.return_value = False
        classic = {
            'is_expired': False,
            'is_valid': True,
            'expires_at': None,
            'days_remaining': None,
            'token_type': 'classic',
        }
        scopes = {'valid': True, 'scopes': ['repo', 'read:org'], 'has_repo': True, 'has_read_org': True}

        with patch('classdock.commands.config._check_token_expiration', return_value=classic), \
             patch('classdock.commands.config._validate_token_scopes', return_value=scopes):
            result = runner.invoke(app, ["config", "check-token"])

        assert result.exit_code == 0
        assert "✓ Token is valid" in result.stdout
        assert "classic (no expiration set)" in result.stdout
        assert "⚠️ Consider setting an expiration date for tracking" in result.stdout

    def test_check_token_missing_repo_scope(self, runner, mock_token_manager):
        """Test check-token with token missing repo scope."""
        mock_token_manager.get_github_token.return_value = "ghp_limited123"
        classic = {
            'is_expired': False,
            'is_valid': True,
            'expires_at': None,
            'days_remaining': None,
            'token_type': 'classic',
        }
        no_repo = {'valid': True, 'scopes': ['public_repo', 'read:org'], 'has_repo': False, 'has_read_org': True}

        with patch('classdock.commands.config._check_token_expiration', return_value=classic), \
             patch('classdock.commands.config._validate_token_scopes', return_value=no_repo):
            result = runner.invoke(app, ["config", "check-token"])

        assert result.exit_code == 0
        assert "❌ repo - MISSING!" in result.stdout
        assert "⚠️ Token is missing some required scopes" in result.stdout

    def test_check_token_missing_read_org_scope(self, runner, mock_token_manager):
        """Test check-token with token missing read:org scope."""
        mock_token_manager.get_github_token.return_value = "ghp_limited123"
        classic = {
            'is_expired': False,
            'is_valid': True,
            'expires_at': None,
            'days_remaining': None,
            'token_type': 'classic',
        }
        no_org = {'valid': True, 'scopes': ['repo'], 'has_repo': True, 'has_read_org': False}

        with patch('classdock.commands.config._check_token_expiration', return_value=classic), \
             patch('classdock.commands.config._validate_token_scopes', return_value=no_org):
            result = runner.invoke(app, ["config", "check-token"])

        assert result.exit_code == 0
        assert "❌ read:org - MISSING!" in result.stdout
        assert "⚠️ Token is missing some required scopes" in result.stdout

    def test_check_token_invalid(self, runner, mock_token_manager):
        """Test check-token when token cannot be verified."""
        mock_token_manager.get_github_token.return_value = "ghp_invalid123"
        mock_token_manager._verify_and_get_token_info.return_value = None

        result = runner.invoke(app, ["config", "check-token"])

        assert result.exit_code == 1
        assert "❌ Token validation failed" in result.stdout


class TestConfigAppIntegration:
    """Integration tests for config app commands."""

    def test_config_help_shows_both_commands(self, runner):
        """Test that config help shows both set-token and check-token."""
        result = runner.invoke(app, ["config", "--help"])

        assert result.exit_code == 0
        assert "Configuration and token management commands" in result.stdout
        assert "set-token" in result.stdout
        assert "check-token" in result.stdout

    def test_config_no_command_shows_help(self, runner):
        """Test that config without subcommand shows help."""
        result = runner.invoke(app, ["config"])

        # Typer shows error when no subcommand provided
        assert result.exit_code == 2
