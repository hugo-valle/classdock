"""
Interactive mode for ClassDock.

Launched when `classdock` is run with no subcommand in a TTY.
Provides a guided menu-driven experience for common workflows.
"""

from typing import Optional

from rich.console import Console

from .utils.prompt import prompt_select

_console = Console()

_MENU_CHOICES = [
    "Run the full assignment workflow",
    "Set up a new assignment",
    "Check assignment status",
    "Fetch student repositories",
    "Manage roster",
    "Configure token",
    "Show help",
    "Exit",
]


def run_interactive() -> Optional[int]:
    """
    Launch the interactive guided menu.

    Returns the exit code (0 = success, 1 = error, None = clean exit).
    """
    _console.print("\n[bold cyan]ClassDock[/bold cyan] — GitHub Classroom automation\n")

    choice = prompt_select("What would you like to do?", _MENU_CHOICES)

    if choice is None or choice == "Exit":
        return 0

    import typer

    if choice == "Run the full assignment workflow":
        from .services.assignment_service import AssignmentService

        service = AssignmentService()
        ok, message = service.orchestrate(config_file="assignment.conf")
        if not ok:
            _console.print(f"[red]{message}[/red]")
            return 1
        _console.print(f"[green]{message}[/green]")
        return 0

    if choice == "Set up a new assignment":
        from .services.assignment_service import AssignmentService

        service = AssignmentService()
        ok, message = service.setup()
        if not ok:
            _console.print(f"[red]{message}[/red]")
            return 1
        _console.print(f"[green]{message}[/green]")
        return 0

    if choice == "Check assignment status":
        from .dashboard import render_dashboard

        render_dashboard()
        return 0

    if choice == "Fetch student repositories":
        from .services.repos_service import ReposService

        service = ReposService()
        ok, message = service.fetch()
        if not ok:
            _console.print(f"[red]{message}[/red]")
            return 1
        _console.print(f"[green]{message}[/green]")
        return 0

    if choice == "Manage roster":
        _console.print(
            "\nRoster commands:\n"
            "  [bold]classdock roster list[/bold]   — list students\n"
            "  [bold]classdock roster import[/bold] — import from CSV\n"
            "  [bold]classdock roster sync[/bold]   — sync repos with roster\n"
            "  [bold]classdock roster status[/bold] — show statistics\n"
        )
        return 0

    if choice == "Configure token":
        _console.print(
            "\nTo set your GitHub token run:\n"
            "  [bold]classdock token[/bold]\n"
            "or\n"
            "  [bold]classdock config set-token <TOKEN>[/bold]\n"
        )
        return 0

    if choice == "Show help":
        _console.print(
            "\nRun [bold]classdock --help[/bold] for full command reference.\n"
            "Run [bold]classdock <group> --help[/bold] for group-specific help.\n"
        )
        return 0

    return 0
