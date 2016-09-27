import pytest
import fauxfactory


@pytest.fixture(scope="function", params=["project", "custom_inventory_source", "job_template", "cleanup_jobs_template"])
def schedulable_resource_as_superuser(request):
    return request.getfuncargvalue(request.param)


@pytest.fixture(scope="function", params=["project", "custom_inventory_source", "job_template"])
def schedulable_resource_as_org_admin(request):
    return request.getfuncargvalue(request.param)


@pytest.fixture(scope="function", params=["project", "custom_inventory_source", "job_template", "cleanup_jobs_template"])
def resource_with_schedule(request):
    """Includes all Tower resources that support schedules."""
    payload = dict(name="Schedule - %s" % fauxfactory.gen_utf8(),
                   rrule="DTSTART:20160926T040000Z RRULE:FREQ=HOURLY;INTERVAL=1")
    resource = request.getfuncargvalue(request.param)
    schedules_pg = resource.get_related('schedules')
    schedule_pg = schedules_pg.post(payload)
    request.addfinalizer(schedule_pg.silent_delete)
    return resource


@pytest.fixture(scope="function", params=["project", "custom_inventory_source", "job_template"])
def organization_resource_with_schedule(request):
    """Includes Tower resources that support schedules that fall under an organization."""
    payload = dict(name="Schedule - %s" % fauxfactory.gen_utf8(),
                   rrule="DTSTART:20160926T040000Z RRULE:FREQ=HOURLY;INTERVAL=1")
    resource = request.getfuncargvalue(request.param)
    schedules_pg = resource.get_related('schedules')
    schedule_pg = schedules_pg.post(payload)
    request.addfinalizer(schedule_pg.silent_delete)
    return resource
