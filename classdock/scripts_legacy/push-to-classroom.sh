#!/bin/bash

# =============================================================================
# push-to-classroom.sh
# 
# Script to push template changes to GitHub Classroom repository
# 
# This script automates the process of updating the GitHub Classroom copy
# when you make changes to your original template repository.
#
# Usage: ./scripts_legacy/push-to-classroom.sh [--force]
# =============================================================================

set -e  # Exit on any error

# Configuration
CLASSROOM_REMOTE="classroom"
BRANCH="main"

# NOTE: CLASSROOM_REPO_URL is now loaded from assignment.conf
# This should be the GitHub Classroom repository URL (not the assignment page URL)
# Format: https://github.com/[ORG]/[classroom-semester-assignment-name]

# Function to print colored output
# Source shared logging utility
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../utils/logging.sh"

# Function to check if we're in the right repository
check_repository() {
    print_status "Checking repository..."
    
    # Determine the assignment repository root when script is in tools submodule
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    if [[ "$SCRIPT_DIR" == */tools/scripts ]]; then
        # Running from tools submodule - assignment root is two levels up
        ASSIGNMENT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
    else
        # Running from legacy location - assignment root is two levels up
        ASSIGNMENT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
    fi
    
    # Load assignment configuration if available
    if [ -f "$ASSIGNMENT_ROOT/assignment.conf" ]; then
        echo "[INFO] Loading assignment configuration from: $ASSIGNMENT_ROOT/assignment.conf"
        source "$ASSIGNMENT_ROOT/assignment.conf"
    fi
    
    # Validate required configuration
    if [ -z "${CLASSROOM_REPO_URL:-}" ]; then
        print_error "CLASSROOM_REPO_URL is not set in assignment.conf"
        print_error "Please add the GitHub Classroom repository URL to your configuration:"
        print_error "CLASSROOM_REPO_URL=\"https://github.com/ORG/classroom-semester-assignment-name\""
        print_error ""
        print_error "This is different from CLASSROOM_URL (which is the assignment page URL)"
        exit 1
    fi
    
    cd "$ASSIGNMENT_ROOT"
    
    if [ ! -d ".git" ]; then
        print_error "Not in a git repository. Please run this script from the template repository root."
        exit 1
    fi
    
    # Check if this looks like the template repository
    # Support universal file types with backward compatibility
    ASSIGNMENT_FILE="${ASSIGNMENT_FILE:-${ASSIGNMENT_NOTEBOOK:-assignment.ipynb}}"
    if [ ! -f "$ASSIGNMENT_FILE" ]; then
        print_error "This doesn't appear to be the template repository."
        print_error "Please run this script from the assignment template directory."
        print_error "Assignment root detected as: $ASSIGNMENT_ROOT"
        print_error "Expected assignment file: $ASSIGNMENT_FILE"
        exit 1
    fi
    
    print_success "Repository check passed"
}

# Function to check if there are uncommitted changes
check_clean_working_tree() {
    print_status "Checking for uncommitted changes..."
    
    if [ -n "$(git status --porcelain)" ]; then
        print_error "You have uncommitted changes in your working directory."
        echo
        git status --short
        echo
        print_error "Please commit or stash your changes before running this script."
        exit 1
    fi
    
    print_success "Working directory is clean"
}

# Function to setup classroom remote if it doesn't exist
setup_classroom_remote() {
    print_status "Setting up classroom remote..."
    
    if git remote | grep -q "^${CLASSROOM_REMOTE}$"; then
        print_status "Classroom remote already exists"
        
        # Update the URL in case it changed
        git remote set-url ${CLASSROOM_REMOTE} ${CLASSROOM_REPO_URL}
        print_status "Updated classroom remote URL"
    else
        print_status "Adding classroom remote..."
        git remote add ${CLASSROOM_REMOTE} ${CLASSROOM_REPO_URL}
        print_success "Added classroom remote"
    fi
}

# Function to fetch classroom repository state
fetch_classroom() {
    print_status "Fetching classroom repository state..."
    
    if git fetch ${CLASSROOM_REMOTE}; then
        print_success "Fetched classroom repository"
    else
        print_error "Failed to fetch classroom repository"
        print_error "Please check your network connection and repository access"
        exit 1
    fi
}

