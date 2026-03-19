"""
Enhanced CLI Interface for ClassDock GitHub Assignment Management.

This module provides:
- Comprehensive command-line interface organized by functional areas
- Modular command structure with intuitive subcommand organization
- Rich console output with progress tracking and error handling
- Legacy command support for backward compatibility
- Integration with all core ClassDock functionality including assignments,
  repositories, secrets, and automation workflows
"""

import sys
import typer
from pathlib import Path
from typing import Optional, List

from .utils import setup_logging, get_logger
from .config.global_config import load_global_config, get_global_config

# Initialize logger
logger = get_logger("cli")


def get_global_options(ctx: typer.Context) -> tuple[bool, bool]:
    """
    Helper to get verbose and dry_run from context.

    Accesses options from root context to work regardless of where
    --verbose and --dry-run were specified in the command.

    Args:
        ctx: Typer context

    Returns:
        tuple: (verbose: bool, dry_run: bool)
    """
    root_ctx = ctx.find_root()
    return (
        root_ctx.obj.get('verbose', False) if root_ctx.obj else False,
        root_ctx.obj.get('dry_run', False) if root_ctx.obj else False
    )


def load_student_repos(file_path: str = "student-repos.txt") -> List[str]:
    """
    Load student repository URLs from file.

    Args:
        file_path: Path to file containing repository URLs

    Returns:
        List of repository URLs

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    from pathlib import Path

    repo_file = Path(file_path)
    if not repo_file.exists():
        raise FileNotFoundError(f"Repository file not found: {file_path}")

    repos = []
    with open(repo_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                repos.append(line)

    return repos


def select_student_repo_interactive(repos: List[str]) -> Optional[str]:
    """
    Allow user to interactively select a repository from a list.

    Args:
        repos: List of repository URLs

    Returns:
        Selected repository URL or None if cancelled
    """
    if not repos:
        return None

    # Use questionary arrow-key selector when running in a real terminal
    import sys
    if sys.stdin.isatty():
        from .utils.prompt import prompt_select
        choices = [repo.split('/')[-1] + "  (" + repo + ")" for repo in repos]
        choices.append("Cancel")
        result = prompt_select("Select a student repository:", choices)
        if result is None or result == "Cancel":
            logger.info("Cancelled")
            return None
        # Extract the URL back from the choice string
        for repo in repos:
            if repo in result:
                student_name = repo.split('/')[-1]
                logger.info(f"Selected: {student_name}")
                return repo
        return None

    # Fallback: numbered list for non-TTY environments
    print("\n📚 Available student repositories:\n")
    for i, repo in enumerate(repos, 1):
        student_name = repo.split('/')[-1]
        print(f"  {i}. {student_name}")
        print(f"     {repo}")
    print("  0. Cancel")

    while True:
        try:
            choice = input("\n👉 Select a repository (enter number): ").strip()
            if not choice:
                continue
            choice_num = int(choice)
            if choice_num == 0:
                print("❌ Cancelled")
                return None
            if 1 <= choice_num <= len(repos):
                selected = repos[choice_num - 1]
                student_name = selected.split('/')[-1]
                print(f"✅ Selected: {student_name}")
                return selected
            else:
                print(f"⚠️  Please enter a number between 0 and {len(repos)}")
        except ValueError:
            print("⚠️  Please enter a valid number")
        except KeyboardInterrupt:
            print("\n❌ Cancelled")
            return None


def version_callback(value: bool):
    """Callback to handle --version flag."""
    if value:
        from . import __version__
        typer.echo(f"ClassDock {__version__}")
        typer.echo("Modular Python CLI for GitHub Classroom automation")
        typer.echo("https://github.com/hugo-valle/classdock")
        raise typer.Exit()


# Create the main Typer application
# NOTE: We define --verbose and --dry-run at both the main level AND in each subcommand callback.
# This allows flexible positioning - options work in BOTH positions:
#   - BEFORE subcommands: classdock --verbose assignments orchestrate
#   - AFTER subcommands: classdock assignments --verbose orchestrate
# Each callback merges options so they work from either position.
app = typer.Typer(
    help="ClassDock - Comprehensive automation suite for managing GitHub Classroom assignments.",
    no_args_is_help=False,
    rich_markup_mode="rich",
)


@app.callback()
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        callback=version_callback,
        help="Show the application version and exit."
    ),
    config_file: str = typer.Option(
        "assignment.conf",
        "--config",
        help="Configuration file to load (default: assignment.conf)"
    ),
    assignment_root: str = typer.Option(
        None,
        "--assignment-root",
        help="Root directory containing assignment.conf file"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Enable verbose output"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be done without executing"
    )
):
    """
    [bold cyan]ClassDock[/bold cyan] — GitHub Classroom automation suite.

    [bold]Common commands:[/bold]
      [cyan]classdock run[/cyan]     Run the full assignment workflow
      [cyan]classdock setup[/cyan]   Configure a new assignment
      [cyan]classdock fetch[/cyan]   Discover student repositories
      [cyan]classdock status[/cyan]  Show assignment dashboard
      [cyan]classdock token[/cyan]   Configure GitHub token

    [bold]Command groups:[/bold]
      [cyan]classdock assignments[/cyan]  Assignment lifecycle commands
      [cyan]classdock repos[/cyan]        Repository operations
      [cyan]classdock secrets[/cyan]      Secret management
      [cyan]classdock automation[/cyan]   Scheduling and batch processing
      [cyan]classdock roster[/cyan]       Student roster management
      [cyan]classdock config[/cyan]       Configuration and token management
    """
    # Set up logging first with verbose flag
    setup_logging(verbose=verbose)

    # Store global options in context for all commands
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['dry_run'] = dry_run
    ctx.obj['config_file'] = config_file
    ctx.obj['assignment_root'] = assignment_root

    # Skip configuration loading in resilient parsing mode (used internally by Click)
    if ctx.resilient_parsing:
        return

    # When invoked with no subcommand, launch interactive mode
    if ctx.invoked_subcommand is None:
        # First-run wizard (only in TTY)
        if sys.stdin.isatty():
            try:
                from .first_run import is_first_run, run_first_run_wizard
                if is_first_run():
                    run_first_run_wizard()
                    raise typer.Exit(0)
            except typer.Exit:
                raise
            except Exception:
                pass
            # Interactive main menu
            try:
                from .interactive import run_interactive
                exit_code = run_interactive()
                raise typer.Exit(exit_code or 0)
            except typer.Exit:
                raise
            except Exception:
                pass
        else:
            # Non-TTY with no subcommand: show help
            typer.echo(ctx.get_help())
            raise typer.Exit(0)
        return

    # Try to load global configuration (don't fail if not found, some commands create it)
    try:
        assignment_root_path = Path(
            assignment_root) if assignment_root else None

        # Context-aware config discovery: if config_file is the default and doesn't
        # exist in CWD, search parent directories for assignment.conf
        resolved_config = config_file
        if config_file == "assignment.conf" and not Path(config_file).exists():
            from .utils.paths import PathManager
            pm = PathManager()
            found = pm.find_config_file("assignment.conf")
            if found and found.parent != Path.cwd():
                resolved_config = str(found)
                logger.info(f"Found assignment.conf in {found.parent}")

        load_global_config(resolved_config, assignment_root_path)
        # Only log success at DEBUG level to avoid polluting help output
        logger.debug("✅ Global configuration loaded and ready")
    except FileNotFoundError:
        # Config file not found - this is OK for commands like 'assignments setup'
        logger.debug(
            f"Configuration file {config_file} not found - will be created by setup command")
    except Exception as e:
        logger.warning(f"Failed to load configuration: {e}")
        logger.debug(
            "Some commands may not work properly without configuration")


# Import sub-apps from command modules
from .commands.assignments import assignments_app
from .commands.repos import repos_app
from .commands.secrets import secrets_app
from .commands.automation import automation_app
from .commands.config import config_app
from .commands.roster import roster_app


# Register sub-apps on the root app
app.add_typer(assignments_app, name="assignments")
app.add_typer(repos_app, name="repos")
app.add_typer(secrets_app, name="secrets")
app.add_typer(automation_app, name="automation")
app.add_typer(config_app, name="config")
app.add_typer(roster_app, name="roster")


# ---------------------------------------------------------------------------
# Top-level shortcut commands
# ---------------------------------------------------------------------------

@app.command("run")
def shortcut_run(
    ctx: typer.Context,
    force_yes: bool = typer.Option(False, "--yes", "-y", help="Confirm all prompts automatically"),
    config_file: str = typer.Option("assignment.conf", "--config", "-c", help="Configuration file path"),
    step: Optional[str] = typer.Option(None, "--step", help="Execute only a specific step"),
    skip_steps: Optional[str] = typer.Option(None, "--skip", help="Skip specific steps (comma-separated)"),
) -> None:
    """Run the full assignment workflow (shortcut for [cyan]assignments orchestrate[/cyan])."""
    verbose, dry_run = get_global_options(ctx)
    setup_logging(verbose=verbose)
    try:
        from .services.assignment_service import AssignmentService
        service = AssignmentService(dry_run=dry_run, verbose=verbose)
        ok, message = service.orchestrate(
            config_file=config_file, force_yes=force_yes, step=step, skip_steps=skip_steps
        )
        if not ok:
            logger.error(message)
            raise typer.Exit(code=1)
        logger.info(f"✅ {message}")
    except typer.Exit:
        raise
    except Exception as e:
        logger.error(f"Workflow failed: {e}")
        raise typer.Exit(code=1)


@app.command("setup")
def shortcut_setup(
    ctx: typer.Context,
    url: Optional[str] = typer.Option(None, "--url", help="GitHub Classroom URL"),
    simplified: bool = typer.Option(False, "--simplified", help="Minimal-prompt setup"),
) -> None:
    """Configure a new assignment (shortcut for [cyan]assignments setup[/cyan])."""
    verbose, dry_run = get_global_options(ctx)
    setup_logging(verbose=verbose)
    try:
        from .services.assignment_service import AssignmentService
        service = AssignmentService(dry_run=dry_run, verbose=verbose)
        ok, message = service.setup(url=url, simplified=simplified)
        if not ok:
            logger.error(message)
            raise typer.Exit(code=1)
        logger.info(f"✅ {message}")
    except typer.Exit:
        raise
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        raise typer.Exit(code=1)


@app.command("fetch")
def shortcut_fetch(
    ctx: typer.Context,
    config_file: str = typer.Option("assignment.conf", "--config", "-c", help="Configuration file path"),
) -> None:
    """Discover student repositories (shortcut for [cyan]repos fetch[/cyan])."""
    verbose, dry_run = get_global_options(ctx)
    setup_logging(verbose=verbose)
    try:
        from .services.repos_service import ReposService
        service = ReposService(dry_run=dry_run, verbose=verbose)
        ok, message = service.fetch(config_file=config_file)
        if not ok:
            logger.error(message)
            raise typer.Exit(code=1)
        logger.info(f"✅ {message}")
    except typer.Exit:
        raise
    except Exception as e:
        logger.error(f"Fetch failed: {e}")
        raise typer.Exit(code=1)


@app.command("status")
def shortcut_status(
    config_file: str = typer.Option("assignment.conf", "--config", "-c", help="Configuration file path"),
) -> None:
    """Show assignment dashboard."""
    from .dashboard import render_dashboard
    render_dashboard(config_file=config_file)


@app.command("token")
def shortcut_token(
    ctx: typer.Context,
) -> None:
    """Configure your GitHub Personal Access Token (shortcut for [cyan]config check-token[/cyan])."""
    verbose, dry_run = get_global_options(ctx)
    setup_logging(verbose=verbose)
    try:
        from .utils.token_manager import GitHubTokenManager
        tm = GitHubTokenManager()
        info = tm.get_token_info()
        if info:
            from rich.console import Console as _C
            _C().print("[green]Token is configured.[/green]")
            days = info.get("days_remaining")
            if days is not None:
                color = "red" if days <= 7 else ("yellow" if days <= 30 else "green")
                _C().print(f"Status: [{color}]valid ({days} days remaining)[/{color}]")
            else:
                _C().print("Status: [green]valid (no expiration)[/green]")
        else:
            from .utils.error_display import error_token_not_found
            error_token_not_found()
            raise typer.Exit(code=1)
    except typer.Exit:
        raise
    except Exception as e:
        logger.error(f"Token check failed: {e}")
        raise typer.Exit(code=1)


@app.command("completion")
def shortcut_completion(
    shell: Optional[str] = typer.Argument(
        None, help="Shell to generate completion for: bash, zsh, fish"
    ),
    install: bool = typer.Option(False, "--install", help="Install completion into shell config file"),
) -> None:
    """Generate or install shell tab-completion scripts."""
    import subprocess
    from rich.console import Console as _C
    _c = _C()

    if shell is None:
        import os
        shell = os.environ.get("SHELL", "bash").split("/")[-1]
        _c.print(f"Detected shell: [cyan]{shell}[/cyan]")

    shell = shell.lower()
    if shell not in ("bash", "zsh", "fish"):
        _c.print(f"[red]Unsupported shell '{shell}'. Choose bash, zsh, or fish.[/red]")
        raise typer.Exit(code=1)

    env_var = "_{}_COMPLETE".format("CLASSDOCK".upper())
    env_val = f"{shell}_source"

    result = subprocess.run(
        ["classdock"],
        env={**__import__("os").environ, env_var: env_val},
        capture_output=True,
        text=True,
    )
    script = result.stdout

    if not install:
        _c.print(script)
        return

    # Install into shell config
    home = Path.home()
    if shell == "bash":
        rc_file = home / ".bashrc"
        snippet = f'\neval "$(_CLASSDOCK_COMPLETE=bash_source classdock)"\n'
    elif shell == "zsh":
        rc_file = home / ".zshrc"
        snippet = f'\neval "$(_CLASSDOCK_COMPLETE=zsh_source classdock)"\n'
    else:  # fish
        rc_file = home / ".config" / "fish" / "completions" / "classdock.fish"
        rc_file.parent.mkdir(parents=True, exist_ok=True)
        snippet = script

    if shell == "fish":
        rc_file.write_text(snippet)
    else:
        with open(rc_file, "a") as f:
            f.write(snippet)

    _c.print(f"[green]Completion installed to {rc_file}[/green]")
    _c.print(f"Restart your shell or run [bold]source {rc_file}[/bold] to activate.")



if __name__ == "__main__":
    app()
