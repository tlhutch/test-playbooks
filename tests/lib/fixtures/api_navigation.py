import sys
import httplib
import pytest
import common.api
from unittestzero import Assert
# from plugins.pytest_restqa import TestSetup

def navigate(api, url, field):
    '''
    Return a json attribute from the given url.  While one can simply
    concatenate strings to form a URL, this method is preferred to ensure the
    API is capable of self-referencing.

    Examples:
     * navigate(api, '/api/', 'current_version') returns '/api/v1'
     * navigate(api, '/api/v1/, 'config') returns '/api/v1/config'
    '''
    if not url.endswith('/'):
        url += '/'
    data = api.get(url).json()
    return data.get(field)

def navigate_old(api, version=None, section=None):
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
    return testsetup.api

@pytest.fixture(scope="session")
def api_home(request, api):
    '''
    Navigate the API and return a link to the base api for the requested version.
    For example, if --api-version=v1, returns string '/api/v1/'
    '''
    api_version = request.config.getvalue('api_version')

    return navigate(api, '/api', 'current_version')
    #return navigate(request.getfuncargvalue('api'),
    #                request.config.getvalue('api_version'),)

@pytest.fixture(scope="session")
def api_authtoken(request, api, api_home):
    return navigate(api, api_home, 'authtoken')

@pytest.fixture(scope="session")
def api_config(request, api, api_home):
    return navigate(api_home, 'config')

@pytest.fixture(scope="session")
def api_me(request, api, api_home):
    return navigate(api, api_home, 'me')

@pytest.fixture(scope="session")
def api_organizations(request, api, api_home):
    return navigate(api, api_home, 'organizations')

@pytest.fixture(scope="session")
def api_users(request, api, api_home):
    return navigate(api, api_home, 'users')

@pytest.fixture(scope="session")
def api_projects(request, api, api_home):
    return navigate(api, api_home, 'projects')

@pytest.fixture(scope="session")
def api_teams(request, api, api_home):
    return navigate(api, api_home, 'teams')

@pytest.fixture(scope="session")
def api_credentials(request, api, api_home):
    return navigate(api, api_home, 'credentials')

@pytest.fixture(scope="session")
def api_inventory(request, api, api_home):
    return navigate(api, api_home, 'inventory')

@pytest.fixture(scope="session")
def api_inventory_sources(request, api, api_home):
    return navigate(api, api_home, 'inventory_sources')

@pytest.fixture(scope="session")
def api_groups(request, api, api_home):
    return navigate(api, api_home, 'groups')

@pytest.fixture(scope="session")
def api_hosts(request, api, api_home):
    return navigate(api, api_home, 'hosts')

@pytest.fixture(scope="session")
def api_job_templates(request, api, api_home):
    return navigate(api, api_home, 'job_templates')

@pytest.fixture(scope="session")
def api_jobs(request, api, api_home):
    return navigate(api, api_home, 'jobs')

@pytest.fixture(scope="session")
def authtoken(request, api_authtoken, testsetup):
    '''
    Logs in to the application with default credentials and returns the
    home page
    '''

    api = request.getfuncargvalue('api')
    testsetup = request.getfuncargvalue('testsetup')

    # Did we already acquire a token
    if hasattr(testsetup.api, 'cached_authtoken'):
        #TestSetup.api.authtoken = TestSetup.api.cached_authtoken
        testsetup.api.authtoken = testsetup.api.cached_authtoken
    else:
        payload = dict(username=testsetup.credentials['default']['username'],
                       password=testsetup.credentials['default']['password'])

        r = api.post(api_authtoken, payload)
        assert r.status_code == httplib.OK
        #TestSetup.api.authtoken = r.json()
        testsetup.api.authtoken = r.json()

@pytest.fixture(scope="session")
def awx_config(request, api, api_home):
    url = navigate(api, api_home, 'config')
    r = api.get(url)
    assert r.status_code == httplib.OK
    return r.json()
