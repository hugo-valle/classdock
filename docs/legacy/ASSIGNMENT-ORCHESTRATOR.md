# Assignment Orchestrator - Workflow Automation

The Assignment Orchestrator provides comprehensive workflow automation for GitHub Classroom assignments through the modern Python CLI interface.

## 🎯 Overview

The orchestrator automates the complete assignment lifecycle through a single command:

1. **Template Synchronization** - Updates GitHub Classroom with latest template changes
2. **Repository Discovery** - Finds all student repositories from the classroom
3. **Secret Management** - Distributes/updates secrets across all student repositories
4. **Student Assistance** - Runs student help and support tools
5. **Collaborator Management** - Manages repository access and permissions

## � Installation

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

## ⚙️ Configuration File Format

The `assignment.conf` file uses shell variable syntax and supports:

### Assignment Information
```bash
CLASSROOM_URL="https://classroom.github.com/..."
TEMPLATE_REPO_URL="https://github.com/..."
GITHUB_ORGANIZATION="WSU-ML-DL"
```

### Secret Management
```bash
SECRETS=(
    "SECRET_NAME:token_file.txt:Description"
    "ANOTHER_SECRET:another_token.txt:Another description"
)
SECRET_MAX_AGE_DAYS=90
SECRET_FORCE_UPDATE=false
```

### Workflow Control
```bash
STEP_SYNC_TEMPLATE=true
STEP_DISCOVER_REPOS=true  
STEP_MANAGE_SECRETS=true
STEP_ASSIST_STUDENTS=false
STEP_CYCLE_COLLABORATORS=false
```

### Output Settings
```bash
OUTPUT_DIR="scripts"
STUDENT_REPOS_FILE="student-repos-batch.txt"
DRY_RUN=false
```

## 🛠️ Command Line Options

### Basic Usage
```bash
# Use default configuration
./scripts/assignment-orchestrator.sh

# Use custom configuration file
./scripts/assignment-orchestrator.sh my-assignment.conf
```

### Workflow Control
```bash
# Run only specific step
./scripts/assignment-orchestrator.sh --step secrets

# Skip specific step  
./scripts/assignment-orchestrator.sh --skip sync

# Run collaborator cycling step
./scripts/assignment-orchestrator.sh --step cycle

# Preview mode
./scripts/assignment-orchestrator.sh --dry-run
```

### Automation Options
```bash
# No confirmation prompts
./scripts/assignment-orchestrator.sh --yes

# Verbose output
./scripts/assignment-orchestrator.sh --verbose

# Combined options
./scripts/assignment-orchestrator.sh --dry-run --verbose
```

## ✨ Key Features

### Automatic Setup Integration
- **Smart detection**: Automatically detects missing `assignment.conf` file
- **Interactive setup**: Offers to run setup wizard when configuration is missing
- **Seamless workflow**: Integrates setup as the first step in the orchestration process
- **Automation friendly**: Supports `--yes` flag to auto-confirm setup for CI/CD pipelines

### Intelligent Workflow Management
- **Step-by-step execution**: Runs all automation tools in the correct order
- **Flexible control**: Run individual steps or skip specific steps as needed
- **Preview mode**: Dry-run capability to preview actions before execution
- **Error handling**: Stops on errors to prevent cascade failures

### Configuration-Driven
- **Single source of truth**: All assignment settings in one configuration file
- **Universal file support**: Works with any file type (.py, .cpp, .sql, .md, etc.)
- **Multi-secret support**: Manage multiple tokens and secrets across repositories
- **Customizable workflows**: Enable/disable specific steps based on assignment needs

## 📋 Workflow Steps

### Step 1: Template Synchronization (`sync`)
- Executes `scripts/push-to-classroom.sh`
- Pushes latest template changes to GitHub Classroom
- Ensures all students get updated template content

### Step 2: Repository Discovery (`discover`)
- Executes `scripts/fetch-student-repos.sh`
- Uses classroom URL to find all student repositories
- Generates batch files for subsequent operations
- Creates both complete and students-only repository lists

### Step 3: Secret Management (`secrets`)
- Executes `scripts/add-secrets-to-students.sh` for each configured secret
- Supports multiple secrets with different token files
- Respects age-based update policies
- Can force update all secrets if needed

### Step 4: Student Assistance (`assist`) 
- Executes `scripts/student-update-helper.sh`
- Provides automated assistance for common student issues
- Optional step (disabled by default)

### Step 5: Collaborator Cycling (`cycle`)
- Executes `scripts/cycle-collaborator.sh` with configuration mode
- Fixes repository access issues by cycling collaborator permissions
- Intelligently detects when cycling is needed vs when access is already correct
- Optional step (disabled by default)
- Useful for resolving GitHub Classroom permission glitches

