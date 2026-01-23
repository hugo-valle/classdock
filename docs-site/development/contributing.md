# Contributing to ClassDock

Thank you for your interest in contributing to ClassDock! This document provides guidelines and instructions for contributors.

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- Poetry for dependency management
- Git for version control

### Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/hugo-valle/classdock.git
   cd classdock
   ```

2. **Install dependencies:**
   ```bash
   poetry install
   ```

3. **Activate the virtual environment:**
   ```bash
   poetry shell
   ```

4. **Verify installation:**
   ```bash
   classdock --help
   ```

## 🏗️ Development Guidelines

### Code Standards

- **Python Style**: Follow PEP 8 conventions
- **Type Hints**: Use type hints where applicable
- **Docstrings**: Maintain consistent docstring format
- **String Formatting**: Prefer f-strings for string formatting

### Testing Requirements

- **Coverage**: Maintain 100% test pass rate
- **New Features**: Write tests for all new functionality
- **Test Framework**: Use pytest with existing fixtures
- **Test Patterns**: Follow existing test patterns in `tests/`

### Version Management

- **Semantic Versioning**: `MAJOR.MINOR.PATCH-prerelease`
- **Pre-release Format**: `alpha.X`, `beta.X`, `rc.X`
- **Version Locations**: Keep synchronized:
  - `pyproject.toml` → `version = "X.Y.Z"`
  - `classdock/__init__.py` → `__version__ = "X.Y.Z"`
  - `classdock/cli.py` → version command output

## 🧪 Testing

### Running Tests

```bash
# Run all tests
poetry run pytest tests/ -v

# Run specific test file
poetry run pytest tests/test_cli.py -v

# Run with coverage
poetry run pytest tests/ --cov=classdock
```

### Test Organization

```python
# tests/test_<module>.py
import pytest
from classdock.<module> import Class

class TestClass:
    def test_method_success(self, mock_config):
        """Test successful operation."""
        pass
    
    def test_method_failure(self, mock_config):
        """Test error handling."""
        pass
```

## 📝 Documentation

### Docstring Format

```python
def function_name(param1: str, param2: int = 0) -> bool:
    """
    Brief description of function purpose.
    
    Args:
        param1: Description of first parameter
        param2: Description of second parameter with default
        
    Returns:
        Description of return value
        
    Raises:
        SpecificException: When specific condition occurs
    """
    pass
```

### CLI Help Text

```python
@app.command()
def command_name(
    param: str = typer.Option(..., help="Clear, concise parameter description")
):
    """
    Command description with example usage.
    
    Example:
        classdock command-name --param value
    """
    pass
```

## 🔄 Workflow

### Development Process

1. **Start**: Create feature branch from main
2. **Develop**: Implement changes with tests
3. **Test**: Run comprehensive test suite
4. **Verify**: Test CLI functionality locally
5. **Update**: Bump version if needed
6. **Document**: Update relevant documentation
7. **Commit**: Use conventional commit messages
8. **PR**: Create pull request with clear description
9. **Merge**: Merge to main after review
10. **Release**: Tag for automated publishing

### Commit Messages

Follow conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

Examples:
- `feat(cli): add new assignment command`
- `fix(repos): handle missing repository error`
- `docs(readme): update installation instructions`
- `test(cli): add tests for assignment commands`

## 🚀 Release Process

1. Update version in all locations
2. Update CHANGELOG.md
3. Commit changes: `git commit -m "bump: version X.Y.Z"`
4. Create tag: `git tag vX.Y.Z`
5. Push: `git push origin main --tags`
6. CI/CD handles automatic PyPI publication

## 🐛 Bug Reports

When reporting bugs, please include:

- Python version
- Operating system
- ClassDock version
- Steps to reproduce
- Expected behavior
- Actual behavior
- Any error messages

## ✨ Feature Requests

For feature requests, please provide:

- Clear description of the feature
- Use case or problem it solves
- Proposed implementation (if any)
- Examples of how it would be used

## 📞 Getting Help

- **Issues**: GitHub Issues for bugs and feature requests
- **Discussions**: GitHub Discussions for questions and ideas
- **Documentation**: Check the documentation first

## 📜 License

By contributing to ClassDock, you agree that your contributions will be licensed under the same license as the project.
