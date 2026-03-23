"""
Tests for classdock.organizations.validators module.

Covers OrgNameValidator.validate(), .build(), and .suggest().
"""

import pytest

from classdock.organizations.validators import (
    OrgNameValidator,
    ValidationResult,
    VALID_SEMESTERS,
)


class TestValidate:
    """Tests for OrgNameValidator.validate()."""

    # --- valid names ---

    def test_valid_no_section(self):
        result = OrgNameValidator.validate("SOC-CS3030-Valle-SU26")
        assert result.is_valid
        assert result.error is None
        assert result.subject == "SOC"
        assert result.course == "CS3030"
        assert result.section is None
        assert result.lastname == "Valle"
        assert result.semester == "SU"
        assert result.year == "26"

    def test_valid_with_section(self):
        result = OrgNameValidator.validate("SOC-CS3550-2-Smith-SP26")
        assert result.is_valid
        assert result.section == "2"
        assert result.lastname == "Smith"
        assert result.semester == "SP"

    def test_valid_fall_semester(self):
        result = OrgNameValidator.validate("SOC-WEB1400-Valle-FA25")
        assert result.is_valid
        assert result.semester == "FA"
        assert result.course == "WEB1400"

    def test_valid_four_letter_subject(self):
        # CYBR is a 4-letter subject (CYBER has 5, which exceeds the 3-4 letter rule)
        result = OrgNameValidator.validate("CYBR-CS2700-Jones-FA25")
        assert result.is_valid
        assert result.subject == "CYBR"

    def test_valid_section_1(self):
        result = OrgNameValidator.validate("SOC-CS2810-1-Brown-SP26")
        assert result.is_valid
        assert result.section == "1"

    # --- invalid names ---

    def test_empty_string(self):
        result = OrgNameValidator.validate("")
        assert not result.is_valid
        assert "empty" in result.error.lower()

    def test_whitespace_only(self):
        result = OrgNameValidator.validate("   ")
        assert not result.is_valid

    def test_lowercase_subject(self):
        result = OrgNameValidator.validate("soc-CS3030-Valle-SU26")
        assert not result.is_valid

    def test_invalid_semester(self):
        result = OrgNameValidator.validate("SOC-CS3030-Valle-WI26")
        assert not result.is_valid

    def test_lowercase_lastname(self):
        result = OrgNameValidator.validate("SOC-CS3030-valle-SU26")
        assert not result.is_valid

    def test_missing_year(self):
        result = OrgNameValidator.validate("SOC-CS3030-Valle-SU")
        assert not result.is_valid

    def test_three_digit_course(self):
        result = OrgNameValidator.validate("SOC-CS303-Valle-SU26")
        assert not result.is_valid

    def test_no_dashes(self):
        result = OrgNameValidator.validate("SOCCS3030ValleSU26")
        assert not result.is_valid

    def test_extra_segment(self):
        # Too many parts that don't match pattern
        result = OrgNameValidator.validate("SOC-CS3030-Valle-SU26-EXTRA")
        assert not result.is_valid

    def test_subject_too_long(self):
        result = OrgNameValidator.validate("SOCIA-CS3030-Valle-SU26")
        assert not result.is_valid

    def test_subject_too_short(self):
        result = OrgNameValidator.validate("SO-CS3030-Valle-SU26")
        assert not result.is_valid


class TestValidationResultProperties:
    """Tests for ValidationResult helper properties."""

    def test_semester_label_fall(self):
        r = OrgNameValidator.validate("SOC-CS3030-Valle-FA25")
        assert r.semester_label == "Fall"

    def test_semester_label_spring(self):
        r = OrgNameValidator.validate("SOC-CS3030-Valle-SP26")
        assert r.semester_label == "Spring"

    def test_semester_label_summer(self):
        r = OrgNameValidator.validate("SOC-CS3030-Valle-SU26")
        assert r.semester_label == "Summer"

    def test_full_year(self):
        r = OrgNameValidator.validate("SOC-CS3030-Valle-FA25")
        assert r.full_year == "2025"

    def test_semester_label_none_when_invalid(self):
        r = ValidationResult(is_valid=False, error="bad")
        assert r.semester_label is None
        assert r.full_year is None


class TestBuild:
    """Tests for OrgNameValidator.build()."""

    def test_build_no_section(self):
        name = OrgNameValidator.build("SOC", "CS3030", "Valle", "SU", "26")
        assert name == "SOC-CS3030-Valle-SU26"

    def test_build_with_section(self):
        name = OrgNameValidator.build("SOC", "CS3550", "Smith", "SP", "26", section="2")
        assert name == "SOC-CS3550-2-Smith-SP26"

    def test_build_normalizes_case(self):
        name = OrgNameValidator.build("soc", "cs3030", "valle", "su", "26")
        assert name == "SOC-CS3030-Valle-SU26"

    def test_build_invalid_raises(self):
        with pytest.raises(ValueError, match="invalid"):
            OrgNameValidator.build("SO", "CS3030", "Valle", "SU", "26")  # subject too short


class TestSuggest:
    """Tests for OrgNameValidator.suggest()."""

    def test_suggest_basic(self):
        name = OrgNameValidator.suggest("SOC", "CS3030", "Valle", "SU", "26")
        assert name == "SOC-CS3030-Valle-SU26"

    def test_suggest_with_section(self):
        name = OrgNameValidator.suggest("SOC", "CS3550", "Smith", "SP", "26", section="2")
        assert name == "SOC-CS3550-2-Smith-SP26"

    def test_suggest_normalizes_lowercase_input(self):
        name = OrgNameValidator.suggest("soc", "cs3030", "valle", "su", "26")
        assert name == "SOC-CS3030-Valle-SU26"

    def test_suggest_invalid_semester_defaults_to_fa(self):
        name = OrgNameValidator.suggest("SOC", "CS3030", "Valle", "WINTER", "26")
        assert "FA" in name

    def test_suggest_strips_special_chars(self):
        name = OrgNameValidator.suggest("S O C!", "CS 3030", "Val-le", "SU", "26")
        assert "SOC" in name
        assert "CS3030" in name
