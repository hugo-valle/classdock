"""
Test fixtures and sample data for testing.

This module contains test configuration files and sample data.
"""

# Sample test configuration content
TEST_CONFIG_CONTENT = '''# Test configuration for classdock
CLASSROOM_URL="https://classroom.github.com/classrooms/test/assignments/test"
TEMPLATE_REPO_URL="https://github.com/test/template"
GITHUB_ORGANIZATION="test-org"
CLASSROOM_REPO_URL="https://github.com/test-org/test-assignment"
SECRETS_JSON='{"TEST_SECRET": "test-value"}'
INSTRUCTOR_HANDLE="instructor"
ASSIGNMENT_NAME="test-assignment"
SEMESTER="fall2025"
'''

# Sample batch file content for cycle operations
SAMPLE_BATCH_CONTENT = '''# Sample batch operations
lab01 student1 test-org
lab01 student2 test-org
homework01 student3 test-org
'''

# Sample invalid configuration
INVALID_CONFIG_CONTENT = '''# Invalid configuration - missing required fields
TEMPLATE_REPO_URL="https://github.com/test/template"
# Missing CLASSROOM_URL and GITHUB_ORGANIZATION
'''
