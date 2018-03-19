import towerkit.exceptions as exc
import pytest


from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.nondestructive
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestInstanceGroups(Base_Api_Test):

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/7936')
    def test_conflict_exception_when_attempting_to_delete_ig_with_running_job(self, v2, factories):
        instance = v2.instances.get().results.pop()
        ig = factories.instance_group()
        ig.add_instance(instance)

        jt = factories.v2_job_template(playbook='sleep.yml', extra_vars='{"sleep_interval": 30}')
        jt.launch()

        with pytest.raises(exc.Conflict):
            ig.delete()

    def test_verify_instance_group_read_only_fields(self, factories):
        ig = factories.instance_group()
        original_json = ig.json

        ig.capacity = 777
        ig.committed_capacity = 777
        ig.consumed_capacity = 9000
        ig.percent_capacity_remaining = 77.7
        ig.jobs_running = 777
        ig.instances = 777
        ig.controller = 'ec2-fake-instance.com'

        ig.get()
        for field in ('capacity', 'committed_capacity', 'consumed_capacity', 'percent_capacity_remaining',
                      'jobs_running', 'instances', 'controller'):
            assert getattr(ig, field) == original_json[field]

    def test_verify_tower_instance_group_is_a_protected_group(self, v2, tower_instance_group):
        instances = [instance.hostname for instance in v2.instances.get().results]

        with pytest.raises(exc.Forbidden):
            tower_instance_group.policy_instance_percentage = 100
        with pytest.raises(exc.Forbidden):
            tower_instance_group.policy_instance_minimum = 0
        with pytest.raises(exc.Forbidden):
            tower_instance_group.policy_instance_list = instances
        with pytest.raises(exc.Forbidden):
            tower_instance_group.put()

        with pytest.raises(exc.Forbidden):
            tower_instance_group.delete()
