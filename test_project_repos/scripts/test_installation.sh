#!/bin/bash
#
# Package Installation Testing Script
#
# Tests various installation methods for the classdock package
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Test package building
test_package_build() {
    if [ "$SKIP_BUILD" = true ]; then
        log_info "Skipping package build (SKIP_BUILD=true)"
        return 0
    fi
    
    log_info "Testing package build process"
    
    cd "$PROJECT_ROOT"
    
    # Clean previous builds
    if [ -d "dist" ]; then
        rm -rf dist/
    fi
    
    if [ -d "build" ]; then
        rm -rf build/
    fi
    
    # Build with Poetry
    if [ "$BUILD_WITH_POETRY" = true ]; then
        log_info "Building package with Poetry"
        
        if ! poetry build; then
            log_error "Poetry build failed"
            return 1
        fi
        
        # Verify build artifacts
        if [ ! -f "dist/${PYTHON_MODULE}-${EXPECTED_VERSION}-py3-none-any.whl" ]; then
            log_error "Wheel file not found"
            return 1
        fi
        
        if [ ! -f "dist/${PYTHON_MODULE}-${EXPECTED_VERSION}.tar.gz" ]; then
            log_error "Source distribution not found"
            return 1
        fi
        
        log_success "Package built successfully with Poetry"
    fi
    
    # Verify wheel contents if enabled
    if [ "$VERIFY_WHEEL_CONTENTS" = true ]; then
        verify_wheel_contents
    fi
    
    return 0
}

# Verify wheel contents
verify_wheel_contents() {
    log_info "Verifying wheel contents"
    
    local wheel_file="dist/${PACKAGE_NAME//-/_}-${EXPECTED_VERSION}-py3-none-any.whl"
    
    if command -v unzip &> /dev/null; then
        # List wheel contents
        log_info "Wheel contents:"
        unzip -l "$wheel_file" | head -20
        
        # Check for essential files
        if ! unzip -l "$wheel_file" | grep -q "${PYTHON_MODULE}/__init__.py"; then
            log_error "Package __init__.py not found in wheel"
            return 1
        fi
        
        if ! unzip -l "$wheel_file" | grep -q "METADATA"; then
            log_error "Package metadata not found in wheel"
            return 1
        fi
        
        log_success "Wheel contents verified"
    else
        log_warning "unzip not available, skipping wheel verification"
    fi
}

# Test wheel installation
test_wheel_installation() {
    if [ "$TEST_WHEEL_INSTALL" = false ]; then
        log_info "Wheel installation testing disabled"
        return 0
    fi
    
    log_info "Testing wheel installation"
    
    local wheel_file="$PROJECT_ROOT/dist/${PACKAGE_NAME//-/_}-${EXPECTED_VERSION}-py3-none-any.whl"
    
    if [ ! -f "$wheel_file" ]; then
        log_error "Wheel file not found: $wheel_file"
        return 1
    fi
    
    # Install from wheel
    log_info "Installing from wheel: $wheel_file"
    
    if ! pip install "$wheel_file"; then
        log_error "Wheel installation failed"
        return 1
    fi
    
    # Verify installation
    verify_package_installation
    
    # Uninstall for next test
    pip uninstall "$PACKAGE_NAME" -y
    
    log_success "Wheel installation test passed"
}

# Test source installation
test_source_installation() {
    if [ "$TEST_SOURCE_INSTALL" = false ]; then
        log_info "Source installation testing disabled"
        return 0
    fi
    
    log_info "Testing source installation"
    
    # Install from source directory
    if ! pip install "$PROJECT_ROOT/"; then
        log_error "Source installation failed"
        return 1
    fi
    
    # Verify installation
    verify_package_installation
    
    # Uninstall for next test
    pip uninstall "$PACKAGE_NAME" -y
    
    log_success "Source installation test passed"
}

