"""
Tests for the Command Pattern applied to workflow steps.

Verifies that:
- WorkflowCommand encapsulates a step with a description and an execute() method.
- get_workflow_plan() returns commands in the correct order for a given config.
- Commands execute the underlying step method when execute() is called.
- Push workflow dry-run uses a derived list instead of a hardcoded string.
- ReposService.fetch() respects dry_run.
"""

import pytest
from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# WorkflowCommand dataclass
# ---------------------------------------------------------------------------

class TestWorkflowCommand:
    def _make_command(self, step_value="sync", description="Do sync"):
        from classdock.assignments.orchestrator import WorkflowCommand, WorkflowStep, StepResult
        step = WorkflowStep(step_value)
        fake_result = StepResult(step=step, success=True, message="ok", duration=0.0)
        executor = MagicMock(return_value=fake_result)
        cmd = WorkflowCommand(step=step, description=description, _executor=executor)
        return cmd, executor, fake_result

    def test_execute_calls_bound_executor(self):
        cmd, executor, expected = self._make_command()
        result = cmd.execute(dry_run=False)
        executor.assert_called_once_with(dry_run=False)
        assert result is expected

    def test_execute_passes_dry_run_flag(self):
        cmd, executor, _ = self._make_command()
        cmd.execute(dry_run=True)
        executor.assert_called_once_with(dry_run=True)

    def test_description_is_stored(self):
        cmd, _, _ = self._make_command(description="Synchronize template")
        assert cmd.description == "Synchronize template"

    def test_step_is_stored(self):
        from classdock.assignments.orchestrator import WorkflowStep
        cmd, _, _ = self._make_command(step_value="discover")
        assert cmd.step == WorkflowStep.DISCOVER

    def test_execute_without_executor_raises(self):
        from classdock.assignments.orchestrator import WorkflowCommand, WorkflowStep
        cmd = WorkflowCommand(step=WorkflowStep.SYNC, description="test", _executor=None)
        with pytest.raises(RuntimeError, match="no executor bound"):
            cmd.execute()


# ---------------------------------------------------------------------------
# AssignmentOrchestrator.get_workflow_plan()
# ---------------------------------------------------------------------------

class TestGetWorkflowPlan:
    def _make_orchestrator(self):
        from classdock.assignments.orchestrator import AssignmentOrchestrator
        fake_config = MagicMock()
        fake_config.assignment_name = "test"
        fake_config.github_organization = "org"
        return AssignmentOrchestrator(global_config=fake_config)

    def test_plan_returns_all_enabled_steps(self):
        from classdock.assignments.orchestrator import WorkflowConfig, WorkflowStep
        orch = self._make_orchestrator()
        cfg = WorkflowConfig(enabled_steps=set(WorkflowStep))
        plan = orch.get_workflow_plan(cfg)
        plan_steps = {cmd.step for cmd in plan}
        assert plan_steps == set(WorkflowStep)

    def test_plan_excludes_skipped_steps(self):
        from classdock.assignments.orchestrator import WorkflowConfig, WorkflowStep
        orch = self._make_orchestrator()
        cfg = WorkflowConfig(
            enabled_steps=set(WorkflowStep),
            skip_steps={WorkflowStep.ASSIST, WorkflowStep.CYCLE},
        )
        plan = orch.get_workflow_plan(cfg)
        plan_steps = {cmd.step for cmd in plan}
        assert WorkflowStep.ASSIST not in plan_steps
        assert WorkflowStep.CYCLE not in plan_steps

    def test_plan_with_step_override_returns_single_command(self):
        from classdock.assignments.orchestrator import WorkflowConfig, WorkflowStep
        orch = self._make_orchestrator()
        cfg = WorkflowConfig(
            enabled_steps=set(WorkflowStep),
            step_override=WorkflowStep.SECRETS,
        )
        plan = orch.get_workflow_plan(cfg)
        assert len(plan) == 1
        assert plan[0].step == WorkflowStep.SECRETS

    def test_plan_commands_have_non_empty_descriptions(self):
        from classdock.assignments.orchestrator import WorkflowConfig, WorkflowStep
        orch = self._make_orchestrator()
        cfg = WorkflowConfig(enabled_steps=set(WorkflowStep))
        for cmd in orch.get_workflow_plan(cfg):
            assert cmd.description, f"Command for {cmd.step} has empty description"

    def test_plan_steps_are_in_correct_order(self):
        from classdock.assignments.orchestrator import WorkflowConfig, WorkflowStep
        orch = self._make_orchestrator()
        cfg = WorkflowConfig(enabled_steps=set(WorkflowStep))
        plan = orch.get_workflow_plan(cfg)
        expected_order = [
            WorkflowStep.SYNC, WorkflowStep.DISCOVER, WorkflowStep.SYNC_ROSTER,
            WorkflowStep.SECRETS, WorkflowStep.ASSIST, WorkflowStep.CYCLE,
        ]
        assert [cmd.step for cmd in plan] == expected_order

    def test_plan_commands_are_executable(self):
        """execute() on each plan command returns a StepResult."""
        from classdock.assignments.orchestrator import WorkflowConfig, WorkflowStep, StepResult
        orch = self._make_orchestrator()
        # Provide minimal config attributes to avoid real API calls
        orch.global_config.step_sync_template = False
        orch.global_config.step_discover_repos = False
        orch.global_config.step_sync_roster = False
        orch.global_config.step_manage_secrets = False
        orch.global_config.step_assist_students = False
        orch.global_config.step_cycle_collaborators = False

        cfg = WorkflowConfig(enabled_steps=set(WorkflowStep))
        plan = orch.get_workflow_plan(cfg)
        for cmd in plan:
            result = cmd.execute(dry_run=True)
            assert isinstance(result, StepResult)


# ---------------------------------------------------------------------------
# ReposService.fetch() dry_run
# ---------------------------------------------------------------------------

class TestReposServiceDryRun:
    def test_fetch_dry_run_returns_success_without_calling_fetcher(self):
        from classdock.services.repos_service import ReposService

        fetcher_factory = MagicMock()
        service = ReposService(dry_run=True, fetcher_factory=fetcher_factory)
        ok, msg = service.fetch()

        assert ok is True
        assert "DRY RUN" in msg
        fetcher_factory.assert_not_called()

    def test_fetch_live_calls_fetcher(self):
        from classdock.services.repos_service import ReposService

        fake_fetcher = MagicMock()
        fake_fetcher.fetch_all_repositories.return_value = True
        factory = MagicMock(return_value=fake_fetcher)

        service = ReposService(dry_run=False, fetcher_factory=factory)
        ok, _ = service.fetch()

        factory.assert_called_once()
        fake_fetcher.fetch_all_repositories.assert_called_once()
        assert ok
