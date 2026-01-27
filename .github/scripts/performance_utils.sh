#!/bin/bash

# Performance Utilities Script for GitHub Actions Workflows
# Extends workflow_utils.sh with performance-specific functionality
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
# PERFORMANCE BENCHMARKING FUNCTIONS
# =============================================================================

# Benchmark script execution with timing and resource monitoring
# Usage: benchmark_script "test_name" "script_path" "script_args"
benchmark_script() {
    local test_name="$1"
    local script_path="$2"
    local script_args="${3:-}"
    
    log_info "🔬 Starting performance benchmark for: $test_name"
    
    # Create benchmark results directory
    local results_dir="performance_results/$test_name"
    mkdir -p "$results_dir"
    
    # Prepare timing and resource monitoring
    local start_time
    local end_time
    local duration
    local memory_usage
    local cpu_usage
    
    # Record start time with high precision
    start_time=$(date +%s.%N)
    
    # Execute script with resource monitoring using GNU time
    if command -v /usr/bin/time >/dev/null 2>&1; then
        log_info "📊 Executing $script_path with resource monitoring..."
        
        # Run script with detailed timing and resource usage
        /usr/bin/time -v -o "$results_dir/time_output.txt" \
            bash "$script_path" $script_args > "$results_dir/stdout.txt" 2> "$results_dir/stderr.txt" || {
            log_warning "Script execution completed with non-zero exit code"
        }
        
        # Extract memory and CPU usage from time output
        if [[ -f "$results_dir/time_output.txt" ]]; then
            memory_usage=$(grep "Maximum resident set size" "$results_dir/time_output.txt" | awk '{print $6}' || echo "0")
            cpu_usage=$(grep "Percent of CPU this job got" "$results_dir/time_output.txt" | awk '{print $7}' | tr -d '%' || echo "0")
        else
            memory_usage="0"
            cpu_usage="0"
        fi
    else
        log_warning "GNU time not available, using basic timing"
        
        # Fallback to basic execution without detailed resource monitoring
        bash "$script_path" $script_args > "$results_dir/stdout.txt" 2> "$results_dir/stderr.txt" || {
            log_warning "Script execution completed with non-zero exit code"
        }
        
        memory_usage="0"
        cpu_usage="0"
    fi
    
    # Record end time and calculate duration
    end_time=$(date +%s.%N)
    duration=$(echo "$end_time - $start_time" | bc -l)
    
    # Create performance metrics JSON
    cat > "$results_dir/metrics.json" << EOF
{
    "test_name": "$test_name",
    "script_path": "$script_path",
    "script_args": "$script_args",
    "execution_time_seconds": $duration,
    "memory_usage_kb": $memory_usage,
    "cpu_usage_percent": $cpu_usage,
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "benchmark_version": "1.0"
}
EOF
    
    log_success "✅ Benchmark completed for $test_name (${duration}s)"
    
    # Store metrics in global performance tracking
    echo "PERF_${test_name}_DURATION=$duration" >> "${GITHUB_ENV:-/dev/null}"
    echo "PERF_${test_name}_MEMORY=$memory_usage" >> "${GITHUB_ENV:-/dev/null}"
    echo "PERF_${test_name}_CPU=$cpu_usage" >> "${GITHUB_ENV:-/dev/null}"
    
    return 0
}

