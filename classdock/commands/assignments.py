"""Assignments command group."""

from pathlib import Path
from typing import Optional

import typer

from ..utils import setup_logging, get_logger
from ._helpers import get_global_options, load_student_repos, select_student_repo_interactive

logger = get_logger("cli")

assignments_app = typer.Typer(help="Assignment setup, orchestration, and management commands")


@assignments_app.callback()
def assignments_callback(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be done without executing"),
):
    """Assignment setup, orchestration, and management commands."""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose or ctx.obj.get('verbose', False)
    ctx.obj['dry_run'] = dry_run or ctx.obj.get('dry_run', False)


@assignments_app.command("setup")
def assignment_setup(
    ctx: typer.Context,
    url: Optional[str] = typer.Option(
        None, "--url",
        help="GitHub Classroom URL for simplified setup (auto-extracts organization and assignment info)"),
    simplified: bool = typer.Option(
        False, "--simplified", help="Use simplified setup wizard with minimal prompts"),
):
    """
    Launch interactive wizard to configure a new assignment.

    Examples:
        $ classdock assignments setup
        $ classdock assignments setup --simplified
        $ classdock assignments setup --url "https://classroom.github.com/..."
    """
    verbose, dry_run = get_global_options(ctx)
    setup_logging(verbose)

    try:
        from ..services.assignment_service import AssignmentService

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
        "assignment.conf", "--config-file", "-c", help="Configuration file path to validate"),
):
    """
    Validate assignment configuration file.

    Example:
        $ classdock assignments validate-config
        $ classdock assignments validate-config --config-file custom.conf
    """
    verbose, dry_run = get_global_options(ctx)
    setup_logging(verbose)

    assignment_root = ctx.parent.parent.params.get(
        'assignment_root', None) if ctx.parent and ctx.parent.parent else None

    if assignment_root and not Path(config_file).is_absolute():
        config_file = str(Path(assignment_root) / config_file)

    if dry_run:
        logger.info(f"DRY RUN: Would validate configuration file: {config_file}")
        return

    try:
        from ..services.assignment_service import AssignmentService

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
    force_yes: bool = typer.Option(False, "--yes", "-y", help="Automatically confirm all prompts"),
    step: Optional[str] = typer.Option(
        None, "--step",
        help="Execute only a specific step (sync, discover, secrets, assist, cycle)"),
    skip_steps: Optional[str] = typer.Option(
        None, "--skip",
        help="Skip specific steps (comma-separated: sync,discover,secrets,assist,cycle)"),
    config_file: str = typer.Option(
        "assignment.conf", "--config", "-c", help="Configuration file path"),
):
    """
    Execute complete assignment workflow with comprehensive orchestration.

    Example:
        $ classdock assignments --dry-run --verbose orchestrate
        $ classdock assignments orchestrate --step discover
        $ classdock assignments orchestrate --skip sync,assist
        $ classdock assignments orchestrate --config my-assignment.conf
    """
    verbose, dry_run = get_global_options(ctx)
    setup_logging(verbose=verbose)
    logger.info("Starting assignment orchestration")

    try:
        from ..services.assignment_service import AssignmentService

        service = AssignmentService(dry_run=dry_run, verbose=verbose)
        ok, message = service.orchestrate(
            config_file=config_file,
            force_yes=force_yes,
            step=step,
            skip_steps=skip_steps,
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
    auto_confirm: bool = typer.Option(False, "--yes", "-y", help="Automatically confirm all prompts"),
    repo_file: str = typer.Option(
        "student-repos.txt", "--file", "-f",
        help="File containing student repository URLs for interactive selection"),
    config_file: str = typer.Option(
        "assignment.conf", "--config", "-c", help="Configuration file path"),
):
    """
    Help a specific student with repository updates.

    If no repository URL is provided, you'll be prompted to select from student-repos.txt.

    Example:
        $ classdock assignments help-student
        $ classdock assignments help-student https://github.com/org/assignment-student123
    """
    verbose, dry_run = get_global_options(ctx)
    setup_logging(verbose)

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
                raise typer.Exit(code=0)

        except FileNotFoundError:
            logger.error(f"Repository file not found: {repo_file}")
            logger.info("💡 To generate a student repository list, run:")
            logger.info("   $ classdock repos fetch")
            raise typer.Exit(code=1)

    try:
        from ..services.assignment_service import AssignmentService

        service = AssignmentService(dry_run=dry_run, verbose=verbose)
        ok, message = service.help_student(
            repo_url=repo_url,
            one_student=one_student,
            auto_confirm=auto_confirm,
            config_file=config_file,
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
    auto_confirm: bool = typer.Option(False, "--yes", "-y", help="Automatically confirm all prompts"),
    config_file: str = typer.Option(
        "assignment.conf", "--config", "-c", help="Configuration file path"),
):
    """
    Help multiple students with repository updates (batch processing).

    Example:
        $ classdock assignments help-students
        $ classdock assignments help-students --yes
        $ classdock assignments help-students --file custom-repos.txt
    """
    verbose, dry_run = get_global_options(ctx)
    setup_logging(verbose)

    if not Path(repo_file).exists():
        logger.error(f"Repository file not found: {repo_file}")
        logger.info("💡 To generate a student repository list, run:")
        logger.info("   $ classdock repos fetch")
        raise typer.Exit(code=1)

    try:
        from ..services.assignment_service import AssignmentService

        service = AssignmentService(dry_run=dry_run, verbose=verbose)
        ok, message = service.help_students(
            repo_file=repo_file,
            auto_confirm=auto_confirm,
            config_file=config_file,
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
        "assignment.conf", "--config", "-c", help="Configuration file path"),
):
    """
    Check the status of a student repository.

    Example:
        $ classdock assignments check-student
        $ classdock assignments check-student https://github.com/org/assignment-student123
    """
    verbose, dry_run = get_global_options(ctx)
    setup_logging(verbose)

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
                raise typer.Exit(code=0)

        except FileNotFoundError:
            logger.error(f"Repository file not found: {repo_file}")
            logger.info("💡 To generate a student repository list, run:")
            logger.info("   $ classdock repos fetch")
            raise typer.Exit(code=1)

    try:
        from ..services.assignment_service import AssignmentService

        service = AssignmentService(dry_run=dry_run, verbose=verbose)
        ok, message = service.check_student(repo_url=repo_url, config_file=config_file)

        if not ok:
            logger.error(message)
            if "not accessible" in message:
                raise typer.Exit(code=1)
            else:
                raise typer.Exit(code=2)

        logger.info(f"✅ {message}")

    except Exception as e:
        logger.error(f"Student status check failed: {e}")
        raise typer.Exit(code=1)


