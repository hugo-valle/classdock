#!/usr/bin/env bash
#
# Secrets Management Testing Script for ClassDock
# Tests the secrets add command with various directory contexts and configurations
#

# Error handling - be gentle when called from comprehensive test framework
if [ "${COMPREHENSIVE_TESTING:-false}" = "true" ]; then
    set +e  # Don't exit on errors, let individual tests handle them
else
    set -e
    trap 'echo "Secrets test failed at line $LINENO with exit code $?" >&2' ERR
fi

# Source configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[SECRETS-TEST]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SECRETS-SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[SECRETS-ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[SECRETS-WARNING]${NC} $1"
}

# Test counters
SECRETS_TESTS_PASSED=0
SECRETS_TESTS_FAILED=0
SECRETS_FAILED_TESTS=()

# Function to run a test and track results
run_secrets_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_result="${3:-0}"  # Default to expecting success (0)
    
    log_info "Running test: $test_name"
    
    # Capture both stdout and stderr, and the exit code
    local output
    local exit_code
    output=$(eval "$test_command" 2>&1) || exit_code=$?
    exit_code=${exit_code:-0}
    
    if [ "$exit_code" -eq "$expected_result" ]; then
        log_success "$test_name: PASSED"
        ((SECRETS_TESTS_PASSED++))
        return 0
    else
        log_error "$test_name: FAILED (expected exit code $expected_result, got $exit_code)"
        log_error "Output: $output"
        SECRETS_FAILED_TESTS+=("$test_name")
        ((SECRETS_TESTS_FAILED++))
        return 1
    fi
}

# Function to test secrets command help
test_secrets_help() {
    log_info "Testing secrets command help and structure"
    
    run_secrets_test "secrets help" \
        "classdock secrets --help"
    
    run_secrets_test "secrets add help" \
        "classdock secrets add --help"
}

# Function to test secrets add with assignment root parameter
test_secrets_with_assignment_root() {
    log_info "Testing secrets add with --assignment-root parameter"
    
    local test_assignment="$TEST_PROJECT_REPOS_DIR/sample_projects/secrets_test_assignment"
    
    # Test with valid assignment root
    run_secrets_test "secrets add with valid assignment root (dry-run)" \
        "classdock secrets add --assignment-root '$test_assignment' --dry-run --verbose"
    
    # Test with invalid assignment root
    run_secrets_test "secrets add with invalid assignment root" \
        "classdock secrets add --assignment-root '/nonexistent/path' --dry-run" \
        1  # Expect failure
}

# Function to test secrets add from assignment directory
test_secrets_from_assignment_directory() {
    log_info "Testing secrets add from within assignment directory"
    
    local test_assignment="$TEST_PROJECT_REPOS_DIR/sample_projects/secrets_test_assignment"
    local original_dir=$(pwd)
    
    # Change to assignment directory and test (template repository)
    cd "$test_assignment"
    
    run_secrets_test "secrets add from template repository directory (dry-run)" \
        "classdock secrets add --dry-run --verbose"
    
    # Test from student repository (has assignment.conf and instructor_token.txt)
    cd "$original_dir"
    local temp_student_repo=$(mktemp -d)
    cp "$test_assignment/assignment.conf" "$temp_student_repo/"
    echo "test_token" > "$temp_student_repo/instructor_token.txt"
    
    cd "$temp_student_repo"
    run_secrets_test "secrets add from student repository directory (dry-run)" \
        "classdock secrets add --dry-run --verbose"
    
    # Return to original directory and cleanup
    cd "$original_dir"
    rm -rf "$temp_student_repo"
}

# Function to test configuration file handling
test_secrets_config_handling() {
    log_info "Testing secrets configuration file handling"
    
    local test_assignment="$TEST_PROJECT_REPOS_DIR/sample_projects/secrets_test_assignment"
    
    # Test with custom config file
    run_secrets_test "secrets add with custom config file" \
        "classdock secrets add --assignment-root '$test_assignment' --config assignment.conf --dry-run"
    
    # Test with missing config file
    run_secrets_test "secrets add with missing config file" \
        "classdock secrets add --assignment-root '$test_assignment' --config nonexistent.conf --dry-run" \
        1  # Expect failure
}

