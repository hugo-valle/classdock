#!/bin/bash
#
# Cron Job Management Helper for GitHub Classroom Assignment
#
# This script helps install, remove, and manage automated workflow cron jobs
# for different assignment management steps.
#
# Usage: ./scripts_legacy/manage-cron.sh [command] [options]
#

set -euo pipefail

# Script directory and paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLS_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$TOOLS_ROOT/.." && pwd)"

# Source shared logging utility
source "$TOOLS_ROOT/utils/logging.sh"

# Additional logging functions for consistency
log_info() { print_status "$@"; }
log_success() { print_success "$@"; }
log_warning() { print_warning "$@"; }
log_error() { print_error "$@"; }

# Configuration
CRON_SCRIPT="$TOOLS_ROOT/scripts_legacy/cron-sync.sh"
LOG_FILE="$REPO_ROOT/tools/generated/cron-workflow.log"
CRON_COMMENT_PREFIX="# GitHub Classroom Assignment Auto"

# Default schedules for different workflow types
declare -A DEFAULT_SCHEDULES=(
    ["sync"]="0 */4 * * *"      # Every 4 hours
    ["secrets"]="0 2 * * *"     # Daily at 2 AM
    ["cycle"]="0 6 * * 0"       # Weekly on Sunday at 6 AM
    ["discover"]="0 1 * * *"    # Daily at 1 AM
    ["assist"]="0 3 * * 0"      # Weekly on Sunday at 3 AM
)

# Help function
show_help() {
    cat << EOF
Cron Job Management Helper

USAGE:
    ./scripts_legacy/manage-cron.sh [command] [options]

COMMANDS:
    install [steps] [schedule]  Install cron job for specified steps
    remove [steps|all]          Remove cron job(s)
    status                      Check installed cron jobs
    logs                        Show recent workflow log entries
    list-schedules             Show default schedules for each step
    help                       Show this help

INSTALL EXAMPLES:
    # Install sync job (every 4 hours)
    ./scripts_legacy/manage-cron.sh install sync

    # Install secrets management (daily at 2 AM)
    ./scripts_legacy/manage-cron.sh install secrets

    # Install cycle job (weekly on Sunday at 6 AM)
    ./scripts_legacy/manage-cron.sh install cycle

    # Install multiple steps together (daily at 1 AM)
    ./scripts_legacy/manage-cron.sh install "sync secrets" "0 1 * * *"

    # Install with custom schedule
    ./scripts_legacy/manage-cron.sh install sync "0 */2 * * *"

REMOVE EXAMPLES:
    # Remove specific step cron job
    ./scripts_legacy/manage-cron.sh remove sync

    # Remove all assignment-related cron jobs
    ./scripts_legacy/manage-cron.sh remove all

WORKFLOW STEPS:
    sync        Template synchronization with GitHub Classroom
    discover    Repository discovery and batch file generation
    secrets     Secret management across student repositories
    assist      Student assistance and conflict resolution
    cycle       Repository access fix through permission cycling

DEFAULT SCHEDULES:
    sync:       Every 4 hours (0 */4 * * *)
    secrets:    Daily at 2 AM (0 2 * * *)
    cycle:      Weekly on Sunday at 6 AM (0 6 * * 0)
    discover:   Daily at 1 AM (0 1 * * *)
    assist:     Weekly on Sunday at 3 AM (0 3 * * 0)

LOG FILE: $LOG_FILE

EOF
}

# Function to check if specific cron job exists
cron_exists() {
    local steps="${1:-sync}"
    local comment="$CRON_COMMENT_PREFIX-${steps// /-}"
    crontab -l 2>/dev/null | grep -F "$comment" >/dev/null 2>&1
}

# Function to get cron job command for given steps
get_cron_command() {
    local steps="$1"
    echo "$CRON_SCRIPT '$REPO_ROOT/assignment.conf' $steps >/dev/null 2>&1"
}

# Function to get cron job comment for given steps
get_cron_comment() {
    local steps="$1"
    echo "$CRON_COMMENT_PREFIX-${steps// /-}"
}

# Function to validate step names
validate_steps() {
    local steps="$1"
    local valid_steps=("sync" "discover" "secrets" "assist" "cycle")
    
    for step in $steps; do
        local found=false
        for valid_step in "${valid_steps[@]}"; do
            if [[ "$step" == "$valid_step" ]]; then
                found=true
                break
            fi
        done
        
        if [[ "$found" == "false" ]]; then
            log_error "Invalid step: $step"
            log_error "Valid steps are: ${valid_steps[*]}"
            return 1
        fi
    done
    return 0
}

# Function to get default schedule for steps
get_default_schedule() {
    local steps="$1"
    
    # If multiple steps, use a common daily schedule
    if [[ "$steps" == *" "* ]]; then
        echo "0 1 * * *"  # Daily at 1 AM for multiple steps
        return
    fi
    
    # Single step - use specific schedule
    echo "${DEFAULT_SCHEDULES[$steps]:-0 */4 * * *}"
}

