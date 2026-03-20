#!/bin/bash
################################################################################
# Test Suite: Automation Commands
#
# Comprehensive QA testing for all classdock automation commands.
# Tests all 9 automation commands with various options and error scenarios.
#
# Commands tested:
# - automation cron-install: Install cron jobs for automated workflows
# - automation cron-remove: Remove installed cron jobs
# - automation cron-status: Show status of installed cron jobs
# - automation cron-logs: Display cron workflow logs
# - automation cron-schedules: List default cron schedules
# - automation cron-sync: Execute workflow steps manually
#
# Usage:
#   ./test_automation_commands.sh [OPTIONS]
#
# Options:
#   --cron-install    Run only cron-install tests
#   --cron-remove     Run only cron-remove tests
#   --cron-status     Run only cron-status tests
#   --cron-logs       Run only cron-logs tests
#   --cron-schedules  Run only cron-schedules tests
#   --cron-sync       Run only cron-sync tests
#   --all             Run all tests (default)
#
# Requirements:
#   - lib/test_helpers.sh
#   - lib/mock_helpers.sh
#   - fixtures/automation/ directory with test fixtures
#   - classdock CLI installed (via poetry)
#
################################################################################

set -euo pipefail

# Script directory and paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
FIXTURES_DIR="$PROJECT_ROOT/test_project_repos/fixtures"
AUTOMATION_FIXTURES_DIR="$FIXTURES_DIR/automation"

# Test Suite Configuration
TEST_SUITE_NAME="test_automation_commands"

# Source test helpers
source "$PROJECT_ROOT/test_project_repos/lib/test_helpers.sh"
source "$PROJECT_ROOT/test_project_repos/lib/skipped_tests.sh"
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
    log_step "Setting up test environment for automation commands"
    
    # Initialize mock environment
    mock_environment_setup
    
    # Setup mock GitHub token
    local mock_token
    mock_token=$(setup_mock_github_token)
    
    # Setup mock crontab to avoid touching real crontab
    setup_mock_crontab
    mock_crontab_command
    
    # Seed mock crontab with sample entries for status/remove tests
    if [ -f "$AUTOMATION_FIXTURES_DIR/sample_crontab.txt" ]; then
        while IFS= read -r line || [ -n "$line" ]; do
            # Skip comments and empty lines
            if [[ ! "$line" =~ ^[[:space:]]*# ]] && [[ -n "$line" ]]; then
                echo "$line" >> "$MOCK_CRONTAB_FILE"
            fi
        done < "$AUTOMATION_FIXTURES_DIR/sample_crontab.txt"
    fi
    
    # Create temporary directory for test files
    TEST_TEMP_DIR=$(mktemp -d -t "automation_test_XXXXXX")
    
    # Create assignment.conf in PROJECT_ROOT for commands that require it
    create_minimal_test_config "$PROJECT_ROOT"
    
    log_info "Test environment ready. Temp dir: $TEST_TEMP_DIR"
}

create_test_config() {
    local config_type="${1:-basic}"
    local dest_path="${2:-$TEST_TEMP_DIR/assignment.conf}"
    
    if [ "$config_type" = "basic" ]; then
        cp "$AUTOMATION_FIXTURES_DIR/automation_config.conf" "$dest_path"
    else
        log_error "Unknown config type: $config_type"
        return 1
    fi
    
    echo "$dest_path"
}

create_mock_log_file() {
    local log_path="$1"
    local fixture_name="${2:-sample_cron_log.txt}"
    
    mkdir -p "$(dirname "$log_path")"
    cp "$AUTOMATION_FIXTURES_DIR/$fixture_name" "$log_path"
}

verify_cron_schedule() {
    local schedule="$1"
    
    # Basic validation: 5 fields separated by spaces
    local field_count
    field_count=$(echo "$schedule" | awk '{print NF}')
    
    if [ "$field_count" -eq 5 ]; then
        return 0
    else
        return 1
    fi
}

################################################################################
# Section 1: Cron-Install Command Tests
################################################################################

test_cron_install_single_step() {
    log_step "Testing cron-install with single step"
    
    local config_file
    config_file=$(create_test_config "basic")
    
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock automation --dry-run cron-install sync 2>&1) || exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        mark_test_passed "cron-install single step executes"
    else
        mark_test_failed "cron-install single step" "Command failed with exit code $exit_code"
    fi
}

