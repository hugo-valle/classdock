# Labels Quick Reference

This is a quick reference for the labels used in the ClassDock project.

## 🏷️ Required Labels (Applied Automatically)

**Issue Templates automatically apply these labels:**

| Template | Auto Labels |
|----------|-------------|
| Feature Request | `enhancement`, `feature` |
| Bug Report | `bug` |
| Hotfix | `hotfix`, `critical`, `urgent` |
| Documentation | `documentation` |
| Maintenance | `maintenance`, `chore` |
| Release | `release` |

## 🚨 Priority Labels (Add Manually)

| Label | Use When |
|-------|----------|
| `P0` | System down or completely unusable |
| `P1` | Major functionality broken, significant impact |
| `P2` | Important feature broken, moderate impact |
| `P3` | Minor issues, cosmetic problems |

## 🔧 Component Labels (Add as Needed)

| Label | Component |
|-------|-----------|
| `cli` | Command-line interface |
| `api` | GitHub API integration |
| `testing` | Test suite changes |
| `automation` | Workflow automation |
| `config` | Configuration system |

## 📊 Status Labels (Update as Work Progresses)

| Label | Status |
|-------|--------|
| `ready for review` | PR is ready for code review |
| `work in progress` | Actively being worked on |
| `blocked` | Waiting on external dependency |
| `needs more info` | Author needs to provide more details |

## 🔒 Security Labels

| Label | Use For |
|-------|---------|
| `security` | General security-related issues |
| `vulnerability` | Known security vulnerabilities |
| `high-priority` | Security issues needing urgent attention |

## 🎯 Common Label Combinations

```
Critical Production Bug:
bug + P0 + critical + [component]

New Feature Request:
enhancement + feature + P2 + [component]

Security Issue:
security + vulnerability + P1 + critical

Documentation Update:
documentation + P3 + good first issue

Maintenance Task:
maintenance + chore + P3 + [component]
```

## 📋 Label Management

- **Automatic**: Issue templates apply base labels
- **Manual**: Add priority, component, and status labels as needed
- **Sync**: Labels are managed via `.github/labels.yml`
- **Updates**: Label sync happens automatically via GitHub Actions

For complete documentation, see [docs/LABELS.md](LABELS.md).