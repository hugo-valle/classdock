# Automation Suite - Comprehensive GitHub Classroom Management

This document describes the complete automation suite for managing GitHub Classroom assignments through the modern Python CLI interface.

## 🎯 Overview

The automation suite provides instructors with powerful tools to:

- **Automated Repository Discovery** - Find student repositories from GitHub Classroom
- **Batch Secret Management** - Distribute secrets across multiple repositories
- **Student Assistance Tools** - Help students with repository issues and conflicts
- **Permission Management** - Fix access issues through intelligent permission cycling
- **Template Synchronization** - Keep assignment templates updated across classrooms
- **Scheduling & Automation** - Set up automated workflows with cron jobs

## 📦 Installation

```bash
# Install from PyPI
pip install classdock

# Verify installation
classdock --help
```

## 🚀 Quick Start

### 1. Setup Assignment Configuration

```bash
# Interactive setup wizard
classdock assignments setup

# This creates assignment.conf with your settings
```

### 2. Repository Discovery

```bash
# Discover all student repositories
classdock repos fetch --config assignment.conf

# Fetch with filtering
classdock repos fetch --config assignment.conf --exclude "template,demo"
```

### 3. Secret Management

```bash
# Add secrets to all student repositories
classdock secrets add --config assignment.conf

# Remove secrets from repositories
classdock secrets remove --config assignment.conf --secrets "OLD_TOKEN"

# List existing secrets
classdock secrets list --config assignment.conf
```

### 4. Complete Automation Workflow

```bash
# Run complete automated workflow
classdock assignments orchestrate --config assignment.conf

# Preview changes first
classdock --dry-run assignments orchestrate --config assignment.conf
```

## 🔧 Automation Commands

### Assignment Management

```bash
# Setup new assignment
classdock assignments setup

# Orchestrate complete workflow
classdock assignments orchestrate [OPTIONS]

# Manage assignment templates
classdock assignments manage [OPTIONS]
```

### Repository Operations

```bash
# Fetch student repositories
classdock repos fetch [OPTIONS]

# Add collaborators to repositories
classdock repos collaborator add [OPTIONS]

# Remove collaborators from repositories
classdock repos collaborator remove [OPTIONS]
```

### Secret Management

```bash
# Add secrets to repositories
classdock secrets add [OPTIONS]

# Remove secrets from repositories
classdock secrets remove [OPTIONS]

# List secrets in repositories
classdock secrets list [OPTIONS]
```

### Automation & Scheduling

```bash
# Setup automated scheduling
classdock automation scheduler setup [OPTIONS]

# Run batch operations
classdock automation batch [OPTIONS]
```

## ⚙️ Configuration

### Assignment Configuration File

Create `assignment.conf` with your assignment settings:

```bash
# GitHub Classroom Configuration
CLASSROOM_URL="https://classroom.github.com/classrooms/123/assignments/456"
TEMPLATE_REPO_URL="https://github.com/instructor/assignment-template"
ASSIGNMENT_FILE="homework.py"

# Authentication
GITHUB_TOKEN_FILE="github_token.txt"

# Secret Management
SECRETS_LIST="API_KEY,DATABASE_URL,GRADING_TOKEN"

# Repository Filtering
EXCLUDE_REPOS="template,example,demo,instructor-solution"
INSTRUCTOR_REPOS="instructor-*"

# GitHub Enterprise Support (optional)
GITHUB_HOSTS="github.enterprise.com"
```

### Environment Variables

Override configuration with environment variables:

```bash
# GitHub token
export GITHUB_TOKEN="ghp_your_token_here"

# Custom GitHub hosts
export GITHUB_HOSTS="github.enterprise.com,git.company.internal"

# Assignment file override
export ASSIGNMENT_FILE="main.cpp"

# Run commands with overrides
classdock assignments orchestrate
```

## 🎯 Advanced Automation

### Batch Processing

Process multiple assignments with automation:

```bash
# Process multiple assignment configurations
for config in assignment-*.conf; do
    echo "Processing $config..."
    classdock --verbose assignments orchestrate --config "$config"
done
```

### Scheduled Automation

Set up automated workflows with cron:

```bash
# Setup automated scheduling
classdock automation scheduler setup --config assignment.conf

# This creates cron jobs for:
# - Regular repository sync
# - Secret updates
# - Student assistance checks
```

### Enterprise Integration

Configure for enterprise GitHub environments:

```bash
# Enterprise configuration
GITHUB_HOSTS="github.enterprise.com,git.company.internal"
GITHUB_TOKEN_FILE="enterprise_token.txt"

# Run with enterprise settings
classdock assignments orchestrate --config enterprise-assignment.conf
```

## 🛡️ Security & Best Practices

### Token Management

```bash
# Secure token storage
echo "ghp_your_token_here" > github_token.txt
chmod 600 github_token.txt

# Use token file in configuration
GITHUB_TOKEN_FILE="github_token.txt"
```

### Repository Filtering

```bash
# Exclude instructor and template repositories
EXCLUDE_REPOS="template,instructor-solution,demo,example"

# Include only specific patterns
INSTRUCTOR_REPOS="instructor-*,solution-*"
```

### Dry-Run Testing

Always test changes before applying:

```bash
# Preview all changes
classdock --dry-run assignments orchestrate --config assignment.conf

# Preview specific operations
classdock --dry-run secrets add --config assignment.conf
classdock --dry-run repos fetch --config assignment.conf
```

## 📊 Monitoring & Logging

### Verbose Output

Enable detailed logging for monitoring:

```bash
# Verbose mode for debugging
classdock --verbose assignments orchestrate --config assignment.conf

# Combine with dry-run for detailed preview
classdock --dry-run --verbose assignments orchestrate --config assignment.conf
```

### Log Analysis

Monitor automation workflows:

```bash
# Check recent automation runs
classdock automation batch --config assignment.conf --verbose

# Review scheduled task logs
classdock automation scheduler status --config assignment.conf
```

## 🔄 Workflow Examples

### Weekly Assignment Update

```bash
#!/bin/bash
# Weekly automation workflow

CONFIG="assignment.conf"

echo "Starting weekly assignment update..."

# 1. Sync template changes
classdock assignments manage --config "$CONFIG"

# 2. Update secrets if needed
classdock secrets add --config "$CONFIG"

# 3. Check student repositories
classdock repos fetch --config "$CONFIG"

# 4. Run complete orchestration
classdock assignments orchestrate --config "$CONFIG"

echo "Weekly update complete!"
```

### Emergency Secret Rotation

```bash
#!/bin/bash
# Emergency secret rotation

CONFIG="assignment.conf"
OLD_SECRET="COMPROMISED_TOKEN"
NEW_SECRET="NEW_SECURE_TOKEN"

echo "Starting emergency secret rotation..."

# 1. Remove old secret
classdock secrets remove --config "$CONFIG" --secrets "$OLD_SECRET"

# 2. Add new secret
SECRETS_LIST="$NEW_SECRET" classdock secrets add --config "$CONFIG"

echo "Secret rotation complete!"
```

### Midterm Repository Preparation

```bash
#!/bin/bash
# Midterm repository preparation

echo "Preparing repositories for midterm..."

# 1. Create midterm configuration
classdock assignments setup

# 2. Discover all student repositories
classdock repos fetch --config midterm-assignment.conf

# 3. Add grading tokens
classdock secrets add --config midterm-assignment.conf

# 4. Set up automated grading
classdock automation scheduler setup --config midterm-assignment.conf

echo "Midterm preparation complete!"
```

## 🆘 Troubleshooting

### Common Issues

1. **Authentication Failures**:
   ```bash
   # Check token permissions
   classdock --verbose repos fetch --config assignment.conf
   ```

2. **Repository Discovery Issues**:
   ```bash
   # Verify classroom URL format
   classdock --dry-run repos fetch --config assignment.conf
   ```

3. **Secret Management Errors**:
   ```bash
   # Test with single repository
   classdock --verbose secrets add --config assignment.conf
   ```

### Debug Mode

```bash
# Maximum debugging information
classdock --verbose --dry-run assignments orchestrate --config assignment.conf
```

## 📚 Related Documentation

- **[Assignment Orchestrator](ASSIGNMENT-ORCHESTRATOR.md)** - Complete workflow automation
- **[Secrets Management](SECRETS-MANAGEMENT.md)** - Detailed secret handling
- **[Cron Automation](CRON-AUTOMATION.md)** - Scheduled task automation
- **[Main CLI Reference](../README.md)** - Complete command documentation

---

The Automation Suite provides comprehensive tools for efficient GitHub Classroom management through modern Python CLI commands.
