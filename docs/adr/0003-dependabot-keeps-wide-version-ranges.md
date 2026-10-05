---
status: accepted
---

# Dependabot keeps wide version ranges in `pyproject.toml`

ClassDock is installed from PyPI, where pip resolves against the ranges in `pyproject.toml`, not `poetry.lock`. Dependabot's default for pip raised every floor on every bump (e.g. `PyGithub>=1.59.0` → `>=2.10.0`), forcing users onto new versions for no reason and making 13 separate PRs that all conflicted on `poetry.lock`.

Dependabot uses `versioning-strategy: increase-if-necessary`: it updates `poetry.lock` and only touches a range when the new version falls outside it. Minor and patch updates arrive as one grouped PR per ecosystem; major updates stay as separate PRs.

## Consequences

- CI tests the latest locked versions, not the floors; an old floor can silently stop working. Raise a floor by hand when the code starts relying on a newer API.
- A major bump still changes the range, so it gets its own PR and its own review.
