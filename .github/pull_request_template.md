# Pull Request

## 📋 Pull Request Information

**Type:** <!-- Choose one: Feature | Bugfix | Hotfix | Documentation | Maintenance | Release -->

**Issue Resolution:**
- **Primary Issue:** <!-- Use appropriate keyword --> #<!-- issue number -->
  - `Closes #123` (closes issue when merged)
  - `Fixes #123` (fixes bug when merged)
  - `Resolves #123` (resolves issue when merged)
- **Related Issues:**
  - `References #456` (links without closing)
  - `Addresses #789` (addresses concern)
  - `Part of #101` (part of larger work)

**Branch Type:** <!-- feature/ | bugfix/ | hotfix/ | docs/ | chore/ | release/ -->
**Target Branch:** <!-- develop (default) | main (releases/hotfixes only) -->

**GitHub Keywords Guide:**
<!-- 
Automatic Issue Closing Keywords:
- Closes, Fixes, Resolves + #number = closes issue when PR merges
- References, Addresses, See + #number = links without closing
- Part of, Contributes to + #number = for epics/milestones

Use multiple issues: "Closes #123, fixes #456, references #789"
-->

## 📝 Description

**What does this PR do?**
<!-- Brief description of changes -->

**Why is this change needed?**
<!-- Business justification or problem being solved -->

## 🔄 Changes Made

**Files Modified:**
- [ ] Core functionality
- [ ] CLI interface
- [ ] Configuration
- [ ] Tests
- [ ] Documentation
- [ ] Dependencies

**Type of Changes:**
- [ ] New feature
- [ ] Bug fix
- [ ] Breaking change
- [ ] Documentation update
- [ ] Maintenance/chore

## 🧪 Testing

**Testing Performed:**
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] CLI functionality verified

**Test Results:**
```bash
# Paste relevant test results
$ poetry run pytest tests/ -v
```

## 📚 Documentation

**Documentation Updates:**
- [ ] Code comments/docstrings
- [ ] README.md
- [ ] CHANGELOG.md
- [ ] CLI help text
- [ ] Other documentation

## ✅ Quality Checklist

**Code Quality:**
- [ ] Follows PEP 8 standards
- [ ] Type hints added
- [ ] Comprehensive docstrings
- [ ] No code duplication
- [ ] Error handling implemented

**Quality Gates:**
- [ ] `poetry run pytest tests/ -v` ✅
- [ ] `poetry run black --check` ✅
- [ ] `poetry run isort --check-only` ✅
- [ ] `poetry run mypy classdock/` ✅
- [ ] All CI checks pass ✅

## 🔒 Security & Performance

**Security:**
- [ ] No security vulnerabilities
- [ ] No sensitive data exposed
- [ ] Authentication handled properly

**Performance:**
- [ ] No performance regression
- [ ] Resource usage acceptable
- [ ] Performance tested

## 💥 Breaking Changes

**Breaking Changes:**
- [ ] CLI interface changes
- [ ] Configuration changes
- [ ] API changes
- [ ] No breaking changes ✅

**Migration Guide:**
<!-- If breaking changes, provide migration instructions -->

## 🌟 Additional Context

**Related Work:**
<!-- Links to related PRs, issues, or discussions -->

**Screenshots/Output:**
<!-- Add any relevant screenshots or command output -->

## 📋 Reviewer Checklist

**For Reviewers:**
- [ ] Code follows project standards
- [ ] Tests are comprehensive
- [ ] Documentation is complete
- [ ] No unintended changes
- [ ] Performance impact acceptable
- [ ] Security considerations addressed

---

**Ready for Review:** <!-- ✅ or ❌ -->

*Thank you for contributing to ClassDock!*