#!/bin/bash
#
# Assignment Workflow Orchestrator
# 
# This script orchestrates the complete workflow for managing GitHub Classroom assignments:
# 1. Template synchronization with classroom
# 2. Student repository discovery
# 3. Secret management across all repositories
# 4. Optional student assistance
#
# Usage: ./scripts_legacy/assignment-orchestrator.sh [config-file] [options]
#

set -euo pipefail

# Script directory and paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# When tools is a submodule, REPO_ROOT should be the parent of the tools directory
TOOLS_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$TOOLS_ROOT/.." && pwd)"
DEFAULT_CONFIG="$REPO_ROOT/assignment.conf"

# Source shared color codes (but keep custom log functions)
source "$TOOLS_ROOT/utils/logging.sh"

# Default values
CONFIG_FILE="$DEFAULT_CONFIG"
VERBOSE=false
FORCE_YES=false
STEP_OVERRIDE=""
CLI_DRY_RUN=false

# Logging functions
log_debug() {
    if [[ "${LOG_LEVEL:-INFO}" == "DEBUG" ]]; then
        echo -e "${CYAN}[DEBUG]${NC} $*" >&2
    fi
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*" >&2
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*" >&2
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

log_header() {
    echo -e "\n${CYAN}=== $* ===${NC}" >&2
}

# Help function
show_help() {
    cat << 'EOF'
Assignment Workflow Orchestrator

USAGE:
    ./scripts_legacy/assignment-orchestrator.sh [config-file] [options]

PARAMETERS:
    config-file          Path to assignment configuration file (default: assignment.conf)

OPTIONS:
    --dry-run           Show what would be done without executing
    --verbose           Enable verbose output
    --yes              Skip confirmation prompts
    --step [step]       Run only specific step (sync|discover|secrets|assist|cycle)
    --skip [step]       Skip specific step
    --help             Show this help

CONFIGURATION FILE:
    The configuration file contains all assignment settings including:
    - GitHub Classroom URL and template repository
    - Secret tokens and management settings
    - Workflow step controls
    - Output and logging preferences
    
    If no assignment.conf file is found, the orchestrator will offer to run
    the setup wizard automatically to create the configuration file.

WORKFLOW STEPS:
    1. sync      - Synchronize template repository with GitHub Classroom
    2. discover  - Discover and list student repositories
    3. secrets   - Add/update secrets in student repositories
    4. assist    - Run student assistance tools (optional)
    5. cycle     - Fix student repository access by cycling collaborator permissions (optional)

EXAMPLES:
    # Run complete workflow with default config
    ./scripts_legacy/assignment-orchestrator.sh

    # Use custom config file
    ./scripts_legacy/assignment-orchestrator.sh my-assignment.conf

    # Dry run to preview actions
    ./scripts_legacy/assignment-orchestrator.sh --dry-run

    # Run only secret management step
    ./scripts_legacy/assignment-orchestrator.sh --step secrets

    # Skip template sync and run everything else
    ./scripts_legacy/assignment-orchestrator.sh --skip sync

    # Verbose output with no prompts
    ./scripts_legacy/assignment-orchestrator.sh --verbose --yes

REQUIREMENTS:
    - GitHub CLI (gh) installed and authenticated
    - All component scripts in scripts_legacy/ directory
    - Valid assignment configuration file
    - Appropriate GitHub permissions

EOF
}

# Parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help|-h)
                show_help
                exit 0
                ;;
            --dry-run)
                CLI_DRY_RUN=true
                shift
                ;;
            --verbose|-v)
                VERBOSE=true
                LOG_LEVEL="DEBUG"
                shift
                ;;
            --yes|-y)
                FORCE_YES=true
                shift
                ;;
            --step)
                if [[ -z "${2:-}" ]]; then
                    log_error "Step name required after --step"
                    exit 1
                fi
                STEP_OVERRIDE="$2"
                shift 2
                ;;
            --skip)
                if [[ -z "${2:-}" ]]; then
                    log_error "Step name required after --skip"
                    exit 1
                fi
                case $2 in
                    sync) STEP_SYNC_TEMPLATE=false ;;
                    discover) STEP_DISCOVER_REPOS=false ;;
                    secrets) STEP_MANAGE_SECRETS=false ;;
                    assist) STEP_ASSIST_STUDENTS=false ;;
                    cycle) STEP_CYCLE_COLLABORATORS=false ;;
                    *) log_error "Unknown step: $2"; exit 1 ;;
                esac
                shift 2
                ;;
            --*)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
            *)
                if [[ -f "$1" ]]; then
                    CONFIG_FILE="$1"
                else
                    log_error "Configuration file not found: $1"
                    exit 1
                fi
                shift
                ;;
        esac
    done
}

