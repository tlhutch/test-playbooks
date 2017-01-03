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


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Cascade_Fail(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    @pytest.mark.fixture_args(source_script='''#!/usr/bin/env python
import json, time
# sleep helps us cancel the inventory update
time.sleep(60)
inventory = dict()
print json.dumps(inventory)
''')
    def test_cascade_cancel_with_inventory_update(self, job_template, custom_group):
        '''
        Tests that if you cancel an inventory update before it finishes that its dependent job fails.
        '''
        inv_source_pg = custom_group.get_related('inventory_source')
        inv_source_pg.patch(update_on_launch=True)

        assert not inv_source_pg.last_updated, "inv_source_pg unexpectedly updated."

        # Launch job
        job_pg = job_template.launch()

        # Wait for the inventory_source to start
        inv_source_pg.wait_until_started()

        # Cancel inventory update
        inv_update_pg = inv_source_pg.get_related('current_update')
        cancel_pg = inv_update_pg.get_related('cancel')
        assert cancel_pg.can_cancel, "The inventory_update is not cancellable, it may have already completed - %s." % inv_update_pg.get()
        cancel_pg.post()

        # Assert launched job failed
        assert job_pg.wait_until_completed().status == "failed", "Unexpected job status - %s." % job_pg

        # Assess job_explanation
        assert job_pg.job_explanation.startswith(u'Previous Task Failed:'), \
            "Unexpected job_explanation: %s." % job_pg.job_explanation
        try:
            job_explanation = json.loads(job_pg.job_explanation[22:])
        except Exception:
            pytest.fail("job_explanation not stored as JSON data: %s.") % job_explanation
        assert job_explanation['job_type'] == inv_update_pg.type
        assert job_explanation['job_name'] == inv_update_pg.name
        assert job_explanation['job_id'] == str(inv_update_pg.id)

        # Assert inventory update and source canceled
        assert inv_update_pg.get().status == 'canceled', \
            "Unexpected job status after cancelling (expected 'canceled') - %s." % inv_update_pg.status
        assert inv_source_pg.get().status == 'canceled', \
            "Unexpected inventory_source status after cancelling (expected 'canceled') - %s." % inv_source_pg.status

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/4225')
    @pytest.mark.fixture_args(source_script='''#!/usr/bin/env python
import json, time
# sleep helps us cancel the inventory update
time.sleep(60)
inventory = dict()
print json.dumps(inventory)
''')
    def test_cascade_cancel_with_multiple_inventory_updates(self, job_template, custom_group, another_custom_group):
        '''
        Tests that if you cancel an inventory update before it finishes that its dependent jobs fail.
        '''
        inv_source_pg = custom_group.get_related('inventory_source')
        inv_source_pg.patch(update_on_launch=True)
        another_inv_source_pg = another_custom_group.get_related('inventory_source')
        another_inv_source_pg.patch(update_on_launch=True)

        assert not inv_source_pg.last_updated, "inv_source_pg unexpectedly updated."
        assert not another_inv_source_pg.last_updated, "another_inv_source_pg unexpectedly updated."

        # Launch job
        job_pg = job_template.launch()

        # Wait for the inventory sources to start
        inv_update_pg = inv_source_pg.wait_until_started().get_related('current_update')
        another_inv_update_pg = another_inv_source_pg.wait_until_started().get_related('current_update')
        inv_update_pg_started = parse(inv_update_pg.created)
        another_inv_update_pg_started = parse(another_inv_update_pg.created)

        # Identify the sequence of the inventory updates and navigate to cancel_pg
        if inv_update_pg_started > another_inv_update_pg_started:
            cancel_pg = another_inv_update_pg.get_related('cancel')
            assert cancel_pg.can_cancel, \
                "Inventory update is not cancellable, it may have already completed - %s." % another_inv_update_pg.get()
            # Set new set of vars
            first_inv_update_pg, first_inv_source_pg = another_inv_update_pg, another_inv_source_pg
            second_inv_update_pg, second_inv_source_pg = inv_update_pg, inv_source_pg
        else:
            cancel_pg = inv_update_pg.get_related('cancel')
            assert cancel_pg.can_cancel, \
                "Inventory update is not cancellable, it may have already completed - %s." % inv_update_pg.get()
            # Set new set of vars
            first_inv_update_pg, first_inv_source_pg = inv_update_pg, inv_source_pg
            second_inv_update_pg, second_inv_source_pg = another_inv_update_pg, another_inv_source_pg

        # Cancel the first inventory update
        cancel_pg.post()

        # Assert launched job failed
        assert job_pg.wait_until_completed().status == "failed", "Unexpected job status - %s." % job_pg

        # Assess job_explanation
        assert job_pg.job_explanation.startswith(u'Previous Task Failed:'), \
            "Unexpected job_explanation: %s." % job_pg.job_explanation
        try:
            job_explanation = json.loads(job_pg.job_explanation[22:])
        except Exception:
            pytest.fail("job_explanation not stored as JSON data: %s.") % job_explanation
        assert job_explanation['job_type'] == first_inv_update_pg.type
        assert job_explanation['job_name'] == first_inv_update_pg.name
        assert job_explanation['job_id'] == str(first_inv_update_pg.id)

        # Assert first inventory update and source cancelled
        assert first_inv_update_pg.get().status == 'canceled', \
            "Did not cancel job as expected (expected status:canceled) - %s." % first_inv_update_pg
        assert first_inv_source_pg.get().status == 'canceled', \
            "Did not cancel job as expected (expected status:canceled) - %s." % first_inv_source_pg

        # Assert second inventory update and source failed
        assert second_inv_update_pg.get().status == 'failed', \
            "Secondary inventory update not failed (status: %s)." % second_inv_update_pg.status
        assert second_inv_source_pg.get().status == 'failed', \
            "Secondary inventory update not failed (status: %s)." % second_inv_source_pg.status

        # Assess second update job_explanation
        assert second_inv_update_pg.job_explanation.startswith(u'Previous Task Failed:'), \
            "Unexpected job_explanation: %s." % second_inv_update_pg.job_explanation
        try:
            inventory_job_explanation = json.loads(second_inv_update_pg.job_explanation[22:])
        except Exception:
            pytest.fail("job_explanation not stored as JSON data: %s.") % inventory_job_explanation
        assert inventory_job_explanation['job_type'] == first_inv_update_pg.type
        assert inventory_job_explanation['job_name'] == first_inv_update_pg.name
        assert inventory_job_explanation['job_id'] == str(first_inv_update_pg.id)

    def test_cascade_cancel_with_project_update(self, job_template_with_project_django):
        '''
        Tests that if you cancel a SCM update before it finishes that its dependent job fails.
        '''
        project_pg = job_template_with_project_django.get_related('project')

        # Launch job
        job_pg = job_template_with_project_django.launch()

        # Wait for new update to start and cancel it
        project_update_pg = project_pg.wait_until_started().get_related('current_update')
        cancel_pg = project_update_pg.get_related('cancel')
        assert cancel_pg.can_cancel, "The project update is not cancellable, it may have already completed - %s." % project_update_pg.get()
        cancel_pg.post()

        # Assert launched job failed
        assert job_pg.wait_until_completed().status == "failed", "Unexpected job status - %s." % job_pg

        # Assess job_explanation
        assert job_pg.job_explanation.startswith(u'Previous Task Failed:'), \
            "Unexpected job_explanation: %s." % job_pg.job_explanation
        try:
            job_explanation = json.loads(job_pg.job_explanation[22:])
        except Exception:
            pytest.fail("job_explanation not stored as JSON data: %s.") % job_explanation
        assert job_explanation['job_type'] == project_update_pg.type
        assert job_explanation['job_name'] == project_update_pg.name
        assert job_explanation['job_id'] == str(project_update_pg.id)

        # Assert project update and project canceled
        assert project_update_pg.get().status == 'canceled', \
            "Unexpected project_update status after cancelling (expected 'canceled') - %s." % project_update_pg
        assert project_pg.get().status == 'canceled', \
            "Unexpected project status (expected status:canceled) - %s." % project_pg

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/4225')
    def test_cascade_cancel_project_update_with_inventory_and_project_updates(self, job_template_with_project_django, custom_group):
        '''
        Tests that if you cancel a scm update before it finishes that its dependent job
        fails. This test runs both inventory and SCM updates on job launch.
        '''
        project_pg = job_template_with_project_django.get_related('project')
        inv_source_pg = custom_group.get_related('inventory_source')
        inv_source_pg.patch(update_on_launch=True)

        assert not inv_source_pg.last_updated, "inv_source_pg unexpectedly updated."

        # Launch job
        job_pg = job_template_with_project_django.launch()

        # Wait for new update to start and cancel it
        project_update_pg = project_pg.wait_until_started().get_related('current_update')
        cancel_pg = project_update_pg.get_related('cancel')
        assert cancel_pg.can_cancel, "The project update is not cancellable, it may have already completed - %s." % project_update_pg.get()
        cancel_pg.post()

        # Assert launched job failed
        assert job_pg.wait_until_completed().status == "failed", "Unexpected job status - %s." % job_pg

        # Assess job_explanation
        assert job_pg.job_explanation.startswith(u'Previous Task Failed:'), \
            "Unexpected job_explanation: %s" % job_pg.job_explanation
        try:
            job_explanation = json.loads(job_pg.job_explanation[22:])
        except Exception:
            pytest.fail("job_explanation not stored as JSON data: %s.") % job_explanation
        assert job_explanation['job_type'] == project_update_pg.type
        assert job_explanation['job_name'] == project_update_pg.name
        assert job_explanation['job_id'] == str(project_update_pg.id)

        # Assert project update and project cancelled
        assert project_update_pg.get().status == 'canceled', \
            "Unexpected job status after cancelling (expected 'canceled') - %s." % project_update_pg
        assert project_pg.get().status == 'canceled', \
            "Unexpected project status after cancelling (expected 'canceled') - %s." % project_pg

        # Assert inventory update and source successful
        inv_update_pg = inv_source_pg.wait_until_completed().get_related('last_update')
        assert inv_update_pg.is_successful, "Inventory update unexpectedly unsuccessful - %s." % inv_update_pg
        assert inv_source_pg.get().is_successful, "inventory_source unexpectedly unsuccessful - %s." % inv_source_pg

    @pytest.mark.fixture_args(source_script='''#!/usr/bin/env python
import json, time
# sleep helps us cancel the inventory update
time.sleep(60)
inventory = dict()
print json.dumps(inventory)
''')
    def test_cascade_cancel_inventory_update_with_inventory_and_project_updates(self, job_template, custom_group):
        '''
        Tests that if you cancel an inventory update before it finishes that its dependent job
        fails. This test runs both inventory and SCM updates on job launch.
        '''
        project_pg = job_template.get_related('project')
        project_pg.patch(update_on_launch=True)
        inv_source_pg = custom_group.get_related('inventory_source')
        inv_source_pg.patch(update_on_launch=True)

        assert not inv_source_pg.last_updated, "inv_source_pg unexpectedly updated."

        # Launch job
        job_pg = job_template.launch()

        # Wait for the inventory_source to start
        inv_source_pg.wait_until_started()

        # Cancel inventory update
        inv_update_pg = inv_source_pg.get_related('current_update')
        cancel_pg = inv_update_pg.get_related('cancel')
        assert cancel_pg.can_cancel, "The inventory_update is not cancellable, it may have already completed - %s." % inv_update_pg.get()
        cancel_pg.post()

        # Assert launched job failed
        assert job_pg.wait_until_completed().status == "failed", "Unexpected job status - %s." % job_pg

        # Assess job_explanation
        assert job_pg.job_explanation.startswith(u'Previous Task Failed:'), \
            "Unexpected job_explanation: %s." % job_pg.job_explanation
        try:
            job_explanation = json.loads(job_pg.job_explanation[22:])
        except Exception:
            pytest.fail("job_explanation not stored as JSON data: %s.") % job_explanation
        assert job_explanation['job_type'] == inv_update_pg.type
        assert job_explanation['job_name'] == inv_update_pg.name
        assert job_explanation['job_id'] == str(inv_update_pg.id)

        # Assert project update and project successful
        project_update_pg = project_pg.get_related('last_update')
        assert project_update_pg.wait_until_completed().status == 'successful', "Project update unsuccessful - %s." % project_update_pg
        assert project_pg.get().status == 'successful', "Project unsuccessful - %s." % project_pg

        # Assert inventory update and source canceled
        assert inv_update_pg.get().status == "canceled", \
            "Unexpected inventory update_pg status after cancelling (expected 'canceled') - %s." % inv_update_pg
        assert inv_source_pg.get().status == "canceled", \
            "Unexpected inventory_source status after cancelling (expected 'canceled') - %s." % inv_source_pg
