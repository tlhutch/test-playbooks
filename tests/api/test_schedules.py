import pytest
import json
import yaml
import re
import common.tower.license
import common.utils
import common.exceptions
import dateutil.rrule
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse
from tests.api import Base_Api_Test

class RRule(dateutil.rrule.rrule):
    '''Sub-class rrule to support __str__'''

    FREQNAMES = ['YEARLY','MONTHLY','WEEKLY','DAILY','HOURLY','MINUTELY','SECONDLY']
    def __str__(self):
        parts = list()
        parts.append('FREQ=' + self.FREQNAMES[self._freq])
        if self._interval:
            parts.append('INTERVAL=' + str(self._interval))
        if self._wkst:
            parts.append('WKST=' + str(self._wkst))
        if self._count:
            parts.append('COUNT=' + str(self._count))

        if False:
            for name, value in [
                    ('BYSETPOS', self._bysetpos),
                    ('BYMONTH', self._bymonth),
                    ('BYMONTHDAY', self._bymonthday),
                    ('BYYEARDAY', self._byyearday),
                    ('BYWEEKNO', self._byweekno),
                    ('BYWEEKDAY', self._byweekday),
                    ('BYHOUR', self._byhour),
                    ('BYMINUTE', self._byminute),
                    ('BYSECOND', self._bysecond),
                    ]:
                if value:
                    parts.append(name + '=' + ','.join(str(v) for v in value))

        return '''DTSTART:%s RRULE:%s ''' % (re.sub(r'[:-]', '', self._dtstart.strftime("%Y%m%dT%H%M%SZ")), ';'.join(parts))

# Create fixture for testing unsupported RRULES
unsupported_rrules = [
    # empty string
    "",
    # missing RRULE
    "DTSTART:%s" % ('asdf asdf', ),
    # missing DTSTART
    "RRULE:%s" % ('asdf asdf', ),
    # empty RRULE
    "DTSTART:%s RRULE:%s" % ('20030925T104941Z', ''),
    # empty DTSTART
    "DTSTART:%s RRULE:%s" % ('', 'FREQ=DAILY;INTERVAL=10;COUNT=5'),
    # multiple RRULES
    "DTSTART:%s RRULE:%s RRULE:%s" % ('20030925T104941Z', 'FREQ=DAILY;INTERVAL=10;COUNT=5', 'FREQ=WEEKLY;INTERVAL=10;COUNT=1'),
    # multiple DSTARTS
    "DTSTART:%s DTSTART:%s RRULE:%s" % ('20030925T104941Z', '20130925T104941Z', 'FREQ=DAILY;INTERVAL=10;COUNT=5',),
    # timezone
    "DTSTART:%s RRULE:%s"% (parse("Thu, 25 Sep 2003 10:49:41 -0300"), 'FREQ=DAILY;INTERVAL=10;COUNT=5'),
]
@pytest.fixture(params=unsupported_rrules)
def unsupported_rrule(request):
    return request.param

@pytest.mark.skip_selenium
@pytest.mark.nondestructive
# @pytest.mark.usefixtures('authtoken', 'backup_license', 'install_license_1000')
@pytest.mark.usefixtures('authtoken')
class Test_Schedules_Project(Base_Api_Test):
    '''
    Test basic schedule CRUD operations: [GET, POST, PUT, PATCH, DELETE]

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

    RBAC
      - admin can view/create/update/delete schedules
      - org_admin can view/create/update/delete schedules
      - user can *only* view schedules
      - user w/ update perm can *only* view/create/update schedules
    '''

    def test_schedule_empty(self, random_project):
        '''assert a fresh project has no schedules'''
        schedules_pg = random_project.get_related('schedules')
        assert schedules_pg.count == 0

    def test_schedule_post_past(self, random_project):
        '''assert creating a schedule with only past occurances'''
        schedules_pg = random_project.get_related('schedules')

        # commemorate first 10 years of pearl_harbor
        pearl_harbor = parse("Dec 7 1942")
        rrule = RRule(dateutil.rrule.YEARLY, dtstart=pearl_harbor, count=10, interval=1)
        payload = dict(name="schedule-%s" % common.utils.random_unicode(),
                       description="Commemorate the attack on pearl harbor (%s)" % common.utils.random_unicode(),
                       rrule=str(rrule))
        schedule_pg = schedules_pg.post(payload)
        assert schedule_pg.next_run is None

    def test_schedule_post_future(self, random_project):
        '''assert creating a schedule with only future occurances'''
        schedules_pg = random_project.get_related('schedules')

        # celebrate Odyssey three date
        odyssey_three = parse("Jan 1 2061")
        rrule = RRule(dateutil.rrule.YEARLY, dtstart=odyssey_three, interval=1)
        payload = dict(name="schedule-%s" % common.utils.random_unicode(),
                       description="2061: Odyssey Three (%s)" % common.utils.random_unicode(),
                       rrule=str(rrule))
        schedule_pg = schedules_pg.post(payload)
        assert schedule_pg.next_run is not None
        # assert schedule_pg.next_run == '2061-01-01T00:00:00Z'
        assert schedule_pg.next_run == rrule[0].isoformat() + 'Z'

    def test_schedule_post_overlap(self, random_project):
        '''assert creating a schedule with past and future occurances'''
        schedules_pg = random_project.get_related('schedules')

        last_week = datetime.now() + relativedelta(weeks=-1)
        next_week = datetime.now() + relativedelta(weeks=+1)
        rrule = RRule(dateutil.rrule.DAILY, dtstart=last_week, until=next_week)
        payload = dict(name="schedule-%s" % common.utils.random_unicode(),
                       description="Daily project update",
                       rrule=str(rrule))
        schedule_pg = schedules_pg.post(payload)
        assert schedule_pg.next_run is not None
        assert schedule_pg.next_run == rrule.after(datetime.now(), inc=False).isoformat() + 'Z'

    def test_schedule_put(self, random_project):
        '''assert successful schedule PUT'''
        schedules_pg = random_project.get_related('schedules')
        assert schedules_pg.count > 0

        schedule_pg = schedules_pg.results[0]
        old_desc = schedule_pg.description
        new_desc = common.utils.random_unicode()
        schedule_pg.description = new_desc
        schedule_pg.put()
        schedule_pg.get()
        assert schedule_pg.description == new_desc

    def test_schedule_patch(self, random_project):
        '''assert successful schedule PATCH'''
        schedules_pg = random_project.get_related('schedules')
        assert schedules_pg.count > 0

        schedule_pg = schedules_pg.results[0]
        old_desc = schedule_pg.description
        new_desc = common.utils.random_unicode()
        schedule_pg.patch(description=new_desc)
        schedule_pg.get()
        assert schedule_pg.description == new_desc

    def test_schedule_delete(self, random_project):
        '''assert successful schedule DELETE'''
        schedules_pg = random_project.get_related('schedules')
        assert schedules_pg.count > 0
        schedules_count = schedules_pg.count
        schedules_pg.results[0].delete()

        # There should be one fewer schedule
        schedules_pg.get()
        assert schedules_pg.count == schedules_count - 1

    def test_schedule_post_invalid(self, random_project, unsupported_rrule):
        '''assert unsupported rrules are rejected'''
        schedules_pg = random_project.get_related('schedules')

        payload = dict(name="schedule-%s" % common.utils.random_unicode(),
                       description="%s" % common.utils.random_unicode(),
                       enabled=True,
                       rrule=str(unsupported_rrule))
        with pytest.raises(common.exceptions.BadRequest_Exception):
            schedules_pg.post(payload)

    # SEE JIRA(AC-1106)
    def test_schedule_cascade_delete(self, api_projects_pg, api_schedules_pg, random_organization):
        '''assert that schedules are deleted when a project is deleted'''
        # create a project
        payload = dict(name="project-%s" % common.utils.random_unicode(),
                       organization=random_organization.id,
                       scm_type='hg',
                       scm_url='https://bitbucket.org/jlaska/ansible-helloworld')
        project = api_projects_pg.post(payload)

        # create schedules
        schedules_pg = project.get_related('schedules')
        assert schedules_pg.count == 0

        schedule_ids = list()
        for repeat in [dateutil.rrule.WEEKLY, dateutil.rrule.MONTHLY, dateutil.rrule.YEARLY]:
            rrule = RRule(repeat, dtstart=datetime.now())
            payload = dict(name="schedule-%s" % common.utils.random_unicode(),
                           description=common.utils.random_unicode(),
                           rrule=str(rrule))
            schedule_pg = schedules_pg.post(payload)
            schedule_ids.append(schedule_pg.id)

        # assert the schedules exist
        schedules_pg = project.get_related('schedules')
        assert schedules_pg.count == 3

        # delete the project
        project.delete()

        # assert the schedules are gone
        remaining_schedules = api_schedules_pg.get(id__in=','.join([str(sid) for sid in schedule_ids]))
        assert remaining_schedules.count == 0
