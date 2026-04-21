"""
Naming convention validation for GitHub organizations.

Enforces the ClassDock organization naming standard:
  [program?-][course][section?]-[last_name]-[semester][year]

Examples:
  soc-cs3030-valle-su26        (with program, single section)
  cs3030-valle-su26            (no program)
  soc-cs3550-2-smith-sp26      (program + section 2)
  soc-web1400-valle-fa25
"""

import re
from dataclasses import dataclass
from typing import Optional

# Regex: (program-)?COURSE(-SECTION)?-LAST_NAME-SEMESTERYEAR
_ORG_NAME_RE = re.compile(
    r"^(?:(?P<program>[a-z]{3,4})-)?"
    r"(?P<course>[a-z]+\d{4})"
    r"(?:-(?P<section>\d))?"
    r"-(?P<last_name>[a-z][a-z]+)"
    r"-(?P<semester>fa|sp|su)(?P<year>\d{2})$"
)

VALID_SEMESTERS = {"fa", "sp", "su"}
SEMESTER_LABELS = {"fa": "Fall", "sp": "Spring", "su": "Summer"}


@dataclass
class ValidationResult:
    """
    Result of an organization name validation.

    Attributes:
        is_valid: Whether the name passes all rules
        error: Human-readable error message (None if valid)
        program: Parsed optional PROGRAM component (e.g., soc, web)
        course: Parsed COURSE component (e.g., cs3030)
        section: Parsed optional SECTION digit (None if absent)
        last_name: Parsed LAST_NAME component (e.g., valle)
        semester: Parsed semester code (fa/sp/su)
        year: Parsed 2-digit year string
    """

    is_valid: bool
    error: Optional[str] = None
    program: Optional[str] = None
    course: Optional[str] = None
    section: Optional[str] = None
    last_name: Optional[str] = None
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

    FORMAT = "[program-][course][-section]-[last_name]-[semester][year]"
    EXAMPLE = "soc-cs3030-valle-su26"

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
                    f"    program   — optional 3–4 lowercase letters (e.g., soc, web, cs)\n"
                    f"    course    — lowercase letters + 4-digit number (e.g., cs3030)\n"
                    f"    section   — optional single digit (e.g., 2)\n"
                    f"    last_name — lowercase last name (e.g., valle)\n"
                    f"    semester  — fa, sp, or su followed by 2-digit year (e.g., su26)"
                ),
            )

        return ValidationResult(
            is_valid=True,
            program=m.group("program"),
            course=m.group("course"),
            section=m.group("section"),
            last_name=m.group("last_name"),
            semester=m.group("semester"),
            year=m.group("year"),
        )

    @staticmethod
    def build(
        course: str,
        last_name: str,
        semester: str,
        year: str,
        program: Optional[str] = None,
        section: Optional[str] = None,
    ) -> str:
        """
        Build a compliant organization name from individual components.

        Args:
            course: Course code with number (e.g., cs3030)
            last_name: Instructor's last name (e.g., valle)
            semester: Semester code — fa, sp, or su
            year: 2-digit year string (e.g., 26)
            program: Optional 3–4 letter program prefix (e.g., soc)
            section: Optional single-digit section number

        Returns:
            Formatted organization name string

        Raises:
            ValueError: If the resulting name fails validation
        """
        if program:
            program = re.sub(r"[^a-z]", "", program.lower().strip())[:4]
        course = course.lower().strip()
        last_name = last_name.lower().strip()
        semester = semester.lower().strip()
        year = year.strip()

        parts = []
        if program:
            parts.append(program)
        parts.append(course)
        if section:
            parts.append(str(section).strip())
        parts.append(last_name)
        parts.append(f"{semester}{year}")

        name = "-".join(parts)

        result = OrgNameValidator.validate(name)
        if not result.is_valid:
            raise ValueError(f"Built name '{name}' is invalid: {result.error}")

        return name

    @staticmethod
    def suggest(
        course_number: str,
        last_name: str,
        semester: str,
        year: str,
        program: Optional[str] = None,
        section: Optional[str] = None,
    ) -> str:
        """
        Suggest an organization name, normalizing inputs leniently.

        Useful for generating a preview before the user finalizes.
        Does not raise on invalid input — returns best-effort string.
        """
        if program:
            program = re.sub(r"[^a-zA-Z]", "", program).lower()[:4]
        course_number = re.sub(r"[^a-zA-Z0-9]", "", course_number).lower()
        last_name = re.sub(r"[^a-zA-Z]", "", last_name).lower()
        semester = semester.lower().strip()
        if semester not in VALID_SEMESTERS:
            semester = "fa"
        year = re.sub(r"[^0-9]", "", year)[-2:]

        parts = []
        if program:
            parts.append(program)
        parts.append(course_number)
        if section:
            sec = re.sub(r"[^0-9]", "", str(section))
            if sec:
                parts.append(sec)
        parts.append(last_name)
        parts.append(f"{semester}{year}")

        return "-".join(parts)
