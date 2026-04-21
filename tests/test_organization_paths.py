"""
Tests for organization-workspace path helpers in classdock.utils.paths.

Covers PathManager.find_master_folder(), .get_org_folder(), .ensure_org_folder().
"""

import pytest

from classdock.utils.paths import PathManager


class TestFindMasterFolder:
    """Tests for PathManager.find_master_folder()."""

    def test_finds_marker_in_start_directory(self, tmp_path):
        (tmp_path / ".classdock-master").touch()
        pm = PathManager(tmp_path)
        result = pm.find_master_folder(start=tmp_path)
        assert result == tmp_path

    def test_finds_marker_in_parent(self, tmp_path):
        (tmp_path / ".classdock-master").touch()
        child = tmp_path / "subdir"
        child.mkdir()
        pm = PathManager(child)
        result = pm.find_master_folder(start=child)
        assert result == tmp_path

    def test_finds_marker_two_levels_up(self, tmp_path):
        (tmp_path / ".classdock-master").touch()
        deep = tmp_path / "a" / "b"
        deep.mkdir(parents=True)
        pm = PathManager(deep)
        result = pm.find_master_folder(start=deep)
        assert result == tmp_path

    def test_returns_none_when_no_marker(self, tmp_path):
        pm = PathManager(tmp_path)
        result = pm.find_master_folder(start=tmp_path)
        assert result is None

    def test_uses_base_path_when_start_is_none(self, tmp_path):
        (tmp_path / ".classdock-master").touch()
        pm = PathManager(tmp_path)
        result = pm.find_master_folder()
        assert result == tmp_path


class TestGetOrgFolder:
    """Tests for PathManager.get_org_folder()."""

    def test_returns_correct_path(self, tmp_path):
        pm = PathManager(tmp_path)
        result = pm.get_org_folder(tmp_path, "soc-cs3030-valle-su26")
        assert result == tmp_path / "soc-cs3030-valle-su26"

    def test_does_not_create_directory(self, tmp_path):
        pm = PathManager(tmp_path)
        result = pm.get_org_folder(tmp_path, "soc-cs3030-valle-su26")
        assert not result.exists()


class TestEnsureOrgFolder:
    """Tests for PathManager.ensure_org_folder()."""

    def test_creates_directory(self, tmp_path):
        pm = PathManager(tmp_path)
        result = pm.ensure_org_folder(tmp_path, "soc-cs3030-valle-su26")
        assert result.is_dir()

    def test_creates_marker_file(self, tmp_path):
        pm = PathManager(tmp_path)
        result = pm.ensure_org_folder(tmp_path, "soc-cs3030-valle-su26")
        marker = result / ".classdock-org"
        assert marker.exists()
        assert marker.read_text(encoding="utf-8") == "soc-cs3030-valle-su26"

    def test_folder_name_matches_org_name(self, tmp_path):
        pm = PathManager(tmp_path)
        result = pm.ensure_org_folder(tmp_path, "soc-cs3550-2-smith-sp26")
        assert result.name == "soc-cs3550-2-smith-sp26"

    def test_idempotent_when_called_twice(self, tmp_path):
        pm = PathManager(tmp_path)
        pm.ensure_org_folder(tmp_path, "soc-cs3030-valle-su26")
        result = pm.ensure_org_folder(tmp_path, "soc-cs3030-valle-su26")
        assert result.is_dir()

    def test_creates_nested_base(self, tmp_path):
        nested_base = tmp_path / "courses" / "2026"
        pm = PathManager(tmp_path)
        result = pm.ensure_org_folder(nested_base, "soc-cs3030-valle-su26")
        assert result.is_dir()
