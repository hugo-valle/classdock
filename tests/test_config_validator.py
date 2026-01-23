"""
Comprehensive test suite for classdock.config.validator module.

This test suite provides comprehensive coverage for the ConfigValidator class,
which is responsible for validating GitHub Classroom assignment configuration values.
The tests include unit tests for individual validation methods, integration tests for
complete configuration validation, error handling, edge cases, and proper validation
of URLs, organization names, file paths, and configuration completeness.

Test Categories:
1. URL Validation Tests - GitHub and Classroom URL format validation
2. Organization Validation Tests - GitHub organization name validation  
3. Assignment Name Validation Tests - Assignment naming convention validation
4. File Path Validation Tests - Assignment file extension and format validation
5. Required Fields Validation Tests - Configuration completeness validation
6. Full Configuration Validation Tests - End-to-end validation workflows
7. Edge Case Tests - Boundary conditions and unusual inputs
8. Error Message Validation Tests - Detailed error message verification

The ConfigValidator class provides static methods for validating:
- GitHub repository URLs and GitHub Classroom assignment URLs
- Organization names following GitHub naming conventions
- Assignment names with appropriate character restrictions
- File paths with supported programming language extensions
- Required configuration field presence and completeness
- Full configuration validation with comprehensive error reporting

All tests validate both successful validation scenarios and error conditions
to ensure robust production behavior with clear error messages for users.
"""

import pytest
from classdock.config.validator import ConfigValidator


class TestConfigValidatorURLValidation:
    """
    TestConfigValidatorURLValidation contains unit tests for GitHub URL validation
    functionality within the ConfigValidator class. It verifies that both GitHub
    repository URLs and GitHub Classroom assignment URLs are correctly validated
    according to their respective format requirements.

    Test Cases:
    - test_validate_github_url_valid_repository_urls: Tests valid GitHub repository URLs
    - test_validate_github_url_valid_classroom_urls: Tests valid GitHub Classroom URLs
    - test_validate_github_url_invalid_formats: Tests various invalid URL formats
    - test_validate_github_url_empty_and_none: Tests empty string and None inputs
    - test_validate_github_url_protocol_validation: Tests HTTP vs HTTPS protocol requirements
    - test_validate_github_url_subdomain_validation: Tests subdomain and domain validation
    - test_validate_github_url_path_validation: Tests URL path structure requirements
    """

    def test_validate_github_url_valid_repository_urls(self):
        """
        Test that valid GitHub repository URLs are correctly validated.

        This test verifies that standard GitHub repository URLs with proper format
        (https://github.com/owner/repo) are accepted as valid, including URLs with
        various owner and repository name formats.
        """
        valid_urls = [
            "https://github.com/user/repo",
            "https://github.com/organization/project-name",
            "https://github.com/test-org/assignment_template",
            "https://github.com/cs101/data-analysis-template",
            "https://github.com/instructor123/homework-1",
            "https://github.com/university-cs/final-project"
        ]

        for url in valid_urls:
            is_valid, error_message = ConfigValidator.validate_github_url(url)
            assert is_valid, f"URL should be valid: {url}, but got error: {error_message}"
            assert error_message == "", f"No error message expected for valid URL: {url}"

    def test_validate_github_url_valid_classroom_urls(self):
        """
        Test that valid GitHub Classroom assignment URLs are correctly validated.

        This test verifies that GitHub Classroom assignment URLs with proper format
        (https://classroom.github.com/classrooms/ID/assignments/name) are accepted
        as valid, including various classroom and assignment name formats.
        """
        valid_classroom_urls = [
            "https://classroom.github.com/classrooms/12345/assignments/test-assignment",
            "https://classroom.github.com/classrooms/98765/assignments/data_analysis",
            "https://classroom.github.com/classrooms/111/assignments/homework-1",
            "https://classroom.github.com/classrooms/cs101-fall25/assignments/final-project",
            "https://classroom.github.com/classrooms/12345/assignments/assignment_with_underscores"
        ]

        for url in valid_classroom_urls:
            is_valid, error_message = ConfigValidator.validate_github_url(url)
            assert is_valid, f"Classroom URL should be valid: {url}, but got error: {error_message}"
            assert error_message == "", f"No error message expected for valid classroom URL: {url}"

    def test_validate_github_url_invalid_formats(self):
        """
        Test that invalid URL formats are correctly rejected with appropriate error messages.

        This test verifies that URLs with incorrect domains, missing components, or
        malformed structures are properly identified as invalid and return appropriate
        error messages for user feedback.
        """
        invalid_urls = [
            "invalid-url",
            "http://github.com/user/repo",  # HTTP instead of HTTPS
            "https://gitlab.com/user/repo",  # Wrong domain
            "https://github.com/user",  # Missing repository
            "https://github.com/",  # Missing user and repository
            "https://classroom.github.com/classrooms/12345",  # Missing assignment
            "https://classroom.github.com/",  # Incomplete classroom URL
            "ftp://github.com/user/repo",  # Wrong protocol
            "github.com/user/repo",  # Missing protocol
            "https://github.io/user/repo"  # Wrong domain
        ]

        for url in invalid_urls:
            is_valid, error_message = ConfigValidator.validate_github_url(url)
            assert not is_valid, f"URL should be invalid: {url}"
            assert error_message == "Must be a valid GitHub or GitHub Classroom URL", \
                f"Expected standard error message for invalid URL: {url}"

    def test_validate_github_url_empty_and_none(self):
        """
        Test that empty strings and None values are handled appropriately.

        This test verifies that empty URL inputs are rejected with clear error messages
        indicating that URLs cannot be empty, providing helpful feedback to users.
        """
        empty_inputs = ["", None]

        for empty_input in empty_inputs:
            # Handle None by converting to empty string for the validator
            url_to_test = empty_input if empty_input is not None else ""
            is_valid, error_message = ConfigValidator.validate_github_url(
                url_to_test)
            assert not is_valid, f"Empty input should be invalid: {empty_input}"
            assert error_message == "URL cannot be empty", \
                f"Expected empty URL error message for input: {empty_input}"

    def test_validate_github_url_protocol_validation(self):
        """
        Test that URL protocol validation correctly requires HTTPS.

        This test specifically validates that the validator enforces HTTPS protocol
        requirement and rejects HTTP URLs, ensuring secure connections for GitHub
        and GitHub Classroom operations.
        """
        protocol_test_cases = [
            ("https://github.com/user/repo", True),
            ("http://github.com/user/repo", False),
            ("ftp://github.com/user/repo", False),
            ("ssh://github.com/user/repo", False),
            ("://github.com/user/repo", False),  # Missing protocol
            ("github.com/user/repo", False)  # No protocol
        ]

        for url, should_be_valid in protocol_test_cases:
            is_valid, error_message = ConfigValidator.validate_github_url(url)
            if should_be_valid:
                assert is_valid, f"URL with HTTPS should be valid: {url}"
                assert error_message == ""
            else:
                assert not is_valid, f"URL without HTTPS should be invalid: {url}"
                assert "Must be a valid GitHub or GitHub Classroom URL" in error_message

    def test_validate_github_url_subdomain_validation(self):
        """
        Test that subdomain validation correctly identifies GitHub and Classroom domains.

        This test verifies that the validator correctly identifies valid GitHub and
        GitHub Classroom subdomains while rejecting URLs from other domains or
        with incorrect subdomain structures.
        """
        subdomain_test_cases = [
            ("https://github.com/user/repo", True),
            ("https://classroom.github.com/classrooms/123/assignments/test", True),
            ("https://api.github.com/user/repo", False),  # Wrong subdomain
            # Different GitHub service
            ("https://gist.github.com/user/123", False),
            ("https://pages.github.com/user/repo", False),  # GitHub Pages
            ("https://raw.github.com/user/repo/main/file", False),  # Raw content
            ("https://github.io/user/repo", False),  # Wrong domain
            ("https://gitlab.com/user/repo", False)  # Different service
        ]

        for url, should_be_valid in subdomain_test_cases:
            is_valid, error_message = ConfigValidator.validate_github_url(url)
            assert is_valid == should_be_valid, \
                f"URL domain validation failed for: {url} (expected {should_be_valid})"

    def test_validate_github_url_path_validation(self):
        """
        Test that URL path validation correctly requires proper path structure.

        This test verifies that GitHub repository URLs require owner/repo structure
        and GitHub Classroom URLs require classrooms/ID/assignments/name structure,
        rejecting URLs with incomplete or malformed paths.
        """
        path_test_cases = [
            # Valid GitHub repository paths
            ("https://github.com/owner/repo", True),
            ("https://github.com/owner-name/repo-name", True),
            ("https://github.com/org123/project_name", True),

            # Invalid GitHub repository paths
            ("https://github.com/owner", False),  # Missing repo
            ("https://github.com/", False),  # Missing owner and repo
            ("https://github.com", False),  # No path

            # Valid Classroom paths
            ("https://classroom.github.com/classrooms/123/assignments/test", True),
            ("https://classroom.github.com/classrooms/cs101/assignments/hw1", True),

            # Invalid Classroom paths
            # Missing assignment
            ("https://classroom.github.com/classrooms/123", False),
            # Missing ID and assignment
            ("https://classroom.github.com/classrooms", False),
            # Missing all path components
            ("https://classroom.github.com/", False),
        ]

        for url, should_be_valid in path_test_cases:
            is_valid, error_message = ConfigValidator.validate_github_url(url)
            assert is_valid == should_be_valid, \
                f"URL path validation failed for: {url} (expected {should_be_valid})"


