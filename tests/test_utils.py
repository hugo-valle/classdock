"""
Test suite for the utilities package.

Tests logging, git operations, path management, and UI components.
"""

from pathlib import Path
import os
import subprocess
from unittest.mock import patch, MagicMock

from classdock.utils.logger import setup_logging, get_logger
from classdock.utils.git import GitManager
from classdock.utils.paths import PathManager
from classdock.utils.ui_components import Colors, print_colored, print_error, print_success
from classdock.utils.input_handlers import InputHandler, Validators, URLParser
from classdock.utils.file_operations import FileManager


class TestLogger:
    """Test logging functionality."""

    def test_setup_logging(self):
        """Test logging setup."""
        # Test basic setup
        setup_logging(verbose=False)
        logger = get_logger("test")
        assert logger is not None
        assert logger.name == "classdock.test"

    def test_verbose_logging(self):
        """Test verbose logging setup."""
        setup_logging(verbose=True)
        logger = get_logger("test_verbose")
        assert logger is not None

    def test_get_logger(self):
        """Test logger creation."""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")

        assert logger1.name == "classdock.module1"
        assert logger2.name == "classdock.module2"
        assert logger1 != logger2


class TestGitManager:
    """Test Git operations."""

    def test_git_manager_init(self):
        """Test GitManager initialization."""
        manager = GitManager()
        assert manager.repo_path == Path.cwd()

        custom_path = Path("/tmp")
        manager_custom = GitManager(custom_path)
        assert manager_custom.repo_path == custom_path

    @patch('subprocess.run')
    def test_get_repo_root(self, mock_run):
        """Test repository root detection."""
        mock_run.return_value = MagicMock(
            stdout='/home/user/repo\n',
            returncode=0
        )

        manager = GitManager()
        root = manager.get_repo_root()

        mock_run.assert_called_once()
        assert root == Path('/home/user/repo')

    @patch('subprocess.run')
    def test_get_repo_root_not_git_repo(self, mock_run):
        """Test repository root detection when not in git repo."""
        mock_run.side_effect = subprocess.CalledProcessError(1, 'git')

        manager = GitManager()
        root = manager.get_repo_root()

        assert root is None

    @patch('subprocess.run')
    def test_get_remote_url(self, mock_run):
        """Test getting remote URL."""
        mock_run.return_value = MagicMock(
            stdout='https://github.com/user/repo.git\n',
            returncode=0
        )

        manager = GitManager()
        url = manager.get_remote_url()

        assert url == 'https://github.com/user/repo.git'

    @patch('subprocess.run')
    def test_get_current_branch(self, mock_run):
        """Test getting current branch."""
        mock_run.return_value = MagicMock(
            stdout='feature/test\n',
            returncode=0
        )

        manager = GitManager()
        branch = manager.get_current_branch()

        assert branch == 'feature/test'

    @patch('subprocess.run')
    def test_get_status(self, mock_run):
        """Test getting git status."""
        mock_run.return_value = MagicMock(
            stdout='M  file1.py\nA  file2.py\nD  file3.py\n?? file4.py\n',
            returncode=0
        )

        manager = GitManager()
        status = manager.get_status()

        assert 'file1.py' in status['modified']
        assert 'file2.py' in status['added']
        assert 'file3.py' in status['deleted']
        assert 'file4.py' in status['untracked']

    @patch('subprocess.run')
    def test_clone_repo(self, mock_run):
        """Test repository cloning."""
        mock_run.return_value = MagicMock(returncode=0)

        manager = GitManager()
        success = manager.clone_repo(
            'https://github.com/user/repo.git',
            Path('/tmp/repo')
        )

        assert success is True
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_pull_repo(self, mock_run):
        """Test repository pulling."""
        mock_run.return_value = MagicMock(returncode=0)

        manager = GitManager()
        success = manager.pull_repo()

        assert success is True


