#!/bin/bash
# Sample QA test to validate framework

source lib/test_helpers.sh 2>/dev/null

init_test_tracking

# Test 1: Verify CLI is available
if command -v classdock >/dev/null 2>&1; then
    mark_test_passed "CLI availability"
else
    mark_test_failed "CLI availability" "classdock not found"
fi

# Test 2: Verify helper functions work
if [ "$(log_info "test" 2>&1 | grep -c INFO)" -eq 1 ]; then
    mark_test_passed "Helper functions"
else
    mark_test_failed "Helper functions" "log_info not working"
fi

# Test 3: Verify fixture exists
if [ -f "fixtures/configs/valid_minimal.conf" ]; then
    mark_test_passed "Fixture availability"
else
    mark_test_failed "Fixture availability" "valid_minimal.conf not found"
fi

show_test_summary

# Exit with proper code
if [ $TESTS_FAILED -eq 0 ]; then
    exit 0
else
    exit 1
fi