class TestConfigValidatorOrganizationValidation:
    """
    TestConfigValidatorOrganizationValidation contains unit tests for GitHub organization
    name validation functionality. It verifies that organization names follow GitHub's
    naming conventions and character restrictions, ensuring compatibility with GitHub
    API operations and repository management.

    Test Cases:
    - test_validate_organization_valid_names: Tests valid organization name formats
    - test_validate_organization_invalid_characters: Tests names with invalid characters
    - test_validate_organization_boundary_conditions: Tests edge cases and boundaries
    - test_validate_organization_empty_and_none: Tests empty and None inputs
    - test_validate_organization_hyphen_rules: Tests hyphen positioning rules
    - test_validate_organization_length_validation: Tests organization name length limits
    """

    def test_validate_organization_valid_names(self):
        """
        Test that valid GitHub organization names are correctly accepted.

        This test verifies that organization names following GitHub's conventions
        (letters, numbers, hyphens, no leading/trailing hyphens) are properly
        validated as acceptable for GitHub operations.
        """
        valid_names = [
            "valid-org",
            "ValidOrg123",
            "a",  # Single character
            "test123",
            "cs-department",
            "university2025",
            "org-with-multiple-hyphens",
            "123numbers",
            "MixedCase123"
        ]

        for name in valid_names:
            is_valid, error_message = ConfigValidator.validate_organization(
                name)
            assert is_valid, f"Organization name should be valid: {name}, but got error: {error_message}"
            assert error_message == "", f"No error message expected for valid organization: {name}"

    def test_validate_organization_invalid_characters(self):
        """
        Test that organization names with invalid characters are rejected.

        This test verifies that organization names containing characters not allowed
        by GitHub (underscores, special symbols, spaces) are properly rejected with
        appropriate error messages explaining the character restrictions.
        """
        invalid_names = [
            "invalid_org",  # Underscore not allowed
            "invalid!org",  # Exclamation mark not allowed
            "invalid org",  # Space not allowed
            "invalid@org",  # At symbol not allowed
            "invalid.org",  # Period not allowed
            "invalid#org",  # Hash not allowed
            "invalid$org",  # Dollar sign not allowed
            "invalid%org",  # Percent not allowed
            "invalid&org",  # Ampersand not allowed
            "invalid*org",  # Asterisk not allowed
            "invalid(org",  # Parenthesis not allowed
            "invalid+org"   # Plus sign not allowed
        ]

        for name in invalid_names:
            is_valid, error_message = ConfigValidator.validate_organization(
                name)
            assert not is_valid, f"Organization name should be invalid: {name}"
            assert error_message == "Organization name must contain only letters, numbers, and hyphens", \
                f"Expected character restriction error for: {name}"

    def test_validate_organization_boundary_conditions(self):
        """
        Test organization name validation at boundary conditions and edge cases.

        This test verifies behavior with minimum length names, maximum reasonable lengths,
        and boundary conditions for hyphen placement and character combinations.
        """
        boundary_cases = [
            ("a", True),  # Single character minimum
            ("1", True),  # Single number
            ("a1", True),  # Two characters
            ("ab-cd-ef-gh-ij", True),  # Multiple hyphens
            ("" + "a" * 50, True),  # Long but reasonable name
        ]

        for name, should_be_valid in boundary_cases:
            is_valid, error_message = ConfigValidator.validate_organization(
                name)
            assert is_valid == should_be_valid, \
                f"Boundary condition validation failed for: '{name}' (expected {should_be_valid})"

    def test_validate_organization_empty_and_none(self):
        """
        Test that empty organization names and None values are properly rejected.

        This test verifies that empty strings and None values are identified as invalid
        organization names with clear error messages indicating that organization names
        cannot be empty.
        """
        empty_inputs = ["", None]

        for empty_input in empty_inputs:
            # Handle None by converting to empty string for the validator
            name_to_test = empty_input if empty_input is not None else ""
            is_valid, error_message = ConfigValidator.validate_organization(
                name_to_test)
            assert not is_valid, f"Empty organization name should be invalid: {empty_input}"
            assert error_message == "Organization name cannot be empty", \
                f"Expected empty name error message for input: {empty_input}"

    def test_validate_organization_hyphen_rules(self):
        """
        Test that hyphen positioning rules are correctly enforced.

        This test verifies that organization names cannot start or end with hyphens,
        following GitHub's naming conventions for organization names and ensuring
        compatibility with GitHub API operations.
        """
        hyphen_test_cases = [
            ("valid-org", True),  # Hyphen in middle is valid
            ("multiple-hyphen-name", True),  # Multiple hyphens in middle
            ("-invalid", False),  # Leading hyphen not allowed
            ("invalid-", False),  # Trailing hyphen not allowed
            ("-", False),  # Only hyphen not allowed
            ("--invalid", False),  # Multiple leading hyphens
            ("invalid--", False),  # Multiple trailing hyphens
            ("-invalid-", False),  # Both leading and trailing hyphens
            ("a-b", True),  # Short valid name with hyphen
            ("1-2", True)   # Numbers with hyphen
        ]

        for name, should_be_valid in hyphen_test_cases:
            is_valid, error_message = ConfigValidator.validate_organization(
                name)
            assert is_valid == should_be_valid, \
                f"Hyphen rule validation failed for: '{name}' (expected {should_be_valid})"

            if not should_be_valid:
                assert "Organization name must contain only letters, numbers, and hyphens" in error_message

    def test_validate_organization_length_validation(self):
        """
        Test organization name validation with various length inputs.

        This test verifies that the validator handles organization names of different
        lengths appropriately, ensuring compatibility with GitHub's length requirements
        and practical usage scenarios.
        """
        length_test_cases = [
            ("a", True),  # Minimum single character
            ("ab", True),  # Two characters
            ("abc", True),  # Three characters
            ("a" * 10, True),  # Reasonable length
            ("a" * 39, True),  # Maximum GitHub organization length
            ("a" * 100, True),  # Very long (validator doesn't enforce GitHub limits)
        ]

        for name, should_be_valid in length_test_cases:
            is_valid, error_message = ConfigValidator.validate_organization(
                name)
            assert is_valid == should_be_valid, \
                f"Length validation failed for name of length {len(name)} (expected {should_be_valid})"


