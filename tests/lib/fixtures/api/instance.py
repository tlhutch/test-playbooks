import pytest


@pytest.fixture
def reset_instance(request):
    def func(instance):
        def teardown():
            instance.patch(capacity_adjustment=1, enabled=True, managed_by_policy=True)
        request.addfinalizer(teardown)
    return func
