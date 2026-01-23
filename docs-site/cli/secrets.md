# Secret Management Commands

Secret management commands provide secure handling of sensitive information for GitHub Classroom assignments.

## Overview

Secret management includes distributing API keys, database credentials, and other sensitive data to student repositories while maintaining security best practices.

## Commands

### `classdock secrets add`

Add secrets to student repositories for an assignment.

```bash
# Add secrets from environment
classdock secrets add --assignment "api-project"

# Add secrets from file
classdock secrets add --secrets-file api-keys.env

# Add specific secret
classdock secrets add --name "API_KEY" --value "secret-value"

# Add secrets with confirmation
classdock secrets add --confirm --verbose
```

**Options:**
- `--assignment NAME`: Target specific assignment
- `--secrets-file FILE`: Load secrets from file
- `--name NAME`: Secret name (for single secret)
- `--value VALUE`: Secret value (for single secret)
- `--confirm`: Require confirmation before adding
- `--overwrite`: Overwrite existing secrets
- `--dry-run`: Preview operations without execution

**Supported File Formats:**
- `.env` files (KEY=value format)
- YAML files with structured data
- JSON files with key-value pairs

### `classdock secrets list`

List secrets across repositories and assignments.

```bash
# List all secrets (names only)
classdock secrets list

# List for specific assignment
classdock secrets list --assignment "database-project"

# List with detailed information
classdock secrets list --detailed

# Export secret inventory
classdock secrets list --output secrets-inventory.json
```

**Options:**
- `--assignment NAME`: Filter by assignment
- `--detailed`: Include metadata (creation date, last updated)
- `--format FORMAT`: Output format (table, json, yaml)
- `--output FILE`: Save to file
- `--show-repos`: Include repository-level details

### `classdock secrets remove`

Remove secrets from repositories.

```bash
# Remove specific secret
classdock secrets remove --name "OLD_API_KEY"

# Remove all secrets for assignment
classdock secrets remove --assignment "completed-project" --all

# Remove secrets matching pattern
classdock secrets remove --pattern "TEMP_*"

# Remove with confirmation
classdock secrets remove --name "CRITICAL_KEY" --confirm
```

**Options:**
- `--name NAME`: Specific secret name
- `--assignment NAME`: Target assignment
- `--pattern GLOB`: Pattern matching secret names
- `--all`: Remove all secrets (use with caution)
- `--confirm`: Require confirmation
- `--dry-run`: Preview deletions

### `classdock secrets rotate`

Rotate secrets across repositories with new values.

```bash
# Rotate specific secret
classdock secrets rotate --name "DATABASE_PASSWORD"

# Rotate from new file
classdock secrets rotate --secrets-file new-credentials.env

# Rotate with backup
classdock secrets rotate --name "API_KEY" --backup

# Schedule rotation
classdock secrets rotate --schedule weekly
```

**Options:**
- `--name NAME`: Secret to rotate
- `--assignment NAME`: Target assignment
- `--secrets-file FILE`: New secret values
- `--backup`: Create backup before rotation
- `--schedule FREQUENCY`: Schedule automatic rotation
- `--notify`: Send notifications on completion

### `classdock secrets validate`

Validate secret distribution and integrity.

```bash
# Validate all secrets
classdock secrets validate

# Validate specific assignment
classdock secrets validate --assignment "secure-app"

# Validate with health check
classdock secrets validate --health-check

# Generate validation report
classdock secrets validate --report validation.html
```

**Options:**
- `--assignment NAME`: Target assignment
- `--health-check`: Perform comprehensive validation
- `--report FILE`: Generate HTML report
- `--fix`: Automatically fix detected issues
- `--strict`: Enable strict validation rules

### `classdock secrets sync`

Synchronize secrets across repositories to ensure consistency.

```bash
# Sync all secrets
classdock secrets sync

# Sync specific assignment
classdock secrets sync --assignment "team-project"

# Sync from master source
classdock secrets sync --source master-secrets.env

# Sync with conflict resolution
classdock secrets sync --resolve-conflicts
```

**Options:**
- `--assignment NAME`: Target assignment
- `--source FILE`: Master secret source
- `--resolve-conflicts`: Automatic conflict resolution
- `--exclude REPOS`: Exclude specific repositories
- `--parallel COUNT`: Parallel sync operations

## Configuration

Secret management uses configuration for security and distribution settings:

```yaml
# secrets.conf
secrets:
  encryption:
    enabled: true
    algorithm: "AES-256-GCM"
    key_source: "environment"
  
  distribution:
    batch_size: 10
    retry_count: 3
    timeout_seconds: 30
  
  validation:
    required_secrets:
      - "API_KEY"
      - "DATABASE_URL"
    pattern_validation: true
    
  rotation:
    schedule: "monthly"
    backup_enabled: true
    notification_webhook: "${WEBHOOK_URL}"

github:
  organization: "my-classroom"
  token: "${GITHUB_TOKEN}"
```

## Security Best Practices

### Secret Storage

```bash
# Use environment variables for sensitive data
export API_KEY="your-secret-key"
classdock secrets add --name "API_KEY"

# Store secrets in encrypted files
classdock secrets add --secrets-file encrypted-secrets.env.gpg

# Use secure secret sources
classdock secrets add --source vault://secrets/api-keys
```

### Access Control

```bash
# Limit secret access by assignment
classdock secrets add \
  --assignment "senior-capstone" \
  --name "PRODUCTION_KEY" \
  --restricted

# Audit secret access
classdock secrets list \
  --detailed \
  --audit-log secrets-audit.log
```

### Rotation Strategy

