#!/bin/bash

# Script to add secrets to student repositories
# This script adds the INSTRUCTOR_TESTS_TOKEN secret to student GitHub repositories
# so they can access the instructor test repository during CI/CD runs

set -e

# Source shared utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../utils/logging.sh"
source "$SCRIPT_DIR/../utils/config.sh"

# Get default values from config
DEFAULT_ORGANIZATION="$(get_config_value GITHUB_ORGANIZATION)"
# Get assignment prefix from template repo URL if ASSIGNMENT_NAME is not set
ASSIGNMENT_NAME="$(get_config_value ASSIGNMENT_NAME)"
if [ -z "$ASSIGNMENT_NAME" ]; then
    TEMPLATE_REPO_URL="$(get_config_value TEMPLATE_REPO_URL)"
    DEFAULT_ASSIGNMENT_PREFIX="$(basename "$TEMPLATE_REPO_URL" .git)"
else
    DEFAULT_ASSIGNMENT_PREFIX="$ASSIGNMENT_NAME"
fi

# Function to show help
show_help() {
    cat << EOF
Add Secrets to Student Repositories - Instructor Tool

USAGE:
    ./scripts_legacy/add-secrets-to-students.sh [SECRET_NAME] [student-repo-url]              # Add secret to specific student
    ./scripts_legacy/add-secrets-to-students.sh [SECRET_NAME] --batch [file-with-urls]       # Add secrets to multiple students
    ./scripts_legacy/add-secrets-to-students.sh [SECRET_NAME] --token-file [file-path]       # Specify custom token file
    ./scripts_legacy/add-secrets-to-students.sh [SECRET_NAME] --max-age [days]               # Set expiration threshold (default: 90)
    ./scripts_legacy/add-secrets-to-students.sh --check-token                                # Verify your GitHub token works
    ./scripts_legacy/add-secrets-to-students.sh --help                                       # Show this help

PARAMETERS:
    SECRET_NAME       Name of the secret to add (default: INSTRUCTOR_TESTS_TOKEN)
    --token-file      Path to file containing the token value (default: instructor_token.txt)
    --max-age         Maximum age in days before updating existing secrets (default: 90)
    --force-update    Always update secrets regardless of age
    --no-validate     Skip GitHub token format validation (for non-GitHub secrets like passwords)

EXAMPLES:
    # Add INSTRUCTOR_TESTS_TOKEN to a specific student (using default token file)
    ./scripts_legacy/add-secrets-to-students.sh INSTRUCTOR_TESTS_TOKEN https://github.com/${DEFAULT_ORGANIZATION}/${DEFAULT_ASSIGNMENT_PREFIX}-student123

    # Add custom secret using default token file
    ./scripts_legacy/add-secrets-to-students.sh MY_CUSTOM_TOKEN https://github.com/${DEFAULT_ORGANIZATION}/${DEFAULT_ASSIGNMENT_PREFIX}-student123

    # Add secrets to multiple students from a file
    ./scripts_legacy/add-secrets-to-students.sh INSTRUCTOR_TESTS_TOKEN --batch student-repos.txt

    # Use custom token file
    ./scripts_legacy/add-secrets-to-students.sh INSTRUCTOR_TESTS_TOKEN --token-file my_token.txt https://github.com/${DEFAULT_ORGANIZATION}/${DEFAULT_ASSIGNMENT_PREFIX}-student123

    # Update secrets older than 30 days instead of default 90
    ./scripts_legacy/add-secrets-to-students.sh INSTRUCTOR_TESTS_TOKEN --max-age 30 https://github.com/${DEFAULT_ORGANIZATION}/${DEFAULT_ASSIGNMENT_PREFIX}-student123

    # Force update all secrets regardless of age
    ./scripts_legacy/add-secrets-to-students.sh INSTRUCTOR_TESTS_TOKEN --force-update --batch student-repos.txt

    # Add a database password (skip GitHub token validation)
    ./scripts_legacy/add-secrets-to-students.sh DB_PASSWORD --token-file db_password.txt --no-validate --batch student-repos.txt

    # Check if your GitHub token has the necessary permissions
    ./scripts_legacy/add-secrets-to-students.sh --check-token

REQUIREMENTS:
    - GitHub CLI (gh) must be installed and authenticated
    - Your GitHub token must have 'repo' and 'admin:repo_hook' permissions
    - Access to both student repositories and instructor tests repository
    - Token file must exist and contain the secret value

TOKEN FILE SETUP:
    1. Create instructor_token.txt in the repository root
    2. Add your token value to the file (single line, no extra whitespace)
    3. The file is automatically ignored by git (.gitignore)

STUDENT REPOS FILE FORMAT (for --batch):
    https://github.com/${DEFAULT_ORGANIZATION}/${DEFAULT_ASSIGNMENT_PREFIX}-student1
    https://github.com/${DEFAULT_ORGANIZATION}/${DEFAULT_ASSIGNMENT_PREFIX}-student2
    https://github.com/${DEFAULT_ORGANIZATION}/${DEFAULT_ASSIGNMENT_PREFIX}-student3

SETUP:
    1. Make sure you have GitHub CLI installed: https://cli.github.com/
    2. Authenticate with GitHub: gh auth login
    3. Create token file: echo "your_token_here" > instructor_token.txt
    4. Test with: ./scripts_legacy/add-secrets-to-students.sh --check-token

EOF
}

