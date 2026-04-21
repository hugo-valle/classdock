"""
Tests for classdock.organizations.workspace.WorkspaceManager.

Uses temporary directories; no network or real git operations.
"""

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from classdock.organizations.models import TemplateRepo
from classdock.organizations.workspace import WorkspaceManager


@pytest.fixture()
def tmp_workspace(tmp_path):
    """Return a tmp_path with a basic workspace layout."""
    return tmp_path


@pytest.fixture()
def manager(tmp_workspace):
    return WorkspaceManager(base_path=tmp_workspace)


# ---------------------------------------------------------------------------
# Master folder discovery
# ---------------------------------------------------------------------------

class TestFindMasterFolder:
    def test_finds_marker_in_base(self, tmp_workspace, manager):
        (tmp_workspace / ".classdock-master").touch()
        wf = manager.find_master_folder(start=tmp_workspace)
        assert wf is not None
        assert wf.is_master
        assert wf.path == tmp_workspace

    def test_finds_marker_in_parent(self, tmp_workspace, manager):
        (tmp_workspace / ".classdock-master").touch()
        child = tmp_workspace / "subdir"
        child.mkdir()
        wf = manager.find_master_folder(start=child)
        assert wf is not None
        assert wf.path == tmp_workspace

    def test_returns_none_when_no_marker(self, tmp_workspace, manager):
        assert manager.find_master_folder(start=tmp_workspace) is None

    def test_course_code_set_from_folder_name(self, tmp_workspace, manager):
        master = tmp_workspace / "CS3030"
        master.mkdir()
        (master / ".classdock-master").touch()
        wf = manager.find_master_folder(start=master)
        assert wf.course_code == "CS3030"

    def test_discovers_git_repos_inside(self, tmp_workspace, manager):
        (tmp_workspace / ".classdock-master").touch()
        repo_dir = tmp_workspace / "python-basics"
        repo_dir.mkdir()
        (repo_dir / ".git").mkdir()
        wf = manager.find_master_folder(start=tmp_workspace)
        assert len(wf.repos) == 1
        assert wf.repos[0].name == "python-basics"

    def test_ignores_non_git_subdirs(self, tmp_workspace, manager):
        (tmp_workspace / ".classdock-master").touch()
        (tmp_workspace / "not-a-repo").mkdir()
        wf = manager.find_master_folder(start=tmp_workspace)
        assert wf.repos == []


# ---------------------------------------------------------------------------
# Init master folder
# ---------------------------------------------------------------------------

class TestInitMasterFolder:
    def test_creates_directory(self, tmp_workspace, manager):
        target = tmp_workspace / "CS3030"
        manager.init_master_folder(target, "CS3030")
        assert target.is_dir()

    def test_creates_marker_file(self, tmp_workspace, manager):
        target = tmp_workspace / "CS3030"
        manager.init_master_folder(target, "CS3030")
        assert (target / ".classdock-master").exists()

    def test_marker_contains_course_code(self, tmp_workspace, manager):
        target = tmp_workspace / "CS3030"
        manager.init_master_folder(target, "CS3030")
        assert (target / ".classdock-master").read_text() == "CS3030"

    def test_returns_workspace_folder(self, tmp_workspace, manager):
        target = tmp_workspace / "CS3030"
        wf = manager.init_master_folder(target, "CS3030")
        assert wf.is_master
        assert wf.course_code == "CS3030"

    def test_idempotent_on_existing_dir(self, tmp_workspace, manager):
        target = tmp_workspace / "CS3030"
        target.mkdir()
        wf = manager.init_master_folder(target, "CS3030")
        assert wf.is_master


# ---------------------------------------------------------------------------
# Org folder creation
# ---------------------------------------------------------------------------

class TestCreateOrgFolder:
    def test_creates_directory(self, tmp_workspace, manager):
        wf = manager.create_org_folder(tmp_workspace, "soc-cs3030-valle-su26")
        assert (tmp_workspace / "soc-cs3030-valle-su26").is_dir()

    def test_creates_marker_file(self, tmp_workspace, manager):
        wf = manager.create_org_folder(tmp_workspace, "soc-cs3030-valle-su26")
        marker = wf.path / ".classdock-org"
        assert marker.exists()

    def test_returns_workspace_folder(self, tmp_workspace, manager):
        wf = manager.create_org_folder(tmp_workspace, "soc-cs3030-valle-su26")
        assert not wf.is_master
        assert wf.org_name == "soc-cs3030-valle-su26"


