"""
Tests for classdock.roster.importer module.

Tests CSV import/export, JSON import/export, and validation.
"""

import tempfile
import json
from pathlib import Path

import pytest

from classdock.utils.database import DatabaseManager
from classdock.roster.manager import RosterManager
from classdock.roster.importer import RosterImporter
from classdock.roster.models import Student


@pytest.fixture
def db_manager():
    """Create a temporary database manager."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)

    db = DatabaseManager(db_path=db_path)
    db.initialize_database()

    yield db

    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def roster_manager(db_manager):
    """Create a RosterManager instance."""
    return RosterManager(db_manager)


@pytest.fixture
def importer(roster_manager):
    """Create a RosterImporter instance."""
    return RosterImporter(roster_manager)


@pytest.fixture
def valid_csv_path():
    """Path to valid test CSV file."""
    return Path(__file__).parent / "fixtures" / "roster" / "valid_students.csv"


@pytest.fixture
def no_github_csv_path():
    """Path to CSV with empty github_username fields."""
    return Path(__file__).parent / "fixtures" / "roster" / "students_no_github.csv"


@pytest.fixture
def invalid_csv_path():
    """Path to invalid CSV (missing required column)."""
    return Path(__file__).parent / "fixtures" / "roster" / "invalid_missing_column.csv"


class TestCSVValidation:
    """Tests for CSV validation."""

    def test_validate_csv_format_valid(self, importer, valid_csv_path):
        """Test validation of valid CSV file."""
        is_valid, message = importer.validate_csv_format(valid_csv_path)
        assert is_valid
        assert message == "CSV format valid"

    def test_validate_csv_format_missing_file(self, importer, tmp_path):
        """Test validation with missing file."""
        nonexistent = tmp_path / "nonexistent.csv"
        is_valid, message = importer.validate_csv_format(nonexistent)
        assert not is_valid
        assert "not found" in message

    def test_validate_csv_format_wrong_extension(self, importer, tmp_path):
        """Test validation with wrong file extension."""
        txt_file = tmp_path / "students.txt"
        txt_file.write_text("email,name\ntest@example.com,Test")
        is_valid, message = importer.validate_csv_format(txt_file)
        assert not is_valid
        assert "must be a CSV file" in message

    def test_validate_csv_format_missing_column(self, importer, invalid_csv_path):
        """Test validation with missing required column."""
        is_valid, message = importer.validate_csv_format(invalid_csv_path)
        assert not is_valid
        assert "Missing required columns" in message
        assert "name" in message

    def test_validate_csv_format_empty_file(self, importer, tmp_path):
        """Test validation with empty CSV file."""
        empty_csv = tmp_path / "empty.csv"
        empty_csv.write_text("")
        is_valid, message = importer.validate_csv_format(empty_csv)
        assert not is_valid

    def test_validate_csv_format_only_headers(self, importer, tmp_path):
        """Test validation with CSV containing only headers."""
        headers_only = tmp_path / "headers.csv"
        headers_only.write_text("email,name,github_username\n")
        is_valid, message = importer.validate_csv_format(headers_only)
        assert not is_valid
        assert "no data rows" in message


class TestCSVImport:
    """Tests for CSV import functionality."""

    def test_import_from_csv_success(self, importer, roster_manager, valid_csv_path):
        """Test successful import from valid CSV."""
        result = importer.import_from_csv(
            valid_csv_path,
            github_organization='test-org'
        )

        assert result.total_rows == 3
        assert result.successful == 3
        assert result.failed == 0
        assert result.skipped == 0
        assert len(result.imported_students) == 3

        # Verify students were added to database
        assert roster_manager.count_students(github_organization='test-org') == 3

        # Verify specific student
        student = roster_manager.get_student_by_email(
            'student1@example.com',
            'test-org'
        )
        assert student is not None
        assert student.name == 'John Doe'
        assert student.github_username == 'johndoe'

    def test_import_from_csv_no_github(self, importer, roster_manager, no_github_csv_path):
        """Test import with empty github_username fields."""
        result = importer.import_from_csv(
            no_github_csv_path,
            github_organization='test-org'
        )

        assert result.successful == 2
        assert result.failed == 0

        # Verify students imported without GitHub usernames
        student = roster_manager.get_student_by_email(
            'student4@example.com',
            'test-org'
        )
        assert student is not None
        assert student.github_username is None

    def test_import_from_csv_duplicates_skip(self, importer, roster_manager, valid_csv_path):
        """Test import with skip_duplicates=True."""
        # First import
        result1 = importer.import_from_csv(
            valid_csv_path,
            github_organization='test-org',
            skip_duplicates=True
        )
        assert result1.successful == 3

        # Second import (should skip all)
        result2 = importer.import_from_csv(
            valid_csv_path,
            github_organization='test-org',
            skip_duplicates=True
        )
        assert result2.successful == 0
        assert result2.skipped == 3

        # Verify no duplicate students in database
        assert roster_manager.count_students(github_organization='test-org') == 3

    def test_import_from_csv_duplicates_fail(self, importer, valid_csv_path):
        """Test import with skip_duplicates=False."""
        # First import
        result1 = importer.import_from_csv(
            valid_csv_path,
            github_organization='test-org',
            skip_duplicates=False
        )
        assert result1.successful == 3

        # Second import (should fail for duplicates)
        result2 = importer.import_from_csv(
            valid_csv_path,
            github_organization='test-org',
            skip_duplicates=False
        )
        assert result2.successful == 0
        assert result2.failed == 3
        assert "Duplicate" in result2.errors[0]

    def test_import_from_csv_different_orgs(self, importer, roster_manager, valid_csv_path):
        """Test importing same emails to different organizations."""
        # Import to org1
        result1 = importer.import_from_csv(
            valid_csv_path,
            github_organization='org1'
        )
        assert result1.successful == 3

        # Import to org2 (should succeed - different org)
        result2 = importer.import_from_csv(
            valid_csv_path,
            github_organization='org2'
        )
        assert result2.successful == 3

        # Verify students in both organizations
        assert roster_manager.count_students(github_organization='org1') == 3
        assert roster_manager.count_students(github_organization='org2') == 3
        assert roster_manager.count_students() == 6

    def test_import_from_csv_invalid_file(self, importer, invalid_csv_path):
        """Test import from invalid CSV."""
        result = importer.import_from_csv(
            invalid_csv_path,
            github_organization='test-org'
        )
        assert result.total_rows == 0
        assert result.successful == 0
        assert result.failed > 0
        assert "Validation failed" in result.errors[0]

    def test_import_from_csv_invalid_data(self, importer, tmp_path):
        """Test import with invalid row data."""
        invalid_data_csv = tmp_path / "invalid_data.csv"
        invalid_data_csv.write_text(
            "email,name,github_username\n"
            ",Missing Email,testuser\n"
            "test@example.com,,\n"  # Missing name
            "valid@example.com,Valid Name,validuser\n"
        )

        result = importer.import_from_csv(
            invalid_data_csv,
            github_organization='test-org'
        )

        assert result.total_rows == 3
        assert result.successful == 1  # Only the valid row
        assert result.failed == 2

    def test_import_google_forms_columns(self, importer, roster_manager, tmp_path):
        """Test import with Google Forms style column names."""
        google_forms_csv = tmp_path / "google_forms.csv"
        google_forms_csv.write_text(
            "Email Address,Enter your name,Enter your GitHub user name\n"
            "student1@example.com,Student One,student1\n"
            "student2@example.com,Student Two,student2\n"
        )

        result = importer.import_from_csv(
            google_forms_csv,
            github_organization='test-org'
        )

        assert result.successful == 2
        assert result.failed == 0

        # Verify students were imported correctly
        students = roster_manager.list_students(github_organization='test-org')
        assert len(students) == 2
        assert students[0].email == 'student1@example.com'
        assert students[0].name == 'Student One'
        assert students[0].github_username == 'student1'

    def test_import_mixed_case_columns(self, importer, roster_manager, tmp_path):
        """Test import with mixed case column names."""
        mixed_case_csv = tmp_path / "mixed_case.csv"
        mixed_case_csv.write_text(
            "EMAIL,Name,GitHub Username\n"
            "test1@example.com,Test User,testuser\n"
        )

        result = importer.import_from_csv(
            mixed_case_csv,
            github_organization='test-org'
        )

        assert result.successful == 1
        student = roster_manager.list_students(github_organization='test-org')[0]
        assert student.email == 'test1@example.com'
        assert student.name == 'Test User'
        assert student.github_username == 'testuser'


class TestCSVExport:
    """Tests for CSV export functionality."""

    def test_export_to_csv(self, importer, roster_manager, tmp_path):
        """Test exporting students to CSV."""
        # Add test students
        for i in range(3):
            student = Student(
                email=f'export{i}@example.com',
                name=f'Export Student {i}',
                github_username=f'export{i}',
                github_organization='test-org'
            )
            roster_manager.add_student(student)

        # Export to CSV
        output_path = tmp_path / "exported.csv"
        assert importer.export_to_csv(output_path, github_organization='test-org')

        # Verify file was created
        assert output_path.exists()

        # Verify CSV content
        import csv
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 3
        assert rows[0]['email'] == 'export0@example.com'
        assert rows[0]['name'] == 'Export Student 0'
        assert rows[0]['github_username'] == 'export0'

    def test_export_to_csv_no_students(self, importer, tmp_path):
        """Test export with no students."""
        output_path = tmp_path / "empty.csv"
        result = importer.export_to_csv(output_path, github_organization='empty-org')
        assert not result

    def test_export_to_csv_custom_list(self, importer, roster_manager, tmp_path):
        """Test export with custom student list."""
        # Add students to different orgs
        students_to_export = []
        for i in range(2):
            student = Student(
                email=f'custom{i}@example.com',
                name=f'Custom {i}',
                github_organization='org1'
            )
            student_id = roster_manager.add_student(student)
            student.id = student_id
            students_to_export.append(student)

        # Add student to different org (should not be exported)
        other_student = Student(
            email='other@example.com',
            name='Other',
            github_organization='org2'
        )
        roster_manager.add_student(other_student)

        # Export only custom list
        output_path = tmp_path / "custom.csv"
        assert importer.export_to_csv(output_path, students=students_to_export)

        # Verify only 2 students exported
        import csv
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 2


class TestJSONOperations:
    """Tests for JSON import/export."""

    def test_export_to_json(self, importer, roster_manager, tmp_path):
        """Test exporting students to JSON."""
        # Add test students
        for i in range(2):
            student = Student(
                email=f'json{i}@example.com',
                name=f'JSON Student {i}',
                github_organization='test-org'
            )
            roster_manager.add_student(student)

        # Export to JSON
        output_path = tmp_path / "exported.json"
        assert importer.export_to_json(output_path, github_organization='test-org')

        # Verify file was created and content
        assert output_path.exists()
        with open(output_path, 'r') as f:
            data = json.load(f)

        assert data['total_students'] == 2
        assert data['github_organization'] == 'test-org'
        assert len(data['students']) == 2
        assert data['students'][0]['email'] == 'json0@example.com'

    def test_import_from_json(self, importer, roster_manager, tmp_path):
        """Test importing students from JSON."""
        # Create JSON file
        json_path = tmp_path / "import.json"
        json_data = {
            'students': [
                {
                    'email': 'json1@example.com',
                    'name': 'JSON Import 1',
                    'github_username': 'json1'
                },
                {
                    'email': 'json2@example.com',
                    'name': 'JSON Import 2',
                    'github_username': None
                }
            ]
        }
        with open(json_path, 'w') as f:
            json.dump(json_data, f)

        # Import from JSON
        result = importer.import_from_json(
            json_path,
            github_organization='test-org'
        )

        assert result.successful == 2
        assert result.failed == 0
        assert roster_manager.count_students(github_organization='test-org') == 2

    def test_import_from_json_simple_list(self, importer, roster_manager, tmp_path):
        """Test importing from simple JSON list format."""
        json_path = tmp_path / "simple.json"
        json_data = [
            {'email': 'simple1@example.com', 'name': 'Simple 1', 'github_username': 's1'},
            {'email': 'simple2@example.com', 'name': 'Simple 2'}
        ]
        with open(json_path, 'w') as f:
            json.dump(json_data, f)

        result = importer.import_from_json(
            json_path,
            github_organization='test-org'
        )

        assert result.successful == 2


class TestSampleGeneration:
    """Tests for sample CSV generation."""

    def test_generate_sample_csv(self, importer, tmp_path):
        """Test generating sample CSV file."""
        output_path = tmp_path / "sample.csv"
        assert importer.generate_sample_csv(output_path)

        # Verify file exists and has content
        assert output_path.exists()

        import csv
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 3
        assert 'email' in rows[0]
        assert 'name' in rows[0]
        assert 'github_username' in rows[0]
