"""
Comprehensive test suite for classdock.config.generator module.

This test suite provides comprehensive coverage for the ConfigGenerator class,
which is responsible for generating GitHub Classroom assignment configuration files.
The tests include unit tests for individual methods, integration tests for complete
configuration generation, error handling, edge cases, and proper validation of
generated configuration file content.

Test Categories:
1. Basic Functionality Tests - Core method testing and initialization
2. Configuration Section Tests - Individual section generation logic
3. Edge Case Tests - Boundary conditions and unusual inputs  
4. Error Handling Tests - Exception scenarios and file operations
5. Integration Tests - End-to-end configuration generation workflows
6. Validation Tests - Content validation and format verification

The ConfigGenerator class generates configuration files with the following sections:
- Header: File metadata with timestamp
- Assignment Information: URLs, organization, file paths
- Secret Management: Token configuration and validation
- Workflow Configuration: Step execution settings
- Advanced Configuration: Repository filtering and logging settings

All tests use proper mocking to isolate the ConfigGenerator from external dependencies
and ensure test reliability and speed. The tests validate both successful operations
and error conditions to ensure robust production behavior.
"""

import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, mock_open

from classdock.config.generator import ConfigGenerator


class TestConfigGeneratorInitialization:
    """
    TestConfigGeneratorInitialization contains unit tests to verify the correct initialization
    of the ConfigGenerator class. It ensures that the constructor properly handles different
    types of file path inputs and that all required attributes and methods are available
    after instantiation.

    Test Cases:
    - test_init_with_path_object: Verifies initialization with pathlib.Path objects
    - test_init_with_string_path: Ensures string paths are handled correctly
    - test_init_with_relative_path: Tests relative path handling
    - test_init_attributes_exist: Confirms all required methods are available
    """

    def test_init_with_path_object(self):
        """
        Test that the ConfigGenerator class properly initializes when provided with a pathlib.Path object.

        This test verifies that the config_file attribute is correctly set and maintains its Path type
        when initialized with a Path object, ensuring compatibility with pathlib operations.
        """
        config_path = Path("/test/config.conf")
        generator = ConfigGenerator(config_path)

        assert generator.config_file == config_path
        assert isinstance(generator.config_file, Path)

    def test_init_with_string_path(self):
        """
        Test that the ConfigGenerator class properly handles initialization with string paths.

        This test ensures that string path inputs are accepted and that the config_file attribute
        correctly stores the path information, whether as a string or converted to a Path object.
        """
        config_path = "/test/config.conf"
        generator = ConfigGenerator(config_path)

        # Even if passed as string, should be stored as Path or work with string
        assert str(generator.config_file) == config_path

    def test_init_with_relative_path(self):
        """
        Test that the ConfigGenerator class correctly handles relative file paths during initialization.

        This test verifies that relative paths are properly stored in the config_file attribute
        without modification, allowing for flexible file path handling in different contexts.
        """
        config_path = Path("assignment.conf")
        generator = ConfigGenerator(config_path)

        assert generator.config_file == config_path

    def test_init_attributes_exist(self):
        """
        Test that the ConfigGenerator class has all required attributes and methods after initialization.

        This test verifies that the ConfigGenerator instance contains all necessary methods for
        configuration file generation, including config_file attribute and all section generation methods.
        """
        generator = ConfigGenerator(Path("/test/config.conf"))

        # Verify that the instance has the expected structure
        assert hasattr(generator, 'config_file')
        assert hasattr(generator, 'create_config_file')
        assert hasattr(generator, '_generate_header')
        assert hasattr(generator, '_generate_assignment_section')
        assert hasattr(generator, '_generate_secrets_section')
        assert hasattr(generator, '_generate_workflow_section')
        assert hasattr(generator, '_generate_advanced_section')


