# Roster Management Testing Guide

This guide helps you build, install, and test the new SQLite Roster Management System locally with real GitHub Classroom data.

## Prerequisites

- Python 3.10+
- Poetry installed
- GitHub CLI (`gh`) authenticated
- Access to a GitHub Classroom organization

## Quick Start: Build and Install

### 1. Switch to Feature Branch

```bash
cd /Users/hugovalle/classdock
git checkout feature/34-sqlite-roster-management
git pull origin feature/34-sqlite-roster-management
```

### 2. Install Development Version

```bash
# Install dependencies and build
poetry install

# Activate virtual environment (Poetry 2.0+)
source $(poetry env info --path)/bin/activate

# Verify installation (now works from any directory!)
classdock --version
classdock roster --help
```

> **Note**: Poetry 2.0+ removed the `shell` command. Activate manually using the command above.
> Once activated, `classdock` commands work from any directory.

### 3. Using ClassDock from Any Directory

After activating the virtual environment, you can use `classdock` from any directory:

```bash
# Activate once per terminal session
source $(cd /Users/hugovalle/classdock && poetry env info --path)/bin/activate

# Now test from anywhere
cd ~/test-assignment
classdock roster init
classdock repos fetch

cd ~/another-assignment
classdock roster sync --assignment=test --org=YOUR_ORG

# When done
deactivate
```

**Alternative Options:**

```bash
# Option 1: Quick one-liner for each new terminal
source $(cd /Users/hugovalle/classdock && poetry env info --path)/bin/activate

# Option 2: From project directory only (no activation needed)
cd /Users/hugovalle/classdock
poetry run classdock roster init

# Option 3: Create shell alias (add to ~/.zshrc)
alias classdock-dev='source $(cd /Users/hugovalle/classdock && poetry env info --path)/bin/activate'
```

### 4. Run Tests (Optional)

```bash
# Run all roster tests
poetry run pytest tests/test_database.py \
                  tests/test_roster_models.py \
                  tests/test_roster_manager.py \
                  tests/test_roster_importer.py \
                  tests/test_roster_sync.py -v

# Expected: 116 passed
```

## Testing with Real Data

### Scenario 1: Basic CSV Import and Roster Management

**Goal**: Import real student data and verify database functionality.

#### Step 1: Prepare Student CSV

Create a CSV file from your Google Forms or student list:

```bash
# Create test CSV (replace with your real data)
cat > ~/test-roster.csv << 'EOF'
email,name,github_username
student1@example.com,John Doe,johndoe
student2@example.com,Jane Smith,janesmith
student3@example.com,Bob Johnson,bobjohnson
EOF
```

**Real Data Source**: Export from Google Forms or create from your LMS roster.

#### Step 2: Initialize Roster Database

```bash
# Initialize global database
classdock roster init

# Verify database creation
ls -lh ~/.config/classdock/roster.db
```

**Expected Output**:
```
✅ Roster database initialized successfully!
Database: ~/.config/classdock/roster.db
```

#### Step 3: Import Students

```bash
# Import CSV (use your real GitHub organization)
classdock roster import ~/test-roster.csv --org=soc-cs3550-f25

# Or with validation (checks if GitHub users exist)
classdock roster import ~/test-roster.csv --org=soc-cs3550-f25 --validate-github
```

**Expected Output**:
```
╭────────── 📋 Import Summary ──────────╮
│ Total Records: 3                      │
│ ✅ Successful: 3                       │
│ ⚠️  Skipped: 0                        │
│ ❌ Failed: 0                          │
╰───────────────────────────────────────╯
```

#### Step 4: Verify Import

```bash
# List all students
classdock roster list --org=soc-cs3550-f25

# Export to verify (creates roster-export.csv by default)
classdock roster export --org=soc-cs3550-f25
cat roster-export.csv
```

#### Step 5: Test Manual Operations

```bash
# Add a student manually
classdock roster add \
  --email="newstudent@example.com" \
  --name="New Student" \
  --github="newstudent" \
  --org="soc-cs3550-f25"

# Link GitHub username to existing student (if they didn't have one)
classdock roster link \
  --email="student1@example.com" \
  --github="johndoe-github" \
  --org="soc-cs3550-f25"

# Check roster status
classdock roster status --org=soc-cs3550-f25
```

---

### Scenario 2: Real GitHub Classroom Integration

**Goal**: Test roster sync with actual GitHub Classroom repositories.

#### Prerequisites

- Existing GitHub Classroom assignment with student repositories
- Assignment already distributed to students

#### Step 1: Configure Assignment

```bash
# Navigate to your test assignment directory
cd ~/path/to/test-assignment

# Create or verify assignment.conf
cat > assignment.conf << 'EOF'
classroom_url="https://classroom.github.com/classrooms/YOUR_CLASSROOM_ID/assignments/YOUR_ASSIGNMENT_ID"
template_repo_url="https://github.com/YOUR_ORG/YOUR_TEMPLATE"
github_organization="soc-cs3550-f25"
assignment_name="python-basics"
token_name="CLASSDOCK_TOKEN"
step_sync_roster=true
EOF
```

