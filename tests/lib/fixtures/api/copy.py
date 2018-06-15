import pytest


@pytest.fixture
def copy_for_test(request):
    def _copy_for_test(resource):
        replica = resource.copy()
        request.addfinalizer(replica.silent_cleanup)
        return replica

    return _copy_for_test