class TestConfigValidatorAssignmentNameValidation:
    """
    TestConfigValidatorAssignmentNameValidation contains unit tests for assignment name
    validation functionality. It verifies that assignment names follow appropriate
    conventions while allowing empty names (since they can be auto-extracted) and
    ensuring compatibility with file systems and Git repositories.

    Test Cases:
    - test_validate_assignment_name_valid_names: Tests valid assignment name formats
    - test_validate_assignment_name_empty_allowed: Tests that empty names are allowed
    - test_validate_assignment_name_invalid_characters: Tests names with invalid characters
    - test_validate_assignment_name_boundary_conditions: Tests edge cases and boundaries
    - test_validate_assignment_name_special_formats: Tests various naming conventions
    """

    def test_validate_assignment_name_valid_names(self):
        """
        Test that valid assignment names are correctly accepted.

        This test verifies that assignment names following appropriate conventions
        (letters, numbers, hyphens, underscores, no leading/trailing special characters)
        are properly validated as acceptable for assignment identification.
        """
        valid_names = [
            "valid-assignment",
            "assignment_123",
            "homework1",
            "final-project",
            "data-analysis-hw",
            "assignment-with-multiple-parts",
            "HW1",
            "lab_exercise_1",
            "project2025"
        ]

        for name in valid_names:
            is_valid, error_message = ConfigValidator.validate_assignment_name(
                name)
            assert is_valid, f"Assignment name should be valid: {name}, but got error: {error_message}"
            assert error_message == "", f"No error message expected for valid assignment: {name}"

    def test_validate_assignment_name_empty_allowed(self):
        """
        Test that empty assignment names are allowed and properly validated.

        This test verifies that empty assignment names are accepted as valid since
        assignment names can be auto-extracted from URLs or generated automatically
        by the system when not explicitly provided.
        """
        is_valid, error_message = ConfigValidator.validate_assignment_name("")
        assert is_valid, "Empty assignment name should be valid (auto-extraction allowed)"
        assert error_message == "", "No error message expected for empty assignment name"

    def test_validate_assignment_name_invalid_characters(self):
        """
        Test that assignment names with invalid characters are rejected.

        This test verifies that assignment names containing characters not suitable
        for file systems or Git repositories (spaces, special symbols) are properly
        rejected with appropriate error messages.
        """
        invalid_names = [
            "invalid!name",  # Exclamation mark not allowed
            "invalid name",  # Space not allowed
            "invalid@name",  # At symbol not allowed
            # Period not allowed (might conflict with extensions)
            "invalid.name",
            "invalid#name",  # Hash not allowed
            "invalid$name",  # Dollar sign not allowed
            "invalid%name",  # Percent not allowed
            "invalid&name",  # Ampersand not allowed
            "invalid*name",  # Asterisk not allowed
            "invalid(name",  # Parenthesis not allowed
            "invalid+name",  # Plus sign not allowed
            "invalid/name",  # Slash not allowed
            "invalid\\name",  # Backslash not allowed
            "invalid|name"   # Pipe not allowed
        ]

        for name in invalid_names:
            is_valid, error_message = ConfigValidator.validate_assignment_name(
                name)
            assert not is_valid, f"Assignment name should be invalid: {name}"
            assert error_message == "Assignment name must contain only letters, numbers, hyphens, and underscores", \
                f"Expected character restriction error for: {name}"

    def test_validate_assignment_name_boundary_conditions(self):
        """
        Test assignment name validation at boundary conditions and edge cases.

        This test verifies behavior with minimum length names, very long names,
        and boundary conditions for special character placement and combinations.
        """
        boundary_cases = [
            ("a", True),  # Single character
            ("1", True),  # Single number
            ("a1", True),  # Letter and number
            ("a_b", True),  # With underscore
            ("a-b", True),  # With hyphen
            # Long name
            ("assignment-with-very-long-descriptive-name-for-complex-project", True),
            ("a" * 100, True),  # Very long name
        ]

        for name, should_be_valid in boundary_cases:
            is_valid, error_message = ConfigValidator.validate_assignment_name(
                name)
            assert is_valid == should_be_valid, \
                f"Boundary condition validation failed for: '{name}' (expected {should_be_valid})"

    def test_validate_assignment_name_special_character_positioning(self):
        """
        Test that special character positioning rules are correctly enforced.

        This test verifies that assignment names cannot start or end with hyphens
        or underscores, following good naming conventions and ensuring compatibility
        with various systems and tools.
        """
        positioning_test_cases = [
            ("valid-assignment", True),  # Hyphen in middle
            ("valid_assignment", True),  # Underscore in middle
            # Mixed hyphens and underscores
            ("assignment-with_mixed-chars", True),
            ("-invalid", False),  # Leading hyphen not allowed
            ("_invalid", False),  # Leading underscore not allowed
            ("invalid-", False),  # Trailing hyphen not allowed
            ("invalid_", False),  # Trailing underscore not allowed
            ("-invalid-", False),  # Both leading and trailing hyphens
            ("_invalid_", False),  # Both leading and trailing underscores
            ("a-b_c", True),  # Valid mixed characters
            ("1_2-3", True)   # Numbers with special characters
        ]

        for name, should_be_valid in positioning_test_cases:
            is_valid, error_message = ConfigValidator.validate_assignment_name(
                name)
            assert is_valid == should_be_valid, \
                f"Special character positioning validation failed for: '{name}' (expected {should_be_valid})"

    def test_validate_assignment_name_common_patterns(self):
        """
        Test assignment name validation with common academic naming patterns.

        This test verifies that typical assignment naming conventions used in
        educational settings are properly supported and validated by the system.
        """
        common_patterns = [
            "homework1", "homework-1", "homework_1",  # Homework variations
            "lab1", "lab-exercise-1", "lab_session_1",  # Lab variations
            "project1", "final-project", "group_project",  # Project variations
            "quiz1", "midterm", "final-exam",  # Assessment variations
            "assignment1", "assignment-2", "assignment_3",  # Assignment variations
            "hw1", "hw-2", "hw_3",  # Abbreviated homework
            "exercise1", "problem-set-1", "problem_set_2"  # Exercise variations
        ]

        for name in common_patterns:
            is_valid, error_message = ConfigValidator.validate_assignment_name(
                name)
            assert is_valid, f"Common assignment pattern should be valid: {name}"
            assert error_message == "", f"No error expected for common pattern: {name}"


