"""
Tests for classdock.organizations.templates.TemplateManager.

All GitHub REST API calls are mocked; no real network I/O occurs.
"""

from unittest.mock import MagicMock, patch

import pytest

from classdock.organizations.models import CloneResult, TemplateRepo
from classdock.organizations.templates import TemplateManager


@pytest.fixture()
def manager():
    """Return a TemplateManager with a mocked REST client."""
    with patch("classdock.organizations.templates.GitHubAPIClient"):
        mgr = TemplateManager(token="fake-token")
    return mgr


_REPO_DICT = {
    "name": "python-basics",
    "owner": {"login": "SOC-CS3030-Valle-SU26"},
    "full_name": "SOC-CS3030-Valle-SU26/python-basics",
    "html_url": "https://github.com/SOC-CS3030-Valle-SU26/python-basics",
    "clone_url": "https://github.com/SOC-CS3030-Valle-SU26/python-basics.git",
    "is_template": True,
    "private": False,
    "description": "Python basics assignment",
}


class TestListOrgTemplates:
    def test_returns_template_repos(self, manager):
        manager._api.list_org_repos.return_value = [_REPO_DICT]
        repos = manager.list_org_templates("SOC-CS3030-Valle-SU26")
        assert len(repos) == 1
        assert isinstance(repos[0], TemplateRepo)

    def test_returns_sorted(self, manager):
        manager._api.list_org_repos.return_value = [
            {**_REPO_DICT, "name": "zzz-repo"},
            {**_REPO_DICT, "name": "aaa-repo"},
        ]
        repos = manager.list_org_templates("org")
        assert repos[0].name == "aaa-repo"

    def test_empty_org(self, manager):
        manager._api.list_org_repos.return_value = []
        assert manager.list_org_templates("empty-org") == []


class TestForkRepository:
    def test_returns_template_repo_on_success(self, manager):
        manager._api.fork_repository.return_value = _REPO_DICT
        repo = manager.fork_repository(
            source_owner="master-org",
            repo_name="python-basics",
            target_org="SOC-CS3030-Valle-SU26",
        )
        assert repo is not None
        assert repo.name == "python-basics"

    def test_returns_none_on_api_failure(self, manager):
        manager._api.fork_repository.return_value = None
        repo = manager.fork_repository("org", "repo", "target-org")
        assert repo is None

    def test_passes_new_name(self, manager):
        manager._api.fork_repository.return_value = _REPO_DICT
        manager.fork_repository("org", "repo", "target-org", new_name="renamed-repo")
        manager._api.fork_repository.assert_called_once_with(
            owner="org",
            repo="repo",
            target_org="target-org",
            new_name="renamed-repo",
        )


class TestMakeTemplate:
    def test_returns_true_on_success(self, manager):
        manager._api.set_repository_template.return_value = True
        assert manager.make_template("org", "repo") is True

    def test_returns_false_on_failure(self, manager):
        manager._api.set_repository_template.return_value = False
        assert manager.make_template("org", "repo") is False


class TestCloneTemplates:
    def _setup_success(self, manager):
        manager._api.fork_repository.return_value = _REPO_DICT
        manager._api.set_repository_template.return_value = True

    def test_all_success(self, manager):
        self._setup_success(manager)
        result = manager.clone_templates(
            source_org="CS3030",
            target_org="SOC-CS3030-Valle-SU26",
            repo_names=["python-basics", "midterm-project"],
            settle_seconds=0,
        )
        assert result.total == 2
        assert result.successful == 2
        assert result.failed == 0
        assert result.success_rate == 100.0

    def test_partial_failure(self, manager):
        call_count = [0]

        def template_side_effect(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return None  # first call fails
            return _REPO_DICT

        manager._api.create_from_template.side_effect = template_side_effect
        manager._api.fork_repository.return_value = None  # fallback also fails
        manager._api.set_repository_template.return_value = True

        result = manager.clone_templates(
            source_org="CS3030",
            target_org="SOC-CS3030-Valle-SU26",
            repo_names=["fail-repo", "ok-repo"],
            settle_seconds=0,
        )
        assert result.successful == 1
        assert result.failed == 1
        assert len(result.errors) == 1

    def test_progress_callback_called(self, manager):
        self._setup_success(manager)
        calls = []
        manager.clone_templates(
            source_org="CS3030",
            target_org="target-org",
            repo_names=["repo-a", "repo-b"],
            progress_callback=lambda cur, total, name: calls.append((cur, total, name)),
            settle_seconds=0,
        )
        assert calls == [(1, 2, "repo-a"), (2, 2, "repo-b")]

    def test_empty_repo_list(self, manager):
        result = manager.clone_templates("src", "tgt", [], settle_seconds=0)
        assert result.total == 0
        assert result.successful == 0

    def test_sets_is_template_true_on_cloned_repos(self, manager):
        self._setup_success(manager)
        result = manager.clone_templates(
            source_org="CS3030",
            target_org="target-org",
            repo_names=["python-basics"],
            settle_seconds=0,
        )
        assert result.cloned_repos[0].is_template is True

    def test_still_counts_as_success_when_template_flag_fails(self, manager):
        manager._api.fork_repository.return_value = _REPO_DICT
        manager._api.set_repository_template.return_value = False  # template flag fails
        result = manager.clone_templates(
            source_org="CS3030",
            target_org="target-org",
            repo_names=["python-basics"],
            settle_seconds=0,
        )
        assert result.successful == 1
        assert result.cloned_repos[0].is_template is False
