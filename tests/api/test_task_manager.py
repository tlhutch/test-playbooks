import json
import time

from awxkit import utils
from dateutil.parser import parse as du_parse
import pytest

from tests.api import APITest


@pytest.fixture
def sleeping_inventory_script(factories):
    source_script = """#!/usr/bin/env python
import json, time
time.sleep(300)
inventory = dict()
print(json.dumps(inventory))
"""
    return factories.inventory_script(script=source_script)


@pytest.fixture(scope="function")
def cloud_inventory_job_template(job_template, cloud_inventory_source):
    # Substitute in no-op playbook that does not attempt to connect to host
    job_template.patch(playbook='debug.yml', inventory=cloud_inventory_source.related.inventory.get())
    return job_template


def wait_for_jobs_to_finish(jobs):
    """Helper function that waits for all jobs to finish.

    :jobs: A list whose elements are either unified jobs or a list containing
    unified jobs.
    """
    # wait for jobs to finish
    for entry in jobs:
        if isinstance(entry, list):
            for uj in entry:
                uj.wait_until_completed()
        else:
            entry.wait_until_completed()


def wait_for_jobs_to_run(jobs):
    """Helper function that waits for all jobs to run.

    :jobs: A list whose elements are either unified jobs or a list containing
    unified jobs.
    """
    # wait for jobs to run
    for entry in jobs:
        if isinstance(entry, list):
            for uj in entry:
                uj.wait_until_status(['running'] + uj.completed_statuses)
                assert uj.status == 'running'
        else:
            entry.wait_until_status(['running'] + entry.completed_statuses)
            assert entry.status == 'running'


def construct_time_series(jobs):
    """Helper function used to create time-series data for job sequence testing.
    Create a list whose elements are a list of the start and end times of either:
    A) A unified job.
    B) A two-element list of unified jobs. When given a list of unified jobs, make
    our entry a list whose first element is the first 'started' time of these jobs.
    Make the second entry the last 'finished' time of these jobs.

    Example:
    construct_time_series([[aws_update, gce_update], job])
    >>> [[start time of first inv_update, finished time of last inv_update], [job.started, job.finished]]
    """
    intervals = list()
    for entry in jobs:
        if isinstance(entry, list):
            # make sure that we actually have overlapping jobs
            check_overlapping_jobs(entry)
            first_started = min([job.started for job in entry])
            last_finished = max([job.finished for job in entry])
            intervals.append([first_started, last_finished])
        else:
            intervals.append([entry.started, entry.finished])
    return intervals


def check_sequential_jobs(jobs):
    """Helper function that will check that jobs ran sequentially. We do this
    by checking that each entry finishes before the next entry starts.

    :jobs: A list whose elements are either unified jobs or a list containing
    unified jobs.
    """
    # sort time series by 'started' value
    sorted_time_series = sorted(construct_time_series(jobs), key=lambda x: x[0])

    # check that we don't have overlapping elements
    for i in range(1, len(sorted_time_series)):
        assert sorted_time_series[i - 1][1] < sorted_time_series[i][0], \
            "Job overlap found: we have an instance where one job starts before the previous job finishes."\
            "\n\nTime series used: {0}.".format(sorted_time_series)


def check_overlapping_jobs(jobs):
    """Helper function that will check that two jobs have overlapping runtimes.
    :jobs: A list of unified job page objects.
    """
    jobs = sorted(jobs, key=lambda x: x.started)

    # assert that job1 starts before job2 finishes
    assert du_parse(jobs[0].started) < du_parse(jobs[1].finished)
    # assert that job1 finishes after job2 starts
    assert du_parse(jobs[0].finished) > du_parse(jobs[1].started)


def check_job_order(jobs):
    """Helper function that will check whether jobs ran in the right order.
    How this works:
    * Sort elements by 'started' time.
    * Sort elements by 'finished' time.
    * Check that our series order remains unchanged after both sorts.

    jobs: A list of page objects where we expect to have:
          jobs[0].started < jobs[1].started < jobs[2].started ...
          jobs[0].finished < jobs[1].finished < job[2].finished ...
    Note: jobs may also be a list of jobs. See the documentation for
    construct_time_series for more details.
    """
    time_series = construct_time_series(jobs)

    # check that our time series is already sorted by start time
    assert time_series == sorted(time_series, key=lambda k: k[0]), \
        "Unexpected job ordering upon sorting by started time.\
        \n\nTime series order: {0}.".format(time_series)
    # check that our time series is already sorted by finished time
    assert time_series == sorted(time_series, key=lambda k: k[1]), \
        "Unexpected job ordering upon sorting by finished time.\
        \n\nTime series order: {0}.".format(time_series)


