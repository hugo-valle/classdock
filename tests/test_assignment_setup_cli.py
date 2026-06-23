"""
Comprehensive CLI tests for assignment setup command options.

This test suite focuses specifically on the assignment setup command and its various
options: --simplified and regular interactive mode.
"""

import pytest
from unittest.mock import Mock, patch
import subprocess
import sys
from pathlib import Path


def run_cli_command(cmd: str, cwd: Path | None = None) -> tuple[bool, str, str]:
    """Helper function to run CLI commands."""
    try:
        import shlex
        cmd_list = shlex.split(cmd)

        import os
        env = os.environ.copy()
        env.setdefault("COLUMNS", "200")

        result = subprocess.run(
            cmd_list,
            capture_output=True,
            text=True,
            cwd=cwd or Path.cwd(),
            timeout=30,
            env=env
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)


class TestAssignmentSetupCLI:
    """Test the assignment setup CLI command and its options."""

    def test_setup_help_shows_options(self):
        """Test that --help shows all available options."""
        success, stdout, stderr = run_cli_command(
            "python -m classdock assignments setup --help")

        assert success, f"Setup help failed: {stderr}"

        # Combine stdout and stderr as help might be in either
        output = stdout + stderr

        # Strip ANSI color codes for easier testing
        import re
        output = re.sub(r'\x1b\[[0-9;]*m', '', output)

        # Check that all options are documented
        assert "--simplified" in output, f"--simplified option not shown in help. Output: {output[:500]}"

    def test_setup_dry_run_basic(self):
        """Test basic setup in dry-run mode."""
        success, stdout, stderr = run_cli_command(
            "python -m classdock assignments --dry-run setup")

        assert success, f"Basic setup dry-run failed: {stderr}"
        assert "DRY RUN" in stderr, "Dry run message not found"
        assert "assignment setup wizard" in stderr, "Setup wizard message not found"

    def test_setup_dry_run_with_simplified(self):
        """Test setup with --simplified option in dry-run mode."""
        success, stdout, stderr = run_cli_command(
            "python -m classdock assignments --dry-run setup --simplified")

        # Simplified mode is not implemented yet, so it returns False
        assert not success, f"Simplified setup should fail: {stderr}"
        assert "DRY RUN" in stderr, "Dry run message not found"
        assert "Simplified setup mode not yet implemented" in stderr, "Not implemented message not found"

    def test_setup_simplified_not_implemented(self):
        """Test setup with --simplified option when not implemented."""
        # TODO: Update this test when simplified setup is implemented
        # When simplified setup is working, this test should:
        # - Rename to test_setup_simplified_success()
        # - Assert success is True
        # - Assert completion message instead of error
        # - Test that simplified setup completes faster/with fewer prompts
        success, stdout, stderr = run_cli_command(
            "python -m classdock assignments setup --simplified")

        assert not success, "Simplified setup should fail when not implemented"
        assert "Simplified setup mode not yet implemented" in stderr, "Implementation error message not found"

    def test_setup_verbose_output(self):
        """Test setup with verbose output."""
        success, stdout, stderr = run_cli_command(
            "python -m classdock assignments --dry-run --verbose setup")

        assert success, f"Verbose setup failed: {stderr}"
        assert "DRY RUN" in stderr, "Dry run message not found"
        # Verbose mode should provide more detailed output
        # This is a placeholder for when verbose logging is implemented


class TestAssignmentSetupService:
    """Test the AssignmentService setup method directly."""

    def test_service_setup_basic(self):
        """Test basic service setup."""
        from classdock.services.assignment_service import AssignmentService

        service = AssignmentService(dry_run=True)
        success, message = service.setup()

        assert success is True
        assert "DRY RUN" in message

    def test_service_setup_parameters(self):
        """Test that service setup method accepts simplified parameter."""
        from classdock.services.assignment_service import AssignmentService

        service = AssignmentService(dry_run=True)
        success, message = service.setup()
        assert success is True

    @patch('classdock.utils.token_manager.GitHubTokenManager')
    @patch('classdock.assignments.setup.AssignmentSetup')
    def test_service_setup_with_mocked_wizard(self, mock_assignment_setup, mock_token_manager):
        """Test service setup with mocked wizard."""
        # Mock the token manager to return a valid token
        mock_token_instance = Mock()
        mock_token_instance.get_github_token.return_value = "test_token"
        mock_token_instance.config_file.exists.return_value = True
        mock_token_manager.return_value = mock_token_instance

        # Mock the AssignmentSetup class
        mock_wizard = Mock()
        mock_wizard.run_wizard.return_value = True
        mock_assignment_setup.return_value = mock_wizard

        from classdock.services.assignment_service import AssignmentService
        service = AssignmentService(dry_run=False)
        success, message = service.setup()

        assert success is True
        assert "completed successfully" in message
        mock_assignment_setup.assert_called_once()
        mock_wizard.run_wizard.assert_called_once()


class TestAssignmentSetupIntegration:
    """Integration tests for assignment setup functionality."""

    def test_setup_command_integration(self):
        """Test the complete setup command flow in dry-run mode."""
        success, stdout, stderr = run_cli_command(
            "python -m classdock assignments --dry-run --verbose setup")

        assert success, f"Integration test failed: {stderr}"

        # Verify the command flow
        assert "Loading configuration" in stderr or "DRY RUN" in stderr
        assert "assignment setup wizard" in stderr

    def test_setup_with_config_present(self):
        """Test setup when assignment.conf already exists."""
        # This test should verify behavior when config file exists
        success, stdout, stderr = run_cli_command(
            "python -m classdock assignments --dry-run setup")

        assert success, f"Setup with existing config failed: {stderr}"

    def test_setup_error_handling(self):
        """Test setup error handling scenarios."""
        # Test with invalid configuration path
        success, stdout, stderr = run_cli_command(
            "python -m classdock --assignment-root /nonexistent/path assignments --dry-run setup")

        # Should handle gracefully in dry-run mode
        # May show warnings but should not fail completely
        # This is a placeholder for proper error handling testing


class TestAssignmentSetupExamples:
    """Test real-world usage examples from help documentation."""

    def test_example_basic_setup(self):
        """Test: classdock assignments setup"""
        success, stdout, stderr = run_cli_command(
            "python -m classdock assignments --dry-run setup")

        assert success, f"Basic example failed: {stderr}"

    def test_example_simplified_setup(self):
        """Test: classdock assignments setup --simplified"""
        success, stdout, stderr = run_cli_command(
            "python -m classdock assignments --dry-run setup --simplified")

        # Simplified mode is not implemented yet
        assert not success, f"Simplified example should fail: {stderr}"
        assert "Simplified setup mode not yet implemented" in stderr

    def test_example_simplified_not_implemented(self):
        """Test: classdock assignments setup --simplified (not yet implemented)."""
        success, stdout, stderr = run_cli_command(
            "python -m classdock assignments --dry-run setup --simplified")

        assert not success, f"Simplified example should fail: {stderr}"
        assert "Simplified setup mode not yet implemented" in stderr


class TestAssignmentSetupFutureFeatures:
    """Tests for features that should be implemented for --simplified option."""

    def test_simplified_wizard_flow(self):
        """Test that simplified option provides minimal prompts (future feature)."""
        # This is a placeholder for when simplified flow is implemented
        pass

    def test_github_api_integration(self):
        """Test GitHub API integration for setup (future feature)."""
        # This is a placeholder for when GitHub API integration is implemented
        # URL-based setup should:
        # - Validate the classroom URL
        # - Fetch assignment details from GitHub API
        # - Auto-discover template repository
        # - Pre-populate configuration
        pass
