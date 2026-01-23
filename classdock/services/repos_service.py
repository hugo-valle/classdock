from pathlib import Path
from typing import Optional, Tuple

from ..utils import get_logger

logger = get_logger("services.repos")


class ReposService:
    """
    Service layer encapsulating repository-related operations.

    Methods mirror the high-level CLI commands and call into the existing
    manager classes under `classdock.repos` and `classdock.assignments`.
    """

    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose

    def fetch(self, config_file: Optional[str] = None) -> Tuple[bool, str]:
        try:
            from ..repos.fetch import RepositoryFetcher

            config_path = Path(config_file) if config_file else None
            fetcher = RepositoryFetcher(config_path)

            success = fetcher.fetch_all_repositories(verbose=self.verbose)
            if not success:
                return False, "Repository fetch failed"
            return True, "Repository fetch completed successfully"
        except Exception as e:
            logger.error(f"ReposService.fetch failed: {e}")
            return False, str(e)

    def update(self, config_file: Optional[str] = None) -> Tuple[bool, str]:
        try:
            from ..assignments.student_helper import StudentUpdateHelper

            config_path = Path(config_file) if config_file else None
            helper = StudentUpdateHelper(config_path)

            success, message = helper.execute_update_workflow(
                auto_confirm=True, verbose=self.verbose)

            if not success:
                return False, message
            return True, message
        except Exception as e:
            logger.error(f"ReposService.update failed: {e}")
            return False, str(e)

    def push(self, config_file: Optional[str] = None) -> Tuple[bool, str]:
        try:
            from ..assignments.push_manager import ClassroomPushManager, PushResult

            manager = ClassroomPushManager(assignment_root=Path.cwd())

            result, message = manager.execute_push_workflow(
                force=False, interactive=False)

            if result == PushResult.SUCCESS:
                return True, message
            if result == PushResult.UP_TO_DATE:
                return True, message
            return False, message
        except Exception as e:
            logger.error(f"ReposService.push failed: {e}")
            return False, str(e)

    def cycle_collaborator(
        self,
        assignment_prefix: Optional[str] = None,
        username: Optional[str] = None,
        organization: Optional[str] = None,
        list_collaborators: bool = False,
        force: bool = False,
        config_file: Optional[str] = None,
    ) -> Tuple[bool, str]:
        try:
            from ..assignments.cycle_collaborator import CycleCollaboratorManager

            config_path = Path(config_file) if config_file else None
            manager = CycleCollaboratorManager(config_path)

            repo_url = None
            if assignment_prefix and username and organization:
                repo_url = f"https://github.com/{organization}/{assignment_prefix}-{username}"

            if list_collaborators:
                if not repo_url:
                    return False, "Repository URL required for listing collaborators"
                collaborators = manager.list_repository_collaborators(repo_url)
                # Return a simple summary string
                lines = [
                    f"{c['login']}: {c.get('permission') or c.get('role')}" for c in collaborators]
                return True, "\n".join(lines)
            else:
                if not repo_url:
                    return False, "Repository URL required for cycling collaborators"
                success, message = manager.cycle_single_repository(
                    repo_url, force=force)
                if not success:
                    return False, message
                return True, message

        except Exception as e:
            logger.error(f"ReposService.cycle_collaborator failed: {e}")
            return False, str(e)
