#!/usr/bin/env bash
################################################################################
# QA Test Orchestrator for ClassDock
#
# This script orchestrates the execution of all QA functional test suites,
# providing comprehensive validation of classdock commands, options,
# and error scenarios.
#
# Features:
# - Run all test suites or specific suites selectively
# - Sequential or parallel execution (experimental)
# - Detailed reporting (Markdown, HTML, JUnit XML)
# - Command-level result tracking and aggregation
# - CI/CD integration support
# - Dry-run mode for planning
#
# Usage:
#   ./run_qa_tests.sh [OPTIONS]
#
# Options:
#   --all              Run all QA test suites (default)
#   --token            Run only token management tests
#   --assignments      Run only assignments commands tests
#   --repos            Run only repos commands tests
#   --secrets          Run only secrets commands tests
#   --automation       Run only automation commands tests
#   --global-options   Run only global options tests
#   --error-scenarios  Run only error scenarios tests
#   --parallel         Run test suites in parallel (experimental)
#   --report           Generate detailed Markdown report
#   --junit            Generate JUnit XML report for CI
#   --verbose          Enable verbose output
#   --dry-run          Show what would be executed
#   --stop-on-failure  Stop execution on first test failure
#   --help             Show this help message
#
# Examples:
#   ./run_qa_tests.sh
#   ./run_qa_tests.sh --assignments
#   ./run_qa_tests.sh --all --report
#   ./run_qa_tests.sh --dry-run
#   ./run_qa_tests.sh --junit --stop-on-failure
#
################################################################################

set -euo pipefail

# Script directory and paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
QA_TESTS_DIR="$SCRIPT_DIR"

# Source required libraries (provides QA_REPORT_DIR, JUNIT_REPORT_DIR)
source "$PROJECT_ROOT/test_project_repos/scripts/config.sh"
source "$PROJECT_ROOT/test_project_repos/lib/test_helpers.sh"
source "$PROJECT_ROOT/test_project_repos/lib/mock_helpers.sh"

# Generate unique run ID for artifact grouping
RUN_ID="$(date +%Y%m%d_%H%M%S)"
TIMESTAMP="$RUN_ID"
RUN_DIR="$QA_REPORT_DIR/$RUN_ID"
mkdir -p "$RUN_DIR"

# Global variables
VERBOSE_MODE=false
DRY_RUN_MODE=false
PARALLEL_MODE=false
GENERATE_REPORT=false
GENERATE_JUNIT=false
STOP_ON_FAILURE=false
SELECTED_SUITES=()
START_TIME=""
END_TIME=""

# Test suite registry
declare -A TEST_SUITES
TEST_SUITES["token"]="test_token_management.sh|Token storage, validation, and security|2-3 min|None"
TEST_SUITES["assignments"]="test_assignments_commands.sh|All 13 assignments commands|5-7 min|Valid config"
TEST_SUITES["repos"]="test_repos_commands.sh|Repository operations and collaborators|3-4 min|Valid config"
TEST_SUITES["secrets"]="test_secrets_commands.sh|Secrets deployment and management|2-3 min|Valid config"
TEST_SUITES["automation"]="test_automation_commands.sh|Cron scheduling and automation|4-5 min|Mock crontab"
TEST_SUITES["global-options"]="test_global_options.sh|Global CLI options testing|3-4 min|Valid config"
TEST_SUITES["error-scenarios"]="test_error_scenarios.sh|Error handling and edge cases|4-5 min|Error fixtures"

# Test results tracking
declare -A SUITE_RESULTS
declare -A SUITE_DURATION
declare -A SUITE_OUTPUT
TOTAL_SUITES=0
PASSED_SUITES=0
FAILED_SUITES=0

################################################################################
# Help System
################################################################################

show_help() {
    cat << EOF
QA Test Orchestrator for ClassDock

USAGE:
    ./run_qa_tests.sh [OPTIONS]

OPTIONS:
    --all              Run all QA test suites (default)
    --token            Run only token management tests
    --assignments      Run only assignments commands tests
    --repos            Run only repos commands tests
    --secrets          Run only secrets commands tests
    --automation       Run only automation commands tests
    --global-options   Run only global options tests
    --error-scenarios  Run only error scenarios tests
    --parallel         Run test suites in parallel (experimental)
    --report           Generate detailed Markdown report
    --junit            Generate JUnit XML report for CI
    --verbose          Enable verbose output
    --dry-run          Show what would be executed
    --stop-on-failure  Stop execution on first test failure
    --help             Show this help message

TEST SUITES:
    Token Management (--token):
        Duration: 2-3 minutes
        Coverage: Token storage, validation, security
        Tests: 40+ scenarios

    Assignments Commands (--assignments):
        Duration: 5-7 minutes
        Coverage: All 13 assignments commands
        Tests: 100+ scenarios

    Repos Commands (--repos):
        Duration: 3-4 minutes
        Coverage: All 4 repos commands
        Tests: 30+ scenarios

    Secrets Commands (--secrets):
        Duration: 2-3 minutes
        Coverage: Secrets management
        Tests: 20+ scenarios

    Automation Commands (--automation):
        Duration: 4-5 minutes
        Coverage: All 9 automation commands
        Tests: 50+ scenarios

    Global Options (--global-options):
        Duration: 3-4 minutes
        Coverage: Global CLI options
        Tests: 40+ scenarios

    Error Scenarios (--error-scenarios):
        Duration: 4-5 minutes
        Coverage: Error handling
        Tests: 60+ scenarios

EXAMPLES:
    # Run all tests
    ./run_qa_tests.sh

    # Run specific suite
    ./run_qa_tests.sh --assignments

    # Run with report
    ./run_qa_tests.sh --all --report

    # Dry-run
    ./run_qa_tests.sh --dry-run

    # CI mode
    ./run_qa_tests.sh --junit --stop-on-failure

    # Multiple suites
    ./run_qa_tests.sh --token --assignments --repos

DOCUMENTATION:
    See docs/QA_AUTOMATION_GUIDE.md for detailed documentation

EOF
}

################################################################################
# Command-Line Argument Parsing
################################################################################

parse_arguments() {
    if [ $# -eq 0 ]; then
        # Default: run all tests
        SELECTED_SUITES=(token assignments repos secrets automation global-options error-scenarios)
        return
    fi

    while [ $# -gt 0 ]; do
        case "$1" in
            --all)
                SELECTED_SUITES=(token assignments repos secrets automation global-options error-scenarios)
                ;;
            --token)
                SELECTED_SUITES+=("token")
                ;;
            --assignments)
                SELECTED_SUITES+=("assignments")
                ;;
            --repos)
                SELECTED_SUITES+=("repos")
                ;;
            --secrets)
                SELECTED_SUITES+=("secrets")
                ;;
            --automation)
                SELECTED_SUITES+=("automation")
                ;;
            --global-options)
                SELECTED_SUITES+=("global-options")
                ;;
            --error-scenarios)
                SELECTED_SUITES+=("error-scenarios")
                ;;
            --parallel)
                PARALLEL_MODE=true
                ;;
            --report)
                GENERATE_REPORT=true
                ;;
            --junit)
                GENERATE_JUNIT=true
                ;;
            --verbose)
                VERBOSE_MODE=true
                ;;
            --dry-run)
                DRY_RUN_MODE=true
                ;;
            --stop-on-failure)
                STOP_ON_FAILURE=true
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                echo "Run with --help for usage information"
                exit 1
                ;;
        esac
        shift
    done

    # If no specific suites selected, run all
    if [ ${#SELECTED_SUITES[@]} -eq 0 ]; then
        SELECTED_SUITES=(token assignments repos secrets automation global-options error-scenarios)
    fi
    
    # De-duplicate selected suites while preserving order
    declare -A seen
    local unique_suites=()
    for suite in "${SELECTED_SUITES[@]}"; do
        if [[ ! ${seen[$suite]+_} ]]; then
            unique_suites+=("$suite")
            seen[$suite]=1
        fi
    done
    SELECTED_SUITES=("${unique_suites[@]}")
}

################################################################################
# Test Execution Functions
################################################################################

run_single_test_suite() {
    local suite_name="$1"
    local suite_info="${TEST_SUITES[$suite_name]}"
    
    IFS='|' read -r suite_script suite_description suite_duration suite_deps <<< "$suite_info"
    local suite_path="$QA_TESTS_DIR/$suite_script"
    
    log_step "Running test suite: $suite_name"
    log_info "Description: $suite_description"
    log_info "Estimated duration: $suite_duration"
    
    if [ ! -f "$suite_path" ]; then
        log_error "Test suite script not found: $suite_path"
        SUITE_RESULTS[$suite_name]="MISSING"
        return 1
    fi
    
    if [ ! -x "$suite_path" ]; then
        log_warning "Test suite not executable, making executable: $suite_path"
        chmod +x "$suite_path"
    fi
    
    # Execute test suite
    local suite_start=$(date +%s)
    local exit_code=0
    local output_file="$RUN_DIR/output_${suite_name}.log"
    
    if $VERBOSE_MODE; then
        "$suite_path" 2>&1 | tee "$output_file" || exit_code=$?
    else
        "$suite_path" > "$output_file" 2>&1 || exit_code=$?
    fi
    
    local suite_end=$(date +%s)
    local duration=$((suite_end - suite_start))
    
    SUITE_DURATION[$suite_name]=$duration
    SUITE_OUTPUT[$suite_name]="$output_file"
    
    if [ $exit_code -eq 0 ]; then
        SUITE_RESULTS[$suite_name]="PASSED"
        PASSED_SUITES=$((PASSED_SUITES + 1))
        mark_test_passed "$suite_name test suite (${duration}s)"
    else
        SUITE_RESULTS[$suite_name]="FAILED"
        FAILED_SUITES=$((FAILED_SUITES + 1))
        mark_test_failed "$suite_name test suite" "Exit code: $exit_code"
        
        if $STOP_ON_FAILURE; then
            log_error "Stopping on failure as requested"
            return $exit_code
        fi
    fi
    
    return $exit_code
}

run_all_test_suites() {
    log_section "Executing QA Test Suites"
    
    TOTAL_SUITES=${#SELECTED_SUITES[@]}
    
    for suite_name in "${SELECTED_SUITES[@]}"; do
        if ! run_single_test_suite "$suite_name"; then
            if $STOP_ON_FAILURE; then
                return 1
            fi
        fi
    done
    
    return 0
}

run_parallel_test_suites() {
    log_section "Executing QA Test Suites (Parallel Mode)"
    log_warning "Parallel mode is experimental - output may be interleaved"
    
    TOTAL_SUITES=${#SELECTED_SUITES[@]}
    local pids=()
    local max_parallel=4
    local running=0
    
    for suite_name in "${SELECTED_SUITES[@]}"; do
        # Wait if we've hit max parallel
        while [ $running -ge $max_parallel ]; do
            for i in "${!pids[@]}"; do
                if ! kill -0 "${pids[$i]}" 2>/dev/null; then
                    wait "${pids[$i]}"
                    unset 'pids[i]'
                    running=$((running - 1))
                fi
            done
            sleep 1
        done
        
        # Start test suite in background
        run_single_test_suite "$suite_name" &
        pids+=($!)
        running=$((running + 1))
    done
    
    # Wait for all remaining jobs
    for pid in "${pids[@]}"; do
        wait "$pid"
    done
    
    return 0
}

################################################################################
# Reporting Functions
################################################################################

generate_markdown_report() {
    local report_file="$RUN_DIR/qa_test_report_${TIMESTAMP}.md"
    
    log_info "Generating Markdown report: $report_file"
    
    cat > "$report_file" << EOF
# QA Test Report - ClassDock

**Run ID**: $RUN_ID
**Date**: $(date '+%Y-%m-%d %H:%M:%S')
**Test Mode**: $([ "$PARALLEL_MODE" = true ] && echo "Parallel" || echo "Sequential")
**Total Suites**: $TOTAL_SUITES
**Execution Time**: $((END_TIME - START_TIME)) seconds

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Suites Executed | $TOTAL_SUITES |
| Passed | $PASSED_SUITES |
| Failed | $FAILED_SUITES |
| Success Rate | $(awk "BEGIN {printf \"%.1f\", ($PASSED_SUITES/$TOTAL_SUITES)*100}")% |

---

## Test Suite Results

EOF

    for suite_name in "${SELECTED_SUITES[@]}"; do
        local result="${SUITE_RESULTS[$suite_name]}"
        local duration="${SUITE_DURATION[$suite_name]:-0}"
        local output_file="${SUITE_OUTPUT[$suite_name]:-}"
        local status_icon="❌"
        
        if [ "$result" = "PASSED" ]; then
            status_icon="✅"
        elif [ "$result" = "MISSING" ]; then
            status_icon="⚠️"
        fi
        
        cat >> "$report_file" << EOF
### $status_icon $suite_name

- **Status**: $result
- **Duration**: ${duration}s
- **Log**: $output_file

EOF
        
        if [ "$result" = "FAILED" ] && [ -n "$output_file" ] && [ -f "$output_file" ]; then
            echo "**Failed Tests:**" >> "$report_file"
            echo '```' >> "$report_file"
            grep -A 5 "FAILED" "$output_file" | head -20 >> "$report_file" || echo "No failure details captured" >> "$report_file"
            echo '```' >> "$report_file"
            echo "" >> "$report_file"
        fi
    done
    
    cat >> "$report_file" << EOF

---

## Recommendations

EOF
    
    if [ $FAILED_SUITES -eq 0 ]; then
        echo "✅ All test suites passed! The CLI is functioning correctly." >> "$report_file"
    else
        echo "❌ $FAILED_SUITES test suite(s) failed. Review the failure details above and:" >> "$report_file"
        echo "1. Check the log files for detailed error messages" >> "$report_file"
        echo "2. Verify prerequisites are met for failed suites" >> "$report_file"
        echo "3. Re-run failed suites individually with --verbose for debugging" >> "$report_file"
    fi
    
    log_success "Markdown report generated: $report_file"
}

generate_junit_xml() {
    local junit_file="$JUNIT_REPORT_DIR/qa_tests_${TIMESTAMP}.xml"
    
    log_info "Generating JUnit XML report: $junit_file"
    
    cat > "$junit_file" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<testsuites name="QA Tests" tests="$TOTAL_SUITES" failures="$FAILED_SUITES" time="$((END_TIME - START_TIME))">
EOF
    
    for suite_name in "${SELECTED_SUITES[@]}"; do
        local result="${SUITE_RESULTS[$suite_name]}"
        local duration="${SUITE_DURATION[$suite_name]:-0}"
        local output_file="${SUITE_OUTPUT[$suite_name]:-}"
        
        cat >> "$junit_file" << EOF
  <testsuite name="$suite_name" tests="1" failures="$([ "$result" = "FAILED" ] && echo "1" || echo "0")" time="$duration">
    <testcase name="$suite_name" classname="qa.$suite_name" time="$duration">
EOF
        
        if [ "$result" = "FAILED" ]; then
            echo "      <failure message=\"Test suite failed\">" >> "$junit_file"
            if [ -n "$output_file" ] && [ -f "$output_file" ]; then
                grep "FAILED" "$output_file" | head -10 >> "$junit_file" || echo "No failure details" >> "$junit_file"
            fi
            echo "      </failure>" >> "$junit_file"
        fi
        
        cat >> "$junit_file" << EOF
    </testcase>
  </testsuite>
EOF
    done
    
    echo "</testsuites>" >> "$junit_file"
    
    log_success "JUnit XML report generated: $junit_file"
}

show_test_summary() {
    echo ""
    log_section "QA Test Execution Summary"
    
    echo ""
    echo "Total Test Suites: $TOTAL_SUITES"
    echo "Passed: $PASSED_SUITES"
    echo "Failed: $FAILED_SUITES"
    
    if [ $TOTAL_SUITES -gt 0 ]; then
        local success_rate=$(awk "BEGIN {printf \"%.1f\", ($PASSED_SUITES/$TOTAL_SUITES)*100}")
        echo "Success Rate: ${success_rate}%"
    fi
    
    echo "Execution Time: $((END_TIME - START_TIME)) seconds"
    echo ""
    
    if [ $FAILED_SUITES -gt 0 ]; then
        log_error "Failed Test Suites:"
        for suite_name in "${SELECTED_SUITES[@]}"; do
            if [ "${SUITE_RESULTS[$suite_name]}" = "FAILED" ]; then
                echo "  - $suite_name"
            fi
        done
        echo ""
    fi
    
    if [ $FAILED_SUITES -eq 0 ]; then
        log_success "All QA test suites passed!"
    else
        log_warning "Some test suites failed. Review logs for details."
    fi
}

################################################################################
# Dry-Run Mode
################################################################################

show_dry_run_summary() {
    log_section "Dry-Run Mode - QA Test Execution Plan"
    
    echo ""
    echo "Configuration:"
    echo "  Test Suites: ${#SELECTED_SUITES[@]}"
    echo "  Execution Mode: $([ "$PARALLEL_MODE" = true ] && echo "Parallel" || echo "Sequential")"
    echo "  Verbose: $VERBOSE_MODE"
    echo "  Stop on Failure: $STOP_ON_FAILURE"
    echo "  Generate Report: $GENERATE_REPORT"
    echo "  Generate JUnit: $GENERATE_JUNIT"
    echo ""
    
    echo "Test Suites to Execute:"
    for suite_name in "${SELECTED_SUITES[@]}"; do
        local suite_info="${TEST_SUITES[$suite_name]}"
        IFS='|' read -r suite_script suite_description suite_duration suite_deps <<< "$suite_info"
        echo "  ✓ $suite_name"
        echo "    - Script: $suite_script"
        echo "    - Description: $suite_description"
        echo "    - Duration: $suite_duration"
        echo "    - Dependencies: $suite_deps"
        echo ""
    done
    
    local total_min_duration=0
    local total_max_duration=0
    for suite_name in "${SELECTED_SUITES[@]}"; do
        local suite_info="${TEST_SUITES[$suite_name]}"
        IFS='|' read -r suite_script suite_description suite_duration suite_deps <<< "$suite_info"
        # Extract min from "X-Y min" format
        local min=$(echo "$suite_duration" | sed 's/\([0-9]*\).*/\1/')
        total_min_duration=$((total_min_duration + min))
        total_max_duration=$((total_max_duration + min + 2))
    done
    
    echo "Estimated Total Execution Time: ${total_min_duration}-${total_max_duration} minutes"
    echo ""
    echo "Test artifacts will be organized in: $RUN_DIR"
    echo "Reports will be generated in: $QA_REPORT_DIR"
    if $GENERATE_JUNIT; then
        echo "JUnit XML will be generated in: $JUNIT_REPORT_DIR"
    fi
    
    log_info "Dry-run complete. Remove --dry-run to execute tests."
}

################################################################################
# Cleanup Functions
################################################################################

cleanup_qa_environment() {
    log_step "Cleaning up QA test environment"
    
    # Call mock cleanup if available
    if declare -f cleanup_mocks > /dev/null; then
        cleanup_mocks
    fi
    
    # Additional cleanup can be added here
}

finalize_qa_testing() {
    END_TIME=$(date +%s)
    
    if $GENERATE_REPORT; then
        generate_markdown_report
    fi
    
    if $GENERATE_JUNIT; then
        generate_junit_xml
    fi
    
    show_test_summary
    
    cleanup_qa_environment
    
    # Return exit code based on results
    if [ $FAILED_SUITES -gt 0 ]; then
        return 1
    else
        return 0
    fi
}

################################################################################
# Main Execution
################################################################################

main() {
    # Parse arguments
    parse_arguments "$@"
    
    # Initialize test tracking
    init_test_tracking
    
    # Handle dry-run mode
    if $DRY_RUN_MODE; then
        show_dry_run_summary
        exit 0
    fi
    
    # Validate prerequisites
    if ! check_qa_prerequisites; then
        log_error "QA prerequisites not met. Please fix issues and try again."
        exit 1
    fi
    
    # Record start time
    START_TIME=$(date +%s)
    
    # Display header
    log_section "QA Test Orchestrator - ClassDock"
    log_info "Test suites to execute: ${#SELECTED_SUITES[@]}"
    log_info "Execution mode: $([ "$PARALLEL_MODE" = true ] && echo "Parallel" || echo "Sequential")"
    echo ""
    
    # Execute tests
    local exit_code=0
    if $PARALLEL_MODE; then
        run_parallel_test_suites || exit_code=$?
    else
        run_all_test_suites || exit_code=$?
    fi
    
    # Finalize and generate reports
    finalize_qa_testing || exit_code=$?
    
    exit $exit_code
}

# Run main function
main "$@"
