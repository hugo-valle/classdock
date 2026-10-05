#!/bin/bash
#
# Configuration file for ClassDock Testing Suite
#
# This file contains all configuration settings for the testing framework.
# Modify these values to customize test behavior.
#

# Package Information
PACKAGE_NAME="classdock"
EXPECTED_VERSION="3.1.0a2"
CLI_COMMAND="classdock"
PYTHON_MODULE="classdock"

# Project Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TEST_DIR="$SCRIPT_DIR/.."
TEST_PROJECT_REPOS_DIR="$TEST_DIR"

# Centralized directory paths
LIB_DIR="$TEST_DIR/lib"
FIXTURES_DIR="$TEST_DIR/fixtures"

# Report directories
REPORTS_DIR="$TEST_DIR/reports"
QA_REPORT_DIR="$REPORTS_DIR/qa"
JUNIT_REPORT_DIR="$REPORTS_DIR/junit"

# Create report directories
mkdir -p "$REPORTS_DIR" "$QA_REPORT_DIR" "$JUNIT_REPORT_DIR"

# Python Version Configuration
DEFAULT_PYTHON_VERSION="3.11"
TEST_PYTHON_VERSIONS=("3.10" "3.11" "3.12")

# Test Environment Configuration
TEST_ENVIRONMENTS=("conda" "venv")
PREFERRED_TEST_ENV="conda"

# Test Execution Settings
TEST_TIMEOUT=300  # seconds
MAX_RETRIES=3
ENABLE_PARALLEL_TESTS=false

# Test Coverage Settings
COMPREHENSIVE_TESTING=true
PERFORMANCE_TESTING=false
MEMORY_TESTING=false
CROSS_PLATFORM_TESTING=true

# Cleanup Settings
CLEANUP_AFTER_TESTS=true
KEEP_SUCCESSFUL_ENVS=false
KEEP_TEST_ARTIFACTS=true

# Output and Logging
DEFAULT_VERBOSE=false
COLORED_OUTPUT=true
LOG_LEVEL="INFO"
GENERATE_JUNIT_XML=false

# Directory Configuration
TEST_ENV_BASE_NAME="classdock_test"
BUILD_DIR="dist"
LOGS_DIR="logs"

# Package Build Configuration
BUILD_WITH_POETRY=true
VERIFY_WHEEL_CONTENTS=true
TEST_SOURCE_INSTALL=true
TEST_WHEEL_INSTALL=true

# CLI Testing Configuration
TEST_ALL_COMMANDS=true
TEST_HELP_SYSTEM=true
TEST_ERROR_HANDLING=true
TEST_AUTOCOMPLETE=false

# API Testing Configuration
TEST_ALL_IMPORTS=true
TEST_CONFIGURATION_SYSTEM=true
TEST_LOGGING_SYSTEM=true
TEST_ERROR_CLASSES=true

# Integration Testing Configuration
RUN_BASIC_SCENARIOS=true
RUN_ADVANCED_SCENARIOS=true
RUN_ERROR_SCENARIOS=true
CREATE_SAMPLE_PROJECTS=true

# Performance Testing Configuration
MEMORY_THRESHOLD_MB=100
EXECUTION_TIME_THRESHOLD_SEC=30
MONITOR_RESOURCE_USAGE=false

# CI/CD Integration
CI_FRIENDLY_OUTPUT=false
FAIL_FAST_MODE=false
GENERATE_COVERAGE_REPORT=false

# Test Data Configuration
USE_MOCK_DATA=true
CLEANUP_TEST_DATA=true
PRESERVE_CONFIG_FILES=false

# External Dependencies
REQUIRE_GIT=true
REQUIRE_GITHUB_CLI=false
REQUIRE_DOCKER=false

# Security Testing
RUN_SECURITY_CHECKS=false
CHECK_VULNERABILITIES=false
VALIDATE_PERMISSIONS=true

