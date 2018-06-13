import random
import six
import itertools
import datetime

from towerkit import utils
import pytest

from tests.lib.helpers import openshift_utils
from tests.api import Base_Api_Test


def do_all_jobs_overlap(jobs):
    def overlap(start1, end1, start2, end2):
        """Does the range (start1, end1) overlap with (start2, end2)?"""
        return end1 >= start2 and end2 >= start1

    for (j1, j2) in list(itertools.combinations(jobs, 2)):
        if not overlap(datetime.datetime.strptime(j1.started, '%Y-%m-%dT%H:%M:%S.%fZ'),
                       datetime.datetime.strptime(j1.finished, '%Y-%m-%dT%H:%M:%S.%fZ'),
                       datetime.datetime.strptime(j2.started, '%Y-%m-%dT%H:%M:%S.%fZ'),
                       datetime.datetime.strptime(j2.finished, '%Y-%m-%dT%H:%M:%S.%fZ')):
            return False
    return True


@pytest.mark.api
@pytest.mark.requires_cluster
@pytest.mark.mp_group('ExecutionNodeAssignment', 'serial')
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestExecutionNodeAssignment(Base_Api_Test):

    @pytest.fixture(autouse=True, scope='class')
    def prepare_openshift_environment(self, is_docker):
        if not is_docker:
            return
        else:
            openshift_utils.prep_environment()

    @pytest.fixture
    def tower_ig_instances(self, tower_instance_group):
        return tower_instance_group.related.instances.get(order_by='hostname').results

    @pytest.fixture
    def reset_instance(self, request):
        def func(instance):
            def teardown():
                instance.enabled = True
                instance.patch(capacity_adjustment=1)
            request.addfinalizer(teardown)
        return func

    def find_num_jobs(self, instances):
        # find number of jobs to distribute among a set of instances
        return 3 * len(instances)

    def find_ig_overflow_jobs(self, ig, uj_impact):
        # find number of jobs such that a single IG is put over capacity
        capacity = sum([instance.capacity for instance in ig.related.instances.get().results])
        return capacity / uj_impact + 1

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
            jt = factories.v2_job_template(allow_simultaneous=True,
                                           forks=capacity_size,
                                           playbook='sleep.yml',
                                           extra_vars=dict(sleep_interval=60),
                                           limit="all[0]")
            map(lambda i: factories.v2_host(inventory=jt.ds.inventory),
                xrange(0, capacity_size + 1))
            return jt
        return fn

    def test_jobs_should_distribute_among_tower_instance_group_members(self, factories, tower_instance_group):
        jt = factories.v2_job_template(allow_simultaneous=True)
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
        jt = factories.v2_job_template(allow_simultaneous=True)

        num_jobs = self.find_num_jobs(tower_ig_instances)
        for _ in range(num_jobs):
            jt.launch()
        jobs = jt.related.jobs.get()
        utils.poll_until(lambda: jobs.get(status='successful').count == num_jobs, interval=5, timeout=300)

        job_execution_nodes = [job.execution_node for job in jobs.results]
        assert set(job_execution_nodes) == set([instance.hostname for instance in tower_ig_instances])

    def test_jobs_should_distribute_among_mutually_exclusive_instance_groups(self, factories, tower_ig_instances,
                                                                             reset_instance):
        ig1, ig2 = [factories.instance_group() for _ in range(2)]
        instances = random.sample(tower_ig_instances, 2)
        for instance in instances:
            reset_instance(instance)
            instance.capacity_adjustment = 0
        ig1.add_instance(instances[0])
        ig2.add_instance(instances[1])
        utils.poll_until(lambda: ig1.get().instances == 1 and ig2.get().instances == 1, interval=5,
                         timeout=300)

        jt = factories.v2_job_template(playbook='sleep.yml', allow_simultaneous=True,
                                       extra_vars='{"sleep_interval": 60}')
        for _ in range(3):
            factories.v2_host(inventory=jt.ds.inventory)
        for ig in (ig1, ig2):
            jt.add_instance_group(ig)

        num_jobs = self.find_ig_overflow_jobs(ig1, 4)
        for _ in range(num_jobs):
            jt.launch()
        jobs = jt.related.jobs.get()
        utils.poll_until(lambda: len([job.execution_node for job in jobs.get().results
                         if job.execution_node != '']) == num_jobs, interval=5, timeout=300)

        job_execution_nodes = [job.execution_node for job in jobs.results]
        assert set(job_execution_nodes) == set([instance.hostname for instance in instances])

    @pytest.mark.github('https://github.com/ansible/tower/issues/1418')
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
        utils.poll_until(lambda: ig1.get().instances == 2 and ig2.get().instances == 2, interval=5,
                         timeout=300)

        jt = factories.v2_job_template(playbook='sleep.yml', allow_simultaneous=True,
                                       extra_vars='{"sleep_interval": 60}')
        for _ in range(3):
            factories.v2_host(inventory=jt.ds.inventory)
        for ig in (ig1, ig2):
            jt.add_instance_group(ig)

        num_jobs = self.find_ig_overflow_jobs(ig1, 4)
        for _ in range(num_jobs):
            jt.launch()
        jobs = jt.related.jobs.get()
        utils.poll_until(lambda: len([job.execution_node for job in jobs.get().results
                         if job.execution_node != '']) == num_jobs, interval=5, timeout=300)

        job_execution_nodes = [job.execution_node for job in jobs.results]
        assert set(job_execution_nodes) == set([instance.hostname for instance in instances])

    def test_jobs_should_distribute_among_completely_overlapping_instance_groups(self, factories, tower_ig_instances,
                                                                                 reset_instance):

        ig1, ig2 = [factories.instance_group() for _ in range(2)]
        instances = random.sample(tower_ig_instances, 2)
        for instance in instances:
            reset_instance(instance)
            instance.capacity_adjustment = 0

        for ig in (ig1, ig2):
            for instance in instances:
                ig.add_instance(instance)
        utils.poll_until(lambda: ig1.get().instances == 2 and ig2.get().instances == 2, interval=5,
                         timeout=300)

        jt = factories.v2_job_template(playbook='sleep.yml', allow_simultaneous=True,
                                       extra_vars='{"sleep_interval": 60}')
        for _ in range(3):
            factories.v2_host(inventory=jt.ds.inventory)
        for ig in (ig1, ig2):
            jt.add_instance_group(ig)

        num_jobs = self.find_ig_overflow_jobs(ig1, 4)
        for _ in range(num_jobs):
            jt.launch()
        jobs = jt.related.jobs.get()
        utils.poll_until(lambda: len([job.execution_node for job in jobs.get().results
                         if job.execution_node != '']) == num_jobs, interval=5, timeout=300)

        job_execution_nodes = [job.execution_node for job in jobs.results]
        assert set(job_execution_nodes) == set([instance.hostname for instance in instances])

    @pytest.mark.github('https://github.com/ansible/tower/issues/1767')
    def test_jobs_should_distribute_among_new_instance_group_members(self, factories, tower_ig_instances):
        ig = factories.instance_group()
        instances = random.sample(tower_ig_instances, 2)
        for instance in instances:
            ig.add_instance(instance)

        jt = factories.v2_job_template(allow_simultaneous=True)
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

        inv = factories.v2_inventory()

        if resource in ('inventory', 'both'):
            inv.add_instance_group(ig)
        if resource in ('organization', 'both'):
            inv.ds.organization.add_instance_group(ig)

        ahc = factories.v2_ad_hoc_command(inventory=inv, module_name='ping')
        assert ahc.wait_until_completed().is_successful
        assert ahc.execution_node == instance.hostname

    def test_ahcs_should_distribute_among_new_instance_group_members(self, factories, tower_ig_instances):
        ig = factories.instance_group()
        instances = random.sample(tower_ig_instances, 2)
        for instance in instances:
            ig.add_instance(instance)

        inv = factories.v2_inventory()
        inv.add_instance_group(ig)

        num_jobs = self.find_num_jobs(instances)
        for _ in range(num_jobs):
            factories.v2_ad_hoc_command(inventory=inv, module_name='ping')
        ahcs = inv.related.ad_hoc_commands.get()
        utils.poll_until(lambda: ahcs.get(status='successful').count == num_jobs, interval=5, timeout=300)

        ahc_execution_nodes = [ahc.execution_node for ahc in ahcs.results]
        assert set(ahc_execution_nodes) == set([instance.hostname for instance in instances])

    def test_project_updates_run_on_target_instance_via_organization_ig_assignment(self, factories,
                                                                                   tower_ig_instances):
        ig = factories.instance_group()
        instance = random.sample(tower_ig_instances, 1).pop()
        ig.add_instance(instance)

        project = factories.v2_project()
        project.ds.organization.add_instance_group(ig)

        project_update = project.update()
        assert project_update.wait_until_completed().is_successful
        assert project_update.execution_node == instance.hostname

    def test_project_updates_should_distribute_among_new_instance_group_members(self, factories,
                                                                                tower_ig_instances):
        ig = factories.instance_group()
        instances = random.sample(tower_ig_instances, 2)
        for instance in instances:
            ig.add_instance(instance)

        project = factories.v2_project()
        project.ds.organization.add_instance_group(ig)
        initial_update = project.get().related.last_update.get()

        num_jobs = self.find_num_jobs(instances)
        for _ in range(num_jobs):
            project.update()
        project_updates = project.related.project_updates.get()
        utils.poll_until(lambda: project_updates.get(status='successful', not__id=initial_update.id).count == num_jobs,
                         interval=5, timeout=300)

        update_execution_nodes = [update.execution_node for update in project_updates.results]
        assert set(update_execution_nodes) == set([instance.hostname for instance in instances])

    @pytest.mark.parametrize('resource', ['inventory', 'organization', 'both'])
    def test_inventory_updates_run_on_target_instance_via_resource_ig_assignment(self, factories, tower_ig_instances,
                                                                                 resource):
        ig = factories.instance_group()
        instance = random.sample(tower_ig_instances, 1).pop()
        ig.add_instance(instance)

        inv_source = factories.v2_inventory_source()
        inv = inv_source.ds.inventory

        if resource in ('inventory', 'both'):
            inv.add_instance_group(ig)
        if resource in ('organization', 'both'):
            inv.ds.organization.add_instance_group(ig)

        inv_update = inv_source.update()
        assert inv_update.wait_until_completed().is_successful
        assert inv_update.execution_node == instance.hostname

    def test_inventory_updates_should_distribute_among_new_instance_group_members(self, factories,
                                                                                  tower_ig_instances):
        ig = factories.instance_group()
        instances = random.sample(tower_ig_instances, 2)
        for instance in instances:
            ig.add_instance(instance)

        inv_source = factories.v2_inventory_source()
        inv_source.ds.inventory.add_instance_group(ig)

        num_jobs = self.find_num_jobs(instances)
        for _ in range(num_jobs):
            inv_source.update()
        inv_updates = inv_source.related.inventory_updates.get()
        utils.poll_until(lambda: inv_updates.get(status='successful').count == num_jobs, interval=5, timeout=300)

        update_execution_nodes = [update.execution_node for update in inv_updates.results]
        assert set(update_execution_nodes) == set([instance.hostname for instance in instances])

    def test_wfjt_node_jobs_run_on_target_instance_via_unified_jt_ig_assignment(self, factories, tower_ig_instances):
        ig = factories.instance_group()
        instance = random.sample(tower_ig_instances, 1).pop()
        ig.add_instance(instance)

        wfjt = factories.v2_workflow_job_template()
        jt = factories.v2_job_template()
        inv_source = factories.v2_inventory_source()
        project = jt.ds.project

        node1 = factories.v2_workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)
        node2 = node1.add_always_node(unified_job_template=inv_source)
        node2.add_always_node(unified_job_template=project)

        for resource in (jt, inv_source.ds.inventory, project.ds.organization):
            resource.add_instance_group(ig)

        wfj = wfjt.launch()
        assert wfj.wait_until_completed().is_successful
        assert jt.get().related.last_job.get().execution_node == instance.hostname
        assert inv_source.get().related.last_update.get().execution_node == instance.hostname
        assert project.get().related.last_update.get().execution_node == instance.hostname

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

        jt = factories.v2_job_template()
        jt.add_instance_group(ig)

        job = jt.launch().wait_until_completed()
        assert job.execution_node == enabled_instance.hostname

    def test_multiple_instances_with_capacity_assigned_as_job_execution_node(self, factories, reset_instance,
                                                                             tower_instance_group):
        ig = factories.instance_group()
        instances = random.sample(tower_instance_group.related.instances.get().results, 3)
        for instance in instances:
            ig.add_instance(instance)

        disabled_instance = instances.pop()
        reset_instance(disabled_instance)
        disabled_instance.enabled = False

        jt = factories.v2_job_template(allow_simultaneous=True)
        jt.add_instance_group(ig)

        num_jobs = self.find_num_jobs(instances)
        for _ in range(num_jobs):
            jt.launch()
        jobs = jt.related.jobs.get()
        utils.poll_until(lambda: jobs.get(status='successful').count == num_jobs, interval=5, timeout=300)

        job_execution_nodes = [job.execution_node for job in jobs.results]
        assert set(job_execution_nodes) == set([instance.hostname for instance in instances])

    def test_additional_ig_instances_assigned_when_primary_ig_has_no_capacity(self, factories, reset_instance,
                                                                              tower_instance_group):
        ig1, ig2 = [factories.instance_group() for _ in range(2)]
        instances = random.sample(tower_instance_group.related.instances.get().results, 3)

        disabled_instance = instances.pop()
        reset_instance(disabled_instance)
        disabled_instance.enabled = False

        ig1.add_instance(disabled_instance)
        for instance in instances:
            ig2.add_instance(instance)

        jt = factories.v2_job_template(allow_simultaneous=True)
        for ig in (ig1, ig2):
            jt.add_instance_group(ig)

        num_jobs = self.find_num_jobs(instances)
        for _ in range(num_jobs):
            jt.launch()
        jobs = jt.related.jobs.get()
        utils.poll_until(lambda: jobs.get(status='successful').count == num_jobs, interval=5, timeout=300)

        job_execution_nodes = [job.execution_node for job in jobs.results]
        assert set(job_execution_nodes) == set([instance.hostname for instance in instances])

    def test_no_execution_node_assigned_with_jt_with_ig_with_no_instances(self, factories):
        ig = factories.instance_group()
        assert ig.instances == 0
        assert ig.capacity == 0

        jt = factories.v2_job_template()
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

        jt = factories.v2_job_template()
        jt.add_instance_group(ig)
        job = jt.launch()

        assert job.get().status == 'pending'

        instance = tower_instance_group.related.instances.get().results.pop()
        ig.add_instance(instance)

        assert job.wait_until_completed(timeout=300).is_successful
        assert job.execution_node == instance.hostname

    def test_jobs_larger_than_max_instance_capacity_assigned_to_instances_with_greatest_capacity_first(self, v2,
                                                                                                       largest_capacity,
                                                                                                       jt_generator_for_consuming_given_capacity,
                                                                                                       reset_instance,
                                                                                                       tower_instance_group,
                                                                                                       tower_ig_instances):
        instances = random.sample(tower_ig_instances, max(3, len(tower_ig_instances)))

        jobs_count = len(instances)
        forks = largest_capacity + 1
        index = len(instances) / 2

        reset_instance(instances[index])
        instances[index].capacity_adjustment = .5

        jt = jt_generator_for_consuming_given_capacity(forks)
        jobs = [jt.launch() for i in xrange(0, jobs_count)]
        jobs = [j.wait_until_completed() for j in jobs]

        # Refresh jobs for execution_node attribute
        jobs_execution_nodes = [j.get().execution_node for j in jobs]

        # Verify all jobs ran overlapping
        assert do_all_jobs_overlap(jobs), \
            "All jobs found to not be running at the same time {}" \
                .format(["(%s, %s), " % (j.started, j.finished) for j in jobs])

        for (instance, execution_node) in zip(instances[:index], jobs_execution_nodes[:index]):
            assert execution_node == instance.hostname, \
                "Job not run on expected instance"

        # Smallest idle node chosen last when a job is too big
        assert jobs_execution_nodes[-1] == instances[index].hostname, \
            "Last job not run on smallest capacity Instance"

        for (instance, execution_node) in zip(instances[index + 1:], jobs_execution_nodes[index:-1]):
            assert execution_node == instance.hostname, \
                "Job not run on expected instance"

    def test_job_distribution_group_spill_over(self, v2,
                                               factories,
                                               largest_capacity, jt_generator_for_consuming_given_capacity,
                                               tower_instance_group,
                                               tower_ig_instances):
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
        forks = (largest_capacity - 1) / 2
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

        map(lambda ig: jt.add_instance_group(ig), instance_groups)
        jobs = [jt.launch() for x in xrange(0, jobs_count)]
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