class TestConfigGeneratorHeaderGeneration:
    """
    TestConfigGeneratorHeaderGeneration contains unit tests for the configuration file header
    generation functionality. It verifies that headers contain proper metadata, timestamps,
    and formatting according to the expected configuration file structure.

    Test Cases:
    - test_generate_header_format: Validates header content and structure with mocked datetime
    - test_generate_header_datetime_integration: Tests real datetime integration and format
    """

    def test_generate_header_format(self):
        """
        Test that the _generate_header method produces a header with correct format and content.

        This test uses mocked datetime to ensure consistent output and verifies that the header
        contains the expected title, timestamp format, and description text. The test ensures
        that the header ends with proper line spacing for the configuration file.
        """
        generator = ConfigGenerator(Path("/test/config.conf"))

        with patch('classdock.config.generator.datetime') as mock_datetime:
            # Mock datetime to ensure consistent output
            mock_datetime.now.return_value.strftime.return_value = "2025-09-17 10:30:45"

            header = generator._generate_header()

            assert "# GitHub Classroom Assignment Configuration" in header
            assert "# Generated by setup-assignment.py on 2025-09-17 10:30:45" in header
            assert "# This file contains all the necessary information" in header
            assert header.endswith("\n\n")

    def test_generate_header_datetime_integration(self):
        """
        Test that the header includes actual datetime information when not mocked.

        This test validates the integration with Python's datetime module by checking that
        the generated header contains the current year and has the expected structure when
        datetime functionality is not mocked.
        """
        generator = ConfigGenerator(Path("/test/config.conf"))

        header = generator._generate_header()

        # Should contain current year
        current_year = str(datetime.now().year)
        assert current_year in header

        # Should have proper structure
        lines = header.strip().split('\n')
        assert len(lines) >= 3
        assert lines[0].startswith(
            "# GitHub Classroom Assignment Configuration")


class TestConfigGeneratorAssignmentSection:
    """
    TestConfigGeneratorAssignmentSection contains unit tests for the assignment information
    section generation within configuration files. It verifies that assignment URLs, repository
    information, organization details, and file paths are correctly formatted and included
    in the generated configuration section.

    Test Cases:
    - test_generate_assignment_section_complete: Tests complete configuration with all values
    - test_generate_assignment_section_minimal: Tests minimal required configuration values
    - test_generate_assignment_section_different_file_types: Tests various assignment file types
    """

    def test_generate_assignment_section_complete(self):
        """
        Test assignment section generation with all configuration values provided.

        This test verifies that when all assignment configuration values are provided,
        including classroom URL, repository URL, template URL, organization, assignment name,
        and main file, they are all correctly included in the generated section with proper
        formatting and section headers.
        """
        generator = ConfigGenerator(Path("/test/config.conf"))

        config_values = {
            'CLASSROOM_URL': 'https://classroom.github.com/classrooms/12345/assignments/test-assignment',
            'CLASSROOM_REPO_URL': 'https://github.com/test-org/classroom-test-assignment',
            'TEMPLATE_REPO_URL': 'https://github.com/test-org/assignment-template',
            'GITHUB_ORGANIZATION': 'test-org',
            'ASSIGNMENT_NAME': 'test-assignment',
            'MAIN_ASSIGNMENT_FILE': 'assignment.ipynb'
        }

        section = generator._generate_assignment_section(config_values)

        # Check for all required fields
        assert 'CLASSROOM_URL="https://classroom.github.com/classrooms/12345/assignments/test-assignment"' in section
        assert 'CLASSROOM_REPO_URL="https://github.com/test-org/classroom-test-assignment"' in section
        assert 'TEMPLATE_REPO_URL="https://github.com/test-org/assignment-template"' in section
        assert 'GITHUB_ORGANIZATION="test-org"' in section
        assert 'ASSIGNMENT_NAME="test-assignment"' in section
        assert 'ASSIGNMENT_FILE="assignment.ipynb"' in section

        # Check for section headers
        assert 'ASSIGNMENT INFORMATION' in section
        assert '=============================================================================' in section

    def test_generate_assignment_section_minimal(self):
        """
        Test assignment section generation with minimal required configuration values.

        This test verifies that when only the essential configuration values are provided,
        the section is generated correctly with required fields present and optional fields
        properly commented out as placeholders for future configuration.
        """
        generator = ConfigGenerator(Path("/test/config.conf"))

        config_values = {
            'CLASSROOM_URL': 'https://classroom.github.com/classrooms/12345/assignments/test',
            'TEMPLATE_REPO_URL': 'https://github.com/test-org/template',
            'GITHUB_ORGANIZATION': 'test-org',
            'MAIN_ASSIGNMENT_FILE': 'main.py'
        }

        section = generator._generate_assignment_section(config_values)

        # Check required fields are present
        assert 'CLASSROOM_URL="https://classroom.github.com/classrooms/12345/assignments/test"' in section
        assert 'TEMPLATE_REPO_URL="https://github.com/test-org/template"' in section
        assert 'GITHUB_ORGANIZATION="test-org"' in section
        assert 'ASSIGNMENT_FILE="main.py"' in section

        # Check optional fields are commented out
        assert '# CLASSROOM_REPO_URL=""' in section
        assert '# ASSIGNMENT_NAME=""' in section

    def test_generate_assignment_section_different_file_types(self):
        """
        Test assignment section generation with various assignment file types.

        This test validates that the ConfigGenerator correctly handles different assignment
        file types including Jupyter notebooks (.ipynb), Python files (.py), C++ files (.cpp),
        SQL files (.sql), HTML files (.html), and Markdown files (.md), ensuring universal
        support for diverse assignment formats.
        """
        generator = ConfigGenerator(Path("/test/config.conf"))

        file_types = [
            'assignment.ipynb',  # Jupyter notebook
            'main.py',           # Python
            'solution.cpp',      # C++
            'queries.sql',       # SQL
            'index.html',        # HTML
            'README.md'          # Markdown
        ]

        for file_type in file_types:
            config_values = {
                'CLASSROOM_URL': 'https://classroom.github.com/test',
                'TEMPLATE_REPO_URL': 'https://github.com/test/template',
                'GITHUB_ORGANIZATION': 'test-org',
                'MAIN_ASSIGNMENT_FILE': file_type
            }

            section = generator._generate_assignment_section(config_values)
            assert f'ASSIGNMENT_FILE="{file_type}"' in section


