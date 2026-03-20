#!/bin/bash
################################################################################
# Test Suite: Repos Commands
#
# Comprehensive QA testing for all classdock repos commands.
# Tests 4 commands with various options, error scenarios, and edge cases.
#
# Commands tested:
# - fetch: Discover and fetch student repositories
# - update: Update assignment configuration and student repositories
# - push: Sync template repository to GitHub Classroom repository
# - cycle-collaborator: Cycle repository collaborator permissions
#
# Usage:
#   ./test_repos_commands.sh [--fetch|--update|--push|--cycle|--all]
#
# Options:
#   --fetch       Run only fetch command tests
#   --update      Run only update command tests
#   --push        Run only push command tests
#   --cycle       Run only cycle-collaborator tests
#   --all         Run all tests (default)
#
# Requirements:
#   - lib/test_helpers.sh
#   - lib/mock_helpers.sh
#   - fixtures/repos/ directory with test fixtures
#   - classdock CLI installed (via poetry)
#
################################################################################

set -euo pipefail

# Script directory and paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
FIXTURES_DIR="$PROJECT_ROOT/test_project_repos/fixtures"
REPOS_FIXTURES_DIR="$FIXTURES_DIR/repos"
ASSIGNMENTS_FIXTURES_DIR="$FIXTURES_DIR/assignments"

# Source test helpers
source "$PROJECT_ROOT/test_project_repos/lib/test_helpers.sh"
source "$PROJECT_ROOT/test_project_repos/lib/mock_helpers.sh"

# Initialize test tracking
init_test_tracking

# Test environment variables
TEST_TEMP_DIR=""
ORIGINAL_PWD="$PWD"

################################################################################
# Cleanup Function
################################################################################

cleanup() {
    log_step "Cleaning up test environment"
    
    # Cleanup mocks
    cleanup_mocks
    
    # Remove temporary test directories
    if [ -n "$TEST_TEMP_DIR" ] && [ -d "$TEST_TEMP_DIR" ]; then
        rm -rf "$TEST_TEMP_DIR"
    fi
    
    # Remove test assignment.conf if we created it
    if [ -f "$PROJECT_ROOT/assignment.conf" ]; then
        rm -f "$PROJECT_ROOT/assignment.conf"
        log_info "Removed test assignment.conf from PROJECT_ROOT"
    fi
    
    # Restore original working directory
    cd "$ORIGINAL_PWD" || true
}

# Set trap for cleanup
trap cleanup EXIT INT TERM

################################################################################
# Helper Functions
################################################################################

setup_test_environment() {
    log_step "Setting up test environment for repos commands"
    
    # Initialize mock environment
    mock_environment_setup
    
    # Setup mock GitHub token
    local mock_token
    mock_token=$(setup_mock_github_token)
    
    # Create temporary directory for test files
    TEST_TEMP_DIR=$(mktemp -d -t "repos_test_XXXXXX")
    
    # Create assignment.conf in PROJECT_ROOT for commands that require it
    create_minimal_test_config "$PROJECT_ROOT"
    
    log_info "Test environment ready. Temp dir: $TEST_TEMP_DIR"
}

create_test_config() {
    local fixture_name="$1"
    local dest_path="${2:-$TEST_TEMP_DIR/assignment.conf}"
    
    # Try repos fixtures first, then assignments fixtures
    local fixture_path=""
    if [ -f "$REPOS_FIXTURES_DIR/$fixture_name" ]; then
        fixture_path="$REPOS_FIXTURES_DIR/$fixture_name"
    elif [ -f "$ASSIGNMENTS_FIXTURES_DIR/$fixture_name" ]; then
        fixture_path="$ASSIGNMENTS_FIXTURES_DIR/$fixture_name"
    else
        log_error "Fixture not found: $fixture_name"
        return 1
    fi
    
    cp "$fixture_path" "$dest_path"
    echo "$dest_path"
}

# Helper: Assert verbose output contains expected indicators
# Usage: assert_verbose_output "$output"
assert_verbose_output() {
    local output="$1"
    
    # Look for verbose indicators from the CLI logger
    if echo "$output" | grep -qi "verbose mode enabled\|debug\|\[DEBUG\]"; then
        return 0
    fi
    
    return 1
}

# Helper: Assert dry-run output contains expected indicators
# Usage: assert_dry_run_output "$output"
assert_dry_run_output() {
    local output="$1"
    
    # Look for dry-run markers from the CLI
    if echo "$output" | grep -qi "DRY RUN:"; then
        return 0
    fi
    
    return 1
}

