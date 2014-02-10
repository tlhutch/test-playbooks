import sys
import httplib
import pytest
import common.api
import logging
from common.api.pages import *
from unittestzero import Assert

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

@pytest.fixture(scope="session")
def api(testsetup):
    '''
    Convenience fixture that returns api object
    '''
    return testsetup.api

@pytest.fixture(scope="session")
def api_home(request, api):
    '''
    Navigate the API and return a link to the base api for the requested version.
    For example, if --api-version=v1, returns string '/api/v1/'
    '''
    api_version = request.config.getvalue('api_version')
    available_versions = navigate(api, '/api', 'available_versions')

    if api_version in [None, 'current_version']:
        current_version = navigate(api, '/api', 'current_version')
        # Update the stored api.version
        for version, link in available_versions.items():
            if current_version == link:
                api.version = version
                request.config.option.api_version = version
                break
        return current_version
    else:
        assert api_version in available_versions
        return available_versions.get(api_version)

#
# /api/v1/authtoken
#
@pytest.fixture(scope="session")
def api_authtoken_url(api, api_home):
    return navigate(api, api_home, 'authtoken')

@pytest.fixture(scope="session")
def api_authtoken_pg(testsetup, api_authtoken_url):
    return AuthToken_Page(testsetup, \
        base_url=api_authtoken_url)

#
# /api/v1/config
#
@pytest.fixture(scope="session")
def api_config_url(api, api_home):
    return navigate(api, api_home, 'config')

@pytest.fixture(scope="session")
def api_config_pg(testsetup, api_config_url):
    return Config_Page(testsetup, \
        base_url=api_config_url)

#
# /api/v1/me
#
@pytest.fixture(scope="session")
def api_me_url(api, api_home):
    return navigate(api, api_home, 'me')

@pytest.fixture(scope="session")
def api_me_pg(testsetup, api_me_url):
    return Me_Page(testsetup, \
        base_url=api_me_url)

#
# /api/v1/organizations
#
@pytest.fixture(scope="session")
def api_organizations_url(api, api_home):
    return navigate(api, api_home, 'organizations')

@pytest.fixture(scope="session")
def api_organizations_pg(testsetup, api_organizations_url):
    return Organizations_Page(testsetup, \
        base_url=api_organizations_url)

#
# /api/v1/users
#
@pytest.fixture(scope="session")
def api_users_url(api, api_home):
    return navigate(api, api_home, 'users')

@pytest.fixture(scope="session")
def api_users_pg(testsetup, api_users_url):
    return Users_Page(testsetup, \
        base_url=api_users_url)

#
# /api/v1/teams
#
@pytest.fixture(scope="session")
def api_teams_url(api, api_home):
    return navigate(api, api_home, 'teams')

@pytest.fixture(scope="session")
def api_teams_pg(testsetup, api_teams_url):
    return Teams_Page(testsetup, \
        base_url=api_teams_url)

#
# /api/v1/projects
#
@pytest.fixture(scope="session")
def api_projects_url(api, api_home):
    return navigate(api, api_home, 'projects')

@pytest.fixture(scope="session")
def api_projects_pg(testsetup, api_projects_url):
    return Projects_Page(testsetup, \
        base_url=api_projects_url)

#
# /api/v1/teams
#
@pytest.fixture(scope="session")
def api_teams_url(api, api_home):
    return navigate(api, api_home, 'teams')

@pytest.fixture(scope="session")
def api_teams_pg(testsetup, api_teams_url):
    return Teams_Page(testsetup, \
        base_url=api_teams_url)

#
# /api/v1/credentials
#
@pytest.fixture(scope="session")
def api_credentials_url(api, api_home):
    return navigate(api, api_home, 'credentials')

@pytest.fixture(scope="session")
def api_credentials_pg(testsetup, api_credentials_url):
    return Credentials_Page(testsetup, \
        base_url=api_credentials_url)

#
# /api/v1/inventory
#
@pytest.fixture(scope="session")
def api_inventories_url(api, api_home):
    return navigate(api, api_home, 'inventory')

@pytest.fixture(scope="session")
def api_inventories_pg(testsetup, api_inventories_url):
    return Inventories_Page(testsetup, \
        base_url=api_inventories_url)

#
# /api/v1/inventory_sources
#
@pytest.fixture(scope="session")
def api_inventory_sources_url(api, api_home):
    return navigate(api, api_home, 'inventory_sources')

@pytest.fixture(scope="session")
def api_inventory_sources_pg(testsetup, api_inventory_sources_url):
    return Inventory_Sources_Page(testsetup, \
        base_url=api_inventory_sources_url)

#
# /api/v1/groups
#
@pytest.fixture(scope="session")
def api_groups_url(api, api_home):
    return navigate(api, api_home, 'groups')

@pytest.fixture(scope="session")
def api_groups_pg(testsetup, api_groups_url):
    return Groups_Page(testsetup, \
        base_url=api_groups_url)

#
# /api/v1/hosts
#
@pytest.fixture(scope="session")
def api_hosts_url(api, api_home):
    return navigate(api, api_home, 'hosts')

@pytest.fixture(scope="session")
def api_hosts_pg(testsetup, api_hosts_url):
    return Hosts_Page(testsetup, \
        base_url=api_hosts_url)

#
# /api/v1/job_templates
#
@pytest.fixture(scope="session")
def api_job_templates_url(api, api_home):
    return navigate(api, api_home, 'job_templates')

@pytest.fixture(scope="session")
def api_job_templates_pg(testsetup, api_job_templates_url):
    return Job_Templates_Page(testsetup, \
        base_url=api_job_templates_url)

#
# /api/v1/jobs
#
@pytest.fixture(scope="session")
def api_jobs_url(api, api_home):
    return navigate(api, api_home, 'jobs')

@pytest.fixture(scope="session")
def api_jobs_pg(testsetup, api_jobs_url):
    return Jobs_Page(testsetup, \
        base_url=api_jobs_url)

@pytest.fixture(scope="session")
def authtoken(api, testsetup, api_authtoken_url):
    '''
    Logs in to the application with default credentials and returns the
    home page
    '''

    payload = dict(username=testsetup.credentials['default']['username'],
                   password=testsetup.credentials['default']['password'])

    r = api.post(api_authtoken_url, payload)
    assert r.status_code == httplib.OK
    # FIXME - build and return a Authtoken_Page() object
    json = r.json()
    testsetup.api.login(token=json['token'])
    return json

@pytest.fixture(scope="session")
def awx_config(api, api_home):
    url = navigate(api, api_home, 'config')
    r = api.get(url)
    assert r.status_code == httplib.OK
    return r.json()

@pytest.fixture(scope="session")
def region_choices(api_inventory_sources_pg):
    options = api_inventory_sources_pg.options()

    # The format is a list of lists in the format: [['<internal-string>', '<human-readable-string>'], ...]
    return dict(ec2=[r[0] for r in options.json.get('actions',{}).get('GET',{}).get('source_regions',{}).get('ec2_region_choices',[])],
                rax=[r[0] for r in options.json.get('actions',{}).get('GET',{}).get('source_regions',{}).get('rax_region_choices',[])])