class TestConfigGeneratorSecretsSection:
    """
    TestConfigGeneratorSecretsSection contains unit tests for the secrets management section
    generation within configuration files. It verifies that secret configurations are properly
    formatted, token validation settings are correct, and both enabled and disabled secret
    scenarios are handled appropriately.

    Test Cases:
    - test_generate_secrets_section_with_secrets: Tests secrets section when secrets are enabled
    - test_generate_secrets_section_without_secrets: Tests secrets section when secrets are disabled
    - test_generate_secrets_section_custom_descriptions: Tests custom secret descriptions
    - test_generate_secrets_section_missing_use_secrets: Tests default behavior when USE_SECRETS is not specified
    """

    def test_generate_secrets_section_with_secrets(self):
        """
        Test secrets section generation when secrets management is enabled.

        This test verifies that when USE_SECRETS is set to 'true', the secrets section
        properly configures INSTRUCTOR_TESTS_TOKEN and additional secrets with correct
        token file paths, validation settings, and format specifications.
        """
        generator = ConfigGenerator(Path("/test/config.conf"))

        config_values = {'USE_SECRETS': 'true'}
        token_files = {
            'INSTRUCTOR_TESTS_TOKEN': 'instructor_token.txt',
            'API_KEY': 'api_key.txt'
        }
        token_validation = {
            'INSTRUCTOR_TESTS_TOKEN': True,
            'API_KEY': False
        }

        section = generator._generate_secrets_section(
            config_values, token_files, token_validation)

        # Check section header
        assert 'SECRET MANAGEMENT' in section
        assert 'SECRETS_CONFIG=' in section

        # Check instructor token configuration (new 3-field format)
        assert 'INSTRUCTOR_TESTS_TOKEN:Token for accessing instructor test repository:true' in section

        # Check additional secret configuration (new 3-field format)
        assert 'API_KEY:API_KEY for assignment functionality:false' in section

    def test_generate_secrets_section_without_secrets(self):
        """
        Test secrets section generation when secrets management is disabled.

        This test verifies that when USE_SECRETS is set to 'false', the secrets section
        includes proper documentation and commented examples while setting SECRETS_CONFIG
        to an empty string to disable secret management functionality.
        """
        generator = ConfigGenerator(Path("/test/config.conf"))

        config_values = {'USE_SECRETS': 'false'}
        token_files = {}
        token_validation = {}

        section = generator._generate_secrets_section(
            config_values, token_files, token_validation)

        # Check section header
        assert 'SECRET MANAGEMENT' in section

        # Check that it includes commented example
        assert '# INSTRUCTOR_TESTS_TOKEN:Token for accessing instructor test repository:instructor_token.txt:90' in section
        assert 'SECRETS_CONFIG=""' in section

    def test_generate_secrets_section_custom_descriptions(self):
        """
        Test secrets section generation with custom secret descriptions.

        This test validates that custom descriptions for secrets (provided via configuration
        values like DATABASE_TOKEN_DESCRIPTION) are properly incorporated into the secrets
        configuration format instead of using default generated descriptions.
        """
        generator = ConfigGenerator(Path("/test/config.conf"))

        config_values = {
            'USE_SECRETS': 'true',
            'DATABASE_TOKEN_DESCRIPTION': 'Database access token for student queries'
        }
        token_files = {
            'INSTRUCTOR_TESTS_TOKEN': 'instructor_token.txt',
            'DATABASE_TOKEN': 'db_token.txt'
        }
        token_validation = {
            'INSTRUCTOR_TESTS_TOKEN': True,
            'DATABASE_TOKEN': False
        }

        section = generator._generate_secrets_section(
            config_values, token_files, token_validation)

        # Check custom description is used (new 3-field format)
        assert 'DATABASE_TOKEN:Database access token for student queries:false' in section

    def test_generate_secrets_section_missing_use_secrets(self):
        """
        Test secrets section generation when USE_SECRETS configuration is not specified.

        This test ensures that when the USE_SECRETS key is missing from the configuration
        values, the secrets section defaults to disabled behavior with empty SECRETS_CONFIG
        and appropriate documentation.
        """
        generator = ConfigGenerator(Path("/test/config.conf"))

        config_values = {}  # No USE_SECRETS key
        token_files = {}
        token_validation = {}

        section = generator._generate_secrets_section(
            config_values, token_files, token_validation)

        # Should default to disabled behavior
        assert 'SECRET MANAGEMENT' in section
        assert 'SECRETS_CONFIG=""' in section


