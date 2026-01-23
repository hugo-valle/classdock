# CI/CD and Automated Release Workflow

This document describes the automated Continuous Integration and Continuous Deployment (CI/CD) pipeline for `classdock`.

## 🎯 Overview

The CI/CD pipeline automates:
- **Testing**: Comprehensive test suite across multiple Python versions
- **Building**: Package creation and validation
- **Publishing**: Automated PyPI publication
- **Releases**: GitHub release creation with notes
- **Documentation**: Automatic updates to publication history

## 🔄 Workflow Triggers

### Automatic Triggers

1. **Git Tags** (Release Publication):
   ```bash
   git tag v3.0.0-alpha.2
   git push origin main --tags
   ```
   - Triggers full CI/CD pipeline
   - Publishes to PyPI
   - Creates GitHub release

2. **Main Branch** (Version Updates):
   ```bash
   # Update version in pyproject.toml
   git add pyproject.toml
   git commit -m "bump: version 3.0.0-alpha.2"
   git push origin main
   ```
   - Runs tests only (no publication)
   - Validates version change

### Manual Triggers

3. **Workflow Dispatch**:
   - Manual trigger from GitHub Actions UI
   - Optional version override
   - Useful for hotfixes or special releases

## 🏗️ Pipeline Architecture

### Job 1: Test Suite (`test`)

**Runs on**: `ubuntu-latest`
**Matrix**: Python 3.10, 3.11, 3.12

```yaml
Steps:
1. Checkout code
2. Setup Python matrix
3. Install Poetry
4. Cache dependencies
5. Install project
6. Run 153 tests
7. Generate coverage report
8. Upload to Codecov
```

**Success Criteria**:
- All 153 tests pass
- Coverage report generated
- No linting errors

### Job 2: Build & Publish (`publish`)

**Runs on**: `ubuntu-latest`
**Depends on**: `test` job success
**Triggers**: Tags or manual dispatch

```yaml
Steps:
1. Checkout with full history
2. Setup Python 3.12
3. Install Poetry
4. Extract/validate version
5. Build package (wheel + sdist)
6. Verify build contents
7. Publish to PyPI
8. Create release notes
9. Create GitHub release
10. Verify publication
```

**Environment**:
- **Name**: `pypi`
- **URL**: https://pypi.org/project/classdock/
- **Permissions**: Trusted publishing

### Job 3: Update Documentation (`update-docs`)

**Runs on**: `ubuntu-latest`
**Depends on**: `publish` job success
**Triggers**: Tag releases only

```yaml
Steps:
1. Checkout code
2. Update PYPI_PUBLICATION.md
3. Commit and push changes
```

## 🔐 Security Configuration

### Required Repository Secrets

Add these secrets in GitHub repository settings:

1. **`PYPI_API_TOKEN`**:
   - PyPI API token for publishing
   - Format: `pypi-...`
   - Scope: Project or organization

2. **`GITHUB_TOKEN`**:
   - Automatically provided by GitHub
   - Used for releases and documentation updates

### Trusted Publishing (Recommended)

For enhanced security, configure trusted publishing:

1. **PyPI Trusted Publishers**:
   - Go to https://pypi.org/manage/project/classdock/settings/
   - Add GitHub as trusted publisher
   - Repository: `hugo-valle/classdock`
   - Workflow: `publish.yml`

2. **Remove API Token**:
   - Delete `PYPI_API_TOKEN` secret
   - Pipeline will use OIDC authentication

## 📦 Release Process

### Standard Release Workflow

1. **Prepare Release**:
   ```bash
   # Update version
   poetry version 3.0.0-alpha.2
   
   # Update CHANGELOG.md
   git add pyproject.toml CHANGELOG.md
   git commit -m "release: prepare v3.0.0-alpha.2"
   git push origin main
   ```

2. **Create Release**:
   ```bash
   # Create and push tag
   git tag v3.0.0-alpha.2
   git push origin main --tags
   ```

3. **Automated Actions**:
   - GitHub Actions triggers automatically
   - Tests run across Python versions
   - Package builds and publishes to PyPI
   - GitHub release created with notes
   - Documentation updated

### Hotfix Release Workflow

1. **Create Hotfix Branch**:
   ```bash
   git checkout -b hotfix/v3.0.0-alpha.2
   # Apply fixes
   poetry version patch  # 3.0.0-alpha.1 → 3.0.0-alpha.2
   ```

2. **Manual Trigger**:
   - Use GitHub Actions UI
   - Select "Workflow Dispatch"
   - Specify version: `3.0.0-alpha.2`

## 🔍 Monitoring and Debugging

### Pipeline Status

Monitor pipeline status at:
- **Actions**: https://github.com/hugo-valle/classdock/actions
- **PyPI**: https://pypi.org/project/classdock/
- **Codecov**: Coverage reports and trends

### Common Issues and Solutions

1. **Test Failures**:
   ```bash
   # Run tests locally first
   poetry run pytest tests/ -v
   ```

2. **Build Failures**:
   ```bash
   # Validate configuration
   poetry check
   poetry build
   ```

3. **Publication Failures**:
   - Check PyPI API token
   - Verify version uniqueness
   - Check network connectivity

4. **Version Conflicts**:
   ```bash
   # Ensure version is incremented
   poetry version --dry-run patch
   ```

### Debug Mode

Enable debug logging by adding to workflow:
```yaml
env:
  ACTIONS_STEP_DEBUG: true
  ACTIONS_RUNNER_DEBUG: true
```

## 📊 Pipeline Metrics

### Performance Targets

- **Test Duration**: < 5 minutes
- **Build Duration**: < 2 minutes
- **Total Pipeline**: < 10 minutes
- **Success Rate**: > 95%

### Quality Gates

All must pass for successful release:
- ✅ 153 tests passing (100% pass rate)
- ✅ Code coverage > 80%
- ✅ No security vulnerabilities
- ✅ Package builds without errors
- ✅ PyPI publication successful

## 🚀 Future Enhancements

### Planned Improvements

1. **Multi-Platform Testing**:
   - Add Windows and macOS runners
   - Test installation across platforms

2. **Security Scanning**:
   - Add dependency vulnerability scanning
   - SAST (Static Application Security Testing)

3. **Performance Testing**:
   - Benchmark CLI command performance
   - Track installation time metrics

4. **Documentation Automation**:
   - Auto-generate API documentation
   - Update README badges automatically

### Advanced Features

1. **Canary Releases**:
   - Test releases with subset of users
   - Gradual rollout strategy

2. **Rollback Automation**:
   - Automatic rollback on critical failures
   - Health check monitoring

3. **Multi-Environment Deployment**:
   - Staging PyPI (TestPyPI)
   - Production PyPI
   - Internal package registry

## 📝 Best Practices

### Commit Messages

Use conventional commits for automation:
```bash
feat: add new automation feature
fix: resolve CLI argument parsing
docs: update API documentation
test: add edge case coverage
bump: version 3.0.0-alpha.2
```

### Version Management

Follow semantic versioning:
- **Breaking changes**: Major version bump
- **New features**: Minor version bump
- **Bug fixes**: Patch version bump
- **Pre-releases**: Alpha/beta/rc suffixes

### Testing Strategy

Maintain comprehensive test coverage:
- **Unit tests**: Individual component testing
- **Integration tests**: Component interaction testing
- **End-to-end tests**: Full workflow validation
- **Regression tests**: Prevent known issue recurrence

---

*This CI/CD pipeline ensures reliable, automated releases while maintaining high quality standards.*
