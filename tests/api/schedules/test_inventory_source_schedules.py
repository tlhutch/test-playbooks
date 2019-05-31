import pytest

from towerkit.utils import poll_until

from tests.api.schedules import SchedulesTest


@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestInventorySourceSchedules(SchedulesTest):

    def test_inventory_source_schedules_are_functional(self, factories):
        schedule = factories.inventory_source().add_schedule(rrule=self.minutely_rrule())

        schedule_jobs = schedule.related.unified_jobs.get()
        poll_until(lambda: schedule_jobs.get().count == 1, interval=15, timeout=5 * 60)

        inventory_update = schedule_jobs.get().results.pop().wait_until_completed()
        inventory_update.assert_successful()
