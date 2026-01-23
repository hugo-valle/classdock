from unittest.mock import patch, Mock

from classdock.services.automation_service import AutomationService


def test_cron_install_success():
    svc = AutomationService()

    mock_cron = Mock()
    mock_cron.install_cron_job.return_value = (
        Mock(value="success"), "installed")

    with patch('classdock.automation.CronManager', return_value=mock_cron):
        ok, message = svc.cron_install(['sync'], None, 'assignment.conf')

    assert ok is True
    assert 'installed' in message


def test_cron_install_failure():
    svc = AutomationService()

    mock_cron = Mock()
    mock_res = Mock()
    mock_res.value = 'error'
    mock_cron.install_cron_job.return_value = (mock_res, 'failed')

    with patch('classdock.automation.CronManager', return_value=mock_cron):
        ok, message = svc.cron_install(['sync'], None, 'assignment.conf')

    assert ok is False
    assert 'failed' in message


def test_cron_remove_success():
    svc = AutomationService()

    mock_cron = Mock()
    mock_cron.remove_cron_job.return_value = (Mock(value='success'), 'removed')

    with patch('classdock.automation.CronManager', return_value=mock_cron):
        ok, message = svc.cron_remove(['sync'], 'assignment.conf')

    assert ok is True
    assert 'removed' in message


def test_cron_remove_failure():
    svc = AutomationService()

    mock_cron = Mock()
    mock_res = Mock()
    mock_res.value = 'not_found'
    mock_cron.remove_cron_job.return_value = (mock_res, 'not found')

    with patch('classdock.automation.CronManager', return_value=mock_cron):
        ok, message = svc.cron_remove(['sync'], 'assignment.conf')

    assert ok is False
    assert 'not found' in message


def test_cron_logs_success():
    svc = AutomationService()

    mock_cron = Mock()
    mock_cron.show_logs.return_value = (True, 'line1\nline2')

    with patch('classdock.automation.CronManager', return_value=mock_cron):
        ok, output = svc.cron_logs(10)

    assert ok is True
    assert 'line1' in output


def test_cron_status_success():
    svc = AutomationService()

    mock_cron = Mock()
    mock_status = Mock()
    mock_status.has_jobs = False
    mock_cron.get_cron_status.return_value = mock_status

    with patch('classdock.automation.CronManager', return_value=mock_cron):
        ok, status = svc.cron_status('assignment.conf')

    assert ok is True
    assert status.has_jobs is False


def test_cron_sync_dry_run():
    svc = AutomationService()

    mock_manager = Mock()
    mock_manager.log_file = '/tmp/log'

    with patch('classdock.automation.cron_sync.CronSyncManager', return_value=mock_manager):
        ok, info = svc.cron_sync(
            ['sync'], dry_run=True, verbose=False, stop_on_failure=False, show_log=False)

    assert ok is True
    assert info['dry_run'] is True


def test_cron_sync_execute_failure():
    svc = AutomationService()

    class FakeResult:
        overall_result = Mock(name='COMPLETE_FAILURE')

    mock_manager = Mock()
    mock_manager.execute_cron_sync.return_value = FakeResult()

    with patch('classdock.automation.cron_sync.CronSyncManager', return_value=mock_manager):
        ok, res = svc.cron_sync(
            ['sync'], dry_run=False, verbose=False, stop_on_failure=False, show_log=False)

    # The service returns True with the result object; callers inspect it
    assert ok is True
    assert hasattr(res, 'overall_result')
