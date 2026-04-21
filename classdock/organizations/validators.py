"""
Naming convention validation for GitHub organizations.

Enforces the ClassDock organization naming standard:
  [SUBJECT]-[COURSE][SECTION?]-[LASTNAME]-[SEMESTER][YEAR]

Examples:
  SOC-CS3030-Valle-SU26        (single section)
  SOC-CS3550-2-Smith-SP26      (section 2)
  SOC-WEB1400-Valle-FA25
"""

import re
from dataclasses import dataclass
from typing import Optional

# Regex: SUBJECT-COURSE(-SECTION)?-LASTNAME-SEMESTERYEAR
_ORG_NAME_RE = re.compile(
    r"^(?P<subject>[A-Z]{3,4})"
    r"-(?P<course>[A-Z]+\d{4})"
    r"(?:-(?P<section>\d))?"
    r"-(?P<lastname>[A-Z][a-z]+)"
    r"-(?P<semester>FA|SP|SU)(?P<year>\d{2})$"
)

VALID_SEMESTERS = {"FA", "SP", "SU"}
SEMESTER_LABELS = {"FA": "Fall", "SP": "Spring", "SU": "Summer"}


@dataclass
class ValidationResult:
    """
    Result of an organization name validation.

    Attributes:
        is_valid: Whether the name passes all rules
        error: Human-readable error message (None if valid)
        subject: Parsed SUBJECT component
        course: Parsed COURSE component (e.g., CS3030)
        section: Parsed optional SECTION digit (None if absent)
        lastname: Parsed LASTNAME component
        semester: Parsed semester code (FA/SP/SU)
        year: Parsed 2-digit year string
    """

    is_valid: bool
    error: Optional[str] = None
    subject: Optional[str] = None
    course: Optional[str] = None
    section: Optional[str] = None
    lastname: Optional[str] = None
    semester: Optional[str] = None
    year: Optional[str] = None

    @property
    def semester_label(self) -> Optional[str]:
        """Return the human-readable semester name (e.g., 'Fall')."""
        if self.semester:
            return SEMESTER_LABELS.get(self.semester)
        return None

    @property
    def full_year(self) -> Optional[str]:
        """Return 4-digit year string (e.g., '2026')."""
        if self.year:
            return f"20{self.year}"
        return None


class OrgNameValidator:
    """Validates and constructs GitHub organization names per ClassDock convention."""

    FORMAT = "[SUBJECT]-[COURSE][-SECTION]-[LASTNAME]-[SEMESTER][YEAR]"
    EXAMPLE = "SOC-CS3030-Valle-SU26"

    @staticmethod
    def validate(name: str) -> ValidationResult:
        """
        Validate an organization name against the ClassDock naming convention.

        Args:
            name: The organization name to validate

        Returns:
            ValidationResult with parsed components if valid
        """
        if not name or not name.strip():
            return ValidationResult(
                is_valid=False, error="Organization name cannot be empty."
            )

        name = name.strip()

        m = _ORG_NAME_RE.match(name)
        if not m:
            return ValidationResult(
                is_valid=False,
                error=(
                    f"'{name}' does not match the required format: {OrgNameValidator.FORMAT}\n"
                    f"  Example: {OrgNameValidator.EXAMPLE}\n"
                    f"  Rules:\n"
                    f"    SUBJECT  — 3–4 uppercase letters (e.g., SOC, WEB, CS)\n"
                    f"    COURSE   — uppercase letters + 4-digit number (e.g., CS3030)\n"
                    f"    SECTION  — optional single digit (e.g., 2)\n"
                    f"    LASTNAME — capitalized last name (e.g., Valle)\n"
                    f"    SEMESTER — FA, SP, or SU followed by 2-digit year (e.g., SU26)"
                ),
            )

        return ValidationResult(
            is_valid=True,
            subject=m.group("subject"),
            course=m.group("course"),
            section=m.group("section"),
            lastname=m.group("lastname"),
            semester=m.group("semester"),
            year=m.group("year"),
        )

    @staticmethod
    def build(
        subject: str,
        course: str,
        lastname: str,
        semester: str,
        year: str,
        section: Optional[str] = None,
    ) -> str:
        """
        Build a compliant organization name from individual components.

        Args:
            subject: 3–4 letter subject prefix (e.g., SOC)
            course: Course code with number (e.g., CS3030)
            lastname: Instructor's last name (e.g., Valle)
            semester: Semester code — FA, SP, or SU
            year: 2-digit year string (e.g., 26)
            section: Optional single-digit section number

        Returns:
            Formatted organization name string

        Raises:
            ValueError: If the resulting name fails validation
        """
        subject = subject.upper().strip()
        course = course.upper().strip()
        lastname = lastname.strip().capitalize()
        semester = semester.upper().strip()
        year = year.strip()

        parts = [subject, course]
        if section:
            parts.append(str(section).strip())
        parts.append(lastname)
        parts.append(f"{semester}{year}")

        name = "-".join(parts)

        result = OrgNameValidator.validate(name)
        if not result.is_valid:
            raise ValueError(f"Built name '{name}' is invalid: {result.error}")

        return name

    @staticmethod
    def suggest(
        subject: str,
        course_number: str,
        lastname: str,
        semester: str,
        year: str,
        section: Optional[str] = None,
    ) -> str:
        """
        Suggest an organization name, normalizing inputs leniently.

        Useful for generating a preview before the user finalizes.
        Does not raise on invalid input — returns best-effort string.
        """
        subject = re.sub(r"[^A-Za-z]", "", subject).upper()[:4]
        course_number = re.sub(r"[^A-Za-z0-9]", "", course_number).upper()
        lastname = re.sub(r"[^A-Za-z]", "", lastname).capitalize()
        semester = semester.upper().strip()
        if semester not in VALID_SEMESTERS:
            semester = "FA"
        year = re.sub(r"[^0-9]", "", year)[-2:]

        parts = [subject, course_number]
        if section:
            sec = re.sub(r"[^0-9]", "", str(section))
            if sec:
                parts.append(sec)
        parts.append(lastname)
        parts.append(f"{semester}{year}")

        return "-".join(parts)