def confirm_unified_jobs(jobs, check_sequential=True, check_order=True):
    """Helper function that performs the following:
    * Waits for unified jobs to finish.
    * Calls check_sequential_jobs and check_job_order if asked.
    """
    wait_for_jobs_to_finish(jobs)
    if check_sequential:
        check_sequential_jobs(jobs)
    if check_order:
        check_job_order(jobs)


def check_chain_canceled_job_explanation(canceled_job, chain_canceled_jobs):
    for chain_job in chain_canceled_jobs:
        assert chain_job.job_explanation.startswith('Previous Task Canceled:'), \
            "Unexpected job_explanation: %s." % chain_job.job_explanation
        try:
            job_explanation = json.loads(chain_job.job_explanation[24:])
        except Exception:
            pytest.fail("job_explanation not stored as JSON data: %s." % chain_job.job_explanation)
        assert job_explanation['job_type'] == canceled_job.type
        assert job_explanation['job_name'] == canceled_job.name
        assert job_explanation['job_id'] == str(canceled_job.id)


@pytest.mark.usefixtures('authtoken')
class Test_Sequential_Jobs(APITest):

    def test_project_update(self, project):
        """Test a project may only have one project update running at a time. Here, we launch
        three project updates on the same project and then check that:
        * Only one update was running at any given point in time.
        * Project updates ran in the order spawned.
        """
        # get three project updates
        update1 = project.related.project_updates.get().results.pop()
        update2 = project.update()
        update3 = project.update()
        ordered_updates = [update1, update2, update3]

        # confirm unified jobs ran as expected
        confirm_unified_jobs(ordered_updates)

    @pytest.mark.yolo
    def test_inventory_update(self, custom_inventory_source):
        """Test an inventory source may only have one inventory update running at a time. Here,
        we launch three inventory updates on the same inventory source and then check that:
        * Only one update was running at any given point in time.
        * Inventory updates ran in the order spawned.
        """
        # launch three updates
        update1 = custom_inventory_source.update()
        update2 = custom_inventory_source.update()
        update3 = custom_inventory_source.update()
        ordered_updates = [update1, update2, update3]

        # confirm unified jobs ran as expected
        confirm_unified_jobs(ordered_updates)

    def test_job_template(self, job_template):
        """Launch several jobs using the same JT. Check that:
        * No jobs ran simultaneously.
        * Jobs ran in the order spawned.
        """
        # launch three jobs
        job1 = job_template.launch()
        job2 = job_template.launch()
        job3 = job_template.launch()
        ordered_jobs = [job1, job2, job3]

        # confirm unified jobs ran as expected
        confirm_unified_jobs(ordered_jobs)

    def test_job_template_with_allow_simultaneous(self, job_template):
        """Launch two jobs using the same JT with allow_simultaneous enabled. Assert that we have
        overlapping jobs.
        """
        job_template.patch(allow_simultaneous=True, playbook="sleep.yml",
                           extra_vars=json.dumps(dict(sleep_interval=20)))

        # launch two jobs
        job_1 = job_template.launch()
        job_2 = job_template.launch()
        jobs = [job_1, job_2]
        wait_for_jobs_to_finish(jobs)

        # check that we have overlapping jobs
        check_overlapping_jobs(jobs)

    # Skip for Openshift because of Github Issue: https://github.com/ansible/tower-qa/issues/2591
    def test_workflow_job_template(self, skip_if_openshift, workflow_job_template, factories):
        """Launch several WFJs using the same WFJT. Check that:
        * No WFJs ran simultaneously.
        * No WFJN jobs ran simultaneously.
        * Jobs ran in the order spawned.
        """
        factories.workflow_job_template_node(workflow_job_template=workflow_job_template)

        # launch two workflow jobs
        ordered_wfjs = [workflow_job_template.launch() for _ in range(2)]
        wait_for_jobs_to_finish(ordered_wfjs)

        wfj1_nodes, wfj2_nodes = [wfj.related.workflow_nodes.get() for wfj in ordered_wfjs]
        ordered_node_jobs = [wfj_nodes.results.pop().related.job.get() for wfj_nodes in (wfj1_nodes, wfj2_nodes)]

        # confirm unified jobs ran as expected
        confirm_unified_jobs(ordered_wfjs)
        confirm_unified_jobs(ordered_node_jobs)

    def test_workflow_job_template_with_allow_simultaneous(self, factories):
        """Launch two WFJs using the same WFJT with allow_simultaneous enabled. Assert that we have
        overlapping WFJs and WFJN jobs.
        """
        wfjt = factories.workflow_job_template(allow_simultaneous=True)
        host = factories.host()
        jt = factories.job_template(allow_simultaneous=True, inventory=host.ds.inventory,
                                    playbook='sleep.yml', extra_vars=dict(sleep_interval=300))
        factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)

        # launch two workflow jobs
        ordered_wfjs = [wfjt.launch() for _ in range(2)]

        wfj1_nodes, wfj2_nodes = [wfj.related.workflow_nodes.get() for wfj in ordered_wfjs]
        utils.poll_until(lambda: hasattr(wfj1_nodes.get().results.pop().related, 'job'), interval=1, timeout=60)
        utils.poll_until(lambda: hasattr(wfj2_nodes.get().results.pop().related, 'job'), interval=1, timeout=60)

        ordered_node_jobs = [wfj_nodes.results.pop().related.job.get() for wfj_nodes in (wfj1_nodes, wfj2_nodes)]
        wait_for_jobs_to_run(ordered_node_jobs)

        # confirm unified jobs ran as expected
        assert ordered_wfjs[0].get().status == 'running'
        assert ordered_wfjs[1].get().status == 'running'
        assert ordered_node_jobs[0].get().status == 'running'
        assert ordered_node_jobs[1].get().status == 'running'

    def test_sequential_ad_hoc_commands(self, request, v2):
        """Launch three ad hoc commands on the same inventory. Check that:
        * No commands ran simultaneously.
        * Commands ran in the order spawned.
        """
        host = v2.hosts.create()
        request.addfinalizer(host.teardown)

        # lauch three commands
        ahc1 = v2.ad_hoc_commands.create(module_name='shell', module_args='true', inventory=host.ds.inventory)
        ahc2 = v2.ad_hoc_commands.create(module_name='shell', module_args='true', inventory=host.ds.inventory)
        ahc3 = v2.ad_hoc_commands.create(module_name='shell', module_args='true', inventory=host.ds.inventory)
        ordered_commands = [ahc1, ahc2, ahc3]

        # confirm unified jobs ran as expected
        confirm_unified_jobs(ordered_commands)

    # Skip for openshift because of Github Issue: https://github.com/ansible/tower-qa/issues/2591
    def test_simultaneous_ad_hoc_commands(self, skip_if_openshift, request, v2):
        """Launch two ad hoc commands on different inventories. Check that
        our commands run simultaneously.
        """
        host1 = v2.hosts.create()
        request.addfinalizer(host1.teardown)
        host2 = v2.hosts.create()
        request.addfinalizer(host2.teardown)

        # launch two commands
        ahc1 = v2.ad_hoc_commands.create(module_name='shell', module_args='sleep 5s', inventory=host1.ds.inventory)
        ahc2 = v2.ad_hoc_commands.create(module_name='shell', module_args='sleep 5s', inventory=host2.ds.inventory)
        ordered_commands = [ahc1, ahc2]
        wait_for_jobs_to_finish(ordered_commands)

        # check that we have overlapping commands
        check_overlapping_jobs(ordered_commands)

    def test_system_job(self, system_jobs):
        """Launch all three of our system jobs. Check that:
        * No system jobs were running simultaneously.
        * System jobs ran in the order spawned.
        """
        # confirm unified jobs ran as expected
        confirm_unified_jobs(system_jobs)

    def test_related_project_update(self, job_template):
        """If a project is used in a JT, then spawned jobs and updates must run sequentially.
        Check that:
        * Spawned unified jobs run sequentially.
        * Unified jobs run in the order launched.
        """
        project = job_template.related.project.get()

        # launch jobs
        update = project.update()
        job = job_template.launch()
        sorted_unified_jobs = [update, job]

        # confirm unified jobs ran as expected
        confirm_unified_jobs(sorted_unified_jobs)

    def test_related_inventory_update_with_job(self, custom_inventory_source, factories):
        """If an inventory is used in a JT and has a group that allows for updates, then spawned
        jobs and updates must run sequentially. Check that:
        * Spawned unified jobs run sequentially.
        * Unified jobs run in the order launched.
        """
        # launch jobs
        update = custom_inventory_source.update()
        job_template = factories.job_template(inventory=custom_inventory_source.related.inventory.get())
        job = job_template.launch()
        sorted_unified_jobs = [update, job]

        # confirm unified jobs ran as expected
        confirm_unified_jobs(sorted_unified_jobs)

    def test_related_inventory_update_with_command(self, request, factories, ad_hoc_command):
        """If an inventory is used in a command and has a group that allows for updates, then spawned
        commands and updates must run sequentially. Check that:
        * Spawned unified jobs run sequentially.
        * Unified jobs run in the order launched.
        """
        org = factories.organization()
        inventory_script = factories.inventory_script(organization=org)
        inventory = factories.inventory(organization=org)
        inv_source = factories.inventory_source(inventory=inventory, source_script=inventory_script)
        assert inv_source.source_script == inventory_script.id

        # launch unified jobs
        update = inv_source.update()
        command = factories.ad_hoc_command(module_name='shell', module_args='true', inventory=inventory)
        sorted_unified_jobs = [update, command]

        # confirm unified jobs ran as expected
        confirm_unified_jobs(sorted_unified_jobs)


