import pytest
import httplib
from common.api.schema import validate
from tests.api import Base_Api_Test
from unittestzero import Assert

@pytest.fixture(scope="module")
def api_projects(request):
    '''
    Navigate the API and return a link to projects
    '''
    api = request.getfuncargvalue('api')
    api_version = request.config.getvalue('api_version')

    if api_version == 'current_version':
        api_projects = api.get('/api/').json().get('current_version')
    else:
        api_projects = api.get('/api/').json().get('available_versions').get(api_version, None)

    Assert.not_none(api_projects, "Unsupported api-version specified: %s" % api_version)

    return api.get(api_projects).json().get('projects')


class Test_Projects(Base_Api_Test):
    @pytest.mark.nondestructive
    def test_unauthorized(self, api, api_projects):
        r = api.get(api_projects)
        assert r.status_code == httplib.UNAUTHORIZED
        validate(r.json(), '/projects', 'unauthorized')

    @pytest.mark.nondestructive
    def test_authorized(self, api, api_projects):
        # login
        api.login(self.testsetup.credentials['default']['username'],
                  self.testsetup.credentials['default']['password'])

        # Get list of available projects
        data = api.get(api_projects).json()

        # Validate schema
        validate(data, '/projects', 'get')

    @pytest.mark.destructive
    def test_create_manual(self, api, api_projects, api_base, ansible_runner):
        # login
        api.login(self.testsetup.credentials['default']['username'],
                  self.testsetup.credentials['default']['password'])

        # Checkout a repository on the target system
        results = ansible_runner.git(
            repo='https://github.com/ansible/ansible-examples.git',
            dest='/var/lib/awx/projects/ansible-examples.manual')

        # Find desired org
        params = dict(name__icontains='Bender Products')
        data = api.get(api_base + 'organizations', params).json()
        assert data.get('results')[0]['name'] == 'Bender Products'
        org_id = data.get('results')[0].get('id',None)

        # Create a new project
        payload = dict(name="ansible-examples",
                       organization=org_id,
                       base_dir="/var/lib/awx/projects",
                       local_path="ansible-examples.manual",
                       scm_type=None,)
        r = api.post(api_projects, payload)
        data = r.json()

        # support idempotency
        if r.status_code == httplib.BAD_REQUEST:
            validate(data, '/projects', 'duplicate')
            pytest.xfail("project already created")
        else:
            assert r.status_code == httplib.CREATED
            validate(data, '/projects', 'post')
