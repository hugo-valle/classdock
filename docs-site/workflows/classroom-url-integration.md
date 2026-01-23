# GitHub Classroom URL Integration

## 🎯 Overview

ClassDock provides seamless integration with GitHub Classroom URLs, making it convenient to manage classroom assignments directly from the GitHub Classroom interface.

## 📦 Installation

```bash
# Install from PyPI
pip install classdock

# Verify installation
classdock --help
```

## 🚀 Classroom URL Integration

### Direct URL Usage

Use GitHub Classroom URLs directly in your configuration:

```bash
# GitHub Classroom Configuration
CLASSROOM_URL="https://classroom.github.com/classrooms/123/assignments/cs6600-homework1"
TEMPLATE_REPO_URL="https://github.com/instructor/cs6600-homework1-template"
ASSIGNMENT_FILE="homework.py"
```

### URL Parsing and Assignment Detection

The CLI automatically extracts assignment information from classroom URLs:

- **Input URL**: `https://classroom.github.com/classrooms/123/assignments/cs6600-homework1`
- **Extracted Assignment**: `cs6600-homework1`
- **Search Pattern**: `cs6600-homework1-*` (for student repositories)

## 🔧 Command Integration

### Repository Discovery

```bash
# Fetch repositories using classroom URL
classdock repos fetch --config assignment.conf

# The CLI automatically:
# 1. Parses the CLASSROOM_URL from configuration
# 2. Extracts assignment name
# 3. Searches for matching student repositories
```

### Assignment Setup

```bash
# Interactive setup with classroom URL
classdock assignments setup

# The wizard will prompt for:
# - GitHub Classroom URL
# - Template repository URL
# - Assignment file name
# - Secret requirements
```

### Complete Workflow

```bash
# Run complete workflow with classroom URL integration
classdock assignments orchestrate --config assignment.conf

# This automatically:
# 1. Validates classroom URL format
# 2. Discovers student repositories
# 3. Manages secrets and permissions
# 4. Synchronizes templates
```

## ⚙️ Configuration Examples

### Basic Assignment Configuration

```bash
# assignment.conf
CLASSROOM_URL="https://classroom.github.com/classrooms/206604610/assignments/cs6600-m1-homework1"
TEMPLATE_REPO_URL="https://github.com/wsu-ml-dl/cs6600-m1-homework1-template"
ASSIGNMENT_FILE="homework1.py"
GITHUB_TOKEN_FILE="github_token.txt"
SECRETS_LIST="API_KEY,GRADING_TOKEN"
```

### Multiple Assignment Management

```bash
# assignment-hw1.conf
CLASSROOM_URL="https://classroom.github.com/classrooms/123/assignments/homework1"
TEMPLATE_REPO_URL="https://github.com/instructor/homework1-template"

# assignment-hw2.conf  
CLASSROOM_URL="https://classroom.github.com/classrooms/123/assignments/homework2"
TEMPLATE_REPO_URL="https://github.com/instructor/homework2-template"

# Process multiple assignments
for config in assignment-*.conf; do
    classdock assignments orchestrate --config "$config"
done
```

### Enterprise GitHub Classroom

```bash
# enterprise-assignment.conf
CLASSROOM_URL="https://github.enterprise.com/classrooms/456/assignments/project1"
TEMPLATE_REPO_URL="https://github.enterprise.com/department/project1-template"
GITHUB_HOSTS="github.enterprise.com"
GITHUB_TOKEN_FILE="enterprise_token.txt"
```

## 🎯 Advanced URL Features

### URL Validation

The CLI performs comprehensive URL validation:

```bash
# Valid classroom URL patterns:
# https://classroom.github.com/classrooms/{id}/assignments/{name}
# https://github.enterprise.com/classrooms/{id}/assignments/{name}

# Automatic validation during setup
classdock assignments setup

# Manual validation
classdock --dry-run repos fetch --config assignment.conf
```

### Assignment Name Extraction

Automatic assignment name extraction supports various patterns:

