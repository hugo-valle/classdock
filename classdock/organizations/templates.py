"""
Template repository management for organization setup.

Handles:
- Listing template repositories in a GitHub organization
- Forking repositories from one org to another
- Configuring forked repositories as GitHub templates
- Batch cloning with progress tracking
"""

import logging
import time
from typing import Callable, List, Optional

from ..utils.github_api_client import GitHubAPIClient
from ..utils.github_exceptions import RepoAlreadyExistsError
from .models import CloneResult, TemplateRepo

logger = logging.getLogger(__name__)

# Seconds to wait after forking before marking a repo as template.
# GitHub's fork API is asynchronous; the repo may not be fully ready immediately.
_FORK_SETTLE_SECONDS = 3


class TemplateManager:
    """
    Manages template repository operations between GitHub organizations.

    Args:
        token: GitHub personal access token.
    """

    def __init__(self, token: Optional[str] = None):
        self._api = GitHubAPIClient(token=token)

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def list_org_templates(self, org_login: str) -> List[TemplateRepo]:
        """
        Return all repositories in an org that are marked as GitHub templates.

        Args:
            org_login: Organization login to search.

        Returns:
            Sorted list of TemplateRepo objects.
        """
        raw = self._api.list_org_repos(org_login, templates_only=True)
        repos = [TemplateRepo.from_dict(r) for r in raw]
        repos.sort(key=lambda r: r.name.lower())
        logger.debug(
            "Found %d template repos in '%s'", len(repos), org_login
        )
        return repos

    def list_org_repos(
        self, org_login: str, templates_only: bool = False
    ) -> List[TemplateRepo]:
        """
        Return all repositories in an org.

        Args:
            org_login: Organization login.
            templates_only: If True, return only template repos.

        Returns:
            Sorted list of TemplateRepo objects.
        """
        raw = self._api.list_org_repos(org_login, templates_only=templates_only)
        repos = [TemplateRepo.from_dict(r) for r in raw]
        repos.sort(key=lambda r: r.name.lower())
        return repos

    # ------------------------------------------------------------------
    # Individual repo operations
    # ------------------------------------------------------------------

    def copy_template_repository(
        self,
        source_owner: str,
        repo_name: str,
        target_org: str,
        new_name: Optional[str] = None,
        private: bool = True,
    ) -> Optional[TemplateRepo]:
        """
        Create a new repository in target_org from a GitHub template repository.

        Uses the "generate from template" API which works even when forking is
        disabled on the source repo.  The source repo must be marked as a GitHub
        template (``is_template: true``).

        Falls back to the fork API if the generate endpoint returns 404
        (e.g., the repo is not marked as a template).

        Args:
            source_owner: Source org/user login.
            repo_name: Repository name in the source org.
            target_org: Target organization login.
            new_name: Name for the new repo (defaults to repo_name).
            private: Whether the created repo should be private.

        Returns:
            TemplateRepo representing the new repo, or None on failure.
        """
        dest_name = new_name or repo_name

        # Primary: generate from template
        raw = self._api.create_from_template(
            template_owner=source_owner,
            template_repo=repo_name,
            target_owner=target_org,
            new_name=dest_name,
            private=private,
        )

        if raw is not None:
            return TemplateRepo.from_dict(raw)

        # Fallback: try fork (for repos not marked as templates)
        logger.debug(
            "generate-from-template returned None for '%s/%s'; falling back to fork.",
            source_owner, repo_name,
        )
        raw = self._api.fork_repository(
            owner=source_owner,
            repo=repo_name,
            target_org=target_org,
            new_name=new_name,
        )
        if raw is None:
            return None
        return TemplateRepo.from_dict(raw)

    def fork_repository(
        self,
        source_owner: str,
        repo_name: str,
        target_org: str,
        new_name: Optional[str] = None,
    ) -> Optional[TemplateRepo]:
        """Fork a single repository into the target organization (legacy path)."""
        raw = self._api.fork_repository(
            owner=source_owner,
            repo=repo_name,
            target_org=target_org,
            new_name=new_name,
        )
        if raw is None:
            return None
        return TemplateRepo.from_dict(raw)

    def make_template(self, owner: str, repo_name: str) -> bool:
        """
        Mark a repository as a GitHub template (``is_template = true``).

        Args:
            owner: Repository owner login.
            repo_name: Repository name.

        Returns:
            True if the update succeeded.
        """
        return self._api.set_repository_template(owner, repo_name, is_template=True)

    # ------------------------------------------------------------------
    # Batch operations
    # ------------------------------------------------------------------

    def clone_templates(
        self,
        source_org: str,
        target_org: str,
        repo_names: List[str],
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        settle_seconds: float = _FORK_SETTLE_SECONDS,
    ) -> CloneResult:
        """
        Fork a list of template repositories from source_org into target_org,
        then configure each forked repo as a GitHub template.

        Args:
            source_org: Organization login to fork repos from.
            target_org: Organization login to fork repos into.
            repo_names: Names of repositories to fork.
            progress_callback: Optional callback called after each repo with
                               (current_index, total, repo_name). Useful for
                               displaying a progress bar.
            settle_seconds: Seconds to wait after each fork before setting the
                            template flag (the fork API is async).

        Returns:
            CloneResult summarising successes and failures.
        """
        result = CloneResult(total=len(repo_names), attempted_names=list(repo_names))

        for idx, name in enumerate(repo_names, start=1):
            if progress_callback:
                progress_callback(idx, len(repo_names), name)

            logger.debug(
                "Copying '%s/%s' → '%s' (%d/%d)",
                source_org,
                name,
                target_org,
                idx,
                len(repo_names),
            )

            try:
                repo = self.copy_template_repository(
                    source_owner=source_org,
                    repo_name=name,
                    target_org=target_org,
                )
            except RepoAlreadyExistsError:
                logger.debug("'%s/%s' already exists; skipping.", target_org, name)
                result.add_already_existed(name)
                continue

            if repo is None:
                error_msg = f"Failed to fork '{source_org}/{name}' into '{target_org}'"
                logger.error(error_msg)
                result.add_failure(error_msg)
                continue

            # Allow GitHub to finish setting up the fork before patching it.
            if settle_seconds > 0:
                time.sleep(settle_seconds)

            # Mark as a GitHub template repository
            template_ok = self.make_template(owner=target_org, repo_name=repo.name)
            if not template_ok:
                logger.warning(
                    "Forked '%s' but could not set is_template flag on '%s/%s'",
                    name,
                    target_org,
                    repo.name,
                )
                # Still count as success — the fork worked, template flag is cosmetic
                repo.is_template = False
            else:
                repo.is_template = True

            result.add_success(repo)
            logger.debug("Cloned and configured '%s/%s'", target_org, repo.name)

        logger.debug(
            "Batch clone complete: %d cloned, %d already existed, %d failed",
            result.successful,
            len(result.already_existed),
            result.failed,
        )
        return result
