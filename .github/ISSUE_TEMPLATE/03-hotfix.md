---
name: 🚨 Hotfix
about: Report a critical issue requiring immediate attention
title: '[HOTFIX] '
labels: ['hotfix', 'critical', 'urgent']
assignees: []
---

## 🌿 Emergency Branch Creation Instructions

**For critical hotfix (authorized personnel only):**

1. **Sync with production code:**
   ```bash
   git checkout main
   git pull origin main
   ```

2. **Create hotfix branch:**
   ```bash
   # Use format: hotfix/issue-number-critical-fix-name
   git checkout -b hotfix/123-fix-critical-issue
   
   # Examples:
   git checkout -b hotfix/456-fix-security-vulnerability
   git checkout -b hotfix/789-resolve-production-crash
   git checkout -b hotfix/101-patch-data-corruption
   ```

3. **Push branch immediately:**
   ```bash
   git push -u origin hotfix/123-fix-critical-issue
   ```

**Emergency Branch Rules:**
- Must start with `hotfix/`
- Include issue number: `hotfix/123-descriptive-name`
- Branch from `main` (not develop)
- Use lowercase with hyphens (kebab-case)
- Be descriptive of critical issue
- Follow pattern: `hotfix/issue-number-fix-critical-problem`

⚠️ **Note:** Hotfixes bypass normal development flow and go directly to production

---

## 🚨 Critical Issue Alert

**Summary:**
Brief description of the critical issue requiring immediate attention.

**Related Branch Type:** `hotfix/`

**Severity Level:**
- [ ] **P0 - Critical**: System is down or completely unusable
- [ ] **P1 - High**: Major functionality broken, significant user impact
- [ ] **P2 - Medium**: Important feature broken, moderate user impact

## 🔥 Impact Assessment

**User Impact:**
- Number of affected users: ___________
- Affected functionality: ___________
- Business impact: ___________

**System Impact:**
- [ ] Complete system failure
- [ ] Core functionality broken
- [ ] Security vulnerability
- [ ] Data loss risk
- [ ] Performance degradation
- [ ] Integration failure

**Urgency Justification:**
Explain why this requires immediate hotfix rather than regular bug fix process.

## 🔍 Problem Details

**What's Broken:**
Detailed description of the issue.

**Error Symptoms:**
```bash
# Error messages, stack traces, or failure indicators
```

**Reproduction Steps:**
1. Step 1
2. Step 2
3. Step 3
4. Issue occurs

**When It Started:**
- [ ] After latest release
- [ ] After specific change
- [ ] Gradually over time
- [ ] Suddenly without changes
- [ ] Unknown

## 🖥️ Environment Information

**Affected Versions:**
- ClassDock Version: ___________
- Python Version: ___________
- Platform: ___________

**Affected Environments:**
- [ ] Production (PyPI)
- [ ] Development
- [ ] CI/CD
- [ ] All environments

## 🛠️ Immediate Actions Taken

**Mitigation Steps:**
- [ ] Rolled back to previous version
- [ ] Disabled affected feature
- [ ] Applied temporary workaround
- [ ] Contacted users
- [ ] Other: ___________

**Current Status:**
- [ ] Issue contained
- [ ] Users notified
- [ ] Workaround available
- [ ] Still investigating

## 🎯 Proposed Solution

**Root Cause (if known):**
Description of what caused the issue.

**Fix Strategy:**
- [ ] Revert problematic changes
- [ ] Apply minimal fix
- [ ] Configuration change
- [ ] Dependency update
- [ ] Other: ___________

**Affected Files/Components:**
- [ ] CLI interface (`cli.py`)
- [ ] Assignments module (`assignments/`)
- [ ] Repository operations (`repos/`)
- [ ] Secret management (`secrets/`)
- [ ] Configuration (`config/`)
- [ ] Dependencies (`pyproject.toml`)
- [ ] Other: ___________

## ⚡ Hotfix Implementation Plan

**Immediate Steps:**
1. [ ] Create hotfix branch from main
2. [ ] Apply minimal fix
3. [ ] Test fix thoroughly
4. [ ] Deploy to staging
5. [ ] Deploy to production
6. [ ] Monitor for issues
7. [ ] Communicate resolution

**Branch Strategy:**
- [ ] Branch from: `main`
- [ ] Branch name: `hotfix/descriptive-name`
- [ ] Merge target: `main`
- [ ] Follow-up PR to: `develop` (if applicable)

**Testing Requirements:**
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing of fix
- [ ] Regression testing
- [ ] Performance testing (if relevant)

## 📋 Quality Gates

**Pre-Deployment Checklist:**
- [ ] Fix verified locally
- [ ] All tests pass
- [ ] Code reviewed
- [ ] Staging deployment successful
- [ ] Manual testing complete
- [ ] Performance impact assessed
- [ ] Rollback plan ready

**Post-Deployment Monitoring:**
- [ ] Error rates
- [ ] Performance metrics
- [ ] User feedback
- [ ] System health

## 📢 Communication Plan

**Stakeholder Notification:**
- [ ] Development team
- [ ] Users/customers
- [ ] Support team
- [ ] Management

**Communication Channels:**
- [ ] GitHub issue updates
- [ ] Documentation updates
- [ ] Release notes
- [ ] User notifications

## 📚 Documentation Updates

**Required Updates:**
- [ ] CHANGELOG.md
- [ ] Version bump
- [ ] Release notes
- [ ] Troubleshooting guides
- [ ] User documentation

## 🔄 Follow-up Actions

**Post-Hotfix Tasks:**
- [ ] Root cause analysis
- [ ] Process improvements
- [ ] Additional testing
- [ ] Documentation updates
- [ ] Team retrospective

**Prevention Measures:**
- [ ] Add regression tests
- [ ] Improve monitoring
- [ ] Update CI/CD checks
- [ ] Review code review process
- [ ] Update testing procedures

## 📊 Timeline

**Target Resolution:**
- Discovery: ___________
- Fix Development: ___________
- Testing: ___________
- Deployment: ___________
- Verification: ___________

---

## ⚠️ Emergency Contacts

**Primary Developer:** @username
**Backup Developer:** @username
**Release Manager:** @username

---

*This is a critical issue requiring immediate attention. Please follow the hotfix process and prioritize resolution.*