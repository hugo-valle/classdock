# Versioning Strategy

ClassDock follows [Semantic Versioning](https://semver.org/) with [PEP 440](https://peps.python.org/pep-0440/) compliant version identifiers for Python package compatibility.

## Version Format

We use the following format for version identifiers:

### Stable Releases
```
MAJOR.MINOR.PATCH
```
Example: `3.1.0`, `3.2.0`, `4.0.0`

### Pre-releases

#### Alpha Releases
```
MAJOR.MINOR.PATCHaN
```
Example: `3.1.0a1`, `3.1.0a2`, `3.2.0a1`

#### Beta Releases
```
MAJOR.MINOR.PATCHbN
```
Example: `3.1.0b1`, `3.1.0b2`, `3.2.0b1`

#### Release Candidates
```
MAJOR.MINOR.PATCHrcN
```
Example: `3.1.0rc1`, `3.1.0rc2`, `3.2.0rc1`

## Git Tag Format

Git tags include a `v` prefix and match the version identifier:

- Stable: `v3.1.0`
- Alpha: `v3.1.0a1`
- Beta: `v3.1.0b1`
- Release Candidate: `v3.1.0rc1`

## Version Components

### MAJOR Version
Incremented for:
- Breaking API changes
- Major architectural changes
- Incompatible changes requiring user action

### MINOR Version  
Incremented for:
- New features (backwards compatible)
- Significant enhancements
- New CLI commands or major functionality

### PATCH Version
Incremented for:
- Bug fixes
- Documentation improvements
- Internal improvements without API changes

### Pre-release Identifiers

#### Alpha (`aN`)
- Early development releases
- May have incomplete features
- API may change significantly
- For internal testing and feedback

#### Beta (`bN`)
- Feature-complete releases
- API is mostly stable
- Focus on bug fixes and polish
- Ready for broader testing

#### Release Candidate (`rcN`)
- Final testing before stable release
- No new features
- Only critical bug fixes
- Intended to become the next stable release

## PEP 440 Compliance

Our versioning follows [PEP 440](https://peps.python.org/pep-0440/) to ensure:

- ✅ **PyPI Compatibility**: Versions work correctly with pip and PyPI
- ✅ **Tool Support**: Compatible with all Python packaging tools
- ✅ **Dependency Resolution**: Proper version ordering and comparison
- ✅ **Standard Compliance**: Follows Python community standards

### Previous Non-Compliant Format

❌ **Old format**: `3.1.0-alpha.1` (hyphen and dot separators)
✅ **New format**: `3.1.0a1` (PEP 440 compliant)

## Release Process

### 1. Development
Work happens on feature branches and `develop` branch.

### 2. Alpha Release
```bash
# Update version to alpha
poetry version 3.2.0a1

# Create and push tag
git tag v3.2.0a1
git push origin v3.2.0a1
```

### 3. Beta Release
```bash
# Update version to beta  
poetry version 3.2.0b1

# Create and push tag
git tag v3.2.0b1
git push origin v3.2.0b1
```

### 4. Release Candidate
```bash
# Update version to rc
poetry version 3.2.0rc1

# Create and push tag
git tag v3.2.0rc1
git push origin v3.2.0rc1
```

### 5. Stable Release
```bash
# Update version to stable
poetry version 3.2.0

# Create and push tag
git tag v3.2.0
git push origin v3.2.0
```

## Automated Workflows

Our GitHub Actions workflows automatically:

- ✅ **Build and test** on all version tags
- ✅ **Publish to PyPI** with correct version format
- ✅ **Create GitHub releases** with appropriate pre-release flags
- ✅ **Generate release notes** based on version type
- ✅ **Update documentation** with new version references

## Version Checking

### Check Current Version
```bash
# Via Poetry
poetry version

# Via CLI
classdock --version

# Via Python
python -c "import classdock; print(classdock.__version__)"
```

### Update Version
```bash
# Set specific version
poetry version 3.2.0a1

# Bump to next alpha
poetry version prerelease

# Bump to next minor
poetry version minor

# Bump to next major  
poetry version major
```

## Examples

### Version Progression Example
```
3.0.0       # Initial stable release
3.1.0a1     # Alpha for next minor
3.1.0a2     # Second alpha
3.1.0b1     # Beta release
3.1.0rc1    # Release candidate
3.1.0       # Stable release
3.1.1       # Patch release
3.2.0a1     # Next minor alpha
```

### PyPI Package URLs
- Stable: `https://pypi.org/project/classdock/3.1.0/`
- Alpha: `https://pypi.org/project/classdock/3.1.0a1/`
- Beta: `https://pypi.org/project/classdock/3.1.0b1/`

## Migration Notes

### From Previous Versioning
If you have references to the old format (`3.1.0-alpha.1`), update them to the new format (`3.1.0a1`):

```bash
# Find old version references
grep -r "3\.1\.0-alpha\.1" .

# Update to new format
sed -i 's/3\.1\.0-alpha\.1/3.1.0a1/g' file.txt
```

### Workflow Updates
Our CI/CD workflows have been updated to handle PEP 440 formats correctly. No manual intervention needed for automated processes.

## References

- [Semantic Versioning](https://semver.org/)
- [PEP 440 - Version Identification](https://peps.python.org/pep-0440/)
- [Python Packaging User Guide](https://packaging.python.org/)
- [Poetry Version Management](https://python-poetry.org/docs/cli/#version)
