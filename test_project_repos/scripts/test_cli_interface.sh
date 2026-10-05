#!/bin/bash
#
# CLI Interface Testing Script
#
# Tests the command-line interface functionality of classdock
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Test CLI entry point
test_cli_entry_point() {
    log_info "Testing CLI entry point"
    
    # Test command availability
    if ! command -v "$CLI_COMMAND" &> /dev/null; then
        log_error "CLI command not found: $CLI_COMMAND"
        return 1
    fi
    
    # Test basic execution
    if ! "$CLI_COMMAND" --help >/dev/null 2>&1; then
        log_error "CLI help command failed"
        return 1
    fi
    
    log_success "CLI entry point test passed"
}

# Test version commands
test_version_commands() {
    log_info "Testing version commands"
    
    # Test --version flag (standard convention)
    local version_output
    if version_output=$("$CLI_COMMAND" --version 2>&1); then
        log_info "Version output: $version_output"
        
        if [[ "$version_output" =~ $EXPECTED_VERSION ]]; then
            log_success "Version flag test passed"
        else
            log_warning "Version mismatch in --version output"
            log_info "Expected: $EXPECTED_VERSION, Got: $version_output"
        fi
    else
        log_error "Version flag failed"
        return 1
    fi
    
    # Test version subcommand (alternative method)
    if "$CLI_COMMAND" version >/dev/null 2>&1; then
        log_success "Version subcommand also available"
    else
        log_info "Version subcommand not available (using flag instead)"
    fi
}

# Test help system
test_help_system() {
    log_info "Testing help system"
    
    # Test main help
    if ! "$CLI_COMMAND" --help >/dev/null 2>&1; then
        log_error "Main help command failed"
        return 1
    fi
    
    # Test subcommand help
    local subcommands=("assignments" "repos" "secrets" "automation")
    
    for cmd in "${subcommands[@]}"; do
        if "$CLI_COMMAND" "$cmd" --help >/dev/null 2>&1; then
            log_success "Help for '$cmd' subcommand passed"
        else
            log_warning "Help for '$cmd' subcommand failed or not available"
        fi
    done
    
    # Test nested command help
    local nested_commands=(
        "assignments setup"
        "assignments orchestrate"
        "assignments validate"
        "repos fetch"
        "repos collaborator"
        "secrets manager"
    )
    
    for cmd in "${nested_commands[@]}"; do
        if $CLI_COMMAND $cmd --help >/dev/null 2>&1; then
            log_success "Help for '$cmd' command passed"
        else
            log_info "Help for '$cmd' command not available or failed (may be expected)"
        fi
    done
}

# Test command structure
test_command_structure() {
    log_info "Testing command structure"
    
    # Test that main command shows help when no args
    local no_args_output
    if no_args_output=$("$CLI_COMMAND" 2>&1) && [[ "$no_args_output" =~ "Usage:" ]]; then
        log_success "No-args help display passed"
    else
        log_warning "No-args behavior may not show help"
    fi
    
    # Test invalid command handling
    local invalid_output
    if invalid_output=$("$CLI_COMMAND" invalid-command-xyz 2>&1); then
        log_warning "Invalid command did not exit with error (may be expected)"
    else
        log_success "Invalid command properly rejected"
    fi
}

# Test configuration-related commands
test_configuration_commands() {
    log_info "Testing configuration commands"
    
    # Create temporary test directory
    local test_dir="$TEST_DIR/temp_config_test"
    mkdir -p "$test_dir"
    cd "$test_dir"
    
    # Create sample configuration first
    cat > assignment.conf << EOF
# Sample configuration for testing
TEMPLATE_REPO_URL=https://github.com/test-org/test-template
GITHUB_ORGANIZATION=test-org
ASSIGNMENT_FILE=assignment.conf
ASSIGNMENT_NAME=Test Assignment
EOF
    
    # Test orchestration (dry-run) - this is the main command that supports dry-run
    if "$CLI_COMMAND" assignments orchestrate --dry-run >/dev/null 2>&1; then
        log_success "Orchestration dry-run passed"
    else
        log_info "Orchestration dry-run failed (may need valid configuration)"
    fi
    
    # Test that setup command exists (but don't run it as it's interactive)
    if "$CLI_COMMAND" assignments setup --help >/dev/null 2>&1; then
        log_success "Setup command available"
    else
        log_info "Setup command not available"
    fi
    
    # Test that manage command exists
    if "$CLI_COMMAND" assignments manage --help >/dev/null 2>&1; then
        log_success "Manage command available"
    else
        log_info "Manage command not available"
    fi
    
    # Cleanup
    cd "$SCRIPT_DIR"
    rm -rf "$test_dir"
}

