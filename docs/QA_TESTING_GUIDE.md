# ClassDock - Comprehensive QA Testing Guide

**Version:** 3.1.0-beta.2  
**Date:** October 17, 2025  
**Purpose:** Complete test scenarios for quality assurance validation

---

## Table of Contents

1. [Setup and Prerequisites](#setup-and-prerequisites)
2. [Global Options](#global-options)
3. [Assignments Commands](#assignments-commands)
4. [Repos Commands](#repos-commands)
5. [Secrets Commands](#secrets-commands)
6. [Automation Commands](#automation-commands)
7. [Test Execution Checklist](#test-execution-checklist)
8. [Expected Behaviors](#expected-behaviors)
9. [Common Issues and Troubleshooting](#common-issues-and-troubleshooting)

---

## Setup and Prerequisites

### Required Setup
1. **GitHub Token**: Configured in keychain or environment variable
2. **Test Repository**: A GitHub Classroom assignment to work with
3. **Configuration File**: `assignment.conf` in test directory
4. **Python Environment**: Python 3.10+ with classdock installed

### Installation
```bash
pip install classdock
# or for development
poetry install
```

### Test Data Requirements
- A GitHub organization with classroom access
- At least one test student repository
- Template repository with sample code
- Student list file (students.txt with GitHub usernames)
- Repository URLs file (repos.txt with full GitHub URLs)

---

## Global Options

These options work with ALL commands across all command groups.

### Main Application Options

| Option | Description | Test Scenarios |
|--------|-------------|----------------|
| `--version` | Show version | `classdock --version` |
| `--config TEXT` | Custom config file | `classdock --config custom.conf assignments setup` |
| `--assignment-root TEXT` | Root directory | `classdock --assignment-root /path/to/root assignments setup` |
| `--help` | Show help | `classdock --help` |

### Universal Command Options

These work with `assignments`, `repos`, `secrets`, and `automation` commands:

| Option | Description | Applies To |
|--------|-------------|------------|
| `--verbose` / `-v` | Verbose output | All command groups |
| `--dry-run` | Preview without executing | All command groups |
| `--help` | Command help | All commands |

**Test Scenarios:**
```bash
# Test verbose mode
classdock assignments --verbose orchestrate

# Test dry-run mode
classdock assignments --dry-run orchestrate

# Combine both
classdock repos --verbose --dry-run fetch

# Test help
classdock assignments --help
classdock assignments orchestrate --help
```

---

## GitHub Token Setup and Validation

**CRITICAL PREREQUISITE:** Before testing any commands, verify GitHub token configuration.

### Token Types

The application supports two types of GitHub Personal Access Tokens:

| Token Type | Permissions | Recommended For | Notes |
|------------|-------------|-----------------|-------|
| **Classic Token** | Full repository access | Development, Testing | Easier to set up, broader permissions |
| **Fine-Grained Token** | Specific repository/org access | Production, Limited scope | More secure, granular control |

### Token Storage Methods

The application uses a **centralized token management system** with the following priority order:

| Priority | Storage Method | Platform | Configuration File/Location | How to Set |
|----------|----------------|----------|----------------------------|------------|
| 1 | **Token Config File** | All | `~/.config/classdock/token_config.json` | Automatic via setup wizard |
| 2 | **Keychain** | macOS | Stored in macOS Keychain | Automatic via setup wizard |
| 3 | **Secret Service** | Linux | Stored in Secret Service (GNOME/KDE) | Automatic via setup wizard |
| 4 | **Windows Credential Manager** | Windows | Stored in Credential Manager | Automatic via setup wizard |
| 5 | **Environment Variable** | All | `GITHUB_TOKEN=ghp_xxx` | `export GITHUB_TOKEN=ghp_xxx` |

**Note:** The token is stored in a centralized location (`~/.config/classdock/token_config.json`), not in the project's `assignment.conf` file. This ensures the same token can be used across multiple assignments and projects.

### Token Testing Scenarios

#### Test 1: Classic Token in Token Config File

```bash
# Create token at https://github.com/settings/tokens (classic)
# Required scopes: repo, workflow, admin:org, admin:repo_hook

# Create or edit token config file
mkdir -p ~/.config/classdock
cat > ~/.config/classdock/token_config.json << 'EOF'
{
  "github_token": "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}
EOF

# Test
classdock assignments setup --url "https://classroom.github.com/..."
```

**Validate:**
- [ ] Token is read from `~/.config/classdock/token_config.json`
- [ ] Setup wizard doesn't prompt for token
- [ ] Token has sufficient permissions
- [ ] API calls succeed
- [ ] Config file created if it doesn't exist

#### Test 2: Fine-Grained Token in Token Config File

```bash
# Create token at https://github.com/settings/tokens?type=beta
# Required permissions: Contents (read/write), Pull requests (read/write), Workflows (read/write)

# Add to token config file
mkdir -p ~/.config/classdock
cat > ~/.config/classdock/token_config.json << 'EOF'
{
  "github_token": "github_pat_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}
EOF

# Test
classdock assignments setup --url "https://classroom.github.com/..."
```

**Validate:**
- [ ] Fine-grained token accepted
- [ ] Proper repository/org scope enforced
- [ ] Limited permissions work correctly
- [ ] Clear error if missing required permissions
- [ ] Token stored in centralized location

#### Test 3: Token in Keychain (macOS)

```bash
# Remove token config file if it exists
rm -f ~/.config/classdock/token_config.json

# Setup wizard should prompt and store in keychain
classdock assignments setup

# When prompted, enter token
# Wizard will store in macOS Keychain automatically

# Verify storage
security find-generic-password -s "github-classdock" -w

# Verify token config file was NOT created
test -f ~/.config/classdock/token_config.json && echo "ERROR: Config file created" || echo "OK: Using keychain"
```

**Validate:**
- [ ] Token stored in macOS Keychain
- [ ] Token retrieved automatically on subsequent runs
- [ ] Token NOT in `~/.config/classdock/token_config.json`
- [ ] Security: Token encrypted by system
- [ ] Keychain has priority over environment variables

#### Test 4: Token in Secret Service (Linux)

```bash
# Remove token config file if it exists
rm -f ~/.config/classdock/token_config.json

# Setup wizard should prompt and store in Secret Service
classdock assignments setup

# When prompted, enter token
# Wizard will store in Secret Service (GNOME Keyring/KWallet)

# Verify with secret-tool (if available)
secret-tool lookup service github-classdock

# Verify token config file was NOT created
test -f ~/.config/classdock/token_config.json && echo "ERROR: Config file created" || echo "OK: Using Secret Service"
```

**Validate:**
- [ ] Token stored in Secret Service
- [ ] Token retrieved automatically
- [ ] Token NOT in `~/.config/classdock/token_config.json`
- [ ] Works with GNOME/KDE environments
- [ ] Secret Service has priority over environment variables

#### Test 5: Token in Windows Credential Manager (Windows)

```bash
# Remove token config file if it exists
Remove-Item -Path "$env:USERPROFILE\.config\classdock\token_config.json" -ErrorAction SilentlyContinue

# Setup wizard should prompt and store in Windows Credential Manager
classdock assignments setup

# When prompted, enter token
# Wizard will store in Windows Credential Manager

# Verify in Control Panel > Credential Manager
# Or use PowerShell: cmdkey /list | Select-String "github-classdock"

# Verify token config file was NOT created
Test-Path "$env:USERPROFILE\.config\classdock\token_config.json"
```

**Validate:**
- [ ] Token stored in Credential Manager
- [ ] Token retrieved automatically
- [ ] Token NOT in `~/.config/classdock/token_config.json`
- [ ] Proper Windows security integration
- [ ] Credential Manager has priority over environment variables

#### Test 6: Token in Environment Variable

```bash
# Remove token config file and keychain/secret service token
rm -f ~/.config/classdock/token_config.json
# Also remove from keychain/secret service if present

# Set environment variable
export GITHUB_TOKEN=ghp_xxxxxxxxxxxx

# Test
classdock assignments setup --url "https://classroom.github.com/..."
```

**Validate:**
- [ ] Token read from environment variable
- [ ] Lower priority than token config file and keychain
- [ ] Works for all commands
- [ ] Session-based (not persistent after terminal closes)
- [ ] No token config file created

#### Test 7: Token Import from Environment

```bash
# Set environment variable
export GITHUB_TOKEN=ghp_xxxxxxxxxxxx

# Run setup wizard
classdock assignments setup

# Wizard should detect and offer to import token to keychain/token config
```

**Validate:**
- [ ] Wizard detects environment token
- [ ] Offers to import to keychain or save to token config file
- [ ] Import successful
- [ ] Token accessible after import from persistent storage

#### Test 8: Missing Token Error Handling

```bash
# Remove token from all locations
rm -f ~/.config/classdock/token_config.json
# Remove from keychain/secret service if present
# Unset environment variable
unset GITHUB_TOKEN

classdock assignments setup
```

**Validate:**
- [ ] Clear error message about missing token
- [ ] Instructions on how to create token
- [ ] Link to GitHub token creation page
- [ ] Option to enter token interactively
- [ ] Setup wizard prompts for token

#### Test 9: Invalid Token Error Handling

```bash
# Set invalid token in token config file
mkdir -p ~/.config/classdock
cat > ~/.config/classdock/token_config.json << 'EOF'
{
  "github_token": "invalid_token_value"
}
EOF

classdock assignments setup --url "https://classroom.github.com/..."
```

**Validate:**
- [ ] API authentication failure detected
- [ ] Clear error message indicating invalid token
- [ ] Instructions to check token validity
- [ ] Suggestion to regenerate token
- [ ] Link to token settings page

#### Test 10: Token Permission Validation
```bash
# Create token with insufficient permissions (e.g., only 'repo' scope)

classdock assignments orchestrate
```

**Validate:**
- [ ] Permission errors caught gracefully
- [ ] Specific missing permissions identified
- [ ] Instructions to update token permissions
- [ ] No partial operations executed

### Token Security Best Practices

**For QA Testing:**
- [ ] Never commit tokens to git repositories
- [ ] Use test organization, not production
- [ ] Rotate tokens after testing
- [ ] Test token revocation scenarios
- [ ] Verify tokens are not logged in verbose mode

**Expected Token Behavior:**
- Token config file (`~/.config/classdock/token_config.json`) takes highest priority
- Keychain/Secret Service/Credential Manager preferred for security (auto-storage by setup wizard)
- Environment variable (`GITHUB_TOKEN`) has lowest priority, used for automation/CI
- Clear error messages for missing/invalid tokens
- Token masked in logs (shows only last 4 characters)
- Setup wizard automatically stores tokens in secure platform-specific storage
- Same token can be reused across multiple assignment projects

---

## Assignments Commands

### 1. `assignments setup`

**Purpose:** Launch interactive wizard to configure a new assignment.

**Command Variants:**

```bash
# Basic setup - interactive wizard
classdock assignments setup

# Simplified setup with minimal prompts
classdock assignments setup --simplified

# Setup with GitHub Classroom URL (auto-extracts info)
classdock assignments setup --url "https://classroom.github.com/classrooms/12345/assignments/abc123"

# Setup with global options
classdock assignments --verbose setup
classdock assignments --dry-run setup
classdock assignments --verbose --dry-run setup --simplified
```

**Test Scenarios:**

| Scenario | Command | Expected Result |
|----------|---------|-----------------|
| Interactive setup | `classdock assignments setup` | Wizard prompts for all configuration |
| Simplified setup | `classdock assignments setup --simplified` | Minimal prompts, uses defaults |
| URL-based setup | `classdock assignments setup --url "https://classroom.github.com/..."` | Auto-extracts org and assignment |
| Dry-run setup | `classdock assignments --dry-run setup` | Shows what would be configured |
| Verbose setup | `classdock assignments --verbose setup` | Detailed output during setup |
| Combined flags | `classdock assignments --verbose --dry-run setup --simplified` | Verbose dry-run simplified setup |

**What to Validate:**
- [ ] Assignment name extracted correctly
- [ ] Organization detected properly
- [ ] Configuration file created (`assignment.conf`)
- [ ] Token management options displayed
- [ ] All required fields populated
- [ ] Dry-run doesn't create files
- [ ] Verbose shows detailed steps

---

### 2. `assignments validate-config`

**Purpose:** Validate assignment configuration file.

**Command Variants:**

```bash
# Validate default config
classdock assignments validate-config

# Validate custom config
classdock assignments validate-config --config-file custom.conf
classdock assignments validate-config -c custom.conf

# With global options
classdock assignments --verbose validate-config
classdock assignments --dry-run validate-config
```

**Test Scenarios:**

| Scenario | Command | Expected Result |
|----------|---------|-----------------|
| Valid config | `classdock assignments validate-config` | ✅ Validation success message |
| Missing config | `classdock assignments validate-config -c nonexistent.conf` | ❌ Error: file not found |
| Invalid config | `classdock assignments validate-config -c broken.conf` | ❌ Error: specific validation failures |
| Custom config path | `classdock assignments validate-config -c /path/to/assignment.conf` | Validates specified file |
| Verbose mode | `classdock assignments --verbose validate-config` | Shows detailed validation steps |

**What to Validate:**
- [ ] All required fields present
- [ ] File paths exist and are accessible
- [ ] Repository URLs are valid
- [ ] GitHub organization format correct
- [ ] Error messages are clear and actionable

---

### 3. `assignments orchestrate`

**Purpose:** Execute complete assignment workflow with comprehensive orchestration.

**Command Variants:**

```bash
# Full orchestration (all steps)
classdock assignments orchestrate

# Auto-confirm all prompts
classdock assignments orchestrate --yes
classdock assignments orchestrate -y

# Execute specific step only
classdock assignments orchestrate --step sync
classdock assignments orchestrate --step discover
classdock assignments orchestrate --step secrets
classdock assignments orchestrate --step assist
classdock assignments orchestrate --step cycle

# Skip specific steps
classdock assignments orchestrate --skip sync
classdock assignments orchestrate --skip sync,discover
classdock assignments orchestrate --skip secrets,assist,cycle

# Custom config
classdock assignments orchestrate --config custom.conf
classdock assignments orchestrate -c custom.conf

# Combined options
classdock assignments --verbose --dry-run orchestrate --yes
classdock assignments orchestrate --step sync --yes --verbose
classdock assignments orchestrate --skip secrets,cycle -y -c custom.conf
```

**Test Scenarios:**

| Scenario | Command | Expected Result |
|----------|---------|-----------------|
| Full orchestration | `classdock assignments orchestrate` | Runs all workflow steps |
| Auto-confirm | `classdock assignments orchestrate -y` | No interactive prompts |
| Sync only | `classdock assignments orchestrate --step sync` | Only syncs template |
| Discover only | `classdock assignments orchestrate --step discover` | Only discovers repos |
| Secrets only | `classdock assignments orchestrate --step secrets` | Only manages secrets |
| Assist only | `classdock assignments orchestrate --step assist` | Only helps students |
| Cycle only | `classdock assignments orchestrate --step cycle` | Only cycles collaborators |
| Skip sync | `classdock assignments orchestrate --skip sync` | Runs all except sync |
| Skip multiple | `classdock assignments orchestrate --skip sync,secrets` | Runs all except specified |
| Dry-run full | `classdock assignments --dry-run orchestrate` | Shows what would execute |
| Verbose orchestration | `classdock assignments --verbose orchestrate -y` | Detailed execution output |

**What to Validate:**
- [ ] Steps execute in correct order
- [ ] Skipped steps are actually skipped
- [ ] Step-specific execution works
- [ ] Error handling between steps
- [ ] Dry-run doesn't execute actions
- [ ] Yes flag skips confirmations
- [ ] Progress indicators work
- [ ] Log files created properly

---

### 4. `assignments help-student`

**Purpose:** Help a specific student with repository updates.

**Command Variants:**

```bash
# Help single student (interactive)
classdock assignments help-student "https://github.com/org/assignment-student123"

# Use template directly (bypass classroom repo)
classdock assignments help-student --one-student "https://github.com/org/assignment-student123"

# Auto-confirm
classdock assignments help-student --yes "https://github.com/org/assignment-student123"
classdock assignments help-student -y "https://github.com/org/assignment-student123"

# Custom config
classdock assignments help-student --config custom.conf "https://github.com/org/assignment-student123"
classdock assignments help-student -c custom.conf "https://github.com/org/assignment-student123"

# Combined options
classdock assignments --verbose help-student --one-student --yes "https://github.com/org/assignment-student123"
classdock assignments --dry-run help-student -y -c custom.conf "https://github.com/org/assignment-student123"
```

**Test Scenarios:**

| Scenario | Command | Expected Result |
|----------|---------|-----------------|
| Basic help | `classdock assignments help-student "https://github.com/org/repo"` | Helps update student repo |
| One-student mode | `classdock assignments help-student --one-student "URL"` | Uses template directly |
| Auto-confirm | `classdock assignments help-student -y "URL"` | No prompts |
| Invalid URL | `classdock assignments help-student "invalid-url"` | ❌ Error: invalid URL |
| Non-existent repo | `classdock assignments help-student "https://github.com/org/fake"` | ❌ Error: repo not found |
| Dry-run help | `classdock assignments --dry-run help-student "URL"` | Shows what would be done |
| Verbose help | `classdock assignments --verbose help-student "URL"` | Detailed update process |

**What to Validate:**
- [ ] Repository access verified
- [ ] Updates applied correctly
- [ ] Conflicts handled properly
- [ ] Student notified (if configured)
- [ ] Dry-run doesn't modify repo
- [ ] One-student mode uses template
- [ ] Error messages clear

---

### 5. `assignments help-students`

**Purpose:** Help multiple students with repository updates (batch processing).

**Command Variants:**

```bash
# Batch help from file
classdock assignments help-students student-repos.txt

# Auto-confirm all
classdock assignments help-students --yes student-repos.txt
classdock assignments help-students -y student-repos.txt

# Custom config
classdock assignments help-students --config custom.conf student-repos.txt
classdock assignments help-students -c custom.conf student-repos.txt

# Combined options
classdock assignments --verbose help-students -y student-repos.txt
classdock assignments --dry-run help-students student-repos.txt
classdock assignments --verbose --dry-run help-students -y -c custom.conf student-repos.txt
```

**Test File Format (student-repos.txt):**
```
https://github.com/org/assignment-student1
https://github.com/org/assignment-student2
https://github.com/org/assignment-student3
```

**Test Scenarios:**

| Scenario | Command | Expected Result |
|----------|---------|-----------------|
| Batch help | `classdock assignments help-students repos.txt` | Helps all students in file |
| Auto-confirm | `classdock assignments help-students -y repos.txt` | No prompts for each student |
| Empty file | `classdock assignments help-students empty.txt` | ❌ Error or warning |
| Missing file | `classdock assignments help-students nonexistent.txt` | ❌ Error: file not found |
| Invalid URLs | `classdock assignments help-students invalid-urls.txt` | ❌ Error for bad URLs |
| Dry-run batch | `classdock assignments --dry-run help-students repos.txt` | Shows what would be done |
| Verbose batch | `classdock assignments --verbose help-students repos.txt` | Detailed progress |

**What to Validate:**
- [ ] All repos processed
- [ ] Errors don't stop batch
- [ ] Progress indicators work
- [ ] Summary report at end
- [ ] Failed repos reported
- [ ] Dry-run doesn't modify
- [ ] Log file created

---

### 6. `assignments check-student`

**Purpose:** Check the status of a student repository.

**Command Variants:**

```bash
# Check student status
classdock assignments check-student "https://github.com/org/assignment-student123"

# Custom config
classdock assignments check-student --config custom.conf "https://github.com/org/assignment-student123"
classdock assignments check-student -c custom.conf "https://github.com/org/assignment-student123"

# With global options
classdock assignments --verbose check-student "https://github.com/org/assignment-student123"
classdock assignments --dry-run check-student "https://github.com/org/assignment-student123"
```

**Test Scenarios:**

| Scenario | Command | Expected Result |
|----------|---------|-----------------|
| Valid repo | `classdock assignments check-student "URL"` | Shows repo status |
| Invalid URL | `classdock assignments check-student "bad-url"` | ❌ Error: invalid URL |
| Private repo | `classdock assignments check-student "private-repo-url"` | Status or access error |
| Non-existent | `classdock assignments check-student "https://github.com/org/fake"` | ❌ Error: not found |
| Verbose check | `classdock assignments --verbose check-student "URL"` | Detailed status info |

**What to Validate:**
- [ ] Repository exists
- [ ] Access permissions verified
- [ ] Commit history shown
- [ ] Branch status displayed
- [ ] Collaborators listed
- [ ] Error messages clear

---

### 7. `assignments student-instructions`

**Purpose:** Generate update instructions for a student.

**Command Variants:**

```bash
# Generate instructions (display)
classdock assignments student-instructions "https://github.com/org/assignment-student123"

# Save to file
classdock assignments student-instructions --output instructions.txt "https://github.com/org/assignment-student123"
classdock assignments student-instructions -o instructions.txt "https://github.com/org/assignment-student123"

# Custom config
classdock assignments student-instructions --config custom.conf "https://github.com/org/assignment-student123"
classdock assignments student-instructions -c custom.conf "https://github.com/org/assignment-student123"

# Combined options
classdock assignments --verbose student-instructions -o instructions.md "https://github.com/org/assignment-student123"
classdock assignments student-instructions -o inst.txt -c custom.conf "https://github.com/org/assignment-student123"
```

**Test Scenarios:**

| Scenario | Command | Expected Result |
|----------|---------|-----------------|
| Display instructions | `classdock assignments student-instructions "URL"` | Instructions shown in terminal |
| Save to file | `classdock assignments student-instructions -o file.txt "URL"` | Instructions saved to file |
| Invalid URL | `classdock assignments student-instructions "bad-url"` | ❌ Error: invalid URL |
| Overwrite file | `classdock assignments student-instructions -o existing.txt "URL"` | File overwritten or prompted |
| Verbose mode | `classdock assignments --verbose student-instructions "URL"` | Detailed generation process |

**What to Validate:**
- [ ] Instructions are complete
- [ ] Multiple methods provided
- [ ] Troubleshooting included
- [ ] File saved correctly
- [ ] Formatting is clear
- [ ] URLs are correct

---

### 8. `assignments check-classroom`

**Purpose:** Check if the classroom repository is ready for student updates.

**Command Variants:**

```bash
# Check classroom readiness
classdock assignments check-classroom

# Verbose check
classdock assignments check-classroom --verbose
classdock assignments check-classroom -v

# Custom config
classdock assignments check-classroom --config custom.conf
classdock assignments check-classroom -c custom.conf

# Combined options
classdock assignments --verbose check-classroom
classdock assignments --dry-run check-classroom
classdock assignments --verbose --dry-run check-classroom -c custom.conf
```

**Test Scenarios:**

| Scenario | Command | Expected Result |
|----------|---------|-----------------|
| Ready classroom | `classdock assignments check-classroom` | ✅ Ready status |
| Unready classroom | `classdock assignments check-classroom` | ⚠️ Issues listed |
| No config | `classdock assignments check-classroom` (no config file) | ❌ Error: config needed |
| Verbose check | `classdock assignments --verbose check-classroom` | Detailed status info |

**What to Validate:**
- [ ] Repository access verified
- [ ] Comparison with template
- [ ] Sync status shown
- [ ] Issues clearly listed
- [ ] Recommendations provided

---

### 9. `assignments manage`

**Purpose:** High-level interface for managing assignment lifecycle (placeholder).

**Command Variants:**

```bash
# Basic manage
classdock assignments manage

# With global options
classdock assignments --verbose manage
classdock assignments --dry-run manage
classdock assignments --verbose --dry-run manage
```

**Test Scenarios:**

| Scenario | Command | Expected Result |
|----------|---------|-----------------|
| Basic manage | `classdock assignments manage` | Shows placeholder message |
| Verbose manage | `classdock assignments --verbose manage` | Verbose placeholder |

**What to Validate:**
- [ ] Command recognized
- [ ] Placeholder message shown
- [ ] Future functionality noted

---

### 10. `assignments cycle-collaborator`

**Purpose:** Cycle collaborator permissions for a single repository.

**Command Variants:**

```bash
# Basic cycle
classdock assignments cycle-collaborator "https://github.com/org/assignment-student123" "student123"

# Force cycle (even if access appears correct)
classdock assignments cycle-collaborator --force "https://github.com/org/repo" "username"
classdock assignments cycle-collaborator -f "https://github.com/org/repo" "username"

# Custom config
classdock assignments cycle-collaborator --config custom.conf "URL" "username"
classdock assignments cycle-collaborator -c custom.conf "URL" "username"

# Combined options
classdock assignments --verbose cycle-collaborator "URL" "username"
classdock assignments --dry-run cycle-collaborator -f "URL" "username"
classdock assignments --verbose --dry-run cycle-collaborator -f -c custom.conf "URL" "username"
```

**Test Scenarios:**

| Scenario | Command | Expected Result |
|----------|---------|-----------------|
| Normal cycle | `classdock assignments cycle-collaborator "URL" "user"` | Cycles if needed |
| Force cycle | `classdock assignments cycle-collaborator -f "URL" "user"` | Always cycles |
| Invalid repo | `classdock assignments cycle-collaborator "bad-url" "user"` | ❌ Error: invalid URL |
| Invalid user | `classdock assignments cycle-collaborator "URL" "fakeuser"` | ❌ Error: user not found |
| Dry-run cycle | `classdock assignments --dry-run cycle-collaborator "URL" "user"` | Shows what would happen |
| Verbose cycle | `classdock assignments --verbose cycle-collaborator "URL" "user"` | Detailed permission changes |

**What to Validate:**
- [ ] Permission removal successful
- [ ] Re-invitation sent
- [ ] Access restored
- [ ] Only cycles when needed (unless forced)
- [ ] Dry-run doesn't change permissions
- [ ] Error messages clear

---

### 11. `assignments cycle-collaborators`

**Purpose:** Cycle collaborator permissions for multiple repositories (batch).

**Command Variants:**

```bash
# Batch cycle (usernames mode - default)
classdock assignments cycle-collaborators usernames.txt

# Repository URLs mode
classdock assignments cycle-collaborators --repo-urls repos.txt

# Force cycle all
classdock assignments cycle-collaborators --force usernames.txt
classdock assignments cycle-collaborators -f usernames.txt

# Custom config
classdock assignments cycle-collaborators --config custom.conf usernames.txt
classdock assignments cycle-collaborators -c custom.conf usernames.txt

# Combined options
classdock assignments --verbose cycle-collaborators --repo-urls --force repos.txt
classdock assignments --dry-run cycle-collaborators -f usernames.txt
classdock assignments --verbose --dry-run cycle-collaborators --repo-urls -f -c custom.conf repos.txt
```

**Test File Formats:**

**usernames.txt (username mode):**
```
student1
student2
student3
```

**repos.txt (repo URLs mode):**
```
https://github.com/org/assignment-student1
https://github.com/org/assignment-student2
https://github.com/org/assignment-student3
```

**Test Scenarios:**

| Scenario | Command | Expected Result |
|----------|---------|-----------------|
| Username batch | `classdock assignments cycle-collaborators users.txt` | Cycles for all users |
| Repo URL batch | `classdock assignments cycle-collaborators --repo-urls repos.txt` | Cycles for all repos |
| Force all | `classdock assignments cycle-collaborators -f users.txt` | Forces cycle for all |
| Empty file | `classdock assignments cycle-collaborators empty.txt` | ❌ Error or warning |
| Missing file | `classdock assignments cycle-collaborators fake.txt` | ❌ Error: file not found |
| Dry-run batch | `classdock assignments --dry-run cycle-collaborators users.txt` | Shows what would happen |
| Verbose batch | `classdock assignments --verbose cycle-collaborators users.txt` | Detailed progress |

**What to Validate:**
- [ ] All entries processed
- [ ] Errors don't stop batch
- [ ] Progress shown
- [ ] Summary report generated
- [ ] Failed cycles reported
- [ ] Dry-run doesn't modify

---

### 12. `assignments check-repository-access`

**Purpose:** Check repository access status for a specific user.

**Command Variants:**

```bash
# Check access
classdock assignments check-repository-access "https://github.com/org/assignment-student123" "student123"

# Verbose check
classdock assignments check-repository-access --verbose "URL" "username"
classdock assignments check-repository-access -v "URL" "username"

# Custom config
classdock assignments check-repository-access --config custom.conf "URL" "username"
classdock assignments check-repository-access -c custom.conf "URL" "username"

# Combined options
classdock assignments --verbose check-repository-access "URL" "username"
classdock assignments --verbose check-repository-access -v -c custom.conf "URL" "username"
```

**Test Scenarios:**

| Scenario | Command | Expected Result |
|----------|---------|-----------------|
| Has access | `classdock assignments check-repository-access "URL" "user"` | ✅ Access confirmed |
| No access | `classdock assignments check-repository-access "URL" "noncollab"` | ❌ No access |
| Pending invite | `classdock assignments check-repository-access "URL" "invited"` | ⚠️ Invitation pending |
| Invalid repo | `classdock assignments check-repository-access "bad-url" "user"` | ❌ Error: invalid URL |
| Invalid user | `classdock assignments check-repository-access "URL" "fakeuser"` | ❌ User not found |
| Verbose check | `classdock assignments --verbose check-repository-access "URL" "user"` | Detailed access info |

**What to Validate:**
- [ ] Access status accurate
- [ ] Collaborator role shown
- [ ] Pending invitations detected
- [ ] Error messages clear
- [ ] Recommendations provided

---

### 13. `assignments push-to-classroom`

**Purpose:** Push template repository changes to the classroom repository.

**Command Variants:**

```bash
# Interactive push (default)
classdock assignments push-to-classroom

# Force push without confirmation
classdock assignments push-to-classroom --force
classdock assignments push-to-classroom -f

# Non-interactive mode
classdock assignments push-to-classroom --non-interactive
classdock assignments push-to-classroom --non-interactive --force

# Specific branch
classdock assignments push-to-classroom --branch develop
classdock assignments push-to-classroom -b develop

# Custom config
classdock assignments push-to-classroom --config custom.conf
classdock assignments push-to-classroom -c custom.conf

# Combined options
classdock assignments --verbose push-to-classroom --force --branch main
classdock assignments --dry-run push-to-classroom -f -b develop
classdock assignments --verbose --dry-run push-to-classroom --non-interactive -f -b main -c custom.conf
```

**Test Scenarios:**

| Scenario | Command | Expected Result |
|----------|---------|-----------------|
| Interactive push | `classdock assignments push-to-classroom` | Prompts for confirmation |
| Force push | `classdock assignments push-to-classroom -f` | No confirmation |
| Non-interactive | `classdock assignments push-to-classroom --non-interactive` | No prompts |
| Specific branch | `classdock assignments push-to-classroom -b develop` | Pushes develop branch |
| Invalid branch | `classdock assignments push-to-classroom -b nonexistent` | ❌ Error: branch not found |
| No changes | `classdock assignments push-to-classroom` | ℹ️ Already up to date |
| Conflicts | `classdock assignments push-to-classroom` | ⚠️ Conflict warning |
| Dry-run push | `classdock assignments --dry-run push-to-classroom` | Shows what would push |
| Verbose push | `classdock assignments --verbose push-to-classroom` | Detailed push process |

**What to Validate:**
- [ ] Changes detected correctly
- [ ] Confirmation works (unless forced)
- [ ] Push successful
- [ ] Branch selection works
- [ ] Dry-run doesn't push
- [ ] Conflicts handled properly
- [ ] Error messages clear

---

## Repos Commands

### 14. `repos fetch`

**Purpose:** Discover and fetch student repositories from GitHub Classroom.

**Command Variants:**

```bash
# Basic fetch
classdock repos fetch

# Custom config
classdock repos fetch --config custom.conf
classdock repos fetch -c custom.conf

# With global options
classdock repos --verbose fetch
classdock repos --dry-run fetch
classdock repos --verbose --dry-run fetch
classdock repos --verbose --dry-run fetch -c custom.conf
```

**Test Scenarios:**

| Scenario | Command | Expected Result |
|----------|---------|-----------------|
| Basic fetch | `classdock repos fetch` | Discovers and clones all student repos |
| No config | `classdock repos fetch` (no config file) | ❌ Error: config required |
| No students | `classdock repos fetch` (empty student list) | ⚠️ No repos found |
| Dry-run fetch | `classdock repos --dry-run fetch` | Shows what would be fetched |
| Verbose fetch | `classdock repos --verbose fetch` | Detailed fetch progress |

**What to Validate:**
- [ ] All repos discovered
- [ ] Repos cloned successfully
- [ ] Directory structure correct
- [ ] Dry-run doesn't clone
- [ ] Progress indicators work
- [ ] Summary report generated

---

### 15. `repos update`

**Purpose:** Update assignment configuration and student repositories.

**Command Variants:**

```bash
# Basic update
classdock repos update

# Custom config
classdock repos update --config custom.conf
classdock repos update -c custom.conf

# With global options
classdock repos --verbose update
classdock repos --dry-run update
classdock repos --verbose --dry-run update
classdock repos --verbose --dry-run update -c custom.conf
```

**Test Scenarios:**

| Scenario | Command | Expected Result |
|----------|---------|-----------------|
| Basic update | `classdock repos update` | Updates all student repos |
| No changes | `classdock repos update` (no updates) | ℹ️ Already up to date |
| With changes | `classdock repos update` (changes exist) | Applies updates |
| Conflicts | `classdock repos update` (conflicts exist) | ⚠️ Conflict warnings |
| Dry-run update | `classdock repos --dry-run update` | Shows what would update |
| Verbose update | `classdock repos --verbose update` | Detailed update process |

**What to Validate:**
- [ ] All repos updated
- [ ] Changes applied correctly
- [ ] Conflicts detected
- [ ] Dry-run doesn't modify
- [ ] Progress shown
- [ ] Summary report generated

---

### 16. `repos push`

**Purpose:** Syncs the template repository to the GitHub Classroom repository.

**Command Variants:**

```bash
# Basic push
classdock repos push

# Custom config
classdock repos push --config custom.conf
classdock repos push -c custom.conf

# With global options
classdock repos --verbose push
classdock repos --dry-run push
classdock repos --verbose --dry-run push
classdock repos --verbose --dry-run push -c custom.conf
```

**Test Scenarios:**

| Scenario | Command | Expected Result |
|----------|---------|-----------------|
| Basic push | `classdock repos push` | Syncs template to classroom |
| No changes | `classdock repos push` (no changes) | ℹ️ Already up to date |
| With changes | `classdock repos push` (changes exist) | Pushes changes |
| Dry-run push | `classdock repos --dry-run push` | Shows what would push |
| Verbose push | `classdock repos --verbose push` | Detailed push process |

**What to Validate:**
- [ ] Changes detected
- [ ] Push successful
- [ ] Dry-run doesn't push
- [ ] Error messages clear
- [ ] Verification performed

---

### 17. `repos cycle-collaborator`

**Purpose:** Cycle repository collaborator permissions for assignments.

**Command Variants:**

```bash
# List collaborators
classdock repos cycle-collaborator --list

# Cycle specific user
classdock repos cycle-collaborator --username student123

# Cycle for assignment
classdock repos cycle-collaborator --assignment-prefix hw1

# Cycle for organization
classdock repos cycle-collaborator --organization myorg

# Force cycle
classdock repos cycle-collaborator --force --username student123

# Custom config
classdock repos cycle-collaborator --config custom.conf --username student123
classdock repos cycle-collaborator -c custom.conf --username student123

# Combined options
classdock repos --verbose cycle-collaborator --assignment-prefix hw1 --username student123 --organization myorg
classdock repos --dry-run cycle-collaborator --force --username student123
classdock repos --verbose --dry-run cycle-collaborator --list
classdock repos cycle-collaborator --assignment-prefix hw1 --username student123 --organization myorg --force -c custom.conf
```

**Test Scenarios:**

| Scenario | Command | Expected Result |
|----------|---------|-----------------|
| List collaborators | `classdock repos cycle-collaborator --list` | Lists all collaborators |
| Cycle user | `classdock repos cycle-collaborator --username user` | Cycles user's permissions |
| Assignment prefix | `classdock repos cycle-collaborator --assignment-prefix hw1` | Cycles for hw1 repos |
| Organization | `classdock repos cycle-collaborator --organization org` | Cycles in org |
| Force cycle | `classdock repos cycle-collaborator --force --username user` | Forces cycle |
| Combined filters | `classdock repos cycle-collaborator --assignment-prefix hw1 --username user --organization org` | Cycles with filters |
| Dry-run cycle | `classdock repos --dry-run cycle-collaborator --username user` | Shows what would cycle |
| Verbose cycle | `classdock repos --verbose cycle-collaborator --list` | Detailed collaborator info |

**What to Validate:**
- [ ] List shows all collaborators
- [ ] Filters work correctly
- [ ] Cycle successful
- [ ] Force works
- [ ] Dry-run doesn't modify
- [ ] Multiple options combine properly

---

## Secrets Commands

### 18. `secrets add`

**Purpose:** Add or update secrets in student repositories.

**Command Variants:**

```bash
# Basic add (auto-discovery)
classdock secrets add

# Specify assignment root
classdock secrets add --assignment-root /path/to/template
classdock secrets add -r /path/to/template

# Specify repository URLs
classdock secrets add --repos "https://github.com/org/repo1,https://github.com/org/repo2"

# Combined options
classdock secrets add --assignment-root /path --repos "url1,url2"
classdock secrets add -r /path --repos "url1,url2"

# With global options
classdock secrets --verbose add
classdock secrets --dry-run add
classdock secrets --verbose --dry-run add
classdock secrets --verbose --dry-run add -r /path --repos "url1,url2"
```

**Test Scenarios:**

| Scenario | Command | Expected Result |
|----------|---------|-----------------|
| Auto-discovery | `classdock secrets add` | Discovers repos and adds secrets |
| Specific root | `classdock secrets add -r /path` | Uses specified template |
| Specific repos | `classdock secrets add --repos "url1,url2"` | Adds to specified repos |
| No secrets config | `classdock secrets add` (no secrets configured) | ⚠️ Warning or error |
| Invalid repos | `classdock secrets add --repos "bad-url"` | ❌ Error: invalid URL |
| Dry-run add | `classdock secrets --dry-run add` | Shows what secrets would be added |
| Verbose add | `classdock secrets --verbose add` | Detailed secret addition process |

**What to Validate:**
- [ ] Secrets added successfully
- [ ] All repos processed
- [ ] Encryption works
- [ ] Dry-run doesn't add secrets
- [ ] Error handling works
- [ ] Progress shown
- [ ] Summary generated

---

### 19. `secrets manage`

**Purpose:** Interface for advanced secret and token management (placeholder).

**Command Variants:**

```bash
# Basic manage
classdock secrets manage

# With global options
classdock secrets --verbose manage
classdock secrets --dry-run manage
classdock secrets --verbose --dry-run manage
```

**Test Scenarios:**

| Scenario | Command | Expected Result |
|----------|---------|-----------------|
| Basic manage | `classdock secrets manage` | Shows placeholder message |
| Verbose manage | `classdock secrets --verbose manage` | Verbose placeholder |

**What to Validate:**
- [ ] Command recognized
- [ ] Placeholder message shown
- [ ] Future functionality noted

---

## Automation Commands

### 20. `automation cron-install`

**Purpose:** Install cron job for automated workflow steps.

**Command Variants:**

```bash
# Install single step
classdock automation cron-install sync
classdock automation cron-install secrets
classdock automation cron-install cycle
classdock automation cron-install discover
classdock automation cron-install assist

# Install multiple steps
classdock automation cron-install sync secrets
classdock automation cron-install sync secrets cycle
classdock automation cron-install sync secrets cycle discover assist

# Custom schedule
classdock automation cron-install sync --schedule "0 2 * * *"
classdock automation cron-install sync -s "0 */4 * * *"

# Custom config
classdock automation cron-install sync --config custom.conf
classdock automation cron-install sync -c custom.conf

# Combined options
classdock automation --verbose cron-install sync secrets --schedule "0 2 * * *"
classdock automation --dry-run cron-install sync secrets cycle
classdock automation --verbose --dry-run cron-install sync -s "0 2 * * *" -c custom.conf
```

**Cron Schedule Examples:**
- `"0 2 * * *"` - Every day at 2:00 AM
- `"0 */4 * * *"` - Every 4 hours
- `"*/30 * * * *"` - Every 30 minutes
- `"0 0 * * 1"` - Every Monday at midnight
- `"0 12 * * 1-5"` - Weekdays at noon

**Test Scenarios:**

| Scenario | Command | Expected Result |
|----------|---------|-----------------|
| Install sync | `classdock automation cron-install sync` | Cron job created for sync |
| Install secrets | `classdock automation cron-install secrets` | Cron job for secrets |
| Install cycle | `classdock automation cron-install cycle` | Cron job for cycle |
| Install multiple | `classdock automation cron-install sync secrets` | Multiple jobs created |
| Custom schedule | `classdock automation cron-install sync -s "0 2 * * *"` | Uses custom schedule |
| Invalid schedule | `classdock automation cron-install sync -s "invalid"` | ❌ Error: invalid cron |
| Duplicate install | `classdock automation cron-install sync` (already exists) | Updates or warns |
| Dry-run install | `classdock automation --dry-run cron-install sync` | Shows what would install |
| Verbose install | `classdock automation --verbose cron-install sync` | Detailed installation |

**What to Validate:**
- [ ] Cron job created
- [ ] Schedule correct
- [ ] Command correct
- [ ] Multiple steps work
- [ ] Dry-run doesn't install
- [ ] Error messages clear

---

### 21. `automation cron-remove`

**Purpose:** Remove cron jobs for automated workflow steps.

**Command Variants:**

```bash
# Remove single step
classdock automation cron-remove sync
classdock automation cron-remove secrets
classdock automation cron-remove cycle

# Remove multiple steps
classdock automation cron-remove sync secrets
classdock automation cron-remove sync secrets cycle

# Remove all
classdock automation cron-remove all

# No arguments (remove all)
classdock automation cron-remove

# Custom config
classdock automation cron-remove sync --config custom.conf
classdock automation cron-remove sync -c custom.conf

# Combined options
classdock automation cron-remove sync secrets -c custom.conf
```

**Test Scenarios:**

| Scenario | Command | Expected Result |
|----------|---------|-----------------|
| Remove sync | `classdock automation cron-remove sync` | Removes sync cron job |
| Remove secrets | `classdock automation cron-remove secrets` | Removes secrets job |
| Remove multiple | `classdock automation cron-remove sync secrets` | Removes multiple jobs |
| Remove all | `classdock automation cron-remove all` | Removes all jobs |
| No jobs | `classdock automation cron-remove sync` (no jobs) | ℹ️ No jobs to remove |
| Non-existent | `classdock automation cron-remove fake-step` | ⚠️ Warning or error |

**What to Validate:**
- [ ] Jobs removed correctly
- [ ] Multiple removals work
- [ ] "all" removes everything
- [ ] Error messages clear
- [ ] Confirmation shown

---

### 22. `automation cron-status`

**Purpose:** Show status of installed cron jobs.

**Command Variants:**

```bash
# Basic status
classdock automation cron-status

# Custom config
classdock automation cron-status --config custom.conf
classdock automation cron-status -c custom.conf

# With global options
classdock automation --verbose cron-status
classdock automation --dry-run cron-status
classdock automation --verbose --dry-run cron-status -c custom.conf
```

**Test Scenarios:**

| Scenario | Command | Expected Result |
|----------|---------|-----------------|
| With jobs | `classdock automation cron-status` | Lists all installed jobs |
| No jobs | `classdock automation cron-status` | ℹ️ No jobs installed |
| Verbose status | `classdock automation --verbose cron-status` | Detailed job information |

**What to Validate:**
- [ ] All jobs listed
- [ ] Schedules shown
- [ ] Commands shown
- [ ] Log activity shown
- [ ] Clear formatting

---

### 23. `automation cron-logs`

**Purpose:** Show recent workflow log entries.

**Command Variants:**

```bash
# Default (30 lines)
classdock automation cron-logs

# Specific number of lines
classdock automation cron-logs --lines 50
classdock automation cron-logs -n 100
classdock automation cron-logs -n 10

# Verbose mode
classdock automation cron-logs --verbose
classdock automation cron-logs -v

# Custom config
classdock automation cron-logs --config custom.conf
classdock automation cron-logs -c custom.conf

# Combined options
classdock automation cron-logs -n 50 -v -c custom.conf
classdock automation --verbose cron-logs -n 100
```

**Test Scenarios:**

| Scenario | Command | Expected Result |
|----------|---------|-----------------|
| Default lines | `classdock automation cron-logs` | Shows last 30 lines |
| 50 lines | `classdock automation cron-logs -n 50` | Shows last 50 lines |
| No logs | `classdock automation cron-logs` (no logs) | ℹ️ No logs available |
| Verbose logs | `classdock automation cron-logs -v` | Detailed log display |

**What to Validate:**
- [ ] Correct number of lines shown
- [ ] Most recent entries first
- [ ] Timestamps shown
- [ ] Error entries highlighted
- [ ] Clear formatting

---

### 24. `automation cron-schedules`

**Purpose:** List default schedules for workflow steps.

**Command Variants:**

```bash
# Show default schedules
classdock automation cron-schedules
```

**Test Scenarios:**

| Scenario | Command | Expected Result |
|----------|---------|-----------------|
| Show schedules | `classdock automation cron-schedules` | Lists all default schedules |

**What to Validate:**
- [ ] All steps shown
- [ ] Default schedules listed
- [ ] Descriptions included
- [ ] Examples provided
- [ ] Cron format explained

---

### 25. `automation cron-sync`

**Purpose:** Execute automated workflow cron job with specified steps.

**Command Variants:**

```bash
# Execute sync (default)
classdock automation cron-sync
classdock automation cron-sync sync

# Execute specific steps
classdock automation cron-sync discover
classdock automation cron-sync secrets
classdock automation cron-sync assist
classdock automation cron-sync cycle

# Execute multiple steps
classdock automation cron-sync sync secrets
classdock automation cron-sync sync discover secrets assist cycle

# Stop on failure
classdock automation cron-sync --stop-on-failure sync secrets
classdock automation cron-sync --stop-on-failure sync secrets cycle

# Show log after execution
classdock automation cron-sync --show-log sync
classdock automation cron-sync --show-log sync secrets

# Custom config
classdock automation cron-sync --config custom.conf sync
classdock automation cron-sync -c custom.conf sync

# Combined options
classdock automation --verbose cron-sync sync secrets --stop-on-failure
classdock automation --dry-run cron-sync --show-log sync secrets
classdock automation --verbose --dry-run cron-sync --stop-on-failure --show-log -c custom.conf sync secrets cycle
```

**Test Scenarios:**

| Scenario | Command | Expected Result |
|----------|---------|-----------------|
| Default sync | `classdock automation cron-sync` | Executes sync step |
| Sync step | `classdock automation cron-sync sync` | Executes sync |
| Discover step | `classdock automation cron-sync discover` | Executes discover |
| Multiple steps | `classdock automation cron-sync sync secrets` | Executes both |
| Stop on failure | `classdock automation cron-sync --stop-on-failure sync secrets` | Stops if sync fails |
| Show log | `classdock automation cron-sync --show-log sync` | Displays log after |
| Invalid step | `classdock automation cron-sync fake-step` | ❌ Error: invalid step |
| Dry-run sync | `classdock automation --dry-run cron-sync sync` | Shows what would execute |
| Verbose sync | `classdock automation --verbose cron-sync sync` | Detailed execution |

**What to Validate:**
- [ ] Steps execute in order
- [ ] Logs created
- [ ] Stop-on-failure works
- [ ] Show-log displays output
- [ ] Error handling works
- [ ] Dry-run doesn't execute
- [ ] Progress shown

---

### 26. `automation cron` (Legacy)

**Purpose:** Manage cron automation jobs via CLI (legacy command).

**Command Variants:**

```bash
# Status (default)
classdock automation cron
classdock automation cron --action status
classdock automation cron -a status

# Install
classdock automation cron --action install
classdock automation cron -a install

# Remove
classdock automation cron --action remove
classdock automation cron -a remove

# Custom config
classdock automation cron --config custom.conf
classdock automation cron -c custom.conf

# Combined options
classdock automation --verbose cron -a install
classdock automation --dry-run cron -a remove
classdock automation --verbose --dry-run cron -a status -c custom.conf
```

**Test Scenarios:**

| Scenario | Command | Expected Result |
|----------|---------|-----------------|
| Default status | `classdock automation cron` | Shows cron status |
| Status action | `classdock automation cron -a status` | Shows status |
| Install action | `classdock automation cron -a install` | Installs cron jobs |
| Remove action | `classdock automation cron -a remove` | Removes jobs |
| Invalid action | `classdock automation cron -a invalid` | ❌ Error: invalid action |
| Dry-run install | `classdock automation --dry-run cron -a install` | Shows what would install |

**What to Validate:**
- [ ] Legacy command works
- [ ] Actions work correctly
- [ ] Warning about new commands shown
- [ ] Redirects to new commands suggested

---

### 27. `automation sync`

**Purpose:** Execute scheduled synchronization tasks.

**Command Variants:**

```bash
# Basic sync
classdock automation sync

# Custom config
classdock automation sync --config custom.conf
classdock automation sync -c custom.conf

# With global options
classdock automation --verbose sync
classdock automation --dry-run sync
classdock automation --verbose --dry-run sync
classdock automation --verbose --dry-run sync -c custom.conf
```

**Test Scenarios:**

| Scenario | Command | Expected Result |
|----------|---------|-----------------|
| Basic sync | `classdock automation sync` | Executes scheduled sync |
| No changes | `classdock automation sync` (up to date) | ℹ️ No changes needed |
| With changes | `classdock automation sync` (changes exist) | Syncs changes |
| Dry-run sync | `classdock automation --dry-run sync` | Shows what would sync |
| Verbose sync | `classdock automation --verbose sync` | Detailed sync process |

**What to Validate:**
- [ ] Sync executes
- [ ] Changes detected
- [ ] Logs created
- [ ] Dry-run doesn't sync
- [ ] Error handling works

---

### 28. `automation batch`

**Purpose:** Run batch processing operations (placeholder).

**Command Variants:**

```bash
# Basic batch
classdock automation batch
```

**Test Scenarios:**

| Scenario | Command | Expected Result |
|----------|---------|-----------------|
| Basic batch | `classdock automation batch` | Shows placeholder message |

**What to Validate:**
- [ ] Command recognized
- [ ] Placeholder message shown
- [ ] Future functionality noted

---

## Test Execution Checklist

### Pre-Test Setup
- [ ] Python 3.10+ installed
- [ ] classdock installed (`pip install classdock`)
- [ ] GitHub token configured
- [ ] Test organization available
- [ ] Test repositories created
- [ ] Configuration file prepared
- [ ] Test data files ready (students.txt, repos.txt, etc.)

### Testing Approach

#### Phase 1: Basic Command Structure
- [ ] Test `--help` for all commands
- [ ] Test `--version`
- [ ] Verify all command groups accessible
- [ ] Check command typos/invalid commands show proper errors

#### Phase 2: Global Options
- [ ] Test `--verbose` with each command group
- [ ] Test `--dry-run` with each command group
- [ ] Test `--config` with custom config files
- [ ] Test combinations of global options

#### Phase 3: Assignments Commands
- [ ] Test `setup` with all variants
- [ ] Test `validate-config` with valid/invalid configs
- [ ] Test `orchestrate` with all step/skip combinations
- [ ] Test student help commands
- [ ] Test status checking commands
- [ ] Test collaborator cycling commands
- [ ] Test push-to-classroom with all options

#### Phase 4: Repos Commands
- [ ] Test `fetch` operations
- [ ] Test `update` operations
- [ ] Test `push` operations
- [ ] Test `cycle-collaborator` with all filters

#### Phase 5: Secrets Commands
- [ ] Test `add` with auto-discovery
- [ ] Test `add` with specific repos
- [ ] Test secret encryption
- [ ] Verify secrets added to GitHub

#### Phase 6: Automation Commands
- [ ] Test cron installation
- [ ] Test cron status
- [ ] Test cron logs
- [ ] Test cron removal
- [ ] Test automated sync execution

#### Phase 7: Error Scenarios
- [ ] Test with missing config files
- [ ] Test with invalid repository URLs
- [ ] Test with non-existent users
- [ ] Test with network issues
- [ ] Test with permission errors
- [ ] Test with invalid input files

#### Phase 8: Edge Cases
- [ ] Test with empty files
- [ ] Test with very long file lists
- [ ] Test with special characters in names
- [ ] Test with concurrent executions
- [ ] Test with interrupted operations

---

## Expected Behaviors

### Success Indicators (✅)
- Exit code: 0
- Success message displayed
- Operation completed as expected
- Log files created (if applicable)
- Progress indicators shown
- Summary reports generated

### Warning Indicators (⚠️)
- Exit code: 0 (usually)
- Warning message displayed
- Operation completed with issues
- Non-critical problems noted
- Recommendations provided

### Error Indicators (❌)
- Exit code: non-zero (typically 1)
- Error message displayed
- Operation failed or aborted
- Clear explanation provided
- Troubleshooting suggestions given

### Dry-Run Behavior
- No actual changes made
- Preview of actions shown
- Exit code: 0 (success)
- Message indicates dry-run mode
- Shows what would happen

### Verbose Behavior
- Detailed output shown
- Progress steps visible
- API calls logged (if applicable)
- Timing information included
- Debug information available

---

## Common Issues and Troubleshooting

### Configuration Issues

**Problem:** Configuration file not found  
**Test:** `classdock assignments validate-config -c nonexistent.conf`  
**Expected:** Clear error message indicating file not found  
**Solution:** Create config file or specify correct path

**Problem:** Invalid configuration format  
**Test:** Create malformed config file and validate  
**Expected:** Specific validation errors with line numbers  
**Solution:** Fix configuration according to error messages

### Authentication Issues

**Problem:** GitHub token not configured  
**Test:** Remove token and run any GitHub operation  
**Expected:** Error indicating token required  
**Solution:** Configure token via keychain or environment variable

**Problem:** Token lacks required permissions  
**Test:** Use token without correct scopes  
**Expected:** Error indicating permission denied  
**Solution:** Generate new token with correct scopes

### Repository Issues

**Problem:** Repository not found  
**Test:** Use non-existent repository URL  
**Expected:** Error indicating repository not found  
**Solution:** Verify repository URL is correct and accessible

**Problem:** No repository access  
**Test:** Use private repository without access  
**Expected:** Error indicating access denied  
**Solution:** Verify collaborator access or token permissions

### Network Issues

**Problem:** Network connection failure  
**Test:** Disconnect network and run command  
**Expected:** Error indicating connection failure  
**Solution:** Check network connection and retry

### File Issues

**Problem:** File not found  
**Test:** Reference non-existent file in command  
**Expected:** Error indicating file not found  
**Solution:** Verify file path is correct

**Problem:** Empty file  
**Test:** Use empty file for batch operations  
**Expected:** Warning indicating no entries to process  
**Solution:** Add entries to file or verify correct file used

---

## Test Result Template

Use this template to document test results:

```markdown
### Test: [Command Name]
**Date:** [Test Date]
**Tester:** [Your Name]
**Command:** `[Full Command]`

**Expected Result:**
[What should happen]

**Actual Result:**
[What actually happened]

**Status:** [✅ PASS / ❌ FAIL / ⚠️ WARNING]

**Notes:**
[Any observations, issues, or recommendations]

**Screenshots/Logs:**
[Attach if applicable]
```

---

## Quick Test Commands

### Smoke Test (Quick Validation)
```bash
# Test basic functionality
classdock --version
classdock --help
classdock assignments --help
classdock repos --help
classdock secrets --help
classdock automation --help

# Test dry-run mode
classdock assignments --dry-run validate-config
classdock repos --dry-run fetch
classdock automation --dry-run cron-status
```

### Full Test Suite (Comprehensive)
```bash
# Save this as test_all.sh and run it
#!/bin/bash

echo "=== Testing Global Options ==="
classdock --version
classdock --help

echo "=== Testing Assignments Commands ==="
classdock assignments --help
classdock assignments --dry-run setup --simplified
classdock assignments --dry-run validate-config
classdock assignments --dry-run orchestrate

echo "=== Testing Repos Commands ==="
classdock repos --help
classdock repos --dry-run fetch
classdock repos --dry-run update

echo "=== Testing Secrets Commands ==="
classdock secrets --help
classdock secrets --dry-run add

echo "=== Testing Automation Commands ==="
classdock automation --help
classdock automation cron-status
classdock automation cron-schedules

echo "=== All Tests Complete ==="
```

---

## Reporting Issues

When reporting issues found during QA testing, include:

1. **Command executed** (exact command with all options)
2. **Expected behavior** (what should have happened)
3. **Actual behavior** (what actually happened)
4. **Error messages** (full error text)
5. **Environment details** (OS, Python version, classdock version)
6. **Configuration** (relevant config file contents, sanitized)
7. **Steps to reproduce** (exact steps to trigger the issue)
8. **Screenshots/logs** (if applicable)

---

## Summary Statistics Tracking

Track these metrics during QA testing:

- **Total commands tested:** [Number]
- **Passed:** [Number] (✅)
- **Failed:** [Number] (❌)
- **Warnings:** [Number] (⚠️)
- **Not tested:** [Number]
- **Blocked:** [Number] (cannot test due to dependencies)

---

**End of QA Testing Guide**

For questions or clarifications, contact the development team.
