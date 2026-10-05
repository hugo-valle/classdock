# Test Fixes Required for Centralized Token Migration

## Overview
The centralized token migration changes broke 17 existing tests. This document outlines the required fixes.

## Root Causes

### 1. Assignment Setup Return Behavior Changed
**Issue**: `run_wizard()` now returns `bool` instead of calling `sys.exit()`
**Impact**: Tests expecting `SystemExit` now fail
**Fix**: Update tests to check return values instead of `pytest.raises(SystemExit)`

### 2. Token Configuration Removed
**Issue**: `_configure_tokens()` no longer prompts for token values or stores them
**Impact**: Tests expecting `INSTRUCTOR_TESTS_TOKEN_VALUE` in config fail
**Fix**: Remove assertions checking for token values in config

### 3. Token File Creation Removed
**Issue**: `_create_files()` no longer calls `create_token_files()`
**Impact**: Tests expecting `create_token_files()` to be called fail
**Fix**: Remove assertions checking for `create_token_files()` calls

### 4. Mock Objects Not Handled
**Issue**: `GitHubAPIClient.is_likely_classroom_name()` expects string but receives Mock
**Impact**: TypeError when Mock objects are passed to `re.match()`
**Fix**: Ensure mocks return proper string values or mock the new method

### 5. Config Field Changed
**Issue**: `ASSIGNMENT_FILE` changed to `STUDENT_FILES`
**Impact**: Config validation fails expecting old field name
**Fix**: Update test config files to use `STUDENT_FILES`

## Detailed Fixes

###

 Test File: `tests/test_setup_wizard.py` (15 failures)

#### Fix 1: Mock `url_parser.parse_classroom_url` properly
**Location**: All tests using `url_parser.extract_org_from_url`
**Change**: Mock to return dict with string 'organization' key

```python
# OLD
setup.url_parser.extract_org_from_url.return_value = "test-org"

# NEW
setup.url_parser.parse_classroom_url.return_value = {
    'organization': 'test-org',
    'assignment_name': 'test-assignment'
}
```

#### Fix 2: Remove token value expectations
**Location**: `test_configure_tokens_*` tests
**Change**: Don't check for `INSTRUCTOR_TESTS_TOKEN_VALUE`

```python
# REMOVE THESE ASSERTIONS
assert 'INSTRUCTOR_TESTS_TOKEN_VALUE' in setup.config_values
```

#### Fix 3: Remove create_token_files expectations
**Location**: `test_create_files_with_secrets_enabled`
**Change**: Don't check for `create_token_files()` call

```python
# REMOVE THIS
setup.file_manager.create_token_files.assert_called_once_with(...)
```

#### Fix 4: Update SystemExit expectations
**Location**: `test_run_wizard_keyboard_interrupt`, `test_run_wizard_unexpected_exception`
**Change**: Check return value instead of SystemExit

```python
# OLD
with pytest.raises(SystemExit):
    setup.run_wizard()

# NEW
result = setup.run_wizard()
assert result is False  # or True depending on scenario
```

### Test File: `tests/test_cli.py` (2 failures)

#### Fix 1: Update config files to use STUDENT_FILES
**Location**: `test_assignment_root_success`, `test_assignment_root_integration_with_config_option`
**Change**: Replace `ASSIGNMENT_FILE` with `STUDENT_FILES` in test config

```python
# In config file creation
STUDENT_FILES="assignment.ipynb"  # Instead of ASSIGNMENT_FILE
```

## Implementation Strategy

1. **Phase 1**: Fix setup.py mocking issues (Mock string returns)
2. **Phase 2**: Remove token-related assertions
3. **Phase 3**: Update SystemExit expectations to return values
4. **Phase 4**: Fix config file field names

## Testing After Fixes

Run specific test files to verify fixes:
```bash
poetry run pytest tests/test_setup_wizard.py -v
poetry run pytest tests/test_cli.py -v
```

## Expected Outcome

All 17 tests should pass after fixes are applied.
