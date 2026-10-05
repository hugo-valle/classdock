#!/usr/bin/env bash
#
# Test Runner - Execute specific test suites
# Provides granular control over test execution
#

set -e

# Source configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"

# Reports directory
REPORTS_DIR="$TEST_PROJECT_REPOS_DIR/reports"
mkdir -p "$REPORTS_DIR"

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

# Show usage information
show_usage() {
    cat << EOF
Usage: $0 [TEST_SUITE] [OPTIONS]

Run specific test suites for classdock package.

Test Suites:
    installation       Test package installation
    cli               Test CLI interface
    python-api        Test Python API
    integration       Test integration scenarios
    real-repo         Test with real GitHub repository
    qa-token          Test token management functionality
    qa-assignments    Test assignments commands
    qa-repos          Test repos commands
    qa-secrets        Test secrets commands
    qa-automation     Test automation commands
    qa-global-options Test global CLI options
    qa-error-scenarios Test error handling
    qa-all            Run all QA test suites
    all               Run all test suites (default)

Options:
    --setup           Set up test environment before running
    --cleanup         Clean up after running tests
    --verbose         Enable verbose output
    --report          Generate detailed report
    --junit           Generate JUnit XML report
    --coverage        Generate coverage report
    -h, --help        Show this help message

Examples:
    $0                              # Run all tests
    $0 installation                 # Run only installation tests
    $0 cli --verbose               # Run CLI tests with verbose output
    $0 integration --setup         # Set up environment and run integration tests
    $0 real-repo                    # Run real repository tests
    $0 qa-all --report             # Run all QA tests with report
    $0 qa-assignments --verbose    # Run assignments QA tests
    $0 all --cleanup --report      # Run all tests, clean up, and generate report
EOF
}

# Parse command line arguments
TEST_SUITE="all"
SETUP_ENV=false
CLEANUP_AFTER=false
VERBOSE=false
GENERATE_REPORT=false
JUNIT_REPORT=false
COVERAGE_REPORT=false

# Parse test suite (first argument without --)
if [[ $# -gt 0 && ! "$1" =~ ^-- ]]; then
    TEST_SUITE="$1"
    shift
fi

# Parse options
while [[ $# -gt 0 ]]; do
    case $1 in
        --setup)
            SETUP_ENV=true
            shift
            ;;
        --cleanup)
            CLEANUP_AFTER=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --report)
            GENERATE_REPORT=true
            shift
            ;;
        --junit)
            JUNIT_REPORT=true
            shift
            ;;
        --coverage)
            COVERAGE_REPORT=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Test result tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
FAILED_SUITES=()

# Track test suite results
track_test_result() {
    local suite_name="$1"
    local exit_code="$2"
    
    ((TOTAL_TESTS++))
    
    if [[ $exit_code -eq 0 ]]; then
        ((PASSED_TESTS++))
        log_success "Test suite '$suite_name' passed"
    else
        ((FAILED_TESTS++))
        FAILED_SUITES+=("$suite_name")
        log_error "Test suite '$suite_name' failed (exit code: $exit_code)"
    fi
}

# Set up test environment
setup_test_environment() {
    log_info "Setting up test environment..."
    
    if [[ -f "$SCRIPT_DIR/setup_test_env.sh" ]]; then
        if "$SCRIPT_DIR/setup_test_env.sh"; then
            log_success "Test environment setup completed"
        else
            log_error "Test environment setup failed"
            exit 1
        fi
    else
        log_error "Setup script not found: $SCRIPT_DIR/setup_test_env.sh"
        exit 1
    fi
}

# Run installation tests
run_installation_tests() {
    log_info "Running installation tests..."
    
    local test_script="$SCRIPT_DIR/test_installation.sh"
    if [[ -f "$test_script" ]]; then
        local args=()
        [[ "$VERBOSE" == "true" ]] && args+=(--verbose)
        
        if "$test_script" "${args[@]}"; then
            track_test_result "installation" 0
        else
            track_test_result "installation" 1
        fi
    else
        log_error "Installation test script not found: $test_script"
        track_test_result "installation" 1
    fi
}

# Run CLI tests
run_cli_tests() {
    log_info "Running CLI tests..."
    
    local test_script="$SCRIPT_DIR/test_cli_interface.sh"
    if [[ -f "$test_script" ]]; then
        local args=()
        [[ "$VERBOSE" == "true" ]] && args+=(--verbose)
        
        if "$test_script" "${args[@]}"; then
            track_test_result "cli" 0
        else
            track_test_result "cli" 1
        fi
    else
        log_error "CLI test script not found: $test_script"
        track_test_result "cli" 1
    fi
}

