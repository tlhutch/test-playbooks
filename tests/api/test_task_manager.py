from dateutil.parser import parse as du_parse
import pytest

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Task_Manager(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_project_update(self, project):
        """Test a project may only have one project update running at a time. Here, we launch
        two project updates on the same project and then check that only one update was
        running at any given point in time.
        """
        # launch two updates
        updates = []
        for _ in range(2):
            update = project.update().wait_until_completed()
            updates.append(update)

        # check that we have no overlapping project updates
        assert du_parse(updates[0].finished) < du_parse(updates[1].started), \
            "Expected update {0} to finish before update {1} started.".format(updates[0].id, updates[1].id)

    def test_inventory_update(self, custom_inventory_source):
        """Test an inventory source may only have one inventory update running at a time. Here,
        we launch two inventory updates on the same inventory source and then check that only one
        update was running at any given point in time.
        """
        # launch two updates
        updates = []
        for _ in range(2):
            update = custom_inventory_source.update().wait_until_completed()
            updates.append(update)

        # check that we have no overlapping project updates
        assert du_parse(updates[0].finished) < du_parse(updates[1].started), \
            "Expected update {0} to finish before update {1} started.".format(updates[0].id, updates[1].id)

    def test_system_job(self, system_jobs):
        """Launch all three of our system jobs. Assert no system job was running when another system
        job was running.
        """
        # wait for system jobs to finish
        for job in system_jobs:
            job.wait_until_completed()
