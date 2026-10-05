#!/usr/bin/env bash
# 
# Integration Testing Script for ClassDock
# Tests the complete workflow with sample projects
#

# Only exit on error if not in debug mode, and handle errors gracefully
# Also check if we're being called from comprehensive test framework
if [ "${DEBUG_INTEGRATION_TEST:-false}" != "true" ] && [ "${COMPREHENSIVE_TESTING:-false}" != "true" ]; then
    set -e
    # Set up error handling to show more details when tests fail
    trap 'echo "Integration test failed at line $LINENO with exit code $?" >&2' ERR
elif [ "${COMPREHENSIVE_TESTING:-false}" = "true" ]; then
    # When called from comprehensive test framework, use gentler error handling
    set +e  # Don't exit on errors, let individual tests handle them
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

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
FAILED_TESTS=()

# Test result tracking
mark_test_passed() {
    local test_name="$1"
    ((TESTS_PASSED++))
    log_success "$test_name"
}

mark_test_failed() {
    local test_name="$1"
    local error_msg="$2"
    ((TESTS_FAILED++))
    FAILED_TESTS+=("$test_name: $error_msg")
    log_error "$test_name: $error_msg"
}

# Test configuration file creation
test_config_file_creation() {
    log_info "Testing configuration file creation"
    
    local test_dir="$TEST_PROJECT_REPOS_DIR/sample_projects/config_test"
    mkdir -p "$test_dir"
    
    # Test basic config creation
    local config_file="$test_dir/assignment.conf"
    cat > "$config_file" << 'EOF'
ASSIGNMENT_NAME="test-assignment"
GITHUB_ORGANIZATION=test-course
TEMPLATE_REPO_URL=https://github.com/test-course/template-repo
ASSIGNMENT_FILE=main.py
STUDENT_REPO_PREFIX=assignment-1
COLLABORATOR_USERS=student1,student2,student3
SECRET_NAME=TEST_SECRET
SECRET_VALUE=test_value_123
EOF

    if [[ -f "$config_file" ]]; then
        mark_test_passed "Configuration file creation"
    else
        mark_test_failed "Configuration file creation" "File not created"
        return 1
    fi
    
    # Test config validation using our new validate-config command
    if command -v classdock &> /dev/null; then
        if classdock assignments validate-config --config-file "$config_file" &> /dev/null; then
            mark_test_passed "Configuration validation"
        else
            mark_test_failed "Configuration validation" "Config validation failed"
        fi
    else
        log_warning "CLI not available for config validation test"
    fi
    
    # Cleanup
    rm -rf "$test_dir"
}

# Test CLI command execution
test_cli_commands() {
    log_info "Testing CLI command execution"
    
    if ! command -v classdock &> /dev/null; then
        mark_test_failed "CLI availability" "classdock command not found"
        return 1
    fi
    
    # Test help command
    if classdock --help &> /dev/null; then
        mark_test_passed "CLI help command"
    else
        mark_test_failed "CLI help command" "Help command failed"
    fi
    
    # Test version command
    if classdock --version &> /dev/null; then
        mark_test_passed "CLI version command"
    else
        mark_test_failed "CLI version command" "Version command failed"
    fi
    
    # Test assignments help
    if classdock assignments --help &> /dev/null; then
        mark_test_passed "Assignments subcommand help"
    else
        mark_test_failed "Assignments subcommand help" "Assignments help failed"
    fi
    
    # Test repos help
    if classdock repos --help &> /dev/null; then
        mark_test_passed "Repos subcommand help"
    else
        mark_test_failed "Repos subcommand help" "Repos help failed"
    fi
    
    # Test secrets help
    if classdock secrets --help &> /dev/null; then
        mark_test_passed "Secrets subcommand help"
    else
        mark_test_failed "Secrets subcommand help" "Secrets help failed"
    fi
}

# Test Python API integration
test_python_api_integration() {
    log_info "Testing Python API integration"
    
    local test_script="$SCRIPT_DIR/test_python_api.py"
    if [[ -f "$test_script" ]]; then
        # Use python (which should use the activated environment) instead of python3
        if python "$test_script"; then
            mark_test_passed "Python API integration tests"
        else
            mark_test_failed "Python API integration tests" "Python API tests failed"
        fi
    else
        mark_test_failed "Python API test script" "Test script not found"
    fi
}

# Test workflow with sample projects
test_sample_project_workflow() {
    log_info "Testing sample project workflow"
    
    local sample_dir="$TEST_PROJECT_REPOS_DIR/sample_projects/basic_assignment"
    
    if [[ ! -d "$sample_dir" ]]; then
        log_warning "Basic assignment sample not found, creating minimal test"
        mkdir -p "$sample_dir"
        
        # Create minimal sample project
        cat > "$sample_dir/assignment.conf" << 'EOF'
ASSIGNMENT_NAME="test-assignment"
GITHUB_ORGANIZATION=test-course
TEMPLATE_REPO_URL=https://github.com/test-course/basic-template
ASSIGNMENT_FILE=assignment.conf
STUDENT_REPO_PREFIX=basic-assignment
EOF
        
        cat > "$sample_dir/README.md" << 'EOF'
# Basic Assignment Test

This is a test assignment for integration testing.

## Instructions
1. Clone this repository
2. Complete the assignment
3. Submit your work
EOF
        
        mkdir -p "$sample_dir/src"
        cat > "$sample_dir/src/main.py" << 'EOF'
#!/usr/bin/env python3
"""
Basic assignment starter code.
"""

def hello_world():
    """Return a greeting."""
    return "Hello, World!"

if __name__ == "__main__":
    print(hello_world())
EOF
    fi
    
    # Test project structure
    if [[ -f "$sample_dir/assignment.conf" ]]; then
        mark_test_passed "Sample project config exists"
    else
        mark_test_failed "Sample project config" "Config file missing"
    fi
    
    if [[ -f "$sample_dir/README.md" ]]; then
        mark_test_passed "Sample project README exists"
    else
        mark_test_failed "Sample project README" "README file missing"
    fi
    
    # Test CLI operations on sample project
    if command -v classdock &> /dev/null; then
        local config_file="$sample_dir/assignment.conf"
        
        # Test dry-run operations with orchestrate command
        if classdock assignments orchestrate --config "$config_file" --dry-run &> /dev/null; then
            mark_test_passed "Assignment orchestrate dry-run"
        else
            mark_test_failed "Assignment orchestrate dry-run" "Dry-run failed"
        fi
    else
        log_warning "CLI not available for sample project workflow test"
    fi
}

# Test error scenarios
test_error_scenarios() {
    log_info "Testing error scenario handling"
    
    local error_dir="$TEST_PROJECT_REPOS_DIR/sample_projects/error_scenarios"
    mkdir -p "$error_dir"
    
    # Test invalid config file
    local invalid_config="$error_dir/invalid.conf"
    cat > "$invalid_config" << 'EOF'
INVALID_KEY=invalid_value
MISSING_REQUIRED_FIELDS=true
EOF
    
    if command -v classdock &> /dev/null; then
        # This should fail gracefully with our new validate-config command
        if ! classdock assignments validate-config --config-file "$invalid_config" &> /dev/null; then
            mark_test_passed "Invalid config error handling"
        else
            mark_test_failed "Invalid config error handling" "Should have failed validation"
        fi
    else
        log_warning "CLI not available for error scenario testing"
    fi
    
    # Test missing config file
    local missing_config="$error_dir/nonexistent.conf"
    if command -v classdock &> /dev/null; then
        if ! classdock assignments validate-config --config-file "$missing_config" &> /dev/null; then
            mark_test_passed "Missing config error handling"
        else
            mark_test_failed "Missing config error handling" "Should have failed with missing file"
        fi
    fi
    
    # Cleanup
    rm -rf "$error_dir"
}

