"""
Roster manager for CRUD operations on students, assignments, and their relationships.

Provides high-level interface for roster management operations.
"""

from typing import Optional, List, Tuple
from datetime import datetime

from .models import Student, Assignment, StudentAssignment
from ..utils.database import DatabaseManager
from ..utils.logger import get_logger

logger = get_logger("roster_manager")


class RosterManager:
    """
    Handles roster CRUD operations for students and assignments.

    Provides methods for creating, reading, updating, and deleting students,
    assignments, and their relationships. All operations are organization-scoped
    to support multiple classrooms.
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize roster manager.

        Args:
            db_manager: DatabaseManager instance
        """
        self.db = db_manager

    # ==================== Student Operations ====================

    def add_student(self, student: Student) -> int:
        """
        Add a new student to the roster.

        Args:
            student: Student instance to add

        Returns:
            Student ID of newly created student

        Raises:
            sqlite3.IntegrityError: If student already exists (duplicate email+org)
            sqlite3.Error: If database operation fails
        """
        query = """
            INSERT INTO students (
                email, name, github_username, github_id, github_organization,
                enrolled_date, status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            student.email,
            student.name,
            student.github_username,
            student.github_id,
            student.github_organization,
            student.enrolled_date or datetime.now(),
            student.status,
            student.notes
        )

        student_id = self.db.execute_update(query, params)
        logger.info(f"Added student: {student.email} (ID: {student_id})")
        return student_id

    def update_student(self, student: Student) -> bool:
        """
        Update an existing student.

        Args:
            student: Student instance with updated data (must have id set)

        Returns:
            True if student was updated

        Raises:
            ValueError: If student.id is None
            sqlite3.Error: If database operation fails
        """
        if student.id is None:
            raise ValueError("Student ID is required for update")

        query = """
            UPDATE students
            SET email = ?, name = ?, github_username = ?, github_id = ?,
                github_organization = ?, enrolled_date = ?, status = ?,
                notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """

        params = (
            student.email,
            student.name,
            student.github_username,
            student.github_id,
            student.github_organization,
            student.enrolled_date,
            student.status,
            student.notes,
            student.id
        )

        rows_affected = self.db.execute_update(query, params)
        if rows_affected > 0:
            logger.info(f"Updated student: {student.email} (ID: {student.id})")
            return True
        return False

    def get_student_by_id(self, student_id: int) -> Optional[Student]:
        """
        Get student by ID.

        Args:
            student_id: Student ID

        Returns:
            Student instance or None if not found
        """
        query = "SELECT * FROM students WHERE id = ?"
        results = self.db.execute_query(query, (student_id,))

        if results:
            return Student.from_dict(results[0])
        return None

    def get_student_by_email(
        self,
        email: str,
        github_organization: str
    ) -> Optional[Student]:
        """
        Get student by email and organization (composite key).

        Args:
            email: Student email
            github_organization: GitHub organization

        Returns:
            Student instance or None if not found
        """
        query = """
            SELECT * FROM students
            WHERE email = ? AND github_organization = ?
        """
        results = self.db.execute_query(
            query,
            (email.lower().strip(), github_organization)
        )

        if results:
            return Student.from_dict(results[0])
        return None

    def get_student_by_github(
        self,
        github_username: str,
        github_organization: Optional[str] = None
    ) -> Optional[Student]:
        """
        Get student by GitHub username.

        Args:
            github_username: GitHub username
            github_organization: Optional organization filter

        Returns:
            Student instance or None if not found
        """
        if github_organization:
            query = """
                SELECT * FROM students
                WHERE github_username = ? AND github_organization = ?
            """
            params = (github_username, github_organization)
        else:
            query = "SELECT * FROM students WHERE github_username = ?"
            params = (github_username,)

        results = self.db.execute_query(query, params)

        if results:
            return Student.from_dict(results[0])
        return None

    def list_students(
        self,
        github_organization: Optional[str] = None,
        status: str = "active"
    ) -> List[Student]:
        """
        List students with optional filters.

        Args:
            github_organization: Filter by organization (None = all)
            status: Filter by status (default: active)

        Returns:
            List of Student instances
        """
        if github_organization:
            query = """
                SELECT * FROM students
                WHERE github_organization = ? AND status = ?
                ORDER BY name
            """
            params = (github_organization, status)
        else:
            query = """
                SELECT * FROM students
                WHERE status = ?
                ORDER BY github_organization, name
            """
            params = (status,)

        results = self.db.execute_query(query, params)
        return [Student.from_dict(row) for row in results]

    def delete_student(self, student_id: int) -> bool:
        """
        Delete a student (cascades to student_assignments).

        Args:
            student_id: Student ID to delete

        Returns:
            True if student was deleted

        Raises:
            sqlite3.Error: If database operation fails
        """
        query = "DELETE FROM students WHERE id = ?"
        rows_affected = self.db.execute_update(query, (student_id,))

        if rows_affected > 0:
            logger.info(f"Deleted student ID: {student_id}")
            return True
        return False

    def link_github_username(
        self,
        student_id: int,
        github_username: str,
        github_id: Optional[int] = None
    ) -> bool:
        """
        Link a GitHub username to a student.

        Args:
            student_id: Student ID
            github_username: GitHub username to link
            github_id: Optional GitHub user ID

        Returns:
            True if link was successful

        Raises:
            sqlite3.Error: If database operation fails
        """
        query = """
            UPDATE students
            SET github_username = ?, github_id = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        rows_affected = self.db.execute_update(
            query,
            (github_username, github_id, student_id)
        )

        if rows_affected > 0:
            logger.info(f"Linked student {student_id} to GitHub: {github_username}")
            return True
        return False

    # ==================== Assignment Operations ====================

    def add_assignment(self, assignment: Assignment) -> int:
        """
        Add a new assignment.

        Args:
            assignment: Assignment instance to add

        Returns:
            Assignment ID of newly created assignment

        Raises:
            sqlite3.IntegrityError: If assignment name already exists
            sqlite3.Error: If database operation fails
        """
        query = """
            INSERT INTO assignments (
                name, classroom_id, classroom_url, template_repo_url,
                github_organization, assignment_type, deadline,
                points_available, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            assignment.name,
            assignment.classroom_id,
            assignment.classroom_url,
            assignment.template_repo_url,
            assignment.github_organization,
            assignment.assignment_type,
            assignment.deadline,
            assignment.points_available,
            assignment.status
        )

        assignment_id = self.db.execute_update(query, params)
        logger.info(f"Added assignment: {assignment.name} (ID: {assignment_id})")
        return assignment_id

    def update_assignment(self, assignment: Assignment) -> bool:
        """
        Update an existing assignment.

        Args:
            assignment: Assignment instance with updated data (must have id set)

        Returns:
            True if assignment was updated

        Raises:
            ValueError: If assignment.id is None
            sqlite3.Error: If database operation fails
        """
        if assignment.id is None:
            raise ValueError("Assignment ID is required for update")

        query = """
            UPDATE assignments
            SET name = ?, classroom_id = ?, classroom_url = ?,
                template_repo_url = ?, github_organization = ?,
                assignment_type = ?, deadline = ?, points_available = ?,
                status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """

        params = (
            assignment.name,
            assignment.classroom_id,
            assignment.classroom_url,
            assignment.template_repo_url,
            assignment.github_organization,
            assignment.assignment_type,
            assignment.deadline,
            assignment.points_available,
            assignment.status,
            assignment.id
        )

        rows_affected = self.db.execute_update(query, params)
        if rows_affected > 0:
            logger.info(f"Updated assignment: {assignment.name} (ID: {assignment.id})")
            return True
        return False

    def get_assignment_by_id(self, assignment_id: int) -> Optional[Assignment]:
        """
        Get assignment by ID.

        Args:
            assignment_id: Assignment ID

        Returns:
            Assignment instance or None if not found
        """
        query = "SELECT * FROM assignments WHERE id = ?"
        results = self.db.execute_query(query, (assignment_id,))

        if results:
            return Assignment.from_dict(results[0])
        return None

    def get_assignment_by_name(self, name: str) -> Optional[Assignment]:
        """
        Get assignment by name.

        Args:
            name: Assignment name

        Returns:
            Assignment instance or None if not found
        """
        query = "SELECT * FROM assignments WHERE name = ?"
        results = self.db.execute_query(query, (name,))

        if results:
            return Assignment.from_dict(results[0])
        return None

    def list_assignments(
        self,
        github_organization: Optional[str] = None,
        status: str = "active"
    ) -> List[Assignment]:
        """
        List assignments with optional filters.

        Args:
            github_organization: Filter by organization (None = all)
            status: Filter by status (default: active)

        Returns:
            List of Assignment instances
        """
        if github_organization:
            query = """
                SELECT * FROM assignments
                WHERE github_organization = ? AND status = ?
                ORDER BY created_at DESC
            """
            params = (github_organization, status)
        else:
            query = """
                SELECT * FROM assignments
                WHERE status = ?
                ORDER BY github_organization, created_at DESC
            """
            params = (status,)

        results = self.db.execute_query(query, params)
        return [Assignment.from_dict(row) for row in results]

    def delete_assignment(self, assignment_id: int) -> bool:
        """
        Delete an assignment (cascades to student_assignments).

        Args:
            assignment_id: Assignment ID to delete

        Returns:
            True if assignment was deleted

        Raises:
            sqlite3.Error: If database operation fails
        """
        query = "DELETE FROM assignments WHERE id = ?"
        rows_affected = self.db.execute_update(query, (assignment_id,))

        if rows_affected > 0:
            logger.info(f"Deleted assignment ID: {assignment_id}")
            return True
        return False

    # ==================== Student-Assignment Linking ====================

    def link_student_to_assignment(
        self,
        student_id: int,
        assignment_id: int,
        repository_url: Optional[str] = None,
        repository_name: Optional[str] = None,
        acceptance_status: str = "pending"
    ) -> int:
        """
        Link a student to an assignment.

        Args:
            student_id: Student ID
            assignment_id: Assignment ID
            repository_url: Optional repository URL
            repository_name: Optional repository name
            acceptance_status: Acceptance status (default: pending)

        Returns:
            StudentAssignment ID

        Raises:
            sqlite3.IntegrityError: If link already exists
            sqlite3.Error: If database operation fails
        """
        query = """
            INSERT INTO student_assignments (
                student_id, assignment_id, repository_url, repository_name,
                acceptance_status
            ) VALUES (?, ?, ?, ?, ?)
        """

        params = (
            student_id,
            assignment_id,
            repository_url,
            repository_name,
            acceptance_status
        )

        link_id = self.db.execute_update(query, params)
        logger.info(
            f"Linked student {student_id} to assignment {assignment_id} "
            f"(Link ID: {link_id})"
        )
        return link_id

    def update_student_assignment(
        self,
        student_assignment: StudentAssignment
    ) -> bool:
        """
        Update a student-assignment link.

        Args:
            student_assignment: StudentAssignment instance with updated data

        Returns:
            True if link was updated

        Raises:
            ValueError: If student_assignment.id is None
            sqlite3.Error: If database operation fails
        """
        if student_assignment.id is None:
            raise ValueError("StudentAssignment ID is required for update")

        query = """
            UPDATE student_assignments
            SET repository_url = ?, repository_name = ?,
                acceptance_status = ?, accepted_at = ?, last_commit_at = ?,
                last_synced_at = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """

        params = (
            student_assignment.repository_url,
            student_assignment.repository_name,
            student_assignment.acceptance_status,
            student_assignment.accepted_at,
            student_assignment.last_commit_at,
            student_assignment.last_synced_at,
            student_assignment.notes,
            student_assignment.id
        )

        rows_affected = self.db.execute_update(query, params)
        if rows_affected > 0:
            logger.info(
                f"Updated student_assignment ID: {student_assignment.id}"
            )
            return True
        return False

    def get_student_assignment(
        self,
        student_id: int,
        assignment_id: int
    ) -> Optional[StudentAssignment]:
        """
        Get student-assignment link.

        Args:
            student_id: Student ID
            assignment_id: Assignment ID

        Returns:
            StudentAssignment instance or None if not found
        """
        query = """
            SELECT * FROM student_assignments
            WHERE student_id = ? AND assignment_id = ?
        """
        results = self.db.execute_query(query, (student_id, assignment_id))

        if results:
            return StudentAssignment.from_dict(results[0])
        return None

    def get_assignment_students(
        self,
        assignment_id: int
    ) -> List[Tuple[Student, StudentAssignment]]:
        """
        Get all students for an assignment with their assignment status.

        Args:
            assignment_id: Assignment ID

        Returns:
            List of (Student, StudentAssignment) tuples
        """
        query = """
            SELECT
                s.id as student_id,
                s.email,
                s.name,
                s.github_username,
                s.github_id,
                s.github_organization,
                s.enrolled_date,
                s.status as student_status,
                s.notes as student_notes,
                s.created_at as student_created_at,
                s.updated_at as student_updated_at,
                sa.id as sa_id,
                sa.student_id as sa_student_id,
                sa.assignment_id,
                sa.repository_url,
                sa.repository_name,
                sa.acceptance_status,
                sa.accepted_at,
                sa.last_commit_at,
                sa.last_synced_at,
                sa.notes as sa_notes,
                sa.created_at as sa_created_at,
                sa.updated_at as sa_updated_at
            FROM students s
            JOIN student_assignments sa ON s.id = sa.student_id
            WHERE sa.assignment_id = ?
            ORDER BY s.name
        """
        results = self.db.execute_query(query, (assignment_id,))

        student_assignments = []
        for row in results:
            # Split row data into student and student_assignment fields
            student_data = {
                'id': row['student_id'],
                'email': row['email'],
                'name': row['name'],
                'github_username': row['github_username'],
                'github_id': row['github_id'],
                'github_organization': row['github_organization'],
                'enrolled_date': row['enrolled_date'],
                'status': row['student_status'],
                'notes': row['student_notes'],
                'created_at': row['student_created_at'],
                'updated_at': row['student_updated_at']
            }

            sa_data = {
                'id': row['sa_id'],
                'student_id': row['sa_student_id'],
                'assignment_id': row['assignment_id'],
                'repository_url': row['repository_url'],
                'repository_name': row['repository_name'],
                'acceptance_status': row['acceptance_status'],
                'accepted_at': row['accepted_at'],
                'last_commit_at': row['last_commit_at'],
                'last_synced_at': row['last_synced_at'],
                'notes': row['sa_notes'],
                'created_at': row['sa_created_at'],
                'updated_at': row['sa_updated_at']
            }

            student = Student.from_dict(student_data)
            student_assignment = StudentAssignment.from_dict(sa_data)
            student_assignments.append((student, student_assignment))

        return student_assignments

    def get_student_assignments(
        self,
        student_id: int
    ) -> List[Tuple[Assignment, StudentAssignment]]:
        """
        Get all assignments for a student with their status.

        Args:
            student_id: Student ID

        Returns:
            List of (Assignment, StudentAssignment) tuples
        """
        query = """
            SELECT
                a.id as assignment_id,
                a.name,
                a.classroom_id,
                a.classroom_url,
                a.template_repo_url,
                a.github_organization,
                a.assignment_type,
                a.deadline,
                a.points_available,
                a.status as assignment_status,
                a.created_at as assignment_created_at,
                a.updated_at as assignment_updated_at,
                sa.id as sa_id,
                sa.student_id,
                sa.assignment_id as sa_assignment_id,
                sa.repository_url,
                sa.repository_name,
                sa.acceptance_status,
                sa.accepted_at,
                sa.last_commit_at,
                sa.last_synced_at,
                sa.notes as sa_notes,
                sa.created_at as sa_created_at,
                sa.updated_at as sa_updated_at
            FROM assignments a
            JOIN student_assignments sa ON a.id = sa.assignment_id
            WHERE sa.student_id = ?
            ORDER BY a.created_at DESC
        """
        results = self.db.execute_query(query, (student_id,))

        assignments = []
        for row in results:
            # Split row data into assignment and student_assignment fields
            assignment_data = {
                'id': row['assignment_id'],
                'name': row['name'],
                'classroom_id': row['classroom_id'],
                'classroom_url': row['classroom_url'],
                'template_repo_url': row['template_repo_url'],
                'github_organization': row['github_organization'],
                'assignment_type': row['assignment_type'],
                'deadline': row['deadline'],
                'points_available': row['points_available'],
                'status': row['assignment_status'],
                'created_at': row['assignment_created_at'],
                'updated_at': row['assignment_updated_at']
            }

            sa_data = {
                'id': row['sa_id'],
                'student_id': row['student_id'],
                'assignment_id': row['sa_assignment_id'],
                'repository_url': row['repository_url'],
                'repository_name': row['repository_name'],
                'acceptance_status': row['acceptance_status'],
                'accepted_at': row['accepted_at'],
                'last_commit_at': row['last_commit_at'],
                'last_synced_at': row['last_synced_at'],
                'notes': row['sa_notes'],
                'created_at': row['sa_created_at'],
                'updated_at': row['sa_updated_at']
            }

            assignment = Assignment.from_dict(assignment_data)
            student_assignment = StudentAssignment.from_dict(sa_data)
            assignments.append((assignment, student_assignment))

        return assignments

    def count_students(self, github_organization: Optional[str] = None) -> int:
        """
        Count total students.

        Args:
            github_organization: Optional organization filter

        Returns:
            Number of students
        """
        if github_organization:
            query = """
                SELECT COUNT(*) as count FROM students
                WHERE github_organization = ?
            """
            params = (github_organization,)
        else:
            query = "SELECT COUNT(*) as count FROM students"
            params = ()

        results = self.db.execute_query(query, params)
        return results[0]['count'] if results else 0

    def count_assignments(self, github_organization: Optional[str] = None) -> int:
        """
        Count total assignments.

        Args:
            github_organization: Optional organization filter

        Returns:
            Number of assignments
        """
        if github_organization:
            query = """
                SELECT COUNT(*) as count FROM assignments
                WHERE github_organization = ?
            """
            params = (github_organization,)
        else:
            query = "SELECT COUNT(*) as count FROM assignments"
            params = ()

        results = self.db.execute_query(query, params)
        return results[0]['count'] if results else 0
