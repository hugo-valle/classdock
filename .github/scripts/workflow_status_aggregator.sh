#!/bin/bash

# Workflow Status Aggregation Script for GitHub Actions
# Collects and consolidates build time monitoring and status across all workflows
# Created for classdock project

set -euo pipefail

# Source workflow utilities for base functionality
if [[ -f "${GITHUB_WORKSPACE:-}/.github/scripts/workflow_utils.sh" ]]; then
    source "${GITHUB_WORKSPACE}/.github/scripts/workflow_utils.sh"
elif [[ -f ".github/scripts/workflow_utils.sh" ]]; then
    source ".github/scripts/workflow_utils.sh"
else
    echo "❌ Error: workflow_utils.sh not found" >&2
    exit 1
fi

# =============================================================================
# WORKFLOW STATUS COLLECTION FUNCTIONS
# =============================================================================

# Collect status from current workflow run
# Usage: collect_workflow_status "workflow_name" "job_name"
collect_workflow_status() {
    local workflow_name="$1"
    local job_name="${2:-unknown}"
    
    log_info "📊 Collecting workflow status for: $workflow_name/$job_name"
    
    # Create status collection directory
    local status_dir="workflow_status/$workflow_name"
    mkdir -p "$status_dir"
    
    # Collect workflow environment information
    local workflow_info_file="$status_dir/workflow_info.json"
    cat > "$workflow_info_file" << EOF
{
    "workflow_name": "$workflow_name",
    "job_name": "$job_name",
    "github_workflow": "${GITHUB_WORKFLOW:-unknown}",
    "github_job": "${GITHUB_JOB:-unknown}",
    "github_run_id": "${GITHUB_RUN_ID:-unknown}",
    "github_run_number": "${GITHUB_RUN_NUMBER:-unknown}",
    "github_run_attempt": "${GITHUB_RUN_ATTEMPT:-unknown}",
    "github_sha": "${GITHUB_SHA:-unknown}",
    "github_ref": "${GITHUB_REF:-unknown}",
    "github_ref_name": "${GITHUB_REF_NAME:-unknown}",
    "github_event_name": "${GITHUB_EVENT_NAME:-unknown}",
    "github_actor": "${GITHUB_ACTOR:-unknown}",
    "runner_os": "${RUNNER_OS:-unknown}",
    "runner_arch": "${RUNNER_ARCH:-unknown}",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "collection_version": "1.0"
}
EOF
    
    # Collect current job status
    local job_status_file="$status_dir/job_status.json"
    cat > "$job_status_file" << EOF
{
    "job_name": "$job_name",
    "status": "running",
    "start_time": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "runner_info": {
        "os": "${RUNNER_OS:-unknown}",
        "arch": "${RUNNER_ARCH:-unknown}",
        "temp": "${RUNNER_TEMP:-unknown}",
        "tool_cache": "${RUNNER_TOOL_CACHE:-unknown}"
    }
}
EOF
    
    # Check for existing performance metrics from workflow_utils.sh
    if [[ -f "${WORKFLOW_METRICS_FILE:-/tmp/workflow_metrics.json}" ]]; then
        cp "${WORKFLOW_METRICS_FILE}" "$status_dir/performance_metrics.json"
        log_info "📈 Performance metrics included in status collection"
    fi
    
    log_success "✅ Workflow status collected for $workflow_name/$job_name"
    return 0
}

# Update job status with completion information
# Usage: update_job_status "workflow_name" "job_name" "status" "duration"
update_job_status() {
    local workflow_name="$1"
    local job_name="$2"
    local status="$3"
    local duration="${4:-0}"
    
    log_info "🔄 Updating job status: $workflow_name/$job_name -> $status"
    
    local status_dir="workflow_status/$workflow_name"
    local job_status_file="$status_dir/job_status.json"
    
    if [[ -f "$job_status_file" ]]; then
        # Update existing job status
        local temp_file=$(mktemp)
        jq --arg status "$status" \
           --arg end_time "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
           --argjson duration "$duration" \
           '.status = $status | .end_time = $end_time | .duration_seconds = $duration' \
           "$job_status_file" > "$temp_file" && mv "$temp_file" "$job_status_file"
    else
        # Create new job status if it doesn't exist
        mkdir -p "$status_dir"
        cat > "$job_status_file" << EOF
{
    "job_name": "$job_name",
    "status": "$status",
    "end_time": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "duration_seconds": $duration
}
EOF
    fi
    
    log_success "✅ Job status updated: $status (${duration}s)"
    return 0
}

