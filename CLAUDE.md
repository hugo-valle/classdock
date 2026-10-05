# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ClassDock** is a Python CLI tool for automating assignment management for GitHub-based courses. It handles assignment setup, repository discovery, secret distribution, automated scheduling, and collaborator management.

- **Package**: `classdock` on PyPI
- **Python**: 3.10+
- **CLI Framework**: Typer
- **Package Manager**: Poetry

> **📋 Workflow**: See the [Workflow](#workflow) section below for branches, PRs and releases.

## Prerequisites

### Required Tools
- Python 3.10+
- Poetry (package manager)
- Git
- GitHub CLI (`gh`) - for issue/PR management

### GitHub CLI Setup
```bash
# Install gh CLI
# macOS: brew install gh
# Linux: See https://cli.github.com/manual/installation
# Windows: See https://cli.github.com/manual/installation

# Authenticate with GitHub
gh auth login

# Configure git to use gh for authentication
gh auth setup-git
```

### Repository Setup
```bash
# Clone repository
git clone https://github.com/hugo-valle/classdock.git
cd classdock

# Install dependencies
poetry install
poetry shell
```

## Common Commands

```bash
# Development setup
poetry install
poetry shell

# Issue Management (requires gh CLI)
gh issue list                          # List all issues
gh issue list --search "keyword"       # Search issues
gh issue create                        # Create new issue
gh issue view <number>                 # View issue details

# Branch Management
git checkout main                      # Switch to main
git pull origin main                   # Update main
git checkout -b feature/123-description # Create feature branch

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

# Pull Request Management
gh pr create --base main --fill        # Create PR
gh pr checks                          # Check PR status
gh pr view                            # View current PR
gh pr list                            # List all PRs
```

## Workflow

Trunk-based: `main` is the only long-lived branch (see `docs/adr/0002-trunk-based-development.md`).

1. **Issue first**: find or create a GitHub issue (`gh issue list --search ...`, `gh issue create`).
2. **Branch from `main`**, named `<type>/<issue>-<slug>` where type is `feature`, `bugfix`, `docs`, `chore` or `claude`:
   ```bash
   git checkout main && git pull
   git checkout -b feature/123-short-description
   ```
3. **Commit** with Conventional Commits (`feat|fix|docs|refactor|test|chore|ci(scope): ...`) and reference the issue.
4. **PR into `main`**: `gh pr create --base main --fill`, body includes `Closes #123`. CI (`ci.yml`: `test (3.10)`, `test (3.14)`, `lint`) must pass. Merging never publishes.

**Releasing** (the version lives only in `pyproject.toml`):

1. On a `chore/<issue>-release-X.Y.Z` branch, run `poetry version X.Y.Z`, then PR and merge into `main`.
2. `git checkout main && git pull`
3. `gh release create X.Y.Z --generate-notes` (bare semver tag, no `v`; add `--draft` to review notes first)
4. Publishing the release runs `release.yml`: it checks the tag matches `pyproject.toml`, runs tests, builds, and publishes to PyPI via **trusted publishing** (OIDC, no tokens).

A hotfix is an ordinary `bugfix/` PR followed by a patch release.

## Architecture

### CLI Command Structure
```
classdock
├── assignments   # Setup, orchestrate, manage assignments
├── repos         # Fetch, collaborate, push operations
├── secrets       # Add, remove, list, manage secrets
├── automation    # Cron scheduling, batch processing
├── roster        # Student roster management, CSV import/export
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
├── roster/                 # Student roster management (SQLite-based)
│   ├── models.py           # Student, Assignment, StudentAssignment dataclasses
│   ├── manager.py          # RosterManager - CRUD operations
│   ├── importer.py         # CSV/JSON import and export
│   └── sync.py             # GitHub repository synchronization
├── services/               # Service layer (assignment, repos, secrets, automation, roster)
├── utils/
│   ├── database.py         # SQLite database manager
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

## Critical Dependencies

```toml
click = ">=8.0.0,<8.2.0"      # Must be compatible with typer
typer = ">=0.12.0"            # Latest stable
```

## Testing Requirements

- Maintain 100% test pass rate
- Use pytest with mocking for GitHub API calls
- Run `poetry run pytest tests/ -v` before submitting changes

## Roster Management (Issue #34)

ClassDock includes a SQLite-based roster management system for tracking student enrollment and assignment acceptance.

### Quick Start

```bash
# Initialize roster database (one-time)
classdock roster init

# Import students from CSV (Google Forms format)
classdock roster import students.csv --org=soc-cs3550-f25

# List students
classdock roster list --org=soc-cs3550-f25

# Sync discovered repos with roster
classdock repos fetch
classdock roster sync --assignment=python-basics --org=soc-cs3550-f25

# Check status
classdock roster status --org=soc-cs3550-f25
```

### Roster Commands

```bash
classdock roster init                  # Initialize global roster database
classdock roster import FILE --org=ORG # Import students from CSV
classdock roster list [--org=ORG]      # List students
classdock roster add                   # Add single student
classdock roster link                  # Link GitHub username to student
classdock roster export FILE           # Export roster to CSV/JSON
classdock roster sync                  # Sync repos with roster
classdock roster status [--org=ORG]    # Show roster statistics
```

### Database Location

- **Global database**: `~/.config/classdock/roster.db`
- Supports multiple GitHub organizations
- Tracks students, assignments, and repository links

### Orchestrator Integration

Enable roster sync in `assignment.conf`:
```bash
step_sync_roster=true
```

Then run: `classdock assignments orchestrate`

See `docs/ROSTER_SYNC.md` for complete documentation.

## Key Documentation

- `docs/CLI_ARCHITECTURE.md` - Typer-based command structure
- `docs/ERROR_HANDLING.md` - Error handling system
- `docs/TESTING.md` - Testing framework and patterns
- `docs/ROSTER_SYNC.md` - Roster management and sync integration guide

## Agent skills

### Issue tracker

Issues live in GitHub Issues (hugo-valle/classdock), via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default five-role vocabulary (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: root `CONTEXT.md` + `docs/adr/`. See `docs/agents/domain.md`.
