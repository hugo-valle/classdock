"""
Configuration File Generator for the ClassDock Setup Wizard.

This module handles the generation of assignment configuration files
with all necessary sections and formatting.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict

from ..utils.ui_components import print_header, print_success


class ConfigGenerator:
    """
    ConfigGenerator is responsible for generating configuration files for GitHub Classroom assignments.

    This class provides methods to assemble and write a configuration file containing assignment information,
    secret management, workflow configuration, and advanced options. It supports injecting values for assignment
    URLs, repository details, secrets, and workflow steps, and can validate and format secrets as needed.

    Args:
        config_file (Path): The path where the generated configuration file will be written.

    Methods:
        create_config_file(config_values, token_files, token_validation):
            Generates and writes the configuration file using provided assignment and secret values.

        _generate_header():
            Returns the header section for the configuration file, including a timestamp.

        _generate_assignment_section(config_values):
            Returns the assignment information section, populated with URLs and assignment metadata.

        _generate_secrets_section(config_values, token_files, token_validation):
            Returns the secrets management section, including secret definitions and validation flags.

        _generate_workflow_section(config_values):
            Returns the workflow configuration section, specifying which steps to execute.

        _generate_advanced_section():
            Returns the advanced configuration section, including repository filtering and logging options.
    """

    def __init__(self, config_file: Path):
        """
        Initializes the configuration generator with the specified configuration file.

        Args:
            config_file (Path): The path to the configuration file.
        """
        self.config_file = config_file

    def create_config_file(
        self,
        config_values: Dict[str, str],
        token_files: Dict[str, str],
        token_validation: Dict[str, bool],
    ) -> None:
        """
        Creates a configuration file for the assignment using the provided configuration values, token files, and token validation results.

        Args:
            config_values (Dict[str, str]): Dictionary containing configuration values for the assignment.
            token_files (Dict[str, str]): Dictionary mapping token names to their corresponding file paths.
            token_validation (Dict[str, bool]): Dictionary indicating the validation status of each token.

        Returns:
            None

        Side Effects:
            Writes the generated configuration content to the file specified by self.config_file.
            Prints status messages to the console.
        """
        print_header("Creating Assignment Configuration")

        config_content = self._generate_header()
        config_content += self._generate_assignment_section(config_values)
        config_content += self._generate_secrets_section(
            config_values, token_files, token_validation
        )
        config_content += self._generate_workflow_section(config_values)
        config_content += self._generate_advanced_section()

        # Write configuration file
        with open(self.config_file, "w") as f:
            f.write(config_content)

        print_success(f"Configuration file created: {self.config_file}")

    def _generate_header(self) -> str:
        return f"""# ClassDock Assignment Configuration
# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# This file contains all the necessary information to manage an assignment with ClassDock

"""

    def _generate_assignment_section(self, config_values: Dict[str, str]) -> str:
        section = """# =============================================================================
# ASSIGNMENT INFORMATION
# =============================================================================

# Assignment name — used as the repository prefix when discovering student repos
# Example: if students have repos like "python-basics-jdoe", set ASSIGNMENT_NAME="python-basics"
ASSIGNMENT_NAME="{}"

# GitHub organization where student repositories live
GITHUB_ORGANIZATION="{}"

""".format(
            config_values.get("ASSIGNMENT_NAME", ""),
            config_values.get("GITHUB_ORGANIZATION", ""),
        )

        # Template repo URL is optional
        template_url = config_values.get("TEMPLATE_REPO_URL", "")
        if template_url:
            section += f'# Template repository (reference only)\nTEMPLATE_REPO_URL="{template_url}"\n\n'
        else:
            section += '# Template repository (optional reference)\n# TEMPLATE_REPO_URL="https://github.com/ORG/TEMPLATE-REPO"\n\n'

        section += f"""# Student Files Protection
# Protect these files/folders during template updates (comma-separated)
# Supports: specific files, glob patterns, and folder paths
STUDENT_FILES="{config_values.get('STUDENT_FILES', config_values.get('MAIN_ASSIGNMENT_FILE', 'assignment.ipynb'))}"

"""

        return section

    def _generate_secrets_section(
        self,
        config_values: Dict[str, str],
        token_files: Dict[str, str],
        token_validation: Dict[str, bool],
    ) -> str:
        """
        Generate the secrets management section for a configuration file.

        This method constructs a formatted string that documents and defines the secrets
        to be added to student repositories, based on the provided configuration values,
        token files, and token validation settings. It supports two modes:
        - When secrets management is enabled (`USE_SECRETS` is 'true'), it lists the secrets
            (including instructor test tokens and any additional secrets) with their descriptions,
            file paths, maximum age, and validation requirements.
        - When secrets management is disabled, it provides commented instructions and examples
            for configuring secrets, including guidance for assignments where tests are included
            in the template repository.

        Args:
                config_values (Dict[str, str]): Configuration values, including flags and secret descriptions.
                token_files (Dict[str, str]): Mapping of secret names to their corresponding token file paths.
                token_validation (Dict[str, bool]): Mapping of secret names to their validation requirements.

        Returns:
                str: The formatted secrets management section as a string.

        """
        section = """# =============================================================================
# SECRET MANAGEMENT
# =============================================================================

"""

        # Add secrets configuration
        if config_values.get("USE_SECRETS") == "true":
            secret_name = config_values.get("SECRET_NAME", "INSTRUCTOR_TESTS_TOKEN")
            description = config_values.get(
                "SECRET_DESCRIPTION", "Token for accessing instructor test repository"
            )
            validation = token_validation.get(secret_name, True)

            section += f"""# Secrets to add to student repositories
# Format: SECRET_NAME:description:validate_format
# validate_format: true for GitHub tokens (ghp_/github_pat_), false for other strings
SECRETS_CONFIG="
{secret_name}:{description}:{str(validation).lower()}
"
"""
        else:
            section += """# Secrets to add to student repositories
# NEW Format (v3.1+): SECRET_NAME:description:validate_format
# Uses centralized token management - no separate token files needed!
# validate_format: true for GitHub tokens (ghp_), false for other secrets
# 
# Use this when you have a separate private instructor repository with tests
# that students need access to via GitHub secrets.
# 
# If your tests are included in the same template repository, you can:
# 1. Set STEP_MANAGE_SECRETS=false in the WORKFLOW CONFIGURATION section, OR
# 2. Leave SECRETS_CONFIG empty (comment out or set to empty string)
# 
# SECRETS_CONFIG="
# INSTRUCTOR_TESTS_TOKEN:Token for accessing instructor test repository:true
# "

# For assignments where tests are in the template repository, use:
SECRETS_CONFIG=""

# Legacy format still supported (will be automatically converted):
# OLD Format: SECRET_NAME:description:token_file_path:max_age_days:validate_format
# SECRETS_CONFIG="
# INSTRUCTOR_TESTS_TOKEN:Token for accessing instructor test repository:instructor_token.txt:90:true
# "
"""

        section += "\n"
        return section

    def _generate_workflow_section(self, config_values: Dict[str, str]) -> str:
        """
        Generate the workflow configuration section as a formatted string.

        Args:
            config_values (Dict[str, str]): A dictionary containing configuration values,
                such as 'USE_SECRETS', to customize the workflow section.

        Returns:
            str: A string representing the workflow configuration section, with values
                interpolated from the provided config_values.

        """
        return f"""# =============================================================================
# WORKFLOW CONFIGURATION
# =============================================================================

# Workflow steps to execute (true/false)
STEP_SYNC_TEMPLATE=true
STEP_DISCOVER_REPOS=true
STEP_MANAGE_SECRETS={config_values.get('USE_SECRETS', 'false')}
STEP_ASSIST_STUDENTS=false

# Output directory for generated files
OUTPUT_DIR="tools/generated"

"""

    def _generate_advanced_section(self) -> str:
        """
        Generate the advanced configuration section as a formatted string.

        Returns:
            str: A multi-line string containing advanced configuration options,
                including repository filtering, dry run mode, logging level,
                and confirmation prompt settings.

        """
        return """# =============================================================================
# ADVANCED CONFIGURATION
# =============================================================================

# Repository filtering
EXCLUDE_INSTRUCTOR_REPOS=true
INCLUDE_TEMPLATE_REPO=false

# Dry run mode (for testing)
DEFAULT_DRY_RUN=false

# Logging level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Confirmation prompts
SKIP_CONFIRMATIONS=false
"""
