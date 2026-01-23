"""
Simple CLI interface for ClassDock using basic Typer patterns.

This module provides a simplified command-line interface that avoids
complex type annotations that cause compatibility issues in CI environments.
"""

import typer

from .config import Configuration
from .bash_wrapper import BashWrapper
from .utils import setup_logging, logger

# Create the absolutely minimal Typer application
app = typer.Typer(
    help="ClassDock - Comprehensive automation suite for managing assignments."
)


@app.command()
def run(
    dry_run: bool = False,
    verbose: bool = False,
    config_file: str = None,
    yes: bool = False,
):
    """Run the complete classroom workflow (sync, discover, secrets, assist)."""
    # Setup logging
    setup_logging(verbose)

    # Load configuration
    config = Configuration.load(config_file)

    wrapper = BashWrapper(
        config,
        dry_run=dry_run,
        verbose=verbose,
        auto_yes=yes
    )
    success = wrapper.assignment_orchestrator(workflow_type="run")

    if success:
        logger.info("✅ Workflow completed successfully")
    else:
        logger.error("❌ Workflow failed")
        raise typer.Exit(code=1)


@app.command()
def sync(
    dry_run: bool = False,
    verbose: bool = False,
    config_file: str = None,
    yes: bool = False,
):
    """Sync template repository to GitHub Classroom."""
    # Setup logging
    setup_logging(verbose)

    # Load configuration
    config = Configuration.load(config_file)

    wrapper = BashWrapper(
        config,
        dry_run=dry_run,
        verbose=verbose,
        auto_yes=yes
    )
    success = wrapper.push_to_classroom()

    if success:
        logger.info("✅ Sync completed successfully")
    else:
        logger.error("❌ Sync failed")
        raise typer.Exit(code=1)


@app.command()
def discover(
    dry_run: bool = False,
    verbose: bool = False,
    config_file: str = None,
    yes: bool = False,
):
    """Discover and fetch student repositories from GitHub Classroom."""
    # Setup logging
    setup_logging(verbose)

    # Load configuration
    config = Configuration.load(config_file)

    wrapper = BashWrapper(
        config,
        dry_run=dry_run,
        verbose=verbose,
        auto_yes=yes
    )
    success = wrapper.fetch_student_repos()

    if success:
        logger.info("✅ Discovery completed successfully")
    else:
        logger.error("❌ Discovery failed")
        raise typer.Exit(code=1)


@app.command()
def secrets(
    dry_run: bool = False,
    verbose: bool = False,
    config_file: str = None,
    yes: bool = False,
):
    """Add or update secrets in student repositories."""
    # Setup logging
    setup_logging(verbose)

    # Load configuration
    config = Configuration.load(config_file)

    wrapper = BashWrapper(
        config,
        dry_run=dry_run,
        verbose=verbose,
        auto_yes=yes
    )
    success = wrapper.add_secrets_to_students()

    if success:
        logger.info("✅ Secrets management completed successfully")
    else:
        logger.error("❌ Secrets management failed")
        raise typer.Exit(code=1)


@app.command()
def assist(
    dry_run: bool = False,
    verbose: bool = False,
    config_file: str = None,
    yes: bool = False,
):
    """Assist students with common repository issues."""
    # Setup logging
    setup_logging(verbose)

    # Load configuration
    config = Configuration.load(config_file)

    wrapper = BashWrapper(
        config,
        dry_run=dry_run,
        verbose=verbose,
        auto_yes=yes
    )
    success = wrapper.student_update_helper()

    if success:
        logger.info("✅ Student assistance completed successfully")
    else:
        logger.error("❌ Student assistance failed")
        raise typer.Exit(code=1)


@app.command()
def setup():
    """Setup a new assignment configuration (Interactive Python wizard)."""
    from .assignments.setup import AssignmentSetup

    # Run the Python setup wizard
    wizard = AssignmentSetup()
    try:
        wizard.run_wizard()
    except KeyboardInterrupt:
        typer.echo("\nSetup wizard cancelled by user.", err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"Setup wizard failed: {e}", err=True)
        raise typer.Exit(code=1)