# Monitor system resources during script execution
# Usage: monitor_resources "monitoring_name" "command_to_monitor"
monitor_resources() {
    local monitoring_name="$1"
    local command_to_monitor="$2"
    
    log_info "📈 Starting resource monitoring for: $monitoring_name"
    
    local results_dir="performance_results/resource_monitoring/$monitoring_name"
    mkdir -p "$results_dir"
    
    # Start background resource monitoring
    {
        while true; do
            echo "$(date +%s),$(free -m | awk 'NR==2{printf "%.2f", $3*100/$2}'),$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)" >> "$results_dir/resource_usage.csv"
            sleep 2
        done
    } &
    local monitor_pid=$!
    
    # Execute the command being monitored
    local start_time end_time duration
    start_time=$(date +%s.%N)
    
    eval "$command_to_monitor" > "$results_dir/command_output.txt" 2> "$results_dir/command_error.txt" || {
        log_warning "Monitored command completed with non-zero exit code"
    }
    
    end_time=$(date +%s.%N)
    duration=$(echo "$end_time - $start_time" | bc -l)
    
    # Stop resource monitoring
    kill $monitor_pid 2>/dev/null || true
    wait $monitor_pid 2>/dev/null || true
    
    # Calculate resource usage statistics
    if [[ -f "$results_dir/resource_usage.csv" ]]; then
        local avg_memory max_memory avg_cpu max_cpu
        avg_memory=$(awk -F',' '{sum+=$2; count++} END {if(count>0) print sum/count; else print 0}' "$results_dir/resource_usage.csv")
        max_memory=$(awk -F',' '{if($2>max) max=$2} END {print max+0}' "$results_dir/resource_usage.csv")
        avg_cpu=$(awk -F',' '{sum+=$3; count++} END {if(count>0) print sum/count; else print 0}' "$results_dir/resource_usage.csv")
        max_cpu=$(awk -F',' '{if($3>max) max=$3} END {print max+0}' "$results_dir/resource_usage.csv")
        
        # Create resource monitoring report
        cat > "$results_dir/resource_report.json" << EOF
{
    "monitoring_name": "$monitoring_name",
    "command": "$command_to_monitor",
    "execution_time_seconds": $duration,
    "memory_usage": {
        "average_percent": $avg_memory,
        "peak_percent": $max_memory
    },
    "cpu_usage": {
        "average_percent": $avg_cpu,
        "peak_percent": $max_cpu
    },
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "monitoring_version": "1.0"
}
EOF
        
        log_success "✅ Resource monitoring completed for $monitoring_name"
        log_info "📊 Avg Memory: ${avg_memory}%, Peak Memory: ${max_memory}%"
        log_info "📊 Avg CPU: ${avg_cpu}%, Peak CPU: ${max_cpu}%"
    else
        log_error "Resource monitoring data not available"
    fi
    
    return 0
}

# =============================================================================
# BASELINE MANAGEMENT FUNCTIONS
# =============================================================================

# Store performance baseline in GitHub artifacts
# Usage: store_baseline "scenario_name"
store_baseline() {
    local scenario_name="$1"
    
    log_info "💾 Storing performance baseline for: $scenario_name"
    
    local baseline_dir="performance_baselines/$scenario_name"
    mkdir -p "$baseline_dir"
    
    # Collect all metrics for this scenario
    if [[ -d "performance_results" ]]; then
        # Create baseline summary from current results
        find performance_results -name "metrics.json" -exec cat {} \; | jq -s '.' > "$baseline_dir/baseline_metrics.json"
        
        # Add baseline metadata
        cat > "$baseline_dir/baseline_info.json" << EOF
{
    "scenario_name": "$scenario_name",
    "created_timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "git_commit": "${GITHUB_SHA:-unknown}",
    "git_ref": "${GITHUB_REF:-unknown}",
    "workflow_run_id": "${GITHUB_RUN_ID:-unknown}",
    "baseline_version": "1.0"
}
EOF
        
        log_success "✅ Performance baseline stored for $scenario_name"
    else
        log_warning "No performance results found to store as baseline"
    fi
    
    return 0
}

