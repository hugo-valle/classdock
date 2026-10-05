# Cycle Collaborator - Repository Access Fix Tool

The Cycle Collaborator script is designed to fix student repository access issues commonly encountered in GitHub environments. It provides intelligent detection and resolution of permission problems by cycling collaborator access.

## 🎯 Overview

GitHub occasionally experiences permission glitches where students lose access to their repositories despite being properly enrolled. This script:

1. **Detects** repository access issues automatically
2. **Intelligently decides** when cycling is needed vs when access is already correct
3. **Safely cycles** collaborator permissions to restore access
4. **Reports** detailed status information and actions taken

## 🚀 Quick Start

### Configuration Mode (Recommended)
```bash
# Basic usage with configuration file
./scripts_legacy/cycle-collaborator.sh --config assignment.conf --batch student-repos.txt --repo-urls

# Preview actions without making changes
./scripts_legacy/cycle-collaborator.sh --config assignment.conf --batch student-repos.txt --repo-urls --dry-run

# Force cycling even when access appears correct
./scripts_legacy/cycle-collaborator.sh --config assignment.conf --batch student-repos.txt --repo-urls --force
```

### Traditional Mode
```bash
# Fix specific student
./scripts_legacy/cycle-collaborator.sh assignment1 student-username organization

# List status without making changes
./scripts_legacy/cycle-collaborator.sh --list assignment1 student-username organization
```

## 📋 Command Line Options

### Core Options
- `--config, -c <file>` - Read assignment configuration from file
- `--batch, -b <file>` - Process multiple users from a file
- `--repo-urls` - Treat batch file as repository URLs instead of usernames
- `--dry-run, -n` - Show what would be done without making changes
- `--list, -l` - List repository status without making changes
- `--verbose, -v` - Show detailed output
- `--force, -f` - Force cycling even when access appears correct
- `--help, -h` - Show help message

### Traditional Mode Parameters
```bash
./scripts_legacy/cycle-collaborator.sh [assignment_prefix] [username] [organization]
```

## 🧠 Intelligent Cycling Logic

### Normal Mode Behavior
The script uses intelligent detection to determine when cycling is actually needed:

1. **Repository Accessibility Check**
   - Verifies repository exists and is accessible
   - Checks if repository has content

2. **Permission Verification**
   - Confirms user is listed as a collaborator
   - Checks for pending invitations
   - Validates write access permissions

3. **Smart Decision Making**
   - **Access is correct**: Reports success and skips cycling
   - **Access has issues**: Automatically cycles permissions
   - **Ambiguous state**: Cycles to ensure proper access

### Force Mode Behavior
When `--force` flag is used:
- Cycles permissions regardless of detected access status
- Useful for troubleshooting persistent issues
- Clearly reports that force mode is active
- Still performs safety checks before cycling

## 🔄 Cycling Process

When cycling is determined to be necessary:

1. **Remove Existing Access**
   - Removes user from repository collaborators
   - Cancels any pending invitations
   - Cleans up existing permission state

2. **Re-invite User**
   - Adds user back as a collaborator with write permissions
   - Sends new invitation via GitHub email
   - Verifies successful invitation creation

3. **Verification**
   - Confirms new invitation was created
   - Reports final status and next steps for student

## 📁 File Formats

### Configuration File Format
Uses standard assignment.conf format:
```bash
GITHUB_ORGANIZATION="your-org"
ASSIGNMENT_PREFIX="assignment1"
```

### Batch File Formats

#### Username Mode (default)
```
student1-github
student2-username
student3-user
```

#### Repository URL Mode (use with --repo-urls)
```
https://github.com/org/assignment-student1
https://github.com/org/assignment-student2
https://github.com/org/assignment-student3
```

## 🎛️ Integration with Assignment Orchestrator

The cycle-collaborator script integrates seamlessly with the assignment orchestrator as Step 5:

```bash
# Enable in configuration
STEP_CYCLE_COLLABORATORS=true

# Run specific step
./scripts_legacy/assignment-orchestrator.sh --step cycle

# Include in full workflow
./scripts_legacy/assignment-orchestrator.sh
```

## 📊 Output and Status Reporting

### Successful Access (No Action Needed)
```
✅ Repository access is working correctly - no action needed.
   Student 'username' has proper collaborator access.

=== Summary ===
Repository: org/assignment-username
Student: username
Permission: write (verified)
Status: ✅ No action required - Repository access is already correct
```

### Access Issues Detected (Cycling Performed)
```
🔄 Repository has access issues - cycling collaborator permissions...

=== Fixing Repository Corruption ===
Removing any existing access and re-inviting username...
User is currently a collaborator, removing...
Adding username to org/assignment-username as writer...

=== Summary ===
Repository: org/assignment-username
Student: username
Permission: write
Status: ✅ Repository corruption fixed. New invitation sent to student via email
```

### Force Mode Active
```
🔄 Force mode enabled - cycling collaborator permissions anyway...
```

## 🚨 Error Handling

### Common Issues and Solutions

#### Repository Not Found
```
❌ Repository not accessible
```
- Verify repository URL is correct
- Check GitHub CLI authentication
- Confirm repository exists and you have access

#### User Not Found
```
❌ User not found or invalid username
```
- Verify GitHub username is correct
- Check if user account exists
- Ensure username matches GitHub profile

#### Permission Denied
```
❌ Insufficient permissions
```
- Verify you have admin access to the repository
- Check GitHub CLI authentication and permissions
- Ensure organization membership if applicable

### Recovery Procedures
1. **Check script output** for specific error messages
2. **Verify authentication** with `gh auth status`
3. **Test repository access** manually in GitHub web interface
4. **Re-run with verbose output** for debugging: `--verbose`
5. **Use dry-run mode** to test without making changes: `--dry-run`

## 🔒 Security Considerations

### Permission Requirements
- **Repository admin access** required for adding/removing collaborators
- **Organization membership** may be required depending on settings
- **GitHub CLI authentication** must have appropriate scopes

### Safe Operation
- **Pre-flight checks** verify access before making changes
- **Dry-run mode** allows testing without modifications
- **Detailed logging** tracks all actions taken
- **Rollback capability** through standard GitHub interfaces

### Data Privacy
- **No sensitive data** stored in logs
- **GitHub tokens** managed through GitHub CLI
- **Repository access** respects existing GitHub permissions

## 🎓 Best Practices

### When to Use Cycle-Collaborator
1. **Students report** they can't access their repositories
2. **GitHub permission glitches** affect multiple students
3. **Permission issues** persist after standard troubleshooting
4. **Batch processing** needed for entire class

### Recommended Workflow
1. **Start with list mode** to assess current status
2. **Use dry-run mode** to preview actions
3. **Run normal mode** to fix detected issues
4. **Use force mode** only for persistent problems
5. **Monitor output** for any errors or unexpected behavior

### Integration with Other Tools
- **Run after** repository discovery to ensure access
- **Combine with** secret management for complete setup
- **Use before** student assistance tools if access issues exist
- **Include in** regular maintenance workflows

---

**Note:** This tool is designed for GitHub environments where instructor has appropriate permissions to manage student repository access. Always test with dry-run mode first when using in new environments.
