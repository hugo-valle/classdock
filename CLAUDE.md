# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ClassDock** is a Python CLI tool for automating assignment management for GitHub-based courses. It handles assignment setup, repository discovery, secret distribution, automated scheduling, and collaborator management.

## Workflow

Full guide: [CONTRIBUTING.md](CONTRIBUTING.md). Rules not to forget:

- **Issue first**: find or create a GitHub issue before starting work.
- **Branch from `main`**, named `<type>/<issue>-<slug>` (type: `feature`, `bugfix`, `docs`, `chore`, `claude`).
- **Conventional Commits**, and PRs target `main` with `Closes #123` (or `Part of #123`).
- **Merging never publishes**; a release is a separate GitHub Release (see CONTRIBUTING.md).

## Architecture

### Design Patterns
- **CLI → Services → Utils**: Clear separation of concerns
- **Centralized Error Handling**: All GitHub API errors go through `utils/github_exceptions.py` with retry logic and rate limit handling
- **Two-Tier Testing**: `tests/` for fast unit tests, `test_project_repos/` for E2E integration tests

## Critical Dependencies

```toml
click = ">=8.0.0,<8.2.0"      # Must be compatible with typer
```

## Testing Requirements

- Maintain 100% test pass rate
- Use pytest with mocking for GitHub API calls
- Run `poetry run pytest tests/ -v` before submitting changes

## Key Documentation

- `docs-site/development/architecture.md` - Typer-based command structure
- `docs-site/development/error-handling.md` - Error handling system
- `docs-site/development/testing.md` - Testing framework and patterns
- `docs-site/workflows/roster-sync.md` - Roster management and sync integration guide

## Agent skills

### Issue tracker

Issues live in GitHub Issues (hugo-valle/classdock), via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default five-role vocabulary (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: root `CONTEXT.md` + `docs/adr/`. See `docs/agents/domain.md`.
