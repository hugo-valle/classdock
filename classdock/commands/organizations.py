"""Organizations command group for ClassDock."""

from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table

from ..organizations.manager import OrganizationManager
from ..organizations.templates import TemplateManager
from ..organizations.validators import OrgNameValidator
from ..services.organization_service import OrganizationService
from ..utils import get_logger, setup_logging
from ._helpers import get_global_options

logger = get_logger("cli.organizations")
console = Console()


def _get_token() -> Optional[str]:
    """Load the GitHub token from classdock's token store (same priority as other commands)."""
    try:
        from ..utils.token_manager import GitHubTokenManager

        return GitHubTokenManager().get_github_token()
    except Exception:
        return None


organizations_app = typer.Typer(
    help="GitHub organization lifecycle management: create, list, and clone templates."
)


@organizations_app.callback()
def organizations_callback(
    ctx: typer.Context,
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be done without executing"
    ),
):
    """GitHub organization lifecycle management."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose or ctx.obj.get("verbose", False)
    ctx.obj["dry_run"] = dry_run or ctx.obj.get("dry_run", False)


@organizations_app.command("init")
def org_init(ctx: typer.Context):
    """
    Launch the interactive wizard to set up a new GitHub organization and workspace.

    The wizard will:
    \\b
      1. Verify your GitHub token scopes
      2. Detect or prompt for your master template folder
      3. Let you select which template repos to carry forward
      4. Build and validate the new organization name
      5. Create a local semester org folder
      6. Clone selected templates locally
      7. Create the GitHub organization
      8. Fork templates into the new org (marking them as GitHub templates)
      9. Generate an assignment.conf starter file

    Examples:
        $ classdock organizations init
        $ classdock organizations init --dry-run
    """
    verbose, dry_run = get_global_options(ctx)
    setup_logging(verbose)

    try:
        service = OrganizationService(
            token=_get_token(), dry_run=dry_run, verbose=verbose
        )
        ok, message = service.setup()

        if ok:
            console.print(f"[green]✓ {message}[/green]")
        else:
            console.print(f"[red]✗ {message}[/red]")
            raise typer.Exit(code=1)

    except typer.Exit:
        raise
    except Exception as exc:
        logger.error("Organization init failed: %s", exc)
        raise typer.Exit(code=1)


@organizations_app.command("create")
def org_create(
    ctx: typer.Context,
    login: str = typer.Option(
        ..., "--login", help="Organization login (e.g., soc-cs3030-valle-su26)"
    ),
    email: str = typer.Option(..., "--email", help="Billing contact email"),
    name: Optional[str] = typer.Option(
        None, "--name", help="Organization display name"
    ),
):
    """
    Create a new GitHub organization (non-interactive).

    Requires the ``admin:org`` scope on your GitHub token.

    Examples:
        $ classdock organizations create --login soc-cs3030-valle-su26 --email me@weber.edu
        $ classdock organizations create --login soc-cs3030-valle-su26 --email me@weber.edu --name "CS3030 SU26"
    """
    verbose, dry_run = get_global_options(ctx)
    setup_logging(verbose)

    result = OrgNameValidator.validate(login)
    if not result.is_valid:
        console.print(f"[red]Invalid organization name:[/red]\n{result.error}")
        raise typer.Exit(code=1)

    if dry_run:
        console.print(f"[dim][dry-run] Would create GitHub org: {login}[/dim]")
        return

    try:
        mgr = OrganizationManager(token=_get_token())
        org = mgr.create_organization(
            login=login, billing_email=email, display_name=name
        )
        console.print(f"[green]✓ Organization '{org.login}' created.[/green]")
        if org.url:
            console.print(f"  URL: {org.url}")
    except PermissionError as exc:
        console.print(f"[red]Permission error:[/red]\n{exc}")
        raise typer.Exit(code=1)
    except NotImplementedError as exc:
        console.print(f"[yellow]{exc}[/yellow]")
        raise typer.Exit(code=1)
    except Exception as exc:
        logger.error("Organization creation failed: %s", exc)
        raise typer.Exit(code=1)


@organizations_app.command("list")
def org_list(ctx: typer.Context):
    """
    List GitHub organizations the authenticated user belongs to.

    Examples:
        $ classdock organizations list
    """
    verbose, _ = get_global_options(ctx)
    setup_logging(verbose)

    try:
        mgr = OrganizationManager(token=_get_token())
        orgs = mgr.list_user_organizations()

        if not orgs:
            console.print("[yellow]No organizations found.[/yellow]")
            return

        table = Table(title="Your GitHub Organizations", show_header=True)
        table.add_column("Login", style="cyan")
        table.add_column("Name")
        table.add_column("Role")

        for org in orgs:
            table.add_row(
                org.login,
                org.name or "",
                org.role or "",
            )

        console.print(table)

    except Exception as exc:
        logger.error("Failed to list organizations: %s", exc)
        raise typer.Exit(code=1)


@organizations_app.command("clone-templates")
def org_clone_templates(
    ctx: typer.Context,
    source_org: str = typer.Option(
        ..., "--source-org", help="Organization to clone templates from"
    ),
    target_org: str = typer.Option(
        ..., "--target-org", help="Organization to clone templates into"
    ),
    repos: Optional[List[str]] = typer.Option(
        None,
        "--repos",
        help="Repo names to clone (repeat for multiple). Omit to clone all templates.",
    ),
):
    """
    Fork template repositories from one organization to another.

    Each forked repository is automatically marked as a GitHub template.
    If --repos is omitted, all template repos in the source org are cloned.

    Examples:
        $ classdock organizations clone-templates \\
              --source-org CS3030 \\
              --target-org soc-cs3030-valle-su26

        $ classdock organizations clone-templates \\
              --source-org CS3030 \\
              --target-org soc-cs3030-valle-su26 \\
              --repos python-basics \\
              --repos midterm-project
    """
    verbose, dry_run = get_global_options(ctx)
    setup_logging(verbose)

    try:
        service = OrganizationService(
            token=_get_token(), dry_run=dry_run, verbose=verbose
        )
        result = service.clone_templates(
            source_org=source_org,
            target_org=target_org,
            repo_names=list(repos) if repos else [],
        )

        if result.total == 0:
            console.print("[yellow]No repositories to clone.[/yellow]")
            return

        # Build per-repo status table
        cloned_names = {r.name for r in result.cloned_repos}
        existed_names = set(result.already_existed)

        table = Table(title=f"Clone: {source_org} → {target_org}", show_header=True)
        table.add_column("Repository", style="cyan")
        table.add_column("Status", justify="center")

        for repo_name in result.attempted_names:
            if repo_name in cloned_names:
                table.add_row(repo_name, "[green]✓ cloned[/green]")
            elif repo_name in existed_names:
                table.add_row(repo_name, "[yellow]↩ exists[/yellow]")
            else:
                table.add_row(repo_name, "[red]✗ failed[/red]")

        console.print(table)

        parts = []
        if result.successful:
            parts.append(f"[green]{result.successful} cloned[/green]")
        if result.already_existed:
            parts.append(
                f"[yellow]{len(result.already_existed)} already existed[/yellow]"
            )
        if result.failed:
            parts.append(f"[red]{result.failed} failed[/red]")
        console.print("\nSummary: " + " · ".join(parts))

        if result.failed > 0:
            raise typer.Exit(code=1)

    except typer.Exit:
        raise
    except Exception as exc:
        logger.error("clone-templates failed: %s", exc)
        raise typer.Exit(code=1)


@organizations_app.command("verify")
def org_verify(
    ctx: typer.Context,
    login: str = typer.Argument(..., help="Organization login to verify"),
):
    """
    Verify that a GitHub organization exists and show its details.

    Examples:
        $ classdock organizations verify soc-cs3030-valle-su26
    """
    verbose, _ = get_global_options(ctx)
    setup_logging(verbose)

    try:
        # Validate name format
        val = OrgNameValidator.validate(login)
        if not val.is_valid:
            console.print(
                f"[yellow]Warning: '{login}' does not match the ClassDock naming convention.[/yellow]"
            )

        token = _get_token()
        mgr = OrganizationManager(token=token)
        org = mgr.get_organization(login)

        if org is None:
            console.print(f"[red]Organization '{login}' not found on GitHub.[/red]")
            raise typer.Exit(code=1)

        # Fetch repo counts
        tmpl_mgr = TemplateManager(token=token)
        all_repos = tmpl_mgr.list_org_repos(login, templates_only=False)
        template_repos = [r for r in all_repos if r.is_template]

        table = Table(title=f"Organization: {org.login}")
        table.add_column("Field", style="cyan")
        table.add_column("Value")
        table.add_row("Login", org.login)
        table.add_row("Name", org.name or "—")
        table.add_row("URL", org.url or "—")
        table.add_row("Role", org.role or "—")
        table.add_row("Repositories", str(len(all_repos)))
        table.add_row("Template repos", str(len(template_repos)))

        if val.is_valid:
            table.add_row("Semester", val.semester_label or "—")
            table.add_row("Year", val.full_year or "—")
            table.add_row("Instructor", val.last_name or "—")

        console.print(table)

        if all_repos:
            repo_table = Table(title="Repositories", show_header=True)
            repo_table.add_column("Name", style="cyan")
            repo_table.add_column("Template", justify="center")
            for repo in all_repos:
                repo_table.add_row(
                    repo.name, "[green]✓[/green]" if repo.is_template else ""
                )
            console.print(repo_table)

        console.print("[green]✓ Organization verified.[/green]")

    except typer.Exit:
        raise
    except Exception as exc:
        logger.error("Organization verification failed: %s", exc)
        raise typer.Exit(code=1)
