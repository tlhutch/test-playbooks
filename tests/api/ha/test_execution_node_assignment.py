import random

from towerkit import utils
import pytest

from tests.lib.helpers import openshift_utils
from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.requires_ha
@pytest.mark.mp_group('ExecutionNodeAssignment', 'serial')
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestExecutionNodeAssignment(Base_Api_Test):

    @pytest.fixture(autouse=True)
    def prepare_openshift_environment(self, is_docker):
        if not is_docker:
            return
        else:
            openshift_utils.prep_environment()

    def test_jobs_should_distribute_among_tower_instance_group_members(self, factories, v2, tower_instance_group):
        jt = factories.v2_job_template(allow_simultaneous=True)
        jt.add_instance_group(tower_instance_group)

        for _ in range(15):
            jt.launch()
        jobs = jt.related.jobs.get()
        utils.poll_until(lambda: jobs.get(status='successful').count == 15, interval=5, timeout=300)

        instances = [instance.hostname for instance in v2.instances.get().results]
        job_execution_nodes = [job.execution_node for job in jobs.results]
        assert set(job_execution_nodes) == set(instances)

    def test_jt_with_no_instance_groups_defaults_to_tower_instance_group_instance(self, factories, v2,
                                                                                  tower_instance_group):
        jt = factories.v2_job_template(allow_simultaneous=True)

        for _ in range(15):
            jt.launch()
        jobs = jt.related.jobs.get()
        utils.poll_until(lambda: jobs.get(status='successful').count == 15, interval=5, timeout=300)

        instances = [instance.hostname for instance in v2.instances.get().results]
        job_execution_nodes = [job.execution_node for job in jobs.results]
        assert set(job_execution_nodes) == set(instances)

    def test_jobs_should_distribute_among_mutually_exclusive_instance_groups(self, request, factories, v2):
        ig1, ig2 = [factories.instance_group() for _ in range(2)]
        instances = random.sample(v2.instances.get().results, 2)
        for instance in instances:
            request.addfinalizer(lambda: instance.patch(capacity_adjustment=1))
            instance.capacity_adjustment = 0
        ig1.add_instance(instances[0])
        ig2.add_instance(instances[1])
        utils.poll_until(lambda: ig1.get().instances == 1 and ig2.get().instances == 1, interval=5, timeout=300)

        jt = factories.v2_job_template(playbook='sleep.yml', allow_simultaneous=True, extra_vars='{"sleep_interval": 60}')
        factories.v2_host(inventory=jt.ds.inventory)
        for ig in (ig1, ig2):
            jt.add_instance_group(ig)

        for _ in range(10):
            jt.launch()
        jobs = jt.related.jobs.get()
        utils.poll_until(lambda: len([job.execution_node for job in jobs.get().results if job.execution_node != '']) == 10,
                         interval=5, timeout=300)

        job_execution_nodes = [job.execution_node for job in jobs.results]
        assert set(job_execution_nodes) == set([instance.hostname for instance in instances])

    @pytest.mark.github('https://github.com/ansible/tower/issues/1179')
    def test_jobs_should_distribute_among_partially_overlapping_instance_groups(self, request, factories, v2):
        ig1, ig2 = [factories.instance_group() for _ in range(2)]
        instances = random.sample(v2.instances.get().results, 3)
        for instance in instances:
            request.addfinalizer(lambda: instance.patch(capacity_adjustment=1))
            instance.capacity_adjustment = 0

        ig1.add_instance(instances[0])
        ig2.add_instance(instances[1])
        for ig in (ig1, ig2):
            ig.add_instance(instances[2])
        utils.poll_until(lambda: ig1.get().instances == 2 and ig2.get().instances == 2, interval=5, timeout=300)

        jt = factories.v2_job_template(playbook='sleep.yml', allow_simultaneous=True, extra_vars='{"sleep_interval": 60}')
        factories.v2_host(inventory=jt.ds.inventory)
        for _ in range(15):
            jt.launch()
        jobs = jt.related.jobs.get()
        utils.poll_until(lambda: len([job.execution_node for job in jobs.get().results if job.execution_node != '']) == 15,
                         interval=5, timeout=300)

        job_execution_nodes = [job.execution_node for job in jobs.results]
        assert set(job_execution_nodes) == set([instance.hostname for instance in instances])

    @pytest.mark.github('https://github.com/ansible/tower/issues/1180')
    def test_jobs_should_distribute_among_completely_overlapping_instance_groups(self, request, factories, v2):
        ig1, ig2 = [factories.instance_group() for _ in range(2)]
        instances = random.sample(v2.instances.get().results, 2)
        for instance in instances:
            request.addfinalizer(lambda: instance.patch(capacity_adjustment=1))
            instance.capacity_adjustment = 0

        for ig in (ig1, ig2):
            for instance in instances:
                ig.add_instance(instance)
        utils.poll_until(lambda: ig1.get().instances == 2 and ig2.get().instances == 2, interval=5, timeout=300)

        jt = factories.v2_job_template(playbook='sleep.yml', allow_simultaneous=True, extra_vars='{"sleep_interval": 60}')
        factories.v2_host(inventory=jt.ds.inventory)
        for _ in range(10):
            jt.launch()
        jobs = jt.related.jobs.get()
        utils.poll_until(lambda: len([job.execution_node for job in jobs.get().results if job.execution_node != '']) == 10,
                         interval=5, timeout=300)

        job_execution_nodes = [job.execution_node for job in jobs.results]
        assert set(job_execution_nodes) == set([instance.hostname for instance in instances])

    @pytest.mark.github('https://github.com/ansible/tower/issues/1177')
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

        job_execution_nodes = [job.execution_node for job in jobs.results]
        assert set(job_execution_nodes) == set([instance.hostname for instance in instances])

    @pytest.mark.parametrize('resource', ['inventory', 'organization', 'both'])
    def test_ahcs_run_on_target_instance_with_resource_ig_assignment(self, factories, v2, resource):
        ig = factories.instance_group()
        instance = v2.instances.get().results.pop()
        ig.add_instance(instance)

        inv = factories.v2_inventory()

        if resource == 'inventory':
            inv.add_instance_group(ig)
        elif resource == 'organization':
            inv.ds.organization.add_instance_group(ig)
        else:
            inv.add_instance_group(ig)
            inv.ds.organization.add_instance_group(ig)

        ahc = factories.v2_ad_hoc_command(inventory=inv, module_name='ping')
        assert ahc.wait_until_completed().is_successful
        assert ahc.execution_node == instance.hostname

    def test_ahcs_should_distribute_among_new_instance_group_members(self, factories, v2):
        ig = factories.instance_group()
        instances = random.sample(v2.instances.get().results, 3)
        for instance in instances:
            ig.add_instance(instance)

        inv = factories.v2_inventory()
        inv.add_instance_group(ig)

        for _ in range(9):
            factories.v2_ad_hoc_command(inventory=inv, module_name='ping')
        ahcs = inv.related.ad_hoc_commands.get()
        utils.poll_until(lambda: ahcs.get(status='successful').count == 9, interval=5, timeout=300)

        ahc_execution_nodes = [ahc.execution_node for ahc in ahcs.results]
        assert set(ahc_execution_nodes) == set([instance.hostname for instance in instances])

    def test_project_updates_run_on_target_instance_via_organization_ig_assignment(self, factories, v2):
        ig = factories.instance_group()
        instance = v2.instances.get().results.pop()
        ig.add_instance(instance)

        project = factories.v2_project()
        project.ds.organization.add_instance_group(ig)

        project_update = project.update()
        assert project_update.wait_until_completed().is_successful
        assert project_update.execution_node == instance.hostname

    def test_project_updates_should_distribute_among_new_instance_group_members(self, factories, v2):
        ig = factories.instance_group()
        instances = random.sample(v2.instances.get().results, 3)
        for instance in instances:
            ig.add_instance(instance)

        project = factories.v2_project()
        project.ds.organization.add_instance_group(ig)
        initial_update = project.get().related.last_update.get()

        for _ in range(9):
            project.update()
        project_updates = project.related.project_updates.get()
        utils.poll_until(lambda: project_updates.get(status='successful', not__id=initial_update.id).count == 9,
                         interval=5, timeout=300)

        update_execution_nodes = [update.execution_node for update in project_updates.results]
        assert set(update_execution_nodes) == set([instance.hostname for instance in instances])

    @pytest.mark.parametrize('resource', ['inventory', 'organization', 'both'])
    def test_inventory_updates_run_on_target_instance_via_resource_ig_assignment(self, factories, v2, resource):
        ig = factories.instance_group()
        instance = v2.instances.get().results.pop()
        ig.add_instance(instance)

        inv_source = factories.v2_inventory_source()
        inv = inv_source.ds.inventory

        if resource == 'inventory':
            inv.add_instance_group(ig)
        elif resource == 'organization':
            inv.ds.organization.add_instance_group(ig)
        else:
            inv.add_instance_group(ig)
            inv.ds.organization.add_instance_group(ig)

        inv_update = inv_source.update()
        assert inv_update.wait_until_completed().is_successful
        assert inv_update.execution_node == instance.hostname

    def test_inventory_updates_should_distribute_among_new_instance_group_members(self, factories, v2):
        ig = factories.instance_group()
        instances = random.sample(v2.instances.get().results, 3)
        for instance in instances:
            ig.add_instance(instance)

        inv_source = factories.v2_inventory_source()
        inv_source.ds.inventory.add_instance_group(ig)

        for _ in range(9):
            inv_source.update()
        inv_updates = inv_source.related.inventory_updates.get()
        utils.poll_until(lambda: inv_updates.get(status='successful').count == 9, interval=5, timeout=300)

        update_execution_nodes = [update.execution_node for update in inv_updates.results]
        assert set(update_execution_nodes) == set([instance.hostname for instance in instances])

    def test_wfjt_node_jobs_run_on_target_instance_via_unified_jt_ig_assignment(self, factories, v2):
        ig = factories.instance_group()
        instance = v2.instances.get().results.pop()
        ig.add_instance(instance)

        wfjt = factories.v2_workflow_job_template()
        jt = factories.v2_job_template()
        inv_source = factories.v2_inventory_source()
        project = jt.ds.project

        node1 = factories.v2_workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)
        node2 = node1.add_always_node(unified_job_template=inv_source)
        node2.add_always_node(unified_job_template=project)

        for resource in (jt, inv_source.ds.inventory, project.ds.organization):
            resource.add_instance_group(ig)

        wfj = wfjt.launch()
        assert wfj.wait_until_completed().is_successful
        assert jt.get().related.last_job.get().execution_node == instance.hostname
        assert inv_source.get().related.last_update.get().execution_node == instance.hostname
        assert project.get().related.last_update.get().execution_node == instance.hostname

    def test_no_execution_node_assigned_with_jt_with_ig_with_no_instances(self, factories):
        ig = factories.instance_group()
        assert ig.instances == 0
        assert ig.capacity == 0

        jt = factories.v2_job_template()
        jt.add_instance_group(ig)
        job = jt.launch()

        utils.logged_sleep(30)

        assert job.get().execution_node == ''
        assert job.status == 'pending'

    def test_execution_node_assigned_with_jt_with_ig_with_recently_added_instance(self, factories,
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

        assert job.wait_until_completed(timeout=300).is_successful
        assert job.execution_node == instance.hostname
