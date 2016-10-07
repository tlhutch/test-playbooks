import logging
import json
import pytest


log = logging.getLogger(__name__)


# WARNING awx-task-system has been obsoleted and this will halt pytest.
# TODO: Establish alternative w/ celery?
@pytest.fixture(scope="function")
def pause_awx_task_system(request, ansible_runner):
    '''Stops awx-task-system and restarts it upon teardown. Aids our cancel tests.'''
    def teardown():
        log.debug("calling supervisorctl teardown pause_awx_task_system")
        contacted = ansible_runner.supervisorctl(name='awx-task-system', state='started')
        result = contacted.values()[0]
        if 'failed' in result:
            pytest.exit("awx-task-system failed to restart - %s." % json.dumps(result, indent=2))
    request.addfinalizer(teardown)

    log.debug("calling supervisorctl fixture pause_awx_task_system")
    contacted = ansible_runner.supervisorctl(name='awx-task-system', state='stopped')
    result = contacted.values()[0]
    assert 'failed' not in result, "Stopping awx-task-system failed - %s." % json.dumps(result, indent=2)