@pytest.mark.usefixtures('authtoken')
class Test_Autospawned_Jobs(APITest):

    def test_inventory(self, factories):
        """Verify that an inventory update is triggered by our job launch. Job ordering
        should be as follows:
        * Inventory update should run first.
        * Job should run after the completion of our inventory update.
        """
        inv_source = factories.inventory_source(update_on_launch=True)
        assert not inv_source.last_updated
        assert not inv_source.last_job_run

        jt = factories.job_template(inventory=inv_source.ds.inventory, playbook='debug.yml')
        job = jt.launch().wait_until_completed()
        job.assert_successful()

        inv_update = inv_source.get().related.last_update.get()
        assert inv_source.get().last_updated
        assert inv_source.last_job_run
        inv_update.assert_successful()
        inv_source.assert_successful()

        # check that jobs ran sequentially and in the right order
        sorted_unified_jobs = [inv_update, job]
        confirm_unified_jobs(sorted_unified_jobs)

    # Skip for Openshift because of Github Issue: https://github.com/ansible/tower-qa/issues/2591
    @pytest.mark.yolo
    def test_inventory_multiple(self, skip_if_openshift, job_template, aws_credential, gce_credential, factories):
        """Verify that multiple inventory updates are triggered by job launch. Job ordering
        should be as follows:
        * AWS and GCE inventory updates should run simultaneously.
        * Upon completion of both inventory imports, job should run.
        """
        # set update_on_launch
        aws_inventory_source = factories.inventory_source(credential=aws_credential, source='ec2')
        inventory = aws_inventory_source.related.inventory.get()
        gce_inventory_source = factories.inventory_source(credential=gce_credential, source='gce', inventory=inventory)
        aws_inventory_source.patch(update_on_launch=True)
        gce_inventory_source.patch(update_on_launch=True)
        # Sanity check
        assert gce_inventory_source.inventory == aws_inventory_source.inventory

        # check inventory sources
        for inv_source in (aws_inventory_source, gce_inventory_source):
            assert inv_source.update_on_launch
            assert inv_source.update_cache_timeout == 0
            assert inv_source.last_updated is None, \
                "Not expecting inventory source to have been updated - %s." % inv_source

        # update job_template to cloud inventory
        # substitute in no-op playbook that does not attempt to connect to host
        job_template.patch(inventory=aws_inventory_source.inventory, playbook='debug.yml')

        # launch job_template and assert successful
        job_pg = job_template.launch().wait_until_completed(timeout=600)
        job_pg.assert_successful()

        # check that inventory updates were triggered
        for inv_source in (aws_inventory_source, gce_inventory_source):
            inv_source.get()
            assert inv_source.last_updated is not None, \
                "Expecting value for inventory_source last_updated - %s." % inv_source
            assert inv_source.last_job_run is not None, \
                "Expecting value for inventory_source last_job_run - %s." % inv_source

        # check that inventory updates were successful
        aws_update, gce_update = aws_inventory_source.related.last_update.get(), gce_inventory_source.related.last_update.get()
        aws_update.assert_successful()
        aws_inventory_source.assert_successful()
        gce_update.assert_successful()
        gce_inventory_source.assert_successful()

        # check that jobs ran sequentially and in the right order
        sorted_unified_jobs = [[aws_update, gce_update], job_pg]
        confirm_unified_jobs(sorted_unified_jobs)

    def test_inventory_cache_timeout(self, factories, custom_inventory_source):
        """Verify that an inventory update is not triggered by the job launch if the
        cache is still valid. Job ordering should be as follows:
        * Manually launched inventory update.
        * Job upon completion of inventory update.
        """
        # set update_on_launch and a five minute update_cache_timeout
        custom_inventory_job_template = factories.job_template(inventory=custom_inventory_source.related.inventory.get())
        cache_timeout = 60 * 5
        custom_inventory_source.patch(update_on_launch=True, update_cache_timeout=cache_timeout)
        assert custom_inventory_source.update_cache_timeout == cache_timeout
        assert custom_inventory_source.last_updated is None, \
            "Not expecting inventory source to have been updated - %s." % custom_inventory_source

        # launch inventory update and wait for completion
        inv_update_pg = custom_inventory_job_template.launch().wait_until_completed(timeout=600)

        # check that inventory source reports our inventory update
        custom_inventory_source.get()
        assert custom_inventory_source.last_updated is not None, "Expecting value for last_updated - %s." % custom_inventory_source
        assert custom_inventory_source.last_job_run is not None, "Expecting value for last_job_run - %s." % custom_inventory_source
        last_updated, last_job_run = custom_inventory_source.last_updated, custom_inventory_source.last_job_run

        # launch job_template and assert successful
        job_pg = custom_inventory_job_template.launch().wait_until_completed(timeout=600)
        job_pg.assert_successful()

        # check that inventory update not triggered
        custom_inventory_source.get()
        assert custom_inventory_source.last_updated == last_updated, \
            "An inventory update was unexpectedly triggered (last_updated changed) - %s." % custom_inventory_source
        assert custom_inventory_source.last_job_run == last_job_run, \
            "An inventory update was unexpectedly triggered (last_job_run changed) - %s." % custom_inventory_source

        # check that jobs ran sequentially and in the right order
        sorted_unified_jobs = [inv_update_pg, job_pg]
        confirm_unified_jobs(sorted_unified_jobs)

    @pytest.mark.github('https://github.com/ansible/tower/issues/4007', ids=['svn'], skip=True)
    @pytest.mark.parametrize('scm_type', ['git', 'hg', 'svn'])
    def test_project_update_on_launch(self, scm_type, factories):
        """Verify that two project updates are triggered by a job launch when we
        enable project update_on_launch. Job ordering should be as follows:
        * Our initial project-post should launch a project update of job_type 'check.'
        * Our JT launch should spawn two additional project updates: one of job_type
        'check' and one of job_type 'run.' Our check update should run before the job
        launch and our run update should run simultaneously with our job.
        """
        project = factories.project(scm_type=scm_type)
        playbook = 'debug.yml'
        if scm_type == 'svn':
            playbook = 'trunk/{}'.format(playbook)
        host = factories.host()
        job_template = factories.job_template(project=project, inventory=host.ds.inventory, playbook=playbook)
        project.scm_update_on_launch = True
        assert project.scm_update_on_launch
        assert project.scm_update_cache_timeout == 0

        # check the autospawned project update
        initial_project_updates = project.related.project_updates.get()
        assert initial_project_updates.count == 1, "Unexpected number of initial project updates."
        initial_project_update = initial_project_updates.results.pop()
        assert initial_project_update.job_type == "check", \
            "Unexpected job_type for our initial project update: {0}.".format(initial_project_update.job_type)

        # launch job_template and assert successful
        job_pg = job_template.launch().wait_until_completed(timeout=600)
        job_pg.assert_successful()

        # check that our new project updates are successful
        spawned_project_updates = project.related.project_updates.get(
            not__id=initial_project_update.id,
            not__launch_type='sync'  # exclude local syncs
        )
        assert spawned_project_updates.count == 1, "Unexpected number of job-spawned project updates."
        for update in spawned_project_updates.results:
            update.assert_successful()

        # check that our new project updates are of the right type
        spawned_check_updates = project.related.project_updates.get(not__id=initial_project_update.id, job_type='check')
        spawned_run_updates = project.related.project_updates.get(not__id=initial_project_update.id, job_type='run')
        assert spawned_check_updates.count == 1, "Unexpected number of spawned check project updates."
        # the local project sync may not be necessary for git
        assert spawned_run_updates.count <= 1, "Unexpected number of spawned run project updates."
        spawned_check_update = spawned_check_updates.results.pop()

        if spawned_run_updates.count:
            spawned_run_update = spawned_run_updates.results.pop()
            # check that jobs ran sequentially and in the right order
            sorted_unified_jobs = [initial_project_update, spawned_check_update, [job_pg, spawned_run_update]]
            confirm_unified_jobs(sorted_unified_jobs)

    def test_project_cache_timeout(self, factories):
        """Verify that dependent project update is NOT triggered by a job launch when we enable
        project update_on_launch and launch a job within the timeout window.
        Verify that when a job is launched AFTER the timeout window, that the dependent
        update is ran.
        """
        # set scm_update_on_launch for the project
        cache_timeout = 30
        before_update = time.time()
        project = factories.project(scm_update_on_launch=True, scm_update_cache_timeout=cache_timeout)
        window_start = time.time()
        job_template = factories.job_template(project=project)
        assert project.scm_update_on_launch is True  # sanity
        assert project.scm_update_cache_timeout == cache_timeout  # sanity
        assert project.last_updated is not None

        # check the autospawned project update
        initial_project_updates = project.related.project_updates.get()
        assert initial_project_updates.count == 1, "Unexpected number of initial project updates."
        initial_project_update = initial_project_updates.results.pop()
        assert initial_project_update.job_type == "check", \
            "Unexpected job_type for our initial project update: {0}.".format(initial_project_update.job_type)

        # launch job_template and assert successful
        job1 = job_template.launch().wait_until_completed()
        job1.assert_successful()
        assert time.time() - before_update < cache_timeout  # sanity, job was ran well inside cache window

        # check that our new project update completes successfully and is of the right type
        spawned_project_updates = project.related.project_updates.get(
            not__id=initial_project_update.id,
            not__launch_type='sync'  # exclude local project syncs
        )
        assert spawned_project_updates.count == 0, "Project not supposed to be updated during cache window."

        # check that jobs ran sequentially and in the right order
        sorted_unified_jobs = [initial_project_update, job1]
        confirm_unified_jobs(sorted_unified_jobs)

        # assure that the cache timeout has passed, but give credit for the
        # time that has already passed without an update happening, to keep test fast
        utils.logged_sleep(cache_timeout - (time.time() - window_start))

        # launch job_template while the project cache is now stale
        job2 = job_template.launch().wait_until_completed()
        job2.assert_successful()

        spawned_project_updates = project.related.project_updates.get(
            not__id=initial_project_update.id,
            not__launch_type='sync'  # exclude local project syncs
        )
        assert spawned_project_updates.count == 1, "Project passed cache window, needed to update once."
        spawned_project_update = spawned_project_updates.results.pop()
        spawned_project_update.assert_successful()
        assert spawned_project_update.job_type == 'check'
        confirm_unified_jobs([initial_project_update, job1, spawned_project_update, job2])

    # Skip for openshift because of Github Issue: https://github.com/ansible/tower-qa/issues/2591
    def test_inventory_and_project(self, skip_if_openshift, factories, custom_inventory_source):
        """Verify that two project updates and an inventory update get triggered
        by a job launch when we enable update_on_launch for both our project and
        custom group. Job ordering should be as follows:
        * Our initial project-post should launch a project update of job_type 'check.'
        * Our 'check' project update and inventory update are allowed to run
        simultaneously and collectively block our job run.
        * Our job should run simultaneously with our 'run' project update.
        """
        # set scm_update_on_launch for the project
        custom_inventory_job_template = factories.job_template(inventory=custom_inventory_source.related.inventory.get())
        project = custom_inventory_job_template.related.project.get()
        project.patch(scm_update_on_launch=True)
        assert project.scm_update_on_launch

        # set update_on_launch for the inventory
        custom_inventory_source.patch(update_on_launch=True)
        assert custom_inventory_source.update_on_launch

        # check the autospawned project update
        initial_project_updates = project.related.project_updates.get()
        assert initial_project_updates.count == 1, "Unexpected number of initial project updates."
        initial_project_update = initial_project_updates.results.pop()
        assert initial_project_update.job_type == "check", \
            "Unexpected job_type for our initial project update: {0}.".format(initial_project_update.job_type)

        # launch job_template and assert successful
        job_pg = custom_inventory_job_template.launch().wait_until_completed(timeout=600)
        job_pg.assert_successful()

        # check our new project updates are successful
        spawned_project_updates = project.related.project_updates.get(
            not__id=initial_project_update.id,
            not__launch_type='sync'  # exclude local sync
        )
        assert spawned_project_updates.count == 1, "Unexpected number of final updates ({0}).".format(spawned_project_updates.count)
        for update in spawned_project_updates.results:
            update.assert_successful()

        # check that our new project updates are of the right type
        spawned_check_updates = project.related.project_updates.get(not__id=initial_project_update.id, job_type='check')
        assert spawned_check_updates.count == 1, "Expected one new project update of job_type 'check.'"
        spawned_check_update = spawned_check_updates.results.pop()

        # check that inventory update was triggered and is successful
        custom_inventory_source.get()
        assert custom_inventory_source.last_updated is not None, "Expecting value for last_updated - %s." % custom_inventory_source
        assert custom_inventory_source.last_job_run is not None, "Expecting value for last_job_run - %s." % custom_inventory_source
        custom_inventory_source.assert_successful()
        inv_update_pg = custom_inventory_source.related.inventory_updates.get().results.pop()
        custom_inventory_source.assert_successful()

        # check that jobs ran sequentially and in the right order
        sorted_unified_jobs = [initial_project_update, [spawned_check_update, inv_update_pg], job_pg]
        confirm_unified_jobs(sorted_unified_jobs)


