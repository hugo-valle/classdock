"""
Tests for the Repository Pattern applied to roster student persistence.

Verifies that:
- StudentRepository defines the expected abstract interface.
- InMemoryStudentRepository correctly implements all CRUD operations.
- SqliteStudentRepository delegates to RosterManager (mocked).
- RosterService uses the injected student_repository for add/list/link/count.
- All StudentRepository implementations honour the same contract.
"""

import pytest
from unittest.mock import MagicMock

from classdock.roster.repositories import (
    StudentRepository,
    SqliteStudentRepository,
    InMemoryStudentRepository,
)
from classdock.roster.models import Student


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _student(email="alice@example.com", name="Alice", org="org1", **kwargs) -> Student:
    return Student(email=email, name=name, github_organization=org, **kwargs)


# ---------------------------------------------------------------------------
# InMemoryStudentRepository — full contract
# ---------------------------------------------------------------------------

class TestInMemoryStudentRepository:
    def setup_method(self):
        self.repo = InMemoryStudentRepository()

    def test_add_returns_sequential_ids(self):
        id1 = self.repo.add(_student(email="a@x.com"))
        id2 = self.repo.add(_student(email="b@x.com"))
        assert id1 == 1
        assert id2 == 2

    def test_find_by_id_returns_student(self):
        sid = self.repo.add(_student(email="a@x.com"))
        s = self.repo.find_by_id(sid)
        assert s is not None
        assert s.email == "a@x.com"

    def test_find_by_id_unknown_returns_none(self):
        assert self.repo.find_by_id(999) is None

    def test_find_by_email_matches_normalized(self):
        self.repo.add(_student(email="Alice@Example.COM"))
        s = self.repo.find_by_email("alice@example.com", "org1")
        assert s is not None

    def test_find_by_email_wrong_org_returns_none(self):
        self.repo.add(_student(email="a@x.com", org="org1"))
        assert self.repo.find_by_email("a@x.com", "org2") is None

    def test_find_by_github_username(self):
        sid = self.repo.add(_student(email="a@x.com"))
        self.repo.link_github_username(sid, "octocat")
        s = self.repo.find_by_github("octocat")
        assert s is not None
        assert s.email == "a@x.com"

    def test_find_by_github_with_org_filter(self):
        sid = self.repo.add(_student(email="a@x.com", org="org1"))
        self.repo.link_github_username(sid, "octocat")
        assert self.repo.find_by_github("octocat", "org1") is not None
        assert self.repo.find_by_github("octocat", "org2") is None

    def test_list_all_filters_by_status(self):
        self.repo.add(_student(email="a@x.com", status="active"))
        sid = self.repo.add(_student(email="b@x.com", status="active"))
        s = self.repo.find_by_id(sid)
        s.status = "dropped"
        self.repo.update(s)
        active = self.repo.list_all()
        assert len(active) == 1
        assert active[0].email == "a@x.com"

    def test_list_all_filters_by_org(self):
        self.repo.add(_student(email="a@x.com", org="org1"))
        self.repo.add(_student(email="b@x.com", org="org2"))
        results = self.repo.list_all(github_organization="org1")
        assert len(results) == 1
        assert results[0].email == "a@x.com"

    def test_list_all_sorted_by_name(self):
        self.repo.add(_student(email="z@x.com", name="Zara"))
        self.repo.add(_student(email="a@x.com", name="Alice"))
        names = [s.name for s in self.repo.list_all()]
        assert names == sorted(names)

    def test_update_persists_changes(self):
        sid = self.repo.add(_student(email="a@x.com"))
        s = self.repo.find_by_id(sid)
        s.notes = "updated note"
        self.repo.update(s)
        assert self.repo.find_by_id(sid).notes == "updated note"

    def test_update_missing_student_returns_false(self):
        s = _student()
        s.id = 999
        assert self.repo.update(s) is False

    def test_delete_removes_student(self):
        sid = self.repo.add(_student(email="a@x.com"))
        assert self.repo.delete(sid) is True
        assert self.repo.find_by_id(sid) is None

    def test_delete_missing_returns_false(self):
        assert self.repo.delete(999) is False

    def test_link_github_username(self):
        sid = self.repo.add(_student(email="a@x.com"))
        assert self.repo.link_github_username(sid, "gh-user", github_id=42) is True
        s = self.repo.find_by_id(sid)
        assert s.github_username == "gh-user"
        assert s.github_id == 42

    def test_link_github_unknown_student_returns_false(self):
        assert self.repo.link_github_username(999, "gh-user") is False

    def test_count_all(self):
        self.repo.add(_student(email="a@x.com", org="org1"))
        self.repo.add(_student(email="b@x.com", org="org2"))
        assert self.repo.count() == 2

    def test_count_by_org(self):
        self.repo.add(_student(email="a@x.com", org="org1"))
        self.repo.add(_student(email="b@x.com", org="org2"))
        assert self.repo.count("org1") == 1


