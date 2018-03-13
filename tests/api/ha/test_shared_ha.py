import subprocess
import random

from towerkit import utils
import pytest

from tests.lib.helpers import openshift_utils
from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.requires_ha
@pytest.mark.mp_group('SharedHA', 'serial')
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestSharedHA(Base_Api_Test):

    @pytest.fixture(autouse=True)
    def prepare_openshift_environment(self, authtoken, v2, is_docker):
        if not is_docker:
            return

        # FIXME: remove 'fo0m4nchU' and update vault file
        ret = subprocess.call('oc login -u jenkins -p fo0m4nchU --insecure-skip-tls-verify=true '
                              'https://console.openshift.ansible.eng.rdu2.redhat.com', shell=True)
        assert ret == 0

        ret = subprocess.call('oc project tower-qe', shell=True)
        assert ret == 0

        openshift_utils.scale_dc('tower', replicas=5)
        utils.poll_until(lambda: v2.instances.get(cpu__gt=0).count == 5, interval=5, timeout=600)

    def test_jobs_should_distribute_among_tower_instance_group_members(self, factories, v2, tower_instance_group):
        jt = factories.v2_job_template(allow_simultaneous=True)
        jt.add_instance_group(tower_instance_group)

        for _ in range(15):
            jt.launch()
        jobs = jt.related.jobs.get()
        utils.poll_until(lambda: jobs.get(status='successful').count == 15, interval=5, timeout=300)

        tower_pods = openshift_utils.get_tower_pods()
        job_execution_nodes = set([job.execution_node for job in jobs.results])
        assert set(tower_pods) == set(job_execution_nodes)

    def test_jt_with_no_instance_groups_defaults_to_tower_instance_group_instance(self, factories, tower_instance_group):
        jt = factories.v2_job_template(allow_simultaneous=True)

        for _ in range(15):
            jt.launch()
        jobs = jt.related.jobs.get()
        utils.poll_until(lambda: jobs.get(status='successful').count == 15, interval=5, timeout=300)

        tower_pods = openshift_utils.get_tower_pods()
        job_execution_nodes = set([job.execution_node for job in jobs.results])
        assert set(tower_pods) == set(job_execution_nodes)

    def test_jobs_should_distribute_among_new_instance_group_members(self, factories, v2):
        ig = factories.instance_group()
        instances = random.sample(v2.instances.get().results, 3)
        for instance in instances:
            ig.add_instance(instance)

        jt = factories.v2_job_template(allow_simultaneous=True)
        jt.add_instance_group(ig)

        for _ in range(9):
            jt.launch()
        jobs = jt.related.jobs.get()
        utils.poll_until(lambda: jobs.get(status='successful').count == 9, interval=5, timeout=300)

        job_execution_nodes = set([job.execution_node for job in jobs.results])
        assert set([instance.hostname for instance in instances]) == set(job_execution_nodes)

    def test_ahcs_should_distribute_among_new_instance_group_members(self, factories, v2):
        import pdb; pdb.set_trace()
        ig = factories.instance_group()
        instances = random.sample(v2.instances.get().results, 3)
        for instance in instances:
            ig.add_instance(instance)

        host = factories.v2_host()
        host.ds.inventory.add_instance_group(ig)

        for _ in range(9):
            factories.v2_ad_hoc_command(inventory=host.ds.inventory, module_name='ping')
        utils.poll_until(lambda: jobs.get(status='successful').count == 9, interval=5, timeout=300)
        import pdb; pdb.set_trace()

        job_execution_nodes = set([job.execution_node for job in jobs.results])
        assert set([instance.hostname for instance in instances]) == set(job_execution_nodes)

    # VERIFY
    def test_jobs_should_distribute_among_mutually_exclusive_instance_groups(self, factories, v2):
        ig1, ig2 = [factories.instance_group() for _ in range(2)]
        instances = v2.instances.get().results
        ig1.add_instance(instances[0])
        ig2.add_instance(instances[1])
        utils.poll_until(lambda: ig1.get().instances == 1, interval=5, timeout=300)
        utils.poll_until(lambda: ig2.get().instances == 1, interval=5, timeout=300)

        jt = factories.v2_job_template(playbook='sleep.yml', allow_simultaneous=True, extra_vars='{"sleep_interval": 60}')
        factories.v2_host(inventory=jt.ds.inventory)
        for ig in (ig1, ig2):
            jt.add_instance_group(ig)

        for _ in range(15):
            jt.launch()
        jobs = jt.related.jobs.get()
        utils.poll_until(lambda: jobs.get(status='successful').count == 15, interval=5, timeout=300)

        tower_pods = openshift_utils.get_tower_pods()
        pod1_jobs = [job for job in jobs.results if job.execution_node == tower_pods[0]]
        pod2_jobs = [job for job in jobs.results if job.execution_node == tower_pods[1]]
        assert len(pod1_jobs) > 0
        assert len(pod2_jobs) > 0

    # VERIFY
    def test_jobs_should_distribute_among_partially_overlapping_instance_groups(self, factories, v2):
        ig1, ig2 = [factories.instance_group() for _ in range(2)]
        instances = v2.instances.get().results
        ig1.add_instance(instances[0])
        ig2.add_instance(instances[1])
        for ig in (ig1, ig2):
            ig.add_instance(instances[2])
        utils.poll_until(lambda: ig1.get().instances == 2, interval=5, timeout=300)
        utils.poll_until(lambda: ig2.get().instances == 2, interval=5, timeout=300)

        jt = factories.v2_job_template(playbook='sleep.yml', allow_simultaneous=True, extra_vars='{"sleep_interval": 60}')
        factories.v2_host(inventory=jt.ds.inventory)
        for _ in range(15):
            jt.launch()
        jobs = jt.related.jobs.get()
        utils.poll_until(lambda: jobs.get(status='successful').count == 15, interval=5, timeout=300)

        tower_pods = openshift_utils.get_tower_pods()
        pod1_jobs = [job for job in jobs.results if job.execution_node == tower_pods[0]]
        pod2_jobs = [job for job in jobs.results if job.execution_node == tower_pods[1]]
        pod3_jobs = [job for job in jobs.results if job.execution_node == tower_pods[2]]
        assert len(pod1_jobs) > 0
        assert len(pod2_jobs) > 0
        assert len(pod3_jobs) > 0

    # VERIFY
    def test_jobs_should_distribute_among_completely_overlapping_instance_groups(self, factories, v2):
        ig1, ig2 = [factories.instance_group() for _ in range(2)]
        instances = v2.instances.get().results
        for ig in (ig1, ig2):
            for instance in instances:
                ig.add_instance(instance)
        utils.poll_until(lambda: ig1.get().instances == 1, interval=5, timeout=300)
        utils.poll_until(lambda: ig2.get().instances == 1, interval=5, timeout=300)

        jt = factories.v2_job_template(playbook='sleep.yml', allow_simultaneous=True, extra_vars='{"sleep_interval": 60}')
        factories.v2_host(inventory=jt.ds.inventory)
        for _ in range(15):
            jt.launch()
        jobs = jt.related.jobs.get()
        utils.poll_until(lambda: jobs.get(status='successful').count == 15, interval=5, timeout=300)

        tower_pods = openshift_utils.get_tower_pods()
        pod1_jobs = [job for job in jobs.results if job.execution_node == tower_pods[0]]
        pod2_jobs = [job for job in jobs.results if job.execution_node == tower_pods[1]]
        assert len(pod1_jobs) > 0
        assert len(pod2_jobs) > 0

    def test_jobs_should_not_run_on_disabled_instances(self, request, v2, factories):
        ig = factories.instance_group()
        instance = v2.instances.get().results.pop()
        ig.add_instance(instance)

        request.addfinalizer(lambda: instance.patch(enabled=True))
        instance.enabled = False

        utils.poll_until(lambda: ig.get().instances == 1, interval=5, timeout=300)

        jt = factories.v2_job_template()
        factories.v2_host(inventory=jt.ds.inventory)
        jt.add_instance_group(ig)
        job = jt.launch()

        utils.logged_sleep(30)
        assert job.get().status == 'pending'

    def test_jobs_should_resume_on_newly_enabled_instances(self, request, v2, factories):
        ig = factories.instance_group()
        instance = v2.instances.get().results.pop()
        ig.add_instance(instance)

        request.addfinalizer(lambda: instance.patch(enabled=True))
        instance.enabled = False

        utils.poll_until(lambda: ig.get().instances == 1, interval=5, timeout=300)

        jt = factories.v2_job_template()
        factories.v2_host(inventory=jt.ds.inventory)
        jt.add_instance_group(ig)
        job = jt.launch()

        utils.logged_sleep(30)
        assert job.get().status == 'pending'

        instance.enabled = True
        assert job.wait_until_completed(timeout=300).is_successful

    def test_disabiling_instance_should_not_impact_currently_running_jobs(self, request, v2, factories):
        ig = factories.instance_group()
        instance = v2.instances.get().results.pop()
        ig.add_instance(instance)

        request.addfinalizer(lambda: instance.patch(enabled=True))
        utils.poll_until(lambda: ig.related.instances.get(cpu__gt=0).count == 1, interval=5, timeout=600)

        jt = factories.v2_job_template(playbook='sleep.yml', extra_vars='{"sleep_interval": 30}')
        factories.v2_host(inventory=jt.ds.inventory)
        jt.add_instance_group(ig)

        job = jt.launch()
        assert job.wait_until_started().execution_node == instance.hostname

        instance.enabled = False
        assert job.wait_until_completed().is_successful

    def test_disabiling_instance_should_set_capacity_to_zero(self, request, v2, factories):
        instance = v2.instances.get().results.pop()
        initial_mem_capacity = instance.mem_capacity
        initial_cpu_capacity = instance.cpu_capacity
        request.addfinalizer(lambda: instance.patch(enabled=True))

        assert initial_mem_capacity > 0
        assert initial_cpu_capacity > 0
        assert instance.capacity == max(instance.mem_capacity, instance.cpu_capacity)

        instance.enabled = False
        assert instance.mem_capacity == initial_mem_capacity
        assert instance.cpu_capacity == initial_cpu_capacity
        assert instance.capacity == 0

        instance.enabled = True
        assert instance.mem_capacity == initial_mem_capacity
        assert instance.cpu_capacity == initial_cpu_capacity
        assert instance.capacity == max(instance.mem_capacity, instance.cpu_capacity)

    def test_jobs_should_not_run_with_jt_with_empty_instance_group(self, factories):
        ig = factories.instance_group()
        assert ig.instances == 0
        assert ig.capacity == 0

        jt = factories.v2_job_template()
        jt.add_instance_group(ig)
        job = jt.launch()

        utils.logged_sleep(30)

        assert job.get().status == 'pending'

    def test_jobs_should_resume_when_capacity_becomes_available_to_an_empty_instance_group(self, factories,
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

        assert job.wait_until_completed(timeout=180).is_successful
        assert job.execution_node == instance.hostname

    @pytest.mark.parametrize('instance_percentage, expected_num_instances', [(0, 0), (50, 3), (100, 5)])
    def test_correct_instances_with_newly_ig_with_policy_instance_percentage(self, factories, instance_percentage,
                                                                             expected_num_instances):
        ig = factories.instance_group(policy_instance_percentage=instance_percentage)
        assert ig.instances == expected_num_instances
        assert ig.related.instances.get().count == expected_num_instances

    @pytest.mark.parametrize('instance_minimum, expected_num_instances', [(0, 0), (3, 2), (5, 5)])
    def test_correct_instances_with_new_ig_with_policy_instance_minimum(self, factories, instance_minimum,
                                                                        expected_num_instances):
        ig = factories.instance_group(policy_instance_minimum=instance_minimum)
        assert ig.instances == expected_num_instances
        assert ig.related.instances.get().count == expected_num_instances
