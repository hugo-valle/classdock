"""
UI Components for the GitHub Classroom Setup Wizard.

This module provides consistent user interface components including
colors, progress indicators, and display screens. Uses Rich for output.
"""

import sys

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

_console = Console()
_err_console = Console(stderr=True)


class Colors:
    """Color constants (kept for backward compatibility)."""

    RED = "red"
    GREEN = "green"
    YELLOW = "yellow"
    BLUE = "blue"
    PURPLE = "magenta"
    CYAN = "cyan"
    GRAY = "white"
    NC = ""

    @classmethod
    def colorize(cls, text: str, color: str) -> str:
        """Apply color markup to text (no-op — Rich handles rendering)."""
        if color:
            return f"[{color}]{text}[/{color}]"
        return text


def print_colored(message: str, color: str = "", end: str = "\n") -> None:
    """Print colored message using Rich markup."""
    if color:
        _console.print(f"[{color}]{message}[/{color}]", end=end)
    else:
        _console.print(message, end=end)


def print_error(message: str) -> None:
    """Print error message in red."""
    _console.print(f":x: ERROR: {message}", style="red")


def print_success(message: str) -> None:
    """Print success message in green."""
    _console.print(f":white_check_mark: {message}", style="green")


def print_warning(message: str) -> None:
    """Print warning message in yellow."""
    _console.print(f":warning:  {message}", style="yellow")


def print_status(message: str) -> None:
    """Print status message in blue."""
    _console.print(f":information_source:  {message}", style="blue")


def print_header(message: str) -> None:
    """Print section header."""
    _console.print(f"\n:small_blue_diamond: {message}", style="cyan")


class ProgressTracker:
    """Track and display progress through wizard steps."""

    def __init__(self, total_steps: int = 8):
        self.total_steps = total_steps
        self.current_step = 0

    def show_progress(self, step_name: str) -> None:
        """Display progress indicator."""
        self.current_step += 1
        _console.rule(style="cyan")
        _console.print(
            f":clipboard: Step {self.current_step}/{self.total_steps}: {step_name}",
            style="magenta",
        )
        _console.rule(style="cyan")


def show_welcome() -> None:
    """Show welcome screen."""
    if sys.stdout.isatty():
        import os

        os.system("clear" if os.name == "posix" else "cls")

    content = Text.assemble(
        ("🚀 ClassDock Assignment Setup Wizard\n\n", "bold magenta"),
        (
            "Welcome! This wizard will help you configure ClassDock for managing\n",
            "white",
        ),
        ("a GitHub assignment: fetching student repos, secrets, and more.\n\n", "white"),
        ("✨ What this wizard will do:\n", "bold green"),
        ("   • Create assignment configuration file (assignment.conf)\n", "white"),
        ("   • Configure .gitignore to protect sensitive files\n", "white"),
        ("   • Set up secret management for instructor-only tests (optional)\n\n", "white"),
        ("📋 You'll need:\n", "bold blue"),
        ("   • Assignment name — the prefix used in student repo names\n", "white"),
        (
            "   • GitHub organization name where student repos live\n",
            "white",
        ),
        ("   • Template repository URL (optional — for reference)\n", "white"),
        ("   • GitHub personal access token with repo and org permissions\n", "white"),
        ("\nTip: run with --url <template-repo-url> to auto-fill org & name.\n", "dim"),
    )
    _console.print(Panel(content, border_style="cyan"))
    _console.print("[green]Press Enter to continue...[/green]")

    if sys.stdin.isatty():
        input()


def show_completion(config_values: dict, token_files: dict) -> None:
    """Show completion screen."""
    if sys.stdout.isatty():
        import os

        os.system("clear" if os.name == "posix" else "cls")

    lines = [
        ("🎉 Assignment Setup Complete!\n\n", "bold magenta"),
        (
            "Your assignment has been successfully configured\n",
            "white",
        ),
        ("with ClassDock. Here's what was created:\n\n", "white"),
        ("📁 Files Created:\n", "bold cyan"),
        ("   • assignment.conf - Complete assignment configuration\n", "white"),
    ]

    if config_values.get("USE_SECRETS") == "true":
        lines.append(
            ("   • Secrets configured (using centralized GitHub token)\n", "white")
        )

    lines += [
        ("   • .gitignore - Updated to protect sensitive files\n\n", "white"),
        ("🔑 Token Management:\n", "bold cyan"),
        ("   • Centralized token: ~/.config/classdock/token_config.json\n", "white"),
        ("   • No token files needed in repository\n\n", "white"),
        ("🚀 Next Steps:\n", "bold yellow"),
        ("   1. Run the complete workflow:\n", "white"),
        ("      classdock run\n\n", "bold"),
        ("   2. Or run individual tools:\n", "white"),
        ("      classdock fetch\n", "bold"),
        ("      classdock secrets add\n\n", "bold"),
        ("📚 Documentation:\n", "bold blue"),
        ("   • docs/ORCHESTRATOR-WORKFLOW.md - Complete workflow guide\n", "white"),
        ("   • docs/TOOLS-USAGE.md - Individual tool documentation\n", "white"),
        ("   • docs/SECRETS-MANAGEMENT.md - Secret management guide\n", "white"),
    ]

    content = Text.assemble(*lines)
    _console.print(Panel(content, border_style="green"))


def show_help():
    """Show help information."""
    help_text = """
GitHub Classroom Assignment Setup Wizard

DESCRIPTION:
    Interactive setup wizard for instructors to configure a new GitHub Classroom
    assignment with automated tools. Creates configuration files, sets up secure
    token storage, and configures .gitignore for instructor-only files.

USAGE:
    classdock setup [options]

OPTIONS:
    --help              Show this help message
    --version           Show version information

FEATURES:
    • Interactive prompts with intelligent defaults
    • Centralized token management (no token files in repo)
    • Automatic .gitignore configuration
    • Configuration validation and GitHub access testing
    • Support for multiple custom secrets/tokens
    • Modern, elegant interface with progress indicators

REQUIREMENTS:
    • GitHub token configured (via ~/.config/classdock/ or environment)
    • Write access to repository root directory
    • GitHub organization access permissions

GENERATED FILES:
    • assignment.conf - Complete assignment configuration
    • .gitignore - Updated to protect sensitive files

TOKEN MANAGEMENT:
    • Centralized: ~/.config/classdock/token_config.json
    • Environment: GITHUB_TOKEN variable
    • No token files stored in repository

NEXT STEPS:
    After running this setup wizard, use:
    • classdock run    - Complete automation workflow
    • classdock fetch  - Discover student repositories
    • classdock secrets add - Add secrets to student repos

DOCUMENTATION:
    • docs/ORCHESTRATOR-WORKFLOW.md - Complete workflow guide
    • docs/TOOLS-USAGE.md - Individual tool documentation
    • docs/SECRETS-MANAGEMENT.md - Secret management guide
"""
    _console.print(help_text)


def show_version():
    """Show version information."""
    from classdock import __version__

    _console.print(f"ClassDock v{__version__}")
    _console.print("GitHub assignment management automation CLI (Python)")