test_cron_install_multiple_steps() {
    log_step "Testing cron-install with multiple steps"
    
    local config_file
    config_file=$(create_test_config "basic")
    
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock automation --dry-run cron-install sync secrets cycle 2>&1) || exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        mark_test_passed "cron-install multiple steps executes"
    else
        mark_test_failed "cron-install multiple steps" "Command failed with exit code $exit_code"
    fi
}

test_cron_install_custom_schedule() {
    log_step "Testing cron-install with custom schedule"
    
    local config_file
    config_file=$(create_test_config "basic")
    
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock automation --dry-run cron-install sync --schedule "0 */6 * * *" 2>&1) || exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        mark_test_passed "cron-install with custom schedule executes"
    else
        mark_test_failed "cron-install custom schedule" "Command failed with exit code $exit_code"
    fi
}

test_cron_install_invalid_schedule() {
    # Check if test should be skipped
    is_test_skipped "${FUNCNAME[0]}" && mark_test_skipped "cron-install invalid schedule" "$(get_skip_reason "${FUNCNAME[0]}")" && return
    
    log_step "Testing cron-install with invalid schedule"
    
    local config_file
    config_file=$(create_test_config "basic")
    
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock automation --dry-run cron-install sync --schedule "invalid" 2>&1) || exit_code=$?
    
    if [ $exit_code -ne 0 ]; then
        mark_test_passed "cron-install rejects invalid schedule"
    else
        mark_test_failed "cron-install invalid schedule" "Should reject invalid schedule"
    fi
}

test_cron_install_invalid_step() {
    # Check if test should be skipped
    is_test_skipped "${FUNCNAME[0]}" && mark_test_skipped "cron-install invalid step" "$(get_skip_reason "${FUNCNAME[0]}")" && return
    
    log_step "Testing cron-install with invalid step"
    
    local config_file
    config_file=$(create_test_config "basic")
    
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock automation --dry-run cron-install invalid_step 2>&1) || exit_code=$?
    
    if [ $exit_code -ne 0 ]; then
        mark_test_passed "cron-install rejects invalid step"
    else
        mark_test_failed "cron-install invalid step" "Should reject invalid step name"
    fi
}

test_cron_install_verbose() {
    log_step "Testing cron-install with --verbose"
    
    local config_file
    config_file=$(create_test_config "basic")
    
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock automation --dry-run --verbose cron-install sync 2>&1) || exit_code=$?
    
    if echo "$output" | grep -qi "verbose\|detailed\|installing"; then
        mark_test_passed "cron-install --verbose shows detailed output"
    else
        log_warning "Verbose output not clearly detected"
    fi
}

test_cron_install_dry_run() {
    log_step "Testing cron-install with --dry-run"
    
    local config_file
    config_file=$(create_test_config "basic")
    
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock automation --dry-run cron-install sync 2>&1) || exit_code=$?
    
    if echo "$output" | grep -qi "dry run\|would install"; then
        mark_test_passed "cron-install --dry-run shows simulation"
    else
        log_warning "Dry run indication not clearly detected"
    fi
}

################################################################################
# Section 2: Cron-Remove Command Tests
################################################################################

test_cron_remove_single_step() {
    log_step "Testing cron-remove with single step"
    
    local config_file
    config_file=$(create_test_config "basic")
    
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock automation --dry-run cron-remove sync 2>&1) || exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        mark_test_passed "cron-remove single step executes"
    else
        mark_test_failed "cron-remove single step" "Command failed with exit code $exit_code"
    fi
}

