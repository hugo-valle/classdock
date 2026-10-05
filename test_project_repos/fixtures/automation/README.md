# Automation Fixtures

This directory contains test fixtures for comprehensive QA testing of automation commands in the `classdock` CLI tool.

## Purpose

These fixtures provide sample data and configuration files needed to test all automation-related commands including cron job management, workflow execution, logging, and scheduling.

## Fixture Categories

### Crontab Files

- **`sample_crontab.txt`** - Example crontab with installed automation jobs
  - Used for testing cron-status and cron-remove commands
  - Shows format of installed cron entries
  - Contains realistic GitHub automation schedules

### Log Files

- **`sample_cron_log.txt`** - Sample workflow log with realistic entries
  - Used for testing cron-logs command
  - Contains success, error, and info log entries
  - Shows timestamp format and log structure
  - Includes examples of successful and failed workflow executions

### Schedule Files

- **`valid_schedules.txt`** - Collection of valid cron schedules
  - Used for testing cron-install command with valid inputs
  - Covers various schedule formats (hourly, daily, weekly, etc.)
  - Includes common automation patterns

- **`invalid_schedules.txt`** - Collection of invalid cron schedules
  - Used for testing cron-install schedule validation
  - Covers various error cases (invalid fields, out of range, malformed)
  - Ensures proper error handling

### Configuration Files

- **`automation_config.conf`** - Valid configuration with workflow steps enabled
  - Used for testing automation commands with proper configuration
  - Includes all workflow step flags (STEP_SYNC, STEP_MANAGE_SECRETS, etc.)
  - Contains SECRETS_CONFIG for complete testing

## Usage Examples

### Test cron-install with valid schedule
```bash
classdock automation cron-install sync --schedule "0 */4 * * *"
```

### Test cron-install with invalid schedule (should fail)
```bash
classdock automation cron-install sync --schedule "invalid"
```

### Test cron-logs with sample log file
```bash
classdock automation cron-logs --lines 30
```

### Test cron-status with sample crontab
```bash
classdock automation cron-status
```

## Cron Schedule Format

```
minute hour day_of_month month day_of_week
  |     |        |         |         |
  |     |        |         |         +-- Day of week (0-7, 0 and 7 are Sunday)
  |     |        |         +------------ Month (1-12)
  |     |        +---------------------- Day of month (1-31)
  |     +------------------------------- Hour (0-23)
  +-------------------------------------- Minute (0-59)
```

### Special Characters

- `*` - Any value
- `,` - Value list separator
- `-` - Range of values
- `/` - Step values

### Examples

- `0 */4 * * *` - Every 4 hours
- `0 2 * * *` - Daily at 2 AM
- `0 6 * * 0` - Weekly on Sunday at 6 AM
- `*/30 * * * *` - Every 30 minutes
- `0 12 * * 1-5` - Weekdays at noon

## Log File Format

Log entries follow the format:
```
[YYYY-MM-DD HH:MM:SS] LEVEL: Message
```

### Levels

- `INFO` - Informational messages
- `SUCCESS` - Successful operations
- `WARNING` - Warning messages
- `ERROR` - Error messages

## Adding New Fixtures

### Naming Conventions

- Crontab files: `*_crontab.txt`
- Log files: `*_log.txt`
- Schedule files: `*_schedules.txt`
- Config files: `*_config.conf`

### Documentation Requirements

1. Add comment header explaining purpose
2. Update this README with new fixture description
3. Provide usage example
4. Note any special considerations

### Validation Checklist

- [ ] File follows correct format specification
- [ ] Contains descriptive comment header
- [ ] Uses realistic but non-existent test values
- [ ] Documented in this README
- [ ] Tested with relevant commands
- [ ] No actual system paths or sensitive data

## Related Documentation

- `docs/QA_TESTING_GUIDE.md` - Comprehensive QA testing guide for automation commands (lines 1234-1635)
- `test_project_repos/qa_tests/test_automation_commands.sh` - Main test suite using these fixtures
- `classdock/automation/cron_manager.py` - CronManager implementation
- `classdock/automation/cron_sync.py` - CronSyncManager implementation

## Security Note

⚠️ **IMPORTANT**: All fixtures use test/mock data only. These are NOT real cron jobs, log files, or system configurations.

### Never commit

- Real crontab entries
- Actual log files with sensitive information
- Production configuration files
- Real system paths
- Actual GitHub tokens or credentials

## Testing Best Practices

1. **Use appropriate fixtures** - Select the fixture that matches your test scenario
2. **Test error cases** - Use invalid fixtures to verify error handling
3. **Mock system commands** - Use mock helpers to avoid real crontab modifications
4. **Verify messages** - Check that error messages are clear and actionable
5. **Test all options** - Verify each command option works correctly
6. **Test global options** - Verify --verbose and --dry-run work with all commands
7. **Isolate tests** - Don't rely on external state or real cron jobs

---

**Last Updated**: October 21, 2025  
**Fixture Count**: 6 files  
**Commands Supported**: 9 automation commands (cron-install, cron-remove, cron-status, cron-logs, cron-schedules, cron-sync, cron, sync, batch)  
**Test Coverage**: Cron job management, workflow execution, logging, scheduling, error handling