@app.command(name="setup-bash")
def setup_bash(
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be done without executing"),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"),
    config_file: str = typer.Option(
        "assignment.conf", "--config-file", "-c", help="Path to configuration file"),
    yes: bool = typer.Option(False, "--yes", "-y",
                             help="Automatically answer yes to prompts")
):
    """Setup a new assignment configuration (Legacy bash version)."""
    setup_logging(verbose)

    # Load configuration
    config = Configuration.load(config_file)

    wrapper = BashWrapper(
        config,
        dry_run=dry_run,
        verbose=verbose,
        auto_yes=yes
    )
    success = wrapper.setup_assignment()

    if success:
        logger.info("✅ Setup completed successfully")
    else:
        logger.error("❌ Setup failed")
        raise typer.Exit(code=1)


@app.command()
def update(
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be done without executing"),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"),
    config_file: str = typer.Option(
        "assignment.conf", "--config-file", "-c", help="Path to configuration file"),
    yes: bool = typer.Option(False, "--yes", "-y",
                             help="Automatically answer yes to prompts")
):
    """Update assignment configuration and repositories."""
    setup_logging(verbose)

    # Load configuration
    config = Configuration.load(config_file)

    wrapper = BashWrapper(
        config,
        dry_run=dry_run,
        verbose=verbose,
        auto_yes=yes
    )
    success = wrapper.update_assignment()

    if success:
        logger.info("✅ Update completed successfully")
    else:
        logger.error("❌ Update failed")
        raise typer.Exit(code=1)


@app.command()
def cron(
    action: str = typer.Option(
        "status", "--action", "-a", help="Action to perform (status, install, remove, etc.)"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be done without executing"),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"),
    config_file: str = typer.Option(
        "assignment.conf", "--config-file", "-c", help="Path to configuration file"),
    yes: bool = typer.Option(False, "--yes", "-y",
                             help="Automatically answer yes to prompts")
):
    """Manage cron automation jobs."""
    setup_logging(verbose)

    # Load configuration
    config = Configuration.load(config_file)

    wrapper = BashWrapper(
        config,
        dry_run=dry_run,
        verbose=verbose,
        auto_yes=yes
    )
    success = wrapper.manage_cron(action)

    if success:
        logger.info("✅ Cron management completed successfully")
    else:
        logger.error("❌ Cron management failed")
        raise typer.Exit(code=1)


@app.command(name="cron-sync")
def cron_sync(
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be done without executing"),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"),
    config_file: str = typer.Option(
        "assignment.conf", "--config-file", "-c", help="Path to configuration file"),
    yes: bool = typer.Option(False, "--yes", "-y",
                             help="Automatically answer yes to prompts")
):
    """Execute scheduled synchronization tasks."""
    setup_logging(verbose)

    # Load configuration
    config = Configuration.load(config_file)

    wrapper = BashWrapper(
        config,
        dry_run=dry_run,
        verbose=verbose,
        auto_yes=yes
    )
    success = wrapper.cron_sync()

    if success:
        logger.info("✅ Cron sync completed successfully")
    else:
        logger.error("❌ Cron sync failed")
        raise typer.Exit(code=1)


@app.command()
def cycle(
    assignment_prefix: str = typer.Option(
        None, "--assignment-prefix", help="Assignment prefix"),
    username: str = typer.Option(None, "--username", help="Username"),
    organization: str = typer.Option(
        None, "--organization", help="Organization"),
    list: bool = typer.Option(False, "--list", help="List collaborators"),
    force: bool = typer.Option(False, "--force", help="Force cycling"),
    repo_urls: bool = typer.Option(False, "--repo-urls", help="Use repo URLs"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be done without executing"),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"),
    config_file: str = typer.Option(
        "assignment.conf", "--config-file", "-c", help="Path to configuration file"),
    yes: bool = typer.Option(False, "--yes", "-y",
                             help="Automatically answer yes to prompts")
):
    """Cycle repository collaborator permissions."""
    setup_logging(verbose)

    # Load configuration
    config = Configuration.load(config_file)

    wrapper = BashWrapper(
        config,
        dry_run=dry_run,
        verbose=verbose,
        auto_yes=yes
    )
    success = wrapper.cycle_collaborator(
        assignment_prefix=assignment_prefix,
        username=username,
        organization=organization,
        list_mode=list,
        force_cycle=force,
        repo_url_mode=repo_urls
    )

    if success:
        logger.info("✅ Collaborator cycling completed successfully")
    else:
        logger.error("❌ Collaborator cycling failed")
        raise typer.Exit(code=1)


@app.command()
def version():
    """Show version information."""
    typer.echo("ClassDock v1.0.0")
    typer.echo("Python CLI for GitHub Classroom automation")


if __name__ == "__main__":
    app()
