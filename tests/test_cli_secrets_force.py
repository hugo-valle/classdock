"""
Tests for CLI secrets add command with --force option.

This module tests the CLI interface for the secrets add command,
specifically the --force / -f flag for forcing secret updates.
"""

import pytest
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner

from classdock.cli import app
from classdock.config.global_config import SecretsConfig, GlobalConfig


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def wide_runner():
    """Create a CLI test runner with wide terminal for full help text."""
    # Set env with multiple variables to ensure full help text rendering:
    # - COLUMNS: Set wide terminal width
    # - LINES: Set tall terminal height
    # - TERM: Set terminal type to ensure full output
    return CliRunner(env={"COLUMNS": "200", "LINES": "100", "TERM": "xterm-256color"})


@pytest.fixture
def mock_global_config():
    """Create a mock global configuration."""
    config = MagicMock(spec=GlobalConfig)
    config.secrets_config = [
        SecretsConfig(
            name="INSTRUCTOR_TESTS_TOKEN",
            description="Token for tests",
            validate_format=False,
            token_file=None,
            max_age_days=90
        )
    ]
    config.step_manage_secrets = True
    return config


class TestSecretsAddCLIForceFlag:
    """Test the --force flag for secrets add CLI command."""

    @patch('classdock.cli.get_global_config')
    @patch('classdock.services.secrets_service.get_global_config')
    @patch('classdock.secrets.github_secrets.GitHubSecretsManager')
    def test_secrets_add_without_force_flag(self, mock_manager_class, mock_get_config_service, mock_get_config_cli, runner, mock_global_config):
        """Test secrets add command without --force flag (default behavior)."""
        # Setup mocks
        mock_get_config_cli.return_value = mock_global_config
        mock_get_config_service.return_value = mock_global_config

        mock_manager = MagicMock()
        mock_manager.add_secrets_from_global_config.return_value = True
        mock_manager_class.return_value = mock_manager

        # Run command without --force
        result = runner.invoke(app, [
            'secrets', 'add',
            '--repos', 'https://github.com/org/repo1'
        ])

        # Verify
        assert result.exit_code == 0
        # Verify force_update=False was passed (default)
        mock_manager.add_secrets_from_global_config.assert_called_once()
        call_kwargs = mock_manager.add_secrets_from_global_config.call_args.kwargs
        assert call_kwargs.get('force_update', False) is False

    @patch('classdock.cli.get_global_config')
    @patch('classdock.services.secrets_service.get_global_config')
    @patch('classdock.secrets.github_secrets.GitHubSecretsManager')
    def test_secrets_add_with_force_flag(self, mock_manager_class, mock_get_config_service, mock_get_config_cli, runner, mock_global_config):
        """Test secrets add command with --force flag."""
        # Setup mocks
        mock_get_config_cli.return_value = mock_global_config
        mock_get_config_service.return_value = mock_global_config

        mock_manager = MagicMock()
        mock_manager.add_secrets_from_global_config.return_value = True
        mock_manager_class.return_value = mock_manager

        # Run command with --force
        result = runner.invoke(app, [
            'secrets', 'add',
            '--repos', 'https://github.com/org/repo1',
            '--force'
        ])

        # Verify
        assert result.exit_code == 0
        # Verify force_update=True was passed
        mock_manager.add_secrets_from_global_config.assert_called_once()
        call_kwargs = mock_manager.add_secrets_from_global_config.call_args.kwargs
        assert call_kwargs.get('force_update') is True

    @patch('classdock.cli.get_global_config')
    @patch('classdock.services.secrets_service.get_global_config')
    @patch('classdock.secrets.github_secrets.GitHubSecretsManager')
    def test_secrets_add_with_force_short_flag(self, mock_manager_class, mock_get_config_service, mock_get_config_cli, runner, mock_global_config):
        """Test secrets add command with -f short flag."""
        # Setup mocks
        mock_get_config_cli.return_value = mock_global_config
        mock_get_config_service.return_value = mock_global_config

        mock_manager = MagicMock()
        mock_manager.add_secrets_from_global_config.return_value = True
        mock_manager_class.return_value = mock_manager

        # Run command with -f
        result = runner.invoke(app, [
            'secrets', 'add',
            '--repos', 'https://github.com/org/repo1',
            '-f'
        ])

        # Verify
        assert result.exit_code == 0
        # Verify force_update=True was passed
        call_kwargs = mock_manager.add_secrets_from_global_config.call_args.kwargs
        assert call_kwargs.get('force_update') is True

    @patch('classdock.cli.get_global_config')
    @patch('classdock.services.secrets_service.get_global_config')
    @patch('classdock.secrets.github_secrets.GitHubSecretsManager')
    def test_secrets_add_force_with_multiple_repos(self, mock_manager_class, mock_get_config_service, mock_get_config_cli, runner, mock_global_config):
        """Test --force with multiple repositories."""
        # Setup mocks
        mock_get_config_cli.return_value = mock_global_config
        mock_get_config_service.return_value = mock_global_config

        mock_manager = MagicMock()
        mock_manager.add_secrets_from_global_config.return_value = True
        mock_manager_class.return_value = mock_manager

        # Run with multiple repos
        result = runner.invoke(app, [
            'secrets', 'add',
            '--repos', 'https://github.com/org/repo1,https://github.com/org/repo2,https://github.com/org/repo3',
            '--force'
        ])

        # Verify
        assert result.exit_code == 0
        call_kwargs = mock_manager.add_secrets_from_global_config.call_args.kwargs
        assert call_kwargs.get('force_update') is True
        # Verify multiple repos were passed
        assert len(call_kwargs.get('repo_urls', [])) == 3

    @patch('classdock.cli.get_global_config')
    @patch('classdock.services.secrets_service.get_global_config')
    @patch('classdock.secrets.github_secrets.GitHubSecretsManager')
    def test_secrets_add_force_without_repos(self, mock_manager_class, mock_get_config_service, mock_get_config_cli, runner, mock_global_config):
        """Test --force without specifying repos (auto-discovery)."""
        # Setup mocks
        mock_get_config_cli.return_value = mock_global_config
        mock_get_config_service.return_value = mock_global_config

        mock_manager = MagicMock()
        mock_manager.add_secrets_from_global_config.return_value = True
        mock_manager_class.return_value = mock_manager

        # Run without repos (will auto-discover)
        result = runner.invoke(app, [
            'secrets', 'add',
            '--force'
        ])

        # Verify
        assert result.exit_code == 0
        call_kwargs = mock_manager.add_secrets_from_global_config.call_args.kwargs
        assert call_kwargs.get('force_update') is True
        assert call_kwargs.get('repo_urls') is None  # Auto-discovery

    def test_secrets_add_help_shows_force_option(self, wide_runner):
        """Test that help text shows the --force option with wide terminal."""
        import re

        result = wide_runner.invoke(app, ['secrets', 'add', '--help'])

        assert result.exit_code == 0

        # Strip ANSI escape codes for reliable testing
        ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
        clean_output = ansi_escape.sub('', result.output)

        # Check for --force option in output (should be clean without log pollution)
        # Using wide terminal (COLUMNS=200) ensures full help text renders in CI
        assert '--force' in clean_output, f"Expected '--force' in output, but got: {clean_output[:500]}"
        assert '-f' in clean_output, f"Expected '-f' in output, but got: {clean_output[:500]}"
        # Check for force update description
        output_lower = clean_output.lower()
        assert 'force' in output_lower and 'update' in output_lower, \
            f"Expected force update description in output, but got: {clean_output[:500]}"

    @patch('classdock.cli.get_global_config')
    def test_secrets_add_force_with_no_config(self, mock_get_config, runner):
        """Test --force flag behavior when no config is available."""
        mock_get_config.return_value = None

        result = runner.invoke(app, [
            'secrets', 'add',
            '--force'
        ])

        # Should fail with error about missing config
        assert result.exit_code == 1
        assert 'not loaded' in result.output.lower(
        ) or 'configuration' in result.output.lower()

    @patch('classdock.cli.get_global_config')
    def test_secrets_add_force_with_no_secrets_config(self, mock_get_config, runner):
        """Test --force flag when no secrets are configured."""
        mock_config = MagicMock(spec=GlobalConfig)
        mock_config.secrets_config = None
        mock_get_config.return_value = mock_config

        result = runner.invoke(app, [
            'secrets', 'add',
            '--force'
        ])

        # Should fail with error about missing secrets config
        assert result.exit_code == 1
        assert 'secrets' in result.output.lower()


class TestSecretsAddCLIIntegration:
    """Integration tests for secrets add CLI with force flag."""

    @patch('classdock.cli.get_global_config')
    @patch('classdock.services.secrets_service.get_global_config')
    @patch('classdock.secrets.github_secrets.GitHubSecretsManager')
    def test_complete_workflow_with_force(self, mock_manager_class, mock_get_config_service, mock_get_config_cli, runner, mock_global_config):
        """Test complete workflow: add secrets, then force update."""
        # Setup
        mock_get_config_cli.return_value = mock_global_config
        mock_get_config_service.return_value = mock_global_config

        mock_manager = MagicMock()
        mock_manager.add_secrets_from_global_config.return_value = True
        mock_manager_class.return_value = mock_manager

        repo_url = 'https://github.com/org/test-repo'

        # First run: normal add (would skip if up-to-date)
        result1 = runner.invoke(app, [
            'secrets', 'add',
            '--repos', repo_url
        ])
        assert result1.exit_code == 0

        # Second run: force update (will update even if up-to-date)
        result2 = runner.invoke(app, [
            'secrets', 'add',
            '--repos', repo_url,
            '--force'
        ])
        assert result2.exit_code == 0

        # Verify both calls succeeded
        assert mock_manager.add_secrets_from_global_config.call_count == 2

        # Verify first call had force_update=False
        first_call_kwargs = mock_manager.add_secrets_from_global_config.call_args_list[
            0].kwargs
        assert first_call_kwargs.get('force_update', False) is False

        # Verify second call had force_update=True
        second_call_kwargs = mock_manager.add_secrets_from_global_config.call_args_list[
            1].kwargs
        assert second_call_kwargs.get('force_update') is True
