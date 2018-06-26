import random

from towerkit import utils
import towerkit.exceptions as exc
import pytest


from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.nondestructive
@pytest.mark.mp_group('InstanceGroups', 'isolated_serial')
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

    def check_resource_is_being_used(self, error, unified_job):
        assert error.value[1] == {
                'active_jobs': [{
                    u'type': unicode(unified_job.type),
                    u'id': unified_job.id
                }],
                'error': u'Resource is being used by running jobs.'}

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

    def test_instance_group_capacity_should_adjust_for_new_instance_capacity_adjustment(self, factories,
                                                                                        tower_instance_group,
                                                                                        reset_instance):
        ig = factories.instance_group()
        instance = tower_instance_group.related.instances.get().results.pop()
        ig.add_instance(instance)
        assert ig.get().capacity == instance.capacity

        reset_instance(instance)
        instance.capacity_adjustment = '0.00'
        utils.poll_until(lambda: instance.get().capacity == min(instance.cpu_capacity, instance.mem_capacity),
                         interval=1, timeout=30)

    def test_instance_group_capacity_should_adjust_for_enabling_and_disabling_instances(self, factories,
                                                                                        tower_instance_group,
                                                                                        reset_instance):
        ig = factories.instance_group()
        instance = tower_instance_group.related.instances.get().results.pop()
        initial_capacity = instance.capacity

        ig.add_instance(instance)
        utils.poll_until(lambda: ig.get().capacity == instance.capacity, interval=1, timeout=30)

        reset_instance(instance)
        instance.enabled = False
        utils.poll_until(lambda: instance.get().capacity == 0, interval=1, timeout=30)

        instance.enabled = True
        utils.poll_until(lambda: ig.get().capacity == initial_capacity, interval=1, timeout=30)

    def test_conflict_exception_when_attempting_to_delete_ig_with_running_job(self, factories, tower_instance_group):
        instance = random.sample(tower_instance_group.related.instances.get().results, 1).pop()
        ig = factories.instance_group()
        ig.add_instance(instance)

        jt = factories.v2_job_template(playbook='sleep.yml', extra_vars=dict(sleep_interval=360))
        factories.v2_host(inventory=jt.ds.inventory)
        jt.add_instance_group(ig)

        job = jt.launch()

        utils.poll_until(lambda: job.get().status == 'running', interval=5, timeout=60)

        with pytest.raises(exc.Conflict) as error:
            ig.delete()

        self.check_resource_is_being_used(error, job)

    def test_conflict_exception_when_attempting_to_delete_ig_with_running_project_update(self, factories, tower_instance_group):
        instance = random.sample(tower_instance_group.related.instances.get().results, 1).pop()
        ig = factories.instance_group()
        ig.add_instance(instance)

        project = factories.v2_project(scm_url='https://github.com/ansible/ansible.git', scm_delete_on_update=True)
        project.ds.organization.add_instance_group(ig)

        pu = project.update()

        utils.poll_until(lambda: pu.get().status == 'running', interval=5, timeout=60)

        with pytest.raises(exc.Conflict) as error:
            ig.delete()

        self.check_resource_is_being_used(error, pu)

    def test_conflict_exception_when_attempting_to_delete_ig_with_running_inventory_update(self,
                                                                                           factories,
                                                                                           tower_instance_group,
                                                                                           inventory_script_code_with_sleep):
        instance = random.sample(tower_instance_group.related.instances.get().results, 1).pop()
        ig = factories.instance_group()
        ig.add_instance(instance)

        inv_script = factories.v2_inventory_script(script=inventory_script_code_with_sleep(20))
        inventory_source = factories.v2_inventory_source(inventory_script=inv_script)
        inventory_source.ds.inventory.add_instance_group(ig)

        iu = inventory_source.update()

        utils.poll_until(lambda: iu.get().status == 'running', interval=5, timeout=60)

        with pytest.raises(exc.Conflict) as error:
            ig.delete()

        self.check_resource_is_being_used(error, iu)

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

    def test_instance_group_names_do_not_allow_unicode(self, factories):
        title = utils.random_title()

        with pytest.raises(exc.BadRequest) as e:
            factories.instance_group(name=title)
        assert e.value[1]['name'] == [u'{0} contains unsupported characters'.format(title)]

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
