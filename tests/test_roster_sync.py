"""
Tests for classdock.roster.sync module.

Tests repository synchronization with roster.
"""

import tempfile
from pathlib import Path
from datetime import datetime

import pytest

from classdock.utils.database import DatabaseManager
from classdock.roster.manager import RosterManager
from classdock.roster.sync import RosterSynchronizer
from classdock.roster.models import Student, Assignment


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
def synchronizer(roster_manager):
    """Create a RosterSynchronizer instance."""
    return RosterSynchronizer(roster_manager)


@pytest.fixture
def sample_students(roster_manager):
    """Create sample students in the roster."""
    students = []
    for i in range(3):
        student = Student(
            email=f'student{i}@example.com',
            name=f'Student {i}',
            github_username=f'student{i}',
            github_organization='test-org'
        )
        student_id = roster_manager.add_student(student)
        student.id = student_id
        students.append(student)
    return students


@pytest.fixture
def sample_repos():
    """Create sample discovered repository data."""
    return [
        ('python-basics-student0', 'https://github.com/test-org/python-basics-student0', 'student0'),
        ('python-basics-student1', 'https://github.com/test-org/python-basics-student1', 'student1'),
        ('python-basics-student2', 'https://github.com/test-org/python-basics-student2', 'student2'),
    ]


class TestRosterSynchronizer:
    """Tests for RosterSynchronizer class."""

    def test_sync_repositories_creates_assignment(self, synchronizer, roster_manager, sample_students, sample_repos):
        """Test syncing repositories creates assignment if it doesn't exist."""
        result = synchronizer.sync_repositories(
            'python-basics',
            'test-org',
            sample_repos
        )

        # Verify assignment was created
        assignment = roster_manager.get_assignment_by_name('python-basics')
        assert assignment is not None
        assert assignment.github_organization == 'test-org'

        # Verify all repos were linked
        assert result.total_repos == 3
        assert result.linked_count == 3
        assert result.unlinked_count == 0

    def test_sync_repositories_links_students(self, synchronizer, roster_manager, sample_students, sample_repos):
        """Test syncing repositories creates student-assignment links."""
        result = synchronizer.sync_repositories(
            'python-basics',
            'test-org',
            sample_repos
        )

        assignment = roster_manager.get_assignment_by_name('python-basics')

        # Verify links were created
        for student in sample_students:
            link = roster_manager.get_student_assignment(student.id, assignment.id)
            assert link is not None
            assert link.acceptance_status == 'accepted'
            assert link.repository_url is not None
            assert link.repository_name is not None

    def test_sync_repositories_updates_existing_links(self, synchronizer, roster_manager, sample_students, sample_repos):
        """Test syncing updates existing links instead of creating duplicates."""
        # First sync
        result1 = synchronizer.sync_repositories(
            'python-basics',
            'test-org',
            sample_repos
        )
        assert result1.linked_count == 3

        # Second sync (should update, not create new)
        result2 = synchronizer.sync_repositories(
            'python-basics',
            'test-org',
            sample_repos
        )
        assert result2.linked_count == 3

        # Verify no duplicates
        assignment = roster_manager.get_assignment_by_name('python-basics')
        students_with_repos = roster_manager.get_assignment_students(assignment.id)
        assert len(students_with_repos) == 3

    def test_sync_repositories_handles_unknown_students(self, synchronizer, roster_manager, sample_students):
        """Test syncing with repositories from unknown students."""
        repos_with_unknown = [
            ('python-basics-student0', 'https://github.com/test-org/python-basics-student0', 'student0'),
            ('python-basics-unknown', 'https://github.com/test-org/python-basics-unknown', 'unknown'),
        ]

        result = synchronizer.sync_repositories(
            'python-basics',
            'test-org',
            repos_with_unknown
        )

        assert result.total_repos == 2
        assert result.linked_count == 1  # Only student0
        assert result.unlinked_count == 1  # unknown
        assert len(result.unlinked_repos) == 1

    def test_sync_repositories_handles_missing_identifier(self, synchronizer, roster_manager, sample_students):
        """Test syncing with repositories missing student identifier."""
        repos_no_identifier = [
            ('python-basics-student0', 'https://github.com/test-org/python-basics-student0', 'student0'),
            ('python-basics', 'https://github.com/test-org/python-basics', None),
        ]

        result = synchronizer.sync_repositories(
            'python-basics',
            'test-org',
            repos_no_identifier
        )

        assert result.total_repos == 2
        assert result.linked_count == 1
        assert result.unlinked_count == 1
        assert len(result.errors) >= 1

    def test_sync_repositories_empty_list(self, synchronizer, roster_manager):
        """Test syncing with empty repository list."""
        result = synchronizer.sync_repositories(
            'python-basics',
            'test-org',
            []
        )

        assert result.total_repos == 0
        assert result.linked_count == 0
        assert result.unlinked_count == 0

    def test_detect_unlinked_students(self, synchronizer, roster_manager, sample_students):
        """Test detecting students without repositories."""
        # Create assignment
        assignment_id = roster_manager.add_assignment(
            Assignment(name='python-basics', github_organization='test-org')
        )

        # Link only first two students
        for i in range(2):
            roster_manager.link_student_to_assignment(
                sample_students[i].id,
                assignment_id,
                repository_url=f'https://github.com/test-org/repo{i}'
            )

        # Detect unlinked students
        unlinked = synchronizer.detect_unlinked_students('python-basics', 'test-org')

        assert len(unlinked) == 1
        assert unlinked[0].email == 'student2@example.com'

    def test_detect_unlinked_students_all_linked(self, synchronizer, roster_manager, sample_students):
        """Test detecting unlinked students when all are linked."""
        # Create assignment and link all students
        assignment_id = roster_manager.add_assignment(
            Assignment(name='python-basics', github_organization='test-org')
        )

        for student in sample_students:
            roster_manager.link_student_to_assignment(
                student.id,
                assignment_id,
                repository_url='https://github.com/test-org/repo'
            )

        unlinked = synchronizer.detect_unlinked_students('python-basics', 'test-org')
        assert len(unlinked) == 0

    def test_detect_unlinked_students_nonexistent_assignment(self, synchronizer, roster_manager, sample_students):
        """Test detecting unlinked students for nonexistent assignment."""
        unlinked = synchronizer.detect_unlinked_students('nonexistent', 'test-org')
        assert len(unlinked) == 0

    def test_detect_unlinked_repositories(self, synchronizer, roster_manager, sample_students, sample_repos):
        """Test detecting repositories without matching roster entries."""
        # Add unknown repo
        repos_with_unknown = sample_repos + [
            ('python-basics-unknown', 'https://github.com/test-org/python-basics-unknown', 'unknown')
        ]

        unlinked = synchronizer.detect_unlinked_repositories(
            'python-basics',
            'test-org',
            repos_with_unknown
        )

        assert len(unlinked) == 1
        assert unlinked[0] == ('python-basics-unknown', 'unknown')

    def test_detect_unlinked_repositories_all_linked(self, synchronizer, roster_manager, sample_students, sample_repos):
        """Test detecting unlinked repos when all have matching students."""
        unlinked = synchronizer.detect_unlinked_repositories(
            'python-basics',
            'test-org',
            sample_repos
        )

        assert len(unlinked) == 0

    def test_detect_unlinked_repositories_no_identifier(self, synchronizer, roster_manager):
        """Test detecting repos without student identifier."""
        repos_no_id = [
            ('python-basics', 'https://github.com/test-org/python-basics', None)
        ]

        unlinked = synchronizer.detect_unlinked_repositories(
            'python-basics',
            'test-org',
            repos_no_id
        )

        assert len(unlinked) == 1
        assert unlinked[0] == ('python-basics', 'unknown')

    def test_get_sync_statistics(self, synchronizer, roster_manager, sample_students):
        """Test getting synchronization statistics."""
        # Create assignment and link some students
        assignment_id = roster_manager.add_assignment(
            Assignment(name='python-basics', github_organization='test-org')
        )

        # Link 2 out of 3 students
        for i in range(2):
            roster_manager.link_student_to_assignment(
                sample_students[i].id,
                assignment_id
            )

        stats = synchronizer.get_sync_statistics('python-basics', 'test-org')

        assert stats['total_students'] == 3
        assert stats['students_with_repos'] == 2
        assert stats['students_without_repos'] == 1
        assert stats['acceptance_rate'] == pytest.approx(66.67, rel=0.1)

    def test_get_sync_statistics_no_assignment(self, synchronizer, roster_manager, sample_students):
        """Test getting statistics for nonexistent assignment."""
        stats = synchronizer.get_sync_statistics('nonexistent', 'test-org')

        assert stats['total_students'] == 0
        assert stats['students_with_repos'] == 0
        assert stats['students_without_repos'] == 0
        assert stats['acceptance_rate'] == 0.0

    def test_get_sync_statistics_no_students(self, synchronizer, roster_manager):
        """Test getting statistics with no students."""
        roster_manager.add_assignment(
            Assignment(name='python-basics', github_organization='test-org')
        )

        stats = synchronizer.get_sync_statistics('python-basics', 'test-org')

        assert stats['total_students'] == 0
        assert stats['acceptance_rate'] == 0.0

    def test_sync_repositories_sets_timestamps(self, synchronizer, roster_manager, sample_students, sample_repos):
        """Test that sync sets appropriate timestamps."""
        synchronizer.sync_repositories(
            'python-basics',
            'test-org',
            sample_repos
        )

        assignment = roster_manager.get_assignment_by_name('python-basics')
        link = roster_manager.get_student_assignment(sample_students[0].id, assignment.id)

        # Verify accepted_at is not set on first sync (would be set when actually accepted)
        # But last_synced_at should be updated
        assert link.last_synced_at is not None

    def test_sync_repositories_different_organizations(self, synchronizer, roster_manager):
        """Test syncing repositories for different organizations."""
        # Add students to different orgs
        student1 = Student(
            email='student@example.com',
            name='Student',
            github_username='studentuser',
            github_organization='org1'
        )
        student1_id = roster_manager.add_student(student1)

        student2 = Student(
            email='student@example.com',  # Same email
            name='Student',
            github_username='studentuser',  # Same GitHub username
            github_organization='org2'  # Different org
        )
        student2_id = roster_manager.add_student(student2)

        # Sync repos for org1
        repos_org1 = [('assignment-studentuser', 'https://github.com/org1/repo', 'studentuser')]
        result1 = synchronizer.sync_repositories('assignment', 'org1', repos_org1)
        assert result1.linked_count == 1

        # Sync repos for org2
        repos_org2 = [('assignment-studentuser', 'https://github.com/org2/repo', 'studentuser')]
        result2 = synchronizer.sync_repositories('assignment', 'org2', repos_org2)
        assert result2.linked_count == 1

        # Verify both are linked to correct organizations
        assignment1 = roster_manager.get_assignment_by_name('assignment')
        link1 = roster_manager.get_student_assignment(student1_id, assignment1.id)
        link2 = roster_manager.get_student_assignment(student2_id, assignment1.id)

        assert link1 is not None
        assert link2 is not None
        assert link1.repository_url != link2.repository_url

    def test_sync_from_classroom_api_not_implemented(self, synchronizer):
        """Test that classroom API sync returns warning."""
        result = synchronizer.sync_from_classroom_api(1, 1, None)

        assert result.sync_type == 'github_classroom'
        # Should return empty result since not implemented
        assert result.total_repos == 0
