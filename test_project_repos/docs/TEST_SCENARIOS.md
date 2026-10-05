# Test Scenarios Documentation

This document describes the various test scenarios implemented in the testing framework for the classdock package.

## Overview

The testing framework includes comprehensive scenarios to validate all aspects of the classdock package, from basic installation to complex integration workflows.

## Test Categories

### 1. Installation Tests

**Purpose**: Verify that the package can be installed correctly in various environments.

**Scenarios**:
- **Wheel Installation**: Install from pre-built wheel package
- **Source Installation**: Install from source distribution 
- **Editable Installation**: Install in development mode with `-e` flag
- **Clean Environment**: Install in isolated virtual environment
- **Dependency Resolution**: Verify all dependencies are correctly installed
- **Version Verification**: Confirm installed version matches expected version

**Test Scripts**: `scripts/test_installation.sh`

**Sample Commands**:
```bash
# Test wheel installation
./scripts/test_runner.sh installation

# Test with environment setup
./scripts/test_runner.sh installation --setup
```

### 2. CLI Interface Tests

**Purpose**: Validate the command-line interface functionality and user experience.

**Scenarios**:
- **Help System**: Test `--help` output for all commands
- **Version Display**: Verify `--version` command works
- **Command Discovery**: Test all subcommands are accessible
- **Error Handling**: Validate graceful error messages
- **Argument Validation**: Test parameter validation
- **Output Formatting**: Verify consistent output formatting

**Test Scripts**: `scripts/test_cli_interface.sh`

**Sample Commands**:
```bash
# Test CLI interface
./scripts/test_runner.sh cli

# Test with verbose output
./scripts/test_runner.sh cli --verbose
```

### 3. Python API Tests

**Purpose**: Test the Python programming interface and module imports.

**Scenarios**:
- **Package Import**: Test main package import
- **Module Loading**: Verify all submodules load correctly
- **Class Instantiation**: Test object creation
- **Method Execution**: Validate method calls work
- **Error Handling**: Test exception handling
- **Memory Usage**: Monitor memory consumption
- **Import Performance**: Measure import time

**Test Scripts**: `scripts/test_python_api.py`

**Sample Commands**:
```bash
# Test Python API
./scripts/test_runner.sh python-api

# Run directly
python3 scripts/test_python_api.py
```

### 4. Integration Tests

**Purpose**: Test complete workflows and real-world usage scenarios.

**Scenarios**:
- **Configuration Workflow**: Create and validate assignment configurations
- **Sample Project Processing**: Test with realistic project structures
- **CLI + API Integration**: Verify CLI and Python API work together
- **Error Recovery**: Test graceful handling of error conditions
- **Performance Testing**: Validate performance with multiple operations
- **Environment Isolation**: Test package works in clean environments

**Test Scripts**: `scripts/test_integration.sh`

**Sample Commands**:
```bash
# Test integration scenarios
./scripts/test_runner.sh integration

# Run all tests with cleanup
./scripts/test_runner.sh all --cleanup
```

### 5. Real Repository Tests

**Purpose**: Validate classdock with actual GitHub repositories and live workflows.

**Scenarios**:
- **Actual Repository Cloning**: Clone real GitHub repositories for testing
- **Live Configuration Parsing**: Parse actual GitHub assignment data
- **Conda Environment Integration**: Test in isolated conda environments
- **Real Token Validation**: Validate GitHub tokens with actual API calls
- **End-to-End Workflows**: Complete assignment setup workflows with real data
- **Security Validation**: Test token handling and repository access permissions

**Test Scripts**: `scripts/test_real_repo.sh`

**Sample Commands**:
```bash
# Complete real repository testing
./scripts/run_full_test.sh --real-repo

# Test with verbose debugging
./scripts/test_real_repo.sh --verbose --keep-env

# Validate configuration only
./scripts/test_real_repo.sh --dry-run
```

**Prerequisites**:
- Valid `sample_projects/real_repo/real_repo_info.conf` configuration
- GitHub personal access token in `sample_projects/real_repo/instructor_token.txt`
- Conda installed and available
- Internet connectivity for GitHub API access

## Sample Projects

### Basic Assignment

**Location**: `sample_projects/basic_assignment/`

**Description**: Simple assignment with minimal configuration for testing basic functionality.

**Files**:
- `assignment.conf` - Basic configuration
- `README.md` - Assignment instructions  
- `src/main.py` - Starter code

**Use Cases**:
- Configuration validation
- CLI command testing
- Basic workflow verification

### Advanced Assignment

**Location**: `sample_projects/advanced_assignment/`

**Description**: Complex assignment with advanced features for testing comprehensive functionality.

**Files**:
- `assignment.conf` - Advanced configuration with multiple options
- Complex project structure
- Multiple file types and directories

**Use Cases**:
- Advanced configuration testing
- Complex workflow validation
- Performance testing with larger projects

### Error Scenarios

**Location**: `sample_projects/error_scenarios/`

**Description**: Intentionally broken configurations and projects for testing error handling.

**Files**:
- `invalid.conf` - Invalid configuration file
- Missing required files
- Malformed project structures

**Use Cases**:
- Error handling validation
- Graceful failure testing
- User experience with errors

## Test Execution Modes

### Quick Mode

**Purpose**: Fast validation of basic functionality.

**Duration**: < 2 minutes

**Coverage**: Basic installation, core CLI commands, essential API functions

**Command**: `./scripts/run_full_test.sh --mode quick`

### Comprehensive Mode

**Purpose**: Complete testing of all functionality.

**Duration**: 5-10 minutes

**Coverage**: All test scenarios, multiple environments, performance testing

**Command**: `./scripts/run_full_test.sh --mode comprehensive`