class TestFindOrgFolder:
    def test_returns_none_when_not_exists(self, tmp_workspace, manager):
        assert manager.find_org_folder(tmp_workspace, "nonexistent-org") is None

    def test_returns_folder_when_exists(self, tmp_workspace, manager):
        (tmp_workspace / "soc-cs3030-valle-su26").mkdir()
        wf = manager.find_org_folder(tmp_workspace, "soc-cs3030-valle-su26")
        assert wf is not None
        assert wf.org_name == "soc-cs3030-valle-su26"


# ---------------------------------------------------------------------------
# Local git-clone operations
# ---------------------------------------------------------------------------

class TestCloneRepoLocally:
    def test_success_returns_path(self, tmp_workspace, manager):
        target = tmp_workspace / "my-repo"

        def fake_run(cmd, **kwargs):
            target.mkdir()
            result = subprocess.CompletedProcess(cmd, returncode=0)
            result.stdout = ""
            result.stderr = ""
            return result

        with patch("classdock.organizations.workspace.subprocess.run", side_effect=fake_run):
            path = manager.clone_repo_locally(
                "https://github.com/org/my-repo.git", tmp_workspace, "my-repo"
            )
        assert path == target

    def test_failure_returns_none(self, tmp_workspace, manager):
        def fake_run(cmd, **kwargs):
            result = subprocess.CompletedProcess(cmd, returncode=128)
            result.stdout = ""
            result.stderr = "fatal: repository not found"
            return result

        with patch("classdock.organizations.workspace.subprocess.run", side_effect=fake_run):
            path = manager.clone_repo_locally(
                "https://github.com/org/bad-repo.git", tmp_workspace, "bad-repo"
            )
        assert path is None

    def test_skips_if_already_exists(self, tmp_workspace, manager):
        existing = tmp_workspace / "existing-repo"
        existing.mkdir()

        with patch("classdock.organizations.workspace.subprocess.run") as mock_run:
            path = manager.clone_repo_locally(
                "https://github.com/org/existing-repo.git", tmp_workspace, "existing-repo"
            )
            mock_run.assert_not_called()

        assert path == existing


class TestCloneTemplatesLocally:
    def test_clones_all_repos(self, tmp_workspace, manager):
        repos = [
            TemplateRepo(
                name="repo-a", owner="org",
                clone_url="https://github.com/org/repo-a.git"
            ),
            TemplateRepo(
                name="repo-b", owner="org",
                clone_url="https://github.com/org/repo-b.git"
            ),
        ]

        def fake_clone(url, dest, name):
            p = dest / name
            p.mkdir()
            return p

        with patch.object(manager, "clone_repo_locally", side_effect=fake_clone):
            cloned = manager.clone_templates_locally(repos, tmp_workspace)

        assert len(cloned) == 2
        assert cloned[0].local_path is not None

    def test_skips_repos_without_clone_url(self, tmp_workspace, manager):
        repos = [TemplateRepo(name="no-url-repo", owner="org", clone_url="")]
        with patch.object(manager, "clone_repo_locally") as mock_clone:
            result = manager.clone_templates_locally(repos, tmp_workspace)
            mock_clone.assert_not_called()
        assert result == []

    def test_progress_callback_called(self, tmp_workspace, manager):
        repos = [
            TemplateRepo(name="r", owner="o", clone_url="https://github.com/o/r.git")
        ]
        calls = []

        def fake_clone(url, dest, name):
            p = dest / name
            p.mkdir()
            return p

        with patch.object(manager, "clone_repo_locally", side_effect=fake_clone):
            manager.clone_templates_locally(
                repos, tmp_workspace,
                progress_callback=lambda cur, tot, nm: calls.append((cur, tot, nm))
            )

        assert calls == [(1, 1, "r")]


# ---------------------------------------------------------------------------
# Discovery helper
# ---------------------------------------------------------------------------

class TestDiscoverReposInFolder:
    def test_finds_git_dirs(self, tmp_workspace, manager):
        for name in ["repo-a", "repo-b"]:
            d = tmp_workspace / name
            d.mkdir()
            (d / ".git").mkdir()

        repos = manager.list_repos_in_folder(tmp_workspace)
        assert len(repos) == 2
        assert {r.name for r in repos} == {"repo-a", "repo-b"}

    def test_ignores_non_git_dirs(self, tmp_workspace, manager):
        (tmp_workspace / "not-a-repo").mkdir()
        assert manager.list_repos_in_folder(tmp_workspace) == []

    def test_returns_sorted_by_name(self, tmp_workspace, manager):
        for name in ["zzz", "aaa", "mmm"]:
            d = tmp_workspace / name
            d.mkdir()
            (d / ".git").mkdir()
        repos = manager.list_repos_in_folder(tmp_workspace)
        assert [r.name for r in repos] == ["aaa", "mmm", "zzz"]
