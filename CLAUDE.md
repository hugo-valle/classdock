# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ClassDock** is a Python CLI tool for automating GitHub Classroom assignment management. It handles assignment setup, repository discovery, secret distribution, automated scheduling, and collaborator management.

- **Package**: `classdock` on PyPI
- **Python**: 3.10+
- **CLI Framework**: Typer
- **Package Manager**: Poetry

## Common Commands

```bash
# Development setup
poetry install
poetry shell

# Testing
make test                  # Quick functionality tests
make test-unit             # Unit tests with pytest
make test-full             # Comprehensive test suite
poetry run pytest tests/ -v                     # Run all tests
poetry run pytest tests/test_file.py -v         # Run single test file
poetry run pytest tests/ --cov=classdock  # With coverage

# Code quality
make lint                  # Run flake8 and pylint
make format                # Format with black
poetry run black classdock/ tests/
poetry run isort classdock/
poetry run mypy classdock/

# Build and run
make build                 # Build package
poetry run classdock --help               # Run CLI locally
python -m classdock --help                # Alternative
```

## Architecture

### CLI Command Structure
```
classdock
├── assignments   # Setup, orchestrate, manage assignments
├── repos         # Fetch, collaborate, push operations
├── secrets       # Add, remove, list, manage secrets
├── automation    # Cron scheduling, batch processing
└── Legacy        # Backward compatibility commands
```

### Package Structure
```
classdock/
├── cli.py                  # Main Typer CLI interface (entry point)
├── config/                 # Configuration management (loader, validator, generator)
├── assignments/            # Assignment lifecycle (setup, orchestrator, manage)
├── repos/                  # Repository operations (fetch, collaborator)
├── secrets/                # Secret management (manager, github_secrets)
├── automation/             # Scheduling (cron_manager, scheduler)
├── services/               # Service layer (assignment, repos, secrets, automation)
├── utils/
│   ├── github_exceptions.py    # Centralized GitHub API error handling
│   ├── github_api_client.py    # GitHub API client
│   ├── token_manager.py        # Centralized token management
│   ├── logger.py               # Rich logging
│   ├── git.py                  # Git operations
│   └── paths.py                # Path management
└── bash_wrapper.py         # Legacy bash script integration
```

### Design Patterns
- **CLI → Services → Utils**: Clear separation of concerns
- **Centralized Error Handling**: All GitHub API errors go through `utils/github_exceptions.py` with retry logic and rate limit handling
- **Two-Tier Testing**: `tests/` for fast unit tests, `test_project_repos/` for E2E integration tests

## Version Management

Keep version synchronized in three locations:
1. `pyproject.toml` → `version = "X.Y.Z"`
2. `classdock/__init__.py` → `__version__ = "X.Y.Z"`
3. `classdock/cli.py` → version command output

## Critical Dependencies

```toml
click = ">=8.0.0,<8.2.0"      # Must be compatible with typer
typer = ">=0.12.0"            # Latest stable
```

## Testing Requirements

- Maintain 100% test pass rate
- Use pytest with mocking for GitHub API calls
- Run `poetry run pytest tests/ -v` before submitting changes

## Key Documentation

- `.github/copilot-instructions.md` - Detailed development patterns and GitHub API integration methodology
- `docs/CLI_ARCHITECTURE.md` - Typer-based command structure
- `docs/ERROR_HANDLING.md` - Error handling system
- `docs/TESTING.md` - Testing framework and patterns
