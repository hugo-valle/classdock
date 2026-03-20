#!/usr/bin/env bash
# GitHub Actions Workflow Utilities
# Shared utility functions for optimized CI/CD workflows
#
# This script provides reusable functions for:
# - Retry logic with exponential backoff
# - Caching helpers and cache key generation
# - Error reporting and notifications
# - Build performance monitoring

# Only set pipefail to avoid breaking existing scripts that source this
# Individual functions can set stricter modes as needed
set -eo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Global variables
SCRIPT_START_TIME=$(date +%s)
RETRY_MAX_ATTEMPTS=3
RETRY_BASE_DELAY=2

#######################################
# Print colored status messages
# Arguments:
#   $1: Message type (info, success, warning, error, step)
#   $2: Message text
#######################################
print_message() {
    local type="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case "$type" in
        "info")    echo -e "${BLUE}[INFO]${NC} [$timestamp] $message" ;;
        "success") echo -e "${GREEN}[SUCCESS]${NC} [$timestamp] $message" ;;
        "warning") echo -e "${YELLOW}[WARNING]${NC} [$timestamp] $message" ;;
        "error")   echo -e "${RED}[ERROR]${NC} [$timestamp] $message" ;;
        "step")    echo -e "${PURPLE}[STEP]${NC} [$timestamp] $message" ;;
        *)         echo "[$timestamp] $message" ;;
    esac
}

#######################################
# Logging helper functions (wrappers around print_message)
#######################################
log_info() {
    print_message "info" "$1"
}

log_success() {
    print_message "success" "$1"
}

log_warning() {
    print_message "warning" "$1"
}

log_error() {
    print_message "error" "$1"
}

#######################################
# Create directory if it doesn't exist
# Arguments:
#   $1: Directory path to create
# Returns:
#   0 on success, 1 on failure
#######################################
create_directory_if_not_exists() {
    local dir_path="$1"
    
    if [[ -z "$dir_path" ]]; then
        log_error "Directory path cannot be empty"
        return 1
    fi
    
    if [[ ! -d "$dir_path" ]]; then
        log_info "Creating directory: $dir_path"
        if mkdir -p "$dir_path"; then
            log_success "Directory created successfully: $dir_path"
            return 0
        else
            log_error "Failed to create directory: $dir_path"
            return 1
        fi
    else
        log_info "Directory already exists: $dir_path"
        return 0
    fi
}

#######################################
# Execute command with retry logic and exponential backoff
# Arguments:
#   $1: Command to execute
#   $2: Description of operation (optional)
#   $3: Max attempts (optional, default: 3)
#   $4: Base delay (optional, default: 2 seconds)
# Returns:
#   0 on success, 1 on failure after all retries
#######################################
retry_with_backoff() {
    local cmd="$1"
    local description="${2:-command}"
    local max_attempts="${3:-$RETRY_MAX_ATTEMPTS}"
    local base_delay="${4:-$RETRY_BASE_DELAY}"
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        print_message "info" "Attempting $description (attempt $attempt/$max_attempts)"
        
        if eval "$cmd"; then
            print_message "success" "$description completed successfully"
            return 0
        else
            local exit_code=$?
            if [ $attempt -eq $max_attempts ]; then
                print_message "error" "$description failed after $max_attempts attempts"
                return $exit_code
            fi
            
            local delay=$((base_delay * (2 ** (attempt - 1))))
            print_message "warning" "$description failed (attempt $attempt), retrying in ${delay}s..."
            sleep $delay
            attempt=$((attempt + 1))
        fi
    done
}

#######################################
# Generate standardized cache key for dependencies
# Arguments:
#   $1: Package manager (poetry, pip, apt)
#   $2: OS identifier (ubuntu-latest, etc.)
#   $3: Python version (optional)
#   $4: Additional key component (optional)
# Returns:
#   Cache key string
#######################################
generate_cache_key() {
    local package_manager="$1"
    local os_id="$2"
    local python_version="${3:-}"
    local additional="${4:-}"
    
    local base_key="$package_manager-$os_id"
    
    if [ -n "$python_version" ]; then
        base_key="$base_key-py$python_version"
    fi
    
    if [ -n "$additional" ]; then
        base_key="$base_key-$additional"
    fi
    
    # Add timestamp component for cache versioning
    local cache_version="v1"
    echo "$base_key-$cache_version"
}

#######################################
# Generate cache key with file hash for dependency files
# Arguments:
#   $1: Package manager (poetry, pip, apt)
#   $2: OS identifier
#   $3: Dependency file path
#   $4: Python version (optional)
# Returns:
#   Cache key with file hash
#######################################
generate_cache_key_with_hash() {
    local package_manager="$1"
    local os_id="$2"
    local dep_file="$3"
    local python_version="${4:-}"
    
    local base_key
    base_key=$(generate_cache_key "$package_manager" "$os_id" "$python_version")
    
    if [ -f "$dep_file" ]; then
        local file_hash
        file_hash=$(sha256sum "$dep_file" | cut -d' ' -f1 | head -c 8)
        echo "$base_key-$file_hash"
    else
        echo "$base_key-nofile"
    fi
}