# Notification Settings
NOTIFY_ON_COMPLETION=false
SLACK_WEBHOOK_URL=""
EMAIL_NOTIFICATIONS=false

# Advanced Settings
ENABLE_DEBUG_MODE=false
CAPTURE_SCREENSHOTS=false
RECORD_EXECUTION_TRACE=false
ENABLE_PROFILING=false

# QA Testing Configuration
QA_TESTING_ENABLED=true
QA_TESTS_DIR="$TEST_DIR/qa_tests"
QA_LIB_DIR="$LIB_DIR"
QA_FIXTURES_DIR="$FIXTURES_DIR/configs"
QA_REPORT_DIR="$TEST_DIR/reports/qa"

# QA Test Categories
QA_TEST_CONFIG_VALIDATION=true
QA_TEST_CLI_INTERFACE=true
QA_TEST_API_FUNCTIONALITY=true
QA_TEST_ERROR_HANDLING=true
QA_TEST_EDGE_CASES=true

# QA Configuration Fixtures
QA_FIXTURE_VALID_MINIMAL="$QA_FIXTURES_DIR/valid_minimal.conf"
QA_FIXTURE_VALID_COMPREHENSIVE="$QA_FIXTURES_DIR/valid_comprehensive.conf"
QA_FIXTURE_INVALID_MISSING="$QA_FIXTURES_DIR/invalid_missing_required.conf"
QA_FIXTURE_INVALID_URLS="$QA_FIXTURES_DIR/invalid_malformed_urls.conf"
QA_FIXTURE_INVALID_TYPES="$QA_FIXTURES_DIR/invalid_wrong_types.conf"
QA_FIXTURE_EDGE_EMPTY="$QA_FIXTURES_DIR/edge_case_empty_values.conf"
QA_FIXTURE_EDGE_SPECIAL="$QA_FIXTURES_DIR/edge_case_special_characters.conf"
QA_FIXTURE_EDGE_LONG="$QA_FIXTURES_DIR/edge_case_very_long_values.conf"

# QA Testing Thresholds
QA_MAX_EXECUTION_TIME=600  # 10 minutes
QA_MIN_COVERAGE_PERCENT=80
QA_MAX_ERROR_RATE_PERCENT=5

# Export configuration for use in other scripts
export PACKAGE_NAME EXPECTED_VERSION CLI_COMMAND PYTHON_MODULE
export DEFAULT_PYTHON_VERSION TEST_PYTHON_VERSIONS
export TEST_TIMEOUT MAX_RETRIES
export COMPREHENSIVE_TESTING CLEANUP_AFTER_TESTS
export DEFAULT_VERBOSE COLORED_OUTPUT
export QA_TESTING_ENABLED QA_TESTS_DIR QA_LIB_DIR QA_FIXTURES_DIR QA_REPORT_DIR
export LIB_DIR FIXTURES_DIR

