from towerkit import utils
import pytest

from tests.lib.helpers import openshift_utils
from tests.api import APITest


@pytest.mark.api
@pytest.mark.mp_group('OpenShiftCluster', 'isolated_serial')
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited', 'skip_if_not_openshift')
class TestOpenShiftCluster(APITest):

    @pytest.fixture(autouse=True)
    def setup(self):
        openshift_utils.prep_environment()

    @pytest.fixture
    def tower_ig_contains_all_instances(self, v2, tower_instance_group):
        def func():
            return set(instance.id for instance in v2.instances.get().results) == \
                   set(instance.id for instance in tower_instance_group.related.instances.get().results)
        return func

    def verify_instance(self, instance):
        assert instance.enabled
        assert instance.cpu == 0
        assert instance.memory == 0
        assert instance.capacity == max(instance.cpu_capacity, instance.mem_capacity)
        assert instance.cpu_capacity > 0
        assert instance.mem_capacity > 0
        assert instance.capacity_adjustment == '1.00'

    def test_scale_up_tower_pod(self, v2, tower_instance_group, tower_version, tower_ig_contains_all_instances):
        num_instances = v2.instances.get().count + 2
        openshift_utils.scale_dc(dc='ansible-tower', replicas=num_instances)
        utils.poll_until(lambda: len(openshift_utils.get_tower_pods()) == num_instances, interval=5, timeout=180)
        tower_pods = set(openshift_utils.get_tower_pods())

        instances = v2.instances.get()
        utils.poll_until(lambda: instances.get(version=tower_version).count == num_instances, interval=5, timeout=600)
        assert set([instance.hostname for instance in instances.get().results]) == tower_pods
        for instance in instances.results:
            self.verify_instance(instance)

        ping = v2.ping.get()
        utils.poll_until(lambda: len(ping.get().instances) == num_instances, interval=5, timeout=180)
        assert set([instance.node for instance in ping.instances]) == tower_pods

        assert tower_ig_contains_all_instances()

    def test_scale_down_tower_pod(self, v2, tower_instance_group, tower_version, tower_ig_contains_all_instances):
        num_instances = v2.instances.get().count - 2
        openshift_utils.scale_dc(dc='ansible-tower', replicas=num_instances)
        utils.poll_until(lambda: len(openshift_utils.get_tower_pods()) == num_instances, interval=5, timeout=180)
        tower_pods = set(openshift_utils.get_tower_pods())

        instances = v2.instances.get()
        utils.poll_until(lambda: instances.get(version=tower_version).count == num_instances, interval=5, timeout=600)
        assert set([instance.hostname for instance in instances.get().results]) == tower_pods
        for instance in instances.results:
            self.verify_instance(instance)

        ping = v2.ping.get()
        utils.poll_until(lambda: len(ping.get().instances) == num_instances, interval=5, timeout=180)
        assert set([instance.node for instance in ping.instances]) == tower_pods

        assert tower_ig_contains_all_instances()

    def test_tower_web_service_should_be_able_to_recover_from_zero_tower_pods(self, factories, v2, tower_instance_group,
                                                                              tower_version, tower_ig_contains_all_instances):
        openshift_utils.scale_dc(dc='ansible-tower', replicas=0)
        utils.poll_until(lambda: len(openshift_utils.get_tower_pods()) == 0, interval=5, timeout=300)

        openshift_utils.scale_dc(dc='ansible-tower', replicas=1)
        utils.poll_until(lambda: len(openshift_utils.get_tower_pods()) == 1, interval=5, timeout=180)
        tower_pod = openshift_utils.get_tower_pods().pop()

        utils.logged_sleep(60)

        # verify API contents
        utils.poll_until(lambda: v2.instances.get(version=tower_version).count == 1, interval=5, timeout=600)
        instance = v2.instances.get().results.pop()
        self.verify_instance(instance)

        ping = v2.ping.get()
        utils.poll_until(lambda: len(ping.get().instances) == 1, interval=5, timeout=180)
        instance = ping.instances.pop()
        assert instance.node == tower_pod
        assert instance.version == tower_version
        assert instance.capacity > 0

        assert tower_ig_contains_all_instances()

        # verify that jobs run
        jt = factories.job_template()
        jt.add_instance_group(tower_instance_group)

        job = jt.launch().wait_until_completed(timeout=180)
        job.assert_successful()
        assert job.execution_node == tower_pod

    def test_verify_jobs_fail_with_execution_node_death(self, factories, v2, tower_version):
        openshift_utils.scale_dc(dc='ansible-tower', replicas=5)
        utils.poll_until(lambda: len(openshift_utils.get_tower_pods()) == 5, interval=5, timeout=180)
        utils.poll_until(lambda: v2.instances.get(version=tower_version).count == 5, interval=5, timeout=600)

        ig = factories.instance_group()
        instance = v2.instances.get().results.pop()
        ig.add_instance(instance)

        jt = factories.job_template(playbook='sleep.yml', extra_vars='{"sleep_interval": 180}')
        jt.add_instance_group(ig)
        factories.host(inventory=jt.ds.inventory)

        job = jt.launch()
        utils.poll_until(lambda: job.get().execution_node, interval=1, timeout=60)

        openshift_utils.delete_pod(job.execution_node)
        # workaround for issue with "wait_until_completed"
        assert utils.poll_until(lambda: job.get().status == 'failed', timeout=600)
        assert job.job_explanation == 'Task was marked as running in Tower but was not present in the job queue, ' \
                                      'so it has been marked as failed.'

        utils.poll_until(lambda: len(openshift_utils.get_tower_pods()) == 5, interval=5, timeout=180)
        utils.poll_until(lambda: v2.instances.get(version=tower_version).count == 5, interval=5, timeout=600)
