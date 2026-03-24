"""Organizations command group for ClassDock."""

from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table

from ._helpers import get_global_options
from ..utils import get_logger, setup_logging
from ..organizations.classroom import ClassroomManager
from ..organizations.manager import OrganizationManager
from ..organizations.templates import TemplateManager
from ..organizations.validators import OrgNameValidator
from ..services.organization_service import OrganizationService
from ..utils.github_classroom_api import GitHubClassroomAPIError

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
      9. Guide you through GitHub Classroom setup

    Examples:
        $ classdock organizations init
        $ classdock organizations init --dry-run
    """
    verbose, dry_run = get_global_options(ctx)
    setup_logging(verbose)

    try:
        service = OrganizationService(token=_get_token(), dry_run=dry_run, verbose=verbose)
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
    login: str = typer.Option(..., "--login", help="Organization login (e.g., SOC-CS3030-Valle-SU26)"),
    email: str = typer.Option(..., "--email", help="Billing contact email"),
    name: Optional[str] = typer.Option(None, "--name", help="Organization display name"),
):
    """
    Create a new GitHub organization (non-interactive).

    Requires the ``admin:org`` scope on your GitHub token.

    Examples:
        $ classdock organizations create --login SOC-CS3030-Valle-SU26 --email me@weber.edu
        $ classdock organizations create --login SOC-CS3030-Valle-SU26 --email me@weber.edu --name "CS3030 SU26"
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
        org = mgr.create_organization(login=login, billing_email=email, display_name=name)
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
    source_org: str = typer.Option(..., "--source-org", help="Organization to clone templates from"),
    target_org: str = typer.Option(..., "--target-org", help="Organization to clone templates into"),
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
              --target-org SOC-CS3030-Valle-SU26

        $ classdock organizations clone-templates \\
              --source-org CS3030 \\
              --target-org SOC-CS3030-Valle-SU26 \\
              --repos python-basics \\
              --repos midterm-project
    """
    verbose, dry_run = get_global_options(ctx)
    setup_logging(verbose)

    try:
        service = OrganizationService(token=_get_token(), dry_run=dry_run, verbose=verbose)
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
            parts.append(f"[yellow]{len(result.already_existed)} already existed[/yellow]")
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
        $ classdock organizations verify SOC-CS3030-Valle-SU26
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
            table.add_row("Instructor", val.lastname or "—")

        console.print(table)

        if all_repos:
            repo_table = Table(title="Repositories", show_header=True)
            repo_table.add_column("Name", style="cyan")
            repo_table.add_column("Template", justify="center")
            for repo in all_repos:
                repo_table.add_row(repo.name, "[green]✓[/green]" if repo.is_template else "")
            console.print(repo_table)

        console.print("[green]✓ Organization verified.[/green]")

    except typer.Exit:
        raise
    except Exception as exc:
        logger.error("Organization verification failed: %s", exc)
        raise typer.Exit(code=1)


# ======================================================================
# Classroom sub-command group
# ======================================================================

classroom_app = typer.Typer(
    help="Inspect and replicate GitHub Classroom structure for an organization."
)
organizations_app.add_typer(classroom_app, name="classroom")


@classroom_app.command("list")
def classroom_list(
    ctx: typer.Context,
    org_login: Optional[str] = typer.Argument(
        None, help="Filter classrooms by GitHub org login (e.g., SOC-CS3030-Valle-FA26)"
    ),
):
    """
    List GitHub Classrooms, optionally filtered to a specific organization.

    Examples:
        $ classdock organizations classroom list
        $ classdock organizations classroom list SOC-CS3030-Valle-FA26
    """
    setup_logging(ctx.obj.get("verbose", False) if ctx.obj else False)
    try:
        mgr = ClassroomManager(token=_get_token())
        classrooms = (
            mgr.list_classrooms_for_org(org_login)
            if org_login
            else mgr.list_classrooms(enrich_org=True)
        )

        if not classrooms:
            msg = f"No classrooms found" + (f" for '{org_login}'" if org_login else "") + "."
            console.print(f"[yellow]{msg}[/yellow]")
            return

        title = f"Classrooms for '{org_login}'" if org_login else "Your GitHub Classrooms"
        table = Table(title=title, show_header=True)
        table.add_column("ID", style="dim", justify="right")
        table.add_column("Name", style="cyan")
        table.add_column("Organization")
        table.add_column("Archived", justify="center")
        table.add_column("URL")

        for c in classrooms:
            table.add_row(
                str(c.id),
                c.name,
                c.org_login or "—",
                "[yellow]yes[/yellow]" if c.archived else "",
                c.url or "—",
            )

        console.print(table)

    except GitHubClassroomAPIError as exc:
        console.print(f"[red]Classroom API error:[/red] {exc}")
        raise typer.Exit(code=1)
    except Exception as exc:
        logger.error("classroom list failed: %s", exc)
        raise typer.Exit(code=1)


@classroom_app.command("assignments")
def classroom_assignments(
    ctx: typer.Context,
    org_login: Optional[str] = typer.Argument(
        None,
        help="GitHub organization login to filter classrooms (e.g., SOC-CS3030-Valle-FA26). "
             "If omitted, you will be prompted to select from all accessible classrooms.",
    ),
):
    """
    Interactively select a classroom and list its assignments.

    When ORG_LOGIN is given, only classrooms linked to that organization are shown.
    You are then prompted to pick a classroom before the assignment table is displayed.

    Examples:
        $ classdock organizations classroom assignments
        $ classdock organizations classroom assignments SOC-CS3030-Valle-FA26
    """
    setup_logging(ctx.obj.get("verbose", False) if ctx.obj else False)
    try:
        mgr = ClassroomManager(token=_get_token())

        # Step 1 — build the classroom list (filtered or all)
        if org_login:
            classrooms = mgr.list_classrooms_for_org(org_login)
            scope = f"'{org_login}'"
        else:
            classrooms = mgr.list_classrooms(enrich_org=True)
            scope = "your account"

        if not classrooms:
            console.print(f"[yellow]No classrooms found for {scope}.[/yellow]")
            return

        # Step 2 — present a numbered menu for classroom selection
        console.print(f"\n[bold]Classrooms in {scope}:[/bold]\n")
        for i, c in enumerate(classrooms, start=1):
            org_hint = f"  [dim]({c.org_login})[/dim]" if c.org_login else ""
            archived = "  [yellow][archived][/yellow]" if c.archived else ""
            console.print(f"  {i}. {c.name}{org_hint}{archived}")

        console.print()
        choice = typer.prompt(
            f"Select classroom [1-{len(classrooms)}]",
            default="1",
        )
        try:
            idx = int(choice) - 1
            if not 0 <= idx < len(classrooms):
                raise ValueError
        except ValueError:
            console.print("[red]Invalid selection.[/red]")
            raise typer.Exit(code=1)

        classroom = classrooms[idx]

        # Step 3 — fetch and display assignments
        assignments = mgr.list_assignments(classroom.id)
        if not assignments:
            console.print(f"[yellow]No assignments in classroom '{classroom.name}'.[/yellow]")
            return

        console.print(f"\n[bold]Assignments in {classroom.name}:[/bold]\n")
        for i, a in enumerate(assignments, start=1):
            deadline = f"  [dim]due {a.deadline}[/dim]" if a.deadline else ""
            console.print(
                f"  {i}. {a.title}  "
                f"[dim]{a.type}[/dim]  "
                f"accepted: {a.accepted_count}{deadline}"
            )

        console.print()
        choice = typer.prompt(
            f"Select assignment to view student repos [1-{len(assignments)}]",
            default="1",
        )
        try:
            aidx = int(choice) - 1
            if not 0 <= aidx < len(assignments):
                raise ValueError
        except ValueError:
            console.print("[red]Invalid selection.[/red]")
            raise typer.Exit(code=1)

        assignment = assignments[aidx]

        # Step 4 — fetch and display student repos for the selected assignment
        console.print(
            f"\nFetching student repos for [bold]{assignment.title}[/bold]…\n"
        )
        accepted = mgr.get_accepted_assignments(assignment.id)

        if not accepted:
            console.print(
                f"[yellow]No student repos found for '{assignment.title}'.[/yellow]"
            )
            return

        repo_table = Table(
            title=f"Student Repos: {assignment.title} ({classroom.name})",
            show_header=True,
        )
        repo_table.add_column("#", style="dim", justify="right")
        repo_table.add_column("GitHub Username", style="cyan")
        repo_table.add_column("Repository")
        repo_table.add_column("Submitted", justify="center")
        repo_table.add_column("Passing", justify="center")
        repo_table.add_column("Commits", justify="right")
        repo_table.add_column("Grade")

        for i, entry in enumerate(accepted, start=1):
            students = entry.get("students") or []
            username = students[0].get("login", "—") if students else "—"
            repo = entry.get("repository") or {}
            repo_name = repo.get("full_name") or repo.get("name", "—")
            submitted = "[green]✓[/green]" if entry.get("submitted") else ""
            passing = "[green]✓[/green]" if entry.get("passing") else ""
            commits = str(entry.get("commit_count", "—"))
            grade = str(entry.get("grade", "—")) if entry.get("grade") is not None else "—"

            repo_table.add_row(
                str(i), username, repo_name, submitted, passing, commits, grade
            )

        console.print(repo_table)
        console.print(
            f"\n[dim]Total: {len(accepted)} student(s) · "
            f"Assignment ID: {assignment.id}[/dim]"
        )

    except GitHubClassroomAPIError as exc:
        console.print(f"[red]Classroom API error:[/red] {exc}")
        raise typer.Exit(code=1)
    except typer.Exit:
        raise
    except Exception as exc:
        logger.error("classroom assignments failed: %s", exc)
        raise typer.Exit(code=1)


@classroom_app.command("grades")
def classroom_grades(
    ctx: typer.Context,
    assignment_id: int = typer.Argument(..., help="GitHub Classroom assignment numeric ID"),
):
    """
    Show grading data for an assignment.

    Examples:
        $ classdock organizations classroom grades 67890
    """
    setup_logging(ctx.obj.get("verbose", False) if ctx.obj else False)
    try:
        mgr = ClassroomManager(token=_get_token())
        assignment = mgr.get_assignment(assignment_id)
        if assignment is None:
            console.print(f"[red]Assignment {assignment_id} not found.[/red]")
            raise typer.Exit(code=1)

        grades = mgr.get_grades(assignment_id)
        if not grades:
            console.print(
                f"[yellow]No grade data for '{assignment.title}' yet.[/yellow]"
            )
            return

        table = Table(title=f"Grades: {assignment.title}", show_header=True)
        table.add_column("GitHub Username", style="cyan")
        table.add_column("Points Awarded", justify="right")
        table.add_column("Points Available", justify="right")
        table.add_column("Submitted At")

        for g in grades:
            table.add_row(
                g.get("github_username", "—"),
                str(g.get("points_awarded", "—")),
                str(g.get("points_available", "—")),
                g.get("submission_timestamp", "—") or "—",
            )

        console.print(table)

    except GitHubClassroomAPIError as exc:
        console.print(f"[red]Classroom API error:[/red] {exc}")
        raise typer.Exit(code=1)
    except typer.Exit:
        raise
    except Exception as exc:
        logger.error("classroom grades failed: %s", exc)
        raise typer.Exit(code=1)


@classroom_app.command("clone")
def classroom_clone(
    ctx: typer.Context,
    source_classroom_id: int = typer.Argument(
        ..., help="Source GitHub Classroom numeric ID to copy structure from"
    ),
    target_org: str = typer.Argument(
        ..., help="Target GitHub organization login to clone repos and assignments into"
    ),
    workspace: Optional[str] = typer.Option(
        None,
        "--workspace",
        help="Local org folder path to write classroom_setup.md (defaults to CWD)",
    ),
):
    """
    Clone a classroom's assignment structure into a new organization.

    For each assignment in the source classroom:
      1. Clones its starter-code repo into TARGET_ORG (skips if already exists)
      2. Generates a direct browser URL to create that assignment in the new classroom

    Since the GitHub Classroom API is read-only, classroom/assignment creation
    must be completed manually — this command gives you everything you need.

    Examples:
        $ classdock organizations classroom clone 12345 SOC-CS3030-Valle-FA26
        $ classdock organizations classroom clone 12345 SOC-CS3030-Valle-FA26 --workspace ~/courses/SOC-CS3030-Valle-FA26
    """
    import re as _re
    from pathlib import Path as _Path
    from rich.panel import Panel

    setup_logging(ctx.obj.get("verbose", False) if ctx.obj else False)
    dry_run = ctx.obj.get("dry_run", False) if ctx.obj else False

    try:
        token = _get_token()
        mgr = ClassroomManager(token=token)

        # Fetch source classroom
        classroom = mgr.get_classroom(source_classroom_id)
        if classroom is None:
            console.print(f"[red]Classroom {source_classroom_id} not found.[/red]")
            raise typer.Exit(code=1)

        assignments = mgr.list_assignments(source_classroom_id)
        if not assignments:
            console.print(
                f"[yellow]No assignments found in classroom '{classroom.name}'.[/yellow]"
            )
            return

        console.print(
            f"\nCloning [cyan]{len(assignments)}[/cyan] assignment(s) from "
            f"[bold]{classroom.name}[/bold] → [bold]{target_org}[/bold]\n"
        )

        # Find or prompt for the target classroom ID
        target_classrooms = mgr.list_classrooms_for_org(target_org)
        target_classroom_id: Optional[int] = None
        if target_classrooms:
            target_classroom_id = target_classrooms[0].id
            console.print(
                f"Found classroom [cyan]{target_classrooms[0].name}[/cyan] "
                f"(ID: {target_classroom_id}) in {target_org}"
            )
        else:
            console.print(
                f"[yellow]No classroom found for '{target_org}' yet.[/yellow] "
                f"Create one at: {ClassroomManager.new_classroom_url()}"
            )

        # Clone starter repos and build checklist
        tmpl_mgr = TemplateManager(token=token)
        rows = []

        for a in assignments:
            starter = a.starter_code_repo  # "owner/repo" or None
            cloned_status = "—"
            new_repo = None

            if starter and not dry_run:
                owner, _, repo_name = starter.partition("/")
                try:
                    result = tmpl_mgr.copy_template_repository(
                        source_owner=owner,
                        repo_name=repo_name,
                        target_org=target_org,
                    )
                    new_repo = f"{target_org}/{repo_name}"
                    cloned_status = "[green]✓ cloned[/green]" if result else "[red]✗ failed[/red]"
                except Exception:
                    new_repo = f"{target_org}/{repo_name}"
                    cloned_status = "[yellow]↩ exists[/yellow]"
            elif dry_run and starter:
                _, _, repo_name = starter.partition("/")
                new_repo = f"{target_org}/{repo_name}"
                cloned_status = "[dim][dry-run][/dim]"

            create_url = (
                ClassroomManager.assignment_creation_url(
                    target_classroom_id, new_repo
                )
                if target_classroom_id
                else ClassroomManager.new_classroom_url()
            )
            rows.append((a.title, a.type, a.deadline or "—", cloned_status, create_url))

        # Display results table
        table = Table(
            title=f"Assignment Checklist: {classroom.name} → {target_org}",
            show_header=True,
        )
        table.add_column("Assignment", style="cyan")
        table.add_column("Type", justify="center")
        table.add_column("Deadline")
        table.add_column("Starter Repo", justify="center")
        table.add_column("Create URL")

        for title, atype, deadline, status, url in rows:
            table.add_row(title, atype, deadline, status, url)

        console.print(table)

        # Write classroom_setup.md
        ws_path = _Path(workspace) if workspace else _Path.cwd()
        md_path = ws_path / "classroom_setup.md"
        if not dry_run:
            lines = [
                f"# Classroom Setup: {classroom.name} → {target_org}\n\n",
                "Create the following assignments in your new GitHub Classroom.\n\n",
                "| Assignment | Type | Deadline | Create URL |\n",
                "|---|---|---|---|\n",
            ]
            for title, atype, deadline, _, url in rows:
                lines.append(f"| {title} | {atype} | {deadline} | {url} |\n")
            md_path.write_text("".join(lines), encoding="utf-8")
            console.print(
                f"\n[dim]Checklist written to:[/dim] {md_path}"
            )

        console.print(
            Panel(
                f"[bold]Next steps:[/bold]\n\n"
                + (
                    f"  1. A classroom already exists for {target_org} — use the Create URLs above.\n"
                    if target_classroom_id
                    else f"  1. Create a classroom for [cyan]{target_org}[/cyan]:\n"
                    f"     {ClassroomManager.new_classroom_url()}\n"
                    f"  2. Then use the Create URLs above to add each assignment.\n"
                )
                + (f"\n  Checklist saved to: {md_path}" if not dry_run else ""),
                title="GitHub Classroom",
                border_style="blue",
            )
        )

    except GitHubClassroomAPIError as exc:
        console.print(f"[red]Classroom API error:[/red] {exc}")
        raise typer.Exit(code=1)
    except typer.Exit:
        raise
    except Exception as exc:
        logger.error("classroom clone failed: %s", exc)
        raise typer.Exit(code=1)