# Function to extract student name from repository URL
get_student_name() {
    local repo_url="$1"
    echo "$repo_url" | sed -E "s/.*${DEFAULT_ASSIGNMENT_PREFIX}-(.+)$/\1/" | sed 's/.git$//'
}

# Function to validate repository URL format
validate_repo_url() {
    local repo_url="$1"
    
    # Get assignment name and organization from config for validation
    local assignment_name="$(get_config_value ASSIGNMENT_NAME)"
    local github_org="$(get_config_value GITHUB_ORGANIZATION)"
    
    if [[ ! "$repo_url" =~ ^https://github\.com/${github_org}/.*${assignment_name}-.* ]]; then
        print_error "Invalid repository URL format"
        print_error "Expected: https://github.com/${github_org}/${assignment_name}-[student-name]"
        return 1
    fi
    
    return 0
}

# Function to get repository name from URL
get_repo_name() {
    local repo_url="$1"
    echo "$repo_url" | sed -E 's|https://github\.com/([^/]+/[^/]+).*|\1|'
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

# Function to check token permissions
check_token_permissions() {
    print_header "Checking GitHub Token Permissions"
    
    print_status "Testing access to instructor tests repository..."
    if ! gh repo view "$INSTRUCTOR_TESTS_REPO" &> /dev/null; then
        print_error "Cannot access instructor tests repository: $INSTRUCTOR_TESTS_REPO"
        print_error "Make sure your token has access to this repository"
        return 1
    fi
    print_success "Can access instructor tests repository"
    
    print_status "Testing repository secrets permissions..."
    # Try to list secrets from instructor repo to test permissions
    if ! gh secret list --repo "$INSTRUCTOR_TESTS_REPO" &> /dev/null; then
        print_error "Cannot manage secrets (insufficient permissions)"
        print_error "Your GitHub token needs 'repo' and 'admin:repo_hook' scopes"
        return 1
    fi
    print_success "Token has sufficient permissions for secret management"
    
    return 0
}

# Function to get the instructor tests token value from file
get_instructor_token() {
    local token_file="${1:-$DEFAULT_TOKEN_FILE}"
    local validate_token_format="${2:-true}"
    
    print_status "Reading token from file: $token_file" >&2
    
    if [ ! -f "$token_file" ]; then
        print_error "Token file not found: $token_file" >&2
        print_error "Please create the file with your token value:" >&2
        print_error "  echo 'your_token_here' > $token_file" >&2
        return 1
    fi
    
    local token_value
    token_value=$(cat "$token_file" | tr -d '\n\r' | xargs)
    
    if [ -z "$token_value" ]; then
        print_error "Token file is empty: $token_file" >&2
        print_error "Please add your token value to the file" >&2
        return 1
    fi
    
    # Conditionally validate token format based on validate_token_format flag
    if [[ "$validate_token_format" == "true" ]]; then
        # Validate token format - GitHub personal access tokens start with "ghp_"
        if [[ ! "$token_value" =~ ^ghp_ ]]; then
            print_error "Invalid token format in $token_file" >&2
            print_error "GitHub personal access tokens must start with 'ghp_'" >&2
            print_error "Current token: ${token_value:0:10}..." >&2
            print_error "Please verify your token is correct" >&2
            return 1
        fi
        
        # Validate token length - GitHub tokens are typically 40+ characters
        if [ ${#token_value} -lt 40 ]; then
            print_error "Token appears too short in $token_file" >&2
            print_error "GitHub personal access tokens are typically 40+ characters" >&2
            print_error "Current length: ${#token_value} characters" >&2
            print_error "Please verify your token is complete" >&2
            return 1
        fi
        
        print_success "Token loaded and validated from $token_file" >&2
    else
        print_success "Token loaded from $token_file (validation skipped)" >&2
    fi
    echo "$token_value"
}

# Function to check if a secret exists and get its age
check_secret_status() {
    local secret_name="$1"
    local repo_name="$2"
    
    # Get secret information
    local secret_info
    if secret_info=$(gh secret list --repo "$repo_name" 2>/dev/null | grep "^$secret_name"); then
        # Secret exists - extract the update date
        local update_date
        update_date=$(echo "$secret_info" | awk '{print $2}')
        
        # Calculate days since last update
        local current_date
        current_date=$(date +%s)
        local secret_date
        
        # Try to parse the date (GitHub CLI returns dates in YYYY-MM-DD format)
        if secret_date=$(date -d "$update_date" +%s 2>/dev/null); then
            local days_old=$(( (current_date - secret_date) / 86400 ))
            echo "EXISTS:$days_old"
        else
            # If we can't parse the date, assume it exists but age unknown
            echo "EXISTS:UNKNOWN"
        fi
    else
        echo "NOT_FOUND"
    fi
}

# Function to determine if a secret needs updating
needs_update() {
    local status="$1"
    local max_age_days="${2:-90}"  # Default 90 days
    
    case "$status" in
        "NOT_FOUND")
            return 0  # Needs to be created
            ;;
        "EXISTS:UNKNOWN")
            return 0  # Update since we can't determine age
            ;;
        "EXISTS:"*)
            local age_days="${status#EXISTS:}"
            if [ "$age_days" -ge "$max_age_days" ]; then
                return 0  # Needs update (too old)
            else
                return 1  # Still fresh
            fi
            ;;
        *)
            return 0  # Unknown status, update to be safe
            ;;
    esac
}

# Function to add secret to a student repository
add_secret_to_student() {
    local secret_name="$1"
    local repo_url="$2"
    local token_value="$3"
    local max_age_days="${4:-90}"
    local validate_token_format="${5:-true}"
    local student_name
    student_name=$(get_student_name "$repo_url")
    local repo_name
    repo_name=$(get_repo_name "$repo_url")
    
    print_header "Adding Secret '$secret_name' to Student: $student_name"
    
    # Validate repository URL
    if ! validate_repo_url "$repo_url"; then
        return 1
    fi
    
    print_status "Checking repository access..."
    if ! gh repo view "$repo_name" &> /dev/null; then
        print_error "Cannot access repository: $repo_name"
        print_error "Make sure the repository exists and you have access"
        return 1
    fi
    print_success "Repository is accessible"
    
    # Check if secret already exists and its age
    print_status "Checking existing secret status..."
    local secret_status
    secret_status=$(check_secret_status "$secret_name" "$repo_name")
    
    case "$secret_status" in
        "NOT_FOUND")
            print_status "Secret '$secret_name' not found - will create new secret"
            ;;
        "EXISTS:UNKNOWN")
            print_warning "Secret '$secret_name' exists but age unknown - will update"
            ;;
        "EXISTS:"*)
            local age_days="${secret_status#EXISTS:}"
            print_status "Secret '$secret_name' found - $age_days days old"
            
            if needs_update "$secret_status" "$max_age_days"; then
                print_warning "Secret is $age_days days old (>$max_age_days days) - will update"
            else
                print_success "Secret is fresh ($age_days days old) - will update anyway for consistency"
            fi
            ;;
    esac
    
    # Validate the token value before adding as secret
    if [ -z "$token_value" ]; then
        print_error "Token value is empty"
        return 1
    fi
    
    # Only validate GitHub token format if validation is enabled
    if [[ "$validate_token_format" == "true" ]]; then
        if [[ ! "$token_value" =~ ^ghp_ ]]; then
            print_error "Invalid token format for secret value"
            print_error "Token should start with 'ghp_' but starts with: ${token_value:0:10}..."
            return 1
        fi
    fi
    
    print_status "Adding/updating $secret_name secret..."
    
    if echo "$token_value" | gh secret set "$secret_name" --repo "$repo_name"; then
        case "$secret_status" in
            "NOT_FOUND")
                print_success "Successfully created $secret_name in $repo_name"
                ;;
            *)
                print_success "Successfully updated $secret_name in $repo_name"
                ;;
        esac
        
        # Verify the secret was actually set by listing secrets
        print_status "Verifying secret was added/updated..."
        if gh secret list --repo "$repo_name" | grep -q "$secret_name"; then
            print_success "Secret verification: $secret_name is present in repository"
        else
            print_warning "Secret verification: $secret_name may not have been processed correctly"
        fi
        
        return 0
    else
        print_error "Failed to add/update $secret_name in $repo_name"
        return 1
    fi
}