# Load and validate configuration
check_initial_setup() {
    if [[ ! -f "$CONFIG_FILE" ]]; then
        echo -e "\n${YELLOW}⚠️  Assignment Configuration Missing${NC}"
        echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo -e "No ${CYAN}assignment.conf${NC} file found in the current directory."
        echo -e "This file is required to configure your GitHub Classroom assignment.\n"
        
        echo -e "${PURPLE}Would you like to run the initial setup wizard now?${NC}"
        echo -e "The setup wizard will guide you through creating the configuration file.\n"
        
        if [[ "$FORCE_YES" == "true" ]]; then
            echo -e "${GREEN}Auto-confirming setup (--yes flag detected)${NC}"
            run_setup=true
        else
            read -p "Run setup wizard? [y/N]: " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                run_setup=true
            else
                run_setup=false
            fi
        fi
        
        if [[ "$run_setup" == "true" ]]; then
            echo -e "\n${BLUE}🚀 Launching Assignment Setup Wizard...${NC}"
            echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            
            # Run the setup script
            if [[ -f "$TOOLS_ROOT/scripts_legacy/setup-assignment.sh" ]]; then
                "$TOOLS_ROOT/scripts_legacy/setup-assignment.sh"
                
                # Check if setup was successful
                if [[ -f "$CONFIG_FILE" ]]; then
                    echo -e "\n${GREEN}✅ Setup completed successfully!${NC}"
                    echo -e "Configuration file created: ${CYAN}$CONFIG_FILE${NC}\n"
                    log_info "Continuing with assignment orchestrator..."
                else
                    log_error "Setup did not create configuration file. Exiting."
                    exit 1
                fi
            else
                log_error "Setup script not found: $TOOLS_ROOT/scripts_legacy/setup-assignment.sh"
                log_error "Please run the setup script manually or create assignment.conf"
                exit 1
            fi
        else
            echo -e "\n${YELLOW}Setup cancelled.${NC}"
            echo -e "To proceed, you can:"
            echo -e "  ${CYAN}1.${NC} Run the setup wizard: $TOOLS_ROOT/scripts_legacy/setup-assignment.sh"
            echo -e "  ${CYAN}2.${NC} Create assignment.conf manually in: $REPO_ROOT"
            echo -e "  ${CYAN}3.${NC} Use a custom config file: ./assignment-orchestrator.sh /path/to/config\n"
            exit 0
        fi
    fi
}

