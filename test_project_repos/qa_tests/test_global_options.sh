#!/bin/bash
################################################################################
# Test Suite: Global Options
#
# Comprehensive QA testing for all classdock global CLI options.
# Tests --verbose, --dry-run, --config, and --assignment-root across all
# command groups (assignments, repos, secrets, automation, config).
#
# Commands tested:
# Global options:
#   - --verbose: Enable detailed logging
#   - --dry-run: Show what would be done without executing
#   - --config: Specify custom configuration file path
#   - --assignment-root: Specify assignment root directory
#
# Usage:
#   ./test_global_options.sh [--verbose-tests|--dry-run-tests|--config-tests|--assignment-root-tests|--combined-tests|--all]
#
# Options:
#   --verbose-tests         Run only --verbose option tests
#   --dry-run-tests         Run only --dry-run option tests
#   --config-tests          Run only --config option tests
#   --assignment-root-tests Run only --assignment-root option tests
#   --combined-tests        Run only combined options tests
#   --all                   Run all tests (default)
#
# Requirements:
#   - lib/test_helpers.sh
#   - lib/mock_helpers.sh
#   - fixtures/ directory with test fixtures
#   - classdock CLI installed (via poetry)
#
################################################################################

set -euo pipefail

# Script directory and paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
FIXTURES_DIR="$PROJECT_ROOT/test_project_repos/fixtures"
CONFIGS_FIXTURES_DIR="$FIXTURES_DIR/configs"
ASSIGNMENTS_FIXTURES_DIR="$FIXTURES_DIR/assignments"

# Store original working directory
ORIGINAL_PWD="$(pwd)"

# Test Suite Configuration
TEST_SUITE_NAME="test_global_options"

# Source test helpers
source "$PROJECT_ROOT/test_project_repos/lib/test_helpers.sh"
source "$PROJECT_ROOT/test_project_repos/lib/skipped_tests.sh"
source "$PROJECT_ROOT/test_project_repos/lib/mock_helpers.sh"

################################################################################
# Cleanup Function
################################################################################

cleanup() {
    log_step "Cleaning up test environment"
    
    # Cleanup mocks
    cleanup_mocks
    
    # Remove temporary test directories
    if [ -n "${TEST_TEMP_DIR:-}" ] && [ -d "$TEST_TEMP_DIR" ]; then
        rm -rf "$TEST_TEMP_DIR"
    fi
    
    # Remove test assignment.conf if we created it
    rm -f "$PROJECT_ROOT/assignment.conf" 2>/dev/null || true
    
    # Restore original working directory
    cd "$ORIGINAL_PWD" || true
}

# Set trap for cleanup
trap cleanup EXIT INT TERM

################################################################################
# Helper Functions
################################################################################

setup_test_environment() {
    log_step "Setting up test environment for global options"
    
    # Initialize mock environment
    mock_environment_setup
    
    # Setup mock GitHub token
    local mock_token
    mock_token=$(setup_mock_github_token)
    
    # Create temporary directory for test files
    TEST_TEMP_DIR=$(mktemp -d -t "global_options_test_XXXXXX")
    
    # Create assignment.conf in PROJECT_ROOT for commands that require it
    create_minimal_test_config "$PROJECT_ROOT"
    
    log_info "Test environment ready. Temp dir: $TEST_TEMP_DIR"
}

create_test_config() {
    local config_type="${1:-valid}"
    local dest_path="${2:-$TEST_TEMP_DIR/assignment.conf}"
    
    case "$config_type" in
        valid)
            if [ -f "$CONFIGS_FIXTURES_DIR/valid_comprehensive.conf" ]; then
                cp "$CONFIGS_FIXTURES_DIR/valid_comprehensive.conf" "$dest_path"
            else
                # Create minimal valid config
                cat > "$dest_path" << 'EOF'
CLASSROOM_URL=https://classroom.github.com/classrooms/123456/assignments/test-assignment
TEMPLATE_REPO_URL=https://github.com/test-org/test-assignment-template
GITHUB_ORGANIZATION=test-org
ASSIGNMENT_NAME=test-assignment
ASSIGNMENT_FILE=assignment.ipynb
CLASSROOM_REPO_URL=https://github.com/test-org/classroom-test-assignment
EOF
            fi
            ;;
        *)
            log_error "Unknown config type: $config_type"
            return 1
            ;;
    esac
    
    echo "$dest_path"
}