# Function to process multiple students from a file
process_batch() {
    local secret_name="$1"
    local file_path="$2"
    local token_file="$3"
    local max_age_days="${4:-90}"
    local validate_token_format="${5:-true}"
    
    if [ ! -f "$file_path" ]; then
        print_error "File not found: $file_path"
        return 1
    fi
    
    print_header "Processing Multiple Students from: $file_path"
    print_status "Secret: $secret_name"
    print_status "Token file: $token_file"
    
    # Get the token value once for all students
    local token_value
    if ! token_value=$(get_instructor_token "$token_file" "$validate_token_format"); then
        return 1
    fi
    
    if [ -z "$token_value" ]; then
        print_error "No token value loaded"
        return 1
    fi
    
    local success_count=0
    local error_count=0
    local total_count=0
    
    while IFS= read -r repo_url; do
        # Skip empty lines and comments
        if [[ -z "$repo_url" || "$repo_url" =~ ^[[:space:]]*# ]]; then
            continue
        fi
        
        # Remove leading/trailing whitespace
        repo_url=$(echo "$repo_url" | xargs)
        
        total_count=$((total_count + 1))
        
        echo
        if add_secret_to_student "$secret_name" "$repo_url" "$token_value" "$max_age_days" "$validate_token_format"; then
            success_count=$((success_count + 1))
        else
            error_count=$((error_count + 1))
        fi
    done < "$file_path"
    
    echo
    print_header "Batch Processing Summary"
    echo "  Secret: $secret_name"
    echo "  Total repositories: $total_count"
    echo "  Successful: $success_count"
    echo "  Errors: $error_count"
    
    if [ $error_count -eq 0 ]; then
        print_success "All secrets added successfully!"
        return 0
    else
        print_warning "Some repositories had errors"
        return 1
    fi
}

# Function to process a single student
process_single_student() {
    local secret_name="$1"
    local repo_url="$2"
    local token_file="$3"
    local max_age_days="${4:-90}"
    local validate_token_format="${5:-true}"
    
    print_status "Secret: $secret_name"
    print_status "Repository: $repo_url"
    print_status "Token file: $token_file"
    
    # Get the token value
    local token_value
    if ! token_value=$(get_instructor_token "$token_file" "$validate_token_format"); then
        return 1
    fi
    
    if [ -z "$token_value" ]; then
        print_error "No token value loaded"
        return 1
    fi
    
    add_secret_to_student "$secret_name" "$repo_url" "$token_value" "$max_age_days" "$validate_token_format"
}

# Main function
main() {
    # Determine the assignment repository root
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    # Check if we're being called from the CLI with a specific working directory
    # If assignment.conf exists in current directory, use current directory as root
    if [ -f "$(pwd)/assignment.conf" ]; then
        ASSIGNMENT_ROOT="$(pwd)"
        echo "[INFO] Using current working directory as assignment root: $ASSIGNMENT_ROOT"
    elif [[ "$SCRIPT_DIR" == */tools/scripts ]]; then
        # Running from tools submodule - assignment root is two levels up
        ASSIGNMENT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
        echo "[INFO] Using tools submodule assignment root: $ASSIGNMENT_ROOT"
    else
        # Running from legacy scripts directory - assignment root is two levels up
        ASSIGNMENT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
        echo "[INFO] Using legacy scripts assignment root: $ASSIGNMENT_ROOT"
    fi
    
    # Load assignment configuration if available
    if [ -f "$ASSIGNMENT_ROOT/assignment.conf" ]; then
        echo "[INFO] Loading assignment configuration from: $ASSIGNMENT_ROOT/assignment.conf"
        source "$ASSIGNMENT_ROOT/assignment.conf"
    fi
    
    # Check if we're in a valid assignment repository
    # Support universal file types with backward compatibility
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
    local secret_name="$DEFAULT_SECRET_NAME"
    local token_file="$DEFAULT_TOKEN_FILE"
    local max_age_days="90"
    local validate_token_format="true"
    local action=""
    local target=""
    
    # Process arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            "--help"|"-h")
                show_help
                exit 0
                ;;
            "--check-token")
                check_token_permissions
                exit $?
                ;;
            "--token-file")
                if [ -z "${2:-}" ]; then
                    print_error "Token file path required after --token-file"
                    exit 1
                fi
                token_file="$2"
                shift 2
                ;;
            "--max-age")
                if [ -z "${2:-}" ]; then
                    print_error "Number of days required after --max-age"
                    exit 1
                fi
                max_age_days="$2"
                shift 2
                ;;
            "--force-update")
                max_age_days="0"  # Force update by setting age to 0
                shift
                ;;
            "--no-validate")
                validate_token_format="false"
                shift
                ;;
            "--batch")
                if [ -z "${2:-}" ]; then
                    print_error "File path required after --batch"
                    exit 1
                fi
                action="batch"
                target="$2"
                shift 2
                ;;
            https://github.com/*)
                action="single"
                target="$1"
                shift
                ;;
            *)
                # If it's not a URL or flag, treat it as secret name
                if [[ "$1" != --* ]] && [[ "$1" != https://github.com/* ]]; then
                    secret_name="$1"
                    shift
                else
                    print_error "Unknown argument: $1"
                    show_help
                    exit 1
                fi
                ;;
        esac
    done
    
    # If no action was determined, show help
    if [ -z "$action" ]; then
        print_error "No action specified"
        echo
        show_help
        exit 1
    fi
    
    print_header "GitHub Secrets Management"
    print_status "Secret name: $secret_name"
    print_status "Token file: $token_file"
    print_status "Max age threshold: $max_age_days days"
    
    # Execute the action
    case "$action" in
        "single")
            process_single_student "$secret_name" "$target" "$token_file" "$max_age_days" "$validate_token_format"
            exit $?
            ;;
        "batch")
            process_batch "$secret_name" "$target" "$token_file" "$max_age_days" "$validate_token_format"
            exit $?
            ;;
        *)
            print_error "Unknown action: $action"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
