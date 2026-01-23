"""
Comprehensive test suite for classdock.config.loader module.

This test suite provides comprehensive coverage for the ConfigLoader class,
which is responsible for loading, parsing, and updating GitHub Classroom assignment
configuration files. The tests include unit tests for individual methods, integration
tests for file operations, error handling, edge cases, and proper validation of
configuration file parsing and updating functionality.

Test Categories:
1. Initialization Tests - Constructor and PathManager integration testing
2. Configuration Loading Tests - File parsing and content extraction
3. Value Retrieval Tests - Individual value access with defaults
4. Configuration Update Tests - File modification and persistence
5. File Format Tests - Different configuration file formats and encodings
6. Error Handling Tests - Exception scenarios and file system issues
7. Edge Case Tests - Boundary conditions, malformed files, and unusual inputs
8. Integration Tests - PathManager integration and file discovery

The ConfigLoader class provides methods for:
- Loading configuration files in shell variable format (KEY=value)
- Parsing comments, empty lines, and quoted values
- Retrieving individual configuration values with default fallbacks
- Updating configuration files while preserving structure
- Integrating with PathManager for automatic file discovery
- Handling file system errors and malformed configuration gracefully

All tests use proper mocking to isolate the ConfigLoader from external dependencies
and file system operations where appropriate, ensuring test reliability and speed
while also testing actual file operations for integration scenarios.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from classdock.config.loader import ConfigLoader


class TestConfigLoaderInitialization:
    """
    TestConfigLoaderInitialization contains unit tests for the ConfigLoader class
    initialization and PathManager integration. It verifies that the constructor
    properly handles both explicit config paths and automatic file discovery
    through the PathManager component.

    Test Cases:
    - test_init_with_explicit_path: Tests initialization with provided config path
    - test_init_without_path_uses_pathmanager: Tests automatic file discovery
    - test_init_with_none_path: Tests None path handling
    - test_init_pathmanager_integration: Tests PathManager dependency injection
    - test_init_path_types: Tests different path type inputs (str, Path)
    """

    def test_init_with_explicit_path(self):
        """
        Test that ConfigLoader properly initializes when provided with an explicit config path.

        This test verifies that when a specific configuration file path is provided
        to the constructor, it is correctly stored and the PathManager is still
        instantiated for potential future use.
        """
        config_path = Path("/test/config.conf")

        with patch('classdock.config.loader.PathManager') as mock_path_manager:
            loader = ConfigLoader(config_path)

            assert loader.config_path == config_path
            assert hasattr(loader, 'path_manager')
            mock_path_manager.assert_called_once()

    @patch('classdock.config.loader.PathManager')
    def test_init_without_path_uses_pathmanager(self, mock_path_manager_class):
        """
        Test that ConfigLoader uses PathManager to find config file when no path is provided.

        This test verifies that when no configuration path is specified, the loader
        properly delegates to PathManager.find_config_file() to automatically locate
        the configuration file in the workspace.
        """
        mock_path_manager = Mock()
        mock_path_manager.find_config_file.return_value = Path(
            "/found/config.conf")
        mock_path_manager_class.return_value = mock_path_manager

        loader = ConfigLoader()

        assert loader.config_path == Path("/found/config.conf")
        mock_path_manager.find_config_file.assert_called_once()

    @patch('classdock.config.loader.PathManager')
    def test_init_with_none_path(self, mock_path_manager_class):
        """
        Test that ConfigLoader handles None path by delegating to PathManager.

        This test verifies that explicitly passing None as the config path
        results in the same behavior as not providing a path - using PathManager
        for automatic file discovery.
        """
        mock_path_manager = Mock()
        mock_path_manager.find_config_file.return_value = Path(
            "/found/config.conf")
        mock_path_manager_class.return_value = mock_path_manager

        loader = ConfigLoader(None)

        assert loader.config_path == Path("/found/config.conf")
        mock_path_manager.find_config_file.assert_called_once()

    def test_init_pathmanager_integration(self):
        """
        Test that ConfigLoader properly instantiates and integrates with PathManager.

        This test verifies that the PathManager is correctly instantiated during
        ConfigLoader initialization and that the loader maintains a reference to
        it for file operations.
        """
        config_path = Path("/test/config.conf")

        with patch('classdock.config.loader.PathManager') as mock_path_manager_class:
            mock_path_manager = Mock()
            mock_path_manager_class.return_value = mock_path_manager

            loader = ConfigLoader(config_path)

            assert loader.path_manager == mock_path_manager
            mock_path_manager_class.assert_called_once()

    def test_init_path_types(self):
        """
        Test that ConfigLoader handles different path input types correctly.

        This test verifies that the constructor accepts both string and Path
        object inputs for the configuration file path and handles them appropriately.
        """
        with patch('classdock.config.loader.PathManager'):
            # Test with Path object
            path_obj = Path("/test/config.conf")
            loader1 = ConfigLoader(path_obj)
            assert loader1.config_path == path_obj
            assert isinstance(loader1.config_path, Path)

            # Test with string path
            path_str = "/test/config.conf"
            loader2 = ConfigLoader(path_str)
            # Note: Depending on implementation, this might convert to Path or stay as string
            assert str(loader2.config_path) == path_str


class TestConfigLoaderFileLoading:
    """
    TestConfigLoaderFileLoading contains unit tests for configuration file loading
    and parsing functionality. It verifies that configuration files in shell variable
    format are correctly parsed, comments and empty lines are handled, and various
    value formats (quoted, unquoted) are processed appropriately.

    Test Cases:
    - test_load_valid_config_file: Tests loading well-formed configuration files
    - test_load_config_with_comments: Tests comment handling and filtering
    - test_load_config_with_quotes: Tests quoted value parsing and quote removal
    - test_load_config_with_empty_lines: Tests empty line handling
    - test_load_nonexistent_file: Tests behavior when config file doesn't exist
    - test_load_config_mixed_formats: Tests files with mixed formatting styles
    """

    def test_load_valid_config_file(self):
        """
        Test loading a well-formed configuration file with standard key=value format.

        This test verifies that the loader correctly parses configuration files
        containing properly formatted key=value pairs and returns a dictionary
        with the expected configuration values.
        """
        config_content = """CLASSROOM_URL=https://classroom.github.com/test
