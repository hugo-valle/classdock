"""
Tests for classdock.roster.manager module.

Tests RosterManager CRUD operations for students, assignments, and relationships.
"""

import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime

import pytest

from classdock.utils.database import DatabaseManager
from classdock.roster.manager import RosterManager
from classdock.roster.models import Student, Assignment, StudentAssignment


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
def sample_student():
    """Create a sample student."""
    return Student(
        email='test@example.com',
        name='Test User',
        github_organization='test-org',
        github_username='testuser'
    )


@pytest.fixture
def sample_assignment():
    """Create a sample assignment."""
    return Assignment(
        name='test-assignment',
        github_organization='test-org'
    )


class TestStudentOperations:
    """Tests for student CRUD operations."""

    def test_add_student(self, roster_manager, sample_student):
        """Test adding a new student."""
        student_id = roster_manager.add_student(sample_student)
        assert student_id > 0

        # Verify student was added
        retrieved = roster_manager.get_student_by_id(student_id)
        assert retrieved is not None
        assert retrieved.email == sample_student.email
        assert retrieved.name == sample_student.name

    def test_add_student_duplicate(self, roster_manager, sample_student):
        """Test adding duplicate student raises error."""
        roster_manager.add_student(sample_student)

        # Try to add again with same email and org
        with pytest.raises(sqlite3.IntegrityError):
            roster_manager.add_student(sample_student)

    def test_add_student_same_email_different_org(self, roster_manager):
        """Test adding same email to different organization."""
        student1 = Student(
            email='multi@example.com',
            name='Multi User',
            github_organization='org1'
        )
        student2 = Student(
            email='multi@example.com',
            name='Multi User',
            github_organization='org2'
        )

        id1 = roster_manager.add_student(student1)
        id2 = roster_manager.add_student(student2)

        assert id1 != id2
        assert roster_manager.count_students() == 2

    def test_update_student(self, roster_manager, sample_student):
        """Test updating a student."""
        student_id = roster_manager.add_student(sample_student)

        # Update student
        sample_student.id = student_id
        sample_student.name = 'Updated Name'
        sample_student.github_username = 'updateduser'

        assert roster_manager.update_student(sample_student)

        # Verify update
        retrieved = roster_manager.get_student_by_id(student_id)
        assert retrieved.name == 'Updated Name'
        assert retrieved.github_username == 'updateduser'

    def test_update_student_no_id(self, roster_manager, sample_student):
        """Test updating student without ID raises error."""
        with pytest.raises(ValueError, match="Student ID is required"):
            roster_manager.update_student(sample_student)

    def test_get_student_by_email(self, roster_manager, sample_student):
        """Test retrieving student by email and organization."""
        roster_manager.add_student(sample_student)

        retrieved = roster_manager.get_student_by_email(
            sample_student.email,
            sample_student.github_organization
        )
        assert retrieved is not None
        assert retrieved.email == sample_student.email

    def test_get_student_by_github(self, roster_manager, sample_student):
        """Test retrieving student by GitHub username."""
        roster_manager.add_student(sample_student)

        retrieved = roster_manager.get_student_by_github(
            sample_student.github_username,
            sample_student.github_organization
        )
        assert retrieved is not None
        assert retrieved.github_username == sample_student.github_username

    def test_list_students(self, roster_manager):
        """Test listing students."""
        # Add students to different organizations
        for i in range(3):
            student = Student(
                email=f'student{i}@example.com',
                name=f'Student {i}',
                github_organization='org1'
            )
            roster_manager.add_student(student)

        student = Student(
            email='other@example.com',
            name='Other Student',
            github_organization='org2'
        )
        roster_manager.add_student(student)

        # List all students
        all_students = roster_manager.list_students()
        assert len(all_students) == 4

        # List by organization
        org1_students = roster_manager.list_students(github_organization='org1')
        assert len(org1_students) == 3

    def test_delete_student(self, roster_manager, sample_student):
        """Test deleting a student."""
        student_id = roster_manager.add_student(sample_student)
        assert roster_manager.delete_student(student_id)

        # Verify deletion
        retrieved = roster_manager.get_student_by_id(student_id)
        assert retrieved is None

    def test_link_github_username(self, roster_manager, sample_student):
        """Test linking GitHub username to student."""
        sample_student.github_username = None
        student_id = roster_manager.add_student(sample_student)

        # Link GitHub username
        assert roster_manager.link_github_username(
            student_id,
            'newusername',
            github_id=12345
        )

        # Verify link
        retrieved = roster_manager.get_student_by_id(student_id)
        assert retrieved.github_username == 'newusername'
        assert retrieved.github_id == 12345


