import pytest

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.nondestructive
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestInstances(Base_Api_Test):
    def test_verify_instance_read_only_fields(self, v2):
        instance = v2.instances.get().results.pop()
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
