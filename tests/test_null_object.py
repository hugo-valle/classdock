"""
Tests for the Null Object pattern.

Verifies that:
- NullOrchestrator implements the full AssignmentOrchestrator interface.
- NullOrchestrator returns successful StepResults with "DRY RUN:" messages.
- NullSecretsManager implements the GitHubSecretsManager interface.
- Services auto-inject null objects when dry_run=True.
"""

import pytest
from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# NullOrchestrator
# ---------------------------------------------------------------------------

class TestNullOrchestrator:
    def _make(self):
        from classdock.assignments.orchestrator import NullOrchestrator
        return NullOrchestrator()

    def test_validate_configuration_always_true(self):
        assert self._make().validate_configuration() is True

    def test_confirm_execution_always_true(self):
        wf = MagicMock()
        assert self._make().confirm_execution(wf) is True

    def test_every_step_returns_dry_run_message(self):
        from classdock.assignments.orchestrator import WorkflowStep
        null = self._make()
        step_methods = {
            WorkflowStep.SYNC: null.step_sync_template,
            WorkflowStep.DISCOVER: null.step_discover_repos,
            WorkflowStep.SYNC_ROSTER: null.step_sync_roster,
            WorkflowStep.SECRETS: null.step_manage_secrets,
            WorkflowStep.ASSIST: null.step_assist_students,
            WorkflowStep.CYCLE: null.step_cycle_collaborators,
        }
        for step, method in step_methods.items():
            result = method()
            assert result.success is True
            assert "DRY RUN" in result.message
            assert result.step == step

    def test_execute_single_step_delegates(self):
        from classdock.assignments.orchestrator import NullOrchestrator, WorkflowStep
        null = NullOrchestrator()
        result = null.execute_single_step(WorkflowStep.SECRETS)
        assert result.success is True
        assert "DRY RUN" in result.message

    def test_execute_workflow_returns_results_for_enabled_steps(self):
        from classdock.assignments.orchestrator import (
            NullOrchestrator, WorkflowConfig, WorkflowStep
        )
        null = NullOrchestrator()
        cfg = WorkflowConfig(enabled_steps={WorkflowStep.SYNC, WorkflowStep.DISCOVER})
        results = null.execute_workflow(cfg)
        assert len(results) == 2
        assert all(r.success for r in results)
        steps_executed = {r.step for r in results}
        assert steps_executed == {WorkflowStep.SYNC, WorkflowStep.DISCOVER}

    def test_execute_workflow_respects_step_override(self):
        from classdock.assignments.orchestrator import (
            NullOrchestrator, WorkflowConfig, WorkflowStep
        )
        null = NullOrchestrator()
        cfg = WorkflowConfig(
            enabled_steps=set(WorkflowStep),
            step_override=WorkflowStep.SECRETS,
        )
        results = null.execute_workflow(cfg)
        assert len(results) == 1
        assert results[0].step == WorkflowStep.SECRETS

    def test_generate_workflow_report_returns_dry_run_flag(self):
        report = self._make().generate_workflow_report()
        assert report.get("dry_run") is True

    def test_show_configuration_summary_is_safe_no_op(self):
        # Must not raise even with no global_config loaded
        self._make().show_configuration_summary()


# ---------------------------------------------------------------------------
# NullSecretsManager
# ---------------------------------------------------------------------------

class TestNullSecretsManager:
    def _make(self):
        from classdock.secrets.github_secrets import NullSecretsManager
        return NullSecretsManager()

    def test_add_secrets_returns_true(self):
        assert self._make().add_secrets_from_global_config() is True

    def test_add_secrets_with_repo_urls_returns_true(self):
        result = self._make().add_secrets_from_global_config(
            repo_urls=["https://github.com/org/repo1"]
        )
        assert result is True

    def test_add_secrets_with_force_update_returns_true(self):
        result = self._make().add_secrets_from_global_config(force_update=True)
        assert result is True

    def test_dry_run_attribute_set(self):
        from classdock.secrets.github_secrets import NullSecretsManager
        mgr = NullSecretsManager(dry_run=True)
        assert mgr.dry_run is True


# ---------------------------------------------------------------------------
# Auto-injection: services wire null objects for dry_run=True
# ---------------------------------------------------------------------------

class TestAutoInjection:
    def test_assignment_service_injects_null_orchestrator(self):
        from classdock.services.assignment_service import AssignmentService
        from classdock.assignments.orchestrator import NullOrchestrator

        service = AssignmentService(dry_run=True)
        assert service._orchestrator_factory is not None
        instance = service._orchestrator_factory(None)
        assert isinstance(instance, NullOrchestrator)

    def test_secrets_service_injects_null_manager(self):
        from classdock.services.secrets_service import SecretsService
        from classdock.secrets.github_secrets import NullSecretsManager

        service = SecretsService(dry_run=True)
        assert service._secrets_manager_factory is not None
        instance = service._secrets_manager_factory(True)
        assert isinstance(instance, NullSecretsManager)

    def test_assignment_service_dry_run_succeeds_without_github(self):
        """NullOrchestrator lets orchestrate() succeed with no config file or token."""
        from classdock.services.assignment_service import AssignmentService

        service = AssignmentService(dry_run=True)
        ok, msg = service.orchestrate()

        assert ok is True

    def test_secrets_service_dry_run_succeeds_without_config(self):
        """NullSecretsManager lets add_secrets() succeed with no global config."""
        from classdock.services.secrets_service import SecretsService

        service = SecretsService(dry_run=True)
        ok, msg = service.add_secrets(
            repo_urls=["https://github.com/org/repo1"]
        )
        assert ok is True
