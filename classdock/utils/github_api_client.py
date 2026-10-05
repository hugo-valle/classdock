"""
GitHub REST API client for organization, repository and template operations.
"""

import logging
import os
from typing import Dict, List, Optional

import requests

from .github_exceptions import RepoAlreadyExistsError

logger = logging.getLogger(__name__)


class GitHubAPIClient:
    """Client for the GitHub REST API."""

    def __init__(self, token: Optional[str] = None):
        """
        Initialize the GitHub API client.

        Args:
            token: GitHub token. If None, will try to get from GITHUB_TOKEN env var.
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError(
                "GitHub token is required. Set GITHUB_TOKEN environment variable or pass token parameter."
            )

        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "classdock",
        }
        self.base_url = "https://api.github.com"

    def verify_token(self) -> bool:
        """
        Verify that the GitHub token is valid.

        Returns:
            bool: True if token is valid, False otherwise.
        """
        try:
            response = requests.get(
                f"{self.base_url}/user", headers=self.headers, timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to verify GitHub token: {e}")
            return False

    def list_user_organizations(self) -> List[Dict]:
        """
        List GitHub organizations the authenticated user belongs to.

        Returns:
            List of organization dicts with at minimum 'login', 'id', and 'url' keys.
        """
        orgs = []
        page = 1
        while True:
            try:
                response = requests.get(
                    f"{self.base_url}/user/orgs",
                    headers=self.headers,
                    params={"per_page": 100, "page": page},
                    timeout=30,
                )
                if response.status_code != 200:
                    logger.error(
                        "Failed to list user orgs: %s %s",
                        response.status_code,
                        response.text[:200],
                    )
                    break
                page_data = response.json()
                if not page_data:
                    break
                orgs.extend(page_data)
                page += 1
                if len(page_data) < 100:
                    break
            except Exception as exc:
                logger.error("Error fetching user organizations: %s", exc)
                break
        return orgs

    def get_organization(self, org_login: str) -> Optional[Dict]:
        """
        Fetch a single organization's details.

        Args:
            org_login: Organization login (slug).

        Returns:
            Organization dict, or None if not found / inaccessible.
        """
        try:
            response = requests.get(
                f"{self.base_url}/orgs/{org_login}",
                headers=self.headers,
                timeout=30,
            )
            if response.status_code == 404:
                return None
            if response.status_code != 200:
                logger.error(
                    "Failed to fetch org '%s': %s", org_login, response.status_code
                )
                return None
            return response.json()
        except Exception as exc:
            logger.error("Error fetching organization '%s': %s", org_login, exc)
            return None

    def organization_exists(self, org_login: str) -> bool:
        """Return True if the organization exists on GitHub."""
        return self.get_organization(org_login) is not None

    def list_org_repos(
        self,
        org_login: str,
        repo_type: str = "all",
        templates_only: bool = False,
    ) -> List[Dict]:
        """
        List repositories in a GitHub organization.

        Args:
            org_login: Organization login.
            repo_type: 'all', 'public', 'private', 'forks', or 'sources'.
            templates_only: If True, return only repos marked as templates.

        Returns:
            List of repository dicts.
        """
        repos = []
        page = 1
        while True:
            try:
                response = requests.get(
                    f"{self.base_url}/orgs/{org_login}/repos",
                    headers=self.headers,
                    params={"type": repo_type, "per_page": 100, "page": page},
                    timeout=30,
                )
                if response.status_code != 200:
                    logger.error(
                        "Failed to list repos for '%s': %s %s",
                        org_login,
                        response.status_code,
                        response.text[:200],
                    )
                    break
                page_data = response.json()
                if not page_data:
                    break
                repos.extend(page_data)
                page += 1
                if len(page_data) < 100:
                    break
            except Exception as exc:
                logger.error("Error listing repos for org '%s': %s", org_login, exc)
                break

        if templates_only:
            repos = [r for r in repos if r.get("is_template", False)]
        return repos

    def fork_repository(
        self,
        owner: str,
        repo: str,
        target_org: str,
        new_name: Optional[str] = None,
    ) -> Optional[Dict]:
        """
        Fork a repository into a target organization.

        Uses ``POST /repos/{owner}/{repo}/forks``.

        Args:
            owner: Source repository owner (org or user login).
            repo: Source repository name.
            target_org: Organization login to fork into.
            new_name: Optional new name for the forked repository.

        Returns:
            Dict with the forked repository data, or None on failure.
        """
        payload: Dict = {"organization": target_org}
        if new_name:
            payload["name"] = new_name

        try:
            response = requests.post(
                f"{self.base_url}/repos/{owner}/{repo}/forks",
                headers=self.headers,
                json=payload,
                timeout=60,
            )
            if response.status_code in (202, 200):
                logger.info("Forked '%s/%s' into '%s'", owner, repo, target_org)
                return response.json()
            logger.error(
                "Fork failed for '%s/%s' → '%s': HTTP %s %s",
                owner,
                repo,
                target_org,
                response.status_code,
                response.text[:300],
            )
            return None
        except Exception as exc:
            logger.error(
                "Error forking '%s/%s' into '%s': %s", owner, repo, target_org, exc
            )
            return None

    def create_from_template(
        self,
        template_owner: str,
        template_repo: str,
        target_owner: str,
        new_name: str,
        private: bool = True,
        description: Optional[str] = None,
        include_all_branches: bool = False,
    ) -> Optional[Dict]:
        """
        Create a new repository from a GitHub template repository.

        Uses ``POST /repos/{template_owner}/{template_repo}/generate``.
        This is the correct approach for template repos — it works even when
        forking is disabled, and creates a clean copy with no fork relationship.

        Args:
            template_owner: Owner of the template repository.
            template_repo: Name of the template repository.
            target_owner: Organization or user that will own the new repo.
            new_name: Name for the newly created repository.
            private: Whether the new repository should be private.
            description: Optional repository description.
            include_all_branches: If True, copy all branches (not just default).

        Returns:
            Dict with the new repository data, or None on failure.
        """
        payload: Dict = {
            "owner": target_owner,
            "name": new_name,
            "private": private,
            "include_all_branches": include_all_branches,
        }
        if description:
            payload["description"] = description

        headers = {**self.headers, "Accept": "application/vnd.github+json"}

        try:
            response = requests.post(
                f"{self.base_url}/repos/{template_owner}/{template_repo}/generate",
                headers=headers,
                json=payload,
                timeout=60,
            )
            if response.status_code in (201, 200):
                logger.info(
                    "Created '%s/%s' from template '%s/%s'",
                    target_owner,
                    new_name,
                    template_owner,
                    template_repo,
                )
                return response.json()
            if response.status_code == 422:
                body = response.text
                if "already exists" in body.lower():
                    logger.debug(
                        "'%s/%s' already exists in '%s'; skipping.",
                        target_owner,
                        new_name,
                        target_owner,
                    )
                    raise RepoAlreadyExistsError(
                        f"'{target_owner}/{new_name}' already exists",
                        repository_name=new_name,
                        operation="create_from_template",
                    )
            logger.error(
                "create_from_template failed for '%s/%s' → '%s/%s': HTTP %s %s",
                template_owner,
                template_repo,
                target_owner,
                new_name,
                response.status_code,
                response.text[:300],
            )
            return None
        except RepoAlreadyExistsError:
            raise
        except Exception as exc:
            logger.error(
                "Error creating '%s/%s' from template '%s/%s': %s",
                target_owner,
                new_name,
                template_owner,
                template_repo,
                exc,
            )
            return None

    def set_repository_template(
        self, owner: str, repo: str, is_template: bool = True
    ) -> bool:
        """
        Set or clear the ``is_template`` flag on a repository.

        Uses ``PATCH /repos/{owner}/{repo}``.

        Args:
            owner: Repository owner.
            repo: Repository name.
            is_template: True to mark as template, False to clear.

        Returns:
            True if the update succeeded, False otherwise.
        """
        try:
            response = requests.patch(
                f"{self.base_url}/repos/{owner}/{repo}",
                headers=self.headers,
                json={"is_template": is_template},
                timeout=30,
            )
            if response.status_code == 200:
                logger.info("Set is_template=%s on '%s/%s'", is_template, owner, repo)
                return True
            logger.error(
                "Failed to set is_template on '%s/%s': HTTP %s %s",
                owner,
                repo,
                response.status_code,
                response.text[:300],
            )
            return False
        except Exception as exc:
            logger.error("Error setting template flag on '%s/%s': %s", owner, repo, exc)
            return False