```bash
# Setup automatic rotation
classdock secrets rotate \
  --schedule monthly \
  --backup \
  --notify

# Emergency rotation
classdock secrets rotate \
  --name "COMPROMISED_KEY" \
  --immediate \
  --notify-urgent
```

## Integration

Secret management integrates with:

- **[Assignment Commands](assignments.md)**: Assignment-scoped secret distribution
- **[Repository Commands](repositories.md)**: Repository-level secret management  
- **[Automation](automation.md)**: Scheduled secret operations

## Examples

### Assignment Secret Setup

```bash
# 1. Prepare secrets file
cat > api-project-secrets.env << EOF
API_KEY=prod-api-key-12345
DATABASE_URL=postgresql://user:pass@host/db
WEBHOOK_SECRET=webhook-secret-abc123
EOF

# 2. Distribute to all assignment repositories
classdock secrets add \
  --assignment "api-integration-project" \
  --secrets-file api-project-secrets.env \
  --confirm

# 3. Validate distribution
classdock secrets validate \
  --assignment "api-integration-project" \
  --report validation.html

# 4. Monitor secret status
classdock secrets list \
  --assignment "api-integration-project" \
  --detailed
```

### Secret Rotation Workflow

```bash
# 1. Generate new API keys (external process)
./generate-new-api-keys.sh > new-keys.env

# 2. Backup existing secrets
classdock secrets list \
  --assignment "production-app" \
  --output backup-$(date +%Y%m%d).json

# 3. Rotate secrets
classdock secrets rotate \
  --assignment "production-app" \
  --secrets-file new-keys.env \
  --backup

# 4. Validate rotation
classdock secrets validate \
  --assignment "production-app" \
  --health-check
```

### Emergency Secret Management

```bash
# Immediate secret removal (security incident)
classdock secrets remove \
  --name "COMPROMISED_KEY" \
  --all-assignments \
  --immediate \
  --confirm

# Emergency rotation with notification
classdock secrets rotate \
  --name "CRITICAL_SECRET" \
  --immediate \
  --notify-urgent \
  --backup

# Audit secret access
classdock secrets list \
  --detailed \
  --audit-trail \
  --format json > security-audit.json
```

## Secret File Formats

### Environment File (.env)

```bash
# api-keys.env
API_KEY=your-api-key-here
DATABASE_URL=postgresql://localhost/mydb
REDIS_URL=redis://localhost:6379
WEBHOOK_SECRET=my-webhook-secret
```

### YAML Format

```yaml
# secrets.yaml
secrets:
  api:
    key: "your-api-key"
    endpoint: "https://api.example.com"
  database:
    url: "postgresql://localhost/mydb"
    password: "secure-password"
  external:
    webhook_secret: "webhook-secret"
```

### JSON Format

```json
{
  "API_KEY": "your-api-key",
  "DATABASE_URL": "postgresql://localhost/mydb",
  "WEBHOOK_SECRET": "webhook-secret",
  "ENCRYPTION_KEY": "encryption-key-here"
}
```

## Troubleshooting

### Common Issues

**Permission Errors:**
```bash
# Check repository permissions
classdock auth check --permissions secrets

# Verify organization access
classdock repos list --assignment "target-assignment"
```

**Distribution Failures:**
```bash
# Retry failed distributions
classdock secrets sync \
  --assignment "failed-assignment" \
  --retry-failed

# Check individual repository status
classdock secrets validate \
  --assignment "target" \
  --detailed
```

**Validation Errors:**
```bash
# Fix secret validation issues
classdock secrets validate \
  --assignment "problem-assignment" \
  --fix \
  --verbose

# Manual secret verification
classdock secrets list \
  --assignment "problem-assignment" \
  --show-repos
```

### Security Troubleshooting

```bash
# Audit secret access
classdock secrets list \
  --detailed \
  --audit-log security.log

# Check for exposed secrets
classdock secrets validate \
  --security-scan \
  --report security-report.html

# Emergency cleanup
classdock secrets remove \
  --pattern "TEMP_*" \
  --all-assignments \
  --force
```

## Advanced Features

### Encrypted Secret Storage

```bash
# Store secrets with encryption
classdock secrets add \
  --secrets-file encrypted-secrets.gpg \
  --decrypt-with gpg

# Use external secret managers
classdock secrets add \
  --source vault://secret/classroom \
  --assignment "secure-project"
```

### Conditional Secret Distribution

```bash
# Distribute secrets based on conditions
classdock secrets add \
  --assignment "advanced-class" \
  --condition "student_level=advanced" \
  --secrets-file advanced-secrets.env
```

### Secret Templates

```bash
# Use secret templates
classdock secrets add \
  --template api-project-template \
  --assignment "new-api-project" \
  --substitute student_name={username}
```

## Best Practices

1. **Security**:
   - Never commit secrets to version control
   - Use environment variables for local development
   - Implement regular secret rotation
   - Monitor secret access and usage

2. **Organization**:
   - Use consistent naming conventions
   - Document secret purposes and requirements
   - Maintain secret inventories
   - Plan for secret lifecycle management

3. **Automation**:
   - Automate secret rotation where possible
   - Set up monitoring and alerting
   - Use backup strategies for critical secrets
   - Implement audit trails

4. **Distribution**:
   - Test secret distribution in staging environments
   - Use batch operations for efficiency
   - Implement rollback procedures
   - Validate secret integrity after distribution

## See Also

- [Assignment Commands](assignments.md)
- [Repository Commands](repositories.md)
- [Automation Commands](automation.md)
- [Security Best Practices](../development/security.md)
