import pytest


@pytest.fixture
def reset_instance(request):
    def func(instance):
        def teardown():
            instance.enabled = True
            instance.patch(capacity_adjustment=1)
        request.addfinalizer(teardown)
    return func
