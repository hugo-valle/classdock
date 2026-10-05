# QA Test Automation Guide

## Overview

This guide provides comprehensive documentation for automating QA functional tests in the `classdock` project. The QA test automation infrastructure enables running functional tests individually, in groups, or as complete test suites with flexible orchestration options.

**Relationship to the testing guide:** the [testing guide](../../docs-site/development/testing.md) covers how to run and write tests; this guide covers orchestration, CI/CD integration, and batch execution of the QA suite.

**Key Features:**
- 🎯 **Modular Execution**: Run individual test suites or complete QA test battery
- 🔄 **Multiple Orchestrators**: Three levels of test execution (standalone, orchestrated, integrated)
- 📊 **Comprehensive Reporting**: Markdown, HTML, and JUnit XML reports
- 🚀 **CI/CD Integration**: GitHub Actions workflow support
- 🛠️ **Developer-Friendly**: Dry-run mode, verbose logging, skip mechanisms

---

## Quick Start

### Running QA Tests

**Run all QA tests:**
```bash
cd test_project_repos/qa_tests
./run_qa_tests.sh --all
```

**Run specific test suite:**
```bash
./run_qa_tests.sh --token
./run_qa_tests.sh --assignments
./run_qa_tests.sh --repos --verbose
```

**Run with reporting:**
```bash
./run_qa_tests.sh --all --report --junit
```

**Dry-run to preview:**
```bash
./run_qa_tests.sh --all --dry-run
```

### Integration with Test Runner

**Run QA tests through test runner:**
```bash
cd test_project_repos/scripts
./test_runner.sh qa-all
./test_runner.sh qa-token --verbose
./test_runner.sh qa-assignments --report
```

**Run all tests including QA:**
```bash
./test_runner.sh all --report --junit
```

---

## Test Infrastructure

### Three-Tier Orchestration Architecture

The QA test infrastructure uses a three-tier architecture for maximum flexibility:

```
┌─────────────────────────────────────────────────────────┐
│ Tier 1: Test Runner (scripts/test_runner.sh)          │
│ - Entry point for all testing                          │
│ - Supports: installation, cli, python-api, integration │
│ - Integrated QA: qa-all, qa-token, qa-assignments, etc│
│ - Report generation, environment setup, cleanup        │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│ Tier 2: QA Orchestrator (qa_tests/run_qa_tests.sh)    │
│ - Dedicated QA test orchestration                      │
│ - Suite registry with metadata (duration, deps)        │
│ - Sequential and parallel execution modes              │
│ - Multi-format reporting (Markdown, JUnit, HTML)       │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│ Tier 3: Test Suites (qa_tests/test_*.sh)              │
│ - token_management.sh                                   │
│ - assignments_commands.sh                               │
│ - repos_commands.sh                                     │
│ - secrets_commands.sh                                   │
│ - automation_commands.sh                                │
│ - global_options.sh                                     │
│ - error_scenarios.sh                                    │
└─────────────────────────────────────────────────────────┘
```

### Directory Structure

```
test_project_repos/
├── scripts/
│   ├── test_runner.sh          # Main test orchestrator (Tier 1)
│   ├── run_full_test.sh        # Legacy full test runner
│   └── config.sh               # Common configuration
├── qa_tests/
│   ├── run_qa_tests.sh         # QA test orchestrator (Tier 2)
│   ├── test_token_management.sh      # Token QA tests (Tier 3)
│   ├── test_assignments_commands.sh  # Assignments QA tests
│   ├── test_repos_commands.sh        # Repos QA tests
│   ├── test_secrets_commands.sh      # Secrets QA tests
│   ├── test_automation_commands.sh   # Automation QA tests
│   ├── test_global_options.sh        # Global options QA tests
│   ├── test_error_scenarios.sh       # Error handling QA tests
│   ├── lib/
│   │   ├── test_helpers.sh     # Common test utilities
│   │   ├── mock_helpers.sh     # Mock GitHub API calls
│   │   └── assertion_helpers.sh # Test assertions
│   └── fixtures/
│       ├── test_assignment_config.conf # Test configs
│       └── test_student_lists/        # Student fixtures
└── docs/
    └── QA_AUTOMATION_GUIDE.md  # This automation guide
```

---

## Running QA Tests

### Using QA Orchestrator (run_qa_tests.sh)

The QA orchestrator provides dedicated QA test execution with advanced features.

#### Basic Execution

**Run all QA tests:**
```bash
cd test_project_repos/qa_tests
./run_qa_tests.sh --all
```

**Run specific test suites:**
```bash
# Token management tests
./run_qa_tests.sh --token

# Assignments commands tests
./run_qa_tests.sh --assignments

# Multiple suites
./run_qa_tests.sh --token --assignments --repos
```

#### Advanced Options

**Verbose output:**
```bash
./run_qa_tests.sh --all --verbose
```

**Stop on first failure:**
```bash
./run_qa_tests.sh --all --stop-on-failure
```

**Dry-run (preview without execution):**
```bash
./run_qa_tests.sh --all --dry-run
```

**Parallel execution (experimental):**
```bash
./run_qa_tests.sh --all --parallel
```

#### Reporting Options

**Generate Markdown report:**
```bash
./run_qa_tests.sh --all --report
# Creates: reports/qa_test_report_YYYYMMDD_HHMMSS.md
```

**Generate JUnit XML report:**
```bash
./run_qa_tests.sh --all --junit
# Creates: reports/qa_junit_YYYYMMDD_HHMMSS.xml
```

**Generate both reports:**
```bash
./run_qa_tests.sh --all --report --junit
```

### Using Test Runner (test_runner.sh)

The test runner provides integrated execution with traditional test suites.

#### Individual QA Suites

```bash
cd test_project_repos/scripts
./test_runner.sh qa-token
./test_runner.sh qa-assignments --verbose
./test_runner.sh qa-repos --report
```

#### All QA Tests

```bash
./test_runner.sh qa-all
./test_runner.sh qa-all --report --junit
```

#### Complete Test Battery

Run all tests (installation, CLI, Python API, integration, real-repo, QA):
```bash
./test_runner.sh all --report --junit
```

---

## Test Suites

### Available QA Test Suites

| Suite | Script | Tests | Duration | Description |
|-------|--------|-------|----------|-------------|
| **token** | `test_token_management.sh` | 32 | ~2 min | GitHub token validation, verification, error handling |
| **assignments** | `test_assignments_commands.sh` | 48 | ~5 min | Assignment setup, orchestration, management commands |
| **repos** | `test_repos_commands.sh` | 42 | ~4 min | Repository operations, cloning, collaboration |
| **secrets** | `test_secrets_commands.sh` | 38 | ~3 min | Secret management, updates, batch operations |
| **automation** | `test_automation_commands.sh` | 25 | ~3 min | Cron scheduling, batch processing |
| **global-options** | `test_global_options.sh` | 15 | ~1 min | CLI global flags (--verbose, --dry-run, --help) |
| **error-scenarios** | `test_error_scenarios.sh` | 30 | ~2 min | Error handling, edge cases, invalid inputs |

### Suite Dependencies

**Token Suite (Foundation):**
- No dependencies
- Tests GitHub token validation
- Required for all other suites that use GitHub API

**Assignments Suite:**
- Dependencies: token (for GitHub operations)
- Tests assignment lifecycle (setup, orchestration, management)

**Repos Suite:**
- Dependencies: token (for repository operations)
- Tests repository cloning, collaboration, management

**Secrets Suite:**
- Dependencies: token, repos (needs repositories to manage secrets)
- Tests secret creation, updates, batch operations

**Automation Suite:**
- Dependencies: assignments (tests automation of assignment workflows)
- Tests cron scheduling, batch processing

**Global Options Suite:**
- No dependencies
- Tests CLI global flags across all commands

**Error Scenarios Suite:**
- Dependencies: all other suites (tests error handling across all features)
- Tests invalid inputs, edge cases, error recovery

### Test Statistics

**Current Test Coverage (as of v3.0.1-alpha.2):**
- Total tests: 230
- Passing tests: 197 (85.7%)
- Skipped tests: 33 (14.3%)
- Failed tests: 0 (0%)

**Skip Reasons:**
- GitHub API integration required: 18 tests
- Real repository operations required: 9 tests
- Manual intervention required: 6 tests

**Target Coverage:**
- Pre-release goal: 100% passing (0 skipped)
- All skipped tests to be enabled with proper fixtures

---

## Reporting

### Report Formats

The QA test infrastructure supports three report formats:

#### 1. Markdown Reports

**Generated by:** `run_qa_tests.sh --report`

**Location:** `test_project_repos/reports/qa_test_report_YYYYMMDD_HHMMSS.md`

**Content:**
- Executive summary with pass/fail statistics
- Test suite results table
- Execution time breakdown
- Test environment details
- Detailed test output for failures

**Example:**
```markdown
# QA Test Report - classdock

Generated: 2024-01-15 14:30:45

## Executive Summary
- **Total Test Suites**: 7
- **Passed**: 7
- **Failed**: 0
- **Total Execution Time**: 20 minutes
- **Overall Status**: ✅ PASSED

## Test Suite Results
| Suite | Status | Duration | Tests Passed | Tests Failed |
|-------|--------|----------|--------------|--------------|
| Token Management | ✅ PASSED | 2m 15s | 32 | 0 |
| Assignments Commands | ✅ PASSED | 5m 30s | 48 | 0 |
...
```

