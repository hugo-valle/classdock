"""
Data models for ClassDock roster management.

Defines dataclasses for students, assignments, and their relationships.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass
class Student:
    """
    Represents a student in the roster.

    Attributes:
        email: Student's email address
        name: Student's full name
        github_organization: GitHub organization (e.g., 'soc-cs3550-f25')
        id: Database primary key (None for new students)
        github_username: GitHub username (optional)
        github_id: GitHub user ID (optional)
        enrolled_date: Date student was enrolled
        status: Student status (active, inactive, dropped)
        notes: Additional notes about the student
        created_at: Record creation timestamp
        updated_at: Record last update timestamp
    """
    email: str
    name: str
    github_organization: str
    id: Optional[int] = None
    github_username: Optional[str] = None
    github_id: Optional[int] = None
    enrolled_date: Optional[datetime] = None
    status: str = "active"
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate and normalize data after initialization."""
        if not self.email or not self.name or not self.github_organization:
            raise ValueError("email, name, and github_organization are required")

        # Normalize email to lowercase
        self.email = self.email.lower().strip()

        # Validate status
        valid_statuses = {"active", "inactive", "dropped"}
        if self.status not in valid_statuses:
            raise ValueError(f"status must be one of {valid_statuses}")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Student':
        """
        Create Student from dictionary (e.g., database row).

        Args:
            data: Dictionary containing student data

        Returns:
            Student instance
        """
        # Convert timestamp strings to datetime objects
        for field_name in ['enrolled_date', 'created_at', 'updated_at']:
            if field_name in data and isinstance(data[field_name], str):
                try:
                    data[field_name] = datetime.fromisoformat(data[field_name])
                except (ValueError, TypeError):
                    data[field_name] = None

        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Student to dictionary.

        Returns:
            Dictionary representation of student
        """
        data = {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'github_username': self.github_username,
            'github_id': self.github_id,
            'github_organization': self.github_organization,
            'enrolled_date': self.enrolled_date.isoformat() if self.enrolled_date else None,
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        return data


@dataclass
class Assignment:
    """
    Represents an assignment in the classroom.

    Attributes:
        name: Assignment name (unique identifier)
        github_organization: GitHub organization
        id: Database primary key (None for new assignments)
        classroom_id: GitHub Classroom assignment ID
        classroom_url: URL to GitHub Classroom assignment
        template_repo_url: URL to template repository
        assignment_type: Type (individual, group)
        deadline: Assignment deadline
        points_available: Total points for assignment
        status: Assignment status (active, closed, archived)
        created_at: Record creation timestamp
        updated_at: Record last update timestamp
    """
    name: str
    github_organization: str
    id: Optional[int] = None
    classroom_id: Optional[int] = None
    classroom_url: Optional[str] = None
    template_repo_url: Optional[str] = None
    assignment_type: str = "individual"
    deadline: Optional[datetime] = None
    points_available: int = 100
    status: str = "active"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate and normalize data after initialization."""
        if not self.name or not self.github_organization:
            raise ValueError("name and github_organization are required")

        # Validate assignment type
        valid_types = {"individual", "group"}
        if self.assignment_type not in valid_types:
            raise ValueError(f"assignment_type must be one of {valid_types}")

        # Validate status
        valid_statuses = {"active", "closed", "archived"}
        if self.status not in valid_statuses:
            raise ValueError(f"status must be one of {valid_statuses}")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Assignment':
        """
        Create Assignment from dictionary.

        Args:
            data: Dictionary containing assignment data

        Returns:
            Assignment instance
        """
        # Convert timestamp strings to datetime objects
        for field_name in ['deadline', 'created_at', 'updated_at']:
            if field_name in data and isinstance(data[field_name], str):
                try:
                    data[field_name] = datetime.fromisoformat(data[field_name])
                except (ValueError, TypeError):
                    data[field_name] = None

        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Assignment to dictionary.

        Returns:
            Dictionary representation of assignment
        """
        data = {
            'id': self.id,
            'name': self.name,
            'classroom_id': self.classroom_id,
            'classroom_url': self.classroom_url,
            'template_repo_url': self.template_repo_url,
            'github_organization': self.github_organization,
            'assignment_type': self.assignment_type,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'points_available': self.points_available,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        return data


@dataclass
class StudentAssignment:
    """
    Represents the relationship between a student and an assignment.

    Attributes:
        student_id: Foreign key to students table
        assignment_id: Foreign key to assignments table
        id: Database primary key (None for new records)
        repository_url: URL to student's assignment repository
        repository_name: Name of student's assignment repository
        acceptance_status: Status (pending, accepted, completed, submitted)
        accepted_at: When student accepted assignment
        last_commit_at: Timestamp of last commit
        last_synced_at: Last synchronization timestamp
        notes: Additional notes
        created_at: Record creation timestamp
        updated_at: Record last update timestamp
    """
    student_id: int
    assignment_id: int
    id: Optional[int] = None
    repository_url: Optional[str] = None
    repository_name: Optional[str] = None
    acceptance_status: str = "pending"
    accepted_at: Optional[datetime] = None
    last_commit_at: Optional[datetime] = None
    last_synced_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate data after initialization."""
        if not self.student_id or not self.assignment_id:
            raise ValueError("student_id and assignment_id are required")

        # Validate acceptance status
        valid_statuses = {"pending", "accepted", "completed", "submitted"}
        if self.acceptance_status not in valid_statuses:
            raise ValueError(f"acceptance_status must be one of {valid_statuses}")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StudentAssignment':
        """
        Create StudentAssignment from dictionary.

        Args:
            data: Dictionary containing student assignment data

        Returns:
            StudentAssignment instance
        """
        # Convert timestamp strings to datetime objects
        for field_name in ['accepted_at', 'last_commit_at', 'last_synced_at',
                           'created_at', 'updated_at']:
            if field_name in data and isinstance(data[field_name], str):
                try:
                    data[field_name] = datetime.fromisoformat(data[field_name])
                except (ValueError, TypeError):
                    data[field_name] = None

        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert StudentAssignment to dictionary.

        Returns:
            Dictionary representation
        """
        data = {
            'id': self.id,
            'student_id': self.student_id,
            'assignment_id': self.assignment_id,
            'repository_url': self.repository_url,
            'repository_name': self.repository_name,
            'acceptance_status': self.acceptance_status,
            'accepted_at': self.accepted_at.isoformat() if self.accepted_at else None,
            'last_commit_at': self.last_commit_at.isoformat() if self.last_commit_at else None,
            'last_synced_at': self.last_synced_at.isoformat() if self.last_synced_at else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        return data


@dataclass
class ImportResult:
    """
    Result of a roster import operation.

    Attributes:
        total_rows: Total rows in import file
        successful: Number of successfully imported students
        failed: Number of failed imports
        skipped: Number of skipped duplicates
        errors: List of error messages
        imported_students: List of successfully imported students
    """
    total_rows: int = 0
    successful: int = 0
    failed: int = 0
    skipped: int = 0
    errors: List[str] = field(default_factory=list)
    imported_students: List[Student] = field(default_factory=list)

    def add_error(self, error: str) -> None:
        """Add an error message to the result."""
        self.errors.append(error)
        self.failed += 1

    def add_success(self, student: Student) -> None:
        """Add a successful import to the result."""
        self.imported_students.append(student)
        self.successful += 1

    def add_skip(self) -> None:
        """Increment skipped count."""
        self.skipped += 1

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_rows == 0:
            return 0.0
        return (self.successful / self.total_rows) * 100


@dataclass
class SyncResult:
    """
    Result of a repository synchronization operation.

    Attributes:
        sync_type: Type of sync (github_classroom, repositories)
        total_repos: Total repositories processed
        linked_count: Number of successfully linked repositories
        unlinked_count: Number of repositories that couldn't be linked
        errors: List of error messages
        unlinked_repos: List of repository URLs that couldn't be linked
    """
    sync_type: str
    total_repos: int = 0
    linked_count: int = 0
    unlinked_count: int = 0
    errors: List[str] = field(default_factory=list)
    unlinked_repos: List[str] = field(default_factory=list)

    def add_error(self, error: str) -> None:
        """Add an error message to the result."""
        self.errors.append(error)

    def add_linked(self) -> None:
        """Increment linked count."""
        self.linked_count += 1

    def add_unlinked(self, repo_url: str) -> None:
        """Add an unlinked repository."""
        self.unlinked_repos.append(repo_url)
        self.unlinked_count += 1

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_repos == 0:
            return 0.0
        return (self.linked_count / self.total_repos) * 100
