#!/bin/bash
set -euo pipefail

# Comprehensive test runner for Python wrapper
# Executes full test suite with coverage reporting

source "$(dirname "$0")/workflow_utils.sh"

PYTHON_VERSION="${1:-3.10}"

run_comprehensive_tests() {
    print_message "info" "Running comprehensive test suite for Python $PYTHON_VERSION"
    
    local test_start_time=$(date +%s)
    
    mkdir -p test-results/python$PYTHON_VERSION
    
    local pytest_cmd=(
        "poetry" "run" "pytest"
        "tests/"
        "-v"
        "--tb=short"
        "--strict-markers"
        "--disable-warnings"
        "--cov=classdock"
        "--cov-branch"
        "--cov-report=term-missing:skip-covered"
        "--cov-report=xml:test-results/python$PYTHON_VERSION/coverage.xml"
        "--cov-report=html:test-results/python$PYTHON_VERSION/htmlcov"
        "--junitxml=test-results/python$PYTHON_VERSION/pytest-results.xml"
    )
    
    if ! "${pytest_cmd[@]}"; then
        print_message "error" "Test execution failed for Python $PYTHON_VERSION"
        return 1
    fi
    
    local test_end_time=$(date +%s)
    local test_duration=$((test_end_time - test_start_time))
    
    print_message "success" "All tests passed for Python $PYTHON_VERSION (${test_duration}s)"
    return 0
}

if ! run_comprehensive_tests; then
    print_message "error" "Comprehensive test execution failed"
    exit 1
fi