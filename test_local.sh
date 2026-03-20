#!/usr/bin/env bash
# Local test runner for ClassDock.
# Runs BOTH testing suites locally before pushing to CI.
#
# Tier 1: Python pytest suite (tests/) — Unit & integration tests
# Tier 2: Bash QA suite (test_project_repos/qa_tests/) — End-to-end tests

set -euo pipefail

# Test execution flags
RUN_TIER1=false
RUN_TIER2=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status()  { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

command_exists() { command -v "$1" >/dev/null 2>&1; }

show_help() {
    cat << EOF
🧪 ClassDock — Local Test Runner

USAGE:
    ./test_local.sh [OPTIONS]

OPTIONS:
    -h, --help      Show this help message
    -1, --tier1     Run only Tier 1 (Python pytest suite)
    -2, --tier2     Run only Tier 2 (Bash QA suite)
    -a, --all       Run both tiers (default if no options specified)

TESTING TIERS:
    Tier 1: Python pytest Suite
        • Location: tests/
        • Type: Unit tests, integration tests
        • Framework: pytest with coverage
        • Speed: Fast (seconds to minutes)
        • Purpose: Development feedback, code validation

    Tier 2: Bash QA Suite
        • Location: test_project_repos/qa_tests/
        • Type: End-to-end tests, real workflow validation
        • Framework: Bash scripts
        • Speed: Slower (minutes)
        • Purpose: Release qualification, user acceptance testing

EXAMPLES:
    ./test_local.sh --all       # comprehensive testing
    ./test_local.sh --tier1     # fast feedback during development
    ./test_local.sh --tier2     # workflow validation before release

EOF
    exit 0
}

parse_arguments() {
    if [[ $# -eq 0 ]]; then
        RUN_TIER1=true
        RUN_TIER2=true
        return
    fi

    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)  show_help ;;
            -1|--tier1) RUN_TIER1=true; shift ;;
            -2|--tier2) RUN_TIER2=true; shift ;;
            -a|--all)   RUN_TIER1=true; RUN_TIER2=true; shift ;;
            *)
                print_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done

    # Default to both tiers if neither was selected
    if [[ "$RUN_TIER1" == false ]] && [[ "$RUN_TIER2" == false ]]; then
        RUN_TIER1=true
        RUN_TIER2=true
    fi
}

