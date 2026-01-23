# GitHub Secrets Management

Comprehensive secret management for GitHub Classroom assignments through the modern Python CLI interface.

## 🎯 Overview

ClassDock provides robust secret management capabilities for:

- **Automated Secret Distribution** - Add secrets across multiple student repositories
- **Secure Token Management** - Handle authentication tokens safely
- **Batch Operations** - Manage secrets for entire classrooms efficiently
- **Secret Rotation** - Update and rotate secrets across repositories
- **Access Control** - Manage secret visibility and permissions

## 📦 Installation

```bash
# Install from PyPI
pip install classdock

# Verify installation
classdock --help
```

## 🚀 Quick Setup

### 1. Provide a GitHub Token (centralized)

ClassDock now prefers a centralized token manager instead of keeping token files in the
current working directory. Tokens may be supplied in one of these ways (priority order):

1. Centralized config file (~/.config/classdock/token_config.json) — recommended
2. System keychain (macOS Keychain) — secure and recommended for interactive users
3. Environment variable `GITHUB_TOKEN` — useful for CI

Example: store token in the centralized config file (JSON format):

```bash
mkdir -p ~/.config/classdock
cat > ~/.config/classdock/token_config.json << 'EOF'
{
    "github_token": "ghp_your_github_token_here",
    "username": "instructor",
    "scopes": ["repo", "read:org", "workflow"],
    "expires_at": null
}
EOF
chmod 600 ~/.config/classdock/token_config.json
```

Or export the token for short-lived use (CI):

```bash
export GITHUB_TOKEN="ghp_your_github_token_here"
```

The built-in token manager (`classdock.utils.token_manager.GitHubTokenManager`)
will automatically detect and use the config file or keychain when available.

### 2. Configure Assignment

Use the new `SECRETS_CONFIG` format to declare secrets. The canonical, simplified
form is a three-field entry per line:

```
SECRET_NAME:description:validate_format
```

Example `assignment.conf` snippet:

```bash
CLASSROOM_URL="https://classroom.github.com/classrooms/123/assignments/homework1"
TEMPLATE_REPO_URL="https://github.com/instructor/homework1-template"
# Use centralized token manager (no GITHUB_TOKEN_FILE required)
SECRETS_CONFIG="
INSTRUCTOR_TESTS_TOKEN:Token for accessing instructor test repository:true
API_KEY:API key for external service:false
"
```

### 3. Distribute Secrets

```bash
# Add secrets to all student repositories
classdock secrets add --config assignment.conf

# Preview what would be done first
classdock --dry-run secrets add --config assignment.conf
```

## 🔧 Secret Management Commands

### Adding Secrets

```bash
# Add all configured secrets
classdock secrets add --config assignment.conf

# Add specific secrets
classdock secrets add --config assignment.conf --secrets "API_KEY,GRADING_TOKEN"

# Add secrets with custom values
API_KEY="custom_value" classdock secrets add --config assignment.conf --secrets "API_KEY"
```

### Removing Secrets

```bash
# Remove specific secrets
classdock secrets remove --config assignment.conf --secrets "OLD_TOKEN"

# Remove all configured secrets
classdock secrets remove --config assignment.conf

# Preview removal (dry-run)
classdock --dry-run secrets remove --config assignment.conf --secrets "OLD_TOKEN"
```

### Listing Secrets

```bash
# List secrets in all repositories
classdock secrets list --config assignment.conf

# List secrets with details
classdock --verbose secrets list --config assignment.conf
```

## ⚙️ Configuration

### Secret Configuration Format

The recommended and supported way to declare secrets is the new `SECRETS_CONFIG`
multiline variable in `assignment.conf`. Each line represents one secret and uses
the 3-field simplified format (or a compatible legacy format):

```
SECRET_NAME:description:validate_format
```