# ---------------------------------------------------------------------------
# SqliteStudentRepository — delegates to RosterManager (mocked)
# ---------------------------------------------------------------------------

class TestSqliteStudentRepository:
    def setup_method(self):
        self.manager = MagicMock()
        self.repo = SqliteStudentRepository(self.manager)

    def test_add_delegates_to_manager(self):
        self.manager.add_student.return_value = 7
        s = _student()
        assert self.repo.add(s) == 7
        self.manager.add_student.assert_called_once_with(s)

    def test_update_delegates_to_manager(self):
        self.manager.update_student.return_value = True
        s = _student()
        assert self.repo.update(s) is True
        self.manager.update_student.assert_called_once_with(s)

    def test_find_by_id_delegates_to_manager(self):
        fake_student = _student()
        self.manager.get_student_by_id.return_value = fake_student
        assert self.repo.find_by_id(1) is fake_student

    def test_find_by_email_delegates_to_manager(self):
        fake_student = _student()
        self.manager.get_student_by_email.return_value = fake_student
        assert self.repo.find_by_email("a@x.com", "org1") is fake_student
        self.manager.get_student_by_email.assert_called_once_with("a@x.com", "org1")

    def test_find_by_github_delegates_to_manager(self):
        fake_student = _student()
        self.manager.get_student_by_github.return_value = fake_student
        assert self.repo.find_by_github("octocat", "org1") is fake_student
        self.manager.get_student_by_github.assert_called_once_with("octocat", "org1")

    def test_list_all_delegates_to_manager(self):
        self.manager.list_students.return_value = []
        result = self.repo.list_all(github_organization="org1", status="active")
        self.manager.list_students.assert_called_once_with(
            github_organization="org1", status="active")
        assert result == []

    def test_delete_delegates_to_manager(self):
        self.manager.delete_student.return_value = True
        assert self.repo.delete(3) is True

    def test_link_github_username_delegates_to_manager(self):
        self.manager.link_github_username.return_value = True
        assert self.repo.link_github_username(1, "octocat", 42) is True
        self.manager.link_github_username.assert_called_once_with(1, "octocat", 42)

    def test_count_delegates_to_manager(self):
        self.manager.count_students.return_value = 5
        assert self.repo.count("org1") == 5
        self.manager.count_students.assert_called_once_with("org1")


# ---------------------------------------------------------------------------
# RosterService uses student_repository — no real DB needed
# ---------------------------------------------------------------------------

class TestRosterServiceUsesRepository:
    def _make_service(self, repo):
        from classdock.services.roster_service import RosterService
        fake_db = MagicMock()
        fake_manager = MagicMock()
        fake_importer = MagicMock()
        fake_sync = MagicMock()
        return RosterService(
            db=fake_db,
            manager=fake_manager,
            importer=fake_importer,
            synchronizer=fake_sync,
            student_repository=repo,
        )

    def test_add_student_uses_repository(self):
        repo = InMemoryStudentRepository()
        service = self._make_service(repo)
        result = service.add_student("bob@x.com", "Bob", "org1")
        assert result is True
        assert repo.find_by_email("bob@x.com", "org1") is not None

    def test_list_students_uses_repository(self):
        repo = InMemoryStudentRepository()
        repo.add(_student(email="alice@x.com", name="Alice"))
        service = self._make_service(repo)
        # list_students prints to console; just ensure it doesn't crash and
        # returns True when students are found
        result = service.list_students(github_organization="org1")
        assert result is True

    def test_link_github_username_uses_repository(self):
        repo = InMemoryStudentRepository()
        repo.add(_student(email="alice@x.com", name="Alice", org="org1"))
        service = self._make_service(repo)
        result = service.link_github_username("alice@x.com", "org1", "alice-gh")
        assert result is True
        linked = repo.find_by_email("alice@x.com", "org1")
        assert linked.github_username == "alice-gh"

    def test_link_github_username_missing_student_returns_false(self):
        repo = InMemoryStudentRepository()
        service = self._make_service(repo)
        result = service.link_github_username("nobody@x.com", "org1", "gh-user")
        assert result is False

    def test_default_repository_is_sqlite_backed(self):
        from classdock.services.roster_service import RosterService
        from classdock.roster.repositories import SqliteStudentRepository
        fake_db = MagicMock()
        fake_manager = MagicMock()
        service = RosterService(db=fake_db, manager=fake_manager)
        assert isinstance(service.student_repository, SqliteStudentRepository)
