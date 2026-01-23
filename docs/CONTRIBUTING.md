# Contributing to ClassDock

Thank you for your interest in contributing to ClassDock! This guide will help you set up your development environment and understand our contribution process.

## 🎯 Project Overview

ClassDock is a modern Python CLI tool for GitHub Classroom automation, built with:

- **Python 3.10+** with type hints and modern syntax
- **Typer** for CLI interface with universal options (`--help`, `--verbose`, `--dry-run`)
- **Poetry** for dependency management and packaging
- **pytest** for comprehensive testing (496+ tests)
- **GitHub Actions** for consolidated CI/CD and automated PyPI publishing

## 🚀 Quick Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/<your-username>/classdock.git
cd classdock

# Add upstream remote
git remote add upstream https://github.com/hugo-valle/classdock.git
```

### 2. Development Environment

```bash
# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Activate virtual environment
poetry shell

# Verify installation and universal options
classdock --help
classdock assignments --help --verbose
classdock repos --help --dry-run
```

### 3. Run Tests

```bash
# Run all tests
poetry run pytest tests/ -v

# Run tests with coverage
poetry run pytest tests/ --cov=classdock

# Run specific test categories
poetry run pytest tests/test_cli.py -v
```

## 🔧 Development Workflow

### 1. Create Feature Branch

```bash
# Always start from main and sync first
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Follow **PEP 8** coding standards
- Add **type hints** where applicable
- Write **comprehensive tests** for new functionality
- Update **documentation** as needed
- Ensure **100% test pass rate**

### 3. Test Your Changes

```bash
# Run tests
poetry run pytest tests/ -v

# Test CLI locally with universal options
poetry run classdock --help
poetry run classdock assignments --help
poetry run classdock repos --verbose --dry-run list

# Check code formatting
poetry run black classdock/ --check
poetry run isort classdock/ --check-only

# Type checking
poetry run mypy classdock/
```

### 4. Commit and Push

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: add new assignment orchestration feature"

# Push to your fork
git push origin feature/your-feature-name
```

### 5. Create Pull Request

- Open a PR from your feature branch to `main`
- Provide clear description of changes
- Reference any related issues
- Ensure all CI checks pass

## 📋 Contribution Guidelines

### Code Standards

1. **Python Style**:
   - Follow PEP 8 conventions
   - Use type hints for function parameters and returns
   - Write descriptive docstrings for all functions and classes
   - Prefer f-strings for string formatting

2. **CLI Development**:
   - Use Typer for all new CLI commands
   - Organize commands in appropriate sub-applications
   - Provide helpful descriptions and examples
   - Include proper error handling with informative messages

3. **Testing Requirements**:
   - Write tests for all new functionality
   - Maintain 100% test pass rate
   - Use existing fixtures from `conftest.py`
   - Follow established test patterns

### Project Structure

```
classdock/
├── __init__.py              # Package initialization
├── cli.py                  # Main CLI interface
├── assignments/            # Assignment management commands
├── repos/                  # Repository operation commands
├── secrets/                # Secret management commands
├── automation/             # Automation and scheduling
├── config/                 # Configuration system
└── utils/                  # Utility functions
```

### Testing Patterns

```python
# Test file example: tests/test_new_feature.py
import pytest
from classdock.new_module import NewClass

class TestNewClass:
    def test_method_success(self, mock_config):
        """Test successful operation."""
        # Test implementation
        pass
    
    def test_method_failure(self, mock_config):
        """Test error handling."""
        # Test implementation
        pass
```

### Documentation Standards

```python
def new_function(param1: str, param2: int = 0) -> bool:
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

## 🧪 Testing

### Test Categories

- **Unit Tests**: Individual component testing
- **Integration Tests**: Component interaction testing
- **CLI Tests**: Command-line interface validation
- **Error Tests**: Exception and error handling

### Running Tests

```bash
# All tests
poetry run pytest tests/ -v

# Specific test file
poetry run pytest tests/test_assignments.py -v

# With coverage report
poetry run pytest tests/ --cov=classdock --cov-report=html

# Watch mode for development
poetry run pytest-watch tests/
```

## 📦 Version Management

### Semantic Versioning

We follow semantic versioning: `MAJOR.MINOR.PATCH-prerelease`

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes
- **Pre-release**: `alpha.X`, `beta.X`, `rc.X`

### Version Update Process

When your changes require a version bump:

1. Update `pyproject.toml` version
2. Update `classdock/__init__.py` `__version__`
3. Update `classdock/cli.py` version command
4. Update `CHANGELOG.md` with changes

## 🚀 Release Process

Releases are automated via GitHub Actions:

1. **Create PR** with your changes
2. **Merge to main** after review
3. **Tag release**: `git tag v3.0.1-alpha.3`
4. **Push tag**: `git push origin main --tags`
5. **CI/CD handles the rest**: testing, building, PyPI publishing

## 🔍 Common Issues

### Dependency Conflicts

```bash
# Update dependencies
poetry update

# Rebuild lock file
poetry lock --no-update
```

### Test Failures

```bash
# Check fixture configuration
poetry run pytest tests/conftest.py -v

# Run with verbose output
poetry run pytest tests/ -v -s
```

### CLI Issues

```bash
# Test CLI installation
poetry run pip show classdock

# Test entry point
poetry run python -m classdock --help
```

## 💬 Getting Help

- **Issues**: [GitHub Issues](https://github.com/hugo-valle/classdock/issues)
- **Discussions**: [GitHub Discussions](https://github.com/hugo-valle/classdock/discussions)
- **Documentation**: [Project Docs](README.md)

## 📝 Issue Templates

### Bug Report
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Environment details (Python version, OS)
- Relevant logs or error messages

### Feature Request
- Clear description of the feature
- Use case and motivation
- Proposed implementation approach
- Potential breaking changes

---

Thank you for contributing to ClassDock! Your help makes this tool better for educators everywhere.
