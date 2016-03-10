import json
import pytest
import common.tower.inventory
from tests.api import Base_Api_Test


@pytest.fixture(scope="function")
def cleanup_jobs_template(request, api_system_job_templates_pg):
    '''
    Return a System_Job_Template object representing the 'cleanup_jobs' system
    job template.
    '''
    matches = api_system_job_templates_pg.get(job_type='cleanup_jobs')
    assert matches.count == 1, "Unexpected number of results (%s) when querying " \
        "for system_job_template job_type:cleanup_jobs" % matches.count
    return matches.results[0]


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_System_Job_Template(Base_Api_Test):
    '''
    Verify actions with system_job_templates

    TODO - verify schedules
    '''

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/1188')
    def test_get_as_superuser(self, api_system_job_templates_pg):
        '''
        Verify that a superuser account is able to GET the system_job_template
        resource.
        '''
        results = api_system_job_templates_pg.get()
        # NOTE: validation on the system_job_template name+description happens
        # during JSON schema validation
        assert results.count > 0, "Unexpected system_job_template count (%s)" % \
            results.count

    def test_get_as_non_superuser(self, api_system_job_templates_pg, non_superusers, user_password):
        '''
        Verify that non-superuser accounts are unable to access the
        system_job_template endpoint
        '''
        for non_superuser in non_superusers:
            with self.current_user(non_superuser.username, user_password):
                with pytest.raises(common.exceptions.NotFound_Exception):
                    api_system_job_templates_pg.get()

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/1188')
    def test_method_not_allowed(self, api_system_job_templates_pg):
        '''
        Verify that PUT, POST and PATCH are unsupported request methods
        '''
        with pytest.raises(common.exceptions.Method_Not_Allowed_Exception):
            api_system_job_templates_pg.post()

        system_job_template = api_system_job_templates_pg.get(id=1)
        with pytest.raises(common.exceptions.Method_Not_Allowed_Exception):
            system_job_template.put()

        with pytest.raises(common.exceptions.Method_Not_Allowed_Exception):
            system_job_template.patch()

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/1188')
    def test_launch_as_superuser(self, system_job_template):
        '''
        Verify successful launch of a system_job_template
        '''

        result = system_job_template.get_related('launch').post()
        assert 'system_job' in result.json, "Unexpected JSON response when " \
            "launching system_job_template\n%s" % json.dumps(result.json, indent=2)

        job_pg = system_job_template.get_related('jobs', id=result.json['system_job']).results[0].wait_until_completed()

        # cleanup_facts jobs will fail when no extra_vars are provided
        if job_pg.job_type == 'cleanup_facts':
            assert not job_pg.is_successful, "System job unexpectedly succeeded - %s" % job_pg
            assert job_pg.result_stdout == "CommandError: Both --granularity and --older_than are required.\r\n"
        # all other system_jobs are expected to succeed
        else:
            assert job_pg.is_successful, "System job unexpectedly failed - %s" % job_pg

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/1188')
    def test_launch_as_non_superuser(self, system_job_template, non_superusers, user_password):
        '''
        Verify launch fails when attempted by a non-superuser
        '''

        launch_pg = system_job_template.get_related('launch')
        for non_superuser in non_superusers:
            with self.current_user(non_superuser.username, user_password):
                with pytest.raises(common.exceptions.Forbidden_Exception):
                    launch_pg.post()

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/1188')
    def test_launch_with_extra_vars(self, system_job_template):
        '''
        Verify successful launch of a system_job_template with extra_vars.
        '''

        launch_pg = system_job_template.get_related('launch')
        payload = dict(extra_vars=dict(days='365', older_than='1y', granularity='1y'))
        result = launch_pg.post(payload)

        # assert json response
        assert 'system_job' in result.json, "Unexpected JSON response when " \
            "launching system_job_template\n%s" % json.dumps(result.json, indent=2)

        job_pg = system_job_template.get_related('jobs', id=result.json['system_job']).results[0].wait_until_completed()

        # assert system_job ran successfully
        assert job_pg.is_successful, "System job unsuccessful - %s" % job_pg

        # assert extra_vars properly passed to system_job
        try:
            extra_vars = json.loads(job_pg.extra_vars)
        except ValueError:
            extra_vars = {}
        assert extra_vars == payload['extra_vars'], \
            "The system_job extra_vars do not match the values provided at launch (%s != %s)" % \
            (extra_vars, payload['extra_vars'])
