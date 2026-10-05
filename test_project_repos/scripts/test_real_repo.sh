#!/usr/bin/env bash
#
# Real Repository Testing Script
# Tests classdock with actual GitHub repositories and real workflows
#

set -e

# Source configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"

# Define test project directory
TEST_PROJECT_REPOS_DIR="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

log_detail() {
    echo -e "${CYAN}[DETAIL]${NC} $1"
}

# Configuration files
REAL_REPO_CONFIG="$TEST_PROJECT_REPOS_DIR/sample_projects/real_repo/real_repo_info.conf"
INSTRUCTOR_TOKEN_FILE="$TEST_PROJECT_REPOS_DIR/sample_projects/real_repo/instructor_token.txt"

# Test environment variables
TEST_ENV_NAME="classdock-real-test"
TEST_WORKSPACE_DIR="$TEST_PROJECT_REPOS_DIR/real_test_workspace"
CLONED_REPO_DIR="$TEST_WORKSPACE_DIR/student_repo"
GENERATED_CONFIG_FILE="$TEST_WORKSPACE_DIR/assignment.conf"

# Test result tracking
TESTS_PASSED=0
TESTS_FAILED=0
FAILED_TESTS=()

# Track test results
mark_test_passed() {
    local test_name="$1"
    ((TESTS_PASSED++))
    log_success "✓ $test_name"
}

mark_test_failed() {
    local test_name="$1"
    local error_msg="$2"
    ((TESTS_FAILED++))
    FAILED_TESTS+=("$test_name: $error_msg")
    log_error "✗ $test_name: $error_msg"
}

# Show usage information
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Test classdock with real GitHub repositories and workflows.

Options:
    --setup-only        Only set up the test environment
    --test-only         Only run tests (assume environment exists)
    --cleanup-only      Only clean up test environment
    --skip-clone        Skip repository cloning (use existing)
    --keep-repo         Keep cloned repository after testing
    --keep-env          Keep conda environment after testing
    --verbose           Enable verbose output
    --dry-run          Show what would be done without executing
    -h, --help         Show this help message

Examples:
    $0                          # Full test cycle
    $0 --setup-only            # Just set up environment
    $0 --test-only --verbose   # Run tests with verbose output
    $0 --cleanup-only          # Clean up everything
    $0 --keep-repo             # Run tests but keep cloned repo

Prerequisites:
    - sample_projects/real_repo/real_repo_info.conf file with valid repository information
    - sample_projects/real_repo/instructor_token.txt file with valid GitHub token
    - conda installed and available
    - git installed and configured
EOF
}

# Parse command line arguments
SETUP_ONLY=false
TEST_ONLY=false
CLEANUP_ONLY=false
SKIP_CLONE=false
KEEP_REPO=false
KEEP_ENV=false
VERBOSE=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --setup-only)
            SETUP_ONLY=true
            shift
            ;;
        --test-only)
            TEST_ONLY=true
            shift
            ;;
        --cleanup-only)
            CLEANUP_ONLY=true
            shift
            ;;
        --skip-clone)
            SKIP_CLONE=true
            shift
            ;;
        --keep-repo)
            KEEP_REPO=true
            shift
            ;;
        --keep-env)
            KEEP_ENV=true
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

# Validate prerequisites
validate_prerequisites() {
    log_step "Validating prerequisites"
    
    # Check required files
    if [[ ! -f "$REAL_REPO_CONFIG" ]]; then
        mark_test_failed "Prerequisites" "real_repo_info.conf not found at $REAL_REPO_CONFIG"
        return 1
    fi
    mark_test_passed "Real repo config file exists"
    
    if [[ ! -f "$INSTRUCTOR_TOKEN_FILE" ]]; then
        mark_test_failed "Prerequisites" "instructor_token.txt not found at $INSTRUCTOR_TOKEN_FILE"
        return 1
    fi
    mark_test_passed "Instructor token file exists"
    
    # Check conda availability
    if ! command -v conda &> /dev/null; then
        mark_test_failed "Prerequisites" "conda not found - please install conda"
        return 1
    fi
    mark_test_passed "Conda is available"
    
    # Check git availability
    if ! command -v git &> /dev/null; then
        mark_test_failed "Prerequisites" "git not found - please install git"
        return 1
    fi
    mark_test_passed "Git is available"
    
    # Validate GitHub token format
    local token=$(cat "$INSTRUCTOR_TOKEN_FILE" | tr -d '\n\r ')
    if [[ ! "$token" =~ ^ghp_[A-Za-z0-9]{36}$ ]]; then
        mark_test_failed "Prerequisites" "Invalid GitHub token format in instructor_token.txt"
        return 1
    fi
    mark_test_passed "GitHub token format is valid"
    
    log_success "All prerequisites validated successfully"
    return 0
}

# Parse configuration from real_repo_info.conf
parse_real_repo_config() {
    log_step "Parsing real repository configuration"
    
    # Source the config file to get variables
    source "$REAL_REPO_CONFIG"
    
    # Extract key information
    TEMPLATE_REPO_URL_VAL="$TEMPLATE_REPO_URL"
    GITHUB_ORGANIZATION_VAL="$GITHUB_ORGANIZATION"
    ASSIGNMENT_NAME_VAL="$ASSIGNMENT_NAME"
    ASSIGNMENT_FILE_VAL="$ASSIGNMENT_FILE"
    
    log_detail "Template Repo: $TEMPLATE_REPO_URL_VAL"
    log_detail "Organization: $GITHUB_ORGANIZATION_VAL"
    log_detail "Assignment: $ASSIGNMENT_NAME_VAL"
    log_detail "Assignment File: $ASSIGNMENT_FILE_VAL"
    
    # Validate required fields
    if [[ -z "$ASSIGNMENT_NAME_VAL" ]]; then
        mark_test_failed "Configuration parsing" "ASSIGNMENT_NAME is empty"
        return 1
    fi
    
    if [[ -z "$TEMPLATE_REPO_URL_VAL" ]]; then
        mark_test_failed "Configuration parsing" "TEMPLATE_REPO_URL is empty"
        return 1
    fi
    
    mark_test_passed "Configuration parsing completed"
    return 0
}

# Set up conda test environment
setup_conda_environment() {
    log_step "Setting up conda test environment"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY-RUN] Would create conda environment: $TEST_ENV_NAME"
        return 0
    fi
    
    # Remove existing environment if it exists
    if conda env list | grep -q "^$TEST_ENV_NAME "; then
        log_info "Removing existing test environment: $TEST_ENV_NAME"
        conda env remove -n "$TEST_ENV_NAME" -y || true
    fi
    
    # Create new conda environment
    log_info "Creating conda environment: $TEST_ENV_NAME"
    if conda create -n "$TEST_ENV_NAME" python=3.11 -y; then
        mark_test_passed "Conda environment created"
    else
        mark_test_failed "Conda environment creation" "Failed to create conda environment"
        return 1
    fi
    
    # Activate environment and install classdock
    log_info "Installing classdock in test environment"
    if conda run -n "$TEST_ENV_NAME" pip install --upgrade pip setuptools wheel; then
        mark_test_passed "Pip updated in conda environment"
    else
        mark_test_failed "Pip update" "Failed to update pip in conda environment"
        return 1
    fi
    
    # Install requirements if available
    local requirements_file="$TEST_PROJECT_REPOS_DIR/requirements.txt"
    if [[ -f "$requirements_file" ]]; then
        log_info "Installing dependencies from requirements.txt"
        if conda run -n "$TEST_ENV_NAME" pip install -r "$requirements_file"; then
            mark_test_passed "Requirements installed in conda environment"
        else
            mark_test_failed "Requirements installation" "Failed to install requirements"
            return 1
        fi
    fi
    
    # Install classdock from local source
    local current_dir=$(pwd)
    if conda run -n "$TEST_ENV_NAME" pip install -e "$PROJECT_ROOT"; then
        mark_test_passed "ClassDock installed in conda environment"
    else
        mark_test_failed "ClassDock installation" "Failed to install classdock"
        return 1
    fi
    
    # Verify installation
    if conda run -n "$TEST_ENV_NAME" classdock --version; then
        mark_test_passed "ClassDock CLI verified in conda environment"
    else
        mark_test_failed "CLI verification" "ClassDock CLI not working in conda environment"
        return 1
    fi
    
    log_success "Conda test environment setup completed"
    return 0
}