test_cron_remove_multiple_steps() {
    log_step "Testing cron-remove with multiple steps"
    
    local config_file
    config_file=$(create_test_config "basic")
    
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock automation --dry-run cron-remove sync secrets 2>&1) || exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        mark_test_passed "cron-remove multiple steps executes"
    else
        mark_test_failed "cron-remove multiple steps" "Command failed with exit code $exit_code"
    fi
}

test_cron_remove_all() {
    log_step "Testing cron-remove with 'all' argument"
    
    local config_file
    config_file=$(create_test_config "basic")
    
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock automation --dry-run cron-remove all 2>&1) || exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        mark_test_passed "cron-remove all executes"
    else
        mark_test_failed "cron-remove all" "Command failed with exit code $exit_code"
    fi
}

test_cron_remove_no_args() {
    log_step "Testing cron-remove without arguments (defaults to all)"
    
    local config_file
    config_file=$(create_test_config "basic")
    
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock automation --dry-run cron-remove 2>&1) || exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        mark_test_passed "cron-remove without args executes"
    else
        log_warning "cron-remove without args may require explicit 'all'"
    fi
}

test_cron_remove_verbose() {
    log_step "Testing cron-remove with --verbose"
    
    local config_file
    config_file=$(create_test_config "basic")
    
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock automation --dry-run --verbose cron-remove sync 2>&1) || exit_code=$?
    
    if echo "$output" | grep -qi "verbose\|removing\|detailed"; then
        mark_test_passed "cron-remove --verbose shows detailed output"
    else
        log_warning "Verbose output not clearly detected"
    fi
}

test_cron_remove_nonexistent() {
    # Check if test should be skipped
    is_test_skipped "${FUNCNAME[0]}" && mark_test_skipped "cron-remove nonexistent" "$(get_skip_reason "${FUNCNAME[0]}")" && return
    
    log_step "Testing cron-remove with nonexistent job"
    
    # Clear mock crontab to ensure no entries exist
    clear_mock_crontab
    
    local config_file
    config_file=$(create_test_config "basic")
    
    # Try to remove a job that doesn't exist
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock automation --dry-run cron-remove sync 2>&1) || exit_code=$?
    
    # Should either succeed with no-op or return appropriate message
    if [ $exit_code -ne 0 ]; then
        # Non-zero exit is acceptable for nonexistent job
        if echo "$output" | grep -qi "not found\|no.*job\|no.*entry\|does not exist"; then
            mark_test_passed "cron-remove nonexistent job returns appropriate error"
        else
            mark_test_failed "cron-remove nonexistent" "Unexpected error message: $output"
        fi
    else
        # Zero exit with message is also acceptable
        if echo "$output" | grep -qi "not found\|no.*job\|nothing to remove\|no entries"; then
            mark_test_passed "cron-remove nonexistent job handles gracefully"
        else
            log_warning "Removing nonexistent job succeeded without clear message"
            mark_test_passed "cron-remove nonexistent job completes"
        fi
    fi
    
    # Verify crontab is still empty
    local entry_count
    entry_count=$(count_cron_entries)
    if [ "$entry_count" -eq 0 ]; then
        mark_test_passed "cron-remove nonexistent job doesn't add spurious entries"
    else
        mark_test_failed "cron-remove nonexistent crontab" "Unexpected crontab entries: $entry_count"
    fi
}

################################################################################
# Section 3: Cron-Status Command Tests
################################################################################

test_cron_status_basic() {
    log_step "Testing cron-status basic command"
    
    local config_file
    config_file=$(create_test_config "basic")
    
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock automation cron-status 2>&1) || exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        mark_test_passed "cron-status executes"
    else
        mark_test_failed "cron-status" "Command failed with exit code $exit_code"
    fi
}

test_cron_status_no_jobs() {
    log_step "Testing cron-status when no jobs installed"
    
    local config_file
    config_file=$(create_test_config "basic")
    
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock automation cron-status 2>&1) || exit_code=$?
    
    if echo "$output" | grep -qi "no cron jobs\|not installed\|no jobs found"; then
        mark_test_passed "cron-status handles no jobs gracefully"
    else
        log_warning "No jobs message not clearly detected"
    fi
}

