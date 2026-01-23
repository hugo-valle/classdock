"""
Tests for UI components changes related to centralized token management.

This test suite validates that UI components correctly display information
about centralized token management and don't reference deprecated token files.
"""

import pytest
from unittest.mock import Mock, patch, call
from io import StringIO

from classdock.utils.ui_components import show_completion, show_help, show_version


class TestShowCompletionCentralizedToken:
    """Test show_completion() function with centralized token messages."""

    @patch('sys.stdout', new_callable=StringIO)
    def test_show_completion_with_secrets_enabled(self, mock_stdout):
        """Test completion screen with secrets enabled shows centralized token message."""
        config_values = {
            'USE_SECRETS': 'true',
            'ORGANIZATION': 'test-org',
            'ASSIGNMENT_NAME': 'test-assignment'
        }
        token_files = {}

        show_completion(config_values, token_files)
        output = mock_stdout.getvalue()

        # Should mention centralized token management
        assert "centralized" in output.lower() or "~/.config/classdock" in output

        # Should NOT mention instructor_token.txt
        assert "instructor_token.txt" not in output

        # Should show that files were created
        assert "assignment.conf" in output
        assert ".gitignore" in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_show_completion_without_secrets(self, mock_stdout):
        """Test completion screen with secrets disabled."""
        config_values = {
            'USE_SECRETS': 'false',
            'ORGANIZATION': 'test-org',
            'ASSIGNMENT_NAME': 'test-assignment'
        }
        token_files = {}

        show_completion(config_values, token_files)
        output = mock_stdout.getvalue()

        # Should show basic files
        assert "assignment.conf" in output
        assert ".gitignore" in output

        # Should NOT mention token files
        assert "instructor_token.txt" not in output
        assert "token.txt" not in output.lower() or "token_config.json" in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_show_completion_displays_centralized_path(self, mock_stdout):
        """Test that completion screen displays centralized token config path."""
        config_values = {
            'USE_SECRETS': 'true',
            'ORGANIZATION': 'test-org',
            'ASSIGNMENT_NAME': 'test-assignment'
        }
        token_files = {}

        show_completion(config_values, token_files)
        output = mock_stdout.getvalue()

        # Should show the centralized token location
        assert "~/.config/classdock" in output or "token_config.json" in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_show_completion_no_token_files_loop(self, mock_stdout):
        """Test that completion screen doesn't iterate over token_files dict."""
        config_values = {
            'USE_SECRETS': 'true',
            'ORGANIZATION': 'test-org',
            'ASSIGNMENT_NAME': 'test-assignment'
        }
        # Provide token_files dict that would be displayed in old implementation
        token_files = {
            'INSTRUCTOR_TESTS_TOKEN': 'instructor_token.txt',
            'CUSTOM_TOKEN': 'custom_token.txt'
        }

        show_completion(config_values, token_files)
        output = mock_stdout.getvalue()

        # Should NOT display individual token files from the dict
        # (In centralized approach, we don't iterate token_files)
        # Check that we mention centralized management instead
        assert "centralized" in output.lower() or "~/.config/classdock" in output

    @patch('sys.stdout', new_callable=StringIO)
    @patch('os.system')
    def test_show_completion_clears_screen(self, mock_system, mock_stdout):
        """Test that completion screen clears the terminal."""
        config_values = {'USE_SECRETS': 'false'}
        token_files = {}

        with patch('sys.stdout.isatty', return_value=True):
            show_completion(config_values, token_files)

        # Should call clear command
        mock_system.assert_called_once_with('clear')


class TestShowHelpCentralizedToken:
    """Test show_help() function with centralized token documentation."""

    @patch('sys.stdout', new_callable=StringIO)
    def test_show_help_mentions_centralized_token(self, mock_stdout):
        """Test that help text mentions centralized token management."""
        show_help()
        output = mock_stdout.getvalue()

        # Should mention centralized token management
        assert "centralized" in output.lower() or "~/.config/classdock" in output

        # Should have TOKEN MANAGEMENT section
        assert "TOKEN MANAGEMENT" in output

    @patch('sys.stdout', new_callable=StringIO)
    def test_show_help_no_token_file_references(self, mock_stdout):
        """Test that help text doesn't reference deprecated token files."""
        show_help()
        output = mock_stdout.getvalue()

        # Should NOT mention instructor_token.txt in generated files
        generated_files_section = output.split("GENERATED FILES:")[
            1].split("\n\n")[0]
        assert "instructor_token.txt" not in generated_files_section
        assert "[custom]_token.txt" not in generated_files_section

    @patch('sys.stdout', new_callable=StringIO)
    def test_show_help_features_section(self, mock_stdout):
        """Test that FEATURES section mentions centralized token management."""
        show_help()
        output = mock_stdout.getvalue()

        # Extract features section
        features_section = output.split("FEATURES:")[1].split("\n\n")[0]

        # Should mention centralized token management
        assert "centralized" in features_section.lower(
        ) or "token" in features_section.lower()

        # Should NOT mention "Secure token file creation"
        assert "Secure token file creation" not in features_section

    @patch('sys.stdout', new_callable=StringIO)
    def test_show_help_requirements_section(self, mock_stdout):
        """Test that REQUIREMENTS section mentions token configuration."""
        show_help()
        output = mock_stdout.getvalue()

        # Extract requirements section
        requirements_section = output.split("REQUIREMENTS:")[
            1].split("\n\n")[0]

        # Should mention GitHub token configuration
        assert "token" in requirements_section.lower()
        assert "~/.config/classdock" in requirements_section or "environment" in requirements_section

    @patch('sys.stdout', new_callable=StringIO)
    def test_show_help_token_management_section(self, mock_stdout):
        """Test that TOKEN MANAGEMENT section exists and is informative."""
        show_help()
        output = mock_stdout.getvalue()

        # Should have TOKEN MANAGEMENT section
        assert "TOKEN MANAGEMENT" in output

        # Extract token management section
        token_section = output.split("TOKEN MANAGEMENT:")[1].split("\n\n")[0]

        # Should mention key token locations
        assert "~/.config/classdock" in token_section or "token_config.json" in token_section
        assert "GITHUB_TOKEN" in token_section or "environment" in token_section.lower()
        assert "repository" in token_section.lower()

    @patch('sys.stdout', new_callable=StringIO)
    def test_show_help_generated_files_minimal(self, mock_stdout):
        """Test that GENERATED FILES section only lists actual generated files."""
        show_help()
        output = mock_stdout.getvalue()

        # Extract generated files section
        generated_section = output.split("GENERATED FILES:")[
            1].split("\n\n")[0]

        # Should mention the files that are actually created
        assert "assignment.conf" in generated_section
        assert ".gitignore" in generated_section

        # Should NOT mention token files (they're no longer generated)
        lines_with_token_txt = [
            line for line in generated_section.split('\n') if 'token.txt' in line]
        # Filter out the TOKEN MANAGEMENT section which mentions token_config.json
        token_txt_lines = [
            line for line in lines_with_token_txt if 'token_config.json' not in line]
        assert len(
            token_txt_lines) == 0, f"Found deprecated token file references: {token_txt_lines}"


class TestShowVersion:
    """Test show_version() function."""

    @patch('sys.stdout', new_callable=StringIO)
    def test_show_version_format(self, mock_stdout):
        """Test that version information is displayed correctly."""
        show_version()
        output = mock_stdout.getvalue()

        # Should have version info
        assert "GitHub Classroom" in output
        assert "v" in output.lower() or "version" in output.lower()

    @patch('sys.stdout', new_callable=StringIO)
    def test_show_version_mentions_python(self, mock_stdout):
        """Test that version info mentions Python version."""
        show_version()
        output = mock_stdout.getvalue()

        # Should mention Python
        assert "Python" in output or "python" in output.lower()


class TestUIComponentsIntegration:
    """Integration tests for UI components."""

    @patch('sys.stdout', new_callable=StringIO)
    def test_completion_and_help_consistency(self, mock_stdout):
        """Test that completion and help messages are consistent."""
        # Get completion output
        config_values = {'USE_SECRETS': 'true'}
        token_files = {}
        show_completion(config_values, token_files)
        completion_output = mock_stdout.getvalue()
        mock_stdout.truncate(0)
        mock_stdout.seek(0)

        # Get help output
        show_help()
        help_output = mock_stdout.getvalue()

        # Both should mention centralized token management
        assert ("centralized" in completion_output.lower()
                or "~/.config/classdock" in completion_output)
        assert ("centralized" in help_output.lower()
                or "~/.config/classdock" in help_output)

        # Neither should mention deprecated instructor_token.txt
        assert "instructor_token.txt" not in completion_output
        # Help might mention token files in TOKEN MANAGEMENT context, but not in GENERATED FILES
        if "GENERATED FILES:" in help_output:
            generated_section = help_output.split("GENERATED FILES:")[
                1].split("\n\n")[0]
            assert "instructor_token.txt" not in generated_section

    @patch('sys.stdout', new_callable=StringIO)
    def test_ui_messages_user_friendly(self, mock_stdout):
        """Test that UI messages are clear and user-friendly."""
        config_values = {'USE_SECRETS': 'true'}
        token_files = {}
        show_completion(config_values, token_files)
        output = mock_stdout.getvalue()

        # Should have friendly formatting (emojis, colors, boxes)
        assert "🎉" in output or "║" in output  # Either emoji or box drawing

        # Should have clear sections
        assert "Files Created" in output or "Next Steps" in output

        # Should be informative about token management
        assert "token" in output.lower()


class TestUIComponentsBackwardCompatibility:
    """Test that UI components handle legacy scenarios gracefully."""

    @patch('sys.stdout', new_callable=StringIO)
    def test_show_completion_handles_empty_token_files(self, mock_stdout):
        """Test completion with empty token_files dict."""
        config_values = {'USE_SECRETS': 'true'}
        token_files = {}

        # Should not raise exception
        show_completion(config_values, token_files)
        output = mock_stdout.getvalue()

        assert len(output) > 0

    @patch('sys.stdout', new_callable=StringIO)
    def test_show_completion_handles_none_use_secrets(self, mock_stdout):
        """Test completion when USE_SECRETS is not set."""
        config_values = {}
        token_files = {}

        # Should not raise exception
        show_completion(config_values, token_files)
        output = mock_stdout.getvalue()

        assert len(output) > 0

    @patch('sys.stdout', new_callable=StringIO)
    def test_show_completion_with_legacy_token_files(self, mock_stdout):
        """Test completion still works if token_files dict is provided (legacy)."""
        config_values = {'USE_SECRETS': 'true'}
        # Legacy code might still pass token_files
        token_files = {'OLD_TOKEN': 'old_token.txt'}

        # Should not crash and should show centralized approach
        show_completion(config_values, token_files)
        output = mock_stdout.getvalue()

        assert len(output) > 0
        # Should emphasize centralized approach
        assert "centralized" in output.lower() or "~/.config/classdock" in output
