"""
GitHub Organization Manager.

Handles CRUD operations for GitHub organizations:
- Listing organizations the user belongs to
- Checking whether an organization exists
- Creating organizations (via GraphQL)
- Fetching organization details

All REST operations reuse the shared GitHubAPIClient.
Organization creation uses the GitHubGraphQLClient because the
REST API does not expose an endpoint for creating organizations.
"""

import logging
from typing import List, Optional

from ..utils.github_api_client import GitHubAPIClient
from ..utils.github_graphql_client import GitHubGraphQLClient
from .models import Organization

logger = logging.getLogger(__name__)


class OrganizationManager:
    """
    Manages GitHub organization lifecycle operations.

    Args:
        token: GitHub personal access token. Falls back to GITHUB_TOKEN env var.
    """

    def __init__(self, token: Optional[str] = None):
        self._rest = GitHubAPIClient(token=token)
        self._graphql = GitHubGraphQLClient(token=token)

    # ------------------------------------------------------------------
    # Listing and discovery
    # ------------------------------------------------------------------

    def list_user_organizations(self) -> List[Organization]:
        """
        Return all GitHub organizations the authenticated user belongs to.

        Returns:
            List of Organization objects, sorted by login.
        """
        raw = self._rest.list_user_organizations()
        orgs = [Organization.from_dict(d) for d in raw]
        orgs.sort(key=lambda o: o.login.lower())
        logger.debug("Found %d user organizations", len(orgs))
        return orgs

    def get_organization(self, login: str) -> Optional[Organization]:
        """
        Fetch a single organization by login.

        Args:
            login: Organization login (slug).

        Returns:
            Organization if found, None otherwise.
        """
        raw = self._rest.get_organization(login)
        if raw is None:
            return None
        return Organization.from_dict(raw)

    def organization_exists(self, login: str) -> bool:
        """
        Check whether an organization with the given login exists on GitHub.

        Args:
            login: Organization login to check.

        Returns:
            True if the organization exists, False otherwise.
        """
        return self._rest.organization_exists(login)

    # ------------------------------------------------------------------
    # Creation
    # ------------------------------------------------------------------

    def create_organization(
        self,
        login: str,
        billing_email: str,
        display_name: Optional[str] = None,
    ) -> Organization:
        """
        Create a new GitHub organization via the GraphQL API.

        This requires the ``admin:org`` OAuth scope on the token.
        If the scope is missing, an informative error is raised before
        making the API call.

        Args:
            login: The organization slug (e.g., SOC-CS3030-Valle-SU26).
            billing_email: Billing contact email for the new organization.
            display_name: Human-readable name for the organization.
                          Falls back to login if not provided.

        Returns:
            Organization object representing the newly created org.

        Raises:
            PermissionError: If the token lacks the ``admin:org`` scope.
            RuntimeError: If the organization creation fails for other reasons.
        """
        # Pre-flight: verify required token scope
        if not self._graphql.has_scope("admin:org"):
            scopes = self._graphql.get_token_scopes()
            raise PermissionError(
                f"GitHub token is missing the 'admin:org' scope.\n"
                f"Current scopes: {', '.join(scopes) or 'none'}\n\n"
                f"To fix:\n"
                f"  1. Visit https://github.com/settings/tokens\n"
                f"  2. Select your ClassDock token\n"
                f"  3. Enable the 'admin:org' scope\n"
                f"  4. Re-save the token with: classdock config token <NEW_TOKEN>"
            )

        logger.info("Creating GitHub organization '%s'", login)
        try:
            org_data = self._graphql.create_organization(
                login=login,
                billing_email=billing_email,
            )
        except Exception as exc:
            msg = str(exc)
            # GitHub's GraphQL `createOrganization` mutation is only available on
            # GitHub Enterprise Cloud/Server — not on github.com personal/pro accounts.
            if "doesn't exist on type 'Mutation'" in msg or "createOrganization" in msg:
                raise NotImplementedError(
                    "GitHub does not support programmatic organization creation via API "
                    "for non-Enterprise accounts.\n\n"
                    "Please create the organization manually:\n"
                    f"  1. Go to https://github.com/organizations/plan\n"
                    f"  2. Choose a free plan\n"
                    f"  3. Set the organization name to: {login}\n"
                    f"  4. Re-run this command or use: classdock organizations clone-templates"
                ) from exc
            raise

        org = Organization(
            login=org_data.get("login", login),
            name=display_name or org_data.get("name") or login,
            url=org_data.get("url"),
        )
        logger.info("Organization '%s' created: %s", login, org.url)
        return org

    # ------------------------------------------------------------------
    # Token scope helpers (exposed for the wizard)
    # ------------------------------------------------------------------

    def get_token_scopes(self) -> List[str]:
        """Return the OAuth scopes of the current token."""
        return self._graphql.get_token_scopes()

    def has_required_scopes(self) -> bool:
        """
        Check that the token has all scopes required for the full wizard.

        Required scopes: repo, read:org, admin:org
        """
        scopes = set(self.get_token_scopes())
        required = {"repo", "admin:org"}
        return required.issubset(scopes)
