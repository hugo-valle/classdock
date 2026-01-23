from typing import List, Optional, Tuple
from ..utils import get_logger

logger = get_logger("services.automation")


class AutomationService:
    """Service layer for automation-related CLI commands."""

    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose

    def cron_install(self, steps: List[str], schedule: Optional[str], config_file: str) -> Tuple[bool, str]:
        try:
            from ..automation import CronManager

            cron_manager = CronManager()
            result, message = cron_manager.install_cron_job(steps, schedule)

            if result.value == "success":
                return True, message
            if result.value == "already_exists":
                return True, message
            return False, message

        except Exception as e:
            logger.error(f"AutomationService.cron_install failed: {e}")
            return False, str(e)

    def cron_remove(self, steps, config_file: str) -> Tuple[bool, str]:
        try:
            from ..automation import CronManager

            cron_manager = CronManager()

            # Normalize steps
            if not steps:
                steps_arg = "all"
            elif len(steps) == 1 and steps[0] == "all":
                steps_arg = "all"
            else:
                steps_arg = steps

            result, message = cron_manager.remove_cron_job(steps_arg)

            if result.value == "success":
                return True, message
            return False, message

        except Exception as e:
            logger.error(f"AutomationService.cron_remove failed: {e}")
            return False, str(e)

    def cron_status(self, config_file: str):
        try:
            from ..automation import CronManager

            cron_manager = CronManager()
            status = cron_manager.get_cron_status()
            return True, status
        except Exception as e:
            logger.error(f"AutomationService.cron_status failed: {e}")
            return False, str(e)

    def cron_logs(self, lines: int = 30):
        try:
            from ..automation import CronManager

            cron_manager = CronManager()
            success, output = cron_manager.show_logs(lines)
            return success, output
        except Exception as e:
            logger.error(f"AutomationService.cron_logs failed: {e}")
            return False, str(e)

    def cron_schedules(self):
        try:
            from ..automation import CronManager

            cron_manager = CronManager()
            output = cron_manager.list_default_schedules()
            return True, output
        except Exception as e:
            logger.error(f"AutomationService.cron_schedules failed: {e}")
            return False, str(e)

    def cron_sync(self, steps, dry_run: bool, verbose: bool, stop_on_failure: bool, show_log: bool):
        try:
            from ..automation.cron_sync import CronSyncManager

            manager = CronSyncManager(assignment_root=None)

            if not steps:
                steps = ["sync"]

            if dry_run:
                # Provide manager info useful for dry-run
                return True, {"dry_run": True, "steps": steps, "log_file": getattr(manager, 'log_file', None)}

            result = manager.execute_cron_sync(
                steps=steps,
                verbose=verbose,
                stop_on_failure=stop_on_failure
            )

            return True, result
        except Exception as e:
            logger.error(f"AutomationService.cron_sync failed: {e}")
            return False, str(e)

    def sync(self, config_file: str, dry_run: bool, verbose: bool) -> Tuple[bool, str]:
        try:
            from ..automation.cron_sync import CronSyncManager, CronSyncResult

            manager = CronSyncManager(assignment_root=None)
            if dry_run:
                return True, f"DRY RUN: Would run scheduled sync (config: {config_file})"

            result = manager.execute_cron_sync(["sync"], verbose=verbose)

            if result.overall_result == CronSyncResult.SUCCESS:
                return True, "Scheduled sync completed successfully"
            return False, result.error_summary
        except Exception as e:
            logger.error(f"AutomationService.sync failed: {e}")
            return False, str(e)

    def batch(self):
        # Placeholder for future batch processing service methods
        return True, "Batch processing commands coming soon"
