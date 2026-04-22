"""
GitHub GraphQL API Client.

Provides a thin wrapper around GitHub's GraphQL endpoint
(https://api.github.com/graphql) for operations not available
via the REST API — primarily organization creation.

Note:
    Organization creation via GraphQL requires the `admin:org` token scope.
    Personal access tokens must include this scope. If the mutation fails
    with a permission error, the wizard will fall back to manual guidance.
"""

import logging
import os
from typing import Any, Dict, Optional

import requests

from .github_exceptions import GitHubAPIError, GitHubAuthenticationError

logger = logging.getLogger(__name__)

GRAPHQL_ENDPOINT = "https://api.github.com/graphql"

# GraphQL mutation for creating a GitHub organization.
# Requires admin:org scope on the authenticated token.
_CREATE_ORG_MUTATION = """
mutation CreateOrganization($login: String!, $adminLogins: [String!]!, $billingEmail: String!) {
  createOrganization(input: {
    login: $login
    adminLogins: $adminLogins
    billingEmail: $billingEmail
  }) {
    organization {
      id
      login
      name
      url
    }
  }
}
"""

_VIEWER_SCOPES_QUERY = """
query ViewerScopes {
  viewer {
    login
  }
}
"""


class GitHubGraphQLClient:
    """
    Minimal GraphQL client for the GitHub API.

    Only used for mutations/queries not available in the REST API.
    For standard operations (repo listing, forking, etc.) prefer
    the REST-based GitHubAPIClient.
    """

    def __init__(self, token: Optional[str] = None):
        """
        Initialize the client.

        Args:
            token: GitHub personal access token. Falls back to
                   the GITHUB_TOKEN environment variable.

        Raises:
            ValueError: If no token is provided or found in environment.
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError(
                "GitHub token is required. "
                "Set the GITHUB_TOKEN environment variable or pass token= explicitly."
            )

        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"bearer {self.token}",
                "Content-Type": "application/json",
                "User-Agent": "classdock",
            }
        )

    # ------------------------------------------------------------------
    # Core request
    # ------------------------------------------------------------------

    def execute(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a GraphQL query or mutation against GitHub's API.

        Args:
            query: GraphQL query/mutation string
            variables: Optional variables dict

        Returns:
            Parsed JSON response (the ``data`` key from the GraphQL response)

        Raises:
            GitHubAuthenticationError: On 401 / missing scope errors
            GitHubAPIError: On non-200 HTTP status or GraphQL errors
        """
        payload: Dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables

        try:
            response = self._session.post(GRAPHQL_ENDPOINT, json=payload, timeout=30)
        except requests.exceptions.ConnectionError as exc:
            raise GitHubAPIError(
                f"Network error connecting to GitHub GraphQL: {exc}"
            ) from exc
        except requests.exceptions.Timeout as exc:
            raise GitHubAPIError("GitHub GraphQL request timed out.") from exc

        if response.status_code == 401:
            raise GitHubAuthenticationError(
                "GitHub token is invalid or expired. "
                "Run `classdock config token` to update your token."
            )

        if response.status_code != 200:
            raise GitHubAPIError(
                f"GitHub GraphQL returned HTTP {response.status_code}: {response.text[:300]}"
            )

        body = response.json()

        if "errors" in body:
            errors = body["errors"]
            messages = "; ".join(e.get("message", str(e)) for e in errors)
            # Surface scope/permission errors distinctly
            if any("insufficient" in e.get("message", "").lower() for e in errors):
                raise GitHubAuthenticationError(
                    f"Insufficient token scopes for this operation. "
                    f"Ensure your token includes 'admin:org'. Details: {messages}"
                )
            raise GitHubAPIError(f"GitHub GraphQL errors: {messages}")

        return body.get("data", {})

    # ------------------------------------------------------------------
    # Organization operations
    # ------------------------------------------------------------------

    def create_organization(
        self,
        login: str,
        billing_email: str,
        admin_login: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new GitHub organization.

        Args:
            login: The organization login/slug (e.g., soc-cs3030-valle-su26)
            billing_email: Billing contact email for the organization
            admin_login: GitHub username to add as admin. Defaults to the
                         authenticated user's login (fetched automatically).

        Returns:
            Dict with organization fields: id, login, name, url

        Raises:
            GitHubAuthenticationError: If the token lacks ``admin:org`` scope
            GitHubAPIError: On API errors
        """
        if admin_login is None:
            admin_login = self._get_viewer_login()

        logger.debug("Creating GitHub organization '%s' via GraphQL", login)

        data = self.execute(
            _CREATE_ORG_MUTATION,
            variables={
                "login": login,
                "adminLogins": [admin_login],
                "billingEmail": billing_email,
            },
        )

        org_data = data.get("createOrganization", {}).get("organization", {})
        if not org_data:
            raise GitHubAPIError(
                f"Organization creation returned empty response. "
                f"The organization may have been created — verify at https://github.com/{login}"
            )

        logger.info("Organization '%s' created successfully", login)
        return org_data

    # ------------------------------------------------------------------
    # Token / viewer helpers
    # ------------------------------------------------------------------

    def get_token_scopes(self) -> list:
        """
        Return the OAuth scopes granted to the current token.

        GitHub returns the ``X-OAuth-Scopes`` header on any API response.
        We issue a lightweight REST HEAD request rather than a GraphQL query
        because the scopes header is only present on REST responses.

        Returns:
            List of scope strings (e.g., ['repo', 'read:org', 'admin:org'])
        """
        try:
            resp = self._session.head(
                "https://api.github.com/user",
                headers={"Authorization": f"bearer {self.token}"},
                timeout=10,
            )
            scopes_header = resp.headers.get("X-OAuth-Scopes", "")
            return [s.strip() for s in scopes_header.split(",") if s.strip()]
        except requests.exceptions.RequestException as exc:
            logger.warning("Could not fetch token scopes: %s", exc)
            return []

    def has_scope(self, scope: str) -> bool:
        """Check whether the current token has a specific OAuth scope."""
        return scope in self.get_token_scopes()

    def _get_viewer_login(self) -> str:
        """Fetch the authenticated user's GitHub login."""
        data = self.execute(_VIEWER_SCOPES_QUERY)
        login = data.get("viewer", {}).get("login", "")
        if not login:
            raise GitHubAPIError(
                "Could not determine authenticated user's GitHub login."
            )
        return login
