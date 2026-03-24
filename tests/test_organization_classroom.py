"""
Tests for classdock.organizations.classroom.ClassroomManager
and the Classroom / ClassroomAssignment models.

All GitHub Classroom API calls are mocked; no real network I/O occurs.
"""

from unittest.mock import MagicMock, patch

import pytest

from classdock.organizations.classroom import ClassroomManager
from classdock.organizations.models import Classroom, ClassroomAssignment


# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------

_CLASSROOM_DICT = {
    "id": 100,
    "name": "CS3030 Summer 2026",
    "url": "https://classroom.github.com/classrooms/100",
    "archived": False,
    "organization": {"login": "SOC-CS3030-Valle-SU26"},
}

_ASSIGNMENT_DICT = {
    "id": 42,
    "title": "python-basics",
    "type": "individual",
    "deadline": "2026-06-01T23:59:00Z",
    "accepted": 15,
    "submitted": 12,
    "passing": 10,
    "starter_code_repository": {"full_name": "CS3030-master/python-basics-template"},
    "invite_link": "https://classroom.github.com/a/abc123",
    "classroom": {"id": 100},
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def manager():
    """Return a ClassroomManager with a mocked GitHubClassroomAPI."""
    with patch("classdock.organizations.classroom.GitHubClassroomAPI"):
        mgr = ClassroomManager(token="fake-token")
    return mgr


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------


class TestClassroomModel:
    def test_from_dict_basic(self):
        c = Classroom.from_dict(_CLASSROOM_DICT)
        assert c.id == 100
        assert c.name == "CS3030 Summer 2026"
        assert c.org_login == "SOC-CS3030-Valle-SU26"
        assert c.archived is False

    def test_from_dict_archived(self):
        d = {**_CLASSROOM_DICT, "archived": True}
        c = Classroom.from_dict(d)
        assert c.archived is True

    def test_from_dict_missing_org(self):
        d = {**_CLASSROOM_DICT, "organization": None}
        c = Classroom.from_dict(d)
        assert c.org_login == ""

    def test_to_dict_roundtrip(self):
        c = Classroom.from_dict(_CLASSROOM_DICT)
        d = c.to_dict()
        assert d["id"] == 100
        assert d["org_login"] == "SOC-CS3030-Valle-SU26"


class TestClassroomAssignmentModel:
    def test_from_dict_basic(self):
        a = ClassroomAssignment.from_dict(_ASSIGNMENT_DICT)
        assert a.id == 42
        assert a.title == "python-basics"
        assert a.type == "individual"
        assert a.deadline == "2026-06-01T23:59:00Z"
        assert a.accepted_count == 15
        assert a.submitted_count == 12
        assert a.passing_count == 10
        assert a.starter_code_repo == "CS3030-master/python-basics-template"
        assert a.invite_link == "https://classroom.github.com/a/abc123"
        assert a.classroom_id == 100

    def test_from_dict_no_starter_repo(self):
        d = {**_ASSIGNMENT_DICT, "starter_code_repository": None}
        a = ClassroomAssignment.from_dict(d)
        assert a.starter_code_repo is None

    def test_from_dict_defaults(self):
        d = {"id": 1, "title": "hw1"}
        a = ClassroomAssignment.from_dict(d)
        assert a.type == "individual"
        assert a.deadline is None
        assert a.accepted_count == 0

    def test_to_dict_roundtrip(self):
        a = ClassroomAssignment.from_dict(_ASSIGNMENT_DICT)
        d = a.to_dict()
        assert d["title"] == "python-basics"
        assert d["starter_code_repo"] == "CS3030-master/python-basics-template"


# ---------------------------------------------------------------------------
# ClassroomManager tests
# ---------------------------------------------------------------------------


class TestListClassrooms:
    def test_returns_classroom_objects(self, manager):
        manager._api.get_classrooms_paginated.return_value = [_CLASSROOM_DICT]
        classrooms = manager.list_classrooms()
        assert len(classrooms) == 1
        assert isinstance(classrooms[0], Classroom)

    def test_returns_sorted(self, manager):
        manager._api.get_classrooms_paginated.return_value = [
            {**_CLASSROOM_DICT, "name": "ZZZ Class"},
            {**_CLASSROOM_DICT, "name": "AAA Class", "id": 101},
        ]
        classrooms = manager.list_classrooms()
        assert classrooms[0].name == "AAA Class"

    def test_empty(self, manager):
        manager._api.get_classrooms_paginated.return_value = []
        assert manager.list_classrooms() == []


class TestListClassroomsForOrg:
    def test_filters_by_org(self, manager):
        manager._api.get_classrooms_paginated.return_value = [
            _CLASSROOM_DICT,
            {**_CLASSROOM_DICT, "id": 200, "organization": {"login": "other-org"}},
        ]
        classrooms = manager.list_classrooms_for_org("SOC-CS3030-Valle-SU26")
        assert len(classrooms) == 1
        assert classrooms[0].org_login == "SOC-CS3030-Valle-SU26"

    def test_case_insensitive(self, manager):
        manager._api.get_classrooms_paginated.return_value = [_CLASSROOM_DICT]
        classrooms = manager.list_classrooms_for_org("soc-cs3030-valle-su26")
        assert len(classrooms) == 1

    def test_no_match_returns_empty(self, manager):
        manager._api.get_classrooms_paginated.return_value = [_CLASSROOM_DICT]
        classrooms = manager.list_classrooms_for_org("unknown-org")
        assert classrooms == []


class TestGetClassroom:
    def test_returns_classroom(self, manager):
        manager._api.get_classroom.return_value = _CLASSROOM_DICT
        c = manager.get_classroom(100)
        assert c is not None
        assert c.id == 100

    def test_returns_none_on_404(self, manager):
        from classdock.utils.github_classroom_api import GitHubClassroomAPIError
        err = GitHubClassroomAPIError("not found", status_code=404)
        manager._api.get_classroom.side_effect = err
        assert manager.get_classroom(999) is None


class TestListAssignments:
    def test_returns_assignment_objects(self, manager):
        manager._api.get_classroom_assignments_paginated.return_value = [_ASSIGNMENT_DICT]
        assignments = manager.list_assignments(100)
        assert len(assignments) == 1
        assert isinstance(assignments[0], ClassroomAssignment)

    def test_empty_classroom(self, manager):
        manager._api.get_classroom_assignments_paginated.return_value = []
        assert manager.list_assignments(100) == []


class TestGetAssignment:
    def test_returns_assignment(self, manager):
        manager._api.get_assignment.return_value = _ASSIGNMENT_DICT
        a = manager.get_assignment(42)
        assert a is not None
        assert a.title == "python-basics"

    def test_returns_none_on_404(self, manager):
        from classdock.utils.github_classroom_api import GitHubClassroomAPIError
        err = GitHubClassroomAPIError("not found", status_code=404)
        manager._api.get_assignment.side_effect = err
        assert manager.get_assignment(999) is None


class TestAssignmentCreationUrl:
    def test_without_template(self):
        url = ClassroomManager.assignment_creation_url(100)
        assert url == "https://classroom.github.com/classrooms/100/assignments/new"

    def test_with_template(self):
        url = ClassroomManager.assignment_creation_url(100, "myorg/my-repo")
        assert "template_repo=myorg/my-repo" in url

    def test_new_classroom_url(self):
        url = ClassroomManager.new_classroom_url()
        assert "classroom.github.com/classrooms/new" in url