load_configuration() {
    log_info "Loading configuration from: $CONFIG_FILE"
    
    if [[ ! -f "$CONFIG_FILE" ]]; then
        log_error "Configuration file not found: $CONFIG_FILE"
        log_error "Run with --help for usage information"
        exit 1
    fi
    
    # Source the configuration file
    # shellcheck source=/dev/null
    source "$CONFIG_FILE"
    
    # Extract assignment name from classroom URL if not specified
    if [[ -z "${ASSIGNMENT_NAME:-}" ]] && [[ -n "${CLASSROOM_URL:-}" ]]; then
        if [[ "$CLASSROOM_URL" =~ /assignments/([^/?]+) ]]; then
            ASSIGNMENT_NAME="${BASH_REMATCH[1]}"
            log_debug "Extracted assignment name: $ASSIGNMENT_NAME"
        else
            log_error "Cannot extract assignment name from classroom URL: $CLASSROOM_URL"
            exit 1
        fi
    fi
    
    # Set default assignment file if not specified
    # Support universal file types with backward compatibility
    if [[ -z "${ASSIGNMENT_FILE:-}" ]]; then
        if [[ -n "${ASSIGNMENT_NOTEBOOK:-}" ]]; then
            # Use legacy ASSIGNMENT_NOTEBOOK if set
            ASSIGNMENT_FILE="$ASSIGNMENT_NOTEBOOK"
            log_debug "Using assignment notebook (legacy): $ASSIGNMENT_FILE"
        else
            ASSIGNMENT_FILE="assignment.ipynb"
            log_debug "Using default assignment file: $ASSIGNMENT_FILE"
        fi
    fi
    
    # Export variables for child scripts (both new and legacy for compatibility)
    export ASSIGNMENT_FILE
    export ASSIGNMENT_NOTEBOOK="$ASSIGNMENT_FILE"  # For backward compatibility
    
    # Validate required configuration
    local required_vars=(
        "CLASSROOM_URL"
        "TEMPLATE_REPO_URL"
        "GITHUB_ORGANIZATION"
        "ASSIGNMENT_NAME"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            log_error "Required configuration variable not set: $var"
            exit 1
        fi
    done
    
    # Set default values for optional configuration
    # Ensure SECRETS is always an array
    if [[ -z "${SECRETS+x}" ]]; then
        SECRETS=()
    fi
    
    # Parse SECRETS_CONFIG into SECRETS array if provided
    if [[ -n "${SECRETS_CONFIG:-}" ]]; then
        # Parse multiline SECRETS_CONFIG into array
        while IFS= read -r line; do
            # Skip empty lines and comments
            if [[ -n "$line" ]] && [[ ! "$line" =~ ^[[:space:]]*# ]] && [[ ! "$line" =~ ^[[:space:]]*$ ]]; then
                SECRETS+=("$line")
            fi
        done <<< "$SECRETS_CONFIG"
    fi
    SECRET_MAX_AGE_DAYS="${SECRET_MAX_AGE_DAYS:-90}"
    SECRET_FORCE_UPDATE="${SECRET_FORCE_UPDATE:-false}"
    OUTPUT_DIR="${OUTPUT_DIR:-scripts}"
    STUDENT_REPOS_FILE="${STUDENT_REPOS_FILE:-student-repos-batch.txt}"
    STUDENTS_ONLY_FILE="${STUDENTS_ONLY_FILE:-student-repos-students-only.txt}"
    
    # Workflow steps
    STEP_SYNC_TEMPLATE="${STEP_SYNC_TEMPLATE:-true}"
    STEP_DISCOVER_REPOS="${STEP_DISCOVER_REPOS:-true}"
    STEP_MANAGE_SECRETS="${STEP_MANAGE_SECRETS:-true}"
    STEP_ASSIST_STUDENTS="${STEP_ASSIST_STUDENTS:-false}"
    STEP_CYCLE_COLLABORATORS="${STEP_CYCLE_COLLABORATORS:-false}"
    
    # Override dry run from config if set via command line
    if [[ "$CLI_DRY_RUN" == "true" ]]; then
        # Command line dry-run takes precedence
        DRY_RUN=true
    else
        DRY_RUN="${DRY_RUN:-false}"
    fi
    
    log_success "Configuration loaded successfully"
    log_debug "Assignment: $ASSIGNMENT_NAME"
    log_debug "Organization: $GITHUB_ORGANIZATION"
    log_debug "Dry run: $DRY_RUN"
}

# Display configuration summary
show_configuration_summary() {
    log_header "Configuration Summary"
    echo "Assignment: $ASSIGNMENT_NAME" >&2
    echo "Organization: $GITHUB_ORGANIZATION" >&2
    echo "Template Repository: $TEMPLATE_REPO_URL" >&2
    echo "Classroom URL: $CLASSROOM_URL" >&2
    echo "Output Directory: $OUTPUT_DIR" >&2
    echo "Secrets to manage: ${#SECRETS[@]}" >&2
    echo "Dry Run: $DRY_RUN" >&2
    echo "" >&2
    echo "Workflow Steps:" >&2
    echo "  1. Sync Template: $STEP_SYNC_TEMPLATE" >&2
    echo "  2. Discover Repos: $STEP_DISCOVER_REPOS" >&2
    echo "  3. Manage Secrets: $STEP_MANAGE_SECRETS" >&2
    echo "  4. Assist Students: $STEP_ASSIST_STUDENTS" >&2
    echo "  5. Cycle Collaborators: $STEP_CYCLE_COLLABORATORS" >&2
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if we're in the right directory (assignment repository with tools submodule)
    if [[ ! -f "$REPO_ROOT/$ASSIGNMENT_FILE" ]] || [[ ! -d "$REPO_ROOT/tools" ]]; then
        log_error "This script must be run from the template repository root"
        log_error "Expected files: $ASSIGNMENT_FILE, tools/ directory"
        exit 1
    fi
    
    # Check required scripts in tools submodule
    local required_scripts=(
        "tools/scripts_legacy/push-to-classroom.sh"
        "tools/scripts_legacy/fetch-student-repos.sh"
        "tools/scripts_legacy/add-secrets-to-students.sh"
    )
    
    # Optional scripts (don't fail if missing, just warn)
    local optional_scripts=(
        "tools/scripts_legacy/cycle-collaborator.sh"
    )
    
    for script in "${required_scripts[@]}"; do
        if [[ ! -f "$REPO_ROOT/$script" ]]; then
            log_error "Required script not found: $script"
            exit 1
        fi
        if [[ ! -x "$REPO_ROOT/$script" ]]; then
            log_warning "Making script executable: $script"
            chmod +x "$REPO_ROOT/$script"
        fi
    done
    
    # Check optional scripts (warn if missing but don't fail)
    for script in "${optional_scripts[@]}"; do
        if [[ ! -f "$REPO_ROOT/$script" ]]; then
            log_warning "Optional script not found: $script"
            log_warning "Some features may not be available"
        elif [[ ! -x "$REPO_ROOT/$script" ]]; then
            log_warning "Making script executable: $script"
            chmod +x "$REPO_ROOT/$script"
        fi
    done
    
    # Check GitHub CLI
    if ! command -v gh &> /dev/null; then
        log_error "GitHub CLI (gh) is not installed"
        log_error "Please install it from: https://cli.github.com/"
        exit 1
    fi
    
    if ! gh auth status &> /dev/null; then
        log_error "GitHub CLI is not authenticated"
        log_error "Please run: gh auth login"
        exit 1
    fi
    
    # Create output directory if it doesn't exist
    if [[ ! -d "$REPO_ROOT/$OUTPUT_DIR" ]]; then
        log_info "Creating output directory: $OUTPUT_DIR"
        mkdir -p "$REPO_ROOT/$OUTPUT_DIR"
    fi
    
    log_success "Prerequisites check passed"
}

# Confirmation prompt
confirm_execution() {
    if [[ "$FORCE_YES" == "true" ]] || [[ "$DRY_RUN" == "true" ]]; then
        return 0
    fi
    
    echo >&2
    read -p "Do you want to proceed with this workflow? (y/N): " -n 1 -r
    echo >&2
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Workflow cancelled by user"
        exit 0
    fi
}

# Step 1: Synchronize template with classroom
step_sync_template() {
    if [[ "$STEP_SYNC_TEMPLATE" != "true" ]]; then
        log_info "Skipping template synchronization (disabled in config)"
        return 0
    fi
    
    log_header "Step 1: Synchronizing Template with Classroom"
    
    local cmd="$REPO_ROOT/tools/scripts_legacy/push-to-classroom.sh"
    local args=()
    
    # Pass force flag for non-interactive execution
    if [[ "$FORCE_YES" == "true" ]]; then
        args+=("--force")
    fi
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN: Would execute: $cmd ${args[*]}"
        log_info "This would sync the template repository to GitHub Classroom"
        return 0
    fi
    
    log_info "Executing: $cmd ${args[*]}"
    if ! "$cmd" "${args[@]}"; then
        log_error "Template synchronization failed"
        return 1
    fi
    
    log_success "Template synchronization completed"
}

# Step 2: Discover student repositories
step_discover_repositories() {
    if [[ "$STEP_DISCOVER_REPOS" != "true" ]]; then
        log_info "Skipping repository discovery (disabled in config)"
        return 0
    fi
    
    log_header "Step 2: Discovering Student Repositories"
    
    local cmd="$REPO_ROOT/tools/scripts_legacy/fetch-student-repos.sh"
    local output_file="$REPO_ROOT/$OUTPUT_DIR/$STUDENT_REPOS_FILE"
    local args=(
        "--classroom-url" "$CLASSROOM_URL"
        "--output" "$output_file"
    )
    
    if [[ "${INCLUDE_TEMPLATE_IN_BATCH:-false}" == "true" ]]; then
        args+=("--include-template")
    fi
    
    if [[ "${EXCLUDE_INSTRUCTOR_REPOS:-false}" == "true" ]]; then
        args+=("--exclude-instructor")
    fi
    
    if [[ "$DRY_RUN" == "true" ]]; then
        args+=("--dry-run")
    fi
    
    log_info "Executing: $cmd ${args[*]}"
    if ! "$cmd" "${args[@]}"; then
        log_error "Repository discovery failed"
        return 1
    fi
    
    # Create students-only file if needed
    if [[ "$DRY_RUN" != "true" ]] && [[ -f "$output_file" ]]; then
        local students_only_file="$REPO_ROOT/$OUTPUT_DIR/$STUDENTS_ONLY_FILE"
        log_info "Creating students-only file: $students_only_file"
        grep -v "instructor-tests" "$output_file" > "$students_only_file" || true
        
        # Count repositories
        local total_repos
        local student_repos
        total_repos=$(grep -c "^https://" "$output_file" || echo "0")
        student_repos=$(grep -c "^https://" "$students_only_file" || echo "0")
        
        log_success "Repository discovery completed"
        log_info "Total repositories: $total_repos"
        log_info "Student repositories: $student_repos"
        log_info "Batch file: $output_file"
        log_info "Students-only file: $students_only_file"
    fi
}

# Step 3: Manage secrets across repositories
step_manage_secrets() {
    if [[ "$STEP_MANAGE_SECRETS" != "true" ]]; then
        log_info "Skipping secret management (disabled in config)"
        return 0
    fi
    
    if [[ ${#SECRETS[@]} -eq 0 ]]; then
        log_info "Skipping secret management (no secrets configured)"
        return 0
    fi
    
    log_header "Step 3: Managing Secrets"
    
    local batch_file="$REPO_ROOT/$OUTPUT_DIR/$STUDENT_REPOS_FILE"
    if [[ ! -f "$batch_file" ]]; then
        log_warning "Batch file not found: $batch_file"
        if [[ "$DRY_RUN" == "true" ]]; then
            log_info "DRY RUN: Would manage secrets for student repositories (batch file would be created by repository discovery)"
            return 0
        else
            log_info "Repository discovery must be run first to manage secrets"
            return 1
        fi
    fi
    
    for secret_config in "${SECRETS[@]}"; do
        # Parse secret configuration: SECRET_NAME:description:token_file_path:max_age_days:validate_format
        IFS=':' read -r secret_name description token_file max_age_days validate_format <<< "$secret_config"
        
        # Default validate_format to true if not specified (backward compatibility)
        validate_format="${validate_format:-true}"
        
        if [[ -z "$secret_name" ]] || [[ -z "$token_file" ]]; then
            log_warning "Invalid secret configuration: $secret_config"
            continue
        fi
        
        log_info "Managing secret: $secret_name ($description)"
        
        local cmd="$REPO_ROOT/tools/scripts_legacy/add-secrets-to-students.sh"
        local args=(
            "$secret_name"
            "--batch" "$batch_file"
            "--token-file" "$token_file"
            "--max-age" "$SECRET_MAX_AGE_DAYS"
        )
        
        # Add validation flag if specified
        if [[ "$validate_format" == "false" ]]; then
            args+=("--no-validate")
        fi
        
        if [[ "$SECRET_FORCE_UPDATE" == "true" ]]; then
            args+=("--force-update")
        fi
        
        if [[ "$DRY_RUN" == "true" ]]; then
            log_info "DRY RUN: Would execute: $cmd ${args[*]}"
            log_info "This would add/update '$secret_name' in all student repositories"
            continue
        fi
        
        log_info "Executing: $cmd ${args[*]}"
        if ! "$cmd" "${args[@]}"; then
            log_error "Secret management failed for: $secret_name"
            return 1
        fi
    done
    
    log_success "Secret management completed"
}

# Step 4: Student assistance (optional)
step_assist_students() {
    if [[ "$STEP_ASSIST_STUDENTS" != "true" ]]; then
        log_info "Skipping student assistance (disabled in config)"
        return 0
    fi
    
    log_header "Step 4: Student Assistance"
    
    local students_file="$REPO_ROOT/$OUTPUT_DIR/$STUDENTS_ONLY_FILE"
    if [[ ! -f "$students_file" ]]; then
        log_warning "Students-only file not found: $students_file"
        log_warning "Using full batch file instead"
        students_file="$REPO_ROOT/$OUTPUT_DIR/$STUDENT_REPOS_FILE"
    fi
    
    if [[ ! -f "$students_file" ]]; then
        log_error "No repository file found for student assistance"
        return 1
    fi
    
    local cmd="$REPO_ROOT/tools/scripts_legacy/student-update-helper.sh"
    local args=("--batch" "$students_file")
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN: Would execute: $cmd ${args[*]}"
        log_info "This would run student assistance tools on all repositories"
        return 0
    fi
    
    log_info "Executing: $cmd ${args[*]}"
    if ! "$cmd" "${args[@]}"; then
        log_error "Student assistance failed"
        return 1
    fi
    
    log_success "Student assistance completed"
}

# Step 5: Cycle collaborator access (fix repository permissions)
step_cycle_collaborators() {
    if [[ "${STEP_CYCLE_COLLABORATORS:-false}" != "true" ]]; then
        log_info "Skipping collaborator cycling (disabled in config)"
        return 0
    fi
    
    log_header "Step 5: Cycling Collaborator Access"
    
    local students_file="$REPO_ROOT/$OUTPUT_DIR/$STUDENTS_ONLY_FILE"
    if [[ ! -f "$students_file" ]]; then
        log_warning "Students-only file not found: $students_file"
        log_warning "Using full batch file instead"
        students_file="$REPO_ROOT/$OUTPUT_DIR/$STUDENT_REPOS_FILE"
    fi
    
    if [[ ! -f "$students_file" ]]; then
        log_error "No repository file found for collaborator cycling"
        return 1
    fi
    
    # Count repositories to process
    local repo_count
    repo_count=$(grep -c "^https://" "$students_file" || echo "0")
    log_info "Found $repo_count student repositories to process"
    
    if [[ "$repo_count" -eq 0 ]]; then
        log_warning "No student repositories found to cycle - skipping"
        return 0
    fi
    
    local cmd="$REPO_ROOT/tools/scripts_legacy/cycle-collaborator.sh"
    local args=(
        "--config" "$CONFIG_FILE"
        "--batch" "$students_file"
        "--repo-urls"
    )
    
    if [[ "$DRY_RUN" == "true" ]]; then
        args+=("--dry-run")
    fi
    
    if [[ "$VERBOSE" == "true" ]]; then
        args+=("--verbose")
    fi
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN: Would execute: $cmd ${args[*]}"
        log_info "This would cycle collaborator access for all student repositories"
        return 0
    fi
    
    log_info "Executing: $cmd ${args[*]}"
    if ! "$cmd" "${args[@]}"; then
        log_error "Collaborator cycling failed"
        return 1
    fi
    
    log_success "Collaborator cycling completed"
}

# Execute specific step
execute_step() {
    local step="$1"
    case $step in
        sync)
            step_sync_template
            ;;
        discover)
            step_discover_repositories
            ;;
        secrets)
            step_manage_secrets
            ;;
        assist)
            step_assist_students
            ;;
        cycle)
            step_cycle_collaborators
            ;;
        *)
            log_error "Unknown step: $step"
            return 1
            ;;
    esac
}

