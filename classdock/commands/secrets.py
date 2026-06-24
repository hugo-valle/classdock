"""Secrets command group."""

from typing import Optional

import typer

from ..config.global_config import get_global_config
from ..utils import get_logger, setup_logging
from ._helpers import get_global_options

logger = get_logger("cli")

secrets_app = typer.Typer(help="Secret and token management commands")


@secrets_app.callback()
def secrets_callback(
    ctx: typer.Context,
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be done without executing"
    ),
):
    """Secret and token management commands."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose or ctx.obj.get("verbose", False)
    ctx.obj["dry_run"] = dry_run or ctx.obj.get("dry_run", False)


@secrets_app.command("add")
def secrets_add(
    ctx: typer.Context,
    assignment_root: Optional[str] = typer.Option(
        None,
        "--assignment-root",
        "-r",
        help="Path to assignment template repository root directory",
    ),
    repo_urls: Optional[str] = typer.Option(
        None, "--repos", help="Comma-separated list of repository URLs to process"
    ),
    force_update: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force update secrets even if they already exist and are up to date",
    ),
):
    """
    Add or update secrets in student repositories using global configuration.

    This function manages the process of adding or updating secrets in student repositories
    based on the global configuration loaded from assignment.conf. It supports dry-run and
    verbose modes for testing and debugging purposes.

    Supports universal options: --verbose, --dry-run

    Example:
        $ classdock secrets add
        $ classdock secrets add --repos "url1,url2" --verbose --dry-run
        $ classdock secrets add --force  # Force update all secrets
    """
    verbose, dry_run = get_global_options(ctx)

    if verbose:
        logger.debug("Verbose mode enabled for secrets add")

    logger.info("Adding secrets to student repositories using global configuration")

    if dry_run:
        logger.info("DRY RUN: Would add secrets to student repositories")
        if repo_urls:
            target_repos = [url.strip() for url in repo_urls.split(",") if url.strip()]
            logger.info(
                f"DRY RUN: Would process {len(target_repos)} specified repositories"
            )
        if assignment_root:
            logger.info(f"DRY RUN: Would use assignment root: {assignment_root}")
        return

    global_config = get_global_config()
    if not global_config:
        logger.error("Global configuration not loaded")
        logger.error(
            "Please ensure you're running from a directory with assignment.conf"
        )
        logger.error("Or use --assignment-root to specify the assignment directory")
        raise typer.Exit(code=1)

    if not global_config.secrets_config:
        logger.error("No secrets configuration found in assignment.conf")
        logger.error(
            "Add a SECRETS_CONFIG block to assignment.conf, for example:\n\n"
            '  SECRETS_CONFIG="\n'
            "  INSTRUCTOR_TESTS_TOKEN:Token for accessing instructor test repo:true\n"
            '  "\n\n'
            "Each line: SECRET_NAME:description:validate_format\n"
            "  validate_format=true  → expects a GitHub token (ghp_...)\n"
            "  validate_format=false → any string value\n\n"
            "Also set STEP_MANAGE_SECRETS=true in the WORKFLOW CONFIGURATION section."
        )
        raise typer.Exit(code=1)

    target_repos = None
    if repo_urls:
        target_repos = [url.strip() for url in repo_urls.split(",") if url.strip()]
        logger.info(f"Processing {len(target_repos)} specified repositories")

    try:
        from ..services.secrets_service import SecretsService

        service = SecretsService(dry_run=dry_run, verbose=verbose)
        ok, message = service.add_secrets(
            repo_urls=target_repos, force_update=force_update
        )

        if not ok:
            logger.error(f"Secret management failed: {message}")
            raise typer.Exit(code=1)

        logger.info(f"✅ {message}")

    except Exception as e:
        logger.error(f"Secrets command failed: {e}")
        raise typer.Exit(code=1)