main() {
    parse_arguments "$@"

    echo "🧪 ClassDock — Comprehensive Local Test Runner"
    echo "================================================"

    if [[ "$RUN_TIER1" == true ]] && [[ "$RUN_TIER2" == true ]]; then
        echo "Testing Strategy: Two-Tier Approach (Both Tiers)"
    elif [[ "$RUN_TIER1" == true ]]; then
        echo "Testing Strategy: Tier 1 Only (Python pytest)"
    else
        echo "Testing Strategy: Tier 2 Only (Bash QA)"
    fi
    echo ""

    # ── Prerequisites ──────────────────────────────────────────────────
    print_status "Checking prerequisites..."

    if ! command_exists python; then
        print_error "Python is not installed or not in PATH"
        exit 1
    fi

    if ! command_exists poetry; then
        print_error "Poetry is not installed or not in PATH"
        print_status "Install Poetry: https://python-poetry.org/docs/#installation"
        exit 1
    fi

    print_status "Using $(python --version 2>&1)"
    print_status "Using $(poetry --version 2>&1)"

    if [[ ! -f "pyproject.toml" ]] || [[ ! -d "classdock" ]]; then
        print_error "Please run this script from the classdock root directory"
        exit 1
    fi

    # ── Install dependencies ───────────────────────────────────────────
    print_status "Installing dependencies with Poetry..."
    if poetry install --no-interaction; then
        print_success "Dependencies installed"
    else
        print_error "Failed to install dependencies with Poetry"
        exit 1
    fi

    # ── Smoke tests ────────────────────────────────────────────────────
    print_status "Running smoke tests..."

    if poetry run python -c "import classdock.cli; print('Import successful')" >/dev/null 2>&1; then
        print_success "Package imports correctly"
    else
        print_error "Package import failed"
        exit 1
    fi

    if poetry run classdock --help >/dev/null 2>&1; then
        print_success "CLI entry point works"
    else
        print_warning "CLI entry point test failed"
    fi

    # ── Tier 1: pytest ─────────────────────────────────────────────────
    if [[ "$RUN_TIER1" == true ]]; then
        echo ""
        echo "📊 TIER 1: Python pytest Suite (Unit & Integration Tests)"
        echo "==========================================================="

        if poetry run pytest tests/ -v --tb=short --cov=classdock --cov-report=term --cov-report=html; then
            print_success "🎉 Tier 1 tests passed!"

            print_status "Total tests: $(poetry run pytest tests/ --collect-only -q 2>/dev/null | tail -1 | grep -o '[0-9]* item' | grep -o '[0-9]*' || echo 'multiple')"

            # Optional flake8 check
            if poetry run python -c "import flake8" 2>/dev/null; then
                print_status "Running flake8 syntax check..."
                if poetry run flake8 classdock/ --count --select=E9,F63,F7,F82 --show-source --statistics; then
                    print_success "Syntax checks passed"
                else
                    print_warning "Some syntax issues found"
                fi
            fi

            if [[ -f "htmlcov/index.html" ]]; then
                print_success "Coverage report: htmlcov/index.html"
            fi
        else
            print_error "❌ Tier 1 tests failed. Check the output above."
            print_status "Common fixes:"
            print_status "  • Run 'poetry install' to refresh dependencies"
            print_status "  • Check import errors in the failing tests"
        fi
    fi

    # ── Tier 2: Bash QA ────────────────────────────────────────────────
    if [[ "$RUN_TIER2" == true ]]; then
        echo ""
        echo "🔧 TIER 2: Bash QA Suite (End-to-End Tests)"
        echo "==========================================================="

        if [[ ! -d "test_project_repos/qa_tests" ]]; then
            print_warning "QA test directory not found (test_project_repos/qa_tests/). Skipping Tier 2."
        else
            set +e

            qa_test_scripts=(
                "test_project_repos/qa_tests/test_assignments_commands.sh"
                "test_project_repos/qa_tests/test_automation_commands.sh"
                "test_project_repos/qa_tests/test_repos_commands.sh"
                "test_project_repos/qa_tests/test_secrets_commands.sh"
                "test_project_repos/qa_tests/test_token_management.sh"
            )

            qa_passed=0
            qa_failed=0
            qa_skipped=0

            for test_script in "${qa_test_scripts[@]}"; do
                if [[ ! -f "$test_script" ]]; then
                    print_warning "Not found: $test_script (skipping)"
                    ((qa_skipped++))
                    continue
                fi

                script_name=$(basename "$test_script")
                print_status "Running $script_name..."
                chmod +x "$test_script"

                test_output=$(mktemp)
                if bash "$test_script" --all > "$test_output" 2>&1; then
                    print_success "✓ $script_name passed"
                    ((qa_passed++))
                else
                    print_error "✗ $script_name failed (exit: $?)"
                    echo "    Last 10 lines:"
                    tail -10 "$test_output" | sed 's/^/    /'
                    ((qa_failed++))
                fi
                rm -f "$test_output"
            done

            echo ""
            echo "QA Results:  Passed: $qa_passed  Failed: $qa_failed  Skipped: $qa_skipped"

            if [[ $qa_failed -gt 0 ]]; then
                print_error "Some QA tests failed. Run scripts individually for details."
            else
                print_success "🎉 All QA tests passed!"
            fi

            set -e
        fi
    fi

    # ── Summary ────────────────────────────────────────────────────────
    echo ""
    print_success "🎉 Testing complete!"
    echo "================================================"
    print_status "  • Poetry environment:    ✅ Working"
    print_status "  • Package installation:  ✅ Functional"
    print_status "  • Core imports:          ✅ Operational"
    print_status "  • CLI entry point:       ✅ Available"
    [[ "$RUN_TIER1" == true ]] && print_status "  • Tier 1 (pytest):       ✅ Executed"
    [[ "$RUN_TIER2" == true ]] && print_status "  • Tier 2 (QA bash):      ✅ Executed"
    [[ -f "htmlcov/index.html" ]] && print_status "  • Coverage report:       ✅ htmlcov/index.html"
}

cleanup() {
    # Remove auto-generated test assignment.conf if we created it
    if [[ -f "assignment.conf" ]] && grep -q "Test configuration for local development" assignment.conf 2>/dev/null; then
        rm -f assignment.conf
        print_status "Removed temporary assignment.conf"
    fi
}

trap cleanup EXIT

main "$@"
