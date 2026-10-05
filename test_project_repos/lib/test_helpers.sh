#!/bin/bash
################################################################################
# Shared Test Helper Library
#
# Provides common testing functions used across all test scripts including:
# - Logging functions with color-coded output
# - Test result tracking and reporting
# - Assertion functions for test validation
# - Test execution helpers
# - Performance timing helpers
# - Output capture utilities
#
# Usage: source lib/test_helpers.sh
#
# IMPORTANT: Test tracking counters (TESTS_PASSED, TESTS_FAILED, FAILED_TESTS)
# are only initialized if not already set, preserving existing values when
# sourced multiple times. To reset counters explicitly, call init_test_tracking().
################################################################################

# Color codes for output formatting
readonly COLOR_RESET='\033[0m'
readonly COLOR_RED='\033[0;31m'
readonly COLOR_GREEN='\033[0;32m'
readonly COLOR_YELLOW='\033[0;33m'
readonly COLOR_BLUE='\033[0;34m'
readonly COLOR_GRAY='\033[0;90m'

# Test tracking variables - only initialize if unset to preserve existing values
: "${TESTS_PASSED:=0}"
: "${TESTS_FAILED:=0}"
: "${TESTS_SKIPPED:=0}"
# Initialize FAILED_TESTS and SKIPPED_TESTS arrays only if not already declared
if ! declare -p FAILED_TESTS &>/dev/null; then
    FAILED_TESTS=()
fi
if ! declare -p SKIPPED_TESTS &>/dev/null; then
    SKIPPED_TESTS=()
fi

# Timer variables
TIMER_START=0
TIMER_STOP=0

################################################################################
# Logging Functions
################################################################################

# Log informational message in blue
# Usage: log_info "message"
log_info() {
    echo -e "${COLOR_BLUE}[INFO]${COLOR_RESET} $*"
}

# Log success message in green
# Usage: log_success "message"
log_success() {
    echo -e "${COLOR_GREEN}[SUCCESS]${COLOR_RESET} $*"
}

# Log error message in red
# Usage: log_error "message"
log_error() {
    echo -e "${COLOR_RED}[ERROR]${COLOR_RESET} $*" >&2
}

# Log warning message in yellow
# Usage: log_warning "message"
log_warning() {
    echo -e "${COLOR_YELLOW}[WARNING]${COLOR_RESET} $*"
}

# Log section header with decorative border
# Usage: log_step "Section Title"
log_step() {
    echo ""
    echo -e "${COLOR_BLUE}============================================================${COLOR_RESET}"
    echo -e "${COLOR_BLUE}  $*${COLOR_RESET}"
    echo -e "${COLOR_BLUE}============================================================${COLOR_RESET}"
    echo ""
}

# Alias for log_step - for backwards compatibility
# Usage: log_section "Section Title"
log_section() {
    log_step "$@"
}

# Log debug message in gray (only shown in verbose mode)
# Usage: log_debug "message"
log_debug() {
    if [ "${VERBOSE:-false}" = "true" ] || [ "${DEBUG:-false}" = "true" ]; then
        echo -e "${COLOR_GRAY}[DEBUG]${COLOR_RESET} $*"
    fi
}

################################################################################
# Test Result Tracking Functions
################################################################################

# Initialize test tracking counters to zero/empty
# Call this function explicitly at the start of test scripts that need a fresh slate.
# Note: Simply sourcing test_helpers.sh will NOT reset counters if already set.
# Usage: init_test_tracking
init_test_tracking() {
    TESTS_PASSED=0
    TESTS_FAILED=0
    TESTS_SKIPPED=0
    FAILED_TESTS=()
    SKIPPED_TESTS=()
    log_debug "Test tracking counters explicitly reset to zero"
}

# Mark a test as passed and log success
# Usage: mark_test_passed "test_name"
mark_test_passed() {
    local test_name="$1"
    # Use assignment form to avoid non-zero exit codes under 'set -e'
    TESTS_PASSED=$((TESTS_PASSED + 1))
    log_success "✓ Test passed: $test_name"
}

# Mark a test as failed, add to failed list, and log error
# Usage: mark_test_failed "test_name" "failure_reason"
mark_test_failed() {
    local test_name="$1"
    local reason="${2:-Unknown reason}"
    # Use assignment form to avoid non-zero exit codes under 'set -e'
    TESTS_FAILED=$((TESTS_FAILED + 1))
    FAILED_TESTS+=("$test_name: $reason")
    log_error "✗ Test failed: $test_name - $reason"
}

