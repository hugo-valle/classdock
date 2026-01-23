# Changelog

All notable changes to ClassDock are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) with [PEP 440](https://peps.python.org/pep-0440/) compliant version identifiers.

## [3.1.1b0] - 2025-10-25

### Fixed
- **CI Test Infrastructure**: Resolved help text pollution and test assertion issues
  - Fixed configuration loading logs appearing in help output
  - Changed config loading log from INFO to DEBUG level
  - Added ANSI escape code stripping for reliable help text testing in CI
  - Created `wide_runner` fixture with terminal width settings for consistent rendering
- **Git Repository Hygiene**: Removed tracked `assignment.conf` file
  - File belongs in assignment repos, not in tool repo
  - Properly added to `.gitignore` to prevent future commits

### Added
- **Extended QA Test Infrastructure**: Comprehensive Tier 2 testing improvements
  - Enhanced `test_project_repos/` end-to-end validation suite
  - Improved mock helpers for GitHub API testing
  - Added test orchestration layer with TDD skip mechanism
  - Better separation between unit tests (Tier 1) and E2E tests (Tier 2)
- **GitHub API Integration Foundation**: Progressive migration from bash to Python
  - Centralized error handling in `utils/github_exceptions.py`
  - Retry logic with exponential backoff for transient failures
  - Standardized response handling across GitHub API interactions

### Changed
- **Test Count**: Increased from 153 to 752+ comprehensive tests
- **Test Architecture**: Clear two-tier testing strategy (unit + E2E)

## [3.1.0a1] - 2025-09-09

### Added
- Complete MkDocs documentation structure with Material theme
- Professional documentation site organization with comprehensive navigation
- Detailed CLI reference documentation for all command groups:
  - Assignment Commands: Complete lifecycle management
  - Repository Commands: Student repository operations
  - Secret Management: Secure credential distribution
  - Automation Commands: Scheduling and batch processing
- GitHub Pages deployment workflow for automated documentation publishing
- Configuration guide with examples for all environments
- Comprehensive workflow documentation for all major operations
- Development documentation including contributing, architecture, and testing guides
- **PEP 440 compliant versioning**: Updated from `3.1.0-alpha.1` to `3.1.0a1` format

### Changed
- Enhanced documentation organization with logical grouping and navigation
- Improved cross-references and internal linking throughout documentation
- Updated all CLI examples to use modern Python commands
- Modernized installation and setup instructions for better user experience
- **Version format compliance**: All version identifiers now follow PEP 440 standard
- **Release workflows**: Updated to handle PEP 440 version formats correctly

### Fixed
- Documentation consistency across all workflow guides
- Internal link references throughout the documentation site
- CLI command examples and usage patterns
- Integration examples with modern Python packaging ecosystem
- **PyPI compatibility**: Version format now fully compatible with Python Package Index standards

## [3.0.1-alpha.2] - 2025-09-05

### Added
- Complete MkDocs documentation structure with Material theme
- Professional documentation site organization
- CLI reference documentation with comprehensive examples
- Workflow documentation for all major operations

### Changed
- Modernized all documentation to use Python CLI commands
- Moved legacy bash script documentation to `docs/legacy/`
- Restructured documentation for better organization and navigation
- Updated installation and setup instructions

### Fixed
- Documentation consistency across all workflow guides
- CLI command examples and usage patterns
- Integration with modern Python packaging ecosystem

## [3.0.1-alpha.1] - 2025-09-01

### Added
- Complete Python CLI implementation using Typer framework
- Modular package structure with organized subcommands
- Comprehensive test suite with 153+ tests
- CI/CD pipeline for automated PyPI publishing
- Professional documentation structure

### Changed
- Migration from bash scripts to Python CLI
- Updated project structure for better maintainability
- Modernized dependency management with Poetry
- Enhanced error handling and user experience

### Deprecated
- Legacy bash script interfaces (moved to scripts/ directory)
- Old configuration formats (backward compatibility maintained)

### Fixed
- Cross-platform compatibility issues
- Dependency conflicts with modern Python ecosystem
- CLI consistency and user experience

## [2.x.x] - Legacy Versions

Previous versions used bash script interfaces and are documented in the legacy documentation.

### Major Features in Legacy Versions
- Bash script-based automation
- Basic GitHub Classroom integration
- Manual configuration management
- Shell-based workflow orchestration

## Migration Guide

### From 2.x to 3.x

The major change in version 3.x is the migration from bash scripts to a Python CLI:

**Old (2.x):**
```bash
./scripts/setup-assignment.sh
./scripts/fetch-student-repos.sh
```

**New (3.x):**
```bash
classdock assignments setup
classdock repos fetch
```

### Configuration Changes

Configuration files maintain backward compatibility, but new features use the updated format:

```yaml
# Modern configuration structure
classroom:
  url: "https://classroom.github.com/classrooms/12345"
  assignment_prefix: "assignment-"

github:
  token: "${GITHUB_TOKEN}"
  organization: "my-org"

automation:
  schedule: "0 */6 * * *"
  dry_run: false
```

### Command Mapping

| Legacy Script | New CLI Command |
|---------------|-----------------|
| `setup-assignment.sh` | `classdock assignments setup` |
| `fetch-student-repos.sh` | `classdock repos fetch` |
| `assignment-orchestrator.sh` | `classdock assignments orchestrate` |
| `add-secrets-to-students.sh` | `classdock secrets add` |
| `cycle-collaborator.sh` | `classdock repos collaborator cycle` |
| `manage-cron.sh` | `classdock automation schedule` |

## Development History

### Vision and Goals

ClassDock was created to solve the challenges of managing GitHub Classroom assignments at scale:

- **Automation**: Reduce manual work in assignment management
- **Consistency**: Ensure consistent setup across all assignments
- **Scalability**: Handle large numbers of students and repositories
- **Integration**: Seamless GitHub Classroom integration
- **Reliability**: Robust error handling and recovery

### Technical Evolution

1. **Phase 1**: Bash script collection for basic automation
2. **Phase 2**: Organized script suite with configuration management
3. **Phase 3**: Python CLI with modern architecture and testing
4. **Phase 4**: Professional packaging and distribution

### Design Principles

- **Modularity**: Clear separation of concerns
- **Testability**: Comprehensive test coverage
- **Usability**: Intuitive command-line interface
- **Reliability**: Robust error handling and validation
- **Maintainability**: Clean code and documentation

## Future Roadmap

### Short Term (v3.1)
- Enhanced GitHub API integration
- Improved error reporting and logging
- Additional automation workflows
- Extended configuration options

### Medium Term (v3.2)
- Web dashboard for assignment monitoring
- Advanced scheduling and batch operations
- Plugin architecture for custom workflows
- Enhanced security and secret management

### Long Term (v4.0)
- Multi-platform desktop application
- Advanced analytics and reporting
- Integration with learning management systems
- Collaborative features for teaching teams

## Contributing

We welcome contributions! See our [Contributing Guide](../development/contributing.md) for details on:

- Development setup
- Coding standards
- Testing requirements
- Pull request process

## Acknowledgments

### Contributors
- Hugo Valle (@hugo-valle) - Project creator and maintainer
- GitHub Classroom Team - Platform and inspiration
- Python Community - Tools and libraries

### Technologies
- **Python**: Core language
- **Typer**: CLI framework
- **Poetry**: Dependency management
- **pytest**: Testing framework
- **GitHub Actions**: CI/CD automation
- **MkDocs**: Documentation site

### Community
Special thanks to educators and developers who have provided feedback, bug reports, and feature requests that have shaped ClassDock's development.

## License

ClassDock is released under the MIT License. See [LICENSE](https://github.com/hugo-valle/classdock/blob/main/LICENSE) for details.
