import pytest


@pytest.fixture
def copy_with_teardown(subrequest):
    def _copy_with_teardown(resource):
        replica = resource.copy()
        subrequest.addfinalizer(replica.silent_cleanup)
        return replica

    return _copy_with_teardown
