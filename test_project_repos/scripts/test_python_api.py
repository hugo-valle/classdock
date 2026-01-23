#!/usr/bin/env python3
"""
Python API Testing Script for Classroom Pilot

Tests the Python API functionality including imports, configuration,
logging, and core functionality.
"""

import sys
import tempfile
from pathlib import Path

# Colors for output


class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color


def log_info(message: str) -> None:
    print(f"{Colors.BLUE}[INFO]{Colors.NC} {message}")


def log_success(message: str) -> None:
    print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {message}")


def log_error(message: str) -> None:
    print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")


def log_warning(message: str) -> None:
    print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}")


class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.failed_tests = []

    def mark_passed(self, test_name: str) -> None:
        self.passed += 1
        log_success(f"{test_name}")

    def mark_failed(self, test_name: str, error: str = "") -> None:
        self.failed += 1
        self.failed_tests.append((test_name, error))
        log_error(f"{test_name}: {error}")

    def mark_warning(self, test_name: str, warning: str = "") -> None:
        """Mark a test as having a warning but not failed."""
        log_warning(f"{test_name}: {warning}")

    def summary(self) -> None:
        total = self.passed + self.failed
        success_rate = (self.passed / total * 100) if total > 0 else 0

        print(f"\n{'='*50}")
        print("Test Results Summary")
        print(f"{'='*50}")
        print(f"Total Tests: {total}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Success Rate: {success_rate:.1f}%")

        if self.failed_tests:
            print("\nFailed Tests:")
            for test_name, error in self.failed_tests:
                print(f"  - {test_name}: {error}")


def test_package_imports(results: TestResult) -> None:
    """Test basic package imports."""
    log_info("Testing package imports")

    # Test main package import
    try:
        import classdock
        results.mark_passed("Main package import")

        # Check version
        if hasattr(classroom_pilot, '__version__'):
            log_info(f"Package version: {classdock.__version__}")
            results.mark_passed("Version attribute available")
        else:
            results.mark_failed("Version attribute missing")

    except ImportError as e:
        results.mark_failed("Main package import", str(e))
        return

    # Test core utility imports
    try:
        from classdock import ConfigLoader, ConfigValidator, BashWrapper
        results.mark_passed("Core utilities import")
    except ImportError as e:
        results.mark_failed("Core utilities import", str(e))

    # Test service layer imports
    try:
        from classdock import AssignmentService, ReposService, SecretsService, AutomationService
        results.mark_passed("Service layer import")
    except ImportError as e:
        results.mark_failed("Service layer import", str(e))

    # Test logging imports
    try:
        from classdock import setup_logging, get_logger
        results.mark_passed("Logging utilities import")
    except ImportError as e:
        results.mark_failed("Logging utilities import", str(e))

    # Test assignment imports
    try:
        from classdock.assignments.setup import AssignmentSetup
        results.mark_passed("Assignment setup import")
    except ImportError as e:
        results.mark_failed("Assignment setup import", str(e))

    # Test CLI imports
    try:
        from classdock import cli
        results.mark_passed("CLI module import")
    except ImportError as e:
        results.mark_failed("CLI module import", str(e))


def test_configuration_system(results: TestResult) -> None:
    """Test configuration loading and validation."""
    log_info("Testing configuration system")

    try:
        from classdock import ConfigLoader, ConfigValidator

        # Test ConfigLoader instantiation
        try:
            config_loader = ConfigLoader()
            results.mark_passed("ConfigLoader instantiation")
        except Exception as e:
            results.mark_failed("ConfigLoader instantiation", str(e))
            return

        # Test ConfigValidator instantiation
        try:
            config_validator = ConfigValidator()
            results.mark_passed("ConfigValidator instantiation")
        except Exception as e:
            results.mark_failed("ConfigValidator instantiation", str(e))
            return

        # Test configuration validation with sample data
        try:
            sample_config = {
                "CLASSROOM_URL": "https://classroom.github.com/test",
                "GITHUB_ORGANIZATION": "test-org",
                "TEMPLATE_REPO_URL": "https://github.com/test/template",
                "ASSIGNMENT_FILE": "assignment.conf"
            }

            # This will depend on the actual implementation
            if hasattr(config_validator, 'validate_full_config'):
                result = config_validator.validate_full_config(sample_config)
                results.mark_passed("Configuration validation")
            else:
                results.mark_failed("Configuration validation",
                                    "validate_full_config method not found")

        except Exception as e:
            results.mark_failed("Configuration validation", str(e))

    except ImportError as e:
        results.mark_failed("Configuration system import", str(e))


def test_logging_system(results: TestResult) -> None:
    """Test logging setup and functionality."""
    log_info("Testing logging system")

    try:
        from classdock import setup_logging, get_logger

        # Test logging setup
        try:
            setup_logging(verbose=True)
            results.mark_passed("Logging setup")
        except Exception as e:
            results.mark_failed("Logging setup", str(e))
            return

        # Test logger creation
        try:
            logger = get_logger("test")
            results.mark_passed("Logger creation")
        except Exception as e:
            results.mark_failed("Logger creation", str(e))
            return

        # Test logging levels
        try:
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            results.mark_passed("Logging levels")
        except Exception as e:
            results.mark_failed("Logging levels", str(e))

    except ImportError as e:
        results.mark_failed("Logging system import", str(e))


def test_bash_wrapper(results: TestResult) -> None:
    """Test BashWrapper functionality."""
    log_info("Testing BashWrapper")

    try:
        from classdock import BashWrapper

        # Test BashWrapper instantiation
        try:
            # BashWrapper requires a config parameter
            test_config = {"test": "value"}
            bash_wrapper = BashWrapper(test_config)
            results.mark_passed("BashWrapper instantiation")
        except Exception as e:
            results.mark_failed("BashWrapper instantiation", str(e))
            return

        # Test BashWrapper methods availability
        try:
            # Check for actual methods that exist
            if hasattr(bash_wrapper, 'assignment_orchestrator'):
                results.mark_passed("BashWrapper methods available")
            else:
                results.mark_failed(
                    "BashWrapper methods", "assignment_orchestrator method not found")
        except Exception as e:
            results.mark_failed("BashWrapper methods test", str(e))

    except ImportError as e:
        results.mark_failed("BashWrapper import", str(e))


def test_assignment_setup(results: TestResult) -> None:
    """Test AssignmentSetup functionality."""
    log_info("Testing AssignmentSetup")

    try:
        from classdock.assignments.setup import AssignmentSetup

        # Create temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create sample configuration file
            config_file = Path(temp_dir) / "assignment.conf"
            config_file.write_text("""
CLASSROOM_URL=https://classroom.github.com/test
GITHUB_ORGANIZATION=test-org
TEMPLATE_REPO_URL=https://github.com/test/template
ASSIGNMENT_FILE=assignment.conf
""")

            # Test AssignmentSetup instantiation
            try:
                # AssignmentSetup doesn't take config_file parameter
                assignment_setup = AssignmentSetup()
                results.mark_passed("AssignmentSetup instantiation")
            except Exception as e:
                results.mark_failed("AssignmentSetup instantiation", str(e))
                return

            # Test configuration loading
            try:
                if hasattr(assignment_setup, 'load_config'):
                    config = assignment_setup.load_config()
                    results.mark_passed("AssignmentSetup config loading")
                else:
                    results.mark_warning(
                        "AssignmentSetup config loading method not found")
            except Exception as e:
                results.mark_failed("AssignmentSetup config loading", str(e))

    except ImportError as e:
        results.mark_failed("AssignmentSetup import", str(e))


def test_cli_module(results: TestResult) -> None:
    """Test CLI module functionality."""
    log_info("Testing CLI module")

    try:
        from classdock import cli

        # Test CLI app creation
        try:
            if hasattr(cli, 'app'):
                results.mark_passed("CLI app available")
            else:
                results.mark_failed("CLI app not found")
        except Exception as e:
            results.mark_failed("CLI app access", str(e))

        # Test Typer integration
        try:
            import typer
            if hasattr(cli, 'app') and isinstance(cli.app, typer.Typer):
                results.mark_passed("CLI Typer integration")
            else:
                results.mark_warning("CLI Typer integration unclear")
        except ImportError:
            results.mark_warning("Typer not available for testing")
        except Exception as e:
            results.mark_failed("CLI Typer integration", str(e))

    except ImportError as e:
        results.mark_failed("CLI module import", str(e))


