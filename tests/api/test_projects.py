'''
# Create projects in /var/lib/awx/projects and verify
# 1) projects starting with '.' or '_' are excluded from config['project_local_paths']
# 2) project appears under config['project_local_paths']
'''

import re
import pytest
import common.utils
import common.exceptions
from tests.api import Base_Api_Test


@pytest.fixture(scope="function")
def project_with_queued_updates(project_ansible_playbooks_git_nowait):
    # Initiate several project updates
    update_pg = project_ansible_playbooks_git_nowait.get_related('update')
    for i in range(4):
        update_pg.post({})
    return project_ansible_playbooks_git_nowait


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.skip_selenium
class Test_Projects(Base_Api_Test):
    '''
    Verify various activities on /projects endpoint
    '''
    pytestmark = pytest.mark.usefixtures('authtoken')

    def test_delete_related_fields(self, project_ansible_playbooks_git):
        '''Verify that related fields on a deleted resource respond as expected'''

        # delete all the projects
        project_ansible_playbooks_git.delete()

        # assert some related resources are okay
        for related in ('last_job', 'last_update'):
            assert project_ansible_playbooks_git.get_related(related)

        # assert specific related resources are forbidden (403)
        for related in ('schedules', 'activity_stream', 'project_updates', 'teams', ):
            print related
            with pytest.raises(common.exceptions.Forbidden_Exception):
                assert project_ansible_playbooks_git.get_related(related)

        # assert specific related resources are notfound (404)
        for related in ('playbooks', 'update'):
            print related
            with pytest.raises(common.exceptions.NotFound_Exception):
                assert project_ansible_playbooks_git.get_related(related)

    def test_cancel_on_delete(self, project_with_queued_updates, api_unified_jobs_pg, ansible_runner):
        '''Verify that queued project_updates are canceled when a project is deleted.

        This test is kind of ugly since we call out to 'tower-manage shell' to
        determine whether queued jobs persist.  We do this because the project
        is marked as active=False, and therefore not visible through the API.
        '''

        # delete all the projects
        project_with_queued_updates.delete()

        # assert no unified_jobs remain running
        result = ansible_runner.shell(
            "echo \"from awx.main.models import *; "
            "print UnifiedJob.objects.filter(status__in=['running','waiting','pending'], unified_job_template={id}).count(); "
            "print ['id:%s, status:%s' % (uj.id, uj.status) for uj in UnifiedJob.objects.filter(unified_job_template={id})]; \" "
            "| tower-manage shell".format(id=project_with_queued_updates.id)
        )
        assert 'stdout' in result, "Unexpected response from ansible_runner.shell"
        match = re.search(r'>>> (\d)\n', result['stdout'], re.MULTILINE)
        if match is None or not match.group(1).isdigit():
            raise Exception("Unhandled response from tower-manage: %s" % result['stdout'])
        num_pending = match.group(1)
        assert int(num_pending) == 0, \
            "A project (id:%d) was deleted, but a project_update (%s) remains queued/waiting/running" % \
            (project_with_queued_updates.id, num_pending)
