# Assignments Fixtures for QA Testing

## Purpose

This directory contains test fixtures for comprehensive QA testing of the classdock assignments commands. These fixtures enable testing of various scenarios including valid configurations, batch operations, error handling, and edge cases without requiring actual GitHub resources or API access.

## Fixture Categories

### Configuration Files

#### Valid Configurations

**`with_secrets.conf`**
- **Type**: Configuration with secrets management enabled
- **Special Fields**: SECRETS_LIST, USE_SECRETS=true
- **Use Case**: Testing orchestrate --step secrets and secrets management
- **Purpose**: Validates secrets synchronization and management

#### Invalid Configurations

**`invalid_no_template_url.conf`**
- **Type**: Missing TEMPLATE_REPO_URL (required field)
- **Purpose**: Test validation error detection for missing template URL
- **Expected**: Validation should fail with clear error message

### Student and Repository Lists

**`student_repos.txt`**
- **Type**: List of student repository URLs
- **Format**: One URL per line
- **Count**: 8 repository URLs
- **Use Case**: Testing batch operations (help-students, cycle-collaborators --repo-urls)
- **Pattern**: https://github.com/test-org/test-assignment-studentN

**`usernames.txt`**
- **Type**: List of student usernames
- **Format**: One username per line
- **Count**: 8 usernames
- **Use Case**: Testing cycle-collaborators in username mode (default)
- **Pattern**: studentN

**`empty_repos.txt`**
- **Type**: Empty file
- **Purpose**: Test error handling with empty input files
- **Expected**: Commands should handle gracefully with appropriate warning/error

**`invalid_repos.txt`**
- **Type**: File containing invalid repository URLs
- **Contents**: Various invalid URL formats
- **Use Case**: Testing URL validation and error messages
- **Includes**: Malformed protocols, incomplete URLs, non-URLs, invalid formats

## Usage Examples

### Using Configuration Files in Tests

```bash
# Test with valid comprehensive configuration
classdock assignments validate-config --config-file fixtures/assignments/valid_assignment.conf

# Test with minimal configuration
classdock assignments orchestrate --config fixtures/assignments/minimal_assignment.conf

# Test with secrets configuration
classdock assignments orchestrate --step secrets --config fixtures/assignments/with_secrets.conf
```

### Using Repository Lists in Tests

```bash
# Test batch help with repository URLs
classdock assignments help-students fixtures/assignments/student_repos.txt --yes

# Test cycle collaborators with usernames
classdock assignments cycle-collaborators fixtures/assignments/usernames.txt

# Test cycle collaborators with repository URLs
classdock assignments cycle-collaborators fixtures/assignments/student_repos.txt --repo-urls
```

### Testing Error Scenarios

# Test batch operation with empty file
classdock assignments help-students fixtures/assignments/empty_repos.txt
# Expected: Error or warning about empty file

# Test batch operation with invalid URLs
classdock assignments help-students fixtures/assignments/invalid_repos.txt --yes
# Expected: Errors for each invalid URL with clear messages
```

### Loading Fixtures in Test Scripts

```bash
#!/bin/bash
# In test_assignments_commands.sh

# Load valid configuration
CONFIG_FILE="$FIXTURES_DIR/assignments/valid_assignment.conf"
source "$CONFIG_FILE"

# Use in tests
test_orchestrate_full() {
    classdock assignments orchestrate --config "$CONFIG_FILE" --yes
    assert_exit_code 0
}

# Load repository list
REPOS_FILE="$FIXTURES_DIR/assignments/student_repos.txt"
test_help_students_batch() {
    classdock assignments help-students "$REPOS_FILE" --yes
    assert_output_contains "processed"
}
```

## Configuration Field Reference

### Required Fields

All assignment configurations must include these fields:

- **TEMPLATE_REPO_URL** - Source template repository URL
  - Format: `https://github.com/{org}/{repo}`
  - Example: `https://github.com/test-org/test-assignment-template`

- **GITHUB_ORGANIZATION** - GitHub organization name
  - Format: Alphanumeric with hyphens
  - Example: `test-org`

- **ASSIGNMENT_NAME** - Assignment identifier/name
  - Format: Alphanumeric with hyphens/underscores
  - Example: `test-assignment`

- **ASSIGNMENT_FILE** - Main assignment file students work on
  - Format: Filename with extension
  - Example: `assignment.ipynb` or `assignment.py`

### Optional Fields

These fields enhance functionality but are not required:

- **SECRETS_LIST** - Comma-separated list of GitHub Actions secrets
  - Purpose: Secrets to synchronize across student repositories
  - Example: `API_KEY,DATABASE_URL,SECRET_TOKEN`

