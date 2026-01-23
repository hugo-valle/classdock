# Cron Automation - Scheduled GitHub Classroom Management

## 🎯 Overview

ClassDock provides comprehensive automation capabilities for scheduling GitHub Classroom management tasks. Set up automated workflows that run unattended to keep your assignments synchronized and students supported.

## 📦 Installation

```bash
# Install from PyPI
pip install classdock

# Verify installation
classdock --help
```

## 🚀 Automation Features

### Flexible Scheduling

- **Individual Tasks**: Schedule each workflow component independently
- **Combined Workflows**: Run multiple tasks in coordinated sequences
- **Custom Schedules**: Configure timing based on your teaching schedule
- **Intelligent Defaults**: Pre-configured schedules optimized for common patterns

### Automated Tasks

- **Assignment Orchestration**: Complete workflow automation
- **Repository Synchronization**: Keep templates updated
- **Secret Management**: Distribute and rotate tokens
- **Student Assistance**: Automated help and conflict resolution
- **Permission Management**: Fix repository access issues

### Monitoring & Logging

- **Comprehensive Logging**: Detailed logs for all automated tasks
- **Status Monitoring**: Check automation status and health
- **Error Tracking**: Automated error reporting and alerting
- **Log Rotation**: Automatic log management and cleanup

## 🔧 Setup Automation

### 1. Configure Assignment

```bash
# Create assignment configuration
classdock assignments setup

# This creates assignment.conf with your settings
```

### 2. Setup Scheduler

```bash
# Setup automated scheduling
classdock automation scheduler setup --config assignment.conf

# This configures cron jobs for:
# - Regular assignment orchestration
# - Template synchronization
# - Secret management
# - Repository monitoring
```

### 3. Verify Automation

```bash
# Check scheduled tasks
classdock automation scheduler status

# View automation logs
classdock automation scheduler logs
```

## ⚙️ Automation Commands

### Scheduler Management

```bash
# Setup automated scheduling
classdock automation scheduler setup [--config FILE]

# Check scheduler status
classdock automation scheduler status

# View scheduler logs
classdock automation scheduler logs

# Disable scheduling
classdock automation scheduler disable

# Re-enable scheduling
classdock automation scheduler enable
```

### Batch Operations

```bash
# Run batch operations
classdock automation batch [--config FILE]

# Run specific batch tasks
classdock automation batch --tasks "secrets,repos" [--config FILE]

# Schedule batch operations
classdock automation batch --schedule "0 */6 * * *" [--config FILE]
```

## 📅 Scheduling Patterns

### Default Schedules

The automation system includes optimized default schedules:

```bash
# Assignment orchestration: Daily at 2 AM
0 2 * * *

# Template synchronization: Every 4 hours
0 */4 * * *

# Secret management: Weekly on Sunday at 3 AM
0 3 * * 0

# Repository monitoring: Every 2 hours during business hours
0 9-17/2 * * 1-5

# Student assistance: Hourly during class days
0 * * * 1-5
```

### Custom Schedules

Configure custom schedules for your specific needs:

```bash
# Custom schedule configuration in assignment.conf
AUTOMATION_SCHEDULE_ORCHESTRATE="0 1 * * *"     # Daily at 1 AM
AUTOMATION_SCHEDULE_SYNC="0 */2 * * *"          # Every 2 hours
AUTOMATION_SCHEDULE_SECRETS="0 4 * * 1"         # Monday at 4 AM
AUTOMATION_SCHEDULE_MONITOR="*/30 9-17 * * 1-5" # Every 30 min during business hours
```

### Academic Calendar Integration

Align automation with your academic schedule:

```bash
# Semester start: Increased frequency
AUTOMATION_SCHEDULE_SEMESTER_START="*/15 * * * *"  # Every 15 minutes

# Regular semester: Standard frequency  
AUTOMATION_SCHEDULE_REGULAR="0 */4 * * *"          # Every 4 hours

# Finals week: Monitoring focus
AUTOMATION_SCHEDULE_FINALS="0 */2 * * *"           # Every 2 hours

# Semester end: Reduced frequency
AUTOMATION_SCHEDULE_END="0 6 * * *"                # Daily at 6 AM
```

## 🔄 Workflow Automation

### Complete Assignment Automation

```bash
# Setup comprehensive automation
cat > automation-assignment.conf << 'EOF'
# Assignment Configuration
CLASSROOM_URL="https://classroom.github.com/classrooms/123/assignments/homework1"
TEMPLATE_REPO_URL="https://github.com/instructor/homework1-template"
ASSIGNMENT_FILE="homework1.py"
GITHUB_TOKEN_FILE="github_token.txt"
SECRETS_LIST="API_KEY,GRADING_TOKEN"

# Automation Schedules
AUTOMATION_SCHEDULE_ORCHESTRATE="0 2 * * *"      # Daily at 2 AM
AUTOMATION_SCHEDULE_SYNC="0 */6 * * *"           # Every 6 hours
AUTOMATION_SCHEDULE_SECRETS="0 3 * * 1"          # Monday at 3 AM
AUTOMATION_SCHEDULE_MONITOR="0 9-17/2 * * 1-5"   # Business hours monitoring
EOF

# Setup automation
classdock automation scheduler setup --config automation-assignment.conf
```

