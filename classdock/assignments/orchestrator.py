"""
Assignment Orchestrator - Python Implementation

This module provides a comprehensive Python implementation
that coordinates the complete workflow for managing GitHub Classroom assignments.

Main workflow steps:
1. Template synchronization with classroom 
2. Student repository discovery
3. Secret management across repositories
4. Optional student assistance 
5. Optional collaborator cycling

Author: ClassDock Team
"""

import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set, Tuple

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.table import Table

from ..config.global_config import get_global_config, load_global_config
from ..utils.logger import get_logger

# Module-level logger for backward compatibility with tests
logger = get_logger("assignments.orchestrator")


class WorkflowStep(Enum):
    """Available workflow steps."""

    SYNC = "sync"
    DISCOVER = "discover"
    SYNC_ROSTER = "sync_roster"
    SECRETS = "secrets"
    ASSIST = "assist"
    CYCLE = "cycle"


@dataclass
class StepResult:
    """Result of executing a workflow step."""

    step: WorkflowStep
    success: bool
    message: str
    duration: float
    data: Optional[Dict] = None


@dataclass
class WorkflowConfig:
    """Configuration for workflow execution."""

    enabled_steps: Set[WorkflowStep]
    dry_run: bool = False
    verbose: bool = False
    force_yes: bool = False
    step_override: Optional[WorkflowStep] = None
    skip_steps: Set[WorkflowStep] = None

    def __post_init__(self):
        if self.skip_steps is None:
            self.skip_steps = set()


@dataclass
class WorkflowCommand:
    """
    Encapsulates a single executable workflow step as a Command object.

    Separates the *description* of what a step will do from the *execution*
    of that step, enabling dry-run preview and ordered planning without
    coupling the caller to step implementation details.
    """

    step: WorkflowStep
    description: str
    _executor: object = None  # callable set by get_workflow_plan

    def execute(self, dry_run: bool = False) -> "StepResult":
        """Execute the step via the bound executor method."""
        if self._executor is None:
            raise RuntimeError(f"WorkflowCommand for {self.step} has no executor bound")
        return self._executor(dry_run=dry_run)