# Mark a test as skipped, add to skipped list, and log warning
# Usage: mark_test_skipped "test_name" "skip_reason"
mark_test_skipped() {
    local test_name="$1"
    local reason="${2:-Not implemented yet}"
    # Use assignment form to avoid non-zero exit codes under 'set -e'
    TESTS_SKIPPED=$((TESTS_SKIPPED + 1))
    SKIPPED_TESTS+=("$test_name: $reason")
    log_warning "⊘ Test skipped: $test_name - $reason"
}

# Get formatted test summary string
# Usage: summary=$(get_test_summary)
get_test_summary() {
    local total=$((TESTS_PASSED + TESTS_FAILED + TESTS_SKIPPED))
    local success_rate=0
    
    if [ "$total" -gt 0 ]; then
        success_rate=$(awk "BEGIN {printf \"%.1f\", ($TESTS_PASSED / $total) * 100}")
    fi
    
    echo "Total: $total | Passed: $TESTS_PASSED | Failed: $TESTS_FAILED | Skipped: $TESTS_SKIPPED | Success Rate: ${success_rate}%"
}

# Display formatted test results summary
# Usage: show_test_summary
show_test_summary() {
    echo ""
    log_step "Test Results Summary"
    
    local total=$((TESTS_PASSED + TESTS_FAILED + TESTS_SKIPPED))
    local success_rate=0
    
    if [ "$total" -gt 0 ]; then
        success_rate=$(awk "BEGIN {printf \"%.1f\", ($TESTS_PASSED / $total) * 100}")
    fi
    
    echo "Total Tests:    $total"
    echo -e "Tests Passed:   ${COLOR_GREEN}$TESTS_PASSED${COLOR_RESET}"
    echo -e "Tests Failed:   ${COLOR_RED}$TESTS_FAILED${COLOR_RESET}"
    echo -e "Tests Skipped:  ${COLOR_YELLOW}$TESTS_SKIPPED${COLOR_RESET}"
    echo "Success Rate:   ${success_rate}%"
    
    if [ "${#FAILED_TESTS[@]}" -gt 0 ]; then
        echo ""
        log_error "Failed Tests:"
        for failed_test in "${FAILED_TESTS[@]}"; do
            echo "  - $failed_test"
        done
    fi
    
    if [ "${#SKIPPED_TESTS[@]}" -gt 0 ]; then
        echo ""
        log_warning "Skipped Tests (TODO - implement features):"
        for skipped_test in "${SKIPPED_TESTS[@]}"; do
            echo "  - $skipped_test"
        done
    fi
    
    echo ""
}

################################################################################
# Assertion Functions
################################################################################

# Verify a command exists in PATH
# Usage: assert_command_exists "command_name"
# Returns: 0 if command exists, 1 otherwise
assert_command_exists() {
    local command="$1"
    if command -v "$command" >/dev/null 2>&1; then
        log_debug "Command exists: $command"
        return 0
    else
        log_error "Command not found: $command"
        return 1
    fi
}

# Verify a file exists at specified path
# Usage: assert_file_exists "file_path"
# Returns: 0 if file exists, 1 otherwise
assert_file_exists() {
    local file_path="$1"
    if [ -f "$file_path" ]; then
        log_debug "File exists: $file_path"
        return 0
    else
        log_error "File not found: $file_path"
        return 1
    fi
}

# Verify file contains expected string/pattern
# Usage: assert_file_contains "file_path" "expected_string"
# Returns: 0 if string found, 1 otherwise
assert_file_contains() {
    local file_path="$1"
    local expected="$2"
    
    if ! assert_file_exists "$file_path"; then
        return 1
    fi
    
    if grep -q "$expected" "$file_path"; then
        log_debug "File contains expected string: $expected"
        return 0
    else
        log_error "File does not contain expected string: $expected"
        return 1
    fi
}

# Verify command exit code matches expected value
# Usage: assert_exit_code "expected_code" "actual_code"
# Returns: 0 if codes match, 1 otherwise
assert_exit_code() {
    local expected="$1"
    local actual="$2"
    
    if [ "$actual" -eq "$expected" ]; then
        log_debug "Exit code matches expected: $expected"
        return 0
    else
        log_error "Exit code mismatch. Expected: $expected, Got: $actual"
        return 1
    fi
}

# Verify command output contains expected string
# Usage: assert_output_contains "output" "expected_string"
# Returns: 0 if string found, 1 otherwise
assert_output_contains() {
    local output="$1"
    local expected="$2"
    
    if echo "$output" | grep -q "$expected"; then
        log_debug "Output contains expected string: $expected"
        return 0
    else
        log_error "Output does not contain expected string: $expected"
        return 1
    fi
}

