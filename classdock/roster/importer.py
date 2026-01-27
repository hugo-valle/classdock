"""
CSV import/export functionality for ClassDock roster management.

Handles importing student rosters from CSV files (e.g., Google Forms exports)
and exporting roster data to CSV/JSON formats.
"""

import csv
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from .models import Student, ImportResult
from .manager import RosterManager
from ..utils.logger import get_logger

logger = get_logger("roster_importer")


class RosterImporter:
    """
    Handles CSV import and export operations for student rosters.

    Expected CSV format (Google Forms export):
    - email: Student email address
    - name: Student full name
    - github_username: GitHub username (optional)

    The GitHub organization is provided via parameter, not in CSV.
    """

    # Expected CSV columns
    REQUIRED_COLUMNS = {'email', 'name'}
    OPTIONAL_COLUMNS = {'github_username'}
    ALL_COLUMNS = REQUIRED_COLUMNS | OPTIONAL_COLUMNS

    def __init__(self, roster_manager: RosterManager):
        """
        Initialize roster importer.

        Args:
            roster_manager: RosterManager instance
        """
        self.roster = roster_manager

    def validate_csv_format(
        self,
        file_path: Path
    ) -> tuple[bool, str]:
        """
        Validate CSV file format and structure.

        Args:
            file_path: Path to CSV file

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not file_path.exists():
            return False, f"File not found: {file_path}"

        if not file_path.suffix.lower() == '.csv':
            return False, f"File must be a CSV file: {file_path}"

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                # Get actual columns from file
                if reader.fieldnames is None:
                    return False, "CSV file is empty or has no headers"

                actual_columns = set(reader.fieldnames)

                # Check for required columns
                missing_columns = self.REQUIRED_COLUMNS - actual_columns
                if missing_columns:
                    return False, (
                        f"Missing required columns: {', '.join(missing_columns)}. "
                        f"Expected: email, name"
                    )

                # Warn about unexpected columns (but don't fail)
                unexpected = actual_columns - self.ALL_COLUMNS
                if unexpected:
                    logger.warning(
                        f"Unexpected columns will be ignored: {', '.join(unexpected)}"
                    )

                # Check if file has at least one row
                try:
                    next(reader)
                except StopIteration:
                    return False, "CSV file has no data rows"

            return True, "CSV format valid"

        except csv.Error as e:
            return False, f"CSV parsing error: {e}"
        except Exception as e:
            return False, f"Error reading file: {e}"

    def import_from_csv(
        self,
        file_path: Path,
        github_organization: str,
        skip_duplicates: bool = True,
        validate_github: bool = False
    ) -> ImportResult:
        """
        Import students from CSV file.

        Args:
            file_path: Path to CSV file
            github_organization: GitHub organization (e.g., 'soc-cs3550-f25')
            skip_duplicates: If True, skip duplicate students; if False, raise error
            validate_github: If True, validate GitHub usernames (not implemented yet)

        Returns:
            ImportResult with import statistics and errors
        """
        result = ImportResult()

        # Validate CSV format
        is_valid, error_msg = self.validate_csv_format(file_path)
        if not is_valid:
            result.add_error(f"Validation failed: {error_msg}")
            return result

        logger.info(f"Importing students from {file_path} for org: {github_organization}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is 1)
                    result.total_rows += 1

                    try:
                        # Extract and validate fields
                        email = row.get('email', '').strip()
                        name = row.get('name', '').strip()
                        github_username = row.get('github_username', '').strip() or None

                        if not email or not name:
                            result.add_error(
                                f"Row {row_num}: Missing required fields (email or name)"
                            )
                            continue

                        # Check for duplicate
                        existing = self.roster.get_student_by_email(
                            email,
                            github_organization
                        )

                        if existing:
                            if skip_duplicates:
                                logger.debug(
                                    f"Row {row_num}: Skipping duplicate student: {email}"
                                )
                                result.add_skip()
                                continue
                            else:
                                result.add_error(
                                    f"Row {row_num}: Duplicate student: {email}"
                                )
                                continue

                        # Create student
                        student = Student(
                            email=email,
                            name=name,
                            github_username=github_username,
                            github_organization=github_organization,
                            enrolled_date=datetime.now()
                        )

                        # Add to database
                        student_id = self.roster.add_student(student)
                        student.id = student_id
                        result.add_success(student)

                        logger.debug(f"Row {row_num}: Imported {email} (ID: {student_id})")

                    except ValueError as e:
                        result.add_error(f"Row {row_num}: Validation error: {e}")
                    except Exception as e:
                        result.add_error(f"Row {row_num}: Unexpected error: {e}")

            logger.info(
                f"Import complete: {result.successful} successful, "
                f"{result.failed} failed, {result.skipped} skipped"
            )

        except Exception as e:
            result.add_error(f"Fatal error reading CSV: {e}")

        return result

    def export_to_csv(
        self,
        output_path: Path,
        github_organization: Optional[str] = None,
        students: Optional[List[Student]] = None
    ) -> bool:
        """
        Export students to CSV file.

        Args:
            output_path: Path for output CSV file
            github_organization: Filter by organization (if students not provided)
            students: Optional list of students to export (overrides organization filter)

        Returns:
            True if export successful

        Raises:
            ValueError: If neither students nor github_organization provided
        """
        if students is None:
            if github_organization is None:
                raise ValueError(
                    "Must provide either students list or github_organization"
                )
            students = self.roster.list_students(github_organization=github_organization)

        if not students:
            logger.warning("No students to export")
            return False

        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=['email', 'name', 'github_username', 'github_organization', 'status']
                )
                writer.writeheader()

                for student in students:
                    writer.writerow({
                        'email': student.email,
                        'name': student.name,
                        'github_username': student.github_username or '',
                        'github_organization': student.github_organization,
                        'status': student.status
                    })

            logger.info(f"Exported {len(students)} students to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Export failed: {e}")
            raise

    def export_to_json(
        self,
        output_path: Path,
        github_organization: Optional[str] = None,
        students: Optional[List[Student]] = None,
        pretty: bool = True
    ) -> bool:
        """
        Export students to JSON file.

        Args:
            output_path: Path for output JSON file
            github_organization: Filter by organization (if students not provided)
            students: Optional list of students to export
            pretty: If True, format JSON with indentation

        Returns:
            True if export successful

        Raises:
            ValueError: If neither students nor github_organization provided
        """
        if students is None:
            if github_organization is None:
                raise ValueError(
                    "Must provide either students list or github_organization"
                )
            students = self.roster.list_students(github_organization=github_organization)

        if not students:
            logger.warning("No students to export")
            return False

        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert students to dictionaries
            data = {
                'exported_at': datetime.now().isoformat(),
                'github_organization': github_organization,
                'total_students': len(students),
                'students': [student.to_dict() for student in students]
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                if pretty:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                else:
                    json.dump(data, f, ensure_ascii=False)

            logger.info(f"Exported {len(students)} students to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Export failed: {e}")
            raise

    def import_from_json(
        self,
        file_path: Path,
        github_organization: str,
        skip_duplicates: bool = True
    ) -> ImportResult:
        """
        Import students from JSON file.

        Args:
            file_path: Path to JSON file
            github_organization: GitHub organization for students
            skip_duplicates: If True, skip duplicate students

        Returns:
            ImportResult with import statistics

        Note:
            JSON format should match export_to_json output or be a simple list
            of student objects with email, name, and optionally github_username.
        """
        result = ImportResult()

        if not file_path.exists():
            result.add_error(f"File not found: {file_path}")
            return result

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Handle different JSON formats
            if isinstance(data, dict) and 'students' in data:
                # Format from export_to_json
                students_data = data['students']
            elif isinstance(data, list):
                # Simple list of student objects
                students_data = data
            else:
                result.add_error("Invalid JSON format")
                return result

            logger.info(
                f"Importing {len(students_data)} students from {file_path}"
            )

            for idx, student_data in enumerate(students_data):
                result.total_rows += 1

                try:
                    email = student_data.get('email', '').strip()
                    name = student_data.get('name', '').strip()
                    github_username = student_data.get('github_username')
                    if github_username:
                        github_username = github_username.strip() or None
                    else:
                        github_username = None

                    if not email or not name:
                        result.add_error(
                            f"Student {idx + 1}: Missing required fields"
                        )
                        continue

                    # Check for duplicate
                    existing = self.roster.get_student_by_email(
                        email,
                        github_organization
                    )

                    if existing:
                        if skip_duplicates:
                            result.add_skip()
                            continue
                        else:
                            result.add_error(
                                f"Student {idx + 1}: Duplicate: {email}"
                            )
                            continue

                    # Create student
                    student = Student(
                        email=email,
                        name=name,
                        github_username=github_username,
                        github_organization=github_organization,
                        enrolled_date=datetime.now()
                    )

                    student_id = self.roster.add_student(student)
                    student.id = student_id
                    result.add_success(student)

                except ValueError as e:
                    result.add_error(f"Student {idx + 1}: Validation error: {e}")
                except Exception as e:
                    result.add_error(f"Student {idx + 1}: Error: {e}")

            logger.info(
                f"Import complete: {result.successful} successful, "
                f"{result.failed} failed, {result.skipped} skipped"
            )

        except json.JSONDecodeError as e:
            result.add_error(f"JSON parsing error: {e}")
        except Exception as e:
            result.add_error(f"Fatal error: {e}")

        return result

    def generate_sample_csv(self, output_path: Path) -> bool:
        """
        Generate a sample CSV file showing the expected format.

        Args:
            output_path: Path for sample CSV file

        Returns:
            True if generation successful
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            sample_data = [
                {
                    'email': 'student1@example.com',
                    'name': 'John Doe',
                    'github_username': 'johndoe'
                },
                {
                    'email': 'student2@example.com',
                    'name': 'Jane Smith',
                    'github_username': 'janesmith'
                },
                {
                    'email': 'student3@example.com',
                    'name': 'Bob Johnson',
                    'github_username': ''  # Optional field
                }
            ]

            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=['email', 'name', 'github_username']
                )
                writer.writeheader()
                writer.writerows(sample_data)

            logger.info(f"Sample CSV generated at {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to generate sample CSV: {e}")
            return False
