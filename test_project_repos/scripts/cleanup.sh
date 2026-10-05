#!/usr/bin/env bash
#
# Cleanup Script for Test Environment
# Removes temporary files, logs, and test artifacts
#

set -e

# Source configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Show usage information
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Cleanup test environment and remove temporary files.

Options:
    --logs              Remove log files only
    --envs              Remove virtual environments only
    --temp              Remove temporary files only
    --reports           Remove test reports only
    --all               Remove everything (default)
    --dry-run          Show what would be deleted without actually deleting
    -h, --help         Show this help message

Examples:
    $0                  # Clean everything
    $0 --logs           # Clean only log files
    $0 --dry-run        # Show what would be cleaned
    $0 --all --dry-run  # Show full cleanup without executing
EOF
}

# Parse command line arguments
CLEAN_LOGS=false
CLEAN_ENVS=false
CLEAN_TEMP=false
CLEAN_REPORTS=false
CLEAN_ALL=true
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --logs)
            CLEAN_LOGS=true
            CLEAN_ALL=false
            shift
            ;;
        --envs)
            CLEAN_ENVS=true
            CLEAN_ALL=false
            shift
            ;;
        --temp)
            CLEAN_TEMP=true
            CLEAN_ALL=false
            shift
            ;;
        --reports)
            CLEAN_REPORTS=true
            CLEAN_ALL=false
            shift
            ;;
        --all)
            CLEAN_ALL=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Set all flags if --all is specified
if [[ "$CLEAN_ALL" == "true" ]]; then
    CLEAN_LOGS=true
    CLEAN_ENVS=true
    CLEAN_TEMP=true
    CLEAN_REPORTS=true
fi

# Function to remove files/directories with dry-run support
safe_remove() {
    local path="$1"
    local description="$2"
    
    if [[ -e "$path" ]]; then
        if [[ "$DRY_RUN" == "true" ]]; then
            log_info "[DRY-RUN] Would remove: $path ($description)"
        else
            log_info "Removing: $path ($description)"
            rm -rf "$path"
            if [[ ! -e "$path" ]]; then
                log_success "Removed: $description"
            else
                log_error "Failed to remove: $path"
            fi
        fi
    else
        log_info "Not found: $path ($description)"
    fi
}

# Clean log files
clean_logs() {
    log_info "Cleaning log files..."
    
    # Remove log files in reports directory
    if [[ -d "$REPORTS_DIR" ]]; then
        find "$REPORTS_DIR" -name "*.log" -type f | while read -r log_file; do
            safe_remove "$log_file" "log file"
        done
    fi
    
    # Remove any temporary log files
    find "$TEST_PROJECT_REPOS_DIR" -name "*.log" -type f | while read -r log_file; do
        safe_remove "$log_file" "temporary log file"
    done
    
    # Remove Python cache files
    find "$TEST_PROJECT_REPOS_DIR" -name "__pycache__" -type d | while read -r cache_dir; do
        safe_remove "$cache_dir" "Python cache directory"
    done
    
    find "$TEST_PROJECT_REPOS_DIR" -name "*.pyc" -type f | while read -r pyc_file; do
        safe_remove "$pyc_file" "Python compiled file"
    done
}

# Clean virtual environments
clean_envs() {
    log_info "Cleaning virtual environments..."
    
    # Remove test virtual environments
    if [[ -d "$TEST_PROJECT_REPOS_DIR/venv" ]]; then
        safe_remove "$TEST_PROJECT_REPOS_DIR/venv" "test virtual environment"
    fi
    
    # Remove any conda environments (be careful here)
    if command -v conda &> /dev/null; then
        local test_envs=$(conda env list | grep "classdock-test" | awk '{print $1}' || true)
        if [[ -n "$test_envs" ]]; then
            echo "$test_envs" | while read -r env_name; do
                if [[ "$DRY_RUN" == "true" ]]; then
                    log_info "[DRY-RUN] Would remove conda environment: $env_name"
                else
                    log_info "Removing conda environment: $env_name"
                    conda env remove -n "$env_name" -y || log_error "Failed to remove conda env: $env_name"
                fi
            done
        fi
    fi
}