#### Step 2: Test Repository Discovery

```bash
# Discover repositories (existing command)
classdock repos fetch

# Verify student-repos.txt was created
cat student-repos.txt
```

**Expected**: List of repository URLs like:
```
https://github.com/soc-cs3550-f25/python-basics-johndoe
https://github.com/soc-cs3550-f25/python-basics-janesmith
...
```

#### Step 3: Manual Roster Sync

```bash
# Sync discovered repos with roster
classdock roster sync \
  --assignment=python-basics \
  --org=soc-cs3550-f25

# Check sync results
classdock roster status --org=soc-cs3550-f25
```

**Expected Output**:
```
📊 Sync Results:
  Total Repositories: 20
  ✅ Linked: 18 (90%)
  ⚠️  Unlinked: 2 (10%)

⚠️ Unlinked Repositories:
  • https://github.com/soc-cs3550-f25/python-basics-unknownuser

⚠️ Students Without Repositories (2):
  • student3@example.com (GitHub: student3)
  • student4@example.com (GitHub: student4)
```

#### Step 4: Test Orchestrator Integration

```bash
# Run full orchestrator workflow with roster sync enabled
classdock assignments orchestrate

# The workflow will:
# 1. Sync template (SYNC_TEMPLATE)
# 2. Discover repositories (DISCOVER_REPOS)
# 3. Sync with roster (SYNC_ROSTER) ← NEW STEP
# 4. Manage secrets (MANAGE_SECRETS)
# ... other steps
```

**Verify**: Check that SYNC_ROSTER step appears in workflow output.

---

### Scenario 3: Multi-Organization Testing

**Goal**: Test with multiple GitHub Classroom organizations (multiple courses).

```bash
# Import students for first course
classdock roster import cs3550-students.csv --org=soc-cs3550-f25

# Import students for second course
classdock roster import cs2350-students.csv --org=soc-cs2350-s26

# Verify separation
classdock roster list --org=soc-cs3550-f25
classdock roster list --org=soc-cs2350-s26

# Check status for each
classdock roster status --org=soc-cs3550-f25
classdock roster status --org=soc-cs2350-s26
```

---

## Code Review Checklist

When reviewing the implementation, check:

### 1. Database Integrity

```bash
# Inspect database schema
sqlite3 ~/.config/classdock/roster.db ".schema"

# Check for data
sqlite3 ~/.config/classdock/roster.db "SELECT COUNT(*) FROM students;"
sqlite3 ~/.config/classdock/roster.db "SELECT * FROM students LIMIT 5;"
```

### 2. Backward Compatibility

```bash
# Test existing workflow WITHOUT roster database
rm ~/.config/classdock/roster.db

# Run existing commands (should work without errors)
cd ~/existing-assignment
classdock repos fetch
classdock secrets add

# Verify: Commands should complete without errors, roster features silently skipped
```

### 3. Error Handling

```bash
# Test with invalid CSV
echo "invalid,csv,format" > /tmp/bad.csv
classdock roster import /tmp/bad.csv --org=test-org

# Test with missing organization
classdock roster list --org=nonexistent-org

# Test sync without database
rm ~/.config/classdock/roster.db
classdock roster sync --assignment=test --org=test-org
```

### 4. File Locations

```bash
# Verify files were created in correct locations
ls -la classdock/roster/          # Should have: __init__.py, models.py, manager.py, importer.py, sync.py
ls -la classdock/utils/           # Should have: database.py
ls -la classdock/services/        # Should have: roster_service.py
ls -la docs/                      # Should have: ROSTER_SYNC.md, ROSTER_MIGRATION.md
ls -la tests/                     # Should have: test_database.py, test_roster_*.py
```

---

## Integration Testing Scenarios

### Scenario A: Mid-Semester Adoption

**Context**: You're halfway through a semester and want to start tracking.

```bash
# 1. Initialize
classdock roster init

# 2. Import current students
classdock roster import current-students.csv --org=YOUR_ORG

# 3. Sync existing assignments
cd assignment-1
classdock repos fetch
classdock roster sync --assignment=assignment-1 --org=YOUR_ORG

cd ../assignment-2
classdock repos fetch
classdock roster sync --assignment=assignment-2 --org=YOUR_ORG

# 4. Check results
classdock roster status --org=YOUR_ORG
```

### Scenario B: New Semester Setup

**Context**: Starting fresh with new students.

```bash
# 1. Export student list from Google Forms
# (Download as CSV from Google Forms)

# 2. Initialize roster at start of semester
classdock roster init
classdock roster import semester-students.csv --org=YOUR_ORG --validate-github

# 3. For each new assignment, enable roster sync in assignment.conf
echo "step_sync_roster=true" >> assignment-1/assignment.conf

# 4. Run orchestrator (roster sync happens automatically)
cd assignment-1
classdock assignments orchestrate

# 5. Monitor acceptance rates
classdock roster status --org=YOUR_ORG
```

