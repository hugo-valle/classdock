# ClassDock

A comprehensive Python CLI tool for automating GitHub Classroom assignment management with modular workflow orchestration, repository operations, and secret management.

[![PyPI version](https://badge.fury.io/py/classdock.svg)](https://badge.fury.io/py/classdock)
[![Python Support](https://img.shields.io/pypi/pyversions/classdock.svg)](https://pypi.org/project/classdock/)
[![Tests](https://github.com/hugo-valle/classdock/workflows/Tests/badge.svg)](https://github.com/hugo-valle/classdock/actions)

## 🎯 Overview

ClassDock provides instructors with a powerful, modern CLI to automate GitHub Classroom workflows:

- **🐍 Modern Python CLI** - Type-safe, intuitive commands with rich help and output
- **📦 PyPI Package** - Simple installation: `pip install classdock`
- **🔧 Modular Architecture** - Organized command structure for different workflow areas
- **🔍 Smart Repository Discovery** - Automated filtering and batch operations
- **🔐 Secret Management** - Secure distribution of tokens and credentials
- **⚙️ Configuration-Driven** - Flexible, reusable assignment setups
- **🛡️ Enterprise Support** - Custom GitHub hosts and internal Git systems
- **🎯 Instructor-Focused** - Excludes instructor repos from batch operations automatically
- **🛡️ Robust Error Handling** - Centralized GitHub API error management with retry logic
- **🔄 Fault Tolerance** - Automatic retry mechanisms with exponential backoff
- **📊 Comprehensive Testing** - 70+ tests with 100% pass rate and extensive coverage
- **📚 Production Ready** - Professional documentation and type-safe implementations

## 📦 Installation

### Quick Install (Recommended)

```bash
# Install from PyPI
pip install classdock

# Verify installation
classdock --help
```

### Development Installation

```bash
# Clone repository
git clone https://github.com/hugo-valle/classdock.git
cd classdock

# Install with Poetry
poetry install
poetry shell

# Or install in development mode
pip install -e .
```

### Requirements

- **Python 3.10+** (3.11+ recommended)
- **Git** for repository operations
- **GitHub CLI** (optional, for enhanced authentication)

## �️ Enterprise Features

### Centralized Error Handling

ClassDock includes a comprehensive error handling system for reliable GitHub operations:

- **🔄 Automatic Retry Logic** - Intelligent retry with exponential backoff for transient failures
- **⏱️ Rate Limit Management** - Automatic handling of GitHub API rate limits
- **🛠️ Fallback Mechanisms** - CLI fallback when GitHub API is unavailable
- **📊 Detailed Error Context** - Comprehensive error reporting with context and suggestions
- **🏗️ Resilient Operations** - Fault-tolerant batch operations with individual error isolation

```python
# Example: Automatic retry with error context
from classdock.utils.github_exceptions import github_api_retry

@github_api_retry(max_attempts=3, base_delay=1.0)
def discover_repositories():
    # Automatic retry for GitHub API failures
    # Handles rate limits, network issues, and transient errors
    pass
```

### Enhanced CLI Architecture

- **📋 Modular Commands** - Organized subcommand structure (`assignments`, `repos`, `secrets`, `automation`)
- **🔗 Legacy Compatibility** - Backward compatibility with deprecation warnings
- **🎯 Rich Output** - Beautiful terminal output with progress indicators
- **⚙️ Flexible Configuration** - Multiple configuration sources with precedence handling
- **🔍 Comprehensive Help** - Context-aware help system with examples

### Production Quality

- **🧪 Comprehensive Testing** - 70+ tests covering all functionality with 100% pass rate
- **📚 Professional Documentation** - Complete docstrings following Python standards
- **🏗️ Type Safety** - Full type hints and mypy compatibility
- **🔒 Security First** - Secure credential handling and validation
- **📦 CI/CD Integration** - Automated testing and publishing pipeline

## �🚀 Quick Start

### 1. Basic Configuration

Create an assignment configuration file:

```bash
# Create assignment.conf
cat > assignment.conf << 'EOF'
# GitHub Classroom Configuration
CLASSROOM_URL="https://classroom.github.com/classrooms/123/assignments/456"
TEMPLATE_REPO_URL="https://github.com/instructor/assignment-template"
ASSIGNMENT_FILE="homework.py"

# Authentication
GITHUB_TOKEN_FILE="github_token.txt"

# Optional: Secrets to distribute
SECRETS_LIST="API_KEY,DATABASE_URL"
EOF
```

### 2. Command Structure

ClassDock uses a modular command structure:

```bash
# Main command groups
classdock assignments    # Assignment setup and orchestration
classdock repos         # Repository operations and collaboration
classdock secrets       # Secret and token management
classdock automation    # Scheduling and batch processing

# Legacy commands (for backward compatibility)
classdock setup         # Interactive assignment setup
classdock run           # Complete workflow execution
```

### 3. Common Workflows

```bash
# Setup a new assignment (interactive)
classdock assignments setup

# Discover student repositories
classdock repos fetch --config assignment.conf

# Add secrets to all student repos
classdock secrets add --config assignment.conf

# Run orchestrated workflow
classdock assignments orchestrate --config assignment.conf

# Check what would happen (dry-run)
classdock --dry-run assignments orchestrate
```

## 🔧 Command Reference

### Assignment Management

```bash
# Setup new assignment configuration
classdock assignments setup

# Orchestrate complete assignment workflow
classdock assignments orchestrate [--config FILE] [--dry-run]

# Manage assignment templates
classdock assignments manage [--config FILE]
```

### Repository Operations

```bash
# Fetch student repositories
classdock repos fetch [--config FILE]

# Manage collaborators
classdock repos collaborator add|remove [--config FILE]
```

### Secret Management

```bash
# Add secrets to repositories
classdock secrets add [--config FILE] [--secrets LIST]

# Remove secrets from repositories  
classdock secrets remove [--config FILE] [--secrets LIST]

# List existing secrets
classdock secrets list [--config FILE]
```

### Automation & Scheduling

```bash
# Setup cron jobs for automation
classdock automation scheduler setup [--config FILE]

# Run batch operations
classdock automation batch [--config FILE]
```

### Global Options

| Option | Description | Example |
|--------|-------------|---------|
| `--dry-run` | Preview actions without executing | `classdock --dry-run assignments orchestrate` |
| `--verbose` | Enable detailed logging | `classdock --verbose repos fetch` |
| `--config FILE` | Use custom configuration file | `classdock --config my.conf assignments setup` |
| `--help` | Show help for any command | `classdock assignments --help` |

## ⚙️ Configuration

### Assignment Configuration File

The `assignment.conf` file contains all settings for your assignment:

```bash
# Required: GitHub Classroom assignment URL
CLASSROOM_URL="https://classroom.github.com/classrooms/123/assignments/456"

# Required: Template repository URL
TEMPLATE_REPO_URL="https://github.com/instructor/assignment-template"

# Required: Assignment file to validate
ASSIGNMENT_FILE="homework.py"

# Optional: GitHub Enterprise support
GITHUB_HOSTS="github.enterprise.com,git.company.internal"

# Optional: Authentication
# Prefer centralized token manager (~/.config/classdock/token_config.json) or set GITHUB_TOKEN
# Example (CI): export GITHUB_TOKEN="ghp_your_token_here"

# Optional: Secrets management
SECRETS_LIST="API_KEY,DATABASE_URL,SECRET_TOKEN"

# Optional: Repository filtering
EXCLUDE_REPOS="template,example,demo"
INSTRUCTOR_REPOS="instructor-solution"
```

### Environment Variables

Override configuration with environment variables:

```bash
# Custom GitHub hosts
export GITHUB_HOSTS="git.company.internal,github.enterprise.com"

# GitHub token
export GITHUB_TOKEN="ghp_your_token_here"

# Custom assignment file
export ASSIGNMENT_FILE="main.cpp"

# Run with overrides
classdock assignments orchestrate
```

## 💡 Best Practices

### Workflow Recommendations

- **Always test with `--dry-run`** before making changes
- **Use `--verbose`** for debugging configuration issues
- **Keep configuration files in version control** with your assignment
- **Use environment variables** for sensitive information
- **Test with single student first** using filtered configuration

### Security Guidelines

- **Store GitHub tokens securely** using the centralized token manager or OS keychain; avoid placing token files in the repository root.
- **Use environment variables** for sensitive configuration
- **Review `--dry-run` output** before executing changes
- **Limit repository access** with proper filtering
- **Audit secret distribution** using verbose logging

### Configuration Management

- **Separate configs per assignment** for better organization
- **Use descriptive filenames** like `midterm-exam.conf`
- **Document custom GitHub hosts** in your assignment README
- **Validate URLs** before running batch operations

## 🛠️ Development

### Project Architecture

```text
classdock/
├── __init__.py              # Package initialization
├── __main__.py             # CLI entry point
├── cli.py                  # Main Typer CLI interface
├── config.py               # Configuration management
├── bash_wrapper.py         # Legacy script wrapper
├── utils.py                # Utility functions
├── utils/                  # Enhanced utilities
│   └── github_exceptions.py # Centralized error handling system
├── assignments/            # Assignment management
│   ├── setup.py           # Interactive setup
│   ├── orchestrator.py    # Workflow orchestration
│   └── manage.py          # Template management
├── repos/                  # Repository operations
│   ├── fetch.py           # Repository discovery (enhanced with error handling)
│   └── collaborator.py    # Collaborator management (with retry logic)
├── secrets/                # Secret management
│   ├── manager.py         # Secret distribution (fault-tolerant)
│   ├── add.py             # Secret distribution
│   ├── remove.py          # Secret removal
│   └── list.py            # Secret listing
├── automation/             # Automation & scheduling
│   ├── scheduler.py       # Cron job management
│   └── batch.py           # Batch processing
└── config/                 # Configuration system
    ├── loader.py          # Configuration loading
    ├── validator.py       # Validation logic
    └── generator.py       # Config generation
```

### Contributing

```bash
# Clone and setup development environment
git clone https://github.com/hugo-valle/classdock.git
cd classdock

# Install with Poetry
poetry install
poetry shell

# Run tests
poetry run pytest tests/ -v

# Test CLI functionality
poetry run classdock --help

# Format code
poetry run black classdock/
poetry run isort classdock/

# Type checking
poetry run mypy classdock/

# Create feature branch
git checkout -b feature/new-feature
```

### Testing

The project includes comprehensive testing with professional-grade coverage:

- **70+ tests** across all modules with 100% pass rate
- **Unit tests** for individual components with proper mocking
- **Integration tests** for workflow validation and API interactions
- **CLI tests** for command-line interface with legacy compatibility
- **Error handling tests** for GitHub API resilience and retry logic
- **Comprehensive mocking** for reliable test execution without external dependencies

```bash
# Run all tests
poetry run pytest tests/ -v

# Run specific test categories
poetry run pytest tests/test_assignments.py -v
poetry run pytest tests/test_cli.py -v
poetry run pytest tests/test_github_exceptions.py -v  # New error handling tests

# Test with coverage
poetry run pytest tests/ --cov=classdock

# Test error handling specifically
poetry run pytest tests/test_github_exceptions.py -v --tb=short
```

#### Test Categories

- **Module Tests** (44 tests) - Core functionality across all components
- **Error Handling Tests** (26 tests) - GitHub API resilience and retry mechanisms
- **CLI Tests** (16 tests) - Command-line interface and backward compatibility
- **Integration Tests** - End-to-end workflow validation

## 📚 Documentation

### Key Resources

- **[PyPI Package](https://pypi.org/project/classdock/)** - Official package page
- **[GitHub Repository](https://github.com/hugo-valle/classdock)** - Source code and issues
- **[CLI Architecture](docs/CLI_ARCHITECTURE.md)** - Modular command structure and design
- **[Error Handling Guide](docs/ERROR_HANDLING.md)** - GitHub API resilience and retry patterns
- **[CI/CD Documentation](docs/CICD_WORKFLOW.md)** - Automated publishing workflow
- **[PyPI Publication Guide](docs/PYPI_PUBLICATION.md)** - Release process documentation

### Technical Documentation

- **Error Handling System** - Comprehensive GitHub API error management with retry logic
- **CLI Design Patterns** - Modular architecture with backward compatibility
- **Testing Framework** - Professional test suite with mocking and coverage
- **Configuration Management** - Flexible, hierarchical configuration system
- **Security Practices** - Secure credential handling and validation patterns

### Version Information

- **Current Version**: 3.1.1b0 (Beta release with GitHub API integration and comprehensive testing)
- **Python Support**: 3.10, 3.11, 3.12
- **Package Distribution**: PyPI with automated CI/CD
- **Release Cycle**: Semantic versioning with [PEP 440](https://peps.python.org/pep-0440/) compliant identifiers
- **Versioning Strategy**: [Development Documentation](docs-site/development/versioning.md)

#### Recent Improvements (v3.1.1b0)

- **🎯 Universal CLI Options** - All commands support `--help`, `--verbose`, `--dry-run`
- **🏗️ CLI Modernization** - Complete Typer-based architecture with consistent UX
- **📁 Legacy Preservation** - Scripts moved to `scripts_legacy/` for backward compatibility
- **🔄 Workflow Consolidation** - Eliminated duplicate testing, enhanced CI/CD pipeline
- **🧪 Enhanced Testing** - 496+ comprehensive tests with consolidated coverage reporting
- **📚 Documentation Updates** - Complete modernization documentation across all resources
- **� Beta Release** - Ready for broader community testing and feedback

## 🆘 Support

- **Documentation**: [GitHub Repository](https://github.com/hugo-valle/classdock)
- **Issues**: [GitHub Issues](https://github.com/hugo-valle/classdock/issues)
- **Package**: [PyPI Package](https://pypi.org/project/classdock/)
- **Discussions**: [GitHub Discussions](https://github.com/hugo-valle/classdock/discussions)

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details.

---

**ClassDock** - Modern Python automation for GitHub Classroom assignment management.
