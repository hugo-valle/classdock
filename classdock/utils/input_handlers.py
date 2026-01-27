"""
Input Handlers and Validation for the GitHub Classroom Setup Wizard.

This module provides input prompting, validation functions, and URL parsing utilities.
"""

import re
import sys
from getpass import getpass
from typing import Optional, Callable

from .ui_components import print_error, print_colored, Colors


class InputHandler:
    """Handle user input with validation and prompting."""

    @staticmethod
    def prompt_input(
        prompt: str,
        default: str = "",
        validator: Optional[Callable] = None,
        help_text: str = "",
        allow_quit: bool = True
    ) -> str:
        """Prompt for input with validation and quit option."""
        while True:
            if help_text:
                print_colored(f"💡 {help_text}", Colors.BLUE)

            # Add quit instruction to help text
            if allow_quit and help_text:
                print_colored("💡 Type 'q' or 'quit' to exit", Colors.CYAN)

            if default:
                quit_hint = " (q to quit)" if allow_quit else ""
                display_prompt = f"{prompt} [{default}]{quit_hint}: "
            else:
                quit_hint = " (q to quit)" if allow_quit else ""
                display_prompt = f"{prompt}{quit_hint}: "

            print_colored(display_prompt, Colors.GREEN, end="")

            try:
                # Handle interactive vs non-interactive mode
                if sys.stdin.isatty():
                    value = input()
                else:
                    value = input() if sys.stdin.readable() else default
            except (EOFError, KeyboardInterrupt):
                if allow_quit:
                    print_colored(
                        "\n👋 Exiting setup wizard. You can restart anytime with: classdock assignments setup", Colors.CYAN)
                    sys.exit(0)
                else:
                    value = default

            # Handle quit commands
            if allow_quit and value.lower().strip() in ['q', 'quit', 'exit']:
                print_colored(
                    "👋 Exiting setup wizard. You can restart anytime with: classdock assignments setup", Colors.CYAN)
                sys.exit(0)

            # Use default if empty
            if not value and default:
                value = default

            # Validate input if validator provided
            if validator:
                try:
                    if validator(value):
                        return value
                    else:
                        print_error("Invalid input. Please try again.")
                        if allow_quit:
                            print_colored(
                                "💡 Type 'q' to quit if you need to exit", Colors.YELLOW)
                        continue
                except Exception as e:
                    print_error(f"Validation error: {e}")
                    if allow_quit:
                        print_colored(
                            "💡 Type 'q' to quit if you need to exit", Colors.YELLOW)
                    continue
            else:
                return value

    @staticmethod
    def prompt_secure(prompt: str, help_text: str = "", allow_quit: bool = True) -> str:
        """Prompt for secure input (passwords/tokens)."""
        if help_text:
            print_colored(f"💡 {help_text}", Colors.BLUE)

        if allow_quit:
            print_colored("💡 Type 'q' or 'quit' to exit", Colors.CYAN)

        quit_hint = " (q to quit)" if allow_quit else ""
        print_colored(f"{prompt}{quit_hint}: ", Colors.GREEN, end="")

        try:
            if sys.stdin.isatty():
                value = getpass("")
            else:
                value = input()  # Fallback for non-interactive mode
        except (EOFError, KeyboardInterrupt):
            if allow_quit:
                print_colored(
                    "\n👋 Exiting setup wizard. You can restart anytime with: classdock assignments setup", Colors.CYAN)
                sys.exit(0)
            value = ""

        # Handle quit commands
        if allow_quit and value.lower().strip() in ['q', 'quit', 'exit']:
            print_colored(
                "👋 Exiting setup wizard. You can restart anytime with: classdock assignments setup", Colors.CYAN)
            sys.exit(0)

        return value

    @staticmethod
    def prompt_yes_no(prompt: str, default: bool = False, allow_quit: bool = True) -> bool:
        """Prompt for yes/no input with optional quit."""
        if allow_quit:
            default_text = "Y/n/q" if default else "y/N/q"
        else:
            default_text = "Y/n" if default else "y/N"

        response = InputHandler.prompt_input(
            f"{prompt} ({default_text})",
            default="",
            allow_quit=allow_quit
        )

        if not response:
            return default

        return response.lower().startswith('y')