class TestConfigGeneratorWorkflowSection:
    """
    TestConfigGeneratorWorkflowSection contains unit tests for the workflow configuration
    section generation within configuration files. It verifies that workflow steps are
    correctly configured based on secrets settings and that output directory and execution
    parameters are properly set.

    Test Cases:
    - test_generate_workflow_section_with_secrets: Tests workflow configuration when secrets are enabled
    - test_generate_workflow_section_without_secrets: Tests workflow configuration when secrets are disabled
    - test_generate_workflow_section_missing_use_secrets: Tests default workflow behavior
    """

    def test_generate_workflow_section_with_secrets(self):
        """
        Test workflow section generation when secrets management is enabled.

        This test verifies that when USE_SECRETS is 'true', the workflow section correctly
        sets STEP_MANAGE_SECRETS=true while maintaining appropriate settings for other workflow
        steps and output directory configuration.
        """
        generator = ConfigGenerator(Path("/test/config.conf"))

        config_values = {'USE_SECRETS': 'true'}

        section = generator._generate_workflow_section(config_values)

        # Check section header
        assert 'WORKFLOW CONFIGURATION' in section

        # Check workflow steps
        assert 'STEP_SYNC_TEMPLATE=true' in section
        assert 'STEP_DISCOVER_REPOS=true' in section
        assert 'STEP_MANAGE_SECRETS=true' in section
        assert 'STEP_ASSIST_STUDENTS=false' in section

        # Check output directory
        assert 'OUTPUT_DIR="tools/generated"' in section

    def test_generate_workflow_section_without_secrets(self):
        """
        Test workflow section generation when secrets management is disabled.

        This test verifies that when USE_SECRETS is 'false', the workflow section correctly
        sets STEP_MANAGE_SECRETS=false while keeping other workflow step configurations
        unchanged for normal assignment processing.
        """
        generator = ConfigGenerator(Path("/test/config.conf"))

        config_values = {'USE_SECRETS': 'false'}

        section = generator._generate_workflow_section(config_values)

        # Check that secrets step is disabled
        assert 'STEP_MANAGE_SECRETS=false' in section

        # Other steps should remain the same
        assert 'STEP_SYNC_TEMPLATE=true' in section
        assert 'STEP_DISCOVER_REPOS=true' in section
        assert 'STEP_ASSIST_STUDENTS=false' in section

    def test_generate_workflow_section_missing_use_secrets(self):
        """
        Test workflow section generation when USE_SECRETS configuration is not specified.

        This test ensures that when the USE_SECRETS key is missing from configuration values,
        the workflow section defaults to STEP_MANAGE_SECRETS=false for safe operation without
        secrets management functionality.
        """
        generator = ConfigGenerator(Path("/test/config.conf"))

        config_values = {}  # No USE_SECRETS key

        section = generator._generate_workflow_section(config_values)

        # Should default to false
        assert 'STEP_MANAGE_SECRETS=false' in section