# Load performance baseline from previous runs
# Usage: load_baseline "scenario_name"
load_baseline() {
    local scenario_name="$1"
    
    log_info "📂 Loading performance baseline for: $scenario_name"
    
    # Try to download baseline from artifacts
    # This would typically be handled by GitHub Actions artifact download
    # For now, we'll create placeholder baseline if none exists
    
    local baseline_dir="performance_baselines/$scenario_name"
    
    if [[ ! -d "$baseline_dir" ]] || [[ ! -f "$baseline_dir/baseline_metrics.json" ]]; then
        log_warning "No previous baseline found for $scenario_name, will create new baseline"
        
        # Create placeholder baseline directory
        mkdir -p "$baseline_dir"
        echo "[]" > "$baseline_dir/baseline_metrics.json"
        
        cat > "$baseline_dir/baseline_info.json" << EOF
{
    "scenario_name": "$scenario_name",
    "created_timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "git_commit": "initial",
    "git_ref": "initial",
    "workflow_run_id": "initial",
    "baseline_version": "1.0",
    "note": "Initial baseline - no previous data available"
}
EOF
        return 1
    fi
    
    log_success "✅ Performance baseline loaded for $scenario_name"
    return 0
}

# Compare current performance with baseline
# Usage: compare_with_baseline "scenario_name" "threshold_percent"
compare_with_baseline() {
    local scenario_name="$1"
    local threshold_percent="${2:-20}"
    
    # Log to stderr so it doesn't interfere with the result capture
    log_info "🔍 Comparing current performance with baseline for: $scenario_name" >&2
    
    local baseline_dir="performance_baselines/$scenario_name"
    local comparison_dir="performance_results/comparisons/$scenario_name"
    mkdir -p "$comparison_dir"
    
    if [[ ! -f "$baseline_dir/baseline_metrics.json" ]]; then
        log_warning "No baseline available for comparison" >&2
        echo "baseline_zero"
        return 0
    fi
    
    # Create comparison script using jq to analyze metrics
    if command -v jq >/dev/null 2>&1; then
        # Compare execution times between baseline and current metrics
        local baseline_times current_times comparison_result
        
        baseline_times=$(jq -r '.[].execution_time_seconds // 0' "$baseline_dir/baseline_metrics.json" 2>/dev/null || echo "0")
        
        if [[ -f "performance_results/aggregated_metrics.json" ]]; then
            current_times=$(jq -r '.[].execution_time_seconds // 0' "performance_results/aggregated_metrics.json" 2>/dev/null || echo "0")
        else
            # Aggregate current metrics if not already done
            find performance_results -name "metrics.json" -exec cat {} \; | jq -s '.' > "performance_results/aggregated_metrics.json" 2>/dev/null || true
            current_times=$(jq -r '.[].execution_time_seconds // 0' "performance_results/aggregated_metrics.json" 2>/dev/null || echo "0")
        fi
        
        # Validate baseline_times and current_times are numeric
        if ! [[ "$baseline_times" =~ ^[0-9]+\.?[0-9]*$ ]]; then
            baseline_times="0"
        fi
        if ! [[ "$current_times" =~ ^[0-9]+\.?[0-9]*$ ]]; then
            current_times="0"
        fi
        
        # Calculate percentage difference
        comparison_result=$(echo "$baseline_times $current_times $threshold_percent" | awk '{
            if ($1 == 0) {
                print "baseline_zero"
            } else {
                diff_percent = (($2 - $1) / $1) * 100
                if (diff_percent > $3) {
                    printf "regression:%.1f", diff_percent
                } else if (diff_percent < -$3) {
                    printf "improvement:%.1f", diff_percent
                } else {
                    printf "acceptable:%.1f", diff_percent
                }
            }
        }')
        
        # Create comparison report
        cat > "$comparison_dir/comparison_report.json" << EOF
{
    "scenario_name": "$scenario_name",
    "baseline_time": $baseline_times,
    "current_time": $current_times,
    "threshold_percent": $threshold_percent,
    "comparison_result": "$comparison_result",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
        
        # Output only the result to stdout
        echo "$comparison_result"
        log_success "✅ Performance comparison completed for $scenario_name" >&2
    else
        log_error "jq not available for performance comparison" >&2
        echo "error:jq_missing"
        return 1
    fi
    
    return 0
}

# =============================================================================
# REGRESSION DETECTION FUNCTIONS
# =============================================================================

# Detect performance regressions against threshold
# Usage: detect_regression "scenario_name" "threshold_percent"
detect_regression() {
    local scenario_name="$1"
    local threshold_percent="${2:-20}"
    
    log_info "🚨 Detecting performance regressions for: $scenario_name"
    
    # Compare with baseline (capture only the result, not log messages)
    local comparison_result
    comparison_result=$(compare_with_baseline "$scenario_name" "$threshold_percent" 2>/dev/null | tail -1)
    
    # Validate comparison result format
    if [[ -z "$comparison_result" ]]; then
        log_error "Failed to get comparison result"
        return 1
    fi
    
    case "$comparison_result" in
        regression:*)
            local regression_percent
            regression_percent=$(echo "$comparison_result" | cut -d':' -f2)
            
            # Validate regression percentage is numeric
            if ! [[ "$regression_percent" =~ ^-?[0-9]+\.?[0-9]*$ ]]; then
                log_error "Invalid regression percentage: $regression_percent"
                return 1
            fi
            
            # Check if regression exceeds threshold
            local exceeds_threshold
            exceeds_threshold=$(echo "$regression_percent $threshold_percent" | awk '{print ($1 > $2) ? "yes" : "no"}')
            
            if [[ "$exceeds_threshold" == "yes" ]]; then
                log_error "⚠️ Performance regression detected above ${threshold_percent}% threshold"
                log_error "Regression: ${regression_percent}% slower than baseline"
                
                # Create regression alert
                mkdir -p "performance_results"
                cat > "performance_results/regression_alert.json" << EOF
{
    "scenario_name": "$scenario_name",
    "regression_type": "performance_slowdown",
    "threshold_percent": $threshold_percent,
    "actual_percent": $regression_percent,
    "severity": "high",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "action_required": "investigate_performance_degradation"
}
EOF
                return 1
            else
                log_info "Performance regression ${regression_percent}% is within acceptable threshold (${threshold_percent}%)"
                return 0
            fi
            ;;
        improvement:*)
            local improvement_percent
            improvement_percent=$(echo "$comparison_result" | cut -d':' -f2 | tr -d '-')
            log_success "✅ Performance improvement detected: ${improvement_percent}% faster than baseline"
            return 0
            ;;
        acceptable:*)
            local change_percent
            change_percent=$(echo "$comparison_result" | cut -d':' -f2)
            log_success "✅ Performance within acceptable range: ${change_percent}% change"
            return 0
            ;;
        baseline_zero)
            log_warning "⚠️ No baseline data available for regression detection"
            return 0
            ;;
        *)
            log_error "Unknown comparison result format: '$comparison_result'" >&2
            log_error "Expected format: 'regression:X.X' or 'improvement:X.X' or 'acceptable:X.X' or 'baseline_zero'" >&2
            log_error "This may indicate a parsing issue in the performance comparison" >&2
            return 1
            ;;
    esac
}