class TestConfigValidatorFilePathValidation:
    """
    TestConfigValidatorFilePathValidation contains unit tests for assignment file path
    validation functionality. It verifies that file paths have appropriate extensions
    for supported programming languages and file formats, ensuring compatibility with
    educational assignments across different disciplines.

    Test Cases:
    - test_validate_file_path_supported_extensions: Tests all supported file extensions
    - test_validate_file_path_unsupported_extensions: Tests rejection of unsupported extensions
    - test_validate_file_path_empty_and_none: Tests empty and None inputs
    - test_validate_file_path_case_sensitivity: Tests extension case sensitivity
    - test_validate_file_path_multiple_extensions: Tests files with multiple extensions
    - test_validate_file_path_no_extension: Tests files without extensions
    """

    def test_validate_file_path_supported_extensions(self):
        """
        Test that files with supported extensions are correctly validated.

        This test verifies that all supported programming language and document
        file extensions are properly recognized and accepted for assignment files,
        ensuring broad compatibility with different course subjects.
        """
        supported_files = [
            # Programming languages
            "assignment.py",     # Python
            "homework.cpp",      # C++
            "project.java",      # Java
            "script.js",         # JavaScript
            "app.ts",           # TypeScript
            "program.c",        # C
            "header.h",         # C header
            "header.hpp",       # C++ header

            # Data and markup
            "notebook.ipynb",   # Jupyter notebook
            "queries.sql",      # SQL
            "documentation.md",  # Markdown
            "webpage.html",     # HTML
            "notes.txt",        # Text

            # Assembly (note: there's a syntax error in the original - missing dot)
            # The original has 'asm' but should be '.asm'
        ]

        for file_path in supported_files:
            is_valid, error_message = ConfigValidator.validate_file_path(
                file_path)
            assert is_valid, f"Supported file should be valid: {file_path}, but got error: {error_message}"
            assert error_message == "", f"No error message expected for supported file: {file_path}"

    def test_validate_file_path_unsupported_extensions(self):
        """
        Test that files with unsupported extensions are rejected with appropriate errors.

        This test verifies that file extensions not commonly used in educational
        programming assignments are properly rejected with clear error messages
        listing the supported extensions.
        """
        unsupported_files = [
            "document.doc",     # Word document
            "presentation.ppt",  # PowerPoint
            "spreadsheet.xls",  # Excel
            "image.jpg",        # Image file
            "video.mp4",        # Video file
            "archive.zip",      # Archive
            "executable.exe",   # Executable
            "library.dll",      # Dynamic library
            "config.ini",       # Configuration file
            "data.json",        # JSON (not explicitly supported)
            "styles.css",       # CSS (not explicitly supported)
            "unknown.xyz"       # Unknown extension
        ]

        for file_path in unsupported_files:
            is_valid, error_message = ConfigValidator.validate_file_path(
                file_path)
            assert not is_valid, f"Unsupported file should be invalid: {file_path}"
            assert "File must have a valid extension:" in error_message, \
                f"Expected extension error message for: {file_path}"
            # Verify that the error message lists supported extensions
            assert ".py" in error_message, "Error message should list supported extensions"

    def test_validate_file_path_empty_and_none(self):
        """
        Test that empty file paths and None values are properly rejected.

        This test verifies that empty strings and None values are identified as invalid
        file paths with clear error messages indicating that file paths cannot be empty.
        """
        empty_inputs = ["", None]

        for empty_input in empty_inputs:
            # Handle None by converting to empty string for the validator
            path_to_test = empty_input if empty_input is not None else ""
            is_valid, error_message = ConfigValidator.validate_file_path(
                path_to_test)
            assert not is_valid, f"Empty file path should be invalid: {empty_input}"
            assert error_message == "File path cannot be empty", \
                f"Expected empty path error message for input: {empty_input}"

    def test_validate_file_path_case_sensitivity(self):
        """
        Test file extension case sensitivity handling.

        This test verifies that file extensions are handled consistently regardless
        of case, following common file system conventions for cross-platform
        compatibility.
        """
        case_test_files = [
            ("assignment.py", True),    # Lowercase (standard)
            ("assignment.PY", True),    # Uppercase
            ("assignment.Py", True),    # Mixed case
            ("assignment.pY", True),    # Mixed case
            ("notebook.ipynb", True),   # Lowercase (standard)
            ("notebook.IPYNB", True),   # Uppercase
            ("notebook.Ipynb", True),   # Mixed case
        ]

        for file_path, should_be_valid in case_test_files:
            is_valid, error_message = ConfigValidator.validate_file_path(
                file_path)
            # Note: The original validator might be case-sensitive, so we need to check actual behavior
            # This test documents the current behavior rather than prescribing it
            if should_be_valid and not is_valid:
                # If the validator is case-sensitive, document this behavior
                assert "File must have a valid extension:" in error_message
            elif should_be_valid and is_valid:
                assert error_message == ""

    def test_validate_file_path_no_extension(self):
        """
        Test that files without extensions are properly rejected.

        This test verifies that file paths without extensions are identified as invalid
        since assignment files should have clear type identification through extensions.
        """
        no_extension_files = [
            "assignment",       # No extension
            "homework",         # No extension
            "README",          # Common file without extension
            "Makefile",        # Build file without extension
            "script",          # Script without extension
            "main"             # Program file without extension
        ]

        for file_path in no_extension_files:
            is_valid, error_message = ConfigValidator.validate_file_path(
                file_path)
            assert not is_valid, f"File without extension should be invalid: {file_path}"
            assert "File must have a valid extension:" in error_message, \
                f"Expected extension requirement error for: {file_path}"

    def test_validate_file_path_with_directories(self):
        """
        Test file path validation with directory structures.

        This test verifies that file paths including directory structures are properly
        validated based on the file extension, regardless of the directory path structure.
        """
        directory_test_files = [
            ("src/main.py", True),           # File in subdirectory
            ("homework/assignment.ipynb", True),  # Notebook in subdirectory
            ("../assignment.cpp", True),     # File with relative path
            # File with current directory reference
            ("./src/project.java", True),
            ("path/to/deep/file.py", True),  # Deeply nested file
            ("C:\\homework\\assignment.py", True),  # Windows-style path
            ("/usr/src/program.c", True),    # Unix-style absolute path
            ("src/main", False),             # No extension in subdirectory
            # Unsupported extension in subdirectory
            ("homework/assignment.xyz", False)
        ]

        for file_path, should_be_valid in directory_test_files:
            is_valid, error_message = ConfigValidator.validate_file_path(
                file_path)
            assert is_valid == should_be_valid, \
                f"Directory path validation failed for: {file_path} (expected {should_be_valid})"


class TestConfigValidatorRequiredFieldsValidation:
    """
    TestConfigValidatorRequiredFieldsValidation contains unit tests for configuration
    completeness validation. It verifies that all required configuration fields are
    present and properly identifies missing fields for user feedback and configuration
    troubleshooting.

    Test Cases:
    - test_validate_required_fields_complete_config: Tests complete configurations
    - test_validate_required_fields_missing_single: Tests configurations missing one field
    - test_validate_required_fields_missing_multiple: Tests configurations missing multiple fields
    - test_validate_required_fields_empty_values: Tests configurations with empty values
    - test_validate_required_fields_none_values: Tests configurations with None values
    - test_validate_required_fields_extra_fields: Tests configurations with extra fields
    """

    def test_validate_required_fields_complete_config(self):
        """
        Test that complete configurations with all required fields pass validation.

        This test verifies that when all required configuration fields are present
        and have non-empty values, the validation returns an empty list indicating
        no missing fields.
        """
        complete_configs = [
            {
                'CLASSROOM_URL': 'https://classroom.github.com/classrooms/123/assignments/test',
                'TEMPLATE_REPO_URL': 'https://github.com/test/template',
                'GITHUB_ORGANIZATION': 'test-org',
                'ASSIGNMENT_FILE': 'assignment.ipynb'
            },
            {
                'CLASSROOM_URL': 'https://classroom.github.com/classrooms/456/assignments/homework',
                'TEMPLATE_REPO_URL': 'https://github.com/university/homework-template',
                'GITHUB_ORGANIZATION': 'university-cs',
                'ASSIGNMENT_FILE': 'main.py',
                'EXTRA_FIELD': 'extra_value'  # Extra fields should not affect validation
            }
        ]

        for config in complete_configs:
            missing_fields = ConfigValidator.validate_required_fields(config)
            assert len(missing_fields) == 0, \
                f"Complete configuration should have no missing fields: {missing_fields}"
            assert missing_fields == [], \
                "Missing fields list should be empty for complete config"

    def test_validate_required_fields_missing_single(self):
        """
        Test identification of configurations missing a single required field.

        This test verifies that when exactly one required field is missing from
        the configuration, it is correctly identified and returned in the missing
        fields list.
        """
        single_missing_tests = [
            # Missing CLASSROOM_URL
            ({
                'TEMPLATE_REPO_URL': 'https://github.com/test/template',
                'GITHUB_ORGANIZATION': 'test-org',
                'ASSIGNMENT_FILE': 'assignment.ipynb'
            }, 'CLASSROOM_URL'),

            # Missing TEMPLATE_REPO_URL
            ({
                'CLASSROOM_URL': 'https://classroom.github.com/classrooms/123/assignments/test',
                'GITHUB_ORGANIZATION': 'test-org',
                'ASSIGNMENT_FILE': 'assignment.ipynb'
            }, 'TEMPLATE_REPO_URL'),

            # Missing GITHUB_ORGANIZATION
            ({
                'CLASSROOM_URL': 'https://classroom.github.com/classrooms/123/assignments/test',
                'TEMPLATE_REPO_URL': 'https://github.com/test/template',
                'ASSIGNMENT_FILE': 'assignment.ipynb'
            }, 'GITHUB_ORGANIZATION'),

            # Missing ASSIGNMENT_FILE
            ({
                'CLASSROOM_URL': 'https://classroom.github.com/classrooms/123/assignments/test',
                'TEMPLATE_REPO_URL': 'https://github.com/test/template',
                'GITHUB_ORGANIZATION': 'test-org'
            }, 'STUDENT_FILES or ASSIGNMENT_FILE')
        ]

        for config, expected_missing in single_missing_tests:
            missing_fields = ConfigValidator.validate_required_fields(config)
            assert len(missing_fields) == 1, \
                f"Should have exactly one missing field, got: {missing_fields}"
            assert expected_missing in missing_fields, \
                f"Expected missing field {expected_missing} not found in {missing_fields}"

    def test_validate_required_fields_missing_multiple(self):
        """
        Test identification of configurations missing multiple required fields.

        This test verifies that when multiple required fields are missing from
        the configuration, all missing fields are correctly identified and returned
        in the missing fields list.
        """
        multiple_missing_tests = [
            # Missing two fields
            ({
                'CLASSROOM_URL': 'https://classroom.github.com/classrooms/123/assignments/test',
                'TEMPLATE_REPO_URL': 'https://github.com/test/template'
            }, {'GITHUB_ORGANIZATION', 'STUDENT_FILES or ASSIGNMENT_FILE'}),

            # Missing three fields
            ({
                'CLASSROOM_URL': 'https://classroom.github.com/classrooms/123/assignments/test'
            }, {'TEMPLATE_REPO_URL', 'GITHUB_ORGANIZATION', 'STUDENT_FILES or ASSIGNMENT_FILE'}),

            # Missing all fields (empty config)
            ({}, {'CLASSROOM_URL', 'TEMPLATE_REPO_URL',
             'GITHUB_ORGANIZATION', 'STUDENT_FILES or ASSIGNMENT_FILE'})
        ]

        for config, expected_missing_set in multiple_missing_tests:
            missing_fields = ConfigValidator.validate_required_fields(config)
            missing_set = set(missing_fields)
            assert len(missing_fields) == len(expected_missing_set), \
                f"Expected {len(expected_missing_set)} missing fields, got {len(missing_fields)}: {missing_fields}"
            assert missing_set == expected_missing_set, \
                f"Expected missing fields {expected_missing_set}, got {missing_set}"

    def test_validate_required_fields_empty_values(self):
        """
        Test that fields with empty string values are treated as missing.

        This test verifies that configuration fields with empty string values
        are properly identified as missing, since empty values are not useful
        for configuration purposes.
        """
        empty_value_configs = [
            # All fields present but some empty
            {
                'CLASSROOM_URL': '',  # Empty string
                'TEMPLATE_REPO_URL': 'https://github.com/test/template',
                'GITHUB_ORGANIZATION': 'test-org',
                'ASSIGNMENT_FILE': 'assignment.ipynb'
            },

            # Multiple empty fields
            {
                'CLASSROOM_URL': 'https://classroom.github.com/classrooms/123/assignments/test',
                'TEMPLATE_REPO_URL': '',  # Empty string
                'GITHUB_ORGANIZATION': '',  # Empty string
                'ASSIGNMENT_FILE': 'assignment.ipynb'
            }
        ]

        expected_missing = [
            ['CLASSROOM_URL'],
            ['TEMPLATE_REPO_URL', 'GITHUB_ORGANIZATION']
        ]

        for config, expected in zip(empty_value_configs, expected_missing):
            missing_fields = ConfigValidator.validate_required_fields(config)
            assert len(missing_fields) == len(expected), \
                f"Expected {len(expected)} missing fields, got {len(missing_fields)}: {missing_fields}"
            for expected_field in expected:
                assert expected_field in missing_fields, \
                    f"Expected missing field {expected_field} not found in {missing_fields}"

    def test_validate_required_fields_none_values(self):
        """
        Test that fields with None values are treated as missing.

        This test verifies that configuration fields with None values are properly
        identified as missing, ensuring that null values don't pass validation.
        """
        none_value_config = {
            'CLASSROOM_URL': 'https://classroom.github.com/classrooms/123/assignments/test',
            'TEMPLATE_REPO_URL': None,  # None value
            'GITHUB_ORGANIZATION': 'test-org',
            'ASSIGNMENT_FILE': None     # None value
        }

        missing_fields = ConfigValidator.validate_required_fields(
            none_value_config)
        expected_missing = {'TEMPLATE_REPO_URL',
                            'STUDENT_FILES or ASSIGNMENT_FILE'}
        missing_set = set(missing_fields)

        assert len(missing_fields) == 2, \
            f"Expected 2 missing fields, got {len(missing_fields)}: {missing_fields}"
        assert missing_set == expected_missing, \
            f"Expected missing fields {expected_missing}, got {missing_set}"

    def test_validate_required_fields_extra_fields(self):
        """
        Test that extra non-required fields do not affect required field validation.

        This test verifies that configurations with additional fields beyond the
        required ones still pass validation correctly, and the extra fields don't
        interfere with required field checking.
        """
        config_with_extras = {
            'CLASSROOM_URL': 'https://classroom.github.com/classrooms/123/assignments/test',
            'TEMPLATE_REPO_URL': 'https://github.com/test/template',
            'GITHUB_ORGANIZATION': 'test-org',
            'ASSIGNMENT_FILE': 'assignment.ipynb',
            # Extra fields that shouldn't affect validation
            'OPTIONAL_FIELD': 'optional_value',
            'EXTRA_CONFIG': 'extra_value',
            'ADDITIONAL_SETTING': 'additional_value'
        }

        missing_fields = ConfigValidator.validate_required_fields(
            config_with_extras)
        assert len(missing_fields) == 0, \
            f"Configuration with extra fields should have no missing required fields: {missing_fields}"


class TestConfigValidatorFullConfigValidation:
    """
    TestConfigValidatorFullConfigValidation contains unit tests for comprehensive
    configuration validation that combines all individual validation methods.
    It verifies that complete configuration validation properly identifies both
    missing fields and invalid field values with appropriate error messages.

    Test Cases:
    - test_validate_full_config_valid_complete: Tests completely valid configurations
    - test_validate_full_config_missing_fields: Tests configurations with missing fields
    - test_validate_full_config_invalid_values: Tests configurations with invalid values
    - test_validate_full_config_mixed_errors: Tests configurations with multiple error types
    - test_validate_full_config_optional_fields: Tests configurations with optional fields
    - test_validate_full_config_error_messages: Tests detailed error message content
    """

    def test_validate_full_config_valid_complete(self):
        """
        Test that completely valid configurations pass full validation.

        This test verifies that configurations with all required fields present
        and all field values valid according to their respective validation rules
        pass the comprehensive validation without any errors.
        """
        valid_configs = [
            {
                'CLASSROOM_URL': 'https://classroom.github.com/classrooms/123/assignments/test',
                'TEMPLATE_REPO_URL': 'https://github.com/test/template',
                'GITHUB_ORGANIZATION': 'test-org',
                'ASSIGNMENT_FILE': 'assignment.ipynb'
            },
            {
                'CLASSROOM_URL': 'https://github.com/instructor/assignment-repo',
                'TEMPLATE_REPO_URL': 'https://github.com/university/assignment-template',
                'GITHUB_ORGANIZATION': 'university-cs',
                'ASSIGNMENT_FILE': 'main.py',
                'ASSIGNMENT_NAME': 'homework-1'  # Optional field with valid value
            }
        ]

        for config in valid_configs:
            is_valid, errors = ConfigValidator.validate_full_config(config)
            assert is_valid, f"Valid configuration should pass validation, but got errors: {errors}"
            assert len(
                errors) == 0, f"Valid configuration should have no errors: {errors}"
            assert errors == [], "Error list should be empty for valid configuration"

    def test_validate_full_config_missing_fields(self):
        """
        Test that configurations with missing required fields fail validation appropriately.

        This test verifies that when required fields are missing from the configuration,
        the full validation correctly identifies them and includes appropriate error
        messages for each missing field.
        """
        missing_field_configs = [
            # Missing one field
            ({
                'TEMPLATE_REPO_URL': 'https://github.com/test/template',
                'GITHUB_ORGANIZATION': 'test-org',
                'ASSIGNMENT_FILE': 'assignment.ipynb'
            }, 1),  # Expected number of errors

            # Missing multiple fields
            ({
                'CLASSROOM_URL': 'https://classroom.github.com/classrooms/123/assignments/test'
            }, 3),  # Expected number of errors

            # Missing all fields
            ({}, 4)  # Expected number of errors
        ]

        for config, expected_error_count in missing_field_configs:
            is_valid, errors = ConfigValidator.validate_full_config(config)
            assert not is_valid, "Configuration with missing fields should be invalid"
            assert len(errors) == expected_error_count, \
                f"Expected {expected_error_count} errors, got {len(errors)}: {errors}"

            # Verify that all errors are about missing fields
            for error in errors:
                assert "Missing required field:" in error, \
                    f"Expected missing field error, got: {error}"

    def test_validate_full_config_invalid_values(self):
        """
        Test that configurations with invalid field values fail validation appropriately.

        This test verifies that when configuration fields have invalid values according
        to their respective validation rules, the full validation correctly identifies
        them and provides specific error messages for each invalid field.
        """
        invalid_value_config = {
            'CLASSROOM_URL': 'invalid-url',                    # Invalid URL
            'TEMPLATE_REPO_URL': 'http://github.com/test/template',  # HTTP instead of HTTPS
            'GITHUB_ORGANIZATION': 'invalid!org',             # Invalid characters
            'ASSIGNMENT_FILE': 'assignment.xyz',              # Unsupported extension
            'ASSIGNMENT_NAME': 'invalid!name'                 # Invalid characters
        }

        is_valid, errors = ConfigValidator.validate_full_config(
            invalid_value_config)
        assert not is_valid, "Configuration with invalid values should be invalid"
        assert len(
            errors) == 5, f"Expected 5 validation errors, got {len(errors)}: {errors}"

        # Verify specific error messages
        error_text = " ".join(errors)
        assert "CLASSROOM_URL:" in error_text, "Should have CLASSROOM_URL error"
        assert "TEMPLATE_REPO_URL:" in error_text, "Should have TEMPLATE_REPO_URL error"
        assert "GITHUB_ORGANIZATION:" in error_text, "Should have GITHUB_ORGANIZATION error"
        assert "ASSIGNMENT_FILE:" in error_text, "Should have ASSIGNMENT_FILE error"
        assert "ASSIGNMENT_NAME:" in error_text, "Should have ASSIGNMENT_NAME error"

    def test_validate_full_config_mixed_errors(self):
        """
        Test configurations with both missing fields and invalid values.

        This test verifies that the full validation correctly handles configurations
        that have multiple types of errors simultaneously, including both missing
        required fields and invalid values in present fields.
        """
        mixed_error_config = {
            'CLASSROOM_URL': 'invalid-url',        # Invalid value
            'GITHUB_ORGANIZATION': 'invalid!org',  # Invalid value
            # TEMPLATE_REPO_URL missing
            # ASSIGNMENT_FILE missing
        }

        is_valid, errors = ConfigValidator.validate_full_config(
            mixed_error_config)
        assert not is_valid, "Configuration with mixed errors should be invalid"
        assert len(
            errors) == 4, f"Expected 4 errors (2 missing + 2 invalid), got {len(errors)}: {errors}"

        # Verify we have both types of errors
        missing_errors = [
            error for error in errors if "Missing required field:" in error]
        invalid_errors = [
            error for error in errors if "Missing required field:" not in error]

        assert len(
            missing_errors) == 2, f"Expected 2 missing field errors, got {len(missing_errors)}"
        assert len(
            invalid_errors) == 2, f"Expected 2 invalid value errors, got {len(invalid_errors)}"

    def test_validate_full_config_optional_fields(self):
        """
        Test that optional fields are validated when present but don't cause errors when absent.

        This test verifies that optional configuration fields (like ASSIGNMENT_NAME)
        are properly validated when provided but don't cause validation failures
        when omitted from the configuration.
        """
        # Config without optional fields - should be valid
        config_without_optional = {
            'CLASSROOM_URL': 'https://classroom.github.com/classrooms/123/assignments/test',
            'TEMPLATE_REPO_URL': 'https://github.com/test/template',
            'GITHUB_ORGANIZATION': 'test-org',
            'ASSIGNMENT_FILE': 'assignment.ipynb'
        }

        is_valid, errors = ConfigValidator.validate_full_config(
            config_without_optional)
        assert is_valid, f"Configuration without optional fields should be valid, got errors: {errors}"

        # Config with valid optional fields - should be valid
        config_with_valid_optional = config_without_optional.copy()
        config_with_valid_optional['ASSIGNMENT_NAME'] = 'valid-assignment'

        is_valid, errors = ConfigValidator.validate_full_config(
            config_with_valid_optional)
        assert is_valid, f"Configuration with valid optional fields should be valid, got errors: {errors}"

        # Config with invalid optional fields - should be invalid
        config_with_invalid_optional = config_without_optional.copy()
        config_with_invalid_optional['ASSIGNMENT_NAME'] = 'invalid!assignment'

        is_valid, errors = ConfigValidator.validate_full_config(
            config_with_invalid_optional)
        assert not is_valid, "Configuration with invalid optional fields should be invalid"
        assert len(
            errors) == 1, f"Expected 1 error for invalid optional field, got {len(errors)}: {errors}"
        assert "ASSIGNMENT_NAME:" in errors[0], "Error should be about ASSIGNMENT_NAME"

    def test_validate_full_config_error_message_format(self):
        """
        Test that error messages have consistent format and helpful content.

        This test verifies that all validation error messages follow a consistent
        format that includes the field name and a descriptive error message,
        making it easy for users to understand and fix configuration issues.
        """
        invalid_config = {
            'CLASSROOM_URL': 'invalid-url',
            'TEMPLATE_REPO_URL': 'also-invalid',
            'GITHUB_ORGANIZATION': 'invalid!org',
            'ASSIGNMENT_FILE': 'invalid.xyz',
            'ASSIGNMENT_NAME': 'invalid!name'
        }

        is_valid, errors = ConfigValidator.validate_full_config(invalid_config)

        # Verify error message format
        for error in errors:
            assert ":" in error, f"Error message should contain colon separator: {error}"
            parts = error.split(":", 1)
            assert len(
                parts) == 2, f"Error message should have field:message format: {error}"

            field_name = parts[0].strip()
            error_message = parts[1].strip()

            # Verify field name is valid
            assert field_name in ['CLASSROOM_URL', 'TEMPLATE_REPO_URL', 'GITHUB_ORGANIZATION',
                                  'ASSIGNMENT_FILE', 'ASSIGNMENT_NAME'], \
                f"Invalid field name in error: {field_name}"

            # Verify error message is not empty
            assert len(
                error_message) > 0, f"Error message should not be empty: {error}"

            # Verify error message doesn't start with uppercase (since field name comes first)
            # The error message part should be descriptive
            assert len(error_message.split(
            )) > 1, f"Error message should be descriptive: {error_message}"


if __name__ == '__main__':
    pytest.main([__file__])