---

## Common Issues and Troubleshooting

### Issue 1: Database Not Found

```bash
# Symptom: "Roster database not initialized"
# Solution:
classdock roster init
```

### Issue 2: Students Not Linking

```bash
# Symptom: All repos show as "unlinked"
# Possible causes:
# - GitHub usernames don't match repository patterns
# - Students not in roster

# Debug:
classdock roster list --org=YOUR_ORG  # Check what's in roster
cat student-repos.txt                  # Check discovered repos

# Fix: Link manually
classdock roster link \
  --email="student@example.com" \
  --github="actual-github-username" \
  --org="YOUR_ORG"
```

### Issue 3: Duplicate Students

```bash
# Symptom: "Student already exists"
# Solution: Use --skip-duplicates flag
classdock roster import students.csv --org=YOUR_ORG --skip-duplicates
```

### Issue 4: Missing GitHub Usernames

```bash
# If students didn't provide GitHub usernames in form
# Option 1: Import without usernames, link later
classdock roster import students.csv --org=YOUR_ORG  # github_username column can be empty

# Option 2: Extract from repo names and link
classdock repos fetch
# Look at student-repos.txt to see GitHub usernames
classdock roster link --email=student@example.com --github=username --org=YOUR_ORG
```

---

## Performance Testing

### Test with Large Roster

```bash
# Create large test CSV (100+ students)
python3 << 'EOF'
import csv
with open('/tmp/large-roster.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['email', 'name', 'github_username'])
    for i in range(1, 101):
        writer.writerow([f'student{i}@example.com', f'Student {i}', f'student{i}'])
EOF

# Import and time it
time classdock roster import /tmp/large-roster.csv --org=test-org

# Check database size
ls -lh ~/.config/classdock/roster.db
```

**Expected**: Import should complete in < 2 seconds for 100 students.

---

## Collecting User Feedback

When gathering instructor feedback, ask:

### Usability Questions

1. **CSV Import**:
   - Was the CSV format clear?
   - Did the import process work smoothly?
   - Any issues with duplicate handling?

2. **Roster Sync**:
   - Did the sync correctly link repositories to students?
   - Were unlinked repositories easy to identify?
   - Was the status output helpful?

3. **Orchestrator Integration**:
   - Did adding `step_sync_roster=true` work as expected?
   - Was the sync step clearly visible in output?
   - Any performance issues?

### Feature Requests

- What additional roster features would be useful?
- What statistics/reports would help?
- Integration with other tools (Canvas, Blackboard)?

### Sample Feedback Survey

```bash
# Create feedback form
cat > ROSTER_FEEDBACK.md << 'EOF'
# Roster Management Feature Feedback

## Testing Environment
- Course: ___________________
- Students: _____ (count)
- Assignments: _____ (count)
- GitHub Organization: _____________________

## Feature Testing

### CSV Import (1-5 stars)
- Ease of use: ⭐____
- Documentation clarity: ⭐____
- Error messages: ⭐____
- Comments: _________________

### Roster Sync (1-5 stars)
- Accuracy: ⭐____
- Performance: ⭐____
- Usefulness: ⭐____
- Comments: _________________

### Overall (1-5 stars)
- Would you use this feature? ⭐____
- Would you recommend it? ⭐____

## Issues Encountered
_____________________________

## Feature Requests
_____________________________
EOF
```

---

## Quick Reference

### Essential Commands

```bash
# Setup
classdock roster init
classdock roster import students.csv --org=YOUR_ORG

# Daily operations
classdock roster status --org=YOUR_ORG
classdock roster list --org=YOUR_ORG

# After new assignment
cd assignment-dir
classdock repos fetch
classdock roster sync --assignment=ASSIGNMENT_NAME --org=YOUR_ORG

# With orchestrator
echo "step_sync_roster=true" >> assignment.conf
classdock assignments orchestrate
```

### Database Location

```bash
# Global database
~/.config/classdock/roster.db

# Backup
cp ~/.config/classdock/roster.db ~/roster-backup-$(date +%Y%m%d).db

# Reset (for testing)
rm ~/.config/classdock/roster.db
classdock roster init
```

---

## Next Steps After Testing

1. **Document Issues**: Create GitHub issues for any bugs found
2. **Update Documentation**: Note any unclear instructions
3. **Performance Metrics**: Record timing for large rosters
4. **User Feedback**: Compile instructor feedback
5. **PR Review**: Submit findings in PR review comments

---

## Support

- **Documentation**: See `docs/ROSTER_SYNC.md` and `docs/ROSTER_MIGRATION.md`
- **Issues**: https://github.com/hugo-valle/classdock/issues/34
- **Tests**: Run `make test` or `poetry run pytest tests/test_roster*.py -v`
