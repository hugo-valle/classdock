"""
Tests for classdock.services.organization_service.OrganizationService.

All external dependencies are mocked.
"""

from unittest.mock import MagicMock, patch

import pytest

from classdock.organizations.models import (
    CloneResult,
    Organization,
    SetupResult,
    TemplateRepo,
)
from classdock.services.organization_service import OrganizationService


def _make_service(wizard_result=None, dry_run=False):
    """Build an OrganizationService with mocked sub-managers."""
    mock_wizard = MagicMock()
    mock_wizard.run.return_value = wizard_result or SetupResult(success=False, error_message="err")

    with patch("classdock.services.organization_service.OrganizationManager"), \
         patch("classdock.services.organization_service.TemplateManager"):
        svc = OrganizationService(
            token="fake-token",
            dry_run=dry_run,
            wizard_factory=lambda: mock_wizard,
        )
    svc._mock_wizard = mock_wizard
    return svc


class TestSetup:
    def test_returns_true_on_success(self):
        org = Organization(login="soc-cs3030-valle-su26")
        result = SetupResult(success=True, organization=org)
        svc = _make_service(wizard_result=result)
        ok, msg = svc.setup()
        assert ok
        assert "soc-cs3030-valle-su26" in msg

    def test_returns_false_on_failure(self):
        result = SetupResult(success=False, error_message="No master folder selected.")
        svc = _make_service(wizard_result=result)
        ok, msg = svc.setup()
        assert not ok
        assert "No master folder" in msg

    def test_handles_exception_gracefully(self):
        mock_wizard = MagicMock()
        mock_wizard.run.side_effect = RuntimeError("API is down")
        with patch("classdock.services.organization_service.OrganizationManager"), \
             patch("classdock.services.organization_service.TemplateManager"):
            svc = OrganizationService(
                token="fake",
                wizard_factory=lambda: mock_wizard,
            )
        ok, msg = svc.setup()
        assert not ok
        assert "API is down" in msg


class TestListOrganizations:
    def test_delegates_to_org_manager(self):
        svc = _make_service()
        orgs = [Organization(login="org-a"), Organization(login="org-b")]
        svc._org_manager.list_user_organizations.return_value = orgs
        result = svc.list_organizations()
        assert result == orgs

    def test_returns_empty_list_when_none(self):
        svc = _make_service()
        svc._org_manager.list_user_organizations.return_value = []
        assert svc.list_organizations() == []


class TestVerifyOrganization:
    def test_returns_true_and_org_when_exists(self):
        svc = _make_service()
        org = Organization(login="soc-cs3030-valle-su26")
        svc._org_manager.get_organization.return_value = org
        exists, found = svc.verify_organization("soc-cs3030-valle-su26")
        assert exists
        assert found == org

    def test_returns_false_and_none_when_missing(self):
        svc = _make_service()
        svc._org_manager.get_organization.return_value = None
        exists, found = svc.verify_organization("ghost-org")
        assert not exists
        assert found is None


class TestCloneTemplates:
    def test_delegates_to_template_manager(self):
        svc = _make_service()
        expected = CloneResult(total=2, successful=2)
        svc._template_manager.clone_templates.return_value = expected

        result = svc.clone_templates("src-org", "target-org", ["repo-a", "repo-b"])
        assert result == expected
        svc._template_manager.clone_templates.assert_called_once()

    def test_uses_all_templates_when_no_names_given(self):
        svc = _make_service()
        svc._template_manager.list_org_templates.return_value = [
            TemplateRepo(name="repo-x", owner="src-org"),
            TemplateRepo(name="repo-y", owner="src-org"),
        ]
        svc._template_manager.clone_templates.return_value = CloneResult(total=2)

        svc.clone_templates("src-org", "target-org", [])

        call_kwargs = svc._template_manager.clone_templates.call_args[1]
        assert set(call_kwargs["repo_names"]) == {"repo-x", "repo-y"}

    def test_dry_run_skips_api_call(self):
        svc = _make_service(dry_run=True)
        result = svc.clone_templates("src", "tgt", ["repo-a"])
        svc._template_manager.clone_templates.assert_not_called()
        assert result.total == 1
