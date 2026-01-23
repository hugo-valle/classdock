# Centralized Token Management Migration

## Overview
This document summarizes the migration from file-based token storage (`instructor_token.txt`) to centralized token management using `GitHubTokenManager`.

## Migration Date
Completed: 2024

## Motivation
- **Single Source of Truth**: One centralized location for GitHub authentication
- **Better Security**: Tokens stored with proper permissions (0o600) outside repository
- **Reduced Complexity**: No need to create/manage multiple token files per assignment
- **Environment Flexibility**: Support for file, keychain, and environment variable sources

## Changes Made

### 1. Service Layer (`classdock/services/assignment_service.py`)
**Purpose**: Pre-check token availability before launching setup wizard

**Changes**:
- Added token pre-check at start of `setup()` method
- Checks for centralized token config file or keychain token
- If only `GITHUB_TOKEN` env var exists, offers to import it to config file
- If no token exists, prompts for interactive token setup
- Validates token before proceeding to wizard

**Code Added**:
```python
from classdock.utils.token_manager import GitHubTokenManager
import os

# Token pre-check logic before AssignmentSetup() instantiation
token_manager = GitHubTokenManager()
config_path = Path.home() / ".config" / "classdock" / "token_config.json"
# ... validation and import flow ...
```

### 2. Secrets Management (`classdock/secrets/github_secrets.py`)
**Purpose**: Use centralized token instead of reading token files

**Changes**:
- Modified `process_single_repo()` signature: `token_file: str` → `secret_value: Optional[str]`
- If `secret_value` is None, uses `self.github_token` (from centralized manager)
- Updated `process_batch_repos()` with same pattern
- Modified `add_secrets_from_global_config()` to:
  - Check `secret_config.uses_centralized_token()`
  - If True: use `self.github_token` directly
  - If False (legacy): read from specified token file path

**Code Pattern**:
```python
def process_single_repo(
    self,
    repo_url: str,
    secret_name: str,
    secret_value: Optional[str] = None,
    dry_run: bool = False
) -> bool:
    # Use centralized token if secret_value not provided
    if secret_value is None:
        secret_value = self.github_token
    # ... rest of implementation
```

### 3. Assignment Setup Wizard (`classdock/assignments/setup.py`)
**Purpose**: Remove token file creation from setup flow

**Changes in `_configure_tokens()`**:
- Removed prompts for token value input
- Removed token_value storage in config_values
- Changed to inform user that centralized token will be used
- Removed token_files mapping creation

**Changes in `_create_files()`**:
- Removed call to `file_manager.create_token_files()`
- Added comment explaining centralized token system

**Before**:
```python
# Prompted for token value, created instructor_token.txt
token_value = self._get_multiline_secret("instructor tests token")
config_values['token_value'] = token_value
file_manager.create_token_files(token_files, config_values)
```

**After**:
```python
# No token files created - centralized token system handles this
print("\n✓ Using centralized GitHub token from configuration")
```

### 4. UI Components (`classdock/utils/ui_components.py`)
**Purpose**: Update completion and help messages to reflect new architecture

**Changes in `show_completion()`**:
- Removed display of `instructor_token.txt` from files list
- Removed loop displaying additional token files
- Added "Token Management" section showing centralized config path
- Updated to show "Secrets configured (using centralized GitHub token)"

**Changes in `show_help()`**:
- Updated FEATURES section to mention "Centralized token management"
- Updated REQUIREMENTS to reference "GitHub token configured via ~/.config/classdock/"
- Updated GENERATED FILES to remove token file references
- Added TOKEN MANAGEMENT section explaining centralized approach

**Before**:
```
GENERATED FILES:
    • assignment.conf - Complete assignment configuration
    • instructor_token.txt - Secure GitHub API token
    • [custom]_token.txt - Additional token files as configured
```

**After**:
```
GENERATED FILES:
    • assignment.conf - Complete assignment configuration
    • .gitignore - Updated to protect sensitive files

TOKEN MANAGEMENT:
    • Centralized: ~/.config/classdock/token_config.json
    • Environment: GITHUB_TOKEN variable
    • No token files stored in repository
```

