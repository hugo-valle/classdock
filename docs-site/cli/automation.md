# Automation Commands

Automation commands provide scheduling and batch processing capabilities for classroom management workflows.

## Overview

Automation features enable scheduled execution of classroom operations, batch processing of assignments, and monitoring of ongoing tasks.

## Commands

### `classdock automation schedule`

Schedule classroom operations using cron-like syntax.

```bash
# Schedule daily assignment orchestration
classdock automation schedule \
  --command "assignments orchestrate" \
  --cron "0 6 * * *" \
  --name "daily-orchestration"

# Schedule weekly repository sync
classdock automation schedule \
  --command "repos sync" \
  --cron "0 0 * * 0" \
  --assignment "ongoing-project"

# Schedule secret rotation
classdock automation schedule \
  --command "secrets rotate" \
  --cron "0 2 1 * *" \
  --name "monthly-rotation"
```

**Options:**
- `--command CMD`: Command to schedule
- `--cron EXPRESSION`: Cron schedule expression
- `--name NAME`: Unique name for scheduled task
- `--assignment NAME`: Target specific assignment
- `--enabled/--disabled`: Enable or disable schedule
- `--timeout SECONDS`: Command timeout (default: 3600)
- `--retry-count COUNT`: Number of retries on failure

**Cron Expression Format:**
```
┌─── minute (0-59)
│ ┌─── hour (0-23)
│ │ ┌─── day of month (1-31)
│ │ │ ┌─── month (1-12)
│ │ │ │ ┌─── day of week (0-6, Sunday=0)
│ │ │ │ │
* * * * *
```

### `classdock automation list`

List scheduled tasks and their status.

```bash
# List all scheduled tasks
classdock automation list

# List with execution history
classdock automation list --history

# List specific assignment schedules
classdock automation list --assignment "homework-series"

# Export schedule configuration
classdock automation list --export schedules.yaml
```

**Options:**
- `--assignment NAME`: Filter by assignment
- `--status STATUS`: Filter by status (active, disabled, failed)
- `--history`: Include execution history
- `--export FILE`: Export configuration
- `--format FORMAT`: Output format (table, json, yaml)

### `classdock automation run`

Execute scheduled tasks manually or run batch operations.

```bash
# Run specific scheduled task
classdock automation run --name "daily-orchestration"

# Run batch operation
classdock automation run --batch assignments-batch.yaml

# Run with override parameters
classdock automation run \
  --name "repo-sync" \
  --override assignment="special-project"

# Run in background
classdock automation run \
  --name "long-operation" \
  --background
```

**Options:**
- `--name NAME`: Scheduled task name
- `--batch FILE`: Batch configuration file
- `--override KEY=VALUE`: Override parameters
- `--background`: Run in background
- `--wait`: Wait for completion
- `--verbose`: Detailed output

### `classdock automation status`

Check status of automation tasks and system health.

```bash
# Check all automation status
classdock automation status

# Check specific task
classdock automation status --name "daily-orchestration"

# System health check
classdock automation status --health-check

# Generate status report
classdock automation status --report automation-report.html
```

**Options:**
- `--name NAME`: Specific task name
- `--health-check`: System health validation
- `--report FILE`: Generate HTML report
- `--format FORMAT`: Output format
- `--real-time`: Real-time status updates

### `classdock automation stop`

Stop running tasks or disable schedules.

```bash
# Stop running task
classdock automation stop --name "running-task"

# Disable schedule
classdock automation stop --name "daily-task" --disable

# Emergency stop all tasks
classdock automation stop --all --emergency

# Stop with graceful shutdown
classdock automation stop --name "task" --graceful
```

**Options:**
- `--name NAME`: Task name to stop
- `--all`: Stop all running tasks
- `--disable`: Disable schedule permanently
- `--emergency`: Force immediate stop
- `--graceful`: Allow task completion
- `--timeout SECONDS`: Stop timeout

### `classdock automation logs`

View automation task logs and execution history.

```bash
# View logs for specific task
classdock automation logs --name "daily-orchestration"

# View recent logs
classdock automation logs --recent --lines 100

# Follow logs in real-time
classdock automation logs --name "task" --follow

# Export logs
classdock automation logs --export logs-backup.tar.gz
```

**Options:**
- `--name NAME`: Task name
- `--recent`: Show recent executions
- `--lines COUNT`: Number of log lines
- `--follow`: Real-time log following
- `--level LEVEL`: Log level filter (debug, info, warning, error)
- `--export FILE`: Export logs to file

## Configuration

Automation uses configuration for scheduling and execution settings:

```yaml
# automation.conf
automation:
  scheduler:
    enabled: true
    timezone: "UTC"
    max_concurrent_jobs: 5
    
  execution:
    default_timeout: 3600
    retry_attempts: 3
    retry_delay: 300
    
  logging:
    level: "info"
    retention_days: 30
    max_log_size: "100MB"
    
  monitoring:
    health_check_interval: 300
    notification_webhook: "${WEBHOOK_URL}"
    alert_on_failure: true

schedules:
  - name: "daily-orchestration"
    command: "assignments orchestrate"
    cron: "0 6 * * *"
    enabled: true
    
  - name: "weekly-repo-sync"
    command: "repos sync"
    cron: "0 0 * * 0"
    assignment: "semester-project"
```

## Batch Operations

### Batch Configuration Files

Create YAML files to define complex batch operations:

