"""
GitHub API Client for Classroom Integration.

This module provides a client for interacting with the GitHub Classroom API
to fetch classroom and assignment data when URL parsing is insufficient.
"""

import os
import requests
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ClassroomInfo:
    """Data class for classroom information."""
    id: int
    name: str
    url: str
    organization: str


@dataclass
class AssignmentInfo:
    """Data class for assignment information."""
    id: int
    title: str
    classroom_id: int
    invite_link: str
    organization: str


class GitHubAPIClient:
    """Client for interacting with GitHub Classroom API."""

    def __init__(self, token: Optional[str] = None):
        """
        Initialize the GitHub API client.

        Args:
            token: GitHub token. If None, will try to get from GITHUB_TOKEN env var.
        """
        self.token = token or os.getenv('GITHUB_TOKEN')
        if not self.token:
            raise ValueError(
                "GitHub token is required. Set GITHUB_TOKEN environment variable or pass token parameter.")

        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28',
            'User-Agent': 'classdock'
        }
        self.base_url = 'https://api.github.com'

    @staticmethod
    def is_likely_classroom_name(organization: str) -> bool:
        """
        Detect if the given organization string is likely a classroom name rather than a real GitHub organization.

        Classroom names typically follow patterns like:
        - Numbers followed by dash and text: "225080578-soc-cs3550-f25"
        - Mixed case with course codes: "cs101-fall2024"
        - Academic term patterns: "spring2024", "fall25"

        Args:
            organization: The organization string to analyze

        Returns:
            bool: True if this looks like a classroom name, False if it looks like a real org
        """
        if not organization:
            return False

        import re

        # Pattern 1: Starts with digits followed by dash (like "225080578-soc-cs3550-f25")
        if re.match(r'^\d+[-_]', organization):
            return True

        # Pattern 2: Contains academic term indicators
        term_patterns = [
            r'(spring|summer|fall|winter)\d{2,4}',  # spring2024, fall25
            r'(sp|su|fa|wi)\d{2,4}',                # sp24, fa25
            r'(s|f)\d{2,4}',                        # s24, f25
            r'\d{4}(spring|summer|fall|winter)',    # 2024fall
        ]

        for pattern in term_patterns:
            if re.search(pattern, organization, re.IGNORECASE):
                return True

        # Pattern 3: Course code patterns (letters followed by numbers)
        if re.search(r'^[a-z]{2,4}\d{3,4}[-_]', organization, re.IGNORECASE):
            return True

        # Pattern 4: Multiple dashes/underscores but only if combined with other patterns
        dash_count = organization.count('-')
        underscore_count = organization.count('_')

        if (dash_count >= 2 or underscore_count >= 2):
            # Check if it also has numbers or academic patterns
            if re.search(r'\d', organization):  # Contains digits
                return True
            # Check for academic year patterns like "fall", "spring", etc.
            if re.search(r'(20|19)\d{2}', organization):  # Years like 2024, 2025
                return True

        return False

    def verify_token(self) -> bool:
        """
        Verify that the GitHub token is valid.

        Returns:
            bool: True if token is valid, False otherwise.
        """
        try:
            response = requests.get(
                f'{self.base_url}/user', headers=self.headers, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to verify GitHub token: {e}")
            return False

    def list_classrooms(self) -> List[ClassroomInfo]:
        """
        List all accessible classrooms.

        Returns:
            List[ClassroomInfo]: List of classroom information objects.
        """
        try:
            response = requests.get(
                f'{self.base_url}/classrooms', headers=self.headers, timeout=30)

            if response.status_code != 200:
                logger.error(
                    f"Failed to list classrooms: {response.status_code} - {response.text}")
                return []

            classrooms = response.json()
            result = []

            for classroom in classrooms:
                try:
                    # Extract organization directly from API response
                    org_name = ''
                    if 'organization' in classroom and classroom['organization']:
                        org_data = classroom['organization']
                        org_name = org_data.get('login', '')
                        logger.debug(
                            f"Found organization: {org_name} for classroom {classroom.get('name', 'Unknown')}")

                    classroom_info = ClassroomInfo(
                        id=classroom.get('id'),
                        name=classroom.get('name', ''),
                        url=classroom.get('url', ''),
                        organization=org_name
                    )
                    result.append(classroom_info)
                except Exception as e:
                    logger.warning(f"Failed to parse classroom data: {e}")
                    continue

            return result

        except Exception as e:
            logger.error(f"Failed to list classrooms: {e}")
            return []

    def get_classroom_by_id(self, classroom_id: int) -> Optional[ClassroomInfo]:
        """
        Get classroom information by ID.

        Args:
            classroom_id: The classroom ID.

        Returns:
            Optional[ClassroomInfo]: Classroom information or None if not found.
        """
        try:
            response = requests.get(
                f'{self.base_url}/classrooms/{classroom_id}', headers=self.headers, timeout=30)

            if response.status_code != 200:
                logger.error(
                    f"Failed to get classroom {classroom_id}: {response.status_code}")
                return None

            classroom = response.json()
            classroom_url = classroom.get('url', '')
            org_name = self._extract_org_from_classroom_url(classroom_url)

            return ClassroomInfo(
                id=classroom.get('id'),
                name=classroom.get('name', ''),
                url=classroom_url,
                organization=org_name
            )

        except Exception as e:
            logger.error(f"Failed to get classroom {classroom_id}: {e}")
            return None

    def list_classroom_assignments(self, classroom_id: int) -> List[AssignmentInfo]:
        """
        List assignments for a specific classroom.

        Args:
            classroom_id: The classroom ID.

        Returns:
            List[AssignmentInfo]: List of assignment information objects.
        """
        try:
            response = requests.get(
                f'{self.base_url}/classrooms/{classroom_id}/assignments',
                headers=self.headers,
                timeout=30
            )

            if response.status_code != 200:
                logger.error(
                    f"Failed to list assignments for classroom {classroom_id}: {response.status_code}")
                return []

            assignments = response.json()
            result = []

            # Get classroom info for organization
            classroom_info = self.get_classroom_by_id(classroom_id)
            org_name = classroom_info.organization if classroom_info else ''

            for assignment in assignments:
                try:
                    assignment_info = AssignmentInfo(
                        id=assignment.get('id'),
                        title=assignment.get('title', ''),
                        classroom_id=classroom_id,
                        invite_link=assignment.get('invite_link', ''),
                        organization=org_name
                    )
                    result.append(assignment_info)
                except Exception as e:
                    logger.warning(f"Failed to parse assignment data: {e}")
                    continue

            return result

        except Exception as e:
            logger.error(
                f"Failed to list assignments for classroom {classroom_id}: {e}")
            return []

    def find_classroom_by_url_segment(self, url_segment: str) -> Optional[ClassroomInfo]:
        """
        Find classroom by matching URL segment.

        Args:
            url_segment: URL segment to match (e.g., "225080578-soc-cs3550-f25").

        Returns:
            Optional[ClassroomInfo]: Matching classroom or None if not found.
        """
        classrooms = self.list_classrooms()

        for classroom in classrooms:
            if url_segment in classroom.url:
                return classroom

        return None

    def extract_classroom_data_from_url(self, classroom_url: str) -> Dict[str, str]:
        """
        Extract comprehensive classroom data from a GitHub Classroom URL using API.

        This method follows the pattern from test examples: list all classrooms, 
        find match by URL segment, extract organization data from the matched classroom.

        URL Format: https://classroom.github.com/classrooms/CLASSROOM_ID-CLASSROOM_NAME/assignments/ASSIGNMENT_NAME
        Where:
        - CLASSROOM_ID: Numeric ID (e.g., 225080578)
        - CLASSROOM_NAME: Human-readable name (e.g., soc-cs3550-f25) - NOT the organization
        - ASSIGNMENT_NAME: Assignment name (e.g., project3)

        Args:
            classroom_url: GitHub Classroom URL

        Returns:
            Dict with classroom information including organization, assignment details, etc.
        """
        result = {
            'organization': '',
            'assignment_name': '',
            'classroom_id': '',
            'classroom_name': '',
            'assignment_id': '',
            'invite_link': '',
            'template_repo': '',
            'success': False,
            'error': ''
        }

        try:
            # Extract URL segments for classroom ID and assignment name
            import re

            # Pattern: https://classroom.github.com/classrooms/ID-NAME/assignments/ASSIGNMENT
            classroom_match = re.search(
                r'classroom\.github\.com/classrooms/([^/]+)/assignments/([^/?]+)', classroom_url)

            if not classroom_match:
                result['error'] = 'Invalid classroom URL format'
                return result

            classroom_id_segment = classroom_match.group(
                1)  # e.g., "225080578-soc-cs3550-f25"
            url_assignment_name = classroom_match.group(2)   # e.g., "project3"

            logger.info(
                f"Extracted classroom segment: {classroom_id_segment}, assignment: {url_assignment_name}")

            # Step 1: List all accessible classrooms (following test pattern)
            classrooms = self.list_classrooms()
            logger.debug(f"Found {len(classrooms)} total classrooms")

            # Step 2: Find matching classroom by URL segment (like test examples)
            matching_classroom = None
            for classroom in classrooms:
                # Check if classroom URL contains our identifier segment
                if classroom.url and classroom_id_segment in classroom.url:
                    matching_classroom = classroom
                    logger.info(
                        f"Found matching classroom: {classroom.name} (ID: {classroom.id})")
                    break

            if not matching_classroom:
                result['error'] = f'No classroom found matching URL segment: {classroom_id_segment}'
                return result

            logger.info(
                f"Found classroom: {matching_classroom.name}, organization: {matching_classroom.organization}")

            # Get assignments for this classroom to find the specific assignment
            assignments = self.list_classroom_assignments(
                matching_classroom.id)

            # Find matching assignment by name
            matching_assignment = None
            for assignment in assignments:
                if assignment.title.lower() == url_assignment_name.lower():
                    matching_assignment = assignment
                    break

            # If exact match not found, try partial matching
            if not matching_assignment:
                for assignment in assignments:
                    if url_assignment_name.lower() in assignment.title.lower():
                        matching_assignment = assignment
                        logger.info(
                            f"Found partial match: '{assignment.title}' for '{url_assignment_name}'")
                        break

            # Populate result with classroom data (organization from API, not URL parsing)
            result.update({
                'organization': matching_classroom.organization,
                'assignment_name': url_assignment_name,
                'classroom_id': str(matching_classroom.id),
                'classroom_name': matching_classroom.name,
                'success': True
            })

            if matching_assignment:
                result.update({
                    'assignment_id': str(matching_assignment.id),
                    'invite_link': matching_assignment.invite_link
                })
                logger.info(
                    f"Found matching assignment: {matching_assignment.title} (ID: {matching_assignment.id})")
            else:
                logger.warning(
                    f"No matching assignment found for '{url_assignment_name}' in classroom {matching_classroom.id}")
                # Still return success since we have the classroom data

            # Try to get template repository information
            if matching_assignment:
                template_repo = self._get_assignment_template_repo(
                    matching_assignment.id)
                if template_repo:
                    result['template_repo'] = template_repo

            return result

        except Exception as e:
            logger.error(
                f"Failed to extract classroom data from URL {classroom_url}: {e}")
            result['error'] = str(e)
            return result

    def _extract_org_from_classroom_url(self, classroom_url: str) -> str:
        """Extract organization name from classroom URL."""
        import re

        # Pattern for classroom URLs that contain organization info
        # Example: https://github.com/organizations/soc-cs3550-f25/classrooms/12345
        org_match = re.search(
            r'github\.com/organizations/([^/]+)/', classroom_url)
        if org_match:
            return org_match.group(1)

        # Fallback: try to extract from path segments
        # This is less reliable but might work for some URL formats
        segments = classroom_url.strip('/').split('/')
        for i, segment in enumerate(segments):
            if segment == 'organizations' and i + 1 < len(segments):
                return segments[i + 1]

        return ''

    def _get_assignment_template_repo(self, assignment_id: int) -> str:
        """
        Get the template repository for an assignment.

        Args:
            assignment_id: The assignment ID

        Returns:
            str: Template repository name (e.g., "user/repo-name") or empty string if not found
        """
        try:
            response = requests.get(
                f'{self.base_url}/assignments/{assignment_id}', headers=self.headers, timeout=30)

            if response.status_code != 200:
                logger.warning(
                    f"Failed to get assignment {assignment_id}: {response.status_code}")
                return ''

            assignment = response.json()

            # Try to extract template repository from assignment data
            template_repo = assignment.get('template_repository', {})
            if template_repo:
                return template_repo.get('full_name', '')

            # Alternative: try to get from starter_code_repository
            starter_repo = assignment.get('starter_code_repository', {})
            if starter_repo:
                return starter_repo.get('full_name', '')

            return ''

        except Exception as e:
            logger.error(
                f"Failed to get template repo for assignment {assignment_id}: {e}")
            return ''