### CI Mode

**Purpose**: Optimized for continuous integration environments.

**Duration**: 3-5 minutes

**Coverage**: Essential tests with parallel execution and optimized reporting

**Command**: `./scripts/run_full_test.sh --mode ci`

## Test Environment Scenarios

### Virtual Environment Testing

**Purpose**: Test package in isolated Python virtual environments.

**Scenarios**:
- Clean venv creation
- Package installation in venv
- Functionality testing in isolation
- Multiple Python versions

**Setup**: `scripts/setup_test_env.sh --env-type venv`

### Conda Environment Testing

**Purpose**: Test package in Conda environments.

**Scenarios**:
- Conda environment creation
- Package installation via pip in conda
- Dependency resolution in conda
- Cross-platform compatibility

**Setup**: `scripts/setup_test_env.sh --env-type conda`

### System Installation Testing

**Purpose**: Test package installed system-wide.

**Scenarios**:
- Global package installation
- User-level installation
- Permission handling
- Conflict resolution

**Setup**: `scripts/setup_test_env.sh --env-type system`

## Error Handling Scenarios

### Configuration Errors

**Test Cases**:
- Missing required configuration fields
- Invalid configuration values
- Malformed configuration files
- Encoding issues

**Expected Behavior**: Clear error messages with guidance for resolution

### Runtime Errors

**Test Cases**:
- Network connectivity issues
- File permission problems
- Missing dependencies
- Resource limitations

**Expected Behavior**: Graceful degradation with helpful error reporting

### CLI Errors

**Test Cases**:
- Invalid command arguments
- Missing required parameters
- Conflicting options
- Help system access

**Expected Behavior**: Consistent error formatting with usage hints

## Performance Testing Scenarios

### Load Testing

**Purpose**: Validate performance under various loads.

**Scenarios**:
- Multiple simultaneous operations
- Large configuration files
- Complex project structures
- Memory usage monitoring

### Benchmark Testing

**Purpose**: Establish performance baselines.

**Scenarios**:
- Command execution time
- Import time measurement
- Memory consumption tracking
- Resource utilization

## Cross-Platform Testing

### Platform-Specific Scenarios

**Platforms Tested**:
- macOS (current development platform)
- Linux (Ubuntu, via CI)
- Windows (via CI when available)

**Test Areas**:
- Path handling differences
- Shell command compatibility
- File permission models
- Unicode/encoding handling

## Continuous Integration Scenarios

### Automated Testing

**Triggers**:
- Pull request validation
- Main branch commits
- Release preparation
- Scheduled health checks

**Coverage**:
- Multi-platform testing
- Multiple Python versions
- Dependency variations
- Performance regression detection

## Test Data Management

### Sample Data

**Location**: `sample_projects/`

**Types**:
- Realistic assignment configurations
- Various project structures  
- Error condition examples
- Performance test data

### Test Artifacts

**Generation**: Tests create temporary files and logs

**Cleanup**: Automated cleanup via `scripts/cleanup.sh`

**Retention**: Reports retained for analysis, temporary files removed

## Reporting and Analysis

### Test Reports

**Formats**:
- HTML reports with detailed results
- JUnit XML for CI integration
- JSON for programmatic analysis
- Plain text for console output

**Content**:
- Test execution results
- Performance metrics
- Error details and stack traces
- Environment information

### Metrics Tracking

**Key Metrics**:
- Test pass/fail rates
- Execution time trends
- Memory usage patterns
- Error frequency analysis

## Troubleshooting Common Issues

### Test Failures

**Common Causes**:
- Missing dependencies
- Environment configuration issues
- Network connectivity problems
- Platform-specific path issues

**Resolution Steps**:
1. Check test environment setup
2. Verify package installation
3. Review error logs and reports
4. Run tests in isolation
5. Check platform-specific requirements

### Performance Issues

**Common Causes**:
- Insufficient system resources
- Network latency
- Large test data sets
- Inefficient test implementations

**Resolution Steps**:
1. Monitor system resources during tests
2. Reduce test data size
3. Optimize test execution order
4. Use parallel execution where appropriate

### Environment Issues

**Common Causes**:
- Python version incompatibilities
- Missing system dependencies
- Virtual environment problems
- Path configuration issues

**Resolution Steps**:
1. Verify Python version requirements
2. Check system dependency installation
3. Recreate virtual environments
4. Validate PATH and environment variables

## Best Practices

### Test Development

1. **Isolation**: Each test should be independent
2. **Repeatability**: Tests should produce consistent results
3. **Clarity**: Test names and documentation should be clear
4. **Coverage**: Tests should cover both success and failure cases
5. **Performance**: Tests should run efficiently

### Test Maintenance

1. **Regular Updates**: Keep tests current with package changes
2. **Cleanup**: Remove obsolete tests and test data
3. **Documentation**: Maintain accurate test documentation
4. **Monitoring**: Track test health and performance trends

### Test Execution

1. **Environment Preparation**: Ensure clean test environments
2. **Result Analysis**: Review test results and reports
3. **Issue Resolution**: Address test failures promptly
4. **Continuous Improvement**: Refine tests based on findings

## Future Enhancements

### Planned Improvements

1. **Parallel Execution**: Implement parallel test execution for faster results
2. **Advanced Reporting**: Enhanced reporting with trends and analytics
3. **Performance Profiling**: Detailed performance analysis and optimization
4. **Platform Expansion**: Extended cross-platform testing coverage

### Integration Opportunities

1. **IDE Integration**: VS Code test discovery and execution
2. **Git Hooks**: Pre-commit and pre-push test execution
3. **Monitoring**: Integration with monitoring and alerting systems
4. **Analytics**: Test result analytics and trend analysis