- `SECRET_NAME`: The environment variable name that will be added to student repos.
- `description`: A short human-readable description used for generated configs.
- `validate_format`: `true` if the value should be validated as a GitHub token (e.g. starts with `ghp_`), otherwise `false`.

Example:

```bash
SECRETS_CONFIG="
INSTRUCTOR_TESTS_TOKEN:Token for accessing instructor test repository:true
API_KEY:API key for external service:false
"
```

Backward compatibility: legacy file-backed entries are still supported in the format:

```
SECRET_NAME:description:token_file_path:max_age_days:validate_format
```

When a `token_file_path` is provided the system will read the token from disk. If
it is omitted (or set to an empty value) the centralized token manager will be used.

## 🎯 Advanced Secret Management

### Secret Rotation

Automate secret rotation across all repositories:

```bash
# Step 1: Generate new secrets
new_api_key=$(generate_new_api_key)
new_token=$(generate_new_token)

# Step 2: Update environment
export API_KEY="$new_api_key"
export GRADING_TOKEN="$new_token"

# Step 3: Distribute new secrets
classdock secrets add --config assignment.conf --secrets "API_KEY,GRADING_TOKEN"

# Step 4: Verify distribution
classdock secrets list --config assignment.conf
```

### Conditional Secret Management

Apply secrets based on conditions:

```bash
# Add secrets only to specific repositories
EXCLUDE_REPOS="template,instructor-solution" classdock secrets add --config assignment.conf

# Add different secrets for different assignments
if [[ "$ASSIGNMENT_TYPE" == "final" ]]; then
    SECRETS_LIST="API_KEY,FINAL_EXAM_TOKEN" classdock secrets add --config assignment.conf
else
    SECRETS_LIST="API_KEY,HOMEWORK_TOKEN" classdock secrets add --config assignment.conf
fi
```

### Batch Secret Operations

Manage secrets across multiple assignments:

```bash
#!/bin/bash
# Batch secret management script

ASSIGNMENTS=("homework1" "homework2" "midterm" "final")
NEW_API_KEY="new_secure_api_key"

for assignment in "${ASSIGNMENTS[@]}"; do
    echo "Updating secrets for $assignment..."
    
    # Set assignment-specific configuration
    config_file="assignment-${assignment}.conf"
    
    # Update API key
    API_KEY="$NEW_API_KEY" classdock secrets add --config "$config_file" --secrets "API_KEY"
    
    echo "Completed $assignment"
done
```

## 🛡️ Security Best Practices

### Token Security

```bash
# Create dedicated tokens for secret management
# Required permissions:
# - repo (for repository access)
# - admin:org (for organization secrets)
# - secrets (for repository secrets)

# Store tokens securely using centralized token manager
mkdir -p ~/.config/classdock
cat > ~/.config/classdock/token_config.json << 'EOF'
{
    "github_token": "ghp_your_token_here",
    "username": "instructor",
    "scopes": ["repo", "admin:org", "secrets"],
    "expires_at": null
}
EOF
chmod 600 ~/.config/classdock/token_config.json

# Or use environment variable for CI/automation
export GITHUB_TOKEN="ghp_your_token_here"
```

### Secret Validation

```bash
# Validate secrets before distribution
classdock --dry-run secrets add --config assignment.conf

# Check secret format and permissions
classdock --verbose secrets add --config assignment.conf

# Verify secret distribution
classdock secrets list --config assignment.conf
```

### Access Control

```bash
# Limit secret access to specific repositories
EXCLUDE_REPOS="public-template,instructor-repo" classdock secrets add --config assignment.conf

# Use different tokens for different secret types via environment
GITHUB_TOKEN="ghp_grading_token_here" classdock secrets add --config assignment.conf --secrets "GRADING_TOKEN"
GITHUB_TOKEN="ghp_api_token_here" classdock secrets add --config assignment.conf --secrets "API_KEY"
```

## 📊 Monitoring & Auditing

### Secret Audit

