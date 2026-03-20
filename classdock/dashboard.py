"""
ClassDock status dashboard.

Renders a Rich overview of the current assignment environment including
token status, discovered repos, roster stats, secrets, and cron jobs.
"""

from pathlib import Path
from typing import Optional

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

_console = Console()


def render_dashboard(config_file: str = "assignment.conf") -> None:
    """Render the status dashboard to stdout."""
    from .utils.paths import PathManager

    pm = PathManager()

    # Locate config file (walk up if needed)
    conf_path: Optional[Path] = None
    if Path(config_file).exists():
        conf_path = Path(config_file).resolve()
    else:
        conf_path = pm.find_config_file(config_file)

    if conf_path is None:
        _console.print(
            Panel(
                "[yellow]No [bold]assignment.conf[/bold] found in this directory or any parent.\n\n"
                "To get started:\n"
                "  [bold]classdock setup[/bold]   — create a new assignment configuration",
                title="[red]ClassDock — not in an assignment directory[/red]",
                border_style="red",
            )
        )
        return

    # --- Load config values ---
    assignment_name = "—"
    org = "—"
    student_repos_file = "student-repos.txt"
    try:
        from .config.global_config import get_global_config, load_global_config

        load_global_config(str(conf_path))
        cfg = get_global_config()
        if cfg:
            assignment_name = cfg.assignment_name or "—"
            org = cfg.github_organization or "—"
    except Exception:
        pass

    # --- Token status ---
    token_line = "[dim]not configured[/dim]"
    try:
        from .utils.token_manager import GitHubTokenManager

        tm = GitHubTokenManager()
        info = tm.get_token_info()
        if info:
            days = info.get("days_remaining")
            if days is not None:
                color = "red" if days <= 7 else ("yellow" if days <= 30 else "green")
                token_line = f"[{color}]valid ({days} days remaining)[/{color}]"
            else:
                token_line = "[green]valid (no expiration)[/green]"
    except Exception:
        pass

    # --- Student repos ---
    repos_file = Path(student_repos_file)
    repos_line = "[dim]not discovered[/dim]"
    if repos_file.exists():
        try:
            import time

            count = sum(
                1
                for ln in repos_file.read_text().splitlines()
                if ln.strip() and not ln.startswith("#")
            )
            mtime = repos_file.stat().st_mtime
            age_h = (time.time() - mtime) / 3600
            age_str = f"{age_h:.0f}h ago" if age_h < 48 else f"{age_h / 24:.0f}d ago"
            repos_line = f"[cyan]{count}[/cyan] discovered  ([dim]{repos_file.name}, {age_str}[/dim])"
        except Exception:
            repos_line = "[yellow]file exists but unreadable[/yellow]"

    # --- Roster ---
    roster_line = "[dim]not initialized[/dim]"
    try:
        from .services.roster_service import RosterService

        rs = RosterService()
        stats = rs.get_statistics(org if org != "—" else None)
        total = stats.get("total_students", 0)
        roster_line = (
            f"[cyan]{total}[/cyan] students  ([dim]~/.config/classdock/roster.db[/dim])"
        )
    except Exception:
        pass

    # --- Secrets ---
    secrets_line = "[dim]none configured[/dim]"
    try:
        from .services.secrets_service import SecretsService

        ss = SecretsService()
        names = ss.list_secret_names()
        if names:
            secrets_line = ", ".join(f"[cyan]{n}[/cyan]" for n in names)
    except Exception:
        pass

    # --- Cron jobs ---
    cron_table: Optional[Table] = None
    try:
        from .services.automation_service import AutomationService

        asvc = AutomationService()
        jobs = asvc.cron_status()
        if jobs:
            cron_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
            cron_table.add_column("name", style="cyan")
            cron_table.add_column("schedule", style="dim")
            cron_table.add_column("last", style="dim")
            cron_table.add_column("status")
            for job in jobs:
                status_icon = "[green]✓[/green]" if job.get("ok") else "[red]✗[/red]"
                cron_table.add_row(
                    job.get("name", "?"),
                    job.get("schedule", "?"),
                    job.get("last_run", "never"),
                    status_icon,
                )
    except Exception:
        pass

    # --- Build the panel ---
    lines = [
        f"[bold]Assignment:[/bold] [cyan]{assignment_name}[/cyan]   "
        f"[bold]Org:[/bold] [cyan]{org}[/cyan]",
        f"[bold]Config:[/bold] [dim]{conf_path}[/dim]   "
        f"[bold]Token:[/bold] {token_line}",
        "",
        f"[bold]Student Repos:[/bold]  {repos_line}",
        f"[bold]Roster:[/bold]        {roster_line}",
        f"[bold]Secrets:[/bold]       {secrets_line}",
    ]

    content = "\n".join(lines)
    _console.print(
        Panel(
            content,
            title="[bold blue]ClassDock Status[/bold blue]",
            border_style="blue",
        )
    )

    if cron_table:
        _console.print("[bold]Automation:[/bold]")
        _console.print(cron_table)

    # --- Next steps ---
    _console.print(
        Panel(
            "[bold]classdock run[/bold]          Run the full workflow\n"
            "[bold]classdock fetch[/bold]        Re-discover student repos\n"
            "[bold]classdock roster sync[/bold]  Link repos to roster",
            title="Next steps",
            border_style="dim",
        )
    )
