# Tests

Fast pytest unit tests for ClassDock. GitHub API calls are mocked and shared fixtures live in `conftest.py`.

```bash
poetry run pytest tests/ -v
```

The full testing guide (unit and E2E tiers, writing tests, fixtures, coverage) is on the docs site:
[docs-site/development/testing.md](../docs-site/development/testing.md).

E2E and QA tests live in [`test_project_repos/`](../test_project_repos/README.md).