- **USE_SECRETS** - Enable secrets management
  - Purpose: Flag to enable/disable secrets operations
  - Values: `true` or `false`
  - Default: `false`

- **STUDENT_FILES** - Files/directories to preserve during updates
  - Purpose: Protect student work from being overwritten
  - Format: Comma-separated list of paths
  - Example: `assignment.ipynb,student_work/,data/`

- **COLLABORATOR_USERS** - Usernames with collaborator access
  - Purpose: Teaching assistants and instructors
  - Format: Comma-separated list of usernames
  - Example: `ta1,ta2,instructor`

## File Format Specifications

### Configuration Files (.conf)

**Format**: KEY=VALUE pairs, one per line

```bash
# Comments start with hash
KEY=value
ANOTHER_KEY=value with spaces

# Blank lines are ignored

LIST_KEY=value1,value2,value3  # Comma-separated lists
```

**Rules**:
- No spaces around `=` sign
- Values can contain spaces (no quoting needed)
- Comments start with `#`
- Blank lines are ignored
- Keys are case-sensitive (use UPPERCASE by convention)

### Repository Lists (.txt files for repos)

**Format**: One URL per line

```
https://github.com/org/repo1
https://github.com/org/repo2
https://github.com/org/repo3
```

**Rules**:
- One full URL per line
- Comments start with `#`
- Blank lines are skipped
- No trailing slashes

### Username Lists (.txt files for usernames)

**Format**: One username per line

```
student1
student2
student3
```

**Rules**:
- One username per line
- No special characters (alphanumeric, hyphens, underscores)
- Comments start with `#`
- Blank lines are skipped
- Case-sensitive

## Adding New Fixtures

When creating additional test fixtures, follow these guidelines:

### Naming Conventions

- **Valid configurations**: `valid_*.conf` or descriptive name like `with_secrets.conf`
- **Invalid configurations**: `invalid_*.conf` with clear description of what's invalid
- **List files**: Descriptive names like `student_repos.txt`, `usernames.txt`
- **Special purpose**: Clear names indicating purpose (e.g., `empty_repos.txt`)

### Documentation Requirements

1. **Add comment header** to each fixture explaining:
   - Purpose of the fixture
   - What scenario it tests
   - Any special characteristics
   - Expected behavior when used

2. **Update this README** when adding fixtures:
   - Add to appropriate category section
   - Describe the fixture's purpose
   - Provide usage example
   - Note any special considerations

3. **Include inline comments** in configuration files:
   - Explain each field's purpose
   - Note if field is required or optional
   - Provide format examples

### Validation Checklist

Before committing new fixtures:

- [ ] File follows the correct format specification
- [ ] Contains descriptive comment header
- [ ] Uses realistic but non-existent test values
- [ ] Documented in this README
- [ ] Tested with relevant commands
- [ ] Error fixtures clearly explain what's invalid
- [ ] No actual GitHub URLs or sensitive data

## Related Documentation

- `docs-site/development/testing.md` - Contributor testing guide
- `test_project_repos/qa_tests/test_assignments_commands.sh` - Main test suite using these fixtures
- `test_project_repos/lib/test_helpers.sh` - Test helper functions and assertions
- `test_project_repos/lib/mock_helpers.sh` - Mocking utilities for GitHub API and file system
- `classdock/cli.py` - CLI implementation for assignments commands
- `classdock/assignments/` - Assignments module implementations

## Security Note

⚠️ **IMPORTANT**: All fixtures in this directory use test/mock data only. These are NOT real GitHub URLs, organizations, or credentials.

**Never commit**:
- Real GitHub organization names
- Real repository URLs
- Actual GitHub tokens or credentials
- Real student usernames or identifying information
- Production configuration files

All fixtures should use:
- `test-org` or similar fictional organization names
- `test-assignment` or descriptive test assignment names
- `studentN` or generic usernames
- Mock/fictional URLs that don't point to real repositories

## Testing Best Practices

1. **Use appropriate fixtures** - Select the fixture that matches your test scenario
2. **Test error cases** - Use invalid fixtures to verify error handling
3. **Clean up** - Remove any temporary files created during testing
4. **Isolate tests** - Don't rely on external state or previous test results
5. **Mock external calls** - Use mock helpers to avoid real GitHub API calls
6. **Verify messages** - Check that error messages are clear and actionable
7. **Test all options** - Verify each command option works correctly

---

**Last Updated**: October 20, 2025  
**Fixture Count**: 11 files  
**Commands Supported**: 13 assignments commands  
**Test Coverage**: Setup, validation, orchestration, help, check, cycle, push operations