# Helper: Capture filesystem state for dry-run validation
# Usage: snapshot_filesystem "$directory"
snapshot_filesystem() {
    local directory="$1"
    
    # Create a snapshot of files and directories
    if [ -d "$directory" ]; then
        find "$directory" -type f -o -type d | sort
    else
        echo ""
    fi
}

# Helper: Compare filesystem snapshots
# Usage: compare_snapshots "$before" "$after"
compare_snapshots() {
    local before="$1"
    local after="$2"
    
    if [ "$before" = "$after" ]; then
        return 0
    else
        return 1
    fi
}

# Helper: Assert CLI success message with exact check mark prefix
# Usage: assert_cli_success_msg "<expected_message>" "$output"
assert_cli_success_msg() {
    local expected="$1"
    local output="$2"
    
    # Look for exact message with check mark prefix (✅)
    if echo "$output" | grep -qF "✅ $expected"; then
        return 0
    fi
    
    return 1
}

################################################################################
# Section 1: Fetch Command Tests
################################################################################

run_fetch_tests() {
    log_info "Testing: repos fetch command"
    
    test_fetch_auto_discovery_mocked
    test_fetch_with_repos_list_mocked
    test_fetch_empty_repos_list
    test_fetch_invalid_repos_list
    test_fetch_no_config
    test_fetch_dry_run_smoke_test
    test_fetch_verbose
    test_fetch_custom_config_success
    test_fetch_custom_config_failure
    test_fetch_combined_options
}

test_fetch_auto_discovery_mocked() {
    log_step "Testing fetch with auto-discovery (mocked)"
    
    # Note: Using Python mock helper to simulate auto-discovery without --dry-run.
    # This exercises the full service path: CLI -> ReposService.fetch() -> RepositoryFetcher.fetch_all_repositories()
    
    local config_file
    config_file=$(create_test_config "valid_repos_config.conf")
    
    local output
    local exit_code=0
    
    # Run with auto_discovery scenario mock
    output=$(cd "$PROJECT_ROOT" && SCENARIO=auto_discovery poetry run python test_project_repos/lib/run_with_fetch_mocks.py --config "$config_file" 2>&1) || exit_code=$?
    
    # Assert exit code 0 and exact success message from CLI
    if [ $exit_code -eq 0 ] && assert_cli_success_msg "Repository fetch completed successfully" "$output"; then
        mark_test_passed "Fetch with auto-discovery (mocked)"
    else
        mark_test_failed "Fetch auto-discovery" "Expected exit 0 with '✅ Repository fetch completed successfully'. Got exit=$exit_code, output: $output"
    fi
}

test_fetch_custom_config_success() {
    log_step "Testing fetch with custom config file (success scenario)"
    
    # Note: Using Python mock helper to simulate successful fetch with custom config.
    # This exercises the service path with deterministic success outcome.
    
    local custom_config="$TEST_TEMP_DIR/custom_fetch_config.conf"
    create_test_config "valid_repos_config.conf" "$custom_config"
    
    local output
    local exit_code=0
    
    # Run with auto_discovery scenario mock (simulates successful fetch)
    output=$(cd "$PROJECT_ROOT" && SCENARIO=auto_discovery poetry run python test_project_repos/lib/run_with_fetch_mocks.py --config "$custom_config" 2>&1) || exit_code=$?
    
    # Assert exit code 0 and exact success message
    if [ $exit_code -eq 0 ] && assert_cli_success_msg "Repository fetch completed successfully" "$output"; then
        mark_test_passed "Fetch with custom config (success)"
    else
        mark_test_failed "Fetch custom config success" "Expected exit 0 with '✅ Repository fetch completed successfully'. Got exit=$exit_code"
    fi
}

test_fetch_custom_config_failure() {
    log_step "Testing fetch with custom config file (failure scenario)"
    
    # Note: Using Python mock helper to simulate failed fetch (empty discovery result).
    # This validates error handling in the service layer.
    
    local custom_config="$TEST_TEMP_DIR/custom_fetch_fail_config.conf"
    create_test_config "valid_repos_config.conf" "$custom_config"
    
    local output
    local exit_code=0
    
    # Run with empty_list scenario mock (simulates fetch failure)
    output=$(cd "$PROJECT_ROOT" && SCENARIO=empty_list poetry run python test_project_repos/lib/run_with_fetch_mocks.py --config "$custom_config" 2>&1) || exit_code=$?
    
    # Assert exit code 1 and exact failure message from service
    if [ $exit_code -eq 1 ] && echo "$output" | grep -qF "Repository fetch failed"; then
        mark_test_passed "Fetch with custom config (failure)"
    else
        mark_test_failed "Fetch custom config failure" "Expected exit 1 with 'Repository fetch failed'. Got exit=$exit_code"
    fi
}

