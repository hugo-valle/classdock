# Roster Management Migration Guide

This guide helps existing ClassDock users adopt the new SQLite-based roster management system introduced in v3.2.0.

## What's New

ClassDock now includes an optional roster management system that:
- Tracks student enrollment across GitHub organizations
- Links students to their assignment repositories
- Calculates assignment acceptance rates
- Identifies students who haven't accepted assignments
- Integrates with the orchestrator workflow

## Is This Breaking?

**No!** The roster system is **completely optional** and **backward compatible**.

- ✅ All existing workflows continue without changes
- ✅ No configuration updates required
- ✅ Roster features are opt-in only
- ✅ If roster database doesn't exist, features are silently skipped

## Should I Migrate?

### Use Roster Management If You:

- ✅ Want to track which students accepted assignments
- ✅ Need acceptance rate statistics
- ✅ Manage multiple GitHub Classroom organizations
- ✅ Want to identify students who haven't started
- ✅ Need centralized student enrollment tracking
- ✅ Use Google Forms for student registration

### Skip Roster Management If You:

- ❌ Prefer file-based repository tracking (`student-repos.txt`)
- ❌ Don't need student enrollment tracking
- ❌ Already have your own tracking system
- ❌ Want minimal dependencies (roster adds SQLite)

## Migration Steps

### 1. Initialize Roster Database (One-Time)

```bash
classdock roster init
```

This creates: `~/.config/classdock/roster.db`

### 2. Import Student Roster

If you have student data from Google Forms or similar:

```bash
# Expected CSV format: email,name,github_username
classdock roster import students-fall2025.csv --org=soc-cs3550-f25
```

**Example CSV:**
```csv
email,name,github_username
john.doe@example.com,John Doe,johndoe
jane.smith@example.com,Jane Smith,janesmith
```

### 3. (Optional) Enable Orchestrator Integration

Add to your `assignment.conf`:

```bash
# Enable automatic roster sync
step_sync_roster=true
```

This will automatically sync repositories with the roster when you run:
```bash
classdock assignments orchestrate
```

### 4. Verify Setup

```bash
# Check roster status
classdock roster status --org=soc-cs3550-f25

# List students
classdock roster list --org=soc-cs3550-f25
```

## Migrating Existing Workflows

### Before: File-Based Tracking

```bash
# Old workflow (still works!)
classdock repos fetch
# Repos saved to student-repos.txt
classdock secrets add
```

### After: With Roster Tracking

```bash
# New workflow (optional)
classdock repos fetch
classdock roster sync --assignment=python-basics --org=soc-cs3550-f25
classdock secrets add

# Check acceptance rate
classdock roster status --org=soc-cs3550-f25
```

### Or: Automatic with Orchestrator

```bash
# Add to assignment.conf
echo "step_sync_roster=true" >> assignment.conf

# Run orchestrator (sync happens automatically)
classdock assignments orchestrate

# Check results
classdock roster status --org=soc-cs3550-f25
```

## Common Scenarios

### Scenario 1: Mid-Semester Migration

You're halfway through a semester and want to start using roster tracking.

```bash
# 1. Initialize roster
classdock roster init

# 2. Import current students
classdock roster import students.csv --org=soc-cs3550-f25

# 3. Sync existing assignments
classdock repos fetch  # For current assignment
classdock roster sync --assignment=current-assignment --org=soc-cs3550-f25

# 4. View results
classdock roster status --org=soc-cs3550-f25
```

**Result**: Existing workflows continue, but now you also get roster tracking.

### Scenario 2: Multiple Courses

You teach multiple courses with different student rosters.

```bash
# Import students for Course A
classdock roster import cs3550-students.csv --org=soc-cs3550-f25

# Import students for Course B
classdock roster import cs2350-students.csv --org=soc-cs2350-f25

# Each course tracks separately
classdock roster status --org=soc-cs3550-f25
classdock roster status --org=soc-cs2350-f25
```

**Result**: Single database tracks multiple organizations separately.

### Scenario 3: Gradual Adoption

You want to try roster tracking for one assignment first.

```bash
# 1. Initialize for testing
classdock roster init
classdock roster import students.csv --org=soc-cs3550-f25

# 2. Try manual sync for one assignment
classdock repos fetch
classdock roster sync --assignment=test-assignment --org=soc-cs3550-f25

# 3. If you like it, enable in orchestrator later
# (Add step_sync_roster=true to assignment.conf when ready)
```

**Result**: Test with one assignment before full adoption.

## Handling Missing GitHub Usernames

If students haven't provided GitHub usernames:

### Option 1: Import Without Usernames

```csv
email,name,github_username
john.doe@example.com,John Doe,
jane.smith@example.com,Jane Smith,
```

Later, link manually:
```bash
classdock roster link --email=john.doe@example.com --github=johndoe --org=soc-cs3550-f25
```

### Option 2: Extract from Repository Names

After running `classdock repos fetch`, you can see repository names like:
- `python-basics-johndoe`
- `python-basics-janesmith`

Extract usernames and update roster:
```bash
classdock roster link --email=john.doe@example.com --github=johndoe --org=soc-cs3550-f25
classdock roster link --email=jane.smith@example.com --github=janesmith --org=soc-cs3550-f25
```

Then re-sync:
```bash
classdock roster sync --assignment=python-basics --org=soc-cs3550-f25
```

## Rollback

If you decide roster tracking isn't for you:

### Option 1: Keep But Don't Use

Simply don't run roster commands. Database exists but doesn't affect workflows.

### Option 2: Disable Orchestrator Integration

Remove from `assignment.conf`:
```bash
# step_sync_roster=true  # Commented out or removed
```

### Option 3: Complete Removal

```bash
# Remove database
rm ~/.config/classdock/roster.db

# Uninstall package (if you want)
# (Not necessary - roster is built-in)
```

## Performance Impact

The roster system has **minimal performance impact**:

- **Database size**: ~50KB for 100 students
- **Query time**: <10ms for typical operations
- **Sync time**: ~1-2 seconds for 50 repositories
- **Storage**: Local SQLite file (no external dependencies)

## Frequently Asked Questions

### Q: Do I need to update existing assignment.conf files?

**A:** No! Roster tracking is optional. Existing configurations work as-is.

### Q: Will this break my CI/CD pipelines?

**A:** No. If roster database doesn't exist, roster features are skipped silently.

### Q: Can I use roster tracking with legacy bash scripts?

**A:** Yes. Roster commands are independent. You can mix Python and bash workflows.

### Q: What if I already track students in a spreadsheet?

**A:** Export your spreadsheet to CSV and import it. The roster database doesn't replace your spreadsheet - it complements automated workflows.

### Q: Do I need to migrate all at once?

**A:** No. You can migrate one course or one assignment at a time.

### Q: Can I still use student-repos.txt?

**A:** Yes! The file-based approach still works. Roster tracking is an additional feature, not a replacement.

## Getting Help

If you encounter issues during migration:

1. **Check roster status**: `classdock roster status`
2. **View documentation**: `docs/ROSTER_SYNC.md`
3. **Check logs**: Run with `--verbose` flag
4. **File an issue**: https://github.com/hugo-valle/classdock/issues

## Summary

**Migration Checklist:**

- [ ] Run `classdock roster init`
- [ ] Import student roster CSV
- [ ] Test with manual sync first
- [ ] (Optional) Enable orchestrator integration
- [ ] Verify with `classdock roster status`

**Remember**: Migration is **optional** and **non-breaking**. You can adopt roster features at your own pace!
