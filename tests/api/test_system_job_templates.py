import json
import pytest
import common.tower.inventory
import common.utils
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


@pytest.fixture(scope="function", params=['cleanup_jobs', 'cleanup_deleted', 'cleanup_activitystream'])
def system_job_template(request, api_system_job_templates_pg):
    matches = api_system_job_templates_pg.get(job_type=request.param)
    assert matches.count == 1, "No matching system_job_template found with job_type=%s" % request.param
    return matches.results[0]


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_System_Job_Template(Base_Api_Test):
    '''
    Verify actions with system_job_templates

    TODO - launch as non-superuser
    TODO - verify schedules
    '''

    pytestmark = pytest.mark.usefixtures('authtoken')

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

    def test_endpoint_visibility(self, non_superusers, user_password, api_v1_pg, api_system_job_templates_url):
        '''
        Verify endpoint /api/v1/system_job_templates visibility for various
        user accounts
        '''

        assert 'system_job_templates' in api_v1_pg.json, "Superuser " \
            "account unable to see endpoint %s" % \
            api_system_job_templates_url

        for non_superuser in non_superusers:
            with self.current_user(non_superuser.username, user_password):
                assert 'system_job_templates' not in api_v1_pg.json, "Non-superuser " \
                    "account is able to see endpoint %s" % \
                    api_system_job_templates_url

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

    def test_launch(self, system_job_template):
        '''
        Verify successful launch of a system_job_template
        '''

        result = system_job_template.get_related('launch').post()
        assert 'system_job' in result.json, "Unexpected JSON response when " \
            "launching system_job_template\n%s" % json.dumps(result.json, indent=2)

        job_pg = system_job_template.get_related('jobs', id=result.json['system_job']).results[0].wait_until_completed()
        assert job_pg.is_successful, job_pg