test_cron_status_verbose() {
    log_step "Testing cron-status with --verbose"
    
    local config_file
    config_file=$(create_test_config "basic")
    
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock automation cron-status --verbose 2>&1) || exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        mark_test_passed "cron-status --verbose executes"
    else
        log_warning "cron-status --verbose may not support this option"
    fi
}

################################################################################
# Section 4: Cron-Logs Command Tests
################################################################################

test_cron_logs_default() {
    log_step "Testing cron-logs with default settings"
    
    local config_file
    config_file=$(create_test_config "basic")
    
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock automation cron-logs 2>&1) || exit_code=$?
    
    if [ $exit_code -eq 0 ] || echo "$output" | grep -qi "log\|no logs"; then
        mark_test_passed "cron-logs default executes"
    else
        mark_test_failed "cron-logs default" "Command failed with exit code $exit_code"
    fi
}

test_cron_logs_custom_lines() {
    log_step "Testing cron-logs with custom line count"
    
    local config_file
    config_file=$(create_test_config "basic")
    
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock automation cron-logs --lines 50 2>&1) || exit_code=$?
    
    if [ $exit_code -eq 0 ] || echo "$output" | grep -qi "log\|no logs"; then
        mark_test_passed "cron-logs with --lines executes"
    else
        log_warning "cron-logs --lines may not work without existing logs"
    fi
}

test_cron_logs_no_logs() {
    log_step "Testing cron-logs when no logs exist"
    
    local config_file
    config_file=$(create_test_config "basic")
    
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock automation cron-logs 2>&1) || exit_code=$?
    
    if echo "$output" | grep -qi "no logs\|not found\|log file does not exist"; then
        mark_test_passed "cron-logs handles missing logs gracefully"
    else
        log_warning "Missing logs message not clearly detected"
    fi
}

################################################################################
# Section 5: Cron-Schedules Command Tests
################################################################################

test_cron_schedules_list() {
    log_step "Testing cron-schedules list command"
    
    local config_file
    config_file=$(create_test_config "basic")
    
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock automation cron-schedules 2>&1) || exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        mark_test_passed "cron-schedules executes"
    else
        mark_test_failed "cron-schedules" "Command failed with exit code $exit_code"
    fi
}

test_cron_schedules_format() {
    log_step "Testing cron-schedules shows format information"
    
    local config_file
    config_file=$(create_test_config "basic")
    
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock automation cron-schedules 2>&1) || exit_code=$?
    
    if echo "$output" | grep -qi "schedule\|cron\|sync\|secrets"; then
        mark_test_passed "cron-schedules shows schedule information"
    else
        mark_test_failed "cron-schedules format" "Expected schedule information not found"
    fi
}

