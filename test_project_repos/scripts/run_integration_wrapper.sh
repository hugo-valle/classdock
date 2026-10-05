#!/bin/bash
#
# Wrapper script to run integration tests in activated conda environment
#

# Source the configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"

# Check if test environment is available
if [ -n "$TEST_ENV_NAME" ] && [ -f "$TEST_DIR/test_environments/$TEST_ENV_NAME/activate_test_env.sh" ]; then
    echo "Running integration test in conda environment: $TEST_ENV_NAME"
    source "$TEST_DIR/test_environments/$TEST_ENV_NAME/activate_test_env.sh"
    echo "Python path after activation: $(which python)"
    echo "Testing classdock import: $(python -c 'import classdock; print("SUCCESS")' 2>/dev/null || echo "FAILED")"
else
    echo "Running integration test in host environment (no conda environment available)"
fi

# Run the integration test
exec "$SCRIPT_DIR/test_integration.sh"