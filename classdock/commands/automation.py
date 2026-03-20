"""Automation command group."""

from typing import List, Optional

import typer

from ..utils import get_logger, setup_logging
from ._helpers import get_global_options

logger = get_logger("cli")

automation_app = typer.Typer(
    help="Automation, scheduling, and batch processing commands"
)


@automation_app.callback()
def automation_callback(
    ctx: typer.Context,
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be done without executing"
    ),
):
    """Automation, scheduling, and batch processing commands."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose or ctx.obj.get("verbose", False)
    ctx.obj["dry_run"] = dry_run or ctx.obj.get("dry_run", False)


@automation_app.command("cron-install")
def automation_cron_install(
    ctx: typer.Context,
    steps: List[str] = typer.Argument(
        ..., help="Workflow steps to schedule (sync, secrets, cycle, discover, assist)"
    ),
    schedule: Optional[str] = typer.Option(
        None,
        "--schedule",
        "-s",
        help="Cron schedule (e.g., '0 */4 * * *'). Uses default if not provided",
    ),
    config_file: str = typer.Option(
        "assignment.conf", "--config", "-c", help="Configuration file path"
    ),
):
    """
    Install cron job for automated workflow steps.

    Install cron jobs to automate GitHub Classroom workflow operations like
    template synchronization, secret management, and repository access cycling.

    Supports universal options: --verbose, --dry-run

    Examples:
        classdock automation cron-install sync
        classdock automation cron-install secrets --schedule "0 2 * * *" --verbose
        classdock automation cron-install sync secrets cycle --dry-run
    """
    verbose, dry_run = get_global_options(ctx)

    if verbose:
        logger.debug(f"Verbose mode enabled for cron installation: {steps}")

    if dry_run:
        logger.info(f"DRY RUN: Would install cron job for steps: {', '.join(steps)}")
        if schedule:
            logger.info(f"DRY RUN: Schedule: {schedule}")
        logger.info(f"DRY RUN: Config file: {config_file}")
        return

    try:
        from ..services.automation_service import AutomationService

        service = AutomationService(dry_run=dry_run, verbose=verbose)
        ok, message = service.cron_install(steps, schedule, config_file)
        if not ok:
            typer.echo(f"❌ {message}", color=typer.colors.RED)
            raise typer.Exit(code=1)
        typer.echo(f"✅ {message}", color=typer.colors.GREEN)
    except Exception as e:
        logger.error(f"Cron job installation failed: {e}")
        raise typer.Exit(code=1)


@automation_app.command("cron-remove")
def automation_cron_remove(
    ctx: typer.Context,
    steps: Optional[List[str]] = typer.Argument(
        None,
        help="Workflow steps to remove (sync, secrets, cycle, discover, assist) or 'all'",
    ),
    config_file: str = typer.Option(
        "assignment.conf", "--config", "-c", help="Configuration file path"
    ),
):
    """
    Remove cron jobs for automated workflow steps.

    Remove specific cron jobs or all assignment-related cron jobs from
    the user's crontab.

    Examples:
        classdock automation cron-remove sync
        classdock automation cron-remove all
        classdock automation cron-remove secrets cycle
    """
    verbose, dry_run = get_global_options(ctx)
    setup_logging(verbose)

    try:
        from ..services.automation_service import AutomationService

        service = AutomationService(dry_run=dry_run, verbose=verbose)

        if dry_run:
            if not steps or (len(steps) == 1 and steps[0] == "all"):
                typer.echo("[DRY RUN] Would remove all assignment cron jobs")
            else:
                typer.echo(
                    f"[DRY RUN] Would remove cron job for steps: {', '.join(steps)}"
                )
            return

        ok, message = service.cron_remove(steps, config_file)
        if not ok:
            typer.echo(f"❌ {message}", color=typer.colors.RED)
            raise typer.Exit(code=1)
        typer.echo(f"✅ {message}", color=typer.colors.GREEN)
    except Exception as e:
        logger.error(f"Cron job removal failed: {e}")
        raise typer.Exit(code=1)


@automation_app.command("cron-status")
def automation_cron_status(
    ctx: typer.Context,
    config_file: str = typer.Option(
        "assignment.conf", "--config", "-c", help="Configuration file path"
    ),
):
    """
    Show status of installed cron jobs.

    Display information about currently installed assignment-related cron jobs,
    including schedules, commands, and recent log activity.

    Supports universal options: --verbose, --dry-run

    Example:
        classdock automation cron-status
        classdock automation --verbose --dry-run cron-status
    """
    verbose, dry_run = get_global_options(ctx)

    if verbose:
        logger.debug("Verbose mode enabled for cron status check")

    logger.info("Checking cron job status...")

    if dry_run:
        logger.info("DRY RUN: Would check cron job status")
        logger.info(f"DRY RUN: Config file: {config_file}")
        return

    try:
        from ..services.automation_service import AutomationService

        service = AutomationService(dry_run=dry_run, verbose=verbose)
        ok, data = service.cron_status(config_file)
        if not ok:
            logger.error(data)
            raise typer.Exit(code=1)

        status = data
        if not status.has_jobs:
            typer.echo(
                "⚠️  No assignment cron jobs are installed", color=typer.colors.YELLOW
            )
            typer.echo("\nTo install a cron job, run:")
            typer.echo("  classdock automation cron-install [steps]")
        else:
            typer.echo(
                f"✅ Assignment cron jobs are installed: {status.total_jobs} job(s)",
                color=typer.colors.GREEN,
            )
            typer.echo()

            for job in status.installed_jobs:
                typer.echo(
                    f"📅 Steps: {', '.join(job.steps) if hasattr(job, 'steps') else job.steps_key}"
                )
                typer.echo(f"   Schedule: {job.schedule}")
                if hasattr(job, "command"):
                    typer.echo(f"   Command: {job.command}")
                typer.echo()

            if status.log_file_exists and status.last_log_activity:
                typer.echo("📋 Recent log activity:")
                log_lines = status.last_log_activity.splitlines()
                for line in log_lines[-3:]:
                    typer.echo(f"   {line}")
            elif status.log_file_exists:
                typer.echo("📋 Log file exists but no recent activity")
            else:
                typer.echo("⚠️  No log file found - cron jobs may not have run yet")

    except Exception as e:
        logger.error(f"Failed to get cron job status: {e}")
        raise typer.Exit(code=1)


@automation_app.command("cron-logs")
def automation_cron_logs(
    lines: int = typer.Option(
        30, "--lines", "-n", help="Number of recent log lines to show"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
    config_file: str = typer.Option(
        "assignment.conf", "--config", "-c", help="Configuration file path"
    ),
):
    """
    Show recent workflow log entries.

    Display recent log entries from automated workflow executions to help
    with debugging and monitoring cron job activity.

    Example:
        classdock automation cron-logs --lines 50
    """
    setup_logging(verbose)

    try:
        from ..services.automation_service import AutomationService

        service = AutomationService(dry_run=False, verbose=verbose)
        success, output = service.cron_logs(lines)
        if success:
            typer.echo(output)
        else:
            if "Log file not found" in output or "not found" in output.lower():
                typer.echo("📋 No logs available yet", color=typer.colors.YELLOW)
                typer.echo(
                    "\nCron jobs may not have run yet, or logging may not be configured."
                )
                typer.echo(
                    "Once cron jobs start running, their output will appear here."
                )
            else:
                typer.echo(f"❌ {output}", color=typer.colors.RED)
                raise typer.Exit(code=1)

    except Exception as e:
        logger.error(f"Failed to show logs: {e}")
        raise typer.Exit(code=1)


@automation_app.command("cron-schedules")
def automation_cron_schedules():
    """
    List default schedules for workflow steps.

    Show the default cron schedules used for different workflow steps
    and provide examples of cron schedule formats.

    Example:
        classdock automation cron-schedules
    """
    try:
        from ..services.automation_service import AutomationService

        service = AutomationService()
        ok, output = service.cron_schedules()
        if not ok:
            logger.error(output)
            raise typer.Exit(code=1)
        typer.echo(output)

    except Exception as e:
        logger.error(f"Failed to list schedules: {e}")
        raise typer.Exit(code=1)


@automation_app.command("cron-sync")
def automation_cron_sync(
    ctx: typer.Context,
    steps: List[str] = typer.Argument(
        None, help="Workflow steps to execute (sync, discover, secrets, assist, cycle)"
    ),
    config_file: str = typer.Option(
        "assignment.conf", "--config", "-c", help="Configuration file path"
    ),
    stop_on_failure: bool = typer.Option(
        False, "--stop-on-failure", help="Stop execution on first step failure"
    ),
    show_log: bool = typer.Option(
        False, "--show-log", help="Show log tail after execution"
    ),
):
    """
    Execute automated workflow cron job with specified steps.

    This command runs workflow steps designed for scheduled execution,
    providing comprehensive logging and error handling suitable for
    cron job automation.

    Available workflow steps:
    - sync: Synchronize template with classroom repository
    - discover: Discover and update student repositories
    - secrets: Manage repository secrets
    - assist: Provide automated student assistance
    - cycle: Cycle collaborator permissions

    Examples:
        classdock automation cron-sync
        classdock automation cron-sync sync secrets cycle
        classdock automation cron-sync --stop-on-failure --show-log sync secrets
    """
    verbose, dry_run = get_global_options(ctx)

    try:
        from ..services.automation_service import AutomationService

        service = AutomationService(dry_run=dry_run, verbose=verbose)
        ok, result = service.cron_sync(
            steps, dry_run, verbose, stop_on_failure, show_log
        )
        if not ok:
            logger.error(result)
            raise typer.Exit(code=1)

        if dry_run:
            logger.info("📋 Workflow steps that would be executed:")
            for i, step in enumerate(steps or ["sync"], 1):
                logger.info(f"  {i}. {step}")
            logger.info(
                f"📂 Log file: {result.get('log_file') if isinstance(result, dict) else 'unknown'}"
            )
            logger.info("✅ Dry run completed - use without --dry-run to execute")
            return

        res = result
        if hasattr(res, "overall_result") and res.overall_result.name == "SUCCESS":
            logger.info(
                f"✅ All workflow steps completed successfully in "
                f"{getattr(res, 'total_execution_time', 0):.2f}s"
            )
        elif (
            hasattr(res, "overall_result")
            and res.overall_result.name == "PARTIAL_FAILURE"
        ):
            logger.warning(
                f"⚠️ Some workflow steps failed: {getattr(res, 'error_summary', '')}"
            )
            logger.info(f"📂 Check log file: {getattr(res, 'log_file_path', '')}")
        elif (
            hasattr(res, "overall_result")
            and res.overall_result.name == "COMPLETE_FAILURE"
        ):
            logger.error(
                f"❌ All workflow steps failed: {getattr(res, 'error_summary', '')}"
            )
            logger.error(f"📂 Check log file: {getattr(res, 'log_file_path', '')}")

        if hasattr(res, "steps_executed") and res.steps_executed:
            logger.info("📊 Step execution summary:")
            for step_result in res.steps_executed:
                status = "✅" if step_result.success else "❌"
                logger.info(
                    f"  {status} {step_result.step.value}: {step_result.message}"
                )

        if show_log and hasattr(res, "get_log_tail"):
            logger.info("📋 Recent log entries:")
            for line in res.get_log_tail(20)[-10:]:
                logger.info(f"  {line}")

        if hasattr(res, "overall_result") and res.overall_result.name in [
            "COMPLETE_FAILURE",
            "ENVIRONMENT_ERROR",
            "CONFIGURATION_ERROR",
        ]:
            raise typer.Exit(code=1)
        if (
            hasattr(res, "overall_result")
            and res.overall_result.name == "PARTIAL_FAILURE"
        ):
            raise typer.Exit(code=2)

    except Exception as e:
        logger.error(f"Cron sync workflow failed: {e}")
        if verbose:
            import traceback

            logger.error(traceback.format_exc())
        raise typer.Exit(code=1)