class TestConfigGeneratorAdvancedSection:
    """
    TestConfigGeneratorAdvancedSection contains unit tests for the advanced configuration
    section generation within configuration files. It verifies that repository filtering,
    logging settings, dry run modes, and confirmation prompt settings are correctly
    configured with appropriate default values.

    Test Cases:
    - test_generate_advanced_section_content: Tests all advanced configuration settings
    - test_generate_advanced_section_format: Tests section formatting and organization
    """

    def test_generate_advanced_section_content(self):
        """
        Test that the advanced configuration section contains all required settings.

        This test verifies that the advanced section includes repository filtering options,
        dry run mode settings, logging level configuration, and confirmation prompt settings
        with appropriate default values for production use.
        """
        generator = ConfigGenerator(Path("/test/config.conf"))

        section = generator._generate_advanced_section()

        # Check section header
        assert 'ADVANCED CONFIGURATION' in section

        # Check repository filtering settings
        assert 'EXCLUDE_INSTRUCTOR_REPOS=true' in section
        assert 'INCLUDE_TEMPLATE_REPO=false' in section

        # Check dry run mode
        assert 'DEFAULT_DRY_RUN=false' in section

        # Check logging level
        assert 'LOG_LEVEL=INFO' in section

        # Check confirmation prompts
        assert 'SKIP_CONFIRMATIONS=false' in section

    def test_generate_advanced_section_format(self):
        """
        Test that the advanced configuration section has proper formatting and organization.

        This test verifies that the advanced section includes proper section delimiters,
        organized comment groups for different setting categories, and clear structure
        for repository filtering, dry run mode, logging, and confirmation settings.
        """
        generator = ConfigGenerator(Path("/test/config.conf"))

        section = generator._generate_advanced_section()

        # Should have proper section delimiter
        assert '=============================================================================' in section

        # Should have comments for each group
        assert '# Repository filtering' in section
        assert '# Dry run mode' in section
        assert '# Logging level' in section
        assert '# Confirmation prompts' in section


