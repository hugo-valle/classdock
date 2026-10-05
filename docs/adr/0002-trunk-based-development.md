---
status: accepted
---

# Trunk-based development: one `main` branch, releases from GitHub Releases

ClassDock used git-flow: a `develop` integration branch, `release/*` and `hotfix/*` branches into `main`, sync PRs to merge `main` back into `develop`, and publish workflows that parsed merge-commit messages to decide whether to release. For a solo maintainer working with Claude, that meant a sync PR after every release, two workflows that could both publish, and releases that broke when a commit message didn't match a regex.

We work on a single `main` branch. Topic branches (`feature|bugfix|docs|chore|claude/<issue>-<slug>`) are a naming convention only, and every PR targets `main`. A release is a GitHub Release with a bare semver tag (`X.Y.Z`); publishing it triggers `release.yml`, which checks the tag against `pyproject.toml`, runs the tests and publishes to PyPI via trusted publishing.

## Consequences

- There is no integration branch: `main` is always the latest code, and merging to it never publishes.
- Tags mark what shipped; the GitHub Release notes are the per-release changelog.
- Hotfixes are ordinary PRs into `main` followed by a patch release.