#######################################
# Check if command exists
# Arguments:
#   $1: Command name
# Returns:
#   0 if command exists, 1 otherwise
#######################################
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

#######################################
# Install package with retry logic
# Arguments:
#   $1: Package manager (apt, pip, poetry)
#   $2: Package name or install command
#   $3: Additional options (optional)
# Returns:
#   0 on success, 1 on failure
#######################################
install_with_retry() {
    local pkg_manager="$1"
    local package="$2"
    local options="${3:-}"
    
    case "$pkg_manager" in
        "apt")
            retry_with_backoff "sudo apt-get update && sudo apt-get install -y $options $package" \
                "apt package installation: $package"
            ;;
        "pip")
            retry_with_backoff "pip install $options $package" \
                "pip package installation: $package"
            ;;
        "poetry")
            retry_with_backoff "poetry install $options" \
                "poetry dependency installation"
            ;;
        *)
            print_message "error" "Unknown package manager: $pkg_manager"
            return 1
            ;;
    esac
}

#######################################
# Start timing a step
# Arguments:
#   $1: Step name
# Returns:
#   Sets STEP_START_TIME_<step_name> environment variable
#######################################
start_step_timing() {
    local step_name="$1"
    local start_time
    start_time=$(date +%s)
    
    # Create a valid environment variable name by replacing non-alphanumeric chars with underscores
    local var_name="STEP_START_TIME_$(echo "$step_name" | tr -c '[:alnum:]' '_' | tr '[:lower:]' '[:upper:]')"
    
    # Set the start time in an environment variable
    export "$var_name=$start_time"
    
    print_message "info" "Started timing: $step_name"
    
    # Export for GitHub Actions
    if [ -n "${GITHUB_ENV:-}" ] && [ -f "${GITHUB_ENV}" ]; then
        echo "$var_name=$start_time" >> "$GITHUB_ENV"
    fi
}

#######################################
# End timing a step and report duration
# Arguments:
#   $1: Step name
# Returns:
#   Duration in seconds
#######################################
end_step_timing() {
    local step_name="$1"
    local end_time
    end_time=$(date +%s)
    
    # Create the corresponding variable name
    local var_name="STEP_START_TIME_$(echo "$step_name" | tr -c '[:alnum:]' '_' | tr '[:lower:]' '[:upper:]')"
    
    # Get the start time from the environment variable
    local start_time
    eval "start_time=\$$var_name"
    
    if [ -z "$start_time" ]; then
        print_message "warning" "No start time found for step: $step_name" >&2
        return 1
    fi

    local duration=$((end_time - start_time))

    # Log to stderr so callers using $() capture only get the numeric duration
    print_message "info" "$step_name completed in ${duration}s" >&2

    # Export for GitHub Actions step summary
    if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
        echo "| $step_name | ${duration}s |" >> "$GITHUB_STEP_SUMMARY"
    fi

    # Export duration for use in other steps
    if [ -n "${GITHUB_ENV:-}" ] && [ -f "${GITHUB_ENV}" ]; then
        local duration_var="STEP_DURATION_$(echo "$step_name" | tr -c '[:alnum:]' '_' | tr '[:lower:]' '[:upper:]')"
        echo "$duration_var=$duration" >> "$GITHUB_ENV"
    fi

    echo "$duration"
}

#######################################
# Monitor build performance and report timing
# Arguments:
#   $1: Step name
#   $2: Start time (from 'date +%s')
# Returns:
#   Duration in seconds
#######################################
report_step_timing() {
    local step_name="$1"
    local start_time="$2"
    local end_time
    end_time=$(date +%s)
    local duration=$((end_time - start_time))

    # Log to stderr so callers using $() capture only get the numeric duration
    print_message "info" "$step_name completed in ${duration}s" >&2

    # Export for GitHub Actions step summary
    if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
        echo "| $step_name | ${duration}s |" >> "$GITHUB_STEP_SUMMARY"
    fi

    echo "$duration"
}

#######################################
# Generate error report for failed operations
# Arguments:
#   $1: Operation name
#   $2: Error message
#   $3: Context (optional)
#   $4: Suggested actions (optional)
# Returns:
#   Formatted error report
#######################################
generate_error_report() {
    local operation="$1"
    local error_msg="$2"
    local context="${3:-}"
    local suggestions="${4:-}"
    
    local error_report="## ❌ $operation Failed\n\n"
    error_report+="**Error:** $error_msg\n\n"
    
    if [ -n "$context" ]; then
        error_report+="**Context:** $context\n\n"
    fi
    
    if [ -n "$suggestions" ]; then
        error_report+="**Suggested Actions:**\n$suggestions\n\n"
    fi
    
    error_report+="**Workflow:** $GITHUB_WORKFLOW\n"
    error_report+="**Job:** $GITHUB_JOB\n"
    error_report+="**Run ID:** $GITHUB_RUN_ID\n"
    error_report+="**Timestamp:** $(date -u '+%Y-%m-%d %H:%M:%S UTC')\n"
    
    echo -e "$error_report"
}