verify_verbose_output() {
    local output="$1"
    
    # Check for verbose indicators (DEBUG messages, detailed steps)
    if echo "$output" | grep -qiE "(DEBUG|verbose|detailed|step)"; then
        return 0
    else
        return 1
    fi
}

verify_dry_run_output() {
    local output="$1"
    
    # Check for "DRY RUN:" prefix
    if echo "$output" | grep -qF "DRY RUN:"; then
        return 0
    else
        return 1
    fi
}

################################################################################
# Section 1: --verbose Option Tests
################################################################################

test_verbose_assignments_setup() {
    # Check if test should be skipped
    is_test_skipped "${FUNCNAME[0]}" && mark_test_skipped "verbose assignments setup" "$(get_skip_reason "${FUNCNAME[0]}")" && return
    log_step "Testing --verbose with assignments setup"
    
    local output
    local exit_code=0
    
    output=$(cd "$PROJECT_ROOT" && poetry run classdock assignments --verbose --dry-run setup 2>&1) || exit_code=$?
    
    if [ $exit_code -eq 0 ] && verify_verbose_output "$output"; then
        mark_test_passed "verbose with assignments setup shows detailed output"
    else
        mark_test_failed "verbose assignments setup" "Expected verbose output with exit 0, got exit=$exit_code"
    fi
}

test_verbose_assignments_validate_config() {
    # Check if test should be skipped
    is_test_skipped "${FUNCNAME[0]}" && mark_test_skipped "verbose assignments validate config" "$(get_skip_reason "${FUNCNAME[0]}")" && return
    log_step "Testing --verbose with assignments validate-config"
    
    local config_file
    config_file=$(create_test_config "valid")
    
    local output
    local exit_code=0
    
    output=$(cd "$PROJECT_ROOT" && poetry run classdock assignments --verbose validate-config --config-file "$config_file" 2>&1) || exit_code=$?
    
    if [ $exit_code -eq 0 ] && verify_verbose_output "$output"; then
        mark_test_passed "verbose with validate-config shows detailed validation"
    else
        mark_test_failed "verbose validate-config" "Expected verbose validation output, got exit=$exit_code"
    fi
}

test_verbose_assignments_orchestrate() {
    # Check if test should be skipped
    is_test_skipped "${FUNCNAME[0]}" && mark_test_skipped "verbose assignments orchestrate" "$(get_skip_reason "${FUNCNAME[0]}")" && return
    log_step "Testing --verbose with assignments orchestrate"
    
    local config_file
    config_file=$(create_test_config "valid")
    
    local output
    local exit_code=0
    
    output=$(cd "$PROJECT_ROOT" && poetry run classdock assignments --verbose --dry-run orchestrate --config "$config_file" 2>&1) || exit_code=$?
    
    if [ $exit_code -eq 0 ] && verify_verbose_output "$output"; then
        mark_test_passed "verbose with orchestrate shows workflow steps"
    else
        mark_test_failed "verbose orchestrate" "Expected verbose workflow output, got exit=$exit_code"
    fi
}

test_verbose_repos_fetch() {
    log_step "Testing --verbose with repos fetch"
    
    local config_file
    config_file=$(create_test_config "valid")
    
    local output
    local exit_code=0
    
    output=$(cd "$PROJECT_ROOT" && poetry run classdock repos --verbose --dry-run fetch --config "$config_file" 2>&1) || exit_code=$?
    
    if [ $exit_code -eq 0 ] && verify_verbose_output "$output"; then
        mark_test_passed "verbose with repos fetch shows discovery logging"
    else
        mark_test_failed "verbose repos fetch" "Expected verbose fetch output, got exit=$exit_code"
    fi
}

test_verbose_combined_with_dry_run() {
    # Check if test should be skipped
    is_test_skipped "${FUNCNAME[0]}" && mark_test_skipped "verbose combined with dry run" "$(get_skip_reason "${FUNCNAME[0]}")" && return
    log_step "Testing --verbose combined with --dry-run"
    
    local config_file
    config_file=$(create_test_config "valid")
    
    local output
    local exit_code=0
    
    output=$(cd "$PROJECT_ROOT" && poetry run classdock assignments --verbose --dry-run orchestrate --config "$config_file" 2>&1) || exit_code=$?
    
    if [ $exit_code -eq 0 ] && verify_verbose_output "$output" && verify_dry_run_output "$output"; then
        mark_test_passed "verbose and dry-run work together"
    else
        mark_test_failed "verbose combined with dry-run" "Expected both verbose and DRY RUN output, got exit=$exit_code"
    fi
}