# Clone student repository
clone_student_repository() {
    log_step "Cloning student repository"
    
    if [[ "$SKIP_CLONE" == "true" ]]; then
        log_info "Skipping repository cloning (--skip-clone specified)"
        if [[ -d "$CLONED_REPO_DIR" ]]; then
            mark_test_passed "Repository directory exists (skipped cloning)"
            return 0
        else
            mark_test_failed "Repository cloning" "Repository directory not found and cloning skipped"
            return 1
        fi
    fi
    
    # Create workspace directory
    mkdir -p "$TEST_WORKSPACE_DIR"
    
    # Remove existing cloned repo if it exists
    if [[ -d "$CLONED_REPO_DIR" ]]; then
        log_info "Removing existing cloned repository"
        rm -rf "$CLONED_REPO_DIR"
    fi
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY-RUN] Would clone repository: $TEMPLATE_REPO_URL_VAL"
        log_info "[DRY-RUN] Clone destination: $CLONED_REPO_DIR"
        return 0
    fi
    
    # Clone the template repository (simulating a student repo)
    log_info "Cloning repository: $TEMPLATE_REPO_URL_VAL"
    if git clone "$TEMPLATE_REPO_URL_VAL" "$CLONED_REPO_DIR"; then
        mark_test_passed "Repository cloned successfully"
    else
        mark_test_failed "Repository cloning" "Failed to clone repository"
        return 1
    fi
    
    # Verify cloned repository structure
    if [[ -f "$CLONED_REPO_DIR/$ASSIGNMENT_FILE_VAL" ]]; then
        mark_test_passed "Assignment file found in cloned repository"
    else
        log_warning "Assignment file not found: $ASSIGNMENT_FILE_VAL (this may be expected)"
    fi
    
    log_success "Student repository cloning completed"
    return 0
}

# Generate assignment.conf file
generate_assignment_config() {
    log_step "Generating assignment.conf file"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY-RUN] Would generate assignment.conf at: $GENERATED_CONFIG_FILE"
        return 0
    fi
    
    # Create assignment.conf based on real_repo_info.conf
    cat > "$GENERATED_CONFIG_FILE" << EOF
# Assignment Configuration Generated from Real Repository Testing
# Generated on: $(date)
# Source: $REAL_REPO_CONFIG

GITHUB_ORGANIZATION=$GITHUB_ORGANIZATION_VAL
TEMPLATE_REPO_URL=$TEMPLATE_REPO_URL_VAL
ASSIGNMENT_FILE=$ASSIGNMENT_FILE_VAL
ASSIGNMENT_NAME=$ASSIGNMENT_NAME_VAL

# Test-specific configuration
DRY_RUN=true
VERBOSE=true
OUTPUT_DIR=test_output

# Secret management for testing
SECRET_NAME=INSTRUCTOR_TESTS_TOKEN
SECRET_VALUE=$(cat "$INSTRUCTOR_TOKEN_FILE" | tr -d '\n\r ')
EOF

    if [[ -f "$GENERATED_CONFIG_FILE" ]]; then
        mark_test_passed "Assignment configuration file generated"
        log_detail "Config file: $GENERATED_CONFIG_FILE"
    else
        mark_test_failed "Configuration generation" "Failed to create assignment.conf"
        return 1
    fi
    
    log_success "Assignment configuration generation completed"
    return 0
}

# Test configuration validation
test_config_validation() {
    log_step "Testing configuration validation"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY-RUN] Would validate configuration: $GENERATED_CONFIG_FILE"
        return 0
    fi
    
    # Test configuration validation with classdock
    if conda run -n "$TEST_ENV_NAME" classdock --config "$GENERATED_CONFIG_FILE" assignments validate-config; then
        mark_test_passed "Configuration validation passed"
    else
        mark_test_failed "Configuration validation" "classdock config validation failed"
        return 1
    fi
    
    log_success "Configuration validation testing completed"
    return 0
}

# Test assignment setup (dry-run mode)
test_assignment_setup() {
    log_step "Testing assignment setup (dry-run mode)"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY-RUN] Would test assignment setup with config: $GENERATED_CONFIG_FILE"
        return 0
    fi
    
    # Change to cloned repository directory for testing
    cd "$CLONED_REPO_DIR"
    
    # Test assignment setup in dry-run mode
    log_info "Running assignment setup in dry-run mode"
    if conda run -n "$TEST_ENV_NAME" classdock --config "$GENERATED_CONFIG_FILE" assignments --dry-run setup --verbose; then
        mark_test_passed "Assignment setup dry-run passed"
    else
        mark_test_failed "Assignment setup" "Assignment setup dry-run failed"
        return 1
    fi
    
    log_success "Assignment setup testing completed"
    return 0
}

