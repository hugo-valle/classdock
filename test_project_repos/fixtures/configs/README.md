# Configuration Fixtures for Testing

This directory contains test configuration files that cover various scenarios for validating `classdock` configuration parsing, validation, and error handling.

## 📁 Fixture Files

### ✅ Valid Configurations

#### `valid_minimal.conf`
**Purpose:** Minimal valid configuration with only required fields.

**Use Cases:**
- Test default value handling
- Verify minimal requirements are sufficient
- Baseline for configuration validation

**Fields:**
- `GITHUB_ORGANIZATION` (required)
- `ASSIGNMENT_NAME` (required)
- `STUDENTS_FILE` (required)

---

#### `valid_comprehensive.conf`
**Purpose:** Complete configuration with all supported fields populated.

**Use Cases:**
- Test full feature coverage
- Verify all fields are parsed correctly
- Reference for complete configuration options
- Integration testing with maximum settings

**Fields:** All 40+ supported configuration parameters including:
- Organization and assignment settings
- File paths (students, repos, output, logs)
- GitHub URLs
- Secrets management
- Repository settings
- Collaboration configuration
- Automation parameters
- Grading and feedback options

---

### ❌ Invalid Configurations

#### `invalid_missing_required.conf`
**Purpose:** Configuration missing required fields.

**Use Cases:**
- Test validation error detection
- Verify helpful error messages for missing fields
- Test fail-fast behavior

**Missing Fields:**
- `GITHUB_ORGANIZATION`
- `ASSIGNMENT_NAME`
- `STUDENTS_FILE`

**Expected Behavior:** Should fail validation with clear error indicating which required fields are missing.

---

#### `invalid_malformed_urls.conf`
**Purpose:** Configuration with incorrectly formatted URLs.

