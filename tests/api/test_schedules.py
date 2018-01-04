import dateutil.rrule
from datetime import datetime
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta

import pytest
import fauxfactory
from towerkit import exceptions as exc
from towerkit.rrule import RRule
from towerkit.utils import poll_until

from tests.api import Base_Api_Test


# Create fixture for testing unsupported RRULES
@pytest.fixture(scope="function")
def unsupported_rrules(request):
    return [
        # empty string
        "",
        # missing RRULE
        "DTSTART:asdf asdf",
        # missing DTSTART
        "RRULE:asdf asdf",
        # empty RRULE
        "DTSTART:20030925T104941Z RRULE:",
        # empty DTSTART
        "DTSTART: RRULE:FREQ=DAILY;INTERVAL=10;COUNT=5",
        # multiple RRULES
        "DTSTART:20030925T104941Z RRULE:FREQ=DAILY;INTERVAL=10;COUNT=5 RRULE:FREQ=WEEKLY;INTERVAL=10;COUNT=1",
        # multiple DSTARTS
        "DTSTART:20030925T104941Z DTSTART:20130925T104941Z RRULE:FREQ=DAILY;INTERVAL=10;COUNT=5",
        # timezone
        "DTSTART:%s RRULE:FREQ=DAILY;INTERVAL=10;COUNT=5" % parse("Thu, 25 Sep 2003 10:49:41 -0300"),
        # taken from tower unittests
        "DTSTART:20140331T055000 RRULE:FREQ=MINUTELY;INTERVAL=10;COUNT=5",
        "RRULE:FREQ=MINUTELY;INTERVAL=10;COUNT=5",
        "FREQ=MINUTELY;INTERVAL=10;COUNT=5",
        "DTSTART:20240331T075000Z RRULE:FREQ=DAILY;INTERVAL=1;COUNT=10000000",
        "DTSTART;TZID=US-Eastern:19961105T090000 RRULE:FREQ=MINUTELY;INTERVAL=10;COUNT=5",
        "DTSTART:20140331T055000Z RRULE:FREQ=SECONDLY;INTERVAL=1",
        "DTSTART:20140331T055000Z RRULE:FREQ=SECONDLY",
        "DTSTART:20140331T055000Z RRULE:FREQ=YEARLY;BYDAY=20MO;INTERVAL=1",
        "DTSTART:20140331T055000Z RRULE:FREQ=MONTHLY;BYMONTHDAY=10,15;INTERVAL=1",
        "DTSTART:20140331T055000Z RRULE:FREQ=YEARLY;BYMONTH=1,2;INTERVAL=1",
        "DTSTART:20140331T055000Z RRULE:FREQ=YEARLY;BYYEARDAY=120;INTERVAL=1",
        "DTSTART:20140331T055000Z RRULE:FREQ=YEARLY;BYWEEKNO=10;INTERVAL=1",
    ]


@pytest.fixture(scope="function", params=["MINUTELY", "HOURLY", "DAILY", "WEEKLY", "MONTHLY", "YEARLY"])
def rrule_frequency(request):
    utcnow = datetime.utcnow()
    if request.param == "MINUTELY":
        dtstart = utcnow + relativedelta(minutes=-1, seconds=+30)
        freq = dateutil.rrule.MINUTELY
    elif request.param == "HOURLY":
        dtstart = utcnow + relativedelta(hours=-1, seconds=+30)
        freq = dateutil.rrule.HOURLY
    elif request.param == "DAILY":
        dtstart = utcnow + relativedelta(days=-1, seconds=+30)
        freq = dateutil.rrule.DAILY
    elif request.param == "WEEKLY":
        dtstart = utcnow + relativedelta(weeks=-1, seconds=+30)
        freq = dateutil.rrule.WEEKLY
    elif request.param == "MONTHLY":
        dtstart = utcnow + relativedelta(months=-1, seconds=+30)
        freq = dateutil.rrule.MONTHLY
    elif request.param == "YEARLY":
        dtstart = utcnow + relativedelta(years=-1, seconds=+30)
        freq = dateutil.rrule.YEARLY
    else:
        raise Exception("Unsupported frequency:%s" % request.param)
    return RRule(freq, dtstart=dtstart)


@pytest.fixture(scope="function")
def utcnow(request):
    return datetime.utcnow()


@pytest.fixture(scope="function")
def rrule_minutely(request, utcnow):
    return RRule(dateutil.rrule.MINUTELY, dtstart=utcnow + relativedelta(minutes=-1, seconds=+30))


