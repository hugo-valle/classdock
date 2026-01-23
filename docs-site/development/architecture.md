# Architecture Overview

This document provides an overview of the ClassDock architecture and design patterns.

## 🏗️ Project Structure

```
classdock/
├── classdock/          # Main package
│   ├── __init__.py          # Package initialization
│   ├── __main__.py          # Entry point
│   ├── cli.py               # Main CLI interface (Typer)
│   ├── bash_wrapper.py      # Shell command wrapper
│   ├── config.py            # Configuration management
│   ├── utils.py             # Utility functions
│   ├── assignments/         # Assignment management
│   ├── automation/          # Scheduling and batch processing
│   ├── config/              # Configuration system
│   ├── repos/               # Repository operations
│   ├── scripts/             # Shell scripts
│   └── secrets/             # Secret management
├── tests/                   # Comprehensive test suite (153 tests)
├── docs/                    # Documentation
├── .github/workflows/       # CI/CD automation
└── pyproject.toml          # Poetry configuration
```

## 🎯 Design Principles

### Modular Architecture

The application is designed with clear separation of concerns:

- **CLI Layer**: Command-line interface using Typer
- **Business Logic**: Core functionality in separate modules
- **Configuration**: Centralized configuration management
- **Utilities**: Common utilities and helpers

### Command Structure

```python
# Main app with sub-applications
app = typer.Typer(help="Main description")
assignments_app = typer.Typer(help="Assignment commands")
repos_app = typer.Typer(help="Repository commands")

# Add sub-apps to main app
app.add_typer(assignments_app, name="assignments")
app.add_typer(repos_app, name="repos")
```

### Configuration Management

- Centralized configuration using `ConfigLoader` class
- Support for file-based and environment variable configuration
- Validation and sensible defaults
- Hierarchical configuration merging

## 🔧 Core Components

### CLI Interface (`cli.py`)

The main command-line interface built with Typer:

- **Sub-applications**: Organized commands by functionality
- **Command patterns**: Consistent parameter handling
- **Error handling**: Graceful error reporting
- **Help system**: Comprehensive help and examples

### Assignment Management (`assignments/`)

Handles assignment lifecycle:

- **Setup**: Assignment configuration and initialization
- **Orchestration**: Automated assignment workflows
- **Management**: Assignment state and operations

### Repository Operations (`repos/`)

Git repository management:

- **Fetching**: Student repository collection
- **Collaboration**: Collaborator management
- **Operations**: Common repository tasks

### Configuration System (`config/`)

Centralized configuration management:

- **Loading**: Configuration file parsing
- **Validation**: Schema validation and defaults
- **Generation**: Configuration file creation

### Secrets Management (`secrets/`)

Secure handling of sensitive data:

- **Storage**: Encrypted secret storage
- **Distribution**: Secure secret distribution
- **Management**: Secret lifecycle operations

### Automation (`automation/`)

Scheduled and batch operations:

- **Scheduling**: Cron-based automation
- **Batch processing**: Bulk operations
- **Monitoring**: Operation tracking

## 🧪 Testing Architecture

### Test Organization

```
tests/
├── conftest.py              # Shared fixtures
├── test_assignments.py      # Assignment tests
├── test_automation.py       # Automation tests
├── test_bash_wrapper.py     # Shell wrapper tests
├── test_cli.py             # CLI interface tests
├── test_config.py          # Configuration tests
├── test_repos.py           # Repository tests
├── test_secrets.py         # Secrets tests
└── fixtures/               # Test data
```

### Test Patterns

- **Unit Tests**: Individual component testing
- **Integration Tests**: Component interaction
- **CLI Tests**: Command-line interface validation
- **Mock Usage**: External dependency mocking

### Fixtures

Common test fixtures provide:

- Mock configuration objects
- Temporary directories
- Mock external services
- Test data setup

## 🔄 Data Flow

### Command Execution Flow

1. **CLI Parsing**: Typer parses command and arguments
2. **Configuration Loading**: Load and validate configuration
3. **Business Logic**: Execute core functionality
4. **Output**: Format and display results
5. **Error Handling**: Graceful error reporting

### Configuration Flow

1. **File Loading**: Load configuration files
2. **Environment Variables**: Override with env vars
3. **Command Arguments**: Override with CLI args
4. **Validation**: Validate final configuration
5. **Default Values**: Apply sensible defaults

## 🏛️ Patterns and Conventions

### Error Handling

```python
try:
    # Operation
    pass
except SpecificException as e:
    logger.error(f"Operation failed: {e}")
    raise typer.Exit(code=1)
```

### Configuration Access

```python
config = ConfigLoader().load()
value = config.get('section.key', default_value)
```

### Command Definition

```python
@app.command()
def command_name(
    param: str = typer.Option(..., help="Parameter description"),
    dry_run: bool = typer.Option(False, help="Show what would be done")
):
    """Command description with usage example."""
    pass
```

## 🔌 External Dependencies

### Core Dependencies

- **Typer**: CLI framework
- **Click**: Command-line utilities
- **PyYAML**: Configuration file parsing
- **Requests**: HTTP client

### Development Dependencies

- **pytest**: Testing framework
- **Poetry**: Dependency management
- **Black**: Code formatting
- **MyPy**: Type checking

## 🚀 Deployment Architecture

### Package Distribution

- **PyPI**: Primary distribution channel
- **GitHub Releases**: Tagged releases
- **CI/CD**: Automated publishing

### Runtime Environment

- **Python 3.10+**: Minimum Python version
- **Cross-platform**: Windows, macOS, Linux
- **Virtual environments**: Poetry-managed dependencies

## 🔮 Future Considerations

### Extensibility

- Plugin architecture for custom commands
- Configuration schema extensibility
- Custom workflow definitions

### Performance

- Async operations for I/O-bound tasks
- Caching for repeated operations
- Batch processing optimizations

### Security

- Enhanced secret encryption
- Audit logging
- Permission management