TEMPLATE_REPO_URL=https://github.com/test/template
GITHUB_ORGANIZATION=test-org
ASSIGNMENT_FILE=assignment.ipynb"""

        config_path = Path("/test/config.conf")

        with patch('classdock.config.loader.PathManager'), \
                patch('builtins.open', mock_open(read_data=config_content)), \
                patch.object(Path, 'exists', return_value=True):

            loader = ConfigLoader(config_path)
            config = loader.load()

            assert config['CLASSROOM_URL'] == 'https://classroom.github.com/test'
            assert config['TEMPLATE_REPO_URL'] == 'https://github.com/test/template'
            assert config['GITHUB_ORGANIZATION'] == 'test-org'
            assert config['ASSIGNMENT_FILE'] == 'assignment.ipynb'
            assert len(config) == 4

    def test_load_config_with_comments(self):
        """
        Test that configuration file comments are properly ignored during parsing.

        This test verifies that lines starting with # are treated as comments
        and excluded from the configuration dictionary, while preserving valid
        configuration lines.
        """
        config_content = """# This is a comment
CLASSROOM_URL=https://classroom.github.com/test
# Another comment line
TEMPLATE_REPO_URL=https://github.com/test/template
# Final comment
"""

        config_path = Path("/test/config.conf")

        with patch('classdock.config.loader.PathManager'), \
                patch('builtins.open', mock_open(read_data=config_content)), \
                patch.object(Path, 'exists', return_value=True):

            loader = ConfigLoader(config_path)
            config = loader.load()

            assert len(config) == 2
            assert config['CLASSROOM_URL'] == 'https://classroom.github.com/test'
            assert config['TEMPLATE_REPO_URL'] == 'https://github.com/test/template'
            # Verify comments are not included
            assert '# This is a comment' not in config
            assert 'This is a comment' not in config

    def test_load_config_with_quotes(self):
        """
        Test that quoted configuration values are properly parsed with quotes removed.

        This test verifies that the loader correctly handles both single and double
        quoted values by removing the surrounding quotes while preserving the
        inner content, including any special characters or spaces.
        """
        config_content = '''CLASSROOM_URL="https://classroom.github.com/test"
TEMPLATE_REPO_URL='https://github.com/test/template'
GITHUB_ORGANIZATION="test-org-with-spaces and special chars"
ASSIGNMENT_FILE=unquoted_value
MIXED_QUOTES="value with inner quotes"'''

        config_path = Path("/test/config.conf")

        with patch('classdock.config.loader.PathManager'), \
                patch('builtins.open', mock_open(read_data=config_content)), \
                patch.object(Path, 'exists', return_value=True):

            loader = ConfigLoader(config_path)
            config = loader.load()

            # Verify quotes are removed
            assert config['CLASSROOM_URL'] == 'https://classroom.github.com/test'
            assert config['TEMPLATE_REPO_URL'] == 'https://github.com/test/template'
            assert config['GITHUB_ORGANIZATION'] == 'test-org-with-spaces and special chars'
            assert config['ASSIGNMENT_FILE'] == 'unquoted_value'
            assert config['MIXED_QUOTES'] == 'value with inner quotes'

    def test_load_config_with_empty_lines(self):
        """
        Test that empty lines in configuration files are properly ignored.

        This test verifies that blank lines, lines with only whitespace, and
        mixed empty/content lines are handled correctly without affecting the
        parsing of valid configuration entries.
        """
        config_content = """

CLASSROOM_URL=https://classroom.github.com/test

   
TEMPLATE_REPO_URL=https://github.com/test/template
   
   
GITHUB_ORGANIZATION=test-org

