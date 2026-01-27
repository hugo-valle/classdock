# PyPI Publication Guide

This document outlines the process for publishing `classdock` to PyPI, both manual and automated approaches.

## 📦 Package Overview

- **Package Name**: `classdock`
- **PyPI URL**: https://pypi.org/project/classdock/
- **Current Version**: `3.0.0-alpha.1`
- **Installation**: `pip install classdock`

## 🚀 Manual Publication Process

### Prerequisites

1. **PyPI Account**: Register at https://pypi.org/account/register/
2. **API Token**: Generate at https://pypi.org/manage/account/token/
3. **Poetry**: Package management tool installed

### Configuration

Configure your PyPI credentials in `~/.pypirc`:

```ini
[pypi]
username = __token__
password = pypi-your-api-token-here
```

### Publication Steps

1. **Update Version** (in `pyproject.toml`):
   ```toml
   [tool.poetry]
   version = "3.0.0-alpha.2"  # or next version
   ```

2. **Run Tests**:
   ```bash
   poetry run pytest tests/ --tb=no -q
   ```

3. **Validate Configuration**:
   ```bash
   poetry check
   ```

4. **Build Package**:
   ```bash
   poetry build
   ```

5. **Publish to PyPI**:
   ```bash
   poetry publish
   ```

6. **Verify Publication**:
   ```bash
   pip install classdock --upgrade
   classdock version
   ```

## 🤖 Automated Publication (GitHub Actions)

### Workflow Triggers

The automated publication is triggered by:
- **Git Tags**: Creating a release tag (e.g., `v3.0.0-alpha.2`)
- **Main Branch**: Merging to main with version changes

### Setup Requirements

1. **Repository Secrets**: Add PyPI API token to GitHub repository secrets
2. **Workflow File**: `.github/workflows/publish.yml` (see automation section)
3. **Version Management**: Consistent versioning in `pyproject.toml`

### Release Process

1. **Update Version**:
   ```bash
   # Update version in pyproject.toml
   git add pyproject.toml
   git commit -m "bump: version 3.0.0-alpha.2"
   ```

2. **Create Release**:
   ```bash
   git tag v3.0.0-alpha.2
   git push origin main --tags
   ```

3. **Automatic Publication**: GitHub Actions will automatically:
   - Run all tests
   - Build the package
   - Publish to PyPI
   - Create GitHub release

## 📊 Version Management

### Semantic Versioning

Follow semantic versioning (semver):
- **Major**: `3.0.0` → `4.0.0` (breaking changes)
- **Minor**: `3.0.0` → `3.1.0` (new features)
- **Patch**: `3.0.0` → `3.0.1` (bug fixes)
- **Alpha**: `3.0.0-alpha.1` → `3.0.0-alpha.2` (pre-release)

### Version Consistency

Ensure version consistency across:
- `pyproject.toml` (Poetry configuration)
- `classdock/__init__.py` (Package version)
- Git tags (release tags)

## 🔍 Testing Publication

### Test Installation

After publication, verify the package works:

```bash
# Create clean environment
python -m venv test_env
source test_env/bin/activate

# Install from PyPI
pip install classdock

# Test CLI
classdock --help
classdock version
```

### Rollback Strategy

If issues are found:
1. **Yank Release**: Use PyPI web interface to yank problematic version
2. **Hotfix**: Create patch version with fixes
3. **Communication**: Update documentation and notify users

## 📈 Publication History

### v3.0.0-alpha.1 (September 9, 2025)
- **Milestone**: First PyPI publication
- **Features**: Complete modular architecture with 153 tests
- **Size**: 95 KB wheel, comprehensive CLI tool
- **Status**: ✅ Successfully published

### v3.1.1b2 (November 14, 2025)
- **Status**: ✅ Published via GitHub Actions
- **Features**: Automated release workflow
- **PyPI**: https://pypi.org/project/classdock/3.1.1b2/

### v0.1.1 (January 27, 2026)
- **Status**: ✅ Published via GitHub Actions
- **Features**: Automated release workflow
- **PyPI**: https://pypi.org/project/classdock/0.1.1/

### Future Releases
- `v3.0.0-alpha.2`: API improvements and additional testing
- `v3.0.0-beta.1`: Feature complete, stability testing
- `v3.0.0`: Production release

## 🛠️ Troubleshooting

### Common Issues

1. **Authentication Failed**: Check API token in `~/.pypirc`
2. **Version Conflict**: Ensure version number is incremented
3. **Build Failures**: Run `poetry build` locally first
4. **Test Failures**: All tests must pass before publication

### Support Resources

- **PyPI Help**: https://pypi.org/help/
- **Poetry Docs**: https://python-poetry.org/docs/
- **GitHub Actions**: https://docs.github.com/en/actions
- **Project Issues**: https://github.com/hugo-valle/classdock/issues

## 📝 Checklist

Before each publication:

- [ ] Version number updated in `pyproject.toml`
- [ ] All tests passing (153 tests)
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Git tag created (for releases)
- [ ] PyPI credentials configured
- [ ] Package builds successfully
- [ ] Test installation verified

---

*This document is part of the classdock project documentation.*