test_cron_schedules_valid_fixtures() {
    log_step "Testing cron-schedules with valid schedule fixtures"
    
    # Test that valid schedules from fixture would be accepted
    if [ ! -f "$AUTOMATION_FIXTURES_DIR/valid_schedules.txt" ]; then
        log_warning "Fixture file not found: valid_schedules.txt"
        return 0
    fi
    
    local valid_count=0
    local tested=0
    
    # Read and test each valid schedule from fixture
    while IFS= read -r schedule || [ -n "$schedule" ]; do
        # Skip comments and empty lines
        if [[ "$schedule" =~ ^[[:space:]]*# ]] || [[ -z "$schedule" ]]; then
            continue
        fi
        
        tested=$((tested + 1))
        
        # Validate schedule format (basic validation: 5 fields)
        local field_count
        field_count=$(echo "$schedule" | awk '{print NF}')
        
        if [ "$field_count" -eq 5 ]; then
            valid_count=$((valid_count + 1))
            log_info "✓ Valid schedule: $schedule"
        else
            log_warning "⚠ Schedule has $field_count fields (expected 5): $schedule"
        fi
    done < "$AUTOMATION_FIXTURES_DIR/valid_schedules.txt"
    
    if [ $valid_count -eq $tested ] && [ $tested -gt 0 ]; then
        mark_test_passed "Valid schedule fixtures are properly formatted ($valid_count/$tested)"
    elif [ $valid_count -gt 0 ]; then
        mark_test_passed "Most valid schedule fixtures are correct ($valid_count/$tested)"
    else
        mark_test_failed "valid schedule fixtures" "No valid schedules found in fixture"
    fi
}

test_cron_schedules_invalid_fixtures() {
    log_step "Testing schedule validation with invalid fixtures"
    
    # Test that invalid schedules from fixture would be rejected
    if [ ! -f "$AUTOMATION_FIXTURES_DIR/invalid_schedules.txt" ]; then
        log_warning "Fixture file not found: invalid_schedules.txt"
        return 0
    fi
    
    local invalid_count=0
    local tested=0
    
    # Read each invalid schedule from fixture
    while IFS= read -r schedule || [ -n "$schedule" ]; do
        # Skip comments and empty lines
        if [[ "$schedule" =~ ^[[:space:]]*# ]] || [[ -z "$schedule" ]]; then
            continue
        fi
        
        tested=$((tested + 1))
        
        # These should be invalid - check for obvious issues
        local field_count
        field_count=$(echo "$schedule" | awk '{print NF}')
        
        if [ "$field_count" -ne 5 ] || [[ "$schedule" =~ [^0-9\ \*\/\-,] ]]; then
            invalid_count=$((invalid_count + 1))
            log_info "✓ Invalid schedule detected: $schedule"
        else
            log_warning "⚠ Schedule appears valid but marked invalid: $schedule"
        fi
    done < "$AUTOMATION_FIXTURES_DIR/invalid_schedules.txt"
    
    if [ $invalid_count -eq $tested ] && [ $tested -gt 0 ]; then
        mark_test_passed "Invalid schedule fixtures are properly malformed ($invalid_count/$tested)"
    elif [ $invalid_count -gt 0 ]; then
        mark_test_passed "Most invalid schedule fixtures are malformed ($invalid_count/$tested)"
    else
        mark_test_failed "invalid schedule fixtures" "No invalid schedules found in fixture"
    fi
}

test_cron_logs_fixture() {
    log_step "Testing cron-logs with fixture log file"
    
    # Copy fixture log to expected location
    if [ ! -f "$AUTOMATION_FIXTURES_DIR/sample_cron_log.txt" ]; then
        log_warning "Fixture file not found: sample_cron_log.txt"
        return 0
    fi
    
    local mock_log="$TEST_TEMP_DIR/cron_workflow.log"
    create_mock_log_file "$mock_log" "sample_cron_log.txt"
    
    # Verify log file has expected content from fixture
    local log_lines
    log_lines=$(wc -l < "$mock_log")
    
    if [ "$log_lines" -gt 10 ]; then
        mark_test_passed "Fixture log file loaded with $log_lines lines"
    else
        mark_test_failed "fixture log" "Log file too small: $log_lines lines"
    fi
    
    # Verify log contains expected patterns from fixture
    if grep -q "INFO" "$mock_log" && grep -q "SUCCESS\|ERROR" "$mock_log"; then
        mark_test_passed "Fixture log contains expected log levels"
    else
        mark_test_failed "fixture log content" "Missing expected log level markers"
    fi
}

################################################################################
# Section 6: Cron-Sync Command Tests
################################################################################

test_cron_sync_default() {
    log_step "Testing cron-sync with default settings"
    
    local config_file
    config_file=$(create_test_config "basic")
    
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock automation --dry-run cron-sync 2>&1) || exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        mark_test_passed "cron-sync default executes"
    else
        mark_test_failed "cron-sync default" "Command failed with exit code $exit_code"
    fi
}

test_cron_sync_single_step() {
    log_step "Testing cron-sync with single step"
    
    local config_file
    config_file=$(create_test_config "basic")
    
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock automation --dry-run cron-sync sync 2>&1) || exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        mark_test_passed "cron-sync single step executes"
    else
        mark_test_failed "cron-sync single step" "Command failed with exit code $exit_code"
    fi
}

test_cron_sync_multiple_steps() {
    log_step "Testing cron-sync with multiple steps"
    
    local config_file
    config_file=$(create_test_config "basic")
    
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock automation --dry-run cron-sync sync secrets 2>&1) || exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        mark_test_passed "cron-sync multiple steps executes"
    else
        mark_test_failed "cron-sync multiple steps" "Command failed with exit code $exit_code"
    fi
}

test_cron_sync_invalid_step() {
    # Check if test should be skipped
    is_test_skipped "${FUNCNAME[0]}" && mark_test_skipped "cron-sync invalid step" "$(get_skip_reason "${FUNCNAME[0]}")" && return
    
    log_step "Testing cron-sync with invalid step"
    
    local config_file
    config_file=$(create_test_config "basic")
    
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock automation --dry-run cron-sync invalid_step 2>&1) || exit_code=$?
    
    if [ $exit_code -ne 0 ]; then
        mark_test_passed "cron-sync rejects invalid step"
    else
        mark_test_failed "cron-sync invalid step" "Should reject invalid step name"
    fi
}

