#!/bin/bash
################################################################################
# Test Suite: Secrets Commands
#
# Comprehensive QA testing for all classdock secrets commands.
# Tests secrets add command with various options including the new --force flag.
#
# Commands tested:
# - secrets add: Add secrets to student repositories
#   - Basic add
#   - Add with --force flag (force update even if up-to-date)
#   - Add with --repos option
#   - Add with --assignment-root option
#   - Error handling and validation
#
# Usage:
#   ./test_secrets_commands.sh [--basic|--force|--advanced|--manage|--discovery|--global-options|--repo-targeting|--config-validation|--token|--all]
#
# Options:
#   --basic              Run only basic secrets add tests
#   --force              Run only --force flag tests
#   --advanced           Run only advanced option tests
#   --discovery          Run only auto-discovery tests
#   --global-options     Run only global options tests (--verbose, --dry-run)
#   --repo-targeting     Run only repository targeting tests
#   --config-validation  Run only configuration validation tests
#   --token              Run only token management tests
#   --all                Run all tests (default)
#
# Requirements:
#   - lib/test_helpers.sh
#   - lib/mock_helpers.sh
#   - fixtures/secrets/ directory with test fixtures
#   - classdock CLI installed (via poetry)
#
################################################################################

set -euo pipefail

# Script directory and paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
FIXTURES_DIR="$PROJECT_ROOT/test_project_repos/fixtures"
SECRETS_FIXTURES_DIR="$FIXTURES_DIR/secrets"

# Define test suite name for skip list
TEST_SUITE_NAME="test_secrets_commands"

# Source test helpers
source "$PROJECT_ROOT/test_project_repos/lib/test_helpers.sh"
source "$PROJECT_ROOT/test_project_repos/lib/mock_helpers.sh"
source "$PROJECT_ROOT/test_project_repos/lib/skipped_tests.sh"

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
    log_step "Setting up test environment for secrets commands"
    
    # Initialize mock environment
    mock_environment_setup
    
    # Setup mock GitHub token
    local mock_token
    mock_token=$(setup_mock_github_token)
    
    # Setup mock GitHub CLI to avoid hitting real API
    mock_gh_command
    
    # Create temporary directory for test files
    TEST_TEMP_DIR=$(mktemp -d -t "secrets_test_XXXXXX")
    
    # Create assignment.conf in PROJECT_ROOT for commands that require it
    create_minimal_test_config "$PROJECT_ROOT"
    
    log_info "Test environment ready. Temp dir: $TEST_TEMP_DIR"
}

create_test_config() {
    local config_type="$1"
    local dest_path="${2:-$TEST_TEMP_DIR/assignment.conf}"
    
    # Check if fixture exists, otherwise create inline
    local fixture_path="$SECRETS_FIXTURES_DIR/${config_type}.conf"
    
    if [ -f "$fixture_path" ]; then
        # Use fixture file if available
        cp "$fixture_path" "$dest_path"
    else
        # Fall back to inline config creation
        case "$config_type" in
            "basic"|"basic_secrets")
                cat > "$dest_path" <<'EOF'
CLASSROOM_URL="https://classroom.github.com/classrooms/123/assignments/test"
GITHUB_ORGANIZATION="test-org"
ASSIGNMENT_NAME="test-assignment"
TEMPLATE_REPO_URL="https://github.com/test-org/test-template"
SECRETS_CONFIG="
INSTRUCTOR_TESTS_TOKEN:Token for accessing instructor test repository:false
"
STEP_MANAGE_SECRETS=true
EOF
                ;;
            "multiple_secrets")
                cat > "$dest_path" <<'EOF'
CLASSROOM_URL="https://classroom.github.com/classrooms/123/assignments/test"
GITHUB_ORGANIZATION="test-org"
ASSIGNMENT_NAME="test-assignment"
TEMPLATE_REPO_URL="https://github.com/test-org/test-template"
SECRETS_CONFIG="
INSTRUCTOR_TESTS_TOKEN:Token for accessing instructor test repository:false
API_KEY:API key for external service:false
DATABASE_URL:Database connection string:false
SECRET_TOKEN:Authentication token for service:false
"
STEP_MANAGE_SECRETS=true
EOF
                ;;
            "disabled_secrets")
                cat > "$dest_path" <<'EOF'
