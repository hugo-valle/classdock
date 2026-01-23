#!/bin/bash
#
# Automated Workflow Cron Job for GitHub Classroom Assignment
#
# This script is designed to run as a cron job to automatically execute
# specific workflow steps like template sync, secret management, or 
# repository access cycling.
#
# Usage: ./scripts_legacy/cron-sync.sh [config-file] [step1] [step2] [...]
#
# Examples:
# ./scripts_legacy/cron-sync.sh assignment.conf sync
# ./scripts_legacy/cron-sync.sh assignment.conf secrets cycle
# ./scripts_legacy/cron-sync.sh assignment.conf sync secrets cycle discover
#
# Cron Example (every 4 hours for sync only):
# 0 */4 * * * /path/to/assignment/tools/scripts_legacy/cron-sync.sh assignment.conf sync >/dev/null 2>&1
#
# Cron Example (daily for secrets management):
# 0 2 * * * /path/to/assignment/tools/scripts_legacy/cron-sync.sh assignment.conf secrets >/dev/null 2>&1
#

set -euo pipefail

# Script directory and paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLS_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$TOOLS_ROOT/.." && pwd)"
DEFAULT_CONFIG="$REPO_ROOT/assignment.conf"

# Source shared logging utility
source "$TOOLS_ROOT/utils/logging.sh"

# Parse command line arguments
CONFIG_FILE="${1:-$DEFAULT_CONFIG}"
shift || true  # Remove first argument (config file)

# Remaining arguments are the steps to execute
STEPS=("$@")

# If no steps specified, default to sync for backward compatibility
if [[ ${#STEPS[@]} -eq 0 ]]; then
    STEPS=("sync")
fi

LOG_FILE="$REPO_ROOT/tools/generated/cron-workflow.log"

# Logging function for cron jobs
log_cron() {
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] $*" >> "$LOG_FILE"
}

# Function to rotate log file if it gets too large (>10MB)
rotate_log() {
    if [[ -f "$LOG_FILE" ]] && [[ $(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null || echo 0) -gt 10485760 ]]; then
        mv "$LOG_FILE" "${LOG_FILE}.old"
        log_cron "INFO: Log file rotated"
    fi
}

# Main cron workflow function
main() {
    # Ensure log directory exists
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # Rotate log if needed
    rotate_log
    
    log_cron "INFO: Starting automated workflow job"
    log_cron "INFO: Using config file: $CONFIG_FILE"
    log_cron "INFO: Executing steps: ${STEPS[*]}"
    
    # Change to repository root
    cd "$REPO_ROOT"
    
    # Check if config file exists
    if [[ ! -f "$CONFIG_FILE" ]]; then
        log_cron "ERROR: Configuration file not found: $CONFIG_FILE"
        exit 1
    fi
    
    # Source configuration to validate it's readable
    # shellcheck source=/dev/null
    if ! source "$CONFIG_FILE" 2>/dev/null; then
        log_cron "ERROR: Failed to load configuration file: $CONFIG_FILE"
        exit 1
    fi
    
    # Check if we're in a git repository
    if [[ ! -d ".git" ]]; then
        log_cron "ERROR: Not in a git repository: $REPO_ROOT"
        exit 1
    fi
    
    # Execute each step
    local overall_success=true
    for step in "${STEPS[@]}"; do
        log_cron "INFO: Executing step: $step"
        
        # Validate step name
        case "$step" in
            sync|discover|secrets|assist|cycle)
                # Valid step
                ;;
            *)
                log_cron "ERROR: Invalid step name: $step"
                log_cron "ERROR: Valid steps are: sync, discover, secrets, assist, cycle"
                overall_success=false
                continue
                ;;
        esac
        
        # Run the orchestrator for this step
        local orchestrator_cmd="$TOOLS_ROOT/scripts_legacy/assignment-orchestrator.sh"
        local orchestrator_args=(
            "$CONFIG_FILE"
            "--step" "$step"
            "--yes"
            "--verbose"
        )
        
        log_cron "INFO: Executing: $orchestrator_cmd ${orchestrator_args[*]}"
        
        # Capture both stdout and stderr for logging
        if "$orchestrator_cmd" "${orchestrator_args[@]}" >> "$LOG_FILE" 2>&1; then
            log_cron "SUCCESS: Step '$step' completed successfully"
        else
            local exit_code=$?
            log_cron "ERROR: Step '$step' failed with exit code: $exit_code"
            overall_success=false
        fi
    done
    
    if [[ "$overall_success" == "true" ]]; then
        log_cron "SUCCESS: All workflow steps completed successfully"
    else
        log_cron "WARNING: Some workflow steps failed - check log for details"
        exit 1
    fi
    
    log_cron "INFO: Automated workflow job completed"
}

# Error handling for cron environment
trap 'log_cron "ERROR: Script failed with exit code $?"' ERR

# Execute main function
main "$@"
