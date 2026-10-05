# 🧪 Local Testing Workflow for ClassDock

This directory contains comprehensive testing tools and documentation for validating the `classdock` Python package before releases.

## Directory Structure

```
test_project_repos/
├── README.md                    # This file - overview and usage
├── docs/                        # Comprehensive documentation
│   ├── TESTING_GUIDE.md         # Detailed testing procedures (430+ lines)
│   ├── TEST_SCENARIOS.md        # Test scenario documentation (320+ lines)
│   └── TROUBLESHOOTING.md       # Issue resolution guide (490+ lines)
├── scripts/                     # Test automation scripts (all executable)
│   ├── run_full_test.sh         # Main test orchestration (400+ lines)
│   ├── config.sh                # Configuration management (200+ lines)
│   ├── setup_test_env.sh        # Environment setup (250+ lines)
│   ├── test_installation.sh     # Package installation testing (300+ lines)
│   ├── test_cli_interface.sh    # CLI functionality testing (400+ lines)
│   ├── test_python_api.py       # Python API testing (330+ lines)
│   ├── test_integration.sh      # Integration testing (350+ lines)
│   ├── test_real_repo.sh        # Real repository testing (600+ lines)
│   ├── test_runner.sh           # Individual test suite runner (400+ lines)
│   └── cleanup.sh               # Environment cleanup (300+ lines)
├── sample_projects/             # Test project examples
│   ├── basic_assignment/        # Simple assignment example
│   │   ├── assignment.conf      # Basic configuration
│   │   ├── README.md            # Assignment instructions
│   │   └── src/main.py          # Starter code
│   ├── advanced_assignment/     # Complex assignment example
│   │   └── assignment.conf      # Advanced configuration
│   ├── real_repo/               # Real repository testing configuration
│   │   ├── real_repo_info.conf  # Real repository configuration
│   │   └── instructor_token.txt # GitHub token for real testing
│   └── error_scenarios/         # Error condition examples (auto-generated)
├── qa_tests/                    # QA functional test suite (230 tests)
│   ├── run_qa_tests.sh          # QA test orchestrator (716 lines)
│   ├── test_token_management.sh # Token validation tests (32 tests)
│   ├── test_assignments_commands.sh # Assignment tests (48 tests)
│   ├── test_repos_commands.sh   # Repository tests (42 tests)
│   ├── test_secrets_commands.sh # Secret management tests (38 tests)
│   ├── test_automation_commands.sh # Automation tests (25 tests)
│   ├── test_global_options.sh   # Global option tests (15 tests)
│   ├── test_error_scenarios.sh  # Error handling tests (30 tests)
│   ├── lib/                     # Test utilities and helpers
│   │   ├── test_helpers.sh      # Common test functions
│   │   ├── mock_helpers.sh      # GitHub API mocks
│   │   └── assertion_helpers.sh # Test assertions
│   └── fixtures/                # Test data and configurations
│       ├── test_assignment_config.conf # Test configurations
│       └── test_student_lists/  # Student roster fixtures
└── reports/                     # Generated test reports (auto-created)
    ├── html/                    # HTML test reports
    ├── junit/                   # JUnit XML reports
    └── logs/                    # Test execution logs
```

## 🚀 Quick Start

### Run Complete Test Suite

```bash
# From the classdock root directory
cd test_project_repos
./scripts/run_full_test.sh
```

### Run Individual Test Components

```bash
# Test package installation
./scripts/test_installation.sh

# Test CLI interface
./scripts/test_cli_interface.sh

# Test Python API
python scripts/test_python_api.py

# Test integration scenarios
./scripts/test_integration.sh
```

## 📋 Test Coverage

### ✅ Installation Testing
- Package building with Poetry
- Clean environment installation
- Dependency resolution validation
- Cross-platform compatibility

### ✅ CLI Interface Testing
- Command structure validation
- Help system functionality
- Subcommand organization
- Error handling and user feedback

### ✅ Python API Testing
- Module imports and exports
- Core functionality validation
- Configuration system testing
- Logging and error handling

