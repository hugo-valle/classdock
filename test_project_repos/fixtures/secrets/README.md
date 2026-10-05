# Secrets Fixtures

This directory contains test fixtures for comprehensive QA testing of secrets commands in the `classdock` CLI tool.

## Purpose

These fixtures provide sample configuration files, repository lists, and token files needed to test all secrets-related commands including secrets add, secrets manage, and various error scenarios.

## Fixture Categories

### Configuration Files

- **`basic_secrets.conf`** - Valid configuration with single secret
  - Used for basic secrets add command testing
  - Contains INSTRUCTOR_TESTS_TOKEN configuration
  - STEP_MANAGE_SECRETS=true

- **`multiple_secrets.conf`** - Valid configuration with multiple secrets
  - Used for testing batch secret operations
  - Contains 4 different secrets (INSTRUCTOR_TESTS_TOKEN, API_KEY, DATABASE_URL, SECRET_TOKEN)
  - Tests multi-secret deployment

- **`disabled_secrets.conf`** - Configuration with secrets management disabled
  - STEP_MANAGE_SECRETS=false
  - Tests that secrets add respects disabled flag
  - SECRETS_CONFIG present but should be ignored

- **`empty_secrets.conf`** - Configuration with empty SECRETS_CONFIG
  - Used for testing configuration validation
  - SECRETS_CONFIG="" (empty string)
  - Should trigger error or warning

- **`no_secrets_config.conf`** - Configuration missing SECRETS_CONFIG
  - SECRETS_CONFIG not defined at all
  - Tests error handling for missing configuration
  - Should provide clear error message

- **`malformed_secrets.conf`** - Configuration with invalid SECRETS_CONFIG format
  - Tests parsing error handling
  - Contains entries missing required colons
  - Invalid format examples for validation testing

### Repository Lists

- **`sample_repos.txt`** - Valid repository URLs for testing
  - 5 sample student repository URLs
  - Format: One URL per line
  - Used with --repos option

- **`invalid_repos.txt`** - Invalid repository URLs for error testing
  - Various invalid URL formats
  - Missing protocols, wrong platforms, incomplete URLs
  - Tests URL validation

### Token Files

- **`sample_token.txt`** - Valid GitHub token format
  - Mock token in correct ghp_ format
  - Used for legacy token file testing
  - Format: ghp_[alphanumeric]

- **`invalid_token.txt`** - Invalid token format
  - Missing ghp_ prefix
  - Tests token format validation
  - Should trigger validation error

## Usage Examples

### Basic secrets add with configuration
```bash
classdock secrets add \
  --assignment-root fixtures/secrets/ \
  --config basic_secrets.conf \
  --repos "https://github.com/test-org/repo1"
```

### Testing with multiple secrets
```bash
classdock secrets add \
  --config fixtures/secrets/multiple_secrets.conf \
  --repos-file fixtures/secrets/sample_repos.txt
```

### Testing force update
```bash
classdock secrets add \
  --config fixtures/secrets/basic_secrets.conf \
  --repos "https://github.com/test-org/repo1" \
  --force
```

### Testing with disabled secrets
```bash
classdock secrets add \
  --config fixtures/secrets/disabled_secrets.conf \
  --repos "https://github.com/test-org/repo1"
# Should skip or warn about disabled secrets
```

### Testing error handling
```bash
# Missing SECRETS_CONFIG
classdock secrets add \
  --config fixtures/secrets/no_secrets_config.conf \
  --repos "https://github.com/test-org/repo1"

# Malformed SECRETS_CONFIG
classdock secrets add \
  --config fixtures/secrets/malformed_secrets.conf \
  --repos "https://github.com/test-org/repo1"

# Invalid repository URLs
classdock secrets add \
  --config fixtures/secrets/basic_secrets.conf \
  --repos-file fixtures/secrets/invalid_repos.txt
```

## SECRETS_CONFIG Format

The SECRETS_CONFIG field follows this format:
```
SECRET_NAME:Description:is_org_level
```

**Fields**:
- `SECRET_NAME` - The name of the GitHub Actions secret (required)
- `Description` - Human-readable description (required)
- `is_org_level` - Boolean flag (true/false) for organization-level secrets (required)