#######################################
# Create GitHub Actions step summary with build metrics
# Arguments:
#   $1: Job name
#   $2: Status (success, failure, warning)
#   $3: Additional metrics (optional)
#######################################
create_step_summary() {
    local job_name="$1"
    local status="$2"
    local metrics="${3:-}"
    
    if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
        local total_time
        total_time=$(report_step_timing "Total $job_name" "$SCRIPT_START_TIME")
        
        {
            echo "# $job_name Summary"
            echo ""
            case "$status" in
                "success") echo "✅ **Status:** Success" ;;
                "failure") echo "❌ **Status:** Failed" ;;
                "warning") echo "⚠️ **Status:** Warning" ;;
            esac
            echo ""
            echo "## Performance Metrics"
            echo "| Metric | Value |"
            echo "|--------|-------|"
            echo "| Total Time | ${total_time}s |"
            
            if [ -n "$metrics" ]; then
                echo "$metrics"
            fi
            echo ""
        } >> "$GITHUB_STEP_SUMMARY"
    fi
}

#######################################
# Validate environment and dependencies
# Arguments:
#   $1: Required commands (space-separated)
#   $2: Optional commands (space-separated, optional)
# Returns:
#   0 if all required commands exist, 1 otherwise
#######################################
validate_environment() {
    local required_cmds="$1"
    local optional_cmds="${2:-}"
    local missing_required=()
    local missing_optional=()
    
    # Check required commands
    for cmd in $required_cmds; do
        if ! command_exists "$cmd"; then
            missing_required+=("$cmd")
        fi
    done
    
    # Check optional commands
    for cmd in $optional_cmds; do
        if ! command_exists "$cmd"; then
            missing_optional+=("$cmd")
        fi
    done
    
    # Report results
    if [ ${#missing_required[@]} -eq 0 ]; then
        print_message "success" "All required dependencies are available"
        
        if [ ${#missing_optional[@]} -gt 0 ]; then
            print_message "warning" "Optional dependencies missing: ${missing_optional[*]}"
        fi
        return 0
    else
        print_message "error" "Required dependencies missing: ${missing_required[*]}"
        return 1
    fi
}

#######################################
# Setup cache directories with proper permissions
# Arguments:
#   $1: Cache directories (space-separated)
# Returns:
#   0 on success
#######################################
setup_cache_directories() {
    local cache_dirs="$1"
    
    for dir in $cache_dirs; do
        if [ ! -d "$dir" ]; then
            print_message "info" "Creating cache directory: $dir"
            mkdir -p "$dir"
        fi
        
        # Ensure proper permissions
        chmod 755 "$dir" 2>/dev/null || true
    done
}

#######################################
# Export timing and performance metrics
# Arguments:
#   None (uses global variables and environment)
# Returns:
#   Performance metrics in various formats
#######################################
export_performance_metrics() {
    local total_time
    total_time=$(report_step_timing "Workflow" "$SCRIPT_START_TIME")
    
    # Ensure total_time is a valid number
    if ! [[ "$total_time" =~ ^[0-9]+$ ]]; then
        total_time=0
    fi
    
    # Export for use in other steps - only if GITHUB_ENV is available and not empty
    if [ -n "${GITHUB_ENV:-}" ] && [ -f "${GITHUB_ENV}" ]; then
        echo "WORKFLOW_DURATION=${total_time}" >> "$GITHUB_ENV"
    fi
    
    # Create performance artifact
    if [ -n "${RUNNER_TEMP:-}" ]; then
        local perf_file="$RUNNER_TEMP/performance_metrics.json"
        {
            echo "{"
            echo "  \"workflow_duration\": ${total_time},"
            echo "  \"timestamp\": \"$(date -u '+%Y-%m-%d %H:%M:%S UTC')\","
            echo "  \"runner_os\": \"${RUNNER_OS:-unknown}\","
            echo "  \"github_run_id\": \"${GITHUB_RUN_ID:-unknown}\","
            echo "  \"github_job\": \"${GITHUB_JOB:-unknown}\""
            echo "}"
        } > "$perf_file"
        
        print_message "info" "Performance metrics saved to $perf_file" >&2
    fi
}

# Export functions for use in workflows
export -f print_message
export -f log_info
export -f log_success
export -f log_warning
export -f log_error
export -f create_directory_if_not_exists
export -f retry_with_backoff
export -f generate_cache_key
export -f generate_cache_key_with_hash
export -f command_exists
export -f install_with_retry
export -f start_step_timing
export -f end_step_timing
export -f report_step_timing
export -f generate_error_report
export -f create_step_summary
export -f validate_environment
export -f setup_cache_directories
export -f export_performance_metrics

print_message "info" "GitHub Actions workflow utilities loaded successfully"