# QA Prerequisites Check Function
check_qa_prerequisites() {
    local errors=0
    
    # Check if classdock CLI is available
    if ! command -v classdock >/dev/null 2>&1; then
        echo "[ERROR] classdock CLI not found in PATH" >&2
        echo "[ERROR] Please install classdock before running QA tests" >&2
        echo "[INFO] Run: poetry install or pip install classdock" >&2
        ((errors++))
    else
        echo "[INFO] classdock CLI found: $(command -v classdock)"
    fi
    
    # Check QA directories exist
    if [ ! -d "$QA_TESTS_DIR" ]; then
        echo "[WARNING] QA tests directory not found: $QA_TESTS_DIR" >&2
        mkdir -p "$QA_TESTS_DIR"
        echo "[INFO] Created QA tests directory"
    fi
    
    if [ ! -d "$QA_LIB_DIR" ]; then
        echo "[ERROR] QA library directory not found: $QA_LIB_DIR" >&2
        ((errors++))
    fi
    
    if [ ! -d "$QA_FIXTURES_DIR" ]; then
        echo "[ERROR] QA fixtures directory not found: $QA_FIXTURES_DIR" >&2
        ((errors++))
    fi
    
    # Check helper libraries exist
    if [ ! -f "$QA_LIB_DIR/test_helpers.sh" ]; then
        echo "[ERROR] Test helpers library not found: $QA_LIB_DIR/test_helpers.sh" >&2
        ((errors++))
    fi
    
    if [ ! -f "$QA_LIB_DIR/mock_helpers.sh" ]; then
        echo "[ERROR] Mock helpers library not found: $QA_LIB_DIR/mock_helpers.sh" >&2
        ((errors++))
    fi
    
    # Check configuration fixtures exist
    local fixtures=(
        "$QA_FIXTURE_VALID_MINIMAL"
        "$QA_FIXTURE_VALID_COMPREHENSIVE"
        "$QA_FIXTURE_INVALID_MISSING"
        "$QA_FIXTURE_INVALID_URLS"
        "$QA_FIXTURE_INVALID_TYPES"
        "$QA_FIXTURE_EDGE_EMPTY"
        "$QA_FIXTURE_EDGE_SPECIAL"
        "$QA_FIXTURE_EDGE_LONG"
    )
    
    local missing_fixtures=0
    for fixture in "${fixtures[@]}"; do
        if [ ! -f "$fixture" ]; then
            echo "[WARNING] Configuration fixture not found: $(basename "$fixture")" >&2
            ((missing_fixtures++))
        fi
    done
    
    if [ "$missing_fixtures" -gt 0 ]; then
        echo "[WARNING] $missing_fixtures configuration fixtures are missing" >&2
    fi
    
    # Create QA report directory if it doesn't exist
    if [ ! -d "$QA_REPORT_DIR" ]; then
        mkdir -p "$QA_REPORT_DIR"
        echo "[INFO] Created QA report directory: $QA_REPORT_DIR"
    fi
    
    if [ "$errors" -gt 0 ]; then
        echo "[ERROR] QA prerequisites check failed with $errors errors" >&2
        return 1
    fi
    
    echo "[INFO] QA prerequisites check passed"
    return 0
}

# Export QA check function
export -f check_qa_prerequisites

# Validation function
validate_config() {
    local errors=0
    
    # Check required tools
    if [ "$REQUIRE_GIT" = true ] && ! command -v git &> /dev/null; then
        echo "Error: git is required but not found" >&2
        ((errors++))
    fi
    
    if [ "$BUILD_WITH_POETRY" = true ] && ! command -v poetry &> /dev/null; then
        echo "Error: poetry is required but not found" >&2
        ((errors++))
    fi
    
    # Check Python versions
    for version in "${TEST_PYTHON_VERSIONS[@]}"; do
        if ! command -v "python$version" &> /dev/null && ! command -v python3 &> /dev/null; then
            echo "Warning: Python $version not found" >&2
        fi
    done
    
    # Validate thresholds
    if [ "$MEMORY_THRESHOLD_MB" -lt 10 ]; then
        echo "Warning: Memory threshold is very low ($MEMORY_THRESHOLD_MB MB)" >&2
    fi
    
    if [ "$TEST_TIMEOUT" -lt 60 ]; then
        echo "Warning: Test timeout is very low ($TEST_TIMEOUT seconds)" >&2
    fi
    
    return $errors
}

# Helper functions for configuration
get_python_executable() {
    local version="${1:-$DEFAULT_PYTHON_VERSION}"
    
    if command -v "python$version" &> /dev/null; then
        echo "python$version"
    elif command -v python3 &> /dev/null; then
        echo "python3"
    elif command -v python &> /dev/null; then
        echo "python"
    else
        echo ""
    fi
}

get_test_env_name() {
    # local suffix="${1:-$(date +%s)}"
    # echo "${TEST_ENV_BASE_NAME}_${suffix}"
    echo "${TEST_ENV_BASE_NAME}"
}


is_ci_environment() {
    [ -n "${CI:-}" ] || [ -n "${GITHUB_ACTIONS:-}" ] || [ -n "${TRAVIS:-}" ] || [ -n "${JENKINS_URL:-}" ]
}

# Conda availability and installation functions
check_conda_available() {
    command -v conda >/dev/null 2>&1
}

install_conda() {
    local os_type="$(uname -s)"
    local arch="$(uname -m)"
    
    echo "[INFO] Conda not found. Installing Miniconda..."
    
    # Determine the appropriate Miniconda installer
    local installer_url
    case "$os_type" in
        "Darwin")
            if [[ "$arch" == "arm64" ]]; then
                installer_url="https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh"
            else
                installer_url="https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh"
            fi
            ;;
        "Linux")
            if [[ "$arch" == "aarch64" ]]; then
                installer_url="https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh"
            else
                installer_url="https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
            fi
            ;;
        *)
            echo "[ERROR] Unsupported operating system: $os_type"
            return 1
            ;;
    esac
    
    # Download and install Miniconda
    local temp_dir="$(mktemp -d)"
    local installer_path="$temp_dir/miniconda.sh"
    
    echo "[INFO] Downloading Miniconda from $installer_url"
    if ! curl -fsSL "$installer_url" -o "$installer_path"; then
        echo "[ERROR] Failed to download Miniconda installer"
        rm -rf "$temp_dir"
        return 1
    fi
    
    # Install Miniconda silently
    local conda_install_dir="$HOME/miniconda3"
    echo "[INFO] Installing Miniconda to $conda_install_dir"
    
    if ! bash "$installer_path" -b -p "$conda_install_dir"; then
        echo "[ERROR] Failed to install Miniconda"
        rm -rf "$temp_dir"
        return 1
    fi
    
    # Initialize conda
    echo "[INFO] Initializing conda"
    "$conda_install_dir/bin/conda" init bash >/dev/null 2>&1 || true
    
    # Add conda to PATH for current session
    export PATH="$conda_install_dir/bin:$PATH"
    
    # Cleanup
    rm -rf "$temp_dir"
    
    echo "[SUCCESS] Miniconda installed successfully"
    echo "[INFO] You may need to restart your terminal or run 'source ~/.bashrc' to use conda"
    
    return 0
}

ensure_conda_available() {
    if check_conda_available; then
        echo "[INFO] Conda is available: $(conda --version)"
        return 0
    else
        echo "[WARNING] Conda not found in PATH"
        
        # Try to find conda in common locations
        local conda_paths=(
            "$HOME/miniconda3/bin/conda"
            "$HOME/anaconda3/bin/conda"
            "/opt/miniconda3/bin/conda"
            "/opt/anaconda3/bin/conda"
            "/usr/local/miniconda3/bin/conda"
            "/usr/local/anaconda3/bin/conda"
        )
        
        for conda_path in "${conda_paths[@]}"; do
            if [ -f "$conda_path" ]; then
                echo "[INFO] Found conda at: $conda_path"
                export PATH="$(dirname "$conda_path"):$PATH"
                echo "[INFO] Added conda to PATH: $(conda --version)"
                return 0
            fi
        done
        
        # If conda is still not found, install it
        echo "[INFO] Conda not found in common locations. Installing..."
        if install_conda; then
            return 0
        else
            echo "[ERROR] Failed to install conda. Falling back to venv"
            export PREFERRED_TEST_ENV="venv"
            return 1
        fi
    fi
}

# Auto-adjust configuration for CI environments
if is_ci_environment; then
    CI_FRIENDLY_OUTPUT=true
    COLORED_OUTPUT=false
    NOTIFY_ON_COMPLETION=false
    CLEANUP_AFTER_TESTS=true
    KEEP_SUCCESSFUL_ENVS=false
fi

# Load user configuration overrides if present
USER_CONFIG_FILE="$(dirname "${BASH_SOURCE[0]}")/../.test_config"
if [ -f "$USER_CONFIG_FILE" ]; then
    source "$USER_CONFIG_FILE"
fi