# Function to compare repositories
compare_repositories() {
    print_status "Comparing local and classroom repositories..."
    
    # Get the latest commit hashes
    LOCAL_COMMIT=$(git rev-parse ${BRANCH})
    CLASSROOM_COMMIT=$(git rev-parse ${CLASSROOM_REMOTE}/${BRANCH} 2>/dev/null || echo "none")
    
    echo "  Local commit:     ${LOCAL_COMMIT:0:8}"
    echo "  Classroom commit: ${CLASSROOM_COMMIT:0:8}"
    
    if [ "$LOCAL_COMMIT" = "$CLASSROOM_COMMIT" ]; then
        print_success "Repositories are already in sync!"
        echo
        print_status "No changes to push. Exiting."
        exit 0
    fi
    
    # Show what files will be updated
    print_status "Files that will be updated in classroom repository:"
    echo
    
    if [ "$CLASSROOM_COMMIT" != "none" ]; then
        # Show diff summary
        git diff --name-status ${CLASSROOM_REMOTE}/${BRANCH}..${BRANCH} || true
    else
        print_warning "Classroom repository appears to be empty or newly created"
    fi
    
    echo
}

# Function to ask for confirmation
ask_confirmation() {
    if [ "$FORCE_PUSH" = "true" ]; then
        print_warning "Force mode enabled - skipping confirmation"
        return 0
    fi
    
    echo -e "${YELLOW}Do you want to push these changes to the classroom repository?${NC}"
    echo "This will update the repository that students fork from."
    echo
    read -p "Continue? [y/N] " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Operation cancelled by user"
        exit 0
    fi
}

# Function to push changes
push_to_classroom() {
    print_status "Pushing changes to classroom repository..."
    
    # Determine if we need to force push
    PUSH_ARGS=""
    if [ "$FORCE_PUSH" = "true" ] || ! git merge-base --is-ancestor ${CLASSROOM_REMOTE}/${BRANCH} ${BRANCH} 2>/dev/null; then
        print_warning "Force push required (histories have diverged)"
        PUSH_ARGS="--force"
    fi
    
    if git push ${CLASSROOM_REMOTE} ${BRANCH} ${PUSH_ARGS}; then
        print_success "Successfully pushed changes to classroom repository!"
    else
        print_error "Failed to push changes"
        print_error "You may need to check repository permissions or network connectivity"
        exit 1
    fi
}

# Function to verify the push
verify_push() {
    print_status "Verifying push was successful..."
    
    # Fetch the latest state
    git fetch ${CLASSROOM_REMOTE}
    
    # Compare commits again
    LOCAL_COMMIT=$(git rev-parse ${BRANCH})
    CLASSROOM_COMMIT=$(git rev-parse ${CLASSROOM_REMOTE}/${BRANCH})
    
    if [ "$LOCAL_COMMIT" = "$CLASSROOM_COMMIT" ]; then
        print_success "Verification passed - repositories are now in sync!"
    else
        print_error "Verification failed - commits don't match"
        exit 1
    fi
}

# Function to show next steps
show_next_steps() {
    echo
    print_success "Template update complete!"
    echo
    echo "📋 Next Steps:"
    echo "  1. Announce the update to students via:"
    echo "     - Course announcement"
    echo "     - Email notification"
    echo "     - Canvas/LMS message"
    echo
    echo "  2. Direct students to update their repositories using:"
    echo "     - Automated script: ./scripts_legacy/update-assignment.sh"
    echo "     - Manual process: docs/UPDATE-GUIDE.md"
    echo
    echo "  3. Monitor for student questions and provide support"
    echo
    echo "  4. Check that student tests still pass with the updates"
    echo
    print_status "Classroom repository URL: ${CLASSROOM_REPO_URL}"
}

# Main script logic
main() {
    echo "=============================================================================="
    echo "🚀 Template to Classroom Repository Update Script"
    echo "=============================================================================="
    echo
    
    # Parse command line arguments
    FORCE_PUSH="false"
    for arg in "$@"; do
        case $arg in
            --force)
                FORCE_PUSH="true"
                print_warning "Force mode enabled"
                ;;
            --help|-h)
                echo "Usage: $0 [--force]"
                echo
                echo "Options:"
                echo "  --force    Skip confirmation and force push if needed"
                echo "  --help     Show this help message"
                echo
                echo "This script pushes changes from your template repository"
                echo "to the GitHub Classroom copy that students fork from."
                exit 0
                ;;
            *)
                print_error "Unknown argument: $arg"
                print_error "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Run all the steps
    check_repository
    check_clean_working_tree
    setup_classroom_remote
    fetch_classroom
    compare_repositories
    ask_confirmation
    push_to_classroom
    verify_push
    show_next_steps
    
    echo
    print_success "All done! 🎉"
}

# Run the main function
main "$@"