# Test performance with multiple operations
test_performance() {
    log_info "Testing performance with multiple operations"
    
    if ! command -v classdock &> /dev/null; then
        log_warning "CLI not available for performance testing"
        return
    fi
    
    local start_time=$(date +%s)
    
    # Run multiple help commands (should be fast)
    for i in {1..5}; do
        classdock --help &> /dev/null
        classdock assignments --help &> /dev/null
        classdock repos --help &> /dev/null
        classdock secrets --help &> /dev/null
    done
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    log_info "Performance test duration: ${duration}s"
    
    if [[ $duration -lt 10 ]]; then
        mark_test_passed "Performance test - multiple commands"
    else
        mark_test_failed "Performance test" "Commands took too long: ${duration}s"
    fi
}

# Test environment isolation
test_environment_isolation() {
    log_info "Testing environment isolation"
    
    # Test that the package works in isolated environment
    local isolated_test_script=$(mktemp)
    cat > "$isolated_test_script" << 'EOF'
#!/usr/bin/env python
import sys
import os

# Remove current directory from path to test installed package
if '' in sys.path:
    sys.path.remove('')
if '.' in sys.path:
    sys.path.remove('.')

try:
    import classdock
    print("SUCCESS: Package import in isolated environment")
    exit(0)
except ImportError as e:
    print(f"FAILED: Package import failed: {e}")
    exit(1)
EOF
    
    chmod +x "$isolated_test_script"
    
    if python "$isolated_test_script"; then
        mark_test_passed "Environment isolation test"
    else
        mark_test_failed "Environment isolation test" "Package not properly isolated"
    fi
    
    rm -f "$isolated_test_script"
}

# Test logging and output
test_logging_output() {
    log_info "Testing logging and output functionality"
    
    if ! command -v classdock &> /dev/null; then
        log_warning "CLI not available for logging tests"
        return
    fi
    
    local log_file=$(mktemp)
    
    # Test verbose flag acceptance (using validate-config which supports verbose)
    if classdock assignments validate-config --verbose --config-file /dev/null > "$log_file" 2>&1; then
        # Command succeeded, verbose flag is accepted
        mark_test_passed "Verbose logging output"
    elif grep -q "📋\|📊\|Loaded configuration from\|Configuration contains" "$log_file"; then
        # Command failed but verbose output was present (expected for /dev/null config)
        mark_test_passed "Verbose logging output"  
    else
        mark_test_failed "Verbose logging output" "Command failed"
    fi
    
    rm -f "$log_file"
}

# Show test summary
show_test_summary() {
    local total_tests=$((TESTS_PASSED + TESTS_FAILED))
    local success_rate=0
    
    if [[ $total_tests -gt 0 ]]; then
        success_rate=$(( (TESTS_PASSED * 100) / total_tests ))
    fi
    
    echo
    echo "=================================================="
    echo "Integration Test Results Summary"
    echo "=================================================="
    echo "Total Tests: $total_tests"
    echo "Passed: $TESTS_PASSED"
    echo "Failed: $TESTS_FAILED"
    echo "Success Rate: ${success_rate}%"
    
    if [[ ${#FAILED_TESTS[@]} -gt 0 ]]; then
        echo
        echo "Failed Tests:"
        for failed_test in "${FAILED_TESTS[@]}"; do
            echo "  - $failed_test"
        done
    fi
    
    echo "=================================================="
}

# Main test execution
main() {
    log_info "Starting Integration Tests for ClassDock"
    log_info "Test directory: $TEST_PROJECT_REPOS_DIR"
    
    # Ensure test environment is set up
    if [[ ! -d "$TEST_PROJECT_REPOS_DIR" ]]; then
        log_error "Test directory not found: $TEST_PROJECT_REPOS_DIR"
        exit 1
    fi
    
    # Run all integration tests
    test_config_file_creation
    test_cli_commands
    test_python_api_integration
    test_sample_project_workflow
    test_error_scenarios
    test_performance
    test_environment_isolation
    test_logging_output
    
    # Show results
    show_test_summary
    
    # Return appropriate exit code
    if [[ $TESTS_FAILED -eq 0 ]]; then
        log_success "All integration tests passed!"
        exit 0
    else
        log_error "Some integration tests failed!"
        exit 1
    fi
}

# Script execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi