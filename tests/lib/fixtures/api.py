import pytest
import common.api
from unittestzero import Assert

@pytest.fixture
def api(request, testsetup):
    '''
    Logs in to the application with default credentials and returns the
    home page
    '''
    user = 'default'

    testsetup.api = common.api.Connection(testsetup.base_url,
        version=request.config.getvalue('api_version'),
        verify=not request.config.getvalue('assume_untrusted'))
    return testsetup.api

@pytest.fixture
def api_base(request):
    '''
    Navigate the API and return a link to the base api for the requested version.
    For example, if --api-version=v1, returns string '/api/v1/'
    '''
    api = request.getfuncargvalue('api')
    api_version = request.config.getvalue('api_version')

    if api_version == 'current_version':
        abi_base = api.get('/api/').json().get('current_version')
    else:
        abi_base = api.get('/api/').json().get('available_versions').get(api_version, None)

    Assert.not_none(abi_base, "Unsupported api-version specified: %s" % api_version)

    return abi_base
