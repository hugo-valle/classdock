"""
Local workspace folder management for organization-level assignment structure.

The ClassDock workspace follows this convention:

    ~/courses/                               ← configurable base dir
    ├── CS3030/                              ← master template folder
    │   ├── .classdock-master               ← marker identifying master folder
    │   ├── python-basics/                   ← local git clone of template repo
    │   └── midterm-project/
    └── soc-cs3030-valle-su26/              ← semester org folder
        ├── .classdock-org                  ← marker with org name
        ├── assignment.conf                  ← generated classdock config
        ├── python-basics/                   ← cloned from master
        └── midterm-project/

This module provides WorkspaceManager which handles all local filesystem
operations.  GitHub API operations are handled by the manager and templates
modules.
"""

import logging
import subprocess
from pathlib import Path
from typing import List, Optional

from ..utils.paths import PathManager
from .models import TemplateRepo, WorkspaceFolder

logger = logging.getLogger(__name__)

_MASTER_MARKER = ".classdock-master"
_ORG_MARKER = ".classdock-org"


class WorkspaceManager:
    """
    Manages the local workspace folder structure for ClassDock organizations.

    Args:
        base_path: Starting path for workspace discovery. Defaults to CWD.
    """

    def __init__(self, base_path: Optional[Path] = None):
        self._path_manager = PathManager(base_path or Path.cwd())

    # ------------------------------------------------------------------
    # Master folder operations
    # ------------------------------------------------------------------

    def find_master_folder(
        self, start: Optional[Path] = None
    ) -> Optional[WorkspaceFolder]:
        """
        Search for the nearest master template folder above the given path.

        The master folder is identified by the presence of a ``.classdock-master``
        marker file.

        Args:
            start: Directory to start searching from. Defaults to the base_path
                   supplied at construction time.

        Returns:
            WorkspaceFolder for the master folder, or None if not found.
        """
        path = self._path_manager.find_master_folder(start=start)
        if path is None:
            return None

        wf = WorkspaceFolder(
            path=path,
            is_master=True,
            course_code=path.name,
        )
        wf.repos = self._discover_repos_in_folder(path)
        return wf

    def init_master_folder(self, path: Path, course_code: str) -> WorkspaceFolder:
        """
        Initialize a directory as a master template folder.

        Creates the directory (if it does not exist) and writes the
        ``.classdock-master`` marker file.

        Args:
            path: Absolute path to the folder.
            course_code: Course code to embed in the marker (e.g., CS3030).

        Returns:
            WorkspaceFolder representing the initialized folder.
        """
        path.mkdir(parents=True, exist_ok=True)
        marker = path / _MASTER_MARKER
        marker.write_text(course_code, encoding="utf-8")
        logger.info("Initialized master folder: %s", path)

        return WorkspaceFolder(path=path, is_master=True, course_code=course_code)

    # ------------------------------------------------------------------
    # Semester org folder operations
    # ------------------------------------------------------------------

    def create_org_folder(self, base: Path, org_name: str) -> WorkspaceFolder:
        """
        Create a semester org folder under the given base directory.

        Args:
            base: Parent directory (typically the same directory that
                  contains the master folder).
            org_name: GitHub organization name (e.g., SOC-CS3030-Valle-SU26).

        Returns:
            WorkspaceFolder representing the new semester org folder.
        """
        org_path = self._path_manager.ensure_org_folder(base, org_name)
        logger.info("Created org folder: %s", org_path)
        return WorkspaceFolder(path=org_path, is_master=False, org_name=org_name)

    def find_org_folder(self, base: Path, org_name: str) -> Optional[WorkspaceFolder]:
        """
        Return a WorkspaceFolder if the org folder already exists under base.

        Args:
            base: Parent directory.
            org_name: Organization name.

        Returns:
            WorkspaceFolder if the folder exists, None otherwise.
        """
        path = self._path_manager.get_org_folder(base, org_name)
        if not path.exists():
            return None
        return WorkspaceFolder(
            path=path,
            is_master=False,
            org_name=org_name,
            repos=self._discover_repos_in_folder(path),
        )

    # ------------------------------------------------------------------
    # Local git-clone operations
    # ------------------------------------------------------------------

    def clone_repo_locally(
        self,
        clone_url: str,
        dest_folder: Path,
        repo_name: str,
    ) -> Optional[Path]:
        """
        Clone a git repository into ``<dest_folder>/<repo_name>``.

        Args:
            clone_url: HTTPS or SSH URL to clone from.
            dest_folder: Parent directory.
            repo_name: Name for the cloned directory.

        Returns:
            Path to the cloned directory, or None if cloning failed.
        """
        target = dest_folder / repo_name
        if target.exists():
            logger.info("Repo '%s' already exists locally; skipping clone.", repo_name)
            return target

        logger.info("Cloning '%s' → %s", clone_url, target)
        try:
            result = subprocess.run(
                ["git", "clone", "--quiet", clone_url, str(target)],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode != 0:
                logger.error(
                    "git clone failed for '%s': %s", clone_url, result.stderr.strip()
                )
                return None
            return target
        except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
            logger.error("git clone error for '%s': %s", clone_url, exc)
            return None

    def clone_templates_locally(
        self,
        repos: List[TemplateRepo],
        dest_folder: Path,
        progress_callback=None,
    ) -> List[TemplateRepo]:
        """
        Clone a list of TemplateRepo objects locally into dest_folder.

        Each repo's ``local_path`` is set on success.

        Args:
            repos: TemplateRepo objects with a populated ``clone_url``.
            dest_folder: Directory to clone repos into.
            progress_callback: Optional callable(current, total, repo_name).

        Returns:
            List of TemplateRepo objects that were cloned successfully
            (with local_path set).
        """
        cloned = []
        total = len(repos)

        for idx, repo in enumerate(repos, start=1):
            if progress_callback:
                progress_callback(idx, total, repo.name)

            if not repo.clone_url:
                logger.warning("No clone_url for '%s'; skipping.", repo.name)
                continue

            local = self.clone_repo_locally(repo.clone_url, dest_folder, repo.name)
            if local:
                repo.local_path = local
                cloned.append(repo)

        return cloned

    # ------------------------------------------------------------------
    # Discovery helpers
    # ------------------------------------------------------------------

    def _discover_repos_in_folder(self, folder: Path) -> List[TemplateRepo]:
        """
        Return a TemplateRepo stub for each subdirectory that looks like a
        git repository (contains a ``.git`` directory).

        Reads each repo's ``origin`` remote URL to populate ``owner`` and
        ``clone_url`` from the actual GitHub organization rather than the
        local folder name.

        Args:
            folder: Folder to inspect.

        Returns:
            List of TemplateRepo objects (metadata from filesystem + git remote).
        """
        repos = []
        try:
            for child in sorted(folder.iterdir()):
                if not (child.is_dir() and (child / ".git").exists()):
                    continue

                owner, clone_url = self._read_git_remote(child)
                repos.append(
                    TemplateRepo(
                        name=child.name,
                        owner=owner or folder.name,
                        clone_url=clone_url,
                        local_path=child,
                    )
                )
        except PermissionError as exc:
            logger.warning("Cannot read folder '%s': %s", folder, exc)
        return repos

    @staticmethod
    def _read_git_remote(repo_path: Path):
        """
        Return (owner, clone_url) parsed from the ``origin`` remote of a local
        git repository.  Returns (None, "") on failure.
        """
        import re as _re

        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                return None, ""

            url = result.stdout.strip()
            # HTTPS: https://github.com/ORG/REPO.git
            m = _re.match(r"https?://github\.com/([^/]+)/[^/]+", url)
            if m:
                return m.group(1), url
            # SSH: git@github.com:ORG/REPO.git
            m = _re.match(r"git@github\.com:([^/]+)/[^/]+", url)
            if m:
                return m.group(1), url
            return None, url
        except Exception as exc:
            logger.debug("Could not read git remote for '%s': %s", repo_path, exc)
            return None, ""

    def list_repos_in_folder(self, folder: Path) -> List[TemplateRepo]:
        """
        Public wrapper for discovering local git repos within a folder.

        Args:
            folder: Directory to inspect.

        Returns:
            List of TemplateRepo objects found.
        """
        return self._discover_repos_in_folder(folder)