## 🎛️ Advanced Usage

### Multiple Assignments
Create separate configuration files for different assignments:

```bash
# CS6600 Module 1
./scripts/assignment-orchestrator.sh cs6600-m1.conf

# CS6600 Module 2  
./scripts/assignment-orchestrator.sh cs6600-m2.conf

# Final Project
./scripts/assignment-orchestrator.sh final-project.conf
```

### Partial Workflows
Run only specific parts of the workflow:

```bash
# Only sync template (for urgent fixes)
./scripts/assignment-orchestrator.sh --step sync

# Only manage secrets (for token updates)
./scripts/assignment-orchestrator.sh --step secrets

# Only fix repository access issues
./scripts/assignment-orchestrator.sh --step cycle

# Everything except student assistance
./scripts/assignment-orchestrator.sh --skip assist
```

### Development and Testing
```bash
# Test configuration without making changes
./scripts/assignment-orchestrator.sh --dry-run

# Debug configuration issues
./scripts/assignment-orchestrator.sh --verbose --dry-run

# Force execution without prompts (for CI/CD)
./scripts/assignment-orchestrator.sh --yes
```

## 🔧 Integration with Existing Scripts

The orchestrator is designed to work seamlessly with existing scripts:

- **`push-to-classroom.sh`** - Called for template synchronization
- **`fetch-student-repos.sh`** - Called with `--classroom-url` parameter
- **`add-secrets-to-students.sh`** - Called with `--batch` mode for each secret
- **`student-update-helper.sh`** - Called with `--batch` mode for assistance
- **`cycle-collaborator.sh`** - Called with `--config` and `--repo-urls` for access fixes

All scripts maintain their individual functionality and can still be used standalone.

## 📊 Output and Logging

### Generated Files
```
scripts/
├── student-repos-batch.txt          # All repositories (students + instructor)
├── student-repos-students-only.txt  # Only student repositories
└── assignment-workflow.log          # Execution log (if enabled)
```

### Console Output
- **Color-coded messages** for different types of information
- **Progress indicators** for each workflow step
- **Summary statistics** showing repository counts and execution time
- **Error reporting** with specific failure details

### Example Output
```
=== Configuration Summary ===
Assignment: cs6600-m1-homework1
Organization: WSU-ML-DL
Template Repository: https://github.com/WSU-ML-DL/cs6600-m1-homework1-template.git
Secrets to manage: 2

=== Step 1: Synchronizing Template with Classroom ===
[SUCCESS] Template synchronization completed

=== Step 2: Discovering Student Repositories ===  
[SUCCESS] Repository discovery completed
[INFO] Total repositories: 5
[INFO] Student repositories: 4

=== Step 3: Managing Secrets ===
[SUCCESS] Secret management completed

=== Workflow Summary ===
[SUCCESS] All workflow steps completed successfully!
[INFO] Total execution time: 45s
```

## 🚨 Error Handling

### Configuration Validation
- **Required variables** are checked before execution
- **File paths** are validated for existence
- **URL formats** are verified for classroom URLs

### Step Failure Handling  
- Each step is independent and can fail without stopping others
- **Failed steps** are reported in the final summary
- **Partial success** scenarios are clearly indicated

### Recovery Procedures
```bash
# Check which step failed
./scripts/assignment-orchestrator.sh --verbose

# Retry specific failed step
./scripts/assignment-orchestrator.sh --step secrets

# Fix configuration and retry
vim assignment.conf
./scripts/assignment-orchestrator.sh
```

## 🔒 Security Considerations

### Token Management
- **Token files** are never committed to git
- **Configuration** can reference multiple token files
- **Age-based updates** prevent using expired tokens

### Dry Run Safety
- **Preview mode** shows all actions without executing
- **Configuration validation** happens before any operations
- **User confirmation** required by default (can be disabled)

### Access Control
- Inherits **GitHub CLI authentication**
- Respects **repository permissions** from component scripts
- **Validates access** before attempting operations

## 🎓 Best Practices

### Configuration Management
1. **Version control** configuration files (but not token files)
2. **Document changes** when updating assignment settings
3. **Test with dry-run** before executing on production

### Workflow Execution
1. **Run sync step** after template changes
2. **Monitor output** for any error messages
3. **Verify results** by checking generated repository files

### Maintenance
1. **Update token files** before they expire
2. **Review configuration** at the start of each semester
3. **Test workflows** with new assignments before deploying

---

**Note:** The orchestrator requires all component scripts to be present and executable. It will check for required dependencies and report any missing components before execution.