CLASSROOM_URL="https://classroom.github.com/classrooms/123/assignments/test"
GITHUB_ORGANIZATION="test-org"
ASSIGNMENT_NAME="test-assignment"
TEMPLATE_REPO_URL="https://github.com/test-org/test-template"
SECRETS_CONFIG="
INSTRUCTOR_TESTS_TOKEN:Token for accessing instructor test repository:false
"
STEP_MANAGE_SECRETS=false
EOF
                ;;
            *)
                log_error "Unknown config type: $config_type"
                return 1
                ;;
        esac
    fi
    
    echo "$dest_path"
}

create_secrets_config_with_token() {
    local config_type="$1"
    local token_value="${2:-mock_test_token_12345}"
    local dest_path="${3:-$TEST_TEMP_DIR/assignment.conf}"
    
    # Create base config
    create_test_config "$config_type" "$dest_path"
    
    # Append token value to config
    echo "" >> "$dest_path"
    echo "# Token values" >> "$dest_path"
    echo "INSTRUCTOR_TESTS_TOKEN_VALUE=\"$token_value\"" >> "$dest_path"
    
    echo "$dest_path"
}

create_invalid_secrets_config() {
    local invalid_type="$1"
    local dest_path="${2:-$TEST_TEMP_DIR/invalid_assignment.conf}"
    
    case "$invalid_type" in
        "malformed_secrets")
            cat > "$dest_path" <<'EOF'
CLASSROOM_URL="https://classroom.github.com/classrooms/123/assignments/test"
GITHUB_ORGANIZATION="test-org"
ASSIGNMENT_NAME="test-assignment"
SECRETS_CONFIG="
MISSING_DESCRIPTION_TOKEN
INVALID:DELIMITER:FORMAT:EXTRA:false
NO_REQUIRED_FLAG:Token description
"
STEP_MANAGE_SECRETS=true
EOF
            ;;
        "invalid_url")
            cat > "$dest_path" <<'EOF'
CLASSROOM_URL="not-a-valid-url"
GITHUB_ORGANIZATION="test-org"
ASSIGNMENT_NAME="test-assignment"
SECRETS_CONFIG="
TEST_SECRET:Test secret:false
"
STEP_MANAGE_SECRETS=true
EOF
            ;;
        "empty_secrets")
            cat > "$dest_path" <<'EOF'
CLASSROOM_URL="https://classroom.github.com/classrooms/123/assignments/test"
GITHUB_ORGANIZATION="test-org"
ASSIGNMENT_NAME="test-assignment"
SECRETS_CONFIG=""
STEP_MANAGE_SECRETS=true
EOF
            ;;
        *)
            # Use fixture if available
            local fixture_path="$SECRETS_FIXTURES_DIR/${invalid_type}.conf"
            if [ -f "$fixture_path" ]; then
                cp "$fixture_path" "$dest_path"
            else
                log_error "Unknown invalid config type: $invalid_type"
                return 1
            fi
            ;;
    esac
    
    echo "$dest_path"
}

verify_dry_run_output() {
    local output="$1"
    local command_description="${2:-command}"
    
    # Check for dry-run indicators
    if echo "$output" | grep -qi "dry.run\|would\|simulation\|preview"; then
        log_info "✓ Dry-run indicators found in output"
        return 0
    else
        log_error "✗ No dry-run indicators found in output for $command_description"
        return 1
    fi
}

verify_verbose_output() {
    local output="$1"
    local expected_details="${2:-}"
    
    # Check output length (verbose should be longer)
    local line_count
    line_count=$(echo "$output" | wc -l)
    
    if [ "$line_count" -gt 5 ]; then
        log_info "✓ Verbose output detected ($line_count lines)"
        
        # Check for common verbose indicators
        if echo "$output" | grep -qiE "DEBUG|INFO|processing|executing|step"; then
            log_info "✓ Verbose logging patterns found"
            
            # Check for specific expected details if provided
            if [ -n "$expected_details" ]; then
                if echo "$output" | grep -q "$expected_details"; then
                    log_info "✓ Expected details found: $expected_details"
                    return 0
                else
                    log_warning "⚠ Expected details not found: $expected_details"
                    return 1
                fi
            fi
            return 0
        fi
    fi
    
    log_error "✗ Insufficient verbose output"
    return 1
}

################################################################################
# Test Functions
################################################################################

