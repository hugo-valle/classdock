# GitHub Copilot Instructions for ClassDock

This document provides comprehensive instructions for AI assistants working on the `classdock` project.

## 🎯 Project Overview

**ClassDock** is a comprehensive Python CLI tool for automating GitHub Classroom assignment management. It provides modular functionality for repository operations, assignment orchestration, secret management, and automation workflows.

### Key Information
- **Language**: Python 3.10+
- **CLI Framework**: Typer + Click
- **Package Manager**: Poetry
- **Testing**: pytest (153+ comprehensive tests)
- **Architecture**: Modular package structure
- **Current Version**: 3.1.1b0

## 📁 Project Structure

```
classdock/
├── classdock/          # Main package
│   ├── __init__.py          # Package initialization
│   ├── __main__.py          # Entry point
│   ├── cli.py               # Main CLI interface (Typer)
│   ├── bash_wrapper.py      # Shell command wrapper
│   ├── config.py            # Configuration management
│   ├── utils.py             # Utility functions
│   ├── assignments/         # Assignment management
│   ├── automation/          # Scheduling and batch processing
│   ├── config/              # Configuration system
│   ├── repos/               # Repository operations
│   ├── scripts/             # Shell scripts
│   └── secrets/             # Secret management
├── tests/                   # Comprehensive test suite (153 tests)
├── docs/                    # Documentation
├── .github/workflows/       # CI/CD automation
└── pyproject.toml          # Poetry configuration
```

## 🔧 Development Guidelines

### Code Standards

1. **Python Style**:
   - Follow PEP 8 conventions
   - Use type hints where applicable
   - Maintain consistent docstring format
   - Prefer f-strings for string formatting

2. **CLI Development**:
   - Use Typer for command definitions
   - Organize commands in logical sub-applications
   - Provide helpful descriptions and examples
   - Include proper error handling

3. **Testing Requirements**:
   - Maintain 100% test pass rate
   - Write tests for all new functionality
   - Use pytest fixtures for setup/teardown
   - Follow existing test patterns

### Dependency Management

**Critical Compatibility Requirements**:
```toml
python = "^3.10"
click = ">=8.0.0,<8.2.0"      # Compatible with typer
typer = ">=0.12.0"            # Latest stable version
pyyaml = "^6.0.1"
requests = "^2.31.0"
```

**Never use**:
- `typer < 0.12.0` with `click >= 8.1.3` (causes make_metavar() errors)
- Unpinned major versions for core dependencies

### Version Management

- **Semantic Versioning**: `MAJOR.MINOR.PATCH-prerelease`
- **Pre-release Format**: `alpha.X`, `beta.X`, `rc.X`
- **Version Locations** (keep synchronized):
  - `pyproject.toml` → `version = "X.Y.Z"`
  - `classdock/__init__.py` → `__version__ = "X.Y.Z"`
  - `classdock/cli.py` → version command output

## 🏗️ Architecture Patterns

### CLI Structure
```python
# Main app with sub-applications
app = typer.Typer(help="Main description")
assignments_app = typer.Typer(help="Assignment commands")
repos_app = typer.Typer(help="Repository commands")

# Add sub-apps to main app
app.add_typer(assignments_app, name="assignments")
app.add_typer(repos_app, name="repos")

# Command pattern
@assignments_app.command()
def setup(
    dry_run: bool = typer.Option(False, help="Show what would be done"),
    verbose: bool = typer.Option(False, help="Enable verbose output")
):
    """Setup assignment configuration."""
    pass
```

### Configuration Management
- Use `ConfigLoader` class for configuration handling
- Support both file-based and environment variable configuration
- Provide sensible defaults for all options
- Validate configuration before use

### Error Handling
```python
try:
    # Operation
    pass
except SpecificException as e:
    logger.error(f"Operation failed: {e}")
    raise typer.Exit(code=1)
```

## 🌐 GitHub API Integration Methodology

**CRITICAL**: This section documents the systematic approach for updating modules to use the GitHub API, ensuring consistency, reliability, and maintainability across all integrations.

### Phase 1: Infrastructure Setup