# Clean temporary files
clean_temp() {
    log_info "Cleaning temporary files..."
    
    # Remove temporary directories created during testing
    find "$TEST_PROJECT_REPOS_DIR" -name "tmp_*" -type d | while read -r tmp_dir; do
        safe_remove "$tmp_dir" "temporary directory"
    done
    
    # Remove any .tmp files
    find "$TEST_PROJECT_REPOS_DIR" -name "*.tmp" -type f | while read -r tmp_file; do
        safe_remove "$tmp_file" "temporary file"
    done
    
    # Remove build artifacts
    find "$TEST_PROJECT_REPOS_DIR" -name "build" -type d | while read -r build_dir; do
        safe_remove "$build_dir" "build directory"
    done
    
    find "$TEST_PROJECT_REPOS_DIR" -name "dist" -type d | while read -r dist_dir; do
        safe_remove "$dist_dir" "distribution directory"
    done
    
    find "$TEST_PROJECT_REPOS_DIR" -name "*.egg-info" -type d | while read -r egg_dir; do
        safe_remove "$egg_dir" "egg-info directory"
    done
    
    # Remove coverage files
    find "$TEST_PROJECT_REPOS_DIR" -name ".coverage" -type f | while read -r cov_file; do
        safe_remove "$cov_file" "coverage file"
    done
    
    find "$TEST_PROJECT_REPOS_DIR" -name "htmlcov" -type d | while read -r htmlcov_dir; do
        safe_remove "$htmlcov_dir" "HTML coverage directory"
    done
}

# Clean test reports
clean_reports() {
    log_info "Cleaning test reports..."
    
    if [[ -d "$REPORTS_DIR" ]]; then
        # Keep the directory structure but remove old files
        find "$REPORTS_DIR" -name "*.html" -type f | while read -r report_file; do
            safe_remove "$report_file" "HTML report"
        done
        
        find "$REPORTS_DIR" -name "*.xml" -type f | while read -r xml_file; do
            safe_remove "$xml_file" "XML report"
        done
        
        find "$REPORTS_DIR" -name "*.json" -type f | while read -r json_file; do
            safe_remove "$json_file" "JSON report"
        done
        
        # Remove old dated directories (older than 7 days)
        find "$REPORTS_DIR" -type d -mtime +7 | while read -r old_dir; do
            if [[ "$old_dir" != "$REPORTS_DIR" ]]; then
                safe_remove "$old_dir" "old report directory"
            fi
        done
    fi
}

# Show cleanup summary
show_cleanup_summary() {
    echo
    echo "=================================================="
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "Cleanup Summary (DRY RUN)"
    else
        echo "Cleanup Summary"
    fi
    echo "=================================================="
    echo "Logs cleaned: $CLEAN_LOGS"
    echo "Environments cleaned: $CLEAN_ENVS"
    echo "Temporary files cleaned: $CLEAN_TEMP"
    echo "Reports cleaned: $CLEAN_REPORTS"
    echo "=================================================="
}

# Main cleanup execution
main() {
    log_info "Starting cleanup of test environment"
    log_info "Test directory: $TEST_PROJECT_REPOS_DIR"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_warning "DRY RUN MODE - No files will actually be deleted"
    fi
    
    # Ensure we're in the right directory
    if [[ ! -d "$TEST_PROJECT_REPOS_DIR" ]]; then
        log_error "Test directory not found: $TEST_PROJECT_REPOS_DIR"
        exit 1
    fi
    
    # Execute cleanup based on options
    if [[ "$CLEAN_LOGS" == "true" ]]; then
        clean_logs
    fi
    
    if [[ "$CLEAN_ENVS" == "true" ]]; then
        clean_envs
    fi
    
    if [[ "$CLEAN_TEMP" == "true" ]]; then
        clean_temp
    fi
    
    if [[ "$CLEAN_REPORTS" == "true" ]]; then
        clean_reports
    fi
    
    # Show summary
    show_cleanup_summary
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "Dry run completed. Use without --dry-run to actually clean files."
    else
        log_success "Cleanup completed successfully!"
    fi
}

# Script execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi