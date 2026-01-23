"""
GitHub Classroom API client for repository discovery and management.

This module provides a client for interacting with the GitHub Classroom API
to discover student repositories, manage assignments, and handle classroom operations.

GitHub Classroom API Documentation:
https://docs.github.com/en/rest/classroom
"""

import re
import requests
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

from . import logger


class GitHubClassroomAPIError(Exception):
    """Exception raised for GitHub Classroom API errors."""

    def __init__(self, message: str, response=None, status_code=None):
        super().__init__(message)
        self.response = response
        self.status_code = status_code


class GitHubClassroomAPI:
    """Client for GitHub Classroom API operations."""

    def __init__(self, github_token: str):
        """
        Initialize GitHub Classroom API client.

        Args:
            github_token: GitHub personal access token with classroom scope
        """
        self.github_token = github_token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "classdock"
        }

    def validate_token_scopes(self) -> Dict[str, bool]:
        """
        Validate that the token has the required scopes.

        Returns:
            Dictionary with scope validation results
        """
        try:
            # Make a request to get token information
            response = requests.get(
                f"{self.base_url}/user",
                headers=self.headers
            )

            # Check for X-OAuth-Scopes header
            scopes = response.headers.get('X-OAuth-Scopes', '')
            scope_list = [s.strip() for s in scopes.split(',') if s.strip()]

            return {
                'valid': response.status_code == 200,
                'scopes': scope_list,
                'has_repo': 'repo' in scope_list or 'public_repo' in scope_list,
                'has_read_org': 'read:org' in scope_list or 'admin:org' in scope_list or 'repo' in scope_list,
                'status_code': response.status_code
            }
        except Exception as e:
            logger.debug(f"Error validating token scopes: {e}")
            return {
                'valid': False,
                'scopes': [],
                'has_repo': False,
                'has_read_org': False,
                'error': str(e)
            }

    def check_token_expiration(self) -> Dict[str, any]:
        """
        Check if the GitHub token has expired or is about to expire.

        For fine-grained tokens, GitHub API returns expiration information.
        For classic tokens, we check if the token is valid (classic tokens don't expire).

        Returns:
            Dictionary with expiration information:
            - is_expired: bool - Whether token is expired
            - is_valid: bool - Whether token is currently valid
            - expires_at: str or None - ISO format expiration date (if available)
            - days_remaining: int or None - Days until expiration
            - token_type: str - 'fine-grained' or 'classic'
            - error: str - Error message if check failed
        """
        from datetime import datetime, timezone

        try:
            # Check token validity with rate limit endpoint (doesn't count against rate limit)
            response = requests.get(
                f"{self.base_url}/rate_limit",
                headers=self.headers
            )

            if response.status_code == 401:
                # Token is invalid/expired, but try to get stored expiration date from token manager
                stored_expires_at = None
                stored_days_remaining = None

                try:
                    from ..utils.token_manager import GitHubTokenManager
                    token_manager = GitHubTokenManager()
                    token_data = token_manager._get_token_from_config()

                    if token_data and isinstance(token_data, dict):
                        stored_expires_at = token_data.get('expires_at')

                        if stored_expires_at:
                            try:
                                expiry_date = datetime.fromisoformat(
                                    stored_expires_at.replace('Z', '+00:00'))
                                now = datetime.now(timezone.utc)
                                stored_days_remaining = (
                                    expiry_date - now).days
                            except Exception as e:
                                logger.debug(
                                    f"Error parsing stored expiration date: {e}")
                except Exception as e:
                    logger.debug(
                        f"Could not retrieve stored token expiration: {e}")

                return {
                    'is_expired': True,
                    'is_valid': False,
                    'expires_at': stored_expires_at,
                    'days_remaining': stored_days_remaining if stored_days_remaining is not None else 0,
                    'token_type': 'expired',
                    'error': 'Token is invalid or expired (401 Unauthorized)'
                }

            if response.status_code != 200:
                return {
                    'is_expired': False,
                    'is_valid': False,
                    'expires_at': None,
                    'days_remaining': None,
                    'token_type': 'unknown',
                    'error': f'Token validation failed with status {response.status_code}'
                }

            # Token is valid, now check if it has expiration info
            # GitHub fine-grained tokens include expiration in X-GitHub-Authentication-Token-Expiration header
            expiration_header = response.headers.get(
                'X-GitHub-Authentication-Token-Expiration')

            if expiration_header:
                # Fine-grained token with expiration
                try:
                    expires_at = datetime.fromisoformat(
                        expiration_header.replace('Z', '+00:00'))
                    now = datetime.now(timezone.utc)
                    days_remaining = (expires_at - now).days

                    return {
                        'is_expired': days_remaining < 0,
                        'is_valid': days_remaining >= 0,
                        'expires_at': expiration_header,
                        'days_remaining': days_remaining,
                        'token_type': 'fine-grained'
                    }
                except Exception as e:
                    logger.debug(f"Error parsing expiration date: {e}")

            # Classic token (no expiration) or couldn't get expiration info
            return {
                'is_expired': False,
                'is_valid': True,
                'expires_at': None,
                'days_remaining': None,
                'token_type': 'classic'
            }

        except Exception as e:
            logger.debug(f"Error checking token expiration: {e}")
            return {
                'is_expired': False,
                'is_valid': False,
                'expires_at': None,
                'days_remaining': None,
                'token_type': 'unknown',
                'error': str(e)
            }

    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Make authenticated request to GitHub API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (with leading slash)
            **kwargs: Additional arguments for requests

        Returns:
            Response object

        Raises:
            GitHubClassroomAPIError: If request fails
        """
        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault("headers", {}).update(self.headers)

        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            error_response = getattr(e, 'response', None)
            status_code = error_response.status_code if error_response else None

            # Enhanced error message for common authentication issues
            error_message = f"API request failed: {e}"
            if status_code == 401:
                error_message += "\n\n💡 Authentication failed. This usually means:"
                error_message += "\n  • Your GitHub token has expired"
                error_message += "\n  • Your token doesn't have the required scopes"
                error_message += "\n  • The token is invalid"
                error_message += "\n\n📋 Required scopes for this operation:"
                error_message += "\n  • 'repo' - Full control of private repositories"
                error_message += "\n  • 'read:org' - Read organization membership and team data"
                error_message += "\n\n🔧 To fix this:"
                error_message += "\n  1. Go to https://github.com/settings/tokens"
                error_message += "\n  2. Generate a new token with 'repo' and 'read:org' scopes"
                error_message += "\n  3. Run: classdock config set-token <your-token>"
            elif status_code == 403:
                error_message += "\n\n💡 Access forbidden. This usually means:"
                error_message += "\n  • Your token lacks the required permissions"
                error_message += "\n  • You don't have access to this organization"
                error_message += "\n  • Rate limit exceeded (check X-RateLimit-Remaining header)"
            elif status_code == 404:
                error_message += "\n\n💡 Resource not found. This usually means:"
                error_message += "\n  • The organization doesn't exist"
                error_message += "\n  • You don't have access to view this resource"
                error_message += "\n  • The repository or assignment URL is incorrect"

            raise GitHubClassroomAPIError(
                error_message,
                response=error_response,
                status_code=status_code
            )

    def parse_classroom_url(self, classroom_url: str) -> Tuple[str, str]:
        """
        Parse GitHub Classroom URL to extract assignment information.

        Args:
            classroom_url: URL like https://classroom.github.com/a/assignment_id

        Returns:
            Tuple of (assignment_id, classroom_type)

        Raises:
            ValueError: If URL format is invalid
        """
        # Expected format: https://classroom.github.com/a/assignment_id
        if not classroom_url:
            raise ValueError("Classroom URL is required")

        # Parse the URL
        parsed = urlparse(classroom_url)
        if parsed.netloc != "classroom.github.com":
            raise ValueError(f"Invalid classroom URL domain: {parsed.netloc}")

        # Extract assignment ID from path
        path_pattern = r'^/a/([a-zA-Z0-9-_]+)/?$'
        match = re.match(path_pattern, parsed.path)
        if not match:
            raise ValueError(
                f"Invalid classroom URL path format: {parsed.path}")

        assignment_id = match.group(1)
        return assignment_id, "assignment"

    def get_classrooms(self) -> List[Dict]:
        """
        Get all classrooms accessible to the authenticated user.

        Returns:
            List of classroom dictionaries
        """
        logger.info("Fetching accessible classrooms")
        response = self._make_request("GET", "/classrooms")
        classrooms = response.json()
        logger.debug(f"Found {len(classrooms)} accessible classrooms")
        return classrooms

    def get_classroom_assignments(self, classroom_id: int) -> List[Dict]:
        """
        Get all assignments for a specific classroom.

        Args:
            classroom_id: GitHub Classroom ID

        Returns:
            List of assignment dictionaries
        """
        logger.info(f"Fetching assignments for classroom {classroom_id}")
        response = self._make_request(
            "GET", f"/classrooms/{classroom_id}/assignments")
        assignments = response.json()
        logger.debug(f"Found {len(assignments)} assignments")
        return assignments

    def get_assignment_repositories(self, assignment_id: int) -> List[Dict]:
        """
        Get all student repositories for a specific assignment.

        Args:
            assignment_id: GitHub Classroom assignment ID

        Returns:
            List of repository dictionaries with student information
        """
        logger.info(f"Fetching repositories for assignment {assignment_id}")

        # GitHub Classroom API endpoint for assignment accepted_assignments
        response = self._make_request(
            "GET", f"/assignments/{assignment_id}/accepted_assignments")
        accepted_assignments = response.json()

        # Extract repository information
        repositories = []
        for assignment in accepted_assignments:
            if "repository" in assignment:
                repo_info = {
                    "repository": assignment["repository"],
                    "student": assignment.get("student", {}),
                    "assignment": assignment,
                    "url": assignment["repository"]["html_url"],
                    "clone_url": assignment["repository"]["clone_url"],
                    "ssh_url": assignment["repository"]["ssh_url"]
                }
                repositories.append(repo_info)

        logger.info(f"Found {len(repositories)} student repositories")
        return repositories

    def get_assignment_metadata(self, classroom_url: str, github_organization: str) -> Dict:
        """
        Get comprehensive assignment metadata from GitHub Classroom.

        Args:
            classroom_url: GitHub Classroom assignment URL
            github_organization: GitHub organization name

        Returns:
            Dictionary with comprehensive assignment metadata
        """
        metadata = {
            'assignment': None,
            'classroom': None,
            'organization': None,
            'template_repository': None,
            'student_count': 0,
            'deadline': None,
            'assignment_type': 'individual',
            'max_teams': None,
            'max_members': None,
            'status': 'active'
        }

        try:
            # Parse the classroom URL to get classroom ID and assignment info
            parsed_url = self._parse_classroom_url_extended(classroom_url)

            # Get all accessible classrooms
            classrooms = self.get_classrooms()

            # Find the specific classroom
            target_classroom = None
            for classroom in classrooms:
                org_login = classroom.get("organization", {}).get("login")
                if org_login == github_organization:
                    # Check if this is the right classroom by ID if available
                    if parsed_url.get('classroom_id'):
                        _classroom_name = classroom.get('name', '')
                        if parsed_url['classroom_id'] in str(classroom.get('id', '')):
                            target_classroom = classroom
                            break
                    else:
                        target_classroom = classroom
                        break

            if not target_classroom:
                logger.warning(
                    f"Classroom not found for organization: {github_organization}")
                return metadata

            metadata['classroom'] = target_classroom
            metadata['organization'] = target_classroom.get("organization", {})

            # Get assignments for this classroom
            assignments = self.get_classroom_assignments(
                target_classroom["id"])

            # Find the specific assignment
            assignment_name = parsed_url.get('assignment_name', '')
            target_assignment = None

            for assignment in assignments:
                assignment_slug = assignment.get("slug", "")
                assignment_title = assignment.get("title", "")
                if (assignment_name in assignment_slug or
                    assignment_slug in assignment_name or
                        assignment_name in assignment_title.lower()):
                    target_assignment = assignment
                    break

            if target_assignment:
                metadata['assignment'] = target_assignment
                metadata['deadline'] = target_assignment.get('deadline')
                metadata['assignment_type'] = 'group' if target_assignment.get(
                    'max_teams', 1) > 1 else 'individual'
                metadata['max_teams'] = target_assignment.get('max_teams')
                metadata['max_members'] = target_assignment.get('max_members')

                # Get student count
                try:
                    accepted_assignments = self.get_assignment_repositories(
                        target_assignment['id'])
                    metadata['student_count'] = len(accepted_assignments)
                except Exception as e:
                    logger.debug(f"Could not get student count: {e}")

                # Try to get template repository info
                try:
                    template_repo_url = self._infer_template_repository(
                        github_organization, assignment_name, target_assignment)
                    if template_repo_url:
                        metadata['template_repository'] = self._get_repository_info(
                            template_repo_url)
                except Exception as e:
                    logger.debug(
                        f"Could not get template repository info: {e}")

            return metadata

        except Exception as e:
            logger.error(f"Error getting assignment metadata: {e}")
            return metadata

    def _parse_classroom_url_extended(self, url: str) -> Dict:
        """Extended URL parsing to extract more details."""
        result = {'classroom_id': '', 'assignment_name': ''}

        # Pattern: https://classroom.github.com/classrooms/ID/assignments/NAME
        full_pattern = r'classroom\.github\.com/classrooms/([^/]+)/assignments/([^/?]+)'
        match = re.search(full_pattern, url)
        if match:
            result['classroom_id'] = match.group(1)
            result['assignment_name'] = match.group(2)

        return result

    def _infer_template_repository(self, organization: str, assignment_name: str, assignment_data: Dict) -> str:
        """Infer template repository URL from assignment data."""
        # Common template repository naming patterns
        possible_names = [
            f"{assignment_name}-template",
            f"{assignment_name}",
            f"template-{assignment_name}",
            assignment_data.get('slug', '') + '-template'
        ]

        for name in possible_names:
            if name:
                template_url = f"https://github.com/{organization}/{name}"
                # We could validate this exists, but for now just return the most likely one
                return template_url

        return None

    def _get_repository_info(self, repo_url: str) -> Dict:
        """Get repository information from GitHub API."""
        try:
            # Extract owner/repo from URL
            match = re.search(r'github\.com/([^/]+)/([^/?]+)', repo_url)
            if not match:
                return {}

            owner, repo = match.groups()
            repo = repo.replace('.git', '')  # Remove .git suffix if present

            response = self._make_request("GET", f"/repos/{owner}/{repo}")
            repo_data = response.json()

            return {
                'name': repo_data.get('name'),
                'description': repo_data.get('description'),
                'language': repo_data.get('language'),
                'topics': repo_data.get('topics', []),
                'created_at': repo_data.get('created_at'),
                'updated_at': repo_data.get('updated_at'),
                'default_branch': repo_data.get('default_branch'),
                'clone_url': repo_data.get('clone_url'),
                'ssh_url': repo_data.get('ssh_url')
            }
        except Exception as e:
            logger.debug(f"Could not get repository info: {e}")
            return {}

    def find_assignment_by_url(self, classroom_url: str, github_organization: str) -> Optional[Dict]:
        """
        Find assignment details by classroom URL and organization.

        This method attempts to find the assignment by:
        1. Looking for assignments in the specified organization
        2. Matching against the classroom URL pattern

        Args:
            classroom_url: GitHub Classroom assignment URL
            github_organization: GitHub organization name

        Returns:
            Assignment dictionary if found, None otherwise
        """
        try:
            assignment_id, _ = self.parse_classroom_url(classroom_url)
            logger.info(
                f"Looking for assignment with ID pattern: {assignment_id}")

            # Get all accessible classrooms
            classrooms = self.get_classrooms()

            # Look for classrooms in the specified organization
            for classroom in classrooms:
                if classroom.get("organization", {}).get("login") == github_organization:
                    logger.debug(
                        f"Checking classroom: {classroom.get('name')}")

                    # Get assignments for this classroom
                    assignments = self.get_classroom_assignments(
                        classroom["id"])

                    # Look for assignment matching the URL pattern
                    for assignment in assignments:
                        # GitHub Classroom assignments often have URLs with specific patterns
                        # We'll look for assignments that could match our URL
                        assignment_slug = assignment.get("slug", "")
                        if assignment_id in assignment_slug or assignment_slug in assignment_id:
                            logger.info(
                                f"Found matching assignment: {assignment.get('title')}")
                            return assignment

            logger.warning(f"Assignment not found for URL: {classroom_url}")
            return None

        except Exception as e:
            logger.error(f"Error finding assignment: {e}")
            return None

    def discover_student_repositories(self, classroom_url: str, github_organization: str,
                                      exclude_template: bool = True) -> List[str]:
        """
        Discover all student repositories for a classroom assignment using organization API.

        This method uses the same approach as the repository fetch functionality:
        1. Extract assignment name from classroom URL or use organization pattern
        2. List all repositories in the organization
        3. Filter by assignment prefix pattern
        4. Return student repository URLs

        Args:
            classroom_url: GitHub Classroom assignment URL (for pattern extraction)
            github_organization: GitHub organization name
            exclude_template: Whether to exclude template repositories

        Returns:
            List of repository URLs
        """
        try:
            # Check token expiration first
            logger.debug("Checking GitHub token expiration...")
            expiration_info = self.check_token_expiration()

            if expiration_info.get('is_expired'):
                logger.error("❌ GitHub token has EXPIRED!")
                logger.error(
                    f"Expired on: {expiration_info.get('expires_at', 'unknown date')}")
                logger.error("")
                logger.error("🔧 To fix this issue:")
                logger.error(
                    "  1. Generate a new token at: https://github.com/settings/tokens")
                logger.error("  2. Select these scopes:")
                logger.error(
                    "     ✓ repo (Full control of private repositories)")
                logger.error("     ✓ read:org (Read organization data)")
                logger.error("  3. Update your token:")
                logger.error(
                    "     classdock config set-token <your-new-token>")
                logger.error("")
                raise GitHubClassroomAPIError(
                    "GitHub token has expired. Please generate a new token and update it using 'classdock config set-token'",
                    status_code=401
                )

            if not expiration_info.get('is_valid'):
                error_msg = expiration_info.get('error', 'Unknown error')
                logger.error(f"❌ GitHub token validation failed: {error_msg}")
                logger.error("")
                logger.error("🔧 To fix this issue:")
                logger.error("  1. Verify your token is correct")
                logger.error(
                    "  2. Generate a new token if needed: https://github.com/settings/tokens")
                logger.error("  3. Update your token:")
                logger.error(
                    "     classdock config set-token <your-token>")
                logger.error("")
                raise GitHubClassroomAPIError(
                    f"GitHub token is invalid: {error_msg}",
                    status_code=401
                )

            # Log token status
            if expiration_info.get('days_remaining') is not None:
                days = expiration_info['days_remaining']
                if days <= 7:
                    logger.warning(f"⚠️ GitHub token expires in {days} days!")
                    logger.warning("Consider generating a new token soon.")
                elif days <= 30:
                    logger.info(f"ℹ️ GitHub token expires in {days} days")
                else:
                    logger.debug(f"✓ Token valid for {days} more days")
            else:
                logger.debug(
                    "✓ Token is valid (classic token with no expiration)")

            # Validate token scopes before attempting to list repos
            logger.debug("Validating GitHub token scopes...")
            scope_info = self.validate_token_scopes()

            if not scope_info.get('valid'):
                logger.error("❌ GitHub token validation failed")
                if 'error' in scope_info:
                    logger.error(f"Error: {scope_info['error']}")
                return []

            # Check if token has required scopes
            if not scope_info.get('has_read_org'):
                logger.warning("⚠️ Token may lack 'read:org' or 'repo' scope")
                logger.warning("Current scopes: " +
                               ", ".join(scope_info.get('scopes', [])))
                logger.info("Attempting to list repositories anyway...")
            else:
                logger.debug(
                    f"✓ Token has valid scopes: {', '.join(scope_info.get('scopes', []))}")

            # Extract assignment prefix from classroom URL
            assignment_prefix = self._extract_assignment_prefix(classroom_url)
            if not assignment_prefix:
                logger.warning(
                    "Could not extract assignment prefix from classroom URL")
                logger.info(
                    "Will attempt to discover repositories using organization listing")

            logger.info(
                f"Discovering repositories with prefix: {assignment_prefix}")
            logger.info(f"From organization: {github_organization}")

            # Get all repositories from the organization
            repositories = self._get_organization_repositories(
                github_organization)

            # Filter repositories by assignment pattern
            student_repos = self._filter_student_repositories(
                repositories, assignment_prefix, exclude_template
            )

            logger.info(
                f"Discovered {len(student_repos)} student repositories")
            return student_repos

        except Exception as e:
            logger.error(f"Error discovering repositories: {e}")
            return []

    def _extract_assignment_prefix(self, classroom_url: str) -> Optional[str]:
        """
        Extract assignment prefix from classroom URL.

        Supports various GitHub Classroom URL formats:
        - https://classroom.github.com/classrooms/ID/assignments/ASSIGNMENT-NAME
        - https://classroom.github.com/a/ASSIGNMENT-ID

        Args:
            classroom_url: GitHub Classroom URL

        Returns:
            Assignment prefix/name if found, None otherwise
        """
        if not classroom_url:
            return None

        try:
            # Format 1: /classrooms/ID/assignments/ASSIGNMENT-NAME
            pattern1 = r'/assignments/([^/?]+)'
            match = re.search(pattern1, classroom_url)
            if match:
                return match.group(1)

            # Format 2: /a/ASSIGNMENT-ID
            pattern2 = r'/a/([^/?]+)'
            match = re.search(pattern2, classroom_url)
            if match:
                return match.group(1)

            logger.warning(
                f"Could not extract assignment prefix from URL: {classroom_url}")
            return None

        except Exception as e:
            logger.error(f"Error parsing classroom URL: {e}")
            return None

    def _get_organization_repositories(self, organization: str, per_page: int = 100) -> List[Dict]:
        """
        Get all repositories from a GitHub organization.

        Args:
            organization: GitHub organization name
            per_page: Number of repositories per page (max 100)

        Returns:
            List of repository dictionaries
        """
        repositories = []
        page = 1

        while True:
            logger.debug(f"Fetching organization repositories page {page}")

            response = self._make_request(
                "GET",
                f"/orgs/{organization}/repos",
                params={
                    "per_page": per_page,
                    "page": page,
                    "sort": "updated",
                    "direction": "desc"
                }
            )

            page_repos = response.json()
            if not page_repos:
                break

            repositories.extend(page_repos)

            # Check if we've received fewer than requested (last page)
            if len(page_repos) < per_page:
                break

            page += 1

            # Safety limit to prevent infinite loops
            if page > 50:  # Max 5000 repositories
                logger.warning(
                    "Reached maximum page limit for repository discovery")
                break

        logger.debug(
            f"Found {len(repositories)} total repositories in organization")
        return repositories

    def _filter_student_repositories(self, repositories: List[Dict], assignment_prefix: Optional[str],
                                     exclude_template: bool) -> List[str]:
        """
        Filter repositories to find student repositories.

        Args:
            repositories: List of repository dictionaries from GitHub API
            assignment_prefix: Assignment prefix to filter by
            exclude_template: Whether to exclude template repositories

        Returns:
            List of student repository URLs
        """
        student_repos = []
        template_repos = []

        for repo in repositories:
            repo_name = repo["name"]
            repo_url = repo["html_url"]

            # If no assignment prefix provided, try to find the most common pattern
            if not assignment_prefix:
                # Look for repositories that could be student repositories
                # (contain dashes and don't have obvious template/instructor keywords)
                if ("-" in repo_name and
                        not any(keyword in repo_name.lower() for keyword in ["template", "instructor", "classroom"])):
                    student_repos.append(repo_url)
                continue

            # Filter by assignment prefix
            if not repo_name.startswith(assignment_prefix):
                continue

            # Check if this is a template repository
            if repo_name.endswith("-template") or "template" in repo_name.lower():
                template_repos.append(repo_url)
                if not exclude_template:
                    student_repos.append(repo_url)
                continue

            # Skip classroom template copies
            if "classroom" in repo_name.lower() and "template" in repo_name.lower():
                continue

            # Skip instructor repositories if they contain "instructor"
            if exclude_template and "instructor" in repo_name.lower():
                continue

            # Student repositories should have the assignment prefix followed by a dash
            if repo_name.startswith(f"{assignment_prefix}-"):
                student_repos.append(repo_url)
                logger.debug(f"Found student repository: {repo_name}")

        # Log template repositories found
        if template_repos:
            logger.info(f"Found {len(template_repos)} template repositories")
            for template_url in template_repos[:3]:  # Show first 3
                logger.debug(f"Template repository: {template_url}")

        return student_repos


def create_classroom_api_client(github_token: str) -> GitHubClassroomAPI:
    """
    Create and return a GitHub Classroom API client.

    Args:
        github_token: GitHub personal access token

    Returns:
        GitHubClassroomAPI client instance
    """
    return GitHubClassroomAPI(github_token)