class TestConfigGeneratorFileOperations:
    """
    TestConfigGeneratorFileOperations contains unit tests for file creation and writing
    operations within the ConfigGenerator class. It verifies that configuration files
    are properly created, content is correctly written, UI feedback is provided, and
    file operation errors are appropriately handled.

    Test Cases:
    - test_create_config_file_success: Tests successful file creation with proper UI feedback
    - test_create_config_file_content_structure: Tests generated content structure and sections
    - test_create_config_file_write_error: Tests error handling for file write operations
    """

    @patch('classdock.config.generator.print_header')
    @patch('classdock.config.generator.print_success')
    def test_create_config_file_success(self, mock_print_success, mock_print_header):
        """
        Test successful configuration file creation with proper UI feedback and file operations.

        This test verifies that the create_config_file method successfully opens a file for writing,
        writes configuration content, and calls the appropriate UI functions (print_header and
        print_success) to provide user feedback during the file creation process.
        """
        config_path = Path("/test/config.conf")
        generator = ConfigGenerator(config_path)

        config_values = {
            'CLASSROOM_URL': 'https://classroom.github.com/test',
            'TEMPLATE_REPO_URL': 'https://github.com/test/template',
            'GITHUB_ORGANIZATION': 'test-org',
            'MAIN_ASSIGNMENT_FILE': 'assignment.ipynb',
            'USE_SECRETS': 'true'
        }

        token_files = {'INSTRUCTOR_TESTS_TOKEN': 'instructor_token.txt'}
        token_validation = {'INSTRUCTOR_TESTS_TOKEN': True}

        with patch('builtins.open', mock_open()) as mock_file:
            generator.create_config_file(
                config_values, token_files, token_validation)

            # Verify file was opened for writing
            mock_file.assert_called_once_with(config_path, 'w')

            # Verify content was written
            handle = mock_file()
            assert handle.write.called

            # Verify UI functions were called
            mock_print_header.assert_called_once_with(
                "Creating Assignment Configuration")
            mock_print_success.assert_called_once_with(
                f"Configuration file created: {config_path}")

    @patch('classdock.config.generator.print_header')
    @patch('classdock.config.generator.print_success')
    def test_create_config_file_content_structure(self, mock_print_success, mock_print_header):
        """
        Test that the created configuration file contains proper content structure and sections.

        This test captures all content written to the file and verifies that the complete
        configuration includes the header, assignment information, secret management, workflow
        configuration, and advanced configuration sections with correct values and formatting.
        """
        config_path = Path("/test/config.conf")
        generator = ConfigGenerator(config_path)

        config_values = {
            'CLASSROOM_URL': 'https://classroom.github.com/test',
            'TEMPLATE_REPO_URL': 'https://github.com/test/template',
            'GITHUB_ORGANIZATION': 'test-org',
            'MAIN_ASSIGNMENT_FILE': 'assignment.ipynb',
            'USE_SECRETS': 'false'
        }

        content_written = []

        def capture_write(content):
            content_written.append(content)

        with patch('builtins.open', mock_open()) as mock_file:
            mock_file().write = capture_write

            generator.create_config_file(config_values, {}, {})

            # Combine all written content
            full_content = ''.join(content_written)

            # Verify all sections are present
            assert '# GitHub Classroom Assignment Configuration' in full_content
            assert 'ASSIGNMENT INFORMATION' in full_content
            assert 'SECRET MANAGEMENT' in full_content
            assert 'WORKFLOW CONFIGURATION' in full_content
            assert 'ADVANCED CONFIGURATION' in full_content

            # Verify specific values
            assert 'CLASSROOM_URL="https://classroom.github.com/test"' in full_content
            assert 'STEP_MANAGE_SECRETS=false' in full_content

    @patch('classdock.config.generator.print_header')
    def test_create_config_file_write_error(self, mock_print_header):
        """
        Test proper handling of file write errors during configuration file creation.

        This test verifies that when file write operations fail (e.g., due to permission issues),
        the ConfigGenerator properly propagates the IOError exception without suppressing
        important error information that users need to resolve file system issues.
        """
        config_path = Path("/test/config.conf")
        generator = ConfigGenerator(config_path)

        config_values = {
            'CLASSROOM_URL': 'https://classroom.github.com/test',
            'TEMPLATE_REPO_URL': 'https://github.com/test/template',
            'GITHUB_ORGANIZATION': 'test-org',
            'MAIN_ASSIGNMENT_FILE': 'assignment.ipynb'
        }

        with patch('builtins.open', side_effect=IOError("Permission denied")):
            with pytest.raises(IOError, match="Permission denied"):
                generator.create_config_file(config_values, {}, {})


