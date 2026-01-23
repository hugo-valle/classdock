"""
Test suite for the configuration management system.

Tests configuration loading, validation, and generation.
"""

from pathlib import Path
import pytest

from classdock.config.loader import ConfigLoader
from classdock.config.validator import ConfigValidator
from classdock.config.generator import ConfigGenerator


class TestConfigLoader:
    """Test configuration loading functionality."""

    def test_load_valid_config(self, test_config_data, temp_config_file):
        """Test loading a valid configuration file."""
        loader = ConfigLoader(temp_config_file)
        config = loader.load()

        assert config is not None
        assert config['CLASSROOM_URL'] == test_config_data['CLASSROOM_URL']
        assert config['TEMPLATE_REPO_URL'] == test_config_data['TEMPLATE_REPO_URL']
        assert config['GITHUB_ORGANIZATION'] == test_config_data['GITHUB_ORGANIZATION']

    def test_load_nonexistent_config(self):
        """Test loading a non-existent configuration file."""
        loader = ConfigLoader(Path("/nonexistent/config.conf"))
        config = loader.load()

        assert config == {}

    def test_get_value_with_default(self, temp_config_file):
        """Test getting configuration values with defaults."""
        loader = ConfigLoader(temp_config_file)

        # Test existing value
        value = loader.get_value('CLASSROOM_URL')
        assert value is not None

        # Test non-existing value with default
        value = loader.get_value('NONEXISTENT_KEY', 'default_value')
        assert value == 'default_value'

    def test_update_config(self, temp_config_file):
        """Test updating configuration values."""
        loader = ConfigLoader(temp_config_file)

        updates = {
            'NEW_KEY': 'new_value',
            'CLASSROOM_URL': 'updated_url'
        }

        success = loader.update_config(updates)
        assert success is True

        # Verify updates
        updated_config = loader.load()
        assert updated_config['NEW_KEY'] == 'new_value'
        assert updated_config['CLASSROOM_URL'] == 'updated_url'

    def test_load_malformed_config(self, temp_directory):
        """Test loading a malformed configuration file."""
        malformed_file = temp_directory / "malformed.conf"
        with open(malformed_file, 'w') as f:
            f.write("INVALID LINE WITHOUT EQUALS\n")
            f.write("VALID_KEY=valid_value\n")
            f.write("=INVALID_EQUALS_FORMAT\n")

        loader = ConfigLoader(malformed_file)
        config = loader.load()

        # Should load valid lines and skip invalid ones
        assert 'VALID_KEY' in config
        assert config['VALID_KEY'] == 'valid_value'


