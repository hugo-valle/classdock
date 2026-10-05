# Testing Guide

This is the single contributor-facing testing guide for ClassDock. Testing has two tiers:

| Tier | Where | What it covers | When to run |
|------|-------|----------------|-------------|
| **Unit** | `tests/` | Fast pytest tests with mocked GitHub API calls | Every change, and in CI |
| **E2E** | `test_project_repos/` | Shell-driven install, CLI, QA functional and real-repository tests | Before a release, or when changing CLI behavior |

CI requires a 100% pass rate on the unit tier.

## Unit Tests

### Running

```bash
# Full suite (run before submitting changes)
poetry run pytest tests/ -v

# One file, class, or method
poetry run pytest tests/test_cli.py -v
poetry run pytest tests/test_cli.py::TestCLI -v
poetry run pytest tests/test_cli.py::TestCLI::test_version_command -v

# Filter by name
poetry run pytest tests/ -k "config"

# Coverage
poetry run pytest tests/ --cov=classdock --cov-report=html

# Debugging
poetry run pytest tests/ -vv -s --tb=long
poetry run pytest tests/ --pdb
poetry run pytest tests/ --log-cli-level=DEBUG
```

pytest runs with `--strict-markers`, so register any new marker in `pyproject.toml` before using it.

### Layout and conventions

- `tests/conftest.py` holds shared fixtures. Reuse them before adding new ones.
- `tests/fixtures/` holds sample configuration and response data.
- Files are named `test_<module>.py`, classes `TestClassName`, methods `test_<behavior>`.
- Follow arrange / act / assert and keep each test focused on one behavior.
- Mock at the boundary. Never call the real GitHub API from `tests/`.

### Writing tests

```python
import pytest
from classdock.module import Class


class TestClass:
    def test_method_success(self, mock_config):
        result = Class(config=mock_config).method()
        assert result.success is True

    def test_method_failure(self, mock_config):
        with pytest.raises(SpecificException):
            Class(config=mock_config).method_that_fails()


@pytest.mark.parametrize("value,expected", [("valid", True), ("", False)])
def test_validation(value, expected):
    assert validate_input(value) is expected
```

CLI commands are tested with Typer's runner:

```python
from typer.testing import CliRunner
from classdock.cli import app


def test_command_success():
    result = CliRunner().invoke(app, ["command", "--option", "value"])
    assert result.exit_code == 0
    assert "Expected output" in result.stdout
```

Error paths matter as much as happy paths. Assert on the exception type and message
(`pytest.raises(...) as exc_info`) and on logged output (`caplog`). GitHub API failures go through
`utils/github_exceptions.py`, so see the [error handling guide](error-handling.md) for what to expect.

## E2E Tests

The E2E harness lives in `test_project_repos/`. Its [README](https://github.com/hugo-valle/classdock/blob/main/test_project_repos/README.md)
documents the directory layout, scripts and configuration. Troubleshooting and scenario docs sit next to it in
`test_project_repos/docs/`.

### Full harness

```bash
cd test_project_repos
./scripts/run_full_test.sh

# Individual components
./scripts/test_installation.sh
./scripts/test_cli_interface.sh
python scripts/test_python_api.py
./scripts/test_integration.sh
```

### QA functional suite

The QA suite exercises every CLI command group (token management, assignments, repos, secrets,
automation, global options and error scenarios).

```bash
cd test_project_repos/qa_tests
./run_qa_tests.sh --all
./run_qa_tests.sh --token
./run_qa_tests.sh --repos --verbose
./run_qa_tests.sh --all --report --junit   # reports/qa_test_report_*.md and qa_junit_*.xml
./run_qa_tests.sh --all --dry-run          # preview without executing

# Or through the test runner
cd ../scripts && ./test_runner.sh qa-all --report
```

See the [QA automation guide](https://github.com/hugo-valle/classdock/blob/main/test_project_repos/docs/QA_AUTOMATION_GUIDE.md)
for suite dependencies, report formats and CI integration.

### Real-repository tests

`scripts/test_real_repo.sh` runs against live repositories. Configure
`sample_projects/real_repo/real_repo_info.conf` and put an instructor token in `instructor_token.txt`
(never commit it). The
[quick reference](https://github.com/hugo-valle/classdock/blob/main/test_project_repos/docs/REAL_REPO_QUICK_REFERENCE.md)
lists the options.

### Manual testing

Use a throwaway organization and assignment. A token is resolved from the environment, a token config file, or the
OS keychain, so test the storage method you changed.

**Pass criteria for any manual pass:**

1. `--help` and `--version` work for every command group.
2. `--verbose` and `--dry-run` behave correctly on each command group (dry-run must not change anything).
3. Each changed command works with valid input and fails cleanly with invalid input, missing token, or
   insufficient token scopes.

**Roster smoke test** (works from any directory once the Poetry environment is active):

```bash
poetry install
eval $(poetry env activate)

classdock roster init
printf 'email,name,github_username\njohn.doe@example.com,John Doe,johndoe\n' > /tmp/students.csv
classdock roster import /tmp/students.csv --org=YOUR_ORG
classdock roster list --org=YOUR_ORG
classdock roster status --org=YOUR_ORG

# With a real assignment directory
classdock repos fetch                      # discover repos
classdock roster sync --assignment=YOUR_ASSIGNMENT --org=YOUR_ORG
```

Check that `init` creates the database, `import` loads the CSV, `list` and `status` show the students,
and `sync` links repositories to students. To exercise the orchestrator, follow the
orchestrator setup in the roster guide and confirm the roster sync step runs. Also confirm existing commands still work when no
roster database exists (roster features are skipped silently). To start over, delete the roster database and
run `classdock roster init` again. See [Roster Sync](../workflows/roster-sync.md) for the full workflow.

## Continuous Integration

GitHub Actions runs the unit tier on pull requests and on `main`, across the supported Python versions. A merge
does not publish; releases are a separate step (see [Contributing](contributing.md)).

## Best Practices

- Keep unit tests fast (well under a second each) and isolated from the network and the real filesystem
  (`tmp_path`).
- Hold new code to 100% coverage and mock external dependencies.
- Clean up resources with fixtures (`yield` for teardown).
- Change code and tests together, and keep the pass rate at 100%.
