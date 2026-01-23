# Testing Guide

This guide covers testing practices and procedures for ClassDock.

## 🧪 Testing Overview

ClassDock maintains a comprehensive test suite with 153+ tests covering all major functionality:

- **Unit Tests**: Individual component testing
- **Integration Tests**: Component interaction testing
- **CLI Tests**: Command-line interface validation
- **Error Handling Tests**: Exception and error scenarios

## 🚀 Running Tests

### Basic Test Execution

```bash
# Run all tests
poetry run pytest tests/ -v

# Run specific test file
poetry run pytest tests/test_cli.py -v

# Run specific test class
poetry run pytest tests/test_cli.py::TestCLI -v

# Run specific test method
poetry run pytest tests/test_cli.py::TestCLI::test_version_command -v
```

### Test Coverage

```bash
# Run tests with coverage report
poetry run pytest tests/ --cov=classdock

# Generate HTML coverage report
poetry run pytest tests/ --cov=classdock --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Test Filtering

```bash
# Run tests matching a pattern
poetry run pytest tests/ -k "test_config"

# Run tests with specific markers
poetry run pytest tests/ -m "integration"

# Skip slow tests
poetry run pytest tests/ -m "not slow"
```

## 📁 Test Structure

### Test Organization

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── test_assignments.py      # Assignment management tests
├── test_automation.py       # Automation and scheduling tests
├── test_bash_wrapper.py     # Shell command wrapper tests
├── test_cli.py             # CLI interface tests
├── test_config_system.py   # Configuration system tests
├── test_config.py          # Legacy configuration tests
├── test_repos.py           # Repository operation tests
├── test_secrets.py         # Secret management tests
├── test_utils.py           # Utility function tests
└── fixtures/               # Test data and fixtures
```

### Test Naming Conventions

- **Test Files**: `test_<module>.py`
- **Test Classes**: `TestClassName`
- **Test Methods**: `test_method_description`
- **Fixtures**: `mock_<component>` or `temp_<resource>`

## 🔧 Writing Tests

### Basic Test Pattern

```python
import pytest
from classdock.module import Class

class TestClass:
    def test_method_success(self, mock_config):
        """Test successful operation."""
        # Arrange
        instance = Class(config=mock_config)
        
        # Act
        result = instance.method()
        
        # Assert
        assert result.success is True
        assert result.data is not None
    
    def test_method_failure(self, mock_config):
        """Test error handling."""
        # Arrange
        instance = Class(config=mock_config)
        
        # Act & Assert
        with pytest.raises(SpecificException):
            instance.method_that_fails()
```

### Using Fixtures

```python
def test_with_fixtures(mock_config, temp_dir, mock_bash_wrapper):
    """Test using multiple fixtures."""
    # All fixtures are automatically available
    assert mock_config is not None
    assert temp_dir.exists()
    assert mock_bash_wrapper.is_configured()
```

### Parametrized Tests

```python
@pytest.mark.parametrize("input_value,expected", [
    ("valid_input", True),
    ("invalid_input", False),
    ("", False),
])
def test_validation(input_value, expected):
    """Test input validation with multiple values."""
    result = validate_input(input_value)
    assert result == expected
```

## 🎭 Fixtures and Mocking

### Available Fixtures

The test suite provides several pre-configured fixtures:

#### Configuration Fixtures

```python
@pytest.fixture
def mock_config():
    """Mock configuration object."""
    return MockConfig()

@pytest.fixture
def temp_config_file(tmp_path):
    """Temporary configuration file."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("test: value")
    return config_file
```

#### File System Fixtures

```python
@pytest.fixture
def temp_dir(tmp_path):
    """Temporary directory for tests."""
    return tmp_path

@pytest.fixture
def mock_git_repo(tmp_path):
    """Mock Git repository."""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    return repo_dir
```

#### External Service Fixtures