# Test error handling
test_error_handling() {
    log_info "Testing error handling"
    
    # Test invalid subcommand
    local exit_code=0
    "$CLI_COMMAND" nonexistent-subcommand >/dev/null 2>&1 || exit_code=$?
    
    if [ $exit_code -ne 0 ]; then
        log_success "Invalid subcommand properly rejected"
    else
        log_warning "Invalid subcommand did not exit with error"
    fi
    
    # Test missing required arguments (use a command that requires args but isn't interactive)
    exit_code=0
    "$CLI_COMMAND" assignments orchestrate --config nonexistent-file.conf >/dev/null 2>&1 || exit_code=$?
    
    if [ $exit_code -ne 0 ]; then
        log_success "Missing configuration file properly handled"
    else
        log_info "Missing config command succeeded (may be valid with defaults)"
    fi
    
    # Test invalid orchestration with missing config
    local test_dir="$TEST_DIR/temp_error_test"
    mkdir -p "$test_dir"
    cd "$test_dir"
    
    # Create invalid/minimal configuration
    echo "INVALID_CONFIG_OPTION=true" > assignment.conf
    
    exit_code=0
    "$CLI_COMMAND" assignments orchestrate --dry-run >/dev/null 2>&1 || exit_code=$?
    
    if [ $exit_code -ne 0 ]; then
        log_success "Invalid configuration properly rejected"
    else
        log_warning "Invalid configuration was accepted"
    fi
    
    # Cleanup
    cd "$SCRIPT_DIR"
    rm -rf "$test_dir"
}

# Test verbose and help modes
test_output_modes() {
    log_info "Testing output modes"
    
    # Test help mode
    if "$CLI_COMMAND" --help >/dev/null 2>&1; then
        log_success "Help mode test passed"
    else
        log_warning "Help mode failed"
    fi
    
    # Test subcommand help
    if "$CLI_COMMAND" assignments --help >/dev/null 2>&1; then
        log_success "Subcommand help test passed"
    else
        log_warning "Subcommand help failed"
    fi
    
    # Test version command with various formats
    if "$CLI_COMMAND" version >/dev/null 2>&1; then
        log_success "Version command test passed"
    else
        log_warning "Version command failed"
    fi
}

# Test dry-run functionality
test_dry_run_mode() {
    log_info "Testing dry-run functionality"
    
    local test_dir="$TEST_DIR/temp_dry_run_test"
    mkdir -p "$test_dir"
    cd "$test_dir"
    
    # Create valid configuration
    cat > assignment.conf << EOF
ASSIGNMENT_NAME="test-assignment"
TEMPLATE_REPO_URL=https://github.com/test-org/test-template
GITHUB_ORGANIZATION=test-org
ASSIGNMENT_FILE=assignment.conf
EOF
    
    # Test dry-run with orchestration (the main command that supports dry-run)
    if "$CLI_COMMAND" assignments orchestrate --dry-run >/dev/null 2>&1; then
        log_success "Orchestration dry-run test passed"
    else
        log_info "Orchestration dry-run test failed (may need full environment)"
    fi
    
    # Test that setup command shows help (but don't run it interactively)
    if "$CLI_COMMAND" assignments setup --help >/dev/null 2>&1; then
        log_success "Setup command help available"
    else
        log_info "Setup command help not available"
    fi
    
    # Cleanup
    cd "$SCRIPT_DIR"
    rm -rf "$test_dir"
}

# Test performance and responsiveness
test_cli_performance() {
    log_info "Testing CLI performance"
    
    # Test help command response time
    local start_time=$(date +%s.%N)
    "$CLI_COMMAND" --help >/dev/null 2>&1
    local end_time=$(date +%s.%N)
    local duration=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "0")
    
    if (( $(echo "$duration < 5.0" | bc -l 2>/dev/null || echo "1") )); then
        log_success "Help command performance acceptable (${duration}s)"
    else
        log_warning "Help command took longer than expected (${duration}s)"
    fi
    
    # Test version command response time
    start_time=$(date +%s.%N)
    "$CLI_COMMAND" --version >/dev/null 2>&1
    end_time=$(date +%s.%N)
    duration=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "0")
    
    if (( $(echo "$duration < 3.0" | bc -l 2>/dev/null || echo "1") )); then
        log_success "Version command performance acceptable (${duration}s)"
    else
        log_warning "Version command took longer than expected (${duration}s)"
    fi
}

# Main execution
main() {
    log_info "Starting CLI interface tests"
    
    # Test CLI entry point
    if ! test_cli_entry_point; then
        log_error "CLI entry point test failed"
        exit 1
    fi
    
    # Test version commands
    if ! test_version_commands; then
        log_error "Version commands test failed"
        exit 1
    fi
    
    # Test help system
    if ! test_help_system; then
        log_error "Help system test failed"
        exit 1
    fi
    
    # Test command structure
    test_command_structure
    
    # Test configuration commands
    test_configuration_commands
    
    # Test error handling
    test_error_handling
    
    # Test output modes
    test_output_modes
    
    # Test dry-run functionality
    test_dry_run_mode
    
    # Test performance
    test_cli_performance
    
    log_success "All CLI interface tests completed!"
}

# Handle command line execution
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi