# CLI Overview

ClassDock provides a comprehensive command-line interface organized into logical command groups.

## 🏗️ Command Structure

The CLI is organized into four main command groups:

```bash
classdock [GLOBAL_OPTIONS] COMMAND [ARGS]...
```

### Command Groups

| Group | Purpose | Commands |
|-------|---------|----------|
| `assignments` | Assignment setup and orchestration | `setup`, `orchestrate`, `manage` |
| `repos` | Repository operations | `fetch`, `collaborator` |
| `secrets` | Secret and token management | `add`, `remove`, `list` |
| `automation` | Scheduling and batch processing | `scheduler`, `batch` |

### Legacy Commands

For backward compatibility:

| Command | Purpose | Modern Equivalent |
|---------|---------|-------------------|
| `setup` | Interactive assignment setup | `assignments setup` |
| `run` | Complete workflow execution | `assignments orchestrate` |
| `version` | Show version information | `version` |

## ⚙️ Global Options

Global options apply to all commands:

| Option | Short | Description | Example |
|--------|-------|-------------|---------|
| `--dry-run` | | Preview actions without executing | `classdock --dry-run assignments orchestrate` |
| `--verbose` | | Enable detailed logging | `classdock --verbose repos fetch` |
| `--config FILE` | | Use custom configuration file | `classdock --config my.conf secrets add` |
| `--help` | | Show help information | `classdock --help` |

## 📋 Quick Reference

### Assignment Management

```bash
# Interactive setup
classdock assignments setup

# Run complete workflow
classdock assignments orchestrate [--config FILE]

# Manage templates
classdock assignments manage [--config FILE]
```

### Repository Operations

```bash
# Discover student repositories
classdock repos fetch [--config FILE]

# Add collaborators
classdock repos collaborator add [--config FILE]

# Remove collaborators
classdock repos collaborator remove [--config FILE]
```

### Secret Management

```bash
# Add secrets to repositories
classdock secrets add [--config FILE] [--secrets LIST]

# Remove secrets
classdock secrets remove [--config FILE] [--secrets LIST]

# List existing secrets
classdock secrets list [--config FILE]
```

### Automation & Scheduling

```bash
# Setup automated scheduling
classdock automation scheduler setup [--config FILE]

# Check scheduler status
classdock automation scheduler status

# Run batch operations
classdock automation batch [--config FILE]
```

## 🔧 Configuration

All commands support configuration via:

1. **Configuration file** (default: `assignment.conf`)
2. **Environment variables**
3. **Command-line options**

### Configuration File Example

```bash
# assignment.conf
CLASSROOM_URL="https://classroom.github.com/classrooms/123/assignments/homework1"
TEMPLATE_REPO_URL="https://github.com/instructor/homework1-template"
ASSIGNMENT_FILE="homework1.py"
GITHUB_TOKEN_FILE="github_token.txt"
SECRETS_LIST="API_KEY,GRADING_TOKEN"
```

### Environment Variable Overrides

```bash
# Override configuration
export GITHUB_TOKEN="ghp_your_token"
export ASSIGNMENT_FILE="main.cpp"

# Run commands
classdock assignments orchestrate
```

## 💡 Usage Patterns

### Development & Testing

```bash
# Always preview first
classdock --dry-run assignments orchestrate --config assignment.conf

# Use verbose for debugging
classdock --verbose repos fetch --config assignment.conf

# Test with single repository
classdock --dry-run secrets add --config assignment.conf
```

### Production Workflows

```bash
# Complete assignment setup
classdock assignments setup

# Daily orchestration
classdock assignments orchestrate --config assignment.conf

# Emergency secret rotation
classdock secrets remove --config assignment.conf --secrets "OLD_TOKEN"
NEW_TOKEN="value" classdock secrets add --config assignment.conf --secrets "NEW_TOKEN"
```

### Batch Operations

```bash
# Multiple assignments
for config in assignment-*.conf; do
    classdock assignments orchestrate --config "$config"
done

# Specific operations across assignments
classdock secrets add --config hw1.conf
classdock secrets add --config hw2.conf
classdock secrets add --config midterm.conf
```

## 🆘 Help System

### Getting Help

```bash
# Main help
classdock --help

# Command group help
classdock assignments --help
classdock repos --help
classdock secrets --help
classdock automation --help

# Specific command help
classdock assignments orchestrate --help
classdock secrets add --help
```

### Error Messages

The CLI provides informative error messages:

- **Configuration errors**: Invalid file paths, missing required fields
- **Authentication errors**: Invalid tokens, insufficient permissions
- **API errors**: Rate limiting, repository access issues
- **Validation errors**: Invalid URLs, malformed configuration

## 🔍 Debugging

### Verbose Mode

Enable detailed logging for troubleshooting:

```bash
# Verbose output
classdock --verbose assignments orchestrate --config assignment.conf

# Combine with dry-run for detailed preview
classdock --dry-run --verbose assignments orchestrate --config assignment.conf
```

### Log Information

Verbose mode shows:

- Configuration loading and validation
- API calls and responses
- Repository discovery process
- Secret distribution status
- Error details and stack traces

## 📚 Related Documentation

- [Assignments](assignments.md) - Assignment management commands
- [Repositories](repositories.md) - Repository operation commands
- [Secrets](secrets.md) - Secret management commands
- [Automation](automation.md) - Automation and scheduling commands
