import random

from towerkit import utils
import towerkit.exceptions as exc
import pytest


from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.nondestructive
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestInstanceGroups(Base_Api_Test):

    def find_expected_capacity(self, ig):
        capacity = 0
        for instance in ig.related.instances.get().results:
            capacity += instance.capacity
        return capacity

    def find_expected_consumed_capacity(self, ig):
        consumed_capacity = 0
        for instance in ig.related.instances.get().results:
            consumed_capacity += instance.consumed_capacity
        return consumed_capacity

    def test_instance_group_capacity_should_be_sum_of_individual_instances(self, factories, tower_instance_group):
        tower_hostnames = [instance.hostname for instance in tower_instance_group.related.instances.get().results]
        ig = factories.instance_group(policy_instance_list=tower_hostnames)
        utils.poll_until(lambda: ig.get().instances == len(tower_hostnames), interval=1, timeout=30)

        assert ig.get().capacity == self.find_expected_capacity(ig)
        assert ig.consumed_capacity == self.find_expected_consumed_capacity(ig)

    def test_instance_group_capacity_should_update_for_added_instances(self, factories, tower_instance_group):
        ig = factories.instance_group()
        assert ig.instances == 0

        num_instances = 0
        for instance in tower_instance_group.related.instances.get().results:
            num_instances += 1
            ig.add_instance(instance)
            assert ig.get().instances == num_instances
            assert ig.capacity == self.find_expected_capacity(ig)
            assert ig.consumed_capacity == self.find_expected_consumed_capacity(ig)

    def test_instance_group_capacity_should_update_for_removed_instances(self, factories, tower_instance_group):
        ig = factories.instance_group()
        num_instances = 0
        for instance in tower_instance_group.related.instances.get().results:
            num_instances += 1
            ig.add_instance(instance)
            assert ig.get().instances == num_instances
            assert ig.capacity == self.find_expected_capacity(ig)
            assert ig.consumed_capacity == self.find_expected_consumed_capacity(ig)

        for instance in tower_instance_group.related.instances.get().results:
            num_instances -= 1
            ig.remove_instance(instance)
            assert ig.get().instances == num_instances
            assert ig.capacity == self.find_expected_capacity(ig)
            assert ig.consumed_capacity == self.find_expected_consumed_capacity(ig)

    @pytest.mark.parametrize('resource_name, method', [('job_template', 'launch'),
                                                       ('project', 'update'),
                                                       ('inventory_source', 'update')],
                             ids=['job', 'project_update', 'inventory_update'])
    def test_conflict_exception_when_attempting_to_delete_ig_with_running_uj(self, factories, tower_instance_group,
                                                                             resource_name, method):
        instance = random.sample(tower_instance_group.related.instances.get().results, 1).pop()
        ig = factories.instance_group()
        ig.add_instance(instance)

        resource = getattr(factories, 'v2_' + resource_name)()

        if resource_name == 'job_template':
            resource.add_instance_group(ig)
        elif resource_name == 'project':
            resource.ds.organization.add_instance_group(ig)
        else:
            resource.ds.inventory.add_instance_group(ig)

        uj = getattr(resource, method)()

        with pytest.raises(exc.Conflict) as e:
            ig.delete()
        assert e.value[1] == dict(active_jobs=[dict(type=uj.type, id=str(uj.id))],
                                  error='Resource is being used by running jobs.')

    def test_verify_tower_instance_group_is_a_partially_protected_group(self, tower_instance_group):
        instances = [instance for instance in tower_instance_group.related.instances.get().results]

        tower_instance_group.policy_instance_percentage = tower_instance_group.policy_instance_percentage
        tower_instance_group.policy_instance_minimum = tower_instance_group.policy_instance_minimum
        tower_instance_group.policy_instance_list = tower_instance_group.policy_instance_list
        tower_instance_group.put()

        for instance in instances:
            tower_instance_group.remove_instance(instance)
            tower_instance_group.add_instance(instance)

        with pytest.raises(exc.Forbidden):
            tower_instance_group.delete()

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
