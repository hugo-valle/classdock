"""
Assignment setup and configuration wizard.

This module provides the interactive setup wizard for creating new assignment configurations.
"""

import sys

from ..config.generator import ConfigGenerator
from ..utils import PathManager, get_logger
from ..utils.file_operations import FileManager
from ..utils.input_handlers import InputHandler, Validators
from ..utils.ui_components import (
    Colors,
    print_colored,
    print_error,
    print_success,
    show_completion,
    show_welcome,
)

logger = get_logger("assignments.setup")


class AssignmentSetup:
    """
    AssignmentSetup provides an interactive wizard for configuring ClassDock assignments.

    Guides the user through setting up assignment configuration, including:
    - Collecting assignment name and organization directly.
    - Configuring optional template repository reference.
    - Gathering assignment-specific details such as the main assignment file.
    - Configuring secret management for instructor-only tests.
    - Creating necessary configuration files.
    """

    def __init__(self):
        self.path_manager = PathManager()
        self.repo_root = self.path_manager.get_workspace_root()
        self.config_file = self.repo_root / "assignment.conf"

        self.input_handler = InputHandler()
        self.validators = Validators()
        self.config_generator = ConfigGenerator(self.config_file)
        self.file_manager = FileManager(self.repo_root)

        self.config_values = {}
        self.token_files = {}
        self.token_validation = {}

    def run_wizard(self):
        """Run the complete setup wizard for assignment configuration."""
        try:
            logger.info("Starting assignment setup wizard")

            show_welcome()

            self._collect_assignment_info()
            self._collect_repository_info()
            self._collect_assignment_details()
            self._configure_secret_management()
            self._create_files()

            show_completion(self.config_values, self.token_files)

            print_success("Assignment setup completed successfully!")
            logger.info("Assignment setup wizard completed")
            return True

        except KeyboardInterrupt:
            print_colored("Setup cancelled by user.", Colors.YELLOW)
            logger.info("Setup wizard cancelled by user")
            return False
        except Exception as e:
            print_error(f"Setup failed: {e}")
            logger.error(f"Setup wizard failed: {e}")
            return False

    def _collect_assignment_info(self):
        """Prompt for assignment name and GitHub organization."""
        logger.debug("Collecting assignment information")

        assignment_name = self.input_handler.prompt_input(
            "Assignment name",
            "",
            self.validators.validate_assignment_name,
            "Used as the prefix when discovering student repos. "
            "Example: if students have 'python-basics-jdoe', enter 'python-basics'",
        )
        self.config_values["ASSIGNMENT_NAME"] = assignment_name

        github_org = self.input_handler.prompt_input(
            "GitHub organization name",
            "",
            self.validators.validate_organization,
            "The GitHub organization where student repositories live",
        )
        self.config_values["GITHUB_ORGANIZATION"] = github_org

    def _collect_repository_info(self):
        """Prompt for optional template repository URL."""
        logger.debug("Collecting repository information")

        assignment_name = self.config_values.get("ASSIGNMENT_NAME", "")
        github_org = self.config_values.get("GITHUB_ORGANIZATION", "")
        default_template = (
            f"https://github.com/{github_org}/{assignment_name}-template"
            if github_org and assignment_name
            else ""
        )

        template_url = self.input_handler.prompt_input(
            "Template repository URL (optional)",
            default_template,
            None,
            "Reference to the template repo (leave empty to skip)",
        )

        if template_url:
            valid, error = self.validators.validate_url(template_url)
            if valid:
                self.config_values["TEMPLATE_REPO_URL"] = template_url
            else:
                print_error(f"Invalid template URL ({error}). Skipping.")
                logger.warning(f"Invalid TEMPLATE_REPO_URL provided: {template_url}")

    def _collect_assignment_details(self):
        """Gather assignment-specific details such as the main assignment file."""
        logger.debug("Collecting assignment details")

        main_file = self.input_handler.prompt_input(
            "Main assignment file",
            "assignment.ipynb",
            self.validators.validate_file_path,
            "The primary file students work on (e.g., assignment.ipynb, main.py, homework.cpp)",
        )
        self.config_values["MAIN_ASSIGNMENT_FILE"] = main_file

    def _configure_secret_management(self):
        """Configure secret management settings for assignment tests."""
        logger.debug("Configuring secret management")

        print_colored("Where are your assignment tests located?", Colors.BLUE)
        print_colored(
            "   Option 1: Tests are included in the template repository (simpler setup)",
            Colors.CYAN,
        )
        print_colored(
            "   Option 2: Tests are in a separate private instructor repository (more secure)",
            Colors.CYAN,
        )

        use_secrets = self.input_handler.prompt_yes_no(
            "Do you have tests in a separate private instructor repository?", False
        )

        if use_secrets:
            self.config_values["USE_SECRETS"] = "true"
            print_success(
                "Secret management will be enabled for accessing instructor test repository"
            )
            self._configure_tokens()
        else:
            self.config_values["USE_SECRETS"] = "false"
            print_success(
                "Secret management will be disabled (tests in template repository)"
            )

    def _configure_tokens(self):
        """Inform the user about centralized token management for secrets."""
        logger.debug("Configuring token settings for secrets")

        print_colored(
            "Secrets will use your centralized GitHub token from GitHubTokenManager",
            Colors.BLUE,
        )
        print_colored(
            "Token is stored in: ~/.config/classdock/token_config.json", Colors.CYAN
        )

    def _create_files(self):
        """Create configuration and .gitignore files."""
        logger.debug("Creating configuration files")

        self.config_generator.create_config_file(
            self.config_values, self.token_files, self.token_validation
        )

        self.file_manager.update_gitignore()


def setup_assignment():
    """Initialize and run the assignment setup wizard."""
    setup = AssignmentSetup()
    setup.run_wizard()


if __name__ == "__main__":
    setup_assignment()
