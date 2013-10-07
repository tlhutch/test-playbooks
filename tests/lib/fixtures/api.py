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