class TestConfigValidator:
    """Test configuration validation functionality."""

    def test_validate_github_url(self):
        """Test GitHub URL validation."""
        # Valid URLs
        assert ConfigValidator.validate_github_url(
            "https://github.com/user/repo")[0] is True
        assert ConfigValidator.validate_github_url(
            "https://classroom.github.com/classrooms/123/assignments/test")[0] is True

        # Invalid URLs
        assert ConfigValidator.validate_github_url("")[0] is False
        assert ConfigValidator.validate_github_url("invalid-url")[0] is False
        assert ConfigValidator.validate_github_url(
            "http://github.com/user/repo")[0] is False  # http not https

    def test_validate_organization(self):
        """Test GitHub organization validation."""
        # Valid organizations
        assert ConfigValidator.validate_organization("valid-org")[0] is True
        assert ConfigValidator.validate_organization("ValidOrg123")[0] is True
        assert ConfigValidator.validate_organization("a")[0] is True

        # Invalid organizations
        assert ConfigValidator.validate_organization("")[0] is False
        assert ConfigValidator.validate_organization("invalid_org!")[
            0] is False
        assert ConfigValidator.validate_organization("-invalid")[0] is False
        assert ConfigValidator.validate_organization("invalid-")[0] is False

    def test_validate_assignment_name(self):
        """Test assignment name validation."""
        # Valid names (including empty)
        assert ConfigValidator.validate_assignment_name("")[0] is True
        assert ConfigValidator.validate_assignment_name(
            "valid-assignment")[0] is True
        assert ConfigValidator.validate_assignment_name("assignment_123")[
            0] is True

        # Invalid names
        assert ConfigValidator.validate_assignment_name("invalid!name")[
            0] is False
        assert ConfigValidator.validate_assignment_name("-invalid")[0] is False

    def test_validate_file_path(self):
        """Test file path validation."""
        # Valid file paths
        assert ConfigValidator.validate_file_path(
            "assignment.ipynb")[0] is True
        assert ConfigValidator.validate_file_path("main.py")[0] is True
        assert ConfigValidator.validate_file_path("homework.cpp")[0] is True
        assert ConfigValidator.validate_file_path("script.sql")[0] is True

        # Invalid file paths
        assert ConfigValidator.validate_file_path("")[0] is False
        assert ConfigValidator.validate_file_path("file.invalid")[0] is False
        assert ConfigValidator.validate_file_path("no_extension")[0] is False

    def test_validate_required_fields(self):
        """Test required fields validation."""
        # Complete config
        complete_config = {
            'CLASSROOM_URL': 'https://classroom.github.com/test',
            'TEMPLATE_REPO_URL': 'https://github.com/test/template',
            'GITHUB_ORGANIZATION': 'test-org',
            'ASSIGNMENT_FILE': 'assignment.ipynb'
        }
        missing = ConfigValidator.validate_required_fields(complete_config)
        assert len(missing) == 0

        # Missing fields
        incomplete_config = {
            'CLASSROOM_URL': 'https://classroom.github.com/test'
        }
        missing = ConfigValidator.validate_required_fields(incomplete_config)
        assert len(missing) == 3
        assert 'TEMPLATE_REPO_URL' in missing
        assert 'GITHUB_ORGANIZATION' in missing
        assert 'STUDENT_FILES or ASSIGNMENT_FILE' in missing

    def test_validate_full_config(self, test_config_data):
        """Test full configuration validation."""
        # Valid config
        valid_config = {
            'CLASSROOM_URL': 'https://classroom.github.com/classrooms/123/assignments/test',
            'TEMPLATE_REPO_URL': 'https://github.com/test/template',
            'GITHUB_ORGANIZATION': 'test-org',
            'ASSIGNMENT_FILE': 'assignment.ipynb'
        }
        is_valid, errors = ConfigValidator.validate_full_config(valid_config)
        assert is_valid is True
        assert len(errors) == 0

        # Invalid config
        invalid_config = {
            'CLASSROOM_URL': 'invalid-url',
            'TEMPLATE_REPO_URL': 'also-invalid',
            'GITHUB_ORGANIZATION': 'invalid!org',
            'ASSIGNMENT_FILE': 'invalid.xyz'
        }
        is_valid, errors = ConfigValidator.validate_full_config(invalid_config)
        assert is_valid is False
        assert len(errors) > 0


class TestConfigGenerator:
    """Test configuration file generation."""

    def test_create_config_file(self, temp_directory):
        """Test configuration file creation."""
        config_file = temp_directory / "test_assignment.conf"
        generator = ConfigGenerator(config_file)

        config_values = {
            'CLASSROOM_URL': 'https://classroom.github.com/test',
            'TEMPLATE_REPO_URL': 'https://github.com/test/template',
            'GITHUB_ORGANIZATION': 'test-org',
            'MAIN_ASSIGNMENT_FILE': 'assignment.ipynb',
            'USE_SECRETS': 'true'
        }

        token_files = {
            'INSTRUCTOR_TESTS_TOKEN': 'instructor_token.txt'
        }

        token_validation = {
            'INSTRUCTOR_TESTS_TOKEN': True
        }

        generator.create_config_file(
            config_values, token_files, token_validation)

        # Verify file was created
        assert config_file.exists()

        # Verify content
        content = config_file.read_text()
        assert 'CLASSROOM_URL="https://classroom.github.com/test"' in content
        assert 'TEMPLATE_REPO_URL="https://github.com/test/template"' in content
        assert 'GITHUB_ORGANIZATION="test-org"' in content
        assert 'ASSIGNMENT_FILE="assignment.ipynb"' in content

    def test_config_file_sections(self, temp_directory):
        """Test that all configuration sections are generated."""
        config_file = temp_directory / "test_sections.conf"
        generator = ConfigGenerator(config_file)

        config_values = {
            'CLASSROOM_URL': 'https://classroom.github.com/test',
            'TEMPLATE_REPO_URL': 'https://github.com/test/template',
            'GITHUB_ORGANIZATION': 'test-org',
            'MAIN_ASSIGNMENT_FILE': 'assignment.ipynb',
            'USE_SECRETS': 'false'
        }

        generator.create_config_file(config_values, {}, {})

        content = config_file.read_text()

        # Check for required sections
        assert 'ASSIGNMENT INFORMATION' in content
        assert 'SECRET MANAGEMENT' in content
        assert 'WORKFLOW CONFIGURATION' in content
        assert 'ADVANCED CONFIGURATION' in content

        # Check for specific settings
        assert 'STEP_MANAGE_SECRETS=false' in content
        assert 'LOG_LEVEL=INFO' in content
        assert 'DEFAULT_DRY_RUN=false' in content


class TestConfigIntegration:
    """Test integration between configuration components."""

    def test_loader_validator_integration(self, temp_config_file):
        """Test that loader and validator work together."""
        loader = ConfigLoader(temp_config_file)
        config = loader.load()

        is_valid, errors = ConfigValidator.validate_full_config(config)
        assert is_valid is True
        assert len(errors) == 0

    def test_generator_loader_roundtrip(self, temp_directory):
        """Test generating and then loading a config file."""
        config_file = temp_directory / "roundtrip.conf"
        generator = ConfigGenerator(config_file)

        original_values = {
            'CLASSROOM_URL': 'https://classroom.github.com/test',
            'TEMPLATE_REPO_URL': 'https://github.com/test/template',
            'GITHUB_ORGANIZATION': 'test-org',
            'MAIN_ASSIGNMENT_FILE': 'assignment.ipynb',
            'USE_SECRETS': 'true'
        }

        # Generate config
        generator.create_config_file(original_values, {}, {})

        # Load config
        loader = ConfigLoader(config_file)
        loaded_config = loader.load()

        # Verify roundtrip
        assert loaded_config['CLASSROOM_URL'] == original_values['CLASSROOM_URL']
        assert loaded_config['TEMPLATE_REPO_URL'] == original_values['TEMPLATE_REPO_URL']
        assert loaded_config['GITHUB_ORGANIZATION'] == original_values['GITHUB_ORGANIZATION']
        # Note: key changes - generator uses STUDENT_FILES instead of ASSIGNMENT_FILE
        assert loaded_config['STUDENT_FILES'] == original_values['MAIN_ASSIGNMENT_FILE']


class TestGlobalConfigManager:
    """Test the global configuration manager and load_global_config functionality."""

    def test_load_global_config_default_location(self, test_config_data, tmp_path):
        """Test loading config from default location (current directory)."""
        from classdock.config.global_config import load_global_config

        # Create assignment.conf in temp directory
        config_dir = tmp_path / "test_config"
        config_dir.mkdir()
        config_file = config_dir / "assignment.conf"

        config_content = "\n".join(
            [f'{key}="{value}"' for key, value in test_config_data.items()])
        config_file.write_text(config_content)

        # Move to the directory containing the config file
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(config_dir)

            # Should load config from current directory
            config = load_global_config()
            assert config is not None
            assert config.classroom_url == test_config_data['CLASSROOM_URL']
            assert config.github_organization == test_config_data['GITHUB_ORGANIZATION']
        finally:
            os.chdir(original_cwd)

    def test_load_global_config_with_assignment_root(self, test_config_data, tmp_path):
        """Test loading config with assignment_root parameter."""
        from classdock.config.global_config import load_global_config
        from pathlib import Path

        # Create assignment.conf in temp directory
        config_dir = tmp_path / "assignment_root"
        config_dir.mkdir()
        config_file = config_dir / "assignment.conf"

        config_content = "\n".join(
            [f'{key}="{value}"' for key, value in test_config_data.items()])
        config_file.write_text(config_content)

        # Load config from specific directory using assignment_root
        config = load_global_config(assignment_root=config_dir)

        assert config is not None
        assert config.classroom_url == test_config_data['CLASSROOM_URL']
        assert config.github_organization == test_config_data['GITHUB_ORGANIZATION']
        assert config.template_repo_url == test_config_data['TEMPLATE_REPO_URL']

    def test_load_global_config_assignment_root_precedence(self, tmp_path):
        """Test that assignment_root parameter takes precedence over current directory."""
        from classdock.config.global_config import load_global_config
        from pathlib import Path
        import os

        # Create config in assignment_root directory
        assignment_dir = tmp_path / "assignment_root"
        assignment_dir.mkdir()
        assignment_config = assignment_dir / "assignment.conf"
        assignment_config.write_text('''# Assignment Root Config
CLASSROOM_URL="https://classroom.github.com/assignment-root/test"
TEMPLATE_REPO_URL="https://github.com/assignment-root/template"
GITHUB_ORGANIZATION="assignment-root-org"
ASSIGNMENT_FILE="assignment.ipynb"
''')

        # Create different config in current directory
        cwd_dir = tmp_path / "current_dir"
        cwd_dir.mkdir()
        cwd_config = cwd_dir / "assignment.conf"
        cwd_config.write_text('''# Current Directory Config
CLASSROOM_URL="https://classroom.github.com/current-dir/test"
TEMPLATE_REPO_URL="https://github.com/current-dir/template"
GITHUB_ORGANIZATION="current-dir-org"
ASSIGNMENT_FILE="assignment.ipynb"
''')

        # Change to current directory and load with assignment_root
        original_cwd = os.getcwd()
        try:
            os.chdir(cwd_dir)

            # Should load from assignment_root, not current directory
            config = load_global_config(assignment_root=assignment_dir)

            assert config.classroom_url == "https://classroom.github.com/assignment-root/test"
            assert config.github_organization == "assignment-root-org"
            assert "assignment-root" in config.template_repo_url
        finally:
            os.chdir(original_cwd)

    def test_load_global_config_custom_filename_with_assignment_root(self, tmp_path):
        """Test loading custom config filename with assignment_root."""
        from classdock.config.global_config import load_global_config

        # Create custom config file in assignment root
        assignment_dir = tmp_path / "custom_assignment"
        assignment_dir.mkdir()
        custom_config = assignment_dir / "custom.conf"
        custom_config.write_text('''# Custom Config
CLASSROOM_URL="https://classroom.github.com/custom/test"
TEMPLATE_REPO_URL="https://github.com/custom/template"
GITHUB_ORGANIZATION="custom-org"
ASSIGNMENT_FILE="assignment.ipynb"
''')

        # Load with both custom filename and assignment_root
        config = load_global_config(
            config_file="custom.conf", assignment_root=assignment_dir)

        assert config is not None
        assert config.classroom_url == "https://classroom.github.com/custom/test"
        assert config.github_organization == "custom-org"

    def test_load_global_config_assignment_root_not_found(self, tmp_path):
        """Test error handling when assignment_root directory doesn't exist."""
        from classdock.config.global_config import load_global_config
        from pathlib import Path

        nonexistent_dir = tmp_path / "nonexistent"

        # Should raise FileNotFoundError
        with pytest.raises(FileNotFoundError) as exc_info:
            load_global_config(assignment_root=nonexistent_dir)

        assert "Configuration file not found" in str(exc_info.value)
        assert str(nonexistent_dir / "assignment.conf") in str(exc_info.value)

    def test_load_global_config_assignment_root_no_config_file(self, tmp_path):
        """Test error handling when assignment_root exists but has no config file."""
        from classdock.config.global_config import load_global_config

        # Create empty directory
        empty_dir = tmp_path / "empty_assignment"
        empty_dir.mkdir()

        # Should raise FileNotFoundError
        with pytest.raises(FileNotFoundError) as exc_info:
            load_global_config(assignment_root=empty_dir)

        assert "Configuration file not found" in str(exc_info.value)
        assert str(empty_dir / "assignment.conf") in str(exc_info.value)

    def test_load_global_config_relative_assignment_root(self, tmp_path):
        """Test loading config with relative assignment_root path."""
        from classdock.config.global_config import load_global_config
        from pathlib import Path
        import os

        # Create config in subdirectory
        sub_dir = tmp_path / "subdir"
        sub_dir.mkdir()
        config_file = sub_dir / "assignment.conf"
        config_file.write_text('''# Relative Path Config
CLASSROOM_URL="https://classroom.github.com/relative/test"
TEMPLATE_REPO_URL="https://github.com/relative/template"
GITHUB_ORGANIZATION="relative-org"
ASSIGNMENT_FILE="assignment.ipynb"
''')

        # Change to parent directory and use relative path
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            # Load using relative path
            config = load_global_config(assignment_root=Path("subdir"))

            assert config is not None
            assert config.classroom_url == "https://classroom.github.com/relative/test"
            assert config.github_organization == "relative-org"
        finally:
            os.chdir(original_cwd)