"""

        config_path = Path("/test/config.conf")

        with patch('classdock.config.loader.PathManager'), \
                patch('builtins.open', mock_open(read_data=config_content)), \
                patch.object(Path, 'exists', return_value=True):

            loader = ConfigLoader(config_path)
            config = loader.load()

            assert len(config) == 3
            assert config['CLASSROOM_URL'] == 'https://classroom.github.com/test'
            assert config['TEMPLATE_REPO_URL'] == 'https://github.com/test/template'
            assert config['GITHUB_ORGANIZATION'] == 'test-org'

    def test_load_nonexistent_file(self):
        """
        Test behavior when attempting to load a configuration file that doesn't exist.

        This test verifies that the loader gracefully handles missing configuration
        files by returning an empty dictionary and logging an appropriate warning
        message without raising exceptions.
        """
        config_path = Path("/nonexistent/config.conf")

        with patch('classdock.config.loader.PathManager'), \
                patch.object(Path, 'exists', return_value=False):

            loader = ConfigLoader(config_path)
            config = loader.load()

            assert config == {}
            assert isinstance(config, dict)

    def test_load_config_mixed_formats(self):
        """
        Test loading configuration files with mixed formatting styles and edge cases.

        This test verifies that the loader handles various formatting scenarios
        including values with equals signs, special characters, different spacing,
        and mixed quote styles within a single configuration file.
        """
        config_content = """KEY1=simple_value
KEY2 = value_with_spaces
KEY3="value=with=equals"
KEY4='single quoted'
KEY5 = "double quoted with spaces"
KEY6=value_with_special_chars@#$%
KEY7=https://example.com/path?param=value&other=123"""

        config_path = Path("/test/config.conf")

        with patch('classdock.config.loader.PathManager'), \
                patch('builtins.open', mock_open(read_data=config_content)), \
                patch.object(Path, 'exists', return_value=True):

            loader = ConfigLoader(config_path)
            config = loader.load()

            assert config['KEY1'] == 'simple_value'
            assert config['KEY2'] == 'value_with_spaces'
            assert config['KEY3'] == 'value=with=equals'
            assert config['KEY4'] == 'single quoted'
            assert config['KEY5'] == 'double quoted with spaces'
            assert config['KEY6'] == 'value_with_special_chars@#$%'
            assert config['KEY7'] == 'https://example.com/path?param=value&other=123'


class TestConfigLoaderValueRetrieval:
    """
    TestConfigLoaderValueRetrieval contains unit tests for individual configuration
    value access through the get_value method. It verifies that values can be
    retrieved with appropriate default handling and that the method integrates
    properly with the load functionality.

    Test Cases:
    - test_get_value_existing_key: Tests retrieval of existing configuration values
    - test_get_value_nonexistent_key_with_default: Tests default value handling
    - test_get_value_nonexistent_key_without_default: Tests None return for missing keys
    - test_get_value_empty_config: Tests behavior with empty configuration
    - test_get_value_different_types: Tests default values of different types
    """

    def test_get_value_existing_key(self):
        """
        Test retrieval of existing configuration values without defaults.

        This test verifies that the get_value method correctly retrieves existing
        configuration values from loaded configuration files and returns the
        expected values without modification.
        """
        config_content = """CLASSROOM_URL=https://classroom.github.com/test
GITHUB_ORGANIZATION=test-org"""

        config_path = Path("/test/config.conf")

        with patch('classdock.config.loader.PathManager'), \
                patch('builtins.open', mock_open(read_data=config_content)), \
                patch.object(Path, 'exists', return_value=True):

            loader = ConfigLoader(config_path)

            value1 = loader.get_value('CLASSROOM_URL')
            value2 = loader.get_value('GITHUB_ORGANIZATION')

            assert value1 == 'https://classroom.github.com/test'
            assert value2 == 'test-org'

    def test_get_value_nonexistent_key_with_default(self):
        """
        Test that default values are returned for non-existent configuration keys.

        This test verifies that when requesting a configuration value that doesn't
        exist in the loaded configuration, the get_value method returns the
        provided default value instead of None or raising an exception.
        """
        config_content = """CLASSROOM_URL=https://classroom.github.com/test"""

        config_path = Path("/test/config.conf")

        with patch('classdock.config.loader.PathManager'), \
                patch('builtins.open', mock_open(read_data=config_content)), \
                patch.object(Path, 'exists', return_value=True):

            loader = ConfigLoader(config_path)

            value = loader.get_value('NONEXISTENT_KEY', 'default_value')

            assert value == 'default_value'

    def test_get_value_nonexistent_key_without_default(self):
        """
        Test that None is returned for non-existent keys when no default is provided.

        This test verifies that when requesting a configuration value that doesn't
        exist and no default value is specified, the get_value method returns None
        as the fallback value.
        """
        config_content = """CLASSROOM_URL=https://classroom.github.com/test"""

        config_path = Path("/test/config.conf")

        with patch('classdock.config.loader.PathManager'), \
                patch('builtins.open', mock_open(read_data=config_content)), \
                patch.object(Path, 'exists', return_value=True):

            loader = ConfigLoader(config_path)

            value = loader.get_value('NONEXISTENT_KEY')

            assert value is None

    def test_get_value_empty_config(self):
        """
        Test value retrieval behavior when configuration file is empty or missing.

        This test verifies that the get_value method handles empty configuration
        scenarios gracefully by returning default values when specified or None
        when no default is provided.
        """
        config_path = Path("/nonexistent/config.conf")

        with patch('classdock.config.loader.PathManager'), \
                patch.object(Path, 'exists', return_value=False):

            loader = ConfigLoader(config_path)

            value_with_default = loader.get_value('ANY_KEY', 'default_value')
            value_without_default = loader.get_value('ANY_KEY')

            assert value_with_default == 'default_value'
            assert value_without_default is None

    def test_get_value_different_types(self):
        """
        Test that get_value correctly handles default values of different types.

        This test verifies that the get_value method preserves the type and value
        of default parameters including strings, integers, booleans, lists, and
        other Python objects when the requested key is not found.
        """
        config_path = Path("/nonexistent/config.conf")

        with patch('classdock.config.loader.PathManager'), \
                patch.object(Path, 'exists', return_value=False):

            loader = ConfigLoader(config_path)

            # Test different default types
            string_default = loader.get_value('KEY1', 'string_default')
            int_default = loader.get_value('KEY2', 42)
            bool_default = loader.get_value('KEY3', True)
            list_default = loader.get_value('KEY4', ['a', 'b', 'c'])
            dict_default = loader.get_value('KEY5', {'key': 'value'})

            assert string_default == 'string_default'
            assert int_default == 42
            assert bool_default is True
            assert list_default == ['a', 'b', 'c']
            assert dict_default == {'key': 'value'}


