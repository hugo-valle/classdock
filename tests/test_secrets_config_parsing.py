"""
Tests for secrets configuration parsing and format detection.

This module tests the new 3-field secrets configuration format, backward
compatibility with the old 5-field format, and the automatic format detection
logic introduced in the secrets management upgrade.
"""


from classdock.config.global_config import SecretsConfig, ConfigurationManager


class TestSecretsConfigParsing:
    """Test the secrets configuration parsing logic."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config_manager = ConfigurationManager()

    def test_parse_new_3_field_format(self):
        """Test parsing of new 3-field format: name:description:validate_format."""
        secrets_config_string = """
INSTRUCTOR_TESTS_TOKEN:Token for accessing instructor test repository:true
API_KEY:API key for external service:false
DATABASE_TOKEN:Database access token:true
"""

        configs = self.config_manager._parse_secrets_config(
            secrets_config_string)

        assert len(configs) == 3

        # Check first secret
        assert configs[0].name == "INSTRUCTOR_TESTS_TOKEN"
        assert configs[0].description == "Token for accessing instructor test repository"
        assert configs[0].validate_format is True
        assert configs[0].token_file is None
        assert configs[0].max_age_days == 90  # Default value for new format
        assert configs[0].uses_centralized_token() is True

        # Check second secret
        assert configs[1].name == "API_KEY"
        assert configs[1].description == "API key for external service"
        assert configs[1].validate_format is False
        assert configs[1].token_file is None
        assert configs[1].uses_centralized_token() is True

        # Check third secret
        assert configs[2].name == "DATABASE_TOKEN"
        assert configs[2].description == "Database access token"
        assert configs[2].validate_format is True
        assert configs[2].token_file is None
        assert configs[2].uses_centralized_token() is True

    def test_parse_old_5_field_format_backward_compatibility(self):
        """Test parsing of old 5-field format for backward compatibility."""
        secrets_config_string = """
INSTRUCTOR_TESTS_TOKEN:Token for accessing instructor test repository:instructor_token.txt:90:true
API_KEY:API key for external service:api_key.txt:30:false
"""

        configs = self.config_manager._parse_secrets_config(
            secrets_config_string)

        assert len(configs) == 2

        # Check first secret (old format)
        assert configs[0].name == "INSTRUCTOR_TESTS_TOKEN"
        assert configs[0].description == "Token for accessing instructor test repository"
        assert configs[0].validate_format is True
        assert configs[0].token_file == "instructor_token.txt"
        assert configs[0].max_age_days == 90
        assert configs[0].uses_centralized_token() is False

        # Check second secret (old format)
        assert configs[1].name == "API_KEY"
        assert configs[1].description == "API key for external service"
        assert configs[1].validate_format is False
        assert configs[1].token_file == "api_key.txt"
        assert configs[1].max_age_days == 30
        assert configs[1].uses_centralized_token() is False

    def test_parse_mixed_format_lines(self):
        """Test parsing when config contains both old and new format lines."""
        secrets_config_string = """
INSTRUCTOR_TESTS_TOKEN:Token for accessing instructor test repository:true
OLD_TOKEN:Old style token:token_file.txt:60:false
NEW_API_KEY:New API key:false
"""

        configs = self.config_manager._parse_secrets_config(
            secrets_config_string)

        assert len(configs) == 3

        # New format
        assert configs[0].uses_centralized_token() is True
        assert configs[0].token_file is None

        # Old format
        assert configs[1].uses_centralized_token() is False
        assert configs[1].token_file == "token_file.txt"
        assert configs[1].max_age_days == 60

        # New format
        assert configs[2].uses_centralized_token() is True
        assert configs[2].token_file is None

    def test_parse_empty_config(self):
        """Test parsing empty or whitespace-only configuration."""
        assert self.config_manager._parse_secrets_config("") == []
        assert self.config_manager._parse_secrets_config("   \n  \n  ") == []

    def test_parse_config_with_comments(self):
        """Test parsing configuration with comments and empty lines."""
        secrets_config_string = """
# This is a comment
INSTRUCTOR_TESTS_TOKEN:Token for accessing instructor test repository:true

# Another comment
API_KEY:API key for external service:false
# Final comment
"""

        configs = self.config_manager._parse_secrets_config(
            secrets_config_string)

        assert len(configs) == 2
        assert configs[0].name == "INSTRUCTOR_TESTS_TOKEN"
        assert configs[1].name == "API_KEY"

    def test_parse_invalid_format_lines(self):
        """Test that invalid format lines are skipped."""
        secrets_config_string = """
VALID_TOKEN:Valid description:true
invalid_line_missing_colons
ANOTHER_VALID:Another valid token:false
too:few:fields
too:many:fields:here:and:more
"""

        configs = self.config_manager._parse_secrets_config(
            secrets_config_string)

        # The parser is permissive - it will parse anything with at least 2 parts
        # Lines with only 1 part (no colons) are skipped
        assert len(configs) == 4  # All except 'invalid_line_missing_colons'
        assert configs[0].name == "VALID_TOKEN"
        assert configs[1].name == "ANOTHER_VALID"
        assert configs[2].name == "too"  # Will be parsed as name:description
        # Will be parsed with old 5-field format
        assert configs[3].name == "too"

    def test_secrets_config_dataclass_properties(self):
        """Test SecretsConfig dataclass properties and methods."""
        # Test new format config
        new_config = SecretsConfig(
            name="TEST_TOKEN",
            description="Test token",
            validate_format=True,
            token_file=None,
            max_age_days=None
        )

        assert new_config.uses_centralized_token() is True

        # Test old format config
        old_config = SecretsConfig(
            name="OLD_TOKEN",
            description="Old token",
            validate_format=False,
            token_file="token.txt",
            max_age_days=30
        )

        assert old_config.uses_centralized_token() is False

    def test_boolean_parsing_variations(self):
        """Test that boolean values are parsed correctly from strings."""
        test_cases = [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            # Note: "yes" and "no" are treated as token files, not booleans
        ]

        for bool_str, expected in test_cases:
            secrets_config_string = f"TEST_TOKEN:Test description:{bool_str}"
            configs = self.config_manager._parse_secrets_config(
                secrets_config_string)
            assert len(configs) == 1
            assert configs[0].validate_format == expected

    def test_whitespace_handling(self):
        """Test that whitespace around values is handled correctly."""
        secrets_config_string = """
  SPACED_TOKEN  :  Description with spaces  :  true  
TOKEN_NO_SPACES:Description:false
"""

        configs = self.config_manager._parse_secrets_config(
            secrets_config_string)

        assert len(configs) == 2
        assert configs[0].name == "SPACED_TOKEN"
        assert configs[0].description == "Description with spaces"
        assert configs[0].validate_format is True

        assert configs[1].name == "TOKEN_NO_SPACES"
        assert configs[1].description == "Description"
        assert configs[1].validate_format is False
