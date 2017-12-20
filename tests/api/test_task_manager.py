import json

from towerkit import utils
from dateutil.parser import parse as du_parse
import fauxfactory
import pytest

from tests.api import Base_Api_Test


@pytest.fixture(scope="function")
def another_custom_group(request, authtoken, api_groups_pg, inventory, inventory_script):
    payload = dict(name="custom-group-%s" % fauxfactory.gen_alphanumeric(),
                   description="Custom Group %s" % fauxfactory.gen_utf8(),
                   inventory=inventory.id,
                   variables=json.dumps(dict(my_group_variable=True)))
    obj = api_groups_pg.post(payload)
    request.addfinalizer(obj.delete)

    inv_source = obj.get_related('inventory_source')
    inv_source.patch(source='custom',
                     source_script=inventory_script.id)
    return obj


@pytest.fixture(scope="function")
def cloud_inventory_job_template(job_template, cloud_group):
    # Substitute in no-op playbook that does not attempt to connect to host
    job_template.patch(playbook='debug.yml', inventory=cloud_group.inventory)
    return job_template


@pytest.fixture(scope="function")
def custom_inventory_job_template(job_template, custom_group):
    job_template.patch(inventory=custom_group.inventory)
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
        assert chain_job.job_explanation.startswith(u'Previous Task Canceled:'), \
            "Unexpected job_explanation: %s." % chain_job.job_explanation
        try:
            job_explanation = json.loads(chain_job.job_explanation[24:])
        except Exception:
            pytest.fail("job_explanation not stored as JSON data: %s." % chain_job.job_explanation)
        assert job_explanation['job_type'] == canceled_job.type
        assert job_explanation['job_name'] == canceled_job.name
        assert job_explanation['job_id'] == str(canceled_job.id)


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Sequential_Jobs(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

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

    def test_workflow_job_template(self, workflow_job_template, factories):
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
        jt = factories.job_template(allow_simultaneous=True)
        factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)

        # launch two workflow jobs
        ordered_wfjs = [wfjt.launch() for _ in range(2)]
        wait_for_jobs_to_finish(ordered_wfjs)

        wfj1_nodes, wfj2_nodes = [wfj.related.workflow_nodes.get() for wfj in ordered_wfjs]
        ordered_node_jobs = [wfj_nodes.results.pop().related.job.get() for wfj_nodes in (wfj1_nodes, wfj2_nodes)]

        # confirm unified jobs ran as expected
        check_overlapping_jobs(ordered_wfjs)
        check_overlapping_jobs(ordered_node_jobs)

    def test_sequential_ad_hoc_commands(self, request, v1):
        """Launch three ad hoc commands on the same inventory. Check that:
        * No commands ran simultaneously.
        * Commands ran in the order spawned.
        """
        host = v1.hosts.create()
        request.addfinalizer(host.teardown)

        # lauch three commands
        ahc1 = v1.ad_hoc_commands.create(module_name='shell', module_args='true', inventory=host.ds.inventory)
        ahc2 = v1.ad_hoc_commands.create(module_name='shell', module_args='true', inventory=host.ds.inventory)
        ahc3 = v1.ad_hoc_commands.create(module_name='shell', module_args='true', inventory=host.ds.inventory)
        ordered_commands = [ahc1, ahc2, ahc3]

        # confirm unified jobs ran as expected
        confirm_unified_jobs(ordered_commands)

    def test_simultaneous_ad_hoc_commands(self, request, v1):
        """Launch two ad hoc commands on different inventories. Check that
        our commands run simultaneously.
        """
        host1 = v1.hosts.create()
        request.addfinalizer(host1.teardown)
        host2 = v1.hosts.create()
        request.addfinalizer(host2.teardown)

        # launch two commands
        ahc1 = v1.ad_hoc_commands.create(module_name='shell', module_args='sleep 5s', inventory=host1.ds.inventory)
        ahc2 = v1.ad_hoc_commands.create(module_name='shell', module_args='sleep 5s', inventory=host2.ds.inventory)
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

    def test_related_inventory_update_with_job(self, job_template, custom_group):
        """If an inventory is used in a JT and has a group that allows for updates, then spawned
        jobs and updates must run sequentially. Check that:
        * Spawned unified jobs run sequentially.
        * Unified jobs run in the order launched.
        """
        inv_source = custom_group.related.inventory_source.get()

        # launch jobs
        update = inv_source.update()
        job = job_template.launch()
        sorted_unified_jobs = [update, job]

        # confirm unified jobs ran as expected
        confirm_unified_jobs(sorted_unified_jobs)

    def test_related_inventory_update_with_command(self, request, v1):
        """If an inventory is used in a command and has a group that allows for updates, then spawned
        commands and updates must run sequentially. Check that:
        * Spawned unified jobs run sequentially.
        * Unified jobs run in the order launched.
        """
        inventory_script = v1.inventory_scripts.create()
        request.addfinalizer(inventory_script.teardown)
        custom_group = v1.groups.create(inventory_script=inventory_script)
        request.addfinalizer(custom_group.teardown)

        # launch unified jobs
        update = custom_group.related.inventory_source.get().update()
        command = v1.ad_hoc_commands.create(module_name='shell', module_args='true', inventory=custom_group.ds.inventory)
        sorted_unified_jobs = [update, command]

        # confirm unified jobs ran as expected
        confirm_unified_jobs(sorted_unified_jobs)


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Autospawned_Jobs(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/7834')
    def test_v1_inventory(self, cloud_inventory_job_template, cloud_group):
        """Verify that an inventory update is triggered by our job launch. Job ordering
        should be as follows:
        * Inventory update should run first.
        * Job should run after the completion of our inventory update.
        """
        # set update_on_launch
        inv_src_pg = cloud_group.get_related('inventory_source')
        inv_src_pg.patch(update_on_launch=True)
        assert inv_src_pg.update_cache_timeout == 0
        assert inv_src_pg.last_updated is None, \
            "Not expecting our inventory source to have been updated - %s." % inv_src_pg

        # launch job_template and assert successful
        job_pg = cloud_inventory_job_template.launch_job().wait_until_completed()
        assert job_pg.is_successful, "Job unsuccessful - %s." % job_pg

        # check that inventory update triggered
        inv_src_pg.get()
        assert inv_src_pg.last_updated is not None, "Expecting value for last_updated - %s." % inv_src_pg
        assert inv_src_pg.last_job_run is not None, "Expecting value for last_job_run - %s." % inv_src_pg

        # check that inventory update and source are successful
        inv_update = inv_src_pg.get_related('last_update')
        assert inv_update.is_successful, "Last update unsuccessful - %s." % inv_update
        assert inv_src_pg.is_successful, "Inventory source unsuccessful - %s." % inv_src_pg

        # check that jobs ran sequentially and in the right order
        sorted_unified_jobs = [inv_update, job_pg]
        confirm_unified_jobs(sorted_unified_jobs)

    def test_v2_inventory(self, factories):
        """Verify that an inventory update is triggered by our job launch. Job ordering
        should be as follows:
        * Inventory update should run first.
        * Job should run after the completion of our inventory update.
        """
        inv_source = factories.v2_inventory_source(update_on_launch=True)
        assert not inv_source.last_updated
        assert not inv_source.last_job_run

        jt = factories.v2_job_template(inventory=inv_source.ds.inventory, playbook='debug.yml')
        job = jt.launch().wait_until_completed()
        assert job.is_successful

        inv_update = inv_source.get().related.last_update.get()
        assert inv_source.get().last_updated
        assert inv_source.last_job_run
        assert inv_update.is_successful
        assert inv_source.is_successful

        # check that jobs ran sequentially and in the right order
        sorted_unified_jobs = [inv_update, job]
        confirm_unified_jobs(sorted_unified_jobs)

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/7834')
    def test_inventory_multiple(self, job_template, aws_inventory_source, gce_inventory_source):
        """Verify that multiple inventory updates are triggered by job launch. Job ordering
        should be as follows:
        * AWS and GCE inventory updates should run simultaneously.
        * Upon completion of both inventory imports, job should run.
        """
        # set update_on_launch
        aws_inventory_source.patch(update_on_launch=True)
        gce_inventory_source.patch(update_on_launch=True)

        # check inventory sources
        for inv_source in (aws_inventory_source, gce_inventory_source):
            assert inv_source.update_on_launch
            assert inv_source.update_cache_timeout == 0
            assert inv_source.last_updated is None, \
                "Not expecting inventory source to have been updated - %s." % inv_source

        # sanity check: cloud groups should be in the same inventory
        assert gce_inventory_source.inventory == aws_inventory_source.inventory, \
            "The inventory differs between the two inventory sources."

        # update job_template to cloud inventory
        # substitute in no-op playbook that does not attempt to connect to host
        job_template.patch(inventory=aws_inventory_source.inventory, playbook='debug.yml')

        # launch job_template and assert successful
        job_pg = job_template.launch_job().wait_until_completed(timeout=50 * 10)
        assert job_pg.is_successful, "Job unsuccessful - %s." % job_pg

        # check that inventory updates were triggered
        for inv_source in (aws_inventory_source, gce_inventory_source):
            inv_source.get()
            assert inv_source.last_updated is not None, \
                "Expecting value for inventory_source last_updated - %s." % inv_source
            assert inv_source.last_job_run is not None, \
                "Expecting value for inventory_source last_job_run - %s." % inv_source

        # check that inventory updates were successful
        aws_update, gce_update = aws_inventory_source.related.last_update.get(), gce_inventory_source.related.last_update.get()
        assert aws_update.is_successful, "aws_inventory_source -> last_update unsuccessful - %s." % aws_update
        assert aws_inventory_source.is_successful, "Inventory source unsuccessful - %s." % aws_inventory_source
        assert gce_update.is_successful, "gce_inventory_source -> last_update unsuccessful - %s." % gce_update
        assert gce_inventory_source.is_successful, "Inventory source unsuccessful - %s." % gce_inventory_source

        # check that jobs ran sequentially and in the right order
        sorted_unified_jobs = [[aws_update, gce_update], job_pg]
        confirm_unified_jobs(sorted_unified_jobs)

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/7834')
    def test_inventory_cache_timeout(self, custom_inventory_job_template, custom_inventory_source):
        """Verify that an inventory update is not triggered by the job launch if the
        cache is still valid. Job ordering should be as follows:
        * Manually launched inventory update.
        * Job upon completion of inventory update.
        """
        # set update_on_launch and a five minute update_cache_timeout
        cache_timeout = 60 * 5
        custom_inventory_source.patch(update_on_launch=True, update_cache_timeout=cache_timeout)
        assert custom_inventory_source.update_cache_timeout == cache_timeout
        assert custom_inventory_source.last_updated is None, \
            "Not expecting inventory source to have been updated - %s." % custom_inventory_source

        # launch inventory update and wait for completion
        inv_update_pg = custom_inventory_job_template.launch_job().wait_until_completed(timeout=50 * 10)

        # check that inventory source reports our inventory update
        custom_inventory_source.get()
        assert custom_inventory_source.last_updated is not None, "Expecting value for last_updated - %s." % custom_inventory_source
        assert custom_inventory_source.last_job_run is not None, "Expecting value for last_job_run - %s." % custom_inventory_source
        last_updated, last_job_run = custom_inventory_source.last_updated, custom_inventory_source.last_job_run

        # launch job_template and assert successful
        job_pg = custom_inventory_job_template.launch_job().wait_until_completed(timeout=50 * 10)
        assert job_pg.is_successful, "Job unsuccessful - %s." % job_pg

        # check that inventory update not triggered
        custom_inventory_source.get()
        assert custom_inventory_source.last_updated == last_updated, \
            "An inventory update was unexpectedly triggered (last_updated changed) - %s." % custom_inventory_source
        assert custom_inventory_source.last_job_run == last_job_run, \
            "An inventory update was unexpectedly triggered (last_job_run changed) - %s." % custom_inventory_source

        # check that jobs ran sequentially and in the right order
        sorted_unified_jobs = [inv_update_pg, job_pg]
        confirm_unified_jobs(sorted_unified_jobs)

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/7834')
    @pytest.mark.parametrize('project', ['project_ansible_playbooks_git', 'project_ansible_helloworld_hg'])
    def test_project_update_on_launch(self, request, factories, project):
        """Verify that two project updates are triggered by a job launch when we
        enable project update_on_launch. Job ordering should be as follows:
        * Our initial project-post should launch a project update of job_type 'check.'
        * Our JT launch should spawn two additional project updates: one of job_type
        'check' and one of job_type 'run.' Our check update should run before the job
        launch and our run update should run simultaneously with our job.
        """
        project = request.getfixturevalue(project)
        host = factories.host()
        job_template = factories.job_template(project=project, inventory=host.ds.inventory)
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
        job_pg = job_template.launch_job().wait_until_completed(timeout=50 * 10)
        assert job_pg.is_successful, "Job unsuccessful - %s." % job_pg

        # check that our new project updates are successful
        spawned_project_updates = project.related.project_updates.get(not__id=initial_project_update.id)
        assert spawned_project_updates.count == 2, "Unexpected number of job-spawned project updates."
        for update in spawned_project_updates.results:
            assert update.is_successful, "Project update unsuccessful - %s." % update

        # check that our new project updates are of the right type
        spawned_check_updates = project.related.project_updates.get(not__id=initial_project_update.id, job_type='check')
        spawned_run_updates = project.related.project_updates.get(not__id=initial_project_update.id, job_type='run')
        assert spawned_check_updates.count == 1, "Unexpected number of spawned check project updates."
        assert spawned_run_updates.count == 1, "Unexpected number of spawned run project updates."
        spawned_check_update, spawned_run_update = spawned_check_updates.results.pop(), spawned_run_updates.results.pop()

        # check that jobs ran sequentially and in the right order
        sorted_unified_jobs = [initial_project_update, spawned_check_update, [job_pg, spawned_run_update]]
        confirm_unified_jobs(sorted_unified_jobs)

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/7834')
    def test_project_cache_timeout(self, project_ansible_playbooks_git, job_template_ansible_playbooks_git):
        """Verify that one project update is triggered by a job launch when we enable
        project update_on_launch and launch a job within the timeout window. Job ordering
        should be as follows:
        * Our initial project-post should launch a project update of job_type 'check.'
        * Our JT launch should spawn an additional project update of job_type 'run.' Our
        run update should run simultaneously with our job.
        """
        # set scm_update_on_launch for the project
        cache_timeout = 60 * 5
        project_ansible_playbooks_git.patch(scm_update_on_launch=True,
                                            scm_update_cache_timeout=cache_timeout)
        assert project_ansible_playbooks_git.scm_update_on_launch
        assert project_ansible_playbooks_git.scm_update_cache_timeout == cache_timeout
        assert project_ansible_playbooks_git.last_updated is not None

        # check the autospawned project update
        initial_project_updates = project_ansible_playbooks_git.related.project_updates.get()
        assert initial_project_updates.count == 1, "Unexpected number of initial project updates."
        initial_project_update = initial_project_updates.results.pop()
        assert initial_project_update.job_type == "check", \
            "Unexpected job_type for our initial project update: {0}.".format(initial_project_update.job_type)

        # launch job_template and assert successful
        job_pg = job_template_ansible_playbooks_git.launch_job().wait_until_completed(timeout=50 * 10)
        assert job_pg.is_successful, "Job unsuccessful - %s." % job_pg

        # check that our new project update completes successfully and is of the right type
        spawned_project_updates = project_ansible_playbooks_git.related.project_updates.get(not__id=initial_project_update.id)
        assert spawned_project_updates.count == 1, "Unexpected number of final updates."
        spawned_project_update = spawned_project_updates.results.pop()
        assert spawned_project_update.is_successful, "Project update unsuccessful."
        assert spawned_project_update.job_type == 'run', "Expected one new project update of job_type 'run.'"

        # check that jobs ran sequentially and in the right order
        sorted_unified_jobs = [initial_project_update, [job_pg, spawned_project_update]]
        confirm_unified_jobs(sorted_unified_jobs)

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/7834')
    def test_inventory_and_project(self, custom_inventory_job_template, custom_inventory_source):
        """Verify that two project updates and an inventory update get triggered
        by a job launch when we enable update_on_launch for both our project and
        custom group. Job ordering should be as follows:
        * Our initial project-post should launch a project update of job_type 'check.'
        * Our 'check' project update and inventory update are allowed to run
        simultaneously and collectively block our job run.
        * Our job should run simultaneously with our 'run' project update.
        """
        # set scm_update_on_launch for the project
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
        job_pg = custom_inventory_job_template.launch_job().wait_until_completed(timeout=50 * 10)
        assert job_pg.is_successful, "Job unsuccessful - %s." % job_pg

        # check our new project updates are successful
        spawned_project_updates = project.related.project_updates.get(not__id=initial_project_update.id)
        assert spawned_project_updates.count == 2, "Unexpected number of final updates ({0}).".format(spawned_project_updates.count)
        for update in spawned_project_updates.results:
            assert update.is_successful, "Project update unsuccessful - %s." % update

        # check that our new project updates are of the right type
        spawned_check_updates = project.related.project_updates.get(not__id=initial_project_update.id, job_type='check')
        spawned_run_updates = project.related.project_updates.get(not__id=initial_project_update.id, job_type='run')
        assert spawned_check_updates.count == 1, "Expected one new project update of job_type 'check.'"
        assert spawned_run_updates.count == 1, "Expected one new project update of job_type 'run.'"
        spawned_check_update, spawned_run_update = spawned_check_updates.results.pop(), spawned_run_updates.results.pop()

        # check that inventory update was triggered and is successful
        custom_inventory_source.get()
        assert custom_inventory_source.last_updated is not None, "Expecting value for last_updated - %s." % custom_inventory_source
        assert custom_inventory_source.last_job_run is not None, "Expecting value for last_job_run - %s." % custom_inventory_source
        assert custom_inventory_source.is_successful, "Inventory source unsuccessful - {0}.".format(custom_inventory_source)
        inv_update_pg = custom_inventory_source.related.inventory_updates.get().results.pop()
        assert custom_inventory_source.is_successful, "Inventory update unsuccessful - {0}.".format(inv_update_pg)

        # check that jobs ran sequentially and in the right order
        sorted_unified_jobs = [initial_project_update, [spawned_check_update, inv_update_pg], [job_pg, spawned_run_update]]
        confirm_unified_jobs(sorted_unified_jobs)


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Cascade_Fail_Dependent_Jobs(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    @pytest.fixture
    def sleeping_inventory_script(self, factories):
        source_script = """#!/usr/bin/env python
import json, time
time.sleep(30)
inventory = dict()
print json.dumps(inventory)
"""
        return factories.v2_inventory_script(script=source_script)

    def test_canceling_inventory_update_should_cascade_cancel_dependent_job(self, factories, sleeping_inventory_script):
        inv_source = factories.v2_inventory_source(inventory_script=sleeping_inventory_script, update_on_launch=True)
        jt = factories.v2_job_template(inventory=inv_source.ds.inventory)

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

    @pytest.mark.fixture_args(source_script="""#!/usr/bin/env python
import json, time
time.sleep(30)
inventory = dict()
print json.dumps(inventory)
""")
    def test_cancel_inventory_update_with_multiple_inventory_updates(self, job_template, custom_group, another_custom_group):
        """Tests that if you cancel an inventory update before it finishes that
        its dependent jobs fail.
        """
        inv_source_pg = custom_group.get_related('inventory_source')
        inv_source_pg.patch(update_on_launch=True)
        another_inv_source_pg = another_custom_group.get_related('inventory_source')
        another_inv_source_pg.patch(update_on_launch=True)

        assert not inv_source_pg.last_updated, "inv_source_pg unexpectedly updated."
        assert not another_inv_source_pg.last_updated, "another_inv_source_pg unexpectedly updated."

        # launch job
        job_pg = job_template.launch()

        # wait for the inventory sources to start
        inv_update_pg = inv_source_pg.wait_until_started(interval=.5).get_related('current_update')
        another_inv_update_pg = another_inv_source_pg.wait_until_started(interval=.5).get_related('current_update')
        inv_update_pg_started = du_parse(inv_update_pg.created)
        another_inv_update_pg_started = du_parse(another_inv_update_pg.created)

        # identify the sequence of the inventory updates and navigate to cancel_pg
        another = inv_update_pg_started > another_inv_update_pg_started
        update_page = another_inv_update_pg if another else inv_update_pg
        assert update_page.related.cancel.get().can_cancel, \
            "Inventory update is not cancellable, it may have already completed - %s." % update_page.get()
        inv_pgs = inv_update_pg, inv_source_pg
        another_pgs = another_inv_update_pg, another_inv_source_pg
        first_inv_update_pg, first_inv_source_pg = another_pgs if another else inv_pgs
        second_inv_update_pg, second_inv_source_pg = inv_pgs if another else another_pgs

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
        project = factories.v2_project(scm_type='git', scm_url='https://github.com/ansible/ansible.git',
                                       scm_delete_on_update=True, scm_update_on_launch=True)
        jt = factories.v2_job_template(project=project, playbook='test/integration/targets/unicode/unicode.yml')

        job = jt.launch()

        utils.poll_until(lambda: project.related.project_updates.get(launch_type='dependency').count == 1, interval=.1,
                                                                     timeout=30)
        project_update = project.related.project_updates.get(launch_type='dependency').results.pop()
        project_update.cancel().wait_until_completed()

        assert project.get().status == 'canceled'
        assert project.last_job_failed
        assert project.last_update_failed
        assert project_update.status == 'canceled'
        assert project_update.failed

        assert job.wait_until_completed().status == 'canceled'
        assert job.failed

        check_chain_canceled_job_explanation(project_update, [job])

    def test_canceling_project_update_should_cascade_cancel_inventory_update_and_dependent_job(self, factories, sleeping_inventory_script):
        project = factories.v2_project(scm_type='git', scm_url='https://github.com/ansible/ansible.git',
                                       scm_delete_on_update=True, scm_update_on_launch=True)
        inv_source = factories.v2_inventory_source(inventory_script=sleeping_inventory_script, update_on_launch=True)
        jt = factories.v2_job_template(project=project, inventory=inv_source.ds.inventory,
                                       playbook='test/integration/targets/unicode/unicode.yml')

        job = jt.launch()

        utils.poll_until(lambda: project.related.project_updates.get(launch_type='dependency').count == 1, interval=.1,
                                                                     timeout=30)
        utils.poll_until(lambda: inv_source.related.inventory_updates.get().count == 1, interval=.1, timeout=30)
        project_update = project.related.project_updates.get(launch_type='dependency').results.pop()
        project_update.cancel().wait_until_completed()

        assert project.get().status == 'canceled'
        assert project.last_job_failed
        assert project.last_update_failed
        assert project_update.status == 'canceled'
        assert project_update.failed

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
        project = factories.v2_project(scm_type='git', scm_url='https://github.com/ansible/ansible.git',
                                       scm_delete_on_update=True, scm_update_on_launch=True)
        inv_source = factories.v2_inventory_source(inventory_script=sleeping_inventory_script, update_on_launch=True)
        jt = factories.v2_job_template(project=project, inventory=inv_source.ds.inventory,
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
        aws_cred = factories.v2_credential(kind='aws', inputs=dict(username='fake', password='fake'))
        inv_source = factories.v2_inventory_source(source='ec2', credential=aws_cred, update_on_launch=True)
        jt = factories.v2_job_template(inventory=inv_source.ds.inventory)
        job = jt.launch().wait_until_completed()

        inv_updates = inv_source.related.inventory_updates.get()
        assert inv_updates.count == 1
        inv_update = inv_updates.results.pop()

        assert job.status == 'failed'
        assert job.failed
        assert job.job_explanation == 'Previous Task Failed: {"job_type": "inventory_update", "job_name": "%s", "job_id": "%s"}' \
                                      % (inv_source.ds.inventory.name, inv_update.id)
        assert jt.get().status == 'failed'
        assert jt.last_job_failed

        assert inv_update.status == 'failed'
        assert inv_update.failed
        assert inv_source.get().status == 'failed'
        assert inv_source.last_job_failed

    def test_failed_project_update_should_cascade_fail_dependent_job(self, factories):
        jt = factories.v2_job_template()
        project = jt.ds.project
        project.scm_url = "will_fail"
        job = jt.launch().wait_until_completed()
        sync_update = project.related.project_updates.get(launch_type='sync').results.pop()

        assert job.status == 'error'
        assert job.failed
        assert job.job_explanation == 'Previous Task Failed: {"job_type": "project_update", "job_name": "%s", "job_id": "%s"}' \
                                      % (project.name, sync_update.id)
        assert jt.get().status == 'failed'
        assert jt.last_job_failed

        assert sync_update.status == 'failed'
        assert sync_update.failed

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/7797')
    def test_canceling_job_should_cascade_cancel_sync_project_update(self, factories):
        project = factories.v2_project(scm_type='git', scm_url='https://github.com/ansible/ansible.git',
                                       scm_delete_on_update=True, scm_update_on_launch=True)
        jt = factories.v2_job_template(project=project, playbook='test/integration/targets/unicode/unicode.yml')

        job = jt.launch().cancel().wait_until_completed()

        assert project.wait_until_completed().status == 'canceled'
        assert project.last_job_failed
        assert project.last_update_failed

        project_update = job.get().related.project_update.get()
        assert project_update.launch_type == 'sync'
        assert project_update.status == 'canceled'
        assert project_update.job_explanation == 'Previous Task Canceled: {"job_type": "%s", "job_name": "%s", "job_id": "%s"}' \
                                                 % (job.type, job.name, job.id)
        assert project_update.failed

        assert job.get().status == 'canceled'
        assert job.failed
        assert job.job_explanation == ""
