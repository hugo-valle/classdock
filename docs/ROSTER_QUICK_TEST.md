# Roster Management - Quick Test Guide

**5-Minute Test to Verify Roster Functionality**

## Step 1: Build and Install (2 min)

```bash
cd /Users/hugovalle/classdock
git checkout feature/34-sqlite-roster-management
poetry install && poetry shell
classdock roster --help  # Verify commands available
```

## Step 2: Initialize and Import (1 min)

```bash
# Initialize database
classdock roster init

# Create quick test CSV
cat > /tmp/test-students.csv << 'EOF'
email,name,github_username
john.doe@example.com,John Doe,johndoe
jane.smith@example.com,Jane Smith,janesmith
bob.jones@example.com,Bob Jones,bobjones
EOF

# Import (replace with your real org)
classdock roster import /tmp/test-students.csv --org=YOUR_GITHUB_ORG
```

**Expected**: "✅ Successful: 3" message

## Step 3: Verify (1 min)

```bash
# List students
classdock roster list --org=YOUR_GITHUB_ORG

# Check status
classdock roster status --org=YOUR_GITHUB_ORG

# Verify database exists
ls -lh ~/.config/classdock/roster.db
```

**Expected**: Table showing 3 students

## Step 4: Test with Real Assignment (1 min)

```bash
# Navigate to existing assignment directory
cd ~/path/to/your/assignment

# Discover repos (existing command)
classdock repos fetch

# Sync with roster
classdock roster sync --assignment=YOUR_ASSIGNMENT_NAME --org=YOUR_GITHUB_ORG

# View results
classdock roster status --org=YOUR_GITHUB_ORG
```

**Expected**: Shows linked/unlinked repo counts

---

## Quick Verification Checklist

- [ ] `classdock roster init` creates database
- [ ] `classdock roster import` imports CSV successfully
- [ ] `classdock roster list` shows students in table
- [ ] `classdock roster status` shows statistics
- [ ] `classdock roster sync` links repos to students
- [ ] All commands complete without errors
- [ ] Database file exists at `~/.config/classdock/roster.db`

---

## Test with Real GitHub Classroom

**Prerequisites**: Active GitHub Classroom assignment with student repos

```bash
# Add to assignment.conf
echo "step_sync_roster=true" >> assignment.conf

# Run orchestrator
classdock assignments orchestrate

# Verify SYNC_ROSTER step appears in output
# Check final statistics
classdock roster status --org=YOUR_ORG
```

---

## Cleanup (for repeated testing)

```bash
# Remove database to start fresh
rm ~/.config/classdock/roster.db

# Re-initialize
classdock roster init
```

---

## Common Issues

| Issue | Solution |
|-------|----------|
| Command not found | Run `poetry shell` to activate environment |
| Database not initialized | Run `classdock roster init` |
| Students not linking | Check GitHub usernames match repo names |
| Duplicate error | Use `--skip-duplicates` flag |

---

## Full Testing

For comprehensive testing, see `docs/ROSTER_TESTING_GUIDE.md`

## Quick Demo

```bash
# Complete workflow in 1 minute
classdock roster init
echo -e "email,name,github_username\ntest@example.com,Test User,testuser" > /tmp/demo.csv
classdock roster import /tmp/demo.csv --org=demo-org
classdock roster list --org=demo-org
classdock roster status --org=demo-org
```
