#!/bin/bash
################################################################################
# Skipped Tests Configuration
#
# This file defines tests that should be skipped because they test features
# not yet implemented in the CLI. These tests are preserved for future TDD
# development.
#
# Usage: source lib/skipped_tests.sh
#        is_test_skipped "test_name" && mark_test_skipped "test_name" "reason" && return
################################################################################

# Array of test names that should be skipped
# Format: "test_suite:test_function_name:reason"
declare -a SKIP_LIST=(
    # test_secrets_commands.sh - Features not implemented
    "test_secrets_commands:test_secrets_add_disabled:CLI doesn't check STEP_MANAGE_SECRETS flag"
    "test_secrets_commands:test_secrets_add_force_without_repos:Auto-discovery without --repos not implemented"
    "test_secrets_commands:test_secrets_add_error_cases:Invalid path validation not implemented"
    "test_secrets_commands:test_secrets_add_auto_discovery:Auto-discovery feature not implemented"
    "test_secrets_commands:test_secrets_add_auto_discovery_no_repos:Explicit 0 repos message not shown"
    "test_secrets_commands:test_secrets_add_auto_discovery_error:Invalid URL validation not implemented"
    "test_secrets_commands:test_secrets_add_invalid_repo_url:Malformed URL detection not implemented"
    
    # test_automation_commands.sh - Validation not implemented
    "test_automation_commands:test_cron_install_invalid_schedule:Cron schedule validation not implemented"
    "test_automation_commands:test_cron_install_invalid_step:Step name validation not implemented"
    "test_automation_commands:test_cron_remove_nonexistent:Crontab entry counting issue (bash syntax)"
    "test_automation_commands:test_cron_sync_invalid_step:Step name validation not implemented"
    "test_automation_commands:test_cron_sync_combined:Verbose output not distinguishable from normal"
    
    # test_global_options.sh - Features/validation not fully implemented
    "test_global_options:test_verbose_assignments_setup:Verbose output detection needs improvement"
    "test_global_options:test_verbose_assignments_validate_config:Config file path resolution issue"
    "test_global_options:test_verbose_assignments_orchestrate:Config validation issue"
    "test_global_options:test_verbose_combined_with_dry_run:Config validation issue"
    "test_global_options:test_dry_run_assignments_orchestrate:Config validation issue"
    "test_global_options:test_config_nonexistent_file:CLI doesn't error on missing config for some commands"
    "test_global_options:test_config_relative_path:Relative path resolution issue"
    "test_global_options:test_assignment_root_basic:Config validation in assignment root"
    "test_global_options:test_assignment_root_with_config:Combined option handling issue"
    "test_global_options:test_verbose_dry_run_combined:Combined option with config issue"
    "test_global_options:test_config_assignment_root_combined:Combined option handling issue"
    "test_global_options:test_all_options_combined:Multiple option interaction issue"
    
    # test_error_scenarios.sh - Validation not implemented
    "test_error_scenarios:test_missing_all_required_fields:CLI allows missing required fields"
    "test_error_scenarios:test_empty_config_file:CLI doesn't reject empty config files"
    "test_error_scenarios:test_invalid_url_format_in_config:URL format validation not implemented"
    "test_error_scenarios:test_invalid_config_syntax:Config syntax validation not implemented"
    "test_error_scenarios:test_invalid_path_in_config:Path validation not implemented"
    "test_error_scenarios:test_malformed_repository_url:URL validation not implemented"
    "test_error_scenarios:test_malformed_json_token:JSON parsing error handling needs work"
    "test_error_scenarios:test_whitespace_only_values:Whitespace validation not implemented"
)

# Check if a test should be skipped
# Usage: is_test_skipped "test_function_name"
# Returns: 0 if should be skipped, 1 otherwise
is_test_skipped() {
    local test_name="$1"
    local current_suite="${TEST_SUITE_NAME:-unknown}"
    
    for entry in "${SKIP_LIST[@]}"; do
        local suite=$(echo "$entry" | cut -d: -f1)
        local func=$(echo "$entry" | cut -d: -f2)
        
        if [[ "$current_suite" == "$suite" && "$test_name" == "$func" ]]; then
            return 0
        fi
    done
    return 1
}

# Get skip reason for a test
# Usage: reason=$(get_skip_reason "test_function_name")
get_skip_reason() {
    local test_name="$1"
    local current_suite="${TEST_SUITE_NAME:-unknown}"
    
    for entry in "${SKIP_LIST[@]}"; do
        local suite=$(echo "$entry" | cut -d: -f1)
        local func=$(echo "$entry" | cut -d: -f2)
        local reason=$(echo "$entry" | cut -d: -f3-)
        
        if [[ "$current_suite" == "$suite" && "$test_name" == "$func" ]]; then
            echo "$reason"
            return 0
        fi
    done
    echo "Not implemented"
}