# Verify command output matches regex pattern
# Usage: assert_output_matches "output" "regex_pattern"
# Returns: 0 if pattern matches, 1 otherwise
assert_output_matches() {
    local output="$1"
    local pattern="$2"
    
    if echo "$output" | grep -E -q "$pattern"; then
        log_debug "Output matches pattern: $pattern"
        return 0
    else
        log_error "Output does not match pattern: $pattern"
        return 1
    fi
}

# Verify variable or file is not empty
# Usage: assert_not_empty "value" "description"
# Returns: 0 if not empty, 1 if empty
assert_not_empty() {
    local value="$1"
    local description="${2:-value}"
    
    if [ -n "$value" ]; then
        log_debug "$description is not empty"
        return 0
    else
        log_error "$description is empty"
        return 1
    fi
}

################################################################################
# Test Execution Helpers
################################################################################

# Detect available timeout command (handles macOS vs Linux differences)
# Returns the timeout command to use, or empty string if none available
get_timeout_command() {
    if command -v timeout >/dev/null 2>&1; then
        echo "timeout"
    elif command -v gtimeout >/dev/null 2>&1; then
        echo "gtimeout"
    else
        echo ""
    fi
}

# Execute a test case with timeout and result tracking
# Usage: run_test_case "test_name" "test_function" [timeout_seconds]
# Returns: 0 if test passes, 1 if test fails
run_test_case() {
    local test_name="$1"
    local test_function="$2"
    local timeout_duration="${3:-60}"
    
    log_info "Running test: $test_name"
    
    local timeout_cmd
    timeout_cmd=$(get_timeout_command)
    
    if [ -n "$timeout_cmd" ]; then
        # Timeout command available
        if $timeout_cmd "$timeout_duration" bash -c "$test_function"; then
            mark_test_passed "$test_name"
            return 0
        else
            local exit_code=$?
            if [ "$exit_code" -eq 124 ] || [ "$exit_code" -eq 143 ]; then
                mark_test_failed "$test_name" "Timeout after ${timeout_duration}s"
            else
                mark_test_failed "$test_name" "Exit code: $exit_code"
            fi
            return 1
        fi
    else
        # No timeout command available, run without timeout
        log_warning "Timeout command not available, running test without timeout"
        if bash -c "$test_function"; then
            mark_test_passed "$test_name"
            return 0
        else
            local exit_code=$?
            mark_test_failed "$test_name" "Exit code: $exit_code"
            return 1
        fi
    fi
}

# Execute a CLI command and validate exit code and output
# Usage: run_command_test "test_name" "command" "expected_exit_code" ["expected_output_pattern"]
# Returns: 0 if validation passes, 1 otherwise
run_command_test() {
    local test_name="$1"
    local command="$2"
    local expected_exit="$3"
    local expected_output="${4:-}"
    
    log_info "Running command test: $test_name"
    log_debug "Command: $command"
    
    local output
    output=$(eval "$command" 2>&1)
    local actual_exit=$?
    
    local test_passed=true
    
    if ! assert_exit_code "$expected_exit" "$actual_exit"; then
        test_passed=false
    fi
    
    if [ -n "$expected_output" ]; then
        if ! assert_output_contains "$output" "$expected_output"; then
            test_passed=false
        fi
    fi
    
    if [ "$test_passed" = true ]; then
        mark_test_passed "$test_name"
        return 0
    else
        mark_test_failed "$test_name" "Validation failed"
        return 1
    fi
}

# Create isolated temporary directory for test
# Usage: temp_dir=$(create_temp_test_dir "test_name")
# Returns: Path to temporary directory
create_temp_test_dir() {
    local test_name="${1:-test}"
    local temp_dir
    temp_dir=$(mktemp -d -t "qa_test_${test_name}_XXXXXX")
    log_debug "Created temp directory: $temp_dir"
    echo "$temp_dir"
}

# Remove temporary test directory
# Usage: cleanup_temp_test_dir "temp_dir_path"
cleanup_temp_test_dir() {
    local temp_dir="$1"
    if [ -d "$temp_dir" ]; then
        rm -rf "$temp_dir"
        log_debug "Cleaned up temp directory: $temp_dir"
    fi
}

