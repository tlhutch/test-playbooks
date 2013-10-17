import httplib
import pytest
import common.api
from unittestzero import Assert
from plugins.restqa import TestSetup

def navigate(api, version=None, section=None):
    '''
    Return the requested REST API resource string.  If no section=None, a link
    to the api home for the specified version is returned.  If a link to the
    provided section is returned.

    Examples:
     * navigate(api) returns '/api/v1'
     * navigate(api, version='v3') returns '/api/v3'
     * navigate(api, section='teams') returns '/api/v1/teams'
     * navigate(api, version='v2', section='groups') returns '/api/v2/groups'
    '''

    if version in [None, 'current_version']:
        api_link = api.get('/api/').json().get('current_version')
    else:
        api_link = api.get('/api/').json().get('available_versions').get(version, None)

    Assert.not_none(api_link, \
        "Unsupported api-version specified: %s" % version)

    if section:
        data = api.get(api_link).json()
        Assert.true(section in data, \
            "No api section '%s' found" % section)

        api_link = data[section]

    return api_link

@pytest.fixture(scope="session")
def api(request, testsetup):
    '''
    Logs in to the application with default credentials and returns the
    home page
    '''
    if not hasattr(testsetup, 'api'):
        TestSetup.api = common.api.Connection(testsetup.base_url,
            version=request.config.getvalue('api_version'),
            verify=not request.config.getvalue('assume_untrusted'))
        testsetup.api = common.api.Connection(testsetup.base_url,
            version=request.config.getvalue('api_version'),
            verify=not request.config.getvalue('assume_untrusted'))
    return testsetup.api

@pytest.fixture
def api_home(request):
    '''
    Navigate the API and return a link to the base api for the requested version.
    For example, if --api-version=v1, returns string '/api/v1/'
    '''
    api = request.getfuncargvalue('api')
    api_version = request.config.getvalue('api_version')

    return navigate(request.getfuncargvalue('api'),
                    request.config.getvalue('api_version'),)

@pytest.fixture(scope="session")
def api_organizations(request):
    return navigate(request.getfuncargvalue('api'),
                    request.config.getvalue('api_version'),
                    'organizations',)

@pytest.fixture(scope="session")
def api_authtoken(request):
    return navigate(request.getfuncargvalue('api'),
                    request.config.getvalue('api_version'),
                    'authtoken',)

@pytest.fixture(scope="session")
def api_config(request):
    return navigate(request.getfuncargvalue('api'),
                    request.config.getvalue('api_version'),
                    'config',)

@pytest.fixture(scope="session")
def api_me(request):
    return navigate(request.getfuncargvalue('api'),
                    request.config.getvalue('api_version'),
                    'me',)

@pytest.fixture(scope="session")
def api_organizations(request):
    return navigate(request.getfuncargvalue('api'),
                    request.config.getvalue('api_version'),
                    'organizations',)

@pytest.fixture(scope="session")
def api_users(request):
    return navigate(request.getfuncargvalue('api'),
                    request.config.getvalue('api_version'),
                    'users',)

@pytest.fixture(scope="session")
def api_projects(request):
    return navigate(request.getfuncargvalue('api'),
                    request.config.getvalue('api_version'),
                    'projects',)

@pytest.fixture(scope="session")
def api_teams(request):
    return navigate(request.getfuncargvalue('api'),
                    request.config.getvalue('api_version'),
                    'teams',)

@pytest.fixture(scope="session")
def api_credentials(request):
    return navigate(request.getfuncargvalue('api'),
                    request.config.getvalue('api_version'),
                    'credentials',)

@pytest.fixture(scope="session")
def api_inventory(request):
    return navigate(request.getfuncargvalue('api'),
                    request.config.getvalue('api_version'),
                    'inventory',)

@pytest.fixture(scope="session")
def api_inventory_sources(request):
    return navigate(request.getfuncargvalue('api'),
                    request.config.getvalue('api_version'),
                    'inventory_sources',)

@pytest.fixture(scope="session")
def api_groups(request):
    return navigate(request.getfuncargvalue('api'),
                    request.config.getvalue('api_version'),
                    'groups',)

@pytest.fixture(scope="session")
def api_hosts(request):
    return navigate(request.getfuncargvalue('api'),
                    request.config.getvalue('api_version'),
                    'hosts',)

@pytest.fixture(scope="session")
def api_job_templates(request):
    return navigate(request.getfuncargvalue('api'),
                    request.config.getvalue('api_version'),
                    'job_templates',)

@pytest.fixture(scope="session")
def api_jobs(request):
    return navigate(request.getfuncargvalue('api'),
                    request.config.getvalue('api_version'),
                    'jobs',)

@pytest.fixture(scope="function")
def authtoken(request, testsetup):
    '''
    Logs in to the application with default credentials and returns the
    home page
    '''

    api = request.getfuncargvalue('api')

    # Did we already acquire a token
    if hasattr(TestSetup.api, 'cached_authtoken'):
        TestSetup.api.authtoken = TestSetup.api.cached_authtoken
        testsetup.api.authtoken = testsetup.api.cached_authtoken
    else:
        base_url = navigate(api, request.config.getvalue('api_version'), 'authtoken',)
        payload = dict(username=testsetup.credentials['default']['username'],
                       password=testsetup.credentials['default']['password'])

        r = api.post(base_url, payload)
        assert r.status_code == httplib.OK
        TestSetup.api.authtoken = r.json()
        testsetup.api.authtoken = r.json()

@pytest.fixture(scope="session")
def awx_config(request, api):
    url = navigate(api, request.config.getvalue('api_version'), 'config',)
    r = api.get(url)
    assert r.status_code == httplib.OK
    return r.json()
