# Troubleshooting Guide

This guide helps resolve common issues encountered when using the classdock testing framework.

## Quick Diagnostics

### Test Environment Check

Run the following commands to verify your test environment:

```bash
# Check Python version
python3 --version

# Check if classdock is installed
python3 -c "import classdock; print(classdock.__version__)"

# Check if CLI is available
classdock --version

# Verify test framework structure
ls -la test_project_repos/scripts/
```

### Common Quick Fixes

1. **Refresh test environment**: `./scripts/setup_test_env.sh --clean`
2. **Clean temporary files**: `./scripts/cleanup.sh --all`
3. **Reinstall package**: `pip uninstall classdock && pip install classdock`
4. **Reset scripts permissions**: `chmod +x scripts/*.sh scripts/*.py`

## Installation Issues

### Package Not Found

**Symptoms**: `ModuleNotFoundError: No module named 'classdock'`

**Causes**:
- Package not installed
- Wrong Python environment
- Installation failed silently

**Solutions**:
```bash
# Check if package is installed
pip list | grep classdock

# Install if missing
pip install classdock

# Install in development mode (if working from source)
pip install -e .

# Verify installation
python3 -c "import classdock; print('OK')"
```

### Version Mismatch

**Symptoms**: Tests fail with unexpected behavior or API errors

**Causes**:
- Old version installed
- Multiple versions in environment
- Development version conflicts

**Solutions**:
```bash
# Check installed version
pip show classdock

# Check expected version
cat pyproject.toml | grep version

# Force reinstall latest version
pip install --force-reinstall classdock

# Clear pip cache
pip cache purge
```

### Dependency Conflicts

**Symptoms**: `pip install` fails with dependency resolution errors

**Causes**:
- Incompatible package versions
- Conflicting requirements
- Outdated pip/setuptools

**Solutions**:
```bash
# Update pip and setuptools
pip install --upgrade pip setuptools wheel

# Install with no dependencies (diagnose specific conflicts)
pip install --no-deps classdock

# Create clean environment
python3 -m venv fresh_env
source fresh_env/bin/activate
pip install classdock
```

## CLI Interface Issues

### Command Not Found

**Symptoms**: `command not found: classdock`

**Causes**:
- Package not installed with CLI entry point
- PATH issues
- Virtual environment not activated

**Solutions**:
```bash
# Check if entry point is installed
pip show -f classdock | grep console_scripts

# Try running via Python module
python3 -m classdock --version

# Check if in PATH
which classdock

# Activate virtual environment if needed
source venv/bin/activate  # or conda activate env_name
```

### CLI Commands Fail

**Symptoms**: CLI commands return errors or unexpected output

**Causes**:
- Missing configuration
- Permission issues
- Invalid arguments

**Solutions**:
```bash
# Enable verbose mode for debugging
classdock --verbose command args

# Check command help
classdock command --help

# Verify configuration
classdock assignments validate-config --config-file path/to/config

# Check file permissions
ls -la assignment.conf
```

### Help System Issues

**Symptoms**: `--help` doesn't work or shows wrong information

**Causes**:
- Typer/Click version conflicts
- Import errors in CLI module
- Broken command definitions

**Solutions**:
```bash
# Check Typer/Click versions
pip list | grep -E "(typer|click)"

# Reinstall with correct versions
pip install "typer>=0.12.0" "click>=8.0.0,<8.2.0"

# Test CLI module import
python3 -c "from classdock import cli; print('CLI import OK')"
```

## Python API Issues

### Import Errors

**Symptoms**: Cannot import specific modules or classes

**Causes**:
- Missing dependencies
- Broken package structure
- Python path issues

**Solutions**:
```bash
# Test systematic imports
python3 -c "import classdock"
python3 -c "from classdock import ConfigLoader"
python3 -c "from classdock.assignments.setup import AssignmentSetup"

# Check package structure
python3 -c "import classdock; print(classdock.__file__)"

# Verify dependencies
pip check
```

### Configuration Loading Errors

**Symptoms**: Configuration validation or loading fails

