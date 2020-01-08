import random
import six
import threading

from awxkit import utils
import pytest

from tests.lib.helpers import openshift_utils
from tests.api import APITest


@pytest.mark.serial
@pytest.mark.usefixtures('authtoken', 'skip_if_not_cluster')
class TestExecutionNodeAssignment(APITest):

    MAX_JOBS_PER_INSTANCE = 3

    @pytest.fixture(autouse=True, scope='class')
    def prepare_openshift_environment(self, is_docker):
        if not is_docker:
            return
        else:
            openshift_utils.prep_environment()

    @pytest.fixture
    def tower_ig_instances(self, tower_instance_group):
        return tower_instance_group.related.instances.get(order_by='hostname').results

    def find_num_jobs(self, instances):
        # find number of jobs to distribute among a set of instances
        return self.MAX_JOBS_PER_INSTANCE * len(instances)

    def find_ig_overflow_jobs(self, ig, uj_impact):
        # find number of jobs such that a single IG is put over capacity
        instances = ig.related.instances.get().results
        capacity = sum([instance.capacity for instance in instances])
        if any([uj_impact > instance.capacity for instance in instances]):
            raise RuntimeError('Method not valid for cases where jobs exceed instance capacity')
        return capacity // uj_impact + 1

    @pytest.fixture
    def largest_capacity(self, v2):
        greatest_capacity = None
        for i in v2.instances.get().results:
            if i.capacity == 0:
                raise RuntimeError(six.text_type("Capacity is 0 on node {}").format(i))
            if not greatest_capacity or i.capacity > greatest_capacity:
                greatest_capacity = i.capacity
        return greatest_capacity

    @pytest.fixture
    def jt_generator_for_consuming_given_capacity(self, v2, organization, factories):
        def fn(capacity_size):
            jt = factories.job_template(allow_simultaneous=True,
                                           forks=capacity_size,
                                           playbook='sleep.yml',
                                           extra_vars=dict(sleep_interval=60),
                                           limit="all[0]")
            [factories.host(inventory=jt.ds.inventory) for _ in range(0, capacity_size - 2)]
            return jt
        return fn

    def test_jobs_should_distribute_among_tower_instance_group_members(self, factories, tower_instance_group):
        jt = factories.job_template(allow_simultaneous=True)
        jt.add_instance_group(tower_instance_group)

        instances = tower_instance_group.related.instances.get().results
        num_jobs = self.find_num_jobs(instances)
        for _ in range(num_jobs):
            jt.launch()
        jobs = jt.related.jobs.get()
        utils.poll_until(lambda: jobs.get(status='successful').count == num_jobs, interval=5, timeout=300)

        job_execution_nodes = [job.execution_node for job in jobs.results]
        assert set(job_execution_nodes) == set([instance.hostname for instance
                                                in tower_instance_group.related.instances.get().results])

    def test_jt_with_no_instance_groups_defaults_to_tower_instance_group_instance(self, factories,
                                                                                  tower_ig_instances):
        jt = factories.job_template(allow_simultaneous=True)

        num_jobs = self.find_num_jobs(tower_ig_instances)
        for _ in range(num_jobs):
            jt.launch()
        jobs = jt.related.jobs.get()
        utils.poll_until(lambda: jobs.get(status='successful').count == num_jobs, interval=5, timeout=300)

        job_execution_nodes = [job.execution_node for job in jobs.results]
        assert set(job_execution_nodes) == set([instance.hostname for instance in tower_ig_instances])

    def test_jobs_should_distribute_among_partially_overlapping_instance_groups(self, factories, tower_ig_instances,
                                                                                reset_instance):
        ig1, ig2 = [factories.instance_group() for _ in range(2)]
        instances = random.sample(tower_ig_instances, 3)
        for instance in instances:
            reset_instance(instance)
            instance.capacity_adjustment = 0

        ig1.add_instance(instances[0])
        ig2.add_instance(instances[1])
        for ig in (ig1, ig2):
            ig.add_instance(instances[2])

        jt = factories.job_template(playbook='sleep.yml', allow_simultaneous=True,
                                       extra_vars='{"sleep_interval": 60}')
        task_impact = 2
        for _ in range(task_impact - 1):
            factories.host(inventory=jt.ds.inventory)
        for ig in (ig1, ig2):
            jt.add_instance_group(ig)

        num_jobs = self.find_ig_overflow_jobs(ig1, task_impact)
        assert num_jobs >= len(instances)
        assert all([instance.get().capacity >= task_impact for instance in instances])
        for _ in range(num_jobs):
            jt.launch()
        jobs = jt.related.jobs.get()
        utils.poll_until(lambda: len([job.execution_node for job in jobs.get().results
                         if job.execution_node != '']) == num_jobs, interval=5, timeout=300)

        jobs = jobs.get()
        assert all([job.status == 'running' for job in jobs.results])
        assert set([ig1.id, ig2.id]) == set(job.instance_group for job in jobs.results)

        job_execution_nodes = [job.execution_node for job in jobs.results]
        assert set(job_execution_nodes) == set([instance.hostname for instance in instances])

    def test_jobs_should_distribute_among_new_instance_group_members(self, factories, tower_ig_instances):
        ig = factories.instance_group()
        instances = random.sample(tower_ig_instances, 2)
        for instance in instances:
            ig.add_instance(instance)

        jt = factories.job_template(allow_simultaneous=True)
        jt.add_instance_group(ig)

        num_jobs = self.find_num_jobs(instances)
        for _ in range(num_jobs):
            jt.launch()
        jobs = jt.related.jobs.get()
        utils.poll_until(lambda: jobs.get(status='successful').count == num_jobs, interval=5, timeout=300)

        job_execution_nodes = [job.execution_node for job in jobs.results]
        assert set(job_execution_nodes) == set([instance.hostname for instance in instances])

    @pytest.mark.parametrize('resource', ['inventory', 'organization', 'both'])
    def test_ahcs_run_on_target_instance_with_resource_ig_assignment(self, factories, tower_ig_instances,
                                                                     resource):
        ig = factories.instance_group()
        instance = random.sample(tower_ig_instances, 1).pop()
        ig.add_instance(instance)
        assert ig.related.instances.get().count == 1  # test flake due to github.com/ansible/tower/issues/2772

        inv = factories.inventory()

        if resource in ('inventory', 'both'):
            inv.add_instance_group(ig)
        if resource in ('organization', 'both'):
            inv.ds.organization.add_instance_group(ig)

        ahc = factories.ad_hoc_command(inventory=inv, module_name='ping')
        ahc.wait_until_completed().assert_successful()
        assert ahc.execution_node == instance.hostname

    def test_ahcs_should_distribute_among_new_instance_group_members(self, factories, tower_ig_instances, v2):
        ig = factories.instance_group()
        instances = random.sample(tower_ig_instances, 2)
        for instance in instances:
            ig.add_instance(instance)

        num_jobs = self.find_num_jobs(instances)
        for _ in range(num_jobs):
            # inventory must be specific to each ad hoc command, otherwise
            # they will block each other from running
            inv = factories.inventory()
            host = factories.host(inventory=inv)
            inv.add_instance_group(ig)
            factories.ad_hoc_command(
                inventory=inv, module_name='command', module_args="sleep 300",
                limit=host.name
            )
        utils.poll_until(lambda: v2.ad_hoc_commands.get(status='running', instance_group=ig.id).count == num_jobs,
                         interval=5, timeout=300)

        ahcs = v2.ad_hoc_commands.get(instance_group=ig.id).results
        ahc_execution_nodes = [ahc.execution_node for ahc in ahcs]
        assert set(ahc_execution_nodes) == set([instance.hostname for instance in instances])
        for instance in instances:
            assert ahc_execution_nodes.count(instance.hostname) == self.MAX_JOBS_PER_INSTANCE

    def test_project_updates_run_on_target_instance_via_organization_ig_assignment(self, factories,
                                                                                   tower_ig_instances):
        ig = factories.instance_group()
        instance = random.sample(tower_ig_instances, 1).pop()
        ig.add_instance(instance)

        project = factories.project()
        project.ds.organization.add_instance_group(ig)

        project_update = project.update()
        project_update.wait_until_completed().assert_successful()
        assert project_update.execution_node == instance.hostname

    def test_project_updates_should_distribute_among_new_instance_group_members(self, factories,
                                                                                tower_ig_instances,
                                                                                wait_for_jobs,
                                                                                do_all_jobs_overlap):
        ig = factories.instance_group()
        instances = random.sample(tower_ig_instances, 2)
        for instance in instances:
            ig.add_instance(instance)

        projects = [factories.project(scm_delete_on_update=True,
                                         scm_url='https://github.com/ansible/ansible.git') for _ in range(2)]
        project_updates = []
        for project in projects:
            project.ds.organization.add_instance_group(ig)
            project_updates.append(project.update())

        wait_for_jobs(project_updates, finished__isnull=False)

        project_updates = [pu.get() for pu in project_updates]
        assert do_all_jobs_overlap(project_updates), \
            "All project updates found to not be running at the same time {}" \
                .format(["(%s, %s), " % (j.started, j.finished) for j in project_updates])

        update_execution_nodes = [update.execution_node for update in project_updates]
        assert set(update_execution_nodes) == set([instance.hostname for instance in instances])

    @pytest.mark.parametrize('resource', ['inventory', 'organization', 'both'])
    def test_inventory_updates_run_on_target_instance_via_resource_ig_assignment(self, factories, tower_ig_instances,
                                                                                 resource):
        ig = factories.instance_group()
        instance = random.sample(tower_ig_instances, 1).pop()
        ig.add_instance(instance)

        inv_source = factories.inventory_source()
        inv = inv_source.ds.inventory

        if resource in ('inventory', 'both'):
            inv.add_instance_group(ig)
        if resource in ('organization', 'both'):
            inv.ds.organization.add_instance_group(ig)

        inv_update = inv_source.update()
        inv_update.wait_until_completed().assert_successful()
        assert inv_update.execution_node == instance.hostname

    # Skip for Openshift because of Github Issue: https://github.com/ansible/tower-qa/issues/2591
    def test_inventory_updates_should_distribute_among_new_instance_group_members(self, factories,
                                                                                  skip_if_openshift,
                                                                                  tower_ig_instances,
                                                                                  wait_for_jobs,
                                                                                  do_all_jobs_overlap,
                                                                                  inventory_script_code_with_sleep):
        ig = factories.instance_group()
        instances = random.sample(tower_ig_instances, 2)
        for instance in instances:
            ig.add_instance(instance)

        num_jobs = self.find_num_jobs(instances)
        inv_script = factories.inventory_script(script=inventory_script_code_with_sleep(20))
        inv_sources = []
        for _ in range(num_jobs):
            inv_source = factories.inventory_source(source_script=inv_script)
            assert inv_source.source_script == inv_script.id
            inv_source.ds.inventory.add_instance_group(ig)
            inv_sources.append(inv_source)

        inv_updates = [inv_source.update() for inv_source in inv_sources]

        wait_for_jobs(inv_updates)

        inv_updates = [iu.get() for iu in inv_updates]
        assert do_all_jobs_overlap(inv_updates), \
            "All jobs found to not be running at the same time {}" \
                .format(["(%s, %s), " % (j.started, j.finished) for j in inv_updates])

        update_execution_nodes = [update.execution_node for update in inv_updates]
        assert set(update_execution_nodes) == set([instance.hostname for instance in instances])

    def test_wfjt_node_jobs_run_on_target_instance_via_unified_jt_ig_assignment(self, factories, tower_ig_instances):
        ig = factories.instance_group()
        instance = random.sample(tower_ig_instances, 1).pop()
        ig.add_instance(instance)

        wfjt = factories.workflow_job_template()
        jt = factories.job_template()
        inv_source = factories.inventory_source()
        project = jt.ds.project

        node1 = factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)
        node2 = node1.add_always_node(unified_job_template=inv_source)
        node2.add_always_node(unified_job_template=project)

        for resource in (jt, inv_source.ds.inventory, project.ds.organization):
            resource.add_instance_group(ig)

        wfj = wfjt.launch()
        wfj.wait_until_completed().assert_successful()
        assert jt.get().related.last_job.get().execution_node == instance.hostname
        assert inv_source.get().related.last_update.get().execution_node == instance.hostname
        assert project.get().related.last_update.get().execution_node == instance.hostname

    def test_jobs_distribute_among_isolated_instance_group_members(self, skip_if_not_traditional_cluster, factories, v2, do_all_jobs_overlap):
        ig = v2.instance_groups.get(name='protected').results.pop()
        instances = ig.related.instances.get().results

        jt = factories.job_template(playbook='sleep.yml', allow_simultaneous=True,
                                       extra_vars=dict(sleep_interval=10))
        jt.ds.inventory.add_host()
        jt.add_instance_group(ig)

        num_jobs = len(instances)
        for _ in range(num_jobs):
            jt.launch()
        jobs = jt.related.jobs.get()

        utils.poll_until(lambda: jobs.get(status='successful').count == num_jobs, interval=5, timeout=60)
        assert do_all_jobs_overlap(jobs.results)

        job_execution_nodes = [job.execution_node for job in jobs.results]
        assert set(job_execution_nodes) == set([instance.hostname for instance in instances])

    def test_single_instance_with_capacity_assigned_as_job_execution_node(self, factories, reset_instance,
                                                                          tower_instance_group):
        ig = factories.instance_group()
        instances = random.sample(tower_instance_group.related.instances.get().results, 3)
        for instance in instances:
            ig.add_instance(instance)

        enabled_instance = instances.pop()
        for instance in instances:
            reset_instance(instance)
            instance.enabled = False

        jt = factories.job_template()
        jt.add_instance_group(ig)

        job = jt.launch().wait_until_completed()
        assert job.execution_node == enabled_instance.hostname

    def test_no_execution_node_assigned_with_jt_with_ig_with_no_instances(self, factories):
        ig = factories.instance_group()
        assert ig.instances == 0
        assert ig.capacity == 0

        jt = factories.job_template()
        jt.add_instance_group(ig)
        job = jt.launch()

        utils.logged_sleep(30)

        assert job.get().execution_node == ''
        assert job.status == 'pending'

    def test_execution_node_assigned_with_jt_with_ig_with_recently_added_instance(self, factories,
                                                                                  tower_instance_group):
        ig = factories.instance_group()
        assert ig.instances == 0
        assert ig.capacity == 0

        jt = factories.job_template()
        jt.add_instance_group(ig)
        job = jt.launch()

        assert job.get().status == 'pending'

        instance = tower_instance_group.related.instances.get().results.pop()
        ig.add_instance(instance)

        job.wait_until_completed(timeout=300).assert_successful()
        assert job.execution_node == instance.hostname

    @pytest.mark.github('https://github.com/ansible/tower/issues/2763', skip=True)
    def test_jobs_larger_than_max_instance_capacity_assigned_to_instances_with_greatest_capacity_first(self, v2,
                                                                                                       largest_capacity,
                                                                                                       jt_generator_for_consuming_given_capacity,
                                                                                                       reset_instance,
                                                                                                       tower_instance_group,
                                                                                                       do_all_jobs_overlap):
        # sort list by hostname
        instances = tower_instance_group.related.instances.get(order_by='hostname').results
        assert all([instance.jobs_running == 0 for instance in instances])

        jobs_count = len(instances)
        forks = largest_capacity + 1
        index = len(instances) / 2
        small_instance = instances[index]

        reset_instance(small_instance)
        # this one instance will have less capacity than the others
        small_instance.capacity_adjustment = .5

        jt = jt_generator_for_consuming_given_capacity(forks)

        # Launch jobs quickly in order to get them in same task manager run
        threads = [threading.Thread(target=jt.launch, args=()) for i in range(0, jobs_count)]
        [t.start() for t in threads]
        [t.join() for t in threads]

        # Wait for jobs to obtain running state, note jobs list is ordered
        jobs = jt.related.jobs.get(order_by='created').results
        jobs = [job.wait_until_status(['running'] + job.completed_statuses) for job in jobs]

        # assure that they were all dispatched
        assert [job.status for job in jobs] == ['running' for job in jobs]
        assert [job.instance_group for job in jobs] == [tower_instance_group.id for job in jobs]
        assert all([job.execution_node != '' for job in jobs])
        jobs_execution_nodes = [j.execution_node for j in jobs]

        # assure that what API reports as consumed capacity is what is expected
        # otherwise the assertions about execution_node will be based on false assumptions
        instances = tower_instance_group.related.instances.get(order_by='hostname').results
        assert [instance.consumed_capacity for instance in instances] == [forks + 1 for i in range(len(instances))]
        assert all([instance.consumed_capacity > instance.capacity for instance in instances])
        # assert target instance is lower capacity than others
        assert small_instance.capacity < min([inst.capacity for inst in instances if inst.id != small_instance.id])

        # Verify all jobs ran overlapping
        assert do_all_jobs_overlap(jobs), \
            "All jobs found to not be running at the same time {}" \
                .format(["(%s, %s), " % (j.started, j.finished) for j in jobs])

        # not checking the distribution of jobs on full-capacity instances,
        # that is done via `test_dispatch_ordering_is_by_hostname`
        # here, we only test that the _last_ job submitted is on the
        # instance which is _under capacity_
        assert set(jobs_execution_nodes) == set([instance.hostname for instance in instances]), \
            ("Jobs did not distribute among all instances where {} instance was free "
             "but lower capacity than others.".format(small_instance.hostname))
        hostname_capacity = {}
        for instance in instances:
            hostname_capacity[instance.hostname] = instance.capacity
        assert jobs_execution_nodes[-1] == small_instance.hostname, \
            ("Last job not run on smallest capacity Instance. Order in which instance "
             "capacity was consumed: {}".format([hostname_capacity.get(hostname) for hostname in jobs_execution_nodes]))

    def test_job_distribution_group_spill_over(self, v2,
                                               factories,
                                               largest_capacity, jt_generator_for_consuming_given_capacity,
                                               tower_instance_group,
                                               tower_ig_instances,
                                               do_all_jobs_overlap):
        """
        * Create a job template designed to consume (a little less than) half the capacity
          of a given node. Configure the JT to run simultaneous jobs.
        * Create a number of instance groups that alternately have one or two instances.
          Assign all instance groups to the JT.
          For Example, with 9 instances:

            ig1.policy_instance_list = [ instance1, instance2 ]
            ig2.policy_instance_list = [ instance3 ]
            ig3.policy_instance_list = [ instance4, instance5 ]
            ig4.policy_instance_list = [ instance6 ]
            ig5.policy_instance_list = [ instance7, instance8 ]
            ig6.policy_instance_list = [ instance9 ]
        * Launch two jobs per instance (all at once).
        * Confirm that each pair of job runs is assigned to a different instance in the
          cluster. Jobs should be assigned to instances based on the alphabetical
          ordering of the instances' hostnames. At the instance group level, job
          assignment should 'spillover' from one instance group to the next (in
          order of instance group assignment to the JT).
        """
        instances = random.sample(tower_ig_instances, max(3, len(tower_ig_instances)))

        jobs_count = len(instances) * 2
        forks = (largest_capacity - 1) // 2
        # 2 Jobs per Instance

        jt = jt_generator_for_consuming_given_capacity(forks)

        temp_instances = [i.hostname for i in instances]
        i = 0
        instance_groups = []
        while temp_instances:
            instance_list = [temp_instances.pop(0)]
            if i % 2 == 0 and instance_list:
                instance_list.append(temp_instances.pop(0))
            instance_groups.append(factories.instance_group(name='group-{}'.format(i),
                                                            policy_instance_list=instance_list))
            i += 1

        # Wait for instance topology recompute
        utils.poll_until(lambda: sum([ig.instances
            for ig in v2.instance_groups.get(id__in=','.join([str(ig.id) for ig in
                instance_groups])).results]) == len(instances), interval=5, timeout=120)

        [jt.add_instance_group(ig) for ig in instance_groups]
        jobs = [jt.launch() for x in range(0, jobs_count)]
        jobs = [j.wait_until_completed() for j in jobs]

        # Verify all jobs ran overlapping
        assert do_all_jobs_overlap(jobs), \
            "All jobs found to not be running at the same time {}" \
                .format(["(%s, %s), " % (j.started, j.finished) for j in jobs])

        for ig in instance_groups:
            if len(ig.policy_instance_list) == 2:
                jobs.pop(0).execution_node == ig.policy_instance_list[0]
                jobs.pop(0).execution_node == ig.policy_instance_list[1]
                jobs.pop(0).execution_node == ig.policy_instance_list[0]
                jobs.pop(0).execution_node == ig.policy_instance_list[1]
            elif len(ig.policy_instance_list) == 1:
                jobs.pop(0).execution_node == ig.policy_instance_list[0]
                jobs.pop(0).execution_node == ig.policy_instance_list[0]