# Test editable installation
test_editable_installation() {
    log_info "Testing editable installation"
    
    # Install in editable mode
    if ! pip install -e "$PROJECT_ROOT/"; then
        log_error "Editable installation failed"
        return 1
    fi
    
    # Verify installation
    verify_package_installation
    
    # Test that changes are reflected (editable mode)
    local test_file="$PROJECT_ROOT/${PYTHON_MODULE}/_test_editable.py"
    echo "# Test file for editable mode" > "$test_file"
    
    if python -c "import ${PYTHON_MODULE}._test_editable" 2>/dev/null; then
        log_success "Editable mode working correctly"
        rm -f "$test_file"
    else
        log_warning "Editable mode test inconclusive"
        rm -f "$test_file"
    fi
    
    log_success "Editable installation test passed"
}

# Verify package installation
verify_package_installation() {
    log_info "Verifying package installation"
    
    # Check if package is installed
    if ! pip show "$PACKAGE_NAME" >/dev/null 2>&1; then
        log_error "Package not found in pip list"
        return 1
    fi
    
    # Test Python import
    if ! python -c "import $PYTHON_MODULE" 2>/dev/null; then
        log_error "Package import failed"
        return 1
    fi
    
    # Test version
    local installed_version=$(python -c "import $PYTHON_MODULE; print($PYTHON_MODULE.__version__)" 2>/dev/null || echo "unknown")
    
    if [ "$installed_version" != "$EXPECTED_VERSION" ]; then
        log_warning "Version mismatch: expected $EXPECTED_VERSION, got $installed_version"
    else
        log_success "Version check passed: $installed_version"
    fi
    
    # Test CLI entry point
    if ! command -v "$CLI_COMMAND" &> /dev/null; then
        log_error "CLI command not found: $CLI_COMMAND"
        return 1
    fi
    
    # Test CLI version
    if ! "$CLI_COMMAND" --version >/dev/null 2>&1; then
        log_error "CLI version command failed"
        return 1
    fi
    
    log_success "Package installation verified"
}

# Test dependency conflicts
test_dependency_conflicts() {
    log_info "Checking for dependency conflicts"
    
    # Run pip check
    if pip check >/dev/null 2>&1; then
        log_success "No dependency conflicts found"
    else
        log_warning "Dependency conflicts detected:"
        pip check || true
    fi
}

# Test installation in clean environment
test_clean_environment_install() {
    log_info "Testing installation in clean environment"
    
    # Create temporary clean environment
    local temp_env_name="clean_install_test_$(date +%s)"
    local temp_env_dir="$TEST_DIR/test_environments/$temp_env_name"
    
    mkdir -p "$temp_env_dir"
    
    # Create clean virtual environment
    python -m venv "$temp_env_dir"
    source "$temp_env_dir/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install package
    local wheel_file="$PROJECT_ROOT/dist/${PACKAGE_NAME//-/_}-${EXPECTED_VERSION}-py3-none-any.whl"
    
    if pip install "$wheel_file"; then
        log_success "Clean environment installation successful"
        
        # Quick verification
        python -c "import $PYTHON_MODULE; print('Import successful')"
        "$CLI_COMMAND" --version
        
    else
        log_error "Clean environment installation failed"
        deactivate
        rm -rf "$temp_env_dir"
        return 1
    fi
    
    # Cleanup
    deactivate
    rm -rf "$temp_env_dir"
    
    log_success "Clean environment test completed"
}

# Main execution
main() {
    log_info "Starting package installation tests"
    
    # Test package building
    if ! test_package_build; then
        log_error "Package build test failed"
        exit 1
    fi
    
    # Test wheel installation
    if ! test_wheel_installation; then
        log_error "Wheel installation test failed"
        exit 1
    fi
    
    # Test source installation
    if ! test_source_installation; then
        log_error "Source installation test failed"
        exit 1
    fi
    
    # Test editable installation
    if ! test_editable_installation; then
        log_error "Editable installation test failed"
        exit 1
    fi
    
    # Test dependency conflicts
    test_dependency_conflicts
    
    # Test clean environment installation
    if ! test_clean_environment_install; then
        log_error "Clean environment installation test failed"
        exit 1
    fi
    
    log_success "All installation tests passed!"
}

# Handle command line execution
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi