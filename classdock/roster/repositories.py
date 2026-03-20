"""
Repository Pattern for roster data access.

Decouples service-layer code from the SQLite storage implementation by
providing a stable ``StudentRepository`` interface.  Two concrete
implementations are included:

- ``SqliteStudentRepository`` — production implementation backed by
  ``RosterManager`` / ``DatabaseManager``.
- ``InMemoryStudentRepository`` — test double that stores students in a
  plain dict; no database required.

Usage
-----
Production code receives the default repository automatically::

    service = RosterService()          # uses SqliteStudentRepository

Test code injects a fake::

    repo = InMemoryStudentRepository()
    service = RosterService(student_repository=repo)
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from .models import Student
from ..utils.logger import get_logger

logger = get_logger("roster.repositories")


# ========================================================================================
# Abstract interface
# ========================================================================================

class StudentRepository(ABC):
    """
    Abstract repository interface for student persistence.

    All methods operate in terms of domain objects (``Student``) rather
    than raw SQL rows.  Concrete implementations handle the translation to
    and from the storage medium.
    """

    @abstractmethod
    def add(self, student: Student) -> int:
        """Persist a new student and return its assigned ID."""

    @abstractmethod
    def update(self, student: Student) -> bool:
        """Persist changes to an existing student. Returns True on success."""

    @abstractmethod
    def find_by_id(self, student_id: int) -> Optional[Student]:
        """Return the student with *student_id*, or None if not found."""

    @abstractmethod
    def find_by_email(self, email: str, github_organization: str) -> Optional[Student]:
        """Return the student matching the (email, org) composite key."""

    @abstractmethod
    def find_by_github(
        self,
        github_username: str,
        github_organization: Optional[str] = None,
    ) -> Optional[Student]:
        """Return the student with the given GitHub username (optionally filtered by org)."""

    @abstractmethod
    def list_all(
        self,
        github_organization: Optional[str] = None,
        status: str = "active",
    ) -> List[Student]:
        """Return students matching the optional org / status filters."""

    @abstractmethod
    def delete(self, student_id: int) -> bool:
        """Remove the student with *student_id*. Returns True if deleted."""

    @abstractmethod
    def link_github_username(
        self,
        student_id: int,
        github_username: str,
        github_id: Optional[int] = None,
    ) -> bool:
        """Associate a GitHub username with an existing student."""

    @abstractmethod
    def count(self, github_organization: Optional[str] = None) -> int:
        """Return the number of students, optionally scoped to an org."""


# ========================================================================================
# SQLite-backed implementation
# ========================================================================================

class SqliteStudentRepository(StudentRepository):
    """
    Production repository backed by ``RosterManager`` (SQLite).

    This is a thin adapter; all logic lives in ``RosterManager``.
    """

    def __init__(self, manager) -> None:
        """
        Args:
            manager: A ``RosterManager`` instance.
        """
        self._manager = manager

    def add(self, student: Student) -> int:
        return self._manager.add_student(student)

    def update(self, student: Student) -> bool:
        return self._manager.update_student(student)

    def find_by_id(self, student_id: int) -> Optional[Student]:
        return self._manager.get_student_by_id(student_id)

    def find_by_email(self, email: str, github_organization: str) -> Optional[Student]:
        return self._manager.get_student_by_email(email, github_organization)

    def find_by_github(
        self,
        github_username: str,
        github_organization: Optional[str] = None,
    ) -> Optional[Student]:
        return self._manager.get_student_by_github(github_username, github_organization)

    def list_all(
        self,
        github_organization: Optional[str] = None,
        status: str = "active",
    ) -> List[Student]:
        return self._manager.list_students(
            github_organization=github_organization,
            status=status,
        )

    def delete(self, student_id: int) -> bool:
        return self._manager.delete_student(student_id)

    def link_github_username(
        self,
        student_id: int,
        github_username: str,
        github_id: Optional[int] = None,
    ) -> bool:
        return self._manager.link_github_username(student_id, github_username, github_id)

    def count(self, github_organization: Optional[str] = None) -> int:
        return self._manager.count_students(github_organization)


# ========================================================================================
# In-memory implementation (for tests)
# ========================================================================================

class InMemoryStudentRepository(StudentRepository):
    """
    Test double that stores students in memory — no SQLite required.

    IDs are assigned sequentially starting at 1.  All query methods
    match on normalized (lowercase) email values to mirror the SQLite
    behaviour.
    """

    def __init__(self) -> None:
        self._store: Dict[int, Student] = {}
        self._next_id: int = 1

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def add(self, student: Student) -> int:
        student_id = self._next_id
        self._next_id += 1
        # Store a copy with the assigned id
        stored = Student(
            email=student.email,
            name=student.name,
            github_organization=student.github_organization,
            id=student_id,
            github_username=student.github_username,
            github_id=student.github_id,
            enrolled_date=student.enrolled_date,
            status=student.status,
            notes=student.notes,
        )
        self._store[student_id] = stored
        logger.debug(f"InMemory: added student {student_id} ({student.email})")
        return student_id

    def update(self, student: Student) -> bool:
        if student.id is None or student.id not in self._store:
            return False
        self._store[student.id] = student
        return True

    def delete(self, student_id: int) -> bool:
        if student_id in self._store:
            del self._store[student_id]
            return True
        return False

    def link_github_username(
        self,
        student_id: int,
        github_username: str,
        github_id: Optional[int] = None,
    ) -> bool:
        if student_id not in self._store:
            return False
        s = self._store[student_id]
        self._store[student_id] = Student(
            email=s.email,
            name=s.name,
            github_organization=s.github_organization,
            id=s.id,
            github_username=github_username,
            github_id=github_id,
            enrolled_date=s.enrolled_date,
            status=s.status,
            notes=s.notes,
        )
        return True

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def find_by_id(self, student_id: int) -> Optional[Student]:
        return self._store.get(student_id)

    def find_by_email(self, email: str, github_organization: str) -> Optional[Student]:
        email_norm = email.lower().strip()
        for s in self._store.values():
            if s.email == email_norm and s.github_organization == github_organization:
                return s
        return None

    def find_by_github(
        self,
        github_username: str,
        github_organization: Optional[str] = None,
    ) -> Optional[Student]:
        for s in self._store.values():
            if s.github_username == github_username:
                if github_organization is None or s.github_organization == github_organization:
                    return s
        return None

    def list_all(
        self,
        github_organization: Optional[str] = None,
        status: str = "active",
    ) -> List[Student]:
        results = [
            s for s in self._store.values()
            if s.status == status
            and (github_organization is None or s.github_organization == github_organization)
        ]
        return sorted(results, key=lambda s: s.name)

    def count(self, github_organization: Optional[str] = None) -> int:
        if github_organization is None:
            return len(self._store)
        return sum(
            1 for s in self._store.values()
            if s.github_organization == github_organization
        )
