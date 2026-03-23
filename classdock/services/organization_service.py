"""
Organization service layer for ClassDock.

Provides high-level operations consumed by CLI commands:
- Running the interactive setup wizard
- Listing the user's GitHub organizations
- Batch-cloning templates between organizations

This service is thin — it delegates to OrganizationManager,
TemplateManager, and OrganizationSetupWizard.
"""

import logging
from typing import List, Optional, Tuple

from ..organizations.manager import OrganizationManager
from ..organizations.models import CloneResult, Organization, SetupResult
from ..organizations.templates import TemplateManager
from ..organizations.wizard import OrganizationSetupWizard

logger = logging.getLogger(__name__)


class OrganizationService:
    """
    Service for organization lifecycle management.

    Args:
        token: GitHub personal access token. Falls back to GITHUB_TOKEN env var.
        dry_run: When True, no side effects are performed.
        verbose: Enable verbose logging.
        wizard_factory: Optional callable returning an OrganizationSetupWizard.
                        Used for dependency injection in tests.
    """

    def __init__(
        self,
        token: Optional[str] = None,
        dry_run: bool = False,
        verbose: bool = False,
        wizard_factory=None,
    ):
        self.token = token
        self.dry_run = dry_run
        self.verbose = verbose
        self._org_manager = OrganizationManager(token=token)
        self._template_manager = TemplateManager(token=token)

        if wizard_factory is not None:
            self._wizard_factory = wizard_factory
        else:
            self._wizard_factory = lambda: OrganizationSetupWizard(
                token=token, dry_run=dry_run
            )

    # ------------------------------------------------------------------
    # Wizard
    # ------------------------------------------------------------------

    def setup(self) -> Tuple[bool, str]:
        """
        Run the interactive organization setup wizard.

        Returns:
            (success: bool, message: str)
        """
        wizard = self._wizard_factory()
        try:
            result: SetupResult = wizard.run()
            if result.success:
                org_url = (
                    f"https://github.com/{result.organization.login}"
                    if result.organization
                    else "N/A"
                )
                return True, f"Organization setup complete. GitHub org: {org_url}"
            return False, result.error_message or "Setup did not complete."
        except Exception as exc:
            logger.error("Organization setup failed: %s", exc)
            return False, str(exc)

    # ------------------------------------------------------------------
    # Organization listing
    # ------------------------------------------------------------------

    def list_organizations(self) -> List[Organization]:
        """
        Return the GitHub organizations the authenticated user belongs to.

        Returns:
            List of Organization objects, sorted alphabetically by login.
        """
        return self._org_manager.list_user_organizations()

    def verify_organization(self, login: str) -> Tuple[bool, Optional[Organization]]:
        """
        Verify that an organization exists and return its details.

        Args:
            login: Organization login to verify.

        Returns:
            (exists: bool, organization: Organization | None)
        """
        org = self._org_manager.get_organization(login)
        return (org is not None, org)

    # ------------------------------------------------------------------
    # Template cloning
    # ------------------------------------------------------------------

    def clone_templates(
        self,
        source_org: str,
        target_org: str,
        repo_names: List[str],
    ) -> CloneResult:
        """
        Fork a list of template repositories from source_org into target_org.

        After forking, each repository is marked as a GitHub template
        (``is_template = true``).

        Args:
            source_org: Organization to fork repos from.
            target_org: Organization to fork repos into.
            repo_names: Names of repos to fork. If empty, all template repos
                        in source_org are used.

        Returns:
            CloneResult with success/failure counts and details.
        """
        if not repo_names:
            templates = self._template_manager.list_org_templates(source_org)
            repo_names = [t.name for t in templates]
            logger.debug(
                "No repos specified; resolved %d template(s) from '%s'",
                len(repo_names),
                source_org,
            )

        if self.dry_run:
            logger.info(
                "[dry-run] Would fork %d repo(s) from '%s' → '%s'",
                len(repo_names),
                source_org,
                target_org,
            )
            result = CloneResult(total=len(repo_names))
            return result

        return self._template_manager.clone_templates(
            source_org=source_org,
            target_org=target_org,
            repo_names=repo_names,
        )
