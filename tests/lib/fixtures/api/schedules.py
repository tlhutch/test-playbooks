import pytest


@pytest.fixture(scope="function", params=["project", "custom_inventory_source", "job_template", "cleanup_jobs_template"])
def schedulable_resource_as_superuser(request):
    return request.getfixturevalue(request.param)


@pytest.fixture(scope="function", params=["project", "custom_inventory_source", "job_template"])
def schedulable_resource_as_org_admin(request):
    return request.getfixturevalue(request.param)


@pytest.fixture(scope="function", params=["project", "custom_inventory_source", "job_template", "cleanup_jobs_template"])
def resource_with_schedule(request):
    """Returns all schedulable Tower resources with a built-in schedule."""
    resource = request.getfixturevalue(request.param)
    schedule = resource.add_schedule()
    if request.param == "cleanup_jobs_template":
        request.addfinalizer(schedule.silent_delete)
    return resource


@pytest.fixture(scope="function", params=["project", "custom_inventory_source", "job_template"])
def organization_resource_with_schedule(request):
    """Returns all organization-scoped schedulable Tower resources with a built-in schedule."""
    resource = request.getfixturevalue(request.param)
    resource.add_schedule()
    return resource
