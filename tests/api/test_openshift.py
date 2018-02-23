import subprocess

from openshift.helper.openshift import OpenShiftObjectHelper
from towerkit import utils
import towerkit.exceptions as exc
import pytest

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.mp_group('OpenShift', 'serial')
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestOpenShift(Base_Api_Test):

    @pytest.fixture(autouse=True)
    def prepare_environment(self):
        # FIXME: remove 'fo0m4nchU' and update vault file
        ret = subprocess.call('oc login -u jenkins -p fo0m4nchU --insecure-skip-tls-verify=true '
                              'https://console.openshift.ansible.eng.rdu2.redhat.com', shell=True)
        assert ret == 0

        ret = subprocess.call('oc project tower-qe', shell=True)
        assert ret == 0

    def get_pods(self):
        client = OpenShiftObjectHelper(api_version='v1', kind='pod_list')
        ret = client.get_object(namespace='tower-qe')
        return [i.metadata.name for i in ret.items]

    def get_tower_pods(self):
        pods = self.get_pods()
        return [pod for pod in pods if 'tower' in pod]

    def get_tower_pods_number(self):
        return len(self.get_tower_pods())

    def scale_dc(self, dc, replicas):
        cmd = 'oc scale dc {0} --replicas={1}'.format(dc, str(replicas))
        ret = subprocess.call(cmd, shell=True)
        assert ret == 0

    @pytest.fixture
    def tower_ig_contains_all_instances(v2, tower_instance_group):
        def func():
            return set(instance.id for instance in v2.instances.get().results) == \
                   set(instance.id for instance in tower_instance_group.related.instances.get().results)
        return func

    def test_scale_up_tower_pod(self, v2, tower_instance_group, tower_version, tower_ig_contains_all_instances):
        self.scale_dc(dc='tower', replicas=3)
        utils.poll_until(lambda: self.get_tower_pods_number() == 3, interval=5, timeout=180)
        tower_pods = set(self.get_tower_pods())

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
        self.scale_dc(dc='tower', replicas=1)
        utils.poll_until(lambda: self.get_tower_pods_number() == 1, interval=5, timeout=180)
        tower_pods = set(self.get_tower_pods())

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
        self.scale_dc(dc='tower', replicas=0)
        utils.poll_until(lambda: self.get_tower_pods_number() == 0, interval=5, timeout=180)

        self.scale_dc(dc='tower', replicas=1)
        utils.poll_until(lambda: self.get_tower_pods_number() == 1, interval=5, timeout=180)
        tower_pod = self.get_tower_pods().pop()

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
        jt.add_instance_group()
        job = jt.launch().wait_until_completed(timeout=180)
        assert job.is_successful
        assert job.execution_node == tower_pod

    def test_tower_stability_while_scaling_etcd_pod(self, v2, factories):
        jt = factories.v2_job_template()

        # assess tower functionality with multiple etcd pods
        self.scale_dc(dc='etcd', replicas=2)
        utils.poll_until(lambda: len([pod for pod in self.get_pods() if 'etcd' in pod]) == 2, interval=5, timeout=180)
        v2.ping.get()
        assert jt.launch().wait_until_completed().is_successful

        # assess tower functionality with one etcd pod
        self.scale_dc(dc='etcd', replicas=1)
        utils.poll_until(lambda: len([pod for pod in self.get_pods() if 'etcd' in pod]) == 1, interval=5, timeout=180)
        v2.ping.get()
        assert jt.launch().wait_until_completed().is_successful

    def test_tower_should_be_able_to_recover_from_zero_etcd_pods(self, v2, factories):
        self.scale_dc(dc='etcd', replicas=0)
        utils.poll_until(lambda: len([pod for pod in self.get_pods() if 'etcd' in pod]) == 0, interval=5, timeout=180)

        self.scale_dc(dc='etcd', replicas=1)
        utils.poll_until(lambda: len([pod for pod in self.get_pods() if 'etcd' in pod]) == 1, interval=5, timeout=180)
        tower_pod = self.get_tower_pods().pop()

        # verify API contents
        v2.ping.get()

        # verify that jobs run
        jt = factories.v2_job_template()
        job = jt.launch().wait_until_completed()
        assert job.is_successful
        assert job.execution_node == tower_pod

    def test_jobs_should_distribute_among_tower_instance_group_members(self, factories, v2, tower_instance_group):
        self.scale_dc(dc='tower', replicas=2)
        utils.poll_until(lambda: self.get_tower_pods_number() == 2, interval=5, timeout=180)
        utils.poll_until(lambda: v2.instances.get(cpu__gt=0).count == 2, interval=5, timeout=600)

        jt = factories.v2_job_template(allow_simultaneous=True)
        jt.add_instance_group(tower_instance_group)

        for _ in range(5):
            jt.launch()
        jobs = jt.related.jobs.get()
        utils.poll_until(lambda: jobs.get(status='successful').count == 5, interval=5, timeout=300)

        tower_pods = self.get_tower_pods()
        pod1_jobs = [job for job in jobs.results if job.execution_node == tower_pods[0]]
        pod2_jobs = [job for job in jobs.results if job.execution_node == tower_pods[1]]
        assert len(pod1_jobs) > 0
        assert len(pod2_jobs) > 0

    def test_jobs_should_distribute_among_new_instance_group_members(self, factories, v2, tower_instance_group):
        self.scale_dc(dc='tower', replicas=2)
        utils.poll_until(lambda: self.get_tower_pods_number() == 2, interval=5, timeout=180)
        utils.poll_until(lambda: v2.instances.get(cpu__gt=0).count == 2, interval=5, timeout=600)

        ig = factories.instance_group()
        instances = v2.instances.get().results
        for instance in instances:
            ig.add_instance(instance)
        assert ig.related.instances.get().count == 2
        assert set(instance.id for instance in ig.related.instances.get().results) == \
               set(instance.id for instance in instances)

        jt = factories.v2_job_template(allow_simultaneous=True)
        jt.add_instance_group(tower_instance_group)

        for _ in range(5):
            jt.launch()
        jobs = jt.related.jobs.get()
        utils.poll_until(lambda: jobs.get(status='successful').count == 5, interval=5, timeout=300)

        tower_pods = self.get_tower_pods()
        pod1_jobs = [job for job in jobs.results if job.execution_node == tower_pods[0]]
        pod2_jobs = [job for job in jobs.results if job.execution_node == tower_pods[1]]
        assert len(pod1_jobs) > 0
        assert len(pod2_jobs) > 0

    # VERIFY
    def test_jobs_should_distribute_among_mutually_exclusive_instance_groups(self, factories, v2):
        self.scale_dc(dc='tower', replicas=2)
        utils.poll_until(lambda: self.get_tower_pods_number() == 2, interval=5, timeout=180)
        utils.poll_until(lambda: v2.instances.get(cpu__gt=0).count == 2, interval=5, timeout=600)

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

        tower_pods = self.get_tower_pods()
        pod1_jobs = [job for job in jobs.results if job.execution_node == tower_pods[0]]
        pod2_jobs = [job for job in jobs.results if job.execution_node == tower_pods[1]]
        assert len(pod1_jobs) > 0
        assert len(pod2_jobs) > 0

    # VERIFY
    def test_jobs_should_distribute_among_partially_overlapping_instance_groups(self, factories, v2):
        self.scale_dc(dc='tower', replicas=3)
        utils.poll_until(lambda: self.get_tower_pods_number() == 3, interval=5, timeout=180)
        utils.poll_until(lambda: v2.instances.get(cpu__gt=0).count == 3, interval=5, timeout=600)

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

        tower_pods = self.get_tower_pods()
        pod1_jobs = [job for job in jobs.results if job.execution_node == tower_pods[0]]
        pod2_jobs = [job for job in jobs.results if job.execution_node == tower_pods[1]]
        pod3_jobs = [job for job in jobs.results if job.execution_node == tower_pods[2]]
        assert len(pod1_jobs) > 0
        assert len(pod2_jobs) > 0
        assert len(pod3_jobs) > 0

    # VERIFY
    def test_jobs_should_distribute_among_completely_overlapping_instance_groups(self, factories, v2):
        self.scale_dc(dc='tower', replicas=2)
        utils.poll_until(lambda: self.get_tower_pods_number() == 2, interval=5, timeout=180)
        utils.poll_until(lambda: v2.instances.get(cpu__gt=0).count == 2, interval=5, timeout=600)

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

        tower_pods = self.get_tower_pods()
        pod1_jobs = [job for job in jobs.results if job.execution_node == tower_pods[0]]
        pod2_jobs = [job for job in jobs.results if job.execution_node == tower_pods[1]]
        assert len(pod1_jobs) > 0
        assert len(pod2_jobs) > 0

    def test_jt_with_no_instance_groups_defaults_to_tower_instance_group_instance(self, factories, tower_instance_group):
        jt = factories.v2_job_template()
        job = jt.launch().wait_until_completed()
        assert job.is_successful

        tower_pods = self.get_tower_pods()
        assert job.execution_node in tower_pods

    # FIXME: provide teardown
    # FIXME: we are disabling 100% of the instances, so the pre-job project sync stays pending indefinitely
    # FIXME: update test plan if necessary
    def test_jobs_should_not_run_on_disabled_instances(self, factories, v2, tower_instance_group):
        self.scale_dc(dc='tower', replicas=2)
        utils.poll_until(lambda: self.get_tower_pods_number() == 2, interval=5, timeout=180)
        utils.poll_until(lambda: v2.instances.get(cpu__gt=0).count == 2, interval=5, timeout=600)

        ig = factories.instance_group()
        instances = v2.instances.get().results
        for instance in instances:
            ig.add_instance(instance)
            instance.enabled = False
        utils.poll_until(lambda: ig.get().instances == 2, interval=5, timeout=300)

        jt = factories.v2_job_template(playbook='sleep.yml', allow_simultaneous=True, extra_vars='{"sleep_interval": 60}')
        factories.v2_host(inventory=jt.ds.inventory)
        jt.add_instance_group(ig)
        for _ in range(5):
            jt.launch()
        jobs = jt.related.jobs.get()

        utils.logged_sleep(30)
        assert jobs.get(status='pending').count == 5

    def test_jobs_should_resume_on_newly_enabled_instances(self, request, v2, factories):
        self.scale_dc(dc='tower', replicas=2)
        utils.poll_until(lambda: self.get_tower_pods_number() == 2, interval=5, timeout=180)
        utils.poll_until(lambda: v2.instances.get(cpu__gt=0).count == 2, interval=5, timeout=600)

        project = factories.v2_project()

        ig = factories.instance_group()
        instances = v2.instances.get().results
        for instance in instances:
            ig.add_instance(instance)
            request.addfinalizer(lambda: instance.patch(enabled=True))
            instance.enabled = False
        utils.poll_until(lambda: ig.get().instances == 2, interval=5, timeout=300)

        jt = factories.v2_job_template(project=project)
        factories.v2_host(inventory=jt.ds.inventory)
        job = jt.launch()

        utils.logged_sleep(30)
        assert job.get().status == 'pending'

        for instance in v2.instances.get().results:
            instance.enabled = True
        assert job.wait_until_completed(timeout=300).is_successful

    def test_disabiling_instance_should_not_impact_currently_running_jobs(self, request, v2, factories):
        self.scale_dc(dc='tower', replicas=2)
        utils.poll_until(lambda: self.get_tower_pods_number() == 2, interval=5, timeout=180)
        utils.poll_until(lambda: v2.instances.get(cpu__gt=0).count == 2, interval=5, timeout=600)

        instance = v2.instances.get().results.pop()
        request.addfinalizer(lambda: instance.patch(enabled=True))

        ig = factories.instance_group()
        ig.add_instance(instance)
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
        request.addfinalizer(lambda: instance.patch(enabled=True))

        assert instance.capacity == max(instance.mem_capacity, instance.cpu_capacity)

        instance.enabled = False
        assert instance.capacity == 0

        instance.enabled = True
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

        instances = tower_instance_group.related.instances.get().results
        for instance in instances:
            ig.add_instance(instance)

        assert job.wait_until_completed(timeout=180).is_successful

    # FIXME: report tower issue
    def test_verify_jobs_fail_with_execution_node_death(self, v2, factories):
        ig = factories.instance_group()
        instance = v2.instances.get().results.pop()
        ig.add_instance(instance)

        jt = factories.v2_job_template()
        jt.add_instance_group(ig)
        job = jt.launch()

        # kill pod
        ret = subprocess.call('oc delete pod {0}'.format(instance.hostname), shell=True)
        assert ret == 0

        assert job.wait_until_completed().status == 'failed'
