import pytest

from towerkit import utils

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.mp_group(group="TestInstances", strategy="isolated_serial")
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestInstances(Base_Api_Test):
    def find_expected_capacity(self, instance):
        return int(float(instance.capacity_adjustment) * abs(instance.mem_capacity - instance.cpu_capacity) +
               min(instance.mem_capacity, instance.cpu_capacity))

    @pytest.mark.github('https://github.com/ansible/tower/issues/1713')
    def test_jobs_should_not_run_on_disabled_instances(self, request, v2, factories):
        ig = factories.instance_group()
        instance = v2.instances.get(rampart_groups__controller__isnull=True).results.pop()
        ig.add_instance(instance)
        utils.poll_until(lambda: ig.get().instances == 1, interval=5, timeout=30)

        jt = factories.v2_job_template()
        factories.v2_host(inventory=jt.ds.inventory)
        jt.add_instance_group(ig)

        request.addfinalizer(lambda: instance.patch(enabled=True))
        instance.enabled = False

        job = jt.launch()
        utils.logged_sleep(30)
        assert job.get().status == 'pending'

    @pytest.mark.github('https://github.com/ansible/tower/issues/1713')
    def test_jobs_should_resume_on_newly_enabled_instances(self, request, v2, factories):
        ig = factories.instance_group()
        instance = v2.instances.get(rampart_groups__controller__isnull=True).results.pop()
        ig.add_instance(instance)
        utils.poll_until(lambda: ig.get().instances == 1, interval=5, timeout=30)

        jt = factories.v2_job_template()
        factories.v2_host(inventory=jt.ds.inventory)
        jt.add_instance_group(ig)

        request.addfinalizer(lambda: instance.patch(enabled=True))
        instance.enabled = False
        job = jt.launch()

        utils.logged_sleep(30)
        assert job.get().status == 'pending'

        instance.enabled = True
        assert job.wait_until_completed(timeout=120).is_successful

    @pytest.mark.github('https://github.com/ansible/tower/issues/1713')
    def test_disabiling_instance_should_not_impact_currently_running_jobs(self, request, v2, factories,
                                                                          tower_version):
        ig = factories.instance_group()
        instance = v2.instances.get(rampart_groups__controller__isnull=True).results.pop()
        ig.add_instance(instance)
        utils.poll_until(lambda: ig.related.instances.get(version=tower_version).count == 1, timeout=30)

        jt = factories.v2_job_template(playbook='sleep.yml', extra_vars='{"sleep_interval": 30}')
        factories.v2_host(inventory=jt.ds.inventory)
        jt.add_instance_group(ig)

        job = jt.launch()
        utils.poll_until(lambda: job.get().execution_node == instance.hostname, interval=1, timeout=30)

        request.addfinalizer(lambda: instance.patch(enabled=True))
        instance.enabled = False
        assert job.wait_until_completed().is_successful

    @pytest.mark.github('https://github.com/ansible/tower/issues/1713')
    def test_disabiling_instance_should_set_capacity_to_zero(self, request, v2, factories):
        instance = v2.instances.get(rampart_groups__controller__isnull=True).results.pop()
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

    @pytest.mark.parametrize('capacity_adjustment', ['0', '.25', '.5', '.75', '1'])
    def test_instance_capacity_updates_for_percent_capacity_remaining(self, request, v2, capacity_adjustment):
        instance = v2.instances.get(rampart_groups__controller__isnull=True).results.pop()
        request.addfinalizer(lambda: instance.patch(capacity_adjustment='1'))
        instance.capacity_adjustment = capacity_adjustment

        assert instance.capacity == self.find_expected_capacity(instance)

    def test_verify_instance_read_only_fields(self, v2):
        instance = v2.instances.get(rampart_groups__controller__isnull=True).results.pop()
        original_json = instance.json

        instance.uuid = '77777777-7777-7777-7777-777777777777'
        instance.hostname = 'ec2-fake-instance.com'
        instance.version = '7.7.7.777'
        instance.capacity = 777
        instance.consumed_capacity = 777
        instance.percent_capacity_remaining = 77.7
        instance.jobs_running = 777
        instance.cpu = 777
        instance.memory = 777
        instance.cpu_capacity = 777
        instance.mem_capacity = 777

        instance.get()
        for field in ('uuid', 'hostname', 'version', 'capacity', 'consumed_capacity', 'percent_capacity_remaining',
                      'jobs_running', 'cpu', 'memory', 'cpu_capacity', 'mem_capacity'):
            assert getattr(instance, field) == original_json[field]