# Main workflow execution
execute_workflow() {
    log_header "Executing Assignment Workflow"
    
    local start_time
    start_time=$(date +%s)
    
    # Execute specific step if requested
    if [[ -n "$STEP_OVERRIDE" ]]; then
        log_info "Executing single step: $STEP_OVERRIDE"
        if ! execute_step "$STEP_OVERRIDE"; then
            log_error "Step failed: $STEP_OVERRIDE"
            exit 1
        fi
        log_success "Single step completed successfully"
        return 0
    fi
    
    # Execute full workflow
    local failed_steps=()
    local repos_discovered=false
    
    # Step 1: Template synchronization (independent)
    if ! step_sync_template; then
        failed_steps+=("sync")
    fi
    
    # Step 2: Repository discovery (can fail if no student repos exist)
    if step_discover_repositories; then
        repos_discovered=true
    else
        log_warning "Repository discovery failed - continuing with remaining steps that don't require student repositories"
    fi
    
    # Step 3: Secret management (only if repositories were discovered)
    if [[ "$repos_discovered" == "true" ]]; then
        if ! step_manage_secrets; then
            failed_steps+=("secrets")
        fi
    else
        log_info "Skipping secret management (no student repositories discovered)"
    fi
    
    # Step 4: Student assistance (only if repositories were discovered)
    if [[ "$repos_discovered" == "true" ]]; then
        if ! step_assist_students; then
            failed_steps+=("assist")
        fi
    else
        log_info "Skipping student assistance (no student repositories discovered)"
    fi

    # Step 5: Cycle collaborator access (only if repositories were discovered)
    if [[ "$repos_discovered" == "true" ]]; then
        if ! step_cycle_collaborators; then
            failed_steps+=("cycle")
        fi
    else
        log_info "Skipping collaborator cycling (no student repositories discovered)"
    fi

    local end_time
    end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    echo >&2
    log_header "Workflow Summary"
    
    if [[ ${#failed_steps[@]} -eq 0 ]]; then
        log_success "All workflow steps completed successfully!"
    else
        log_error "The following steps failed: ${failed_steps[*]}"
        exit 1
    fi
    
    log_info "Total execution time: ${duration}s"
    
    # Show final file locations
    echo >&2
    echo "Generated Files:" >&2
    echo "  Repository batch file: $OUTPUT_DIR/$STUDENT_REPOS_FILE" >&2
    echo "  Students-only file: $OUTPUT_DIR/$STUDENTS_ONLY_FILE" >&2
    
    if [[ "$DRY_RUN" == "true" ]]; then
        echo >&2
        log_info "This was a dry run. No actual changes were made."
        log_info "Run without --dry-run to execute the workflow."
    fi
}

# Main function
main() {
    cd "$REPO_ROOT"
    
    parse_arguments "$@"
    check_initial_setup
    load_configuration
    show_configuration_summary
    check_prerequisites
    confirm_execution
    execute_workflow
}

# Execute main function if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
