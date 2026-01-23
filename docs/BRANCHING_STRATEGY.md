# 🌿 Branching Strategy & Release Workflow

## Overview
This document defines the branching strategy, merge rules, and automated release workflow for the classdock project.

## Branch Structure

### Primary Branches

#### `develop` (Default Branch)
- **Purpose**: Main development branch
- **Protection**: Requires PR reviews, CI passes
- **Merges from**: `feature/*`, `bugfix/*`, `hotfix/*`
- **Merges to**: `release/*` branches only

#### `main` (Production Branch)  
- **Purpose**: Production-ready, stable code
- **Protection**: Requires PR reviews, CI passes, admin override only
- **Merges from**: `release/*`, `hotfix/*` 
- **Triggers**: PyPI publication, GitHub releases

### Supporting Branches

#### `feature/*` - New Features
- **Naming**: `feature/issue-number-short-description` or `feature/short-description`
- **Source**: Branch from `develop`
- **Merge to**: `develop` via Pull Request
- **Lifecycle**: Delete after merge
- **Example**: `feature/123-add-assignment-templates`

#### `bugfix/*` - Bug Fixes
- **Naming**: `bugfix/issue-number-short-description`
- **Source**: Branch from `develop`
- **Merge to**: `develop` via Pull Request
- **Lifecycle**: Delete after merge
- **Example**: `bugfix/456-fix-repo-clone-timeout`

#### `release/*` - Release Preparation
- **Naming**: `release/vX.Y.Z` (semantic version)
- **Source**: Branch from `develop`
- **Purpose**: Final testing, documentation, version bumping
- **Merge to**: `main` via Pull Request → **TRIGGERS PYPI RELEASE**
- **Lifecycle**: Keep for historical reference
- **Example**: `release/v3.1.0`, `release/v3.1.0b2`

#### `hotfix/*` - Critical Production Fixes
- **Naming**: `hotfix/issue-number-short-description`
- **Source**: Branch from `main`
- **Merge to**: `main` AND `develop` (dual merge)
- **Purpose**: Critical production bug fixes
- **Lifecycle**: Delete after dual merge
- **Example**: `hotfix/789-security-vulnerability`

## Release Workflow

### 1. Development Phase
```
feature/new-feature → develop (via PR)
bugfix/fix-bug → develop (via PR)
```

### 2. Release Preparation
```
develop → release/vX.Y.Z (branch creation)
```
**Actions in release branch:**
- Update version in `pyproject.toml` and `__init__.py`
- Update `CHANGELOG.md`
- Final testing and documentation
- Address any release-specific issues

### 3. Release Deployment
```
release/vX.Y.Z → main (via PR) 
```
**Automated Actions:**
- ✅ Create Git tag `X.Y.Z` (no 'v' prefix for PyPI compatibility)
- ✅ Build and publish to PyPI
- ✅ Create GitHub Release with notes
- ✅ Run full CI/CD pipeline

### 4. Post-Release Sync
```
main → develop (merge back)
```
**Actions:**
- Sync version numbers
- Ensure develop has all release changes

### 5. Hotfix Process (Emergency)
```
main → hotfix/critical-fix → main (via PR)
            ↓
         develop (via PR)
```

## Automated Triggers

### CI/CD Workflows

#### `ci.yml` - Continuous Integration
- **Triggers**: Push/PR to `develop`, `main`
- **Actions**: Run tests, linting, security scans
- **Matrix**: Python 3.10, 3.11, 3.12

#### `publish.yml` - PyPI Publication
- **Triggers**: 
  - Merge to `main` from `release/*` branch
  - Manual workflow dispatch
- **Actions**: Build, test, publish to PyPI, create GitHub release

#### `auto-release.yml` - Hotfix Releases
- **Triggers**: Merge to `main` from `hotfix/*` branch
- **Actions**: Auto-increment patch version, publish hotfix

### Version Management

### Semantic Versioning
- **MAJOR.MINOR.PATCH** (e.g., `3.1.0`)
- **Pre-releases**: `3.1.0a1` (alpha), `3.1.0b1` (beta), `3.1.0rc1` (release candidate)

