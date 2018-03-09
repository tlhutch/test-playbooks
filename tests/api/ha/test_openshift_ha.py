import subprocess

from towerkit import utils
import pytest

from tests.lib.helpers import openshift_utils
from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.requires_openshift_ha
@pytest.mark.mp_group('OpenShiftHA', 'serial')
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestOpenShiftHA(Base_Api_Test):

    @pytest.fixture(autouse=True)
    def prepare_environment(self):
        # FIXME: remove 'fo0m4nchU' and update vault file
        ret = subprocess.call('oc login -u jenkins -p fo0m4nchU --insecure-skip-tls-verify=true '
                              'https://console.openshift.ansible.eng.rdu2.redhat.com', shell=True)
        assert ret == 0

        ret = subprocess.call('oc project tower-qe', shell=True)
        assert ret == 0

    @pytest.fixture
    def tower_ig_contains_all_instances(self, v2, tower_instance_group):
        def func():
            return set(instance.id for instance in v2.instances.get().results) == \
                   set(instance.id for instance in tower_instance_group.related.instances.get().results)
        return func

    def test_scale_up_tower_pod(self, v2, tower_instance_group, tower_version, tower_ig_contains_all_instances):
        openshift_utils.scale_dc(dc='tower', replicas=3)
        utils.poll_until(lambda: openshift_utils.get_tower_pods_number() == 3, interval=5, timeout=180)
        tower_pods = set(openshift_utils.get_tower_pods())

        instances = v2.instances.get()
        utils.poll_until(lambda: instances.get(cpu__gt=0).count == 3, interval=5, timeout=600)
        assert set([instance.hostname for instance in instances.get().results]) == tower_pods
        for instance in instances.results:
            assert instance.enabled
            assert instance.version == tower_version

        ping = v2.ping.get()
        utils.poll_until(lambda: len(ping.get().instances) == 3, interval=5, timeout=180)
        assert set([instance.node for instance in ping.instances]) == tower_pods
        assert set(ping.instance_groups.pop().instances) == tower_pods
        for instance in instances.results:
            assert instance.version == tower_version

        assert tower_ig_contains_all_instances()

    def test_scale_down_tower_pod(self, v2, tower_instance_group, tower_version, tower_ig_contains_all_instances):
        openshift_utils.scale_dc(dc='tower', replicas=1)
        utils.poll_until(lambda: openshift_utils.get_tower_pods_number() == 1, interval=5, timeout=180)
        tower_pods = set(openshift_utils.get_tower_pods())

        instances = v2.instances.get()
        utils.poll_until(lambda: instances.get(cpu__gt=0).count == 1, interval=5, timeout=600)
        assert set([instance.hostname for instance in instances.get().results]) == tower_pods
        for instance in instances.results:
            assert instance.enabled
            assert instance.version == tower_version

        ping = v2.ping.get()
        utils.poll_until(lambda: len(ping.get().instances) == 1, interval=5, timeout=180)
        assert set([instance.node for instance in ping.instances]) == tower_pods
        assert set(ping.instance_groups.pop().instances) == tower_pods
        for instance in instances.results:
            assert instance.version == tower_version

        assert tower_ig_contains_all_instances()

    def test_tower_web_service_should_be_able_to_recover_from_zero_tower_pods(self, v2, factories, tower_instance_group,
                                                                              tower_version, tower_ig_contains_all_instances):
        openshift_utils.scale_dc(dc='tower', replicas=0)
        utils.poll_until(lambda: openshift_utils.get_tower_pods_number() == 0, interval=5, timeout=180)

        openshift_utils.scale_dc(dc='tower', replicas=1)
        utils.poll_until(lambda: openshift_utils.get_tower_pods_number() == 1, interval=5, timeout=180)
        tower_pod = openshift_utils.get_tower_pods().pop()

        utils.logged_sleep(60)

        # verify API contents
        utils.poll_until(lambda: v2.instances.get(cpu__gt=0).count == 1, interval=5, timeout=600)
        instance = v2.instances.get().results.pop()
        utils.poll_until(lambda: instance.get().cpu > 0, interval=5, timeout=180)
        assert instance.enabled
        assert instance.version == tower_version

        ping = v2.ping.get()
        utils.poll_until(lambda: len(ping.get().instances) == 1, interval=5, timeout=180)
        instance = ping.instances.pop()
        assert instance.node == tower_pod
        assert instance.version == tower_version
        assert len(ping.instance_groups) == 1
        assert ping.instance_groups.pop().instances.pop() == tower_pod

        assert tower_ig_contains_all_instances()

        # verify that jobs run
        jt = factories.v2_job_template()
        jt.add_instance_group(tower_instance_group)
        job = jt.launch().wait_until_completed(timeout=180)
        assert job.is_successful
        assert job.execution_node == tower_pod

    def test_tower_stability_while_scaling_etcd_pod(self, v2, factories):
        jt = factories.v2_job_template()

        # assess tower functionality with multiple etcd pods
        openshift_utils.scale_dc(dc='etcd', replicas=2)
        utils.poll_until(lambda: len([pod for pod in openshift_utils.get_pods() if 'etcd' in pod]) == 2, interval=5, timeout=180)
        v2.ping.get()
        assert jt.launch().wait_until_completed().is_successful

        # assess tower functionality with one etcd pod
        openshift_utils.scale_dc(dc='etcd', replicas=1)
        utils.poll_until(lambda: len([pod for pod in openshift_utils.get_pods() if 'etcd' in pod]) == 1, interval=5, timeout=180)
        v2.ping.get()
        assert jt.launch().wait_until_completed().is_successful

    def test_tower_should_be_able_to_recover_from_zero_etcd_pods(self, v2, factories):
        openshift_utils.scale_dc(dc='etcd', replicas=0)
        utils.poll_until(lambda: len([pod for pod in openshift_utils.get_pods() if 'etcd' in pod]) == 0, interval=5, timeout=180)

        openshift_utils.scale_dc(dc='etcd', replicas=1)
        utils.poll_until(lambda: len([pod for pod in openshift_utils.get_pods() if 'etcd' in pod]) == 1, interval=5, timeout=180)
        tower_pod = openshift_utils.get_tower_pods().pop()

        # verify API contents
        v2.ping.get()

        # verify that jobs run
        jt = factories.v2_job_template()
        job = jt.launch().wait_until_completed()
        assert job.is_successful
        assert job.execution_node == tower_pod

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/7934')
    def test_verify_jobs_fail_with_execution_node_death(self, v2, factories):
        openshift_utils.scale_dc(dc='tower', replicas=2)
        utils.poll_until(lambda: openshift_utils.get_tower_pods_number() == 2, interval=5, timeout=180)
        utils.poll_until(lambda: v2.instances.get(cpu__gt=0).count == 2, interval=5, timeout=600)
        execution_node = openshift_utils.get_tower_pods().pop()

        ig = factories.instance_group()
        instance = v2.instances.get(hostname=execution_node).results.pop()
        ig.add_instance(instance)

        jt = factories.v2_job_template(playbook='sleep.yml', extra_vars='{"sleep_interval": 180}')
        jt.add_instance_group(ig)
        factories.v2_host(inventory=jt.ds.inventory)

        job = jt.launch()

        ret = subprocess.call('oc delete pod {0}'.format(execution_node), shell=True)
        assert ret == 0

        assert job.wait_until_completed(timeout=600).status == 'failed'
        assert job.job_explanation == 'Task was marked as running in Tower but was not present in the job queue, ' \
                                      'so it has been marked as failed.'