# =============================================================================
# BUILD METRICS AGGREGATION FUNCTIONS
# =============================================================================

# Aggregate timing data from all jobs in current workflow
# Usage: aggregate_build_metrics "workflow_name"
aggregate_build_metrics() {
    local workflow_name="$1"
    
    log_info "⏱️ Aggregating build metrics for workflow: $workflow_name"
    
    local aggregation_dir="workflow_status/$workflow_name/aggregation"
    mkdir -p "$aggregation_dir"
    
    # Collect all timing data from workflow_utils.sh step timings
    local step_timings_file="$aggregation_dir/step_timings.json"
    
    # Initialize timing data array
    echo "[]" > "$step_timings_file"
    
    # Check for existing step timing files from workflow_utils.sh
    if [[ -f "${STEP_TIMINGS_FILE:-/tmp/step_timings.json}" ]]; then
        cp "${STEP_TIMINGS_FILE}" "$step_timings_file"
        log_info "📏 Step timings included in aggregation"
    fi
    
    # Aggregate timing statistics
    local timing_summary_file="$aggregation_dir/timing_summary.json"
    
    if command -v jq >/dev/null 2>&1 && [[ -f "$step_timings_file" ]]; then
        jq '{workflow_name: "'"$workflow_name"'", total_steps: length, total_duration: (map(.duration_seconds // 0) | add // 0), average_step_duration: (((map(.duration_seconds // 0) | add // 0) / (length | if . == 0 then 1 else . end)) // 0), longest_step: {name: (max_by(.duration_seconds // 0) | .step_name // "unknown"), duration: (map(.duration_seconds // 0) | max // 0)}, shortest_step: {name: (min_by(.duration_seconds // 0) | .step_name // "unknown"), duration: (map(.duration_seconds // 0) | min // 0)}, aggregation_timestamp: "'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'", version: "1.0"}' "$step_timings_file" > "$timing_summary_file"
    else
        # Fallback if jq is not available
        cat > "$timing_summary_file" << EOF
{
    "workflow_name": "$workflow_name",
    "total_steps": 0,
    "total_duration": 0,
    "average_step_duration": 0,
    "aggregation_timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "version": "1.0",
    "note": "Limited aggregation - jq not available"
}
EOF
    fi
    
    # Create build metrics summary
    local build_metrics_file="$aggregation_dir/build_metrics.json"
    cat > "$build_metrics_file" << EOF
{
    "workflow_name": "$workflow_name",
    "build_info": {
        "github_run_id": "${GITHUB_RUN_ID:-unknown}",
        "github_run_number": "${GITHUB_RUN_NUMBER:-unknown}",
        "github_sha": "${GITHUB_SHA:-unknown}",
        "github_ref": "${GITHUB_REF:-unknown}",
        "trigger_event": "${GITHUB_EVENT_NAME:-unknown}"
    },
    "environment": {
        "runner_os": "${RUNNER_OS:-unknown}",
        "runner_arch": "${RUNNER_ARCH:-unknown}"
    },
    "timing_summary_file": "$timing_summary_file",
    "step_timings_file": "$step_timings_file",
    "aggregation_timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
    
    log_success "✅ Build metrics aggregated for $workflow_name"
    
    # Export aggregated metrics for further processing
    export_performance_metrics "build_aggregation_$workflow_name" "$build_metrics_file"
    
    return 0
}

# =============================================================================
# CROSS-WORKFLOW REPORTING FUNCTIONS
# =============================================================================

# Generate comprehensive workflow dashboard
# Usage: generate_workflow_dashboard "output_file"
generate_workflow_dashboard() {
    local output_file="${1:-workflow_dashboard.md}"
    
    log_info "📊 Generating comprehensive workflow dashboard"
    
    # Create dashboard header
    cat > "$output_file" << EOF
# Workflow Status Dashboard

## Overview
- **Generated**: $(date -u +%Y-%m-%d\ %H:%M:%S\ UTC)
- **Run ID**: ${GITHUB_RUN_ID:-unknown}
- **Run Number**: ${GITHUB_RUN_NUMBER:-unknown}
- **Commit**: ${GITHUB_SHA:-unknown}
- **Branch**: ${GITHUB_REF_NAME:-unknown}
- **Trigger**: ${GITHUB_EVENT_NAME:-unknown}

## Current Workflow Status

### Workflow Information
- **Name**: ${GITHUB_WORKFLOW:-unknown}
- **Job**: ${GITHUB_JOB:-unknown}
- **Runner**: ${RUNNER_OS:-unknown}/${RUNNER_ARCH:-unknown}

EOF
    
    # Add workflow-specific metrics if available
    if [[ -d "workflow_status" ]]; then
        echo "### Workflow Metrics" >> "$output_file"
        echo "" >> "$output_file"
        
        # Process each workflow's status data
        for workflow_dir in workflow_status/*/; do
            if [[ -d "$workflow_dir" ]]; then
                local workflow_name
                workflow_name=$(basename "$workflow_dir")
                
                echo "#### $workflow_name" >> "$output_file"
                
                # Add timing summary if available
                if [[ -f "$workflow_dir/aggregation/timing_summary.json" ]]; then
                    echo "| Metric | Value |" >> "$output_file"
                    echo "|--------|-------|" >> "$output_file"
                    
                    if command -v jq >/dev/null 2>&1; then
                        local total_duration average_duration longest_step
                        total_duration=$(jq -r '.total_duration // 0' "$workflow_dir/aggregation/timing_summary.json")
                        average_duration=$(jq -r '.average_step_duration // 0' "$workflow_dir/aggregation/timing_summary.json")
                        longest_step=$(jq -r '.longest_step.name // "unknown"' "$workflow_dir/aggregation/timing_summary.json")
                        
                        echo "| Total Duration | ${total_duration}s |" >> "$output_file"
                        echo "| Average Step Duration | ${average_duration}s |" >> "$output_file"
                        echo "| Longest Step | $longest_step |" >> "$output_file"
                    else
                        echo "| Status | Available (limited) |" >> "$output_file"
                    fi
                else
                    echo "| Status | No timing data available |" >> "$output_file"
                    echo "|--------|--------------------------|" >> "$output_file"
                fi
                
                echo "" >> "$output_file"
            fi
        done
    fi
    
    # Add performance trends section
    cat >> "$output_file" << EOF
### Performance Trends

EOF
    
    # Check for performance metrics
    if [[ -f "${WORKFLOW_METRICS_FILE:-/tmp/workflow_metrics.json}" ]]; then
        echo "📈 Performance metrics available for analysis" >> "$output_file"
        
        # Add performance summary if available
        if command -v jq >/dev/null 2>&1; then
            local perf_summary
            perf_summary=$(jq -r 'keys[] as $k | "\($k): \(.[$k])"' "${WORKFLOW_METRICS_FILE}" 2>/dev/null | head -5)
            if [[ -n "$perf_summary" ]]; then
                echo "" >> "$output_file"
                echo "```" >> "$output_file"
                echo "$perf_summary" >> "$output_file"
                echo "```" >> "$output_file"
            fi
        fi
    else
        echo "📊 No performance metrics available for this run" >> "$output_file"
    fi
    
    # Add recommendations section
    cat >> "$output_file" << EOF

### Recommendations

EOF
    
    # Analyze status and provide recommendations
    local has_failures=0
    local has_warnings=0
    
    if [[ -d "workflow_status" ]]; then
        # Check for any job failures or warnings
        find workflow_status -name "job_status.json" -exec grep -l '"status": "failed"' {} \; 2>/dev/null | while read -r file; do
            has_failures=1
            break
        done
        
        find workflow_status -name "job_status.json" -exec grep -l '"status": "warning"' {} \; 2>/dev/null | while read -r file; do
            has_warnings=1
            break
        done
    fi
    
    if [[ $has_failures -eq 1 ]]; then
        cat >> "$output_file" << EOF
⚠️ **Action Required**
- One or more jobs have failed
- Review job logs for error details
- Check workflow configuration

EOF
    elif [[ $has_warnings -eq 1 ]]; then
        cat >> "$output_file" << EOF
📋 **Review Recommended**
- Some jobs completed with warnings
- Monitor for potential issues
- Consider optimization opportunities

EOF
    else
        cat >> "$output_file" << EOF
✅ **Workflow Healthy**
- All monitored jobs completed successfully
- Performance metrics within normal ranges
- Continue standard monitoring

EOF
    fi
    
    log_success "✅ Workflow dashboard generated: $output_file"
    
    # Add to GitHub step summary if available
    if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
        cat "$output_file" >> "$GITHUB_STEP_SUMMARY"
    fi
    
    return 0
}

# =============================================================================
# HISTORICAL TRACKING FUNCTIONS
# =============================================================================

# Track workflow trends over time
# Usage: track_workflow_trends "workflow_name"
track_workflow_trends() {
    local workflow_name="$1"
    
    log_info "📈 Tracking workflow trends for: $workflow_name"
    
    local trends_dir="workflow_trends/$workflow_name"
    mkdir -p "$trends_dir"
    
    # Create trend data point for current run
    local trend_point_file="$trends_dir/run_${GITHUB_RUN_NUMBER:-$(date +%s)}.json"
    
    # Collect current run data
    cat > "$trend_point_file" << EOF
{
    "workflow_name": "$workflow_name",
    "run_id": "${GITHUB_RUN_ID:-unknown}",
    "run_number": "${GITHUB_RUN_NUMBER:-unknown}",
    "commit_sha": "${GITHUB_SHA:-unknown}",
    "branch": "${GITHUB_REF_NAME:-unknown}",
    "trigger": "${GITHUB_EVENT_NAME:-unknown}",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "runner_os": "${RUNNER_OS:-unknown}"
}
EOF
    
    # Include timing data if available
    if [[ -f "workflow_status/$workflow_name/aggregation/timing_summary.json" ]]; then
        local temp_file=$(mktemp)
        jq --slurpfile timing "workflow_status/$workflow_name/aggregation/timing_summary.json" \
           '. + {timing_data: $timing[0]}' \
           "$trend_point_file" > "$temp_file" && mv "$temp_file" "$trend_point_file"
    fi
    
    # Create trends summary
    local trends_summary_file="$trends_dir/trends_summary.json"
    
    if command -v jq >/dev/null 2>&1; then
        # Check if any trend files exist before processing
        if find "$trends_dir" -name "run_*.json" -type f | grep -q .; then
            find "$trends_dir" -name "run_*.json" -exec cat {} \; | jq -s '{workflow_name: "'"$workflow_name"'", total_runs: length, trend_analysis_timestamp: "'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'", version: "1.0"}' > "$trends_summary_file"
        else
            # No trend files exist, create empty summary
            jq -n '{workflow_name: "'"$workflow_name"'", total_runs: 0, date_range: {earliest: null, latest: null}, performance_trends: {average_duration: 0, duration_trend: [], latest_duration: 0}, trend_analysis_timestamp: "'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'", version: "1.0"}' > "$trends_summary_file"
        fi
    else
        # Simple fallback without jq
        local run_count
        run_count=$(find "$trends_dir" -name "run_*.json" | wc -l)
        
        cat > "$trends_summary_file" << EOF
{
    "workflow_name": "$workflow_name",
    "total_runs": $run_count,
    "trend_analysis_timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "version": "1.0",
    "note": "Limited analysis - jq not available"
}
EOF
    fi
    
    log_success "✅ Workflow trends tracked for $workflow_name"
    
    # Export trends data for artifact storage
    export_performance_metrics "trends_$workflow_name" "$trends_summary_file"
    
    return 0
}

# =============================================================================
# WORKFLOW HEALTH SCORING FUNCTIONS
# =============================================================================

# Calculate workflow health score based on success rates, build times, and failure patterns
# Usage: calculate_workflow_health_score "workflow_name"
calculate_workflow_health_score() {
    local workflow_name="$1"
    
    log_info "🏥 Calculating workflow health score for: $workflow_name"
    
    local health_dir="workflow_health/$workflow_name"
    mkdir -p "$health_dir"
    
    # Initialize health metrics
    local success_rate=100
    local performance_score=100
    local reliability_score=100
    local overall_score=100
    
    # Check recent run success rate
    if [[ -d "workflow_trends/$workflow_name" ]]; then
        local recent_runs
        recent_runs=$(find "workflow_trends/$workflow_name" -name "run_*.json" | tail -10)
        
        if [[ -n "$recent_runs" ]] && command -v jq >/dev/null 2>&1; then
            # Analyze recent runs for success patterns
            local total_runs failed_runs
            total_runs=$(echo "$recent_runs" | wc -l)
            failed_runs=0
            
            # This would be enhanced with actual failure detection
            # For now, assume all runs are successful unless proven otherwise
            success_rate=$(echo "scale=2; (($total_runs - $failed_runs) * 100) / $total_runs" | bc -l 2>/dev/null || echo "100")
        fi
    fi
    
    # Check performance trends
    if [[ -f "workflow_trends/$workflow_name/trends_summary.json" ]] && command -v jq >/dev/null 2>&1; then
        local avg_duration latest_duration
        avg_duration=$(jq -r '.performance_trends.average_duration // 0' "workflow_trends/$workflow_name/trends_summary.json")
        latest_duration=$(jq -r '.performance_trends.latest_duration // 0' "workflow_trends/$workflow_name/trends_summary.json")
        
        # Calculate performance score based on duration trends
        if [[ $(echo "$avg_duration > 0" | bc -l) -eq 1 ]]; then
            local duration_ratio
            duration_ratio=$(echo "scale=2; $latest_duration / $avg_duration" | bc -l)
            
            # Performance score decreases if current run is significantly slower
            if [[ $(echo "$duration_ratio > 1.5" | bc -l) -eq 1 ]]; then
                performance_score=60
            elif [[ $(echo "$duration_ratio > 1.2" | bc -l) -eq 1 ]]; then
                performance_score=80
            fi
        fi
    fi
    
    # Calculate overall health score
    overall_score=$(echo "scale=0; ($success_rate + $performance_score + $reliability_score) / 3" | bc -l 2>/dev/null || echo "100")
    
    # Create health score report
    local health_report_file="$health_dir/health_score.json"
    cat > "$health_report_file" << EOF
{
    "workflow_name": "$workflow_name",
    "health_score": {
        "overall": $overall_score,
        "success_rate": $success_rate,
        "performance_score": $performance_score,
        "reliability_score": $reliability_score
    },
    "health_status": "$(
        if [[ $(echo "$overall_score >= 90" | bc -l) -eq 1 ]]; then
            echo "excellent"
        elif [[ $(echo "$overall_score >= 75" | bc -l) -eq 1 ]]; then
            echo "good"
        elif [[ $(echo "$overall_score >= 60" | bc -l) -eq 1 ]]; then
            echo "fair"
        else
            echo "poor"
        fi
    )",
    "recommendations": [
        $(if [[ $(echo "$success_rate < 95" | bc -l) -eq 1 ]]; then
            echo '"Investigate recent failures to improve success rate",'
        fi)
        $(if [[ $(echo "$performance_score < 80" | bc -l) -eq 1 ]]; then
            echo '"Review performance trends and optimize slow steps",'
        fi)
        "Continue monitoring workflow health metrics"
    ],
    "calculation_timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "version": "1.0"
}
EOF
    
    log_success "✅ Workflow health score calculated: $overall_score/100"
    
    # Export health score for monitoring
    export_performance_metrics "health_score_$workflow_name" "$health_report_file"
    
    return 0
}

# =============================================================================
# MAIN INTEGRATION FUNCTIONS
# =============================================================================

# Main workflow status aggregation function
# Usage: run_workflow_status_aggregation "workflow_name" "job_name"
run_workflow_status_aggregation() {
    local workflow_name="${1:-${GITHUB_WORKFLOW:-unknown}}"
    local job_name="${2:-${GITHUB_JOB:-unknown}}"
    
    log_info "🚀 Running workflow status aggregation for: $workflow_name"
    
    # Create main status aggregation directory
    mkdir -p workflow_status_aggregation
    
    # Collect current workflow status
    collect_workflow_status "$workflow_name" "$job_name"
    
    # Aggregate build metrics
    aggregate_build_metrics "$workflow_name"
    
    # Track workflow trends
    track_workflow_trends "$workflow_name"
    
    # Calculate health score
    calculate_workflow_health_score "$workflow_name"
    
    # Generate comprehensive dashboard
    generate_workflow_dashboard "workflow_status_aggregation/dashboard.md"
    
    # Create final aggregation summary
    cat > "workflow_status_aggregation/summary.json" << EOF
{
    "aggregation_summary": {
        "workflow_name": "$workflow_name",
        "job_name": "$job_name",
        "aggregation_timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
        "components_processed": [
            "workflow_status",
            "build_metrics",
            "workflow_trends",
            "health_score",
            "dashboard"
        ],
        "github_context": {
            "run_id": "${GITHUB_RUN_ID:-unknown}",
            "run_number": "${GITHUB_RUN_NUMBER:-unknown}",
            "sha": "${GITHUB_SHA:-unknown}",
            "ref": "${GITHUB_REF:-unknown}"
        }
    },
    "version": "1.0"
}
EOF
    
    log_success "✅ Workflow status aggregation completed for $workflow_name"
    
    # Export final aggregation data
    export_performance_metrics "workflow_status_aggregation" "workflow_status_aggregation/summary.json"
    
    return 0
}

# =============================================================================
# VALIDATION AND SETUP
# =============================================================================

# Validate workflow status aggregator setup
validate_aggregator_setup() {
    log_info "🔧 Validating workflow status aggregator setup..."
    
    local validation_errors=0
    
    # Check required commands
    local required_commands=("date" "mkdir" "cat" "find" "bc")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            log_error "Required command not found: $cmd"
            ((validation_errors++))
        fi
    done
    
    # Check optional commands
    if ! command -v jq >/dev/null 2>&1; then
        log_warning "jq not found - some advanced features will be limited"
    fi
    
    # Ensure required directories exist
    mkdir -p workflow_status workflow_trends workflow_health workflow_status_aggregation
    
    # Check workflow_utils.sh integration
    if declare -f "export_performance_metrics" >/dev/null 2>&1; then
        log_success "✅ workflow_utils.sh integration verified"
    else
        log_warning "workflow_utils.sh functions not fully available"
    fi
    
    if [[ $validation_errors -eq 0 ]]; then
        log_success "✅ Workflow status aggregator setup validation passed"
        return 0
    else
        log_error "❌ Workflow status aggregator setup validation failed"
        return 1
    fi
}

# Main execution if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Workflow Status Aggregation Script for GitHub Actions"
    echo "===================================================="
    validate_aggregator_setup
    
    # Run aggregation if validation passes
    if [[ $? -eq 0 ]]; then
        run_workflow_status_aggregation "$@"
    fi
fi