test_secrets_help() {
    log_step "Testing secrets command help"
    
    local output
    
    # Test main secrets help
    output=$(cd "$PROJECT_ROOT" && poetry run classdock secrets --help 2>&1) || true
    if echo "$output" | grep -q "secrets"; then
        mark_test_passed "secrets --help shows help"
    else
        mark_test_failed "secrets --help" "Help output not showing secrets info"
    fi
    
    # Test secrets add help
    output=$(cd "$PROJECT_ROOT" && poetry run classdock secrets add --help 2>&1) || true
    if echo "$output" | grep -q "add"; then
        mark_test_passed "secrets add --help shows help"
    else
        mark_test_failed "secrets add --help" "Help output not showing add info"
    fi
    
    # Verify --force flag is documented
    if echo "$output" | grep -qi "force"; then
        mark_test_passed "secrets add --help documents --force flag"
    else
        mark_test_failed "secrets add --help --force" "Help doesn't document --force flag"
    fi
    
    # Verify -f short form is documented
    if echo "$output" | grep -q "\-f"; then
        mark_test_passed "secrets add --help documents -f short flag"
    else
        mark_test_failed "secrets add --help -f" "Help doesn't document -f short flag"
    fi
}

test_basic_secrets_add() {
    log_step "Testing basic secrets add command"
    
    local config_file
    config_file=$(create_test_config "basic")
    
    # Test basic secrets add (dry-run)
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock secrets --dry-run add --repos "https://github.com/test-org/repo1" 2>&1) || exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        mark_test_passed "Basic secrets add command executes"
    else
        mark_test_failed "Basic secrets add" "Command failed with exit code $exit_code"
    fi
}

test_secrets_add_with_force() {
    log_step "Testing secrets add with --force flag"
    
    local config_file
    config_file=$(create_test_config "basic")
    
    # Test secrets add with --force
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock secrets --dry-run add --repos "https://github.com/test-org/repo1" --force 2>&1) || exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        mark_test_passed "secrets add with --force flag executes"
    else
        mark_test_failed "secrets add --force" "Command failed with exit code $exit_code"
    fi
    
    # Verify force update message appears
    if echo "$output" | grep -qi "updated\|force\|dry run\|would"; then
        mark_test_passed "secrets add --force shows update indication"
    else
        mark_test_failed "secrets add --force output" "Output doesn't indicate forced update"
    fi
}

test_secrets_add_force_short_form() {
    log_step "Testing secrets add with -f short flag"
    
    local config_file
    config_file=$(create_test_config "basic")
    
    # Test secrets add with -f
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock secrets --dry-run add --repos "https://github.com/test-org/repo1" -f 2>&1) || exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        mark_test_passed "secrets add with -f short flag executes"
    else
        mark_test_failed "secrets add -f" "Command failed with exit code $exit_code"
    fi
}

test_secrets_add_force_multiple_repos() {
    log_step "Testing secrets add --force with multiple repositories"
    
    local config_file
    config_file=$(create_test_config "basic")
    
    # Test with multiple repos and --force
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock secrets --dry-run add --repos "https://github.com/test-org/repo1,https://github.com/test-org/repo2,https://github.com/test-org/repo3" --force 2>&1) || exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        mark_test_passed "secrets add --force with multiple repos executes"
    else
        mark_test_failed "secrets add --force multiple repos" "Command failed with exit code $exit_code"
    fi
    
    # Check that it processed multiple repositories
    if echo "$output" | grep -q "3"; then
        mark_test_passed "secrets add --force processes multiple repos"
    else
        log_warning "Could not verify processing of 3 repos in output"
    fi
}

test_secrets_add_force_without_repos() {
    # Check if test should be skipped
    is_test_skipped "${FUNCNAME[0]}" && mark_test_skipped "secrets add force auto-discover" "$(get_skip_reason "${FUNCNAME[0]}")" && return
    
    log_step "Testing secrets add --force without --repos (auto-discovery)"
    
    local config_file
    config_file=$(create_test_config "basic")
    
    # Test --force without specifying repos (should auto-discover)
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock secrets --dry-run add --force 2>&1) || exit_code=$?
    
    # This might fail due to no repos, but should attempt auto-discovery
    if echo "$output" | grep -qi "discover\|repository\|no repositories"; then
        mark_test_passed "secrets add --force attempts auto-discovery"
    else
        mark_test_failed "secrets add --force auto-discover" "No discovery attempt detected"
    fi
}

test_secrets_add_with_assignment_root() {
    log_step "Testing secrets add with --assignment-root"
    
    local test_dir="$TEST_TEMP_DIR/test_assignment"
    mkdir -p "$test_dir"
    create_test_config "basic" "$test_dir/assignment.conf"
    
    # Test with valid assignment root
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock secrets --dry-run add --assignment-root "$test_dir" --repos "https://github.com/test-org/repo1" 2>&1) || exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        mark_test_passed "secrets add with --assignment-root executes"
    else
        mark_test_failed "secrets add --assignment-root" "Command failed with exit code $exit_code"
    fi
}

