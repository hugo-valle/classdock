# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ClassDock** is a Python CLI tool for automating GitHub Classroom assignment management. It handles assignment setup, repository discovery, secret distribution, automated scheduling, and collaborator management.

- **Package**: `classdock` on PyPI
- **Python**: 3.10+
- **CLI Framework**: Typer
- **Package Manager**: Poetry

> **📋 Development Workflow**: See the [Development Workflow](#development-workflow) section below for step-by-step instructions on creating issues, branches, and PRs.

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
git checkout develop                   # Switch to develop
git pull origin develop                # Update develop
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
gh pr create --base develop --fill     # Create PR
gh pr checks                          # Check PR status
gh pr view                            # View current PR
gh pr list                            # List all PRs
```

## Development Workflow

### Working with Plan Mode

When using plan mode for complex tasks:

1. **Create and Finalize Your Plan**
   - Use plan mode to design the implementation approach
   - Explore the codebase and create a detailed plan
   - Exit plan mode when the plan is complete

2. **Create an Issue from the Plan**

   **Use Issue Templates**: Choose the appropriate template for your work type:
   - 🚀 **Feature Request** (`01-feature-request.md`) - New features
   - 🐛 **Bug Report** (`02-bug-report.md`) - Bug fixes
   - 🔥 **Hotfix** (`03-hotfix.md`) - Critical production fixes
   - 📚 **Documentation** (`04-documentation.md`) - Documentation updates
   - 🛠️ **Maintenance** (`05-maintenance.md`) - Code maintenance
   - 📦 **Release** (`06-release.md`) - Release preparation

   ```bash
   # Create issue using web interface with templates (recommended):
   # https://github.com/hugo-valle/classdock/issues/new/choose

   # Or create via CLI with plan content:
   gh issue create --title "Brief description of planned work" \
     --body "$(cat /path/to/plan/file.md)"
   ```

3. **Follow Standard Development Workflow**
   - Note the issue number from step 2
   - Create a branch referencing the issue (e.g., `feature/123-description`)
   - Implement according to the plan
   - Create PR linking back to the issue

**Why This Matters**: Creating an issue from your plan ensures the work is tracked, provides context for reviewers, and maintains a clear development history.

### Before Starting Any Work

1. **Check for Existing Issues**
   ```bash
   # Search GitHub issues for related work
   gh issue list --search "keyword"
   gh issue view <issue-number>
   ```

2. **Create an Issue (if none exists)**

   **Use Issue Templates** (recommended for consistency):

   Visit [New Issue with Templates](https://github.com/hugo-valle/classdock/issues/new/choose) and select:
   - 🚀 **Feature Request** - New features or enhancements
   - 🐛 **Bug Report** - Bug fixes and issues
   - 🔥 **Hotfix** - Critical production fixes
   - 📚 **Documentation** - Documentation improvements
   - 🛠️ **Maintenance** - Code maintenance tasks
   - 📦 **Release** - Release preparation

   ```bash
   # Or create via CLI (less structured):
   gh issue create --title "Brief description" --body "Detailed description"
   ```

3. **Note the Issue Number**
   - You'll reference this in your branch name and PR
   - Format: `#<number>` (e.g., #123)

### Branch Strategy Quick Reference

**Branch Types & Naming**:
- `feature/<issue>-brief-description` → New features (from develop)
- `bugfix/<issue>-brief-description` → Bug fixes (from develop)
- `hotfix/<issue>-brief-description` → Critical fixes (from main)
- `release/vX.Y.Z` → Release preparation (from develop)

**Examples**:
```bash
# Feature branch for issue #68
git checkout develop
git pull origin develop
git checkout -b feature/68-fix-global-cli-options

# Bugfix branch for issue #123
git checkout develop
git pull origin develop
git checkout -b bugfix/123-fix-token-validation

# Hotfix branch for issue #456 (critical production issue)
git checkout main
git pull origin main
git checkout -b hotfix/456-fix-security-vulnerability
```

### Complete Development Workflow

1. **Create Your Branch**
   ```bash
   # Start from develop (or main for hotfix)
   git checkout develop
   git pull origin develop
   git checkout -b feature/<issue>-description
   ```

2. **Make Changes and Test**
   ```bash
   # Run tests frequently
   make test              # Quick functionality tests
   make test-unit         # Full unit test suite

   # Check code quality before committing
   make lint              # Run flake8 and pylint
   make format            # Format with black
   poetry run mypy classdock/
   ```

3. **Commit Your Changes**
   ```bash
   # Use Conventional Commits format
   git add <files>
   git commit -m "type(scope): description

   - Detailed change explanation
   - Reference issue: #<issue-number>

   Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

   # Commit types: feat, fix, docs, refactor, test, chore
   ```

4. **Push and Create PR**
   ```bash
   # Push your branch
   git push -u origin feature/<issue>-description

   # Create PR (will auto-populate from template)
   gh pr create --base develop --fill

   # Or create with specific details
   gh pr create --title "Title" --body "Description" --base develop
   ```

5. **PR Requirements**
   - Links to issue using GitHub keywords (Closes #123, Fixes #456)
   - All tests passing (CI will verify)
   - 2 reviewer approvals required
   - Code coverage maintained or improved
   - Documentation updated if needed

6. **After Merge**
   - Branch auto-deletes
   - Issue auto-closes (if using Closes/Fixes keywords)
   - Switch back to develop: `git checkout develop && git pull`

### Hotfix Emergency Workflow

For critical production issues ONLY:

```bash
# 1. Create hotfix branch from main
git checkout main
git pull origin main
git checkout -b hotfix/<issue>-description

# 2. Make minimal fix and test thoroughly
make test-unit

# 3. Create PR to main
gh pr create --base main --title "Hotfix: description"

# 4. After merge to main, MUST merge to develop
# (Automated workflow handles this, but verify)
```

### Version Management for Releases

When creating a release:

```bash
# 1. Create release branch
git checkout develop
git checkout -b release/v1.2.3

# 2. Update version in 3 locations:
# - pyproject.toml (version = "1.2.3")
# - classdock/__init__.py (__version__ = "1.2.3")
# - classdock/cli.py (version command output)

# 3. Commit and PR to main
git commit -m "chore: bump version to 1.2.3"
gh pr create --base main --title "Release v1.2.3"

# 4. After merge, CI automatically:
# - Creates git tag (1.2.3 - no 'v' prefix)
# - Publishes to PyPI
# - Merges back to develop
```

### CI/CD Workflows

GitHub Actions automatically run on:
- **All PRs**: `ci.yml` (tests, linting, coverage)
- **Merge to main**: `publish.yml` (PyPI release)
- **Hotfix tags**: `auto-release.yml` (automated patch release)

**View workflow status**:
```bash
gh pr checks        # Check status of current PR
gh run list         # List recent workflow runs
gh run view <id>    # View specific run details
```

### Troubleshooting

**Common Issues**:
- **Tests failing locally**: Ensure `poetry install` is up to date
- **CI failing but local passes**: Check Python version (3.10+)
- **Branch protection blocks push**: Never force push to develop/main
- **PR blocked**: Ensure 2 approvals and all CI checks pass
- **Version mismatch**: Update all 3 version locations

**Getting Help**:
- Review `/docs/CONTRIBUTING.md` for detailed guidelines
- Check `/docs/branching_strategy.md` for branch workflows
- See `/.github/README.md` for GitHub Actions details

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

- `.github/copilot-instructions.md` - Detailed development patterns and GitHub API integration methodology
- `docs/CLI_ARCHITECTURE.md` - Typer-based command structure
- `docs/ERROR_HANDLING.md` - Error handling system
- `docs/TESTING.md` - Testing framework and patterns
- `docs/ROSTER_SYNC.md` - Roster management and sync integration guide