# =============================================================================
# PERFORMANCE REPORTING FUNCTIONS
# =============================================================================

# Generate comprehensive performance report
# Usage: generate_performance_report "scenario_name" "output_directory"
generate_performance_report() {
    local scenario_name="$1"
    local output_directory="${2:-performance_results}"
    
    log_info "📊 Generating performance report for: $scenario_name"
    
    mkdir -p "$output_directory"
    
    local report_file="$output_directory/performance_report_${scenario_name}.md"
    
    # Create comprehensive performance report
    cat > "$report_file" << EOF
# Performance Report: $scenario_name

## Summary
- **Scenario**: $scenario_name
- **Report Generated**: $(date -u +%Y-%m-%d\ %H:%M:%S\ UTC)
- **Git Commit**: ${GITHUB_SHA:-unknown}
- **Workflow Run**: ${GITHUB_RUN_ID:-unknown}

## Performance Metrics

### Execution Times
EOF
    
    # Add performance metrics if available
    if [[ -d "performance_results/$scenario_name" ]]; then
        echo "| Test Name | Duration (s) | Memory (KB) | CPU (%) |" >> "$report_file"
        echo "|-----------|--------------|-------------|---------|" >> "$report_file"
        
        # Process all metrics files for this scenario
        find "performance_results/$scenario_name" -name "metrics.json" -exec cat {} \; | jq -r '
            [.test_name, .execution_time_seconds, .memory_usage_kb, .cpu_usage_percent] | 
            @csv' | sed 's/"//g' | while IFS=',' read -r test_name duration memory cpu; do
            echo "| $test_name | $duration | $memory | $cpu |" >> "$report_file"
        done 2>/dev/null || {
            echo "| No detailed metrics available | - | - | - |" >> "$report_file"
        }
    fi
    
    # Add resource monitoring section if available
    if [[ -d "performance_results/resource_monitoring" ]]; then
        cat >> "$report_file" << EOF

### Resource Usage

EOF
        find "performance_results/resource_monitoring" -name "resource_report.json" -exec cat {} \; | jq -r '
            "- **" + .monitoring_name + "**: Avg Memory " + (.memory_usage.average_percent|tostring) + "%, Peak CPU " + (.cpu_usage.peak_percent|tostring) + "%"
        ' >> "$report_file" 2>/dev/null || {
            echo "- No resource monitoring data available" >> "$report_file"
        }
    fi
    
    # Add baseline comparison if available
    if [[ -d "performance_results/comparisons" ]]; then
        cat >> "$report_file" << EOF

