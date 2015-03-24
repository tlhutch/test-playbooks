import json
import pytest
import common.tower.inventory
import common.utils
from tests.api import Base_Api_Test


@pytest.fixture(scope="function")
def multiple_jobs_with_status_completed(cleanup_jobs_with_status_completed, cleanup_deleted_with_status_completed, cleanup_activitystream_with_status_completed, custom_inventory_update_with_status_completed, project_ansible_playbooks_git, job_with_status_completed):
    '''
    Launches all three system jobs, an inventory update, an SCM update, and a job template.

    Returns a list of the jobs run.
    '''
    return [cleanup_jobs_with_status_completed, cleanup_deleted_with_status_completed, cleanup_activitystream_with_status_completed, custom_inventory_update_with_status_completed, project_ansible_playbooks_git, job_with_status_completed]


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_System_Jobs(Base_Api_Test):
    '''
    Verify actions with system_job_templates
    '''

    pytestmark = pytest.mark.usefixtures('authtoken')

    @pytest.mark.fixture_args(days=1000)
    def test_get_as_superuser(self, system_job):
        '''
        Verify that a superuser account is able to GET a system_job resource.
        '''
        system_job.get()

    @pytest.mark.fixture_args(days=1000)
    def test_get_as_non_superuser(self, non_superusers, user_password, api_system_jobs_pg, system_job):
        '''
        Verify that non-superuser accounts are unable to access a system_job.
        '''
        for non_superuser in non_superusers:
            with self.current_user(non_superuser.username, user_password):
                with pytest.raises(common.exceptions.NotFound_Exception):
                    api_system_jobs_pg.get(id=system_job.id)

    @pytest.mark.fixture_args(days=1000)
    def test_method_not_allowed(self, system_job):
        '''
        Verify that PUT, POST and PATCH are unsupported request methods
        '''
        with pytest.raises(common.exceptions.Method_Not_Allowed_Exception):
            system_job.post()

        with pytest.raises(common.exceptions.Method_Not_Allowed_Exception):
            system_job.put()

        with pytest.raises(common.exceptions.Method_Not_Allowed_Exception):
            system_job.patch()

    def test_cleanup_jobs_on_multiple_jobs(self, cleanup_jobs_template, multiple_jobs_with_status_completed, api_jobs_pg, api_system_jobs_pg, api_unified_jobs_pg):
        '''
        Run jobs of different types and check that cleanup jobs deletes all of them.
        '''
        # pretest
        job_types = [uj.type for uj in multiple_jobs_with_status_completed]

        # assert expected jobs are present
        jobs_pg = api_jobs_pg.get()
        assert jobs_pg.count >= job_types.count('job'), "An unexpected number of jobs were found (%s < %s)" \
            % (jobs_pg.count, job_types.count('job'))

        system_jobs_pg = api_system_jobs_pg.get()
        assert system_jobs_pg.count >= job_types.count('system_job'), "An unexpected number of system jobs were found (%s < %s)" \
            % (system_jobs_pg.count, job_types.count('system_job'))

        unified_jobs_pg = api_unified_jobs_pg.get()
        assert unified_jobs_pg.count >= len(job_types), "An unexpected number of unified jobs were found were found (%s < %s)" \
            % (unified_jobs_pg.count, len(job_types))

        # launch cleanup job
        payload = dict(extra_vars=dict(days=0))
        cleanup_jobs_pg = cleanup_jobs_template.launch(payload).wait_until_completed()

        # check cleanup job status
        assert cleanup_jobs_pg.is_successful, "Job unsuccessful - %s" % cleanup_jobs_pg

        # assert jobs_pg is empty
        jobs_pg = api_jobs_pg.get()
        assert jobs_pg.count == 0, "jobs_pg.count not zero (%s != 0)" % jobs_pg.count

        # assert that the cleanup_jobs job is the only job listed in system jobs
        system_jobs_pg = api_system_jobs_pg.get()
        assert system_jobs_pg.count == 1, "An unexpected number of system_jobs were found after running cleanup_jobs (%s != 1)" % system_jobs_pg.count
        assert system_jobs_pg.results[0].id == cleanup_jobs_pg.id, "After running cleanup_jobs, an unexpected system_job.id was found (%s != %s)" \
            % (system_jobs_pg.results[0].id, cleanup_jobs_pg.id)

        # assert that the cleanup_jobs job is the only job listed in unified jobs
        # Trello: https://trello.com/c/Kg5IBdUx
        unified_jobs_pg = api_unified_jobs_pg.get()
        assert unified_jobs_pg.count == 1, "An unexpected number of unified_jobs were found after running cleanup_jobs (%s != 1)" % unified_jobs_pg.count
        assert unified_jobs_pg.results[0].id == cleanup_jobs_pg.id, "After running cleanup_jobs, an unexpected system_job.id was found (%s != %s)" \
            % (unified_jobs_pg.results[0].id, cleanup_jobs_pg.id)

    @pytest.mark.skipif(True, reason="not yet implemented")
    def test_cleanup_deleted(self):
        '''
        Verifies cleanup_deleted functionality.
        '''
        # Create a fixture that populates tower with information and then deletes everything.
        # Run cleanup job and verify that objects are deleted from the API? They already are deleted - what does this system job actually do?
        pass

    def test_cleanup_activitystream(self, cleanup_activitystream_template, multiple_jobs_with_status_completed, api_activity_stream_pg):
        '''
        Launch jobs of different types, run cleanup activitystreams, and verify that the activitystream is cleared.
        '''
        # Create a fixture that runs a variety of tasks in Tower such as, create objects, delete objects, run jobs, edit items, etc.
        # Do this for several different organizations. Parametrization will be good here.
        # Run cleanup_activitystream for one user and verify that actity stream is cleaned for that user and others in the same organization.
        # Check for all users

        # pretest
        activity_stream_pg = api_activity_stream_pg.get()
        assert activity_stream_pg.count != 0, "Activity stream empty (%s == 0)." % activity_stream_pg.count

        # launch job
        payload = dict(extra_vars=dict(days=0))
        system_jobs_pg = cleanup_activitystream_template.launch(payload)

        # assess success
        system_jobs_pg.wait_until_completed()
        assert system_jobs_pg.is_successful, "Job unsuccessful - %s" % system_jobs_pg

        # assert that activity_stream is cleared
        activity_stream_pg = api_activity_stream_pg.get()
        assert activity_stream_pg.count == 0, "After running cleanup_activitystream, activity_stream data is still present (count == %s)" % activity_stream_pg.count
