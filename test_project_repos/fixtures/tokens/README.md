# Token Fixtures for QA Testing

## Purpose

This directory contains token configuration fixtures for comprehensive QA testing of the classdock token management system. These fixtures enable testing of various token scenarios, validation logic, and error handling without requiring actual GitHub tokens or API access.

## Fixture Categories

### Valid Token Fixtures

#### `valid_classic_token.json`
- **Type**: Classic token (ghp_ prefix)
- **Permissions**: Full required scopes (repo, read:org, admin:repo_hook, workflow)
- **Expiration**: None (classic tokens don't always have expiration from API)
- **Use Case**: Testing standard token operations, storage, and retrieval

#### `valid_fine_grained_token.json`
- **Type**: Fine-grained token (github_pat_ prefix)
- **Permissions**: Standard fine-grained scopes (repo, read:org, workflow)
- **Expiration**: 1 year in the future
- **Use Case**: Testing fine-grained token features and expiration tracking

### Invalid Token Fixtures

#### `invalid_token_format.json`
- **Type**: Invalid format (doesn't start with ghp_ or github_pat_)
- **Use Case**: Testing token format validation and error handling

#### `insufficient_permissions_token.json`
- **Type**: Classic token with limited scopes
- **Permissions**: Only 'repo' scope (missing read:org, admin:repo_hook, workflow)
- **Use Case**: Testing permission validation logic and missing scope detection

### Expiration Testing Fixtures

#### `expired_token.json`
- **Type**: Fine-grained token with past expiration date
- **Expiration**: 30 days ago
- **Use Case**: Testing expired token detection and handling

#### `expiring_soon_token.json`
- **Type**: Fine-grained token expiring within warning threshold
- **Expiration**: 5 days in the future
- **Use Case**: Testing expiration warning logic (triggers when < 7 days remaining)

## Usage Examples

### Basic Usage in Test Scripts

```bash
#!/bin/bash
source "lib/test_helpers.sh"

# Test with valid classic token
test_valid_classic_token() {
    local config_dir="$HOME/.config/classdock"
    local config_file="$config_dir/token_config.json"

    # Backup existing config if present
    if [ -f "$config_file" ]; then
        mv "$config_file" "${config_file}.backup"
    fi

    # Copy fixture to config location
    mkdir -p "$config_dir"
    cp "fixtures/tokens/valid_classic_token.json" "$config_file"
    chmod 0600 "$config_file"

    # Run test operations
    # ... your test logic here ...

    # Cleanup
    rm "$config_file"
    if [ -f "${config_file}.backup" ]; then
        mv "${config_file}.backup" "$config_file"
    fi
}
```

### Using with setup_test_config() Helper

```bash
# Create temporary test config from fixture
test_token_verification() {
    local test_config=$(create_temp_test_dir "token_test")
    local token_config="$test_config/token_config.json"

    # Copy and customize fixture
    cp "fixtures/tokens/valid_classic_token.json" "$token_config"

    # Run token manager operations
    # ... test logic ...

    # Cleanup
    cleanup_temp_test_dir "$test_config"
}
```

### Modifying Fixture Values for Specific Scenarios

```bash
# Test with custom expiration date
test_custom_expiration() {
    local token_config="/tmp/test_token_config.json"

    # Copy fixture
    cp "fixtures/tokens/valid_fine_grained_token.json" "$token_config"

    # Modify expiration date using jq
    local new_expiration=$(date -u -v+3d +"%Y-%m-%dT%H:%M:%SZ")
    jq --arg exp "$new_expiration" '.github_token.expires_at = $exp' \
        "$token_config" > "${token_config}.tmp"
    mv "${token_config}.tmp" "$token_config"

    # Run test
    # ... test logic ...

    # Cleanup
    rm "$token_config"
}
```

## Token Structure Reference

All token fixtures follow this JSON structure expected by `classdock/utils/token_manager.py`:

```json
{
  "github_token": {
    "token": "ghp_... or github_pat_...",
    "verified_at": "ISO 8601 timestamp",
    "username": "GitHub username",
    "user_type": "User or Organization",
    "user_id": "GitHub user ID",
    "scopes": ["array", "of", "permission", "scopes"],
    "expires_at": "ISO 8601 timestamp or null",
    "expires_at_source": "github_api or manual (optional)",
    "token_type": "classic or fine-grained",
    "rate_limit_remaining": "string number",
    "rate_limit_limit": "string number"
  },
  "stored_at": "ISO 8601 timestamp",
  "storage_type": "config_file, keychain, or environment"
}
```

### Field Descriptions

- **token**: The GitHub personal access token (ghp_ for classic, github_pat_ for fine-grained)
- **verified_at**: Timestamp when token was last verified against GitHub API
- **username**: GitHub username associated with the token
- **user_type**: Account type ("User" or "Organization")
- **user_id**: Numeric GitHub user ID
- **scopes**: Array of OAuth scopes/permissions granted to the token
- **expires_at**: Token expiration date (null for classic tokens without expiration)
- **expires_at_source**: How expiration was determined ("github_api" or "manual")
- **token_type**: Token classification ("classic" or "fine-grained")
- **rate_limit_remaining**: Current API rate limit remaining calls
- **rate_limit_limit**: Total API rate limit for the token
- **stored_at**: Timestamp when token was stored in this location
- **storage_type**: Storage method used ("config_file", "keychain", "environment")

### Valid Scope Values

**Required for classdock operations**:
- `repo` - Full control of private repositories
- `read:org` - Read org and team membership
- `admin:repo_hook` - Full control of repository hooks
- `workflow` - Update GitHub Action workflows

**Additional common scopes**:
- `write:org` - Write org and team membership
- `delete_repo` - Delete repositories
- `notifications` - Access notifications
- `user` - Update user data

## Security Note

⚠️ **IMPORTANT**: All tokens in these fixtures are mock/fake tokens for testing purposes only. These are NOT real GitHub tokens and cannot be used to access GitHub APIs.

**Never commit real GitHub tokens to this repository.** If you need to test with a real token:
1. Use environment variables
2. Store tokens in `.gitignore`d files
3. Use secure credential storage (keychain on macOS)
4. Revoke tokens immediately after testing

## Adding New Fixtures

When creating additional token test fixtures:

1. **Follow the established JSON structure** - Use the structure shown above
2. **Use realistic but fake token values** - Token prefixes must be correct (ghp_ or github_pat_), but the rest should be obviously fake
3. **Include descriptive comments** - Add a comment at the top of the JSON file explaining the test scenario
4. **Document expected behavior** - Update this README with how the fixture should be used
5. **Test thoroughly** - Verify the fixture works with token_manager.py before committing
6. **Name descriptively** - Use clear names like `expired_token.json` or `missing_scopes_token.json`

### Example New Fixture Template

```json
{
  "_comment": "Description of what this fixture tests",
  "github_token": {
    "token": "ghp_or_github_pat_fake_token_value_here",
    "verified_at": "2025-10-19T12:00:00Z",
    "username": "test-user",
    "user_type": "User",
    "user_id": "12345678",
    "scopes": ["required", "scopes", "here"],
    "expires_at": "2026-10-19T12:00:00Z or null",
    "token_type": "classic or fine-grained"
  },
  "stored_at": "2025-10-19T12:00:00Z",
  "storage_type": "config_file"
}
```

## Testing Best Practices

1. **Always cleanup** - Restore original config files after tests
2. **Isolate tests** - Use temporary directories for test operations
3. **Check permissions** - Verify config file permissions (0600) are set correctly
4. **Test all scenarios** - Use multiple fixtures to cover success and failure cases
5. **Validate structure** - Ensure fixtures match the expected schema
6. **Mock API calls** - Don't make real GitHub API requests during tests
7. **Document assumptions** - Comment test code to explain fixture usage

## Related Documentation

- `classdock/utils/token_manager.py` - Token management implementation
- `docs/QA_TESTING_GUIDE.md` - Comprehensive QA testing guide
- `test_project_repos/lib/test_helpers.sh` - Test helper functions
- `test_project_repos/lib/mock_helpers.sh` - Mocking utilities
- `test_project_repos/qa_tests/test_token_management.sh` - Token management tests
