import pytest
from dateutil.parser import parse as du_parse

from tests.api import Base_Api_Test


def check_sequential_jobs(jobs):
    """Helper function that will check that jobs ran sequentially. How this works:
    * Wait for jobs to finish
    * Sort jobs by start time.
    * Check that each job finishes before the next job starts.

    :jobs: A list of job page objects.
    """
    # wait for jobs to finish
    for job in jobs:
        job.wait_until_completed()

    # check that jobs ran sequentially
    intervals = [[job.started, job.finished] for job in jobs]
    sorted_intervals = sorted(intervals, key=lambda x: x[0])
    for i in range(1, len(sorted_intervals)):
        assert sorted_intervals[i-1][1] < sorted_intervals[i][0], \
            "Job overlap found: we have an instance where one job starts before previous job finishes."


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
        # launch three updates
        for _ in range(3):
            project.update()
        updates = project.related.project_updates.get()

        # check that we have no overlapping project updates
        updates = project.related.project_updates.get()
        check_sequential_jobs(updates.results)

    def test_inventory_update(self, custom_inventory_source):
        """Test an inventory source may only have one inventory update running at a time. Here,
        we launch three inventory updates on the same inventory source and then check that only one
        update was running at any given point in time.
        """
        # launch three updates
        for _ in range(3):
            custom_inventory_source.update()

        # check that we have no overlapping inventory updates
        updates = custom_inventory_source.related.inventory_updates.get()
        check_sequential_jobs(updates.results)

    def test_job_template(self, job_template):
        """Launch several jobs using the same JT. Assert no job was running when another job was
        running.
        """
        # launch three jobs
        for _ in range(3):
            job_template.launch()

        # check that we have no overlapping jobs
        jobs = job_template.related.jobs.get()
        check_sequential_jobs(jobs.results)

    def test_job_template_with_allow_simultaneous(self, job_template):
        """Launch two jobs using the same JT with allow_simultaneous enabled. Assert that we have
        overlapping jobs.
        """
        job_template.patch(allow_simultaneous=True, playbook="sleep.yml", extra_vars=dict(sleep_interval=10))

        # launch two jobs
        job_1 = job_template.launch()
        job_2 = job_template.launch()
        job_1.wait_until_completed()
        job_2.wait_until_completed()

        # check that we have overlapping jobs
        # assert that job_1 started before job_2 finished
        assert du_parse(job_1.started) < du_parse(job_2.finished)

        # assert that job_1 finished after job_2 started
        assert du_parse(job_1.finished) > du_parse(job_2.started)

    def test_system_job(self, system_jobs):
        """Launch all three of our system jobs. Assert no system job was running when another system
        job was running.
        """
        # check that we have no overlapping system jobs
        check_sequential_jobs(system_jobs)

    def test_related_project_update(self, job_template):
        """If a project is used in a JT, then spawned jobs and updates must run sequentially.
        """
        project = job_template.related.project.get()

        # launch jobs
        job = job_template.launch()
        update = project.update()

        # check that our update and job ran sequentially
        jobs = [job, update]
        check_sequential_jobs(jobs)

    def test_related_inventory_update(self, job_template, custom_group):
        """If an inventory is used in a JT and has a group that allows for updates, then spawned
        jobs and updates must run sequentially.
        """
        inv_source = custom_group.related.inventory_source.get()

        # launch jobs
        job = job_template.launch()
        update = inv_source.update()

        # check that our update and job ran sequentially
        jobs = [job, update]
        check_sequential_jobs(jobs)