run_verbose_tests() {
    log_section "Running --verbose Option Tests"
    
    test_verbose_assignments_setup
    test_verbose_assignments_validate_config
    test_verbose_assignments_orchestrate
    test_verbose_repos_fetch
    test_verbose_combined_with_dry_run
}

################################################################################
# Section 2: --dry-run Option Tests
################################################################################

test_dry_run_assignments_setup() {
    log_step "Testing --dry-run with assignments setup"
    
    local output
    local exit_code=0
    
    # Ensure no assignment.conf exists before test
    rm -f "$PROJECT_ROOT/assignment.conf"
    
    output=$(cd "$PROJECT_ROOT" && poetry run classdock assignments --dry-run setup 2>&1) || exit_code=$?
    
    # Verify DRY RUN message and no file created
    if [ $exit_code -eq 0 ] && verify_dry_run_output "$output" && [ ! -f "$PROJECT_ROOT/assignment.conf" ]; then
        mark_test_passed "dry-run setup shows DRY RUN and creates no file"
    else
        mark_test_failed "dry-run assignments setup" "Expected DRY RUN with no file creation, got exit=$exit_code"
    fi
    
    # Restore config for other tests
    create_minimal_test_config "$PROJECT_ROOT"
}

test_dry_run_assignments_orchestrate() {
    # Check if test should be skipped
    is_test_skipped "${FUNCNAME[0]}" && mark_test_skipped "dry-run orchestrate" "$(get_skip_reason "${FUNCNAME[0]}")" && return
    
    log_step "Testing --dry-run with assignments orchestrate"
    
    local config_file
    config_file=$(create_test_config "valid")
    
    local output
    local exit_code=0
    
    output=$(cd "$PROJECT_ROOT" && poetry run classdock assignments --dry-run orchestrate --config "$config_file" 2>&1) || exit_code=$?
    
    if [ $exit_code -eq 0 ] && verify_dry_run_output "$output"; then
        mark_test_passed "dry-run orchestrate shows workflow plan without execution"
    else
        mark_test_failed "dry-run orchestrate" "Expected DRY RUN output, got exit=$exit_code"
    fi
}

test_dry_run_repos_fetch() {
    log_step "Testing --dry-run with repos fetch"
    
    local config_file
    config_file=$(create_test_config "valid")
    
    local output
    local exit_code=0
    
    output=$(cd "$PROJECT_ROOT" && poetry run classdock repos --dry-run fetch --config "$config_file" 2>&1) || exit_code=$?
    
    if [ $exit_code -eq 0 ] && verify_dry_run_output "$output"; then
        mark_test_passed "dry-run fetch shows plan without cloning"
    else
        mark_test_failed "dry-run repos fetch" "Expected DRY RUN output, got exit=$exit_code"
    fi
}

run_dry_run_tests() {
    log_section "Running --dry-run Option Tests"
    
    test_dry_run_assignments_setup
    test_dry_run_assignments_orchestrate
    test_dry_run_repos_fetch
}

################################################################################
# Section 3: --config Option Tests
################################################################################

test_config_custom_path_assignments() {
    log_step "Testing --config with custom path for assignments"
    
    local custom_config="$TEST_TEMP_DIR/custom_assignment.conf"
    create_test_config "valid" "$custom_config"
    
    local output
    local exit_code=0
    
    output=$(cd "$PROJECT_ROOT" && poetry run classdock --config "$custom_config" assignments validate-config 2>&1) || exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        mark_test_passed "config option loads from custom path"
    else
        mark_test_failed "config custom path assignments" "Expected successful validation, got exit=$exit_code"
    fi
}

test_config_nonexistent_file() {
    # Check if test should be skipped
    is_test_skipped "${FUNCNAME[0]}" && mark_test_skipped "config nonexistent file" "$(get_skip_reason "${FUNCNAME[0]}")" && return
    log_step "Testing --config with nonexistent file"
    
    local output
    local exit_code=0
    
    output=$(cd "$PROJECT_ROOT" && poetry run classdock --config nonexistent.conf assignments validate-config 2>&1) || exit_code=$?
    
    if [ $exit_code -ne 0 ] && echo "$output" | grep -qiE "(not found|missing|does not exist)"; then
        mark_test_passed "config nonexistent file shows clear error"
    else
        mark_test_failed "config nonexistent file" "Expected error about missing config, got exit=$exit_code"
    fi
}