# Run Python API tests
run_python_api_tests() {
    log_info "Running Python API tests..."
    
    local test_script="$SCRIPT_DIR/test_python_api.py"
    if [[ -f "$test_script" ]]; then
        if python3 "$test_script"; then
            track_test_result "python-api" 0
        else
            track_test_result "python-api" 1
        fi
    else
        log_error "Python API test script not found: $test_script"
        track_test_result "python-api" 1
    fi
}

# Run real repository tests
run_real_repo_tests() {
    log_info "Running real repository tests..."
    
    local test_script="$SCRIPT_DIR/test_real_repo.sh"
    if [[ -f "$test_script" ]]; then
        local args=()
        [[ "$VERBOSE" == "true" ]] && args+=(--verbose)
        
        if "$test_script" "${args[@]}"; then
            track_test_result "real-repo" 0
        else
            track_test_result "real-repo" 1
        fi
    else
        log_error "Real repository test script not found: $test_script"
        track_test_result "real-repo" 1
    fi
}

# Run integration tests
run_integration_tests() {
    log_info "Running integration tests..."
    
    local test_script="$SCRIPT_DIR/test_integration.sh"
    if [[ -f "$test_script" ]]; then
        if "$test_script"; then
            track_test_result "integration" 0
        else
            track_test_result "integration" 1
        fi
    else
        log_error "Integration test script not found: $test_script"
        track_test_result "integration" 1
    fi
}

# Run QA token tests
run_qa_token_tests() {
    log_info "Running QA token tests..."
    
    local qa_runner="$SCRIPT_DIR/../qa_tests/run_qa_tests.sh"
    if [[ -f "$qa_runner" ]]; then
        local args=()
        [[ "$VERBOSE" == "true" ]] && args+=(--verbose)
        
        if "$qa_runner" --token "${args[@]}"; then
            track_test_result "qa-token" 0
        else
            track_test_result "qa-token" 1
        fi
    else
        log_error "QA test runner not found: $qa_runner"
        track_test_result "qa-token" 1
    fi
}

# Run QA assignments tests
run_qa_assignments_tests() {
    log_info "Running QA assignments tests..."
    
    local qa_runner="$SCRIPT_DIR/../qa_tests/run_qa_tests.sh"
    if [[ -f "$qa_runner" ]]; then
        local args=()
        [[ "$VERBOSE" == "true" ]] && args+=(--verbose)
        
        if "$qa_runner" --assignments "${args[@]}"; then
            track_test_result "qa-assignments" 0
        else
            track_test_result "qa-assignments" 1
        fi
    else
        log_error "QA test runner not found: $qa_runner"
        track_test_result "qa-assignments" 1
    fi
}

# Run QA repos tests
run_qa_repos_tests() {
    log_info "Running QA repos tests..."
    
    local qa_runner="$SCRIPT_DIR/../qa_tests/run_qa_tests.sh"
    if [[ -f "$qa_runner" ]]; then
        local args=()
        [[ "$VERBOSE" == "true" ]] && args+=(--verbose)
        
        if "$qa_runner" --repos "${args[@]}"; then
            track_test_result "qa-repos" 0
        else
            track_test_result "qa-repos" 1
        fi
    else
        log_error "QA test runner not found: $qa_runner"
        track_test_result "qa-repos" 1
    fi
}

# Run QA secrets tests
run_qa_secrets_tests() {
    log_info "Running QA secrets tests..."
    
    local qa_runner="$SCRIPT_DIR/../qa_tests/run_qa_tests.sh"
    if [[ -f "$qa_runner" ]]; then
        local args=()
        [[ "$VERBOSE" == "true" ]] && args+=(--verbose)
        
        if "$qa_runner" --secrets "${args[@]}"; then
            track_test_result "qa-secrets" 0
        else
            track_test_result "qa-secrets" 1
        fi
    else
        log_error "QA test runner not found: $qa_runner"
        track_test_result "qa-secrets" 1
    fi
}

# Run QA automation tests
run_qa_automation_tests() {
    log_info "Running QA automation tests..."
    
    local qa_runner="$SCRIPT_DIR/../qa_tests/run_qa_tests.sh"
    if [[ -f "$qa_runner" ]]; then
        local args=()
        [[ "$VERBOSE" == "true" ]] && args+=(--verbose)
        
        if "$qa_runner" --automation "${args[@]}"; then
            track_test_result "qa-automation" 0
        else
            track_test_result "qa-automation" 1
        fi
    else
        log_error "QA test runner not found: $qa_runner"
        track_test_result "qa-automation" 1
    fi
}

