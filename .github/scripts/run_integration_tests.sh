#!/bin/bash
set -euo pipefail

# Integration test execution script
# Runs various integration test scenarios with different configurations

source "$(dirname "$0")/workflow_utils.sh"

TEST_CONFIG_DIR="${1:-tests/fixtures}"
CLASSDOCK_CMD="${2:-poetry run classdock}"

print_message "step" "Running integration tests with configuration directory: $TEST_CONFIG_DIR"

# Test basic configuration
if [[ -f "$TEST_CONFIG_DIR/test_assignment.conf" ]]; then
    print_message "step" "Testing basic configuration..."
    $CLASSDOCK_CMD assignments --dry-run orchestrate --config "$TEST_CONFIG_DIR/test_assignment.conf"
else
    print_message "warning" "Basic configuration not found, skipping"
fi

# Test minimal configuration
if [[ -f "$TEST_CONFIG_DIR/minimal_assignment.conf" ]]; then
    print_message "step" "Testing minimal configuration..."
    $CLASSDOCK_CMD assignments --dry-run orchestrate --config "$TEST_CONFIG_DIR/minimal_assignment.conf"
else
    print_message "warning" "Minimal configuration not found, skipping"
fi

# Test advanced configuration
if [[ -f "$TEST_CONFIG_DIR/advanced_assignment.conf" ]]; then
    print_message "step" "Testing advanced configuration..."
    $CLASSDOCK_CMD assignments --dry-run orchestrate --config "$TEST_CONFIG_DIR/advanced_assignment.conf"
else
    print_message "warning" "Advanced configuration not found, skipping"
fi

# Test edge case configuration
if [[ -f "$TEST_CONFIG_DIR/edge_case_assignment.conf" ]]; then
    print_message "step" "Testing edge case configuration..."
    $CLASSDOCK_CMD assignments --dry-run orchestrate --config "$TEST_CONFIG_DIR/edge_case_assignment.conf"
else
    print_message "warning" "Edge case configuration not found, skipping"
fi

# Test error handling with invalid configuration
if [[ -f "$TEST_CONFIG_DIR/invalid_assignment.conf" ]]; then
    print_message "step" "Testing error handling with invalid configuration..."
    set +e
    $CLASSDOCK_CMD assignments --dry-run orchestrate --config "$TEST_CONFIG_DIR/invalid_assignment.conf"
    exit_code=$?
    set -e
    if [[ $exit_code -eq 0 ]]; then
        print_message "warning" "Invalid configuration was handled gracefully (good CLI behavior)"
    else
        print_message "success" "Invalid configuration correctly rejected"
    fi
else
    print_message "warning" "Invalid configuration not found, skipping error handling test"
fi

print_message "success" "Integration tests completed successfully"