**Causes**:
- Invalid configuration file format
- Missing required fields
- File encoding issues

**Solutions**:
```bash
# Validate configuration file syntax
python3 -c "
import configparser
config = configparser.ConfigParser()
config.read('assignment.conf')
print('Config syntax OK')
"

# Check file encoding
file assignment.conf

# Create minimal test config
cat > test.conf << EOF
GITHUB_ORGANIZATION=test-org
TEMPLATE_REPO_URL=https://github.com/test/template
ASSIGNMENT_FILE=assignment.conf
EOF
```

### Memory or Performance Issues

**Symptoms**: High memory usage or slow performance

**Causes**:
- Memory leaks
- Inefficient operations
- Large configuration files

**Solutions**:
```bash
# Monitor memory usage
python3 -c "
import psutil
import classdock
process = psutil.Process()
print(f'Memory before: {process.memory_info().rss / 1024 / 1024:.1f} MB')
# Your operations here
print(f'Memory after: {process.memory_info().rss / 1024 / 1024:.1f} MB')
"

# Profile imports
python3 -c "
import time
start = time.time()
import classdock
print(f'Import time: {time.time() - start:.3f}s')
"
```

## Test Framework Issues

### Script Permission Errors

**Symptoms**: `Permission denied` when running scripts

**Causes**:
- Scripts not executable
- File system permissions
- SELinux/security policies

**Solutions**:
```bash
# Make scripts executable
chmod +x scripts/*.sh scripts/*.py

# Check current permissions
ls -la scripts/

# Set correct permissions for entire directory
find scripts/ -type f -name "*.sh" -exec chmod +x {} \;
find scripts/ -type f -name "*.py" -exec chmod +x {} \;
```

### Test Environment Setup Failures

**Symptoms**: `setup_test_env.sh` fails or creates broken environment

**Causes**:
- Python version incompatibility
- Virtual environment creation failures
- Network connectivity issues

**Solutions**:
```bash
# Clean and recreate environment
./scripts/cleanup.sh --envs
./scripts/setup_test_env.sh --clean

# Use specific Python version
./scripts/setup_test_env.sh --python-version 3.11

# Debug setup process
./scripts/setup_test_env.sh --verbose

# Manual environment setup
python3 -m venv test_env
source test_env/bin/activate
pip install --upgrade pip
pip install classdock
```

### Test Execution Failures

**Symptoms**: Tests fail unexpectedly or inconsistently

**Causes**:
- Environment contamination
- Resource conflicts
- Timing issues

**Solutions**:
```bash
# Run tests in isolation
./scripts/test_runner.sh installation --setup --cleanup

# Use fresh environment for each test
./scripts/cleanup.sh --all
./scripts/setup_test_env.sh --clean
./scripts/run_full_test.sh

# Run specific test with debugging
./scripts/test_installation.sh --verbose

# Check for resource conflicts
ps aux | grep classdock
lsof | grep classdock
```

### Report Generation Issues

**Symptoms**: Test reports are empty, malformed, or missing

**Causes**:
- Insufficient permissions
- Disk space issues
- Template problems

**Solutions**:
```bash
# Check reports directory
ls -la reports/

# Create reports directory if missing
mkdir -p reports

# Check disk space
df -h

# Generate simple report manually
./scripts/test_runner.sh all --report

# Check report template
cat scripts/test_runner.sh | grep -A 20 "Generate test report"
```

## Real Repository Testing Issues

### Configuration Problems

**Symptoms**: Real repository tests fail during setup or configuration parsing

**Causes**:
- Missing or invalid configuration files
- Incorrect repository URLs
- GitHub token permission issues
- Network connectivity problems

**Solutions**:
```bash
# Validate configuration format
./scripts/test_real_repo.sh --dry-run

# Check configuration file syntax
source sample_projects/real_repo/real_repo_info.conf && echo "Config syntax OK"

# Verify GitHub token format
grep -E '^ghp_[A-Za-z0-9]{36}$' sample_projects/real_repo/instructor_token.txt

# Test repository access
git ls-remote https://github.com/ORG/REPO

# Validate token permissions
curl -H "Authorization: token $(cat sample_projects/real_repo/instructor_token.txt)" https://api.github.com/user
```

