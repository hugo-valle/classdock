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
from .assignments.setup import AssignmentSetup
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

    print("\n📚 Available student repositories:\n")
    for i, repo in enumerate(repos, 1):
        # Extract student name from URL
        student_name = repo.split('/')[-1]
        print(f"  {i}. {student_name}")
        print(f"     {repo}")

    print(f"\n  0. Cancel")

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
    no_args_is_help=True
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
    ClassDock - Comprehensive automation suite for managing GitHub Classroom assignments.

    This tool automatically loads configuration from assignment.conf file and makes
    all configuration variables globally available to all commands.
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

    # Skip configuration loading if showing main command help only
    # Check if this is main help (no subcommand) vs subcommand help
    subcommands = ['assignments', 'repos', 'secrets', 'automation', 'config']
    has_subcommand = any(cmd in sys.argv for cmd in subcommands)
    is_help_request = '--help' in sys.argv or '-h' in sys.argv

    # Only skip config loading for main command help (no subcommand specified)
    if is_help_request and not has_subcommand:
        return

    # Try to load global configuration (don't fail if not found, some commands create it)
    try:
        assignment_root_path = Path(
            assignment_root) if assignment_root else None
        load_global_config(config_file, assignment_root_path)
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


# Create subcommand groups
assignments_app = typer.Typer(
    help="Assignment setup, orchestration, and management commands")
repos_app = typer.Typer(
    help="Repository operations and collaborator management commands")
secrets_app = typer.Typer(help="Secret and token management commands")
automation_app = typer.Typer(
    help="Automation, scheduling, and batch processing commands")
config_app = typer.Typer(
    help="Configuration and token management commands")


# Callback for config commands with global options
@config_app.callback()
def config_callback(
    ctx: typer.Context,
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
    """Configuration and token management commands."""
    # Store options in context for subcommands to access
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose or ctx.obj.get('verbose', False)
    ctx.obj['dry_run'] = dry_run or ctx.obj.get('dry_run', False)


# Callback for assignments commands with global options
@assignments_app.callback()
def assignments_callback(
    ctx: typer.Context,
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
    """Assignment setup, orchestration, and management commands."""
    # Store options in context for subcommands to access
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose or ctx.obj.get('verbose', False)
    ctx.obj['dry_run'] = dry_run or ctx.obj.get('dry_run', False)


# Callback for repos commands with global options
@repos_app.callback()
def repos_callback(
    ctx: typer.Context,
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
    """Repository operations and collaborator management commands."""
    # Store options in context for subcommands to access
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose or ctx.obj.get('verbose', False)
    ctx.obj['dry_run'] = dry_run or ctx.obj.get('dry_run', False)


# Callback for secrets commands with global options
@secrets_app.callback()
def secrets_callback(
    ctx: typer.Context,
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
    """Secret and token management commands."""
    # Store options in context for subcommands to access
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose or ctx.obj.get('verbose', False)
    ctx.obj['dry_run'] = dry_run or ctx.obj.get('dry_run', False)


# Callback for automation commands with global options
@automation_app.callback()
def automation_callback(
    ctx: typer.Context,
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
    """Automation, scheduling, and batch processing commands."""
    # Store options in context for subcommands to access
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose or ctx.obj.get('verbose', False)
    ctx.obj['dry_run'] = dry_run or ctx.obj.get('dry_run', False)


# Add subcommand groups to main app
app.add_typer(assignments_app, name="assignments")
app.add_typer(repos_app, name="repos")
app.add_typer(secrets_app, name="secrets")
app.add_typer(automation_app, name="automation")
app.add_typer(config_app, name="config")


# Assignment Commands
@assignments_app.command("setup")
def assignment_setup(
    ctx: typer.Context,
    url: str = typer.Option(
        None,
        "--url",
        help="GitHub Classroom URL for simplified setup (auto-extracts organization and assignment info)"
    ),
    simplified: bool = typer.Option(
        False,
        "--simplified",
        help="Use simplified setup wizard with minimal prompts"
    )
):
    """
    Launch interactive wizard to configure a new assignment.

    This command initializes an interactive setup wizard that guides users through
    the complete process of configuring a new GitHub Classroom assignment.

    Examples:
        $ classdock assignments setup
        $ classdock assignments setup --simplified
        $ classdock assignments setup --url "https://classroom.github.com/..."
    """
    # Access universal options from root context
    verbose, dry_run = get_global_options(ctx)

    setup_logging(verbose)

    # Delegate to AssignmentService (including dry-run logic)
    try:
        from .services.assignment_service import AssignmentService

        service = AssignmentService(dry_run=dry_run, verbose=verbose)
        ok, message = service.setup(url=url, simplified=simplified)

        if not ok:
            logger.error(message)
            raise typer.Exit(code=1)

        logger.info(f"✅ {message}")

    except Exception as e:
        logger.error(f"Assignment setup failed: {e}")
        raise typer.Exit(code=1)


@assignments_app.command("validate-config")
def assignment_validate_config(
    ctx: typer.Context,
    config_file: str = typer.Option(
        "assignment.conf", "--config-file", "-c", help="Configuration file path to validate"
    )
):
    """
    Validate assignment configuration file.

    Example:
        $ classdock assignments validate-config
        $ classdock assignments validate-config --config-file custom.conf
    """
    # Access universal options from root context
    verbose, dry_run = get_global_options(ctx)

    setup_logging(verbose)

    # Get assignment_root from parent context if it was specified
    assignment_root = ctx.parent.parent.params.get(
        'assignment_root', None) if ctx.parent and ctx.parent.parent else None

    # Resolve config file path relative to assignment_root if specified
    if assignment_root and not Path(config_file).is_absolute():
        config_file = str(Path(assignment_root) / config_file)

    if dry_run:
        logger.info(
            f"DRY RUN: Would validate configuration file: {config_file}")
        return

    # Delegate to AssignmentService
    try:
        from .services.assignment_service import AssignmentService

        service = AssignmentService(dry_run=dry_run, verbose=verbose)
        ok, message = service.validate_config(config_file=config_file)

        if not ok:
            logger.error(message)
            raise typer.Exit(code=1)

        logger.info(f"✅ {message}")

    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        raise typer.Exit(code=1)


@assignments_app.command("orchestrate")
def assignment_orchestrate(
    ctx: typer.Context,
    force_yes: bool = typer.Option(
        False, "--yes", "-y", help="Automatically confirm all prompts"),
    step: str = typer.Option(
        None, "--step", help="Execute only a specific step (sync, discover, secrets, assist, cycle)"),
    skip_steps: str = typer.Option(
        None, "--skip", help="Skip specific steps (comma-separated: sync,discover,secrets,assist,cycle)"),
    config_file: str = typer.Option(
        "assignment.conf", "--config", "-c", help="Configuration file path")
):
    """
    Execute complete assignment workflow with comprehensive orchestration.

    This command runs the full assignment management workflow including repository
    synchronization, student repository discovery, secrets deployment, and 
    assistance operations. It provides the primary automation interface for
    managing GitHub Classroom assignments end-to-end.

    Example:
        $ classdock assignments --dry-run --verbose orchestrate
        $ classdock assignments orchestrate --step discover
        $ classdock assignments orchestrate --skip sync,assist
        $ classdock assignments orchestrate --config my-assignment.conf
    """
    # Get universal options from root context
    verbose, dry_run = get_global_options(ctx)

    setup_logging(verbose=verbose)
    logger.info("Starting assignment orchestration")

    # Delegate to AssignmentService
    try:
        from .services.assignment_service import AssignmentService

        service = AssignmentService(dry_run=dry_run, verbose=verbose)
        ok, message = service.orchestrate(
            config_file=config_file,
            force_yes=force_yes,
            step=step,
            skip_steps=skip_steps
        )

        if not ok:
            logger.error(message)
            raise typer.Exit(code=1)

        logger.info(f"✅ {message}")

    except Exception as e:
        logger.error(f"Assignment orchestration failed: {e}")
        raise typer.Exit(code=1)


@assignments_app.command("help-student")
def help_student(
    ctx: typer.Context,
    repo_url: Optional[str] = typer.Argument(
        None, help="Student repository URL (or leave empty to select from student-repos.txt)"),
    one_student: bool = typer.Option(
        False, "--one-student", help="Use template directly (bypass classroom repository)"),
    auto_confirm: bool = typer.Option(
        False, "--yes", "-y", help="Automatically confirm all prompts"),
    repo_file: str = typer.Option(
        "student-repos.txt", "--file", "-f",
        help="File containing student repository URLs for interactive selection"),
    config_file: str = typer.Option(
        "assignment.conf", "--config", "-c", help="Configuration file path")
):
    """
    Help a specific student with repository updates.

    If no repository URL is provided, you'll be prompted to select from student-repos.txt.

    Example:
        $ classdock assignments help-student
        $ classdock assignments help-student https://github.com/org/assignment-student123
        $ classdock assignments help-student --one-student https://github.com/org/assignment-student123
    """
    # Access universal options from root context
    verbose, dry_run = get_global_options(ctx)

    setup_logging(verbose)

    # If no repo_url provided, load from file and allow selection
    if not repo_url:
        try:
            repos = load_student_repos(repo_file)
            if not repos:
                logger.error(f"No repositories found in {repo_file}")
                logger.info("💡 To generate a student repository list, run:")
                logger.info("   $ classdock repos fetch")
                raise typer.Exit(code=1)

            repo_url = select_student_repo_interactive(repos)
            if not repo_url:
                raise typer.Exit(code=0)  # User cancelled

        except FileNotFoundError:
            logger.error(f"Repository file not found: {repo_file}")
            logger.info("💡 To generate a student repository list, run:")
            logger.info("   $ classdock repos fetch")
            raise typer.Exit(code=1)

    # Delegate to AssignmentService
    try:
        from .services.assignment_service import AssignmentService

        service = AssignmentService(dry_run=dry_run, verbose=verbose)
        ok, message = service.help_student(
            repo_url=repo_url,
            one_student=one_student,
            auto_confirm=auto_confirm,
            config_file=config_file
        )

        if not ok:
            logger.error(message)
            raise typer.Exit(code=1)

        logger.info(f"✅ {message}")

    except Exception as e:
        logger.error(f"Student assistance failed: {e}")
        raise typer.Exit(code=1)


@assignments_app.command("help-students")
def help_students(
    ctx: typer.Context,
    repo_file: str = typer.Option(
        "student-repos.txt", "--file", "-f",
        help="File containing student repository URLs (default: student-repos.txt)"),
    auto_confirm: bool = typer.Option(
        False, "--yes", "-y", help="Automatically confirm all prompts"),
    config_file: str = typer.Option(
        "assignment.conf", "--config", "-c", help="Configuration file path")
):
    """
    Help multiple students with repository updates (batch processing).

    By default, uses student-repos.txt which is generated by 'repos fetch'.
    You can specify a different file with --file option.

    Note: If you don't have a student-repos.txt file, generate one first by running:
        $ classdock repos fetch

    Example:
        $ classdock assignments help-students
        $ classdock assignments help-students --yes
        $ classdock assignments help-students --file custom-repos.txt
    """
    # Access universal options from root context
    verbose, dry_run = get_global_options(ctx)

    setup_logging(verbose)

    # Check if repo_file exists
    from pathlib import Path
    if not Path(repo_file).exists():
        logger.error(f"Repository file not found: {repo_file}")
        logger.info("💡 To generate a student repository list, run:")
        logger.info("   $ classdock repos fetch")
        raise typer.Exit(code=1)

    # Delegate to AssignmentService
    try:
        from .services.assignment_service import AssignmentService

        service = AssignmentService(dry_run=dry_run, verbose=verbose)
        ok, message = service.help_students(
            repo_file=repo_file,
            auto_confirm=auto_confirm,
            config_file=config_file
        )

        if not ok:
            logger.error(message)
            raise typer.Exit(code=1)

        logger.info(f"✅ {message}")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        logger.info("💡 To generate a student repository list, run:")
        logger.info("   $ classdock repos fetch")
        raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"Batch student assistance failed: {e}")
        raise typer.Exit(code=1)


@assignments_app.command("check-student")
def check_student(
    ctx: typer.Context,
    repo_url: Optional[str] = typer.Argument(
        None, help="Student repository URL (or leave empty to select from student-repos.txt)"),
    repo_file: str = typer.Option(
        "student-repos.txt", "--file", "-f",
        help="File containing student repository URLs for interactive selection"),
    config_file: str = typer.Option(
        "assignment.conf", "--config", "-c", help="Configuration file path")
):
    """
    Check the status of a student repository.

    If no repository URL is provided, you'll be prompted to select from student-repos.txt.

    Example:
        $ classdock assignments check-student
        $ classdock assignments check-student https://github.com/org/assignment-student123
    """
    # Access universal options from root context
    verbose, dry_run = get_global_options(ctx)

    setup_logging(verbose)

    # If no repo_url provided, load from file and allow selection
    if not repo_url:
        try:
            repos = load_student_repos(repo_file)
            if not repos:
                logger.error(f"No repositories found in {repo_file}")
                logger.info("💡 To generate a student repository list, run:")
                logger.info("   $ classdock repos fetch")
                raise typer.Exit(code=1)

            repo_url = select_student_repo_interactive(repos)
            if not repo_url:
                raise typer.Exit(code=0)  # User cancelled

        except FileNotFoundError:
            logger.error(f"Repository file not found: {repo_file}")
            logger.info("💡 To generate a student repository list, run:")
            logger.info("   $ classdock repos fetch")
            raise typer.Exit(code=1)

    # Delegate to AssignmentService
    try:
        from .services.assignment_service import AssignmentService

        service = AssignmentService(dry_run=dry_run, verbose=verbose)
        ok, message = service.check_student(
            repo_url=repo_url,
            config_file=config_file
        )

        if not ok:
            logger.error(message)
            # Check if it's an accessibility issue vs update needed
            if "not accessible" in message:
                raise typer.Exit(code=1)
            else:
                raise typer.Exit(code=2)  # Needs update

        logger.info(f"✅ {message}")

    except Exception as e:
        logger.error(f"Student status check failed: {e}")
        raise typer.Exit(code=1)


@assignments_app.command("student-instructions")
def student_instructions(
    ctx: typer.Context,
    repo_url: Optional[str] = typer.Argument(
        None, help="Student repository URL (or leave empty to select from student-repos.txt)"),
    output_file: Optional[str] = typer.Option(
        None, "--output", "-o", help="Save instructions to file"),
    repo_file: str = typer.Option(
        "student-repos.txt", "--file", "-f",
        help="File containing student repository URLs for interactive selection"),
    config_file: str = typer.Option(
        "assignment.conf", "--config", "-c", help="Configuration file path")
):
    """
    Generate update instructions for a student.

    This command generates detailed instructions that can be sent to a student
    to help them update their repository manually. The instructions include
    multiple methods and troubleshooting tips.

    If no repository URL is provided, you'll be prompted to select from student-repos.txt.

    Args:
        repo_url: URL of the student repository
        output_file: Optional file to save instructions to
        repo_file: File containing student repository URLs for interactive selection
        config_file: Path to configuration file

    Example:
        $ classdock assignments student-instructions
        $ classdock assignments student-instructions https://github.com/org/assignment-student123
        $ classdock assignments student-instructions https://github.com/org/assignment-student123 -o instructions.txt
    """
    # Access universal options from root context
    verbose, dry_run = get_global_options(ctx)
    setup_logging(verbose=verbose)

    if dry_run:
        logger.info("DRY RUN: Would generate student instructions")
        if repo_url:
            logger.info(f"DRY RUN: Repository: {repo_url}")
        if output_file:
            logger.info(f"DRY RUN: Would save to: {output_file}")
        return

    # If no repo_url provided, load from file and allow selection
    if not repo_url:
        try:
            repos = load_student_repos(repo_file)
            if not repos:
                logger.error(f"No repositories found in {repo_file}")
                logger.info("💡 To generate a student repository list, run:")
                logger.info("   $ classdock repos fetch")
                raise typer.Exit(code=1)

            repo_url = select_student_repo_interactive(repos)
            if not repo_url:
                raise typer.Exit(code=0)  # User cancelled

        except FileNotFoundError:
            logger.error(f"Repository file not found: {repo_file}")
            logger.info("💡 To generate a student repository list, run:")
            logger.info("   $ classdock repos fetch")
            raise typer.Exit(code=1)

    logger.info("Generating student instructions")

    try:
        from .assignments.student_helper import StudentUpdateHelper

        # Initialize helper
        config_path = Path(config_file) if config_file else None
        helper = StudentUpdateHelper(config_path)

        # Generate instructions
        instructions = helper.generate_student_instructions(repo_url)

        # Output instructions
        if output_file:
            with open(output_file, 'w') as f:
                f.write(instructions)
            logger.info(f"Instructions saved to: {output_file}")
        else:
            print(instructions)

    except ImportError as e:
        logger.error(f"Failed to import student helper: {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"Failed to generate instructions: {e}")
        raise typer.Exit(code=1)


@assignments_app.command("check-classroom")
def check_classroom(
    ctx: typer.Context,
    config_file: str = typer.Option(
        "assignment.conf", "--config", "-c", help="Configuration file path")
):
    """
    Check if the classroom repository is ready for student updates.

    This command verifies that the classroom repository is accessible and
    compares its state with the template repository to ensure it's ready
    for student assistance operations.

    Args:
        config_file: Path to configuration file

    Example:
        $ classdock assignments check-classroom
    """
    # Access universal options from root context
    verbose, dry_run = get_global_options(ctx)
    setup_logging(verbose=verbose)

    if dry_run:
        logger.info("DRY RUN: Would check classroom repository status")
        return

    logger.info("Checking classroom repository status")

    try:
        from .assignments.student_helper import StudentUpdateHelper

        # Initialize helper
        config_path = Path(config_file) if config_file else None
        helper = StudentUpdateHelper(config_path)

        # Validate configuration
        if not helper.validate_configuration():
            logger.error("Configuration validation failed")
            raise typer.Exit(code=1)

        # Check classroom status
        is_ready = helper.check_classroom_ready()

        if is_ready:
            logger.info("✅ Classroom repository is ready")
        else:
            logger.error("❌ Classroom repository is not ready")
            raise typer.Exit(code=1)

    except ImportError as e:
        logger.error(f"Failed to import student helper: {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"Classroom status check failed: {e}")
        raise typer.Exit(code=1)


@assignments_app.command("cycle-collaborator")
def cycle_single_collaborator(
    ctx: typer.Context,
    repo_url: Optional[str] = typer.Argument(
        None, help="Repository URL to cycle collaborator permissions for (or leave empty to select from student-repos.txt)"),
    username: Optional[str] = typer.Argument(
        None, help="Username to cycle permissions for (auto-extracted from URL if not provided)"),
    force: bool = typer.Option(
        False, "--force", help="Force cycling even when access appears correct"),
    repo_file: str = typer.Option(
        "student-repos.txt", "--file", "-f",
        help="File containing student repository URLs for interactive selection"),
    config_file: str = typer.Option(
        "assignment.conf", "--config", "-c", help="Configuration file path")
):
    """
    Cycle collaborator permissions for a single repository.

    This command fixes repository access issues by cycling collaborator permissions.
    It intelligently detects when cycling is needed and only performs the operation
    when necessary, unless force mode is enabled.

    If no repository URL is provided, you'll be prompted to select from student-repos.txt.
    The username is automatically extracted from the repository URL if not explicitly provided.

    Args:
        repo_url: URL of the repository to cycle permissions for (auto-selected if omitted)
        username: Username to cycle permissions for (auto-extracted if not provided)
        force: Force cycling even when access appears correct
        repo_file: File containing student repository URLs for interactive selection
        config_file: Path to configuration file

    Supports universal options: --verbose, --dry-run

    Example:
        $ classdock assignments cycle-collaborator
        $ classdock assignments cycle-collaborator https://github.com/org/repo-student123
        $ classdock assignments cycle-collaborator https://github.com/org/repo student123 --force
    """
    # Access universal options from root context
    verbose, dry_run = get_global_options(ctx)

    setup_logging(verbose=verbose)

    logger.info("Cycling single repository collaborator permissions")

    # If no repo_url provided, load from file and allow selection
    if not repo_url:
        try:
            repos = load_student_repos(repo_file)
            if not repos:
                logger.error(f"No repositories found in {repo_file}")
                logger.info("💡 To generate a student repository list, run:")
                logger.info("   $ classdock repos fetch")
                raise typer.Exit(code=1)

            repo_url = select_student_repo_interactive(repos)
            if not repo_url:
                raise typer.Exit(code=0)  # User cancelled

        except FileNotFoundError:
            logger.error(f"Repository file not found: {repo_file}")
            logger.info("💡 To generate a student repository list, run:")
            logger.info("   $ classdock repos fetch")
            raise typer.Exit(code=1)

    # Extract username from URL if not provided
    if not username:
        try:
            # Extract username from URL (e.g., https://github.com/org/assignment-username -> username)
            url_parts = repo_url.rstrip('/').split('/')
            repo_name = url_parts[-1]
            # Try to extract username after last dash
            if '-' in repo_name:
                username = repo_name.split('-')[-1]
                logger.info(f"Extracted username from URL: {username}")
            else:
                logger.error("Could not extract username from repository URL")
                logger.error(
                    "Please provide username explicitly: cycle-collaborator <repo_url> <username>")
                raise typer.Exit(code=1)
        except (IndexError, AttributeError) as e:
            logger.error(f"Failed to parse repository URL: {e}")
            raise typer.Exit(code=1)

    if verbose:
        logger.debug(
            f"Verbose mode enabled for cycling collaborator {username} on {repo_url}")

    if dry_run:
        logger.info(
            f"DRY RUN: Would cycle collaborator {username} on {repo_url}")
        logger.info(f"DRY RUN: Force mode: {force}")
        logger.info(f"DRY RUN: Config file: {config_file}")
        return

    try:
        from .assignments.cycle_collaborator import CycleCollaboratorManager

        # Initialize manager
        config_path = Path(config_file) if config_file else None
        manager = CycleCollaboratorManager(config_path, auto_confirm=True)

        # Validate configuration
        if not manager.validate_configuration():
            logger.error("Configuration validation failed")
            raise typer.Exit(code=1)

        # Cycle permissions
        result = manager.cycle_single_repository(repo_url, username, force)

        # Display result
        manager.display_cycle_result(result)

        # Exit with appropriate code
        if result.result.value == "success":
            logger.info("✅ Collaborator cycling completed successfully")
        elif result.result.value == "skipped":
            logger.info("ℹ️ Collaborator cycling skipped - no action needed")
        else:
            logger.error("❌ Collaborator cycling failed")
            raise typer.Exit(code=1)

    except ImportError as e:
        logger.error(f"Failed to import cycle collaborator manager: {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"Collaborator cycling failed: {e}")
        raise typer.Exit(code=1)


@assignments_app.command("cycle-collaborators")
def cycle_multiple_collaborators(
    ctx: typer.Context,
    batch_file: str = typer.Argument(
        "student-repos.txt",
        help="File containing repository URLs or usernames (default: student-repos.txt)"),
    repo_url_mode: bool = typer.Option(
        False, "--repo-urls", help="Treat batch file as repository URLs (extract usernames)"),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force cycling even when access appears correct"),
    config_file: str = typer.Option(
        "assignment.conf", "--config", "-c", help="Configuration file path")
):
    """
    Cycle collaborator permissions for multiple repositories (batch processing).

    This command processes a file containing either repository URLs or usernames
    and cycles collaborator permissions for each entry. It provides intelligent
    detection of access issues and only cycles when necessary.

    By default, uses student-repos.txt which is generated by 'repos fetch'.
    You can specify a different file as an argument.

    The batch file format depends on the mode:
    - Username mode (default): One username per line
    - Repository URL mode (--repo-urls): One repository URL per line

    Args:
        batch_file: Path to file containing repository URLs or usernames (default: student-repos.txt)
        repo_url_mode: Treat file as repository URLs instead of usernames
        force: Force cycling even when access appears correct
        dry_run: Preview actions without making changes
        verbose: Enable detailed logging
        Supports universal options: --verbose, --dry-run

    Example:
        $ classdock assignments cycle-collaborators
        $ classdock assignments cycle-collaborators --repo-urls
        $ classdock assignments cycle-collaborators custom-repos.txt --repo-urls --force
    """
    # Access universal options from root context
    verbose, dry_run = get_global_options(ctx)

    setup_logging(verbose=verbose)
    logger.info("Cycling multiple repository collaborator permissions")

    try:
        from .assignments.cycle_collaborator import CycleCollaboratorManager

        # Initialize manager
        config_path = Path(config_file) if config_file else None
        manager = CycleCollaboratorManager(config_path, auto_confirm=True)

        # Skip validation in dry-run mode
        if not dry_run:
            # Validate configuration
            if not manager.validate_configuration():
                logger.error("Configuration validation failed")
                raise typer.Exit(code=1)

        batch_file_path = Path(batch_file)
        if not batch_file_path.exists():
            logger.error(f"Batch file not found: {batch_file}")
            raise typer.Exit(code=1)

        if dry_run:
            logger.info(
                "DRY RUN: Would cycle collaborator permissions for batch")
            logger.info(f"Batch file: {batch_file}")
            logger.info(f"Repository URL mode: {repo_url_mode}")
            logger.info(f"Force mode: {force}")
            return

        # Process batch file
        summary = manager.batch_cycle_from_file(
            batch_file_path, repo_url_mode, force)

        # Display summary
        manager.display_batch_summary(summary)

        # Exit with appropriate code
        if summary.failed_operations > 0:
            logger.warning(
                f"Completed with {summary.failed_operations} failures")
            raise typer.Exit(code=1)
        else:
            logger.info("✅ Batch collaborator cycling completed successfully")

    except ImportError as e:
        logger.error(f"Failed to import cycle collaborator manager: {e}")
        raise typer.Exit(code=1)
    except FileNotFoundError as e:
        logger.error(f"Batch file not found: {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"Batch collaborator cycling failed: {e}")
        raise typer.Exit(code=1)


@assignments_app.command("check-repository-access")
def check_repository_access(
    ctx: typer.Context,
    repo_url: Optional[str] = typer.Argument(
        None, help="Repository URL to check access for (or leave empty to select from student-repos.txt)"),
    username: Optional[str] = typer.Argument(
        None, help="Username to check access for (auto-extracted from URL if not provided)"),
    repo_file: str = typer.Option(
        "student-repos.txt", "--file", "-f",
        help="File containing student repository URLs for interactive selection"),
    config_file: str = typer.Option(
        "assignment.conf", "--config", "-c", help="Configuration file path")
):
    """
    Check repository access status for a specific user.

    This command checks whether a user has proper access to a repository,
    including collaborator status and pending invitations. It provides
    detailed status information to help diagnose access issues.

    If no repository URL is provided, you'll be prompted to select from student-repos.txt.
    The username is automatically extracted from the repository URL if not explicitly provided.

    Args:
        repo_url: URL of the repository to check
        username: Username to check access for (auto-extracted if not provided)
        repo_file: File containing student repository URLs for interactive selection
        config_file: Path to configuration file

    Example:
        $ classdock assignments check-repository-access
        $ classdock assignments check-repository-access https://github.com/org/assignment-student123
        $ classdock assignments check-repository-access https://github.com/org/assignment-student123 student123
    """
    # Access universal options from root context
    verbose, dry_run = get_global_options(ctx)
    setup_logging(verbose=verbose)

    if dry_run:
        logger.info("DRY RUN: Would check repository access status")
        if repo_url:
            logger.info(f"DRY RUN: Repository: {repo_url}")
        if username:
            logger.info(f"DRY RUN: Username: {username}")
        return

    logger.info("Checking repository access status")

    # If no repo_url provided, load from file and allow selection
    if not repo_url:
        try:
            repos = load_student_repos(repo_file)
            if not repos:
                logger.error(f"No repositories found in {repo_file}")
                logger.info("💡 To generate a student repository list, run:")
                logger.info("   $ classdock repos fetch")
                raise typer.Exit(code=1)

            repo_url = select_student_repo_interactive(repos)
            if not repo_url:
                raise typer.Exit(code=0)  # User cancelled

        except FileNotFoundError:
            logger.error(f"Repository file not found: {repo_file}")
            logger.info("💡 To generate a student repository list, run:")
            logger.info("   $ classdock repos fetch")
            raise typer.Exit(code=1)

    # Extract username from URL if not provided
    if not username:
        try:
            # Extract username from URL (e.g., https://github.com/org/assignment-username -> username)
            url_parts = repo_url.rstrip('/').split('/')
            repo_name = url_parts[-1]
            # Try to extract username after last dash
            if '-' in repo_name:
                username = repo_name.split('-')[-1]
                logger.info(f"Extracted username from URL: {username}")
            else:
                logger.error("Could not extract username from repository URL")
                logger.error(
                    "Please provide username explicitly: check-repository-access <repo_url> <username>")
                raise typer.Exit(code=1)
        except (IndexError, AttributeError) as e:
            logger.error(f"Failed to parse repository URL: {e}")
            raise typer.Exit(code=1)

    try:
        from .assignments.cycle_collaborator import CycleCollaboratorManager

        # Initialize manager
        config_path = Path(config_file) if config_file else None
        manager = CycleCollaboratorManager(config_path)

        # Validate configuration
        if not manager.validate_configuration():
            logger.error("Configuration validation failed")
            raise typer.Exit(code=1)

        # Check repository status
        status = manager.check_repository_status(repo_url, username)

        # Display status
        manager.display_repository_status(status)

        # Exit with appropriate code based on status
        if not status.accessible:
            logger.error("❌ Repository is not accessible")
            raise typer.Exit(code=1)
        elif status.needs_cycling:
            logger.warning(
                "⚠️ Repository access issues detected - cycling recommended")
            raise typer.Exit(code=2)
        else:
            logger.info("✅ Repository access is working correctly")

    except ImportError as e:
        logger.error(f"Failed to import cycle collaborator manager: {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"Repository access check failed: {e}")
        raise typer.Exit(code=1)


@assignments_app.command("push-to-classroom")
def push_to_classroom(
    ctx: typer.Context,
    force: bool = typer.Option(
        False, "--force", "-f", help="Force push without confirmation"),
    interactive: bool = typer.Option(
        True, "--interactive/--non-interactive", help="Enable interactive mode for confirmations"),
    branch: str = typer.Option(
        "main", "--branch", "-b", help="Branch to push to classroom repository"),
    config_file: str = typer.Option(
        "assignment.conf", "--config", "-c", help="Configuration file path")
):
    """
    Push template repository changes to the classroom repository.

    This command synchronizes your local template repository with the
    GitHub Classroom repository, ensuring students receive the latest
    assignment updates and fixes.

    The command performs:
    - Repository validation and status checks
    - Git remote configuration for classroom repository
    - Change analysis and conflict detection
    - Interactive confirmation (unless --force is used)
    - Push execution with appropriate force handling
    - Verification of successful synchronization

    Examples:
        # Interactive push with confirmation
        classdock assignments push-to-classroom

        # Force push without confirmation
        classdock assignments push-to-classroom --force

        # Push specific branch
        classdock assignments push-to-classroom --branch develop

        # Non-interactive mode for automation
        classdock assignments push-to-classroom --non-interactive --force
    """
    # Access universal options from root context
    verbose, dry_run = get_global_options(ctx)

    try:
        from .assignments.push_manager import ClassroomPushManager, PushResult

        # Set up logging
        setup_logging(verbose=verbose)
        logger.info("🚀 Starting classroom repository push workflow")

        if dry_run:
            logger.info("🔍 DRY RUN MODE - No changes will be made")

        # Get the loaded global configuration
        global_config = get_global_config()

        # Initialize manager with global config
        manager = ClassroomPushManager(
            global_config=global_config, assignment_root=Path.cwd())
        manager.branch = branch

        if dry_run:
            # In dry run mode, only show what would be done
            logger.info("📋 Push workflow steps that would be executed:")
            logger.info("  1. Validate repository structure and configuration")
            logger.info("  2. Check for uncommitted changes")
            logger.info("  3. Setup classroom remote repository")
            logger.info("  4. Fetch latest classroom repository state")
            logger.info("  5. Analyze changes between local and classroom")
            logger.info("  6. Display changes summary and get confirmation")
            logger.info("  7. Push changes to classroom repository")
            logger.info("  8. Verify push completed successfully")
            logger.info("  9. Provide next steps guidance")
            logger.info(
                "✅ Dry run completed - use without --dry-run to execute")
            return

        # Execute the push workflow
        result, message = manager.execute_push_workflow(
            force=(force and not interactive),
            interactive=interactive
        )

        # Handle results
        if result == PushResult.SUCCESS:
            logger.info(f"✅ {message}")
        elif result == PushResult.UP_TO_DATE:
            logger.info(f"ℹ️ {message}")
        elif result == PushResult.CANCELLED:
            logger.info(f"❌ {message}")
        elif result == PushResult.PERMISSION_ERROR:
            logger.error(f"🔒 {message}")
            logger.error("Check your GitHub permissions and authentication")
            raise typer.Exit(code=1)
        elif result == PushResult.NETWORK_ERROR:
            logger.error(f"🌐 {message}")
            logger.error("Check your network connection and try again")
            raise typer.Exit(code=1)
        elif result == PushResult.REPOSITORY_ERROR:
            logger.error(f"📁 {message}")
            logger.error("Fix repository issues and try again")
            raise typer.Exit(code=1)
        else:
            logger.error(f"❌ Push failed: {message}")
            raise typer.Exit(code=1)

    except ImportError as e:
        logger.error(f"Failed to import push manager: {e}")
        raise typer.Exit(code=1)
    except KeyboardInterrupt:
        logger.info("❌ Push cancelled by user")
        raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"Push workflow failed: {e}")
        if verbose:
            import traceback
            logger.error(traceback.format_exc())
        raise typer.Exit(code=1)


# Repository Commands
@repos_app.command("fetch")
def repos_fetch(
    ctx: typer.Context,
    config_file: str = typer.Option(
        "assignment.conf", "--config", "-c", help="Configuration file path")
):
    """
    Discover and fetch student repositories from GitHub Classroom.

    This command loads the assignment configuration, then uses a Bash wrapper to fetch
    student repositories as specified in the configuration file. It supports dry-run and
    verbose modes for safer and more informative execution.

    Args:
        config_file (str): Path to the configuration file (default: "assignment.conf").

    Supports universal options: --verbose, --dry-run

    Raises:
        typer.Exit: If the repository fetch operation fails.

    Example:
        $ classdock repos fetch
        $ classdock repos fetch --config custom.conf --verbose --dry-run
    """
    # Access universal options from root context
    verbose, dry_run = get_global_options(ctx)

    if verbose:
        logger.debug(
            f"Verbose mode enabled for repo fetch with config: {config_file}")

    logger.info("Fetching student repositories")

    if dry_run:
        logger.info(
            f"DRY RUN: Would fetch student repositories using config: {config_file}")
        return
    # Delegate to ReposService
    try:
        from .services.repos_service import ReposService

        service = ReposService(dry_run=dry_run, verbose=verbose)
        ok, message = service.fetch(config_file=config_file)
        if not ok:
            logger.error(message)
            raise typer.Exit(code=1)
        logger.info(f"✅ {message}")
    except Exception as e:
        logger.error(f"Repository fetch failed: {e}")
        raise typer.Exit(code=1)


# Secret Commands
@secrets_app.command("add")
def secrets_add(
    ctx: typer.Context,
    assignment_root: str = typer.Option(
        None, "--assignment-root", "-r", help="Path to assignment template repository root directory"),
    repo_urls: str = typer.Option(
        None, "--repos", help="Comma-separated list of repository URLs to process"),
    force_update: bool = typer.Option(
        False, "--force", "-f", help="Force update secrets even if they already exist and are up to date")
):
    """
    Add or update secrets in student repositories using global configuration.

    This function manages the process of adding or updating secrets in student repositories
    based on the global configuration loaded from assignment.conf. It supports dry-run and
    verbose modes for testing and debugging purposes.

    The command uses the globally loaded configuration, which contains all necessary
    settings including SECRETS_CONFIG, GITHUB_ORGANIZATION, and INSTRUCTOR_TOKEN_FILE.

    Args:
        assignment_root (str, optional): Path to assignment template repository root. 
                                       If not provided, uses current directory.
        repo_urls (str, optional): Comma-separated list of repository URLs. If not provided,
                                  auto-discovery will be attempted (when implemented).
        force_update (bool, optional): Force update secrets even if they already exist and are up to date.
                                      Useful for fixing incorrect secret values.

    Supports universal options: --verbose, --dry-run

    Raises:
        typer.Exit: Exits with code 1 if secret management fails.

    Example:
        $ classdock secrets add
        $ classdock secrets add --repos "url1,url2" --verbose --dry-run
        $ classdock secrets add --force  # Force update all secrets
    """

    # Access universal options from root context
    verbose, dry_run = get_global_options(ctx)

    if verbose:
        logger.debug("Verbose mode enabled for secrets add")

    logger.info(
        "Adding secrets to student repositories using global configuration")

    if dry_run:
        logger.info("DRY RUN: Would add secrets to student repositories")
        if repo_urls:
            target_repos = [url.strip()
                            for url in repo_urls.split(',') if url.strip()]
            logger.info(
                f"DRY RUN: Would process {len(target_repos)} specified repositories")
        if assignment_root:
            logger.info(
                f"DRY RUN: Would use assignment root: {assignment_root}")
        return

    # Check if global configuration is loaded
    global_config = get_global_config()
    if not global_config:
        logger.error("Global configuration not loaded")
        logger.error(
            "Please ensure you're running from a directory with assignment.conf")
        logger.error(
            "Or use --assignment-root to specify the assignment directory")
        raise typer.Exit(code=1)

    # Validate secrets configuration
    if not global_config.secrets_config:
        logger.error("No secrets configuration found in assignment.conf")
        logger.error(
            "Please configure SECRETS_CONFIG in your assignment.conf file")
        raise typer.Exit(code=1)

    # Parse repository URLs if provided
    target_repos = None
    if repo_urls:
        target_repos = [url.strip()
                        for url in repo_urls.split(',') if url.strip()]
        logger.info(f"Processing {len(target_repos)} specified repositories")

    # Delegate secrets deployment to service layer
    try:
        from .services.secrets_service import SecretsService

        service = SecretsService(dry_run=dry_run, verbose=verbose)
        ok, message = service.add_secrets(
            repo_urls=target_repos, force_update=force_update)

        if not ok:
            logger.error(f"Secret management failed: {message}")
            raise typer.Exit(code=1)

        logger.info(f"✅ {message}")

    except Exception as e:
        logger.error(f"Secrets command failed: {e}")
        raise typer.Exit(code=1)


@secrets_app.command("manage")
def secrets_manage(ctx: typer.Context):
    """
    Provides an interface for advanced secret and token management.

    This function provides access to advanced secret management functionality with
    support for universal options. Advanced secret management commands will be
    implemented in future versions.

    Supports universal options: --verbose, --dry-run

    Example:
        $ classdock secrets manage
        $ classdock secrets manage --verbose --dry-run
    """
    # Access universal options from root context
    verbose, dry_run = get_global_options(ctx)

    setup_logging(verbose=verbose)
    if verbose:
        logger.debug("Verbose mode enabled for secrets management")

    if dry_run:
        logger.info("DRY RUN: Would start secret management interface")
        typer.echo("🚧 DRY RUN: Advanced secret management commands coming soon!")
        return

    logger.info("Secret management interface")
    # TODO: Implement secret management
    typer.echo("🚧 Advanced secret management commands coming soon!")


# Automation Commands
@automation_app.command("cron-install")
def automation_cron_install(
    ctx: typer.Context,
    steps: List[str] = typer.Argument(
        ..., help="Workflow steps to schedule (sync, secrets, cycle, discover, assist)"),
    schedule: Optional[str] = typer.Option(
        None, "--schedule", "-s", help="Cron schedule (e.g., '0 */4 * * *'). Uses default if not provided"),
    config_file: str = typer.Option(
        "assignment.conf", "--config", "-c", help="Configuration file path")
):
    """
    Install cron job for automated workflow steps.

    Install cron jobs to automate GitHub Classroom workflow operations like
    template synchronization, secret management, and repository access cycling.

    Supports universal options: --verbose, --dry-run

    Examples:
        classdock automation cron-install sync
        classdock automation cron-install secrets --schedule "0 2 * * *" --verbose
        classdock automation cron-install sync secrets cycle --dry-run
    """
    # Access universal options from root context
    verbose, dry_run = get_global_options(ctx)

    if verbose:
        logger.debug(f"Verbose mode enabled for cron installation: {steps}")

    if dry_run:
        logger.info(
            f"DRY RUN: Would install cron job for steps: {', '.join(steps)}")
        if schedule:
            logger.info(f"DRY RUN: Schedule: {schedule}")
        logger.info(f"DRY RUN: Config file: {config_file}")
        return
    try:
        from .services.automation_service import AutomationService

        service = AutomationService(dry_run=dry_run, verbose=verbose)
        ok, message = service.cron_install(steps, schedule, config_file)
        if not ok:
            typer.echo(f"❌ {message}", color=typer.colors.RED)
            raise typer.Exit(code=1)
        typer.echo(f"✅ {message}", color=typer.colors.GREEN)
    except Exception as e:
        logger.error(f"Cron job installation failed: {e}")
        raise typer.Exit(code=1)


@automation_app.command("cron-remove")
def automation_cron_remove(
    ctx: typer.Context,
    steps: Optional[List[str]] = typer.Argument(
        None, help="Workflow steps to remove (sync, secrets, cycle, discover, assist) or 'all'"),
    config_file: str = typer.Option(
        "assignment.conf", "--config", "-c", help="Configuration file path")
):
    """
    Remove cron jobs for automated workflow steps.

    Remove specific cron jobs or all assignment-related cron jobs from
    the user's crontab.

    Examples:
        classdock automation cron-remove sync
        classdock automation cron-remove all
        classdock automation cron-remove secrets cycle
    """
    # Access universal options from root context
    verbose, dry_run = get_global_options(ctx)

    setup_logging(verbose)

    try:
        from .services.automation_service import AutomationService

        service = AutomationService(dry_run=dry_run, verbose=verbose)

        if dry_run:
            if not steps or (len(steps) == 1 and steps[0] == 'all'):
                typer.echo("[DRY RUN] Would remove all assignment cron jobs")
            else:
                typer.echo(
                    f"[DRY RUN] Would remove cron job for steps: {', '.join(steps)}")
            return

        ok, message = service.cron_remove(steps, config_file)
        if not ok:
            typer.echo(f"❌ {message}", color=typer.colors.RED)
            raise typer.Exit(code=1)
        typer.echo(f"✅ {message}", color=typer.colors.GREEN)
    except Exception as e:
        logger.error(f"Cron job removal failed: {e}")
        raise typer.Exit(code=1)


@automation_app.command("cron-status")
def automation_cron_status(
    ctx: typer.Context,
    config_file: str = typer.Option(
        "assignment.conf", "--config", "-c", help="Configuration file path")
):
    """
    Show status of installed cron jobs.

    Display information about currently installed assignment-related cron jobs,
    including schedules, commands, and recent log activity.

    Supports universal options: --verbose, --dry-run

    Example:
        classdock automation cron-status
        classdock automation --verbose --dry-run cron-status
    """
    # Access universal options from root context
    verbose, dry_run = get_global_options(ctx)

    if verbose:
        logger.debug("Verbose mode enabled for cron status check")

    logger.info("Checking cron job status...")

    if dry_run:
        logger.info("DRY RUN: Would check cron job status")
        logger.info(f"DRY RUN: Config file: {config_file}")
        return

    try:
        from .services.automation_service import AutomationService

        service = AutomationService(dry_run=dry_run, verbose=verbose)
        ok, data = service.cron_status(config_file)
        if not ok:
            logger.error(data)
            raise typer.Exit(code=1)

        status = data
        if not status.has_jobs:
            typer.echo("⚠️  No assignment cron jobs are installed",
                       color=typer.colors.YELLOW)
            typer.echo("\nTo install a cron job, run:")
            typer.echo("  classdock automation cron-install [steps]")
        else:
            typer.echo(
                f"✅ Assignment cron jobs are installed: {status.total_jobs} job(s)", color=typer.colors.GREEN)
            typer.echo()

            for job in status.installed_jobs:
                typer.echo(
                    f"📅 Steps: {', '.join(job.steps) if hasattr(job, 'steps') else job.steps_key}")
                typer.echo(f"   Schedule: {job.schedule}")
                if hasattr(job, 'command'):
                    typer.echo(f"   Command: {job.command}")
                typer.echo()

            if status.log_file_exists and status.last_log_activity:
                typer.echo("📋 Recent log activity:")
                log_lines = status.last_log_activity.splitlines()
                for line in log_lines[-3:]:
                    typer.echo(f"   {line}")
            elif status.log_file_exists:
                typer.echo("📋 Log file exists but no recent activity")
            else:
                typer.echo(
                    "⚠️  No log file found - cron jobs may not have run yet")

    except Exception as e:
        logger.error(f"Failed to get cron job status: {e}")
        raise typer.Exit(code=1)


@automation_app.command("cron-logs")
def automation_cron_logs(
    lines: int = typer.Option(
        30, "--lines", "-n", help="Number of recent log lines to show"),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"),
    config_file: str = typer.Option(
        "assignment.conf", "--config", "-c", help="Configuration file path")
):
    """
    Show recent workflow log entries.

    Display recent log entries from automated workflow executions to help
    with debugging and monitoring cron job activity.

    Example:
        classdock automation cron-logs --lines 50
    """
    setup_logging(verbose)

    try:
        from .services.automation_service import AutomationService

        service = AutomationService(dry_run=False, verbose=verbose)
        success, output = service.cron_logs(lines)
        if success:
            typer.echo(output)
        else:
            if "Log file not found" in output or "not found" in output.lower():
                typer.echo("📋 No logs available yet",
                           color=typer.colors.YELLOW)
                typer.echo(
                    "\nCron jobs may not have run yet, or logging may not be configured.")
                typer.echo(
                    "Once cron jobs start running, their output will appear here.")
            else:
                typer.echo(f"❌ {output}", color=typer.colors.RED)
                raise typer.Exit(code=1)

    except Exception as e:
        logger.error(f"Failed to show logs: {e}")
        raise typer.Exit(code=1)


@automation_app.command("cron-schedules")
def automation_cron_schedules():
    """
    List default schedules for workflow steps.

    Show the default cron schedules used for different workflow steps
    and provide examples of cron schedule formats.

    Example:
        classdock automation cron-schedules
    """
    try:
        from .services.automation_service import AutomationService

        service = AutomationService()
        ok, output = service.cron_schedules()
        if not ok:
            logger.error(output)
            raise typer.Exit(code=1)
        typer.echo(output)

    except Exception as e:
        logger.error(f"Failed to list schedules: {e}")
        raise typer.Exit(code=1)


@automation_app.command("cron-sync")
def automation_cron_sync(
    ctx: typer.Context,
    steps: List[str] = typer.Argument(
        None, help="Workflow steps to execute (sync, discover, secrets, assist, cycle)"),
    config_file: str = typer.Option(
        "assignment.conf", "--config", "-c", help="Configuration file path"),
    stop_on_failure: bool = typer.Option(
        False, "--stop-on-failure", help="Stop execution on first step failure"),
    show_log: bool = typer.Option(
        False, "--show-log", help="Show log tail after execution")
):
    """
    Execute automated workflow cron job with specified steps.

    This command runs workflow steps designed for scheduled execution,
    providing comprehensive logging and error handling suitable for
    cron job automation.

    The command performs:
    - Environment validation and step verification
    - Sequential execution of specified workflow steps
    - Comprehensive logging with automatic log rotation
    - Error handling and result reporting
    - Optional log display for immediate feedback

    Available workflow steps:
    - sync: Synchronize template with classroom repository
    - discover: Discover and update student repositories
    - secrets: Manage repository secrets
    - assist: Provide automated student assistance
    - cycle: Cycle collaborator permissions

    Examples:
        # Execute sync step only (default)
        classdock automation cron-sync

        # Execute multiple steps
        classdock automation cron-sync sync secrets cycle

        # Dry run to see what would be executed
        classdock automation cron-sync --dry-run sync secrets

        # Stop on first failure and show logs
        classdock automation cron-sync --stop-on-failure --show-log sync secrets

        # Verbose execution for debugging
        classdock automation cron-sync --verbose sync
    """
    # Access universal options from root context
    verbose, dry_run = get_global_options(ctx)

    try:
        from .services.automation_service import AutomationService

        service = AutomationService(dry_run=dry_run, verbose=verbose)
        ok, result = service.cron_sync(
            steps, dry_run, verbose, stop_on_failure, show_log)
        if not ok:
            logger.error(result)
            raise typer.Exit(code=1)

        # If dry-run, print summary and return
        if dry_run:
            logger.info("📋 Workflow steps that would be executed:")
            for i, step in enumerate(steps or ["sync"], 1):
                logger.info(f"  {i}. {step}")
            logger.info(
                f"📂 Log file: {result.get('log_file') if isinstance(result, dict) else 'unknown'}")
            logger.info(
                "✅ Dry run completed - use without --dry-run to execute")
            return

        # Otherwise result is the CronSync result object
        res = result
        try:
            getattr(res, 'overall_result', None)
        except Exception:
            pass

        # Attempt to interpret result similar to prior behavior
        if hasattr(res, 'overall_result') and res.overall_result.name == 'SUCCESS':
            logger.info(
                f"✅ All workflow steps completed successfully in {getattr(res, 'total_execution_time', 0):.2f}s")
        elif hasattr(res, 'overall_result') and res.overall_result.name == 'PARTIAL_FAILURE':
            logger.warning(
                f"⚠️ Some workflow steps failed: {getattr(res, 'error_summary', '')}")
            logger.info(
                f"📂 Check log file: {getattr(res, 'log_file_path', '')}")
        elif hasattr(res, 'overall_result') and res.overall_result.name == 'COMPLETE_FAILURE':
            logger.error(
                f"❌ All workflow steps failed: {getattr(res, 'error_summary', '')}")
            logger.error(
                f"📂 Check log file: {getattr(res, 'log_file_path', '')}")

        if hasattr(res, 'steps_executed') and res.steps_executed:
            logger.info("📊 Step execution summary:")
            for step_result in res.steps_executed:
                status = "✅" if step_result.success else "❌"
                logger.info(
                    f"  {status} {step_result.step.value}: {step_result.message}")

        if show_log and hasattr(res, 'get_log_tail'):
            logger.info("📋 Recent log entries:")
            log_lines = res.get_log_tail(20)
            for line in log_lines[-10:]:
                logger.info(f"  {line}")

        if hasattr(res, 'overall_result') and res.overall_result.name in ['COMPLETE_FAILURE', 'ENVIRONMENT_ERROR', 'CONFIGURATION_ERROR']:
            raise typer.Exit(code=1)
        if hasattr(res, 'overall_result') and res.overall_result.name == 'PARTIAL_FAILURE':
            raise typer.Exit(code=2)

    except Exception as e:
        logger.error(f"Cron sync workflow failed: {e}")
        if verbose:
            import traceback
            logger.error(traceback.format_exc())
        raise typer.Exit(code=1)


# ========================================
# Configuration Commands
# ========================================

@config_app.command("set-token")
def config_set_token(
    token: str = typer.Argument(
        ...,
        help="GitHub Personal Access Token (classic or fine-grained)"
    ),
    expires_at: str = typer.Option(
        None,
        "--expires-at",
        "-e",
        help="Token expiration date in ISO format (e.g., '2026-10-19T00:00:00+00:00')"
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force update even if existing token is valid"
    )
):
    """
    Update the GitHub Personal Access Token used for API operations.

    This command validates and saves a new GitHub token to the token configuration file.
    The token is validated for required scopes and expiration before being saved.

    Required token scopes:
    - repo (Full control of private repositories)
    - read:org (Read organization data)

    Examples:
        # Set a new token (expiration auto-detected for fine-grained tokens)
        classdock config set-token ghp_YourNewTokenHere

        # Set token with explicit expiration date (for classic tokens)
        classdock config set-token ghp_YourToken --expires-at "2026-10-19T00:00:00+00:00"

        # Force update without validation
        classdock config set-token ghp_YourNewTokenHere --force

    Generate tokens at: https://github.com/settings/tokens
    """
    setup_logging()

    try:
        from .utils.token_manager import GitHubTokenManager
        from .utils.github_classroom_api import GitHubClassroomAPI

        logger.info("🔑 Updating GitHub Personal Access Token...")

        # Validate token format
        if not token.startswith(('ghp_', 'github_pat_')):
            logger.warning(
                "⚠️ Token doesn't start with 'ghp_' or 'github_pat_'")
            logger.warning("This might not be a valid GitHub token format")
            if not force:
                confirm = typer.confirm("Continue anyway?")
                if not confirm:
                    logger.info("Token update cancelled")
                    raise typer.Exit(0)

        # Create API client to validate token
        if not force:
            logger.info("Validating token...")
            api_client = GitHubClassroomAPI(token)

            # Check token expiration
            expiration_info = api_client.check_token_expiration()

            if expiration_info.get('is_expired'):
                logger.error("❌ Token has already expired!")
                logger.error(
                    f"Expired on: {expiration_info.get('expires_at', 'unknown date')}")
                logger.error(
                    "Please generate a new token at: https://github.com/settings/tokens")
                raise typer.Exit(1)

            if not expiration_info.get('is_valid'):
                error_msg = expiration_info.get('error', 'Unknown error')
                logger.error(f"❌ Token validation failed: {error_msg}")
                raise typer.Exit(1)

            # Log expiration info
            if expiration_info.get('days_remaining') is not None:
                days = expiration_info['days_remaining']
                if days <= 7:
                    logger.warning(f"⚠️ Token expires in {days} days!")
                elif days <= 30:
                    logger.info(f"ℹ️ Token expires in {days} days")
                else:
                    logger.info(f"✓ Token valid for {days} more days")
            else:
                logger.info(
                    "✓ Token is valid (classic token with no expiration)")

            # Check token scopes
            scope_info = api_client.validate_token_scopes()

            if not scope_info.get('valid'):
                logger.error("❌ Token validation failed")
                raise typer.Exit(1)

            scopes = scope_info.get('scopes', [])
            logger.info(
                f"Token scopes: {', '.join(scopes) if scopes else 'none'}")

            # Check for required scopes
            if not scope_info.get('has_repo'):
                logger.warning(
                    "⚠️ Token lacks 'repo' scope - some operations may fail")
            else:
                logger.info("✓ Token has 'repo' scope")

            if not scope_info.get('has_read_org'):
                logger.warning(
                    "⚠️ Token lacks 'read:org' scope - organization access may be limited")
            else:
                logger.info("✓ Token has 'read:org' or 'admin:org' scope")

            # Warn if critical scopes are missing
            if not scope_info.get('has_repo') or not scope_info.get('has_read_org'):
                logger.warning("")
                logger.warning(
                    "⚠️ IMPORTANT: This token is missing critical scopes!")
                logger.warning("You may experience authorization failures.")
                logger.warning("")
                logger.warning("Required scopes:")
                logger.warning(
                    "  ✓ repo - Full control of private repositories")
                logger.warning("  ✓ read:org - Read organization data")
                logger.warning("")
                if not typer.confirm("Do you want to save this token anyway?"):
                    logger.info("Token update cancelled")
                    raise typer.Exit(0)

        # Validate expiration date format if provided
        validated_expires_at = None
        if expires_at:
            try:
                from datetime import datetime
                # Parse to validate format
                datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                validated_expires_at = expires_at
                logger.info(f"✓ Expiration date set to: {expires_at}")
            except ValueError as e:
                logger.error(f"❌ Invalid date format: {e}")
                logger.error("Expected ISO format: YYYY-MM-DDTHH:MM:SS+00:00")
                raise typer.Exit(1)

        # Save token with metadata
        token_manager = GitHubTokenManager()

        # Get scopes from validation if we ran it, otherwise let save_token detect them
        scopes_to_save = None
        if not force:
            scopes_to_save = scope_info.get('scopes', [])

        success = token_manager.save_token(
            token,
            expires_at=validated_expires_at,
            scopes=scopes_to_save
        )

        if not success:
            logger.error("❌ Failed to save token")
            raise typer.Exit(1)

        logger.info("")
        logger.info("✅ Token updated successfully!")
        logger.info(f"Token saved to: {token_manager.config_file}")
        logger.info("")
        logger.info(
            "You can now use classdock commands with the new token.")

    except Exception as e:
        logger.error(f"Failed to update token: {e}")
        raise typer.Exit(1)


@config_app.command("check-token")
def config_check_token(ctx: typer.Context):
    """
    Check the current GitHub token status, expiration, and scopes.

    This command validates the currently configured token and displays:
    - Token validity status
    - Expiration date (for fine-grained tokens)
    - Days until expiration
    - Configured scopes
    - Warnings for missing required scopes

    Example:
        classdock config check-token
    """
    # Access universal options from root context
    verbose, dry_run = get_global_options(ctx)
    setup_logging(verbose=verbose)

    if dry_run:
        logger.info("DRY RUN: Would check GitHub token status")
        return

    try:
        from .utils.token_manager import GitHubTokenManager
        from .utils.github_classroom_api import GitHubClassroomAPI

        logger.info("🔍 Checking GitHub token status...")
        logger.info("")

        # Get token
        token_manager = GitHubTokenManager()
        token = token_manager.get_github_token()

        if not token:
            logger.error("❌ No GitHub token found!")
            logger.error("")
            logger.error("To set a token:")
            logger.error("  classdock config set-token <your-token>")
            logger.error("")
            logger.error(
                "Generate tokens at: https://github.com/settings/tokens")
            raise typer.Exit(1)

        # Create API client
        api_client = GitHubClassroomAPI(token)

        # Check expiration
        logger.info("📅 Token Expiration:")
        expiration_info = api_client.check_token_expiration()

        if expiration_info.get('is_expired'):
            expires_at = expiration_info.get('expires_at')
            days_past = abs(expiration_info.get('days_remaining', 0))

            logger.error("  ❌ Token has EXPIRED!")
            if expires_at:
                # Format the date in a more readable way
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(
                        expires_at.replace('Z', '+00:00'))
                    formatted_date = dt.strftime('%B %d, %Y at %I:%M %p %Z')
                    logger.error(f"  Expired on: {formatted_date}")
                except Exception:
                    # Fallback to ISO format if parsing fails
                    logger.error(f"  Expired on: {expires_at}")

                if days_past > 0:
                    logger.error(
                        f"  ({days_past} day{'s' if days_past != 1 else ''} ago)")
            else:
                logger.error(
                    "  Expiration date: Not available in token config")
            logger.error("")
            logger.error("🔧 To fix:")
            logger.error(
                "  1. Generate new token: https://github.com/settings/tokens")
            logger.error(
                "  2. Update token: classdock config set-token <new-token>")
            raise typer.Exit(1)

        if not expiration_info.get('is_valid'):
            error_msg = expiration_info.get('error', 'Unknown error')
            logger.error(f"  ❌ Token is invalid: {error_msg}")
            raise typer.Exit(1)

        # Display expiration info
        if expiration_info.get('days_remaining') is not None:
            days = expiration_info['days_remaining']
            expires_at = expiration_info.get('expires_at', 'unknown')
            if days <= 7:
                logger.warning(
                    f"  ⚠️ Expires in {days} days (on {expires_at})")
                logger.warning("  Consider generating a new token soon!")
            elif days <= 30:
                logger.info(f"  ⏰ Expires in {days} days (on {expires_at})")
            else:
                logger.info(
                    f"  ✓ Valid for {days} more days (until {expires_at})")
            logger.info(
                f"  Token type: {expiration_info.get('token_type', 'unknown')}")
        else:
            # Classic token - check if user manually set expiration in config
            logger.info("  ✓ Token is valid")

            # Try to get stored expiration date from config file
            stored_expiration = None
            try:
                import json
                if token_manager.config_file.exists():
                    with open(token_manager.config_file, 'r') as f:
                        config_data = json.load(f)
                        stored_expiration = config_data.get(
                            'github_token', {}).get('expires_at')
            except Exception as e:
                logger.debug(f"Could not read stored expiration: {e}")

            if stored_expiration:
                # Calculate days remaining from stored expiration
                try:
                    from datetime import datetime, timezone
                    expires_dt = datetime.fromisoformat(
                        stored_expiration.replace('Z', '+00:00'))
                    now = datetime.now(timezone.utc)
                    days_remaining = (expires_dt - now).days

                    # Format the date nicely
                    formatted_date = expires_dt.strftime(
                        '%B %d, %Y at %I:%M %p %Z')

                    if days_remaining < 0:
                        logger.error(f"  ❌ Token expired on: {formatted_date}")
                        logger.error(f"  ({abs(days_remaining)} days ago)")
                    elif days_remaining <= 7:
                        logger.warning(
                            f"  ⚠️ Expires in {days_remaining} days")
                        logger.warning(f"  Expiration date: {formatted_date}")
                        logger.warning(
                            "  Consider generating a new token soon!")
                    elif days_remaining <= 30:
                        logger.info(f"  ⏰ Expires in {days_remaining} days")
                        logger.info(f"  Expiration date: {formatted_date}")
                    else:
                        logger.info(
                            f"  ✓ Valid for {days_remaining} more days")
                        logger.info(f"  Expiration date: {formatted_date}")

                    logger.info(
                        f"  Token type: classic (expiration set manually)")
                except Exception as e:
                    logger.debug(
                        f"Could not parse stored expiration date: {e}")
                    logger.info(
                        f"  Expiration date (manually set): {stored_expiration}")
                    logger.info(f"  Token type: classic")
            else:
                logger.info(f"  Token type: classic (no expiration set)")
                logger.warning(
                    "  ⚠️ Consider setting an expiration date for tracking:")
                logger.warning(
                    "     classdock config set-token <token> --expires-at <date>")

        logger.info("")

        # Check scopes
        logger.info("🔐 Token Scopes:")
        scope_info = api_client.validate_token_scopes()

        if not scope_info.get('valid'):
            logger.error("  ❌ Could not validate token scopes")
            raise typer.Exit(1)

        scopes = scope_info.get('scopes', [])
        if scopes:
            logger.info(f"  Configured scopes: {', '.join(scopes)}")
        else:
            logger.warning("  ⚠️ No scopes found (this is unusual)")

        logger.info("")
        logger.info("📋 Required Scopes Check:")

        if scope_info.get('has_repo'):
            logger.info("  ✓ repo - Full control of private repositories")
        else:
            logger.error(
                "  ❌ repo - MISSING! (Required for repository operations)")

        if scope_info.get('has_read_org'):
            logger.info("  ✓ read:org - Read organization data")
        else:
            logger.error(
                "  ❌ read:org - MISSING! (Required for organization access)")

        logger.info("")

        # Overall status
        if scope_info.get('has_repo') and scope_info.get('has_read_org'):
            logger.info(
                "✅ Token is properly configured with all required scopes!")
        else:
            logger.warning("⚠️ Token is missing some required scopes")
            logger.warning(
                "Some operations may fail with authorization errors")
            logger.warning("")
            logger.warning("To fix:")
            logger.warning("  1. Generate new token with required scopes")
            logger.warning(
                "  2. Update: classdock config set-token <new-token>")

    except Exception as e:
        logger.error(f"Failed to check token: {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