# Install cron job
install_cron() {
    local steps="${1:-sync}"
    local schedule="$2"
    
    log_info "Installing cron job for steps: $steps"
    
    # Validate steps
    if ! validate_steps "$steps"; then
        exit 1
    fi
    
    # Get default schedule if not provided
    if [[ -z "$schedule" ]]; then
        schedule=$(get_default_schedule "$steps")
        log_info "Using default schedule: $schedule"
    fi
    
    # Check if script exists and is executable
    if [[ ! -x "$CRON_SCRIPT" ]]; then
        log_error "Cron script not found or not executable: $CRON_SCRIPT"
        exit 1
    fi
    
    # Check if assignment config exists
    if [[ ! -f "$REPO_ROOT/assignment.conf" ]]; then
        log_error "Assignment configuration not found: $REPO_ROOT/assignment.conf"
        log_error "Please create the configuration file before installing the cron job"
        exit 1
    fi
    
    # Check if cron job already exists
    if cron_exists "$steps"; then
        log_warning "Cron job for steps '$steps' already exists. Remove it first if you want to reinstall."
        log_info "Current cron job:"
        local comment=$(get_cron_comment "$steps")
        crontab -l | grep -A1 -F "$comment" || true
        return 0
    fi
    
    # Create the cron job entry
    local comment=$(get_cron_comment "$steps")
    local command=$(get_cron_command "$steps")
    local cron_entry="$comment"$'\n'"$schedule $command"
    
    # Add to existing crontab or create new one
    if crontab -l >/dev/null 2>&1; then
        # Append to existing crontab
        (crontab -l; echo "$cron_entry") | crontab -
    else
        # Create new crontab
        echo "$cron_entry" | crontab -
    fi
    
    log_success "Cron job installed successfully!"
    log_info "Steps: $steps"
    log_info "Schedule: $schedule"
    log_info "Command: $command"
    log_info "Logs will be written to: $LOG_FILE"
    
    echo
    log_info "You can check the status with: ./scripts_legacy/manage-cron.sh status"
    log_info "You can view logs with: ./scripts_legacy/manage-cron.sh logs"
}

# Remove cron job
remove_cron() {
    local steps="${1:-sync}"
    
    log_info "Removing cron job..."
    
    if [[ "$steps" == "all" ]]; then
        log_info "Removing all assignment-related cron jobs..."
        
        # Remove all cron jobs with our comment prefix
        local temp_cron
        temp_cron=$(mktemp)
        if crontab -l >/dev/null 2>&1; then
            crontab -l | grep -v -F "$CRON_COMMENT_PREFIX" > "$temp_cron" || true
            if [[ -s "$temp_cron" ]]; then
                crontab "$temp_cron"
            else
                crontab -r 2>/dev/null || true
            fi
        fi
        rm -f "$temp_cron"
        
        log_success "All assignment cron jobs removed successfully!"
        return 0
    fi
    
    if ! cron_exists "$steps"; then
        log_warning "Cron job for steps '$steps' not found. Nothing to remove."
        return 0
    fi
    
    # Remove the specific cron job and its comment
    local comment
    comment=$(get_cron_comment "$steps")
    local temp_cron
    temp_cron=$(mktemp)
    
    if crontab -l >/dev/null 2>&1; then
        crontab -l | grep -v -F "$comment" | grep -v -F "$(get_cron_command "$steps")" > "$temp_cron" || true
        if [[ -s "$temp_cron" ]]; then
            crontab "$temp_cron"
        else
            crontab -r 2>/dev/null || true
        fi
    fi
    rm -f "$temp_cron"
    
    log_success "Cron job for steps '$steps' removed successfully!"
}

# Show cron job status
show_status() {
    log_info "Checking cron job status..."
    
    # Check for any assignment-related cron jobs
    if crontab -l >/dev/null 2>&1; then
        local found_jobs
        found_jobs=$(crontab -l | grep -F "$CRON_COMMENT_PREFIX" || true)
        
        if [[ -n "$found_jobs" ]]; then
            log_success "Assignment cron jobs are installed:"
            echo
            echo "$found_jobs"
            
            # Check if log file exists and show last activity
            if [[ -f "$LOG_FILE" ]]; then
                echo
                echo "Last log activity:"
                tail -n 3 "$LOG_FILE" 2>/dev/null || echo "No recent log entries"
            fi
        else
            log_warning "No assignment cron jobs are installed"
            echo
            log_info "To install one, run: ./scripts_legacy/manage-cron.sh install [steps]"
        fi
    else
        log_warning "No crontab exists for current user"
        echo
        log_info "To install a cron job, run: ./scripts_legacy/manage-cron.sh install [steps]"
    fi
}

# Show recent logs
show_logs() {
    log_info "Showing recent workflow logs..."
    
    if [[ ! -f "$LOG_FILE" ]]; then
        log_warning "Log file not found: $LOG_FILE"
        log_info "The cron job may not have run yet, or logging is not working."
        return 0
    fi
    
    echo
    echo "=== Recent Workflow Log Entries ==="
    tail -n 30 "$LOG_FILE"
    
    echo
    echo "=== Log File Info ==="
    echo "File: $LOG_FILE"
    echo "Size: $(du -h "$LOG_FILE" 2>/dev/null | cut -f1 || echo "unknown")"
    echo "Last modified: $(ls -l "$LOG_FILE" | awk '{print $6, $7, $8}')"
}

# Show default schedules
list_schedules() {
    log_info "Default schedules for workflow steps:"
    echo
    for step in sync discover secrets assist cycle; do
        local schedule="${DEFAULT_SCHEDULES[$step]}"
        printf "  %-10s %s\n" "$step:" "$schedule"
    done
    
    echo
    echo "Schedule format: minute hour day_of_month month day_of_week"
    echo "Examples:"
    echo "  0 */4 * * *   - Every 4 hours"
    echo "  0 2 * * *     - Daily at 2 AM"
    echo "  0 6 * * 0     - Weekly on Sunday at 6 AM"
}

# Main function
main() {
    local command="${1:-help}"
    
    case "$command" in
        "install")
            local steps="${2:-sync}"
            local schedule="${3:-}"
            install_cron "$steps" "$schedule"
            ;;
        "remove")
            local steps="${2:-sync}"
            remove_cron "$steps"
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs
            ;;
        "list-schedules")
            list_schedules
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            log_error "Unknown command: $command"
            echo
            show_help
            exit 1
            ;;
    esac
}

# Execute main function
main "$@"
