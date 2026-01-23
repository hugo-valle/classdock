#!/bin/bash
set -euo pipefail

# CLI command testing script
# Tests various CLI command combinations and scenarios

source "$(dirname "$0")/workflow_utils.sh"

CLASSDOCK_CMD="${1:-poetry run classdock}"

print_message "step" "Testing CLI commands and help system"

# Test main help command
print_message "step" "Testing main help..."
$CLASSDOCK_CMD --help

# Test version flag
print_message "step" "Testing version flag..."
$CLASSDOCK_CMD --version

# Test subcommand help
print_message "step" "Testing assignments help..."
$CLASSDOCK_CMD assignments --help

print_message "step" "Testing repos help..."
$CLASSDOCK_CMD repos --help

print_message "step" "Testing secrets help..."
$CLASSDOCK_CMD secrets --help

print_message "step" "Testing automation help..."
$CLASSDOCK_CMD automation --help

# Test specific command help
print_message "step" "Testing specific command help..."
$CLASSDOCK_CMD assignments orchestrate --help
$CLASSDOCK_CMD repos fetch --help
$CLASSDOCK_CMD secrets manage --help

# Test error conditions
print_message "step" "Testing error conditions..."
set +e

# Test invalid command
$CLASSDOCK_CMD invalid-command 2>/dev/null
if [[ $? -eq 0 ]]; then
    print_message "error" "Expected error for invalid command, but succeeded"
    exit 1
fi

# Test missing required arguments (should show help)
$CLASSDOCK_CMD assignments orchestrate 2>/dev/null
if [[ $? -eq 0 ]]; then
    print_message "warning" "Command succeeded without required arguments (may be using defaults)"
fi

set -e

print_message "success" "CLI command tests completed successfully"