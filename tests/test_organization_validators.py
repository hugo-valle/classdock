"""
Tests for classdock.organizations.validators module.

Covers OrgNameValidator.validate(), .build(), and .suggest().
"""

import pytest

from classdock.organizations.validators import (
    VALID_SEMESTERS,
    OrgNameValidator,
    ValidationResult,
)


class TestValidate:
    """Tests for OrgNameValidator.validate()."""

    # --- valid names ---

    def test_valid_no_section(self):
        result = OrgNameValidator.validate("soc-cs3030-valle-su26")
        assert result.is_valid
        assert result.error is None
        assert result.program == "soc"
        assert result.course == "cs3030"
        assert result.section is None
        assert result.last_name == "valle"
        assert result.semester == "su"
        assert result.year == "26"

    def test_valid_with_section(self):
        result = OrgNameValidator.validate("soc-cs3550-2-smith-sp26")
        assert result.is_valid
        assert result.section == "2"
        assert result.last_name == "smith"
        assert result.semester == "sp"

    def test_valid_fall_semester(self):
        result = OrgNameValidator.validate("soc-web1400-valle-fa25")
        assert result.is_valid
        assert result.semester == "fa"
        assert result.course == "web1400"

    def test_valid_four_letter_program(self):
        result = OrgNameValidator.validate("cybr-cs2700-jones-fa25")
        assert result.is_valid
        assert result.program == "cybr"

    def test_valid_section_1(self):
        result = OrgNameValidator.validate("soc-cs2810-1-brown-sp26")
        assert result.is_valid
        assert result.section == "1"

    def test_valid_without_program(self):
        result = OrgNameValidator.validate("cs3030-valle-su26")
        assert result.is_valid
        assert result.program is None
        assert result.course == "cs3030"
        assert result.last_name == "valle"

    def test_valid_without_program_with_section(self):
        result = OrgNameValidator.validate("cs3550-2-smith-sp26")
        assert result.is_valid
        assert result.program is None
        assert result.section == "2"

    # --- invalid names ---

    def test_empty_string(self):
        result = OrgNameValidator.validate("")
        assert not result.is_valid
        assert "empty" in result.error.lower()

    def test_whitespace_only(self):
        result = OrgNameValidator.validate("   ")
        assert not result.is_valid

    def test_uppercase_org_name_invalid(self):
        result = OrgNameValidator.validate("SOC-CS3030-VALLE-SU26")
        assert not result.is_valid

    def test_invalid_semester(self):
        result = OrgNameValidator.validate("soc-cs3030-valle-wi26")
        assert not result.is_valid

    def test_uppercase_lastname_invalid(self):
        result = OrgNameValidator.validate("soc-cs3030-VALLE-su26")
        assert not result.is_valid

    def test_missing_year(self):
        result = OrgNameValidator.validate("soc-cs3030-valle-su")
        assert not result.is_valid

    def test_three_digit_course(self):
        result = OrgNameValidator.validate("soc-cs303-valle-su26")
        assert not result.is_valid

    def test_no_dashes(self):
        result = OrgNameValidator.validate("soccs3030vallesu26")
        assert not result.is_valid

    def test_extra_segment(self):
        result = OrgNameValidator.validate("soc-cs3030-valle-su26-extra")
        assert not result.is_valid

    def test_program_too_long(self):
        # 5-letter program prefix is invalid
        result = OrgNameValidator.validate("socia-cs3030-valle-su26")
        assert not result.is_valid

    def test_program_too_short(self):
        # 2-letter program prefix is invalid
        result = OrgNameValidator.validate("so-cs3030-valle-su26")
        assert not result.is_valid


class TestValidationResultProperties:
    """Tests for ValidationResult helper properties."""

    def test_semester_label_fall(self):
        r = OrgNameValidator.validate("soc-cs3030-valle-fa25")
        assert r.semester_label == "Fall"

    def test_semester_label_spring(self):
        r = OrgNameValidator.validate("soc-cs3030-valle-sp26")
        assert r.semester_label == "Spring"

    def test_semester_label_summer(self):
        r = OrgNameValidator.validate("soc-cs3030-valle-su26")
        assert r.semester_label == "Summer"

    def test_full_year(self):
        r = OrgNameValidator.validate("soc-cs3030-valle-fa25")
        assert r.full_year == "2025"

    def test_semester_label_none_when_invalid(self):
        r = ValidationResult(is_valid=False, error="bad")
        assert r.semester_label is None
        assert r.full_year is None


class TestBuild:
    """Tests for OrgNameValidator.build()."""

    def test_build_no_section(self):
        name = OrgNameValidator.build("cs3030", "valle", "su", "26", program="soc")
        assert name == "soc-cs3030-valle-su26"

    def test_build_with_section(self):
        name = OrgNameValidator.build(
            "cs3550", "smith", "sp", "26", program="soc", section="2"
        )
        assert name == "soc-cs3550-2-smith-sp26"

    def test_build_without_program(self):
        name = OrgNameValidator.build("cs3030", "valle", "su", "26")
        assert name == "cs3030-valle-su26"

    def test_build_normalizes_to_lowercase(self):
        name = OrgNameValidator.build("CS3030", "VALLE", "SU", "26", program="SOC")
        assert name == "soc-cs3030-valle-su26"

    def test_build_invalid_raises(self):
        with pytest.raises(ValueError, match="invalid"):
            # Single-letter last name is invalid (regex requires [a-z][a-z]+)
            OrgNameValidator.build("cs3030", "v", "su", "26")

    def test_valid_semesters_are_lowercase(self):
        assert VALID_SEMESTERS == {"fa", "sp", "su"}


class TestSuggest:
    """Tests for OrgNameValidator.suggest()."""

    def test_suggest_basic(self):
        name = OrgNameValidator.suggest("cs3030", "valle", "su", "26", program="soc")
        assert name == "soc-cs3030-valle-su26"

    def test_suggest_with_section(self):
        name = OrgNameValidator.suggest(
            "cs3550", "smith", "sp", "26", program="soc", section="2"
        )
        assert name == "soc-cs3550-2-smith-sp26"

    def test_suggest_without_program(self):
        name = OrgNameValidator.suggest("cs3030", "valle", "su", "26")
        assert name == "cs3030-valle-su26"

    def test_suggest_normalizes_to_lowercase(self):
        name = OrgNameValidator.suggest("CS3030", "VALLE", "SU", "26", program="SOC")
        assert name == "soc-cs3030-valle-su26"

    def test_suggest_invalid_semester_defaults_to_fa(self):
        name = OrgNameValidator.suggest(
            "cs3030", "valle", "winter", "26", program="soc"
        )
        assert "fa" in name

    def test_suggest_strips_special_chars(self):
        name = OrgNameValidator.suggest(
            "cs 3030", "val-le", "su", "26", program="s o c!"
        )
        assert "soc" in name
        assert "cs3030" in name