class AssignmentOrchestrator:
    """
    Main workflow coordinator for GitHub Classroom assignments.

    Orchestrates template sync, discovery, secrets, and assistance steps
    using the Python implementations we've already created.
    """

    def __init__(self, config_file: Optional[Path] = None, global_config=None):
        """Initialize the orchestrator with configuration.

        Args:
            config_file: Path to assignment configuration file.
            global_config: Pre-loaded GlobalConfig instance. When provided,
                ``load_global_config`` is not called, which removes the hidden
                module-level side-effect and makes the class easier to test.
        """
        self.logger = get_logger(__name__)
        self.console = Console()

        if global_config is not None:
            # Injected config — skip file I/O entirely
            self.global_config = global_config
        else:
            # Load global configuration from file (original behaviour)
            if config_file:
                try:
                    load_global_config(str(config_file))
                except FileNotFoundError:
                    self.logger.warning(f"Configuration file not found: {config_file}")
            self.global_config = get_global_config()

        self.config_file = config_file or Path.cwd() / "assignment.conf"

        # Workflow state
        self.results: List[StepResult] = []
        self.start_time: Optional[float] = None
        self.discovered_repos: List[str] = []

    def validate_configuration(self) -> bool:
        """Validate that required configuration is present."""
        try:
            # Check if global config is loaded
            if not self.global_config:
                self.logger.error("Global configuration not loaded")
                return False

            # Check required fields
            required_fields = [
                "classroom_url",
                "template_repo_url",
                "github_organization",
                "assignment_name",
            ]

            for field in required_fields:
                if not getattr(self.global_config, field, None):
                    self.logger.error(f"Required configuration field missing: {field}")
                    return False

            self.logger.info("Configuration validation passed")
            return True

        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            return False

    def show_configuration_summary(self) -> None:
        """Display configuration summary."""
        table = Table(title="Assignment Configuration")
        table.add_column("Setting", style="bold blue")
        table.add_column("Value", style="green")

        table.add_row("Assignment", self.global_config.assignment_name or "Not set")
        table.add_row(
            "Organization", self.global_config.github_organization or "Not set"
        )
        table.add_row(
            "Template Repository", self.global_config.template_repo_url or "Not set"
        )
        table.add_row("Classroom URL", self.global_config.classroom_url or "Not set")
        table.add_row(
            "Assignment File", self.global_config.assignment_file or "assignment.conf"
        )

        # Show enabled workflow steps
        enabled_steps = []
        if getattr(self.global_config, "step_sync_template", True):
            enabled_steps.append("✓ Sync Template")
        if getattr(self.global_config, "step_discover_repos", True):
            enabled_steps.append("✓ Discover Repos")
        if getattr(self.global_config, "step_sync_roster", False):
            enabled_steps.append("✓ Sync Roster")
        if getattr(self.global_config, "step_manage_secrets", True):
            enabled_steps.append("✓ Manage Secrets")
        if getattr(self.global_config, "step_assist_students", False):
            enabled_steps.append("✓ Assist Students")
        if getattr(self.global_config, "step_cycle_collaborators", False):
            enabled_steps.append("✓ Cycle Collaborators")

        table.add_row("Workflow Steps", "\n".join(enabled_steps))

        self.console.print(table)

    def get_workflow_plan(
        self, workflow_config: "WorkflowConfig"
    ) -> "List[WorkflowCommand]":
        """
        Return the ordered list of WorkflowCommands that would run for *workflow_config*
        without executing any of them.

        The live path calls ``command.execute()`` on each item; the dry-run path
        iterates the plan and logs ``command.description`` without executing.
        """
        all_commands = [
            WorkflowCommand(
                WorkflowStep.SYNC,
                "Synchronize template with classroom",
                self.step_sync_template,
            ),
            WorkflowCommand(
                WorkflowStep.DISCOVER,
                "Discover student repositories",
                self.step_discover_repos,
            ),
            WorkflowCommand(
                WorkflowStep.SYNC_ROSTER,
                "Sync repositories with roster",
                self.step_sync_roster,
            ),
            WorkflowCommand(
                WorkflowStep.SECRETS,
                "Manage secrets for student repositories",
                self.step_manage_secrets,
            ),
            WorkflowCommand(
                WorkflowStep.ASSIST,
                "Run student assistance tools",
                self.step_assist_students,
            ),
            WorkflowCommand(
                WorkflowStep.CYCLE,
                "Cycle collaborator access",
                self.step_cycle_collaborators,
            ),
        ]

        if workflow_config.step_override:
            return [
                cmd for cmd in all_commands if cmd.step == workflow_config.step_override
            ]

        return [
            cmd
            for cmd in all_commands
            if cmd.step in workflow_config.enabled_steps
            and cmd.step not in workflow_config.skip_steps
        ]

    def confirm_execution(self, workflow_config: WorkflowConfig) -> bool:
        """Confirm workflow execution with user."""
        if workflow_config.force_yes or workflow_config.dry_run:
            return True

        return typer.confirm("Do you want to proceed with this workflow?")

    # ------------------------------------------------------------------
    # Template Method: common algorithm skeleton for every workflow step
    # ------------------------------------------------------------------

    def _run_step(
        self,
        step: WorkflowStep,
        config_attr: str,
        config_default: bool,
        dry_run: bool,
        body: Callable[[bool], Tuple[bool, str, Optional[Dict]]],
    ) -> StepResult:
        """
        Template Method that defines the invariant algorithm for a workflow step.

        The skeleton is:
            1. Check whether the step is enabled in global config.
               If not, return a "Skipped" result immediately.
            2. Execute the step-specific *body* callable.
            3. Wrap execution in try/except; on failure return a failed
               ``StepResult`` with the error message.

        Subclasses or future steps only need to supply a *body* callable that
        implements the varying part of the algorithm.

        Args:
            step:           The ``WorkflowStep`` enum value for this step.
            config_attr:    Attribute name on ``global_config`` that enables/disables this step.
            config_default: Default value when the attribute is absent.
            dry_run:        Passed through to *body*.
            body:           ``(dry_run) -> (success, message, data | None)``
        """
        if not getattr(self.global_config, config_attr, config_default):
            return StepResult(
                step=step,
                success=True,
                message="Skipped (disabled in config)",
                duration=0.0,
            )

        start_time = time.time()
        try:
            success, message, data = body(dry_run)
            return StepResult(
                step=step,
                success=success,
                message=message,
                duration=time.time() - start_time,
                data=data,
            )
        except Exception as e:
            self.logger.error(f"{step.value} failed: {e}")
            return StepResult(
                step=step,
                success=False,
                message=f"{step.value} failed: {e}",
                duration=time.time() - start_time,
            )

    # ------------------------------------------------------------------
    # Workflow step methods — each delegates to _run_step
    # ------------------------------------------------------------------

    def step_sync_template(self, dry_run: bool = False) -> StepResult:
        """
        Step 1: Synchronize template with classroom.

        Note: This step requires template push functionality that will be
        implemented in the push manager component.
        For now, we'll provide a placeholder that logs the action.
        """

        def body(dry_run: bool) -> Tuple[bool, str, None]:
            if dry_run:
                self.logger.info("DRY RUN: Would synchronize template with classroom")
                self.logger.info(
                    f"Template repo: {self.global_config.template_repo_url}"
                )
                return True, "DRY RUN: Template sync simulated", None
            self.logger.warning("Template sync requires push manager integration")
            self.logger.info("Use 'classdock repos push' for template synchronization")
            return True, "Template sync available via push manager", None

        return self._run_step(
            WorkflowStep.SYNC, "step_sync_template", True, dry_run, body
        )

    def step_discover_repos(self, dry_run: bool = False) -> StepResult:
        """Step 2: Discover student repositories using GitHub Classroom API."""

        def body(dry_run: bool) -> Tuple[bool, str, Optional[Dict]]:
            if dry_run:
                self.logger.info("DRY RUN: Would discover student repositories")
                self.logger.info(
                    f"Organization: {self.global_config.github_organization}"
                )
                self.logger.info(f"Assignment: {self.global_config.assignment_name}")
                repos = [
                    "https://github.com/example/student-repo-1",
                    "https://github.com/example/student-repo-2",
                ]
                return (
                    True,
                    f"DRY RUN: Would discover {len(repos)} repositories",
                    {"repositories": None, "count": len(repos)},
                )

            from ..services.repos_service import ReposService

            self.logger.info("Discovering student repositories...")
            repos_service = ReposService(dry_run=False, verbose=self.logger.level <= 10)
            success, fetch_message = repos_service.fetch(
                config_file=str(self.config_file)
            )

            if not success:
                return False, f"Repository discovery failed: {fetch_message}", None

            student_repos_file = Path("student-repos.txt")
            if student_repos_file.exists():
                with open(student_repos_file, "r") as f:
                    repos = [
                        line.strip()
                        for line in f
                        if line.strip() and not line.startswith("#")
                    ]
                self.discovered_repos = repos
                return (
                    True,
                    f"Discovered {len(repos)} student repositories",
                    {"repositories": repos, "count": len(repos)},
                )

            self.discovered_repos = []
            return True, "No repositories discovered", {"repositories": [], "count": 0}

        return self._run_step(
            WorkflowStep.DISCOVER, "step_discover_repos", True, dry_run, body
        )

    def step_sync_roster(self, dry_run: bool = False) -> StepResult:
        """Step 2.5: Sync discovered repositories with roster database."""

        def body(dry_run: bool) -> Tuple[bool, str, None]:
            from ..utils.database import DatabaseManager

            db = DatabaseManager()
            if not db.database_exists():
                self.logger.warning(
                    "Roster database not initialized. Run 'classdock roster init' first."
                )
                return True, "Skipped (roster database not initialized)", None

            if dry_run:
                self.logger.info("DRY RUN: Would sync repositories with roster")
                return (
                    True,
                    f"DRY RUN: Would sync {len(self.discovered_repos)} repositories with roster",
                    None,
                )

            if not self.discovered_repos:
                self.logger.info("No repositories to sync")
                return True, "No repositories to sync", None

            from ..services.roster_service import RosterService

            self.logger.info("Syncing repositories with roster...")
            roster_service = RosterService()

            repos_data = []
            for repo_url in self.discovered_repos:
                if "/" in repo_url:
                    repo_name = repo_url.split("/")[-1]
                    if "-" in repo_name:
                        parts = repo_name.split("-")
                        repos_data.append((repo_name, repo_url, parts[-1]))

            if not repos_data:
                return True, "No valid repositories to sync", None

            result = roster_service.sync_repositories(
                self.global_config.assignment_name,
                self.global_config.github_organization,
                repos_data,
            )
            message = (
                f"Synced {result.linked_count}/{result.total_repos} repositories "
                f"({result.success_rate:.1f}% success rate)"
            )
            if result.unlinked_count > 0:
                self.logger.warning(
                    f"{result.unlinked_count} repositories could not be linked to roster"
                )
            return True, message, None

        # Roster sync errors are non-fatal — catch inside and return success
        try:
            return self._run_step(
                WorkflowStep.SYNC_ROSTER, "step_sync_roster", False, dry_run, body
            )
        except Exception as e:
            self.logger.error(f"Roster sync failed: {e}")
            return StepResult(
                step=WorkflowStep.SYNC_ROSTER,
                success=True,
                message=f"Roster sync skipped: {e}",
                duration=0.0,
            )

    def step_manage_secrets(self, dry_run: bool = False) -> StepResult:
        """Step 3: Manage secrets across repositories using our GitHub secrets manager."""

        def body(dry_run: bool) -> Tuple[bool, str, Optional[Dict]]:
            if not dry_run and not self.discovered_repos:
                student_repos_file = Path("student-repos.txt")
                if student_repos_file.exists():
                    with open(student_repos_file, "r") as f:
                        self.discovered_repos = [
                            line.strip()
                            for line in f
                            if line.strip() and not line.startswith("#")
                        ]
                else:
                    return (
                        False,
                        "No repositories found. Run discovery step first.",
                        None,
                    )

            if dry_run:
                self.logger.info(
                    "DRY RUN: Would manage secrets for student repositories"
                )
                return True, "DRY RUN: Secret management simulated", {}

            from ..services.secrets_service import SecretsService

            self.logger.info(
                f"Managing secrets for {len(self.discovered_repos)} repositories..."
            )
            secrets_service = SecretsService(
                dry_run=False, verbose=self.logger.level <= 10
            )
            success, message = secrets_service.add_secrets(
                repo_urls=self.discovered_repos, force_update=False
            )
            return success, message, {}

        return self._run_step(
            WorkflowStep.SECRETS, "step_manage_secrets", True, dry_run, body
        )

    def step_assist_students(self, dry_run: bool = False) -> StepResult:
        """
        Step 4: Student assistance.

        Note: This step requires student update helper functionality that will be
        implemented in the student helper component.
        """

        def body(dry_run: bool) -> Tuple[bool, str, None]:
            if dry_run:
                self.logger.info("DRY RUN: Would run student assistance tools")
                return True, "DRY RUN: Student assistance simulated", None
            self.logger.warning(
                "Student assistance requires direct student helper usage"
            )
            self.logger.info(
                "Use 'classdock assignments student-help' for assistance tools"
            )
            return True, "Student assistance available via student helper", None

        return self._run_step(
            WorkflowStep.ASSIST, "step_assist_students", False, dry_run, body
        )

    def step_cycle_collaborators(self, dry_run: bool = False) -> StepResult:
        """
        Step 5: Cycle collaborator access.

        Note: This step requires collaborator cycling functionality that will be
        implemented in the cycle collaborator component.
        """

        def body(dry_run: bool) -> Tuple[bool, str, None]:
            if dry_run:
                self.logger.info("DRY RUN: Would cycle collaborator access")
                return True, "DRY RUN: Collaborator cycling simulated", None
            self.logger.warning(
                "Collaborator cycling requires direct cycle collaborator usage"
            )
            self.logger.info(
                "Use 'classdock repos cycle-collaborator' for access management"
            )
            return True, "Collaborator cycling available via cycle collaborator", None

        return self._run_step(
            WorkflowStep.CYCLE, "step_cycle_collaborators", False, dry_run, body
        )

    def execute_single_step(
        self, step: WorkflowStep, dry_run: bool = False
    ) -> StepResult:
        """Execute a single workflow step."""
        self.logger.info(f"Executing single step: {step.value}")

        step_methods = {
            WorkflowStep.SYNC: self.step_sync_template,
            WorkflowStep.DISCOVER: self.step_discover_repos,
            WorkflowStep.SYNC_ROSTER: self.step_sync_roster,
            WorkflowStep.SECRETS: self.step_manage_secrets,
            WorkflowStep.ASSIST: self.step_assist_students,
            WorkflowStep.CYCLE: self.step_cycle_collaborators,
        }

        if step not in step_methods:
            raise ValueError(f"Unknown step: {step}")

        return step_methods[step](dry_run)

    def execute_workflow(self, workflow_config: WorkflowConfig) -> List[StepResult]:
        """Execute the complete workflow or a specific step."""
        self.start_time = time.time()
        self.results = []

        self.logger.info("Starting assignment workflow execution")

        # Show workflow header
        if workflow_config.dry_run:
            self.console.print(
                Panel("🧪 DRY RUN MODE - No actual changes will be made", style="yellow")
            )

        try:
            # Execute single step if specified
            if workflow_config.step_override:
                result = self.execute_single_step(
                    workflow_config.step_override, workflow_config.dry_run
                )
                self.results.append(result)
                return self.results

            # Execute full workflow
            steps_to_run = [
                (WorkflowStep.SYNC, self.step_sync_template),
                (WorkflowStep.DISCOVER, self.step_discover_repos),
                (WorkflowStep.SYNC_ROSTER, self.step_sync_roster),
                (WorkflowStep.SECRETS, self.step_manage_secrets),
                (WorkflowStep.ASSIST, self.step_assist_students),
                (WorkflowStep.CYCLE, self.step_cycle_collaborators),
            ]

            repos_discovered = False

            with Progress() as progress:
                task = progress.add_task("Workflow Progress", total=len(steps_to_run))

                for step_enum, step_method in steps_to_run:
                    # Skip if not in enabled steps or is in skip list
                    if (
                        workflow_config.enabled_steps
                        and step_enum not in workflow_config.enabled_steps
                    ):
                        continue
                    if step_enum in workflow_config.skip_steps:
                        continue

                    progress.update(task, description=f"Executing {step_enum.value}...")
                    result = step_method(workflow_config.dry_run)
                    self.results.append(result)

                    # Track if repositories were discovered for dependent steps
                    if step_enum == WorkflowStep.DISCOVER and result.success:
                        repos_discovered = True

                    # Skip repository-dependent steps if no repos were discovered
                    if not repos_discovered and step_enum in [
                        WorkflowStep.SYNC_ROSTER,
                        WorkflowStep.SECRETS,
                        WorkflowStep.ASSIST,
                        WorkflowStep.CYCLE,
                    ]:
                        if not workflow_config.dry_run:
                            self.logger.warning(
                                f"Skipping {step_enum.value} (no repositories discovered)"
                            )
                            continue

                    progress.advance(task)

            return self.results

        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}")
            raise

    def generate_workflow_report(self) -> Dict:
        """Generate a comprehensive workflow report."""
        if not self.start_time:
            return {}

        total_duration = time.time() - self.start_time

        # Count successes and failures
        successful_steps = [r for r in self.results if r.success]
        failed_steps = [r for r in self.results if not r.success]

        # Create summary table
        table = Table(title="Workflow Execution Report")
        table.add_column("Step", style="bold")
        table.add_column("Status", style="bold")
        table.add_column("Duration", style="cyan")
        table.add_column("Message", style="dim")

        for result in self.results:
            status = "✅ SUCCESS" if result.success else "❌ FAILED"
            status_style = "green" if result.success else "red"
            table.add_row(
                result.step.value.title(),
                f"[{status_style}]{status}[/{status_style}]",
                f"{result.duration:.2f}s",
                result.message,
            )

        self.console.print(table)

        # Summary
        self.console.print(f"\n[bold green]Total Steps:[/] {len(self.results)}")
        self.console.print(f"[bold green]Successful:[/] {len(successful_steps)}")
        self.console.print(f"[bold red]Failed:[/] {len(failed_steps)}")
        self.console.print(f"[bold blue]Total Duration:[/] {total_duration:.2f}s")

        return {
            "total_steps": len(self.results),
            "successful_steps": len(successful_steps),
            "failed_steps": len(failed_steps),
            "total_duration": total_duration,
            "results": [
                {
                    "step": r.step.value,
                    "success": r.success,
                    "message": r.message,
                    "duration": r.duration,
                    "data": r.data,
                }
                for r in self.results
            ],
        }

    # Legacy methods for backward compatibility with existing tests
    def run_complete_workflow(self):
        """Legacy method - use execute_workflow instead."""
        logger.info("Running complete workflow")
        workflow_config = WorkflowConfig(
            enabled_steps=set(WorkflowStep),
            dry_run=False,
            verbose=False,
            force_yes=True,
        )
        return self.execute_workflow(workflow_config)

    def sync_template(self):
        """Legacy method - use step_sync_template instead."""
        logger.info("Syncing template repository")
        return self.step_sync_template(dry_run=False)

    def discover_repositories(self):
        """Legacy method - use step_discover_repos instead."""
        logger.info("Discovering student repositories")
        return self.step_discover_repos(dry_run=False)

    def manage_secrets(self):
        """Legacy method - use step_manage_secrets instead."""
        logger.info("Managing secrets")
        return self.step_manage_secrets(dry_run=False)

    def assist_students(self):
        """Legacy method - use step_assist_students instead."""
        logger.info("Assisting students")
        return self.step_assist_students(dry_run=False)


