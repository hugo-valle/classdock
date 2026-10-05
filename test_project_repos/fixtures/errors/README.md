# Error Scenario Test Fixtures

## Purpose

This directory contains test fixtures specifically designed to trigger various error conditions for comprehensive error handling testing in the QA test suite. These fixtures enable systematic testing of validation errors, resource errors, format errors, permission errors, and other failure scenarios.

## Fixture Categories

### Missing Configuration Fixtures

- **`completely_empty.conf`** - Completely empty configuration file
  - Tests handling of completely empty configuration files
  - Expected: Error about missing required fields

### Invalid Format Fixtures

- **`invalid_url_formats.conf`** - Configuration with various malformed URLs
  - Tests URL validation with invalid protocols, missing protocols, incomplete URLs
  - Expected: Error about malformed URLs with specific field names

- **`corrupted_json_token.json`** - Malformed JSON token configuration
  - Contains JSON syntax errors (comments, missing commas)
  - Tests JSON parsing error handling
  - Expected: Error about malformed JSON in token configuration

### Nonexistent Resource Fixtures

- **`nonexistent_repos.txt`** - List of repository URLs that don't exist
  - Contains URLs to repositories that should not exist (trigger 404 errors)
  - Tests 404 error handling in batch operations
  - Expected: Errors for each nonexistent repo, summary of failures

- **`mixed_valid_invalid_repos.txt`** - Mix of valid and invalid repository URLs
  - Contains both well-formed and malformed URLs
  - Tests partial failure scenarios in batch processing
  - Expected: Process valid entries, report errors for invalid ones, show summary

### Permission Error Fixtures

- **`permission_denied.conf`** - Configuration pointing to inaccessible resources
  - Points to private organization and repositories without access
  - Tests 403 Forbidden error handling
  - Expected: Error about access denied with suggestions to check permissions

## Usage Examples

### Test missing configuration fields
```bash
classdock assignments validate-config --config-file fixtures/errors/missing_all_required.conf
# Expected: Error listing all missing required fields
```

### Test invalid URL formats
```bash
classdock assignments validate-config --config-file fixtures/errors/invalid_url_formats.conf
# Expected: Error about malformed URLs with specific field names
```

### Test nonexistent repositories
```bash
classdock assignments help-students fixtures/errors/nonexistent_repos.txt
# Expected: Errors for each nonexistent repo, summary of failures
```

### Test mixed valid/invalid entries
```bash
classdock assignments help-students fixtures/errors/mixed_valid_invalid_repos.txt
# Expected: Process valid entries, report errors for invalid ones, show summary
```

### Test permission errors
```bash
classdock assignments orchestrate --config fixtures/errors/permission_denied.conf
# Expected: Error about access denied with suggestions to check permissions
```

### Test corrupted JSON
```bash
# Copy corrupted_json_token.json to ~/.config/classdock/token_config.json
classdock assignments validate-config
# Expected: Error about malformed JSON in token configuration
```

## Error Testing Strategy

1. **Validation Errors**: Test that invalid configurations are caught early with clear error messages
2. **Resource Errors**: Test that missing or inaccessible resources are handled gracefully
3. **Format Errors**: Test that malformed data is detected and reported clearly
4. **Permission Errors**: Test that access issues are explained with actionable suggestions
5. **Partial Failures**: Test that batch operations handle mixed success/failure scenarios

## Expected Error Behaviors

### Exit Codes
- All error scenarios should return non-zero exit codes (typically 1)
- Batch operations may return 0 with warnings for partial success

### Error Messages
- Should be clear and specific about what went wrong
- Should identify the problematic field, file, or resource
- Should provide actionable suggestions for fixing the issue
- Should include relevant context (file paths, URLs, field names)

### Error Message Examples

```
# Missing configuration
Error: Configuration file not found: /path/to/nonexistent.conf
Suggestion: Create the configuration file or specify a different path with --config

# Nonexistent repository
Error: Repository not found: https://github.com/test-org/nonexistent-repo
Suggestion: Verify the repository URL is correct and you have access

# Permission denied
Error: Access denied to organization: private-org-no-access
Suggestion: Verify you are a member of the organization and your token has the required permissions

# Malformed JSON
Error: Failed to parse token configuration: Invalid JSON syntax
Suggestion: Check ~/.config/classdock/token_config.json for syntax errors
```

## Adding New Error Fixtures

### Naming Conventions
- Use descriptive names that indicate the error type
- Prefix with error category (missing_, invalid_, corrupted_, etc.)
- Use .conf for configuration files, .txt for lists, .json for JSON files

### Documentation Requirements
- Add comment header explaining the error scenario
- Document expected error behavior
- Update this README with new fixture description
- Provide usage example

### Testing Checklist
- [ ] Fixture triggers the intended error
- [ ] Error message is clear and actionable
- [ ] Exit code is non-zero (or appropriate for scenario)
- [ ] No crashes or unexpected behavior
- [ ] Error is logged appropriately
- [ ] Documented in this README

## Related Documentation

- `docs/QA_TESTING_GUIDE.md` - Comprehensive QA testing guide (lines 1691-1705 for error scenarios, lines 1748-1804 for troubleshooting)
- `test_project_repos/qa_tests/test_error_scenarios.sh` - Main error scenarios test suite
- `classdock/utils/github_exceptions.py` - Custom exception classes and error handling
- `classdock/services/` - Service layer error handling patterns

## Security Note

⚠️ **IMPORTANT**: All fixtures use test/mock data only. These are NOT real GitHub URLs, organizations, tokens, or credentials.

**Never commit**:
- Real GitHub organization names
- Real repository URLs
- Actual GitHub tokens or credentials
- Real user information
- Production configuration files

## Testing Best Practices

1. **Test error paths thoroughly** - Errors are as important as success cases
2. **Verify error messages** - Ensure they're clear, specific, and actionable
3. **Check exit codes** - Verify non-zero exit codes for all error scenarios
4. **Test partial failures** - Ensure batch operations handle mixed results
5. **Validate cleanup** - Ensure errors don't leave system in bad state
6. **Test error recovery** - Verify users can fix issues and retry
7. **Mock external failures** - Use mock helpers to simulate network/API errors
8. **Test edge cases** - Empty files, malformed data, extreme values

---

**Last Updated**: October 21, 2025  
**Fixture Count**: 7 files  
**Error Categories**: Missing configs, invalid formats, nonexistent resources, permission errors, corrupted data  
**Test Coverage**: Configuration validation, URL validation, resource existence, permission checking, JSON parsing, batch error handling
