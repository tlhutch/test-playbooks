'''
# Create projects in /var/lib/awx/projects and verify
# 1) projects starting with '.' or '_' are excluded from config['project_local_paths']
# 2) project appears under config['project_local_paths']
'''

import re
import time
import pytest
import fauxfactory
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

    def test_manual_project(self, project_ansible_playbooks_manual):
        '''
        Verify tower can successfully creates a manual project (scm_type='').
        This includes verifying UTF-8 local-path.
        '''

        # if we make it through the fixure, post worked
        # assert various project attributes are empty ('')
        for attr in ('scm_type', 'scm_url', 'scm_branch'):
            assert hasattr(project_ansible_playbooks_manual, attr), \
                "Unhandled project attribute: %s" % attr
            attr_value = getattr(project_ansible_playbooks_manual, attr)
            assert attr_value == '', \
                "Unexpected project.%s (%s != %s)" % \
                (attr, attr_value, '')

        # assert various project attributes are false
        for attr in ('scm_clean', 'scm_delete_on_update', 'last_job_failed',
                     'has_schedules', 'scm_delete_on_next_update',
                     'scm_update_on_launch', 'last_update_failed',):

            assert hasattr(project_ansible_playbooks_manual, attr), \
                "Unhandled project attribute: %s" % attr
            attr_value = getattr(project_ansible_playbooks_manual, attr)
            assert attr_value is False, \
                "Unexpected project.%s (%s != %s)" % \
                (attr, attr_value, False)

        # assert related.update.can_update == false
        update_pg = project_ansible_playbooks_manual.get_related('update')
        assert not update_pg.json['can_update'], \
            "Manual project incorrectly has can_update:%s" % \
            (update_pg.json['can_update'],)

        # assert related.project_updates.count == 0
        for related_attr in ('project_updates', 'schedules'):
            related_pg = project_ansible_playbooks_manual.get_related(related_attr)
            assert related_pg.count == 0, \
                "A manual project has %d %s, but should have %d %s" % \
                (related_pg.count, related_attr, 0, related_attr)

    # Override the project local_path to workaround and unicode issues
    @pytest.mark.fixture_args(local_path="project_dir_%s" % fauxfactory.gen_alphanumeric())
    def test_change_from_manual_to_scm_project(self, project_ansible_playbooks_manual):
        '''
        Verify tower can successfully convert a manual project, into a scm
        managed project.

        Trello: https://trello.com/c/YFlvkd4Y
        '''

        # change the scm_type to 'git'
        project_pg = project_ansible_playbooks_manual.patch(
            scm_type='git',
            scm_url='https://github.com/jlaska/ansible-playbooks.git',
        )

        # update the project and wait for completion
        latest_update_pg = project_pg.update().wait_until_completed()

        # assert project_update was successful
        assert latest_update_pg.is_successful, "Project update unsuccessful - %s" % latest_update_pg

        # update the project endpoint
        project_pg.get()

        # assert project is marked as successful
        assert project_pg.is_successful, "After a successful project update, " \
            "the project is not marked as successful - id:%s" % project_pg.id

    @pytest.mark.parametrize(
        "attr,value",
        [
            ("scm_type", 'hg'),
            ("scm_url", 'https://bitbucket.org/jlaska/ansible-helloworld'),
        ]
    )
    def test_scm_delete_on_next_update(self, project_ansible_playbooks_git, attr, value):
        '''
        Verify changing the scm_type or the scm_url causes tower to enable
        scm_delete_on_next_update.

        Also assert that after subsequently updating the project, the field
        scm_delete_on_next_update is disabled.
        '''

        # assert scm_delete_on_update == False
        assert not project_ansible_playbooks_git.scm_delete_on_update, \
            "Unable to test scm_delete_on_next_update when scm_delete_on_update==True"

        # assert scm_delete_on_next_update == False
        assert not project_ansible_playbooks_git.scm_delete_on_next_update, \
            "Before changing '%s', the value of 'scm_delete_on_next_update' is unexpected (%s != False)" % \
            (attr, project_ansible_playbooks_git.scm_delete_on_next_update)

        # change+restore the attribute value
        orig_value = getattr(project_ansible_playbooks_git, attr)
        project_ansible_playbooks_git.patch(**{attr: value})
        project_ansible_playbooks_git = project_ansible_playbooks_git.patch(**{attr: orig_value})

        # assert scm_delete_on_next_update == True
        assert project_ansible_playbooks_git.scm_delete_on_next_update, \
            "After changing '%s', the value of 'scm_delete_on_next_update' is unexpected (%s != True)" % \
            (attr, project_ansible_playbooks_git.scm_delete_on_next_update)

        # update the project
        update_pg = project_ansible_playbooks_git.get_related('update')
        result = update_pg.post()
        updates_pg = project_ansible_playbooks_git.get_related('project_updates', id=result.json['project_update'])
        assert updates_pg.count == 1, 'No project update matching id:%s found' % result.json['project_update']

        # wait for update to complete
        project_ansible_playbooks_git = project_ansible_playbooks_git.wait_until_completed()

        # assert project_update was successful
        assert project_ansible_playbooks_git.is_successful, \
            "Project update unsuccesful - %s" % project_ansible_playbooks_git

        # FIXME - verify that the project *was* deleted before updating
        # TASK: [delete project directory before update] ********************************
        # changed: [localhost] => {"changed": true, "path": "/var/lib/awx/projects/_3811__ansible_examplesgit_git", "state": "absent"}

        # assert scm_delete_on_next_update == False
        assert not project_ansible_playbooks_git.scm_delete_on_next_update, \
            "After completing a project_update, the value of 'scm_delete_on_next_update' is unexpected (%s != False)" % \
            (project_ansible_playbooks_git.scm_delete_on_next_update)

    def test_cancel_queued_update(self, project_ansible_git_nowait):
        '''
        Verify the project->current_update->cancel endpoint behaves as expected when canceling a
        queued project_update.  Note, the project_ansible_git repo is used
        because the repo is large enough that the git-clone should take enough
        time to trigger a project_update cancel.
        '''
        update_pg = project_ansible_git_nowait.get_related('current_update')
        cancel_pg = update_pg.get_related('cancel')
        assert cancel_pg.can_cancel, "Unable to cancel project_update (can_cancel:%s)" % cancel_pg.can_cancel

        # cancel job
        cancel_pg.post()

        # wait for project_update to cancel
        update_pg = update_pg.wait_until_status('canceled')

        # assert project_update status is canceled
        assert update_pg.status == 'canceled', \
            "Unexpected project_update status after cancelling project update (status:%s)" % \
            update_pg.status

        # update project resource
        project_ansible_git_nowait = project_ansible_git_nowait.wait_until_completed()

        # assert project status is failed
        assert project_ansible_git_nowait.status == 'canceled', \
            "Unexpected project status after cancelling project update (status:%s)" % \
            project_ansible_git_nowait.status

    def test_cancel_running_update(self, project_ansible_git_nowait):
        '''
        Verify the project->current_update->cancel endpoint behaves as expected
        when canceling a running project_update.  Note, the project_ansible_git
        repo is used because the repo is large enough that the git-clone should
        take enough time to trigger a project_update cancel.
        '''

        update_pg = project_ansible_git_nowait.get_related('current_update')
        cancel_pg = update_pg.get_related('cancel')
        assert cancel_pg.can_cancel, "Unable to cancel project_update (can_cancel:%s)" % cancel_pg.can_cancel

        # wait for project_update to be running
        update_pg = update_pg.wait_until_status('running')

        # cancel job
        cancel_pg.post()

        # wait for project_update to cancel
        # ansible.git includes submodules, which can take time to update
        update_pg = update_pg.wait_until_status('canceled', timeout=60 * 4)

        # assert project_update status is canceled
        assert update_pg.status == 'canceled', \
            "Unexpected project_update status after cancelling project update (status:%s)" % \
            update_pg.status

        # update project resource
        project_ansible_git_nowait = project_ansible_git_nowait.wait_until_completed()

        # assert project status is failed
        assert project_ansible_git_nowait.status == 'canceled', \
            "Unexpected project status after cancelling project update (status:%s)" % \
            project_ansible_git_nowait.status

    def test_delete_related_fields(self, install_enterprise_license_unlimited, project_ansible_playbooks_git):
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

    def test_cancel_on_delete(self, project_with_queued_updates, ansible_runner):
        '''Verify that queued project_updates are canceled when a project is deleted.

        This test is kind of ugly since we call out to 'tower-manage shell' to
        determine whether queued jobs persist.  We do this because the project
        is marked as active=False, and therefore not visible through the API.
        '''

        # delete the projects
        project_with_queued_updates.delete()

        # assert no unified_jobs remain running.  Poll using tower-manage until
        # queued project_updates have been removed.
        attempts = 0
        num_pending = -1
        while attempts < 5 and num_pending != 0:
            attempts += 1
            time.sleep(5)
            contacted = ansible_runner.shell(
                "echo \"from awx.main.models import *; "
                "print UnifiedJob.objects.filter(status__in=['running','waiting','pending'], unified_job_template={id}).count(); "
                "print ['id:%s, status:%s' % (uj.id, uj.status) for uj in UnifiedJob.objects.filter(unified_job_template={id})]; \" "
                "| tower-manage shell".format(id=project_with_queued_updates.id)
            )
            for result in contacted.values():
                assert 'stdout' in result, "Unexpected response from ansible_runner.shell"
                match = re.search(r'>>> (\d)\n', result['stdout'], re.MULTILINE)
                if match is None or not match.group(1).isdigit():
                    raise Exception("Unhandled response from tower-manage: %s" % result['stdout'])
                num_pending = match.group(1)

        assert int(num_pending) == 0, \
            "A project (id:%d) was deleted, but %s project_update(s) remains queued/waiting/running (attempts:%s)" % \
            (project_with_queued_updates.id, num_pending, attempts)