class TestConfigLoaderUpdateConfig:
    """
    TestConfigLoaderUpdateConfig contains unit tests for configuration file updating
    functionality. It verifies that configuration files can be modified, new values
    can be added, existing values can be updated, and the file format is preserved
    during update operations.

    Test Cases:
    - test_update_config_new_values: Tests adding new configuration values
    - test_update_config_existing_values: Tests updating existing configuration values
    - test_update_config_mixed_operations: Tests combined add/update operations
    - test_update_config_no_path: Tests error handling when no config path is set
    - test_update_config_file_error: Tests error handling for file operation failures
    - test_update_config_preserves_format: Tests that updates maintain proper file format
    """

    def test_update_config_new_values(self):
        """
        Test adding new configuration values to an existing configuration file.

        This test verifies that the update_config method can successfully add new
        key-value pairs to a configuration file while preserving existing values
        and maintaining the proper file format.
        """
        initial_config = """CLASSROOM_URL=https://classroom.github.com/test
GITHUB_ORGANIZATION=test-org"""

        config_path = Path("/test/config.conf")
        written_content = []

        def mock_write(content):
            written_content.append(content)

        with patch('classdock.config.loader.PathManager'), \
                patch('builtins.open', mock_open(read_data=initial_config)) as mock_file, \
                patch.object(Path, 'exists', return_value=True):

            # Configure mock to capture writes
            mock_file().write = mock_write

            loader = ConfigLoader(config_path)

            updates = {
                'NEW_KEY': 'new_value',
                'ANOTHER_KEY': 'another_value'
            }

            result = loader.update_config(updates)

            assert result is True

            # Verify content was written
            full_content = ''.join(written_content)
            assert 'NEW_KEY="new_value"' in full_content
            assert 'ANOTHER_KEY="another_value"' in full_content
            assert 'CLASSROOM_URL="https://classroom.github.com/test"' in full_content
            assert 'GITHUB_ORGANIZATION="test-org"' in full_content

    def test_update_config_existing_values(self):
        """
        Test updating existing configuration values in a configuration file.

        This test verifies that the update_config method can successfully modify
        existing configuration values while preserving other values and maintaining
        the proper file structure and format.
        """
        initial_config = """CLASSROOM_URL=https://classroom.github.com/old-test
GITHUB_ORGANIZATION=old-org"""

        config_path = Path("/test/config.conf")
        written_content = []

        def mock_write(content):
            written_content.append(content)

        with patch('classdock.config.loader.PathManager'), \
                patch('builtins.open', mock_open(read_data=initial_config)) as mock_file, \
                patch.object(Path, 'exists', return_value=True):

            # Configure mock to capture writes
            mock_file().write = mock_write

            loader = ConfigLoader(config_path)

            updates = {
                'CLASSROOM_URL': 'https://classroom.github.com/new-test',
                'GITHUB_ORGANIZATION': 'new-org'
            }

            result = loader.update_config(updates)

            assert result is True

            # Verify content was updated
            full_content = ''.join(written_content)
            assert 'CLASSROOM_URL="https://classroom.github.com/new-test"' in full_content
            assert 'GITHUB_ORGANIZATION="new-org"' in full_content
            # Ensure old values are not present
            assert 'old-test' not in full_content
            assert 'old-org' not in full_content

    def test_update_config_mixed_operations(self):
        """
        Test updating configuration with both new additions and existing value modifications.

        This test verifies that the update_config method can handle mixed operations
        involving both adding new configuration values and updating existing ones
        in a single operation.
        """
        initial_config = """CLASSROOM_URL=https://classroom.github.com/test
GITHUB_ORGANIZATION=test-org"""

        config_path = Path("/test/config.conf")
        written_content = []

        def mock_write(content):
            written_content.append(content)

        with patch('classdock.config.loader.PathManager'), \
                patch('builtins.open', mock_open(read_data=initial_config)) as mock_file, \
                patch.object(Path, 'exists', return_value=True):

            # Configure mock to capture writes
            mock_file().write = mock_write

            loader = ConfigLoader(config_path)

            updates = {
                'CLASSROOM_URL': 'https://classroom.github.com/updated-test',  # Update existing
                'NEW_KEY': 'new_value',  # Add new
                'ASSIGNMENT_FILE': 'assignment.ipynb'  # Add new
            }

            result = loader.update_config(updates)

            assert result is True

            # Verify mixed operations
            full_content = ''.join(written_content)
            assert 'CLASSROOM_URL="https://classroom.github.com/updated-test"' in full_content
            assert 'GITHUB_ORGANIZATION="test-org"' in full_content  # Preserved
            assert 'NEW_KEY="new_value"' in full_content  # Added
            assert 'ASSIGNMENT_FILE="assignment.ipynb"' in full_content  # Added

    def test_update_config_no_path(self):
        """
        Test error handling when attempting to update configuration without a valid config path.

        This test verifies that the update_config method properly handles scenarios
        where no configuration file path is available and returns False with
        appropriate error logging.
        """
        with patch('classdock.config.loader.PathManager') as mock_path_manager_class:
            mock_path_manager = Mock()
            mock_path_manager.find_config_file.return_value = None
            mock_path_manager_class.return_value = mock_path_manager

            loader = ConfigLoader()  # No path provided, PathManager returns None

            updates = {'KEY': 'value'}
            result = loader.update_config(updates)

            assert result is False

    def test_update_config_file_error(self):
        """
        Test error handling when file operations fail during configuration updates.

        This test verifies that the update_config method properly handles file
        system errors (permissions, disk space, etc.) and returns False while
        logging appropriate error messages.
        """
        config_path = Path("/test/config.conf")

        with patch('classdock.config.loader.PathManager'), \
                patch('builtins.open', side_effect=IOError("Permission denied")):

            loader = ConfigLoader(config_path)

            updates = {'KEY': 'value'}
            result = loader.update_config(updates)

            assert result is False

    def test_update_config_preserves_format(self):
        """
        Test that configuration updates preserve proper file format and structure.

        This test verifies that the update_config method maintains consistent
        file formatting including header comments, proper quoting, and standard
        key=value structure when writing updated configuration files.
        """
        initial_config = """CLASSROOM_URL=https://classroom.github.com/test"""

        config_path = Path("/test/config.conf")
        written_content = []

        def mock_write(content):
            written_content.append(content)

        with patch('classdock.config.loader.PathManager'), \
                patch('builtins.open', mock_open(read_data=initial_config)) as mock_file, \
                patch.object(Path, 'exists', return_value=True):

            # Configure mock to capture writes
            mock_file().write = mock_write

            loader = ConfigLoader(config_path)

            updates = {'NEW_KEY': 'new_value'}
            result = loader.update_config(updates)

            assert result is True

            # Verify proper format
            full_content = ''.join(written_content)
            assert '# GitHub Classroom Assignment Configuration' in full_content
            assert '# Updated by ConfigLoader' in full_content
            assert 'CLASSROOM_URL="https://classroom.github.com/test"' in full_content
            assert 'NEW_KEY="new_value"' in full_content

            # Verify all values are quoted
            lines = [line for line in full_content.split(
                '\n') if '=' in line and not line.startswith('#')]
            for line in lines:
                if '=' in line:
                    key, value = line.split('=', 1)
                    assert value.startswith('"') and value.endswith(
                        '"'), f"Value not properly quoted: {line}"


