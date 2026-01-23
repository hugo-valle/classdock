#!/bin/bash

# Script to fetch student repository URLs from GitHub Classroom
# This script connects to GitHub Classroom and retrieves all student repositories
# for a specific assignment, then saves them to a file for batch processing

set -e

# Configuration
DEFAULT_OUTPUT_FILE="tools/generated/student-repos-batch.txt"

# Source shared utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../utils/config.sh"
source "$SCRIPT_DIR/../utils/logging.sh"

# Get organization and assignment prefix from config
DEFAULT_ORGANIZATION="$(get_config_value GITHUB_ORGANIZATION)"
# Get assignment prefix from template repo URL if ASSIGNMENT_NAME is not set
ASSIGNMENT_NAME="$(get_config_value ASSIGNMENT_NAME)"
if [ -z "$ASSIGNMENT_NAME" ]; then
    TEMPLATE_REPO_URL="$(get_config_value TEMPLATE_REPO_URL)"
    DEFAULT_ASSIGNMENT_PREFIX="$(basename "$TEMPLATE_REPO_URL" .git)"
else
    DEFAULT_ASSIGNMENT_PREFIX="$ASSIGNMENT_NAME"
fi
DEFAULT_CLASSROOM_URL="$(get_config_value CLASSROOM_URL)"

# Custom print function for this script
print_student() {
    echo -e "${CYAN}[FOUND]${NC} $1"
}

# Function to show help
show_help() {
    cat << EOF
GitHub Classroom Student Repository Fetcher

USAGE:
    ./scripts_legacy/fetch-student-repos.sh [assignment-prefix] [organization]          # Fetch repos with custom settings
    ./scripts_legacy/fetch-student-repos.sh --output [file-path]                       # Specify output file
    ./scripts_legacy/fetch-student-repos.sh --assignment [prefix]                      # Set assignment prefix
    ./scripts_legacy/fetch-student-repos.sh --org [organization]                       # Set GitHub organization
    ./scripts_legacy/fetch-student-repos.sh --help                                     # Show this help

PARAMETERS:
    assignment-prefix     Repository prefix pattern (default: ${DEFAULT_ASSIGNMENT_PREFIX})
    organization         GitHub organization name (default: ${DEFAULT_ORGANIZATION})
    --output             Output file path (default: scripts_legacy/student-repos-batch.txt)
    --assignment         Assignment prefix (alternative to positional arg)
    --org                Organization name (alternative to positional arg)
    --classroom-url      GitHub Classroom assignment URL (extracts assignment name automatically)
    --include-template    Include template repository in output
    --exclude-instructor  Exclude instructor-tests repositories
    --dry-run            Show what would be fetched without writing file

EXAMPLES:
    # Fetch all ${DEFAULT_ASSIGNMENT_PREFIX} student repos from ${DEFAULT_ORGANIZATION} organization
    ./scripts_legacy/fetch-student-repos.sh

    # Fetch with custom assignment and organization
    ./scripts_legacy/fetch-student-repos.sh my-assignment MY-ORG

    # Save to custom file
    ./scripts_legacy/fetch-student-repos.sh --output my-students.txt

    # Dry run to see what would be fetched
    ./scripts_legacy/fetch-student-repos.sh --dry-run

    # Include template repository in the list
    ./scripts_legacy/fetch-student-repos.sh --include-template

    # Exclude instructor repositories (students only)
    ./scripts_legacy/fetch-student-repos.sh --exclude-instructor

    # Use GitHub Classroom URL directly
    ./scripts_legacy/fetch-student-repos.sh --classroom-url "${DEFAULT_CLASSROOM_URL}"

    # Fetch specific assignment with custom output
    ./scripts_legacy/fetch-student-repos.sh --assignment final-project --output final-project-repos.txt

OUTPUT FORMAT:
    The output file will contain one repository URL per line:
    https://github.com/${DEFAULT_ORGANIZATION}/${DEFAULT_ASSIGNMENT_PREFIX}-student1
    https://github.com/${DEFAULT_ORGANIZATION}/${DEFAULT_ASSIGNMENT_PREFIX}-student2
    https://github.com/${DEFAULT_ORGANIZATION}/${DEFAULT_ASSIGNMENT_PREFIX}-student3

REQUIREMENTS:
    - GitHub CLI (gh) must be installed and authenticated
    - Access to the GitHub organization containing student repositories
    - Repositories must follow the naming pattern: [assignment-prefix]-[student-identifier]

INTEGRATION:
    Use the generated file with other scripts:
    ./scripts_legacy/add-secrets-to-students.sh INSTRUCTOR_TESTS_TOKEN --batch scripts_legacy/student-repos-batch.txt
    ./scripts_legacy/student-update-helper.sh --batch scripts_legacy/student-repos-batch.txt

EOF
}