### Baseline Comparison

EOF
        find "performance_results/comparisons" -name "comparison_report.json" -exec cat {} \; | jq -r '
            "- **" + .scenario_name + "**: " + .comparison_result + " (threshold: " + (.threshold_percent|tostring) + "%)"
        ' >> "$report_file" 2>/dev/null || {
            echo "- No baseline comparison data available" >> "$report_file"
        }
    fi
    
    # Add recommendations section
    cat >> "$report_file" << EOF

## Recommendations

EOF
    
    # Check for regressions and add recommendations
    if [[ -f "performance_results/regression_alert.json" ]]; then
        cat >> "$report_file" << EOF
⚠️ **Performance Regression Detected**

$(jq -r '"- Scenario: " + .scenario_name + "\n- Regression: " + (.actual_percent|tostring) + "% slower\n- Action: " + .action_required' performance_results/regression_alert.json 2>/dev/null || echo "- Review performance regression details")

EOF
    else
        cat >> "$report_file" << EOF
✅ **No Performance Regressions Detected**

- All performance metrics are within acceptable thresholds
- Continue monitoring for future regressions

EOF
    fi
    
    log_success "✅ Performance report generated: $report_file"
    
    # Create GitHub step summary if in Actions environment
    if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
        cat "$report_file" >> "$GITHUB_STEP_SUMMARY"
    fi
    
    return 0
}

# =============================================================================
# METRICS AGGREGATION FUNCTIONS
# =============================================================================