#### 2. JUnit XML Reports

**Generated by:** `run_qa_tests.sh --junit`

**Location:** `test_project_repos/reports/qa_junit_YYYYMMDD_HHMMSS.xml`

**Purpose:** CI/CD integration, test result tracking, test history

**Format:** Standard JUnit XML compatible with:
- GitHub Actions
- Jenkins
- CircleCI
- Azure DevOps
- GitLab CI

**Example:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<testsuites name="QA Tests" tests="230" failures="0" skipped="33" time="1200">
  <testsuite name="Token Management" tests="32" failures="0" skipped="0" time="135">
    <testcase classname="qa_tests.token_management" name="test_token_validation" time="2.5"/>
    <testcase classname="qa_tests.token_management" name="test_token_verification" time="3.1"/>
    ...
  </testsuite>
  ...
</testsuites>
```

#### 3. HTML Reports

**Generated by:** `test_runner.sh --report`

**Location:** `test_project_repos/reports/test_runner_report_YYYYMMDD_HHMMSS.html`

**Content:**
- Interactive HTML with CSS styling
- Pass/fail status with color coding
- Test suite breakdown
- Environment information
- Clickable sections for drill-down

---

## CI/CD Integration

### GitHub Actions Workflow

**Workflow file:** `.github/workflows/qa_tests.yml`

```yaml
name: QA Functional Tests