test_config_relative_path() {
    # Check if test should be skipped
    is_test_skipped "${FUNCNAME[0]}" && mark_test_skipped "config relative path" "$(get_skip_reason "${FUNCNAME[0]}")" && return
    log_step "Testing --config with relative path"
    
    # Create config in subdirectory
    mkdir -p "$TEST_TEMP_DIR/subdir"
    local rel_config="$TEST_TEMP_DIR/subdir/assignment.conf"
    create_test_config "valid" "$rel_config"
    
    local output
    local exit_code=0
    
    # Use relative path from PROJECT_ROOT
    cd "$TEST_TEMP_DIR"
    output=$(poetry run classdock --config "./subdir/assignment.conf" assignments validate-config 2>&1) || exit_code=$?
    cd "$PROJECT_ROOT"
    
    if [ $exit_code -eq 0 ]; then
        mark_test_passed "config relative path resolution works"
    else
        mark_test_failed "config relative path" "Expected successful validation, got exit=$exit_code"
    fi
}

test_config_absolute_path() {
    log_step "Testing --config with absolute path"
    
    local abs_config="$TEST_TEMP_DIR/absolute_assignment.conf"
    create_test_config "valid" "$abs_config"
    
    local output
    local exit_code=0
    
    output=$(cd "$PROJECT_ROOT" && poetry run classdock --config "$abs_config" assignments validate-config 2>&1) || exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        mark_test_passed "config absolute path works"
    else
        mark_test_failed "config absolute path" "Expected successful validation, got exit=$exit_code"
    fi
}

run_config_tests() {
    log_section "Running --config Option Tests"
    
    test_config_custom_path_assignments
    test_config_nonexistent_file
    test_config_relative_path
    test_config_absolute_path
}

################################################################################
# Section 4: --assignment-root Option Tests
################################################################################

test_assignment_root_basic() {
    # Check if test should be skipped
    is_test_skipped "${FUNCNAME[0]}" && mark_test_skipped "assignment root basic" "$(get_skip_reason "${FUNCNAME[0]}")" && return
    log_step "Testing --assignment-root basic functionality"
    
    local root_dir="$TEST_TEMP_DIR/assignment_root"
    mkdir -p "$root_dir"
    create_test_config "valid" "$root_dir/assignment.conf"
    
    local output
    local exit_code=0
    
    output=$(cd "$PROJECT_ROOT" && poetry run classdock --assignment-root "$root_dir" assignments validate-config 2>&1) || exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        mark_test_passed "assignment-root loads config from specified directory"
    else
        mark_test_failed "assignment-root basic" "Expected successful validation, got exit=$exit_code"
    fi
}

test_assignment_root_with_config() {
    # Check if test should be skipped
    is_test_skipped "${FUNCNAME[0]}" && mark_test_skipped "assignment root with config" "$(get_skip_reason "${FUNCNAME[0]}")" && return
    log_step "Testing --assignment-root with --config"
    
    local root_dir="$TEST_TEMP_DIR/assignment_root2"
    mkdir -p "$root_dir"
    create_test_config "valid" "$root_dir/custom.conf"
    
    local output
    local exit_code=0
    
    output=$(cd "$PROJECT_ROOT" && poetry run classdock --assignment-root "$root_dir" --config custom.conf assignments validate-config 2>&1) || exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        mark_test_passed "assignment-root with config resolves paths correctly"
    else
        mark_test_failed "assignment-root with config" "Expected successful validation, got exit=$exit_code"
    fi
}

test_assignment_root_nonexistent() {
    log_step "Testing --assignment-root with nonexistent directory"
    
    local output
    local exit_code=0
    
    output=$(cd "$PROJECT_ROOT" && poetry run classdock --assignment-root "/nonexistent/directory" assignments validate-config 2>&1) || exit_code=$?
    
    if [ $exit_code -ne 0 ] && echo "$output" | grep -qiE "(not found|missing|does not exist)"; then
        mark_test_passed "assignment-root nonexistent directory shows error"
    else
        mark_test_failed "assignment-root nonexistent" "Expected error about missing directory, got exit=$exit_code"
    fi
}

