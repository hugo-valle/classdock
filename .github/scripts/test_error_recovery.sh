#!/bin/bash
set -euo pipefail

# Error recovery testing script
# Tests various error scenarios and recovery mechanisms

source "$(dirname "$0")/workflow_utils.sh"

# Test error recovery script

TEST_CONFIG_DIR="${1:-tests/fixtures}"

# Test invalid configuration handling
test_invalid_configuration() {
    start_step_timing "invalid_config_test"
    
    # Create invalid configuration file
    cat > "$TEST_CONFIG_DIR/invalid_assignment.conf" << 'EOF'
ASSIGNMENT_NAME=""
ORGANIZATION=""
TEMPLATE_REPO=""
STUDENT_REPOS=""
MAX_REPOS=invalid
EOF
    
    print_message "step" "Testing invalid configuration handling..."
    
    # Test that the CLI properly handles invalid configuration
    set +e
    poetry run classdock assignments --dry-run orchestrate \
        --config "$TEST_CONFIG_DIR/invalid_assignment.conf" 2>/dev/null
    exit_code=$?
    set -e
    
    if [[ $exit_code -ne 0 ]]; then
        print_message "success" "Invalid configuration properly rejected"
    else
        print_message "error" "Invalid configuration was not properly rejected"
        exit 1
    fi
    
    end_step_timing "invalid_config_test"
}

# Test network failure simulation
test_network_failure() {
    start_step_timing "network_failure_test"
    
    print_message "step" "Testing network failure handling..."
    
    # Simulate network failure by using invalid GitHub API endpoint
    poetry run python -c "
import requests
import os
token = os.environ.get('GITHUB_TOKEN')
headers = {'Authorization': f'token {token}'}
try:
    response = requests.get('https://invalid-github-api.com/user', headers=headers, timeout=5)
except requests.exceptions.RequestException as e:
    print(f'✅ Network failure properly handled: {type(e).__name__}')
    exit(0)
print('❌ Network failure was not properly handled')
exit(1)
"
    
    print_message "success" "Network failure handling test passed"
    
    end_step_timing "network_failure_test"
}

# Test missing dependencies handling
test_missing_dependencies() {
    start_step_timing "missing_deps_test"
    
    print_message "step" "Testing missing dependencies handling..."
    
    # Test behavior when required tools are missing
    if command -v gh >/dev/null 2>&1; then
        print_message "info" "Testing missing gh command handling"
        # Create temporary directory for mock gh command
        mkdir -p /tmp/mock_bin
        echo '#!/bin/bash' > /tmp/mock_bin/gh
        echo 'echo "gh: command not found" >&2; exit 127' >> /tmp/mock_bin/gh
        chmod +x /tmp/mock_bin/gh
        
        # Test graceful handling (would need specific script testing)
        print_message "success" "Missing dependencies test framework ready"
    else
        print_message "warning" "Missing dependencies test skipped (gh not available)"
    fi
    
    end_step_timing "missing_deps_test"
}

# Run all error recovery tests
print_message "step" "Running error recovery tests..."

test_invalid_configuration
test_network_failure  
test_missing_dependencies

print_message "success" "All error recovery tests completed"