from copy import deepcopy
from dateutil import rrule
from datetime import datetime
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
import traceback
import io

import pytest
from awxkit import exceptions as exc, config
from tests.lib.rrule import RRule
from awxkit.utils import poll_until, random_title
import pytz

from tests.api.schedules import SchedulesTest


# Skip for Openshift because of Github Issue: https://github.com/ansible/tower-qa/issues/2591
@pytest.mark.usefixtures('authtoken', 'skip_if_openshift')
class TestSchedules(SchedulesTest):

    def test_new_resources_are_without_schedules(self, unified_job_template):
        assert unified_job_template.related.schedules.get().count == 0

    def test_duplicate_schedules_disallowed(self, unified_job_template):
        schedule = unified_job_template.add_schedule()

        with pytest.raises(exc.Duplicate) as e:
            unified_job_template.add_schedule(name=schedule.name)
        assert e.match('Schedule with this Unified job template and Name already exists.')

    def test_non_regression_valid_rrules(self, unified_job_template):
        valid_rrules = [
            'DTSTART:20301017T080000Z+2:00 RRULE:FREQ=DAILY;INTERVAL=1;COUNT=1',  # Adding Z+02:00 offset to DTSTART
        ]

        for _rrule in valid_rrules:
            unified_job_template.add_schedule(rrule=_rrule)

    def test_invalid_rrules_are_rejected(self, unified_job_template):
        invalid_rrules = [
            ('', 'This field may not be blank.'),
            ('DTSTART:asdf asdf', 'Valid DTSTART required in rrule. Value should start with: DTSTART:YYYYMMDDTHHMMSSZ'),
            ('RRULE:asdf asdf', 'Valid DTSTART required in rrule. Value should start with: DTSTART:YYYYMMDDTHHMMSSZ'),
            ('DTSTART:20030925T104941Z RRULE:', 'INTERVAL required in rrule.'),
            ('DTSTART: RRULE:FREQ=DAILY;INTERVAL=10;COUNT=5',
             'Valid DTSTART required in rrule. Value should start with: DTSTART:YYYYMMDDTHHMMSSZ'),
            ('DTSTART:20030925T104941Z RRULE:FREQ=DAILY;INTERVAL=10;COUNT=500;UNTIL=29040925T104941Z',
             'RRULE may not contain both COUNT and UNTIL'),
            ('DTSTART:20030925T104941Z RRULE:FREQ=DAILY;INTERVAL=10;COUNT=5 RRULE:FREQ=WEEKLY;INTERVAL=10;COUNT=1',
             'Multiple RRULE is not supported.'),
            ('DTSTART:20030925T104941Z DTSTART:20130925T104941Z RRULE:FREQ=DAILY;INTERVAL=10;COUNT=5',
             'Multiple DTSTART is not supported.'),
            ('DTSTART:{} RRULE:FREQ=DAILY;INTERVAL=10;COUNT=5'.format(parse('Thu, 25 Sep 2003 10:49:41 -0300')),
             'Valid DTSTART required in rrule. Value should start with: DTSTART:YYYYMMDDTHHMMSSZ'),
            ('DTSTART:20140331T055000 RRULE:FREQ=MINUTELY;INTERVAL=10;COUNT=5',
             'DTSTART cannot be a naive datetime.  Specify ;TZINFO= or YYYYMMDDTHHMMSSZZ.'),
            ('RRULE:FREQ=MINUTELY;INTERVAL=10;COUNT=5',
             'Valid DTSTART required in rrule. Value should start with: DTSTART:YYYYMMDDTHHMMSSZ'),
            ('FREQ=MINUTELY;INTERVAL=10;COUNT=5',
             'Valid DTSTART required in rrule. Value should start with: DTSTART:YYYYMMDDTHHMMSSZ'),
            ('DTSTART:20240331T075000Z RRULE:FREQ=DAILY;INTERVAL=1;COUNT=10000000', 'COUNT > 999 is unsupported.'),
            ('DTSTART;TZID=Not-A-Real-Timezone:19961105T090000 RRULE:FREQ=MINUTELY;INTERVAL=10;COUNT=5',
             'rrule parsing failed validation: A valid TZID must be provided (e.g., America/New_York)'),
            ('DTSTART:20140331T055000Z RRULE:FREQ=SECONDLY;INTERVAL=1', 'SECONDLY is not supported.'),
            ('DTSTART:20140331T055000Z RRULE:FREQ=SECONDLY', 'INTERVAL required in rrule.'),
            ('DTSTART:20140331T055000Z RRULE:FREQ=YEARLY;BYDAY=20MO;INTERVAL=1',
             'BYDAY with numeric prefix not supported.'),
            ('DTSTART:20140331T055000Z RRULE:FREQ=MONTHLY;BYMONTHDAY=10,15;INTERVAL=1',
             'Multiple BYMONTHDAYs not supported.'),
            ('DTSTART:20140331T055000Z RRULE:FREQ=YEARLY;BYMONTH=1,2;INTERVAL=1', 'Multiple BYMONTHs not supported.'),
            ('DTSTART:20140331T055000Z RRULE:FREQ=YEARLY;BYYEARDAY=120;INTERVAL=1', 'BYYEARDAY not supported.'),
            ('DTSTART:20140331T055000Z RRULE:FREQ=YEARLY;BYWEEKNO=10;INTERVAL=1', 'BYWEEKNO not supported.'),
            ('DTSTART:20030925T104941Z RRULE:FREQ=DAILY;INTERVAL=10;COUNT=500;UNTIL=20040925T104941Z', 'RRULE may not contain both COUNT and UNTIL'),
        ]
        for invalid, expected in invalid_rrules:
            with pytest.raises(exc.BadRequest) as e:
                unified_job_template.add_schedule(rrule=invalid)
                pytest.fail('Failed to raise for invalid rrule "{}"'.format(invalid))
            assert e.value[1].get('rrule', [e.value[1]])[0] == expected

    @pytest.mark.yolo
    def test_schedule_basic_integrity(self, unified_job_template):
        if unified_job_template.type in ('job_template', 'workflow_job_template'):
            unified_job_template.ask_variables_on_launch = True
            extra_data = {random_title(): random_title() for _ in range(20)}
        else:
            extra_data = {}
        rule = self.minutely_rrule()
        payload = dict(name=random_title(),
                       description=random_title(),
                       enabled=False,
                       rrule=str(rule),
                       extra_data=extra_data)
        schedule = unified_job_template.related.schedules.post(payload)
        assert schedule.name == payload['name']
        assert schedule.description == payload['description']
        assert schedule.rrule == str(rule)
        assert not schedule.enabled
        assert schedule.extra_data == extra_data

        schedules = unified_job_template.related.schedules.get()
        assert schedules.count == 1
        assert schedules.results.pop().id == schedule.id
        # Confirm basic REST operations are successful
        schedule.put()
        content = deepcopy(schedule.json)
        content['description'] = 'A New Description'
        schedule.put(content)
        assert schedule.get().description == 'A New Description'
        schedule.description = 'Some Other Description'
        assert schedule.get().description == 'Some Other Description'

    def test_only_count_limited_previous_recurrencences_are_evaluated(self, unified_job_template):
        epoch = parse('Jan 1 1970')
        dtend = epoch + relativedelta(years=9)
        rule = RRule(rrule.YEARLY, dtstart=epoch, count=10, interval=1)
        schedule = unified_job_template.add_schedule(rrule=rule)
        assert schedule.dtstart == self.strftime(epoch)
        assert schedule.dtend == self.strftime(dtend)
        assert schedule.next_run is None

    def test_only_count_limited_future_recurrences_are_evaluated(self, unified_job_template):
        odyssey_three = parse('Jan 1 2061')
        dtend = odyssey_three + relativedelta(years=9)
        rule = RRule(rrule.YEARLY, dtstart=odyssey_three, count=10, interval=1)
        schedule = unified_job_template.add_schedule(rrule=rule)
        assert schedule.dtstart == self.strftime(odyssey_three)
        assert schedule.dtend == self.strftime(dtend)
        assert schedule.next_run == rule.next_run

    def test_only_count_limited_overlapping_recurrences_are_evaluated(self, unified_job_template):
        last_week = datetime.utcnow() + relativedelta(weeks=-1, minutes=+1)
        dtend = datetime.utcnow() + relativedelta(days=2, minutes=+1)
        rule = RRule(rrule.DAILY, dtstart=last_week, count=10)
        schedule = unified_job_template.add_schedule(rrule=rule)
        assert schedule.dtstart == self.strftime(last_week)
        assert schedule.dtend == self.strftime(dtend)
        assert schedule.next_run == rule.next_run

    def test_only_until_limited_previous_recurrencences_are_evaluated(self, unified_job_template):
        epoch = parse('Jan 1 1970')
        dtend = epoch + relativedelta(years=9)
        rule = RRule(rrule.YEARLY, dtstart=epoch, until=dtend, interval=1)
        schedule = unified_job_template.add_schedule(rrule=rule)
        assert schedule.dtstart == self.strftime(epoch)
        assert schedule.dtend == self.strftime(dtend)
        assert schedule.next_run is None

    def test_only_until_limited_future_recurrences_are_evaluated(self, unified_job_template):
        odyssey_three = parse('Jan 1 2061')
        dtend = odyssey_three + relativedelta(years=9)
        rule = RRule(rrule.YEARLY, dtstart=odyssey_three, until=dtend, interval=1)
        schedule = unified_job_template.add_schedule(rrule=rule)
        assert schedule.dtstart == self.strftime(odyssey_three)
        assert schedule.dtend == self.strftime(dtend)
        assert schedule.next_run == rule.next_run

    def test_only_until_limited_overlapping_recurrences_are_evaluated(self, project):
        last_week = datetime.utcnow() + relativedelta(weeks=-1, minutes=+1)
        next_week = datetime.utcnow() + relativedelta(weeks=+1, minutes=+1)
        rule = RRule(rrule.DAILY, dtstart=last_week, until=next_week)
        schedule = project.add_schedule(rrule=rule)
        assert schedule.dtstart == self.strftime(last_week)
        assert schedule.dtend == self.strftime(next_week)
        assert schedule.next_run == rule.next_run

    def test_expected_fields_are_readonly(self, factories):
        schedule = factories.job_template().add_schedule()
        original_dtstart = schedule.dtstart
        schedule.dtstart = 'Undesired dtstart'
        assert schedule.dtstart == original_dtstart
        original_dtend = schedule.dtend
        schedule.dtend = 'Undesired dtend'
        assert schedule.dtend == original_dtend
        original_next_run = schedule.next_run
        schedule.next_run = 'Undesired next_run'
        assert schedule.next_run == original_next_run
        schedule.json.update(dict(dtstart='Undesired dtstart',
                                  dtend='Undesired dtend',
                                  next_run='Undesired next_run'))
        schedule.put()
        assert schedule.dtstart == original_dtstart
        assert schedule.dtend == original_dtend
        assert schedule.next_run == original_next_run

    def test_successful_schedule_deletions(self, unified_job_template):
        added_schedules = [unified_job_template.add_schedule() for _ in range(5)]
        schedules = unified_job_template.related.schedules.get()
        for _ in range(5):
            assert set([s.id for s in schedules.get().results]) == set([s.id for s in added_schedules])
            added_schedules.pop().delete()
        assert not schedules.get().count
        assert not schedules.results

    def test_successful_cascade_schedule_deletions(self, unified_job_template):
        schedules = [unified_job_template.add_schedule() for _ in range(5)]
        unified_job_template.delete()
        for schedule in schedules:
            with pytest.raises(exc.NotFound):
                schedule.get()

    @pytest.mark.github('https://github.com/ansible/tower-qa/issues/2591', skip=True)
    def test_schedule_triggers_launch_without_count(self, unified_job_template):
        rule = self.minutely_rrule()
        schedule = unified_job_template.add_schedule(rrule=rule)
        assert schedule.next_run == rule.next_run

        unified_jobs = schedule.related.unified_jobs.get()
        poll_until(lambda: unified_jobs.get().count == 1, interval=15, timeout=5 * 60)
        job = unified_jobs.results.pop()
        job.wait_until_completed().assert_successful()
        assert schedule.get().next_run == rule.next_run

    @pytest.mark.github('https://github.com/ansible/tower-qa/issues/2591', skip=True)
    def test_schedule_triggers_launch_with_count(self, unified_job_template):
        rule = self.minutely_rrule(count=2)
        schedule = unified_job_template.add_schedule(rrule=rule)
        assert schedule.next_run == rule.next_run

        unified_jobs = schedule.related.unified_jobs.get()
        poll_until(lambda: unified_jobs.get().count == 1, interval=15, timeout=5 * 60)
        job = unified_jobs.results.pop()
        job.wait_until_completed().assert_successful()
        assert schedule.get().next_run is None

    def test_modified_by_unaffected_by_launch(self, v2, job_template_ping):
        assert job_template_ping.summary_fields.modified_by['username'] == config.credentials.users.admin.username
        schedule = job_template_ping.add_schedule(rrule=self.minutely_rrule())

        unified_jobs = schedule.related.unified_jobs.get()
        poll_until(lambda: unified_jobs.get().count == 1, interval=15, timeout=5 * 60)
        tmpl = v2.job_templates.get(id=job_template_ping.id).results.pop()
        assert tmpl.summary_fields.get('modified_by', {}).get('username') == config.credentials.users.admin.username

    def test_awx_metavars_for_scheduled_jobs(self, v2, factories, update_setting_pg):
        update_setting_pg(
            v2.settings.get().get_endpoint('jobs'),
            dict(ALLOW_JINJA_IN_EXTRA_VARS='always')
        )
        jt = factories.job_template(playbook='debug_extra_vars.yml',
                                       extra_vars='var1: "{{ awx_schedule_id }}"')
        factories.host(inventory=jt.ds.inventory)
        schedule = jt.add_schedule(rrule=self.minutely_rrule())

        unified_jobs = schedule.related.unified_jobs.get()
        poll_until(lambda: unified_jobs.get().count == 1, interval=15, timeout=5 * 60)
        job = unified_jobs.results.pop()
        job.wait_until_completed().assert_successful()
        assert '"var1": "{}"'.format(schedule.id) in job.result_stdout

    @pytest.mark.github('https://github.com/ansible/tower/issues/891', skip=True)
    def test_schedule_preview_accounts_for_missing_dst_hour(self, v2):
        schedules = v2.schedules.get()
        dst_starts = ('20190310', '20200308', '20210314', '20220313',
                      '20230312', '20240310', '20250309', '20260308',
                      '20270314', '20280312', '20290311')
        for dst_start in dst_starts:
            rule = 'DTSTART;TZID=America/New_York:{}T013000 RRULE:FREQ=HOURLY;INTERVAL=1;COUNT=3'.format(dst_start)
            prev = schedules.preview(rule)
            assert '06:30:00Z' in prev.utc[0]
            assert '07:30:00Z' in prev.utc[1]
            assert '08:30:00Z' in prev.utc[2]
            assert '01:30:00-05:00' in prev.local[0]
            assert '03:30:00-04:00' in prev.local[1]
            assert '04:30:00-04:00' in prev.local[2]

    def test_schedule_preview_accounts_for_repeated_dst_hour(self, v2):
        schedules = v2.schedules.get()
        dst_ends = ('20191103', '20211107', '20221106', '20231105',
                    '20241103', '20251102', '20261101', '20271107',
                    '20281105', '20291104')
        for dst_end in dst_ends:
            rule = 'DTSTART;TZID=America/New_York:{}T013000 RRULE:FREQ=HOURLY;INTERVAL=1;COUNT=3'.format(dst_end)
            prev = schedules.preview(rule)
            assert '05:30:00Z' in prev.utc[0]
            assert '07:30:00Z' in prev.utc[1]
            assert '08:30:00Z' in prev.utc[2]
            assert '01:30:00-04:00' in prev.local[0]
            assert '02:30:00-05:00' in prev.local[1]
            assert '03:30:00-05:00' in prev.local[2]

    @pytest.mark.parametrize('month', (1, 6))  # Jan & June, to test DST
    def test_schedule_preview_supports_all_zoneinfo_provided_zones(self, v2, month):
        schedules = v2.schedules.get()
        zones = [zi['name'] for zi in schedules.get_zoneinfo()]
        assert zones

        dt = datetime(2035, month, 1, 0, 0, 1)

        from awxkit.utils import UTC
        utc = UTC()

        offsets = ['+0000', '+0100', '+0200', '+0300', '+0330', '+0400', '+0430', '+0500', '+0530', '+0545', '+0600', '+0630',
                   '+0700', '+0800', '+0830', '+0845', '+0900', '+0930', '+1000', '+1030', '+1100', '+1200', '+1300', '+1345',
                   '+1400', '-0100', '-0200', '-0300', '-0330', '-0400', '-0500', '-0600', '-0700', '-0800', '-0900', '-0930',
                   '-1000', '-1100', '-1200']

        def expected_utc(offset):
            return parse('2035 {} 1 0:0:1 {}'.format(month, offset)).astimezone(utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        def expected_local(offset):
            return '2035-0{}-01T00:00:01{}:{}'.format(month, offset[:3], offset[3:]) if offset != '+0000' else '2035-0{}-01T00:00:01Z'.format(month)

        failed_zones = []
        error_stream = io.StringIO()
        for zone in zones:
            if zone in ['Africa/Khartoum', 'Africa/Sao_Tome', 'Africa/Windhoek', 'America/Grand_Turk',
                        'Antarctica/Casey', 'Asia/Famagusta', 'Asia/Pyongyang', 'Pacific/Tongatapu',
                        'Europe/Volgograd', 'Africa/Casablanca', 'Africa/El_Aaiun', 'Asia/Qyzylorda',
                        'America/Campo_Grande', 'America/Cuiaba', 'America/Sao_Paulo', 'Brazil/East',
                        'Pacific/Norfolk']:
                # Bug in dateutil, timezone not supported, exported restricted or not important
                continue
            try:
                rule = 'DTSTART;TZID={}:20350{}01T000001 RRULE:FREQ=HOURLY;INTERVAL=1;COUNT=1'.format(zone, month)
                prev = schedules.preview(rule)
                try:
                    expected_offset = pytz.timezone(zone).localize(dt).strftime('%z')
                except pytz.UnknownTimeZoneError:
                    continue
                if month == 1:
                    assert expected_offset in offsets
                expected = (expected_utc(expected_offset), expected_local(expected_offset))
                assert prev.utc[0] == expected[0]
                assert prev.local[0] == expected[1]
                assert len(prev.utc) == 1
                assert len(prev.local) == 1
            except Exception:
                error_stream.write('Error testing zone "{}"'.format(zone))
                traceback.print_exc(file=error_stream)
                failed_zones.append(zone)
        if failed_zones:
            error_str = error_stream.getvalue()
            error_stream.close()
            raise Exception(
                'Assertions for some time zones failed.\nFailed zones: {}\nErrors: {}'.format(
                    failed_zones, error_str
                )
            )
        error_stream.close()