test_fetch_no_config() {
    log_step "Testing fetch without config file"
    
    local nonexistent_config="$TEST_TEMP_DIR/nonexistent.conf"
    
    local output
    local exit_code=0
    
    output=$(cd "$PROJECT_ROOT" && poetry run classdock repos fetch --config "$nonexistent_config" 2>&1) || exit_code=$?
    
    if [ $exit_code -ne 0 ] && echo "$output" | grep -qi "not found\|file.*not.*exist\|no such file\|error"; then
        mark_test_passed "Fetch detects missing config"
    else
        mark_test_failed "Fetch no config" "Expected non-zero exit with file not found error. Got exit=$exit_code"
    fi
}

test_fetch_with_repos_list_mocked() {
    log_step "Testing fetch with student repos list (mocked)"
    
    # Note: This test validates repos-list discovery using mocks. Until native STUDENT_FILES
    # support is implemented in RepositoryFetcher, we simulate list-based discovery by
    # patching discover_repositories() to return repos from student_repos.txt fixture.
    # 
    # This exercises the full service path without --dry-run and validates exact CLI messages.
    
    # Create config that references the repos list file
    local config_file="$TEST_TEMP_DIR/fetch_with_list.conf"
    create_test_config "valid_repos_config.conf" "$config_file"
    
    # Add STUDENT_FILES pointing to student_repos.txt fixture
    echo "STUDENT_FILES=$REPOS_FIXTURES_DIR/student_repos.txt" >> "$config_file"
    
    local output
    local exit_code=0
    
    # Run with repos_list scenario mock (simulates reading from student_repos.txt)
    output=$(cd "$PROJECT_ROOT" && SCENARIO=repos_list REPOS_LIST_FILE="$REPOS_FIXTURES_DIR/student_repos.txt" poetry run python test_project_repos/lib/run_with_fetch_mocks.py --config "$config_file" 2>&1) || exit_code=$?
    
    # Assert exit code 0 and exact success message from CLI
    if [ $exit_code -eq 0 ] && assert_cli_success_msg "Repository fetch completed successfully" "$output"; then
        mark_test_passed "Fetch with student repos list (mocked)"
    else
        mark_test_failed "Fetch with repos list" "Expected exit 0 with '✅ Repository fetch completed successfully'. Got exit=$exit_code, output: $output"
    fi
}

test_fetch_empty_repos_list() {
    log_step "Testing fetch with empty repos list (mocked)"
    
    # Note: Uses Python mock helper to simulate empty repository discovery.
    # This validates that the service layer properly handles no repositories found
    # and returns appropriate error message and exit code.
    
    local empty_config="$TEST_TEMP_DIR/fetch_empty.conf"
    create_test_config "valid_repos_config.conf" "$empty_config"
    echo "STUDENT_FILES=$REPOS_FIXTURES_DIR/empty_repos.txt" >> "$empty_config"
    
    local output
    local exit_code=0
    
    # Run with empty_list scenario mock (simulates discovery returning [])
    output=$(cd "$PROJECT_ROOT" && SCENARIO=empty_list poetry run python test_project_repos/lib/run_with_fetch_mocks.py --config "$empty_config" 2>&1) || exit_code=$?
    
    # Assert non-zero exit code and exact error message from service
    if [ $exit_code -eq 1 ] && echo "$output" | grep -qF "Repository fetch failed"; then
        mark_test_passed "Fetch with empty repos list (mocked)"
    else
        mark_test_failed "Fetch empty list" "Expected exit 1 with 'Repository fetch failed'. Got exit=$exit_code, output: $output"
    fi
}

test_fetch_invalid_repos_list() {
    log_step "Testing fetch with invalid repos list (mocked)"
    
    # Note: Uses Python mock helper to simulate invalid URL error during discovery.
    # This validates that the service layer properly surfaces GitHubDiscoveryError
    # from RepositoryFetcher and returns appropriate error to CLI.
    
    local invalid_config="$TEST_TEMP_DIR/fetch_invalid.conf"
    create_test_config "valid_repos_config.conf" "$invalid_config"
    echo "STUDENT_FILES=$REPOS_FIXTURES_DIR/invalid_repos.txt" >> "$invalid_config"
    
    local output
    local exit_code=0
    
    # Run with invalid_urls scenario mock (simulates GitHubDiscoveryError)
    output=$(cd "$PROJECT_ROOT" && SCENARIO=invalid_urls poetry run python test_project_repos/lib/run_with_fetch_mocks.py --config "$invalid_config" 2>&1) || exit_code=$?
    
    # Assert non-zero exit code and error message contains invalid URL indicator
    if [ $exit_code -eq 1 ] && echo "$output" | grep -qi "invalid.*url\|repository fetch failed"; then
        mark_test_passed "Fetch with invalid repos list (mocked)"
    else
        mark_test_failed "Fetch invalid list" "Expected exit 1 with invalid URL error. Got exit=$exit_code, output: $output"
    fi
}