class NullOrchestrator:
    """
    Null Object implementation of AssignmentOrchestrator for dry-run mode.

    Every step method immediately returns a successful StepResult with a
    ``DRY RUN:`` message without touching GitHub, the filesystem, or any
    external service.  This eliminates the scattered ``if dry_run: return``
    guards that previously littered the service and orchestrator layers.
    """

    def __init__(self, config_file=None, global_config=None):
        self.global_config = global_config
        self.config_file = config_file or Path.cwd() / "assignment.conf"
        self.results: List[StepResult] = []
        self.start_time: Optional[float] = None
        self.discovered_repos: List[str] = []

    def _dry_step(self, step: WorkflowStep, description: str) -> StepResult:
        return StepResult(
            step=step,
            success=True,
            message=f"DRY RUN: {description}",
            duration=0.0,
        )

    def validate_configuration(self) -> bool:
        return True

    def show_configuration_summary(self) -> None:
        pass

    def confirm_execution(self, workflow_config) -> bool:
        return True

    def step_sync_template(self, dry_run: bool = False) -> StepResult:
        return self._dry_step(
            WorkflowStep.SYNC, "Would synchronize template with classroom"
        )

    def step_discover_repos(self, dry_run: bool = False) -> StepResult:
        return self._dry_step(
            WorkflowStep.DISCOVER, "Would discover student repositories"
        )

    def step_sync_roster(self, dry_run: bool = False) -> StepResult:
        return self._dry_step(
            WorkflowStep.SYNC_ROSTER, "Would sync repositories with roster"
        )

    def step_manage_secrets(self, dry_run: bool = False) -> StepResult:
        return self._dry_step(
            WorkflowStep.SECRETS, "Would manage secrets for student repositories"
        )

    def step_assist_students(self, dry_run: bool = False) -> StepResult:
        return self._dry_step(WorkflowStep.ASSIST, "Would run student assistance tools")

    def step_cycle_collaborators(self, dry_run: bool = False) -> StepResult:
        return self._dry_step(WorkflowStep.CYCLE, "Would cycle collaborator access")

    def execute_single_step(
        self, step: WorkflowStep, dry_run: bool = False
    ) -> StepResult:
        step_methods = {
            WorkflowStep.SYNC: self.step_sync_template,
            WorkflowStep.DISCOVER: self.step_discover_repos,
            WorkflowStep.SYNC_ROSTER: self.step_sync_roster,
            WorkflowStep.SECRETS: self.step_manage_secrets,
            WorkflowStep.ASSIST: self.step_assist_students,
            WorkflowStep.CYCLE: self.step_cycle_collaborators,
        }
        return step_methods[step](dry_run)

    def execute_workflow(self, workflow_config) -> List[StepResult]:
        _log = get_logger(__name__)
        _log.info("DRY RUN: Workflow execution simulated — no changes made")
        self.start_time = time.time()
        steps = [
            WorkflowStep.SYNC,
            WorkflowStep.DISCOVER,
            WorkflowStep.SYNC_ROSTER,
            WorkflowStep.SECRETS,
            WorkflowStep.ASSIST,
            WorkflowStep.CYCLE,
        ]
        if workflow_config.step_override:
            self.results = [self.execute_single_step(workflow_config.step_override)]
        else:
            self.results = [
                self.execute_single_step(s)
                for s in steps
                if s in workflow_config.enabled_steps
                and s not in workflow_config.skip_steps
            ]
        for r in self.results:
            _log.info(f"  {r.step.value}: {r.message}")
        return self.results

    def generate_workflow_report(self) -> Dict:
        return {"dry_run": True, "results": []}
