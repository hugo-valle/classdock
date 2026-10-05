# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ClassDock** is a Python CLI tool for automating assignment management for GitHub-based courses. It handles assignment setup, repository discovery, secret distribution, automated scheduling, and collaborator management.

> **📋 Workflow**: See the [Workflow](#workflow) section below for branches, PRs and releases.

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

- `docs/CLI_ARCHITECTURE.md` - Typer-based command structure
- `docs/ERROR_HANDLING.md` - Error handling system
- `docs/TESTING.md` - Testing framework and patterns
- `docs-site/workflows/roster-sync.md` - Roster management and sync integration guide

## Agent skills

### Issue tracker

Issues live in GitHub Issues (hugo-valle/classdock), via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default five-role vocabulary (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: root `CONTEXT.md` + `docs/adr/`. See `docs/agents/domain.md`.
