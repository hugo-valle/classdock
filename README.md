# ClassDock

> Automation for GitHub-based courses, from a modern Python CLI

[![PyPI version](https://badge.fury.io/py/classdock.svg)](https://badge.fury.io/py/classdock)
[![Python Support](https://img.shields.io/pypi/pyversions/classdock.svg)](https://pypi.org/project/classdock/)
[![CI](https://github.com/hugo-valle/classdock/actions/workflows/ci.yml/badge.svg)](https://github.com/hugo-valle/classdock/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

ClassDock is a command-line tool for computer science instructors who run assignments as template repositories in a GitHub organization. Instead of manually clicking through dozens of student repositories, ClassDock automates the repetitive work — discovering repos, distributing secrets, tracking roster acceptance — so you can focus on teaching.

**Perfect for:** Instructors managing assignments on GitHub for classes of any size.

---

## Installation

```bash
pip install classdock
```

**Requirements:** Python 3.10+ and Git

---

## Quick Start

```bash
# 1. Set up your GitHub token (one-time)
classdock token

# 2. Create a new assignment
classdock setup

# 3. Discover all student repositories
classdock fetch

# 4. Add secrets to every student repo at once
classdock secrets add

# 5. Run the full workflow end-to-end
classdock run
```

---

## Shortcut Commands

These shortcuts cover the most common operations without navigating command groups:

| Command | What it does |
|---------|--------------|
| `classdock run` | Run the full assignment workflow (`assignments orchestrate`) |
| `classdock setup` | Launch the interactive assignment setup wizard |
| `classdock fetch` | Discover all student repositories in the organization |
| `classdock status` | Show assignment dashboard (repos, roster, token status) |
| `classdock token` | Configure your GitHub Personal Access Token |

---

## Command Groups

For full control, every feature is available through organized command groups:

| Group | Description |
|-------|-------------|
| `classdock assignments` | Assignment lifecycle: setup wizard, orchestration, student helpers |
| `classdock repos` | Repository discovery |
| `classdock secrets` | Distribute secrets and tokens to all student repos |
| `classdock roster` | Student roster management with CSV import and assignment tracking |
| `classdock automation` | Cron scheduling for automated workflow steps |
| `classdock config` | GitHub token configuration and validation |

See the **[Full Command Reference](https://hugo-valle.github.io/classdock/cli/commands/)** for every subcommand and option.

---

## Configuration

ClassDock reads an `assignment.conf` file from your assignment directory:

```bash
# Minimal configuration
GITHUB_ORGANIZATION="your-github-org"
ASSIGNMENT_NAME="homework-1"
TEMPLATE_REPO_URL="https://github.com/your-github-org/homework-1-template"

# Optional: secrets to distribute to every student repo
secrets_list="API_KEY,DATABASE_URL"

# Optional: enable roster sync during orchestration
step_sync_roster=true
```

Run `classdock setup` to generate this file interactively.

---

## Roster Management

Track which students accepted an assignment and link their GitHub repos to your class roster:

```bash
# Initialize (one-time, stores data in ~/.config/classdock/roster.db)
classdock roster init

# Import your student list from a Google Forms CSV export
classdock roster import students.csv --org=cs101-fall2025

# After fetching repos, link them to roster entries
classdock roster sync --assignment=homework-1 --org=cs101-fall2025

# See who has and hasn't accepted
classdock roster status --org=cs101-fall2025
```

See **[Roster Sync Guide](https://hugo-valle.github.io/classdock/workflows/roster-sync/)** for detailed setup.

---

## Documentation

| Document | Description |
|----------|-------------|
| [Full Command Reference](https://hugo-valle.github.io/classdock/cli/commands/) | Every command, subcommand, and option |
| [Roster Sync Guide](https://hugo-valle.github.io/classdock/workflows/roster-sync/) | Roster management and orchestrator integration |
| [Error Handling](https://hugo-valle.github.io/classdock/development/error-handling/) | GitHub API resilience and retry patterns |
| [Contributing Guide](CONTRIBUTING.md) | Development workflow and guidelines |
| [Changelog](docs/CHANGELOG.md) | Release history |

---

## Contributing

Contributions are welcome. Please read the [Contributing Guide](CONTRIBUTING.md) before opening a pull request.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

Made with care for computer science educators.
