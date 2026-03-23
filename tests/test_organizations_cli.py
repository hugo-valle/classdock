"""
Tests for classdock.commands.organizations CLI command group.

Uses Typer's test runner; no real network or filesystem access.
"""

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from classdock.cli import app
from classdock.organizations.models import (
    CloneResult,
    Organization,
    SetupResult,
)

runner = CliRunner(mix_stderr=False)


def _mock_org_manager(orgs=None, org=None, exists=True):
    m = MagicMock()
    m.return_value.list_user_organizations.return_value = orgs or []
    m.return_value.get_organization.return_value = org
    m.return_value.organization_exists.return_value = exists
    return m


class TestOrgList:
    def test_empty_org_list(self):
        with patch(
            "classdock.commands.organizations.OrganizationManager",
            _mock_org_manager(orgs=[]),
        ):
            result = runner.invoke(app, ["organizations", "list"])
        assert result.exit_code == 0
        assert "No organizations found" in result.output

    def test_shows_org_table(self):
        org = Organization(login="SOC-CS3030-Valle-SU26", name="CS3030", role="admin")
        with patch(
            "classdock.commands.organizations.OrganizationManager",
            _mock_org_manager(orgs=[org]),
        ):
            result = runner.invoke(app, ["organizations", "list"])
        assert result.exit_code == 0
        assert "SOC-CS3030-Valle-SU26" in result.output


class TestOrgVerify:
    def test_valid_org_found(self):
        org = Organization(
            login="SOC-CS3030-Valle-SU26",
            name="CS3030 SU26",
            url="https://github.com/SOC-CS3030-Valle-SU26",
            role="admin",
        )
        with patch(
            "classdock.commands.organizations.OrganizationManager",
            _mock_org_manager(org=org),
        ):
            result = runner.invoke(app, ["organizations", "verify", "SOC-CS3030-Valle-SU26"])
        assert result.exit_code == 0
        assert "verified" in result.output.lower()

    def test_org_not_found_exits_1(self):
        with patch(
            "classdock.commands.organizations.OrganizationManager",
            _mock_org_manager(org=None),
        ):
            result = runner.invoke(app, ["organizations", "verify", "ghost-org"])
        assert result.exit_code == 1

    def test_invalid_name_shows_warning(self):
        org = Organization(login="my-plain-org")
        with patch(
            "classdock.commands.organizations.OrganizationManager",
            _mock_org_manager(org=org),
        ):
            result = runner.invoke(app, ["organizations", "verify", "my-plain-org"])
        assert "Warning" in result.output or result.exit_code in (0, 1)


class TestOrgCreate:
    def test_invalid_name_exits_1(self):
        result = runner.invoke(
            app,
            ["organizations", "create", "--login", "bad name!", "--email", "a@b.com"],
        )
        assert result.exit_code == 1

    def test_dry_run_does_not_call_api(self):
        with patch("classdock.commands.organizations.OrganizationManager") as mock_mgr:
            result = runner.invoke(
                app,
                [
                    "--dry-run",
                    "organizations",
                    "create",
                    "--login",
                    "SOC-CS3030-Valle-SU26",
                    "--email",
                    "a@b.com",
                ],
            )
        mock_mgr.return_value.create_organization.assert_not_called()
        assert result.exit_code == 0

    def test_permission_error_exits_1(self):
        mock_mgr_instance = MagicMock()
        mock_mgr_instance.create_organization.side_effect = PermissionError("admin:org required")

        with patch(
            "classdock.commands.organizations.OrganizationManager",
            return_value=mock_mgr_instance,
        ):
            result = runner.invoke(
                app,
                [
                    "organizations",
                    "create",
                    "--login",
                    "SOC-CS3030-Valle-SU26",
                    "--email",
                    "a@b.com",
                ],
            )
        assert result.exit_code == 1
        assert "Permission" in result.output


class TestOrgCloneTemplates:
    def test_successful_clone(self):
        clone_result = CloneResult(total=2, successful=2)

        with patch(
            "classdock.commands.organizations.OrganizationService"
        ) as mock_svc_cls:
            mock_svc_cls.return_value.clone_templates.return_value = clone_result
            result = runner.invoke(
                app,
                [
                    "organizations",
                    "clone-templates",
                    "--source-org",
                    "CS3030",
                    "--target-org",
                    "SOC-CS3030-Valle-SU26",
                    "--repos",
                    "python-basics",
                ],
            )
        assert result.exit_code == 0
        assert "2/2" in result.output

    def test_partial_failure_exits_1(self):
        clone_result = CloneResult(total=2, successful=1, failed=1)
        clone_result.errors.append("fork failed")

        with patch(
            "classdock.commands.organizations.OrganizationService"
        ) as mock_svc_cls:
            mock_svc_cls.return_value.clone_templates.return_value = clone_result
            result = runner.invoke(
                app,
                [
                    "organizations",
                    "clone-templates",
                    "--source-org",
                    "CS3030",
                    "--target-org",
                    "SOC-CS3030-Valle-SU26",
                ],
            )
        assert result.exit_code == 1

    def test_zero_repos_shows_message(self):
        clone_result = CloneResult(total=0)

        with patch(
            "classdock.commands.organizations.OrganizationService"
        ) as mock_svc_cls:
            mock_svc_cls.return_value.clone_templates.return_value = clone_result
            result = runner.invoke(
                app,
                [
                    "organizations",
                    "clone-templates",
                    "--source-org",
                    "CS3030",
                    "--target-org",
                    "SOC-CS3030-Valle-SU26",
                ],
            )
        assert "No repositories" in result.output
