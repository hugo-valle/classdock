"""
Tests for the Template Method pattern in AssignmentOrchestrator._run_step().

Verifies that:
- _run_step returns "Skipped" when the config flag is disabled.
- _run_step returns a success StepResult when body returns (True, msg, data).
- _run_step returns a failure StepResult when body returns (False, msg, None).
- _run_step catches exceptions from body and returns a failure StepResult.
- Each step_* method delegates to _run_step (config flag respected).
- duration is populated (>= 0) in returned results.
"""

import pytest
from unittest.mock import MagicMock, patch

from classdock.assignments.orchestrator import (
    AssignmentOrchestrator,
    WorkflowStep,
    StepResult,
)


def _make_orchestrator():
    """Return an orchestrator with a fully-mocked global_config."""
    fake_config = MagicMock()
    fake_config.assignment_name = "test-assignment"
    fake_config.github_organization = "test-org"
    fake_config.template_repo_url = "https://github.com/org/template"
    fake_config.classroom_url = "https://classroom.github.com/a/abc"
    return AssignmentOrchestrator(global_config=fake_config)


# ---------------------------------------------------------------------------
# Direct _run_step tests
# ---------------------------------------------------------------------------

class TestRunStep:
    def test_returns_skipped_when_config_flag_is_false(self):
        orch = _make_orchestrator()
        orch.global_config.step_sync_template = False

        body = MagicMock()  # should NOT be called
        result = orch._run_step(
            WorkflowStep.SYNC, 'step_sync_template', True, False, body)

        assert result.success is True
        assert "Skipped" in result.message
        body.assert_not_called()

    def test_returns_success_result_from_body(self):
        orch = _make_orchestrator()
        orch.global_config.step_sync_template = True

        body = MagicMock(return_value=(True, "done", {"x": 1}))
        result = orch._run_step(
            WorkflowStep.SYNC, 'step_sync_template', True, False, body)

        assert result.success is True
        assert result.message == "done"
        assert result.data == {"x": 1}
        assert result.step == WorkflowStep.SYNC

    def test_returns_failure_result_from_body(self):
        orch = _make_orchestrator()
        orch.global_config.step_discover_repos = True

        body = MagicMock(return_value=(False, "oops", None))
        result = orch._run_step(
            WorkflowStep.DISCOVER, 'step_discover_repos', True, False, body)

        assert result.success is False
        assert result.message == "oops"

    def test_catches_exception_and_returns_failure(self):
        orch = _make_orchestrator()
        orch.global_config.step_manage_secrets = True

        def boom(_dry_run):
            raise RuntimeError("network down")

        result = orch._run_step(
            WorkflowStep.SECRETS, 'step_manage_secrets', True, False, boom)

        assert result.success is False
        assert "network down" in result.message

    def test_duration_is_non_negative(self):
        orch = _make_orchestrator()
        orch.global_config.step_sync_template = True

        body = MagicMock(return_value=(True, "ok", None))
        result = orch._run_step(
            WorkflowStep.SYNC, 'step_sync_template', True, False, body)

        assert result.duration >= 0.0

    def test_body_receives_dry_run_flag(self):
        orch = _make_orchestrator()
        orch.global_config.step_assist_students = True

        body = MagicMock(return_value=(True, "ok", None))
        orch._run_step(WorkflowStep.ASSIST, 'step_assist_students', False, True, body)
        body.assert_called_once_with(True)

    def test_uses_config_default_when_attribute_absent(self):
        orch = _make_orchestrator()
        # Ensure the attribute does NOT exist on the mock
        del orch.global_config.step_cycle_collaborators

        body = MagicMock(return_value=(True, "ok", None))
        # default=False → should return Skipped
        result = orch._run_step(
            WorkflowStep.CYCLE, 'step_cycle_collaborators', False, False, body)

        assert "Skipped" in result.message
        body.assert_not_called()


# ---------------------------------------------------------------------------
# step_* methods delegate to _run_step (config flag respected)
# ---------------------------------------------------------------------------

class TestStepMethodsDelegation:
    def _orch_with(self, **flags) -> AssignmentOrchestrator:
        orch = _make_orchestrator()
        for attr, val in flags.items():
            setattr(orch.global_config, attr, val)
        return orch

    def test_step_sync_template_skips_when_disabled(self):
        orch = self._orch_with(step_sync_template=False)
        result = orch.step_sync_template(dry_run=False)
        assert "Skipped" in result.message

    def test_step_sync_template_dry_run(self):
        orch = self._orch_with(step_sync_template=True)
        result = orch.step_sync_template(dry_run=True)
        assert result.success is True
        assert "DRY RUN" in result.message

    def test_step_discover_repos_skips_when_disabled(self):
        orch = self._orch_with(step_discover_repos=False)
        result = orch.step_discover_repos(dry_run=False)
        assert "Skipped" in result.message

    def test_step_discover_repos_dry_run(self):
        orch = self._orch_with(step_discover_repos=True)
        result = orch.step_discover_repos(dry_run=True)
        assert result.success is True
        assert "DRY RUN" in result.message

    def test_step_assist_students_skips_when_disabled(self):
        orch = self._orch_with(step_assist_students=False)
        result = orch.step_assist_students(dry_run=False)
        assert "Skipped" in result.message

    def test_step_cycle_collaborators_skips_when_disabled(self):
        orch = self._orch_with(step_cycle_collaborators=False)
        result = orch.step_cycle_collaborators(dry_run=False)
        assert "Skipped" in result.message

    def test_step_cycle_collaborators_dry_run(self):
        orch = self._orch_with(step_cycle_collaborators=True)
        result = orch.step_cycle_collaborators(dry_run=True)
        assert result.success is True
        assert "DRY RUN" in result.message

    def test_all_step_methods_return_step_result(self):
        orch = _make_orchestrator()
        for attr in ['step_sync_template', 'step_discover_repos',
                     'step_sync_roster', 'step_manage_secrets',
                     'step_assist_students', 'step_cycle_collaborators']:
            setattr(orch.global_config, attr, False)

        step_methods = [
            orch.step_sync_template,
            orch.step_discover_repos,
            orch.step_sync_roster,
            orch.step_manage_secrets,
            orch.step_assist_students,
            orch.step_cycle_collaborators,
        ]
        for method in step_methods:
            result = method(dry_run=True)
            assert isinstance(result, StepResult), \
                f"{method.__name__} did not return StepResult"
