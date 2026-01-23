#!/bin/bash
#
# GitHub Classroom Assignment Setup Script
# 
# This script provides an interactive setup wizard for instructors to configure
# a new GitHub Classroom assignment with automated tools. It creates all necessary
# configuration files and sets up the environment for seamless assignment management.
#
# Features:
# - Interactive prompts for all configuration values
# - Intelligent defaults and validation
# - Secure token file creation and .gitignore management
# - Configuration file generation with comprehensive comments
# - Elegant, modern interface with progress indicators
#

set -e

# Source shared utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../utils/logging.sh"

# Configuration
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CONFIG_FILE="$REPO_ROOT/assignment.conf"
GITIGNORE_FILE="$REPO_ROOT/.gitignore"
TOKEN_FILE="$REPO_ROOT/instructor_token.txt"

# Setup wizard data
declare -A CONFIG_VALUES
declare -A TOKEN_FILES
declare -A TOKEN_VALIDATION  # Store validation choices for each secret
PROMPT_RESULT=""  # Global variable for prompt results

# Progress tracking
TOTAL_STEPS=8
CURRENT_STEP=0

# Function to show progress
show_progress() {
    local step_name="$1"
    CURRENT_STEP=$((CURRENT_STEP + 1))
    echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${PURPLE}📋 Step ${CURRENT_STEP}/${TOTAL_STEPS}: ${step_name}${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Function to prompt for input with validation
prompt_input() {
    local prompt="$1"
    local default="$2"
    local validator="$3"
    local help_text="$4"
    local value
    
    while true; do
        if [ -n "$help_text" ]; then
            echo -e "${BLUE}💡 ${help_text}${NC}"
        fi
        
        if [ -n "$default" ]; then
            echo -e -n "${GREEN}${prompt} ${YELLOW}[${default}]${NC}: "
        else
            echo -e -n "${GREEN}${prompt}${NC}: "
        fi
        
        # Read input from appropriate source
        if [[ -t 0 ]]; then
            # Interactive mode: read from stdin
            read -r value
        elif [[ -t 1 ]] && [[ -r /dev/tty ]]; then
            # Non-interactive with tty available: read from tty
            read -r value < /dev/tty
        else
            # Fallback: read from stdin, or use default if non-interactive
            if read -r value 2>/dev/null; then
                : # Successfully read from stdin
            else
                # No input available, use default or empty
                value="${default:-}"
            fi
        fi
        
        # Use default if empty
        if [ -z "$value" ] && [ -n "$default" ]; then
            value="$default"
        fi
        
        # Validate input if validator provided
        if [ -n "$validator" ]; then
            if $validator "$value"; then
                PROMPT_RESULT="$value"
                return 0
            else
                print_error "Invalid input. Please try again."
                continue
            fi
        else
            PROMPT_RESULT="$value"
            return 0
        fi
    done
}

# Function to prompt for secure input (passwords/tokens)
prompt_secure() {
    local prompt="$1"
    local help_text="$2"
    local value
    
    if [ -n "$help_text" ]; then
        echo -e "${BLUE}💡 ${help_text}${NC}"
    fi
    
    echo -e -n "${GREEN}${prompt}${NC}: "
    # Only read input if we have a TTY (interactive terminal)
    if [[ -t 0 ]]; then
        read -rs value
    else
        # In non-interactive mode, read from stdin
        read -r value || value=""
    fi
    echo  # New line after hidden input
    PROMPT_RESULT="$value"
}

# Validation functions
validate_url() {
    local url="$1"
    if [[ "$url" =~ ^https://github\.com/.+/.+$ ]]; then
        return 0
    elif [[ "$url" =~ ^https://classroom\.github\.com/classrooms/.+/assignments/.+$ ]]; then
        return 0
    else
        print_error "Please enter a valid GitHub or GitHub Classroom URL"
        return 1
    fi
}

validate_organization() {
    local org="$1"
    if [[ "$org" =~ ^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$ ]]; then
        return 0
    else
        print_error "Organization name must contain only letters, numbers, and hyphens"
        return 1
    fi
}

validate_assignment_name() {
    local name="$1"
    if [[ "$name" =~ ^[a-zA-Z0-9]([a-zA-Z0-9_-]*[a-zA-Z0-9])?$ ]]; then
        return 0
    else
        print_error "Assignment name must contain only letters, numbers, hyphens, and underscores"
        return 1
    fi
}

validate_file_path() {
    local file="$1"
    if [[ "$file" =~ \.(ipynb|py|cpp|sql|md|html|js|ts|java|c|h|hpp|txt)$ ]]; then
        return 0
    else
        print_error "Please specify a valid file extension (.ipynb, .py, .cpp, .sql, .md, etc.)"
        return 1
    fi
}

validate_non_empty() {
    local value="$1"
    if [ -n "$value" ]; then
        return 0
    else
        print_error "This field cannot be empty"
        return 1
    fi
}

# Function to extract assignment name from URL
extract_assignment_from_url() {
    local url="$1"
    if [[ "$url" =~ /([^/]+)/?$ ]]; then
        echo "${BASH_REMATCH[1]}"
    else
        echo ""
    fi
}

# Function to extract organization from URL
extract_org_from_url() {
    local url="$1"
    if [[ "$url" =~ github\.com/([^/]+)/ ]]; then
        echo "${BASH_REMATCH[1]}"
    else
        echo ""
    fi
}

# Function to create configuration file
create_config_file() {
    print_header "Creating Assignment Configuration"
    
    cat > "$CONFIG_FILE" << EOF
# GitHub Classroom Assignment Configuration
# Generated by setup-assignment.sh on $(date)
# This file contains all the necessary information to manage a GitHub Classroom assignment

# =============================================================================
# ASSIGNMENT INFORMATION
# =============================================================================

# GitHub Classroom assignment URL (used to extract assignment name and discover student repos)
# This is the URL you see when managing the assignment in GitHub Classroom
# Example: https://classroom.github.com/classrooms/12345/assignments/assignment-name
CLASSROOM_URL="${CONFIG_VALUES[CLASSROOM_URL]}"

# GitHub Classroom repository URL (OPTIONAL - only needed for push-to-classroom.sh)
# This is the actual repository URL created by GitHub Classroom for the assignment
# Different from CLASSROOM_URL above - this is the git repository URL
# Format: https://github.com/[ORG]/[classroom-semester-assignment-name]
# To find this: look for a repo in your organization with a name like "classroom-fall25-assignment-name"
EOF

    if [ -n "${CONFIG_VALUES[CLASSROOM_REPO_URL]}" ]; then
        echo "CLASSROOM_REPO_URL=\"${CONFIG_VALUES[CLASSROOM_REPO_URL]}\"" >> "$CONFIG_FILE"
    else
        echo "# CLASSROOM_REPO_URL=\"\"  # Optional - add if using push-to-classroom.sh" >> "$CONFIG_FILE"
    fi

    cat >> "$CONFIG_FILE" << EOF

# Template repository URL (source of truth for updates)
TEMPLATE_REPO_URL="${CONFIG_VALUES[TEMPLATE_REPO_URL]}"

# GitHub organization name (usually extracted from URLs but can be overridden)
GITHUB_ORGANIZATION="${CONFIG_VALUES[GITHUB_ORGANIZATION]}"

# Assignment name (auto-extracted from classroom URL if not specified)
EOF

    if [ -n "${CONFIG_VALUES[ASSIGNMENT_NAME]}" ]; then
        echo "ASSIGNMENT_NAME=\"${CONFIG_VALUES[ASSIGNMENT_NAME]}\"" >> "$CONFIG_FILE"
    else
        echo "# ASSIGNMENT_NAME=\"\"  # Auto-extracted from template URL if not specified" >> "$CONFIG_FILE"
    fi

    cat >> "$CONFIG_FILE" << EOF

# Main assignment file (the primary file students work on - any type)
# Universal support: .ipynb, .py, .cpp, .sql, .md, .html, etc.
ASSIGNMENT_FILE="${CONFIG_VALUES[MAIN_ASSIGNMENT_FILE]}"

# =============================================================================
# SECRET MANAGEMENT
# =============================================================================

EOF

    # Conditionally add secrets configuration based on user choice
    if [[ "${CONFIG_VALUES[USE_SECRETS]}" == "true" ]]; then
        cat >> "$CONFIG_FILE" << EOF
# Secrets to add to student repositories
# Format: SECRET_NAME:description:token_file_path:max_age_days:validate_format
# validate_format: true for GitHub tokens (ghp_), false for other secrets like passwords
# 
# Use this when you have a separate private instructor repository with tests
# that students need access to via GitHub secrets.
SECRETS_CONFIG="
INSTRUCTOR_TESTS_TOKEN:Token for accessing instructor test repository:instructor_token.txt:90:${TOKEN_VALIDATION[INSTRUCTOR_TESTS_TOKEN]}
EOF

        # Add additional secrets if configured
        for secret_name in "${!TOKEN_FILES[@]}"; do
            if [ "$secret_name" != "INSTRUCTOR_TESTS_TOKEN" ]; then
                local validation_choice="${TOKEN_VALIDATION[$secret_name]}"
                local description="${CONFIG_VALUES[${secret_name}_DESCRIPTION]}"
                echo "${secret_name}:${description}:${TOKEN_FILES[$secret_name]}:90:${validation_choice}" >> "$CONFIG_FILE"
            fi
        done

        cat >> "$CONFIG_FILE" << EOF
"
EOF
    else
        cat >> "$CONFIG_FILE" << EOF
# Secrets to add to student repositories
# Format: SECRET_NAME:description:token_file_path:max_age_days:validate_format
# validate_format: true for GitHub tokens (ghp_), false for other secrets like passwords
# 
# Use this when you have a separate private instructor repository with tests
# that students need access to via GitHub secrets.
# 
# If your tests are included in the same template repository, you can:
# 1. Set STEP_MANAGE_SECRETS=false in the WORKFLOW CONFIGURATION section, OR
# 2. Leave SECRETS_CONFIG empty (comment out or set to empty string)
# SECRETS_CONFIG="
# INSTRUCTOR_TESTS_TOKEN:Token for accessing instructor test repository:instructor_token.txt:90
# "

# For assignments where tests are in the template repository, use:
SECRETS_CONFIG=""
EOF
    fi

    cat >> "$CONFIG_FILE" << EOF

# =============================================================================
# WORKFLOW CONFIGURATION
# =============================================================================

# Workflow steps to execute (true/false)
STEP_SYNC_TEMPLATE=true
STEP_DISCOVER_REPOS=true
STEP_MANAGE_SECRETS=${CONFIG_VALUES[USE_SECRETS]}   # Set to false if tests are in template repo (no separate instructor repo)
STEP_ASSIST_STUDENTS=false

# Output directory for generated files
OUTPUT_DIR="tools/generated"

# =============================================================================
# ADVANCED CONFIGURATION
# =============================================================================

# Repository filtering
EXCLUDE_INSTRUCTOR_REPOS=true
INCLUDE_TEMPLATE_REPO=false

# Dry run mode (for testing)
DEFAULT_DRY_RUN=false

# Logging level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Confirmation prompts
SKIP_CONFIRMATIONS=false
EOF

    print_success "Configuration file created: $CONFIG_FILE"
}

# Function to create token files
create_token_files() {
    print_header "Creating Token Files"
    
    for secret_name in "${!TOKEN_FILES[@]}"; do
        local token_file="$REPO_ROOT/${TOKEN_FILES[$secret_name]}"
        local token_value="${CONFIG_VALUES[${secret_name}_VALUE]}"
        
        echo "$token_value" > "$token_file"
        chmod 600 "$token_file"  # Secure permissions
        print_success "Created secure token file: ${TOKEN_FILES[$secret_name]}"
    done
}

# Function to update .gitignore
update_gitignore() {
    print_header "Updating .gitignore"
    
    # Check if .gitignore exists
    if [ ! -f "$GITIGNORE_FILE" ]; then
        touch "$GITIGNORE_FILE"
        print_status "Created new .gitignore file"
    fi
    
    # Add instructor files section if not present
    if ! grep -q "# Instructor-only files" "$GITIGNORE_FILE"; then
        cat >> "$GITIGNORE_FILE" << EOF

# =============================================================================
# Instructor-only files (GitHub Classroom automation)
# =============================================================================
# Token files for GitHub API access
*token*.txt
instructor_token.txt
api_token.txt

# Assignment configuration (contains sensitive paths)
assignment.conf

# Generated batch files
tools/generated/
*.batch

# Temporary files from automation scripts
.temp_*
temp_*

# IDE and editor files
.vscode/settings.json
.idea/
*.swp
*.swo
*~

EOF
        print_success "Added instructor files to .gitignore"
    else
        print_status ".gitignore already contains instructor file patterns"
    fi
}

# Function to validate GitHub CLI access
validate_github_access() {
    print_header "Validating GitHub Access"
    
    if ! command -v gh &> /dev/null; then
        print_error "GitHub CLI (gh) is not installed"
        echo -e "${YELLOW}Please install GitHub CLI from: https://cli.github.com/${NC}"
        return 1
    fi
    
    if ! gh auth status &> /dev/null; then
        print_error "GitHub CLI is not authenticated"
        echo -e "${YELLOW}Please run: gh auth login${NC}"
        return 1
    fi
    
    # Test access to organization
    local org="${CONFIG_VALUES[GITHUB_ORGANIZATION]}"
    if ! gh api "orgs/$org" &> /dev/null; then
        print_warning "Cannot access organization '$org'. You may need additional permissions."
        echo -e "${YELLOW}Please ensure you have access to the GitHub organization${NC}"
    else
        print_success "GitHub CLI authenticated and organization access confirmed"
    fi
}

# Function to show help
show_help() {
    cat << EOF
GitHub Classroom Assignment Setup Wizard

DESCRIPTION:
    Interactive setup wizard for instructors to configure a new GitHub Classroom
    assignment with automated tools. Creates configuration files, sets up secure
    token storage, and configures .gitignore for instructor-only files.

USAGE:
    ./tools/scripts_legacy/setup-assignment.sh [options]

OPTIONS:
    --help              Show this help message
    --version           Show version information

FEATURES:
    • Interactive prompts with intelligent defaults
    • Secure token file creation with proper permissions
    • Automatic .gitignore configuration
    • Configuration validation and GitHub access testing
    • Support for multiple custom secrets/tokens
    • Modern, elegant interface with progress indicators

REQUIREMENTS:
    • GitHub CLI (gh) installed and authenticated
    • Write access to repository root directory
    • GitHub organization access permissions

GENERATED FILES:
    • assignment.conf - Complete assignment configuration
    • instructor_token.txt - Secure GitHub API token
    • [custom]_token.txt - Additional token files as configured
    • .gitignore - Updated to protect sensitive files

NEXT STEPS:
    After running this setup wizard, use:
    • ./tools/scripts_legacy/assignment-orchestrator.sh - Complete automation workflow
    • ./tools/scripts_legacy/fetch-student-repos.sh - Discover student repositories
    • ./tools/scripts_legacy/add-secrets-to-students.sh - Add secrets to student repos

DOCUMENTATION:
    • docs/ORCHESTRATOR-WORKFLOW.md - Complete workflow guide
    • docs/TOOLS-USAGE.md - Individual tool documentation
    • docs/SECRETS-MANAGEMENT.md - Secret management guide

EOF
}

# Function to show version
show_version() {
    echo "GitHub Classroom Assignment Setup Wizard v1.0.0"
    echo "Part of the GitHub Classroom automation tools suite"
}
show_welcome() {
    # Clear screen only if we have a TTY (interactive terminal)
    if [[ -t 0 ]]; then
        clear
    fi
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                                                                              ║${NC}"
    echo -e "${CYAN}║${NC}  ${PURPLE}🚀 GitHub Classroom Assignment Setup Wizard${NC}"
    echo -e "${CYAN}║                                                                              ║${NC}"
    echo -e "${CYAN}║${NC}  Welcome! This wizard will help you configure your GitHub Classroom"
    echo -e "${CYAN}║${NC}  assignment with automated tools for seamless management."
    echo -e "${CYAN}║                                                                              ║${NC}"
    echo -e "${CYAN}║${NC}  ${GREEN}✨ What this wizard will do:${NC}"
    echo -e "${CYAN}║${NC}     • Create assignment configuration file"
    echo -e "${CYAN}║${NC}     • Set up secure token files for GitHub API access"
    echo -e "${CYAN}║${NC}     • Configure .gitignore to protect sensitive files"
    echo -e "${CYAN}║${NC}     • Validate GitHub CLI access and permissions"
    echo -e "${CYAN}║                                                                              ║${NC}"
    echo -e "${CYAN}║${NC}  ${BLUE}📋 You'll need:${NC}"
    echo -e "${CYAN}║${NC}     • GitHub Classroom assignment URL"
    echo -e "${CYAN}║${NC}     • Template repository URL (students fork this - has starter code)"
    echo -e "${CYAN}║${NC}     • Classroom repository URL (optional - for pushing updates)"
    echo -e "${CYAN}║${NC}     • GitHub personal access token with repo permissions"
    echo -e "${CYAN}║                                                                              ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo
    echo -e "${GREEN}Press Enter to continue...${NC}"
    # Only wait for input if we have a TTY (interactive terminal)
    if [[ -t 0 ]]; then
        read -r
    fi
}

# Function to show completion screen
show_completion() {
    # Clear screen only if we have a TTY (interactive terminal)
    if [[ -t 0 ]]; then
        clear
    fi
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                                              ║${NC}"
    echo -e "${GREEN}║${NC}  ${PURPLE}🎉 Assignment Setup Complete!${NC}"
    echo -e "${GREEN}║                                                                              ║${NC}"
    echo -e "${GREEN}║${NC}  Your GitHub Classroom assignment has been successfully configured"
    echo -e "${GREEN}║${NC}  with automated tools. Here's what was created:"
    echo -e "${GREEN}║                                                                              ║${NC}"
    echo -e "${GREEN}║${NC}  ${CYAN}📁 Files Created:${NC}"
    echo -e "${GREEN}║${NC}     • assignment.conf - Complete assignment configuration"
    
    # Conditionally show token files
    if [[ "${CONFIG_VALUES[USE_SECRETS]}" == "true" ]]; then
        echo -e "${GREEN}║${NC}     • instructor_token.txt - Secure GitHub API token"
        
        for secret_name in "${!TOKEN_FILES[@]}"; do
            if [ "$secret_name" != "INSTRUCTOR_TESTS_TOKEN" ]; then
                echo -e "${GREEN}║${NC}     • ${TOKEN_FILES[$secret_name]} - Additional token file"
            fi
        done
    fi
    
    echo -e "${GREEN}║${NC}     • .gitignore - Updated to protect sensitive files"
    echo -e "${GREEN}║                                                                              ║${NC}"
    echo -e "${GREEN}║${NC}  ${YELLOW}🚀 Next Steps:${NC}"
    echo -e "${GREEN}║${NC}     1. Run the complete workflow:"
    echo -e "${GREEN}║${NC}        ./tools/scripts_legacy/assignment-orchestrator.sh"
    echo -e "${GREEN}║                                                                              ║${NC}"
    echo -e "${GREEN}║${NC}     2. Or run individual tools:"
    echo -e "${GREEN}║${NC}        ./tools/scripts_legacy/fetch-student-repos.sh"
    echo -e "${GREEN}║${NC}        ./tools/scripts_legacy/add-secrets-to-students.sh"
    echo -e "${GREEN}║                                                                              ║${NC}"
    echo -e "${GREEN}║${NC}  ${BLUE}📚 Documentation:${NC}"
    echo -e "${GREEN}║${NC}     • docs/ORCHESTRATOR-WORKFLOW.md - Complete workflow guide"
    echo -e "${GREEN}║${NC}     • docs/TOOLS-USAGE.md - Individual tool documentation"
    echo -e "${GREEN}║${NC}     • docs/SECRETS-MANAGEMENT.md - Secret management guide"
    echo -e "${GREEN}║                                                                              ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
}

# Main setup wizard flow
main() {
    # Handle command line arguments
    case "${1:-}" in
        --help|-h)
            show_help
            exit 0
            ;;
        --version|-v)
            show_version
            exit 0
            ;;
        --*)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac

    # Show welcome screen
    show_welcome
    
    # Step 1: Collect assignment information
    show_progress "Assignment Information"
    
    # Get classroom URL
    prompt_input \
        "GitHub Classroom assignment URL" \
        "" \
        "validate_url" \
        "Find this in GitHub Classroom when managing your assignment. Example: https://classroom.github.com/classrooms/12345/assignments/assignment-name"
    CONFIG_VALUES[CLASSROOM_URL]="$PROMPT_RESULT"
    
    # Extract organization and assignment name from URL
    local extracted_org=$(extract_org_from_url "${CONFIG_VALUES[CLASSROOM_URL]}")
    local extracted_assignment=$(extract_assignment_from_url "${CONFIG_VALUES[CLASSROOM_URL]}")
    
    # Step 2: Organization and repository information
    show_progress "Template Repository Information"
    
    prompt_input \
        "GitHub organization name" \
        "$extracted_org" \
        "validate_organization" \
        "The GitHub organization that contains your assignment repositories"
    CONFIG_VALUES[GITHUB_ORGANIZATION]="$PROMPT_RESULT"
    
    prompt_input \
        "Template repository URL" \
        "https://github.com/${CONFIG_VALUES[GITHUB_ORGANIZATION]}/${extracted_assignment}-template.git" \
        "validate_url" \
        "The TEMPLATE repository that students fork from (contains starter code/files). Usually has '-template' suffix."\
        "This is the repo created by GitHub Classroom for this assignment"
    CONFIG_VALUES[TEMPLATE_REPO_URL]="$PROMPT_RESULT"
    # Error and exit if TEMPLATE_REPO_URL is empty
    if [ -z "${CONFIG_VALUES[TEMPLATE_REPO_URL]}" ]; then
        echo -e "${RED}ERROR:${NC} The Template repository URL is required for assignment setup. Please provide a valid URL." >&2
        exit 1
    fi
    
    # Step 3: Assignment details
    show_progress "Assignment Details"
    
    prompt_input \
        "Assignment name (optional)" \
        "$extracted_assignment" \
        "validate_assignment_name" \
        "Leave empty to auto-extract from template URL"
    CONFIG_VALUES[ASSIGNMENT_NAME]="$PROMPT_RESULT"
    
    prompt_input \
        "Main assignment file" \
        "assignment.ipynb" \
        "validate_file_path" \
        "The primary file students work on (e.g., assignment.ipynb, main.py, homework.cpp)"
    CONFIG_VALUES[MAIN_ASSIGNMENT_FILE]="$PROMPT_RESULT"
    
    # Step 4: Optional classroom repository
    show_progress "Classroom Repository (Optional)"
    
    echo -e "${BLUE}💡 CLASSROOM repository vs TEMPLATE repository:${NC}"
    echo -e "${CYAN}   • Template repo (Step 2): Students fork this (has starter code)${NC}"
    echo -e "${CYAN}   • Classroom repo (Step 4): Instructor management repo (no '-template' suffix)${NC}"
    echo -e "${YELLOW}   • Classroom repo is only needed if you plan to push updates to all students${NC}"
    echo -e "${YELLOW}   • You can skip this and add it later if needed${NC}"
    prompt_input \
        "Classroom repository URL (optional)" \
        "" \
        "" \
        "The GitHub Classroom management repository (WITHOUT '-template' suffix). Used to push updates to all student repos."
    CONFIG_VALUES[CLASSROOM_REPO_URL]="$PROMPT_RESULT"
    
    # Step 5: Secret Management Configuration
    show_progress "Secret Management Configuration"
    
    echo -e "${BLUE}Where are your assignment tests located?${NC}"
    echo -e "${CYAN}   Option 1: Tests are included in the template repository (simpler setup)${NC}"
    echo -e "${CYAN}   Option 2: Tests are in a separate private instructor repository (more secure)${NC}"
    echo
    echo -e "${BLUE}Do you have tests in a separate private instructor repository? (y/N)${NC}"
    
    if [[ -t 0 ]]; then
        read -r use_secrets
    else
        read -r use_secrets || use_secrets="N"
    fi
    
    if [[ "$use_secrets" =~ ^[Yy]$ ]]; then
        CONFIG_VALUES[USE_SECRETS]="true"
        echo -e "${GREEN}✓ Secret management will be enabled for accessing instructor test repository${NC}"
    else
        CONFIG_VALUES[USE_SECRETS]="false"
        echo -e "${GREEN}✓ Secret management will be disabled (tests in template repository)${NC}"
    fi

    # Step 6: Token setup (conditional)
    if [[ "${CONFIG_VALUES[USE_SECRETS]}" == "true" ]]; then
        show_progress "GitHub Token Configuration"
    
        echo -e "${BLUE}💡 You need a GitHub personal access token with 'repo' and 'admin:repo_hook' permissions${NC}"
        echo -e "${YELLOW}Create one at: https://github.com/settings/tokens${NC}"
        
        prompt_secure \
            "GitHub personal access token" \
            "This token will be securely stored in instructor_token.txt"
        CONFIG_VALUES[INSTRUCTOR_TESTS_TOKEN_VALUE]="$PROMPT_RESULT"
        
        # Ask if this token should be validated as a GitHub token
        echo -e "\n${BLUE}Should this token be validated as a GitHub token (starts with 'ghp_')? (Y/n)${NC}"
        echo -e "${GRAY}  - Choose 'Y' for GitHub personal access tokens${NC}"
        echo -e "${GRAY}  - Choose 'n' for database passwords or other non-GitHub secrets${NC}"
        # Only read input if we have a TTY (interactive terminal)
        if [[ -t 0 ]]; then
            read -r validate_instructor_token
        else
            # In non-interactive mode, read from stdin
            read -r validate_instructor_token || validate_instructor_token="Y"
        fi
        
        if [[ "$validate_instructor_token" =~ ^[Nn]$ ]]; then
            TOKEN_VALIDATION[INSTRUCTOR_TESTS_TOKEN]="false"
        else
            TOKEN_VALIDATION[INSTRUCTOR_TESTS_TOKEN]="true"
        fi
        
        TOKEN_FILES[INSTRUCTOR_TESTS_TOKEN]="instructor_token.txt"
        
        # Ask for additional tokens
        echo -e "\n${BLUE}Do you need to configure additional tokens/secrets? (y/N)${NC}"
        # Only read input if we have a TTY (interactive terminal)
        if [[ -t 0 ]]; then
            read -r add_tokens
        else
            # In non-interactive mode, read from stdin
            read -r add_tokens || add_tokens="N"
        fi
        
        if [[ "$add_tokens" =~ ^[Yy]$ ]]; then
            while true; do
                echo -e "\n${GREEN}Enter additional secret name (or press Enter to finish):${NC}"
                # Only read input if we have a TTY (interactive terminal)
                if [[ -t 0 ]]; then
                    read -r secret_name
                else
                    # In non-interactive mode, read from stdin
                    read -r secret_name || secret_name=""
                fi
                
                if [ -z "$secret_name" ]; then
                    break
                fi
                
                if validate_non_empty "$secret_name" && [[ "$secret_name" =~ ^[A-Z_][A-Z0-9_]*$ ]]; then
                    # Ask for description
                    echo -e "\n${GREEN}Enter a description for '$secret_name':${NC}"
                    echo -e "${GRAY}(e.g., 'Database password for student submissions', 'API key for external service')${NC}"
                    # Only read input if we have a TTY (interactive terminal)
                    if [[ -t 0 ]]; then
                        read -r secret_description
                    else
                        # In non-interactive mode, read from stdin
                        read -r secret_description || secret_description="$secret_name for assignment functionality"
                    fi
                    
                    # Use default description if empty
                    if [ -z "$secret_description" ]; then
                        secret_description="$secret_name for assignment functionality"
                    fi
                    
                    local token_file="${secret_name,,}_token.txt"  # lowercase filename
                    prompt_secure \
                        "Token value for $secret_name" \
                        "This will be stored in $token_file"
                    CONFIG_VALUES[${secret_name}_VALUE]="$PROMPT_RESULT"
                    
                    # Ask if this secret should be validated as a GitHub token
                    echo -e "\n${BLUE}Should '$secret_name' be validated as a GitHub token (starts with 'ghp_')? (Y/n)${NC}"
                    echo -e "${GRAY}  - Choose 'Y' for GitHub personal access tokens${NC}"
                    echo -e "${GRAY}  - Choose 'n' for database passwords or other non-GitHub secrets${NC}"
                    # Only read input if we have a TTY (interactive terminal)
                    if [[ -t 0 ]]; then
                        read -r validate_secret
                    else
                        # In non-interactive mode, read from stdin
                        read -r validate_secret || validate_secret="Y"
                    fi
                    
                    if [[ "$validate_secret" =~ ^[Nn]$ ]]; then
                        TOKEN_VALIDATION[$secret_name]="false"
                    else
                        TOKEN_VALIDATION[$secret_name]="true"
                    fi
                    
                    # Store the description for later use
                    CONFIG_VALUES[${secret_name}_DESCRIPTION]="$secret_description"
                    TOKEN_FILES[$secret_name]="$token_file"
                else
                    print_error "Secret name must be uppercase with underscores (e.g., API_KEY, DATABASE_TOKEN)"
                fi
            done
        fi
    else
        echo -e "${BLUE}ℹ️  Skipping token configuration (tests are in template repository)${NC}"
    fi

    # Step 7: Create files
    show_progress "Creating Configuration Files"
    create_config_file
    
    # Only create token files if secrets are enabled
    if [[ "${CONFIG_VALUES[USE_SECRETS]}" == "true" ]]; then
        create_token_files
    fi
    
    update_gitignore
    
    # Step 8: Validation
    show_progress "Validating Setup"
    validate_github_access
    
    # Show completion
    show_completion
    
    print_success "Setup wizard completed successfully!"
    echo -e "\n${GREEN}You're ready to manage your GitHub Classroom assignment!${NC}"
}

# Check if running as main script
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