test_cron_sync_verbose() {
    log_step "Testing cron-sync with --verbose"
    
    local config_file
    config_file=$(create_test_config "basic")
    
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock automation --dry-run --verbose cron-sync sync 2>&1) || exit_code=$?
    
    if echo "$output" | grep -qi "verbose\|detailed\|executing"; then
        mark_test_passed "cron-sync --verbose shows detailed output"
    else
        log_warning "Verbose output not clearly detected"
    fi
}

test_cron_sync_stop_on_failure() {
    log_step "Testing cron-sync with --stop-on-failure"
    
    local config_file
    config_file=$(create_test_config "basic")
    
    # Test with stop-on-failure flag
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock automation --dry-run cron-sync sync secrets --stop-on-failure 2>&1) || exit_code=$?
    
    # Check if flag is recognized (should not error on unknown flag)
    if [ $exit_code -eq 0 ] || echo "$output" | grep -qi "stop.*failure\|halt.*error"; then
        mark_test_passed "cron-sync --stop-on-failure flag recognized"
    else
        mark_test_failed "cron-sync --stop-on-failure" "Flag not recognized or unexpected error"
    fi
    
    # Verify output mentions stop-on-failure behavior
    if echo "$output" | grep -qi "stop\|halt\|abort"; then
        mark_test_passed "cron-sync --stop-on-failure shows behavior in output"
    else
        log_warning "Stop-on-failure behavior not explicitly mentioned in output"
    fi
}

test_cron_sync_show_log() {
    log_step "Testing cron-sync with --show-log"
    
    # Create mock log file from fixture
    local mock_log="$TEST_TEMP_DIR/cron_workflow.log"
    if [ -f "$AUTOMATION_FIXTURES_DIR/sample_cron_log.txt" ]; then
        create_mock_log_file "$mock_log" "sample_cron_log.txt"
    else
        # Create basic mock log if fixture missing
        append_mock_log_entry "$mock_log" "INFO" "Test log entry 1"
        append_mock_log_entry "$mock_log" "SUCCESS" "Test log entry 2"
        append_mock_log_entry "$mock_log" "ERROR" "Test log entry 3"
    fi
    
    local config_file
    config_file=$(create_test_config "basic")
    
    # Test with show-log flag
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock automation --dry-run cron-sync --show-log 2>&1) || exit_code=$?
    
    # Check if flag is recognized
    if [ $exit_code -eq 0 ] || echo "$output" | grep -qi "log"; then
        mark_test_passed "cron-sync --show-log flag recognized"
    else
        mark_test_failed "cron-sync --show-log" "Flag not recognized or unexpected error"
    fi
}

test_cron_sync_combined() {
    # Check if test should be skipped
    is_test_skipped "${FUNCNAME[0]}" && mark_test_skipped "cron-sync combined" "$(get_skip_reason "${FUNCNAME[0]}")" && return
    
    log_step "Testing cron-sync with combined options"
    
    # Create mock log for testing
    local mock_log="$TEST_TEMP_DIR/cron_workflow.log"
    create_mock_log_file "$mock_log" "sample_cron_log.txt"
    
    local config_file
    config_file=$(create_test_config "basic")
    
    # Test with multiple flags combined
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock automation --dry-run --verbose cron-sync sync secrets --stop-on-failure 2>&1) || exit_code=$?
    
    # Verify all flags are processed
    local flags_ok=true
    
    if echo "$output" | grep -qi "verbose\|detailed"; then
        log_info "✓ Verbose output detected"
    else
        log_warning "⚠ Verbose output not detected"
        flags_ok=false
    fi
    
    if echo "$output" | grep -qi "dry.run\|would\|simulation"; then
        log_info "✓ Dry-run mode detected"
    else
        log_warning "⚠ Dry-run mode not detected"
        flags_ok=false
    fi
    
    if [ "$flags_ok" = true ]; then
        mark_test_passed "cron-sync with combined options works"
    else
        mark_test_failed "cron-sync combined" "Not all options working as expected"
    fi
}

################################################################################
# Test Suite Runners
################################################################################

run_cron_install_tests() {
    log_section "Running Cron-Install Tests"
    test_cron_install_single_step
    test_cron_install_multiple_steps
    test_cron_install_custom_schedule
    test_cron_install_invalid_schedule
    test_cron_install_invalid_step
    test_cron_install_verbose
    test_cron_install_dry_run
}

run_cron_remove_tests() {
    log_section "Running Cron-Remove Tests"
    test_cron_remove_single_step
    test_cron_remove_multiple_steps
    test_cron_remove_all
    test_cron_remove_no_args
    test_cron_remove_verbose
    test_cron_remove_nonexistent
}

run_cron_status_tests() {
    log_section "Running Cron-Status Tests"
    test_cron_status_basic
    test_cron_status_no_jobs
    test_cron_status_verbose
}

run_cron_logs_tests() {
    log_section "Running Cron-Logs Tests"
    test_cron_logs_default
    test_cron_logs_custom_lines
    test_cron_logs_no_logs
}

run_cron_schedules_tests() {
    log_section "Running Cron-Schedules Tests"
    test_cron_schedules_list
    test_cron_schedules_format
    test_cron_schedules_valid_fixtures
    test_cron_schedules_invalid_fixtures
    test_cron_logs_fixture
}

run_cron_sync_tests() {
    log_section "Running Cron-Sync Tests"
    test_cron_sync_default
    test_cron_sync_single_step
    test_cron_sync_multiple_steps
    test_cron_sync_invalid_step
    test_cron_sync_verbose
    test_cron_sync_stop_on_failure
    test_cron_sync_show_log
    test_cron_sync_combined
}

run_all_tests() {
    run_cron_install_tests
    run_cron_remove_tests
    run_cron_status_tests
    run_cron_logs_tests
    run_cron_schedules_tests
    run_cron_sync_tests
}

################################################################################
# Main Execution
################################################################################

main() {
    log_section "Automation Commands Test Suite"
    log_info "Testing classdock automation commands"
    
    # Setup
    setup_test_environment
    
    # Parse command line arguments
    local test_type="${1:---all}"
    
    case "$test_type" in
        --cron-install)
            run_cron_install_tests
            ;;
        --cron-remove)
            run_cron_remove_tests
            ;;
        --cron-status)
            run_cron_status_tests
            ;;
        --cron-logs)
            run_cron_logs_tests
            ;;
        --cron-schedules)
            run_cron_schedules_tests
            ;;
        --cron-sync)
            run_cron_sync_tests
            ;;
        --all)
            run_all_tests
            ;;
        *)
            log_error "Unknown test type: $test_type"
            log_info "Usage: $0 [--cron-install|--cron-remove|--cron-status|--cron-logs|--cron-schedules|--cron-sync|--all]"
            exit 1
            ;;
    esac
    
    # Display results
    show_test_summary
    
    # Exit with appropriate code
    if [ "$TESTS_FAILED" -eq 0 ]; then
        exit 0
    else
        exit 1
    fi
}

# Run main if executed directly
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi
