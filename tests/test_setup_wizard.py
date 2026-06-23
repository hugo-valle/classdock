"""
Comprehensive test suite for classdock.assignments.setup module.

This test suite provides comprehensive coverage for the AssignmentSetup class,
including unit tests for individual methods, integration tests for the complete
workflow, error handling, edge cases, and proper mocking of external dependencies.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from classdock.assignments.setup import AssignmentSetup


@pytest.fixture
def mock_dependencies():
    """
    Creates and yields a dictionary of mocked dependencies for the AssignmentSetup class.

    This function uses the `unittest.mock.patch` context manager to mock the following classes
    from the `classdock.assignments.setup` module:
        - PathManager
        - InputHandler
        - Validators
        - ConfigGenerator
        - FileManager

    Each mock is configured to return a Mock instance, with `PathManager.get_workspace_root`
    specifically set to return a test Path. The function yields a dictionary mapping dependency
    names to their respective mock instances, allowing tests to inject these mocks as needed.

    Yields:
        dict: A dictionary containing the mocked instances of the dependencies.
    """
    with patch('classdock.assignments.setup.PathManager') as mock_path_mgr, \
            patch('classdock.assignments.setup.InputHandler') as mock_input, \
            patch('classdock.assignments.setup.Validators') as mock_validators, \
            patch('classdock.assignments.setup.ConfigGenerator') as mock_config_gen, \
            patch('classdock.assignments.setup.FileManager') as mock_file_mgr:

        # Configure PathManager mock
        mock_path_instance = Mock()
        mock_path_instance.get_workspace_root.return_value = Path(
            "/test/workspace")
        mock_path_mgr.return_value = mock_path_instance

        # Configure other mocks
        mock_input_instance = Mock()
        mock_input.return_value = mock_input_instance

        mock_validators_instance = Mock()
        mock_validators.return_value = mock_validators_instance

        mock_config_gen_instance = Mock()
        mock_config_gen.return_value = mock_config_gen_instance

        mock_file_mgr_instance = Mock()
        mock_file_mgr.return_value = mock_file_mgr_instance

        yield {
            'path_manager': mock_path_instance,
            'input_handler': mock_input_instance,
            'validators': mock_validators_instance,
            'config_generator': mock_config_gen_instance,
            'file_manager': mock_file_mgr_instance
        }


class TestAssignmentSetupInitialization:
    """
    TestAssignmentSetupInitialization contains unit tests to verify the correct initialization of the AssignmentSetup class.
    It ensures that all required components are instantiated and that internal data structures are initialized as empty.
    """

    def test_init_components_instantiated(self, mock_dependencies):
        """
        Test that the AssignmentSetup class properly instantiates all required components.

        This test verifies that after initializing an AssignmentSetup instance, the following
        attributes are present: 'path_manager', 'input_handler', 'validators',
        'config_generator', and 'file_manager'. The presence of these attributes indicates
        that the corresponding components have been instantiated as part of the setup process.
        """
        setup = AssignmentSetup()

        # Verify all components were instantiated
        assert hasattr(setup, 'path_manager')
        assert hasattr(setup, 'input_handler')
        assert hasattr(setup, 'validators')
        assert hasattr(setup, 'config_generator')
        assert hasattr(setup, 'file_manager')

    def test_init_empty_data_structures(self, mock_dependencies):
        """
        Test that the AssignmentSetup class initializes its internal data structures
        (config_values, token_files, token_validation) as empty dictionaries upon instantiation.
        """
        setup = AssignmentSetup()

        # Test that data structures are initialized correctly
        assert setup.config_values == {}
        assert setup.token_files == {}
        assert setup.token_validation == {}


class TestCollectAssignmentInfo:
    """
    TestCollectAssignmentInfo contains unit tests for the assignment information collection process
    within the AssignmentSetup class. It verifies that assignment name and organization are correctly
    collected and stored, and that logging occurs as expected during the collection process.

    Test Cases:
    - test_collect_assignment_info_success: Ensures that a valid assignment name and organization are
        collected and stored in the configuration, and that the input handler is called.
    - test_collect_assignment_info_with_logger: Checks that the logger's debug method is called
        with the appropriate message when collecting assignment information.
    """

    def test_collect_assignment_info_success(self, mock_dependencies):
        """
        Test that the _collect_assignment_info method successfully collects the assignment name
        and GitHub organization from user input and stores them in the config_values dictionary
        under 'ASSIGNMENT_NAME' and 'GITHUB_ORGANIZATION' keys.
        Also verifies that the input handler's prompt_input method is called.
        """
        setup = AssignmentSetup()
        test_name = "python-basics"
        test_org = "my-org"

        # Setup mock to return assignment name then org
        setup.input_handler.prompt_input.side_effect = [test_name, test_org]

        # Execute
        setup._collect_assignment_info()

        # Assert
        assert setup.config_values['ASSIGNMENT_NAME'] == test_name
        assert setup.config_values['GITHUB_ORGANIZATION'] == test_org
        assert setup.input_handler.prompt_input.call_count == 2

    def test_collect_assignment_info_with_logger(self, mock_dependencies):
        """
        Test that the logger's debug method is called with the expected message
        when collecting assignment information using the AssignmentSetup class.
        This ensures that logging is properly integrated during the assignment
        information collection process.
        """
        with patch('classdock.assignments.setup.logger') as mock_logger:
            setup = AssignmentSetup()
            setup.input_handler.prompt_input.side_effect = ["test-assignment", "test-org"]

            setup._collect_assignment_info()

            # Verify logging was called
            mock_logger.debug.assert_called_with(
                "Collecting assignment information")


class TestCollectRepositoryInfo:
    """
    TestCollectRepositoryInfo contains unit tests for the repository information collection logic in the AssignmentSetup class.

    Test Cases:
    - test_collect_repository_info_success: Verifies that template repository URL is correctly
        collected and stored in config_values when a valid URL is provided.
    - test_collect_repository_info_empty_template_url_skips: Ensures that an empty template URL
        is silently skipped (no TEMPLATE_REPO_URL in config).
    """

    def test_collect_repository_info_success(self, mock_dependencies):
        """
        Test that the _collect_repository_info method successfully collects and stores
        the template repository URL in the config_values dictionary.
        Verifies that the correct value is stored after user input.
        """
        setup = AssignmentSetup()
        setup.config_values = {
            'GITHUB_ORGANIZATION': 'test-org',
            'ASSIGNMENT_NAME': 'test-assignment'
        }

        # Mock validators.validate_url to return (True, None)
        setup.validators.validate_url = Mock(return_value=(True, None))

        # Setup mock: user provides a template URL
        setup.input_handler.prompt_input.return_value = \
            "https://github.com/test-org/test-assignment-template"

        # Execute
        setup._collect_repository_info()

        # Assert
        assert setup.config_values['TEMPLATE_REPO_URL'] == \
            "https://github.com/test-org/test-assignment-template"

    def test_collect_repository_info_empty_template_url_skips(self, mock_dependencies):
        """
        Test that the _collect_repository_info method skips setting TEMPLATE_REPO_URL
        when the user provides an empty value.
        """
        setup = AssignmentSetup()
        setup.config_values = {
            'GITHUB_ORGANIZATION': 'test-org',
            'ASSIGNMENT_NAME': 'test-assignment'
        }

        # Setup mock: user leaves template URL empty
        setup.input_handler.prompt_input.return_value = ""

        # Execute
        setup._collect_repository_info()

        # Assert: TEMPLATE_REPO_URL should not be set when empty
        assert 'TEMPLATE_REPO_URL' not in setup.config_values


class TestCollectAssignmentDetails:
    """
    TestCollectAssignmentDetails contains test cases for verifying the behavior of the assignment details
    collection process in the AssignmentSetup class. It ensures that the main assignment file is correctly
    collected from user input.

    Test Cases:
    - test_collect_assignment_details_with_defaults: Verifies that the main assignment file is
        set from user input with default value.
    - test_collect_assignment_details_custom_values: Verifies that custom main file values
        provided by the user are correctly set in the configuration.
    """

    def test_collect_assignment_details_with_defaults(self, mock_dependencies):
        """
        Test that the _collect_assignment_details method correctly populates assignment details
        using user input. Verifies that the main assignment file is set from user input and
        the input handler is called the expected number of times.
        """
        setup = AssignmentSetup()
        setup.config_values = {
            'ASSIGNMENT_NAME': 'test-assignment'
        }

        # Setup mocks
        setup.input_handler.prompt_input.return_value = "assignment.ipynb"

        # Execute
        setup._collect_assignment_details()

        # Assert
        assert setup.config_values['MAIN_ASSIGNMENT_FILE'] == "assignment.ipynb"
        assert setup.input_handler.prompt_input.call_count == 1

    def test_collect_assignment_details_custom_values(self, mock_dependencies):
        """
        Test that the assignment details collection method correctly handles custom user input values.
        This test verifies that when the user provides a custom value for the main file,
        the value is stored in the configuration as expected.
        """
        setup = AssignmentSetup()
        setup.config_values = {
            'ASSIGNMENT_NAME': 'homework'
        }

        # Setup mocks
        setup.input_handler.prompt_input.return_value = "main.py"

        # Execute
        setup._collect_assignment_details()

        # Assert
        assert setup.config_values['MAIN_ASSIGNMENT_FILE'] == "main.py"


class TestConfigureTokens:
    """
    Test suite for the token configuration process in the AssignmentSetup class.

    This class contains tests to verify that tokens are configured correctly,
    including scenarios where token validation is enabled or disabled. It ensures
    that the appropriate values are set in the configuration, validation, and file
    mappings based on user input.

    Test Cases:
    - test_configure_tokens_with_validation: Verifies correct behavior when token
        validation is enabled.
    - test_configure_tokens_without_validation: Verifies correct behavior when token
        validation is disabled.
    """

    def test_configure_tokens_with_validation(self, mock_dependencies):
        """
        Test that the _configure_tokens method informs user about centralized token management.

        With centralized tokens, this method no longer prompts for token values or creates token files.
        Instead, it informs the user that the centralized GitHub token will be used.
        """
        with patch('classdock.assignments.setup.print_colored') as mock_print:
            setup = AssignmentSetup()

            # Execute
            setup._configure_tokens()

            # Assert - should inform about centralized token, not prompt for values
            # No longer creates token_files mapping or stores token values
            # Token no longer stored in config
            assert 'INSTRUCTOR_TESTS_TOKEN_VALUE' not in setup.config_values
            assert len(setup.token_files) == 0  # No token files created
            # Verify user was informed (print_colored should be called)
            assert mock_print.called

    def test_configure_tokens_without_validation(self, mock_dependencies):
        """
        Test that the token configuration process uses centralized token management.

        With centralized tokens, validation is handled by the token manager, not the setup wizard.
        The wizard simply informs the user that centralized tokens will be used.
        """
        with patch('classdock.assignments.setup.print_colored') as mock_print:
            setup = AssignmentSetup()

            # Execute
            setup._configure_tokens()

            # Assert - centralized approach doesn't store tokens or create files
            assert 'INSTRUCTOR_TESTS_TOKEN_VALUE' not in setup.config_values  # No token in config
            assert len(setup.token_files) == 0  # No token files
            assert len(setup.token_validation) == 0  # No validation mapping
            # Verify user was informed
            assert mock_print.called


class TestCreateFiles:
    """
    TestCreateFiles contains unit tests for the file creation logic in the AssignmentSetup class.
    It verifies that configuration and token files are created or skipped appropriately based on
    the 'USE_SECRETS' configuration value. The tests ensure that the correct methods are called
    on the config_generator and file_manager dependencies, and that token file creation is
    conditional on secrets being enabled.
    """

    def test_create_files_with_secrets_enabled(self, mock_dependencies):
        """
        Test that the _create_files method creates configuration file and updates .gitignore.

        With centralized token management:
        - Configuration file is still created
        - .gitignore is still updated
        - Token files are NO LONGER created (centralized management)
        """
        setup = AssignmentSetup()
        setup.config_values = {'USE_SECRETS': 'true'}
        setup.token_files = {}  # Empty with centralized tokens
        setup.token_validation = {}  # Empty with centralized tokens

        # Execute
        setup._create_files()

        # Assert
        setup.config_generator.create_config_file.assert_called_once_with(
            setup.config_values,
            setup.token_files,
            setup.token_validation
        )
        # create_token_files() is NO LONGER called with centralized tokens
        # Token files are managed centrally in ~/.config/classdock/
        setup.file_manager.update_gitignore.assert_called_once()

    def test_create_files_with_secrets_disabled(self, mock_dependencies):
        """
        Test that the _create_files method does not create token files when secrets are disabled.

        This test verifies that:
        - The configuration file is created with the provided config values, token files, and token validation.
        - The file manager does not attempt to create token files when 'USE_SECRETS' is set to 'false'.
        - The .gitignore file is updated as expected.
        """
        setup = AssignmentSetup()
        setup.config_values = {'USE_SECRETS': 'false'}
        setup.token_files = {}
        setup.token_validation = {}

        # Execute
        setup._create_files()

        # Assert
        setup.config_generator.create_config_file.assert_called_once_with(
            setup.config_values,
            setup.token_files,
            setup.token_validation
        )
        # Should not create token files when secrets disabled
        setup.file_manager.create_token_files.assert_not_called()
        setup.file_manager.update_gitignore.assert_called_once()


class TestConfigureSecretManagement:
    """
    Test suite for the secret management configuration functionality in the AssignmentSetup class.

    This class contains tests to verify that the secret management setup behaves correctly
    when enabled or disabled by the user. It mocks user input and internal methods to ensure
    the configuration values and method calls are as expected.

    Test Cases:
    - test_configure_secret_management_enabled: Ensures that enabling secret management sets
        the correct configuration and triggers token configuration.
    - test_configure_secret_management_disabled: Ensures that disabling secret management sets
        the correct configuration and does not trigger token configuration.
    """

    def test_configure_secret_management_enabled(self, mock_dependencies):
        """
        Test that secret management is correctly enabled during assignment setup.

        This test verifies that when the user confirms enabling secret management,
        the 'USE_SECRETS' configuration value is set to 'true' and the token
        configuration method is called exactly once.

        Mocks:
            - 'print_colored' and 'print_success' to suppress output.
            - 'input_handler.prompt_yes_no' to simulate user confirmation.
            - '_configure_tokens' to monitor invocation.

        Asserts:
            - 'USE_SECRETS' is set to 'true' in the configuration.
            - '_configure_tokens' is called once.
        """
        with patch('classdock.assignments.setup.print_colored'), \
                patch('classdock.assignments.setup.print_success'):

            setup = AssignmentSetup()
            setup.input_handler.prompt_yes_no.return_value = True
            setup._configure_tokens = Mock()

            # Execute
            setup._configure_secret_management()

            # Assert
            assert setup.config_values['USE_SECRETS'] == 'true'
            setup._configure_tokens.assert_called_once()

    def test_configure_secret_management_disabled(self, mock_dependencies):
        """
        Test that the _configure_secret_management method correctly sets the 'USE_SECRETS' configuration
        value to 'false' when secret management is disabled by the user (i.e., when the prompt returns False).
        Mocks out colored printing functions to isolate test behavior.
        """
        with patch('classdock.assignments.setup.print_colored'), \
                patch('classdock.assignments.setup.print_success'):

            setup = AssignmentSetup()
            setup.input_handler.prompt_yes_no.return_value = False

            # Execute
            setup._configure_secret_management()

            # Assert
            assert setup.config_values['USE_SECRETS'] == 'false'


class TestRunWizardIntegration:
    """
    Integration tests for the AssignmentSetup wizard workflow.

    This test class verifies the end-to-end behavior of the setup wizard, ensuring that:
    - The complete wizard flow executes all required steps in sequence.
    - The wizard correctly handles user interruptions (e.g., KeyboardInterrupt) and exits gracefully.

    Test Cases:
    - test_run_wizard_success_complete_flow: Ensures all internal setup steps are called during a successful wizard run.
    - test_run_wizard_keyboard_interrupt: Verifies that a KeyboardInterrupt during the wizard run results in a proper system exit with code 1.
    """

    def test_run_wizard_success_complete_flow(self, mock_dependencies):
        """
        Test that the AssignmentSetup wizard runs through the complete workflow successfully.

        This test verifies that when `run_wizard` is called on an `AssignmentSetup` instance,
        all the internal steps of the wizard are executed exactly once. It mocks out
        external dependencies and internal methods to ensure the flow proceeds as expected,
        without side effects or actual I/O.

        Steps verified:
        - Assignment information collection
        - Repository information collection
        - Assignment details collection
        - Secret management configuration
        - File creation

        All steps are asserted to be called once, confirming the complete flow.
        """
        with patch('classdock.assignments.setup.show_welcome'), \
                patch('classdock.assignments.setup.show_completion'), \
                patch('classdock.assignments.setup.print_success'), \
                patch('classdock.assignments.setup.logger'):

            setup = AssignmentSetup()

            # Mock all the internal methods
            setup._collect_assignment_info = Mock()
            setup._collect_repository_info = Mock()
            setup._collect_assignment_details = Mock()
            setup._configure_secret_management = Mock()
            setup._create_files = Mock()

            # Execute
            setup.run_wizard()

            # Assert all steps were called
            setup._collect_assignment_info.assert_called_once()
            setup._collect_repository_info.assert_called_once()
            setup._collect_assignment_details.assert_called_once()
            setup._configure_secret_management.assert_called_once()
            setup._create_files.assert_called_once()

    def test_run_wizard_keyboard_interrupt(self, mock_dependencies):
        """
        Test that the assignment setup wizard gracefully handles a KeyboardInterrupt
        (by the user pressing Ctrl+C) during the assignment information collection phase.

        With updated behavior, run_wizard() returns False instead of calling sys.exit().
        """
        with patch('classdock.assignments.setup.show_welcome'), \
                patch('classdock.assignments.setup.print_colored'), \
                patch('classdock.assignments.setup.logger'):

            setup = AssignmentSetup()
            setup._collect_assignment_info = Mock(
                side_effect=KeyboardInterrupt())

            # Execute - now returns False instead of raising SystemExit
            result = setup.run_wizard()

            # Assert - should return False to indicate cancellation
            assert result is False


def test_setup_assignment_function():
    """
    Unit test for the `setup_assignment` function.

    This test verifies that:
    - The `AssignmentSetup` class is instantiated exactly once when `setup_assignment` is called.
    - The `run_wizard` method of the `AssignmentSetup` instance is called exactly once.

    Mocks are used to isolate the test from actual implementation details.
    """
    with patch('classdock.assignments.setup.AssignmentSetup') as mock_class:
        mock_instance = Mock()
        mock_class.return_value = mock_instance

        from classdock.assignments.setup import setup_assignment

        # Execute
        setup_assignment()

        # Assert
        mock_class.assert_called_once()
        mock_instance.run_wizard.assert_called_once()


class TestEdgeCasesAndErrorHandling:
    """
    TestEdgeCasesAndErrorHandling
    -----------------------------

    This test class contains comprehensive test cases for the `AssignmentSetup` wizard, focusing on edge cases and error handling scenarios. The tests ensure that the setup wizard behaves correctly under various failure conditions, unexpected inputs, and state management requirements. Covered scenarios include:

    - Handling of unexpected exceptions during the wizard workflow, ensuring proper exit codes.
    - Error propagation and handling when file creation or configuration generation fails due to permission or file system errors.
    - Token configuration logic, including cases where empty tokens are provided.
    - Input handling with leading/trailing whitespace and ensuring values are stored as received.
    - State isolation between multiple consecutive wizard runs to prevent cross-contamination.
    - Initialization failures in dependencies such as `PathManager` and `ConfigGenerator`, ensuring exceptions are raised and handled as expected.

    Each test method is designed to simulate a specific edge case or error, using mocks and patches to control dependencies and assert correct behavior.
    """

    def test_run_wizard_unexpected_exception(self, mock_dependencies):
        """
        Test that the setup wizard returns False when an unexpected exception occurs.

        With updated behavior, run_wizard() returns False instead of calling sys.exit().
        """
        with patch('classdock.assignments.setup.show_welcome'), \
                patch('classdock.assignments.setup.print_error'), \
                patch('classdock.assignments.setup.logger'):

            setup = AssignmentSetup()
            setup._collect_assignment_info = Mock(
                side_effect=ValueError("Unexpected error"))

            # Execute - now returns False instead of raising SystemExit
            result = setup.run_wizard()

            # Assert - should return False to indicate failure
            assert result is False

    def test_collect_repository_info_invalid_url_skips(self, mock_dependencies):
        """
        Test that _collect_repository_info skips setting TEMPLATE_REPO_URL when the provided
        URL is invalid (validators.validate_url returns False).
        """
        setup = AssignmentSetup()
        setup.config_values = {
            'ASSIGNMENT_NAME': 'test-assignment',
            'GITHUB_ORGANIZATION': 'test-org',
        }

        # Mock validators to indicate invalid URL
        setup.validators.validate_url = Mock(return_value=(False, "bad URL"))
        setup.input_handler.prompt_input.return_value = "not-a-valid-url"

        with patch('classdock.assignments.setup.print_error'):
            setup._collect_repository_info()

        # TEMPLATE_REPO_URL should not be set because URL was invalid
        assert 'TEMPLATE_REPO_URL' not in setup.config_values

    def test_collect_assignment_details_stores_main_file(self, mock_dependencies):
        """
        Test that _collect_assignment_details correctly stores the main file name
        provided by the user.
        """
        setup = AssignmentSetup()
        setup.config_values = {
            'ASSIGNMENT_NAME': 'test-assignment'
        }

        setup.input_handler.prompt_input.return_value = "custom.py"

        # Execute
        setup._collect_assignment_details()

        # Assert
        assert setup.config_values['MAIN_ASSIGNMENT_FILE'] == "custom.py"

    def test_create_files_config_generator_failure(self, mock_dependencies):
        """
        Test that AssignmentSetup._create_files raises an IOError with the correct message
        when the config_generator's create_config_file method fails due to a permission error.
        """
        setup = AssignmentSetup()
        setup.config_values = {'USE_SECRETS': 'false'}
        setup.token_files = {}
        setup.token_validation = {}

        # Setup mock to fail
        setup.config_generator.create_config_file.side_effect = IOError(
            "Permission denied")

        # Execute and Assert
        with pytest.raises(IOError, match="Permission denied"):
            setup._create_files()

    def test_create_files_token_file_creation_failure(self, mock_dependencies):
        """
        Test that the _create_files method no longer raises errors for token file creation.

        With centralized token management, token files are not created during setup,
        so this test is no longer applicable. Instead, verify that _create_files
        completes successfully without calling create_token_files().
        """
        setup = AssignmentSetup()
        setup.config_values = {'USE_SECRETS': 'true'}
        setup.token_files = {}  # Empty with centralized tokens
        setup.token_validation = {}  # Empty with centralized tokens

        # Execute - should complete without error since no token files are created
        setup._create_files()

        # Assert - verify create_token_files was NOT called
        setup.file_manager.create_token_files.assert_not_called()

    def test_create_files_gitignore_update_failure(self, mock_dependencies):
        """
        Test that the _create_files method raises an OSError when updating the .gitignore file fails.

        This test simulates a failure in the file_manager's update_gitignore method by setting its side_effect to an OSError.
        It verifies that the _create_files method properly propagates the exception when such a failure occurs.
        """
        setup = AssignmentSetup()
        setup.config_values = {'USE_SECRETS': 'false'}
        setup.token_files = {}
        setup.token_validation = {}

        # Setup mock to fail on gitignore update
        setup.file_manager.update_gitignore.side_effect = OSError(
            "File system error")

        # Execute and Assert
        with pytest.raises(OSError, match="File system error"):
            setup._create_files()

    def test_configure_tokens_empty_token_input(self, mock_dependencies):
        """
        Test that the token configuration process uses centralized token management.

        With centralized tokens, this method no longer prompts for token input,
        so empty token scenarios are not applicable to the setup wizard.
        Tokens are validated by the centralized token manager.
        """
        with patch('classdock.assignments.setup.print_colored'):
            setup = AssignmentSetup()

            # Execute
            setup._configure_tokens()

            # Assert - no token values are stored in config with centralized approach
            assert 'INSTRUCTOR_TESTS_TOKEN_VALUE' not in setup.config_values
            assert len(setup.token_validation) == 0

    def test_collect_repository_info_whitespace_in_url(self, mock_dependencies):
        """
        Test that the _collect_repository_info method correctly handles whitespace in template URL input.
        The URL is validated and stored as-is (trimming is the responsibility of validators if needed).
        """
        setup = AssignmentSetup()
        setup.config_values = {
            'GITHUB_ORGANIZATION': 'test-org',
            'ASSIGNMENT_NAME': 'test-assignment'
        }

        # Mock validators to accept the whitespace URL
        setup.validators.validate_url = Mock(return_value=(True, None))
        setup.input_handler.prompt_input.return_value = \
            "  https://github.com/test-org/test-assignment-template  "

        # Execute
        setup._collect_repository_info()

        # Assert value stored as returned by input handler
        assert setup.config_values['TEMPLATE_REPO_URL'] == \
            "  https://github.com/test-org/test-assignment-template  "

    def test_multiple_consecutive_wizard_runs(self, mock_dependencies):
        """
        Test that running the setup wizard multiple times in succession maintains state isolation between runs.

        This test ensures that each instance of the AssignmentSetup class has its own independent state,
        so that changes in one run do not affect another. It mocks out all interactive and side-effectful
        methods to focus on state management, and verifies that configuration values set in one wizard run
        do not leak into another.
        """
        with patch('classdock.assignments.setup.show_welcome'), \
                patch('classdock.assignments.setup.show_completion'), \
                patch('classdock.assignments.setup.print_success'), \
                patch('classdock.assignments.setup.logger'):

            # First wizard run
            setup1 = AssignmentSetup()
            setup1._collect_assignment_info = Mock()
            setup1._collect_repository_info = Mock()
            setup1._collect_assignment_details = Mock()
            setup1._configure_secret_management = Mock()
            setup1._create_files = Mock()

            setup1.config_values['TEST_KEY'] = 'first_run'
            setup1.run_wizard()

            # Second wizard run
            setup2 = AssignmentSetup()
            setup2._collect_assignment_info = Mock()
            setup2._collect_repository_info = Mock()
            setup2._collect_assignment_details = Mock()
            setup2._configure_secret_management = Mock()
            setup2._create_files = Mock()

            setup2.config_values['TEST_KEY'] = 'second_run'
            setup2.run_wizard()

            # Assert state isolation
            assert setup1.config_values['TEST_KEY'] == 'first_run'
            assert setup2.config_values['TEST_KEY'] == 'second_run'

    def test_path_manager_workspace_root_failure(self, mock_dependencies):
        """
        Test that AssignmentSetup raises a FileNotFoundError with the expected message
        when PathManager fails to find the workspace root during initialization.
        """
        with patch('classdock.assignments.setup.PathManager') as mock_path_mgr:
            mock_path_instance = Mock()
            mock_path_instance.get_workspace_root.side_effect = FileNotFoundError(
                "No workspace found")
            mock_path_mgr.return_value = mock_path_instance

            # Execute and Assert
            with pytest.raises(FileNotFoundError, match="No workspace found"):
                AssignmentSetup()

    def test_config_generator_initialization_failure(self, mock_dependencies):
        """
        Test that AssignmentSetup raises a ValueError with the expected message when
        ConfigGenerator fails to initialize due to an invalid config file path.
        This ensures proper error propagation during setup initialization.
        """
        with patch('classdock.assignments.setup.ConfigGenerator') as mock_config_gen:
            mock_config_gen.side_effect = ValueError(
                "Invalid config file path")

            # Execute and Assert
            with pytest.raises(ValueError, match="Invalid config file path"):
                AssignmentSetup()


class TestInputValidationEdgeCases:
    """
    TestInputValidationEdgeCases contains test cases focused on verifying the robustness of input validation logic within the assignment setup workflow.

    This test class ensures:
    - The system correctly handles validation failures followed by user retries during assignment information collection.
    - Organization names with special characters (such as dashes, dots, and underscores) are properly accepted.

    Mocks are used to simulate user input and validation behaviors, and assertions verify that configuration values are set as expected after handling these edge cases.
    """

    def test_collect_assignment_info_stores_name_and_org(self, mock_dependencies):
        """
        Test that the assignment info collection process stores assignment name and org.
        Simulates providing both an assignment name and a GitHub organization.
        """
        setup = AssignmentSetup()

        setup.input_handler.prompt_input.side_effect = [
            "python-basics",  # assignment name
            "my-github-org",  # GitHub organization
        ]

        # Execute
        setup._collect_assignment_info()

        # Assert
        assert setup.config_values['ASSIGNMENT_NAME'] == "python-basics"
        assert setup.config_values['GITHUB_ORGANIZATION'] == "my-github-org"
        assert setup.input_handler.prompt_input.called

    def test_collect_repository_info_organization_validation_edge_cases(self, mock_dependencies):
        """
        Test that the _collect_repository_info method correctly handles edge cases for template URLs,
        such as URLs containing dashes, underscores, and dots. Ensures that the template repository URL
        is properly stored in the configuration.
        """
        setup = AssignmentSetup()
        setup.config_values = {
            'GITHUB_ORGANIZATION': 'Org.With.Dots',
            'ASSIGNMENT_NAME': 'assignment_with_underscores'
        }

        # Mock validators to accept the URL
        setup.validators.validate_url = Mock(return_value=(True, None))

        setup.input_handler.prompt_input.return_value = \
            "https://github.com/Org.With.Dots/assignment_with_underscores-template.git"

        # Execute
        setup._collect_repository_info()

        # Assert
        assert "Org.With.Dots" in setup.config_values['TEMPLATE_REPO_URL']


class TestAssignmentSetupURLMethods:
    """Test that removed URL-based setup methods no longer exist on AssignmentSetup."""

    def test_run_wizard_with_url_method_removed(self, mock_dependencies):
        """Verify run_wizard_with_url has been removed from AssignmentSetup."""
        setup = AssignmentSetup()
        assert not hasattr(setup, 'run_wizard_with_url'), \
            "run_wizard_with_url should have been removed"

    def test_populate_from_url_method_removed(self, mock_dependencies):
        """Verify _populate_from_url has been removed from AssignmentSetup."""
        setup = AssignmentSetup()
        assert not hasattr(setup, '_populate_from_url'), \
            "_populate_from_url should have been removed"

    def test_url_parser_attribute_removed(self, mock_dependencies):
        """Verify url_parser attribute has been removed from AssignmentSetup."""
        setup = AssignmentSetup()
        assert not hasattr(setup, 'url_parser'), \
            "url_parser attribute should have been removed"

    def test_run_wizard_succeeds_without_url(self, mock_dependencies):
        """Test that run_wizard works correctly without any URL input."""
        with patch('classdock.assignments.setup.show_welcome'), \
                patch('classdock.assignments.setup.show_completion'), \
                patch('classdock.assignments.setup.print_success'), \
                patch('classdock.assignments.setup.logger'):

            setup = AssignmentSetup()
            setup._collect_assignment_info = Mock()
            setup._collect_repository_info = Mock()
            setup._collect_assignment_details = Mock()
            setup._configure_secret_management = Mock()
            setup._create_files = Mock()

            result = setup.run_wizard()

            assert result is True

    def test_collect_assignment_info_uses_assignment_name_key(self, mock_dependencies):
        """Test that _collect_assignment_info stores ASSIGNMENT_NAME (not CLASSROOM_URL)."""
        setup = AssignmentSetup()
        setup.input_handler.prompt_input.side_effect = ["my-assignment", "my-org"]

        setup._collect_assignment_info()

        assert 'ASSIGNMENT_NAME' in setup.config_values
        assert 'CLASSROOM_URL' not in setup.config_values


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
