#!/bin/bash

# =============================================================================
# student-update-helper.sh
# 
# Instructor helper script to assist students with repository updates
# 
# This script helps instructors troubleshoot and assist students who are
# having difficulty updating their repositories with template changes.
#
# Usage: 
#   ./scripts_legacy/student-update-helper.sh [student-repo-url]
#   ./scripts_legacy/student-update-helper.sh --batch [file-with-repo-urls] [--yes]
#   ./scripts_legacy/student-update-helper.sh --status [student-repo-url]
#   ./scripts_legacy/student-update-helper.sh --yes  # Auto-confirm all prompts
# =============================================================================

set -e  # Exit on any error

# Configuration
TEMPLATE_REMOTE="origin"
CLASSROOM_REMOTE="classroom"
# NOTE: CLASSROOM_REPO_URL is now loaded from assignment.conf
# The classroom repository URL will be determined automatically or from configuration
BRANCH="main"
TEMP_DIR="/tmp/student-helper"

# Auto-confirm flag for automated execution
AUTO_CONFIRM=false

# Source shared utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../utils/config.sh"
source "$SCRIPT_DIR/../utils/logging.sh"

# Get organization from config
GITHUB_ORGANIZATION="$(get_config_value GITHUB_ORGANIZATION)"

# Get template repo URL and extract assignment prefix
TEMPLATE_REPO_URL="$(get_config_value TEMPLATE_REPO_URL)"
DEFAULT_ASSIGNMENT_PREFIX="$(basename "$TEMPLATE_REPO_URL" .git)"

# Function to show help
show_help() {
    cat << EOF
USAGE:
    $0 [student-repo-url]                    # Help specific student (requires classroom repo)
    $0 --one-student [student-repo-url]      # Help single student (uses template directly)
    $0 --batch [file-with-urls]             # Help multiple students
    $0 --status [student-repo-url]          # Check student's update status
    $0 --check-classroom                    # Verify classroom repo is ready
    $0 --yes                                # Auto-confirm all prompts (for automation)
    $0 --help                               # Show this help

OPTIONS:
    --yes                                   # Automatically answer 'yes' to all prompts

EXAMPLES:
    # Help a specific student using classroom repository
    $0 https://github.com/${GITHUB_ORGANIZATION}/${DEFAULT_ASSIGNMENT_PREFIX}-student123

    # Help a single student using template repository directly (NEW)
    $0 --one-student https://github.com/${GITHUB_ORGANIZATION}/${DEFAULT_ASSIGNMENT_PREFIX}-student123

    # Check multiple students from a file
    $0 --batch student-repos.txt

    # Automated batch processing (no prompts)
    $0 --batch student-repos.txt --yes

    # Check if a student needs updates
    $0 --status https://github.com/${GITHUB_ORGANIZATION}/${DEFAULT_ASSIGNMENT_PREFIX}-student123

    # Verify classroom repository is ready for student updates
    $0 --check-classroom

FEATURES:
    - Check if students need updates
    - Clone and fix student repositories
    - Apply updates safely with backups (from classroom or template)
    - Generate status reports
    - Batch process multiple students
    - Provide update instructions for students
    - NEW: Single student mode bypasses classroom repository

MODES:
    Default mode:     Uses classroom repository for updates (requires valid classroom URL)
    --one-student:    Uses template repository directly (bypasses classroom URL issues)

STUDENT REPOS FILE FORMAT (for --batch):
    https://github.com/${GITHUB_ORGANIZATION}/${DEFAULT_ASSIGNMENT_PREFIX}-student1
    https://github.com/${GITHUB_ORGANIZATION}/${DEFAULT_ASSIGNMENT_PREFIX}-student2
    https://github.com/${GITHUB_ORGANIZATION}/${DEFAULT_ASSIGNMENT_PREFIX}-student3

EOF
}

# Function to handle confirmations with auto-confirm support
confirm_action() {
    local prompt="$1"
    local default="${2:-N}"
    
    if [ "$AUTO_CONFIRM" = true ]; then
        echo "$prompt [auto-confirmed: Y]"
        return 0
    fi
    
    read -p "$prompt [y/N] " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        return 0
    else
        return 1
    fi
}