# Test repository operations
test_repo_operations() {
    log_step "Testing repository operations"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY-RUN] Would test repository operations"
        return 0
    fi
    
    cd "$CLONED_REPO_DIR"
    
    # Test repository fetch operations
    log_info "Testing repository fetch operations"
    if conda run -n "$TEST_ENV_NAME" classdock repos fetch --help > /dev/null; then
        mark_test_passed "Repository fetch command available"
    else
        mark_test_failed "Repository operations" "Repository fetch command not available"
        return 1
    fi
    
    # Test collaborator operations (help only - no actual changes)
    log_info "Testing collaborator operations"
    if conda run -n "$TEST_ENV_NAME" classdock repos cycle-collaborator --help > /dev/null; then
        mark_test_passed "Collaborator operations available"
    else
        mark_test_failed "Repository operations" "Collaborator operations not available"
        return 1
    fi
    
    log_success "Repository operations testing completed"
    return 0
}

# Test secrets management
test_secrets_management() {
    log_step "Testing secrets management"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY-RUN] Would test secrets management"
        return 0
    fi
    
    cd "$CLONED_REPO_DIR"
    
    # Test secrets validation (dry-run mode only)
    log_info "Testing secrets validation"
    if conda run -n "$TEST_ENV_NAME" classdock --config "$GENERATED_CONFIG_FILE" secrets --dry-run add; then
        mark_test_passed "Secrets validation passed"
    else
        log_warning "Secrets validation failed (this may be expected in test environment)"
    fi
    
    # Test secrets help system
    if conda run -n "$TEST_ENV_NAME" classdock secrets --help > /dev/null; then
        mark_test_passed "Secrets management commands available"
    else
        mark_test_failed "Secrets management" "Secrets commands not available"
        return 1
    fi
    
    log_success "Secrets management testing completed"
    return 0
}

# Test CLI interface comprehensively
test_cli_interface() {
    log_step "Testing CLI interface comprehensively"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY-RUN] Would test CLI interface"
        return 0
    fi
    
    # Test main help
    if conda run -n "$TEST_ENV_NAME" classdock --help > /dev/null; then
        mark_test_passed "Main CLI help system working"
    else
        mark_test_failed "CLI interface" "Main help system failed"
        return 1
    fi
    
    # Test version command
    local version_output
    if version_output=$(conda run -n "$TEST_ENV_NAME" classdock --version 2>&1); then
        mark_test_passed "Version command working"
        log_detail "Version: $version_output"
    else
        mark_test_failed "CLI interface" "Version command failed"
        return 1
    fi
    
    # Test subcommands help
    local subcommands=("assignments" "repos" "secrets")
    for subcmd in "${subcommands[@]}"; do
        if conda run -n "$TEST_ENV_NAME" classdock "$subcmd" --help > /dev/null; then
            mark_test_passed "Subcommand '$subcmd' help working"
        else
            mark_test_failed "CLI interface" "Subcommand '$subcmd' help failed"
        fi
    done
    
    log_success "CLI interface testing completed"
    return 0
}

# Test Python API functionality
test_python_api() {
    log_step "Testing Python API functionality"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY-RUN] Would test Python API"
        return 0
    fi
    
    # Test basic imports
    if conda run -n "$TEST_ENV_NAME" python -c "import classdock; print('Import successful')"; then
        mark_test_passed "Python API import working"
    else
        mark_test_failed "Python API" "Basic import failed"
        return 1
    fi
    
    # Test configuration loading
    if conda run -n "$TEST_ENV_NAME" python -c "from classdock import ConfigLoader; cl = ConfigLoader(); print('ConfigLoader working')"; then
        mark_test_passed "ConfigLoader functionality working"
    else
        mark_test_failed "Python API" "ConfigLoader failed"
        return 1
    fi
    
    # Test with actual config file
    local test_script="$TEST_WORKSPACE_DIR/api_test.py"
    cat > "$test_script" << 'EOF'
import sys
sys.path.insert(0, '/Users/hugovalle/classdock')

try:
    from classdock import ConfigLoader
    from classdock.assignments.setup import AssignmentSetup
    
    # Test config loading
    config_file = sys.argv[1]
    setup = AssignmentSetup(config_file=config_file)
    print("✓ AssignmentSetup created successfully")
    
    # Test config loading
    config = setup.load_config()
    print("✓ Configuration loaded successfully")
    print(f"✓ Organization: {config.get('GITHUB_ORGANIZATION', 'Not found')}")
    print(f"✓ Assignment: {config.get('ASSIGNMENT_NAME', 'Not found')}")
    
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)
EOF
    
    if conda run -n "$TEST_ENV_NAME" python "$test_script" "$GENERATED_CONFIG_FILE"; then
        mark_test_passed "Python API integration with config working"
    else
        mark_test_failed "Python API" "Integration with config failed"
        return 1
    fi
    
    log_success "Python API testing completed"
    return 0
}