### ✅ Integration Testing
- Real-world workflow scenarios
- Sample project configurations
- End-to-end command execution
- Error recovery and validation

### ✅ Real Repository Testing
- Actual GitHub repository cloning and testing
- Real workflow validation with live repositories
- Conda environment setup and isolation
- Complete assignment configuration generation
- End-to-end testing with real data
- Automatic cleanup of test environments

### ✅ QA Functional Testing
- Comprehensive command-line interface testing
- Token management and GitHub API integration
- Assignment lifecycle operations (setup, orchestration, management)
- Repository operations (cloning, collaboration, secret management)
- Automation workflows (cron scheduling, batch processing)
- Global CLI options and error scenario validation
- 230 functional tests with 85.7% passing rate (197 passed, 33 skipped)
- Multi-format reporting (Markdown, HTML, JUnit XML)

## 🎯 Usage Scenarios

### QA Functional Testing (Featured!)

**Quick Start:**
```bash
# Run all QA tests with reporting
cd qa_tests
./run_qa_tests.sh --all --report --junit

# Run specific test suites
./run_qa_tests.sh --token              # Token management tests
./run_qa_tests.sh --assignments        # Assignment commands tests
./run_qa_tests.sh --repos              # Repository operations tests
./run_qa_tests.sh --secrets            # Secret management tests

# Dry-run to preview tests
./run_qa_tests.sh --all --dry-run

# Integrated execution through test runner
cd ../scripts
./test_runner.sh qa-all                # Run all QA tests
./test_runner.sh qa-token --verbose    # Run token tests with verbose output
```

**Available Test Suites:**
| Suite | Tests | Duration | Description |
|-------|-------|----------|-------------|
| **token** | 32 | ~2 min | GitHub token validation and verification |
| **assignments** | 48 | ~5 min | Assignment setup, orchestration, management |
| **repos** | 42 | ~4 min | Repository cloning and collaboration |
| **secrets** | 38 | ~3 min | Secret management and batch operations |
| **automation** | 25 | ~3 min | Cron scheduling and automation workflows |
| **global-options** | 15 | ~1 min | CLI global flags (--verbose, --dry-run, etc.) |
| **error-scenarios** | 30 | ~2 min | Error handling and edge cases |

**Advanced Usage:**
```bash
# Run with comprehensive reporting
./run_qa_tests.sh --all --report --junit --verbose

# Stop on first failure for quick debugging
./run_qa_tests.sh --all --stop-on-failure

# Parallel execution (experimental, faster in CI)
./run_qa_tests.sh --all --parallel
```

**QA Test Infrastructure:**
- **Test Suites**: `qa_tests/test_*.sh` (7 comprehensive test suites)
- **Orchestrator**: `qa_tests/run_qa_tests.sh` (716-line orchestration script)
- **Helpers**: `qa_tests/lib/test_helpers.sh`, `mock_helpers.sh`, `assertion_helpers.sh`
- **Fixtures**: `qa_tests/fixtures/` (test URLs, configs, student lists)
- **Reports**: `reports/` (Markdown, HTML, JUnit XML formats)

**Documentation:**
- **[QA_TESTING_GUIDE.md](docs/QA_TESTING_GUIDE.md)**: Manual testing guide for test development
- **[QA_AUTOMATION_GUIDE.md](docs/QA_AUTOMATION_GUIDE.md)**: Automation guide for CI/CD integration
- **[QA_TEST_CERTIFICATION_RESULTS.md](docs/QA_TEST_CERTIFICATION_RESULTS.md)**: Latest test results

### Real Repository Testing (New!)

**Prerequisites:**
1. Set up configuration in `sample_projects/real_repo/`:
   - Edit `real_repo_info.conf` with your actual GitHub assignment details
   - Add your GitHub token to `instructor_token.txt`
   - See `sample_projects/real_repo/README.md` for detailed setup instructions