### Environment Setup Failures

**Symptoms**: Conda environment creation fails or classdock installation errors

**Causes**:
- Conda not in PATH
- Permission issues
- Network connectivity
- Package dependency conflicts

**Solutions**:
```bash
# Check conda installation
conda --version
conda info

# Verify conda in PATH
which conda

# Manual environment creation
conda create -n test-env python=3.11 -y
conda activate test-env
pip install -e /path/to/classdock

# Clean up failed environments
conda env remove -n classdock-real-test -y
./scripts/test_real_repo.sh --cleanup-only
```

### Repository Cloning Issues

**Symptoms**: Git clone operations fail or repository access denied

**Causes**:
- Invalid repository URLs
- Authentication issues
- Network connectivity
- Repository permissions

**Solutions**:
```bash
# Test repository access manually
git clone https://github.com/ORG/REPO test-clone
rm -rf test-clone

# Check SSH vs HTTPS access
git config --global credential.helper

# Verify organization access
curl -H "Authorization: token $TOKEN" https://api.github.com/orgs/ORG/repos

# Test with different authentication
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### GitHub API Issues

**Symptoms**: API calls fail with authentication or rate limiting errors

**Causes**:
- Invalid or expired tokens
- Insufficient token permissions
- API rate limiting
- Network connectivity issues

**Solutions**:
```bash
# Validate token permissions
curl -H "Authorization: token $TOKEN" https://api.github.com/user

# Check rate limits
curl -H "Authorization: token $TOKEN" https://api.github.com/rate_limit

# Test specific API endpoints
curl -H "Authorization: token $TOKEN" https://api.github.com/repos/ORG/REPO

# Wait for rate limit reset if needed
echo "Rate limit resets at: $(curl -s -H "Authorization: token $TOKEN" https://api.github.com/rate_limit | jq -r '.rate.reset')"
```

### Test Execution Failures

**Symptoms**: Individual test components fail during real repository testing

**Causes**:
- Environment contamination
- Resource conflicts
- Timing issues
- Configuration inconsistencies

**Solutions**:
```bash
# Run step-by-step for debugging
./scripts/test_real_repo.sh --setup-only --verbose
./scripts/test_real_repo.sh --test-only --verbose
./scripts/test_real_repo.sh --cleanup-only

# Keep environment for inspection
./scripts/test_real_repo.sh --keep-env --keep-repo --verbose

# Run with maximum debugging
DEBUG=1 VERBOSE=1 ./scripts/test_real_repo.sh --dry-run

# Check individual components
conda activate classdock-real-test
classdock --version
classdock assignments --help
```

## Environment-Specific Issues

### macOS Issues

**Common Problems**:
- Xcode command line tools missing
- Permission issues with system Python
- PATH configuration with multiple Python installations

**Solutions**:
```bash
# Install Xcode command line tools
xcode-select --install

# Use Homebrew Python instead of system Python
brew install python3
which python3

# Fix PATH in shell profile
echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.bash_profile
source ~/.bash_profile
```

### Linux Issues

**Common Problems**:
- Missing system dependencies
- Package manager conflicts
- User permission issues

**Solutions**:
```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install python3-pip python3-venv python3-dev

# Install system dependencies (CentOS/RHEL)
sudo yum install python3-pip python3-venv python3-devel

# Fix user permissions
pip install --user classdock
export PATH="$HOME/.local/bin:$PATH"
```

### Virtual Environment Issues

**Common Problems**:
- Environment activation failures
- Package installation in wrong environment
- Environment corruption

**Solutions**:
```bash
# Verify environment activation
which python3
which pip

# Check environment variables
echo $VIRTUAL_ENV
echo $PATH

# Recreate environment
deactivate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
```

## Performance Troubleshooting

### Slow Test Execution

**Symptoms**: Tests take much longer than expected

**Causes**:
- Network latency
- Disk I/O bottlenecks
- Inefficient test implementations

**Solutions**:
```bash
# Run subset of tests
./scripts/test_runner.sh installation