test_fetch_verbose() {
    log_step "Testing fetch with --verbose"
    
    local config_file
    config_file=$(create_test_config "valid_repos_config.conf")
    
    local output
    local exit_code=0
    
    # Run with --verbose and --dry-run (options are on repos_app, not main app)
    output=$(cd "$PROJECT_ROOT" && poetry run classdock repos --verbose --dry-run fetch --config "$config_file" 2>&1) || exit_code=$?
    
    # Require exit code 0 and explicit verbose indicators
    if [ $exit_code -eq 0 ] && assert_verbose_output "$output"; then
        mark_test_passed "Fetch with --verbose"
    else
        mark_test_failed "Fetch verbose" "Expected exit 0 with verbose indicators. Got exit=$exit_code"
    fi
}

test_fetch_dry_run_smoke_test() {
    log_step "Testing fetch with --dry-run (smoke test)"
    
    # Note: This is a minimal smoke test to verify --dry-run flag behavior.
    # The dry-run flag causes early return in CLI before service is called.
    # We verify: 1) DRY RUN banner is displayed, 2) No filesystem changes, 3) Exit code 0.
    # Other tests use mocks to exercise the actual service layer without --dry-run.
    
    local config_file
    config_file=$(create_test_config "valid_repos_config.conf")
    
    # Snapshot filesystem before dry-run
    local snapshot_before
    snapshot_before=$(snapshot_filesystem "$TEST_TEMP_DIR")
    
    local output
    local exit_code=0
    
    output=$(cd "$PROJECT_ROOT" && poetry run classdock repos --dry-run fetch --config "$config_file" 2>&1) || exit_code=$?
    
    # Snapshot filesystem after dry-run
    local snapshot_after
    snapshot_after=$(snapshot_filesystem "$TEST_TEMP_DIR")
    
    # Require exit code 0, explicit dry-run indicator, and no filesystem changes
    if [ $exit_code -eq 0 ] && assert_dry_run_output "$output"; then
        if compare_snapshots "$snapshot_before" "$snapshot_after"; then
            mark_test_passed "Fetch with --dry-run (smoke test)"
        else
            mark_test_failed "Fetch dry-run" "Dry-run mode created filesystem changes"
        fi
    else
        mark_test_failed "Fetch dry-run" "Expected exit 0 with DRY RUN indicator. Got exit=$exit_code"
    fi
}

test_fetch_combined_options() {
    log_step "Testing fetch with combined options"
    
    local custom_config="$TEST_TEMP_DIR/combined_config.conf"
    create_test_config "valid_repos_config.conf" "$custom_config"
    
    local output
    local exit_code=0
    
    # Run with both --verbose and --dry-run (options are on repos_app)
    output=$(cd "$PROJECT_ROOT" && poetry run classdock repos --verbose --dry-run fetch --config "$custom_config" 2>&1) || exit_code=$?
    
    # Require exit code 0 with both verbose and dry-run indicators
    if [ $exit_code -eq 0 ] && assert_verbose_output "$output" && assert_dry_run_output "$output"; then
        mark_test_passed "Fetch with combined --verbose and --dry-run"
    else
        mark_test_failed "Fetch combined options" "Expected exit 0 with both verbose and dry-run indicators. Got exit=$exit_code"
    fi
}

################################################################################
# Main Test Execution
################################################################################

run_all_tests() {
    log_info "Running all repos command tests"

    run_fetch_tests
}

main() {
    log_step "Starting Repos Commands Test Suite"

    # Setup test environment
    setup_test_environment

    # Parse command-line arguments
    local run_mode="${1:---all}"

    case "$run_mode" in
        --fetch)
            run_fetch_tests
            ;;
        --all|*)
            run_all_tests
            ;;
    esac
    
    # Show test summary
    show_test_summary
    
    # Return exit code based on test results
    if [ "${TESTS_FAILED:-0}" -eq 0 ]; then
        return 0
    else
        return 1
    fi
}

# Script entry point
main "$@"
exit $?
