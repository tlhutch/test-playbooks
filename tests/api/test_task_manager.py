import pytest

from tests.api import Base_Api_Test


def check_sequential_jobs(jobs):
    """Helper function that will check that jobs ran sequentially. How this works:
    * Sort jobs by start time.
    * Check that each job finishes before the next job starts.

    :jobs: A list of job page objects.
    """
    intervals = [[job.started, job.finished] for job in jobs]
    sorted_intervals = sorted(intervals, key=lambda x: x[0])
    for i in range(1, len(sorted_intervals)):
        assert sorted_intervals[i-1][1] <= sorted_intervals[i][0], \
            "We have overlapping jobs. Format: [job.started, job.finished]."


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Task_Manager(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_project_update(self, project):
        """Test a project may only have one project update running at a time. Here, we launch
        three project updates on the same project and then check that only one update was
        running at any given point in time.
        """
        # launch two updates
        for _ in range(3):
            project.update().wait_until_completed()

        # check that we have no overlapping project updates
        updates = project.related.project_updates.get()
        check_sequential_jobs(updates.results)

    def test_inventory_update(self, custom_inventory_source):
        """Test an inventory source may only have one inventory update running at a time. Here,
        we launch three inventory updates on the same inventory source and then check that only one
        update was running at any given point in time.
        """
        # launch two updates
        for _ in range(3):
            custom_inventory_source.update().wait_until_completed()

        # check that we have no overlapping inventory updates
        updates = custom_inventory_source.related.inventory_updates.get()
        check_sequential_jobs(updates.results)

    def test_system_job(self, system_jobs):
        """Launch all three of our system jobs. Assert no system job was running when another system
        job was running.
        """
        # wait for system jobs to finish
        for job in system_jobs:
            job.wait_until_completed()

        # check that we have no overlapping system jobs
        check_sequential_jobs(system_jobs)