class Validators:
    """Collection of input validation functions."""

    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate GitHub or GitHub Classroom URL."""
        github_pattern = r'^https://github\.com/.+/.+$'

        # Multiple classroom URL patterns to be more flexible
        classroom_patterns = [
            r'^https://classroom\.github\.com/classrooms/.+/assignments/.+$',
            r'^https://classroom\.github\.com/a/.+$',
            r'^https://classroom\.github\.com/assignment-invitations/.+$',
            r'^https://classroom\.github\.com/assignments/.+$'
        ]

        # Check GitHub repository URL
        if re.match(github_pattern, url):
            return True

        # Check any of the classroom URL patterns
        for pattern in classroom_patterns:
            if re.match(pattern, url):
                return True

        print_error("Please enter a valid GitHub or GitHub Classroom URL")
        return False

    @staticmethod
    def validate_organization(org: str) -> bool:
        """Validate GitHub organization name."""
        if re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$', org):
            return True
        else:
            print_error(
                "Organization name must contain only letters, numbers, and hyphens")
            return False

    @staticmethod
    def validate_assignment_name(name: str) -> bool:
        """Validate assignment name."""
        if not name:  # Allow empty names
            return True
        if re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9_-]*[a-zA-Z0-9])?$', name):
            return True
        else:
            print_error(
                "Assignment name must contain only letters, numbers, hyphens, and underscores")
            return False

    @staticmethod
    def validate_file_path(file_path: str) -> bool:
        """Validate file path has proper extension."""
        valid_extensions = {'.ipynb', '.py', '.cpp', '.sql', '.md',
                            '.html', '.js', '.ts', '.java', '.c', '.h', '.hpp', '.txt'}

        if any(file_path.endswith(ext) for ext in valid_extensions):
            return True
        else:
            print_error(
                "Please specify a valid file extension (.ipynb, .py, .cpp, .sql, .md, etc.)")
            return False

    @staticmethod
    def validate_student_files(student_files: str) -> bool:
        """
        Validate student files configuration (supports comma-separated files, patterns, and folders).

        Args:
            student_files: Comma-separated list of files, patterns, or folders to validate

        Returns:
            bool: True if valid, False otherwise
        """
        if not student_files:
            print_error("Student files cannot be empty")
            return False

        # Split by comma and validate each entry
        file_entries = [entry.strip()
                        for entry in student_files.split(',') if entry.strip()]

        if not file_entries:
            print_error(
                "At least one file, pattern, or folder must be specified")
            return False

        valid_extensions = {'.ipynb', '.py', '.cpp', '.sql', '.md', '.asm',
                            '.html', '.js', '.ts', '.java', '.c', '.h', '.hpp', '.txt', '.csv', '.json'}

        for entry in file_entries:
            # Check for folders (ending with /)
            if entry.endswith('/'):
                if len(entry) < 2:
                    print_error(f"Folder path '{entry}' is too short")
                    return False
                continue

            # Check for glob patterns (containing wildcards)
            if '*' in entry or '?' in entry or '[' in entry:
                # Basic validation for glob patterns
                if entry.startswith('**/') or entry.endswith('/**'):
                    continue  # Valid recursive patterns
                if any(char in entry for char in ['*', '?']):
                    continue  # Valid glob patterns

            # Check regular files
            if not any(entry.endswith(ext) for ext in valid_extensions):
                print_error(
                    f"File '{entry}' must have a valid extension: {', '.join(sorted(valid_extensions))}")
                return False

        return True

    @staticmethod
    def validate_non_empty(value: str) -> bool:
        """Validate that value is not empty."""
        if value.strip():
            return True
        else:
            print_error("This field cannot be empty")
            return False


class URLParser:
    """Utility functions for parsing URLs and extracting information."""

    @staticmethod
    def extract_assignment_from_url(url: str) -> str:
        """Extract assignment name from URL."""
        match = re.search(r'/([^/]+)/?$', url)
        return match.group(1) if match else ""

    @staticmethod
    def extract_org_from_url(url: str) -> str:
        """Extract organization from GitHub URL."""
        match = re.search(r'github\.com/([^/]+)/', url)
        return match.group(1) if match else ""

    @staticmethod
    def parse_classroom_url(url: str) -> dict:
        """
        Parse GitHub Classroom assignment URL and extract information.

        Supports URLs like:
        - https://classroom.github.com/classrooms/12345/assignments/assignment-name
        - https://classroom.github.com/a/assignment-id
        - https://classroom.github.com/assignment-invitations/assignment-id
        - Direct GitHub repo URLs from classroom templates

        Args:
            url: GitHub Classroom assignment URL

        Returns:
            dict: Extracted information including assignment_id, organization, etc.
        """
        result = {
            'assignment_id': '',
            'organization': '',
            'template_repo': '',
            'assignment_name': '',
            'classroom_id': '',
            'is_classroom_url': False,
            'is_repo_url': False
        }

        # GitHub Classroom URL patterns
        classroom_patterns = [
            # Pattern: https://classroom.github.com/classrooms/ID/assignments/NAME
            (r'classroom\.github\.com/classrooms/([^/]+)/assignments/([^/?]+)', 'full_classroom'),
            # Pattern: https://classroom.github.com/a/assignment-id
            (r'classroom\.github\.com/a/([^/?]+)', 'short_classroom'),
            # Pattern: https://classroom.github.com/assignment-invitations/assignment-id
            (r'classroom\.github\.com/assignment-invitations/([^/?]+)', 'invitation'),
            # Pattern: https://classroom.github.com/assignments/assignment-id
            (r'classroom\.github\.com/assignments/([^/?]+)',
             'direct_assignment')
        ]

        for pattern, pattern_type in classroom_patterns:
            match = re.search(pattern, url)
            if match:
                result['is_classroom_url'] = True
                if pattern_type == 'full_classroom':
                    result['classroom_id'] = match.group(1)
                    result['assignment_name'] = match.group(2)
                    result['assignment_id'] = match.group(2)

                    # Try to extract organization from classroom ID if it contains org info
                    classroom_id = match.group(1)
                    if '-' in classroom_id:
                        # Format like: 228391192-soc-simple-classroom-template
                        parts = classroom_id.split('-', 1)
                        if len(parts) > 1:
                            # Extract potential organization from the second part
                            org_part = parts[1]
                            # Remove common classroom suffixes (classroom, template)
                            # This handles cases like "soc-simple-classroom-template" -> "soc-simple"
                            org_part = re.sub(
                                r'(-classroom|-template)+.*$', '', org_part)
                            if org_part:  # Only set if we have a valid org part left
                                result['organization'] = org_part
                else:
                    result['assignment_id'] = match.group(1)
                    result['assignment_name'] = match.group(1)
                break

        # Direct GitHub repository URL (template or student repo)
        github_repo_pattern = r'github\.com/([^/]+)/([^/?]+)'
        repo_match = re.search(github_repo_pattern, url)
        if repo_match and not result['is_classroom_url']:
            result['organization'] = repo_match.group(1)
            result['template_repo'] = repo_match.group(2)
            result['assignment_name'] = repo_match.group(2)
            result['is_repo_url'] = True

        return result

    @staticmethod
    def validate_classroom_url(url: str) -> bool:
        """Validate if URL is a valid GitHub Classroom or GitHub repository URL."""
        if not url:
            return False

        # Check for GitHub Classroom URLs
        classroom_patterns = [
            r'classroom\.github\.com/classrooms/[^/]+/assignments/',
            r'classroom\.github\.com/a/',
            r'classroom\.github\.com/assignment-invitations/',
            r'classroom\.github\.com/assignments/'
        ]

        for pattern in classroom_patterns:
            if re.search(pattern, url):
                return True

        # Check for GitHub repository URLs
        if re.search(r'github\.com/[^/]+/[^/?]+', url):
            return True

        return False
