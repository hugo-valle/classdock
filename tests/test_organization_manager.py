"""
Tests for classdock.organizations.manager.OrganizationManager.

All GitHub API calls are mocked; no real network I/O occurs.
"""

from unittest.mock import MagicMock, patch

import pytest

from classdock.organizations.manager import OrganizationManager
from classdock.organizations.models import Organization


@pytest.fixture()
def manager():
    """Return an OrganizationManager with a stub token."""
    with patch("classdock.organizations.manager.GitHubAPIClient"), \
         patch("classdock.organizations.manager.GitHubGraphQLClient"):
        mgr = OrganizationManager(token="fake-token")
    return mgr


class TestListUserOrganizations:
    def test_returns_sorted_list(self, manager):
        manager._rest.list_user_organizations.return_value = [
            {"login": "zoo-org", "id": 2},
            {"login": "alpha-org", "id": 1},
        ]
        orgs = manager.list_user_organizations()
        assert [o.login for o in orgs] == ["alpha-org", "zoo-org"]

    def test_returns_empty_when_no_orgs(self, manager):
        manager._rest.list_user_organizations.return_value = []
        assert manager.list_user_organizations() == []

    def test_maps_to_organization_objects(self, manager):
        manager._rest.list_user_organizations.return_value = [
            {"login": "my-org", "id": 42, "html_url": "https://github.com/my-org"},
        ]
        orgs = manager.list_user_organizations()
        assert isinstance(orgs[0], Organization)
        assert orgs[0].login == "my-org"
        assert orgs[0].id == 42


class TestGetOrganization:
    def test_returns_organization(self, manager):
        manager._rest.get_organization.return_value = {
            "login": "SOC-CS3030-Valle-SU26",
            "id": 99,
        }
        org = manager.get_organization("SOC-CS3030-Valle-SU26")
        assert org is not None
        assert org.login == "SOC-CS3030-Valle-SU26"

    def test_returns_none_when_not_found(self, manager):
        manager._rest.get_organization.return_value = None
        org = manager.get_organization("nonexistent-org")
        assert org is None


class TestOrganizationExists:
    def test_true_when_exists(self, manager):
        manager._rest.organization_exists.return_value = True
        assert manager.organization_exists("real-org")

    def test_false_when_not_exists(self, manager):
        manager._rest.organization_exists.return_value = False
        assert not manager.organization_exists("ghost-org")


class TestCreateOrganization:
    def test_raises_permission_error_when_scope_missing(self, manager):
        manager._graphql.has_scope.return_value = False
        manager._graphql.get_token_scopes.return_value = ["repo"]
        with pytest.raises(PermissionError, match="admin:org"):
            manager.create_organization(
                "SOC-CS3030-Valle-SU26", "instructor@example.com"
            )

    def test_creates_org_when_scope_present(self, manager):
        manager._graphql.has_scope.return_value = True
        manager._graphql.create_organization.return_value = {
            "login": "SOC-CS3030-Valle-SU26",
            "name": "CS3030 Summer 2026",
            "url": "https://github.com/SOC-CS3030-Valle-SU26",
        }
        org = manager.create_organization(
            "SOC-CS3030-Valle-SU26", "instructor@example.com", display_name="CS3030"
        )
        assert org.login == "SOC-CS3030-Valle-SU26"
        assert org.name == "CS3030"

    def test_uses_login_as_name_fallback(self, manager):
        manager._graphql.has_scope.return_value = True
        manager._graphql.create_organization.return_value = {
            "login": "SOC-CS3030-Valle-SU26",
        }
        org = manager.create_organization(
            "SOC-CS3030-Valle-SU26", "instructor@example.com"
        )
        assert org.name == "SOC-CS3030-Valle-SU26"


class TestTokenHelpers:
    def test_get_token_scopes(self, manager):
        manager._graphql.get_token_scopes.return_value = ["repo", "admin:org"]
        assert manager.get_token_scopes() == ["repo", "admin:org"]

    def test_has_required_scopes_true(self, manager):
        manager._graphql.get_token_scopes.return_value = ["repo", "admin:org", "read:org"]
        assert manager.has_required_scopes()

    def test_has_required_scopes_false_missing_admin(self, manager):
        manager._graphql.get_token_scopes.return_value = ["repo", "read:org"]
        assert not manager.has_required_scopes()