run_assignment_root_tests() {
    log_section "Running --assignment-root Option Tests"
    
    test_assignment_root_basic
    test_assignment_root_with_config
    test_assignment_root_nonexistent
}

################################################################################
# Section 5: Combined Options Tests
################################################################################

test_verbose_dry_run_combined() {
    # Check if test should be skipped
    is_test_skipped "${FUNCNAME[0]}" && mark_test_skipped "verbose dry run combined" "$(get_skip_reason "${FUNCNAME[0]}")" && return
    log_step "Testing --verbose and --dry-run combined"
    
    local config_file
    config_file=$(create_test_config "valid")
    
    local output
    local exit_code=0
    
    output=$(cd "$PROJECT_ROOT" && poetry run classdock assignments --verbose --dry-run orchestrate --config "$config_file" 2>&1) || exit_code=$?
    
    if [ $exit_code -eq 0 ] && verify_verbose_output "$output" && verify_dry_run_output "$output"; then
        mark_test_passed "verbose and dry-run work together seamlessly"
    else
        mark_test_failed "verbose dry-run combined" "Expected both verbose and DRY RUN indicators, got exit=$exit_code"
    fi
}

test_config_assignment_root_combined() {
    # Check if test should be skipped
    is_test_skipped "${FUNCNAME[0]}" && mark_test_skipped "config assignment root combined" "$(get_skip_reason "${FUNCNAME[0]}")" && return
    log_step "Testing --config and --assignment-root combined"
    
    local root_dir="$TEST_TEMP_DIR/combined_root"
    mkdir -p "$root_dir"
    create_test_config "valid" "$root_dir/custom.conf"
    
    local output
    local exit_code=0
    
    output=$(cd "$PROJECT_ROOT" && poetry run classdock --assignment-root "$root_dir" --config custom.conf assignments validate-config 2>&1) || exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        mark_test_passed "config and assignment-root resolve paths correctly together"
    else
        mark_test_failed "config assignment-root combined" "Expected successful validation, got exit=$exit_code"
    fi
}

test_all_options_combined() {
    # Check if test should be skipped
    is_test_skipped "${FUNCNAME[0]}" && mark_test_skipped "all options combined" "$(get_skip_reason "${FUNCNAME[0]}")" && return
    
    log_step "Testing all global options combined"
    
    local root_dir="$TEST_TEMP_DIR/all_options_root"
    mkdir -p "$root_dir"
    create_test_config "valid" "$root_dir/custom.conf"
    
    local output
    local exit_code=0
    
    output=$(cd "$PROJECT_ROOT" && poetry run classdock --verbose --assignment-root "$root_dir" --config custom.conf assignments --dry-run orchestrate 2>&1) || exit_code=$?
    
    if [ $exit_code -eq 0 ] && verify_verbose_output "$output" && verify_dry_run_output "$output"; then
        mark_test_passed "all global options work together without conflicts"
    else
        mark_test_failed "all options combined" "Expected all options working together, got exit=$exit_code"
    fi
}

run_combined_tests() {
    log_section "Running Combined Options Tests"
    
    test_verbose_dry_run_combined
    test_config_assignment_root_combined
    test_all_options_combined
}

################################################################################
# Main Test Execution
################################################################################

run_all_tests() {
    run_verbose_tests
    run_dry_run_tests
    run_config_tests
    run_assignment_root_tests
    run_combined_tests
}

main() {
    log_step "Global Options Test Suite"
    log_info "Testing all classdock global CLI options"
    
    # Setup test environment
    setup_test_environment
    
    # Parse command line arguments
    case "${1:---all}" in
        --verbose-tests)
            run_verbose_tests
            ;;
        --dry-run-tests)
            run_dry_run_tests
            ;;
        --config-tests)
            run_config_tests
            ;;
        --assignment-root-tests)
            run_assignment_root_tests
            ;;
        --combined-tests)
            run_combined_tests
            ;;
        --all|*)
            run_all_tests
            ;;
    esac
    
    # Display results
    show_test_summary
    
    # Return exit code based on test results
    if [ "$TESTS_FAILED" -eq 0 ]; then
        log_success "All global options tests passed!"
        return 0
    else
        log_error "Some global options tests failed"
        return 1
    fi
}

# Execute main function
main "$@"