# Create a test configuration file from template
# Usage: setup_test_config "template_file" "output_file" [variable_overrides]
# Returns: 0 if successful, 1 otherwise
setup_test_config() {
    local template="$1"
    local output="$2"
    shift 2
    
    if ! assert_file_exists "$template"; then
        return 1
    fi
    
    cp "$template" "$output"
    
    # Apply any variable overrides passed as KEY=VALUE arguments
    while [ $# -gt 0 ]; do
        local var_assignment="$1"
        shift
        
        # Parse KEY=VALUE
        if [[ "$var_assignment" =~ ^([A-Z_][A-Z0-9_]*)=(.*)$ ]]; then
            local key="${BASH_REMATCH[1]}"
            local value="${BASH_REMATCH[2]}"
            
            # Replace or append the key in config file
            if grep -q "^${key}=" "$output"; then
                # Key exists, replace it
                sed -i.bak "s|^${key}=.*|${key}=${value}|" "$output"
                rm -f "${output}.bak"
                log_debug "Config override: ${key}=${value} (replaced)"
            else
                # Key doesn't exist, append it
                echo "${key}=${value}" >> "$output"
                log_debug "Config override: ${key}=${value} (appended)"
            fi
        else
            log_warning "Invalid override format (expected KEY=VALUE): $var_assignment"
        fi
    done
    
    log_debug "Created test config: $output"
    return 0
}

################################################################################
# Timing and Performance Helpers
################################################################################

# Record start time for performance measurement
# Usage: start_timer
start_timer() {
    TIMER_START=$(date +%s)
    log_debug "Timer started at $TIMER_START"
}

# Calculate elapsed time since start_timer
# Usage: elapsed=$(stop_timer)
# Returns: Elapsed time in seconds
stop_timer() {
    TIMER_STOP=$(date +%s)
    local elapsed=$((TIMER_STOP - TIMER_START))
    log_debug "Timer stopped. Elapsed: ${elapsed}s"
    echo "$elapsed"
}

# Verify operation completed within time threshold
# Usage: assert_performance "operation_name" "max_seconds"
# Returns: 0 if within threshold, 1 otherwise
assert_performance() {
    local operation="$1"
    local max_seconds="$2"
    local elapsed
    elapsed=$(stop_timer)
    
    if [ "$elapsed" -le "$max_seconds" ]; then
        log_debug "$operation completed in ${elapsed}s (threshold: ${max_seconds}s)"
        return 0
    else
        log_error "$operation took ${elapsed}s (exceeded threshold: ${max_seconds}s)"
        return 1
    fi
}

################################################################################
# Output Capture Helpers
################################################################################

# Execute command and capture stdout only
# Usage: output=$(capture_stdout "command")
# Returns: Command's stdout
capture_stdout() {
    local command="$1"
    eval "$command" 2>/dev/null
}

# Execute command and capture stderr only
# Usage: errors=$(capture_stderr "command")
# Returns: Command's stderr
capture_stderr() {
    local command="$1"
    eval "$command" 2>&1 1>/dev/null
}

# Execute command and capture both stdout and stderr
# Usage: output=$(capture_both "command")
# Returns: Combined stdout and stderr
capture_both() {
    local command="$1"
    eval "$command" 2>&1
}

################################################################################
# Test Configuration Helper
################################################################################

# Create a minimal assignment.conf for testing
# Usage: create_minimal_test_config "/path/to/project_root"
# Creates assignment.conf in the specified directory if it doesn't exist
create_minimal_test_config() {
    local target_dir="${1:-.}"
    local config_file="$target_dir/assignment.conf"
    
    if [ -f "$config_file" ]; then
        log_debug "assignment.conf already exists at $config_file"
        return 0
    fi
    
    log_info "Creating minimal test assignment.conf at $config_file"
    
    cat > "$config_file" << 'EOF'
# Minimal Test Configuration
# Auto-generated for QA testing
TEMPLATE_REPO_URL=https://github.com/test-org/test-assignment-template
GITHUB_ORGANIZATION=test-org
ASSIGNMENT_NAME=test-assignment
ASSIGNMENT_FILE=assignment.ipynb
COLLABORATOR_USERS=ta1,ta2,instructor
EOF
    
    if [ -f "$config_file" ]; then
        log_debug "Successfully created test assignment.conf"
        return 0
    else
        log_error "Failed to create test assignment.conf"
        return 1
    fi
}

################################################################################
# Export all functions
################################################################################

export -f log_info log_success log_error log_warning log_step log_section log_debug
export -f init_test_tracking mark_test_passed mark_test_failed get_test_summary show_test_summary
export -f assert_command_exists assert_file_exists assert_file_contains assert_exit_code
export -f assert_output_contains assert_output_matches assert_not_empty
export -f create_minimal_test_config
export -f run_test_case run_command_test create_temp_test_dir cleanup_temp_test_dir setup_test_config
export -f start_timer stop_timer assert_performance
export -f capture_stdout capture_stderr capture_both

log_debug "Test helpers library loaded successfully"