class TestConfigGeneratorEdgeCases:
    """
    TestConfigGeneratorEdgeCases contains unit tests for boundary conditions and unusual
    input scenarios within the ConfigGenerator class. It verifies that the generator
    handles edge cases gracefully, including empty configurations, special characters,
    very long values, and None values without causing failures.

    Test Cases:
    - test_empty_config_values: Tests behavior with completely empty configuration dictionaries
    - test_minimal_required_config_values: Tests minimal configuration with empty string values
    - test_special_characters_in_values: Tests handling of URLs and paths with special characters
    - test_very_long_values: Tests handling of extremely long configuration values
    - test_none_values_in_config: Tests resilience when configuration contains None values
    """

    def test_empty_config_values(self):
        """
        Test assignment section generation with completely empty configuration dictionary.

        This test verifies that the ConfigGenerator gracefully handles empty configuration
        dictionaries by using default empty string values for all required fields, ensuring
        the generated configuration file has proper structure even without input values.
        """
        generator = ConfigGenerator(Path("/test/config.conf"))

        # Test assignment section with empty values - should now work gracefully
        config_values = {}
        section = generator._generate_assignment_section(config_values)

        # Should handle missing keys gracefully with empty strings
        assert 'CLASSROOM_URL=""' in section
        assert 'TEMPLATE_REPO_URL=""' in section
        assert 'GITHUB_ORGANIZATION=""' in section
        assert 'ASSIGNMENT_FILE=""' in section

    def test_minimal_required_config_values(self):
        """
        Test assignment section generation with minimal required configuration containing empty strings.

        This test validates that when required configuration keys are present but contain empty
        string values, the ConfigGenerator produces a valid configuration section with properly
        formatted empty values that can be filled in later by users.
        """
        generator = ConfigGenerator(Path("/test/config.conf"))

        # Test assignment section with minimal required values
        config_values = {
            'CLASSROOM_URL': '',
            'TEMPLATE_REPO_URL': '',
            'GITHUB_ORGANIZATION': '',
            'MAIN_ASSIGNMENT_FILE': ''
        }
        section = generator._generate_assignment_section(config_values)

        # Should handle empty values gracefully
        assert 'CLASSROOM_URL=""' in section
        assert 'TEMPLATE_REPO_URL=""' in section
        assert 'GITHUB_ORGANIZATION=""' in section
        assert 'ASSIGNMENT_FILE=""' in section

    def test_special_characters_in_values(self):
        """
        Test handling of special characters in configuration values like URLs and file paths.

        This test verifies that the ConfigGenerator correctly handles URLs with query parameters,
        repository names with hyphens, organization names with underscores and numbers, and
        file names with spaces and parentheses by properly quoting values in the output.
        """
        generator = ConfigGenerator(Path("/test/config.conf"))

        config_values = {
            'CLASSROOM_URL': 'https://classroom.github.com/test?param=value&other=123',
            'TEMPLATE_REPO_URL': 'https://github.com/test/repo-with-dashes',
            'GITHUB_ORGANIZATION': 'test-org_123',
            'MAIN_ASSIGNMENT_FILE': 'assignment (copy).ipynb'
        }

        section = generator._generate_assignment_section(config_values)

        # Values should be properly quoted
        assert 'CLASSROOM_URL="https://classroom.github.com/test?param=value&other=123"' in section
        assert 'ASSIGNMENT_FILE="assignment (copy).ipynb"' in section

    def test_very_long_values(self):
        """
        Test handling of extremely long configuration values without truncation or errors.

        This test validates that the ConfigGenerator can handle very long URLs and paths
        (created by repeating path segments) without causing string processing errors,
        memory issues, or truncation of important configuration information.
        """
        generator = ConfigGenerator(Path("/test/config.conf"))

        long_url = 'https://classroom.github.com/' + \
            'very-long-path/' * 50 + 'assignment'

        config_values = {
            'CLASSROOM_URL': long_url,
            'TEMPLATE_REPO_URL': 'https://github.com/test/template',
            'GITHUB_ORGANIZATION': 'test-org',
            'MAIN_ASSIGNMENT_FILE': 'assignment.ipynb'
        }

        section = generator._generate_assignment_section(config_values)

        # Should handle long values without issues
        assert long_url in section

    def test_none_values_in_config(self):
        """
        Test resilience when configuration dictionary contains None values.

        This test ensures that the ConfigGenerator handles None values in configuration
        dictionaries without raising exceptions, maintaining system stability even when
        configuration parsing or user input produces None values for some settings.
        """
        generator = ConfigGenerator(Path("/test/config.conf"))

        config_values = {
            'CLASSROOM_URL': 'https://classroom.github.com/test',
            'TEMPLATE_REPO_URL': None,
            'GITHUB_ORGANIZATION': 'test-org',
            'MAIN_ASSIGNMENT_FILE': 'assignment.ipynb'
        }

        # Should not raise an exception
        section = generator._generate_assignment_section(config_values)
        assert isinstance(section, str)


