# Roster Sync Integration Guide

This guide explains how to use the roster sync feature to automatically link discovered repositories with your student roster during assignment workflows.

## Overview

The roster sync feature integrates with the ClassDock orchestrator to automatically:
- Link discovered student repositories to roster entries
- Track assignment acceptance rates
- Identify students who haven't accepted assignments
- Detect repositories without matching roster entries

## Quick Start

### 1. Initialize Roster Database

```bash
classdock roster init
```

This creates a global database at `~/.config/classdock/roster.db`.

### 2. Import Student Roster

```bash
classdock roster import students.csv --org=soc-cs3550-f25
```

Expected CSV format:
```csv
email,name,github_username
student1@example.com,John Doe,johndoe
student2@example.com,Jane Smith,janesmith
```

### 3. Enable Roster Sync in Configuration

Add to your `assignment.conf`:

```bash
# Enable roster sync in orchestrator workflow (optional)
step_sync_roster=true
```

### 4. Run Orchestrator with Roster Sync

```bash
classdock assignments orchestrate
```

The orchestrator will now:
1. Sync template
2. Discover repositories
3. **Sync repositories with roster** ← NEW
4. Manage secrets
5. (Optional) Assist students
6. (Optional) Cycle collaborators

## Manual Roster Sync

You can also sync repositories manually after discovery:

```bash
# Discover repositories
classdock repos fetch

# Sync with roster
classdock roster sync --assignment=python-basics --org=soc-cs3550-f25
```

## Workflow Integration

### Configuration Options

Add these to your `assignment.conf`:

```bash
# Roster sync (disabled by default)
step_sync_roster=true
```

### Workflow Behavior

- **If roster database doesn't exist**: Step is skipped with a warning
- **If roster sync is disabled**: Step is skipped
- **If no repositories discovered**: Step is skipped
- **If sync fails**: Warning is logged, but workflow continues

This ensures roster sync is optional and won't break existing workflows.

## Checking Sync Status

```bash
# View roster status for an organization
classdock roster status --org=soc-cs3550-f25
```

Output:
```
╭────────────────── 📊 Roster Status ──────────────────╮
│                                                      │
│ Roster Status - soc-cs3550-f25                       │
│                                                      │
│ Students:                                            │
│   Total: 25                                          │
│   With GitHub: 23 (92%)                              │
│   Without GitHub: 2 (8%)                             │
│                                                      │
│ Assignments:                                         │
│   Total: 1                                           │
│                                                      │
│ Database:                                            │
│   Location: ~/.config/classdock/roster.db            │
│   Schema Version: 1                                  │
│                                                      │
╰──────────────────────────────────────────────────────╯
```

## Example Workflow

Complete example with roster sync:

```bash
# 1. Setup (one-time)
classdock roster init
classdock roster import students-fall2025.csv --org=soc-cs3550-f25

# 2. Configure assignment
cat > assignment.conf << 'EOF'
classroom_url="https://classroom.github.com/classrooms/12345/assignments/67890"
template_repo_url="https://github.com/soc-cs3550-f25/python-basics"
github_organization="soc-cs3550-f25"
assignment_name="python-basics"
step_sync_roster=true
EOF

# 3. Run orchestrator
classdock assignments orchestrate

# 4. Check results
classdock roster status --org=soc-cs3550-f25
```

## Multi-Organization Support

The global roster database supports multiple GitHub organizations:

```bash
# Import students for Fall 2025
classdock roster import students-fall25.csv --org=soc-cs3550-f25

# Import students for Spring 2026
classdock roster import students-spring26.csv --org=soc-cs3550-s26

# Each organization tracks separately
classdock roster status --org=soc-cs3550-f25
classdock roster status --org=soc-cs3550-s26
```

## Benefits

### For Instructors

- **Automatic tracking**: Know which students accepted assignments
- **Acceptance rates**: See percentage of students who started
- **Identify issues**: Find students who haven't accepted
- **Multi-class support**: Track students across multiple courses

### For Workflows

- **No manual steps**: Sync happens automatically during orchestration
- **Backward compatible**: Existing workflows continue without changes
- **Graceful degradation**: Sync is skipped if roster isn't initialized
- **Error resilient**: Workflow continues even if sync fails

## Troubleshooting

### Roster database not initialized

```
Warning: Roster database not initialized. Run 'classdock roster init' first.
```

**Solution**: Run `classdock roster init`

### No students linked

```
Synced 0/25 repositories (0.0% success rate)
```

**Possible causes**:
- Students don't have GitHub usernames in roster
- GitHub usernames don't match repository names

**Solution**:
1. Check roster: `classdock roster list --org=soc-cs3550-f25`
2. Link GitHub usernames: `classdock roster link --email=student@example.com --github=username --org=soc-cs3550-f25`

### Unlinked repositories

```
⚠️ Unlinked Repositories:
  • https://github.com/org/assignment-unknown-user
```

**Solution**: Add missing students to roster:
```bash
classdock roster add --email=unknown@example.com --name="Unknown Student" \
  --github=unknown-user --org=soc-cs3550-f25
```

## See Also

- [Roster CLI Commands](../CLAUDE.md#roster-commands)
- [Assignment Orchestrator](CLI_ARCHITECTURE.md#orchestrator)
- [Configuration Guide](../README.md#configuration)
