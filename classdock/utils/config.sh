#!/bin/bash
# Utility functions for reading assignment.conf configuration

# Function to get a config value from assignment.conf
get_config_value() {
    local key="$1"
    local conf_file="${2:-$(dirname "$0")/../../assignment.conf}"
    grep -E "^${key}=" "$conf_file" | sed -E "s/^${key}=[\"']?([^\"']*)[\"']?$/\1/" | tail -n 1
}

# Example usage:
# org=$(get_config_value GITHUB_ORGANIZATION)
# echo "Organization: $org"