#### 1.1 GitHub API Error Handling (Foundation)
- **Location**: `classdock/utils/github_exceptions.py`
- **Purpose**: Centralized error handling for all GitHub API interactions
- **Components**:
  ```python
  # Core exception classes
  class GitHubAPIError(Exception): pass
  class RateLimitError(GitHubAPIError): pass
  class AuthenticationError(GitHubAPIError): pass
  class ResourceNotFoundError(GitHubAPIError): pass
  class PermissionError(GitHubAPIError): pass
  
  # Smart retry decorator with exponential backoff
  @retry_on_github_error(max_retries=3, base_delay=1)
  def api_operation():
      # API call implementation
  ```

#### 1.2 HTTP Client Wrapper
- **Pattern**: Create wrapper around `requests` with GitHub-specific handling
- **Features**:
  - Automatic authentication header injection
  - Rate limiting respect (X-RateLimit headers)
  - Intelligent retry logic for transient failures
  - Standardized error response parsing
  - Request/response logging for debugging

### Phase 2: Module Conversion Strategy

#### 2.1 Analysis Phase
**Before touching any code:**
1. **Identify current bash commands** used in the module
2. **Map bash operations to GitHub API endpoints**
3. **Document required permissions** and scopes
4. **List all error scenarios** that need handling
5. **Determine data transformation** requirements

#### 2.2 Implementation Pattern
**Standard conversion workflow:**

1. **Import GitHub Error Handling**:
   ```python
   from classdock.utils.github_exceptions import (
       GitHubAPIError, RateLimitError, AuthenticationError,
       retry_on_github_error, handle_github_response
   )
   ```

2. **Replace BashWrapper with HTTP Client**:
   ```python
   # OLD: bash_wrapper.run(['gh', 'api', '/repos/owner/repo'])
   # NEW: 
   response = self._make_github_request('GET', f'/repos/{owner}/{repo}')
   ```

3. **Add Comprehensive Error Handling**:
   ```python
   @retry_on_github_error(max_retries=3)
   def _make_github_request(self, method: str, endpoint: str, **kwargs):
       try:
           response = requests.request(method, f"{self.base_url}{endpoint}", **kwargs)
           return handle_github_response(response)
       except requests.RequestException as e:
           raise GitHubAPIError(f"Request failed: {e}")
   ```

#### 2.3 Data Transformation
**Standardize response handling:**
- **Parse JSON responses** into Python dictionaries
- **Extract relevant fields** for business logic
- **Handle paginated responses** with proper iteration
- **Maintain backward compatibility** with existing interfaces

### Phase 3: Testing Integration

#### 3.1 Mock Strategy
**Comprehensive mocking approach:**
```python
@pytest.fixture
def mock_github_api(mocker):
    """Mock GitHub API responses for testing."""
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": 123, "name": "test-repo"}
    mock_response.headers = {"X-RateLimit-Remaining": "4999"}
    
    mocker.patch('requests.request', return_value=mock_response)
    return mock_response
```

#### 3.2 Test Categories
**Required test coverage:**
1. **Success scenarios** - Normal API operation
2. **Authentication failures** - Invalid token handling
3. **Rate limiting** - Retry logic validation
4. **Network failures** - Connection error handling
5. **Resource not found** - 404 response handling
6. **Permission errors** - 403 response handling
7. **Malformed responses** - Invalid JSON handling

### Phase 4: Module-Specific Patterns

#### 4.1 Repository Operations (`repos/`)
**Key API endpoints:**
- `GET /repos/{owner}/{repo}` - Repository information
- `GET /repos/{owner}/{repo}/collaborators` - Collaborator management
- `POST /repos/{owner}/{repo}/collaborators/{username}` - Add collaborators
- `GET /repos/{owner}/{repo}/contents/{path}` - File operations

**Bash to API mapping:**
```python
# OLD: gh repo view owner/repo --json name,description
# NEW: GET /repos/owner/repo -> response['name'], response['description']

# OLD: gh api repos/owner/repo/collaborators
# NEW: GET /repos/owner/repo/collaborators -> list of collaborator objects
```