```yaml
# assignments-batch.yaml
batch:
  name: "weekly-assignment-processing"
  description: "Process all weekly assignments"
  
  tasks:
    - name: "fetch-repositories"
      command: "repos fetch"
      assignment: "week-{week_number}"
      parallel: true
      
    - name: "distribute-secrets"
      command: "secrets add"
      depends_on: ["fetch-repositories"]
      secrets_file: "week-{week_number}-secrets.env"
      
    - name: "setup-collaborators"
      command: "repos collaborator add"
      depends_on: ["fetch-repositories"]
      user: "grading-assistant"
      
    - name: "validate-setup"
      command: "assignments validate"
      depends_on: ["distribute-secrets", "setup-collaborators"]
      
  variables:
    week_number: "{{ current_week }}"
    
  error_handling:
    continue_on_error: false
    retry_failed: true
    notification_on_failure: true
```

### Running Batch Operations

```bash
# Execute batch operation
classdock automation run --batch assignments-batch.yaml

# Execute with variable substitution
classdock automation run \
  --batch assignments-batch.yaml \
  --override week_number=5

# Schedule batch operation
classdock automation schedule \
  --batch assignments-batch.yaml \
  --cron "0 8 * * 1" \
  --name "weekly-batch"
```

## Integration

Automation integrates with all other command groups:

- **[Assignment Commands](assignments.md)**: Automated assignment workflows
- **[Repository Commands](repositories.md)**: Scheduled repository operations
- **[Secret Management](secrets.md)**: Automated secret rotation

## Examples

### Complete Assignment Automation

```bash
# 1. Setup daily assignment orchestration
classdock automation schedule \
  --command "assignments orchestrate" \
  --cron "0 6 * * *" \
  --name "daily-orchestration" \
  --timeout 7200

# 2. Setup weekly repository sync
classdock automation schedule \
  --command "repos sync" \
  --cron "0 0 * * 0" \
  --name "weekly-sync" \
  --assignment "semester-project"

# 3. Setup monthly secret rotation
classdock automation schedule \
  --command "secrets rotate" \
  --cron "0 2 1 * *" \
  --name "monthly-rotation" \
  --retry-count 3

# 4. Monitor automation health
classdock automation status --health-check
```

### Batch Assignment Processing

```bash
# Create batch configuration for new assignment
cat > new-assignment-batch.yaml << EOF
batch:
  name: "new-assignment-setup"
  tasks:
    - name: "setup-assignment"
      command: "assignments setup"
      assignment: "midterm-project"
    - name: "fetch-repos"
      command: "repos fetch"
      depends_on: ["setup-assignment"]
    - name: "add-secrets"
      command: "secrets add"
      depends_on: ["fetch-repos"]
      secrets_file: "midterm-secrets.env"
EOF

# Execute batch operation
classdock automation run --batch new-assignment-batch.yaml

# Schedule for future assignments
classdock automation schedule \
  --batch new-assignment-batch.yaml \
  --cron "0 9 * * 1" \
  --name "weekly-assignment-setup"
```

### Monitoring and Maintenance

```bash
# Check automation system health
classdock automation status \
  --health-check \
  --report health-report.html

# View execution logs
classdock automation logs \
  --recent \
  --lines 200 \
  --level warning

# Export automation configuration
classdock automation list \
  --export automation-backup.yaml

# Clean up completed tasks
classdock automation cleanup \
  --older-than "30 days" \
  --status completed
```

## Advanced Features

### Conditional Execution

```yaml
# conditional-batch.yaml
batch:
  name: "conditional-processing"
  tasks:
    - name: "check-submissions"
      command: "repos status"
      assignment: "homework-01"
      
    - name: "process-if-ready"
      command: "assignments orchestrate"
      condition: "submissions_ready == true"
      depends_on: ["check-submissions"]
```

### Parallel Execution

```bash
# Run multiple assignments in parallel
classdock automation run \
  --batch parallel-assignments.yaml \
  --parallel 3 \
  --max-concurrent 5
```

### Error Handling and Recovery

```yaml
# robust-batch.yaml
batch:
  name: "robust-operation"
  error_handling:
    continue_on_error: true
    retry_failed: true
    max_retries: 3
    retry_delay: 600
    notification_on_failure: true
    recovery_script: "./recovery.sh"
```

## Troubleshooting

### Common Issues

**Scheduling Problems:**
```bash
# Check scheduler status
classdock automation status --health-check

# Verify cron expressions
classdock automation validate --cron "0 6 * * *"

# Debug scheduling
classdock automation logs \
  --name "scheduler" \
  --level debug
```

**Execution Failures:**
```bash
# Check task logs
classdock automation logs \
  --name "failed-task" \
  --level error

# Retry failed task
classdock automation run \
  --name "failed-task" \
  --retry

# Check system resources
classdock automation status \
  --health-check \
  --detailed
```

**Performance Issues:**
```bash
# Monitor concurrent executions
classdock automation status --real-time

# Adjust concurrency limits
classdock automation configure \
  --max-concurrent 3

# Check resource usage
classdock automation logs \
  --name "performance" \
  --metrics
```

## Best Practices

1. **Scheduling**:
   - Use appropriate cron expressions for task frequency
   - Avoid resource conflicts with concurrent executions
   - Set reasonable timeouts for long-running tasks
   - Implement proper error handling and retries

2. **Monitoring**:
   - Regular health checks and status monitoring
   - Set up alerting for critical task failures
   - Monitor resource usage and performance
   - Maintain log retention policies

3. **Configuration**:
   - Use version control for automation configurations
   - Test batch operations before scheduling
   - Document automation workflows and dependencies
   - Implement backup and recovery procedures

4. **Security**:
   - Secure automation credentials and tokens
   - Limit automation permissions to required operations
   - Audit automation logs regularly
   - Implement change management for automation updates

## See Also

- [Assignment Commands](assignments.md)
- [Repository Commands](repositories.md)
- [Secret Management](secrets.md)
- [Configuration Guide](../getting-started/configuration.md)
