"""
Rich error panels with recovery suggestions.

Provides structured error display for the four most common failure modes:
  - token not found
  - config not found
  - student-repos.txt not found
  - cron not installed
"""

from rich.console import Console
from rich.panel import Panel

_console = Console(stderr=True)


def _show(title: str, body: str, border: str = "red") -> None:
    _console.print(
        Panel(body, title=f"[bold red]{title}[/bold red]", border_style=border)
    )


def error_token_not_found() -> None:
    """Display a structured error for a missing GitHub token."""
    _show(
        "Error: GitHub token not configured",
        "ClassDock needs a GitHub Personal Access Token to interact with the API.\n\n"
        "[bold]To fix this:[/bold]\n"
        "  • Run [bold]classdock token[/bold] to configure your token interactively\n"
        "  • Or run [bold]classdock config set-token <TOKEN>[/bold] directly\n\n"
        "Generate a token at: [dim]https://github.com/settings/tokens[/dim]\n"
        "Required scopes: [cyan]repo[/cyan], [cyan]read:org[/cyan]",
    )


def error_config_not_found(config_file: str = "assignment.conf") -> None:
    """Display a structured error for a missing assignment config."""
    _show(
        "Error: Config not found",
        f"No [bold]{config_file}[/bold] found in this directory or any parent.\n\n"
        "[bold]To fix this:[/bold]\n"
        "  • Run [bold]classdock setup[/bold] to create a new assignment configuration\n"
        "  • Or [bold]cd[/bold] into an existing assignment directory",
    )


def error_repos_file_not_found(repos_file: str = "student-repos.txt") -> None:
    """Display a structured error for a missing student repos file."""
    _show(
        "Error: Student repos not found",
        f"No [bold]{repos_file}[/bold] found in the current directory.\n\n"
        "[bold]To fix this:[/bold]\n"
        "  • Run [bold]classdock fetch[/bold] to discover student repositories\n"
        "  • Or run [bold]classdock repos fetch[/bold]",
    )


def error_cron_not_installed() -> None:
    """Display a structured error when cron is not available."""
    _show(
        "Error: Cron not installed",
        "No cron daemon was found on this system.\n\n"
        "[bold]To fix this:[/bold]\n"
        "  • On Linux: install [cyan]cron[/cyan] or [cyan]cronie[/cyan] via your package manager\n"
        "  • On macOS: cron is built-in; check that it has Full Disk Access in System Preferences\n"
        "  • As an alternative, use [bold]classdock automation schedule[/bold] for manual scheduling",
    )
