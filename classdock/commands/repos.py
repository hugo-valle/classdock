"""Repos command group."""

import typer

from ..utils import get_logger, setup_logging
from ._helpers import get_global_options

logger = get_logger("cli")

repos_app = typer.Typer(
    help="Repository operations and collaborator management commands"
)


@repos_app.callback()
def repos_callback(
    ctx: typer.Context,
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be done without executing"
    ),
):
    """Repository operations and collaborator management commands."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose or ctx.obj.get("verbose", False)
    ctx.obj["dry_run"] = dry_run or ctx.obj.get("dry_run", False)


@repos_app.command("fetch")
def repos_fetch(
    ctx: typer.Context,
    config_file: str = typer.Option(
        "assignment.conf", "--config", "-c", help="Configuration file path"
    ),
):
    """
    Discover and fetch student repositories from GitHub Classroom.

    This command loads the assignment configuration, then uses a Bash wrapper to fetch
    student repositories as specified in the configuration file. It supports dry-run and
    verbose modes for safer and more informative execution.

    Supports universal options: --verbose, --dry-run

    Example:
        $ classdock repos fetch
        $ classdock repos fetch --config custom.conf --verbose --dry-run
    """
    verbose, dry_run = get_global_options(ctx)

    if verbose:
        logger.debug(f"Verbose mode enabled for repo fetch with config: {config_file}")

    logger.info("Fetching student repositories")

    if dry_run:
        logger.info(
            f"DRY RUN: Would fetch student repositories using config: {config_file}"
        )
        return

    try:
        from ..services.repos_service import ReposService

        service = ReposService(dry_run=dry_run, verbose=verbose)
        ok, message = service.fetch(config_file=config_file)
        if not ok:
            logger.error(message)
            raise typer.Exit(code=1)
        logger.info(f"✅ {message}")
    except Exception as e:
        logger.error(f"Repository fetch failed: {e}")
        raise typer.Exit(code=1)
