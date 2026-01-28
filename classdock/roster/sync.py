"""
GitHub synchronization for ClassDock roster management.

Provides functionality to synchronize discovered repositories with the roster
database, linking students to their assignments.
"""

from typing import List, Optional, Tuple
from datetime import datetime

from .models import Student, Assignment, StudentAssignment, SyncResult
from .manager import RosterManager
from ..utils.logger import get_logger

logger = get_logger("roster_sync")


class RosterSynchronizer:
    """
    Synchronizes roster with GitHub Classroom repositories.

    Coordinates between discovered GitHub repositories and the roster database,
    creating links between students and their assignment repositories.
    """

    def __init__(self, roster_manager: RosterManager):
        """
        Initialize roster synchronizer.

        Args:
            roster_manager: RosterManager instance
        """
        self.roster = roster_manager

    def sync_repositories(
        self,
        assignment_name: str,
        github_organization: str,
        discovered_repos: List[Tuple[str, str, str]]
    ) -> SyncResult:
        """
        Synchronize discovered repositories with roster.

        Links student repositories to their roster entries by matching
        GitHub usernames. Creates assignment record if needed.

        Args:
            assignment_name: Name of the assignment
            github_organization: GitHub organization
            discovered_repos: List of (repo_name, repo_url, student_identifier) tuples

        Returns:
            SyncResult with synchronization statistics

        Example:
            >>> repos = [
            ...     ("python-basics-johndoe", "https://github.com/org/repo1", "johndoe"),
            ...     ("python-basics-janesmith", "https://github.com/org/repo2", "janesmith")
            ... ]
            >>> result = syncer.sync_repositories("python-basics", "org", repos)
            >>> print(f"Linked: {result.linked_count}, Unlinked: {result.unlinked_count}")
        """
        result = SyncResult(sync_type="repositories", total_repos=len(discovered_repos))

        logger.info(
            f"Syncing {len(discovered_repos)} repositories for assignment: {assignment_name}"
        )

        # Get or create assignment
        assignment = self.roster.get_assignment_by_name(assignment_name)
        if not assignment:
            logger.info(f"Creating new assignment: {assignment_name}")
            assignment_id = self.roster.add_assignment(
                Assignment(
                    name=assignment_name,
                    github_organization=github_organization
                )
            )
            assignment = self.roster.get_assignment_by_id(assignment_id)

        # Process each repository
        for repo_name, repo_url, student_identifier in discovered_repos:
            try:
                if not student_identifier:
                    result.add_unlinked(repo_url)
                    result.add_error(
                        f"Repository {repo_name} has no student identifier"
                    )
                    continue

                # Try to find student by GitHub username
                student = self.roster.get_student_by_github(
                    student_identifier,
                    github_organization
                )

                if not student:
                    result.add_unlinked(repo_url)
                    logger.debug(
                        f"No roster entry for GitHub user: {student_identifier}"
                    )
                    continue

                # Check if link already exists
                existing_link = self.roster.get_student_assignment(
                    student.id,
                    assignment.id
                )

                if existing_link:
                    # Update existing link
                    existing_link.repository_url = repo_url
                    existing_link.repository_name = repo_name
                    existing_link.acceptance_status = "accepted"
                    existing_link.accepted_at = existing_link.accepted_at or datetime.now()
                    existing_link.last_synced_at = datetime.now()

                    self.roster.update_student_assignment(existing_link)
                    result.add_linked()
                    logger.debug(f"Updated link: {student.email} -> {repo_name}")
                else:
                    # Create new link
                    link_id = self.roster.link_student_to_assignment(
                        student.id,
                        assignment.id,
                        repository_url=repo_url,
                        repository_name=repo_name,
                        acceptance_status="accepted"
                    )
                    # Update the link to set last_synced_at
                    new_link = self.roster.get_student_assignment(student.id, assignment.id)
                    new_link.last_synced_at = datetime.now()
                    self.roster.update_student_assignment(new_link)

                    result.add_linked()
                    logger.debug(f"Created link: {student.email} -> {repo_name}")

            except Exception as e:
                result.add_error(f"Error processing {repo_name}: {e}")
                logger.error(f"Failed to process repository {repo_name}: {e}")

        logger.info(
            f"Sync complete: {result.linked_count} linked, "
            f"{result.unlinked_count} unlinked"
        )

        return result

    def detect_unlinked_students(
        self,
        assignment_name: str,
        github_organization: str
    ) -> List[Student]:
        """
        Detect students without repositories for an assignment.

        Finds students in the roster who don't have a repository linked
        to the specified assignment.

        Args:
            assignment_name: Assignment name
            github_organization: GitHub organization

        Returns:
            List of Student objects without linked repositories
        """
        # Get assignment
        assignment = self.roster.get_assignment_by_name(assignment_name)
        if not assignment:
            logger.warning(f"Assignment not found: {assignment_name}")
            return []

        # Get all students in organization
        all_students = self.roster.list_students(
            github_organization=github_organization,
            status="active"
        )

        # Get students with repositories
        students_with_repos = self.roster.get_assignment_students(assignment.id)
        student_ids_with_repos = {student.id for student, _ in students_with_repos}

        # Find students without repos
        unlinked_students = [
            student for student in all_students
            if student.id not in student_ids_with_repos
        ]

        logger.info(
            f"Found {len(unlinked_students)} students without repositories "
            f"for {assignment_name}"
        )

        return unlinked_students

    def detect_unlinked_repositories(
        self,
        assignment_name: str,
        github_organization: str,
        discovered_repos: List[Tuple[str, str, str]]
    ) -> List[Tuple[str, str]]:
        """
        Detect repositories without matching roster entries.

        Identifies repositories that couldn't be matched to any student
        in the roster.

        Args:
            assignment_name: Assignment name
            github_organization: GitHub organization
            discovered_repos: List of (repo_name, repo_url, student_identifier) tuples

        Returns:
            List of (repo_name, student_identifier) tuples for unmatched repos
        """
        unlinked_repos = []

        for repo_name, repo_url, student_identifier in discovered_repos:
            if not student_identifier:
                unlinked_repos.append((repo_name, "unknown"))
                continue

            # Try to find student
            student = self.roster.get_student_by_github(
                student_identifier,
                github_organization
            )

            if not student:
                unlinked_repos.append((repo_name, student_identifier))

        logger.info(
            f"Found {len(unlinked_repos)} unlinked repositories "
            f"for {assignment_name}"
        )

        return unlinked_repos

    def get_sync_statistics(
        self,
        assignment_name: str,
        github_organization: str
    ) -> dict:
        """
        Get synchronization statistics for an assignment.

        Args:
            assignment_name: Assignment name
            github_organization: GitHub organization

        Returns:
            Dictionary with sync statistics:
            - total_students: Total students in roster
            - students_with_repos: Students with linked repositories
            - students_without_repos: Students without repositories
            - acceptance_rate: Percentage of students with repositories
        """
        assignment = self.roster.get_assignment_by_name(assignment_name)
        if not assignment:
            return {
                'total_students': 0,
                'students_with_repos': 0,
                'students_without_repos': 0,
                'acceptance_rate': 0.0
            }

        # Get all students in organization
        all_students = self.roster.list_students(
            github_organization=github_organization,
            status="active"
        )

        # Get students with repositories
        students_with_repos = self.roster.get_assignment_students(assignment.id)

        total_students = len(all_students)
        with_repos = len(students_with_repos)
        without_repos = total_students - with_repos

        acceptance_rate = (with_repos / total_students * 100) if total_students > 0 else 0.0

        return {
            'total_students': total_students,
            'students_with_repos': with_repos,
            'students_without_repos': without_repos,
            'acceptance_rate': acceptance_rate
        }

    def sync_from_classroom_api(
        self,
        assignment_id: int,
        classroom_assignment_id: int,
        classroom_api_client
    ) -> SyncResult:
        """
        Sync assignment data from GitHub Classroom API.

        Retrieves assignment and student data directly from GitHub Classroom API
        and synchronizes with roster.

        Args:
            assignment_id: Local assignment ID in roster
            classroom_assignment_id: GitHub Classroom assignment ID
            classroom_api_client: GitHubClassroomAPI client instance

        Returns:
            SyncResult with synchronization statistics

        Note:
            This is a placeholder for future GitHub Classroom API integration.
            Currently not implemented as it requires the GitHub Classroom API client.
        """
        result = SyncResult(sync_type="github_classroom")

        # TODO: Implement when GitHub Classroom API integration is available
        # This would query the classroom API for:
        # - Assignment details (deadline, points, etc.)
        # - Student acceptance status
        # - Repository URLs
        # And sync this data to the roster

        logger.warning(
            "GitHub Classroom API sync not yet implemented. "
            "Use sync_repositories() with discovered repos instead."
        )

        return result