**Use Cases:**
- Test URL validation logic
- Verify protocol requirements (https://)
- Test domain format validation

**Expected Behavior:** Should fail with URL validation errors, indicating which fields contain invalid URLs.

---

#### `invalid_wrong_types.conf`
**Purpose:** Configuration with wrong data types for fields.

**Use Cases:**
- Test type checking and coercion
- Verify boolean/numeric validation
- Test enum-like field validation

**Invalid Values:**
- Boolean fields with string values: `DRY_RUN=maybe`, `VERBOSE=yes`
- Numeric fields with text: `PARALLEL_LIMIT=many`, `TIMEOUT=forever`
- Invalid enum values: `COLLABORATOR_PERMISSION=superuser`

**Expected Behavior:** Should fail with type validation errors or attempt safe coercion with warnings.

---

### ⚠️ Edge Case Configurations

#### `edge_case_empty_values.conf`
**Purpose:** Configuration with empty strings and whitespace-only values.

**Use Cases:**
- Test empty string handling
- Verify default value substitution
- Test whitespace trimming

**Test Cases:**
- Empty strings: `ASSIGNMENT_DESCRIPTION=`
- Whitespace-only: `COLLABORATOR_USERNAME=   `
- Empty lists: `SECRETS_LIST=`

**Expected Behavior:**
- Empty optional fields → Use defaults
- Empty required fields → Validation error
- Whitespace → Trimmed or rejected

---

#### `edge_case_special_characters.conf`
**Purpose:** Configuration with special characters, Unicode, and escape sequences.

**Use Cases:**
- Test character encoding handling
- Verify shell escape prevention
- Test Unicode/emoji support

**Test Cases:**
- Quotes and symbols: `ASSIGNMENT_DESCRIPTION="Assignment with 'quotes' @#$%"`
- Paths with spaces: `OUTPUT_DIR="./output with spaces"`
- Unicode/emoji: `COLLABORATOR_USERNAME=user-🎓`
- URL parameters: `TEMPLATE_REPO="https://github.com/org/repo?ref=main&depth=1"`

**Expected Behavior:**
- Proper escaping for shell commands
- Unicode preserved in strings
- Special characters in paths handled correctly

---

#### `edge_case_very_long_values.conf`
**Purpose:** Configuration with unusually long field values.

**Use Cases:**
- Test buffer limit handling
- Verify truncation behavior
- Stress test parsing logic

**Test Cases:**
- 300+ character description
- Very long nested paths
- 100+ item comma-separated lists
- 4KB+ secret values
- Boundary values (GitHub username 39 char limit)

**Expected Behavior:**
- Graceful handling of long values
- Truncation with warnings if needed
- No buffer overflows or crashes

---

## 🧪 Usage in Tests

### Basic Test Pattern

```bash
#!/bin/bash
source lib/test_helpers.sh

# Test valid minimal configuration
run_test_case "Valid minimal config loads successfully" \
    classdock assignments setup --config fixtures/configs/valid_minimal.conf --dry-run

# Test invalid configuration detection
run_test_case "Missing required fields detected" \
    "! classdock assignments setup --config fixtures/configs/invalid_missing_required.conf --dry-run"
```

### Validation Testing

```bash
# Test all invalid configurations should fail
for config in fixtures/configs/invalid_*.conf; do
    config_name=$(basename "$config" .conf)
    run_test_case "Invalid config rejected: $config_name" \
        "! classdock assignments setup --config $config --dry-run"
done

# Test all valid configurations should succeed
for config in fixtures/configs/valid_*.conf; do
    config_name=$(basename "$config" .conf)
    run_test_case "Valid config accepted: $config_name" \
        classdock assignments setup --config $config --dry-run
done
```

### Edge Case Testing

```bash
# Test edge cases with specific assertions
setup_test_config fixtures/configs/edge_case_empty_values.conf

result=$(classdock assignments setup --config $TEST_CONFIG_PATH --dry-run 2>&1)

assert_output_contains "$result" "Using default value"
assert_exit_code 0
```

---

## 📝 Adding New Fixtures

When adding new test configurations:

1. **Name clearly:** Use prefix `valid_`, `invalid_`, or `edge_case_`
2. **Document purpose:** Add comments explaining test scenario
3. **Update this README:** Add entry with use cases and expected behavior
4. **Test thoroughly:** Verify fixture behaves as expected
5. **Consider combinations:** Think about interactions between fields

### Template for New Fixture

```bash
# [Category] Configuration - [Specific Test Scenario]
# Description of what this fixture tests

# Required fields (if valid)
ORGANIZATION=test-org
ASSIGNMENT_NAME=test-assignment
STUDENTS_FILE=students.txt

# Test-specific fields
[FIELD_NAME]=[TEST_VALUE]

# Expected behavior: [describe what should happen]
```

---

## 🔍 Validation Rules Reference

### Required Fields
- `GITHUB_ORGANIZATION`: GitHub organization name
- `ASSIGNMENT_NAME`: Assignment identifier
- `STUDENTS_FILE`: Path to student list file

### Validation Checks
1. **Required field presence**
2. **Type compatibility**
3. **URL format** (must start with `https://`)
4. **File existence** (for input files)
5. **Directory writability** (for output directories)
6. **Value ranges** (e.g., `PARALLEL_LIMIT > 0`)

---

## 🎯 Testing Strategy

### Coverage Goals
- ✅ All required fields validated
- ✅ All optional fields tested
- ✅ All error conditions covered
- ✅ Edge cases and boundary values tested
- ✅ Type coercion and validation verified

### Test Execution
```bash
# Run all configuration validation tests
cd test_project_repos
./scripts/run_full_test.sh --qa --filter config

# Run specific configuration test
./qa_tests/test_config_validation.sh fixtures/configs/valid_comprehensive.conf
```

---

## 📊 Fixture Coverage Matrix

| Fixture | Required Fields | Optional Fields | Invalid Data | Edge Cases | Purpose |
|---------|----------------|-----------------|--------------|------------|---------|
| `valid_minimal.conf` | ✅ | ❌ | ❌ | ❌ | Baseline |
| `valid_comprehensive.conf` | ✅ | ✅ | ❌ | ❌ | Full coverage |
| `invalid_missing_required.conf` | ❌ | ✅ | ❌ | ❌ | Required validation |
| `invalid_malformed_urls.conf` | ✅ | ❌ | ✅ | ❌ | URL validation |
| `invalid_wrong_types.conf` | ✅ | ❌ | ✅ | ❌ | Type validation |
| `edge_case_empty_values.conf` | ✅ | ✅ | ❌ | ✅ | Empty handling |
| `edge_case_special_characters.conf` | ✅ | ✅ | ❌ | ✅ | Character encoding |
| `edge_case_very_long_values.conf` | ✅ | ✅ | ❌ | ✅ | Buffer limits |

---

*These fixtures are essential for comprehensive QA testing of configuration parsing and validation in classdock.*
