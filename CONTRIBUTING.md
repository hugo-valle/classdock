# Contributing to ClassDock

Thanks for contributing. This is the single guide to the development workflow; other docs link here instead of repeating it.

## Setup

Requires Python 3.10+ and [Poetry](https://python-poetry.org/).

```bash
git clone https://github.com/<your-username>/classdock.git   # your fork
cd classdock
git remote add upstream https://github.com/hugo-valle/classdock.git
poetry install
poetry run classdock --help
```

## Workflow

Trunk-based: `main` is the only long-lived branch and every PR targets it ([ADR 0002](docs/adr/0002-trunk-based-development.md)).

1. **Issue first.** Find or create a GitHub issue (`gh issue list --search ...`, `gh issue create`).
2. **Branch from `main`**, named `<type>/<issue>-<slug>`, where type is `feature`, `bugfix`, `docs`, `chore` or `claude`:
   ```bash
   git checkout main && git pull upstream main
   git checkout -b feature/123-short-description
   ```
3. **Commit** with [Conventional Commits](https://www.conventionalcommits.org/) (`feat|fix|docs|refactor|test|chore|ci(scope): ...`) and reference the issue.
4. **Open a PR into `main`** (`gh pr create --base main --fill`). The body includes `Closes #123` (or `Part of #123` when the issue has more work left).

### Checks before pushing

```bash
poetry run pytest tests/ -v
poetry run black classdock/ --check
poetry run isort classdock/ --check-only
poetry run mypy classdock/
```

CI (`ci.yml`) must pass before merge: `test (3.10)`, `test (3.14)` and `lint`. Merging to `main` never publishes; releasing is a separate step.

## Code standards

- Follow PEP 8, use type hints, and prefer f-strings.
- New CLI commands use Typer, grouped in the matching sub-app, with helpful `--help` text and informative errors.
- GitHub API errors go through `classdock/utils/github_exceptions.py`.
- Write tests for new behaviour and keep the pass rate at 100%. Mock GitHub API calls and reuse fixtures from `tests/conftest.py`. See [docs/TESTING.md](docs/TESTING.md).

## Releasing

Versions follow [PEP 440](https://peps.python.org/pep-0440/) (`1.2.3`, `1.3.0a1`). The version lives only in `pyproject.toml`; `classdock.__version__` and `classdock --version` read it from there.

1. On a `chore/<issue>-release-X.Y.Z` branch run `poetry version X.Y.Z`, then PR and merge into `main`.
2. `git checkout main && git pull`
3. Create the release with a bare semver tag (no `v`):
   ```bash
   gh release create X.Y.Z --generate-notes              # add --draft to review notes first
   gh release create X.Y.ZaN --generate-notes --prerelease   # pre-releases
   ```
4. Publishing the release runs `.github/workflows/release.yml`. It checks the tag matches `pyproject.toml`, runs tests, builds with Poetry and publishes to PyPI via trusted publishing (OIDC, no tokens).

Release notes come from merged PR titles, grouped by label (`.github/release.yml`). A hotfix is an ordinary `bugfix/` PR followed by a patch release.

## Getting help

- [GitHub Issues](https://github.com/hugo-valle/classdock/issues)
- [GitHub Discussions](https://github.com/hugo-valle/classdock/discussions)
