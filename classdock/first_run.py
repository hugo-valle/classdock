"""
First-run guided experience for ClassDock.

Detects whether ClassDock has been initialized on this machine and, if not,
shows a welcome panel and offers a quick-start menu.
"""

from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from .utils.prompt import prompt_select

_console = Console()
_MARKER = Path.home() / ".config" / "classdock" / ".initialized"

_CHOICES = [
    "Configure your GitHub token (required)",
    "See what ClassDock can do",
    "Skip for now",
]


def is_first_run() -> bool:
    """Return True when the marker file does not exist."""
    return not _MARKER.exists()


def mark_initialized() -> None:
    """Write the marker file so first-run won't trigger again."""
    _MARKER.parent.mkdir(parents=True, exist_ok=True)
    _MARKER.touch()


def run_first_run_wizard() -> None:
    """Show welcome panel and quick-start menu on first run."""
    _console.print(
        Panel(
            "[bold magenta]Welcome to ClassDock![/bold magenta]\n\n"
            "ClassDock automates GitHub Classroom assignment management:\n"
            "  • Discover student repositories\n"
            "  • Distribute secrets to student repos\n"
            "  • Schedule automated workflows\n"
            "  • Manage student rosters\n\n"
            "Run [bold]classdock --help[/bold] anytime for the full command reference.",
            border_style="cyan",
        )
    )

    choice = prompt_select("What would you like to do first?", _CHOICES)

    if choice == "Configure your GitHub token (required)":
        _console.print(
            "\nRun the following command to set your GitHub Personal Access Token:\n\n"
            "  [bold]classdock token[/bold]\n\n"
            "You can generate a token at: https://github.com/settings/tokens\n"
            "Required scopes: [cyan]repo[/cyan], [cyan]read:org[/cyan]\n"
        )
    elif choice == "See what ClassDock can do":
        _console.print(
            "\n[bold]Key commands:[/bold]\n"
            "  [bold]classdock setup[/bold]        — configure a new assignment\n"
            "  [bold]classdock run[/bold]           — run the full workflow\n"
            "  [bold]classdock fetch[/bold]         — discover student repos\n"
            "  [bold]classdock status[/bold]        — show dashboard\n"
            "  [bold]classdock roster import[/bold] — import student roster from CSV\n"
            "  [bold]classdock token[/bold]         — configure GitHub token\n\n"
            "Run [bold]classdock <command> --help[/bold] for details on any command.\n"
        )

    mark_initialized()
