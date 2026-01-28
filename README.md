# ClassDock

> Automate GitHub Classroom assignment management with a modern Python CLI

[![PyPI version](https://badge.fury.io/py/classdock.svg)](https://badge.fury.io/py/classdock)
[![Python Support](https://img.shields.io/pypi/pyversions/classdock.svg)](https://pypi.org/project/classdock/)
[![Tests](https://github.com/hugo-valle/classdock/workflows/Tests/badge.svg)](https://github.com/hugo-valle/classdock/actions)

## What is ClassDock?

ClassDock is a command-line tool that helps instructors manage GitHub Classroom assignments efficiently. Instead of manually managing hundreds of student repositories, ClassDock automates common workflows like:

- **Discovering student repositories** from GitHub Classroom
- **Managing student rosters** with CSV imports from Google Forms
- **Distributing secrets and tokens** to all student repos at once
- **Tracking assignment acceptance** rates and student progress
- **Managing collaborators** across multiple repositories
- **Automating repetitive tasks** with scheduled workflows

**Perfect for:** Computer science instructors managing GitHub Classroom assignments for classes of any size.

## Quick Start

### Installation

```bash
# Install from PyPI (recommended)
pip install classdock

# Verify installation
classdock --version
```

**Requirements:** Python 3.10+ and Git

### Your First Workflow

```bash
# 1. Navigate to your assignment directory
cd ~/my-assignment

# 2. Discover all student repositories from GitHub Classroom
classdock repos fetch

# 3. Import your student roster (from Google Forms CSV)
classdock roster init
classdock roster import students.csv --org=your-github-org

# 4. Check which students accepted the assignment
classdock roster status --org=your-github-org

# 5. Add secrets to all student repositories
classdock secrets add
```

That's it! You've automated what would normally take hours of manual work.

## Core Features

### 📋 Roster Management (New in 0.2.0!)

Track student enrollment and assignment acceptance with SQLite database:

```bash
# Initialize roster database
classdock roster init

# Import students from Google Forms CSV
classdock roster import students.csv --org=cs101-fall2025

# View roster and acceptance rates
classdock roster status --org=cs101-fall2025

# List all students
classdock roster list --org=cs101-fall2025

# Export roster data
classdock roster export roster-backup.csv --org=cs101-fall2025
```

**Features:**
- Import student rosters from CSV (Google Forms compatible)
- Track assignment acceptance rates
- Identify students who haven't started
- Multi-organization support for multiple classes
- Automatic sync with discovered repositories

**[📚 Roster Documentation](docs/ROSTER_MIGRATION.md)** | **[🚀 Quick Test Guide](docs/ROSTER_QUICK_TEST.md)**

### 🔍 Repository Discovery

Automatically find all student repositories for an assignment:

```bash
# Discover repositories from GitHub Classroom
classdock repos fetch

# Repositories are saved to student-repos.txt
# Automatically excludes instructor and template repos
```

### 🔐 Secret Management

Distribute tokens, API keys, and credentials to all student repos:

```bash
# Add secrets to all discovered repositories
classdock secrets add

# Remove secrets when assignment is complete
classdock secrets remove

# List current secrets
classdock secrets list
```

### 👥 Collaborator Management

Add or remove collaborators (TAs, graders) across all repositories:

```bash
# Add a TA to all student repos
classdock repos collaborator add --username ta-github-username

# Remove a collaborator
classdock repos collaborator remove --username ta-github-username
```

### ⚙️ Workflow Orchestration

Run complete workflows with a single command:

```bash
# Run the complete assignment setup workflow
classdock assignments orchestrate

# Preview what would happen (dry run)
classdock --dry-run assignments orchestrate
```

## Command Reference

### Roster Commands

```bash
classdock roster init                           # Initialize database
classdock roster import <csv> --org=<org>       # Import students
classdock roster list [--org=<org>]             # List students
classdock roster status [--org=<org>]           # Show statistics
classdock roster sync --assignment=<name>       # Sync repos with roster
classdock roster export <output> [--org=<org>]  # Export roster
classdock roster add --email=<email> --name=<name> --org=<org>  # Add student
classdock roster link --email=<email> --github=<username>        # Link GitHub
```

### Repository Commands

```bash
classdock repos fetch                           # Discover student repos
classdock repos collaborator add --username=<user>  # Add collaborator
classdock repos collaborator remove --username=<user>  # Remove collaborator
```

### Secret Commands

```bash
classdock secrets add                           # Add secrets to repos
classdock secrets remove                        # Remove secrets
classdock secrets list                          # List current secrets
```

### Assignment Commands

```bash
classdock assignments setup                     # Interactive setup wizard
classdock assignments orchestrate               # Run complete workflow
classdock assignments manage                    # Manage templates
```

### Global Options

```bash
--dry-run          # Preview actions without executing
--verbose          # Show detailed output
--config FILE      # Use specific configuration file
--help             # Show help for any command
```

## Configuration

ClassDock uses an `assignment.conf` file in your assignment directory:

```bash
# Minimal configuration
classroom_url="https://classroom.github.com/classrooms/123/assignments/456"
template_repo_url="https://github.com/your-org/assignment-template"
github_organization="your-github-org"
assignment_name="homework-1"

# Optional: Token configuration (uses ~/.config/classdock/token_config.json by default)
token_name="GITHUB_TOKEN"

# Optional: Secrets to distribute
secrets_list="API_KEY,DATABASE_URL"

# Optional: Enable roster sync in orchestrator
step_sync_roster=true
```

### Configuration File Generation

```bash
# Interactive setup creates assignment.conf for you
classdock assignments setup
```

## Common Workflows

### Workflow 1: New Assignment Setup

```bash
# 1. Create assignment directory
mkdir homework-1 && cd homework-1

# 2. Run interactive setup
classdock assignments setup

# 3. Discover student repositories
classdock repos fetch

# 4. (Optional) Sync with roster
classdock roster sync --assignment=homework-1 --org=cs101

# 5. Add required secrets
classdock secrets add
```

### Workflow 2: Mid-Semester Roster Tracking

```bash
# 1. Initialize roster (one-time)
classdock roster init

# 2. Import your student list
classdock roster import students.csv --org=cs101-fall2025

# 3. For each assignment, sync repos
cd assignment-1
classdock repos fetch
classdock roster sync --assignment=assignment-1 --org=cs101-fall2025

# 4. Check acceptance rates
classdock roster status --org=cs101-fall2025
```

### Workflow 3: Complete Automation

```bash
# Enable roster sync in assignment.conf
echo "step_sync_roster=true" >> assignment.conf

# Run complete orchestrated workflow
classdock assignments orchestrate

# This will:
# 1. Sync template repository
# 2. Discover student repositories
# 3. Sync with roster (if enabled)
# 4. Manage secrets
# 5. (Optional) Assist students
# 6. (Optional) Cycle collaborators
```

## Installation Options

### Production Use (Recommended)

```bash
# Install from PyPI
pip install classdock

# Upgrade to latest version
pip install --upgrade classdock
```

### Development Installation

```bash
# Clone repository
git clone https://github.com/hugo-valle/classdock.git
cd classdock

# Install with Poetry
poetry install

# Activate virtual environment
source $(poetry env info --path)/bin/activate

# Verify installation
classdock --help
```

## Documentation

### User Guides

- **[Roster Migration Guide](docs/ROSTER_MIGRATION.md)** - Adopt roster management for existing workflows
- **[Roster Sync Integration](docs/ROSTER_SYNC.md)** - Integrate roster sync with orchestrator
- **[Roster Testing Guide](docs/ROSTER_TESTING_GUIDE.md)** - Test roster features with real data
- **[CLI Architecture](docs/CLI_ARCHITECTURE.md)** - Command structure and design

### Technical Documentation

- **[Error Handling Guide](docs/ERROR_HANDLING.md)** - GitHub API resilience and retry patterns
- **[CI/CD Workflow](docs/CICD_WORKFLOW.md)** - Automated testing and publishing
- **[PyPI Publication](docs/PYPI_PUBLICATION.md)** - Release process

### Developer Resources

- **[Contributing Guide](docs/CONTRIBUTING.md)** - Development workflow and guidelines
- **[Branching Strategy](docs/branching_strategy.md)** - Git workflow and branch management
- **[CLAUDE.md](CLAUDE.md)** - AI assistant development guidelines

## Requirements

- **Python:** 3.10 or higher (3.11+ recommended)
- **Git:** For repository operations
- **GitHub Account:** With appropriate permissions for your classroom organization

### Optional Dependencies

- **GitHub CLI** (`gh`) - For enhanced authentication and PR management
- **Poetry** - For development installation

## Architecture

```
classdock/
├── cli.py                    # Main CLI interface (Typer)
├── assignments/              # Assignment management
│   ├── setup.py             # Interactive setup wizard
│   ├── orchestrator.py      # Workflow orchestration
│   └── manage.py            # Template management
├── repos/                    # Repository operations
│   ├── fetch.py             # Repository discovery
│   └── collaborator.py      # Collaborator management
├── secrets/                  # Secret management
│   ├── manager.py           # Secret operations
│   └── github_secrets.py    # GitHub API integration
├── roster/                   # Roster management (NEW in 0.2.0)
│   ├── models.py            # Data models
│   ├── manager.py           # CRUD operations
│   ├── importer.py          # CSV/JSON import/export
│   └── sync.py              # GitHub sync integration
├── automation/               # Scheduling and automation
├── config/                   # Configuration management
├── services/                 # Service layer
└── utils/                    # Utilities and helpers
```

## Testing

ClassDock has comprehensive test coverage:

```bash
# Run all tests
poetry run pytest tests/ -v

# Run specific test suite
poetry run pytest tests/test_roster*.py -v

# Run with coverage
poetry run pytest tests/ --cov=classdock

# Quick functionality test
make test
```

**Test Coverage:**
- 118+ tests for roster management
- 70+ tests for core functionality
- 100% pass rate
- Integration and unit tests

## Version History

### Version 0.2.0 (Upcoming)

**New Features:**
- 🎉 **SQLite Roster Management** - Track student enrollment and assignment acceptance
- 📊 **CSV Import** - Import rosters from Google Forms with flexible column mapping
- 🔄 **Repository Sync** - Link discovered repos to student roster
- 📈 **Acceptance Tracking** - Monitor which students accepted assignments
- 🏢 **Multi-Organization** - Manage rosters for multiple classes

**Improvements:**
- Flexible CSV column name mapping (case-insensitive)
- Support for Google Forms exported column names
- Orchestrator integration with optional roster sync

**Documentation:**
- Complete roster management guides
- Migration guide for existing users
- Testing documentation

### Version 0.1.1 (Current)

- Core GitHub Classroom automation
- Repository discovery and management
- Secret distribution
- Collaborator management
- Workflow orchestration

## Support

- **Issues:** [GitHub Issues](https://github.com/hugo-valle/classdock/issues)
- **Discussions:** [GitHub Discussions](https://github.com/hugo-valle/classdock/discussions)
- **Package:** [PyPI Package](https://pypi.org/project/classdock/)
- **Source:** [GitHub Repository](https://github.com/hugo-valle/classdock)

## Contributing

Contributions are welcome! Please see our [Contributing Guide](docs/CONTRIBUTING.md) for details on:

- Development workflow
- Branching strategy
- Testing requirements
- Code style guidelines
- Pull request process

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

**ClassDock** - Simplifying GitHub Classroom management, one command at a time.

Made with ❤️ for computer science educators.