class TestPathManager:
    """Test path management functionality."""

    def test_path_manager_init(self):
        """Test PathManager initialization."""
        manager = PathManager()
        assert manager.base_path == Path.cwd()

        custom_path = Path("/tmp")
        manager_custom = PathManager(custom_path)
        assert manager_custom.base_path == custom_path

    def test_find_config_file(self, temp_directory):
        """Test configuration file discovery."""
        # Create a config file
        config_file = temp_directory / "assignment.conf"
        config_file.write_text("TEST=value")

        manager = PathManager(temp_directory)
        found_file = manager.find_config_file()

        # Use resolve() to handle symlinks consistently
        assert found_file.resolve() == config_file.resolve()

    def test_find_config_file_not_found(self, temp_directory):
        """Test config file discovery when file doesn't exist."""
        manager = PathManager(temp_directory)
        found_file = manager.find_config_file()

        assert found_file is None

    def test_get_workspace_root(self, temp_directory):
        """Test workspace root detection."""
        # Create git indicator
        git_dir = temp_directory / ".git"
        git_dir.mkdir()

        manager = PathManager(temp_directory)
        root = manager.get_workspace_root()

        # Use resolve() to handle symlinks consistently
        assert root.resolve() == temp_directory.resolve()

    def test_ensure_output_directory(self, temp_directory):
        """Test output directory creation."""
        manager = PathManager(temp_directory)
        output_dir = manager.ensure_output_directory("test/output")

        assert output_dir.exists()
        assert output_dir.is_dir()
        assert output_dir == temp_directory / "test/output"

    def test_list_assignment_files(self, temp_directory):
        """Test assignment file discovery."""
        # Create test files
        (temp_directory / "assignment.ipynb").touch()
        (temp_directory / "main.py").touch()
        (temp_directory / "README.md").touch()
        (temp_directory / "__pycache__").mkdir()
        (temp_directory / "__pycache__" / "test.py").touch()

        manager = PathManager(temp_directory)
        files = manager.list_assignment_files()

        # Should find assignment files but not __pycache__ files
        file_names = [f.name for f in files]
        assert "assignment.ipynb" in file_names
        assert "main.py" in file_names
        assert "README.md" in file_names
        assert len([f for f in files if "__pycache__" in str(f)]) == 0

    def test_get_relative_path(self, temp_directory):
        """Test relative path calculation."""
        manager = PathManager(temp_directory)
        test_file = temp_directory / "subdir" / "test.py"

        relative = manager.get_relative_path(test_file)
        assert relative == "subdir/test.py"


class TestUIComponents:
    """Test UI components and formatting."""

    def test_colors_class(self):
        """Test Colors class."""
        assert hasattr(Colors, 'RED')
        assert hasattr(Colors, 'GREEN')
        assert hasattr(Colors, 'BLUE')
        assert hasattr(Colors, 'NC')

        # Test colorize method
        colored = Colors.colorize("test", Colors.RED)
        assert isinstance(colored, str)

    def test_print_functions(self, capsys):
        """Test printing functions."""
        print_colored("test message", Colors.BLUE)
        captured = capsys.readouterr()
        assert "test message" in captured.out

        print_error("error message")
        captured = capsys.readouterr()
        assert "error message" in captured.out
        assert "ERROR" in captured.out

        print_success("success message")
        captured = capsys.readouterr()
        assert "success message" in captured.out


class TestInputHandlers:
    """Test input handling and validation."""

    def test_validators(self):
        """Test validation functions."""
        # URL validation
        assert Validators.validate_url("https://github.com/user/repo") is True
        assert Validators.validate_url("invalid-url") is False

        # Organization validation
        assert Validators.validate_organization("valid-org") is True
        assert Validators.validate_organization("invalid!org") is False

        # File path validation
        assert Validators.validate_file_path("test.py") is True
        assert Validators.validate_file_path("test.invalid") is False

        # Non-empty validation
        assert Validators.validate_non_empty("not empty") is True
        assert Validators.validate_non_empty("") is False

    def test_url_parser(self):
        """Test URL parsing utilities."""
        # Test assignment extraction
        url = "https://github.com/org/assignment-template"
        assignment = URLParser.extract_assignment_from_url(url)
        assert assignment == "assignment-template"

        # Test organization extraction
        org = URLParser.extract_org_from_url(url)
        assert org == "org"

    @patch('builtins.input')
    @patch('sys.stdin.isatty')
    def test_input_handler_prompt(self, mock_isatty, mock_input):
        """Test input prompting."""
        mock_isatty.return_value = True
        mock_input.return_value = "test value"

        result = InputHandler.prompt_input("Test prompt")
        assert result == "test value"

    @patch('builtins.input')
    @patch('sys.stdin.isatty')
    def test_input_handler_with_default(self, mock_isatty, mock_input):
        """Test input prompting with default value."""
        mock_isatty.return_value = True
        mock_input.return_value = ""  # User hits enter

        result = InputHandler.prompt_input(
            "Test prompt", default="default value")
        assert result == "default value"

    @patch('builtins.input')
    @patch('sys.stdin.isatty')
    def test_prompt_yes_no(self, mock_isatty, mock_input):
        """Test yes/no prompting."""
        mock_isatty.return_value = True

        mock_input.return_value = "y"
        result = InputHandler.prompt_yes_no("Continue?")
        assert result is True

        mock_input.return_value = "n"
        result = InputHandler.prompt_yes_no("Continue?")
        assert result is False

        mock_input.return_value = ""
        result = InputHandler.prompt_yes_no("Continue?", default=True)
        assert result is True


class TestFileOperations:
    """Test file operation utilities."""

    def test_file_manager_init(self, temp_directory):
        """Test FileManager initialization."""
        manager = FileManager(temp_directory)
        assert manager.repo_root == temp_directory
        assert manager.gitignore_file == temp_directory / ".gitignore"

    def test_create_token_files(self, temp_directory):
        """Test token file creation."""
        manager = FileManager(temp_directory)

        config_values = {
            'INSTRUCTOR_TESTS_TOKEN_VALUE': 'test_token_value'
        }

        token_files = {
            'INSTRUCTOR_TESTS_TOKEN': 'instructor_token.txt'
        }

        manager.create_token_files(config_values, token_files)

        # Verify file was created
        token_file = temp_directory / "instructor_token.txt"
        assert token_file.exists()

        # Verify content
        assert token_file.read_text() == 'test_token_value'

        # Verify permissions (on Unix systems)
        if os.name == 'posix':
            stat = token_file.stat()
            # Check that only owner has read/write permissions
            assert oct(stat.st_mode)[-3:] == '600'

    def test_update_gitignore_new(self, temp_directory):
        """Test .gitignore update for new file."""
        manager = FileManager(temp_directory)
        manager.update_gitignore()

        gitignore = temp_directory / ".gitignore"
        assert gitignore.exists()

        content = gitignore.read_text()
        assert "instructor_token.txt" in content
        assert "assignment.conf" in content
        assert "tools/generated/" in content

    def test_update_gitignore_existing(self, temp_directory):
        """Test .gitignore update for existing file."""
        gitignore = temp_directory / ".gitignore"
        gitignore.write_text("# Existing content\n*.pyc\n")

        manager = FileManager(temp_directory)
        manager.update_gitignore()

        content = gitignore.read_text()
        assert "# Existing content" in content
        assert "*.pyc" in content
        assert "instructor_token.txt" in content

    def test_update_gitignore_already_updated(self, temp_directory):
        """Test .gitignore update when already contains instructor files."""
        gitignore = temp_directory / ".gitignore"
        gitignore.write_text("# Instructor-only files\ninstructor_token.txt\n")

        manager = FileManager(temp_directory)
        manager.update_gitignore()

        content = gitignore.read_text()
        # Should not duplicate the section
        assert content.count("# Instructor-only files") == 1


class TestUtilsIntegration:
    """Test integration between utility components."""

    def test_logger_git_integration(self, temp_directory):
        """Test that git operations use proper logging."""
        setup_logging(verbose=True)

        manager = GitManager(temp_directory)
        # This should log appropriately even if git operations fail
        assert manager.repo_path == temp_directory

    def test_path_config_integration(self, temp_directory):
        """Test that path manager works with config discovery."""
        # Create config file
        config_file = temp_directory / "assignment.conf"
        config_file.write_text("TEST=value")

        # Path manager should find it
        path_manager = PathManager(temp_directory)
        found_config = path_manager.find_config_file()

        # Use resolve() to handle symlinks consistently
        assert found_config.resolve() == config_file.resolve()

    def test_file_operations_path_integration(self, temp_directory):
        """Test file operations with path management."""
        path_manager = PathManager(temp_directory)
        workspace_root = path_manager.get_workspace_root()

        file_manager = FileManager(workspace_root)
        assert file_manager.repo_root == workspace_root
