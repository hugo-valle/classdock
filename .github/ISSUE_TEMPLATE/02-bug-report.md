---
name: 🐛 Bug Report
about: Report a bug or issue with ClassDock
title: '[BUG] '
labels: ['bug']
assignees: []
---

## 🌿 Branch Creation Instructions

**When you're ready to fix this bug:**

1. **Sync with latest code:**
   ```bash
   git checkout main
   git pull origin main
   ```

2. **Create bugfix branch:**
   ```bash
   # Use format: bugfix/issue-number-descriptive-name
   git checkout -b bugfix/123-fix-issue-description
   
   # Examples:
   git checkout -b bugfix/456-fix-login-authentication
   git checkout -b bugfix/789-resolve-config-parsing
   git checkout -b bugfix/101-handle-api-timeout
   ```

3. **Push branch to your fork:**
   ```bash
   git push -u origin bugfix/123-fix-issue-description
   ```

**Branch Naming Rules:**
- Must start with `bugfix/`
- Include issue number: `bugfix/123-descriptive-name`
- Use lowercase with hyphens (kebab-case)
- Be descriptive of what is being fixed
- Follow pattern: `bugfix/issue-number-fix-what-is-broken`

---

## 🐛 Bug Description

**Summary:**
A clear and concise description of what the bug is.

**Related Branch Type:** `bugfix/`

## 🔄 Steps to Reproduce

1. Go to '...'
2. Run command '...'
3. Enter input '...'
4. See error

**Minimal Reproduction:**
```bash
# Exact commands that reproduce the issue
classdock command --option value
```

## 🎯 Expected Behavior

Describe what you expected to happen.

## ❌ Actual Behavior

Describe what actually happened instead.

## 📊 Error Details

**Error Message:**
```
Paste the complete error message here
```

**Stack Trace:**
```
Full stack trace if available
```

**Exit Code:**
What exit code did the command return? (if applicable)

## 🖥️ Environment Information

**ClassDock Version:**
```bash
# Output of: classdock --version
```

**System Information:**
- OS: [e.g., macOS 13.5, Ubuntu 22.04, Windows 11]
- Python Version: [e.g., 3.11.5]
- Poetry Version: [e.g., 1.6.1]
- Shell: [e.g., bash, zsh, PowerShell]

**Installation Method:**
- [ ] PyPI (`pip install classdock`)
- [ ] Development install (`poetry install`)
- [ ] Other: _________________

**Python Environment:**
```bash
# Output of: poetry env info
# Or: python --version && which python
```

## 📁 Configuration

**Configuration Files:**
```yaml
# Contents of relevant config files (remove sensitive data)
# assignment.conf, .classdock/config.yml, etc.
```

**Environment Variables:**
```bash
# Relevant environment variables (remove tokens/secrets)
GITHUB_TOKEN=<redacted>
CLASSROOM_PILOT_CONFIG=...
```

## 🔍 Additional Context

**Related Issues:**
- Related to #(issue number)
- Duplicate of #(issue number)

**Workaround:**
Describe any workaround you've found (if applicable).

**Frequency:**
- [ ] Always occurs
- [ ] Occurs sometimes
- [ ] Occurred once
- [ ] Only in specific conditions

**Impact:**
- [ ] Blocks core functionality
- [ ] Reduces functionality
- [ ] Minor inconvenience
- [ ] Cosmetic issue

## 📎 Attachments

**Log Files:**
```
# Relevant log output (remove sensitive information)
```

**Screenshots:**
If applicable, add screenshots to help explain the problem.

**Sample Files:**
Attach any configuration files, scripts, or other files that help reproduce the issue.

---

## 🔧 Developer Investigation

**Affected Components:**
- [ ] CLI interface (`cli.py`)
- [ ] Assignments module (`assignments/`)
- [ ] Repository operations (`repos/`)
- [ ] Secret management (`secrets/`)
- [ ] Automation (`automation/`)
- [ ] Configuration (`config/`)
- [ ] Utilities (`utils/`)
- [ ] GitHub API integration
- [ ] Dependencies

**Potential Root Cause:**
- [ ] Logic error
- [ ] Configuration issue
- [ ] Environment issue
- [ ] Dependency conflict
- [ ] GitHub API change
- [ ] Authentication problem
- [ ] Permission issue

**Testing Checklist:**
- [ ] Reproduced locally
- [ ] Tested on multiple platforms
- [ ] Verified with clean environment
- [ ] Checked with different Python versions
- [ ] Validated configuration

---

## 📝 Fix Planning

**Branch Naming:**
- [ ] Use `bugfix/descriptive-name` branch naming convention
- [ ] Follow branch-name-check.yml requirements

**Development Standards:**
- [ ] Follow PEP 8 coding standards
- [ ] Add type hints for any new code
- [ ] Write comprehensive docstrings
- [ ] Maintain 100% test pass rate
- [ ] Add regression tests

**Testing Requirements:**
- [ ] Unit tests for the fix
- [ ] Integration tests covering the bug scenario
- [ ] Regression tests to prevent future occurrences
- [ ] Manual testing with reproduction steps

**Quality Assurance:**
- [ ] All tests pass (`poetry run pytest tests/ -v`)
- [ ] CLI works locally (`poetry run classdock --help`)
- [ ] Code formatting (`poetry run black --check`)
- [ ] Import sorting (`poetry run isort --check-only`)
- [ ] Type checking (`poetry run mypy`)

**Documentation:**
- [ ] Updated relevant documentation
- [ ] Added troubleshooting notes if needed
- [ ] Updated CHANGELOG.md

---

*Thank you for reporting this bug! Your help makes ClassDock more reliable for all users.*