**Quick Start:**
```bash
# Test configuration setup (safe dry-run)
./scripts/test_real_repo.sh --dry-run

# Run complete real repository testing
./scripts/run_full_test.sh --real-repo

# Test specific real repository functionality
./scripts/test_runner.sh --real-repo --verbose
```

**Advanced Usage:**
```bash
# Setup environment only (for debugging)
./scripts/test_real_repo.sh --setup-only --keep-env

# Run tests with existing environment
./scripts/test_real_repo.sh --test-only --verbose

# Keep cloned repository for inspection
./scripts/test_real_repo.sh --keep-repo --verbose

# Clean up specific components
./scripts/test_real_repo.sh --cleanup-only
```

### Before Release Testing
```bash
# Complete validation before creating a release
./scripts/run_full_test.sh --comprehensive

# Test with real GitHub repository (requires real_repo_info.conf)
./scripts/run_full_test.sh --real-repo

# Generate detailed test report
./scripts/run_full_test.sh --report
```

### Development Testing
```bash
# Quick validation during development
./scripts/run_full_test.sh --quick

# Test specific functionality
# Test with real GitHub repository (requires setup)
./scripts/run_full_test.sh --real-repo

# Test specific real repository functionality
./scripts/test_runner.sh real-repo --verbose
```

### CI/CD Integration
```bash
# Automated testing in CI pipeline
./scripts/run_full_test.sh --ci-mode
```

## 📊 Test Reports

Test results are automatically generated in the `reports/` directory:

- `test_report_YYYYMMDD_HHMMSS.md` - Comprehensive test results
- `installation_log.txt` - Installation process details
- `cli_test_output.txt` - CLI command testing output
- `api_test_results.json` - Python API test results
- `integration_results.txt` - Integration test outcomes

## 🔧 Configuration

Edit `scripts/config.sh` to customize test behavior:

```bash
# Test environment settings
TEST_PYTHON_VERSIONS=("3.10" "3.11" "3.12")
TEST_ENVIRONMENTS=("venv" "conda")
COMPREHENSIVE_TESTING=true
CLEANUP_AFTER_TESTS=true

# Package settings
PACKAGE_NAME="classdock"
EXPECTED_VERSION="3.1.0a2"
CLI_COMMAND="classdock"
```

## 🆘 Troubleshooting

Common issues and solutions:

- **Permission Errors**: Ensure scripts are executable: `chmod +x scripts/*.sh`
- **Python Version Issues**: Install required Python versions or update config
- **Environment Conflicts**: Run cleanup script: `./scripts/cleanup_test_env.sh`
- **Package Build Failures**: Check Poetry configuration and dependencies

For detailed troubleshooting, see `docs/TROUBLESHOOTING.md`.

## 🤝 Contributing

To add new test scenarios:

1. Create test script in `scripts/`
2. Add sample project in `sample_projects/`
3. Update documentation in `docs/`
4. Add test case to main orchestration script

## 📚 Documentation

- [`docs/TESTING_GUIDE.md`](docs/TESTING_GUIDE.md) - Comprehensive testing documentation
- [`docs/TEST_SCENARIOS.md`](docs/TEST_SCENARIOS.md) - Detailed test scenarios
- [`docs/QA_TESTING_GUIDE.md`](docs/QA_TESTING_GUIDE.md) - QA functional test development guide
- [`docs/QA_AUTOMATION_GUIDE.md`](docs/QA_AUTOMATION_GUIDE.md) - QA test automation and CI/CD integration
- [`docs/QA_TEST_CERTIFICATION_RESULTS.md`](docs/QA_TEST_CERTIFICATION_RESULTS.md) - Latest QA test results and certification
- [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md) - Solutions for common issues
- [`docs/REAL_REPO_QUICK_REFERENCE.md`](docs/REAL_REPO_QUICK_REFERENCE.md) - Quick reference for real repository testing
- [`sample_projects/real_repo/README.md`](sample_projects/real_repo/README.md) - Real repository testing setup guide

---

*This testing framework ensures the `classdock` package is thoroughly validated before release, providing confidence in package quality and user experience.*