@pytest.fixture()
def disabled_rrule_minutely(request, utcnow):
    return RRule(dateutil.rrule.MINUTELY, dtstart=utcnow + relativedelta(minutes=-1, seconds=+30))


@pytest.fixture(scope="function")
def disabled_project_schedule(request, project, disabled_rrule_minutely):
    schedules_pg = project.get_related('schedules')

    payload = dict(name="disabled-%s" % fauxfactory.gen_utf8(),
                   description="Disabled schedule",
                   enabled=False,
                   rrule=str(disabled_rrule_minutely))
    obj = schedules_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def disabled_inventory_schedule(request, aws_inventory_source, disabled_rrule_minutely):
    schedules_pg = aws_inventory_source.get_related('schedules')

    payload = dict(name="disabled-%s" % fauxfactory.gen_utf8(),
                   description="Disabled schedule",
                   enabled=False,
                   rrule=str(disabled_rrule_minutely))
    obj = schedules_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def multiple_management_job_schedules(request, system_job_template, rrule_minutely, tower_version_cmp):
    """Create two schedules per each system job template."""
    if tower_version_cmp('2.4.0') < 0:
        pytest.xfail("Only supported on tower-2.4.0 and later.")

    # Create schedule payload
    payload = dict(name="schedule-%s" % fauxfactory.gen_utf8(),
                   description="Update every %s" % rrule_minutely._freq,
                   rrule=str(rrule_minutely))

    # Update payload for system job template type
    if system_job_template.job_type == "cleanup_facts":
        payload.update(dict(extra_data=dict(older_than='120d', granularity='1w')))
    else:
        payload.update(dict(extra_data=dict(days='120')))

    # Create first schedule
    schedules_pg = system_job_template.get_related('schedules')
    first_schedule = schedules_pg.post(payload)

    # Update payload and create second schedule
    payload.update(name="schedule-%s" % fauxfactory.gen_utf8())
    second_schedule = schedules_pg.post(payload)

    request.addfinalizer(first_schedule.silent_delete)
    request.addfinalizer(second_schedule.silent_delete)
    return schedules_pg.get()


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.skip_selenium
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class Test_Project_Schedules(Base_Api_Test):
    """Test basic schedule CRUD operations: [GET, POST, PUT, PATCH, DELETE]

    Test schedule rrule support ...
      1. valid should be accepted
      2. invalid should return BadRequest

    Test related->project is correct?

    Create single schedule (rrule), verify ...
      1. project.next_update is expected
      2. project is updated at desired time

    Create multiple schedules (rrules), verify ...
      1. project.next_update is expected
      2. project is updated at desired time
    """
    def test_duplicate_schedules_disallowed_by_project(self, factories):
        project = factories.v2_project()
        schedule = project.add_schedule()

        with pytest.raises(exc.Duplicate) as e:
            project.add_schedule(name=schedule.name)
        assert e.value[1]['name'] == ['Schedule with this Name already exists.']

    def test_empty(self, project):
        """assert a fresh project has no schedules"""
        schedules_pg = project.get_related('schedules')
        assert schedules_pg.count == 0

    def test_post_invalid(self, project, unsupported_rrules):
        """assert unsupported rrules are rejected"""
        schedules_pg = project.get_related('schedules')

        for unsupported_rrule in unsupported_rrules:
            payload = dict(name="schedule-%s" % fauxfactory.gen_utf8(),
                           description="%s" % fauxfactory.gen_utf8(),
                           enabled=True,
                           rrule=str(unsupported_rrule))
            with pytest.raises(exc.BadRequest):
                schedules_pg.post(payload)

    def test_post_duplicate(self, project, disabled_project_schedule):
        """assert duplicate schedules are rejected"""
        schedules_pg = project.get_related('schedules')

        payload = dict(name=disabled_project_schedule.name,
                       rrule=disabled_project_schedule.rrule)
        with pytest.raises(exc.Duplicate):
            schedules_pg.post(payload)

    def test_post_disabled(self, project, disabled_project_schedule):
        """assert can POST disabled schedules"""
        assert not disabled_project_schedule.enabled
        schedules_pg = project.get_related('schedules')

        # Appears in related->schedules
        assert disabled_project_schedule.id in [sched.id for sched in schedules_pg.results]

    def test_post_past(self, project):
        """assert creating a schedule with only past occurances"""
        schedules_pg = project.get_related('schedules')

        # commemorate first 10 years of pearl_harbor
        pearl_harbor = parse("Dec 7 1942")
        rrule = RRule(dateutil.rrule.YEARLY, dtstart=pearl_harbor, count=10, interval=1)
        payload = dict(name="schedule-%s" % fauxfactory.gen_utf8(),
                       description="Commemorate the attack on pearl harbor (%s)" % fauxfactory.gen_utf8(),
                       rrule=str(rrule))
        schedule_pg = schedules_pg.post(payload)
        assert schedule_pg.dtstart == pearl_harbor.strftime("%Y-%m-%dT%H:%M:%SZ")
        assert schedule_pg.next_run is None

    def test_post_future(self, project):
        """assert creating a schedule with only future occurances"""
        schedules_pg = project.get_related('schedules')

        # celebrate Odyssey three date
        odyssey_three = parse("Jan 1 2061")
        rrule = RRule(dateutil.rrule.YEARLY, dtstart=odyssey_three, interval=1)
        payload = dict(name="schedule-%s" % fauxfactory.gen_utf8(),
                       description="2061: Odyssey Three (%s)" % fauxfactory.gen_utf8(),
                       rrule=str(rrule))
        schedule_pg = schedules_pg.post(payload)
        assert schedule_pg.dtstart == odyssey_three.strftime("%Y-%m-%dT%H:%M:%SZ")
        assert schedule_pg.next_run == rrule[0].isoformat() + 'Z'

    def test_post_overlap(self, project):
        """assert creating a schedule with past and future occurances"""
        schedules_pg = project.get_related('schedules')

        last_week = datetime.utcnow() + relativedelta(weeks=-1, minutes=+1)
        next_week = datetime.utcnow() + relativedelta(weeks=+1, minutes=+1)
        rrule = RRule(dateutil.rrule.DAILY, dtstart=last_week, until=next_week)
        payload = dict(name="schedule-%s" % fauxfactory.gen_utf8(),
                       description="Daily update",
                       rrule=str(rrule))
        schedule_pg = schedules_pg.post(payload)
        assert schedule_pg.next_run == rrule.after(datetime.utcnow()).isoformat() + 'Z'

    def test_put(self, project, disabled_project_schedule):
        """assert successful schedule PUT"""
        schedules_pg = project.get_related('schedules')
        assert schedules_pg.count > 0

        schedule_pg = schedules_pg.results[0]
        # change description
        new_desc = fauxfactory.gen_utf8()
        schedule_pg.description = new_desc
        # PUT changes
        schedule_pg.put()
        # GET updates
        schedule_pg.get()
        # Was the description changed?
        assert schedule_pg.description == new_desc

    def test_patch(self, project, disabled_project_schedule):
        """assert successful schedule PATCH"""
        schedules_pg = project.get_related('schedules')
        assert schedules_pg.count > 0

        schedule_pg = schedules_pg.results[0]
        new_desc = fauxfactory.gen_utf8()
        # PATCH changes
        schedule_pg.patch(description=new_desc)
        # GET updates
        schedule_pg.get()
        assert schedule_pg.description == new_desc

    def test_readonly_fields(self, api_schedules_pg, project):
        """assert read-only fields are not writable"""
        schedules_pg = project.get_related('schedules')

        # Create a schedule
        rrule = RRule(dateutil.rrule.HOURLY, dtstart=datetime.utcnow() + relativedelta(seconds=-30), count=2)
        payload = dict(name="schedule-%s" % fauxfactory.gen_utf8(),
                       description="Update (count:2)",
                       rrule=str(rrule))
        schedule_pg = schedules_pg.post(payload)

        # PUT read-only fields
        ro_schedule = api_schedules_pg.get(id=schedule_pg.id).results[0]
        ro_schedule.dtstart = "A new dtstart"
        ro_schedule.dtend = "Some dtend"
        ro_schedule.next_run = "Next run please"
        # PUT changes
        ro_schedule.put()
        # GET updates
        ro_schedule = api_schedules_pg.get(id=schedule_pg.id).results[0]
        assert schedule_pg.dtstart == ro_schedule.dtstart
        assert schedule_pg.dtend == ro_schedule.dtend
        assert schedule_pg.next_run == ro_schedule.next_run

    def test_update_with_credential_prompt(self, project_with_credential_prompt):
        """assert projects with credential prompts launch, but fail"""
        schedules_pg = project_with_credential_prompt.get_related('schedules')

        # Create a schedule
        rrule = RRule(dateutil.rrule.MINUTELY, dtstart=datetime.utcnow() + relativedelta(seconds=+30), count=1)
        payload = dict(name="schedule-%s" % fauxfactory.gen_utf8(),
                       description="Update %s (interval:60, count:1)" % fauxfactory.gen_utf8(),
                       rrule=str(rrule))
        schedule_pg = schedules_pg.post(payload)

        # Is the next_run what we expect?
        assert schedule_pg.next_run == rrule.after(datetime.utcnow()).isoformat() + 'Z'

        # wait 5 minutes for 1 scheduled update to complete
        unified_jobs_pg = schedule_pg.get_related('unified_jobs')

        poll_until(lambda: getattr(unified_jobs_pg.get(), 'count') == 1, interval=15, timeout=5 * 60)

        # Ensure the job status is failed
        job = unified_jobs_pg.get().results[0]
        poll_until(lambda: getattr(job.get(), 'status') == 'failed', interval=15, timeout=5 * 60)

        # Is the next_run still what we expect?
        schedule_pg.get()
        assert schedule_pg.next_run is None

    def test_delete(self, project, rrule_minutely):
        """assert successful schedule DELETE"""
        schedules_pg = project.get_related('schedules')

        # Create a schedule
        payload = dict(name="schedule-%s" % fauxfactory.gen_utf8(),
                       rrule=str(rrule_minutely))
        schedule_pg = schedules_pg.post(payload)

        # Record number of schedules
        schedules_pg.get()
        schedules_count = schedules_pg.count

        # Delete single schedule
        schedule_pg.delete()

        # Check number of schedules
        schedules_pg.get()
        assert schedules_pg.count == schedules_count - 1

        # Delete any remaining schedules
        for schedule in schedules_pg.results:
            schedule.delete()

        # Assert no remaining schedules
        schedules_pg.get()
        assert schedules_pg.count == 0

    def test_update_count1(self, project, rrule_frequency):
        """assert a schedule launches at the proper interval"""
        schedules_pg = project.get_related('schedules')

        # Create schedule
        payload = dict(name="schedule-%s" % fauxfactory.gen_utf8(),
                       description="Update every %s" % rrule_frequency._freq,
                       rrule=str(rrule_frequency))
        print rrule_frequency
        schedule_pg = schedules_pg.post(payload)

        # Is the next_run what we expect?
        assert schedule_pg.next_run == rrule_frequency.after(datetime.utcnow()).isoformat() + 'Z'

        # wait 5 minutes for 1 scheduled update to complete
        jobs = schedule_pg.get_related('unified_jobs')
        poll_until(lambda: getattr(jobs.get(), 'count') == 1, interval=15, timeout=5 * 60)

        # Is the next_run still what we expect?
        schedule_pg.get()
        assert schedule_pg.next_run == rrule_frequency.after(datetime.utcnow()).isoformat() + 'Z'

    def test_update_minutely_count3(self, project):
        """assert a minutely schedule launches properly"""
        schedules_pg = project.get_related('schedules')

        # Create schedule
        now = datetime.utcnow() + relativedelta(seconds=+30)
        now_plus_5m = now + relativedelta(minutes=+5)
        rrule = RRule(dateutil.rrule.MINUTELY, dtstart=now, count=3, until=now_plus_5m)
        payload = dict(name="minutely-%s" % fauxfactory.gen_utf8(),
                       description="Update every minute (count:3)",
                       rrule=str(rrule))
        schedule_pg = schedules_pg.post(payload)

        # Is the next_run what we expect?
        assert schedule_pg.next_run == rrule.after(datetime.utcnow()).isoformat() + 'Z'

        # wait 5 minutes for scheduled updates to complete
        jobs = schedule_pg.get_related('unified_jobs')
        poll_until(lambda: getattr(jobs.get(), 'count') == rrule.count(), interval=15, timeout=5 * 60)

        # ensure the schedule has no remaining runs
        schedule_pg.get()
        assert schedule_pg.next_run is None

    # SEE JIRA(AC-1106)
    def test_project_delete(self, api_projects_pg, api_schedules_pg, organization):
        """assert that schedules are deleted when a project is deleted"""
        # create a project
        payload = dict(name="project-%s" % fauxfactory.gen_utf8(),
                       organization=organization.id,
                       scm_type='hg',
                       scm_url='https://bitbucket.org/jlaska/ansible-helloworld')
        project_pg = api_projects_pg.post(payload)

        # create schedules
        schedules_pg = project_pg.get_related('schedules')
        assert schedules_pg.count == 0

        schedule_ids = list()
        for repeat in [dateutil.rrule.WEEKLY, dateutil.rrule.MONTHLY, dateutil.rrule.YEARLY]:
            rrule = RRule(repeat, dtstart=datetime.utcnow())
            payload = dict(name="schedule-%s" % fauxfactory.gen_utf8(),
                           description=fauxfactory.gen_utf8(),
                           rrule=str(rrule))
            schedule_pg = schedules_pg.post(payload)
            schedule_ids.append(schedule_pg.id)

        # assert the schedules exist
        schedules_pg = project_pg.get_related('schedules')
        assert schedules_pg.count == 3

        # delete the project
        project_pg.wait_until_completed().delete()

        query_ids = ','.join(map(str, schedule_ids))

        def schedules_are_deleted():
            schedules = api_schedules_pg.get(id__in=query_ids)
            return getattr(schedules, 'count') == 0

        poll_until(schedules_are_deleted, interval=5, timeout=120)


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.skip_selenium
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class Test_Inventory_Schedules(Base_Api_Test):
    """Test basic schedule CRUD operations: [GET, POST, PUT, PATCH, DELETE]

    Test schedule rrule support ...
      1. valid should be accepted
      2. invalid should return BadRequest

    Test related->inventory_source is correct?

    Create single schedule (rrule), verify ...
      1. inventory_source.next_update is expected
      2. inventory_source is updated at desired time

    Create multiple schedules (rrules), verify ...
      1. inventory_source.next_update is expected
      2. inventory_source is updated at desired time

    FIXME
      - Verify interaction between schedule and cache_timeout
    """

    def test_empty(self, inventory_source):
        """assert a fresh inventory_source has no schedules"""
        schedules_pg = inventory_source.get_related('schedules')
        assert schedules_pg.count == 0

    def test_post_nocloud(self, inventory_source):
        """assert unable to schedule against an non-cloud inventory"""
        schedules_pg = inventory_source.get_related('schedules')

        rrule = RRule(dateutil.rrule.DAILY, dtstart=datetime.utcnow(), count=10, interval=5)
        payload = dict(name="schedule-%s" % fauxfactory.gen_utf8(),
                       description="%s" % fauxfactory.gen_utf8(),
                       enabled=True,
                       rrule=str(rrule))
        with pytest.raises(exc.BadRequest):
            schedules_pg.post(payload)

    def test_post_invalid(self, aws_inventory_source, unsupported_rrules):
        """assert unsupported rrules are rejected"""
        schedules_pg = aws_inventory_source.get_related('schedules')

        for unsupported_rrule in unsupported_rrules:
            payload = dict(name="schedule-%s" % fauxfactory.gen_utf8(),
                           description="%s" % fauxfactory.gen_utf8(),
                           enabled=True,
                           rrule=str(unsupported_rrule))
            with pytest.raises(exc.BadRequest):
                schedules_pg.post(payload)

    def test_post_duplicate(self, aws_inventory_source, disabled_inventory_schedule):
        """assert duplicate schedules are rejected"""
        schedules_pg = aws_inventory_source.get_related('schedules')

        payload = dict(name=disabled_inventory_schedule.name,
                       rrule=disabled_inventory_schedule.rrule)
        with pytest.raises(exc.Duplicate):
            schedules_pg.post(payload)

    def test_post_disabled(self, aws_inventory_source, disabled_inventory_schedule):
        """assert can POST disabled schedules"""
        assert not disabled_inventory_schedule.enabled
        schedules_pg = aws_inventory_source.get_related('schedules')

        # Appears in related->schedules
        assert disabled_inventory_schedule.id in [sched.id for sched in schedules_pg.results]

    def test_post_cloud(self, cloud_group):
        """Verify successful schedule creation for all supported cloud types inventory_source"""
        schedules_pg = cloud_group.get_related('inventory_source').get_related('schedules')

        # commemorate first 10 years of pearl_harbor
        pearl_harbor = parse("Dec 7 1942")
        rrule = RRule(dateutil.rrule.YEARLY, dtstart=pearl_harbor, count=10, interval=1)
        payload = dict(name="schedule-%s" % fauxfactory.gen_utf8(),
                       description="Commemorate the attack on pearl harbor (%s)" % fauxfactory.gen_utf8(),
                       rrule=str(rrule))
        schedule_pg = schedules_pg.post(payload)
        assert schedule_pg.dtstart == pearl_harbor.strftime("%Y-%m-%dT%H:%M:%SZ")
        assert schedule_pg.next_run is None

    def test_post_past(self, aws_inventory_source):
        """assert creating a schedule with only past occurances"""
        schedules_pg = aws_inventory_source.get_related('schedules')

        # commemorate first 10 years of pearl_harbor
        pearl_harbor = parse("Dec 7 1942")
        rrule = RRule(dateutil.rrule.YEARLY, dtstart=pearl_harbor, count=10, interval=1)
        payload = dict(name="schedule-%s" % fauxfactory.gen_utf8(),
                       description="Commemorate the attack on pearl harbor (%s)" % fauxfactory.gen_utf8(),
                       rrule=str(rrule))
        schedule_pg = schedules_pg.post(payload)
        assert schedule_pg.dtstart == pearl_harbor.strftime("%Y-%m-%dT%H:%M:%SZ")
        assert schedule_pg.next_run is None

    def test_post_future(self, aws_inventory_source):
        """assert creating a schedule with only future occurances"""
        schedules_pg = aws_inventory_source.get_related('schedules')

        # celebrate Odyssey three date
        odyssey_three = parse("Jan 1 2061")
        rrule = RRule(dateutil.rrule.YEARLY, dtstart=odyssey_three, interval=1)
        payload = dict(name="schedule-%s" % fauxfactory.gen_utf8(),
                       description="2061: Odyssey Three (%s)" % fauxfactory.gen_utf8(),
                       rrule=str(rrule))
        schedule_pg = schedules_pg.post(payload)
        assert schedule_pg.dtstart == odyssey_three.strftime("%Y-%m-%dT%H:%M:%SZ")
        assert schedule_pg.next_run == rrule[0].isoformat() + 'Z'

    def test_post_overlap(self, aws_inventory_source):
        """assert creating a schedule with past and future occurances"""
        schedules_pg = aws_inventory_source.get_related('schedules')

        last_week = datetime.utcnow() + relativedelta(weeks=-1, minutes=+1)
        next_week = datetime.utcnow() + relativedelta(weeks=+1, minutes=+1)
        rrule = RRule(dateutil.rrule.DAILY, dtstart=last_week, until=next_week)
        payload = dict(name="schedule-%s" % fauxfactory.gen_utf8(),
                       description="Daily update",
                       rrule=str(rrule))
        schedule_pg = schedules_pg.post(payload)
        assert schedule_pg.next_run == rrule.after(datetime.utcnow()).isoformat() + 'Z'

    def test_put(self, aws_inventory_source, disabled_inventory_schedule):
        """assert successful schedule PUT"""
        schedules_pg = aws_inventory_source.get_related('schedules')
        assert schedules_pg.count > 0

        schedule_pg = schedules_pg.results[0]
        # change description
        new_desc = fauxfactory.gen_utf8()
        schedule_pg.description = new_desc
        # PUT changes
        schedule_pg.put()
        # GET updates
        schedule_pg.get()
        # Was the description changed?
        assert schedule_pg.description == new_desc

    def test_patch(self, aws_inventory_source, disabled_inventory_schedule):
        """assert successful schedule PATCH"""
        schedules_pg = aws_inventory_source.get_related('schedules')
        assert schedules_pg.count > 0

        schedule_pg = schedules_pg.results[0]
        new_desc = fauxfactory.gen_utf8()
        # PATCH changes
        schedule_pg.patch(description=new_desc)
        # GET updates
        schedule_pg.get()
        assert schedule_pg.description == new_desc

    def test_readonly_fields(self, api_schedules_pg, aws_inventory_source):
        """assert read-only fields are not writable"""
        schedules_pg = aws_inventory_source.get_related('schedules')

        # Create a schedule
        rrule = RRule(dateutil.rrule.HOURLY, dtstart=datetime.utcnow() + relativedelta(seconds=-30), count=2)
        payload = dict(name="schedule-%s" % fauxfactory.gen_utf8(),
                       description="Update (count:2)",
                       rrule=str(rrule))
        schedule_pg = schedules_pg.post(payload)

        # PUT read-only fields
        ro_schedule = api_schedules_pg.get(id=schedule_pg.id).results[0]
        ro_schedule.dtstart = "A new dtstart"
        ro_schedule.dtend = "Some dtend"
        ro_schedule.next_run = "Next run please"
        # PUT changes
        ro_schedule.put()
        # GET updates
        ro_schedule = api_schedules_pg.get(id=schedule_pg.id).results[0]
        assert schedule_pg.dtstart == ro_schedule.dtstart
        assert schedule_pg.dtend == ro_schedule.dtend
        assert schedule_pg.next_run == ro_schedule.next_run

    def test_delete(self, aws_inventory_source, rrule_minutely):
        """assert successful schedule DELETE"""
        schedules_pg = aws_inventory_source.get_related('schedules')

        # Create a schedule
        payload = dict(name="schedule-%s" % fauxfactory.gen_utf8(),
                       rrule=str(rrule_minutely))
        schedule_pg = schedules_pg.post(payload)

        # Record number of schedules
        schedules_pg.get()
        schedules_count = schedules_pg.count

        # Delete single schedule
        schedule_pg.delete()

        # Check number of schedules
        schedules_pg.get()
        assert schedules_pg.count == schedules_count - 1

        # Delete any remaining schedules
        for schedule in schedules_pg.results:
            schedule.delete()

        # Assert no remaining schedules
        schedules_pg.get()
        assert schedules_pg.count == 0

    def test_update_count1(self, aws_inventory_source, rrule_frequency):
        """assert a schedule launches at the proper interval"""
        schedules_pg = aws_inventory_source.get_related('schedules')

        # Create schedule
        payload = dict(name="schedule-%s" % fauxfactory.gen_utf8(),
                       description="Update every %s" % rrule_frequency._freq,
                       rrule=str(rrule_frequency))
        print rrule_frequency
        schedule_pg = schedules_pg.post(payload)

        # Is the next_run what we expect?
        assert schedule_pg.next_run == rrule_frequency.after(datetime.utcnow()).isoformat() + 'Z'

        # wait 5 minutes for 1 scheduled update to complete
        unified_jobs_pg = schedule_pg.get_related('unified_jobs')

        poll_until(lambda: getattr(unified_jobs_pg.get(), 'count') == 1, interval=15, timeout=5 * 60)

        # Is the next_run still what we expect?
        schedule_pg.get()
        assert schedule_pg.next_run == rrule_frequency.after(datetime.utcnow()).isoformat() + 'Z'

    def test_update_minutely_count3(self, aws_inventory_source):
        """assert a minutely schedule launches properly"""
        schedules_pg = aws_inventory_source.get_related('schedules')

        # Create schedule
        now = datetime.utcnow() + relativedelta(seconds=+30)
        now_plus_5m = now + relativedelta(minutes=+5)
        rrule = RRule(dateutil.rrule.MINUTELY, dtstart=now, count=3, until=now_plus_5m)
        payload = dict(name="minutely-%s" % fauxfactory.gen_utf8(),
                       description="Update every minute (count:3)",
                       rrule=str(rrule))
        schedule_pg = schedules_pg.post(payload)

        # Is the next_run what we expect?
        assert schedule_pg.next_run == rrule.after(datetime.utcnow()).isoformat() + 'Z'

        # wait 5 minutes for scheduled updates to complete
        jobs = schedule_pg.get_related('unified_jobs')
        poll_until(lambda: getattr(jobs.get(), 'count') == rrule.count(), interval=15, timeout=5 * 60)

        # ensure the schedule has no remaining runs
        schedule_pg.get()
        assert schedule_pg.next_run is None

    # SEE JIRA(AC-1106)
    def test_inventory_group_delete(self, api_schedules_pg, api_groups_pg, inventory, aws_credential):
        """assert that schedules are deleted when a inventory group is deleted"""
        # create group/inventory_source
        payload = dict(name="aws-group-%s" % fauxfactory.gen_alphanumeric(),
                       description="AWS group %s" % fauxfactory.gen_utf8(),
                       inventory=inventory.id,
                       credential=aws_credential.id)
        aws_group = api_groups_pg.post(payload)
        aws_inventory_source = aws_group.get_related('inventory_source')
        aws_inventory_source.patch(source='ec2', credential=aws_credential.id)

        # assert no schedules exist
        schedules_pg = aws_inventory_source.get_related('schedules')
        assert schedules_pg.count == 0

        # create schedules
        schedule_ids = list()
        for repeat in [dateutil.rrule.WEEKLY, dateutil.rrule.MONTHLY, dateutil.rrule.YEARLY]:
            rrule = RRule(repeat, dtstart=datetime.utcnow())
            payload = dict(name="schedule-%s" % fauxfactory.gen_utf8(),
                           description=fauxfactory.gen_utf8(),
                           rrule=str(rrule))
            schedule_pg = schedules_pg.post(payload)
            schedule_ids.append(schedule_pg.id)

        # assert the schedules exist
        schedules_pg = aws_inventory_source.get_related('schedules')
        assert schedules_pg.count == 3

        # delete the group
        aws_group.delete()

        # assert the group schedules are gone
        # Group deletes take much longer than project deletes.  Wait 2 minutes for
        # cascade schedule deletion.

        query_ids = ','.join(map(str, schedule_ids))

        def schedules_are_deleted():
            schedules = api_schedules_pg.get(id__in=query_ids)
            return getattr(schedules, 'count') == 0

        poll_until(schedules_are_deleted, interval=5, timeout=120)


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.skip_selenium
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class Test_Job_Template_Schedules(Base_Api_Test):
    """TODO - Validation of job_template schedules

    This class tests the following:
    * Verify basic schedule CRUD operations: [GET, POST, PUT, PATCH, DELETE]
    * Verify RBAC for above operations
    * Verify related fields map correctly (schedule->job_template and job_templates->schedules)
    * Verify extra_vars handling
    """

    def test_schedule_with_no_credential(self, job_template_no_credential):
        """Verify that a job_template with no credential launches jobs that fail."""
        schedules_pg = job_template_no_credential.get_related('schedules')

        # Create a schedule
        rrule = RRule(dateutil.rrule.MINUTELY, dtstart=datetime.utcnow() + relativedelta(seconds=+30), count=1)
        payload = dict(name="schedule-%s" % fauxfactory.gen_utf8(),
                       description="Update %s (interval:60, count:1)" % fauxfactory.gen_utf8(),
                       rrule=str(rrule))
        schedule_pg = schedules_pg.post(payload)

        # Is the next_run what we expect?
        assert schedule_pg.next_run == rrule.after(datetime.utcnow()).isoformat() + 'Z'

        # wait for a scheduled job to launch
        unified_jobs_pg = schedule_pg.get_related('unified_jobs', launch_type='scheduled')
        poll_until(lambda: getattr(unified_jobs_pg.get(), 'count') == 1, interval=15, timeout=60)

        # Is the next_run still what we expect?
        schedule_pg.get()
        assert schedule_pg.next_run is None

        # Wait for job to complete
        job_pg = unified_jobs_pg.results[0].wait_until_completed(timeout=60)

        # Assert the expected job status
        assert not job_pg.is_successful, "Job unexpectedly completed successfully - %s" % job_pg

        # Assert the expected job_explanation
        expected_explanation = "Scheduled job could not start because it was " \
            "not in the right state or required manual credentials"
        assert job_pg.job_explanation == expected_explanation, \
            "Unexpected job_explanation from scheduled job (%s != %s)" \
            % (job_pg.job_explanation, expected_explanation)


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.skip_selenium
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class Test_System_Job_Template_Schedules(Base_Api_Test):
    """Tests system job schedules."""

    @pytest.mark.parametrize("name, count, system_job_template_id, kwargs", [
        ("Cleanup Job Schedule", 1, 1, dict(days='120')),
        ("Cleanup Activity Schedule", 1, 2, dict(days='355')),
        ("Cleanup Fact Schedule", 1, 3, dict(older_than='120d', granularity='1w')),
    ], ids=['Cleanup Job Schedule', 'Cleanup Activity Schedule', 'Cleanup Fact Schedule'])
    def test_prepopulated_schedules(self, api_schedules_pg, name, count, system_job_template_id, kwargs):
        """Tests default system jobs"""
        schedules_pg = api_schedules_pg.get()

        # find prepopulated system jobs
        default_schedules = filter(lambda x: x.name == name and x.extra_data == kwargs, schedules_pg.results)
        assert len(default_schedules) == count, "Unexpected number of schedules with name '%s' found." % name

        # assess system job
        if default_schedules:
            default_schedule_pg = default_schedules[0]
            assert default_schedule_pg.unified_job_template == system_job_template_id, \
                "Schedule '%s' is of wrong unified_job_template. Expected %s, got %s." \
                % (name, system_job_template_id, default_schedule_pg.unified_job_template)
            assert default_schedule_pg.enabled, "System job schedule not enabled by default."

    def test_multiple_schedules(self, multiple_management_job_schedules):
        """Tests that multiple schedules may be created for each system_job_template."""
        # assert correct number of schedules
        assert multiple_management_job_schedules.count >= 2, \
            "Unexpected number of system_job_template schedules found after creating an additional two schedules."