#### 4.2 Secret Management (`secrets/`)
**Key API endpoints:**
- `GET /repos/{owner}/{repo}/actions/secrets` - List secrets
- `PUT /repos/{owner}/{repo}/actions/secrets/{secret_name}` - Update secret
- `GET /repos/{owner}/{repo}/actions/secrets/public-key` - Get public key

**Special considerations:**
- **Secret encryption** using repository public key
- **Base64 encoding** for secret values
- **Batch operations** for multiple secrets

#### 4.3 Assignment Management (`assignments/`)
**Integration points:**
- **Repository creation** via GitHub API
- **Template cloning** and customization
- **Webhook configuration** for assignment events
- **Issue/PR automation** for feedback

### Phase 5: Quality Assurance

#### 5.1 Code Review Checklist
**Before merging GitHub API integration:**
- [ ] **Error handling** covers all GitHub API error types
- [ ] **Retry logic** implemented with exponential backoff
- [ ] **Rate limiting** respected and handled gracefully
- [ ] **Authentication** properly configured and tested
- [ ] **Logging** adequate for debugging and monitoring
- [ ] **Tests** cover success and failure scenarios
- [ ] **Documentation** updated with new API usage
- [ ] **Backward compatibility** maintained where possible

#### 5.2 Performance Considerations
**Optimization strategies:**
- **Batch API calls** where possible to reduce requests
- **Cache responses** for frequently accessed data
- **Implement pagination** properly for large result sets
- **Use conditional requests** (ETags) to avoid unnecessary transfers
- **Monitor rate limit usage** and adjust request patterns

### Phase 6: Migration Execution

#### 6.1 Module Priority Order
**Recommended conversion sequence:**
1. **Core utilities** (`utils/github_exceptions.py`) - Foundation first
2. **Repository operations** (`repos/fetch.py`, `repos/collaborator.py`) - High usage
3. **Secret management** (`secrets/manager.py`) - Security critical
4. **Assignment operations** (`assignments/setup.py`) - Business logic
5. **Automation workflows** (`automation/`) - Lower priority

#### 6.2 Rollback Strategy
**Safety measures:**
- **Maintain bash wrapper** as fallback during transition
- **Feature flags** to enable/disable API usage
- **Comprehensive logging** for issue identification
- **Gradual rollout** with monitoring at each step

### Phase 7: Documentation and Maintenance

#### 7.1 API Documentation
**Required documentation:**
- **Endpoint mapping** - Bash command to API endpoint reference
- **Error scenarios** - Common failures and resolutions
- **Rate limiting** - Current usage and optimization strategies
- **Authentication** - Token requirements and permissions

#### 7.2 Monitoring and Observability
**Production considerations:**
- **API usage metrics** - Request counts and patterns
- **Error rate tracking** - Failure analysis and alerting
- **Performance monitoring** - Response times and bottlenecks
- **Rate limit tracking** - Usage against GitHub quotas

### Phase 8: Practical Implementation Examples

#### 8.1 Error Handling Infrastructure
**Real implementation from `classdock/utils/github_exceptions.py`:**
```python
class GitHubAPIError(Exception):
    """Base exception for GitHub API errors."""
    def __init__(self, message: str, response=None, status_code=None):
        super().__init__(message)
        self.response = response
        self.status_code = status_code

@retry_on_github_error(max_retries=3, base_delay=1)
def make_github_request(method: str, url: str, **kwargs) -> requests.Response:
    """Make authenticated GitHub API request with retry logic."""
    headers = kwargs.get('headers', {})
    headers.update({
        'Authorization': f'token {get_github_token()}',
        'Accept': 'application/vnd.github.v3+json'
    })
    kwargs['headers'] = headers
    
    response = requests.request(method, url, **kwargs)
    return handle_github_response(response)
```

#### 8.2 Module Conversion Example
**From `classdock/repos/fetch.py` - bash to API conversion:**
```python
# BEFORE: Bash wrapper approach
def get_repo_info(self, repo_url: str) -> dict:
    result = self.bash_wrapper.run(['gh', 'repo', 'view', repo_url, '--json', 'name,description'])
    return json.loads(result.stdout)

# AFTER: Direct GitHub API approach  
def get_repo_info(self, repo_url: str) -> dict:
    owner, repo = self._parse_repo_url(repo_url)
    response = self._make_github_request('GET', f'/repos/{owner}/{repo}')
    return {
        'name': response['name'],
        'description': response['description'],
        'clone_url': response['clone_url'],
        'private': response['private']
    }
```

#### 8.3 Testing Pattern Implementation
**Comprehensive test coverage example:**
```python
class TestReposFetch:
    def test_get_repo_info_success(self, mock_github_api, repo_fetch):
        """Test successful repository information retrieval."""
        mock_github_api.return_value.json.return_value = {
            'name': 'test-repo',
            'description': 'Test repository',
            'clone_url': 'https://github.com/owner/test-repo.git',
            'private': False
        }
        
        result = repo_fetch.get_repo_info('https://github.com/owner/test-repo')
        
        assert result['name'] == 'test-repo'
        assert result['description'] == 'Test repository'
        mock_github_api.assert_called_once()
    
    def test_get_repo_info_not_found(self, mock_github_api, repo_fetch):
        """Test repository not found error handling."""
        mock_github_api.side_effect = ResourceNotFoundError("Repository not found")
        
        with pytest.raises(ResourceNotFoundError):
            repo_fetch.get_repo_info('https://github.com/owner/nonexistent')
```

#### 8.4 Secrets Management API Pattern
**From `classdock/secrets/manager.py`:**
```python
def update_repository_secret(self, repo_url: str, secret_name: str, secret_value: str) -> bool:
    """Update a repository secret using GitHub API."""
    try:
        owner, repo = self._parse_repo_url(repo_url)
        
        # Get repository public key for encryption
        key_response = self._make_github_request(
            'GET', 
            f'/repos/{owner}/{repo}/actions/secrets/public-key'
        )
        
        # Encrypt secret value
        encrypted_value = self._encrypt_secret(secret_value, key_response['key'])
        
        # Update secret
        self._make_github_request(
            'PUT',
            f'/repos/{owner}/{repo}/actions/secrets/{secret_name}',
            json={
                'encrypted_value': encrypted_value,
                'key_id': key_response['key_id']
            }
        )
        return True
        
    except GitHubAPIError as e:
        logger.error(f"Failed to update secret {secret_name}: {e}")
        return False
```

#### 8.5 Rate Limiting Implementation
**Smart rate limiting with exponential backoff:**
```python
def retry_on_github_error(max_retries: int = 3, base_delay: float = 1):
    """Decorator for GitHub API retry logic with exponential backoff."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except RateLimitError as e:
                    if attempt == max_retries:
                        raise
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Rate limit hit, retrying in {delay}s...")
                    time.sleep(delay)
                except (ConnectionError, Timeout) as e:
                    if attempt == max_retries:
                        raise GitHubAPIError(f"Network error after {max_retries} retries: {e}")
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Network error, retrying in {delay}s...")
                    time.sleep(delay)
        return wrapper
    return decorator
```

## 🧪 Testing Patterns

### Test Organization
```python
# tests/test_<module>.py
import pytest
from classdock.<module> import Class

class TestClass:
    def test_method_success(self, mock_config):
        """Test successful operation."""
        pass
    
    def test_method_failure(self, mock_config):
        """Test error handling."""
        pass
```

### Fixture Usage
```python
# Use existing fixtures from conftest.py
def test_function(mock_config, temp_dir, mock_bash_wrapper):
    # Test implementation
    pass
```

### Test Categories
- **Unit Tests**: Individual component testing
- **Integration Tests**: Component interaction
- **CLI Tests**: Command-line interface validation
- **Error Tests**: Exception and error handling

### 🎯 Testing Strategy: Two-Tier Approach

This project uses a **two-tier testing strategy** with distinct but complementary testing environments:

#### **Tier 1: `tests/` - Developer Testing (Primary Development)**
- **Purpose**: Fast feedback during development, code validation, CI/CD integration
- **Technology**: Python pytest (603+ test functions, ~12K lines)
- **Scope**: Unit tests, integration tests, mocked dependencies
- **Target Audience**: Developers during active development
- **Execution**: `pytest tests/ -v` (runs in seconds)
- **Examples**:
  ```python
  def test_assignment_service_setup_with_url():
      service = AssignmentService(dry_run=True) 
      success, message = service.setup(url="https://classroom.github.com/a/test")
      assert "GitHub Classroom URL" in message
  ```

