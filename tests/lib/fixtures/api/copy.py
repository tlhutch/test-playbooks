import pytest


@pytest.fixture
def copy_for_test(subrequest):
    def _copy_for_test(resource):
        replica = resource.copy()
        subrequest.addfinalizer(replica.silent_cleanup)
        return replica

    return _copy_for_test
