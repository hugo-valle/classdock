"""
GitHub Classroom integration for organization management.

Provides ClassroomManager which wraps the GitHub Classroom REST API to:
- List classrooms linked to a GitHub organization
- List assignments within a classroom
- Retrieve grade and accepted-assignment data
- Generate deep-link URLs for one-click assignment creation in the web UI
- Clone a classroom's starter repo set into a target org
"""

import logging
from typing import List, Optional

from ..utils.github_classroom_api import GitHubClassroomAPI, GitHubClassroomAPIError
from .models import Classroom, ClassroomAssignment

logger = logging.getLogger(__name__)

_CLASSROOM_NEW_URL = (
    "https://classroom.github.com/classrooms/{classroom_id}/assignments/new"
)


class ClassroomManager:
    """
    Manages GitHub Classroom data for a given token holder.

    Wraps GitHubClassroomAPI with typed models, pagination, and org-scoped
    filtering.  All write operations (create classroom, create assignment) must
    be performed via the GitHub Classroom web UI — the REST API is read-only.

    Args:
        token: GitHub personal access token.
    """

    def __init__(self, token: Optional[str] = None):
        if not token:
            raise ValueError("GitHub token is required for Classroom API access.")
        self._api = GitHubClassroomAPI(github_token=token)

    # ------------------------------------------------------------------
    # Classroom discovery
    # ------------------------------------------------------------------

    def list_classrooms(self, enrich_org: bool = False) -> List[Classroom]:
        """
        Return all classrooms accessible to the authenticated user.

        Args:
            enrich_org: If True, fetch full classroom details for each entry
                        to populate org_login (extra N API calls).  Use only
                        when the org column is needed in display output.

        Returns:
            Sorted list of Classroom objects (alphabetically by name).
        """
        raw = self._api.get_classrooms_paginated()
        classrooms = [Classroom.from_dict(c) for c in raw]
        if enrich_org:
            enriched = []
            for c in classrooms:
                if not c.org_login:
                    full = self.get_classroom(c.id)
                    enriched.append(full if full else c)
                else:
                    enriched.append(c)
            classrooms = enriched
        classrooms.sort(key=lambda c: c.name.lower())
        logger.debug("Found %d accessible classrooms", len(classrooms))
        return classrooms

    def list_classrooms_for_org(self, org_login: str) -> List[Classroom]:
        """
        Return classrooms linked to a specific GitHub organization.

        The GitHub Classroom list endpoint does not include organization details,
        so this method fetches full details for each classroom to resolve the
        org login.  Most instructors have few classrooms, so N+1 calls are
        acceptable here.

        Args:
            org_login: GitHub organization login to filter by.

        Returns:
            List of Classroom objects linked to that org.
        """
        all_classrooms = self.list_classrooms()
        matched = []
        for c in all_classrooms:
            # Enrich with full details if org_login not already populated
            if not c.org_login:
                full = self.get_classroom(c.id)
                if full:
                    c = full
            if c.org_login.lower() == org_login.lower():
                matched.append(c)
        return matched

    def get_classroom(self, classroom_id: int) -> Optional[Classroom]:
        """
        Return a single classroom by ID, or None if not found / not accessible.

        Args:
            classroom_id: GitHub Classroom numeric ID.
        """
        try:
            raw = self._api.get_classroom(classroom_id)
            return Classroom.from_dict(raw)
        except GitHubClassroomAPIError as exc:
            if exc.status_code == 404:
                return None
            raise

    # ------------------------------------------------------------------
    # Assignment operations
    # ------------------------------------------------------------------

    def list_assignments(self, classroom_id: int) -> List[ClassroomAssignment]:
        """
        Return all assignments for a classroom.

        Args:
            classroom_id: GitHub Classroom numeric ID.

        Returns:
            List of ClassroomAssignment objects.
        """
        raw = self._api.get_classroom_assignments_paginated(classroom_id)
        assignments = [ClassroomAssignment.from_dict(a) for a in raw]
        logger.debug(
            "Found %d assignments in classroom %d", len(assignments), classroom_id
        )
        return assignments

    def get_assignment(self, assignment_id: int) -> Optional[ClassroomAssignment]:
        """
        Return a single assignment by ID, or None if not found.

        Args:
            assignment_id: GitHub Classroom assignment numeric ID.
        """
        try:
            raw = self._api.get_assignment(assignment_id)
            return ClassroomAssignment.from_dict(raw)
        except GitHubClassroomAPIError as exc:
            if exc.status_code == 404:
                return None
            raise

    def get_accepted_assignments(self, assignment_id: int) -> List[dict]:
        """
        Return all student-accepted repositories for an assignment.

        Args:
            assignment_id: GitHub Classroom assignment numeric ID.

        Returns:
            List of raw accepted-assignment dicts from the API.
        """
        return self._api.get_accepted_assignments_paginated(assignment_id)

    def get_grades(self, assignment_id: int) -> List[dict]:
        """
        Return grading records for an assignment.

        Args:
            assignment_id: GitHub Classroom assignment numeric ID.

        Returns:
            List of grade record dicts from the API.
        """
        return self._api.get_assignment_grades(assignment_id)

    # ------------------------------------------------------------------
    # Deep-link URL helpers
    # ------------------------------------------------------------------

    @staticmethod
    def assignment_creation_url(
        classroom_id: int,
        template_repo: Optional[str] = None,
    ) -> str:
        """
        Return the GitHub Classroom URL to pre-fill a new assignment.

        Since the Classroom API has no create endpoint, instructors must use
        the web UI.  This URL deep-links directly to the new-assignment form
        with the template repo pre-selected (when provided).

        Args:
            classroom_id: GitHub Classroom numeric ID.
            template_repo: "owner/repo" of the starter code template (optional).

        Returns:
            URL string the instructor can open in a browser.
        """
        base = _CLASSROOM_NEW_URL.format(classroom_id=classroom_id)
        if template_repo:
            return f"{base}?template_repo={template_repo}"
        return base

    @staticmethod
    def new_classroom_url() -> str:
        """Return the URL to create a new GitHub Classroom."""
        return "https://classroom.github.com/classrooms/new"