# Function to extract student name from repo URL
get_student_name() {
    local repo_url="$1"
    echo "$repo_url" | sed -E "s/.*${DEFAULT_ASSIGNMENT_PREFIX}-(.+)$/\1/" | sed 's/.git$//'
}

# Function to validate repository URL
validate_repo_url() {
    local repo_url="$1"
    
        # Get assignment name from config for validation
        local assignment_name="$(get_config_value ASSIGNMENT_NAME)"
        
        if [[ ! "$repo_url" =~ ^https://github\.com/${GITHUB_ORGANIZATION}/.*${assignment_name}-.* ]]; then
        print_error "Invalid repository URL format"
            print_error "Expected: https://github.com/${GITHUB_ORGANIZATION}/${assignment_name}-[student-name]"
        return 1
    fi
    
    return 0
}

# Function to check if classroom repository is ready
check_classroom_ready() {
    print_header "Checking Classroom Repository Status"
    
    print_status "Fetching classroom repository..."
    if ! git ls-remote "$CLASSROOM_REPO_URL" &>/dev/null; then
        print_error "Cannot access classroom repository: $CLASSROOM_REPO_URL"
        print_error "Please check the URL and your access permissions"
        return 1
    fi
    
    print_success "Classroom repository is accessible"
    
    # Get latest commit info
    local classroom_commit=$(git ls-remote "$CLASSROOM_REPO_URL" refs/heads/main | cut -f1)
    local local_commit=$(git rev-parse HEAD)
    
    echo "  Classroom commit: ${classroom_commit:0:8}"
    echo "  Local commit:     ${local_commit:0:8}"
    
    if [ "$classroom_commit" = "$local_commit" ]; then
        print_success "Classroom repository is up to date with local template"
    else
        print_warning "Classroom repository may not have latest changes"
        print_warning "Consider running: ./scripts_legacy/push-to-classroom.sh"
    fi
    
    return 0
}

# Function to check student repository status
check_student_status() {
    local repo_url="$1"
    local student_name
    student_name=$(get_student_name "$repo_url")
    
    print_header "Checking Status for Student: $repo_url"
    
    # Check if repository is accessible
    print_status "Checking repository access..."
    if ! git ls-remote "$repo_url" &>/dev/null; then
        print_error "Cannot access student repository: $repo_url"
        print_error "Repository may be private or URL may be incorrect"
        return 1
    fi
    
    print_success "Student repository is accessible"
    
    # Get commit information
    local student_commit
    local classroom_commit
    local local_commit
    
    student_commit=$(git ls-remote "$repo_url" refs/heads/main | cut -f1)
    classroom_commit=$(git ls-remote "$CLASSROOM_REPO_URL" refs/heads/main | cut -f1)
    local_commit=$(git rev-parse HEAD)
    
    echo
    echo "Commit Status:"
    echo "  Student:   ${student_commit:0:8}"
    echo "  Classroom: ${classroom_commit:0:8}"
    echo "  Template:  ${local_commit:0:8}"
    
    if [ "$student_commit" = "$classroom_commit" ]; then
        print_success "Student is up to date with classroom repository"
        return 0
    elif [ "$student_commit" = "$local_commit" ]; then
        print_success "Student is up to date with template repository"
        return 0
    else
        print_warning "Student needs to update their repository"
        echo
        print_student "Student should run: ./scripts_legacy/update-assignment.sh"
        print_student "Or follow manual instructions in: docs/UPDATE-GUIDE.md"
        return 2  # Needs update
    fi
}

# Function to help a single student using template repository directly
help_single_student() {
    local repo_url="$1"
    local student_name=$(get_student_name "$repo_url")
    local work_dir="$TEMP_DIR/$student_name"
    
    print_header "Helping Single Student: $student_name"
    
    # Validate URL
    if ! validate_repo_url "$repo_url"; then
        return 1
    fi
    
    # Basic repository access check (no classroom comparison)
    print_status "Checking repository access..."
    if ! git ls-remote "$repo_url" &>/dev/null; then
        print_error "Cannot access student repository: $repo_url"
        return 1
    fi
    print_success "Student repository is accessible"
    
    # Show template information
    if [ -n "${TEMPLATE_REPO_URL:-}" ]; then
        print_status "Template repository: $TEMPLATE_REPO_URL"
    fi
    
    # Ask for confirmation to proceed
    echo
    print_warning "This will clone the student's repository and apply template updates"
    if ! confirm_action "Do you want to proceed?"; then
        print_status "Operation cancelled"
        return 0
    fi
    
    # Setup work directory
    print_status "Setting up work directory..."
    rm -rf "$work_dir"
    mkdir -p "$work_dir"
    
    # Clone student repository
    print_status "Cloning student repository..."
    if ! git clone "$repo_url" "$work_dir"; then
        print_error "Failed to clone student repository"
        return 1
    fi
    
    cd "$work_dir"
    
    # Add template as remote (use TEMPLATE_REPO_URL from config)
    local template_url="${TEMPLATE_REPO_URL}"
    if [[ -z "$template_url" ]]; then
        print_error "TEMPLATE_REPO_URL not set in configuration"
        return 1
    fi
    print_status "Adding template repository as upstream..."
    git remote add upstream "$template_url"
    
    # Fetch updates from template
    print_status "Fetching updates from template repository..."
    if ! git fetch upstream; then
        print_error "Failed to fetch from template repository"
        return 1
    fi
    
    # Create backup branch
    local backup_branch="backup-before-update-$(date +%Y%m%d-%H%M%S)"
    print_status "Creating backup branch: $backup_branch"
    git checkout -b "$backup_branch"
    git checkout main
    
    # Apply updates from template
    print_status "Applying updates from template..."
    if git merge upstream/main --no-edit --allow-unrelated-histories; then
        print_success "Updates applied successfully!"
        
        # Push changes back to student repository
        print_status "Pushing updates to student repository..."
        if git push origin main; then
            print_success "Student repository updated successfully!"
            print_status "Student should now pull the latest changes"
            return 0
        else
            print_error "Failed to push updates to student repository"
            return 1
        fi
    else
        print_warning "Merge conflicts detected. Attempting automatic resolution..."
        
        # Reset to before merge
        git merge --abort 2>/dev/null || true
        
        if git merge upstream/main --no-edit --allow-unrelated-histories -X theirs; then
            print_status "Automatic resolution succeeded, preserving student work..."
            
            # Restore student's assignment file from backup branch
            # Support universal file types with backward compatibility
            ASSIGNMENT_FILE="${ASSIGNMENT_FILE:-${ASSIGNMENT_NOTEBOOK:-assignment.ipynb}}"
            git checkout "$backup_branch" -- "$ASSIGNMENT_FILE" 2>/dev/null || true
            
            # Commit the preserved student work
            if git diff --cached --quiet; then
                # No staged changes, add any modified files
                git add . 2>/dev/null || true
            fi
            
            if ! git diff --cached --quiet; then
                git commit -m "Preserve student work after template update"
            fi
            
            print_status "Pushing resolved updates..."
            if git push origin main; then
                print_success "Updates with conflict resolution applied successfully!"
                print_status "Student should pull the latest changes"
                return 0
            else
                print_error "Failed to push resolved updates"
                return 1
            fi
        else
            print_error "Automatic conflict resolution failed"
            print_error "Manual intervention required"
            print_status "Backup created in branch: $backup_branch"
            return 1
        fi
    fi
}

# Function to help a specific student
help_student() {
    local repo_url="$1"
    local student_name=$(get_student_name "$repo_url")
    local work_dir="$TEMP_DIR/$student_name"
    
    print_header "Helping Student: $student_name"
    
    # Validate URL
    if ! validate_repo_url "$repo_url"; then
        return 1
    fi
    
    # Check status first
    local status_result=0
    set +e  # Temporarily disable exit on error
    check_student_status "$repo_url"
    status_result=$?
    set -e  # Re-enable exit on error
    
    if [ $status_result -eq 0 ]; then
        print_success "Student is already up to date. No action needed."
        return 0
    elif [ $status_result -eq 1 ]; then
        print_error "Cannot proceed due to access issues"
        return 1
    fi
    
    # Ask for confirmation to proceed
    echo
    print_warning "This will clone the student's repository and apply updates"
    if ! confirm_action "Do you want to proceed?"; then
        print_status "Operation cancelled"
        return 0
    fi
    
    # Setup work directory
    print_status "Setting up work directory..."
    rm -rf "$work_dir"
    mkdir -p "$work_dir"
    
    # Clone student repository
    print_status "Cloning student repository..."
    if ! git clone "$repo_url" "$work_dir"; then
        print_error "Failed to clone student repository"
        return 1
    fi
    
    cd "$work_dir"
    
    # Add classroom as remote
    print_status "Adding classroom remote..."
    git remote add upstream "$CLASSROOM_REPO_URL"

    # Fetch updates
    print_status "Fetching updates from classroom..."
    git fetch upstream
    
    # Create backup branch
    local backup_branch="backup-before-update-$(date +%Y%m%d-%H%M%S)"
    print_status "Creating backup branch: $backup_branch"
    git checkout -b "$backup_branch"
    git checkout main
    
    # Apply updates
    print_status "Applying updates..."
    if git merge upstream/main --no-edit --allow-unrelated-histories; then
        print_success "Updates applied successfully!"
        
        # Push changes
        print_status "Pushing updates to student repository..."
        if git push origin main && git push origin "$backup_branch"; then
            print_success "Successfully updated student repository!"
            
            # Generate summary
            echo
            print_header "Update Summary for $student_name"
            echo "✅ Backup created: $backup_branch"
            echo "✅ Updates applied from classroom repository"
            echo "✅ Changes pushed to student repository"
            echo
            print_student "Student can now pull the latest changes:"
            print_student "  git pull origin main"
            
        else
            print_error "Failed to push changes"
            print_error "You may need to resolve this manually"
        fi
        
    else
        print_warning "Merge conflicts detected!"
        echo
        print_status "Attempting automatic conflict resolution..."
        
        # Try to resolve automatically by favoring template changes for infrastructure files
        # but preserving student work in the main assignment file
        git merge --abort 2>/dev/null || true
        
        if git merge upstream/main --no-edit --allow-unrelated-histories -X theirs; then
            print_status "Automatic resolution succeeded, preserving student work..."
            
            # Restore student's assignment file from backup branch
            # Support universal file types with backward compatibility
            ASSIGNMENT_FILE="${ASSIGNMENT_FILE:-${ASSIGNMENT_NOTEBOOK:-assignment.ipynb}}"
            git checkout "$backup_branch" -- "$ASSIGNMENT_FILE" 2>/dev/null || true
            
            # Commit the preserved student work
            if git diff --cached --quiet; then
                # No staged changes, add any modified files
                git add . 2>/dev/null || true
            fi
            
            if ! git diff --cached --quiet; then
                git commit -m "Preserve student work in notebook after template update" || true
            fi
            
            # Push changes
            print_status "Pushing updates to student repository..."
            if git push origin main && git push origin "$backup_branch"; then
                print_success "Successfully updated with automatic conflict resolution!"
                
                # Generate summary
                echo
                print_header "Update Summary for $student_name"
                echo "✅ Backup created: $backup_branch"
                echo "✅ Updates applied with automatic conflict resolution"
                echo "✅ Student notebook work preserved"
                echo "✅ Changes pushed to student repository"
                echo
                print_student "Student can now pull the latest changes:"
                print_student "  git pull origin main"
                
            else
                print_error "Failed to push changes after automatic resolution"
            fi
            
        else
            print_warning "Automatic resolution failed. Manual intervention required."
            echo
            print_status "Conflict resolution needed:"
            git status --porcelain | grep "^UU" | while read -r line; do
                echo "  - ${line:3}"
            done
            
            echo
            print_warning "Manual intervention required:"
            echo "1. Navigate to: $work_dir"
            echo "2. Resolve conflicts in the files listed above"
            echo "3. Run: git add <resolved-files>"
            echo "4. Run: git commit -m 'Resolve merge conflicts'"
            echo "5. Run: git push origin main && git push origin $backup_branch"
            echo
        fi
        
        print_status "Work directory preserved at: $work_dir"
        print_status "You can navigate there to resolve conflicts manually"
    fi
    
    cd - > /dev/null
    return 0
}

# Function to process multiple students
batch_help_students() {
    local repo_file="$1"
    
    if [ ! -f "$repo_file" ]; then
        print_error "Repository file not found: $repo_file"
        return 1
    fi
    
    print_header "Batch Processing Students"
    
    if [ "$AUTO_CONFIRM" = true ]; then
        print_status "Auto-confirm mode enabled - all prompts will be automatically accepted"
    fi
    
    # Count total repositories
    local total_repos=$(grep -c "^https://" "$repo_file" || echo "0")
    print_status "Found $total_repos student repositories to process"
    
    if [ "$total_repos" -eq 0 ]; then
        print_error "No valid repository URLs found in file"
        return 1
    fi
    
    # Ask for confirmation
    echo
    if ! confirm_action "Process all $total_repos repositories?"; then
        print_status "Batch processing cancelled"
        return 0
    fi
    
    # Process each repository
    local count=0
    local success_count=0
    local skip_count=0
    local error_count=0
    
    # echo "DEBUG: Starting to read from file: $repo_file" >&2
    
    # Read entire file into array to avoid I/O conflicts during processing
    local repo_urls=()
    while IFS= read -r line; do
        # echo "DEBUG: Read line from file: '$line'" >&2
        # Skip empty lines and comments
        [[ "$line" =~ ^[[:space:]]*$ ]] && continue
        [[ "$line" =~ ^[[:space:]]*# ]] && continue
        
        # Clean input more carefully - only remove known problematic characters
        # Remove carriage returns first
        line=$(echo "$line" | tr -d '\r')
        # Remove leading/trailing whitespace
        line=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        # Remove BOM if present (only at very beginning)
        if [[ "$line" =~ ^\xEF\xBB\xBF ]]; then
            line="${line#???}"  # Remove first 3 bytes (BOM)
        fi
        
        # Add to array if it looks like a URL
        if [[ "$line" =~ ^https:// ]]; then
            repo_urls+=("$line")
            # echo "DEBUG: Added to array: '$line'" >&2
        fi
    done < "$repo_file"
    
    # echo "DEBUG: Total URLs found: ${#repo_urls[@]}" >&2
    
    # Now process each URL from the array
    for repo_url in "${repo_urls[@]}"; do
        # echo "DEBUG: Processing from array: '$repo_url'" >&2
        
        count=$((count + 1))
        local student_name=$(get_student_name "$repo_url")
        
        echo
        print_status "Processing $count/${#repo_urls[@]}: $repo_url"
        
        # Check status first
        local status_result=0
        check_student_status "$repo_url" || status_result=$?
        
        if [ $status_result -eq 0 ]; then
            print_success "Already up to date - skipping"
            skip_count=$((skip_count + 1))
        elif [ $status_result -eq 1 ]; then
            print_error "Access error - skipping"
            error_count=$((error_count + 1))
        else
            # Try to help the student
            if help_student "$repo_url"; then
                success_count=$((success_count + 1))
            else
                error_count=$((error_count + 1))
            fi
        fi
        
    done
    
    # Summary
    echo
    print_header "Batch Processing Summary"
    echo "Total processed: $count"
    echo "Successfully updated: $success_count"
    echo "Already up to date: $skip_count"
    echo "Errors/skipped: $error_count"
    
    if [ $error_count -gt 0 ]; then
        print_warning "Some repositories had issues. Check output above for details."
    fi
    
    return 0
}

# Function to generate student instructions
generate_instructions() {
    local repo_url="$1"
    local student_name=$(get_student_name "$repo_url")
    
    print_header "Update Instructions for $student_name"
    
    cat << EOF

Dear $student_name,

There are updates available for the assignment template. Please follow these steps to update your repository:

OPTION 1 - Automated Script (Recommended):
1. Open your terminal in your assignment directory
2. Run: ./scripts_legacy/update-assignment.sh
3. Follow the prompts

OPTION 2 - Manual Process:
1. Save and commit your current work:
   git add .
   git commit -m "Save work before template update"

2. Add the template as a remote (one-time setup):
   git remote add upstream $CLASSROOM_REPO_URL

3. Get the updates:
   git fetch upstream
   git merge upstream/main

4. If there are conflicts, resolve them and commit:
   git add .
   git commit -m "Resolve merge conflicts"

OPTION 3 - Detailed Guide:
Follow the complete guide in: docs/UPDATE-GUIDE.md

If you encounter any issues, please:
- Check the troubleshooting section in docs/UPDATE-GUIDE.md
- Ask for help during office hours
- Contact the instructor

Best regards,
Instructional Team

EOF
}

# Main script logic
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
        print_status "Loading assignment configuration from: $ASSIGNMENT_ROOT/assignment.conf"
        source "$ASSIGNMENT_ROOT/assignment.conf"
    fi
    
    # Check if we're in a valid assignment repository
    # Support universal file types with backward compatibility
    ASSIGNMENT_FILE="${ASSIGNMENT_FILE:-${ASSIGNMENT_NOTEBOOK:-assignment.ipynb}}"
    if [ ! -f "$ASSIGNMENT_ROOT/$ASSIGNMENT_FILE" ]; then
        print_error "This script must be run from the template repository root"
        print_error "Please navigate to the assignment template directory"
        print_error "Assignment root detected as: $ASSIGNMENT_ROOT"
        print_error "Expected assignment file: $ASSIGNMENT_FILE"
        exit 1
    fi
    
    # Parse arguments
    local command=""
    local target=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help|-h)
                show_help
                exit 0
                ;;
            --yes)
                AUTO_CONFIRM=true
                shift
                ;;
            --check-classroom)
                command="check-classroom"
                shift
                ;;
            --status)
                command="status"
                target="$2"
                if [ -z "$target" ]; then
                    print_error "Student repository URL required for --status"
                    print_error "Usage: $0 --status [student-repo-url]"
                    exit 1
                fi
                shift 2
                ;;
            --one-student)
                command="one-student"
                target="$2"
                if [ -z "$target" ]; then
                    print_error "Student repository URL required for --one-student"
                    print_error "Usage: $0 --one-student [student-repo-url]"
                    exit 1
                fi
                shift 2
                ;;
            --batch)
                command="batch"
                target="$2"
                if [ -z "$target" ]; then
                    print_error "Repository file required for --batch"
                    print_error "Usage: $0 --batch [file-with-repo-urls] [--yes]"
                    exit 1
                fi
                shift 2
                ;;
            --instructions)
                command="instructions"
                target="$2"
                if [ -z "$target" ]; then
                    print_error "Student repository URL required for --instructions"
                    exit 1
                fi
                shift 2
                ;;
            "")
                if [ -z "$command" ]; then
                    print_error "Student repository URL required"
                    echo
                    show_help
                    exit 1
                fi
                break
                ;;
            -*)
                print_error "Unknown option: $1"
                echo
                show_help
                exit 1
                ;;
            *)
                if [ -z "$command" ]; then
                    # Single student repository URL
                    command="single"
                    target="$1"
                fi
                shift
                ;;
        esac
    done
    
    # Execute the command
    case "$command" in
        "check-classroom")
            check_classroom_ready
            exit $?
            ;;
        "status")
            check_student_status "$target"
            exit $?
            ;;
        "one-student")
            help_single_student "$target"
            exit $?
            ;;
        "batch")
            batch_help_students "$target"
            exit $?
            ;;
        "instructions")
            generate_instructions "$target"
            exit 0
            ;;
        "single")
            help_student "$target"
            exit $?
            ;;
        "")
            print_error "No command specified"
            echo
            show_help
            exit 1
            ;;
    esac
}

# Cleanup function
cleanup() {
    if [ -d "$TEMP_DIR" ]; then
        print_status "Cleaning up temporary files..."
        rm -rf "$TEMP_DIR"
    fi
}

# Set up cleanup trap
trap cleanup EXIT

# Run main function
main "$@"
