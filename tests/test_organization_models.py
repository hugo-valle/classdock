"""
Tests for classdock.organizations.models module.

Covers Organization, TemplateRepo, WorkspaceFolder, CloneResult, SetupResult.
"""

from pathlib import Path

import pytest

from classdock.organizations.models import (
    CloneResult,
    Organization,
    SetupResult,
    TemplateRepo,
    WorkspaceFolder,
)


class TestOrganization:
    """Tests for Organization model."""

    def test_create_minimal(self):
        org = Organization(login="soc-cs3030-valle-su26")
        assert org.login == "soc-cs3030-valle-su26"
        assert org.id is None
        assert org.name is None

    def test_from_dict(self):
        data = {
            "login": "soc-cs3030-valle-su26",
            "name": "CS3030 Summer 2026",
            "id": 42,
            "description": "Test org",
            "html_url": "https://github.com/soc-cs3030-valle-su26",
            "avatar_url": "https://example.com/avatar.png",
            "role": "admin",
        }
        org = Organization.from_dict(data)
        assert org.login == "soc-cs3030-valle-su26"
        assert org.name == "CS3030 Summer 2026"
        assert org.id == 42
        assert org.role == "admin"
        assert "github.com" in org.url

    def test_to_dict_roundtrip(self):
        org = Organization(login="soc-cs3030-valle-su26", name="CS3030", id=1, role="admin")
        d = org.to_dict()
        assert d["login"] == "soc-cs3030-valle-su26"
        assert d["name"] == "CS3030"
        assert d["id"] == 1


class TestTemplateRepo:
    """Tests for TemplateRepo model."""

    def test_create_minimal(self):
        repo = TemplateRepo(name="python-basics", owner="soc-cs3030-valle-su26")
        assert repo.full_name == "soc-cs3030-valle-su26/python-basics"
        assert not repo.is_template

    def test_full_name_auto_populated(self):
        repo = TemplateRepo(name="repo", owner="myorg")
        assert repo.full_name == "myorg/repo"

    def test_explicit_full_name_not_overwritten(self):
        repo = TemplateRepo(name="repo", owner="myorg", full_name="myorg/repo-custom")
        assert repo.full_name == "myorg/repo-custom"

    def test_from_dict(self):
        data = {
            "name": "python-basics",
            "owner": {"login": "soc-cs3030-valle-su26"},
            "full_name": "soc-cs3030-valle-su26/python-basics",
            "html_url": "https://github.com/soc-cs3030-valle-su26/python-basics",
            "clone_url": "https://github.com/soc-cs3030-valle-su26/python-basics.git",
            "is_template": True,
            "private": False,
            "description": "Python basics assignment",
        }
        repo = TemplateRepo.from_dict(data)
        assert repo.name == "python-basics"
        assert repo.owner == "soc-cs3030-valle-su26"
        assert repo.is_template is True

    def test_to_dict(self):
        repo = TemplateRepo(name="repo", owner="org", is_template=True)
        d = repo.to_dict()
        assert d["name"] == "repo"
        assert d["is_template"] is True
        assert d["local_path"] is None

    def test_to_dict_with_local_path(self):
        repo = TemplateRepo(name="repo", owner="org", local_path=Path("/tmp/repo"))
        d = repo.to_dict()
        assert d["local_path"] == "/tmp/repo"


class TestWorkspaceFolder:
    """Tests for WorkspaceFolder model."""

    def test_create(self, tmp_path):
        wf = WorkspaceFolder(path=tmp_path, is_master=True, course_code="CS3030")
        assert wf.path == tmp_path
        assert wf.is_master
        assert wf.course_code == "CS3030"

    def test_marker_path(self, tmp_path):
        wf = WorkspaceFolder(path=tmp_path)
        assert wf.marker_path == tmp_path / ".classdock-master"

    def test_is_marked_as_master_true(self, tmp_path):
        (tmp_path / ".classdock-master").touch()
        wf = WorkspaceFolder(path=tmp_path)
        assert wf.is_marked_as_master()

    def test_is_marked_as_master_false(self, tmp_path):
        wf = WorkspaceFolder(path=tmp_path)
        assert not wf.is_marked_as_master()

    def test_to_dict(self, tmp_path):
        wf = WorkspaceFolder(path=tmp_path, is_master=True, course_code="CS3030")
        d = wf.to_dict()
        assert d["is_master"] is True
        assert d["course_code"] == "CS3030"
        assert d["repos"] == []


class TestCloneResult:
    """Tests for CloneResult model."""

    def test_initial_state(self):
        r = CloneResult(total=5)
        assert r.successful == 0
        assert r.failed == 0
        assert r.success_rate == 0.0

    def test_add_success(self):
        r = CloneResult(total=2)
        repo = TemplateRepo(name="repo", owner="org")
        r.add_success(repo)
        assert r.successful == 1
        assert repo in r.cloned_repos

    def test_add_failure(self):
        r = CloneResult(total=2)
        r.add_failure("API error")
        assert r.failed == 1
        assert "API error" in r.errors

    def test_success_rate(self):
        r = CloneResult(total=4)
        for _ in range(3):
            r.add_success(TemplateRepo(name="r", owner="o"))
        assert r.success_rate == 75.0

    def test_success_rate_zero_total(self):
        r = CloneResult(total=0)
        assert r.success_rate == 0.0


class TestSetupResult:
    """Tests for SetupResult model."""

    def test_default_is_failure(self):
        r = SetupResult()
        assert not r.success
        assert r.organization is None

    def test_with_all_fields(self):
        org = Organization(login="soc-cs3030-valle-su26")
        r = SetupResult(organization=org, success=True)
        assert r.success
        assert r.organization.login == "soc-cs3030-valle-su26"