class TestAssignmentOperations:
    """Tests for assignment CRUD operations."""

    def test_add_assignment(self, roster_manager, sample_assignment):
        """Test adding a new assignment."""
        assignment_id = roster_manager.add_assignment(sample_assignment)
        assert assignment_id > 0

        # Verify assignment was added
        retrieved = roster_manager.get_assignment_by_id(assignment_id)
        assert retrieved is not None
        assert retrieved.name == sample_assignment.name

    def test_add_assignment_duplicate_name(self, roster_manager, sample_assignment):
        """Test adding duplicate assignment name raises error."""
        roster_manager.add_assignment(sample_assignment)

        # Try to add again with same name
        with pytest.raises(sqlite3.IntegrityError):
            roster_manager.add_assignment(sample_assignment)

    def test_update_assignment(self, roster_manager, sample_assignment):
        """Test updating an assignment."""
        assignment_id = roster_manager.add_assignment(sample_assignment)

        # Update assignment
        sample_assignment.id = assignment_id
        sample_assignment.points_available = 150
        sample_assignment.status = 'closed'

        assert roster_manager.update_assignment(sample_assignment)

        # Verify update
        retrieved = roster_manager.get_assignment_by_id(assignment_id)
        assert retrieved.points_available == 150
        assert retrieved.status == 'closed'

    def test_get_assignment_by_name(self, roster_manager, sample_assignment):
        """Test retrieving assignment by name."""
        roster_manager.add_assignment(sample_assignment)

        retrieved = roster_manager.get_assignment_by_name(sample_assignment.name)
        assert retrieved is not None
        assert retrieved.name == sample_assignment.name

    def test_list_assignments(self, roster_manager):
        """Test listing assignments."""
        # Add assignments to different organizations
        for i in range(2):
            assignment = Assignment(
                name=f'assignment-{i}',
                github_organization='org1'
            )
            roster_manager.add_assignment(assignment)

        assignment = Assignment(
            name='other-assignment',
            github_organization='org2'
        )
        roster_manager.add_assignment(assignment)

        # List all assignments
        all_assignments = roster_manager.list_assignments()
        assert len(all_assignments) == 3

        # List by organization
        org1_assignments = roster_manager.list_assignments(github_organization='org1')
        assert len(org1_assignments) == 2

    def test_delete_assignment(self, roster_manager, sample_assignment):
        """Test deleting an assignment."""
        assignment_id = roster_manager.add_assignment(sample_assignment)
        assert roster_manager.delete_assignment(assignment_id)

        # Verify deletion
        retrieved = roster_manager.get_assignment_by_id(assignment_id)
        assert retrieved is None


class TestStudentAssignmentLinking:
    """Tests for student-assignment relationships."""

    def test_link_student_to_assignment(self, roster_manager, sample_student, sample_assignment):
        """Test linking a student to an assignment."""
        student_id = roster_manager.add_student(sample_student)
        assignment_id = roster_manager.add_assignment(sample_assignment)

        link_id = roster_manager.link_student_to_assignment(
            student_id,
            assignment_id,
            repository_url='https://github.com/org/repo',
            acceptance_status='accepted'
        )
        assert link_id > 0

        # Verify link
        link = roster_manager.get_student_assignment(student_id, assignment_id)
        assert link is not None
        assert link.repository_url == 'https://github.com/org/repo'
        assert link.acceptance_status == 'accepted'

    def test_link_student_to_assignment_duplicate(
        self, roster_manager, sample_student, sample_assignment
    ):
        """Test duplicate link raises error."""
        student_id = roster_manager.add_student(sample_student)
        assignment_id = roster_manager.add_assignment(sample_assignment)

        roster_manager.link_student_to_assignment(student_id, assignment_id)

        # Try to link again
        with pytest.raises(sqlite3.IntegrityError):
            roster_manager.link_student_to_assignment(student_id, assignment_id)

    def test_update_student_assignment(
        self, roster_manager, sample_student, sample_assignment
    ):
        """Test updating student-assignment link."""
        student_id = roster_manager.add_student(sample_student)
        assignment_id = roster_manager.add_assignment(sample_assignment)
        link_id = roster_manager.link_student_to_assignment(student_id, assignment_id)

        # Update link
        link = roster_manager.get_student_assignment(student_id, assignment_id)
        link.repository_url = 'https://github.com/org/new-repo'
        link.acceptance_status = 'completed'
        link.accepted_at = datetime.now()

        assert roster_manager.update_student_assignment(link)

        # Verify update
        updated = roster_manager.get_student_assignment(student_id, assignment_id)
        assert updated.repository_url == 'https://github.com/org/new-repo'
        assert updated.acceptance_status == 'completed'
        assert updated.accepted_at is not None

    def test_get_assignment_students(
        self, roster_manager, sample_assignment
    ):
        """Test getting all students for an assignment."""
        assignment_id = roster_manager.add_assignment(sample_assignment)

        # Add multiple students to assignment
        for i in range(3):
            student = Student(
                email=f'student{i}@example.com',
                name=f'Student {i}',
                github_organization='test-org'
            )
            student_id = roster_manager.add_student(student)
            roster_manager.link_student_to_assignment(student_id, assignment_id)

        # Get all students for assignment
        students = roster_manager.get_assignment_students(assignment_id)
        assert len(students) == 3

        # Verify structure (list of tuples: Student, StudentAssignment)
        for student, student_assignment in students:
            assert isinstance(student, Student)
            assert isinstance(student_assignment, StudentAssignment)
            assert student_assignment.assignment_id == assignment_id

    def test_get_student_assignments(self, roster_manager, sample_student):
        """Test getting all assignments for a student."""
        student_id = roster_manager.add_student(sample_student)

        # Add student to multiple assignments
        for i in range(2):
            assignment = Assignment(
                name=f'assignment-{i}',
                github_organization='test-org'
            )
            assignment_id = roster_manager.add_assignment(assignment)
            roster_manager.link_student_to_assignment(student_id, assignment_id)

        # Get all assignments for student
        assignments = roster_manager.get_student_assignments(student_id)
        assert len(assignments) == 2

        # Verify structure
        for assignment, student_assignment in assignments:
            assert isinstance(assignment, Assignment)
            assert isinstance(student_assignment, StudentAssignment)
            assert student_assignment.student_id == student_id

    def test_cascade_delete_student(
        self, roster_manager, sample_student, sample_assignment
    ):
        """Test deleting student cascades to student_assignments."""
        student_id = roster_manager.add_student(sample_student)
        assignment_id = roster_manager.add_assignment(sample_assignment)
        roster_manager.link_student_to_assignment(student_id, assignment_id)

        # Delete student
        roster_manager.delete_student(student_id)

        # Verify link is also deleted
        link = roster_manager.get_student_assignment(student_id, assignment_id)
        assert link is None


class TestCountOperations:
    """Tests for count operations."""

    def test_count_students(self, roster_manager):
        """Test counting students."""
        # Add students to different organizations
        for i in range(3):
            student = Student(
                email=f'student{i}@example.com',
                name=f'Student {i}',
                github_organization='org1'
            )
            roster_manager.add_student(student)

        student = Student(
            email='other@example.com',
            name='Other',
            github_organization='org2'
        )
        roster_manager.add_student(student)

        # Count all
        assert roster_manager.count_students() == 4

        # Count by organization
        assert roster_manager.count_students(github_organization='org1') == 3
        assert roster_manager.count_students(github_organization='org2') == 1

    def test_count_assignments(self, roster_manager):
        """Test counting assignments."""
        for i in range(2):
            assignment = Assignment(
                name=f'assignment-{i}',
                github_organization='org1'
            )
            roster_manager.add_assignment(assignment)

        # Count all
        assert roster_manager.count_assignments() == 2

        # Count by organization
        assert roster_manager.count_assignments(github_organization='org1') == 2
        assert roster_manager.count_assignments(github_organization='org2') == 0
