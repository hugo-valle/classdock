# GitHub Labels Documentation

This document explains the labeling system used in the ClassDock project for issues and pull requests.

## 📋 Label Categories

### Issue Type Labels

These labels are automatically applied by issue templates:

| Label | Description | Color | Used In Template |
|-------|-------------|-------|------------------|
| `enhancement` | New feature or request | ![#a2eeef](https://via.placeholder.com/15/a2eeef/000000?text=+) | Feature Request |
| `feature` | A new feature | ![#0075ca](https://via.placeholder.com/15/0075ca/000000?text=+) | Feature Request |
| `bug` | Something isn't working | ![#d73a4a](https://via.placeholder.com/15/d73a4a/000000?text=+) | Bug Report |
| `hotfix` | Critical issue requiring immediate attention | ![#b60205](https://via.placeholder.com/15/b60205/000000?text=+) | Hotfix |
| `critical` | Critical priority issue | ![#b60205](https://via.placeholder.com/15/b60205/000000?text=+) | Hotfix |
| `urgent` | Urgent priority issue | ![#d93f0b](https://via.placeholder.com/15/d93f0b/000000?text=+) | Hotfix |
| `documentation` | Improvements or additions to documentation | ![#0075ca](https://via.placeholder.com/15/0075ca/000000?text=+) | Documentation |
| `maintenance` | Regular maintenance and upkeep | ![#fef2c0](https://via.placeholder.com/15/fef2c0/000000?text=+) | Maintenance |
| `chore` | Routine tasks and maintenance | ![#fef2c0](https://via.placeholder.com/15/fef2c0/000000?text=+) | Maintenance |
| `release` | Release preparation and management | ![#0e8a16](https://via.placeholder.com/15/0e8a16/000000?text=+) | Release |

### Priority Labels

Use these to indicate issue priority (referenced in hotfix template):

| Label | Description | Color | When to Use |
|-------|-------------|-------|-------------|
| `P0` | Critical - System down or unusable | ![#b60205](https://via.placeholder.com/15/b60205/000000?text=+) | Complete system failure |
| `P1` | High - Major functionality broken | ![#d93f0b](https://via.placeholder.com/15/d93f0b/000000?text=+) | Significant user impact |
| `P2` | Medium - Important feature broken | ![#fbca04](https://via.placeholder.com/15/fbca04/000000?text=+) | Moderate user impact |
| `P3` | Low - Minor issues | ![#0e8a16](https://via.placeholder.com/15/0e8a16/000000?text=+) | Cosmetic or minor issues |

### Security Labels

For security-related issues (referenced in workflows):

| Label | Description | Color |
|-------|-------------|-------|
| `security` | Security-related issues | ![#d73a4a](https://via.placeholder.com/15/d73a4a/000000?text=+) |
| `vulnerability` | Security vulnerability | ![#b60205](https://via.placeholder.com/15/b60205/000000?text=+) |
| `high-priority` | High priority item | ![#d93f0b](https://via.placeholder.com/15/d93f0b/000000?text=+) |

### Component Labels

To categorize by affected component:

| Label | Description | Color |
|-------|-------------|-------|
| `cli` | Command-line interface related | ![#c5def5](https://via.placeholder.com/15/c5def5/000000?text=+) |
| `api` | API related changes | ![#c5def5](https://via.placeholder.com/15/c5def5/000000?text=+) |
| `testing` | Testing related changes | ![#c5def5](https://via.placeholder.com/15/c5def5/000000?text=+) |
| `automation` | Automation and workflows | ![#c5def5](https://via.placeholder.com/15/c5def5/000000?text=+) |
| `config` | Configuration changes | ![#c5def5](https://via.placeholder.com/15/c5def5/000000?text=+) |

### Status Labels

To track issue/PR status:

| Label | Description | Color |
|-------|-------------|-------|
| `ready for review` | Ready for code review | ![#0e8a16](https://via.placeholder.com/15/0e8a16/000000?text=+) |
| `work in progress` | Work in progress | ![#fbca04](https://via.placeholder.com/15/fbca04/000000?text=+) |
| `blocked` | Blocked by external dependency | ![#d73a4a](https://via.placeholder.com/15/d73a4a/000000?text=+) |
| `needs more info` | More information needed from author | ![#d876e3](https://via.placeholder.com/15/d876e3/000000?text=+) |

### General Labels

Standard GitHub labels for workflow:

| Label | Description | Color |
|-------|-------------|-------|
| `dependencies` | Pull requests that update a dependency file | ![#0366d6](https://via.placeholder.com/15/0366d6/000000?text=+) |
| `duplicate` | This issue or pull request already exists | ![#cfd3d7](https://via.placeholder.com/15/cfd3d7/000000?text=+) |
| `good first issue` | Good for newcomers | ![#7057ff](https://via.placeholder.com/15/7057ff/000000?text=+) |
| `help wanted` | Extra attention is needed | ![#008672](https://via.placeholder.com/15/008672/000000?text=+) |
| `invalid` | This doesn't seem right | ![#e4e669](https://via.placeholder.com/15/e4e669/000000?text=+) |
| `question` | Further information is requested | ![#d876e3](https://via.placeholder.com/15/d876e3/000000?text=+) |
| `wontfix` | This will not be worked on | ![#ffffff](https://via.placeholder.com/15/ffffff/000000?text=+) |

## 🔄 Automatic Label Management

### Issue Templates

Labels are automatically applied when creating issues using templates:

- **Feature Request** → `enhancement`, `feature`
- **Bug Report** → `bug`
- **Hotfix** → `hotfix`, `critical`, `urgent`
- **Documentation** → `documentation`
- **Maintenance** → `maintenance`, `chore`
- **Release** → `release`

### Label Sync Workflow

The repository includes a GitHub Action (`.github/workflows/sync-labels.yml`) that automatically syncs labels when:

- Changes are made to `.github/labels.yml`
- Manually triggered via workflow dispatch
- Push to `main` or `develop` branches

## 📝 Usage Guidelines

### For Issue Authors

1. **Use appropriate templates** - Labels will be applied automatically
2. **Add priority labels** if needed (P0-P3)
3. **Add component labels** to categorize the affected area
4. **Update status labels** as work progresses

### For Maintainers

1. **Review automatic labels** and adjust if needed
2. **Add priority labels** for proper triage
3. **Use status labels** to track progress
4. **Apply component labels** for better organization

### Example Label Combinations

**Critical Bug:**
```
bug, P0, critical, cli
```

**New Feature:**
```
enhancement, feature, P2, automation
```

**Documentation Update:**
```
documentation, P3, good first issue
```

**Security Issue:**
```
security, vulnerability, P1, critical
```

## 🛠️ Managing Labels

### Sync Labels Manually

```bash
# Install GitHub CLI if not already installed
# brew install gh

# Sync labels from configuration
gh label sync --file .github/labels.yml
```

### Update Label Configuration

1. Edit `.github/labels.yml`
2. Commit and push changes
3. Labels will be automatically synced via GitHub Actions

### Add New Labels

Add new labels to `.github/labels.yml`:

```yaml
- name: "new-label"
  description: "Description of new label"
  color: "hex-color-code"
```

## 🎯 Best Practices

1. **Consistent Naming**: Use lowercase with hyphens for multi-word labels
2. **Clear Descriptions**: Provide helpful descriptions for all labels
3. **Color Coding**: Use consistent colors for related label categories
4. **Regular Review**: Periodically review and clean up unused labels
5. **Template Integration**: Ensure issue templates reference correct labels

---

*This labeling system helps maintain organization and enables efficient issue triage and project management.*