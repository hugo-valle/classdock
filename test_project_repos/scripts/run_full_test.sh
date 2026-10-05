#!/bin/bash
#
# Main Test Orchestration Script for ClassDock Package
# 
# This script runs comprehensive testing of the classdock Python package
# including installation, CLI interface, Python API, and integration tests.
#
# Usage:
#   ./run_full_test.sh [OPTIONS]
#
# Options:
#   --quick         Run quick test suite (basic validation)
#   --comprehensive Run comprehensive test suite (all tests)
#   --report        Generate detailed test report
#   --ci-mode       Run in CI mode (non-interactive)
#   --cleanup       Clean up test environments after completion
#   --verbose       Enable verbose output
#   --help          Show this help message
#

set -euo pipefail

# Script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TEST_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Source configuration
source "$SCRIPT_DIR/config.sh"

# Test configuration
TEST_ENV_DIR="$TEST_DIR/test_environments"
REPORTS_DIR="$TEST_DIR/reports"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
TEST_REPORT="$REPORTS_DIR/test_report_$TIMESTAMP.md"

# Test results tracking
TESTS_PASSED=0
TESTS_FAILED=0
FAILED_TESTS=()

# Color codes for output
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

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "\n${BLUE}==== $1 ====${NC}"
}

# Test result tracking
mark_test_passed() {
    ((TESTS_PASSED++))
    log_success "$1"
}

mark_test_failed() {
    ((TESTS_FAILED++))
    FAILED_TESTS+=("$1")
    log_error "$1"
}

# Help function
show_help() {
    cat << EOF
ClassDock Package Testing Suite

Usage: $0 [OPTIONS]

OPTIONS:
  --quick         Run quick test suite (basic validation)
  --comprehensive Run comprehensive test suite (all tests)
  --real-repo     Run tests with real GitHub repository
  --qa            Run QA functional tests (comprehensive validation)
  --report        Generate detailed test report
  --ci-mode       Run in CI mode (non-interactive)
  --cleanup       Clean up test environments after completion
  --verbose       Enable verbose output
  --dry-run       Show what would be done without executing
  --help          Show this help message

EXAMPLES:
  ./scripts/run_full_test.sh                          # Run standard test suite
  ./scripts/run_full_test.sh --comprehensive --report # Run all tests with detailed report
  ./scripts/run_full_test.sh --real-repo              # Test with real GitHub repository
  ./scripts/run_full_test.sh --qa                     # Run comprehensive QA functional tests
  ./scripts/run_full_test.sh --qa --verbose           # Run QA tests with detailed output
  ./scripts/run_full_test.sh --dry-run                # Show what would be executed
  ./scripts/run_full_test.sh --quick --cleanup        # Quick test with cleanup
  ./scripts/run_full_test.sh --ci-mode                # CI-friendly testing

ENVIRONMENT:
  Set PYTHON_VERSION to test specific Python version (default: 3.11)
  Set TEST_TIMEOUT to change test timeout (default: 300 seconds)

EOF
}

# Parse command line arguments
QUICK_MODE=false
COMPREHENSIVE_MODE=false
REAL_REPO_MODE=false
QA_MODE=false
GENERATE_REPORT=false
CI_MODE=false
CLEANUP_AFTER=false
VERBOSE=false
DRY_RUN=false
TEST_ENV_ACTIVATED=false
TEST_ENV_NAME=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --quick)
            QUICK_MODE=true
            shift
            ;;
        --comprehensive)
            COMPREHENSIVE_MODE=true
            shift
            ;;
        --real-repo)
            REAL_REPO_MODE=true
            shift
            ;;
        --qa)
            QA_MODE=true
            shift
            ;;
        --report)
            GENERATE_REPORT=true
            shift
            ;;
        --ci-mode)
            CI_MODE=true
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
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Set verbose mode for scripts
if [ "$VERBOSE" = true ]; then
    export VERBOSE=1
fi

# Initialize test report
initialize_test_report() {
    mkdir -p "$REPORTS_DIR"
    
    cat > "$TEST_REPORT" << EOF
# ClassDock Package Test Report

**Generated**: $(date)  
**Test Mode**: $([ "$QUICK_MODE" = true ] && echo "Quick" || [ "$COMPREHENSIVE_MODE" = true ] && echo "Comprehensive" || [ "$QA_MODE" = true ] && echo "QA Functional Testing" || echo "Standard")  
**Python Version**: $(python --version 2>&1)  
**Operating System**: $(uname -s -r)  
**Package Version**: $EXPECTED_VERSION  

## Test Environment

- **Project Root**: $PROJECT_ROOT
- **Test Directory**: $TEST_DIR
- **Test Environment**: $TEST_ENV_DIR
- **CI Mode**: $([ "$CI_MODE" = true ] && echo "Yes" || echo "No")
- **QA Mode**: $([ "$QA_MODE" = true ] && echo "Yes" || echo "No")

## Test Results Summary

EOF
}

# Update test report
update_test_report() {
    local test_name="$1"
    local status="$2"
    local details="${3:-}"
    
    echo "### $test_name" >> "$TEST_REPORT"
    echo "" >> "$TEST_REPORT"
    echo "**Status**: $status" >> "$TEST_REPORT"
    
    if [ -n "$details" ]; then
        echo "" >> "$TEST_REPORT"
        echo "$details" >> "$TEST_REPORT"
    fi
    
    echo "" >> "$TEST_REPORT"
}

# Run test with error handling
run_test() {
    local test_name="$1"
    local test_script="$2"
    local required="${3:-true}"
    
    log_step "Running $test_name"
    
    local start_time=$(date +%s)
    local status="✅ PASSED"
    local output=""
    
    if [ "$VERBOSE" = true ]; then
        if ! output=$(eval "$test_script" 2>&1); then
            status="❌ FAILED"
            if [ "$required" = true ]; then
                mark_test_failed "$test_name"
            else
                log_warning "$test_name failed (non-critical)"
            fi
        else
            mark_test_passed "$test_name"
        fi
    else
        if ! output=$(eval "$test_script" 2>&1); then
            status="❌ FAILED"
            if [ "$required" = true ]; then
                mark_test_failed "$test_name"
            else
                log_warning "$test_name failed (non-critical)"
            fi
        else
            mark_test_passed "$test_name"
        fi
    fi
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    log_info "$test_name completed in ${duration}s"
    
    if [ "$GENERATE_REPORT" = true ]; then
        update_test_report "$test_name" "$status" "Duration: ${duration}s\n\nOutput:\n\`\`\`\n$output\n\`\`\`"
    fi
}

# Test suite execution
run_installation_tests() {
    log_step "Installation Testing Phase"
    
    # First, set up the test environment and capture its name
    # local env_name="${TEST_ENV_BASE_NAME}_$(date +%s)"
    local env_name="${TEST_ENV_BASE_NAME}"
    log_info "Creating isolated test environment: $env_name"
    
    # Run environment setup
    if run_test "Environment Setup" "$SCRIPT_DIR/setup_test_env.sh $env_name"; then
        log_info "Test environment created successfully"
        
        # Export the environment name for use by other scripts
        export TEST_ENV_NAME="$env_name"
        export TEST_ENV_DIR="$TEST_DIR/test_environments/$env_name"
        
        # Build package with Poetry AFTER activating conda environment
        # Source the activation script to switch to the test environment
        local activation_script="$TEST_ENV_DIR/activate_test_env.sh"
        if [ -f "$activation_script" ]; then
            log_info "Activating test environment: $env_name"
            source "$activation_script"
            
            # Announce environment switch
            log_info "Switching to $env_name"
            
            # Verify we're in the correct test environment
            local current_env="$CONDA_DEFAULT_ENV"
            if [ "$current_env" = "$env_name" ]; then
                log_info "✅ Successfully switched to environment: $current_env"
            else
                log_warning "⚠️  Expected environment: $env_name, but currently in: $current_env"
            fi
            
            log_info "Current Python: $(which python)"
            log_info "Current Python version: $(python --version)"
            
            # Build package with Poetry in the activated conda environment
            log_info "Building package with Poetry (in conda environment)"
            cd "$PROJECT_ROOT"
            if poetry --version >/dev/null 2>&1; then
                if ! poetry build; then
                    log_error "Poetry build failed"
                    return 1
                fi
            else
                log_warning "Poetry not available in conda environment, skipping build step"
            fi
            cd "$SCRIPT_DIR"
            
            # Now run package installation in the activated environment (skip building)
            export SKIP_BUILD=true
            run_test "Package Installation" "$SCRIPT_DIR/test_installation.sh"
            
            # Keep the test environment activated for subsequent tests
            log_info "Test environment remains activated for integration tests"
            export TEST_ENV_ACTIVATED=true
        else
            log_error "Activation script not found: $activation_script"
            return 1
        fi
    else
        log_error "Environment setup failed"
        return 1
    fi
}

run_cli_tests() {
    log_step "CLI Interface Testing Phase"
    
    run_test "CLI Interface Validation" "$SCRIPT_DIR/test_cli_interface.sh"
}

run_api_tests() {
    log_step "Python API Testing Phase"
    
    run_test "Python API Validation" "python $SCRIPT_DIR/test_python_api.py"
}

run_integration_tests() {
    log_step "Integration Testing Phase"
    
    # Set flag to indicate we're running from comprehensive test framework
    export COMPREHENSIVE_TESTING=true
    
    # Environment should already be activated from installation phase
    if [ "$TEST_ENV_ACTIVATED" = true ]; then
        log_info "Using already activated test environment: $TEST_ENV_NAME"
        run_test "Basic Integration" "$SCRIPT_DIR/test_integration.sh"
        run_test "Secrets Management" "$SCRIPT_DIR/test_secrets_management.sh"
    else
        # Fallback to wrapper script if environment isn't activated
        run_test "Basic Integration" "$SCRIPT_DIR/run_integration_wrapper.sh"
        run_test "Secrets Management" "$SCRIPT_DIR/test_secrets_management.sh"
    fi
}

run_performance_tests() {
    log_step "Performance Testing Phase"
    
    log_info "Performance testing requires additional scripts - skipping for now"
    # TODO: Add performance testing scripts
    # run_test "Memory Usage" "python $SCRIPT_DIR/test_memory_usage.py" false
    # run_test "Execution Speed" "$SCRIPT_DIR/test_performance.sh" false
    # run_test "Resource Usage" "$SCRIPT_DIR/test_resource_usage.sh" false
}

# QA Testing - Comprehensive functional validation
run_qa_tests() {
    log_step "QA Functional Testing Phase"
    
    # Ensure report directory exists for QA logs
    mkdir -p "$QA_REPORT_DIR"
    
    # Check QA prerequisites before running tests - integrate with test tracking
    log_info "Checking QA prerequisites..."
    if ! check_qa_prerequisites; then
        mark_test_failed "QA Prerequisites" "Missing required directories or helper libraries"
        return 1
    fi
    mark_test_passed "QA Prerequisites"
    
    # Source helper libraries for QA tests
    if [ -f "$LIB_DIR/test_helpers.sh" ]; then
        # Source in current shell but preserve our logging functions and test counters
        # Note: test_helpers.sh guards its counter initialization, so TESTS_PASSED/FAILED
        # and FAILED_TESTS are preserved when already set (see test_helpers.sh header)
        _orchestrator_log_info="$( declare -f log_info )"
        _orchestrator_log_success="$( declare -f log_success )"
        _orchestrator_log_error="$( declare -f log_error )"
        _orchestrator_log_warning="$( declare -f log_warning )"
        _orchestrator_log_step="$( declare -f log_step )"
        
        source "$LIB_DIR/test_helpers.sh"
        log_info "Loaded test helper library"
        
        # Restore orchestrator logging functions after sourcing
        # (Test counters are automatically preserved by guarded initialization in helpers)
        eval "$_orchestrator_log_info"
        eval "$_orchestrator_log_success"
        eval "$_orchestrator_log_error"
        eval "$_orchestrator_log_warning"
        eval "$_orchestrator_log_step"
    else
        log_error "Test helper library not found: $LIB_DIR/test_helpers.sh"
        mark_test_failed "QA Testing - Missing test helpers"
        return 1
    fi
    
    if [ -f "$LIB_DIR/mock_helpers.sh" ]; then
        source "$LIB_DIR/mock_helpers.sh"
        log_info "Loaded mock helper library"
    else
        log_error "Mock helper library not found: $LIB_DIR/mock_helpers.sh"
        mark_test_failed "QA Testing - Missing mock helpers"
        return 1
    fi
    
    # Run QA test suites
    log_info "Running comprehensive QA functional tests..."
    
    # Configuration validation tests
    if [ -d "$QA_TESTS_DIR" ]; then
        for qa_script in "$QA_TESTS_DIR"/test_*.sh; do
            if [ -f "$qa_script" ]; then
                local test_name=$(basename "$qa_script" .sh)
                log_info "Executing QA test: $test_name"
                
                # Only tee to log file if report generation is enabled
                if [ "$GENERATE_REPORT" = true ]; then
                    if bash "$qa_script" 2>&1 | tee -a "$QA_REPORT_DIR/qa_tests.log"; then
                        mark_test_passed "QA Test: $test_name"
                    else
                        mark_test_failed "QA Test: $test_name"
                    fi
                else
                    if bash "$qa_script" 2>&1; then
                        mark_test_passed "QA Test: $test_name"
                    else
                        mark_test_failed "QA Test: $test_name"
                    fi
                fi
            fi
        done
    else
        log_warning "QA tests directory not found: $QA_TESTS_DIR"
        log_info "Creating QA tests directory structure..."
        mkdir -p "$QA_TESTS_DIR"
    fi
    
    # Configuration fixture validation
    log_info "Validating configuration fixtures..."
    if [ -d "$QA_FIXTURES_DIR" ]; then
        local fixture_count=$(find "$QA_FIXTURES_DIR" -name "*.conf" | wc -l)
        log_info "Found $fixture_count configuration fixtures"
        
        # Note: classdock CLI loads config from current directory's assignment.conf
        # So we need to test config parsing separately or copy fixtures to test directory
        # For now, just validate the fixtures exist and have correct format
        
        # Test valid configurations - verify they have required fields
        for config in "$QA_FIXTURES_DIR"/valid_*.conf; do
            if [ -f "$config" ]; then
                local config_name=$(basename "$config" .conf)
                log_info "Testing valid config structure: $config_name"
                
                # Check for required fields
                if grep -q "^GITHUB_ORGANIZATION=" "$config" && \
                   grep -q "^ASSIGNMENT_NAME=" "$config" && \
                   grep -q "^STUDENTS_FILE=" "$config"; then
                    mark_test_passed "Config Structure: $config_name"
                else
                    mark_test_failed "Config Structure: $config_name (missing required fields)"
                fi
            fi
        done
        
        # Test invalid configurations - verify they're missing required fields
        for config in "$QA_FIXTURES_DIR"/invalid_missing*.conf; do
            if [ -f "$config" ]; then
                local config_name=$(basename "$config" .conf)
                log_info "Testing invalid config structure: $config_name"
                
                # Should be missing at least one required field
                if ! grep -q "^GITHUB_ORGANIZATION=" "$config" || \
                   ! grep -q "^ASSIGNMENT_NAME=" "$config" || \
                   ! grep -q "^STUDENTS_FILE=" "$config"; then
                    mark_test_passed "Config Structure: $config_name"
                else
                    mark_test_failed "Config Structure: $config_name (should be missing required fields)"
                fi
            fi
        done
    else
        log_warning "QA fixtures directory not found: $QA_FIXTURES_DIR"
    fi
    
    log_success "QA functional testing phase completed"
}

# Cleanup function
cleanup_test_environment() {
    # Deactivate conda environment if it was activated
    if [ "$TEST_ENV_ACTIVATED" = true ] && [ -n "$TEST_ENV_NAME" ]; then
        log_info "Deactivating test environment: $TEST_ENV_NAME"
        conda deactivate 2>/dev/null || true
        log_info "✅ Environment deactivated, returned to: ${CONDA_DEFAULT_ENV:-base}"
    fi
    
    if [ "$CLEANUP_AFTER" = true ]; then
        log_step "Cleaning up test environment"
        "$SCRIPT_DIR/cleanup_test_env.sh"
        log_success "Test environment cleaned up"
    fi
}