# Aggregate performance metrics from multiple test runs
# Usage: aggregate_performance_metrics "input_directory" "output_directory"
aggregate_performance_metrics() {
    local input_directory="$1"
    local output_directory="${2:-aggregated_results}"
    
    log_info "📈 Aggregating performance metrics from: $input_directory"
    
    mkdir -p "$output_directory"
    
    # Collect all metrics files
    local all_metrics_file="$output_directory/all_metrics.json"
    local summary_file="$output_directory/summary.json"
    local dashboard_file="$output_directory/dashboard.md"
    
    # Aggregate all JSON metrics files
    find "$input_directory" -name "*.json" -path "*/metrics.json" -exec cat {} \; | jq -s '.' > "$all_metrics_file" 2>/dev/null || {
        echo "[]" > "$all_metrics_file"
        log_warning "No metrics files found for aggregation"
    }
    
    # Generate summary statistics
    if command -v jq >/dev/null 2>&1; then
        jq '
        {
            "total_tests": length,
            "total_execution_time": map(.execution_time_seconds // 0) | add,
            "average_execution_time": (map(.execution_time_seconds // 0) | add) / length,
            "max_execution_time": map(.execution_time_seconds // 0) | max,
            "min_execution_time": map(.execution_time_seconds // 0) | min,
            "total_memory_usage": map(.memory_usage_kb // 0) | add,
            "average_memory_usage": (map(.memory_usage_kb // 0) | add) / length,
            "aggregation_timestamp": "'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'",
            "aggregation_version": "1.0"
        }
        ' "$all_metrics_file" > "$summary_file" 2>/dev/null || {
            echo '{"error": "Failed to generate summary statistics"}' > "$summary_file"
        }
    fi
    
    # Generate performance dashboard
    cat > "$dashboard_file" << EOF
# Performance Monitoring Dashboard

## Overview
- **Aggregation Date**: $(date -u +%Y-%m-%d\ %H:%M:%S\ UTC)
- **Total Tests**: $(jq -r '.total_tests // "unknown"' "$summary_file" 2>/dev/null)
- **Total Execution Time**: $(jq -r '.total_execution_time // "unknown"' "$summary_file" 2>/dev/null)s

## Performance Summary

### Execution Time Statistics
- **Average**: $(jq -r '.average_execution_time // "unknown"' "$summary_file" 2>/dev/null)s
- **Maximum**: $(jq -r '.max_execution_time // "unknown"' "$summary_file" 2>/dev/null)s
- **Minimum**: $(jq -r '.min_execution_time // "unknown"' "$summary_file" 2>/dev/null)s

### Memory Usage Statistics
- **Total**: $(jq -r '.total_memory_usage // "unknown"' "$summary_file" 2>/dev/null) KB
- **Average**: $(jq -r '.average_memory_usage // "unknown"' "$summary_file" 2>/dev/null) KB

## Detailed Results

| Test Name | Duration (s) | Memory (KB) | CPU (%) |
|-----------|--------------|-------------|---------|
EOF
    
    # Add detailed results table
    if [[ -f "$all_metrics_file" ]]; then
        jq -r '.[] | [.test_name // "unknown", .execution_time_seconds // 0, .memory_usage_kb // 0, .cpu_usage_percent // 0] | @csv' "$all_metrics_file" | \
        sed 's/"//g' | while IFS=',' read -r test_name duration memory cpu; do
            echo "| $test_name | $duration | $memory | $cpu |" >> "$dashboard_file"
        done 2>/dev/null || {
            echo "| No detailed results available | - | - | - |" >> "$dashboard_file"
        }
    fi
    
    log_success "✅ Performance metrics aggregated in: $output_directory"
    
    # Export aggregated metrics for workflow status
    if [[ -f "$summary_file" ]]; then
        export_performance_metrics "aggregated_performance" "$summary_file"
    fi
    
    return 0
}

# =============================================================================
# MAIN EXECUTION AND VALIDATION
# =============================================================================

# Validate performance utilities setup
validate_performance_setup() {
    log_info "🔧 Validating performance utilities setup..."
    
    local validation_errors=0
    
    # Check required commands
    local required_commands=("bc" "awk" "find" "mkdir" "cat")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            log_error "Required command not found: $cmd"
            ((validation_errors++))
        fi
    done
    
    # Check optional but recommended commands
    local optional_commands=("jq" "/usr/bin/time")
    for cmd in "${optional_commands[@]}"; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            log_warning "Optional command not found: $cmd (some features may be limited)"
        fi
    done
    
    # Check for required directories
    mkdir -p performance_results performance_baselines
    
    if [[ $validation_errors -eq 0 ]]; then
        log_success "✅ Performance utilities setup validation passed"
        return 0
    else
        log_error "❌ Performance utilities setup validation failed with $validation_errors errors"
        return 1
    fi
}

# Main execution if script is run directly
if [[ "${BASH_SOURCE[0]:-}" == "${0:-}" ]]; then
    echo "Performance Utilities Script for GitHub Actions"
    echo "==============================================="
    validate_performance_setup
fi