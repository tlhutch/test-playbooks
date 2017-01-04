"""performance: mark a test as a complex performance suite

Performance tests can be hard on a system, or specific to a system
configuration. Using this marker allows one to distinguish performance tests
from other tests.
"""


def pytest_configure(config):
    config.addinivalue_line("markers", __doc__)
