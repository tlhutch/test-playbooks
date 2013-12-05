'''integration: mark a test as a complex integration suite

Integration tests tend to be complex, interdependent and take significant
runtime.  Using this marker allows one to distinguish integration tests from
other functional tests. '''

import pytest

def pytest_configure(config):
    config.addinivalue_line("markers", __doc__)

