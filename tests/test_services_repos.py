from unittest.mock import patch, Mock

from classdock.services.repos_service import ReposService





def test_fetch_success(monkeypatch):
    service = ReposService(dry_run=False, verbose=True)

    mock_fetcher = Mock()
    mock_fetcher.fetch_all_repositories.return_value = True

    with patch('classdock.repos.fetch.RepositoryFetcher', return_value=mock_fetcher):
        ok, message = service.fetch(config_file='assignment.conf')

    assert ok is True
    assert 'completed' in message.lower()


def test_fetch_failure(monkeypatch):
    service = ReposService(dry_run=False, verbose=False)

    mock_fetcher = Mock()
    mock_fetcher.fetch_all_repositories.return_value = False

    with patch('classdock.repos.fetch.RepositoryFetcher', return_value=mock_fetcher):
        ok, message = service.fetch(config_file='assignment.conf')

    assert ok is False
    assert 'failed' in message.lower()


def test_push_success():
    service = ReposService(dry_run=False, verbose=False)

    mock_manager = Mock()
    from classdock.assignments.push_manager import PushResult

    mock_manager.execute_push_workflow.return_value = (
        PushResult.SUCCESS, 'pushed')

    with patch('classdock.assignments.push_manager.ClassroomPushManager', return_value=mock_manager):
        ok, message = service.push(config_file='assignment.conf')

    assert ok is True
    assert 'pushed' in message


def test_push_up_to_date():
    service = ReposService(dry_run=False, verbose=False)

    mock_manager = Mock()
    from classdock.assignments.push_manager import PushResult

    mock_manager.execute_push_workflow.return_value = (
        PushResult.UP_TO_DATE, 'up-to-date')

    with patch('classdock.assignments.push_manager.ClassroomPushManager', return_value=mock_manager):
        ok, message = service.push(config_file='assignment.conf')

    assert ok is True
    assert 'up-to-date' in message


def test_cycle_list(monkeypatch):
    service = ReposService(dry_run=False, verbose=False)

    mock_manager = Mock()
    mock_manager.list_repository_collaborators.return_value = [
        {'login': 'student1', 'permission': 'write'},
        {'login': 'student2', 'permission': 'read'}
    ]

    with patch('classdock.assignments.cycle_collaborator.CycleCollaboratorManager', return_value=mock_manager):
        ok, message = service.cycle_collaborator(
            assignment_prefix='hw1', username='student1', organization='org', list_collaborators=True)

    assert ok is True
    assert 'student1' in message


def test_cycle_single(monkeypatch):
    service = ReposService(dry_run=False, verbose=False)

    mock_manager = Mock()
    mock_manager.cycle_single_repository.return_value = (True, 'cycled')

    with patch('classdock.assignments.cycle_collaborator.CycleCollaboratorManager', return_value=mock_manager):
        ok, message = service.cycle_collaborator(
            assignment_prefix='hw1', username='student1', organization='org', list_collaborators=False)

    assert ok is True
    assert 'cycled' in message
