import pytest
import common.tower.inventory
import common.exceptions
import re
from tests.api import Base_Api_Test


@pytest.fixture(scope="function", params=['cleanup_jobs_with_status_completed',
                                          'cleanup_deleted_with_status_completed',
                                          'cleanup_activitystream_with_status_completed',
                                          'custom_inventory_update_with_status_completed',
                                          'project_update_with_status_completed',
                                          'job_with_status_completed',
                                          'ad_hoc_with_status_completed'])
def unified_job_with_status_completed(request):
    '''
    Launches jobs of all types sequentially.

    Returns the job run.
    '''
    return request.getfuncargvalue(request.param)


@pytest.fixture(scope="function")
def multiple_jobs_with_status_completed(cleanup_jobs_with_status_completed,
                                        cleanup_deleted_with_status_completed,
                                        cleanup_activitystream_with_status_completed,
                                        custom_inventory_update_with_status_completed,
                                        project_update_with_status_completed,
                                        job_with_status_completed,
                                        ad_hoc_with_status_completed):
    '''
    Launches all three system jobs, an inventory update, an SCM update, a job template, and an ad hoc command.

    Returns a list of the jobs run.
    '''
    return [cleanup_jobs_with_status_completed,
            cleanup_deleted_with_status_completed,
            cleanup_activitystream_with_status_completed,
            custom_inventory_update_with_status_completed,
            project_update_with_status_completed,
            job_with_status_completed,
            ad_hoc_with_status_completed]


@pytest.fixture(scope="function", params=['organization', 'org_user', 'team',
                                          'ssh_credential', 'project',
                                          'inventory', 'job_template',
                                          'job_with_status_completed'])
def deleted_object(request):
    '''
    Creates and deletes an object.

    Returns the deleted object.
    '''
    obj = request.getfuncargvalue(request.param)
    obj.delete()
    return obj


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_System_Jobs(Base_Api_Test):
    '''
    Verify actions with system_job_templates
    '''

    pytestmark = pytest.mark.usefixtures('authtoken', 'backup_license', 'install_license_unlimited')

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

    def test_cleanup_jobs(self, cleanup_jobs_template, unified_job_with_status_completed, api_jobs_pg, api_system_jobs_pg, api_unified_jobs_pg):
        '''
        Run jobs of different types sequentially and check that cleanup jobs deletes all of them.
        '''
        # launch cleanup job
        payload = dict(extra_vars=dict(days=0))
        cleanup_jobs_pg = cleanup_jobs_template.launch(payload).wait_until_completed()

        # check cleanup job status
        assert cleanup_jobs_pg.is_successful, "Job unsuccessful - %s" % cleanup_jobs_pg

        # assert provided job has been deleted
        if unified_job_with_status_completed.type not in ['inventory_update', 'project_update']:
            with pytest.raises(common.exceptions.NotFound_Exception):
                unified_job_with_status_completed.get()

        # query for unified_jobs matching the provided job id
        results = api_unified_jobs_pg.get(id=unified_job_with_status_completed.id)

        # calculate expected count
        if unified_job_with_status_completed.type in ['inventory_update', 'project_update']:
            expected_count = 1
        else:
            expected_count = 0

        # assert no matching jobs found
        assert results.count == expected_count, "An unexpected number of unified jobs were found (%s != %s)" \
            % (results.count, expected_count)

    def test_cleanup_jobs_on_multiple_jobs(self, cleanup_jobs_template, multiple_jobs_with_status_completed, api_jobs_pg, api_system_jobs_pg,
                                           api_unified_jobs_pg):
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

        # calculate number of remaining jobs
        number_special_cases = len(filter(lambda x: x.type in ('project_update', 'inventory_update'), multiple_jobs_with_status_completed))
        expected_number_remaining_jobs = number_special_cases + system_jobs_pg.count

        # assess remaming unified jobs
        unified_jobs_pg = api_unified_jobs_pg.get()
        assert unified_jobs_pg.count == expected_number_remaining_jobs, "Unexpected number of unified_jobs returned \
            (unified_jobs_pg.count: %s != expected_number_remaining_jobs: %s)" % (unified_jobs_pg.count, expected_number_remaining_jobs)

    @pytest.mark.trello('https://trello.com/c/2wB7DMdt')
    def test_cleanup_deleted(self, deleted_object, cleanup_deleted_template, ansible_runner):
        '''
        Creates and deletes different types of objects, runs cleanup_deleted, and then verifies that
        objects are deleted.
        '''
        # XXX BEGIN temporary aid in debugging
        import json
        contacted = ansible_runner.shell('tower-manage cleanup_deleted --dry-run --days=0')
        result = contacted.values()[0]
        print json.dumps(result, indent=2)
        # XXX END ============================

        # launch job first time
        payload = dict(extra_vars=dict(days=0))
        system_jobs_pg = cleanup_deleted_template.launch(payload)

        # assert success
        system_jobs_pg.wait_until_completed()
        assert system_jobs_pg.is_successful, "Job unsuccessful - %s" % system_jobs_pg

        # assert something deleted
        match = re.search(r'^Removed (\d+) items', system_jobs_pg.result_stdout, re.MULTILINE)
        assert match, "Unexpected output from system job - %s" % system_jobs_pg
        assert int(match.group(1)) > 0, "Unexpected number of deleted objects (%s)" % match.group(1)

        # launch job second time
        payload = dict(extra_vars=dict(days=0))
        system_jobs_pg = cleanup_deleted_template.launch(payload)

        # assert success
        system_jobs_pg.wait_until_completed()
        assert system_jobs_pg.is_successful, "Job unsuccessful - %s" % system_jobs_pg

        # assert that nothing was deleted on the second job run
        match = re.search(r'^Removed (\d+) items', system_jobs_pg.result_stdout, re.MULTILINE)
        assert match, "Unexpected output from system job - %s" % system_jobs_pg
        assert int(match.group(1)) == 0, "Unexpected number of deleted objects (%s)" % match.group(1)

    def test_cleanup_activitystream(self, cleanup_activitystream_template, multiple_jobs_with_status_completed, api_activity_stream_pg):
        '''
        Launch jobs of different types, run cleanup activitystreams, and verify that the activitystream is cleared.
        '''
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
        assert activity_stream_pg.count == 0, "After running cleanup_activitystream, " \
            "activity_stream data is still present (count == %s)" \
            % activity_stream_pg.count