**Example**:
```bash
SECRETS_CONFIG="
INSTRUCTOR_TESTS_TOKEN:Token for accessing instructor test repository:false
API_KEY:API key for external service:false
DATABASE_URL:Database connection string:true
"
```

**Special Handling**:
- Empty lines are ignored
- Lines starting with # are comments
- Whitespace is trimmed
- All three fields must be present

## Token File Format

Legacy token files should contain a single line with the GitHub token:

**Valid format**:
```
ghp_[40 alphanumeric characters]
```

**Example**:
```
ghp_1234567890abcdefghijklmnopqrstuvwxyzAB
```

## Repository URL Format

Repository URLs should follow GitHub's format:

**Valid formats**:
```
https://github.com/organization/repository
https://github.com/organization/repository.git
```

**Invalid formats** (for testing):
```
http://github.com/org/repo          # Wrong protocol
github.com/org/repo                 # Missing protocol
https://bitbucket.org/org/repo      # Wrong platform
not-a-url                           # Malformed
```

## Adding New Fixtures

### Naming Conventions

- Configuration files: `*_secrets.conf` or descriptive name
- Repository lists: `*_repos.txt`
- Token files: `*_token.txt`
- Use underscores for multi-word names

### Documentation Requirements

1. Add comment header in file explaining purpose
2. Update this README with new fixture description
3. Provide usage example
4. Note any special considerations

### Validation Checklist

- [ ] File follows correct format specification
- [ ] Contains descriptive comment header
- [ ] Uses realistic but non-existent test values
- [ ] Documented in this README
- [ ] Tested with relevant commands
- [ ] No actual secrets, tokens, or sensitive data
- [ ] Works with test_secrets_commands.sh

## Related Documentation

- `docs-site/development/testing.md` - Contributor testing guide
- `test_project_repos/qa_tests/test_secrets_commands.sh` - Main test suite using these fixtures
- `classdock/secrets/github_secrets.py` - GitHubSecretsManager implementation
- `classdock/services/secrets_service.py` - SecretsService layer

## Security Note

⚠️ **CRITICAL**: All fixtures use mock/test data only. These are NOT real secrets, tokens, or configurations.

### Never commit

- Real GitHub tokens or credentials
- Actual secret values
- Production configuration files
- Real repository URLs containing private information
- Any sensitive data

### Safe practices

- Use mock token format: `ghp_mock[random]`
- Use test organization names: `test-org`, `example-org`
- Use test repository names: `test-assignment-student1`, etc.
- Use test URLs: `https://github.com/test-org/test-repo`

## Testing Best Practices

1. **Use appropriate fixtures** - Select the fixture that matches your test scenario
2. **Test error cases** - Use invalid fixtures to verify error handling
3. **Test all options** - Verify --force, --verbose, --dry-run flags
4. **Test configuration variations** - Empty, missing, malformed configs
5. **Test token handling** - Centralized, file-based, missing tokens
6. **Test URL validation** - Valid, invalid, malformed repository URLs
7. **Verify messages** - Check that error messages are clear and actionable
8. **Isolate tests** - Don't rely on external state or real secrets

## Test Coverage

### Configuration Tests
- ✅ Valid single secret configuration
- ✅ Valid multiple secrets configuration
- ✅ Disabled secrets management
- ✅ Empty SECRETS_CONFIG
- ✅ Missing SECRETS_CONFIG
- ✅ Malformed SECRETS_CONFIG format
- ✅ Invalid GitHub URL

### Repository Tests
- ✅ Valid repository URLs
- ✅ Invalid repository URLs
- ✅ Single repository
- ✅ Multiple repositories
- ✅ Non-existent repositories

### Token Tests
- ✅ Valid token format
- ✅ Invalid token format
- ✅ Centralized token manager
- ✅ Legacy token file
- ✅ Missing token

### Command Options Tests
- ✅ --force flag
- ✅ --verbose flag
- ✅ --dry-run flag
- ✅ --assignment-root option
- ✅ --repos option
- ✅ Combined options

---

**Last Updated**: October 21, 2025  
**Fixture Count**: 11 files  
**Commands Supported**: secrets add, secrets manage  
**Test Coverage**: Configuration validation, token management, repository targeting, error handling, global options
