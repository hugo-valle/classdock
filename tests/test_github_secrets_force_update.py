"""
Tests for GitHubSecretsManager force_update functionality.

This module tests the force_update parameter in GitHubSecretsManager
to ensure secrets are properly updated even when they already exist.
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime, timezone
from pathlib import Path

from classdock.secrets.github_secrets import GitHubSecretsManager
from classdock.config.global_config import SecretsConfig, GlobalConfig


class TestGitHubSecretsManagerForceUpdate:
    """Test force_update functionality in GitHubSecretsManager."""

    @pytest.fixture
    def mock_global_config(self):
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

    @pytest.fixture
    def secrets_manager(self, mock_global_config):
        """Create a GitHubSecretsManager instance with mocked config."""
        with patch('classdock.secrets.github_secrets.get_global_config', return_value=mock_global_config):
            with patch('classdock.secrets.github_secrets.GitHubSecretsManager._get_github_token', return_value='ghp_test_token_1234567890'):
                manager = GitHubSecretsManager(dry_run=False)
                return manager

    def test_add_secret_without_force_update_skips_recent_secret(self, secrets_manager):
        """Test that without force_update, recent secrets are skipped."""
        # Mock existing secret that was just updated
        existing_secret = {
            'name': 'INSTRUCTOR_TESTS_TOKEN',
            'updated_at': datetime.now(timezone.utc).isoformat()
        }

        with patch.object(secrets_manager, 'check_repo_access', return_value=True):
            with patch.object(secrets_manager, 'get_secret_info', return_value=existing_secret):
                with patch.object(secrets_manager, 'secret_needs_update', return_value=False):
                    # Should skip update
                    result = secrets_manager.add_secret_to_repo(
                        owner='test-org',
                        repo='test-repo',
                        secret_name='INSTRUCTOR_TESTS_TOKEN',
                        secret_value='test-token',
                        max_age_days=90,
                        force_update=False
                    )

                    assert result is True
                    # Verify we didn't call subprocess (no actual update)
                    with patch('subprocess.run') as mock_subprocess:
                        mock_subprocess.assert_not_called()

    def test_add_secret_with_force_update_updates_recent_secret(self, secrets_manager):
        """Test that with force_update=True, even recent secrets are updated."""
        # Mock existing secret that was just updated
        existing_secret = {
            'name': 'INSTRUCTOR_TESTS_TOKEN',
            'updated_at': datetime.now(timezone.utc).isoformat()
        }

        with patch.object(secrets_manager, 'check_repo_access', return_value=True):
            with patch.object(secrets_manager, 'get_secret_info', return_value=existing_secret):
                with patch.object(secrets_manager, 'secret_needs_update', return_value=False):
                    with patch('subprocess.run') as mock_subprocess:
                        mock_subprocess.return_value = MagicMock(returncode=0)

                        # Should force update despite being recent
                        result = secrets_manager.add_secret_to_repo(
                            owner='test-org',
                            repo='test-repo',
                            secret_name='INSTRUCTOR_TESTS_TOKEN',
                            secret_value='test-token',
                            max_age_days=90,
                            force_update=True
                        )

                        assert result is True
                        # Verify subprocess was called to update the secret
                        mock_subprocess.assert_called_once()
                        cmd = mock_subprocess.call_args[0][0]
                        assert 'gh' in cmd
                        assert 'secret' in cmd
                        assert 'set' in cmd
                        assert 'INSTRUCTOR_TESTS_TOKEN' in cmd

    def test_process_batch_repos_with_force_update(self, secrets_manager):
        """Test batch processing with force_update parameter."""
        repo_urls = [
            'https://github.com/org/repo1',
            'https://github.com/org/repo2',
            'https://github.com/org/repo3'
        ]

        with patch.object(secrets_manager, 'process_single_repo', return_value=True) as mock_process:
            results = secrets_manager.process_batch_repos(
                repo_urls=repo_urls,
                secret_name='INSTRUCTOR_TESTS_TOKEN',
                secret_value='test-token',
                max_age_days=90,
                force_update=True,
                skip_validation=True
            )

            assert results['success'] == 3
            assert results['failed'] == 0

            # Verify force_update was passed to each call
            assert mock_process.call_count == 3
            for call in mock_process.call_args_list:
                # Arguments are passed positionally: repo_url, secret_name, secret_value, max_age_days, force_update, skip_validation
                args = call[0]
                assert len(args) == 6
                # force_update is 5th positional argument    def test_add_secrets_from_global_config_with_force_update(self, secrets_manager, mock_global_config):
                assert args[4] is True
        """Test add_secrets_from_global_config with force_update parameter."""
        repo_urls = ['https://github.com/org/repo1']

        with patch.object(secrets_manager, '_discover_repositories', return_value=repo_urls):
            with patch.object(secrets_manager, 'process_batch_repos', return_value={'success': 1, 'failed': 0}) as mock_batch:
                result = secrets_manager.add_secrets_from_global_config(
                    repo_urls=None,
                    force_update=True
                )

                assert result is True
                # Verify force_update was passed
                mock_batch.assert_called_once()
                assert mock_batch.call_args[1]['force_update'] is True

    def test_force_update_false_by_default(self, secrets_manager, mock_global_config):
        """Test that force_update defaults to False."""
        repo_urls = ['https://github.com/org/repo1']

        with patch.object(secrets_manager, 'process_batch_repos', return_value={'success': 1, 'failed': 0}) as mock_batch:
            # Call without specifying force_update
            result = secrets_manager.add_secrets_from_global_config(
                repo_urls=repo_urls
            )

            # Verify force_update defaults to False
            mock_batch.assert_called_once()
            assert mock_batch.call_args[1]['force_update'] is False

    def test_force_update_with_validation_skip(self, secrets_manager):
        """Test force_update works correctly with validation skipping."""
        existing_secret = {
            'name': 'INSTRUCTOR_TESTS_TOKEN',
            'updated_at': datetime.now(timezone.utc).isoformat()
        }

        with patch.object(secrets_manager, 'check_repo_access', return_value=True):
            with patch.object(secrets_manager, 'get_secret_info', return_value=existing_secret):
                with patch.object(secrets_manager, 'secret_needs_update', return_value=False):
                    with patch('subprocess.run') as mock_subprocess:
                        mock_subprocess.return_value = MagicMock(returncode=0)

                        # Test with force_update and validation skip
                        result = secrets_manager.process_single_repo(
                            repo_url='https://github.com/org/repo',
                            secret_name='INSTRUCTOR_TESTS_TOKEN',
                            secret_value='test-token',
                            max_age_days=90,
                            force_update=True,
                            skip_validation=True
                        )

                        assert result is True
                        mock_subprocess.assert_called_once()


class TestForceUpdateEdgeCases:
    """Test edge cases for force_update functionality."""

    @pytest.fixture
    def mock_global_config(self):
        """Create a mock global configuration."""
        config = MagicMock(spec=GlobalConfig)
        config.secrets_config = [
            SecretsConfig(
                name="TEST_TOKEN",
                description="Test",
                validate_format=False,
                token_file=None,
                max_age_days=90
            )
        ]
        config.step_manage_secrets = True
        return config

    @pytest.fixture
    def secrets_manager(self, mock_global_config):
        """Create a GitHubSecretsManager instance."""
        with patch('classdock.secrets.github_secrets.get_global_config', return_value=mock_global_config):
            with patch('classdock.secrets.github_secrets.GitHubSecretsManager._get_github_token', return_value='ghp_test_token'):
                return GitHubSecretsManager(dry_run=False)

    def test_force_update_with_no_existing_secret(self, secrets_manager):
        """Test force_update when secret doesn't exist (should create it)."""
        with patch.object(secrets_manager, 'check_repo_access', return_value=True):
            with patch.object(secrets_manager, 'get_secret_info', return_value=None):
                with patch('subprocess.run') as mock_subprocess:
                    mock_subprocess.return_value = MagicMock(returncode=0)

                    result = secrets_manager.add_secret_to_repo(
                        owner='org',
                        repo='repo',
                        secret_name='TEST_TOKEN',
                        secret_value='token',
                        force_update=True
                    )

                    assert result is True
                    mock_subprocess.assert_called_once()

    def test_force_update_with_empty_repo_list(self, secrets_manager):
        """Test force_update with empty repository list."""
        results = secrets_manager.process_batch_repos(
            repo_urls=[],
            secret_name='TEST_TOKEN',
            secret_value='token',
            force_update=True
        )

        assert results['total'] == 0
        assert results['success'] == 0
        assert results['failed'] == 0

    def test_force_update_preserves_other_parameters(self, secrets_manager):
        """Test that force_update doesn't interfere with other parameters."""
        with patch.object(secrets_manager, 'process_single_repo', return_value=True) as mock_process:
            secrets_manager.process_batch_repos(
                repo_urls=['https://github.com/org/repo'],
                secret_name='CUSTOM_SECRET',
                secret_value='custom-value',
                max_age_days=30,
                force_update=True,
                skip_validation=True
            )

            # Verify all parameters were passed correctly
            # Arguments are passed positionally: repo_url, secret_name, secret_value, max_age_days, force_update, skip_validation
            call_args = mock_process.call_args[0]
            assert call_args[1] == 'CUSTOM_SECRET'  # secret_name
            assert call_args[2] == 'custom-value'    # secret_value
            assert call_args[3] == 30                # max_age_days
            assert call_args[4] is True              # force_update
            assert call_args[5] is True              # skip_validation

    def test_force_update_in_dry_run_mode(self, mock_global_config):
        """Test that force_update works correctly in dry run mode."""
        with patch('classdock.secrets.github_secrets.get_global_config', return_value=mock_global_config):
            with patch('classdock.secrets.github_secrets.GitHubSecretsManager._get_github_token', return_value='ghp_test'):
                manager = GitHubSecretsManager(dry_run=True)

                existing_secret = {
                    'name': 'TEST_TOKEN',
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }

                with patch.object(manager, 'check_repo_access', return_value=True):
                    with patch.object(manager, 'get_secret_info', return_value=existing_secret):
                        with patch.object(manager, 'secret_needs_update', return_value=False):
                            # Even with force_update in dry run, should indicate success
                            result = manager.add_secret_to_repo(
                                owner='org',
                                repo='repo',
                                secret_name='TEST_TOKEN',
                                secret_value='token',
                                force_update=True
                            )

                            assert result is True