@pytest.mark.usefixtures('authtoken')
class Test_Cascade_Fail_Dependent_Jobs(APITest):

    def test_canceling_inventory_update_should_cascade_cancel_dependent_job(self, factories, sleeping_inventory_script):
        inv_source = factories.inventory_source(source_script=sleeping_inventory_script, update_on_launch=True)
        assert inv_source.source_script == sleeping_inventory_script.id
        jt = factories.job_template(inventory=inv_source.ds.inventory)

        job = jt.launch()

        inv_update = inv_source.wait_until_started().related.current_update.get()
        inv_update.cancel().wait_until_completed()

        assert inv_update.status == 'canceled'
        assert inv_update.failed
        assert inv_source.get().status == 'canceled'
        assert inv_source.last_job_failed
        assert inv_source.last_update_failed

        assert job.wait_until_completed().status == "canceled"
        assert job.failed

        check_chain_canceled_job_explanation(inv_update, [job])

    def test_cancel_inventory_update_with_multiple_inventory_updates(self, factories, sleeping_inventory_script):
        """Tests that if you cancel an inventory update before it finishes that
        its dependent jobs fail.
        """
        inventory = factories.inventory(organization=sleeping_inventory_script.ds.organization)
        sources = [factories.inventory_source(inventory=inventory, source_script=sleeping_inventory_script,
                                                 update_on_launch=True) for _ in range(2)]
        for source in sources:
            assert not source.get().last_updated
            assert source.source_script == sleeping_inventory_script.id

        job_template = factories.job_template(inventory=inventory)
        job_pg = job_template.launch()

        update_1, update_2 = [src.wait_until_started(interval=.5,
                                                     timeout=300).related.current_update.get() for src in sources]
        update_1_started = du_parse(update_1.created)
        update_2_started = du_parse(update_2.created)

        # identify the sequence of the inventory updates and navigate to cancel_pg
        second_first = update_1_started > update_2_started
        update_page = update_2 if second_first else update_1
        assert update_page.related.cancel.get().can_cancel, \
            "Inventory update is not cancelable, it may have already completed - {}.".format(update_page.get())
        inv_1_pgs = update_1, sources[0]
        inv_2_pgs = update_2, sources[1]
        first_inv_update_pg, first_inv_source_pg = inv_2_pgs if second_first else inv_1_pgs
        second_inv_update_pg, second_inv_source_pg = inv_1_pgs if second_first else inv_2_pgs

        # cancel the first inventory update
        first_inv_update_pg.related.cancel.post()

        assert first_inv_update_pg.wait_until_completed().status == 'canceled'

        # assert launched job failed
        assert job_pg.wait_until_completed().status == "canceled", "Unexpected job status - %s." % job_pg

        assert first_inv_source_pg.get().status == 'canceled', \
            "Did not cancel job as expected (expected status:canceled) - %s." % first_inv_source_pg

        # assert second inventory update and source successful
        assert second_inv_update_pg.wait_until_completed().status == 'canceled', \
            "Did not cancel job as expected (expected status:canceled) - %s." % second_inv_update_pg

        # assess job_explanation
        check_chain_canceled_job_explanation(first_inv_update_pg, [job_pg, second_inv_update_pg])

    def test_canceling_project_update_should_cascade_cancel_dependent_job(self, factories):
        project = factories.project(scm_type='git', scm_url='https://github.com/ansible/ansible.git',
                                       scm_delete_on_update=True, scm_update_on_launch=True)
        jt = factories.job_template(project=project, playbook='test/integration/targets/unicode/unicode.yml')

        job = jt.launch()

        utils.poll_until(lambda: project.related.project_updates.get(launch_type='dependency').count == 1, interval=.1,
                         timeout=30)
        project_update = project.related.project_updates.get(launch_type='dependency').results.pop()
        project_update.cancel().wait_until_completed()

        assert project_update.status == 'canceled'
        assert project_update.failed
        assert project.get().status == 'canceled'
        assert project.last_job_failed
        assert project.last_update_failed

        assert job.wait_until_completed().status == 'canceled'
        assert job.failed

        check_chain_canceled_job_explanation(project_update, [job])

    def test_canceling_project_update_should_cascade_cancel_inventory_update_and_dependent_job(self, factories, sleeping_inventory_script):
        project = factories.project(scm_type='git', scm_url='https://github.com/ansible/ansible.git',
                                       scm_delete_on_update=True, scm_update_on_launch=True)
        inv_source = factories.inventory_source(source_script=sleeping_inventory_script, update_on_launch=True)
        assert inv_source.source_script == sleeping_inventory_script.id
        jt = factories.job_template(project=project, inventory=inv_source.ds.inventory,
                                       playbook='test/integration/targets/unicode/unicode.yml')

        job = jt.launch()

        utils.poll_until(lambda: project.related.project_updates.get(launch_type='dependency').count == 1, interval=.1,
                         timeout=30)
        utils.poll_until(lambda: inv_source.related.inventory_updates.get().count == 1, interval=.1, timeout=30)
        project_update = project.related.project_updates.get(launch_type='dependency').results.pop()
        project_update.cancel().wait_until_completed()

        assert project_update.status == 'canceled'
        assert project_update.failed
        assert project.get().status == 'canceled'
        assert project.last_job_failed
        assert project.last_update_failed

        inv_update = inv_source.wait_until_completed().related.last_update.get()
        assert inv_update.status == "canceled"
        assert inv_update.failed
        assert inv_source.get().status == "canceled"
        assert inv_source.last_job_failed
        assert inv_source.last_update_failed

        assert job.wait_until_completed().status == "canceled"
        assert job.failed

        check_chain_canceled_job_explanation(project_update, [job, inv_update])

    def test_canceling_inventory_update_should_cascade_cancel_project_update_and_dependent_job(self, factories,
            sleeping_inventory_script):
        project = factories.project(scm_type='git', scm_url='https://github.com/ansible/ansible.git',
                                       scm_delete_on_update=True, scm_update_on_launch=True)
        inv_source = factories.inventory_source(source_script=sleeping_inventory_script, update_on_launch=True)
        assert inv_source.source_script == sleeping_inventory_script.id
        jt = factories.job_template(project=project, inventory=inv_source.ds.inventory,
                                       playbook='test/integration/targets/unicode/unicode.yml')

        job = jt.launch()

        utils.poll_until(lambda: project.related.project_updates.get(launch_type='dependency').count == 1, interval=.1,
                                                                     timeout=30)
        utils.poll_until(lambda: inv_source.related.inventory_updates.get().count == 1, interval=.1, timeout=30)
        inv_update = inv_source.related.inventory_updates.get().results.pop()
        inv_update.cancel().wait_until_completed()

        assert inv_update.status == 'canceled'
        assert inv_update.failed
        assert inv_source.get().status == "canceled"
        assert inv_source.last_job_failed
        assert inv_source.last_update_failed

        project_update = project.related.project_updates.get(launch_type='dependency').results.pop() \
                                                        .wait_until_completed()
        assert project_update.status == 'canceled'
        assert project_update.failed
        assert project.get().status == 'canceled'
        assert project.last_job_failed
        assert project.last_update_failed

        assert job.wait_until_completed().status == 'canceled'
        assert job.failed

        check_chain_canceled_job_explanation(inv_update, [job, project_update])

    def test_failed_inventory_update_should_cascade_fail_dependent_job(self, factories):
        aws_cred = factories.credential(kind='aws', inputs=dict(username='fake', password='fake'))
        inv_source = factories.inventory_source(source='ec2', credential=aws_cred, update_on_launch=True)
        jt = factories.job_template(inventory=inv_source.ds.inventory)
        job = jt.launch().wait_until_completed()

        inv_updates = inv_source.related.inventory_updates.get()
        assert inv_updates.count == 1
        inv_update = inv_updates.results.pop()

        assert job.status == 'failed'
        assert job.failed
        assert job.job_explanation == 'Previous Task Failed: {"job_type": "inventory_update", "job_name": "%s", "job_id": "%s"}' \
                                      % (inv_update.name, inv_update.id)
        assert jt.get().status == 'failed'
        assert jt.last_job_failed

        assert inv_update.status == 'failed'
        assert inv_update.failed
        assert inv_source.get().status == 'failed'
        assert inv_source.last_job_failed

    def test_failed_project_update_should_cascade_fail_dependent_job(self, factories):
        jt = factories.job_template()
        project = jt.ds.project
        project.scm_url = "will_fail"
        failed_update = project.get_related('last_update')  # changing details created new update
        failed_update.wait_until_completed()
        job = jt.launch().wait_until_completed()

        job.assert_status('error')
        assert job.failed
        assert job.job_explanation == (
            'The project revision for this job template is unknown due to a failed update.'
        )
        assert jt.get().status == 'failed'
        assert jt.last_job_failed
