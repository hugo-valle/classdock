#!/bin/bash
set -euo pipefail

# Integration test configuration generator
# Creates test configuration files for various scenarios

source "$(dirname "$0")/workflow_utils.sh"

CONFIG_TYPE="${1:-basic}"
# Default output directory
OUTPUT_DIR="${2:-tests/fixtures}"

mkdir -p "$OUTPUT_DIR"

case "$CONFIG_TYPE" in
    "basic")
        print_message "step" "Creating basic test configuration"
        cat > "$OUTPUT_DIR/test_assignment.conf" << 'EOF'
# Basic test assignment configuration
TEMPLATE_REPO_URL="https://github.com/test-org/assignment-template"
GITHUB_ORGANIZATION="test-org"
ASSIGNMENT_NAME="test-assignment"
ASSIGNMENT_FILE="assignment.ipynb"

# Optional settings for testing
SECRETS_LIST="API_KEY,DATABASE_URL"
EXCLUDE_REPOS="template,example"
DRY_RUN=true
EOF
        ;;
    "minimal")
        print_message "step" "Creating minimal test configuration"
        cat > "$OUTPUT_DIR/minimal_assignment.conf" << 'EOF'
# Minimal test assignment configuration
TEMPLATE_REPO_URL="https://github.com/test-org/minimal-template"
GITHUB_ORGANIZATION="test-org"
ASSIGNMENT_NAME="minimal-test"
ASSIGNMENT_FILE="homework.py"
EOF
        ;;
    "advanced")
        print_message "step" "Creating advanced test configuration"
        cat > "$OUTPUT_DIR/advanced_assignment.conf" << 'EOF'
# Advanced test assignment configuration with all options
TEMPLATE_REPO_URL="https://github.com/test-org/advanced-template"
GITHUB_ORGANIZATION="test-org"
ASSIGNMENT_NAME="advanced-test"
ASSIGNMENT_FILE="lab_notebook.ipynb"

# Advanced features
SECRETS_LIST="API_KEY,DATABASE_URL,SECRET_TOKEN,THIRD_PARTY_KEY"
EXCLUDE_REPOS="template,example,demo,instructor-solution"
INSTRUCTOR_REPOS="instructor-advanced-solution"
MAX_REPOS=100
SECRET_MAX_AGE_DAYS=90
SECRET_FORCE_UPDATE=false

# Workflow control
STEP_SYNC_TEMPLATE=true
STEP_DISCOVER_REPOS=true
STEP_MANAGE_SECRETS=true
STEP_ASSIST_STUDENTS=false
STEP_CYCLE_COLLABORATORS=false

# Output settings
OUTPUT_DIR="advanced_scripts"
STUDENT_REPOS_FILE="advanced-student-repos.txt"
DRY_RUN=true
EOF
        ;;
    "edge-case")
        print_message "step" "Creating edge case test configuration"
        cat > "$OUTPUT_DIR/edge_case_assignment.conf" << 'EOF'
# Edge case test assignment configuration
TEMPLATE_REPO_URL="https://github.com/edge-case-org/special-chars-template"
GITHUB_ORGANIZATION="edge-case-org"
ASSIGNMENT_NAME="edge-case-test"
ASSIGNMENT_FILE="special_assignment.md"

# Edge case values
SECRETS_LIST=""
EXCLUDE_REPOS=""
MAX_REPOS=1
SECRET_MAX_AGE_DAYS=1
DRY_RUN=true
EOF
        ;;
    "invalid")
        print_message "step" "Creating invalid test configuration"
        cat > "$OUTPUT_DIR/invalid_assignment.conf" << 'EOF'
ASSIGNMENT_NAME=""
ORGANIZATION=""
TEMPLATE_REPO=""
STUDENT_REPOS=""
MAX_REPOS=invalid
EOF
        ;;
    *)
        print_message "error" "Unknown configuration type: $CONFIG_TYPE"
        exit 1
        ;;
esac

print_message "success" "Created $CONFIG_TYPE configuration in $OUTPUT_DIR"