#!/usr/bin/env bash
# Repository health check script
# Performs comprehensive repository configuration and file checks

set -euo pipefail

source "$(dirname "$0")/workflow_utils.sh"

print_message "step" "Running repository health check"

# Check for required files
print_message "info" "Checking file structure..."
required_files=(
  "README.md"
  "LICENSE" 
  "pyproject.toml"
  "classdock/scripts_legacy/setup-assignment.sh"
  "classdock/scripts_legacy/assignment-orchestrator.sh"
  "classdock/scripts_legacy/fetch-student-repos.sh"
  "docs/CHANGELOG.md"
)

missing_files=()
for file in "${required_files[@]}"; do
  if [ -f "$file" ]; then
    print_message "success" "✅ $file exists"
  else
    print_message "warning" "❌ $file missing"
    missing_files+=("$file")
  fi
done

# Check for basic project structure
print_message "info" "Checking directory structure..."
required_dirs=(".github" "tests" "docs" "classdock/scripts_legacy")
missing_dirs=()

for dir in "${required_dirs[@]}"; do
    if [[ -d "$dir" ]]; then
        print_message "success" "✅ $dir directory exists"
    else
        print_message "warning" "❌ $dir directory missing"
        missing_dirs+=("$dir")
    fi
done

# Repository statistics
print_message "info" "Repository statistics:"
script_total=$(find classdock/scripts_legacy/ -name "*.sh" 2>/dev/null | wc -l || echo "0")
docs_total=$(find docs/ -name "*.md" 2>/dev/null | wc -l || echo "0")
workflow_total=$(find .github/workflows/ -name "*.yml" 2>/dev/null | wc -l || echo "0")

print_message "info" "- Scripts: ${script_total}"
print_message "info" "- Documentation files: ${docs_total}"
print_message "info" "- Workflow files: ${workflow_total}"

# Overall health assessment
if [[ ${#missing_files[@]} -eq 0 && ${#missing_dirs[@]} -eq 0 ]]; then
    print_message "success" "Repository health check passed - all requirements met"
    exit 0
else
    print_message "warning" "Repository health check completed with warnings"
    exit 1
fi
