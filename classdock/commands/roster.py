"""Roster command group."""

from pathlib import Path
from typing import Optional

import typer

from ..utils import setup_logging, get_logger
from ._helpers import get_global_options

logger = get_logger("cli")

roster_app = typer.Typer(help="Student roster management and CSV import/export commands")


@roster_app.callback()
def roster_callback(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be done without executing"),
):
    """Student roster management and CSV import/export commands."""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose or ctx.obj.get('verbose', False)
    ctx.obj['dry_run'] = dry_run or ctx.obj.get('dry_run', False)


@roster_app.command("init")
def roster_init(ctx: typer.Context):
    """
    Initialize the roster database.

    Creates a global database at ~/.config/classdock/roster.db for tracking
    student rosters across multiple GitHub organizations.
    """
    from ..services.roster_service import RosterService

    verbose, dry_run = get_global_options(ctx)
    setup_logging(verbose=verbose)

    if dry_run:
        logger.info("🔍 DRY RUN: Would initialize roster database")
        return

    service = RosterService()
    if service.initialize_database():
        raise typer.Exit(0)
    else:
        raise typer.Exit(1)


@roster_app.command("import")
def roster_import(
    ctx: typer.Context,
    csv_file: str = typer.Argument(..., help="Path to CSV file to import"),
    org: str = typer.Option(..., "--org", help="GitHub organization (e.g., 'soc-cs3550-f25')"),
    skip_duplicates: bool = typer.Option(
        True, "--skip-duplicates/--fail-on-duplicates",
        help="Skip duplicate students instead of failing"
    ),
):
    """
    Import students from CSV file.

    Expected CSV format (Google Forms export):
    - email: Student email address
    - name: Student full name
    - github_username: GitHub username (optional)

    Example:
      classdock roster import students.csv --org=soc-cs3550-f25
    """
    from ..services.roster_service import RosterService

    verbose, dry_run = get_global_options(ctx)
    setup_logging(verbose=verbose)

    if dry_run:
        logger.info(f"🔍 DRY RUN: Would import from {csv_file} to org {org}")
        return

    service = RosterService()
    csv_path = Path(csv_file)

    if not csv_path.exists():
        logger.error(f"❌ File not found: {csv_file}")
        raise typer.Exit(1)

    if service.import_students_from_csv(csv_path, org, skip_duplicates):
        raise typer.Exit(0)
    else:
        raise typer.Exit(1)


@roster_app.command("list")
def roster_list(
    ctx: typer.Context,
    org: Optional[str] = typer.Option(None, "--org", help="Filter by GitHub organization"),
    status: str = typer.Option("active", "--status", help="Filter by status (active, inactive, dropped)"),
    format: str = typer.Option("table", "--format", help="Output format (table, csv, json)"),
):
    """
    List students in the roster.

    Examples:
      classdock roster list --org=soc-cs3550-f25
      classdock roster list --format=csv > students.csv
      classdock roster list --org=soc-cs3550-f25 --status=active
    """
    from ..services.roster_service import RosterService

    verbose, dry_run = get_global_options(ctx)
    setup_logging(verbose=verbose)

    service = RosterService()
    if service.list_students(org, status, format):
        raise typer.Exit(0)
    else:
        raise typer.Exit(1)


@roster_app.command("add")
def roster_add(
    ctx: typer.Context,
    email: str = typer.Option(..., "--email", help="Student email address"),
    name: str = typer.Option(..., "--name", help="Student full name"),
    org: str = typer.Option(..., "--org", help="GitHub organization"),
    github: Optional[str] = typer.Option(None, "--github", help="GitHub username (optional)"),
):
    """
    Add a single student to the roster.

    Example:
      classdock roster add --email=student@example.com --name="John Doe" \\
        --org=soc-cs3550-f25 --github=johndoe
    """
    from ..services.roster_service import RosterService

    verbose, dry_run = get_global_options(ctx)
    setup_logging(verbose=verbose)

    if dry_run:
        logger.info(f"🔍 DRY RUN: Would add student {email} to {org}")
        return

    service = RosterService()
    if service.add_student(email, name, org, github):
        raise typer.Exit(0)
    else:
        raise typer.Exit(1)


@roster_app.command("link")
def roster_link(
    ctx: typer.Context,
    email: str = typer.Option(..., "--email", help="Student email address"),
    github: str = typer.Option(..., "--github", help="GitHub username to link"),
    org: str = typer.Option(..., "--org", help="GitHub organization"),
):
    """
    Link a GitHub username to a student.

    Example:
      classdock roster link --email=student@example.com \\
        --github=johndoe --org=soc-cs3550-f25
    """
    from ..services.roster_service import RosterService

    verbose, dry_run = get_global_options(ctx)
    setup_logging(verbose=verbose)

    if dry_run:
        logger.info(f"🔍 DRY RUN: Would link {email} to GitHub user {github}")
        return

    service = RosterService()
    if service.link_github_username(email, org, github):
        raise typer.Exit(0)
    else:
        raise typer.Exit(1)


@roster_app.command("export")
def roster_export(
    ctx: typer.Context,
    output: str = typer.Argument(..., help="Output file path"),
    org: Optional[str] = typer.Option(None, "--org", help="Filter by GitHub organization"),
    format: str = typer.Option("csv", "--format", help="Output format (csv, json)"),
):
    """
    Export roster to file.

    Examples:
      classdock roster export students.csv --org=soc-cs3550-f25
      classdock roster export roster.json --org=soc-cs3550-f25 --format=json
    """
    from ..services.roster_service import RosterService

    verbose, dry_run = get_global_options(ctx)
    setup_logging(verbose=verbose)

    if dry_run:
        logger.info(f"🔍 DRY RUN: Would export to {output}")
        return

    service = RosterService()
    output_path = Path(output)

    if service.export_students(output_path, org, format):
        raise typer.Exit(0)
    else:
        raise typer.Exit(1)


@roster_app.command("status")
def roster_status(
    ctx: typer.Context,
    org: Optional[str] = typer.Option(None, "--org", help="Filter by GitHub organization"),
):
    """
    Show roster status and statistics.

    Example:
      classdock roster status --org=soc-cs3550-f25
    """
    from ..services.roster_service import RosterService

    verbose, dry_run = get_global_options(ctx)
    setup_logging(verbose=verbose)

    service = RosterService()
    service.show_status(org)


@roster_app.command("sync")
def roster_sync(
    ctx: typer.Context,
    assignment: str = typer.Option(..., "--assignment", help="Assignment name"),
    org: str = typer.Option(..., "--org", help="GitHub organization"),
    repos_file: str = typer.Option(
        "student-repos.txt", "--repos-file",
        help="File containing discovered repository URLs"
    ),
):
    """
    Synchronize discovered repositories with roster.

    Links student repositories to roster entries by matching GitHub usernames.
    Run 'classdock repos fetch' first to discover repositories.

    Example:
      classdock repos fetch
      classdock roster sync --assignment=python-basics --org=soc-cs3550-f25
    """
    from ..services.roster_service import RosterService
    from rich.console import Console
    from rich.table import Table

    verbose, dry_run = get_global_options(ctx)
    setup_logging(verbose=verbose)

    if dry_run:
        logger.info(f"🔍 DRY RUN: Would sync {assignment} repos from {repos_file}")
        return

    console = Console()
    service = RosterService()

    repos_path = Path(repos_file)
    if not repos_path.exists():
        logger.error(f"❌ Repository file not found: {repos_file}")
        logger.info("Run 'classdock repos fetch' first to discover repositories")
        raise typer.Exit(1)

    repos = []
    try:
        with open(repos_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '/' in line:
                        repo_name = line.split('/')[-1]
                        if '-' in repo_name:
                            parts = repo_name.split('-')
                            student_identifier = parts[-1]
                            repos.append((repo_name, line, student_identifier))
    except Exception as e:
        logger.error(f"❌ Failed to read repository file: {e}")
        raise typer.Exit(1)

    if not repos:
        logger.warning("⚠️  No repositories found in file")
        raise typer.Exit(1)

    console.print(f"\n🔄 Synchronizing {len(repos)} repositories...\n", style="bold")

    result = service.sync_repositories(assignment, org, repos)

    table = Table(title="Sync Results", show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Count", justify="right", style="magenta")
    table.add_row("Total Repositories", str(result.total_repos))
    table.add_row("✅ Linked", str(result.linked_count))
    table.add_row("❌ Unlinked", str(result.unlinked_count))
    table.add_row("Success Rate", f"{result.success_rate:.1f}%")
    console.print(table)

    if result.unlinked_repos:
        console.print("\n⚠️  Unlinked Repositories:", style="yellow bold")
        for repo_url in result.unlinked_repos[:10]:
            console.print(f"   • {repo_url}", style="yellow")
        if len(result.unlinked_repos) > 10:
            console.print(
                f"   ... and {len(result.unlinked_repos) - 10} more",
                style="yellow dim"
            )

    if result.errors:
        console.print("\n❌ Errors:", style="red bold")
        for error in result.errors[:10]:
            console.print(f"   • {error}", style="red")
        if len(result.errors) > 10:
            console.print(
                f"   ... and {len(result.errors) - 10} more errors",
                style="red dim"
            )

    if result.linked_count > 0:
        console.print(f"\n✅ Successfully linked {result.linked_count} repositories\n", style="green bold")
        raise typer.Exit(0)
    else:
        raise typer.Exit(1)