# Function to check if GitHub CLI is installed and authenticated
check_gh_cli() {
    print_status "Checking GitHub CLI..."
    
    if ! command -v gh &> /dev/null; then
        print_error "GitHub CLI (gh) is not installed"
        print_error "Please install it from: https://cli.github.com/"
        return 1
    fi
    
    if ! gh auth status &> /dev/null; then
        print_error "GitHub CLI is not authenticated"
        print_error "Please run: gh auth login"
        return 1
    fi
    
    print_success "GitHub CLI is installed and authenticated"
    return 0
}

# Function to extract assignment name from GitHub Classroom URL
extract_assignment_from_url() {
    local url="$1"
    
    # Expected format: https://classroom.github.com/classrooms/CLASSROOM-ID/assignments/ASSIGNMENT-NAME
    # We want to extract ASSIGNMENT-NAME
    
    if [[ "$url" =~ /assignments/([^/?]+) ]]; then
        echo "${BASH_REMATCH[1]}"
    else
        return 1
    fi
}

# Function to check organization access
check_organization_access() {
    local org="$1"
    
    print_status "Checking access to organization: $org"
    
    if ! gh repo list "$org" --limit 1 &> /dev/null; then
        print_error "Cannot access organization: $org"
        print_error "Please ensure you have access to this organization"
        print_error "You may need to be a member or have the appropriate permissions"
        return 1
    fi
    
    print_success "Organization access confirmed"
    return 0
}