class TestConfigGeneratorIntegration:
    """
    TestConfigGeneratorIntegration contains unit tests for complete integration scenarios
    and end-to-end configuration generation workflows. These tests verify that all
    components work together correctly to produce valid, complete configuration files
    for both secrets-enabled and secrets-disabled assignment setups.

    Test Cases:
    - test_complete_config_generation_with_secrets: Tests end-to-end generation with secrets enabled
    - test_complete_config_generation_without_secrets: Tests end-to-end generation with secrets disabled
    """

    @patch('classdock.config.generator.print_header')
    @patch('classdock.config.generator.print_success')
    def test_complete_config_generation_with_secrets(self, mock_print_success, mock_print_header):
        """
        Test complete end-to-end configuration file generation with secrets management enabled.

        This integration test verifies that a complete configuration file is properly generated
        when secrets are enabled, including all sections (header, assignment, secrets, workflow,
        advanced), proper secret token configuration, and correct workflow step settings for
        assignments that require separate instructor test repositories.
        """
        config_path = Path("/test/complete.conf")
        generator = ConfigGenerator(config_path)

        config_values = {
            'CLASSROOM_URL': 'https://classroom.github.com/classrooms/12345/assignments/data-analysis',
            'CLASSROOM_REPO_URL': 'https://github.com/cs101/classroom-fall25-data-analysis',
            'TEMPLATE_REPO_URL': 'https://github.com/cs101/data-analysis-template',
            'GITHUB_ORGANIZATION': 'cs101',
            'ASSIGNMENT_NAME': 'data-analysis',
            'MAIN_ASSIGNMENT_FILE': 'analysis.ipynb',
            'USE_SECRETS': 'true'
        }

        token_files = {
            'INSTRUCTOR_TESTS_TOKEN': 'instructor_token.txt',
            'DATABASE_ACCESS_TOKEN': 'db_token.txt'
        }

        token_validation = {
            'INSTRUCTOR_TESTS_TOKEN': True,
            'DATABASE_ACCESS_TOKEN': False
        }

        content_written = []

        def capture_write(content):
            content_written.append(content)

        with patch('builtins.open', mock_open()) as mock_file:
            mock_file().write = capture_write

            generator.create_config_file(
                config_values, token_files, token_validation)

            full_content = ''.join(content_written)

            # Verify complete configuration structure
            assert 'GitHub Classroom Assignment Configuration' in full_content
            assert 'ASSIGNMENT INFORMATION' in full_content
            assert 'SECRET MANAGEMENT' in full_content
            assert 'WORKFLOW CONFIGURATION' in full_content
            assert 'ADVANCED CONFIGURATION' in full_content

            # Verify assignment details
            assert 'CLASSROOM_URL="https://classroom.github.com/classrooms/12345/assignments/data-analysis"' in full_content
            assert 'ASSIGNMENT_NAME="data-analysis"' in full_content
            assert 'ASSIGNMENT_FILE="analysis.ipynb"' in full_content

            # Verify secrets configuration\n            assert 'STEP_MANAGE_SECRETS=true' in full_content\n            assert 'INSTRUCTOR_TESTS_TOKEN:Token for accessing instructor test repository:true' in full_content\n            assert 'DATABASE_ACCESS_TOKEN:DATABASE_ACCESS_TOKEN for assignment functionality:false' in full_content

    @patch('classdock.config.generator.print_header')
    @patch('classdock.config.generator.print_success')
    def test_complete_config_generation_without_secrets(self, mock_print_success, mock_print_header):
        """
        Test complete end-to-end configuration file generation with secrets management disabled.

        This integration test verifies that a complete configuration file is properly generated
        when secrets are disabled, ensuring that the secrets section is properly configured
        for assignments where tests are included in the template repository rather than requiring
        separate instructor repositories and secret token management.
        """
        config_path = Path("/test/no_secrets.conf")
        generator = ConfigGenerator(config_path)

        config_values = {
            'CLASSROOM_URL': 'https://classroom.github.com/classrooms/12345/assignments/simple-assignment',
            'TEMPLATE_REPO_URL': 'https://github.com/cs101/simple-template',
            'GITHUB_ORGANIZATION': 'cs101',
            'MAIN_ASSIGNMENT_FILE': 'main.py',
            'USE_SECRETS': 'false'
        }

        content_written = []

        def capture_write(content):
            content_written.append(content)

        with patch('builtins.open', mock_open()) as mock_file:
            mock_file().write = capture_write

            generator.create_config_file(config_values, {}, {})

            full_content = ''.join(content_written)

            # Verify secrets are disabled
            assert 'STEP_MANAGE_SECRETS=false' in full_content
            assert 'SECRETS_CONFIG=""' in full_content

            # Verify other sections are still present
            assert 'ASSIGNMENT INFORMATION' in full_content
            assert 'WORKFLOW CONFIGURATION' in full_content
            assert 'ADVANCED CONFIGURATION' in full_content


if __name__ == '__main__':
    pytest.main([__file__])
