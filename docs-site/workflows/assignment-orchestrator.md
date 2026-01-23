# Assignment Orchestrator - Workflow Automation

The Assignment Orchestrator provides comprehensive workflow automation for GitHub Classroom assignments through the modern Python CLI interface.

## 🎯 Overview

The orchestrator automates the complete assignment lifecycle through a single command:

1. **Template Synchronization** - Updates GitHub Classroom with latest template changes
2. **Repository Discovery** - Finds all student repositories from the classroom
3. **Secret Management** - Distributes/updates secrets across all student repositories
4. **Student Assistance** - Runs student help and support tools
5. **Collaborator Management** - Manages repository access and permissions

## 📦 Installation

```bash
# Install from PyPI
pip install classdock

# Verify installation
classdock --help
```

## 🚀 Quick Start

### 1. Interactive Setup

Create assignment configuration interactively:

```bash
# Run interactive setup wizard
classdock assignments setup

# This creates an assignment.conf file with your settings
```

### 2. Complete Workflow Orchestration

```bash
# Run complete orchestrated workflow
classdock assignments orchestrate --config assignment.conf

# Preview what would be done (dry-run)
classdock --dry-run assignments orchestrate --config assignment.conf

# Run with verbose output for debugging
classdock --verbose assignments orchestrate --config assignment.conf
```

## ⚙️ Configuration

### Assignment Configuration File

The `assignment.conf` file contains all settings for your assignment:

```bash
# GitHub Classroom Configuration
CLASSROOM_URL="https://classroom.github.com/classrooms/123/assignments/456"
TEMPLATE_REPO_URL="https://github.com/instructor/assignment-template"
ASSIGNMENT_FILE="homework.py"

# Authentication
GITHUB_TOKEN_FILE="github_token.txt"

# Secret Management
SECRETS_LIST="API_KEY,DATABASE_URL,SECRET_TOKEN"

# Repository Filtering
EXCLUDE_REPOS="template,example,demo"
INSTRUCTOR_REPOS="instructor-solution"
```

### Environment Variable Overrides

Override configuration with environment variables:

```bash
# Set custom GitHub hosts
export GITHUB_HOSTS="github.enterprise.com"

# Set GitHub token directly
export GITHUB_TOKEN="ghp_your_token_here"

# Run orchestrator
classdock assignments orchestrate
```

## 🔧 Command Options

### Basic Usage

```bash
# Interactive orchestration with prompts
classdock assignments orchestrate

# Use specific configuration file
classdock assignments orchestrate --config my-assignment.conf

# Preview without executing changes
classdock --dry-run assignments orchestrate

# Enable detailed logging
classdock --verbose assignments orchestrate
```

### Workflow Components

The orchestrator runs these components in sequence:

1. **Configuration Validation** - Validates all settings and URLs
2. **Template Sync** - Updates GitHub Classroom template
3. **Repository Discovery** - Finds student repositories
4. **Secret Distribution** - Adds/updates repository secrets
5. **Access Management** - Manages collaborator permissions

## 🔄 Workflow Steps

### Step 1: Assignment Setup

```bash
# Create new assignment configuration
classdock assignments setup

# Or manage existing assignment
classdock assignments manage --config assignment.conf
```

### Step 2: Repository Operations

```bash
# Fetch student repositories
classdock repos fetch --config assignment.conf

# Manage collaborators
classdock repos collaborator add --config assignment.conf
```

### Step 3: Secret Management

```bash
# Add secrets to all repositories
classdock secrets add --config assignment.conf

# List existing secrets
classdock secrets list --config assignment.conf
```

### Step 4: Complete Orchestration

```bash
# Run all steps together
classdock assignments orchestrate --config assignment.conf
```

## 🎯 Advanced Features

### Batch Operations

Process multiple assignments with different configurations:

```bash
# Process multiple assignments
for config in assignment-*.conf; do
    classdock --verbose assignments orchestrate --config "$config"
done
```

### Automation Integration

Integrate with scheduling systems:

```bash
# Setup automated scheduling
classdock automation scheduler setup --config assignment.conf

# Run batch operations
classdock automation batch --config assignment.conf
```

### Enterprise GitHub Support

Configure for GitHub Enterprise or custom hosts:

```bash
# Set enterprise hosts in configuration
GITHUB_HOSTS="github.enterprise.com,git.company.internal"

# Or via environment variable
export GITHUB_HOSTS="github.enterprise.com"
classdock assignments orchestrate
```

## 🛡️ Security & Best Practices

### Token Management

- Store tokens securely using `GITHUB_TOKEN_FILE`
- Use environment variables for sensitive information
- Regularly rotate API tokens
- Limit token permissions to required scopes

### Repository Access

- Use `--dry-run` to preview changes before execution
- Configure repository filtering to exclude instructor repos
- Monitor access logs for unauthorized changes
- Implement proper backup procedures

### Configuration Security

```bash
# Secure configuration file permissions
chmod 600 assignment.conf

# Use environment variables for sensitive data
export GITHUB_TOKEN="$(cat secure_token.txt)"
classdock assignments orchestrate --config assignment.conf
```

## 🔍 Troubleshooting

### Common Issues

1. **Authentication Errors**:
   ```bash
   # Verify token permissions
   classdock --verbose assignments orchestrate
   ```

2. **Repository Not Found**:
   ```bash
   # Check URL format and access
   classdock repos fetch --config assignment.conf --verbose
   ```

3. **Secret Distribution Failures**:
   ```bash
   # Test with single repository first
   classdock --dry-run secrets add --config assignment.conf
   ```

### Debug Mode

Enable comprehensive logging for troubleshooting:

```bash
# Maximum verbosity
classdock --verbose assignments orchestrate --config assignment.conf

# Dry-run with detailed output
classdock --dry-run --verbose assignments orchestrate --config assignment.conf
```

## 📚 Related Documentation

- **[Main CLI Reference](../README.md#command-reference)** - Complete command documentation
- **[Secrets Management](secrets-management.md)** - Detailed secret handling guide
- **[Repository Operations](../README.md#repository-operations)** - Repository management commands
- **[Configuration Guide](../README.md#configuration)** - Configuration file setup

---

The Assignment Orchestrator provides a comprehensive, automated solution for managing GitHub Classroom assignments through the modern Python CLI interface.