@assignments_app.command("student-instructions")
def student_instructions(
    ctx: typer.Context,
    repo_url: Optional[str] = typer.Argument(
        None, help="Student repository URL (or leave empty to select from student-repos.txt)"),
    output_file: Optional[str] = typer.Option(None, "--output", "-o", help="Save instructions to file"),
    repo_file: str = typer.Option(
        "student-repos.txt", "--file", "-f",
        help="File containing student repository URLs for interactive selection"),
    config_file: str = typer.Option(
        "assignment.conf", "--config", "-c", help="Configuration file path"),
):
    """
    Generate update instructions for a student.

    Example:
        $ classdock assignments student-instructions
        $ classdock assignments student-instructions https://github.com/org/assignment-student123
        $ classdock assignments student-instructions https://... -o instructions.txt
    """
    verbose, dry_run = get_global_options(ctx)
    setup_logging(verbose=verbose)

    if dry_run:
        logger.info("DRY RUN: Would generate student instructions")
        if repo_url:
            logger.info(f"DRY RUN: Repository: {repo_url}")
        if output_file:
            logger.info(f"DRY RUN: Would save to: {output_file}")
        return

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
                raise typer.Exit(code=0)

        except FileNotFoundError:
            logger.error(f"Repository file not found: {repo_file}")
            logger.info("💡 To generate a student repository list, run:")
            logger.info("   $ classdock repos fetch")
            raise typer.Exit(code=1)

    logger.info("Generating student instructions")

    try:
        from ..assignments.student_helper import StudentUpdateHelper

        config_path = Path(config_file) if config_file else None
        helper = StudentUpdateHelper(config_path)
        instructions = helper.generate_student_instructions(repo_url)

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
        "assignment.conf", "--config", "-c", help="Configuration file path"),
):
    """
    Check if the classroom repository is ready for student updates.

    Example:
        $ classdock assignments check-classroom
    """
    verbose, dry_run = get_global_options(ctx)
    setup_logging(verbose=verbose)

    if dry_run:
        logger.info("DRY RUN: Would check classroom repository status")
        return

    logger.info("Checking classroom repository status")

    try:
        from ..assignments.student_helper import StudentUpdateHelper

        config_path = Path(config_file) if config_file else None
        helper = StudentUpdateHelper(config_path)

        if not helper.validate_configuration():
            logger.error("Configuration validation failed")
            raise typer.Exit(code=1)

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
        None,
        help="Repository URL to cycle collaborator permissions for "
             "(or leave empty to select from student-repos.txt)"),
    username: Optional[str] = typer.Argument(
        None, help="Username to cycle permissions for (auto-extracted from URL if not provided)"),
    force: bool = typer.Option(False, "--force", help="Force cycling even when access appears correct"),
    repo_file: str = typer.Option(
        "student-repos.txt", "--file", "-f",
        help="File containing student repository URLs for interactive selection"),
    config_file: str = typer.Option(
        "assignment.conf", "--config", "-c", help="Configuration file path"),
):
    """
    Cycle collaborator permissions for a single repository.

    Supports universal options: --verbose, --dry-run

    Example:
        $ classdock assignments cycle-collaborator
        $ classdock assignments cycle-collaborator https://github.com/org/repo-student123
        $ classdock assignments cycle-collaborator https://github.com/org/repo student123 --force
    """
    verbose, dry_run = get_global_options(ctx)
    setup_logging(verbose=verbose)
    logger.info("Cycling single repository collaborator permissions")

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
                raise typer.Exit(code=0)

        except FileNotFoundError:
            logger.error(f"Repository file not found: {repo_file}")
            logger.info("💡 To generate a student repository list, run:")
            logger.info("   $ classdock repos fetch")
            raise typer.Exit(code=1)

    if not username:
        try:
            url_parts = repo_url.rstrip('/').split('/')
            repo_name = url_parts[-1]
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
        logger.debug(f"Verbose mode enabled for cycling collaborator {username} on {repo_url}")

    if dry_run:
        logger.info(f"DRY RUN: Would cycle collaborator {username} on {repo_url}")
        logger.info(f"DRY RUN: Force mode: {force}")
        logger.info(f"DRY RUN: Config file: {config_file}")
        return

    try:
        from ..assignments.cycle_collaborator import CycleCollaboratorManager

        config_path = Path(config_file) if config_file else None
        manager = CycleCollaboratorManager(config_path, auto_confirm=True)

        if not manager.validate_configuration():
            logger.error("Configuration validation failed")
            raise typer.Exit(code=1)

        result = manager.cycle_single_repository(repo_url, username, force)
        manager.display_cycle_result(result)

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
        "assignment.conf", "--config", "-c", help="Configuration file path"),
):
    """
    Cycle collaborator permissions for multiple repositories (batch processing).

    Example:
        $ classdock assignments cycle-collaborators
        $ classdock assignments cycle-collaborators --repo-urls
        $ classdock assignments cycle-collaborators custom-repos.txt --repo-urls --force
    """
    verbose, dry_run = get_global_options(ctx)
    setup_logging(verbose=verbose)
    logger.info("Cycling multiple repository collaborator permissions")

    try:
        from ..assignments.cycle_collaborator import CycleCollaboratorManager

        config_path = Path(config_file) if config_file else None
        manager = CycleCollaboratorManager(config_path, auto_confirm=True)

        if not dry_run:
            if not manager.validate_configuration():
                logger.error("Configuration validation failed")
                raise typer.Exit(code=1)

        batch_file_path = Path(batch_file)
        if not batch_file_path.exists():
            logger.error(f"Batch file not found: {batch_file}")
            raise typer.Exit(code=1)

        if dry_run:
            logger.info("DRY RUN: Would cycle collaborator permissions for batch")
            logger.info(f"Batch file: {batch_file}")
            logger.info(f"Repository URL mode: {repo_url_mode}")
            logger.info(f"Force mode: {force}")
            return

        summary = manager.batch_cycle_from_file(batch_file_path, repo_url_mode, force)
        manager.display_batch_summary(summary)

        if summary.failed_operations > 0:
            logger.warning(f"Completed with {summary.failed_operations} failures")
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
        None,
        help="Repository URL to check access for "
             "(or leave empty to select from student-repos.txt)"),
    username: Optional[str] = typer.Argument(
        None, help="Username to check access for (auto-extracted from URL if not provided)"),
    repo_file: str = typer.Option(
        "student-repos.txt", "--file", "-f",
        help="File containing student repository URLs for interactive selection"),
    config_file: str = typer.Option(
        "assignment.conf", "--config", "-c", help="Configuration file path"),
):
    """
    Check repository access status for a specific user.

    Example:
        $ classdock assignments check-repository-access
        $ classdock assignments check-repository-access https://github.com/org/assignment-student123
    """
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
                raise typer.Exit(code=0)

        except FileNotFoundError:
            logger.error(f"Repository file not found: {repo_file}")
            logger.info("💡 To generate a student repository list, run:")
            logger.info("   $ classdock repos fetch")
            raise typer.Exit(code=1)

    if not username:
        try:
            url_parts = repo_url.rstrip('/').split('/')
            repo_name = url_parts[-1]
            if '-' in repo_name:
                username = repo_name.split('-')[-1]
                logger.info(f"Extracted username from URL: {username}")
            else:
                logger.error("Could not extract username from repository URL")
                logger.error(
                    "Please provide username explicitly: "
                    "check-repository-access <repo_url> <username>")
                raise typer.Exit(code=1)
        except (IndexError, AttributeError) as e:
            logger.error(f"Failed to parse repository URL: {e}")
            raise typer.Exit(code=1)

    try:
        from ..assignments.cycle_collaborator import CycleCollaboratorManager

        config_path = Path(config_file) if config_file else None
        manager = CycleCollaboratorManager(config_path)

        if not manager.validate_configuration():
            logger.error("Configuration validation failed")
            raise typer.Exit(code=1)

        status = manager.check_repository_status(repo_url, username)
        manager.display_repository_status(status)

        if not status.accessible:
            logger.error("❌ Repository is not accessible")
            raise typer.Exit(code=1)
        elif status.needs_cycling:
            logger.warning("⚠️ Repository access issues detected - cycling recommended")
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
    force: bool = typer.Option(False, "--force", "-f", help="Force push without confirmation"),
    interactive: bool = typer.Option(
        True, "--interactive/--non-interactive", help="Enable interactive mode for confirmations"),
    branch: str = typer.Option("main", "--branch", "-b", help="Branch to push to classroom repository"),
    config_file: str = typer.Option(
        "assignment.conf", "--config", "-c", help="Configuration file path"),
):
    """
    Push template repository changes to the classroom repository.

    Examples:
        classdock assignments push-to-classroom
        classdock assignments push-to-classroom --force
        classdock assignments push-to-classroom --branch develop
        classdock assignments push-to-classroom --non-interactive --force
    """
    from ..config.global_config import get_global_config

    verbose, dry_run = get_global_options(ctx)

    try:
        from ..assignments.push_manager import ClassroomPushManager, PushResult

        setup_logging(verbose=verbose)
        logger.info("🚀 Starting classroom repository push workflow")

        if dry_run:
            logger.info("🔍 DRY RUN MODE - No changes will be made")

        global_config = get_global_config()

        manager = ClassroomPushManager(global_config=global_config, assignment_root=Path.cwd())
        manager.branch = branch

        if dry_run:
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
            logger.info("✅ Dry run completed - use without --dry-run to execute")
            return

        result, message = manager.execute_push_workflow(
            force=(force and not interactive),
            interactive=interactive,
        )

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
