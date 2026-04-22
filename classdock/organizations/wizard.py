"""
Organization setup wizard for ClassDock.

Guides the instructor interactively through the full workflow:

  1. Verify GitHub token scopes
  2. Detect or prompt for the master template folder
  3. List and select template repos to carry forward
  4. Build and validate the new org name
  5. Create the local semester org folder
  6. Clone selected templates locally
  7. Create the GitHub organization (requires admin:org scope)
  8. Fork each local repo to the new GitHub org and mark as template
  9. Guide through manual GitHub Classroom setup (API limitation)
  10. Generate assignment.conf in the new org folder

All I/O is done via ``rich`` console for a consistent look.
"""

import logging
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..utils.ui_components import print_error, print_status, print_success
from .classroom import ClassroomManager
from .manager import OrganizationManager
from .models import Organization, SetupResult, TemplateRepo, WorkspaceFolder
from .templates import TemplateManager
from .validators import OrgNameValidator
from .workspace import WorkspaceManager

logger = logging.getLogger(__name__)
console = Console()


class OrganizationSetupWizard:
    """
    Interactive wizard for setting up a new GitHub organization and local workspace.

    Args:
        token: GitHub personal access token.
        dry_run: If True, print what would happen but make no changes.
    """

    def __init__(self, token: Optional[str] = None, dry_run: bool = False):
        self.token = token
        self.dry_run = dry_run
        self._org_manager = OrganizationManager(token=token)
        self._template_manager = TemplateManager(token=token)
        self._workspace_manager = WorkspaceManager()

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def run(self) -> SetupResult:
        """
        Execute the full organization setup wizard.

        Returns:
            SetupResult summarising the outcome.
        """
        self._show_org_welcome()

        # Step 1 — token scopes
        if not self._step_verify_token():
            return SetupResult(
                success=False,
                error_message="Token verification failed. Run `classdock config token` to update.",
            )

        # Step 2 — master folder
        master_folder = self._step_select_master_folder()
        if master_folder is None:
            return SetupResult(
                success=False, error_message="No master template folder selected."
            )

        # Step 2b — pick the source GitHub org (filters the repo list)
        source_org = self._step_select_source_org(master_folder)
        if not source_org:
            return SetupResult(
                success=False, error_message="No source organization selected."
            )

        # Step 3 — select template repos (filtered to source_org only)
        selected_repos = self._step_select_templates(
            master_folder, source_org=source_org
        )
        if not selected_repos:
            console.print("[yellow]No templates selected. Setup cancelled.[/yellow]")
            return SetupResult(success=False, error_message="No templates selected.")

        # Step 4 — org name
        org_name = self._step_collect_org_name()
        if not org_name:
            return SetupResult(
                success=False, error_message="No organization name provided."
            )

        # Step 5 — create local folder
        base_dir = master_folder.path.parent
        org_folder = self._step_create_org_folder(base_dir, org_name)
        if org_folder is None:
            return SetupResult(
                success=False, error_message="Failed to create local org folder."
            )

        # Step 6 — clone templates locally
        self._step_clone_locally(selected_repos, org_folder)

        # Step 7 — create GitHub organization
        github_org = self._step_create_github_org(org_name)
        if github_org is None:
            console.print(
                "[yellow]GitHub organization not created. "
                "Proceed with manual org creation and re-run.[/yellow]"
            )

        # Step 8 — fork repos to GitHub org (each repo forked from its own source org)
        clone_result = None
        if github_org is not None:
            clone_result = self._step_fork_to_github(
                target_org=org_name,
                repos=selected_repos,
            )

        # Step 9 — classroom guidance
        self._step_classroom_guidance(
            org_name, org_folder=org_folder, source_org=source_org
        )

        # Step 10 — generate assignment.conf
        self._step_generate_config(org_folder, org_name, github_org)

        console.print()
        console.print(
            Panel(
                f"[green bold]✓ Organization workspace ready![/green bold]\n\n"
                f"  Local folder:  {org_folder.path}\n"
                f"  GitHub org:    https://github.com/{org_name}\n\n"
                f"  Next: [bold]classdock assignments setup[/bold]",
                title="Setup Complete",
                border_style="green",
            )
        )

        return SetupResult(
            organization=github_org,
            workspace_folder=org_folder,
            clone_result=clone_result,
            success=True,
        )

    # ------------------------------------------------------------------
    # Welcome screen
    # ------------------------------------------------------------------

    def _show_org_welcome(self) -> None:
        """Display the organization setup wizard welcome panel."""
        content = Text.assemble(
            ("🏫 ClassDock — New Semester Organization Setup\n\n", "bold magenta"),
            (
                "This wizard sets up a GitHub organization and local workspace\n",
                "white",
            ),
            (
                "for a new semester, ready for GitHub Classroom assignments.\n\n",
                "white",
            ),
            ("✨ What this wizard will do:\n", "bold green"),
            ("   • Verify your GitHub token scopes\n", "white"),
            ("   • Detect your master template folder (e.g., CS3030/)\n", "white"),
            ("   • Let you select which template repos to carry forward\n", "white"),
            ("   • Build and validate the new organization name\n", "white"),
            ("   • Create a local semester org folder\n", "white"),
            ("   • Clone selected templates locally\n", "white"),
            ("   • Guide you to create the GitHub organization\n", "white"),
            ("   • Fork templates into the new org as GitHub templates\n\n", "white"),
            ("📋 You'll need:\n", "bold blue"),
            ("   • A master template folder with cloned assignment repos\n", "white"),
            ("   • New organization name (e.g., soc-cs3030-valle-su26)\n", "white"),
            ("   • GitHub token with repo + admin:org scopes\n", "white"),
            ("   • A billing email for the new organization\n", "white"),
        )
        console.print(Panel(content, border_style="cyan"))

    # ------------------------------------------------------------------
    # Individual wizard steps
    # ------------------------------------------------------------------

    def _step_verify_token(self) -> bool:
        """Verify GitHub token scopes. Return False if critical scopes are missing."""
        print_status("Verifying GitHub token scopes…")
        scopes = self._org_manager.get_token_scopes()

        table = Table(title="Token Scopes", show_header=True)
        table.add_column("Scope", style="cyan")
        table.add_column("Status", style="bold")

        required = {"repo": "Repository access", "admin:org": "Organization creation"}
        all_ok = True
        for scope, label in required.items():
            if scope in scopes:
                table.add_row(f"{scope} ({label})", "[green]✓ present[/green]")
            else:
                table.add_row(f"{scope} ({label})", "[red]✗ missing[/red]")
                all_ok = False

        console.print(table)

        if not all_ok:
            print_error(
                "Token is missing required scopes.\n"
                "Visit https://github.com/settings/tokens and add: admin:org, repo"
            )
        else:
            print_success("Token scopes verified.")

        return all_ok

    def _step_select_master_folder(self) -> Optional[WorkspaceFolder]:
        """Detect or prompt for the master template folder."""
        print_status("Looking for master template folder…")

        detected = self._workspace_manager.find_master_folder()
        if detected:
            console.print(f"  Found: [cyan]{detected.path}[/cyan]")
            if typer.confirm("  Use this as the master template folder?", default=True):
                return detected

        # Manual entry
        while True:
            raw = typer.prompt(
                "  Enter the path to your master template folder",
                default=str(Path.cwd()),
            )
            path = Path(raw).expanduser().resolve()
            if not path.is_dir():
                print_error(f"Directory not found: {path}")
                continue

            wf = self._workspace_manager.find_master_folder(start=path)
            if wf:
                return wf

            # Path exists but isn't marked — offer to initialize it
            if typer.confirm(
                f"  '{path}' is not a master folder. Initialize it as one?",
                default=True,
            ):
                course_code = typer.prompt("  Course code (e.g., CS3030)")
                return self._workspace_manager.init_master_folder(path, course_code)

    def _step_select_source_org(self, master_folder: WorkspaceFolder) -> Optional[str]:
        """
        Ask the user which source GitHub organization the template repos belong to.

        Detects all distinct owners from the local git remotes and presents them
        as a numbered list.  The most common owner is offered as the default.
        """
        all_repos = master_folder.repos
        if not all_repos:
            return None

        # Count how many repos each owner has
        from collections import Counter

        owner_counts = Counter(r.owner for r in all_repos if r.owner)

        if not owner_counts:
            return typer.prompt(
                "  Enter the source GitHub organization (e.g., cs3030-master)"
            )

        # Sort by frequency (most common first)
        ranked = owner_counts.most_common()

        if len(ranked) == 1:
            org = ranked[0][0]
            console.print(f"\n  Source GitHub org detected: [cyan]{org}[/cyan]")
            if typer.confirm(
                f"  Use '{org}' as the source organization?", default=True
            ):
                return org
            return typer.prompt("  Enter the source GitHub organization")

        console.print(
            "\n[bold]Source GitHub organizations found in master folder:[/bold]\n"
        )
        for i, (owner, count) in enumerate(ranked, start=1):
            console.print(f"  {i}. [cyan]{owner}[/cyan]  ({count} repo(s))")

        console.print()
        raw = typer.prompt(
            "  Select source org number",
            default="1",
        )
        try:
            idx = int(raw.strip()) - 1
            if 0 <= idx < len(ranked):
                return ranked[idx][0]
        except ValueError:
            pass

        return typer.prompt("  Enter the source GitHub organization")

    def _step_select_templates(
        self, master_folder: WorkspaceFolder, source_org: Optional[str] = None
    ) -> List[TemplateRepo]:
        """List repos that belong to source_org and let the user multi-select."""
        all_repos = master_folder.repos

        # Filter to the chosen source org
        repos = (
            [r for r in all_repos if r.owner == source_org] if source_org else all_repos
        )

        if not repos:
            console.print(
                f"[yellow]No repos from '{source_org}' found in {master_folder.path}.[/yellow]\n"
                "  Make sure the repos are cloned there with the correct git remote."
            )
            return []

        console.print(
            f"\nFound [bold]{len(repos)}[/bold] repo(s) from "
            f"[cyan]{source_org}[/cyan] in master folder:\n"
        )
        for i, repo in enumerate(repos, start=1):
            console.print(f"  {i:2d}. [cyan]{repo.name}[/cyan]")

        console.print()
        raw = typer.prompt(
            "Select repos to include (comma-separated numbers, or 'all')",
            default="all",
        )

        if raw.strip().lower() == "all":
            return repos

        selected = []
        for part in raw.split(","):
            try:
                idx = int(part.strip()) - 1
                if 0 <= idx < len(repos):
                    selected.append(repos[idx])
            except ValueError:
                pass

        if not selected:
            console.print("[yellow]No valid selections.[/yellow]")
        return selected

    def _step_collect_org_name(self) -> Optional[str]:
        """Prompt for and validate the new GitHub organization name."""
        console.print(
            "\n[bold]Organization Naming Convention:[/bold]\n"
            "  [program-][course][-section]-[last_name]-[semester][year]\n"
            "  Example: soc-cs3030-valle-su26\n"
        )

        # Offer component-by-component guidance
        if typer.confirm("Build org name from components?", default=True):
            return self._build_org_name_interactively()

        # Free-form entry with validation
        while True:
            name = typer.prompt("Enter organization name").strip()
            result = OrgNameValidator.validate(name)
            if result.is_valid:
                return name
            print_error(result.error)
            if not typer.confirm("Try again?", default=True):
                return None

    def _build_org_name_interactively(self) -> Optional[str]:
        """Prompt for each component individually and build a validated name."""
        program_raw = typer.prompt(
            "  PROGRAM (3-4 letters, e.g., soc — press Enter to skip)", default=""
        )
        program = program_raw.strip().lower() or None
        course = (
            typer.prompt("  COURSE (letters + 4 digits, e.g., cs3030)").strip().lower()
        )
        section_raw = typer.prompt(
            "  SECTION (single digit, press Enter to skip)", default=""
        )
        section = section_raw.strip() or None
        last_name = (
            typer.prompt("  LAST NAME (your last name, e.g., valle)").strip().lower()
        )
        semester = typer.prompt("  SEMESTER (fa / sp / su)").strip().lower()
        year = typer.prompt("  YEAR (2-digit, e.g., 26)").strip()

        try:
            name = OrgNameValidator.build(
                course, last_name, semester, year, program, section
            )
            console.print(f"\n  Generated name: [green bold]{name}[/green bold]")
            if typer.confirm("  Use this name?", default=True):
                return name
            return None
        except ValueError as exc:
            print_error(str(exc))
            return None

    def _step_create_org_folder(
        self, base: Path, org_name: str
    ) -> Optional[WorkspaceFolder]:
        """Create the local semester org folder."""
        if self.dry_run:
            console.print(f"[dry-run] Would create folder: {base / org_name}")
            return WorkspaceFolder(path=base / org_name, org_name=org_name)

        existing = self._workspace_manager.find_org_folder(base, org_name)
        if existing:
            console.print(f"  [yellow]Folder already exists: {existing.path}[/yellow]")
            if not typer.confirm("  Continue using existing folder?", default=True):
                return None
            return existing

        try:
            folder = self._workspace_manager.create_org_folder(base, org_name)
            print_success(f"Created local folder: {folder.path}")
            return folder
        except Exception as exc:
            print_error(f"Failed to create folder: {exc}")
            return None

    def _step_clone_locally(
        self, repos: List[TemplateRepo], org_folder: WorkspaceFolder
    ) -> None:
        """Clone selected templates into the local org folder."""
        if self.dry_run:
            console.print(
                f"[dry-run] Would clone {len(repos)} repo(s) into {org_folder.path}"
            )
            return

        print_status(f"Cloning {len(repos)} template(s) locally…")

        def progress(cur, total, name):
            console.print(f"  [{cur}/{total}] Cloning {name}…")

        repos_with_url = [r for r in repos if r.clone_url]
        if not repos_with_url:
            console.print(
                "[yellow]  No clone URLs found on local repos. "
                "Skipping local clone step.[/yellow]"
            )
            return

        self._workspace_manager.clone_templates_locally(
            repos_with_url, org_folder.path, progress_callback=progress
        )

    def _step_create_github_org(self, org_name: str) -> Optional[Organization]:
        """Create the GitHub organization, handling known errors gracefully."""
        print_status(f"Creating GitHub organization '{org_name}'…")

        if self.dry_run:
            console.print(f"[dry-run] Would create GitHub org: {org_name}")
            return Organization(login=org_name)

        # Check if org already exists
        if self._org_manager.organization_exists(org_name):
            console.print(
                f"  [yellow]Organization '{org_name}' already exists on GitHub.[/yellow]"
            )
            if typer.confirm("  Use existing organization?", default=True):
                return self._org_manager.get_organization(org_name)
            return None

        billing_email = typer.prompt("  Billing contact email for the new organization")

        try:
            org = self._org_manager.create_organization(
                login=org_name,
                billing_email=billing_email,
            )
            print_success(f"Organization created: https://github.com/{org_name}")
            return org
        except NotImplementedError as exc:
            console.print(f"\n[yellow]{exc}[/yellow]\n")
            console.print(
                "Once you have created the organization manually, press Enter to continue."
            )
            typer.prompt(
                "  Press Enter when the org is ready", default="", show_default=False
            )
            # Verify the org now exists
            if self._org_manager.organization_exists(org_name):
                print_success(f"Organization '{org_name}' confirmed on GitHub.")
                return self._org_manager.get_organization(org_name)
            else:
                print_error(
                    f"Organization '{org_name}' not found. Continuing without GitHub org."
                )
                return None
        except PermissionError as exc:
            print_error(str(exc))
            return None
        except Exception as exc:
            print_error(f"Organization creation failed: {exc}")
            if typer.confirm(
                "  Continue setup without creating the org?", default=True
            ):
                return None
            raise

    def _step_fork_to_github(self, target_org: str, repos: List[TemplateRepo]):
        """
        Fork selected repos to the new GitHub org.

        Each repo is forked from its own source org (read from the git remote),
        so repos from different organizations are handled correctly.
        """
        print_status(f"Forking {len(repos)} repo(s) to '{target_org}'…")

        if self.dry_run:
            for repo in repos:
                console.print(
                    f"  [dim][dry-run] Would fork {repo.owner}/{repo.name} → {target_org}[/dim]"
                )
            return None

        from .models import CloneResult

        result = CloneResult(total=len(repos))

        for idx, repo in enumerate(repos, start=1):
            console.print(
                f"  [{idx}/{len(repos)}] Forking [cyan]{repo.owner}/{repo.name}[/cyan]…"
            )
            forked = self._template_manager.copy_template_repository(
                source_owner=repo.owner,
                repo_name=repo.name,
                target_org=target_org,
            )
            if forked is None:
                error_msg = (
                    f"Failed to copy '{repo.owner}/{repo.name}' into '{target_org}'"
                )
                result.add_failure(error_msg)
                console.print(f"    [red]✗ {error_msg}[/red]")
                continue

            # Brief pause then mark as template
            import time

            time.sleep(3)
            ok = self._template_manager.make_template(target_org, forked.name)
            forked.is_template = ok
            result.add_success(forked)
            console.print(f"    [green]✓ {target_org}/{forked.name}[/green]")

        if result.failed > 0:
            console.print(f"\n  [yellow]{result.failed} fork(s) failed:[/yellow]")
            for err in result.errors:
                console.print(f"    • {err}")

        print_success(
            f"Forked {result.successful}/{result.total} repo(s) to '{target_org}'"
        )
        return result

    def _step_classroom_guidance(
        self,
        org_name: str,
        org_folder: Optional[WorkspaceFolder] = None,
        source_org: Optional[str] = None,
    ) -> None:
        """
        Guide the instructor through GitHub Classroom setup.

        If the source org has an accessible classroom, offer to pre-populate
        a clone checklist.  Otherwise fall back to static guidance.
        """
        # Try to find a source classroom to clone from
        source_classroom_id: Optional[int] = None
        if source_org and self.token:
            try:
                classroom_mgr = ClassroomManager(token=self.token)
                source_classrooms = classroom_mgr.list_classrooms_for_org(source_org)
                if source_classrooms:
                    sc = source_classrooms[0]
                    console.print(
                        f"\nFound classroom [cyan]{sc.name}[/cyan] in source org "
                        f"[bold]{source_org}[/bold]."
                    )
                    clone_it = typer.confirm(
                        "Generate assignment checklist from this classroom?",
                        default=True,
                    )
                    if clone_it:
                        source_classroom_id = sc.id
            except Exception as exc:
                logger.debug("Could not check source classrooms: %s", exc)

        if source_classroom_id and self.token:
            self._generate_classroom_checklist(
                source_classroom_id=source_classroom_id,
                target_org=org_name,
                org_folder=org_folder,
            )
        else:
            # Static fallback guidance
            console.print(
                Panel(
                    "[bold]GitHub Classroom — Manual Setup Required[/bold]\n\n"
                    "The GitHub Classroom API does not support classroom creation.\n"
                    "Please follow these steps:\n\n"
                    f"  1. Go to [link=https://classroom.github.com/classrooms/new]"
                    f"https://classroom.github.com/classrooms/new[/link]\n"
                    f"  2. Select organization: [cyan]{org_name}[/cyan]\n"
                    f"  3. Name your classroom (e.g., 'CS3030 Fall 2026')\n"
                    f"  4. Click 'Create classroom'\n"
                    f"  5. Create assignments using the template repos now in '{org_name}'\n\n"
                    f"  Once done, run: [bold]classdock assignments setup[/bold]\n\n"
                    f"  To clone an existing classroom structure later:\n"
                    f"  [bold]classdock organizations classroom clone <ID> {org_name}[/bold]",
                    title="Next Steps",
                    border_style="blue",
                )
            )

    def _generate_classroom_checklist(
        self,
        source_classroom_id: int,
        target_org: str,
        org_folder: Optional[WorkspaceFolder] = None,
    ) -> None:
        """Clone starter repos from a source classroom and generate a setup checklist."""
        from pathlib import Path as _Path

        classroom_mgr = ClassroomManager(token=self.token)
        assignments = classroom_mgr.list_assignments(source_classroom_id)
        if not assignments:
            console.print("[yellow]No assignments found in source classroom.[/yellow]")
            return

        # Find target classroom (may not exist yet)
        target_classrooms = classroom_mgr.list_classrooms_for_org(target_org)
        target_classroom_id = target_classrooms[0].id if target_classrooms else None

        rows = []
        for a in assignments:
            starter = a.starter_code_repo
            cloned_status = "—"
            new_repo: Optional[str] = None

            if starter and not self.dry_run:
                owner, _, repo_name = starter.partition("/")
                try:
                    result = self._template_manager.copy_template_repository(
                        source_owner=owner,
                        repo_name=repo_name,
                        target_org=target_org,
                    )
                    new_repo = f"{target_org}/{repo_name}"
                    cloned_status = "✓ cloned" if result else "✗ failed"
                except Exception:
                    new_repo = f"{target_org}/{repo_name}"
                    cloned_status = "↩ exists"
            elif starter:
                _, _, repo_name = starter.partition("/")
                new_repo = f"{target_org}/{repo_name}"
                cloned_status = "[dry-run]"

            create_url = (
                ClassroomManager.assignment_creation_url(target_classroom_id, new_repo)
                if target_classroom_id
                else ClassroomManager.new_classroom_url()
            )
            rows.append((a.title, a.type, a.deadline or "—", cloned_status, create_url))

        # Display table
        table = Table(title=f"Assignment Checklist → {target_org}", show_header=True)
        table.add_column("Assignment", style="cyan")
        table.add_column("Type", justify="center")
        table.add_column("Deadline")
        table.add_column("Starter Repo", justify="center")
        table.add_column("Create URL")
        for title, atype, deadline, status, url in rows:
            table.add_row(title, atype, deadline, status, url)
        console.print(table)

        # Write classroom_setup.md
        ws_path = org_folder.path if org_folder else _Path.cwd()
        ws_path.mkdir(parents=True, exist_ok=True)
        md_path = ws_path / "classroom_setup.md"
        if not self.dry_run:
            lines = [
                f"# Classroom Setup → {target_org}\n\n",
                "Create the following assignments in your GitHub Classroom.\n\n",
                "| Assignment | Type | Deadline | Create URL |\n",
                "|---|---|---|---|\n",
            ]
            for title, atype, deadline, _, url in rows:
                lines.append(f"| {title} | {atype} | {deadline} | {url} |\n")
            md_path.write_text("".join(lines), encoding="utf-8")

        console.print(
            Panel(
                "[bold]Next steps:[/bold]\n\n"
                + (
                    f"  A classroom already exists for {target_org}.\n"
                    f"  Use the Create URLs above to add each assignment.\n"
                    if target_classroom_id
                    else f"  1. Create a classroom for [cyan]{target_org}[/cyan]:\n"
                    f"     {ClassroomManager.new_classroom_url()}\n"
                    f"  2. Use the Create URLs in the checklist above.\n"
                )
                + (f"\n  Checklist saved to: {md_path}" if not self.dry_run else ""),
                title="GitHub Classroom",
                border_style="blue",
            )
        )

    def _step_generate_config(
        self,
        org_folder: WorkspaceFolder,
        org_name: str,
        github_org: Optional[Organization],
    ) -> None:
        """Write a minimal assignment.conf into the org folder."""
        if self.dry_run:
            console.print(f"[dry-run] Would write assignment.conf to {org_folder.path}")
            return

        config_path = org_folder.path / "assignment.conf"
        if config_path.exists():
            logger.debug("assignment.conf already exists; skipping generation.")
            return

        content = (
            "# ClassDock Assignment Configuration\n"
            f"# Generated for organization: {org_name}\n\n"
            f"GITHUB_ORGANIZATION={org_name}\n"
            "CLASSROOM_URL=\n"
            "TEMPLATE_REPO_URL=\n"
            "ASSIGNMENT_NAME=\n"
            "STUDENT_FILES=\n\n"
            "# Workflow\n"
            "STEP_SYNC_TEMPLATE=true\n"
            "STEP_DISCOVER_REPOS=true\n"
            "STEP_MANAGE_SECRETS=false\n"
            "STEP_ASSIST_STUDENTS=false\n"
        )
        config_path.write_text(content, encoding="utf-8")
        print_success(f"Generated assignment.conf at {config_path}")