# Run QA global options tests
run_qa_global_options_tests() {
    log_info "Running QA global options tests..."
    
    local qa_runner="$SCRIPT_DIR/../qa_tests/run_qa_tests.sh"
    if [[ -f "$qa_runner" ]]; then
        local args=()
        [[ "$VERBOSE" == "true" ]] && args+=(--verbose)
        
        if "$qa_runner" --global-options "${args[@]}"; then
            track_test_result "qa-global-options" 0
        else
            track_test_result "qa-global-options" 1
        fi
    else
        log_error "QA test runner not found: $qa_runner"
        track_test_result "qa-global-options" 1
    fi
}

# Run QA error scenarios tests
run_qa_error_scenarios_tests() {
    log_info "Running QA error scenarios tests..."
    
    local qa_runner="$SCRIPT_DIR/../qa_tests/run_qa_tests.sh"
    if [[ -f "$qa_runner" ]]; then
        local args=()
        [[ "$VERBOSE" == "true" ]] && args+=(--verbose)
        
        if "$qa_runner" --error-scenarios "${args[@]}"; then
            track_test_result "qa-error-scenarios" 0
        else
            track_test_result "qa-error-scenarios" 1
        fi
    else
        log_error "QA test runner not found: $qa_runner"
        track_test_result "qa-error-scenarios" 1
    fi
}

# Run all QA tests
run_qa_all_tests() {
    log_info "Running all QA tests..."
    
    local qa_runner="$SCRIPT_DIR/../qa_tests/run_qa_tests.sh"
    if [[ -f "$qa_runner" ]]; then
        local args=()
        [[ "$VERBOSE" == "true" ]] && args+=(--verbose)
        
        if "$qa_runner" --all "${args[@]}"; then
            track_test_result "qa-all" 0
        else
            track_test_result "qa-all" 1
        fi
    else
        log_error "QA test runner not found: $qa_runner"
        track_test_result "qa-all" 1
    fi
}

# Generate test report
generate_test_report() {
    log_info "Generating test report..."
    
    local report_file="$REPORTS_DIR/test_runner_report_$(date +%Y%m%d_%H%M%S).html"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    mkdir -p "$REPORTS_DIR"
    
    cat > "$report_file" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>ClassDock Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { background-color: #f4f4f4; padding: 20px; border-radius: 5px; }
        .summary { margin: 20px 0; padding: 15px; border-left: 4px solid #007cba; }
        .passed { color: #28a745; }
        .failed { color: #dc3545; }
        .warning { color: #ffc107; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f2f2f2; }
        .status-passed { background-color: #d4edda; }
        .status-failed { background-color: #f8d7da; }
    </style>
</head>
<body>
    <div class="header">
        <h1>ClassDock Test Report</h1>
        <p><strong>Generated:</strong> $timestamp</p>
        <p><strong>Test Suite:</strong> $TEST_SUITE</p>
    </div>
    
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Total Test Suites:</strong> $TOTAL_TESTS</p>
        <p><strong>Passed:</strong> <span class="passed">$PASSED_TESTS</span></p>
        <p><strong>Failed:</strong> <span class="failed">$FAILED_TESTS</span></p>
        <p><strong>Success Rate:</strong> $(( TOTAL_TESTS > 0 ? (PASSED_TESTS * 100) / TOTAL_TESTS : 0 ))%</p>
    </div>
    
    <table>
        <thead>
            <tr>
                <th>Test Suite</th>
                <th>Status</th>
                <th>Notes</th>
            </tr>
        </thead>
        <tbody>
EOF

    # Add test results to report
    case "$TEST_SUITE" in
        "installation"|"all")
            if [[ " ${FAILED_SUITES[@]} " =~ " installation " ]]; then
                echo "            <tr class=\"status-failed\"><td>Installation</td><td>FAILED</td><td>Package installation tests failed</td></tr>" >> "$report_file"
            else
                echo "            <tr class=\"status-passed\"><td>Installation</td><td>PASSED</td><td>Package installation successful</td></tr>" >> "$report_file"
            fi
            ;;
    esac
    
    case "$TEST_SUITE" in
        "cli"|"all")
            if [[ " ${FAILED_SUITES[@]} " =~ " cli " ]]; then
                echo "            <tr class=\"status-failed\"><td>CLI Interface</td><td>FAILED</td><td>CLI tests failed</td></tr>" >> "$report_file"
            else
                echo "            <tr class=\"status-passed\"><td>CLI Interface</td><td>PASSED</td><td>CLI interface working correctly</td></tr>" >> "$report_file"
            fi
            ;;
    esac
    
    case "$TEST_SUITE" in
        "python-api"|"all")
            if [[ " ${FAILED_SUITES[@]} " =~ " python-api " ]]; then
                echo "            <tr class=\"status-failed\"><td>Python API</td><td>FAILED</td><td>Python API tests failed</td></tr>" >> "$report_file"
            else
                echo "            <tr class=\"status-passed\"><td>Python API</td><td>PASSED</td><td>Python API functioning correctly</td></tr>" >> "$report_file"
            fi
            ;;
    esac
    
    case "$TEST_SUITE" in
        "integration"|"all")
            if [[ " ${FAILED_SUITES[@]} " =~ " integration " ]]; then
                echo "            <tr class=\"status-failed\"><td>Integration</td><td>FAILED</td><td>Integration tests failed</td></tr>" >> "$report_file"
            else
                echo "            <tr class=\"status-passed\"><td>Integration</td><td>PASSED</td><td>Integration tests successful</td></tr>" >> "$report_file"
            fi
            ;;
    esac
    
    case "$TEST_SUITE" in
        "qa-token"|"qa-all"|"all")
            if [[ " ${FAILED_SUITES[@]} " =~ " qa-token " ]]; then
                echo "            <tr class=\"status-failed\"><td>QA Token</td><td>FAILED</td><td>Token management tests failed</td></tr>" >> "$report_file"
            else
                echo "            <tr class=\"status-passed\"><td>QA Token</td><td>PASSED</td><td>Token management tests successful</td></tr>" >> "$report_file"
            fi
            ;;
    esac
    
    case "$TEST_SUITE" in
        "qa-assignments"|"qa-all"|"all")
            if [[ " ${FAILED_SUITES[@]} " =~ " qa-assignments " ]]; then
                echo "            <tr class=\"status-failed\"><td>QA Assignments</td><td>FAILED</td><td>Assignments tests failed</td></tr>" >> "$report_file"
            else
                echo "            <tr class=\"status-passed\"><td>QA Assignments</td><td>PASSED</td><td>Assignments tests successful</td></tr>" >> "$report_file"
            fi
            ;;
    esac
    
    case "$TEST_SUITE" in
        "qa-repos"|"qa-all"|"all")
            if [[ " ${FAILED_SUITES[@]} " =~ " qa-repos " ]]; then
                echo "            <tr class=\"status-failed\"><td>QA Repos</td><td>FAILED</td><td>Repos tests failed</td></tr>" >> "$report_file"
            else
                echo "            <tr class=\"status-passed\"><td>QA Repos</td><td>PASSED</td><td>Repos tests successful</td></tr>" >> "$report_file"
            fi
            ;;
    esac
    
    case "$TEST_SUITE" in
        "qa-secrets"|"qa-all"|"all")
            if [[ " ${FAILED_SUITES[@]} " =~ " qa-secrets " ]]; then
                echo "            <tr class=\"status-failed\"><td>QA Secrets</td><td>FAILED</td><td>Secrets tests failed</td></tr>" >> "$report_file"
            else
                echo "            <tr class=\"status-passed\"><td>QA Secrets</td><td>PASSED</td><td>Secrets tests successful</td></tr>" >> "$report_file"
            fi
            ;;
    esac
    
    case "$TEST_SUITE" in
        "qa-automation"|"qa-all"|"all")
            if [[ " ${FAILED_SUITES[@]} " =~ " qa-automation " ]]; then
                echo "            <tr class=\"status-failed\"><td>QA Automation</td><td>FAILED</td><td>Automation tests failed</td></tr>" >> "$report_file"
            else
                echo "            <tr class=\"status-passed\"><td>QA Automation</td><td>PASSED</td><td>Automation tests successful</td></tr>" >> "$report_file"
            fi
            ;;
    esac
    
    case "$TEST_SUITE" in
        "qa-global-options"|"qa-all"|"all")
            if [[ " ${FAILED_SUITES[@]} " =~ " qa-global-options " ]]; then
                echo "            <tr class=\"status-failed\"><td>QA Global Options</td><td>FAILED</td><td>Global options tests failed</td></tr>" >> "$report_file"
            else
                echo "            <tr class=\"status-passed\"><td>QA Global Options</td><td>PASSED</td><td>Global options tests successful</td></tr>" >> "$report_file"
            fi
            ;;
    esac
    
    case "$TEST_SUITE" in
        "qa-error-scenarios"|"qa-all"|"all")
            if [[ " ${FAILED_SUITES[@]} " =~ " qa-error-scenarios " ]]; then
                echo "            <tr class=\"status-failed\"><td>QA Error Scenarios</td><td>FAILED</td><td>Error handling tests failed</td></tr>" >> "$report_file"
            else
                echo "            <tr class=\"status-passed\"><td>QA Error Scenarios</td><td>PASSED</td><td>Error handling tests successful</td></tr>" >> "$report_file"
            fi
            ;;
    esac
    
    cat >> "$report_file" << EOF
        </tbody>
    </table>
    
    <div class="summary">
        <h2>Environment Information</h2>
        <p><strong>Python Version:</strong> $(python3 --version 2>/dev/null || echo "Unknown")</p>
        <p><strong>Platform:</strong> $(uname -s) $(uname -r)</p>
        <p><strong>Test Directory:</strong> $TEST_PROJECT_REPOS_DIR</p>
    </div>
</body>
</html>
EOF

    log_success "Test report generated: $report_file"
}

# Cleanup test environment
cleanup_test_environment() {
    log_info "Cleaning up test environment..."
    
    if [[ -f "$SCRIPT_DIR/cleanup.sh" ]]; then
        if "$SCRIPT_DIR/cleanup.sh" --temp --logs; then
            log_success "Test environment cleanup completed"
        else
            log_warning "Test environment cleanup had some issues"
        fi
    else
        log_warning "Cleanup script not found: $SCRIPT_DIR/cleanup.sh"
    fi
}

# Show test summary
show_test_summary() {
    local success_rate=0
    if [[ $TOTAL_TESTS -gt 0 ]]; then
        success_rate=$(( (PASSED_TESTS * 100) / TOTAL_TESTS ))
    fi
    
    echo
    echo "=================================================="
    echo "Test Runner Summary"
    echo "=================================================="
    echo "Test Suite: $TEST_SUITE"
    echo "Total Test Suites: $TOTAL_TESTS"
    echo "Passed: $PASSED_TESTS"
    echo "Failed: $FAILED_TESTS"
    echo "Success Rate: ${success_rate}%"
    
    if [[ ${#FAILED_SUITES[@]} -gt 0 ]]; then
        echo
        echo "Failed Test Suites:"
        for suite in "${FAILED_SUITES[@]}"; do
            echo "  - $suite"
        done
    fi
    
    echo "=================================================="
}

# Main test execution
main() {
    log_info "Starting test runner for classdock"
    log_info "Test suite: $TEST_SUITE"
    log_info "Options: setup=$SETUP_ENV, cleanup=$CLEANUP_AFTER, verbose=$VERBOSE"
    
    # Set up environment if requested
    if [[ "$SETUP_ENV" == "true" ]]; then
        setup_test_environment
    fi
    
    # Run specified test suites
    case "$TEST_SUITE" in
        "installation")
            run_installation_tests
            ;;
        "cli")
            run_cli_tests
            ;;
        "python-api")
            run_python_api_tests
            ;;
        "integration")
            run_integration_tests
            ;;
        "real-repo")
            run_real_repo_tests
            ;;
        "qa-token")
            run_qa_token_tests
            ;;
        "qa-assignments")
            run_qa_assignments_tests
            ;;
        "qa-repos")
            run_qa_repos_tests
            ;;
        "qa-secrets")
            run_qa_secrets_tests
            ;;
        "qa-automation")
            run_qa_automation_tests
            ;;
        "qa-global-options")
            run_qa_global_options_tests
            ;;
        "qa-error-scenarios")
            run_qa_error_scenarios_tests
            ;;
        "qa-all")
            run_qa_all_tests
            ;;
        "all")
            run_installation_tests
            run_cli_tests
            run_python_api_tests
            run_integration_tests
            run_real_repo_tests
            run_qa_all_tests
            ;;
        *)
            log_error "Unknown test suite: $TEST_SUITE"
            show_usage
            exit 1
            ;;
    esac
    
    # Generate report if requested
    if [[ "$GENERATE_REPORT" == "true" ]]; then
        generate_test_report
    fi
    
    # Cleanup if requested
    if [[ "$CLEANUP_AFTER" == "true" ]]; then
        cleanup_test_environment
    fi
    
    # Show summary
    show_test_summary
    
    # Return appropriate exit code
    if [[ $FAILED_TESTS -eq 0 ]]; then
        log_success "All test suites passed!"
        exit 0
    else
        log_error "Some test suites failed!"
        exit 1
    fi
}

# Script execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi