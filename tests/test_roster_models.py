"""
Tests for classdock.roster.models module.

Tests Student, Assignment, StudentAssignment, ImportResult, and SyncResult models.
"""

from datetime import datetime

import pytest

from classdock.roster.models import (
    Student, Assignment, StudentAssignment,
    ImportResult, SyncResult
)


class TestStudent:
    """Tests for Student model."""

    def test_create_student_minimal(self):
        """Test creating student with minimal required fields."""
        student = Student(
            email='test@example.com',
            name='Test User',
            github_organization='test-org'
        )

        assert student.email == 'test@example.com'
        assert student.name == 'Test User'
        assert student.github_organization == 'test-org'
        assert student.status == 'active'
        assert student.id is None
        assert student.github_username is None

    def test_create_student_full(self):
        """Test creating student with all fields."""
        now = datetime.now()
        student = Student(
            id=1,
            email='full@example.com',
            name='Full User',
            github_username='fulluser',
            github_id=12345,
            github_organization='test-org',
            enrolled_date=now,
            status='active',
            notes='Test notes',
            created_at=now,
            updated_at=now
        )

        assert student.id == 1
        assert student.email == 'full@example.com'
        assert student.github_username == 'fulluser'
        assert student.github_id == 12345
        assert student.notes == 'Test notes'

    def test_student_email_normalization(self):
        """Test email is normalized to lowercase."""
        student = Student(
            email='  Test@EXAMPLE.com  ',
            name='Test User',
            github_organization='test-org'
        )
        assert student.email == 'test@example.com'

    def test_student_required_fields(self):
        """Test student requires email, name, and organization."""
        with pytest.raises(ValueError, match="email, name, and github_organization are required"):
            Student(email='', name='Test', github_organization='org')

        with pytest.raises(ValueError):
            Student(email='test@example.com', name='', github_organization='org')

        with pytest.raises(ValueError):
            Student(email='test@example.com', name='Test', github_organization='')

    def test_student_status_validation(self):
        """Test student status validation."""
        # Valid status
        student = Student(
            email='test@example.com',
            name='Test',
            github_organization='org',
            status='inactive'
        )
        assert student.status == 'inactive'

        # Invalid status
        with pytest.raises(ValueError, match="status must be one of"):
            Student(
                email='test@example.com',
                name='Test',
                github_organization='org',
                status='invalid'
            )

    def test_student_from_dict(self):
        """Test creating student from dictionary."""
        data = {
            'id': 1,
            'email': 'dict@example.com',
            'name': 'Dict User',
            'github_username': 'dictuser',
            'github_id': 123,
            'github_organization': 'test-org',
            'enrolled_date': '2025-01-01T10:00:00',
            'status': 'active',
            'notes': None,
            'created_at': '2025-01-01T10:00:00',
            'updated_at': '2025-01-01T10:00:00'
        }

        student = Student.from_dict(data)
        assert student.id == 1
        assert student.email == 'dict@example.com'
        assert isinstance(student.enrolled_date, datetime)
        assert isinstance(student.created_at, datetime)

    def test_student_to_dict(self):
        """Test converting student to dictionary."""
        now = datetime.now()
        student = Student(
            id=1,
            email='test@example.com',
            name='Test User',
            github_username='testuser',
            github_id=123,
            github_organization='test-org',
            enrolled_date=now,
            status='active',
            notes='Test notes',
            created_at=now,
            updated_at=now
        )

        data = student.to_dict()
        assert data['id'] == 1
        assert data['email'] == 'test@example.com'
        assert data['github_username'] == 'testuser'
        assert data['enrolled_date'] == now.isoformat()


class TestAssignment:
    """Tests for Assignment model."""

    def test_create_assignment_minimal(self):
        """Test creating assignment with minimal fields."""
        assignment = Assignment(
            name='test-assignment',
            github_organization='test-org'
        )

        assert assignment.name == 'test-assignment'
        assert assignment.github_organization == 'test-org'
        assert assignment.assignment_type == 'individual'
        assert assignment.status == 'active'
        assert assignment.points_available == 100

    def test_create_assignment_full(self):
        """Test creating assignment with all fields."""
        now = datetime.now()
        deadline = datetime(2025, 12, 31)

        assignment = Assignment(
            id=1,
            name='full-assignment',
            classroom_id=12345,
            classroom_url='https://classroom.github.com/assignments/test',
            template_repo_url='https://github.com/org/template',
            github_organization='test-org',
            assignment_type='group',
            deadline=deadline,
            points_available=150,
            status='closed',
            created_at=now,
            updated_at=now
        )

        assert assignment.id == 1
        assert assignment.classroom_id == 12345
        assert assignment.assignment_type == 'group'
        assert assignment.deadline == deadline

    def test_assignment_required_fields(self):
        """Test assignment requires name and organization."""
        with pytest.raises(ValueError, match="name and github_organization are required"):
            Assignment(name='', github_organization='org')

        with pytest.raises(ValueError):
            Assignment(name='test', github_organization='')

    def test_assignment_type_validation(self):
        """Test assignment type validation."""
        # Valid type
        assignment = Assignment(
            name='test',
            github_organization='org',
            assignment_type='group'
        )
        assert assignment.assignment_type == 'group'

        # Invalid type
        with pytest.raises(ValueError, match="assignment_type must be one of"):
            Assignment(
                name='test',
                github_organization='org',
                assignment_type='invalid'
            )

    def test_assignment_status_validation(self):
        """Test assignment status validation."""
        # Valid statuses
        for status in ['active', 'closed', 'archived']:
            assignment = Assignment(
                name='test',
                github_organization='org',
                status=status
            )
            assert assignment.status == status

        # Invalid status
        with pytest.raises(ValueError, match="status must be one of"):
            Assignment(
                name='test',
                github_organization='org',
                status='invalid'
            )

    def test_assignment_from_dict(self):
        """Test creating assignment from dictionary."""
        data = {
            'id': 1,
            'name': 'dict-assignment',
            'classroom_id': 123,
            'classroom_url': None,
            'template_repo_url': None,
            'github_organization': 'test-org',
            'assignment_type': 'individual',
            'deadline': '2025-12-31T23:59:59',
            'points_available': 100,
            'status': 'active',
            'created_at': '2025-01-01T10:00:00',
            'updated_at': '2025-01-01T10:00:00'
        }

        assignment = Assignment.from_dict(data)
        assert assignment.id == 1
        assert assignment.name == 'dict-assignment'
        assert isinstance(assignment.deadline, datetime)

    def test_assignment_to_dict(self):
        """Test converting assignment to dictionary."""
        now = datetime.now()
        assignment = Assignment(
            id=1,
            name='test-assignment',
            classroom_id=123,
            github_organization='test-org',
            deadline=now,
            created_at=now,
            updated_at=now
        )

        data = assignment.to_dict()
        assert data['id'] == 1
        assert data['name'] == 'test-assignment'
        assert data['deadline'] == now.isoformat()


class TestStudentAssignment:
    """Tests for StudentAssignment model."""

    def test_create_student_assignment_minimal(self):
        """Test creating student assignment with minimal fields."""
        sa = StudentAssignment(
            student_id=1,
            assignment_id=1
        )

        assert sa.student_id == 1
        assert sa.assignment_id == 1
        assert sa.acceptance_status == 'pending'
        assert sa.repository_url is None

    def test_create_student_assignment_full(self):
        """Test creating student assignment with all fields."""
        now = datetime.now()
        sa = StudentAssignment(
            id=1,
            student_id=1,
            assignment_id=1,
            repository_url='https://github.com/org/repo',
            repository_name='test-assignment-user',
            acceptance_status='accepted',
            accepted_at=now,
            last_commit_at=now,
            last_synced_at=now,
            notes='Test notes',
            created_at=now,
            updated_at=now
        )

        assert sa.id == 1
        assert sa.repository_url == 'https://github.com/org/repo'
        assert sa.acceptance_status == 'accepted'
        assert sa.accepted_at == now

    def test_student_assignment_required_fields(self):
        """Test student assignment requires student_id and assignment_id."""
        with pytest.raises(ValueError, match="student_id and assignment_id are required"):
            StudentAssignment(student_id=0, assignment_id=1)

        with pytest.raises(ValueError):
            StudentAssignment(student_id=1, assignment_id=0)

    def test_student_assignment_status_validation(self):
        """Test acceptance status validation."""
        # Valid statuses
        for status in ['pending', 'accepted', 'completed', 'submitted']:
            sa = StudentAssignment(
                student_id=1,
                assignment_id=1,
                acceptance_status=status
            )
            assert sa.acceptance_status == status

        # Invalid status
        with pytest.raises(ValueError, match="acceptance_status must be one of"):
            StudentAssignment(
                student_id=1,
                assignment_id=1,
                acceptance_status='invalid'
            )

    def test_student_assignment_from_dict(self):
        """Test creating student assignment from dictionary."""
        data = {
            'id': 1,
            'student_id': 1,
            'assignment_id': 1,
            'repository_url': 'https://github.com/org/repo',
            'repository_name': 'test-repo',
            'acceptance_status': 'accepted',
            'accepted_at': '2025-01-01T10:00:00',
            'last_commit_at': None,
            'last_synced_at': '2025-01-01T10:00:00',
            'notes': None,
            'created_at': '2025-01-01T10:00:00',
            'updated_at': '2025-01-01T10:00:00'
        }

        sa = StudentAssignment.from_dict(data)
        assert sa.id == 1
        assert sa.repository_url == 'https://github.com/org/repo'
        assert isinstance(sa.accepted_at, datetime)

    def test_student_assignment_to_dict(self):
        """Test converting student assignment to dictionary."""
        now = datetime.now()
        sa = StudentAssignment(
            id=1,
            student_id=1,
            assignment_id=1,
            repository_url='https://github.com/org/repo',
            acceptance_status='accepted',
            accepted_at=now,
            created_at=now,
            updated_at=now
        )

        data = sa.to_dict()
        assert data['id'] == 1
        assert data['student_id'] == 1
        assert data['repository_url'] == 'https://github.com/org/repo'
        assert data['accepted_at'] == now.isoformat()


class TestImportResult:
    """Tests for ImportResult model."""

    def test_import_result_initialization(self):
        """Test import result initialization."""
        result = ImportResult()
        assert result.total_rows == 0
        assert result.successful == 0
        assert result.failed == 0
        assert result.skipped == 0
        assert result.errors == []
        assert result.imported_students == []

    def test_add_error(self):
        """Test adding errors to import result."""
        result = ImportResult(total_rows=3)
        result.add_error("Error 1")
        result.add_error("Error 2")

        assert result.failed == 2
        assert len(result.errors) == 2
        assert "Error 1" in result.errors

    def test_add_success(self):
        """Test adding successful imports."""
        result = ImportResult(total_rows=2)
        student = Student(
            email='test@example.com',
            name='Test',
            github_organization='org'
        )
        result.add_success(student)

        assert result.successful == 1
        assert len(result.imported_students) == 1
        assert result.imported_students[0] == student

    def test_add_skip(self):
        """Test incrementing skipped count."""
        result = ImportResult(total_rows=3)
        result.add_skip()
        result.add_skip()

        assert result.skipped == 2

    def test_success_rate(self):
        """Test success rate calculation."""
        result = ImportResult(total_rows=10)
        result.successful = 8
        result.failed = 1
        result.skipped = 1

        assert result.success_rate == 80.0

    def test_success_rate_zero_rows(self):
        """Test success rate with zero rows."""
        result = ImportResult(total_rows=0)
        assert result.success_rate == 0.0


class TestSyncResult:
    """Tests for SyncResult model."""

    def test_sync_result_initialization(self):
        """Test sync result initialization."""
        result = SyncResult(sync_type='repositories')
        assert result.sync_type == 'repositories'
        assert result.total_repos == 0
        assert result.linked_count == 0
        assert result.unlinked_count == 0
        assert result.errors == []
        assert result.unlinked_repos == []

    def test_add_error(self):
        """Test adding errors to sync result."""
        result = SyncResult(sync_type='repositories')
        result.add_error("Error 1")

        assert len(result.errors) == 1
        assert "Error 1" in result.errors

    def test_add_linked(self):
        """Test incrementing linked count."""
        result = SyncResult(sync_type='repositories', total_repos=5)
        result.add_linked()
        result.add_linked()

        assert result.linked_count == 2

    def test_add_unlinked(self):
        """Test adding unlinked repositories."""
        result = SyncResult(sync_type='repositories', total_repos=5)
        result.add_unlinked('https://github.com/org/repo1')
        result.add_unlinked('https://github.com/org/repo2')

        assert result.unlinked_count == 2
        assert len(result.unlinked_repos) == 2
        assert 'https://github.com/org/repo1' in result.unlinked_repos

    def test_success_rate(self):
        """Test success rate calculation."""
        result = SyncResult(sync_type='repositories', total_repos=10)
        result.linked_count = 7
        result.unlinked_count = 3

        assert result.success_rate == 70.0

    def test_success_rate_zero_repos(self):
        """Test success rate with zero repos."""
        result = SyncResult(sync_type='repositories', total_repos=0)
        assert result.success_rate == 0.0