```bash
# List all secrets across repositories
classdock secrets list --config assignment.conf > secret_audit.txt

# Check secret distribution status
classdock --verbose secrets list --config assignment.conf

# Verify specific secrets
classdock secrets list --config assignment.conf --secrets "API_KEY,GRADING_TOKEN"
```

### Distribution Monitoring

```bash
# Monitor secret distribution in real-time
classdock --verbose secrets add --config assignment.conf

# Check for distribution failures
classdock secrets add --config assignment.conf 2>&1 | grep -i error

# Validate distribution success
classdock secrets list --config assignment.conf | grep -c "API_KEY"
```

## 🔄 Integration with Automation

### Automated Secret Management

```bash
# Setup automated secret rotation
cat > secret-rotation.conf << 'EOF'
CLASSROOM_URL="https://classroom.github.com/classrooms/123/assignments/homework1"
SECRETS_LIST="API_KEY,DATABASE_URL"

# Automation schedules
AUTOMATION_SCHEDULE_SECRETS="0 3 * * 1"  # Monday at 3 AM
AUTOMATION_SCHEDULE_ROTATION="0 2 1 * *" # First day of month at 2 AM
EOF

# Set token via environment for automation
export GITHUB_TOKEN="ghp_automation_token_here"
classdock automation scheduler setup --config secret-rotation.conf
```

### Workflow Integration

```bash
# Integrate secret management with complete workflow
classdock assignments orchestrate --config assignment.conf

# This automatically:
# 1. Discovers student repositories
# 2. Distributes configured secrets
# 3. Validates secret distribution
# 4. Reports success/failure status
```

## 🔍 Troubleshooting

### Common Issues

1. **Authentication Failures**:
   ```bash
   # Check token permissions
   classdock --verbose secrets add --config assignment.conf
   ```

2. **Secret Not Found**:
   ```bash
   # Verify secret configuration
   classdock --dry-run secrets add --config assignment.conf
   ```

3. **Distribution Failures**:
   ```bash
   # Check repository access
   classdock repos fetch --config assignment.conf
   ```

### Debug Mode

```bash
# Enable detailed logging
classdock --verbose secrets add --config assignment.conf

# Dry-run with maximum detail
classdock --dry-run --verbose secrets add --config assignment.conf
```

## 📚 Related Documentation

- **[Assignment Orchestrator](ASSIGNMENT-ORCHESTRATOR.md)** - Complete workflow automation
- **[Automation Suite](AUTOMATION-SUITE.md)** - Comprehensive automation capabilities
- **[Cron Automation](CRON-AUTOMATION.md)** - Scheduled secret management
- **[Main CLI Reference](../README.md)** - Complete command documentation

## 💡 Examples & Use Cases

### Exam Environment Setup

```bash
# Setup secure exam environment
cat > exam-secrets.conf << 'EOF'
CLASSROOM_URL="https://classroom.github.com/classrooms/123/assignments/midterm"
SECRETS_LIST="EXAM_API_KEY,GRADING_DATABASE,SECURE_TOKEN"
EXCLUDE_REPOS="template,instructor-solution"
EOF

# Set exam token and distribute secrets
export GITHUB_TOKEN="ghp_exam_token_here"
classdock secrets add --config exam-secrets.conf

# Verify distribution
classdock secrets list --config exam-secrets.conf
```

### API Key Management

```bash
# Rotate API keys for new semester
OLD_KEY="old_api_key_value"
NEW_KEY="new_api_key_value"

# Remove old key
API_KEY="$OLD_KEY" classdock secrets remove --config assignment.conf --secrets "API_KEY"

# Add new key
API_KEY="$NEW_KEY" classdock secrets add --config assignment.conf --secrets "API_KEY"

# Verify update
classdock secrets list --config assignment.conf --secrets "API_KEY"
```

---

GitHub Secrets Management provides secure, efficient handling of sensitive information across GitHub Classroom assignments.