# Function to test directory context validation
test_directory_context_validation() {
    log_info "Testing directory context validation"
    
    # Test from main project directory without assignment root (should fail - no assignment files or token)
    run_secrets_test "secrets add from main project (no assignment root)" \
        "classdock secrets add --dry-run" \
        1  # Expect failure due to missing assignment files and instructor_token.txt
    
    # Test with missing assignment files and missing instructor_token.txt
    local temp_dir=$(mktemp -d)
    echo "GITHUB_ORGANIZATION=test" > "$temp_dir/assignment.conf"
    echo "ASSIGNMENT_FILE=missing.py" >> "$temp_dir/assignment.conf"
    
    run_secrets_test "secrets add with incomplete directory (no files or token)" \
        "classdock secrets add --assignment-root '$temp_dir' --dry-run" \
        1  # Expect failure due to missing assignment files and instructor_token.txt
    
    # Cleanup
    rm -rf "$temp_dir"
}

# Function to test error handling and edge cases
test_secrets_error_handling() {
    log_info "Testing secrets error handling and edge cases"
    
    local test_assignment="$TEST_PROJECT_REPOS_DIR/sample_projects/secrets_test_assignment"
    
    # Test verbose mode
    run_secrets_test "secrets add verbose mode" \
        "classdock secrets add --assignment-root '$test_assignment' --dry-run --verbose"
    
    # Test with absolute path
    local abs_path=$(realpath "$test_assignment")
    run_secrets_test "secrets add with absolute path" \
        "classdock secrets add --assignment-root '$abs_path' --dry-run"
}

# Function to validate test assignment structure
validate_test_assignment_structure() {
    log_info "Validating test assignment structure"
    
    local test_assignment="$TEST_PROJECT_REPOS_DIR/sample_projects/secrets_test_assignment"
    
    # Check required files exist
    local required_files=(
        "assignment.conf"
        "calculator.py"
        "assignment.ipynb"
        "solution.py"
        "instructor_token.txt"
    )
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$test_assignment/$file" ]; then
            log_error "Required test file missing: $file"
            return 1
        fi
    done
    
    # Check assignment.conf has required variables
    local required_vars=(
        "ASSIGNMENT_NAME"
        "GITHUB_ORGANIZATION"
        "TEMPLATE_REPO_URL"
        "ASSIGNMENT_FILE"
        "SECRET_NAME"
    )
    
    for var in "${required_vars[@]}"; do
        if ! grep -q "^$var=" "$test_assignment/assignment.conf"; then
            log_error "Required configuration variable missing: $var"
            return 1
        fi
    done
    
    log_success "Test assignment structure validation passed"
    return 0
}

# Main test execution function
run_secrets_tests() {
    log_info "Starting Secrets Management Tests"
    log_info "================================"
    
    # Validate test environment
    if ! validate_test_assignment_structure; then
        log_error "Test assignment structure validation failed - aborting secrets tests"
        return 1
    fi
    
    # Run test suites
    test_secrets_help
    test_secrets_with_assignment_root
    test_secrets_from_assignment_directory
    test_secrets_config_handling
    test_directory_context_validation
    test_secrets_error_handling
    
    # Report results
    log_info "Secrets Management Test Results"
    log_info "==============================="
    log_success "Tests passed: $SECRETS_TESTS_PASSED"
    
    if [ $SECRETS_TESTS_FAILED -gt 0 ]; then
        log_error "Tests failed: $SECRETS_TESTS_FAILED"
        log_error "Failed tests:"
        for failed_test in "${SECRETS_FAILED_TESTS[@]}"; do
            log_error "  - $failed_test"
        done
        return 1
    else
        log_success "All secrets management tests passed!"
        return 0
    fi
}

# Export variables for use by other scripts
export SECRETS_TESTS_PASSED
export SECRETS_TESTS_FAILED
export SECRETS_FAILED_TESTS

# Run tests if script is executed directly
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    run_secrets_tests
    exit $?
fi