```python
@pytest.fixture
def mock_bash_wrapper():
    """Mock bash command wrapper."""
    return MockBashWrapper()

@pytest.fixture
def mock_github_api():
    """Mock GitHub API responses."""
    return MockGitHubAPI()
```

### Creating Custom Fixtures

```python
@pytest.fixture
def custom_fixture(mock_config):
    """Custom fixture for specific tests."""
    # Setup
    resource = CustomResource(config=mock_config)
    yield resource
    # Cleanup
    resource.cleanup()
```

## 🔍 Testing CLI Commands

### CLI Test Patterns

```python
from typer.testing import CliRunner
from classdock.cli import app

def test_command_success():
    """Test successful command execution."""
    runner = CliRunner()
    result = runner.invoke(app, ["command", "--option", "value"])
    
    assert result.exit_code == 0
    assert "Expected output" in result.stdout

def test_command_error():
    """Test command error handling."""
    runner = CliRunner()
    result = runner.invoke(app, ["command", "--invalid", "option"])
    
    assert result.exit_code != 0
    assert "Error message" in result.stderr
```

### Testing Command Options

```python
def test_command_with_options():
    """Test command with various options."""
    runner = CliRunner()
    
    # Test with required options
    result = runner.invoke(app, ["command", "--required", "value"])
    assert result.exit_code == 0
    
    # Test with optional flags
    result = runner.invoke(app, ["command", "--required", "value", "--verbose"])
    assert result.exit_code == 0
    assert "verbose output" in result.stdout
```

## 🚨 Error Testing

### Exception Testing

```python
def test_specific_exception():
    """Test specific exception handling."""
    with pytest.raises(ConfigurationError) as exc_info:
        load_invalid_config()
    
    assert "Invalid configuration" in str(exc_info.value)

def test_exception_chain():
    """Test exception chaining."""
    with pytest.raises(ProcessingError) as exc_info:
        process_with_chain_error()
    
    assert exc_info.value.__cause__ is not None
```

### Error Message Testing

```python
def test_error_messages(caplog):
    """Test error message logging."""
    with caplog.at_level(logging.ERROR):
        process_with_error()
    
    assert "Expected error message" in caplog.text
    assert len(caplog.records) == 1
```

## 🔄 Continuous Integration

### GitHub Actions

Tests run automatically on:

- **Pull Requests**: All tests must pass
- **Main Branch**: Full test suite execution
- **Releases**: Complete validation before publishing

### Test Matrix

```yaml
strategy:
  matrix:
    python-version: [3.10, 3.11, 3.12]
    os: [ubuntu-latest, windows-latest, macos-latest]
```

### Coverage Requirements

- **Minimum Coverage**: 90%
- **New Code**: 100% coverage required
- **Critical Paths**: Full coverage mandatory

## 📊 Test Debugging

### Debug Mode

```bash
# Run tests with debug output
poetry run pytest tests/ -v -s

# Run with PDB on failure
poetry run pytest tests/ --pdb

# Run with detailed output
poetry run pytest tests/ -vv --tb=long
```

### Log Output

```bash
# Capture log output
poetry run pytest tests/ --log-cli-level=DEBUG

# Save logs to file
poetry run pytest tests/ --log-file=test.log
```

## 🎯 Best Practices

### Test Guidelines

1. **One Assertion Per Test**: Focus on single behavior
2. **Clear Test Names**: Describe what is being tested
3. **Arrange-Act-Assert**: Follow AAA pattern
4. **Mock External Dependencies**: Isolate units under test
5. **Clean Up Resources**: Use fixtures for setup/teardown

### Performance Considerations

- **Fast Tests**: Keep individual tests under 1 second
- **Parallel Execution**: Use pytest-xdist for speed
- **Resource Management**: Clean up temporary files
- **Network Isolation**: Mock external API calls

### Maintenance

- **Regular Updates**: Keep test dependencies current
- **Refactor Tests**: Maintain test quality alongside code
- **Documentation**: Document complex test scenarios
- **Review Coverage**: Monitor and improve coverage gaps