# Use quick mode
./scripts/run_full_test.sh --mode quick

# Monitor system resources
top -p $(pgrep -f classdock)

# Profile test execution
time ./scripts/test_runner.sh cli
```

### High Memory Usage

**Symptoms**: System becomes slow or tests fail with memory errors

**Causes**:
- Memory leaks in tests
- Large test data sets
- Concurrent test execution

**Solutions**:
```bash
# Monitor memory usage
watch -n 1 'ps aux | grep python'

# Reduce test parallelism
export PYTEST_WORKERS=1

# Clean up between tests
./scripts/cleanup.sh --temp

# Run tests sequentially
./scripts/test_runner.sh python-api
./scripts/cleanup.sh --temp
./scripts/test_runner.sh cli
```

## Integration Issues

### GitHub API Issues

**Symptoms**: Tests fail with GitHub API errors

**Causes**:
- Rate limiting
- Authentication issues
- Network connectivity

**Solutions**:
```bash
# Check GitHub CLI authentication
gh auth status

# Test GitHub connectivity
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user

# Skip GitHub-dependent tests
export SKIP_GITHUB_TESTS=1
./scripts/test_runner.sh all
```

### Configuration File Issues

**Symptoms**: Configuration validation fails

**Causes**:
- Invalid syntax
- Missing required fields
- Encoding problems

**Solutions**:
```bash
# Validate configuration manually
python3 -c "
import configparser
config = configparser.ConfigParser()
try:
    config.read('assignment.conf')
    print('Configuration is valid')
    for section in config.sections():
        print(f'Section: {section}')
        for key, value in config[section].items():
            print(f'  {key} = {value}')
except Exception as e:
    print(f'Configuration error: {e}')
"

# Check for required fields
```

## Network and Connectivity Issues

### Network Timeouts

**Symptoms**: Tests fail with timeout errors

**Causes**:
- Slow network connection
- Firewall blocking requests
- Server unavailability

**Solutions**:
```bash
# Test network connectivity
ping github.com
curl -I https://api.github.com

# Use offline mode if available
export OFFLINE_MODE=1

# Increase timeout values
export NETWORK_TIMEOUT=30
```

### SSL/TLS Issues

**Symptoms**: Certificate verification errors

**Causes**:
- Outdated certificates
- Corporate firewall
- System clock issues

**Solutions**:
```bash
# Check system time
date

# Update certificates (macOS)
brew install ca-certificates

# Test SSL connection
openssl s_client -connect api.github.com:443

# Temporary workaround (not recommended for production)
export PYTHONHTTPSVERIFY=0
```

## Getting Help

### Enable Debug Mode

```bash
# Set debug environment variables
export DEBUG=1
export VERBOSE=1

# Run tests with maximum verbosity
./scripts/run_full_test.sh --mode comprehensive --verbose
```

### Collect Diagnostic Information

```bash
# System information
uname -a
python3 --version
pip --version

# Package information
pip show classdock
pip list | grep -E "(classdock|typer|click)"

# Environment information
env | grep -E "(PYTHON|PATH|VIRTUAL_ENV)"

# Test framework information
ls -la scripts/
./scripts/test_runner.sh --help
```

### Create Minimal Reproduction

```bash
# Create clean test case
mkdir debug_test
cd debug_test
python3 -m venv venv
source venv/bin/activate
pip install classdock

# Test minimal functionality
classdock --version
python3 -c "import classdock; print('OK')"
```

### Contact Support

When reporting issues, please include:

1. **Environment Information**: OS, Python version, package version
2. **Full Error Messages**: Complete error output and stack traces
3. **Reproduction Steps**: Exact commands that trigger the issue
4. **Configuration Files**: Relevant configuration (sanitized)
5. **Test Output**: Complete test logs with verbose mode enabled

**Note**: Remove any sensitive information (tokens, passwords, etc.) before sharing logs or configuration files.