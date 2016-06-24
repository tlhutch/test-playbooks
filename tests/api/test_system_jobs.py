import pytest
import common.tower.inventory
import common.exceptions
from tests.api import Base_Api_Test


def convert_to_camelcase(s):
    return ''.join(x.capitalize() or '_' for x in s.split('_'))


@pytest.fixture(scope="function", params=['cleanup_jobs_with_status_completed',
                                          'cleanup_activitystream_with_status_completed',
                                          'cleanup_facts_with_status_completed',
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
                                        cleanup_activitystream_with_status_completed,
                                        cleanup_facts_with_status_completed,
                                        custom_inventory_update_with_status_completed,
                                        project_update_with_status_completed,
                                        job_with_status_completed,
                                        ad_hoc_with_status_completed):
    '''
    Launches all four system jobs, an inventory update, an SCM update, a job template, and an ad hoc command.

    Returns a list of the jobs run.
    '''
    return [cleanup_jobs_with_status_completed,
            cleanup_activitystream_with_status_completed,
            cleanup_facts_with_status_completed,
            custom_inventory_update_with_status_completed,
            project_update_with_status_completed,
            job_with_status_completed,
            ad_hoc_with_status_completed]


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
@pytest.mark.first
class Test_System_Jobs(Base_Api_Test):
    '''
    Verify actions with system_job_templates
    '''

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    @pytest.mark.fixture_args(days=1000, granularity='1y', older_than='1y')
    def test_get_as_superuser(self, system_job):
        '''
        Verify that a superuser account is able to GET a system_job resource.
        '''
        system_job.get()

    @pytest.mark.fixture_args(days=1000, granularity='1y', older_than='1y')
    def test_get_as_non_superuser(self, non_superusers, user_password, api_system_jobs_pg, system_job):
        '''
        Verify that non-superuser accounts are unable to access a system_job.
        '''
        for non_superuser in non_superusers:
            with self.current_user(non_superuser.username, user_password):
                with pytest.raises(common.exceptions.Forbidden_Exception):
                    api_system_jobs_pg.get(id=system_job.id)

    @pytest.mark.fixture_args(days=1000, granularity='1y', older_than='1y')
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
        Run jobs of different types and check that cleanup_jobs deletes expected jobs.
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

        # launch cleanup job and assert job successful
        payload = dict(extra_vars=dict(days=0))
        cleanup_jobs_pg = cleanup_jobs_template.launch(payload).wait_until_completed()
        assert cleanup_jobs_pg.is_successful, "Job unsuccessful - %s" % cleanup_jobs_pg

        # assert jobs_pg is empty
        assert jobs_pg.get().count == 0, "jobs_pg.count not zero (%s != 0)" % jobs_pg.count

        # assert that the cleanup_jobs job is the only job listed in system jobs
        system_jobs_pg = api_system_jobs_pg.get()
        assert system_jobs_pg.count == 1, "An unexpected number of system_jobs were found after running cleanup_jobs (%s != 1)" % system_jobs_pg.count
        assert system_jobs_pg.results[0].id == cleanup_jobs_pg.id, "After running cleanup_jobs, an unexpected system_job.id was found (%s != %s)" \
            % (system_jobs_pg.results[0].id, cleanup_jobs_pg.id)

        # calculate expected number of remaining unified jobs
        # Note: cleanup_jobs does not clean up project and inventory updates
        unified_jobs_pg = api_unified_jobs_pg.get()
        number_special_cases = len(filter(lambda x: x.type in ('project_update', 'inventory_update'), unified_jobs_pg.results))
        expected_number_remaining_jobs = number_special_cases + system_jobs_pg.count

        # check actual remaining jobs
        assert unified_jobs_pg.count == expected_number_remaining_jobs, "Unexpected number of unified_jobs returned \
            (unified_jobs_pg.count: %s != expected_number_remaining_jobs: %s)" % (unified_jobs_pg.count, expected_number_remaining_jobs)

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

        # wait 25 minutes for cleanup to finish
        system_jobs_pg.wait_until_completed(timeout=60 * 25)

        # assess success
        assert system_jobs_pg.is_successful, "Job unsuccessful - %s" % system_jobs_pg

        # assert that activity_stream is cleared
        activity_stream_pg = api_activity_stream_pg.get()
        assert activity_stream_pg.count == 0, "After running cleanup_activitystream, " \
            "activity_stream data is still present (count == %s)" \
            % activity_stream_pg.count

    def test_cleanup_facts(self, files_scan_job_with_status_completed, cleanup_facts_template):
        '''
        Launch a cleanup_facts job and assert facts have been deleted.
        '''
        # navigate to fact_versions
        host_pg = files_scan_job_with_status_completed.get_related('inventory').get_related('hosts').results[0]
        fact_versions_pg = host_pg.get_related('fact_versions')

        # assert facts in fact_versions
        assert fact_versions_pg.count > 0, "Even though scan job was run, facts do not exist: %s." % fact_versions_pg.count

        # launch job
        payload = dict(extra_vars=dict(granularity='0d', older_than='0d'))
        system_jobs_pg = cleanup_facts_template.launch(payload)

        # wait 2 minutes for cleanup to finish
        system_jobs_pg.wait_until_completed(timeout=60 * 2)

        # assess success
        assert system_jobs_pg.is_successful, "Job unsuccessful - %s" % system_jobs_pg

        # assert no facts in fact_versions
        assert fact_versions_pg.get().count == 0, "Even though cleanup_facts was run, facts still exist: %s." % fact_versions_pg.count

    def test_cancel_system_job(self, system_job_with_status_pending):
        '''
        Test that system_jobs may be cancelled.
        '''
        cancel_pg = system_job_with_status_pending.get_related('cancel')
        assert cancel_pg.can_cancel, "Unable to cancel job (can_cancel:%s)" % cancel_pg.can_cancel

        # cancel job
        cancel_pg.post()

        # wait for job to complete
        system_job_with_status_pending = system_job_with_status_pending.wait_until_completed()

        # assert that the system job was cancelled
        assert system_job_with_status_pending.status == 'canceled', \
            "Unexpected job status after cancelling system job (status:%s)" % \
            system_job_with_status_pending.status