#### **Tier 2: `test_project_repos/` - End-to-End Validation (Release Testing)**
- **Purpose**: Real-world validation, user workflow testing, release qualification
- **Technology**: Bash scripts + Python (5.5K lines shell, 615 lines Python)
- **Scope**: Complete workflows, real GitHub repositories, actual environments
- **Target Audience**: QA engineers, release validation, user acceptance testing
- **Execution**: `cd test_project_repos && ./scripts/run_full_test.sh` (runs in minutes)
- **Examples**:
  ```bash
  # Tests real GitHub API integration, actual repository cloning
  classdock assignments setup --url "https://real-github-classroom-url"
  classdock assignments orchestrate --config real_assignment.conf
  ```

#### **When to Use Each Tier:**

**Use `tests/` for:**
- ✅ Daily development work
- ✅ Feature development and bug fixes  
- ✅ CI/CD pipeline integration
- ✅ Code review validation
- ✅ Component-level testing

**Use `test_project_repos/` for:**
- ✅ Pre-release validation
- ✅ User acceptance testing
- ✅ Cross-platform compatibility testing
- ✅ Real GitHub integration testing
- ✅ End-to-end workflow validation

#### **Testing Pyramid Implementation:**
```
     /\
    /  \  E2E Tests (test_project_repos/) 
   /____\  - Real workflows, GitHub repos, user scenarios
  /      \  Integration Tests (parts of tests/)
 /        \  - Service integration, CLI integration  
/          \ Unit Tests (most of tests/)
\__________/ - Methods, classes, isolated components
```

**Critical Note**: Both tiers are essential. `tests/` provides fast developer feedback, while `test_project_repos/` ensures real-world functionality. Maintain both but focus daily development on `tests/` tier.

## 📝 Documentation Standards

### Docstring Format
```python
def function_name(param1: str, param2: int = 0) -> bool:
    """
    Brief description of function purpose.
    
    Args:
        param1: Description of first parameter
        param2: Description of second parameter with default
        
    Returns:
        Description of return value
        
    Raises:
        SpecificException: When specific condition occurs
    """
    pass
```

### CLI Help Text
```python
@app.command()
def command_name(
    param: str = typer.Option(..., help="Clear, concise parameter description")
):
    """
    Command description with example usage.
    
    Example:
        classdock command-name --param value
    """
    pass
```

## 🚀 CI/CD Integration

### GitHub Actions Workflow
- **Triggers**: Git tags (`v*`), main branch updates to `pyproject.toml`
- **Testing**: Multi-Python versions (3.10, 3.11, 3.12)
- **Publishing**: Automated PyPI publication
- **Requirements**: `PYPI_API_TOKEN` repository secret

### Release Process
1. Update version in all locations
2. Update CHANGELOG.md
3. Commit changes: `git commit -m "bump: version X.Y.Z"`
4. Create tag: `git tag vX.Y.Z`
5. Push: `git push origin main --tags`
6. CI/CD handles the rest automatically

## 🔍 Common Issues and Solutions

### Typer/Click Compatibility
- **Problem**: `make_metavar() missing argument` error
- **Solution**: Use `typer >= 0.12.0` with `click >= 8.0.0,<8.2.0`

### Test Failures
- **Check**: Fixture configuration in `conftest.py`
- **Verify**: Mock objects are properly configured
- **Ensure**: Test isolation (no shared state)

### Import Errors
- **Verify**: Package structure matches imports
- **Check**: `__init__.py` files exist in all packages
- **Confirm**: Dependencies are properly installed

### CLI Issues
- **Test locally**: `poetry run classdock --help`
- **Check logs**: Enable verbose mode for debugging
- **Verify config**: Ensure configuration files are valid

🛠️ Workflow Authoring Guidelines

This project uses GitHub Actions workflows to automate testing, packaging, and deployment. To keep workflows clean, maintainable, and consistent, follow these rules:

⸻

