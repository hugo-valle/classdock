"""
Assignment setup and configuration wizard.

This module provides the interactive setup wizard for creating new assignment configurations.
"""

import os
import sys

from ..config.generator import ConfigGenerator
from ..utils import get_logger, PathManager
from ..utils.ui_components import (
    Colors, print_colored, print_error, print_success, print_status,
    show_welcome, show_completion
)
from ..utils.input_handlers import InputHandler, Validators, URLParser
from ..utils.file_operations import FileManager

logger = get_logger("assignments.setup")


class AssignmentSetup:
    """
    AssignmentSetup provides an interactive wizard for configuring GitHub Classroom assignments.

    This class guides the user through the process of setting up assignment configuration, including:
    - Collecting assignment and repository information.
    - Gathering assignment-specific details such as assignment name and main file.
    - Configuring secret management for instructor-only tests.
    - Creating necessary configuration and token files.
    - Handling user input, validation, and error management throughout the setup process.

    Attributes:
        path_manager (PathManager): Handles workspace and path management.
        repo_root (Path): The root directory of the repository.
        config_file (Path): Path to the assignment configuration file.
        input_handler (InputHandler): Manages user input and prompts.
        validators (Validators): Provides input validation methods.
        url_parser (URLParser): Extracts information from GitHub Classroom URLs.
        config_generator (ConfigGenerator): Generates configuration files.
        file_manager (FileManager): Manages file creation and updates.
        config_values (dict): Stores collected configuration values.
        token_files (dict): Maps token names to their respective file paths.
        token_validation (dict): Stores token validation preferences.

    Methods:
        run_wizard():
            Runs the interactive setup wizard, orchestrating the full configuration process.
        _collect_assignment_info():
            Prompts for and validates the GitHub Classroom assignment URL.
        _collect_repository_info():
            Extracts and collects repository-related information, including organization and template repo URL.
        _collect_assignment_details():
            Gathers assignment-specific details such as assignment name and main file.
        _configure_secret_management():
            Configures secret management options for instructor-only tests.
        _configure_tokens():
            Prompts for and stores GitHub personal access tokens for instructor test repositories.
        _create_files():
            Creates configuration and token files, and updates .gitignore as needed.
    """

    def __init__(self):
        """
        Initializes the class by setting up path management, configuration file location, input handling, validation, URL parsing, configuration generation, and file management. 
        Also initializes dictionaries for storing configuration values, token files, and token validation results.
        """
        self.path_manager = PathManager()
        self.repo_root = self.path_manager.get_workspace_root()
        self.config_file = self.repo_root / "assignment.conf"

        # Initialize handlers
        self.input_handler = InputHandler()
        self.validators = Validators()
        self.url_parser = URLParser()
        self.config_generator = ConfigGenerator(self.config_file)
        self.file_manager = FileManager(self.repo_root)

        # Data storage
        self.config_values = {}
        self.token_files = {}
        self.token_validation = {}

    def run_wizard_with_url(self, classroom_url: str):
        """
        Runs the setup wizard with a pre-populated GitHub Classroom URL.

        This method pre-populates the configuration with information extracted from
        the provided GitHub Classroom URL and then runs the interactive setup process
        for the remaining configuration options.

        Args:
            classroom_url: GitHub Classroom assignment URL

        Returns:
            bool: True if setup completed successfully, False otherwise
        """
        try:
            logger.info(
                f"Starting assignment setup wizard with URL: {classroom_url}")

            # Pre-populate configuration with URL information
            if not self._populate_from_url(classroom_url):
                return False

            # Show welcome screen
            show_welcome()

            # Skip assignment info collection since we have the URL
            logger.info("Using provided GitHub Classroom URL")
            print_colored(
                f"✓ GitHub Classroom URL: {classroom_url}", Colors.GREEN)

            # Collect repository information (may auto-populate from URL)
            self._collect_repository_info()

            # Collect assignment details
            self._collect_assignment_details()

            # Configure secret management
            self._configure_secret_management()

            # Create configuration files
            self._create_files()

            # Show completion
            show_completion(self.config_values, self.token_files)

            logger.info("Assignment setup completed successfully")
            return True

        except KeyboardInterrupt:
            print_error("\nSetup cancelled by user")
            logger.info("Setup cancelled by user")
            return False
        except Exception as e:
            print_error(f"Setup failed: {e}")
            logger.error(f"Setup failed: {e}")
            return False

    def _populate_from_url(self, classroom_url: str) -> bool:
        """
        Extract information from GitHub Classroom URL and populate configuration.

        This method first attempts to parse the URL directly. If URL parsing fails
        to extract the organization or if verification is needed, it falls back to
        using the GitHub API to fetch comprehensive classroom data.

        Args:
            classroom_url: GitHub Classroom assignment URL

        Returns:
            bool: True if URL was successfully parsed, False otherwise
        """
        try:
            # Validate and parse the URL
            if not URLParser.validate_classroom_url(classroom_url):
                print_error("Invalid GitHub Classroom URL format")
                return False

            # Store the classroom URL
            self.config_values['CLASSROOM_URL'] = classroom_url

            # First attempt: URL parsing
            parsed_result = self.url_parser.parse_classroom_url(classroom_url)
            org_name = parsed_result.get('organization', '')
            assignment_name = parsed_result.get('assignment_name', '')

            logger.info(
                f"URL parsing result: org='{org_name}', assignment='{assignment_name}'")

            # Determine if we should use API enhancement/validation
            should_use_api = False
            api_mode = os.getenv('CLASSROOM_API_MODE', 'auto').lower()

            if api_mode == 'always':
                # Always use API for validation/enhancement
                should_use_api = True
                logger.info("🔄 API mode set to 'always', will use GitHub API")
            elif api_mode == 'never':
                # Never use API, rely solely on URL parsing
                should_use_api = False
                logger.info(
                    "⚠️ API mode set to 'never', using URL parsing only")
            else:  # api_mode == 'auto' (default)
                if not (org_name and assignment_name):
                    # URL parsing failed to extract required data
                    should_use_api = True
                    logger.info(
                        "🔄 URL parsing incomplete, will use GitHub API")
                else:
                    # URL parsing succeeded, but check if organization looks like a classroom name
                    from ..utils.github_api_client import GitHubAPIClient
                    if GitHubAPIClient.is_likely_classroom_name(org_name):
                        should_use_api = True
                        logger.info(
                            f"🔍 Organization '{org_name}' appears to be a classroom name, will validate with GitHub API")
                    else:
                        logger.info(
                            f"✅ Organization '{org_name}' looks like a real GitHub organization, using URL parsing result")

            # Use URL parsing result if it looks reliable
            if not should_use_api:
                self.config_values['GITHUB_ORGANIZATION'] = org_name
                self.config_values['ASSIGNMENT_NAME'] = assignment_name
                logger.info(
                    f"✅ Successfully extracted from URL - Organization: {org_name}, Assignment: {assignment_name}")
                return True

            # Use GitHub API to extract/validate classroom data
            logger.info(
                "🔄 Using GitHub API to extract classroom data...")
            print_status(
                "Connecting to GitHub Classroom API to fetch assignment details...")

            try:
                from ..utils.github_api_client import GitHubAPIClient

                # Initialize API client and verify token
                api_client = GitHubAPIClient()
                if not api_client.verify_token():
                    print_error(
                        "GitHub token verification failed. Please check your GITHUB_TOKEN environment variable.")
                    return False

                print_status("✅ GitHub token verified successfully")

                # Extract classroom data using API
                api_result = api_client.extract_classroom_data_from_url(
                    classroom_url)

                if not api_result['success']:
                    print_error(
                        f"Failed to extract classroom data: {api_result['error']}")
                    # If API fails but we have partial data from URL parsing, use it
                    if org_name or assignment_name:
                        logger.info(
                            "Using partial data from URL parsing as fallback")
                        if org_name:
                            self.config_values['GITHUB_ORGANIZATION'] = org_name
                        if assignment_name:
                            self.config_values['ASSIGNMENT_NAME'] = assignment_name
                        return True
                    return False

                # Use API-extracted data
                api_org = api_result['organization']
                api_assignment = api_result['assignment_name']

                # Check if API provided useful organization data
                api_provided_org = bool(api_org and api_org.strip())

                if api_provided_org:
                    self.config_values['GITHUB_ORGANIZATION'] = api_org
                    logger.info(f"✅ API extracted organization: {api_org}")
                    print_status(f"Found organization: {api_org}")
                else:
                    # API succeeded but didn't provide organization - need user input
                    logger.info(
                        f"🔄 API succeeded but no organization data available")
                    logger.info(
                        f"URL parsing extracted classroom identifier: {org_name}")

                    # Since we know this is likely a classroom name, we should ask the user for the real org
                    from ..utils.github_api_client import GitHubAPIClient
                    if GitHubAPIClient.is_likely_classroom_name(org_name):
                        print_status(
                            f"⚠️  '{org_name}' appears to be a classroom identifier, not a GitHub organization")
                        print_status(
                            f"Please provide the actual GitHub organization name where student repositories are created")
                        # Don't pre-populate with classroom name - leave it empty for user to fill
                        # This will be handled in _collect_repository_info
                        logger.info(
                            f"Will prompt user for real organization name")
                    else:
                        # Use the URL parsing result as it might be valid
                        self.config_values['GITHUB_ORGANIZATION'] = org_name
                        print_status(
                            f"Using organization from URL: {org_name}")

                if api_assignment:
                    self.config_values['ASSIGNMENT_NAME'] = api_assignment
                    logger.info(
                        f"✅ API extracted assignment: {api_assignment}")
                    print_status(f"Found assignment: {api_assignment}")
                elif assignment_name:
                    # Fallback to URL parsing assignment name
                    self.config_values['ASSIGNMENT_NAME'] = assignment_name
                    logger.info(
                        f"🔄 Using URL parsing assignment: {assignment_name}")

                # Store additional API data if available
                if api_result.get('classroom_name'):
                    logger.info(
                        f"Classroom name: {api_result['classroom_name']}")

                if api_result.get('invite_link'):
                    logger.info(
                        f"Assignment invite link: {api_result['invite_link']}")

                return True

            except ImportError as e:
                logger.error(f"Failed to import GitHub API client: {e}")
                print_error("GitHub API client not available")
                return False
            except Exception as e:
                logger.error(f"GitHub API extraction failed: {e}")
                print_error(
                    f"Failed to fetch classroom data from GitHub API: {e}")

                # If API fails but we have partial data from URL parsing, use it
                if org_name or assignment_name:
                    logger.info(
                        "Using partial data from URL parsing as fallback")
                    if org_name:
                        self.config_values['GITHUB_ORGANIZATION'] = org_name
                    if assignment_name:
                        self.config_values['ASSIGNMENT_NAME'] = assignment_name
                    return True
                return False

        except Exception as e:
            print_error(f"Failed to parse GitHub Classroom URL: {e}")
            logger.error(f"URL parsing failed: {e}")
            return False

    # TODO: Implement simplified setup wizard
    # FEATURE REQUEST: Add run_wizard_simplified() method for streamlined setup
    # Should include:
    # - Minimal prompts (skip optional features)
    # - Sensible defaults for common configurations
    # - Focus on core fields: organization, assignment name, template repo
    # - Skip secret management setup (can be added later)
    # - Faster workflow for experienced users
    # - Same validation and file creation as full wizard
    # def run_wizard_simplified(self):
    #     """Simplified setup wizard with minimal prompts and sensible defaults."""
    #     pass

    def run_wizard(self):
        """
        Runs the complete setup wizard for assignment configuration.

        This method orchestrates the interactive setup process, including:
        - Displaying a welcome screen.
        - Collecting basic assignment and repository information.
        - Gathering assignment-specific details.
        - Configuring secret management.
        - Creating necessary configuration files.
        - Displaying a completion message upon success.

        Handles user cancellation (KeyboardInterrupt) and unexpected errors gracefully,
        logging relevant information and exiting with appropriate status codes.
        """
        try:
            logger.info("Starting assignment setup wizard")

            # Show welcome screen
            show_welcome()

            # Collect basic assignment information
            self._collect_assignment_info()

            # Collect repository information
            self._collect_repository_info()

            # Collect assignment details
            self._collect_assignment_details()

            # Configure secret management
            self._configure_secret_management()

            # Create configuration files
            self._create_files()

            # Show completion
            show_completion(self.config_values, self.token_files)

            print_success("Assignment setup completed successfully!")
            logger.info("Assignment setup wizard completed")
            # Return True to indicate success to callers (AssignmentService.setup)
            return True

        except KeyboardInterrupt:
            print_colored("Setup cancelled by user.", Colors.YELLOW)
            logger.info("Setup wizard cancelled by user")
            # Return False to indicate cancellation to the caller instead of exiting
            return False
        except Exception as e:
            print_error(f"Setup failed: {e}")
            logger.error(f"Setup wizard failed: {e}")
            # Return False so the service layer can handle the failure
            return False

    def _collect_assignment_info(self):
        """
        Collects basic assignment information from the user.

        Prompts the user to enter the GitHub Classroom assignment URL, validates the input,
        and stores it in the configuration values under the key 'CLASSROOM_URL'.

        Returns:
            None
        """
        logger.debug("Collecting assignment information")

        classroom_url = self.input_handler.prompt_input(
            "GitHub Classroom assignment URL",
            "",
            self.validators.validate_url,
            "Find this in GitHub Classroom when managing your assignment. Example: https://classroom.github.com/classrooms/12345/assignments/assignment-name"
        )
        self.config_values['CLASSROOM_URL'] = classroom_url

    def _collect_repository_info(self):
        """
        Collects and prompts for repository-related configuration values required for assignment setup.

        This method performs the following steps:
        1. Extracts the GitHub organization and assignment name from the provided classroom URL.
        2. Prompts the user to confirm or edit the GitHub organization name, validating the input.
        3. Prompts the user for the template repository URL, suggesting a default based on the organization and assignment name, and validates the input.
        4. Stores the collected values in the configuration dictionary.
        5. Exits the program with an error message if the template repository URL is not provided.

        Raises:
            SystemExit: If the template repository URL is not provided by the user.
        """
        logger.debug("Collecting repository information")

        # Use organization that was already extracted during URL parsing, or extract from URL as fallback
        if 'GITHUB_ORGANIZATION' in self.config_values and self.config_values['GITHUB_ORGANIZATION']:
            # Use the organization that was already correctly extracted during URL parsing
            extracted_org = self.config_values['GITHUB_ORGANIZATION']
        else:
            # No organization in config, check what URL parsing would give us
            parsed_result = self.url_parser.parse_classroom_url(
                self.config_values['CLASSROOM_URL'])
            url_org = parsed_result.get('organization', '')

            # If the URL organization looks like a classroom name, don't use it as default
            from ..utils.github_api_client import GitHubAPIClient
            if url_org and GitHubAPIClient.is_likely_classroom_name(url_org):
                # Use empty default when we detect classroom name - user should provide real org
                extracted_org = ''
                logger.info(
                    f"Detected classroom identifier '{url_org}' - prompting user for real organization")
                print_status(
                    f"⚠️  Detected classroom identifier '{url_org}' - please provide the actual GitHub organization name")
            else:
                # Use URL extraction result for non-classroom URLs
                extracted_org = url_org or self.url_parser.extract_org_from_url(
                    self.config_values['CLASSROOM_URL'])

        github_org = self.input_handler.prompt_input(
            "GitHub organization name",
            extracted_org,
            self.validators.validate_organization,
            "The GitHub organization that contains your assignment repositories (not the classroom name)"
        )
        self.config_values['GITHUB_ORGANIZATION'] = github_org

        # Extract assignment name
        if 'ASSIGNMENT_NAME' in self.config_values and self.config_values['ASSIGNMENT_NAME']:
            extracted_assignment = self.config_values['ASSIGNMENT_NAME']
        else:
            extracted_assignment = self.url_parser.extract_assignment_from_url(
                self.config_values['CLASSROOM_URL'])

        template_url = self.input_handler.prompt_input(
            "Template repository URL",
            f"https://github.com/{github_org}/{extracted_assignment}-template.git",
            self.validators.validate_url,
            "The TEMPLATE repository that students fork from (contains starter code/files). Usually has '-template' suffix."
        )

        if not template_url:
            print_error(
                "The Template repository URL is required for assignment setup.")
            sys.exit(1)

        self.config_values['TEMPLATE_REPO_URL'] = template_url

        # Prompt for classroom repository URL (optional but recommended for template synchronization)
        # Note: No validator since this is optional - user can press Enter to skip
        classroom_repo_url = self.input_handler.prompt_input(
            "GitHub Classroom repository URL (optional)",
            "",
            None,  # No validator - field is optional
            "The repository URL created by GitHub Classroom (e.g., https://github.com/org/classroom-semester-assignment). Leave empty if not using template synchronization."
        )

        if classroom_repo_url:
            # Validate the URL if one was provided
            if self.validators.validate_url(classroom_repo_url):
                self.config_values['CLASSROOM_REPO_URL'] = classroom_repo_url
            else:
                print_error(
                    "Invalid URL provided for Classroom repository. Skipping...")
                logger.warning(
                    f"Invalid CLASSROOM_REPO_URL provided: {classroom_repo_url}")

    def _collect_assignment_details(self):
        """
        Collects assignment-specific details from the user and updates the configuration values.

        This method prompts the user to provide the assignment name and the main assignment file.
        If the assignment name is not provided, it can be auto-extracted from the template URL.
        The main assignment file is the primary file students will work on (e.g., assignment.ipynb, main.py, homework.cpp).
        Both inputs are validated using the appropriate validators before being stored in the configuration.

        Raises:
            ValidationError: If the provided assignment name or file path does not pass validation.
        """
        logger.debug("Collecting assignment details")

        # Use assignment name that was already extracted during URL parsing, or extract from URL as fallback
        if 'ASSIGNMENT_NAME' in self.config_values and self.config_values['ASSIGNMENT_NAME']:
            # Use the assignment name that was already correctly extracted during URL parsing
            extracted_assignment = self.config_values['ASSIGNMENT_NAME']
        else:
            # Fallback to URL extraction
            extracted_assignment = self.url_parser.extract_assignment_from_url(
                self.config_values['CLASSROOM_URL'])

        assignment_name = self.input_handler.prompt_input(
            "Assignment name (optional)",
            extracted_assignment,
            self.validators.validate_assignment_name,
            "Leave empty to auto-extract from template URL"
        )
        self.config_values['ASSIGNMENT_NAME'] = assignment_name

        main_file = self.input_handler.prompt_input(
            "Main assignment file",
            "assignment.ipynb",
            self.validators.validate_file_path,
            "The primary file students work on (e.g., assignment.ipynb, main.py, homework.cpp)"
        )
        self.config_values['MAIN_ASSIGNMENT_FILE'] = main_file

    def _configure_secret_management(self):
        """
        Configure secret management settings for assignment tests.

        This method prompts the user to specify the location of assignment tests:
        either within the template repository (simpler setup) or in a separate
        private instructor repository (more secure). Based on the user's choice,
        it enables or disables secret management for accessing the instructor test
        repository and updates the configuration accordingly.
        """
        logger.debug("Configuring secret management")

        print_colored("Where are your assignment tests located?", Colors.BLUE)
        print_colored(
            "   Option 1: Tests are included in the template repository (simpler setup)", Colors.CYAN)
        print_colored(
            "   Option 2: Tests are in a separate private instructor repository (more secure)", Colors.CYAN)

        use_secrets = self.input_handler.prompt_yes_no(
            "Do you have tests in a separate private instructor repository?",
            False
        )

        if use_secrets:
            self.config_values['USE_SECRETS'] = 'true'
            print_success(
                "✓ Secret management will be enabled for accessing instructor test repository")
            self._configure_tokens()
        else:
            self.config_values['USE_SECRETS'] = 'false'
            print_success(
                "✓ Secret management will be disabled (tests in template repository)")

    def _configure_tokens(self):
        """
        Configure token settings for secrets management.

        This method informs the user that the centralized GitHub token from
        GitHubTokenManager will be used for secrets management. No token files
        are created since tokens are managed centrally via ~/.config/classdock/.
        """
        logger.debug("Configuring token settings for secrets")

        print_colored(
            "💡 Secrets will use your centralized GitHub token from GitHubTokenManager", Colors.BLUE)
        print_colored(
            "Token is stored in: ~/.config/classdock/token_config.json", Colors.CYAN)

        # No longer prompt for token values or create token files
        # The centralized token system handles this automatically

    def _create_files(self):
        """
        Creates all necessary configuration files for the application.

        This method performs the following actions:
        1. Generates the main configuration file using the provided configuration values, token files, and token validation settings.
        2. Updates the .gitignore file to ensure sensitive files are excluded from version control.

        Note: Token files are no longer created since we use the centralized token system.
        """
        logger.debug("Creating configuration files")

        # Create configuration file
        self.config_generator.create_config_file(
            self.config_values,
            self.token_files,
            self.token_validation
        )

        # Skip creating token files - we use centralized token management now
        # No need to create instructor_token.txt or other token files

        # Update .gitignore
        self.file_manager.update_gitignore()


def setup_assignment():
    """
    Initializes and runs the assignment setup wizard.

    This function creates an instance of the AssignmentSetup class and starts
    the interactive setup process for configuring an assignment.

    Returns:
        None
    """
    setup = AssignmentSetup()
    setup.run_wizard()


if __name__ == "__main__":
    setup_assignment()