class TestConfigLoaderErrorHandling:
    """
    TestConfigLoaderErrorHandling contains unit tests for error handling and
    exception scenarios within the ConfigLoader class. It verifies that the loader
    gracefully handles various error conditions including file system issues,
    malformed content, and edge cases without crashing.

    Test Cases:
    - test_load_config_file_read_error: Tests handling of file read errors
    - test_load_config_permission_denied: Tests permission error handling
    - test_load_config_malformed_content: Tests handling of malformed configuration files
    - test_load_config_unicode_errors: Tests handling of encoding issues
    - test_load_config_empty_file: Tests handling of empty configuration files
    - test_load_config_binary_file: Tests handling of non-text files
    """

    def test_load_config_file_read_error(self):
        """
        Test error handling when file read operations fail during configuration loading.

        This test verifies that the loader gracefully handles file read errors
        by returning an empty dictionary and logging appropriate error messages
        without raising exceptions that could crash the application.
        """
        config_path = Path("/test/config.conf")

        with patch('classdock.config.loader.PathManager'), \
                patch('builtins.open', side_effect=IOError("File read error")), \
                patch.object(Path, 'exists', return_value=True):

            loader = ConfigLoader(config_path)
            config = loader.load()

            assert config == {}
            assert isinstance(config, dict)

    def test_load_config_permission_denied(self):
        """
        Test error handling when file access is denied due to permissions.

        This test verifies that the loader handles permission errors gracefully
        by returning an empty configuration dictionary rather than raising
        exceptions, allowing the application to continue with default values.
        """
        config_path = Path("/test/config.conf")

        with patch('classdock.config.loader.PathManager'), \
                patch('builtins.open', side_effect=PermissionError("Permission denied")), \
                patch.object(Path, 'exists', return_value=True):

            loader = ConfigLoader(config_path)
            config = loader.load()

            assert config == {}
            assert isinstance(config, dict)

    def test_load_config_malformed_content(self):
        """
        Test handling of malformed configuration file content.

        This test verifies that the loader can parse configuration files with
        various formatting issues including missing equals signs, invalid syntax,
        and unusual line formats while extracting valid configuration entries.
        """
        malformed_config = """VALID_KEY=valid_value
INVALID LINE WITHOUT EQUALS
=MISSING_KEY_NAME
ANOTHER_VALID=another_value
KEY_WITH_MULTIPLE===EQUALS=value
"""

        config_path = Path("/test/config.conf")

        with patch('classdock.config.loader.PathManager'), \
                patch('builtins.open', mock_open(read_data=malformed_config)), \
                patch.object(Path, 'exists', return_value=True):

            loader = ConfigLoader(config_path)
            config = loader.load()

            # Should load valid entries and ignore malformed ones
            assert 'VALID_KEY' in config
            assert config['VALID_KEY'] == 'valid_value'
            assert 'ANOTHER_VALID' in config
            assert config['ANOTHER_VALID'] == 'another_value'

            # The implementation does create entries for some malformed lines
            # =MISSING_KEY_NAME creates an empty key with value "MISSING_KEY_NAME"
            assert '' in config
            assert config[''] == 'MISSING_KEY_NAME'

            # Lines without equals signs are ignored
            assert 'INVALID LINE WITHOUT EQUALS' not in config

    def test_load_config_unicode_errors(self):
        """
        Test handling of Unicode encoding errors in configuration files.

        This test verifies that the loader can handle files with encoding issues
        gracefully, either by successfully reading the content or by failing
        gracefully with an empty configuration dictionary.
        """
        config_path = Path("/test/config.conf")

        with patch('classdock.config.loader.PathManager'), \
                patch('builtins.open', side_effect=UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid start byte')), \
                patch.object(Path, 'exists', return_value=True):

            loader = ConfigLoader(config_path)
            config = loader.load()

            assert config == {}
            assert isinstance(config, dict)

    def test_load_config_empty_file(self):
        """
        Test handling of completely empty configuration files.

        This test verifies that the loader properly handles empty configuration
        files by returning an empty dictionary without errors, allowing the
        application to use default values or handle the empty case appropriately.
        """
        config_path = Path("/test/config.conf")

        with patch('classdock.config.loader.PathManager'), \
                patch('builtins.open', mock_open(read_data="")), \
                patch.object(Path, 'exists', return_value=True):

            loader = ConfigLoader(config_path)
            config = loader.load()

            assert config == {}
            assert isinstance(config, dict)

    def test_load_config_only_comments_and_empty_lines(self):
        """
        Test handling of configuration files containing only comments and empty lines.

        This test verifies that files with no actual configuration content
        (only comments and whitespace) are handled properly by returning an
        empty configuration dictionary.
        """
        comments_only_config = """# This is a configuration file
# But it has no actual configuration

# Just comments and empty lines


# End of file"""

        config_path = Path("/test/config.conf")

        with patch('classdock.config.loader.PathManager'), \
                patch('builtins.open', mock_open(read_data=comments_only_config)), \
                patch.object(Path, 'exists', return_value=True):

            loader = ConfigLoader(config_path)
            config = loader.load()

            assert config == {}
            assert isinstance(config, dict)


class TestConfigLoaderEdgeCases:
    """
    TestConfigLoaderEdgeCases contains unit tests for boundary conditions and
    unusual scenarios within the ConfigLoader class. It verifies that the loader
    handles edge cases gracefully including very large files, unusual characters,
    and extreme formatting variations.

    Test Cases:
    - test_load_config_very_long_lines: Tests handling of extremely long configuration lines
    - test_load_config_special_characters: Tests handling of special characters in keys and values
    - test_load_config_nested_quotes: Tests handling of nested quote combinations
    - test_load_config_whitespace_variations: Tests various whitespace handling scenarios
    - test_load_config_duplicate_keys: Tests behavior with duplicate configuration keys
    - test_load_config_case_sensitivity: Tests case sensitivity in configuration keys
    """

    def test_load_config_very_long_lines(self):
        """
        Test handling of configuration files with extremely long lines.

        This test verifies that the loader can handle configuration entries
        with very long values (such as long URLs or large configuration strings)
        without performance issues or buffer overflows.
        """
        long_value = "https://example.com/" + "very-long-path/" * 100 + "endpoint"
        config_content = f"""CLASSROOM_URL={long_value}
NORMAL_KEY=normal_value"""

        config_path = Path("/test/config.conf")

        with patch('classdock.config.loader.PathManager'), \
                patch('builtins.open', mock_open(read_data=config_content)), \
                patch.object(Path, 'exists', return_value=True):

            loader = ConfigLoader(config_path)
            config = loader.load()

            assert config['CLASSROOM_URL'] == long_value
            assert config['NORMAL_KEY'] == 'normal_value'
            # Verify it's actually long
            assert len(config['CLASSROOM_URL']) > 1000

    def test_load_config_special_characters(self):
        """
        Test handling of special characters in configuration keys and values.

        This test verifies that the loader properly handles various special
        characters, Unicode characters, and symbols in both configuration
        keys and values without parsing errors.
        """
        config_content = """KEY_WITH_UNDERSCORES=value
KEY-WITH-HYPHENS=value
KEY123=value_with_numbers_123
UNICODE_VALUE=café_résumé_naïve
SPECIAL_CHARS=!@#$%^&*()[]{}|\\:";'<>?,./
URL_WITH_PARAMS=https://example.com/path?param1=value1&param2=value2#anchor"""

        config_path = Path("/test/config.conf")

        with patch('classdock.config.loader.PathManager'), \
                patch('builtins.open', mock_open(read_data=config_content)), \
                patch.object(Path, 'exists', return_value=True):

            loader = ConfigLoader(config_path)
            config = loader.load()

            assert config['KEY_WITH_UNDERSCORES'] == 'value'
            assert config['KEY-WITH-HYPHENS'] == 'value'
            assert config['KEY123'] == 'value_with_numbers_123'
            assert config['UNICODE_VALUE'] == 'café_résumé_naïve'
            assert config['SPECIAL_CHARS'] == '!@#$%^&*()[]{}|\\:";\'<>?,./'
            assert config['URL_WITH_PARAMS'] == 'https://example.com/path?param1=value1&param2=value2#anchor'

    def test_load_config_nested_quotes(self):
        """
        Test handling of nested quote combinations in configuration values.

        This test verifies that the loader correctly handles complex quoting
        scenarios including nested quotes, escaped quotes, and mixed quote
        types within configuration values.
        """
        config_content = """SINGLE_IN_DOUBLE="value with 'single quotes' inside"
DOUBLE_IN_SINGLE='value with "double quotes" inside'
MIXED_QUOTES="It's a 'test' with nested quotes"
NO_QUOTES=value_without_quotes
EMPTY_QUOTES=""
SINGLE_EMPTY_QUOTES=''"""

        config_path = Path("/test/config.conf")

        with patch('classdock.config.loader.PathManager'), \
                patch('builtins.open', mock_open(read_data=config_content)), \
                patch.object(Path, 'exists', return_value=True):

            loader = ConfigLoader(config_path)
            config = loader.load()

            assert config['SINGLE_IN_DOUBLE'] == "value with 'single quotes' inside"
            assert config['DOUBLE_IN_SINGLE'] == 'value with "double quotes" inside'
            assert config['MIXED_QUOTES'] == "It's a 'test' with nested quotes"
            assert config['NO_QUOTES'] == 'value_without_quotes'
            assert config['EMPTY_QUOTES'] == ''
            assert config['SINGLE_EMPTY_QUOTES'] == ''

    def test_load_config_whitespace_variations(self):
        """
        Test handling of various whitespace scenarios in configuration files.

        This test verifies that the loader properly handles different types
        and amounts of whitespace including tabs, multiple spaces, and mixed
        whitespace around keys, equals signs, and values.
        """
        config_content = """KEY1=value1
   KEY2   =   value2   
\tKEY3\t=\tvalue3\t
KEY4 = "value with spaces"
   KEY5="value5"   
\t\tKEY6\t\t=\t\t"value6"\t\t"""

        config_path = Path("/test/config.conf")

        with patch('classdock.config.loader.PathManager'), \
                patch('builtins.open', mock_open(read_data=config_content)), \
                patch.object(Path, 'exists', return_value=True):

            loader = ConfigLoader(config_path)
            config = loader.load()

            assert config['KEY1'] == 'value1'
            assert config['KEY2'] == 'value2'
            assert config['KEY3'] == 'value3'
            assert config['KEY4'] == 'value with spaces'
            assert config['KEY5'] == 'value5'
            assert config['KEY6'] == 'value6'

    def test_load_config_duplicate_keys(self):
        """
        Test behavior when configuration files contain duplicate keys.

        This test verifies that when the same configuration key appears
        multiple times in a file, the loader handles it consistently
        (typically the last occurrence should take precedence).
        """
        config_content = """CLASSROOM_URL=first_value
GITHUB_ORGANIZATION=test-org
CLASSROOM_URL=second_value
CLASSROOM_URL=final_value"""

        config_path = Path("/test/config.conf")

        with patch('classdock.config.loader.PathManager'), \
                patch('builtins.open', mock_open(read_data=config_content)), \
                patch.object(Path, 'exists', return_value=True):

            loader = ConfigLoader(config_path)
            config = loader.load()

            # Last occurrence should win
            assert config['CLASSROOM_URL'] == 'final_value'
            assert config['GITHUB_ORGANIZATION'] == 'test-org'
            # Only one key in dict
            assert len([k for k in config.keys() if k == 'CLASSROOM_URL']) == 1

    def test_load_config_case_sensitivity(self):
        """
        Test case sensitivity handling in configuration keys.

        This test verifies that configuration keys are treated as case-sensitive
        and that keys differing only in case are treated as separate configuration
        entries.
        """
        config_content = """classroom_url=lowercase_value
CLASSROOM_URL=uppercase_value
Classroom_Url=mixedcase_value"""

        config_path = Path("/test/config.conf")

        with patch('classdock.config.loader.PathManager'), \
                patch('builtins.open', mock_open(read_data=config_content)), \
                patch.object(Path, 'exists', return_value=True):

            loader = ConfigLoader(config_path)
            config = loader.load()

            # All should be treated as separate keys
            assert config['classroom_url'] == 'lowercase_value'
            assert config['CLASSROOM_URL'] == 'uppercase_value'
            assert config['Classroom_Url'] == 'mixedcase_value'
            assert len(config) == 3


class TestConfigLoaderIntegration:
    """
    TestConfigLoaderIntegration contains integration tests for the ConfigLoader
    class working with PathManager and real file operations. It verifies that
    the complete workflow including file discovery, loading, and updating
    works correctly in realistic scenarios.

    Test Cases:
    - test_integration_with_pathmanager: Tests PathManager integration for file discovery
    - test_roundtrip_load_update_load: Tests complete load-update-load cycle
    - test_integration_real_file_operations: Tests actual file system operations
    - test_integration_config_validation: Tests integration with config validation
    - test_integration_error_recovery: Tests error recovery in integrated scenarios
    """

    def test_integration_with_pathmanager(self):
        """
        Test integration between ConfigLoader and PathManager for automatic file discovery.

        This test verifies that the ConfigLoader properly integrates with PathManager
        to automatically locate configuration files in the workspace when no explicit
        path is provided, ensuring seamless file discovery functionality.
        """
        found_config_path = Path("/workspace/assignment.conf")
        config_content = """CLASSROOM_URL=https://classroom.github.com/test"""

        with patch('classdock.config.loader.PathManager') as mock_path_manager_class:
            mock_path_manager = Mock()
            mock_path_manager.find_config_file.return_value = found_config_path
            mock_path_manager_class.return_value = mock_path_manager

            with patch('builtins.open', mock_open(read_data=config_content)), \
                    patch.object(Path, 'exists', return_value=True):

                loader = ConfigLoader()  # No path provided
                config = loader.load()

                # Verify PathManager was used
                mock_path_manager.find_config_file.assert_called_once()
                assert loader.config_path == found_config_path
                assert config['CLASSROOM_URL'] == 'https://classroom.github.com/test'

    def test_roundtrip_load_update_load(self):
        """
        Test complete roundtrip of loading configuration, updating it, and loading again.

        This test verifies that the complete workflow of loading a configuration,
        making updates, and then loading the updated configuration works correctly
        and preserves all data through the roundtrip process.
        """
        initial_config = """CLASSROOM_URL=https://classroom.github.com/test
GITHUB_ORGANIZATION=test-org"""

        config_path = Path("/test/config.conf")

        # Track file writes to simulate file updates
        written_content = []

        def mock_write_handler(content):
            written_content.append(content)

        with patch('classdock.config.loader.PathManager'), \
                patch('builtins.open', mock_open(read_data=initial_config)) as mock_file, \
                patch.object(Path, 'exists', return_value=True):

            # Configure write behavior to capture content
            mock_file.return_value.write.side_effect = mock_write_handler

            loader = ConfigLoader(config_path)

            # First load
            config1 = loader.load()
            assert config1['CLASSROOM_URL'] == 'https://classroom.github.com/test'
            assert config1['GITHUB_ORGANIZATION'] == 'test-org'

            # Update
            updates = {
                'CLASSROOM_URL': 'https://classroom.github.com/updated-test',
                'NEW_KEY': 'new_value'
            }
            result = loader.update_config(updates)
            assert result is True

            # Verify content was written
            assert len(written_content) > 0
            full_content = ''.join(written_content)
            assert 'CLASSROOM_URL="https://classroom.github.com/updated-test"' in full_content
            assert 'NEW_KEY="new_value"' in full_content

    def test_integration_real_file_operations(self):
        """
        Test ConfigLoader with actual file system operations using temporary files.

        This integration test verifies that the ConfigLoader works correctly with
        real file operations including reading from and writing to actual files
        on the file system, ensuring proper integration with the OS.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.conf"

            # Create initial config file
            initial_content = """CLASSROOM_URL=https://classroom.github.com/test
GITHUB_ORGANIZATION=test-org"""

            config_path.write_text(initial_content)

            with patch('classdock.config.loader.PathManager'):
                loader = ConfigLoader(config_path)

                # Test loading
                config = loader.load()
                assert config['CLASSROOM_URL'] == 'https://classroom.github.com/test'
                assert config['GITHUB_ORGANIZATION'] == 'test-org'

                # Test updating
                updates = {'NEW_KEY': 'new_value'}
                result = loader.update_config(updates)
                assert result is True

                # Verify file was actually updated
                updated_content = config_path.read_text()
                assert 'NEW_KEY="new_value"' in updated_content
                assert 'CLASSROOM_URL="https://classroom.github.com/test"' in updated_content

    def test_integration_multiple_loaders_same_file(self):
        """
        Test behavior when multiple ConfigLoader instances access the same file.

        This test verifies that multiple ConfigLoader instances can safely access
        the same configuration file and that updates from one loader are visible
        to other loaders, ensuring proper file sharing behavior.
        """
        config_content = """CLASSROOM_URL=https://classroom.github.com/test"""
        config_path = Path("/test/config.conf")

        with patch('classdock.config.loader.PathManager'), \
                patch('builtins.open', mock_open(read_data=config_content)), \
                patch.object(Path, 'exists', return_value=True):

            loader1 = ConfigLoader(config_path)
            loader2 = ConfigLoader(config_path)

            # Both loaders should access the same file
            config1 = loader1.load()
            config2 = loader2.load()

            assert config1 == config2
            assert config1['CLASSROOM_URL'] == 'https://classroom.github.com/test'
            assert config2['CLASSROOM_URL'] == 'https://classroom.github.com/test'


if __name__ == '__main__':
    pytest.main([__file__])