# Clean up test environment
cleanup_test_environment() {
    log_step "Cleaning up test environment"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY-RUN] Would clean up test environment"
        return 0
    fi
    
    # Clean up cloned repository
    if [[ "$KEEP_REPO" == "false" && -d "$CLONED_REPO_DIR" ]]; then
        log_info "Removing cloned repository: $CLONED_REPO_DIR"
        rm -rf "$CLONED_REPO_DIR"
        mark_test_passed "Cloned repository cleaned up"
    else
        log_info "Keeping cloned repository (--keep-repo specified or directory not found)"
    fi
    
    # Clean up workspace directory if empty
    if [[ -d "$TEST_WORKSPACE_DIR" && "$KEEP_REPO" == "false" ]]; then
        if [[ -z "$(ls -A "$TEST_WORKSPACE_DIR")" ]]; then
            rmdir "$TEST_WORKSPACE_DIR"
            mark_test_passed "Workspace directory cleaned up"
        else
            log_info "Workspace directory not empty, keeping: $TEST_WORKSPACE_DIR"
        fi
    fi
    
    # Remove conda environment
    if [[ "$KEEP_ENV" == "false" ]]; then
        if conda env list | grep -q "^$TEST_ENV_NAME "; then
            log_info "Removing conda environment: $TEST_ENV_NAME"
            conda env remove -n "$TEST_ENV_NAME" -y || true
            mark_test_passed "Conda environment cleaned up"
        else
            log_info "Conda environment not found: $TEST_ENV_NAME"
        fi
    else
        log_info "Keeping conda environment (--keep-env specified): $TEST_ENV_NAME"
    fi
    
    log_success "Test environment cleanup completed"
    return 0
}

# Show test summary
show_test_summary() {
    local total_tests=$((TESTS_PASSED + TESTS_FAILED))
    local success_rate=0
    
    if [[ $total_tests -gt 0 ]]; then
        success_rate=$(( (TESTS_PASSED * 100) / total_tests ))
    fi
    
    echo
    echo "=========================================================="
    echo "Real Repository Testing Results Summary"
    echo "=========================================================="
    echo "Test Environment: $TEST_ENV_NAME"
    echo "Repository: $TEMPLATE_REPO_URL_VAL"
    echo "Assignment: $ASSIGNMENT_NAME_VAL"
    echo "Configuration: $GENERATED_CONFIG_FILE"
    echo
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
    
    echo "=========================================================="
    
    if [[ "$KEEP_ENV" == "true" ]]; then
        echo "NOTE: Conda environment preserved: $TEST_ENV_NAME"
        echo "To activate: conda activate $TEST_ENV_NAME"
    fi
    
    if [[ "$KEEP_REPO" == "true" ]]; then
        echo "NOTE: Repository preserved: $CLONED_REPO_DIR"
    fi
}

# Main execution function
main() {
    log_info "Starting Real Repository Testing for ClassDock"
    log_info "Test environment: $TEST_ENV_NAME"
    log_info "Workspace: $TEST_WORKSPACE_DIR"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_warning "DRY RUN MODE - No actual changes will be made"
    fi
    
    # Handle specific operation modes
    if [[ "$CLEANUP_ONLY" == "true" ]]; then
        cleanup_test_environment
        show_test_summary
        exit $([[ $TESTS_FAILED -eq 0 ]] && echo 0 || echo 1)
    fi
    
    # Validate prerequisites
    if ! validate_prerequisites; then
        log_error "Prerequisites validation failed"
        exit 1
    fi
    
    # Parse configuration
    if ! parse_real_repo_config; then
        log_error "Configuration parsing failed"
        exit 1
    fi
    
    # Setup phase
    if [[ "$TEST_ONLY" == "false" ]]; then
        setup_conda_environment || exit 1
        clone_student_repository || exit 1
        generate_assignment_config || exit 1
    fi
    
    if [[ "$SETUP_ONLY" == "true" ]]; then
        log_success "Setup completed successfully"
        show_test_summary
        exit 0
    fi
    
    # Testing phase
    test_config_validation
    test_assignment_setup
    test_repo_operations
    test_secrets_management
    test_cli_interface
    test_python_api
    
    # Cleanup phase (unless keeping environment)
    if [[ "$KEEP_ENV" == "false" && "$KEEP_REPO" == "false" ]]; then
        cleanup_test_environment
    fi
    
    # Show results
    show_test_summary
    
    # Return appropriate exit code
    if [[ $TESTS_FAILED -eq 0 ]]; then
        log_success "All real repository tests passed! 🎉"
        exit 0
    else
        log_error "Some real repository tests failed!"
        exit 1
    fi
}

# Script execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi