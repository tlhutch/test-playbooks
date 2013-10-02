import pytest
import common.api
from unittestzero import Assert

@pytest.fixture
def api(testsetup):
    '''Logs in to the application with default credentials and returns the
    home page'''
    user = 'default'

    testsetup.conn = common.api.Connection(testsetup.base_url)
    return testsetup.conn
