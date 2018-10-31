import pytest


@pytest.fixture
def active_instances(v2):
    """Returns instance list that excludes corner cases that tests should
    not normally run jobs against
    * no disabled instances
    * no lost instances
    * no isolated instances
    """
    return v2.instances.get(
        rampart_groups__controller__isnull=True,
        enabled=True,
        capacity__gt=0,
        page_size=200
    )


@pytest.fixture
def reset_instance(request):
    def func(instance):
        def teardown():
            instance.patch(capacity_adjustment=1, enabled=True, managed_by_policy=True)
        request.addfinalizer(teardown)
    return func