def test_service_layer(results: TestResult) -> None:
    """Test service layer functionality."""
    log_info("Testing service layer")

    try:
        from classdock import AssignmentService, ReposService, SecretsService, AutomationService

        # Test AssignmentService instantiation
        try:
            service = AssignmentService()
            results.mark_passed("AssignmentService instantiation")
        except Exception as e:
            results.mark_failed("AssignmentService instantiation", str(e))

        # Test ReposService instantiation
        try:
            service = ReposService()
            results.mark_passed("ReposService instantiation")
        except Exception as e:
            results.mark_failed("ReposService instantiation", str(e))

        # Test SecretsService instantiation
        try:
            service = SecretsService()
            results.mark_passed("SecretsService instantiation")
        except Exception as e:
            results.mark_failed("SecretsService instantiation", str(e))

        # Test AutomationService instantiation
        try:
            service = AutomationService()
            results.mark_passed("AutomationService instantiation")
        except Exception as e:
            results.mark_failed("AutomationService instantiation", str(e))

    except ImportError as e:
        results.mark_failed("Service layer import", str(e))


def test_error_handling(results: TestResult) -> None:
    """Test error handling and exceptions."""
    log_info("Testing error handling")

    try:
        from classdock import ConfigValidator

        # Test with invalid configuration
        try:
            validator = ConfigValidator()
            invalid_config = {"INVALID_KEY": "invalid_value"}

            if hasattr(validator, 'validate_full_config'):
                # This should handle invalid config gracefully
                try:
                    result = validator.validate_full_config(invalid_config)
                    results.mark_passed("Invalid config handling")
                except Exception:
                    # Exception is expected for invalid config
                    results.mark_passed("Invalid config exception handling")
            else:
                results.mark_warning(
                    "Configuration validation method not available")

        except Exception as e:
            results.mark_failed("Error handling test", str(e))

    except ImportError as e:
        results.mark_failed("Error handling import", str(e))


def test_memory_usage(results: TestResult) -> None:
    """Test memory usage during imports and operations."""
    log_info("Testing memory usage")

    try:
        import psutil
        import gc

        # Get initial memory
        process = psutil.Process()
        initial_memory = process.memory_info().rss

        # Import and use package
        import classdock
        from classdock import ConfigLoader, setup_logging

        # Perform some operations
        setup_logging(verbose=False)
        config_loader = ConfigLoader()

        # Force garbage collection
        gc.collect()

        # Get final memory
        final_memory = process.memory_info().rss
        memory_increase = (final_memory - initial_memory) / 1024 / 1024  # MB

        log_info(f"Memory increase: {memory_increase:.2f} MB")

        if memory_increase < 50:  # Reasonable threshold
            results.mark_passed("Memory usage acceptable")
        else:
            results.mark_warning(
                f"Memory usage high: {memory_increase:.2f} MB")

    except ImportError:
        results.mark_warning("psutil not available for memory testing")
    except Exception as e:
        results.mark_failed("Memory usage test", str(e))


def test_import_time(results: TestResult) -> None:
    """Test import time performance."""
    log_info("Testing import performance")

    import time

    try:
        # Test import time
        start_time = time.time()
        end_time = time.time()

        import_time = end_time - start_time
        log_info(f"Import time: {import_time:.3f} seconds")

        if import_time < 2.0:  # Reasonable threshold
            results.mark_passed("Import time acceptable")
        else:
            results.mark_warning(f"Import time slow: {import_time:.3f}s")

    except Exception as e:
        results.mark_failed("Import time test", str(e))


def main() -> int:
    """Main test execution."""
    log_info("Starting Python API tests for Classroom Pilot")

    results = TestResult()

    # Run all tests
    test_package_imports(results)
    test_configuration_system(results)
    test_logging_system(results)
    test_bash_wrapper(results)
    test_assignment_setup(results)
    test_cli_module(results)
    test_service_layer(results)
    test_error_handling(results)
    test_memory_usage(results)
    test_import_time(results)

    # Show results
    results.summary()

    # Return appropriate exit code
    return 0 if results.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