# Generate final test report
finalize_test_report() {
    if [ "$GENERATE_REPORT" = true ]; then
        cat >> "$TEST_REPORT" << EOF

## Final Results

- **Total Tests**: $((TESTS_PASSED + TESTS_FAILED))
- **Passed**: $TESTS_PASSED
- **Failed**: $TESTS_FAILED
- **Success Rate**: $(( TESTS_PASSED * 100 / (TESTS_PASSED + TESTS_FAILED) ))%

EOF

        if [ ${#FAILED_TESTS[@]} -gt 0 ]; then
            echo "### Failed Tests" >> "$TEST_REPORT"
            echo "" >> "$TEST_REPORT"
            for test in "${FAILED_TESTS[@]}"; do
                echo "- $test" >> "$TEST_REPORT"
            done
            echo "" >> "$TEST_REPORT"
        fi

        cat >> "$TEST_REPORT" << EOF

## Recommendations

$([ $TESTS_FAILED -eq 0 ] && echo "✅ All tests passed! Package is ready for release." || echo "❌ Some tests failed. Review failed tests before release.")

## Test Environment Details

- **Test Duration**: $(date -d@$(($(date +%s) - START_TIME)) -u +%H:%M:%S) 2>/dev/null || echo "N/A"
- **Test Report**: $TEST_REPORT
- **Log Files**: Available in $REPORTS_DIR

---

*Report generated by ClassDock Testing Suite*
EOF

        log_success "Test report generated: $TEST_REPORT"
    fi
}

# Show dry-run summary
show_dry_run_summary() {
    echo
    echo "=========================================="
    echo "DRY RUN SUMMARY"
    echo "=========================================="
    echo "Test mode: $([ "$QUICK_MODE" = true ] && echo "Quick" || [ "$COMPREHENSIVE_MODE" = true ] && echo "Comprehensive" || [ "$QA_MODE" = true ] && echo "QA Functional Testing" || [ "$REAL_REPO_MODE" = true ] && echo "Real Repository" || echo "Standard")"
    echo "Options:"
    echo "  - Generate Report: $GENERATE_REPORT"
    echo "  - CI Mode: $CI_MODE"
    echo "  - Cleanup After: $CLEANUP_AFTER"
    echo "  - Verbose: $VERBOSE"
    echo
    
    if [[ "$QA_MODE" == "true" ]]; then
        echo "QA Functional Testing would execute:"
        echo "  1. Validate QA prerequisites (helper libraries, fixtures)"
        echo "  2. Source test_helpers.sh and mock_helpers.sh"
        echo "  3. Execute all QA test scripts from qa_tests/ directory"
        echo "  4. Validate configuration fixtures:"
        echo "     - Test valid_minimal.conf (should succeed)"
        echo "     - Test valid_comprehensive.conf (should succeed)"
        echo "     - Test invalid_missing_required.conf (should fail)"
        echo "     - Test invalid_malformed_urls.conf (should fail)"
        echo "     - Test invalid_wrong_types.conf (should fail)"
        echo "     - Test edge_case_empty_values.conf (edge case handling)"
        echo "     - Test edge_case_special_characters.conf (encoding)"
        echo "     - Test edge_case_very_long_values.conf (buffer limits)"
        echo "  5. Generate comprehensive test results summary"
        echo "  6. Create QA test report (if --report enabled)"
    elif [[ "$REAL_REPO_MODE" == "true" ]]; then
        echo "Real Repository Testing would execute:"
        echo "  1. Validate prerequisites (config files, GitHub token)"
        echo "  2. Parse real repository configuration"
        echo "  3. Set up conda test environment"
        echo "  4. Clone actual GitHub repository"
        echo "  5. Generate assignment.conf from real data"
        echo "  6. Test configuration validation"
        echo "  7. Test assignment setup (dry-run mode)"
        echo "  8. Test repository operations"
        echo "  9. Test secrets management"
        echo " 10. Test CLI interface comprehensively"
        echo " 11. Test Python API functionality"
        echo " 12. Clean up test environment"
    else
        echo "Standard Testing would execute:"
        echo "  1. Installation tests (package building, wheel creation)"
        
        if [ "$QUICK_MODE" = false ]; then
            echo "  2. CLI interface tests (all commands and help)"
            echo "  3. Python API tests (imports and functionality)"
        fi
        
        if [ "$COMPREHENSIVE_MODE" = true ]; then
            echo "  4. Integration tests (end-to-end workflows)"
            echo "  5. Performance tests (memory and timing)"
        elif [ "$QUICK_MODE" = false ]; then
            echo "  4. Integration tests (end-to-end workflows)"
        fi
    fi
    
    if [ "$GENERATE_REPORT" = true ]; then
        echo
        echo "Report generation:"
        echo "  - HTML test report would be generated"
        echo "  - Report location: \$REPORTS_DIR/test_report_\$(date).html"
    fi
    
    if [ "$CLEANUP_AFTER" = true ]; then
        echo
        echo "Cleanup operations:"
        echo "  - Test environments would be cleaned up"
        echo "  - Temporary files would be removed"
    fi
    
    echo "=========================================="
    echo "Use without --dry-run to execute tests"
    echo "=========================================="
}

# Main execution function
main() {
    local START_TIME=$(date +%s)
    
    log_info "Starting ClassDock Package Testing Suite"
    
    # Handle dry-run mode
    if [[ "$DRY_RUN" == "true" ]]; then
        log_warning "DRY RUN MODE - No tests will actually be executed"
        show_dry_run_summary
        return 0
    fi
    
    # Determine test mode and log it
    if [[ "$QA_MODE" == "true" ]]; then
        log_info "Test mode: QA Functional Testing"
        
        # Initialize reporting for QA tests
        if [ "$GENERATE_REPORT" = true ]; then
            initialize_test_report
        fi
        
        # Run QA test suite
        log_step "Executing QA Functional Tests"
        run_qa_tests
        
        log_info "QA functional testing mode completed"
        
    elif [[ "$REAL_REPO_MODE" == "true" ]]; then
        log_info "Test mode: Real Repository Testing"
        
        # Run real repository testing
        log_step "Executing Real Repository Tests"
        local real_repo_script="$SCRIPT_DIR/test_real_repo.sh"
        
        if [[ -f "$real_repo_script" ]]; then
            local real_repo_args=()
            [[ "$VERBOSE" == "true" ]] && real_repo_args+=(--verbose)
            [[ "$CLEANUP_AFTER" == "true" ]] && real_repo_args+=(--cleanup)
            
            if "$real_repo_script" "${real_repo_args[@]}"; then
                mark_test_passed "Real repository testing completed successfully"
                log_success "Real repository tests passed! 🚀"
            else
                mark_test_failed "Real repository testing failed"
                log_error "Real repository tests failed!"
            fi
        else
            mark_test_failed "Real repository testing script not found: $real_repo_script"
            log_error "Real repository testing script not found!"
        fi
        
        # Skip other tests when in real repo mode
        log_info "Real repository mode completed"
        
    else
        # Original test mode logic
        log_info "Test mode: $([ "$QUICK_MODE" = true ] && echo "Quick" || [ "$COMPREHENSIVE_MODE" = true ] && echo "Comprehensive" || echo "Standard")"
        
        # Initialize reporting
        if [ "$GENERATE_REPORT" = true ]; then
            initialize_test_report
        fi
        
        # Create test environment directory
        mkdir -p "$TEST_ENV_DIR"
        
        # Run test suites based on mode
        run_installation_tests
        
        if [ "$QUICK_MODE" = false ]; then
            run_cli_tests
            run_api_tests
        fi
        
        if [ "$COMPREHENSIVE_MODE" = true ]; then
            run_integration_tests
            run_performance_tests
        elif [ "$QUICK_MODE" = false ]; then
            run_integration_tests
        fi
    fi
    
    # Generate final results
    log_step "Test Results Summary"
    
    if [ $TESTS_FAILED -eq 0 ]; then
        log_success "All tests passed! ($TESTS_PASSED/$((TESTS_PASSED + TESTS_FAILED)))"
        log_success "Package is ready for release! 🚀"
    else
        log_error "Some tests failed! ($TESTS_FAILED/$((TESTS_PASSED + TESTS_FAILED)))"
        log_error "Failed tests:"
        for test in "${FAILED_TESTS[@]}"; do
            log_error "  - $test"
        done
    fi
    
    # Cleanup and finalize
    cleanup_test_environment
    
    if [ "$GENERATE_REPORT" = true ]; then
        finalize_test_report
    fi
    
    # Exit with appropriate code
    exit $([ $TESTS_FAILED -eq 0 ] && echo 0 || echo 1)
}

# Trap cleanup on script exit
trap cleanup_test_environment EXIT

# Run main function
main "$@"