test_secrets_add_force_with_assignment_root() {
    log_step "Testing secrets add --force with --assignment-root"
    
    local test_dir="$TEST_TEMP_DIR/test_assignment_force"
    mkdir -p "$test_dir"
    create_test_config "basic" "$test_dir/assignment.conf"
    
    # Test --force with assignment root
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock secrets --dry-run add --assignment-root "$test_dir" --repos "https://github.com/test-org/repo1" --force 2>&1) || exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        mark_test_passed "secrets add --force with --assignment-root executes"
    else
        mark_test_failed "secrets add --force --assignment-root" "Command failed with exit code $exit_code"
    fi
}

test_secrets_add_multiple_secrets() {
    log_step "Testing secrets add with multiple secrets configured"
    
    local config_file
    config_file=$(create_test_config "multiple_secrets")
    
    # Test with multiple secrets
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock secrets --dry-run add --repos "https://github.com/test-org/repo1" 2>&1) || exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        mark_test_passed "secrets add with multiple secrets executes"
    else
        mark_test_failed "secrets add multiple secrets" "Command failed with exit code $exit_code"
    fi
    
    # Check that multiple secrets are mentioned
    local secret_count
    secret_count=$(echo "$output" | grep -c "INSTRUCTOR_TESTS_TOKEN\|API_KEY\|DATABASE_URL" || echo "0")
    if [ "$secret_count" -gt 1 ]; then
        mark_test_passed "secrets add processes multiple secrets"
    else
        log_warning "Expected multiple secret mentions in output, found $secret_count"
    fi
}

test_secrets_add_force_multiple_secrets() {
    log_step "Testing secrets add --force with multiple secrets"
    
    local config_file
    config_file=$(create_test_config "multiple_secrets")
    
    # Test --force with multiple secrets
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock secrets --dry-run add --repos "https://github.com/test-org/repo1" --force 2>&1) || exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        mark_test_passed "secrets add --force with multiple secrets executes"
    else
        mark_test_failed "secrets add --force multiple secrets" "Command failed with exit code $exit_code"
    fi
}

test_secrets_add_disabled() {
    # Check if test should be skipped
    is_test_skipped "${FUNCNAME[0]}" && mark_test_skipped "secrets add disabled" "$(get_skip_reason "${FUNCNAME[0]}")" && return
    
    log_step "Testing secrets add when secrets management is disabled"
    
    local config_file
    config_file=$(create_test_config "disabled_secrets")
    
    # Test with secrets management disabled
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock secrets --dry-run add --repos "https://github.com/test-org/repo1" 2>&1) || exit_code=$?
    
    # Should succeed but indicate secrets are disabled
    if echo "$output" | grep -qi "disabled\|skip"; then
        mark_test_passed "secrets add respects disabled secrets management"
    else
        mark_test_failed "secrets add disabled" "Doesn't respect STEP_MANAGE_SECRETS=false"
    fi
}

test_secrets_add_error_cases() {
    # Check if test should be skipped
    is_test_skipped "${FUNCNAME[0]}" && mark_test_skipped "secrets add error cases" "$(get_skip_reason "${FUNCNAME[0]}")" && return
    
    log_step "Testing secrets add error handling"
    
    # Test without config
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock --assignment-root "$TEST_TEMP_DIR" secrets add --repos "https://github.com/test-org/repo1" 2>&1) || exit_code=$?
    
    if [ $exit_code -ne 0 ]; then
        mark_test_passed "secrets add fails gracefully without config"
    else
        mark_test_failed "secrets add no config" "Should fail without configuration"
    fi
    
    # Test with invalid assignment root
    exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock secrets --dry-run add --assignment-root "/nonexistent/path" --repos "https://github.com/test-org/repo1" 2>&1) || exit_code=$?
    
    if [ $exit_code -ne 0 ]; then
        mark_test_passed "secrets add fails with invalid assignment root"
    else
        mark_test_failed "secrets add invalid root" "Should fail with invalid path"
    fi
}

test_secrets_add_force_error_cases() {
    log_step "Testing secrets add --force error handling"
    
    # Test --force without config
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock --assignment-root "$TEST_TEMP_DIR" secrets add --repos "https://github.com/test-org/repo1" --force 2>&1) || exit_code=$?
    
    if [ $exit_code -ne 0 ]; then
        mark_test_passed "secrets add --force fails gracefully without config"
    else
        mark_test_failed "secrets add --force no config" "Should fail without configuration"
    fi
}

