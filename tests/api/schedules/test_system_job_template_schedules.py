import pytest

from tests.api.schedules import SchedulesTest


@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestSystemJobTemplateSchedules(SchedulesTest):

    @pytest.mark.parametrize('name, extra_data',
                             [('Cleanup Job Schedule', dict(days='120')),
                              ('Cleanup Activity Schedule', dict(days='355'))],
                             ids=['Cleanup Job Schedule', 'Cleanup Activity Schedule'])
    def test_default_schedules_are_prepopulated(self, v2, name, extra_data):
        schedules = v2.schedules.get(name=name)
        assert schedules.count == 1
        assert schedules.results.pop().extra_data == extra_data

    def test_sjt_can_have_multiple_schedules(self, request, system_job_template):
        extra_data = dict(days='120')
        schedules = [system_job_template.add_schedule(extra_data=extra_data) for _ in range(5)]

        def teardown():
            for s in schedules:
                s.delete()

        request.addfinalizer(teardown)

        assert system_job_template.related.schedules.get().count == 6
