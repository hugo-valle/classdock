# Quick Start

Get started with ClassDock in 5 minutes.

## 🎯 Overview

This guide will walk you through:

1. Setting up your first assignment
2. Discovering student repositories 
3. Managing secrets
4. Running automated workflows

## 📋 Prerequisites

- [ClassDock installed](installation.md)
- GitHub personal access token
- GitHub Classroom assignment URL

## 🚀 Step 1: Assignment Setup

### Interactive Setup

Use the interactive setup wizard to create your first assignment:

```bash
# Run interactive setup
classdock assignments setup
```

The wizard will guide you through:

- GitHub Classroom URL
- Template repository URL
- Assignment file name
- Secret requirements
- Authentication setup

### Manual Configuration

Alternatively, create an `assignment.conf` file manually:

```bash
# Create assignment.conf
cat > assignment.conf << 'EOF'
# GitHub Classroom Configuration
CLASSROOM_URL="https://classroom.github.com/classrooms/123/assignments/homework1"
TEMPLATE_REPO_URL="https://github.com/instructor/homework1-template"
ASSIGNMENT_FILE="homework1.py"

# Secret Management (using centralized token manager)
SECRETS_CONFIG="
API_KEY:API key for external service:true
GRADING_TOKEN:Token for automated grading:true
"
EOF

# Set GitHub token (centralized approach)
export GITHUB_TOKEN="ghp_your_token_here"
```

## 🔍 Step 2: Repository Discovery

Discover all student repositories for your assignment:

```bash
# Discover student repositories
classdock repos fetch --config assignment.conf

# Preview without making changes
classdock --dry-run repos fetch --config assignment.conf

# Discover with verbose output
classdock --verbose repos fetch --config assignment.conf
```

This will:

- Parse your classroom URL
- Find all student repositories
- Filter out instructor/template repositories
- Generate a list for batch operations

## 🔐 Step 3: Secret Management

Distribute secrets to all student repositories:

```bash
# Add secrets to all repositories
classdock secrets add --config assignment.conf

# Preview secret distribution
classdock --dry-run secrets add --config assignment.conf

# Add specific secrets only
classdock secrets add --config assignment.conf --secrets "API_KEY"
```

### Setting Secret Values

Set secret values via environment variables:

```bash
# Set secret values
export API_KEY="your_api_key_here"
export GRADING_TOKEN="your_grading_token"

# Distribute secrets
classdock secrets add --config assignment.conf
```

## 🔄 Step 4: Complete Workflow

Run the complete automated workflow:

```bash
# Run complete orchestration
classdock assignments orchestrate --config assignment.conf

# Preview complete workflow
classdock --dry-run assignments orchestrate --config assignment.conf

# Run with detailed logging
classdock --verbose assignments orchestrate --config assignment.conf
```

This orchestrates:

1. Configuration validation
2. Repository discovery
3. Secret distribution
4. Template synchronization
5. Access management

## 📊 Step 5: Verify Results

Check that everything worked correctly:

```bash
# List distributed secrets
classdock secrets list --config assignment.conf

# Check repository status
classdock repos fetch --config assignment.conf

# View detailed status
classdock --verbose assignments orchestrate --config assignment.conf --dry-run
```

## 🎯 Common Workflows

### Daily Assignment Management

```bash
# Morning workflow: Check and update
classdock assignments orchestrate --config assignment.conf
```

### Emergency Secret Rotation

```bash
# Remove old secret
classdock secrets remove --config assignment.conf --secrets "OLD_TOKEN"

# Add new secret
NEW_TOKEN="new_value" classdock secrets add --config assignment.conf --secrets "NEW_TOKEN"
```

### Multiple Assignment Processing

```bash
# Process multiple assignments
for config in assignment-*.conf; do
    echo "Processing $config..."
    classdock assignments orchestrate --config "$config"
done
```

## 🛡️ Best Practices

### Security

- **Always use `--dry-run`** to preview changes
- **Store tokens securely** in files with restricted permissions
- **Use environment variables** for sensitive values
- **Regularly rotate** API tokens and secrets

### Configuration

- **Version control** your assignment configurations
- **Use descriptive filenames** like `midterm-assignment.conf`
- **Test with single student** before batch operations
- **Document custom settings** in your assignment README

### Monitoring

- **Use `--verbose`** for debugging issues
- **Check logs** regularly for errors
- **Monitor API rate limits** with large classrooms
- **Validate results** after batch operations

## 🆘 Troubleshooting

### Common Issues

**Authentication Errors**:
```bash
# Check token permissions
classdock --verbose repos fetch --config assignment.conf
```

**Repository Not Found**:
```bash
# Verify classroom URL format
classdock --dry-run repos fetch --config assignment.conf
```

**Secret Distribution Failures**:
```bash
# Test with dry-run first
classdock --dry-run secrets add --config assignment.conf
```

### Getting Help

- Use `--help` with any command for detailed usage
- Check the [CLI Reference](../cli/overview.md) for complete documentation
- Enable `--verbose` mode for detailed error information

## 🚀 Next Steps

- [Configuration Guide](configuration.md) - Advanced configuration options
- [CLI Reference](../cli/overview.md) - Complete command documentation  
- [Workflow Automation](../workflows/assignment-orchestrator.md) - Automate your processes
- [Development Guide](../development/contributing.md) - Contribute to the project