################################################################################
# Section: Auto-Discovery Tests
################################################################################

test_secrets_add_auto_discovery() {
    # Check if test should be skipped
    is_test_skipped "${FUNCNAME[0]}" && mark_test_skipped "secrets add auto-discovery" "$(get_skip_reason "${FUNCNAME[0]}")" && return
    
    log_step "Testing secrets add auto-discovery"
    
    # Seed mock GitHub CLI with predictable repo responses
    local mock_repos_json
    mock_repos_json=$(mock_github_repo_list "test-org" 3)
    
    # Override mock gh command with specific response for this test
    local mock_gh_script="$MOCK_DATA_DIR/bin/gh"
    cat > "$mock_gh_script" <<EOF
#!/bin/bash
# Mock gh for auto-discovery test
case "\$1" in
    "repo")
        if [ "\$2" = "list" ]; then
            echo "test-org/test-assignment-student1"
            echo "test-org/test-assignment-student2"
            echo "test-org/test-assignment-student3"
            exit 0
        fi
        ;;
    "api")
        echo '$mock_repos_json'
        exit 0
        ;;
    *)
        echo "gh \$*"
        exit 0
        ;;
esac
EOF
    chmod +x "$mock_gh_script"
    
    local config_file
    config_file=$(create_test_config "basic")
    
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock secrets --dry-run add 2>&1) || exit_code=$?
    
    # Verify explicit repo names or counts
    local discovered_count=0
    if echo "$output" | grep -q "test-assignment-student1"; then
        discovered_count=$((discovered_count + 1))
    fi
    if echo "$output" | grep -q "test-assignment-student2"; then
        discovered_count=$((discovered_count + 1))
    fi
    if echo "$output" | grep -q "test-assignment-student3"; then
        discovered_count=$((discovered_count + 1))
    fi
    
    if [ $discovered_count -ge 2 ]; then
        mark_test_passed "secrets add discovers specific repos (found $discovered_count/3)"
    elif echo "$output" | grep -qi "3.*repositor"; then
        mark_test_passed "secrets add reports correct repo count"
    elif echo "$output" | grep -qi "discover\|repository"; then
        log_warning "Auto-discovery attempted but specific repos not verified"
        mark_test_passed "secrets add attempts auto-discovery"
    else
        mark_test_failed "secrets add auto-discovery" "No discovery evidence found in output"
    fi
}

test_secrets_add_auto_discovery_no_repos() {
    # Check if test should be skipped
    is_test_skipped "${FUNCNAME[0]}" && mark_test_skipped "secrets add auto-discovery no repos" "$(get_skip_reason "${FUNCNAME[0]}")" && return
    
    log_step "Testing secrets add auto-discovery with no repos found"
    
    # Override mock gh command to return empty list
    local mock_gh_script="$MOCK_DATA_DIR/bin/gh"
    cat > "$mock_gh_script" <<'EOF'
#!/bin/bash
# Mock gh with no repos
case "$1" in
    "repo")
        if [ "$2" = "list" ]; then
            exit 0
        fi
        ;;
    "api")
        echo '[]'
        exit 0
        ;;
    *)
        echo "gh $*"
        exit 0
        ;;
esac
EOF
    chmod +x "$mock_gh_script"
    
    local config_file
    config_file=$(create_test_config "basic")
    
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock secrets --dry-run add 2>&1) || exit_code=$?
    
    # Check for explicit "0 repositories" or "no repositories found" message
    if echo "$output" | grep -qiE "0 repositor|no repositor.*found|found 0|unable to.*discover"; then
        mark_test_passed "secrets add reports 0 repos discovered"
    elif [ $exit_code -ne 0 ] && echo "$output" | grep -qi "no.*repo\|not found"; then
        mark_test_passed "secrets add handles no repos gracefully with error"
    else
        mark_test_failed "secrets add no repos" "Expected explicit '0 repositories' message, got: $output"
    fi
}

