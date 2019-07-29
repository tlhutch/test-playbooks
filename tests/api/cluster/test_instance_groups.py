import random

from towerkit import utils
import towerkit.exceptions as exc
import pytest


from tests.api import APITest


@pytest.mark.serial
@pytest.mark.usefixtures('authtoken')
class TestInstanceGroups(APITest):

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
        assert 'error' in error.value[1]
        assert 'active_jobs' in error.value[1]
        assert error.value[1]['error'] == 'Resource is being used by running jobs.'
        assert {
            'type': str(unified_job.type),
            'id': unified_job.id
        } in error.value[1]['active_jobs']

    def test_instance_group_capacity_should_be_sum_of_individual_instances(self, factories, active_instances):
        hostnames = [instance.hostname for instance in active_instances.results]
        ig = factories.instance_group(policy_instance_list=hostnames)
        utils.poll_until(lambda: ig.get().instances == len(hostnames), interval=1, timeout=30)

        assert ig.get().capacity == self.find_expected_capacity(ig)
        assert ig.consumed_capacity == self.find_expected_consumed_capacity(ig)

    @pytest.mark.yolo
    def test_instance_group_capacity_should_update_for_added_instances(self, factories, active_instances):
        ig = factories.instance_group()
        assert ig.instances == 0

        num_instances = 0
        for instance in active_instances.results:
            num_instances += 1
            ig.add_instance(instance)
            assert ig.get().instances == num_instances
            assert ig.capacity == self.find_expected_capacity(ig)
            assert ig.consumed_capacity == self.find_expected_consumed_capacity(ig)

    def test_instance_group_capacity_should_update_for_removed_instances(self, factories, active_instances):
        ig = factories.instance_group()
        num_instances = 0
        for instance in active_instances.results:
            num_instances += 1
            ig.add_instance(instance)
            assert ig.get().instances == num_instances
            assert ig.capacity == self.find_expected_capacity(ig)
            assert ig.consumed_capacity == self.find_expected_consumed_capacity(ig)

        for instance in active_instances.results:
            num_instances -= 1
            ig.remove_instance(instance)
            assert ig.get().instances == num_instances
            assert ig.capacity == self.find_expected_capacity(ig)
            assert ig.consumed_capacity == self.find_expected_consumed_capacity(ig)

    def test_instance_group_capacity_should_adjust_for_new_instance_capacity_adjustment(self, factories,
                                                                                        active_instances,
                                                                                        reset_instance):
        ig = factories.instance_group()
        instance = active_instances.results.pop()
        ig.add_instance(instance)
        assert ig.get().capacity == instance.capacity

        reset_instance(instance)
        instance.capacity_adjustment = '0.00'
        utils.poll_until(lambda: instance.get().capacity == min(instance.cpu_capacity, instance.mem_capacity),
                         interval=1, timeout=30)

    def test_instance_group_capacity_should_adjust_for_enabling_and_disabling_instances(self, factories,
                                                                                        active_instances,
                                                                                        reset_instance):
        ig = factories.instance_group()
        instance = active_instances.results.pop()
        initial_capacity = instance.capacity

        ig.add_instance(instance)
        utils.poll_until(lambda: ig.get().capacity == instance.capacity, interval=1, timeout=30)

        reset_instance(instance)
        instance.enabled = False
        utils.poll_until(lambda: instance.get().capacity == 0, interval=1, timeout=30)

        instance.enabled = True
        utils.poll_until(lambda: ig.get().capacity == initial_capacity, interval=1, timeout=30)

    def test_that_instance_groups_not_duplicated(self, v2, factories):
        """Test that when a user is the admin of two organizations that both use the same instance group,
        instance groups are not duplicated in API responses."""
        # Create test objects
        ig = factories.instance_group()
        user = factories.user()
        org1 = factories.organization()
        org2 = factories.organization()

        # Assign the user as admin to both the organizations
        org1.set_object_roles(user, 'admin')
        org2.set_object_roles(user, 'admin')

        # Add the same instance group to both the organizations
        with pytest.raises(exc.NoContent):
            org1.related.instance_groups.post(dict(id=ig.id))
        with pytest.raises(exc.NoContent):
            org2.related.instance_groups.post(dict(id=ig.id))

    # Login as the test user and gather instance groups
        with self.current_user(user.username, user.password):
            instance_names = [instance.name for instance in v2.instance_groups.get().results]

    # Assert that the instance group we added is present, and is not duplicated
        assert len(instance_names) == 1, f"Unexpected number of instance groups! Found {instance_names}"
        assert instance_names == [ig.name], f"Unexpected name of instance groups! Found {instance_names}"

    def test_conflict_exception_when_attempting_to_delete_ig_with_running_job(self, factories, active_instances):
        instance = random.sample(active_instances.results, 1).pop()
        ig = factories.instance_group()
        ig.add_instance(instance)

        jt = factories.job_template(playbook='sleep.yml', extra_vars=dict(sleep_interval=360))
        factories.host(inventory=jt.ds.inventory)
        jt.add_instance_group(ig)

        job = jt.launch()

        utils.poll_until(lambda: job.get().status == 'running', interval=5, timeout=60)

        with pytest.raises(exc.Conflict) as error:
            ig.delete()

        self.check_resource_is_being_used(error, job)

    def test_conflict_exception_when_attempting_to_delete_ig_with_running_project_update(self, factories, active_instances):
        instance = random.sample(active_instances.results, 1).pop()
        ig = factories.instance_group()
        ig.add_instance(instance)

        project = factories.project(scm_url='https://github.com/ansible/ansible.git', scm_delete_on_update=True)
        project.ds.organization.add_instance_group(ig)

        assert ig.related.instances.get().count == 1  # test flake due to github.com/ansible/tower/issues/2772

        pu = project.update()

        utils.poll_until(lambda: pu.get().status == 'running', interval=5, timeout=60)

        with pytest.raises(exc.Conflict) as error:
            ig.delete()

        self.check_resource_is_being_used(error, pu)

    def test_conflict_exception_when_attempting_to_delete_ig_with_running_inventory_update(self,
                                                                                           factories,
                                                                                           active_instances,
                                                                                           inventory_script_code_with_sleep):
        instance = random.sample(active_instances.results, 1).pop()
        ig = factories.instance_group()
        ig.add_instance(instance)

        inv_script = factories.inventory_script(script=inventory_script_code_with_sleep(20))
        inv_source = factories.inventory_source(source_script=inv_script)
        assert inv_source.source_script == inv_script.id
        inv_source.ds.inventory.add_instance_group(ig)

        iu = inv_source.update()

        utils.poll_until(lambda: iu.get().status == 'running', interval=5, timeout=60)

        with pytest.raises(exc.Conflict) as error:
            ig.delete()

        self.check_resource_is_being_used(error, iu)

    @pytest.mark.yolo
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


@pytest.mark.serial
@pytest.mark.usefixtures('authtoken', 'skip_if_not_cluster')
class TestInstanceGroupOrderOnObjects(APITest):

    def test_instance_group_order_respected(self, v2, factories):
        """A list of instance groups on an object should be ordered, and that order should be respected when launching
        jobs.
        """
        instance_groups = v2.instance_groups.get().results
        instance_group_ids = [ig.id for ig in instance_groups]
        instance_group_ids_to_instances_map = {ig.id: ig.policy_instance_list for ig in instance_groups}
        org = factories.organization()
        inv = factories.inventory(organization=org)
        jt_with_igs = factories.job_template(inventory=inv, organization=org)
        jt = factories.job_template(inventory=inv, organization=org)
        org_igs = instance_group_ids[1::2]
        jt_igs = org_igs[1::2]
        jt_igs.reverse()
        assert jt_igs[0] != org_igs[0]
        for ig in org_igs:
            with pytest.raises(exc.NoContent):
                org.related.instance_groups.post(dict(id=ig, associate=True))
        actual_org_igs = org.related.instance_groups.get().results
        actual_org_igs = [ig.id for ig in actual_org_igs]
        assert actual_org_igs == org_igs

        for ig in jt_igs:
            with pytest.raises(exc.NoContent):
                jt_with_igs.related.instance_groups.post(dict(id=ig, associate=True))
        actual_jt_igs = jt_with_igs.related.instance_groups.get().results
        actual_jt_igs = [ig.id for ig in actual_jt_igs]
        assert actual_jt_igs == jt_igs

        job_default_org_ig = jt.launch().wait_until_completed()
        job_default_org_ig.assert_successful()
        job_from_jt_with_ig = jt_with_igs.launch().wait_until_completed()
        job_from_jt_with_ig.assert_successful()
        # Assert job used appropriate execution node
        assert job_default_org_ig.execution_node in instance_group_ids_to_instances_map[org_igs[0]]
        assert job_from_jt_with_ig.execution_node in instance_group_ids_to_instances_map[jt_igs[0]]