## Token Lookup Priority (Unchanged)
The `GitHubTokenManager` maintains this priority order:
1. **Config file**: `~/.config/classdock/token_config.json`
2. **System keychain**: macOS Keychain (platform-specific)
3. **Environment variable**: `GITHUB_TOKEN`
4. **Interactive setup**: Prompts user if none found

## Backward Compatibility
Legacy configs that specify explicit token file paths are still supported:
- If `SecretsConfig.uses_centralized_token()` returns False
- The system will read from the specified token file path
- This ensures existing assignments continue to work

## Files Modified
1. `classdock/services/assignment_service.py` - Token pre-check
2. `classdock/secrets/github_secrets.py` - Centralized token usage
3. `classdock/assignments/setup.py` - Removed token file creation
4. `classdock/utils/ui_components.py` - Updated UI messages
5. `classdock/utils/token_manager.py` - Fixed datetime import bug

## Files NOT Modified (Intentionally)
1. `classdock/utils/file_operations.py` - .gitignore template still protects token files (backward compatibility)
2. `classdock/config/global_config.py` - Legacy config support maintained
3. `classdock/config/generator.py` - Template includes legacy token options
4. `scripts_legacy/` - Legacy bash scripts unchanged

## Testing Performed
✅ Import tests for all modified modules
✅ Service layer instantiation test
✅ Token manager availability test
✅ Method signature validation
✅ Dry-run setup execution

## Remaining Work
- [ ] End-to-end test: Run full `classdock assignments setup` in test directory
- [ ] End-to-end test: Run `classdock secrets add` with centralized token
- [ ] Integration test: Verify no `instructor_token.txt` created during setup
- [ ] Integration test: Verify secrets deployment works with centralized token

## Migration Guide for Users

### For New Assignments
No action needed! The setup wizard will:
1. Check for existing token configuration
2. Offer to import `GITHUB_TOKEN` env var if present
3. Guide you through interactive token setup if needed
4. Store token centrally (no files in repository)

### For Existing Assignments
Your existing token files will continue to work:
- Keep using `assignment.conf` as-is
- Legacy configs with token file paths are supported
- Consider migrating to centralized token for better security

### To Migrate Existing Setup
1. Run: `classdock tokens setup` (if available) OR
2. Export your token: `export GITHUB_TOKEN="ghp_your_token_here"`
3. Run setup in new assignment directory
4. Setup will detect env var and offer to import to centralized config
5. Future assignments automatically use centralized token

## Security Improvements
- **File permissions**: Centralized config uses `0o600` (user read/write only)
- **Location**: Stored in user config directory (not in repository)
- **No accidental commits**: Tokens never stored in repository directories
- **Single credential**: One token for all assignments (easier to rotate)

## Benefits
1. **Simplified Workflow**: No token file management per assignment
2. **Better Security**: Tokens outside repository, proper permissions
3. **Easier Maintenance**: Update token once, applies to all assignments
4. **Cleaner Repos**: No token files to manage or protect
5. **Environment Support**: Works with CI/CD via environment variables

## Documentation Updates Needed
- [ ] Update `docs/SECRETS-MANAGEMENT.md` with centralized token info
- [ ] Update README with new token setup instructions
- [ ] Update `docs/TOOLS-USAGE.md` to remove token file references
- [ ] Create user migration guide from file-based to centralized tokens

## Related Issues
- Fixed: Setup wizard launched without checking for token
- Fixed: "expected str, bytes or os.PathLike object, not NoneType" in secrets add
- Fixed: Empty `instructor_token.txt` files created during setup
- Fixed: datetime import shadowing in token_manager.py

---

**Migration Status**: ✅ Complete (UI/code changes done, end-to-end testing pending)
**Backward Compatibility**: ✅ Maintained (legacy token files still supported)
**Security Impact**: ✅ Improved (centralized storage with proper permissions)