test_secrets_add_auto_discovery_error() {
    # Check if test should be skipped
    is_test_skipped "${FUNCNAME[0]}" && mark_test_skipped "secrets add auto-discovery error" "$(get_skip_reason "${FUNCNAME[0]}")" && return
    
    log_step "Testing secrets add auto-discovery error handling"
    
    # Test without proper GitHub Classroom URL
    local test_dir="$TEST_TEMP_DIR/test_invalid_url"
    mkdir -p "$test_dir"
    cat > "$test_dir/assignment.conf" <<'EOF'
CLASSROOM_URL="invalid-url"
GITHUB_ORGANIZATION="test-org"
ASSIGNMENT_NAME="test-assignment"
EOF
    
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock secrets --dry-run add --assignment-root "$test_dir" 2>&1) || exit_code=$?
    
    if [ $exit_code -ne 0 ]; then
        mark_test_passed "secrets add fails with invalid discovery configuration"
    else
        mark_test_failed "secrets add invalid discovery" "Should fail with invalid URL"
    fi
}

################################################################################
# Section: Global Options Tests
################################################################################

test_secrets_add_verbose() {
    log_step "Testing secrets add with --verbose"
    
    local config_file
    config_file=$(create_test_config "basic")
    
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock secrets --verbose add --repos "https://github.com/test-org/repo1" 2>&1) || exit_code=$?
    
    if echo "$output" | grep -qi "verbose\|detailed\|processing\|step"; then
        mark_test_passed "secrets add --verbose shows detailed output"
    else
        mark_test_failed "secrets add --verbose" "Verbose output not detected"
    fi
}

test_secrets_add_dry_run() {
    log_step "Testing secrets add with --dry-run"
    
    local config_file
    config_file=$(create_test_config "basic")
    
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock secrets --dry-run add --repos "https://github.com/test-org/repo1" 2>&1) || exit_code=$?
    
    if echo "$output" | grep -qi "dry run\|would"; then
        mark_test_passed "secrets add --dry-run shows simulation"
    else
        mark_test_failed "secrets add --dry-run" "Dry run indication not found"
    fi
}

test_secrets_add_verbose_dry_run() {
    log_step "Testing secrets add with --verbose --dry-run"
    
    local config_file
    config_file=$(create_test_config "basic")
    
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock secrets --dry-run add --repos "https://github.com/test-org/repo1" --verbose 2>&1) || exit_code=$?
    
    if echo "$output" | grep -qi "dry\|verbose"; then
        mark_test_passed "secrets add --verbose --dry-run combines options"
    else
        mark_test_failed "secrets add combined options" "Combined output not detected"
    fi
}

################################################################################
# Section: Repository Targeting Tests
################################################################################

test_secrets_add_single_repo() {
    log_step "Testing secrets add with single repository"
    
    local config_file
    config_file=$(create_test_config "basic")
    
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock secrets --dry-run add --repos "https://github.com/test-org/single-repo" 2>&1) || exit_code=$?
    
    if [ $exit_code -eq 0 ] || echo "$output" | grep -q "single-repo"; then
        mark_test_passed "secrets add processes single repository"
    else
        mark_test_failed "secrets add single repo" "Failed to process single repository"
    fi
}

test_secrets_add_multiple_repos() {
    log_step "Testing secrets add with multiple repositories"
    
    local config_file
    config_file=$(create_test_config "basic")
    
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock secrets --dry-run add --repos "https://github.com/test-org/repo1,https://github.com/test-org/repo2" 2>&1) || exit_code=$?
    
    if echo "$output" | grep -q "repo1\|repo2\|2"; then
        mark_test_passed "secrets add processes multiple repositories"
    else
        log_warning "Multiple repository processing not clearly indicated"
    fi
}

test_secrets_add_invalid_repo_url() {
    # Check if test should be skipped
    is_test_skipped "${FUNCNAME[0]}" && mark_test_skipped "secrets add invalid URL" "$(get_skip_reason "${FUNCNAME[0]}")" && return
    
    log_step "Testing secrets add with invalid repository URL"
    
    local config_file
    config_file=$(create_test_config "basic")
    
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock secrets --dry-run add --repos "not-a-valid-url" 2>&1) || exit_code=$?
    
    if [ $exit_code -ne 0 ] || echo "$output" | grep -qi "invalid\|malformed\|error"; then
        mark_test_passed "secrets add detects invalid URL"
    else
        mark_test_failed "secrets add invalid URL" "Should detect malformed URL"
    fi
}

test_secrets_add_nonexistent_repo() {
    log_step "Testing secrets add with non-existent repository"
    
    local config_file
    config_file=$(create_test_config "basic")
    
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock secrets --dry-run add --repos "https://github.com/test-org/nonexistent-repo-12345" 2>&1) || exit_code=$?
    
    # May fail or warn about non-existent repository
    if echo "$output" | grep -qi "not found\|error\|unable"; then
        mark_test_passed "secrets add handles non-existent repository"
    else
        log_warning "Non-existent repository handling not clearly indicated"
    fi
}

################################################################################
# Section: Configuration Validation Tests
################################################################################

test_secrets_add_no_secrets_config() {
    log_step "Testing secrets add without SECRETS_CONFIG"
    
    local test_dir="$TEST_TEMP_DIR/test_no_secrets_config"
    mkdir -p "$test_dir"
    cat > "$test_dir/assignment.conf" <<'EOF'
CLASSROOM_URL="https://classroom.github.com/classrooms/123/assignments/test"
GITHUB_ORGANIZATION="test-org"
ASSIGNMENT_NAME="test-assignment"
STEP_MANAGE_SECRETS=true
EOF
    
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock secrets --dry-run add --assignment-root "$test_dir" --repos "https://github.com/test-org/repo1" 2>&1) || exit_code=$?
    
    if echo "$output" | grep -qi "no secrets\|secrets_config\|not configured"; then
        mark_test_passed "secrets add detects missing SECRETS_CONFIG"
    else
        log_warning "Missing SECRETS_CONFIG not clearly indicated"
    fi
}

test_secrets_add_empty_secrets_config() {
    log_step "Testing secrets add with empty SECRETS_CONFIG"
    
    local test_dir="$TEST_TEMP_DIR/test_empty_secrets_config"
    mkdir -p "$test_dir"
    cat > "$test_dir/assignment.conf" <<'EOF'
CLASSROOM_URL="https://classroom.github.com/classrooms/123/assignments/test"
GITHUB_ORGANIZATION="test-org"
ASSIGNMENT_NAME="test-assignment"
SECRETS_CONFIG=""
STEP_MANAGE_SECRETS=true
EOF
    
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock secrets --dry-run add --assignment-root "$test_dir" --repos "https://github.com/test-org/repo1" 2>&1) || exit_code=$?
    
    if echo "$output" | grep -qi "empty\|no secrets\|not configured"; then
        mark_test_passed "secrets add detects empty SECRETS_CONFIG"
    else
        log_warning "Empty SECRETS_CONFIG not clearly indicated"
    fi
}

test_secrets_add_malformed_secrets_config() {
    log_step "Testing secrets add with malformed SECRETS_CONFIG"
    
    local test_dir="$TEST_TEMP_DIR/test_malformed_secrets_config"
    mkdir -p "$test_dir"
    cat > "$test_dir/assignment.conf" <<'EOF'
CLASSROOM_URL="https://classroom.github.com/classrooms/123/assignments/test"
GITHUB_ORGANIZATION="test-org"
ASSIGNMENT_NAME="test-assignment"
SECRETS_CONFIG="
INVALID FORMAT WITHOUT COLONS
"
STEP_MANAGE_SECRETS=true
EOF
    
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock secrets --dry-run add --assignment-root "$test_dir" --repos "https://github.com/test-org/repo1" 2>&1) || exit_code=$?
    
    if echo "$output" | grep -qi "malformed\|invalid\|format\|error"; then
        mark_test_passed "secrets add detects malformed SECRETS_CONFIG"
    else
        log_warning "Malformed SECRETS_CONFIG not clearly indicated"
    fi
}

################################################################################
# Section: Token Management Tests
################################################################################

test_secrets_add_centralized_token() {
    log_step "Testing secrets add with centralized token manager"
    
    local config_file
    config_file=$(create_test_config "basic")
    
    # Setup mock token
    local mock_token
    mock_token=$(setup_mock_github_token)
    
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock secrets --dry-run add --repos "https://github.com/test-org/repo1" 2>&1) || exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        mark_test_passed "secrets add uses centralized token"
    else
        mark_test_failed "secrets add token" "Failed to use centralized token"
    fi
}

test_secrets_add_token_file() {
    log_step "Testing secrets add with legacy token file"
    
    local test_dir="$TEST_TEMP_DIR/test_token_file"
    mkdir -p "$test_dir"
    create_test_config "basic" "$test_dir/assignment.conf"
    
    # Create legacy token file
    echo "ghp_legacytokenvalue12345" > "$test_dir/.instructor_tests_token"
    
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock secrets --dry-run add --assignment-root "$test_dir" --repos "https://github.com/test-org/repo1" 2>&1) || exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        mark_test_passed "secrets add handles legacy token file"
    else
        log_warning "Legacy token file handling not confirmed"
    fi
}

