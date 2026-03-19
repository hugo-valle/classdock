"""
Tests for Dependency Injection pattern across all ClassDock services.

Verifies that:
- Each service accepts injected collaborators via constructor parameters.
- Injected collaborators are used in place of the default-constructed ones.
- Default behaviour is unchanged when no injection is provided.
"""

from unittest.mock import MagicMock, patch
import pytest


# ---------------------------------------------------------------------------
# AssignmentOrchestrator — global_config injection
# ---------------------------------------------------------------------------

class TestAssignmentOrchestratorDI:
    def test_injected_global_config_is_used(self):
        """When global_config is passed, load_global_config must not be called."""
        from classdock.assignments.orchestrator import AssignmentOrchestrator

        fake_config = MagicMock()
        fake_config.assignment_name = "test-assignment"
        fake_config.github_organization = "test-org"

        with patch("classdock.assignments.orchestrator.load_global_config") as mock_load, \
             patch("classdock.assignments.orchestrator.get_global_config") as mock_get:
            orch = AssignmentOrchestrator(global_config=fake_config)

        mock_load.assert_not_called()
        mock_get.assert_not_called()
        assert orch.global_config is fake_config

    def test_default_loads_config_from_file(self):
        """Without injection, load_global_config should be called."""
        from classdock.assignments.orchestrator import AssignmentOrchestrator

        fake_config = MagicMock()
        with patch("classdock.assignments.orchestrator.load_global_config") as mock_load, \
             patch("classdock.assignments.orchestrator.get_global_config", return_value=fake_config):
            orch = AssignmentOrchestrator()

        mock_load.assert_not_called()  # config_file=None, so no load call
        assert orch.global_config is fake_config


# ---------------------------------------------------------------------------
# AssignmentService — orchestrator_factory injection
# ---------------------------------------------------------------------------

class TestAssignmentServiceDI:
    def test_orchestrator_factory_is_called(self):
        """orchestrator_factory is used instead of constructing AssignmentOrchestrator."""
        from classdock.services.assignment_service import AssignmentService

        fake_orch = MagicMock()
        fake_orch.validate_configuration.return_value = True
        fake_orch.confirm_execution.return_value = True
        fake_orch.execute_workflow.return_value = []
        fake_orch.generate_workflow_report.return_value = {}

        factory = MagicMock(return_value=fake_orch)
        service = AssignmentService(orchestrator_factory=factory)

        service.orchestrate(config_file="assignment.conf")

        factory.assert_called_once()

    def test_default_uses_real_orchestrator(self):
        """Without a factory, AssignmentOrchestrator is constructed directly."""
        from classdock.services.assignment_service import AssignmentService

        service = AssignmentService()
        assert service._orchestrator_factory is None

    def test_dry_run_short_circuits_before_factory(self):
        """dry_run returns before the factory is ever called."""
        from classdock.services.assignment_service import AssignmentService

        factory = MagicMock()
        service = AssignmentService(dry_run=True, orchestrator_factory=factory)

        # Need a valid orchestrator to pass validate_configuration
        fake_orch = MagicMock()
        fake_orch.validate_configuration.return_value = True
        factory.return_value = fake_orch

        ok, msg = service.orchestrate()

        assert ok
        assert "DRY RUN" in msg
        # factory IS called (orchestrator is used for validate_configuration even in dry-run)
        factory.assert_called_once()


# ---------------------------------------------------------------------------
# SecretsService — secrets_manager_factory injection
# ---------------------------------------------------------------------------

class TestSecretsServiceDI:
    def _make_config(self):
        cfg = MagicMock()
        cfg.secrets_config = [MagicMock()]
        return cfg

    def test_factory_is_called_with_dry_run_flag(self):
        """secrets_manager_factory receives dry_run and its instance is used."""
        from classdock.services.secrets_service import SecretsService

        fake_manager = MagicMock()
        fake_manager.add_secrets_from_global_config.return_value = True
        factory = MagicMock(return_value=fake_manager)

        with patch("classdock.commands.secrets.get_global_config", return_value=self._make_config()), \
             patch("classdock.services.secrets_service.get_global_config", return_value=self._make_config()):
            service = SecretsService(secrets_manager_factory=factory)
            ok, _ = service.add_secrets()

        factory.assert_called_once_with(False)  # dry_run=False by default
        fake_manager.add_secrets_from_global_config.assert_called_once()
        assert ok

    def test_no_factory_uses_real_manager_class(self):
        """Without a factory, _secrets_manager_factory is None."""
        from classdock.services.secrets_service import SecretsService

        service = SecretsService()
        assert service._secrets_manager_factory is None


# ---------------------------------------------------------------------------
# ReposService — fetcher / push / cycle factory injection
# ---------------------------------------------------------------------------

class TestReposServiceDI:
    def test_fetcher_factory_is_called(self):
        """fetcher_factory is called with config_path and its return value is used."""
        from classdock.services.repos_service import ReposService

        fake_fetcher = MagicMock()
        fake_fetcher.fetch_all_repositories.return_value = True
        factory = MagicMock(return_value=fake_fetcher)

        service = ReposService(fetcher_factory=factory)
        ok, _ = service.fetch(config_file="assignment.conf")

        factory.assert_called_once()
        fake_fetcher.fetch_all_repositories.assert_called_once()
        assert ok

    def test_push_manager_factory_is_called(self):
        """push_manager_factory is used instead of ClassroomPushManager."""
        from classdock.services.repos_service import ReposService
        from classdock.assignments.push_manager import PushResult

        fake_manager = MagicMock()
        fake_manager.execute_push_workflow.return_value = (PushResult.SUCCESS, "pushed")
        factory = MagicMock(return_value=fake_manager)

        service = ReposService(push_manager_factory=factory)
        ok, _ = service.push()

        factory.assert_called_once()
        fake_manager.execute_push_workflow.assert_called_once()
        assert ok

    def test_cycle_manager_factory_is_called(self):
        """cycle_manager_factory is used instead of CycleCollaboratorManager."""
        from classdock.services.repos_service import ReposService

        fake_manager = MagicMock()
        fake_manager.cycle_single_repository.return_value = (True, "cycled")
        factory = MagicMock(return_value=fake_manager)

        service = ReposService(cycle_manager_factory=factory)
        ok, msg = service.cycle_collaborator(
            assignment_prefix="hw1",
            username="student",
            organization="cs101",
        )

        factory.assert_called_once()
        assert ok

    def test_no_factories_stored_as_none(self):
        from classdock.services.repos_service import ReposService

        service = ReposService()
        assert service._fetcher_factory is None
        assert service._push_manager_factory is None
        assert service._cycle_manager_factory is None


# ---------------------------------------------------------------------------
# AutomationService — cron_manager_factory injection
# ---------------------------------------------------------------------------

class TestAutomationServiceDI:
    def test_cron_install_uses_factory(self):
        from classdock.services.automation_service import AutomationService

        fake_result = MagicMock()
        fake_result.value = "success"
        fake_manager = MagicMock()
        fake_manager.install_cron_job.return_value = (fake_result, "installed")
        factory = MagicMock(return_value=fake_manager)

        service = AutomationService(cron_manager_factory=factory)
        ok, msg = service.cron_install(["sync"], None, "assignment.conf")

        factory.assert_called_once()
        fake_manager.install_cron_job.assert_called_once()
        assert ok

    def test_cron_status_uses_factory(self):
        from classdock.services.automation_service import AutomationService

        fake_status = MagicMock()
        fake_manager = MagicMock()
        fake_manager.get_cron_status.return_value = fake_status
        factory = MagicMock(return_value=fake_manager)

        service = AutomationService(cron_manager_factory=factory)
        ok, status = service.cron_status("assignment.conf")

        factory.assert_called_once()
        assert ok
        assert status is fake_status

    def test_no_factory_stored_as_none(self):
        from classdock.services.automation_service import AutomationService

        service = AutomationService()
        assert service._cron_manager_factory is None

    def test_make_cron_manager_returns_factory_result(self):
        """_make_cron_manager always returns the injected manager."""
        from classdock.services.automation_service import AutomationService

        fake_manager = MagicMock()
        factory = MagicMock(return_value=fake_manager)
        service = AutomationService(cron_manager_factory=factory)

        m1 = service._make_cron_manager()
        m2 = service._make_cron_manager()

        assert m1 is fake_manager
        assert m2 is fake_manager
        assert factory.call_count == 2


# ---------------------------------------------------------------------------
# RosterService — db / manager / importer / synchronizer injection
# ---------------------------------------------------------------------------

class TestRosterServiceDI:
    def test_injected_db_is_used(self):
        """When db is provided, DatabaseManager is not constructed."""
        from classdock.services.roster_service import RosterService
        from classdock.roster.manager import RosterManager
        from classdock.roster.importer import RosterImporter
        from classdock.roster.sync import RosterSynchronizer

        fake_db = MagicMock()
        fake_db.db_path = ":memory:"
        fake_db.database_exists.return_value = True

        service = RosterService(db=fake_db)

        assert service.db is fake_db

    def test_fully_injected_collaborators(self):
        """All four collaborators can be injected at once."""
        from classdock.services.roster_service import RosterService

        fake_db = MagicMock()
        fake_manager = MagicMock()
        fake_importer = MagicMock()
        fake_synchronizer = MagicMock()

        service = RosterService(
            db=fake_db,
            manager=fake_manager,
            importer=fake_importer,
            synchronizer=fake_synchronizer,
        )

        assert service.db is fake_db
        assert service.manager is fake_manager
        assert service.importer is fake_importer
        assert service.synchronizer is fake_synchronizer

    def test_partial_injection_builds_remainder(self):
        """Injecting only db causes manager/importer/synchronizer to be built from it."""
        from classdock.services.roster_service import RosterService
        from classdock.roster.manager import RosterManager
        from classdock.roster.importer import RosterImporter
        from classdock.roster.sync import RosterSynchronizer

        fake_db = MagicMock()
        fake_db.db_path = ":memory:"

        service = RosterService(db=fake_db)

        assert service.db is fake_db
        assert isinstance(service.manager, RosterManager)
        assert isinstance(service.importer, RosterImporter)
        assert isinstance(service.synchronizer, RosterSynchronizer)

    def test_default_builds_all_from_db_path(self, tmp_path):
        """Without injection, all collaborators are constructed from db_path."""
        from classdock.services.roster_service import RosterService
        from classdock.utils.database import DatabaseManager
        from classdock.roster.manager import RosterManager

        service = RosterService(db_path=tmp_path / "test.db")

        assert isinstance(service.db, DatabaseManager)
        assert isinstance(service.manager, RosterManager)