📂 Workflow File Format
        •       Location: .github/workflows/*.yml
        •       Each workflow should have:
        •       Name: A descriptive name (e.g., CI - Tests, Release Build).
        •       Triggers: Define when it runs (push, pull_request, schedule).
        •       Jobs: Break logic into jobs (e.g., test, build, deploy).
        •       Steps: Keep inline steps short, clean, and readable.

Example:

name: CI - Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: poetry install
      - run: poetry run pytest -v


⸻

📏 Step Size Rule
        •       Keep inline run: scripts ≤ 6 lines of code.
        •       If logic is more than 6 lines, move it into a dedicated script.

Why?
        •       Keeps workflows readable.
        •       Easier to reuse across workflows.
        •       Simplifies debugging and version control.

⸻

📂 Script Location
        •       Long scripts must live under:

.github/scripts/


        •       Scripts must be executable (chmod +x) and well-commented.
        •       Use descriptive names (e.g., setup-poetry.sh, publish-pypi.sh).

Example (workflow referencing a script):

- name: Publish to PyPI
  run: ./.github/scripts/publish-pypi.sh


⸻

## ✅ Best Practices
        •       Use official actions (like actions/checkout) when available.
        •       Use matrix builds for multiple Python versions.
        •       Cache dependencies where possible (actions/cache).
        •       Fail fast: configure set -e in scripts to stop on errors.
        •       Log clearly: echo progress messages for better CI visibility.
⸻

### Structure & Size
	•	Modules: aim for ≤ 300–400 lines; split by concern (e.g., cli.py, services.py, io.py, config.py).
	•	Functions: target ≤ 30–40 lines; early-returns; single responsibility.
	•	Classes: small, focused; prefer plain functions for stateless helpers.
	•	Cyclomatic complexity: keep ≤ 10 (use radon to check).

### Reusability & Separation
	•	Keep business logic out of CLI command handlers—put it in services/ or core/.
	•	CLI layer does: parse args → call service → format output → set exit code.
	•	Make services pure & testable; pass dependencies via parameters (or lightweight DI).
	•	Provide a stable Python API so the same code can back GUI/Web later.

### CLI UX Conventions
	•	Global flags: --version, --help, --verbose/-v (stackable), --quiet, --debug, --dry-run.
	•	Subcommands > flags for clarity: tool repos clone, not tool --clone.
	•	Print human-friendly output to stdout; errors to stderr; exit with non-zero on failure.
	•	Support file/dir globs, stdin (-), and JSON/YAML output via --format.
	•	Be cross-platform (paths via pathlib; avoid bashisms; use shutil.which).

### Config & Env
	•	Precedence: CLI flags > env vars > config file > defaults.
	•	Use pydantic-settings or dynaconf/django-environ-style approach.
	•	Support XDG locations (Linux/macOS) and %APPDATA% (Windows).

### Logging & Errors
	•	Use Loguru or logging with a console handler (--debug sets level to DEBUG).
	•	Don’t traceback on user errors—emit clear messages; show traceback only with --debug.
	•	Map known failures to consistent exit codes (e.g., 2=usage, 3=not found, 4=network).

### I/O, Subprocess, Perf
	•	For subprocesses use subprocess.run(..., check=True, text=True, capture_output=True); set timeouts.
	•	Stream large outputs; don’t load big files fully if avoidable.
	•	Gracefully handle Ctrl+C (KeyboardInterrupt) and SIGTERM; clean temp files.

### Type Safety & Style
	•	Type hints everywhere; run mypy (or pyright) in CI.
	•	ruff + black for lint/format; pre-commit hooks enabled.
	•	Avoid global state; pure functions where possible.

### Testing
	•	pytest with:
	•	Unit tests for services (no CLI).
	•	CLI tests using typer.testing.CliRunner / Click runner.
	•	Golden tests (snapshot output) for stable commands.
	•	Mocks for filesystem (pyfakefs) and network (responses/httpx-mock).
	•	Coverage: enforce ≥ 85% line coverage (exclude CLI glue if needed).
	•	Test matrix: Python 3.9–3.11; Linux/macOS/Windows if possible.

### Packaging & Distribution
	•	Use pyproject.toml; build with hatchling or setuptools.
	•	Entry point:

```bash
[project.scripts]
mytool = "mytool.cli:app"
```

	•	Pin minimal versions; avoid heavy deps; keep install fast.
	•	Version with SemVer; git tags drive release automation.

### Security & Reliability
	•	Never log secrets; redact tokens.
	•	Validate all external inputs (files, URLs).
	•	Add retries with backoff for network calls (e.g., tenacity).
	•	Respect proxies and SSL; verify certificates.

### Helpful Snippets

Typer command skeleton (clean separation):
```python
# cli.py
import sys, typer
from loguru import logger
from mytool.services.repos import clone_all
app = typer.Typer()

@app.callback()
def main(verbose: int = typer.Option(0, "--verbose", "-v", count=True), debug: bool = False):
    logger.remove()
    level = "DEBUG" if debug or verbose >= 2 else "INFO" if verbose == 1 else "WARNING"
    logger.add(sys.stderr, level=level, enqueue=True)

@app.command()
def clone(org: str, assignment: str, students: str, dest: str = "./repos", dry_run: bool = False) -> None:
    try:
        result = clone_all(org, assignment, students_path=students, dest=dest, dry_run=dry_run)
        typer.echo(result.summary)
    except Exception as exc:
        logger.exception("Clone failed")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
``` 
Service (pure, testable):

```python
# services/repos.py
from pathlib import Path
from dataclasses import dataclass

@dataclass
class CloneResult:
    total: int
    ok: int
    failed: int
    @property
    def summary(self) -> str:
        return f"Cloned: {self.ok}/{self.total}, failed: {self.failed}"

def clone_all(org: str, assignment: str, students_path: str, dest: str, dry_run: bool) -> CloneResult:
    students = [s.strip() for s in Path(students_path).read_text().splitlines() if s.strip()]
    ok = failed = 0
    Path(dest).mkdir(parents=True, exist_ok=True)
    for s in students:
        repo = f"https://github.com/{org}/{assignment}-{s}.git"
        if dry_run:
            ok += 1
            continue
        # call git via helper; raise on failure
        from mytool.util.git import safe_clone
        ok += 1 if safe_clone(repo, Path(dest) / f"{assignment}-{s}") else 0
    failed = len(students) - ok
    return CloneResult(total=len(students), ok=ok, failed=failed)

CLI test:

# tests/test_cli.py
from typer.testing import CliRunner
from mytool.cli import app

def test_clone_help():
    runner = CliRunner()
    result = runner.invoke(app, ["clone", "--help"])
    assert result.exit_code == 0
    assert "assignment" in result.stdout
```

⸻

## 📚 Key Resources

### Documentation Files
- `docs/PYPI_PUBLICATION.md` - PyPI publishing guide
- `docs/CICD_WORKFLOW.md` - CI/CD pipeline documentation
- `docs/PROJECT_STATUS_V3_ALPHA1.md` - Current project status

### Important Files
- `pyproject.toml` - Project configuration and dependencies
- `conftest.py` - Test fixtures and configuration
- `.github/workflows/publish.yml` - Automated publishing workflow

### External Links
- **PyPI Package**: https://pypi.org/project/classdock/
- **Repository**: https://github.com/hugo-valle/classdock
- **Documentation**: Repository README and docs/ folder

## ⚠️ Critical Reminders

1. **Always run tests** before making changes: `poetry run pytest tests/ -v`
2. **Update version** in all three locations when bumping
3. **Test CLI locally** after dependency changes
4. **Check compatibility** when updating typer/click versions
5. **Follow semantic versioning** for all releases
6. **Maintain 100% test pass rate** - no exceptions
7. **Use Poetry** for all dependency management
8. **Test in clean environment** before publishing

## 🎯 Development Workflow

1. **Start**: Create feature branch from main
2. **Develop**: Implement changes with tests
3. **Test**: Run comprehensive test suite
4. **Verify**: Test CLI functionality locally
5. **Update**: Bump version if needed
6. **Document**: Update relevant documentation
7. **Commit**: Use conventional commit messages
8. **PR**: Create pull request with clear description
9. **Merge**: Merge to main after review
10. **Release**: Tag for automated publishing

---

*This project maintains high standards for code quality, testing, and documentation. Always prioritize reliability and user experience in all changes.*