### Version Synchronization
All versions must be updated consistently:
- `pyproject.toml` → `version = "X.Y.Z"`
- `classdock/__init__.py` → `__version__ = "X.Y.Z"`
- Git tag → `X.Y.Z` (auto-created, no 'v' prefix for PyPI compatibility)

### Branch and Tag Naming
- **Branch names**: `release/vX.Y.Z` (with 'v' prefix for clarity)
- **Git tags**: `X.Y.Z` (without 'v' prefix for PyPI compatibility)  
- **Display names**: Can use 'v' prefix for readability (e.g., "classdock v3.1.0")

### Release Types

#### Alpha Releases (`X.Y.Za1`)
- **Source**: `develop` branch
- **Purpose**: Early testing, major features
- **Trigger**: Manual tag creation

#### Beta Releases (`X.Y.Zb1`)
- **Source**: `release/*` branch  
- **Purpose**: Feature complete, final testing
- **Trigger**: `release/*` → `main` merge

#### Release Candidates (`X.Y.Zrc1`)
- **Source**: `release/*` branch
- **Purpose**: Production ready, final validation
- **Trigger**: `release/*` → `main` merge

#### Stable Releases (`X.Y.Z`)
- **Source**: `release/*` branch
- **Purpose**: Production deployment
- **Trigger**: `release/*` → `main` merge

## Branch Protection Rules

### `develop` Branch
- ✅ Require pull request reviews (2 reviewers)
- ✅ Require status checks to pass (CI)
- ✅ Require branches to be up to date
- ✅ Include administrators
- ❌ Allow force pushes
- ❌ Allow deletions

### `main` Branch
- ✅ Require pull request reviews (2 reviewers) 
- ✅ Require status checks to pass (CI)
- ✅ Require branches to be up to date
- ✅ Include administrators
- ✅ Restrict pushes (admins only)
- ❌ Allow force pushes
- ❌ Allow deletions

## Workflow Examples

### Feature Development
```bash
# 1. Create feature branch from develop
git checkout develop
git pull origin develop
git checkout -b feature/new-awesome-feature

# 2. Develop and commit
git add .
git commit -m "feat: add awesome new feature"
git push origin feature/new-awesome-feature

# 3. Create PR: feature/new-awesome-feature → develop
# 4. After review and CI passes, merge and delete branch
```

### Release Process
```bash
# 1. Create release branch from develop
git checkout develop
git pull origin develop
git checkout -b release/v3.2.0

# 2. Update version and changelog
# Edit pyproject.toml: version = "3.2.0"
# Edit classdock/__init__.py: __version__ = "3.2.0"
# Update docs/CHANGELOG.md

# 3. Test and commit
git add .
git commit -m "release: prepare v3.2.0"
git push origin release/v3.2.0

# 4. Create PR: release/v3.2.0 → main
# 5. After merge, automatic PyPI publication occurs
```

### Hotfix Process
```bash
# 1. Create hotfix branch from main
git checkout main
git pull origin main
git checkout -b hotfix/critical-security-fix

# 2. Fix issue and test
git add .
git commit -m "fix: resolve critical security vulnerability"
git push origin hotfix/critical-security-fix

# 3. Create PR: hotfix/critical-security-fix → main
# 4. Create PR: hotfix/critical-security-fix → develop
# 5. After merges, automatic patch release occurs
```

## Best Practices

### Commit Messages
Use [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `style:` - Code style changes
- `refactor:` - Code refactoring
- `test:` - Test additions/changes
- `chore:` - Maintenance tasks

### PR Guidelines
- **Title**: Clear, descriptive summary
- **Description**: Link to issues, explain changes
- **Labels**: Use appropriate labels (feature, bugfix, etc.)
- **Reviewers**: Assign relevant team members
- **Checks**: Ensure all CI checks pass

### Version Strategy
- **Major**: Breaking changes, major new features
- **Minor**: New features, backward compatible
- **Patch**: Bug fixes, backward compatible
- **Pre-release**: Testing versions (alpha, beta, rc)

---

*This strategy ensures predictable, automated releases while maintaining code quality and stability.*