on:
  push:
    branches: [ main, feature/* ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC

jobs:
  qa-tests:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    
    - name: Install classdock
      run: |
        pip install -e .
    
    - name: Run QA tests
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        GH_TOKEN: ${{ secrets.GH_TOKEN }}
      run: |
        cd test_project_repos/qa_tests
        ./run_qa_tests.sh --all --report --junit
    
    - name: Publish test results
      uses: EnricoMi/publish-unit-test-result-action@v2
      if: always()
      with:
        junit_files: 'test_project_repos/reports/qa_junit_*.xml'
    
    - name: Upload test reports
      uses: actions/upload-artifact@v4
      if: always()
      with:
        name: qa-test-reports
        path: test_project_repos/reports/
```

### Running in CI

**Prerequisites:**
- Set `GITHUB_TOKEN` secret (for GitHub API operations)
- Set `GH_TOKEN` secret (for GitHub operations)
- Install `classdock` package
- Set up Python 3.10+ environment

**CI Execution:**
```bash
# In CI environment
cd test_project_repos/qa_tests
./run_qa_tests.sh --all --report --junit
```

**CI Exit Codes:**
- `0`: All tests passed
- `1`: One or more tests failed
- `2`: Test execution error (e.g., missing dependencies)

---

## Troubleshooting

### Common Issues

#### Issue: Tests fail with "GitHub token not found"

**Solution:**
```bash
# Set GitHub token
export GITHUB_TOKEN="your-github-token"
export GH_TOKEN="your-course-token"

# Or use test helper
cd test_project_repos/qa_tests
source lib/test_helpers.sh
setup_test_github_token
```

#### Issue: Tests skip with "Real repository required"

**Solution:**
```bash
# Create real test repositories (one-time setup)
cd test_project_repos/qa_tests/fixtures
./setup_real_repos.sh

# Or set environment to use fixtures
export USE_REAL_REPOS=false  # Use mocked operations
```

#### Issue: Parallel execution causes race conditions

**Solution:**
```bash
# Use sequential execution
./run_qa_tests.sh --all  # Default is sequential

# Or isolate parallel tests
./run_qa_tests.sh --token --assignments  # Parallel-safe
./run_qa_tests.sh --secrets  # Run separately if issues persist
```

#### Issue: Reports not generated

**Solution:**
```bash
# Ensure reports directory exists
mkdir -p test_project_repos/reports

# Check permissions
chmod 755 test_project_repos/reports

# Verify report flags
./run_qa_tests.sh --all --report --junit --verbose
```

### Debug Mode

**Enable verbose output:**
```bash
./run_qa_tests.sh --all --verbose
```

**Enable bash debug mode:**
```bash
bash -x test_project_repos/qa_tests/run_qa_tests.sh --all
```

**Check test execution:**
```bash
# Dry-run to see what will execute
./run_qa_tests.sh --all --dry-run

# Run single suite with verbose
./run_qa_tests.sh --token --verbose
```

### Log Files

**Test execution logs:**
- Location: `test_project_repos/qa_tests/logs/`
- Format: `qa_test_YYYYMMDD_HHMMSS.log`
- Content: Full test output, errors, warnings

**Accessing logs:**
```bash
# View latest log
tail -f test_project_repos/qa_tests/logs/qa_test_*.log

# Search for errors
grep -r "ERROR" test_project_repos/qa_tests/logs/

# Check specific test output
grep "test_token_validation" test_project_repos/qa_tests/logs/qa_test_*.log
```

---

## Advanced Usage

### Custom Test Execution

**Run specific test within a suite:**
```bash
cd test_project_repos/qa_tests
./test_token_management.sh  # Run single suite directly
```

**Run with custom environment:**
```bash
export GITHUB_TOKEN="test-token"
export USE_REAL_REPOS=false
./run_qa_tests.sh --all
```

**Run with custom timeout:**
```bash
timeout 30m ./run_qa_tests.sh --all
```

### Parallel Execution

**Enable parallel mode (experimental):**
```bash
./run_qa_tests.sh --all --parallel
```

**How it works:**
- Independent test suites run concurrently
- Dependent suites run sequentially (e.g., secrets waits for repos)
- Uses GNU Parallel or background jobs
- Faster execution but requires more resources

**Limitations:**
- Shared state can cause race conditions
- Log output may be interleaved
- Debug mode less useful
- Not recommended for local development

**Best practice:** Use parallel mode in CI for faster builds, sequential mode for local development.

### Custom Reporting

**Generate custom report:**
```bash
# Run tests with JSON output
./run_qa_tests.sh --all --verbose > qa_output.txt

# Parse output to custom format
python scripts/parse_qa_results.py qa_output.txt --format html
```

**Aggregate multiple runs:**
```bash
# Combine multiple JUnit reports
junitparser merge reports/qa_junit_*.xml > reports/combined_results.xml
```

---

## Best Practices

### Development Workflow

**Before committing code:**
```bash
# Run affected test suites
cd test_project_repos/qa_tests
./run_qa_tests.sh --token --assignments  # If you changed token/assignment code
```

**Before creating PR:**
```bash
# Run all QA tests
./run_qa_tests.sh --all --report
# Review report for failures
```

**Before release:**
```bash
# Run complete test battery
cd test_project_repos/scripts
./test_runner.sh all --report --junit
# Ensure 100% pass rate
```

### CI/CD Best Practices

**Trigger QA tests on:**
- Every push to the main branch
- Every pull request
- Nightly builds (scheduled workflow)
- Pre-release tags

**Parallel CI jobs:**
```yaml
strategy:
  matrix:
    suite: [token, assignments, repos, secrets, automation, global-options, error-scenarios]

steps:
- name: Run QA suite
  run: ./run_qa_tests.sh --${{ matrix.suite }}
```

**Artifact preservation:**
```yaml
- name: Upload reports
  uses: actions/upload-artifact@v4
  if: always()
  with:
    name: qa-reports-${{ matrix.suite }}
    path: reports/
```

### Test Maintenance

**Update fixtures regularly:**
```bash
# Update test URLs

# Update test configurations
vim qa_tests/fixtures/test_assignment_config.conf
```

**Review skip reasons:**
```bash
# Find all skipped tests
grep -r "skip_test" qa_tests/test_*.sh

# Track skip metrics
./run_qa_tests.sh --all --report | grep "Skipped"
```

**Update test counts:**
```bash
# After adding tests, update documentation
vim docs/QA_TEST_CERTIFICATION_RESULTS.md
vim docs/QA_AUTOMATION_GUIDE.md
```

---

## Related Documentation

- **[Testing guide](../../docs-site/development/testing.md)**: Contributor testing guide
- **[QA_TEST_CERTIFICATION_RESULTS.md](QA_TEST_CERTIFICATION_RESULTS.md)**: Latest test certification results
- **[README.md](../README.md)**: Main project documentation with quick start

---

## Summary

The QA test automation infrastructure provides:
- ✅ **Flexible execution**: Run individual suites or complete battery
- ✅ **Three-tier architecture**: Standalone, orchestrated, and integrated execution
- ✅ **Comprehensive reporting**: Markdown, HTML, JUnit XML formats
- ✅ **CI/CD ready**: GitHub Actions workflows and exit codes
- ✅ **Developer-friendly**: Dry-run, verbose, skip mechanisms

**Next Steps:**
1. Run QA tests locally: `./run_qa_tests.sh --all --dry-run`
2. Execute full test suite: `./run_qa_tests.sh --all --report`
3. Integrate with CI: Add `.github/workflows/qa_tests.yml`
4. Review results: Check `reports/qa_test_report_*.md`

For questions or issues, see the troubleshooting section or refer to the related documentation.
