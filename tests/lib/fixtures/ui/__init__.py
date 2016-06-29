import pytest


@pytest.fixture
def default_credentials(testsetup):
    return testsetup.credentials['default']