### Midterm Exam Automation

```bash
# High-frequency monitoring for exam period
cat > midterm-automation.conf << 'EOF'
CLASSROOM_URL="https://classroom.github.com/classrooms/123/assignments/midterm"
TEMPLATE_REPO_URL="https://github.com/instructor/midterm-template"

# Intensive monitoring during exam
AUTOMATION_SCHEDULE_MONITOR="*/10 8-20 * * *"     # Every 10 minutes, 8 AM - 8 PM
AUTOMATION_SCHEDULE_ASSISTANCE="*/5 8-20 * * *"   # Every 5 minutes during exam
AUTOMATION_SCHEDULE_SYNC="0 */1 * * *"            # Hourly sync
EOF

classdock automation scheduler setup --config midterm-automation.conf
```

### Semester-End Automation

```bash
# Reduced automation for semester end
cat > semester-end-automation.conf << 'EOF'
CLASSROOM_URL="https://classroom.github.com/classrooms/123/assignments/final-project"

# Minimal automation
AUTOMATION_SCHEDULE_ORCHESTRATE="0 6 * * *"       # Daily at 6 AM
AUTOMATION_SCHEDULE_BACKUP="0 0 * * 0"            # Weekly backup
AUTOMATION_SCHEDULE_CLEANUP="0 1 * * 0"           # Weekly cleanup
EOF

classdock automation scheduler setup --config semester-end-automation.conf
```

## 📊 Monitoring & Management

### Status Monitoring

```bash
# Check all automation status
classdock automation scheduler status

# View active cron jobs
crontab -l | grep classdock

# Check automation health
classdock automation scheduler health
```

### Log Management

```bash
# View automation logs
classdock automation scheduler logs

# View specific task logs
classdock automation scheduler logs --task orchestrate

# Tail live logs
classdock automation scheduler logs --follow

# Rotate logs manually
classdock automation scheduler logs --rotate
```

### Performance Monitoring

```bash
# Check automation performance
classdock automation scheduler metrics

# View task execution times
classdock automation scheduler metrics --task-times

# Monitor resource usage
classdock automation scheduler metrics --resources
```

## 🛡️ Security & Best Practices

### Token Management

```bash
# Secure token storage for automation
echo "ghp_your_automation_token" > automation_token.txt
chmod 600 automation_token.txt

# Use dedicated automation token
GITHUB_TOKEN_FILE="automation_token.txt"
```

### Access Control

```bash
# Limit automation token permissions
# Required scopes:
# - repo (for repository access)
# - admin:org (for organization management)
# - write:org (for secret management)

# Avoid overly broad permissions
# Never use personal access tokens for automation
```

### Error Handling

```bash
# Configure error notifications
AUTOMATION_ERROR_EMAIL="instructor@university.edu"
AUTOMATION_ERROR_SLACK_WEBHOOK="https://hooks.slack.com/..."

# Setup automated alerting
classdock automation scheduler setup --config assignment.conf --alerts
```

## 🔍 Troubleshooting

### Common Issues

1. **Cron Jobs Not Running**:
   ```bash
   # Check cron service status
   systemctl status cron
   
   # Verify cron job syntax
   classdock automation scheduler validate
   ```

2. **Authentication Failures**:
   ```bash
   # Check token permissions
   classdock --verbose automation batch --config assignment.conf
   ```

3. **Schedule Conflicts**:
   ```bash
   # Review active schedules
   classdock automation scheduler status --detailed
   ```

### Debug Mode

```bash
# Run automation in debug mode
classdock --verbose automation batch --config assignment.conf

# Test automation without scheduling
classdock --dry-run automation scheduler setup --config assignment.conf
```

## 📚 Related Documentation

- **[Automation Suite](automation-suite.md)** - Complete automation capabilities
- **[Assignment Orchestrator](assignment-orchestrator.md)** - Workflow automation
- **[Secrets Management](secrets-management.md)** - Automated secret handling
- **[Main CLI Reference](../README.md)** - Complete command documentation

## 💡 Tips for Effective Automation

### Scheduling Strategy

- **Start Conservative**: Begin with less frequent schedules and increase as needed
- **Consider Time Zones**: Schedule automation during low-activity periods
- **Plan for Peaks**: Increase frequency during assignment deadlines
- **Monitor Resource Usage**: Avoid overwhelming GitHub API limits

### Maintenance Planning

- **Regular Reviews**: Monthly review of automation effectiveness
- **Schedule Adjustments**: Modify schedules based on semester patterns
- **Token Rotation**: Regularly rotate automation tokens
- **Log Analysis**: Review logs for optimization opportunities

---

Cron automation provides powerful, unattended management of GitHub Classroom assignments through intelligent scheduling and monitoring.