# Function to fetch student repositories
fetch_student_repos() {
    local assignment_prefix="$1"
    local organization="$2"
    local include_template="$3"
    
    print_status "Fetching repositories with prefix: $assignment_prefix" >&2
    print_status "From organization: $organization" >&2
    
    # Get all repositories from the organization that match the assignment prefix
    local repos
    if ! repos=$(gh repo list "$organization" --limit 1000 | grep "$assignment_prefix" | cut -f1 | cut -d'/' -f2); then
        print_error "Failed to fetch repositories from $organization"
        return 1
    fi
    
    # Convert repository names to HTTPS URLs and filter
    local https_repos=()
    local template_repo=""
    local student_count=0
    
    while IFS= read -r repo_name; do
        if [ -z "$repo_name" ]; then
            continue
        fi
        
        # Create HTTPS URL from repository name
        local repo_https="https://github.com/$organization/$repo_name"
        
        # Check if this is the template repository (ends with -template)
        if [[ "$repo_name" == "$assignment_prefix-template" ]]; then
            template_repo="$repo_https"
            continue
        fi
        
        # Skip classroom template copy
        if [[ "$repo_name" == *"classroom"* ]] && [[ "$repo_name" == *"template"* ]]; then
            continue
        fi
        
        # Skip instructor repositories if requested
        if [[ "${exclude_instructor:-false}" == "true" ]] && [[ "$repo_name" == *"instructor"* ]]; then
            continue
        fi
        
        # Only include repositories that have the assignment prefix followed by a dash (student repos)
        if [[ "$repo_name" == "$assignment_prefix-"* ]]; then
            https_repos+=("$repo_https")
            student_count=$((student_count + 1))
        fi
    done <<< "$repos"
    
    # Add template repository if requested and found
    if [ "$include_template" = "true" ] && [ -n "$template_repo" ]; then
        https_repos=("$template_repo" "${https_repos[@]}")
        print_status "Including template repository: $template_repo" >&2
    fi
    
    if [ ${#https_repos[@]} -eq 0 ]; then
        print_warning "No repositories found matching pattern: $assignment_prefix-*" >&2
        print_status "Available repositories in $organization:" >&2
        gh repo list "$organization" --limit 20 | grep "$assignment_prefix" >&2 || print_status "No repositories with prefix '$assignment_prefix' found" >&2
        return 1
    fi
    
    print_success "Found $student_count student repositories" >&2
    if [ -n "$template_repo" ]; then
        print_status "Template repository found: $template_repo" >&2
    fi
    
    # Return the array
    printf '%s\n' "${https_repos[@]}"
    return 0
}

# Function to save repositories to file
save_repos_to_file() {
    local output_file="$1"
    local assignment_prefix="$2"
    local organization="$3"
    shift 3
    local repos=("$@")
    
    print_status "Saving repositories to: $output_file" >&2
    
    # Create header comment
    cat > "$output_file" << EOF
# Student Repository URLs for $assignment_prefix
# Generated on $(date)
# Organization: $organization
# Total repositories: ${#repos[@]}
#
# Use this file with batch scripts:
# ./scripts_legacy/add-secrets-to-students.sh INSTRUCTOR_TESTS_TOKEN --batch $output_file
# ./scripts_legacy/student-update-helper.sh --batch $output_file

EOF
    
    # Add repositories
    for repo in "${repos[@]}"; do
        echo "$repo" >> "$output_file"
    done
    
    print_success "Saved ${#repos[@]} repositories to $output_file" >&2
    return 0
}

# Function to display dry run results
show_dry_run() {
    local assignment_prefix="$1"
    local organization="$2"
    shift 2
    local repos=("$@")
    
    print_header "Dry Run Results" >&2
    echo "Assignment: $assignment_prefix" >&2
    echo "Organization: $organization" >&2
    echo "Total repositories: ${#repos[@]}" >&2
    echo >&2
    print_status "Repositories that would be saved:" >&2
    
    for repo in "${repos[@]}"; do
        print_student "$repo" >&2
    done
    
    echo >&2
    print_status "To save these repositories, run without --dry-run" >&2
}

# Main function
main() {
    # Determine the assignment repository root when script is in tools submodule
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    if [[ "$SCRIPT_DIR" == */tools/scripts ]]; then
        # Running from tools submodule - assignment root is two levels up
        ASSIGNMENT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
    else
        # Running from legacy scripts directory - assignment root is two levels up
        ASSIGNMENT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
    fi
    
    # Load assignment configuration if available
    if [ -f "$ASSIGNMENT_ROOT/assignment.conf" ]; then
        echo "[INFO] Loading assignment configuration from: $ASSIGNMENT_ROOT/assignment.conf"
        source "$ASSIGNMENT_ROOT/assignment.conf"
    fi
    
    # Check if we're in a valid assignment repository
    # Support both new ASSIGNMENT_FILE and legacy ASSIGNMENT_NOTEBOOK
    ASSIGNMENT_FILE="${ASSIGNMENT_FILE:-${ASSIGNMENT_NOTEBOOK:-assignment.ipynb}}"
    if [ ! -f "$ASSIGNMENT_ROOT/$ASSIGNMENT_FILE" ]; then
        print_error "This script must be run from the template repository root directory"
        print_error "Make sure you're in the assignment template directory"
        print_error "Assignment root detected as: $ASSIGNMENT_ROOT"
        print_error "Expected assignment file: $ASSIGNMENT_FILE"
        exit 1
    fi
    
    # Check GitHub CLI first
    if ! check_gh_cli; then
        exit 1
    fi
    
    # Parse arguments
    local assignment_prefix="$DEFAULT_ASSIGNMENT_PREFIX"
    local organization="$DEFAULT_ORGANIZATION"
    local output_file="$DEFAULT_OUTPUT_FILE"
    local include_template="false"
    local dry_run="false"
    
    # Process arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            "--help"|"-h")
                show_help
                exit 0
                ;;
            "--output")
                if [ -z "${2:-}" ]; then
                    print_error "Output file path required after --output"
                    exit 1
                fi
                output_file="$2"
                shift 2
                ;;
            "--assignment")
                if [ -z "${2:-}" ]; then
                    print_error "Assignment prefix required after --assignment"
                    exit 1
                fi
                assignment_prefix="$2"
                shift 2
                ;;
            "--org")
                if [ -z "${2:-}" ]; then
                    print_error "Organization name required after --org"
                    exit 1
                fi
                organization="$2"
                shift 2
                ;;
            "--classroom-url")
                if [ -z "${2:-}" ]; then
                    print_error "GitHub Classroom URL required after --classroom-url"
                    exit 1
                fi
                assignment_prefix=$(extract_assignment_from_url "$2")
                if [ -z "$assignment_prefix" ]; then
                    print_error "Could not extract assignment name from URL: $2"
                    print_error "Expected format: https://classroom.github.com/.../assignments/ASSIGNMENT-NAME"
                    exit 1
                fi
                print_status "Extracted assignment prefix: $assignment_prefix" >&2
                shift 2
                ;;
            "--include-template")
                include_template="true"
                shift
                ;;
            "--exclude-instructor")
                exclude_instructor="true"
                shift
                ;;
            "--dry-run")
                dry_run="true"
                shift
                ;;
            --*)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
            *)
                # Positional arguments: assignment_prefix [organization]
                if [ "$assignment_prefix" = "$DEFAULT_ASSIGNMENT_PREFIX" ]; then
                    assignment_prefix="$1"
                elif [ "$organization" = "$DEFAULT_ORGANIZATION" ]; then
                    organization="$1"
                else
                    print_error "Too many positional arguments"
                    show_help
                    exit 1
                fi
                shift
                ;;
        esac
    done
    
    print_header "GitHub Classroom Repository Fetcher"
    print_status "Assignment prefix: $assignment_prefix"
    print_status "Organization: $organization"
    print_status "Output file: $output_file"
    print_status "Include template: $include_template"
    print_status "Dry run: $dry_run"
    
    # Check organization access
    if ! check_organization_access "$organization"; then
        exit 1
    fi
    
    # Fetch repositories
    print_status "Fetching student repositories..."
    local repos_output
    if ! repos_output=$(fetch_student_repos "$assignment_prefix" "$organization" "$include_template"); then
        exit 1
    fi
    
    # Convert output to array
    IFS=$'\n' read -d '' -r -a repos_array <<< "$repos_output" || true
    
    if [ ${#repos_array[@]} -eq 0 ]; then
        print_error "No repositories found"
        exit 1
    fi
    
    # Handle dry run or save to file
    if [ "$dry_run" = "true" ]; then
        show_dry_run "$assignment_prefix" "$organization" "${repos_array[@]}"
    else
        if ! save_repos_to_file "$output_file" "$assignment_prefix" "$organization" "${repos_array[@]}"; then
            exit 1
        fi
        
        echo
        print_success "Repository fetch completed successfully!"
        print_status "Use the generated file with:"
        print_status "  ./scripts_legacy/add-secrets-to-students.sh INSTRUCTOR_TESTS_TOKEN --batch $output_file"
        print_status "  ./scripts_legacy/student-update-helper.sh --batch $output_file"
    fi
}

# Run main function
main "$@"