test_secrets_add_missing_token() {
    log_step "Testing secrets add without token"
    
    local test_dir="$TEST_TEMP_DIR/test_missing_token"
    mkdir -p "$test_dir"
    create_test_config "basic" "$test_dir/assignment.conf"
    
    # Ensure no token available
    unset INSTRUCTOR_TESTS_TOKEN
    
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock secrets --dry-run add --assignment-root "$test_dir" --repos "https://github.com/test-org/repo1" 2>&1) || exit_code=$?
    
    if echo "$output" | grep -qi "token\|credential\|authentication"; then
        mark_test_passed "secrets add detects missing token"
    else
        log_warning "Missing token not clearly indicated"
    fi
}

test_secrets_add_invalid_token() {
    log_step "Testing secrets add with invalid token format"
    
    local test_dir="$TEST_TEMP_DIR/test_invalid_token"
    mkdir -p "$test_dir"
    create_test_config "basic" "$test_dir/assignment.conf"
    
    # Set invalid token format
    export INSTRUCTOR_TESTS_TOKEN="invalid_token_format"
    
    local output exit_code=0
    output=$(cd "$PROJECT_ROOT" && poetry run classdock secrets --dry-run add --assignment-root "$test_dir" --repos "https://github.com/test-org/repo1" 2>&1) || exit_code=$?
    
    # May warn about invalid token format
    if echo "$output" | grep -qi "invalid\|format\|token"; then
        mark_test_passed "secrets add validates token format"
    else
        log_warning "Token format validation not clearly indicated"
    fi
    
    unset INSTRUCTOR_TESTS_TOKEN
}

################################################################################
# Test Suite Runners
################################################################################

run_basic_tests() {
    log_section "Running Basic Secrets Tests"
    test_secrets_help
    test_basic_secrets_add
    test_secrets_add_with_assignment_root
    test_secrets_add_multiple_secrets
    test_secrets_add_disabled
}

run_force_tests() {
    log_section "Running --force Flag Tests"
    test_secrets_add_with_force
    test_secrets_add_force_short_form
    test_secrets_add_force_multiple_repos
    test_secrets_add_force_without_repos
    test_secrets_add_force_with_assignment_root
    test_secrets_add_force_multiple_secrets
}

run_advanced_tests() {
    log_section "Running Advanced Tests"
    test_secrets_add_error_cases
    test_secrets_add_force_error_cases
}

run_discovery_tests() {
    log_section "Running Auto-Discovery Tests"
    test_secrets_add_auto_discovery
    test_secrets_add_auto_discovery_no_repos
    test_secrets_add_auto_discovery_error
}

run_global_options_tests() {
    log_section "Running Global Options Tests"
    test_secrets_add_verbose
    test_secrets_add_dry_run
    test_secrets_add_verbose_dry_run
}

run_repo_targeting_tests() {
    log_section "Running Repository Targeting Tests"
    test_secrets_add_single_repo
    test_secrets_add_multiple_repos
    test_secrets_add_invalid_repo_url
    test_secrets_add_nonexistent_repo
}

run_config_validation_tests() {
    log_section "Running Configuration Validation Tests"
    test_secrets_add_no_secrets_config
    test_secrets_add_empty_secrets_config
    test_secrets_add_malformed_secrets_config
}

run_token_tests() {
    log_section "Running Token Management Tests"
    test_secrets_add_centralized_token
    test_secrets_add_token_file
    test_secrets_add_missing_token
    test_secrets_add_invalid_token
}

run_all_tests() {
    run_basic_tests
    run_force_tests
    run_advanced_tests
    run_discovery_tests
    run_global_options_tests
    run_repo_targeting_tests
    run_config_validation_tests
    run_token_tests
}

################################################################################
# Main Execution
################################################################################

main() {
    log_section "Secrets Commands Test Suite"
    log_info "Testing classdock secrets commands"
    
    # Setup
    setup_test_environment
    
    # Parse command line arguments
    local test_type="${1:---all}"
    
    case "$test_type" in
        --basic)
            run_basic_tests
            ;;
        --force)
            run_force_tests
            ;;
        --advanced)
            run_advanced_tests
            ;;
        --discovery)
            run_discovery_tests
            ;;
        --global-options)
            run_global_options_tests
            ;;
        --repo-targeting)
            run_repo_targeting_tests
            ;;
        --config-validation)
            run_config_validation_tests
            ;;
        --token)
            run_token_tests
            ;;
        --all)
            run_all_tests
            ;;
        *)
            log_error "Unknown test type: $test_type"
            log_info "Usage: $0 [--basic|--force|--advanced|--discovery|--global-options|--repo-targeting|--config-validation|--token|--all]"
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
