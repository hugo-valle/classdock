"""
Data models for ClassDock organization management.

Defines dataclasses for GitHub organizations, template repositories,
local workspace folders, operation results, and GitHub Classroom data.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class Organization:
    """
    Represents a GitHub organization.

    Attributes:
        login: Organization login (slug used in URLs)
        name: Organization display name
        id: GitHub organization ID
        description: Organization description
        url: HTML URL to organization on GitHub
        avatar_url: Organization avatar URL
        role: Authenticated user's role in the org (admin, member)
    """

    login: str
    name: Optional[str] = None
    id: Optional[int] = None
    description: Optional[str] = None
    url: Optional[str] = None
    avatar_url: Optional[str] = None
    role: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Organization":
        """Create Organization from a GitHub API response dict."""
        return cls(
            login=data.get("login", ""),
            name=data.get("name"),
            id=data.get("id"),
            description=data.get("description"),
            url=data.get("html_url"),
            avatar_url=data.get("avatar_url"),
            role=data.get("role"),
        )

    def to_dict(self) -> dict:
        """Convert Organization to dictionary."""
        return {
            "login": self.login,
            "name": self.name,
            "id": self.id,
            "description": self.description,
            "url": self.url,
            "avatar_url": self.avatar_url,
            "role": self.role,
        }


@dataclass
class TemplateRepo:
    """
    Represents a template repository (master or cloned).

    Attributes:
        name: Repository name (without owner prefix)
        owner: Repository owner (org login or username)
        full_name: Full repository name (owner/name)
        url: HTML URL to repository on GitHub
        clone_url: Git clone URL (HTTPS)
        is_template: Whether the repo is marked as a GitHub template
        private: Whether the repository is private
        description: Repository description
        local_path: Local filesystem path if cloned
    """

    name: str
    owner: str
    full_name: str = ""
    url: str = ""
    clone_url: str = ""
    is_template: bool = False
    private: bool = False
    description: Optional[str] = None
    local_path: Optional[Path] = None

    def __post_init__(self):
        if not self.full_name:
            self.full_name = f"{self.owner}/{self.name}"

    @classmethod
    def from_dict(cls, data: dict) -> "TemplateRepo":
        """Create TemplateRepo from a GitHub API response dict."""
        owner_login = (
            data["owner"]["login"] if isinstance(data.get("owner"), dict) else data.get("owner", "")
        )
        return cls(
            name=data.get("name", ""),
            owner=owner_login,
            full_name=data.get("full_name", ""),
            url=data.get("html_url", ""),
            clone_url=data.get("clone_url", ""),
            is_template=data.get("is_template", False),
            private=data.get("private", False),
            description=data.get("description"),
        )

    def to_dict(self) -> dict:
        """Convert TemplateRepo to dictionary."""
        return {
            "name": self.name,
            "owner": self.owner,
            "full_name": self.full_name,
            "url": self.url,
            "clone_url": self.clone_url,
            "is_template": self.is_template,
            "private": self.private,
            "description": self.description,
            "local_path": str(self.local_path) if self.local_path else None,
        }


@dataclass
class WorkspaceFolder:
    """
    Represents a local workspace folder (master or semester org).

    Attributes:
        path: Absolute path to the workspace folder
        is_master: True if this is a master template folder
        course_code: Course code (e.g., CS3030)
        org_name: GitHub org name this folder is linked to (None for master)
        repos: List of template repos found in this folder
    """

    path: Path
    is_master: bool = False
    course_code: Optional[str] = None
    org_name: Optional[str] = None
    repos: List[TemplateRepo] = field(default_factory=list)

    MASTER_MARKER = ".classdock-master"

    @property
    def marker_path(self) -> Path:
        """Path to the master marker file."""
        return self.path / self.MASTER_MARKER

    def is_marked_as_master(self) -> bool:
        """Check if this folder has the master marker file."""
        return self.marker_path.exists()

    def to_dict(self) -> dict:
        """Convert WorkspaceFolder to dictionary."""
        return {
            "path": str(self.path),
            "is_master": self.is_master,
            "course_code": self.course_code,
            "org_name": self.org_name,
            "repos": [r.to_dict() for r in self.repos],
        }


@dataclass
class CloneResult:
    """
    Result of a batch template cloning operation.

    Attributes:
        total: Total repositories attempted
        successful: Successfully cloned count
        failed: Failed clone count
        cloned_repos: List of successfully cloned repos
        errors: Error messages for failures
    """

    total: int = 0
    successful: int = 0
    failed: int = 0
    cloned_repos: List[TemplateRepo] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    already_existed: List[str] = field(default_factory=list)
    attempted_names: List[str] = field(default_factory=list)

    def add_success(self, repo: TemplateRepo) -> None:
        """Record a successful clone."""
        self.cloned_repos.append(repo)
        self.successful += 1

    def add_failure(self, error: str) -> None:
        """Record a clone failure."""
        self.errors.append(error)
        self.failed += 1

    def add_already_existed(self, repo_name: str) -> None:
        """Record a repo that was skipped because it already exists in the target org."""
        self.already_existed.append(repo_name)

    @property
    def success_rate(self) -> float:
        """Return success rate as a percentage (0-100)."""
        if self.total == 0:
            return 0.0
        return (self.successful / self.total) * 100


@dataclass
class SetupResult:
    """
    Result of the full organization setup wizard.

    Attributes:
        organization: The newly created or selected organization
        workspace_folder: The local semester org folder created
        clone_result: Results of template cloning
        success: Whether the overall setup succeeded
        error_message: Human-readable error if setup failed
    """

    organization: Optional[Organization] = None
    workspace_folder: Optional[WorkspaceFolder] = None
    clone_result: Optional[CloneResult] = None
    success: bool = False
    error_message: Optional[str] = None


@dataclass
class Classroom:
    """
    Represents a GitHub Classroom.

    Attributes:
        id: GitHub Classroom numeric ID
        name: Classroom display name
        url: URL to the classroom on classroom.github.com
        archived: Whether the classroom is archived
        org_login: Login of the GitHub organization linked to this classroom
    """

    id: int
    name: str
    url: str = ""
    archived: bool = False
    org_login: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "Classroom":
        """Create a Classroom from a GitHub Classroom API response dict."""
        org = data.get("organization") or {}
        return cls(
            id=data["id"],
            name=data.get("name", ""),
            url=data.get("url", ""),
            archived=data.get("archived", False),
            org_login=org.get("login", "") if isinstance(org, dict) else "",
        )

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "archived": self.archived,
            "org_login": self.org_login,
        }


@dataclass
class ClassroomAssignment:
    """
    Represents an assignment within a GitHub Classroom.

    Attributes:
        id: GitHub Classroom assignment numeric ID
        title: Assignment title
        type: Assignment type — "individual" or "group"
        deadline: ISO-8601 deadline string, or None
        accepted_count: Number of students who accepted
        submitted_count: Number of students who submitted
        passing_count: Number of submissions passing autograding
        starter_code_repo: "owner/repo" of the starter code template, or None
        invite_link: GitHub Classroom invite URL for students
        classroom_id: ID of the parent classroom
    """

    id: int
    title: str
    type: str = "individual"
    deadline: Optional[str] = None
    accepted_count: int = 0
    submitted_count: int = 0
    passing_count: int = 0
    starter_code_repo: Optional[str] = None
    invite_link: Optional[str] = None
    classroom_id: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> "ClassroomAssignment":
        """Create a ClassroomAssignment from a GitHub Classroom API response dict."""
        starter = data.get("starter_code_repository") or {}
        starter_repo = starter.get("full_name") if isinstance(starter, dict) else None
        classroom = data.get("classroom") or {}
        return cls(
            id=data["id"],
            title=data.get("title", ""),
            type=data.get("type", "individual"),
            deadline=data.get("deadline"),
            accepted_count=data.get("accepted", 0),
            submitted_count=data.get("submitted", 0),
            passing_count=data.get("passing", 0),
            starter_code_repo=starter_repo,
            invite_link=data.get("invite_link"),
            classroom_id=classroom.get("id", 0) if isinstance(classroom, dict) else 0,
        )

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "type": self.type,
            "deadline": self.deadline,
            "accepted_count": self.accepted_count,
            "submitted_count": self.submitted_count,
            "passing_count": self.passing_count,
            "starter_code_repo": self.starter_code_repo,
            "invite_link": self.invite_link,
            "classroom_id": self.classroom_id,
        }