```bash
# Standard assignment names
cs6600-homework1                    # → cs6600-homework1-*
final-project                       # → final-project-*
midterm-exam-2024                  # → midterm-exam-2024-*

# Special characters handled
data-structures-hw_1               # → data-structures-hw_1-*
ml-assignment.part2                # → ml-assignment.part2-*
```

### Repository Pattern Matching

The CLI intelligently matches student repositories:

```bash
# From assignment "cs6600-homework1", finds:
cs6600-homework1-student1          # ✅ Match
cs6600-homework1-student2          # ✅ Match
cs6600-homework1-template          # ❌ Excluded (template)
cs6600-homework1-instructor        # ❌ Excluded (instructor)
different-assignment-student1      # ❌ No match
```

## 🛠️ Workflow Integration

### Complete Assignment Lifecycle

```bash
# 1. Setup assignment with classroom URL
classdock assignments setup
# Enter classroom URL when prompted

# 2. Validate configuration
classdock --dry-run assignments orchestrate --config assignment.conf

# 3. Execute complete workflow
classdock assignments orchestrate --config assignment.conf
```

### Batch Classroom Management

```bash
#!/bin/bash
# Manage multiple classroom assignments

CLASSROOM_URLS=(
    "https://classroom.github.com/classrooms/123/assignments/hw1"
    "https://classroom.github.com/classrooms/123/assignments/hw2"
    "https://classroom.github.com/classrooms/123/assignments/final"
)

for url in "${CLASSROOM_URLS[@]}"; do
    echo "Processing classroom: $url"
    
    # Create temporary config
    cat > temp-config.conf << EOF
CLASSROOM_URL="$url"
TEMPLATE_REPO_URL="https://github.com/instructor/template"
ASSIGNMENT_FILE="main.py"
GITHUB_TOKEN_FILE="github_token.txt"
EOF

    # Process assignment
    classdock assignments orchestrate --config temp-config.conf
    
    # Cleanup
    rm temp-config.conf
done
```

## 🔍 Troubleshooting

### URL Format Issues

```bash
# Check URL format
classdock --verbose repos fetch --config assignment.conf

# Common issues:
# ❌ Missing /assignments/ in URL
# ❌ Incorrect classroom ID
# ❌ Special characters in assignment name
# ❌ Wrong GitHub host (enterprise vs public)
```

### Repository Discovery Problems

```bash
# Debug repository discovery
classdock --dry-run --verbose repos fetch --config assignment.conf

# Check:
# 1. Assignment name extraction
# 2. Repository search patterns
# 3. Access permissions
# 4. Repository filtering rules
```

### Authentication Issues

```bash
# Verify GitHub authentication
classdock --verbose assignments orchestrate --config assignment.conf

# Check:
# 1. Token permissions
# 2. Organization access
# 3. Classroom membership
# 4. Repository visibility
```

## 📚 Related Documentation

- **[Main CLI Reference](../README.md)** - Complete command documentation
- **[Assignment Orchestrator](assignment-orchestrator.md)** - Workflow automation
- **[Repository Operations](../README.md#repository-operations)** - Repository management
- **[Configuration Guide](../README.md#configuration)** - Configuration setup

## 💡 Tips & Best Practices

### URL Management

- **Use consistent naming**: Keep assignment names consistent across semesters
- **Validate URLs early**: Use `--dry-run` to catch URL issues before execution
- **Document patterns**: Maintain documentation of URL patterns for your organization

### Automation Integration

- **Store URLs in configs**: Keep classroom URLs in version-controlled configuration files
- **Use environment variables**: Override URLs for different environments (dev/staging/prod)
- **Batch processing**: Process multiple classroom assignments efficiently

### Security Considerations

- **Verify permissions**: Ensure tokens have appropriate classroom access
- **Monitor access**: Track repository access and modifications
- **Audit regularly**: Review classroom integrations and permissions

---

GitHub Classroom URL integration makes managing assignments seamless and efficient through the modern Python CLI interface.
