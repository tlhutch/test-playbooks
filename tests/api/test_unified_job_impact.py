from towerkit import utils
import pytest

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.mp_group('UnifiedJobImpact', 'isolated_serial')
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestUnifiedJobImpact(Base_Api_Test):

    @pytest.fixture
    def ig_with_single_instance(self, factories, v2):
        ig = factories.instance_group()
        instance = v2.instances.get().results.pop()
        ig.add_instance(instance)
        return ig

    def unified_job_impact(self, unified_job_type, forks=0, num_hosts=0):
        if unified_job_type in ('job', 'ahc'):
            if forks == 0:
                return min(num_hosts, 5) + 1
            else:
                return min(forks, num_hosts) + 1
        elif unified_job_type in ('inventory_update', 'project_update'):
            return 1
        elif unified_job_type == 'system_job':
            return 5
        elif unified_job_type == 'workflow_job':
            return 0
        raise RuntimeError("Job impact not calculatable for job type {}".format(unified_job_type))

    def assert_instance_reflects_zero_running_jobs(self, instance):
        assert instance.jobs_running == 0
        assert instance.consumed_capacity == 0
        assert instance.percent_capacity_remaining == 100.0

    def assert_instance_group_reflects_zero_running_jobs(self, ig):
        assert ig.jobs_running == 0
        assert ig.committed_capacity == 0
        assert ig.consumed_capacity == 0
        assert ig.percent_capacity_remaining == 100.0

    def verify_resource_percent_capacity_remaining(self, resource):
        # works for both instances and instance groups
        expected_percent_remaining = round(100 * (1 - float(resource.consumed_capacity) / resource.capacity), 2)
        assert resource.percent_capacity_remaining == expected_percent_remaining

    @pytest.mark.parametrize('num_hosts', [3, 5, 7])
    def test_job_impact_scales_with_number_of_hosts(self, factories, ig_with_single_instance, num_hosts):
        jt = factories.v2_job_template(playbook='sleep.yml', extra_vars='{"sleep_interval": 120}')
        jt.add_instance_group(ig_with_single_instance)
        instance = ig_with_single_instance.related.instances.get().results.pop()

        inventory = jt.ds.inventory
        for _ in range(num_hosts):
            factories.v2_host(inventory=inventory)

        self.assert_instance_reflects_zero_running_jobs(instance.get())
        self.assert_instance_group_reflects_zero_running_jobs(ig_with_single_instance.get())

        jt.launch()
        utils.poll_until(lambda: jt.ds.project.related.project_updates.get(status='successful',
                         launch_type='sync').count == 1, interval=1, timeout=60)

        utils.poll_until(lambda: instance.get().jobs_running == 1, interval=1, timeout=60)
        assert instance.get().consumed_capacity == self.unified_job_impact('job', num_hosts=num_hosts)
        self.verify_resource_percent_capacity_remaining(instance)

        utils.poll_until(lambda: ig_with_single_instance.get().jobs_running == 1, interval=1, timeout=60)
        assert ig_with_single_instance.get().consumed_capacity == self.unified_job_impact('job', num_hosts=num_hosts)
        self.verify_resource_percent_capacity_remaining(ig_with_single_instance)

    @pytest.mark.parametrize('num_hosts', [3, 5, 7])
    def test_ahc_impact_scales_with_number_of_hosts(self, factories, ig_with_single_instance, num_hosts):
        instance = ig_with_single_instance.related.instances.get().results.pop()

        inventory = factories.v2_inventory()
        inventory.add_instance_group(ig_with_single_instance)
        for _ in range(num_hosts):
            factories.v2_host(inventory=inventory)

        self.assert_instance_reflects_zero_running_jobs(instance.get())
        self.assert_instance_group_reflects_zero_running_jobs(ig_with_single_instance.get())

        factories.v2_ad_hoc_command(inventory=inventory, module_name='shell', module_args='sleep 120')

        utils.poll_until(lambda: instance.get().jobs_running == 1, interval=1, timeout=60)
        assert instance.get().consumed_capacity == self.unified_job_impact('ahc', num_hosts=num_hosts)
        self.verify_resource_percent_capacity_remaining(instance)

        utils.poll_until(lambda: ig_with_single_instance.get().jobs_running == 1, interval=1, timeout=60)
        assert ig_with_single_instance.get().consumed_capacity == self.unified_job_impact('ahc', num_hosts=num_hosts)
        self.verify_resource_percent_capacity_remaining(ig_with_single_instance)

    @pytest.mark.parametrize('forks', [3, 5, 7])
    def test_job_impact_scales_with_number_of_forks(self, factories, ig_with_single_instance, forks):
        jt = factories.v2_job_template(playbook='sleep.yml', extra_vars='{"sleep_interval": 120}', forks=forks)
        jt.add_instance_group(ig_with_single_instance)
        instance = ig_with_single_instance.related.instances.get().results.pop()

        inventory = jt.ds.inventory
        for _ in range(5):
            factories.v2_host(inventory=inventory)

        self.assert_instance_reflects_zero_running_jobs(instance.get())
        self.assert_instance_group_reflects_zero_running_jobs(ig_with_single_instance.get())

        jt.launch()
        utils.poll_until(lambda: jt.ds.project.related.project_updates.get(status='successful',
                         launch_type='sync').count == 1, interval=1, timeout=60)

        utils.poll_until(lambda: instance.get().jobs_running == 1, interval=1, timeout=60)
        assert instance.get().consumed_capacity == self.unified_job_impact('job', forks=forks, num_hosts=5)
        self.verify_resource_percent_capacity_remaining(instance)

        utils.poll_until(lambda: ig_with_single_instance.get().jobs_running == 1, interval=1, timeout=60)
        assert ig_with_single_instance.get().consumed_capacity == self.unified_job_impact('job', forks=forks,
                                                                                    num_hosts=5)
        self.verify_resource_percent_capacity_remaining(ig_with_single_instance)

    @pytest.mark.parametrize('forks', [3, 5, 7])
    def test_ahc_impact_scales_with_number_of_forks(self, factories, ig_with_single_instance, forks):
        instance = ig_with_single_instance.related.instances.get().results.pop()

        inventory = factories.v2_inventory()
        inventory.add_instance_group(ig_with_single_instance)
        for _ in range(5):
            factories.v2_host(inventory=inventory)

        self.assert_instance_reflects_zero_running_jobs(instance.get())
        self.assert_instance_group_reflects_zero_running_jobs(ig_with_single_instance.get())

        factories.v2_ad_hoc_command(inventory=inventory, module_name='shell', module_args='sleep 120',
                                    forks=forks)

        utils.poll_until(lambda: instance.get().jobs_running == 1, interval=1, timeout=60)
        assert instance.get().consumed_capacity == self.unified_job_impact('ahc', num_hosts=5, forks=forks)
        self.verify_resource_percent_capacity_remaining(instance)

        utils.poll_until(lambda: ig_with_single_instance.get().jobs_running == 1, interval=1, timeout=60)
        assert ig_with_single_instance.get().consumed_capacity == self.unified_job_impact('ahc', num_hosts=5,
                                                                                    forks=forks)
        self.verify_resource_percent_capacity_remaining(ig_with_single_instance)

    def test_instance_group_updates_for_simultaneously_running_jobs(self, factories, ig_with_single_instance):
        instance = ig_with_single_instance.related.instances.get().results.pop()
        jt = factories.v2_job_template(playbook='sleep.yml', extra_vars='{"sleep_interval": 120}',
                                       allow_simultaneous=True)
        jt.add_instance_group(ig_with_single_instance)
        inventory = jt.ds.inventory
        factories.v2_host(inventory=inventory)

        self.assert_instance_reflects_zero_running_jobs(instance.get())
        self.assert_instance_group_reflects_zero_running_jobs(ig_with_single_instance.get())

        for _ in range(2):
            jt.launch()
        utils.poll_until(lambda: jt.ds.project.related.project_updates.get(status='successful',
                         launch_type='sync').count == 2, interval=5, timeout=60)

        utils.poll_until(lambda: instance.get().jobs_running == 2, interval=1, timeout=60)
        assert instance.consumed_capacity == 2 * self.unified_job_impact('job', 1)
        self.verify_resource_percent_capacity_remaining(instance)

        utils.poll_until(lambda: ig_with_single_instance.get().jobs_running == 2, interval=1, timeout=60)
        assert ig_with_single_instance.consumed_capacity == 2 * self.unified_job_impact('job', 1)
        self.verify_resource_percent_capacity_remaining(ig_with_single_instance)

    @pytest.mark.requires_cluster
    def test_instance_group_updates_for_simultaneously_running_unified_jobs(self, factories, v2):
        ig = factories.instance_group()
        instances = v2.instances.get().results
        for instance in instances:
            ig.add_instance(instance)

        jt = factories.v2_job_template(playbook='sleep.yml', extra_vars='{"sleep_inverval": 120}')
        factories.v2_host(inventory=jt.ds.inventory)
        jt.add_instance_group(ig)

        ahc_host = factories.v2_host()
        ahc_host.ds.inventory.add_instance_group(ig)

        project = factories.v2_project(scm_url='https://github.com/django/django.git')
        project.ds.organization.add_instance_group(ig)

        cred = factories.v2_credential(kind='aws')
        inv_source = factories.v2_inventory_source(source='ec2', credential=cred)
        inv = inv_source.ds.inventory
        inv.add_instance_group(ig)

        for instance in instances:
            self.assert_instance_reflects_zero_running_jobs(instance.get())
        self.assert_instance_group_reflects_zero_running_jobs(ig.get())

        jt.launch()
        factories.v2_ad_hoc_command(inventory=ahc_host.ds.inventory, module_name='shell', module_args='sleep 120')
        project.update()
        inv_source.update()

        utils.poll_until(lambda: ig.get().jobs_running == 4, interval=1, timeout=120)
        utils.poll_until(lambda: ig.get().consumed_capacity == self.unified_job_impact('job', 1) +
                                 self.unified_job_impact('ahc', 1) + self.unified_job_impact('project_update') +
                                 self.unified_job_impact('inventory_update'), interval=1, timeout=120)
        self.verify_resource_percent_capacity_remaining(ig)

    def test_all_groups_that_contain_job_execution_node_update_for_running_job(self, factories, v2,
                                                                               ig_with_single_instance):
        jt = factories.v2_job_template(playbook='sleep.yml', extra_vars='{"sleep_interval": 120}',
                                       allow_simultaneous=True)
        jt.add_instance_group(ig_with_single_instance)
        factories.v2_host(inventory=jt.ds.inventory)

        instance = v2.instances.get().results.pop()
        igs = [factories.instance_group() for _ in range(3)]
        for ig in igs:
            ig.add_instance(instance)

        self.assert_instance_reflects_zero_running_jobs(instance.get())
        self.assert_instance_group_reflects_zero_running_jobs(ig_with_single_instance.get())

        jt.launch()
        utils.poll_until(lambda: jt.ds.project.related.project_updates.get(status='successful',
                         launch_type='sync').count == 1, interval=5, timeout=60)

        utils.poll_until(lambda: instance.get().jobs_running == 1, interval=1, timeout=60)
        assert instance.consumed_capacity == self.unified_job_impact('job', 1)
        self.verify_resource_percent_capacity_remaining(instance)

        utils.poll_until(lambda: ig_with_single_instance.get().jobs_running == 1, interval=1, timeout=60)
        assert ig_with_single_instance.consumed_capacity == self.unified_job_impact('job', 1)
        self.verify_resource_percent_capacity_remaining(ig_with_single_instance)

        for ig in igs:
            assert ig.get().jobs_running == 0
            assert ig.consumed_capacity == self.unified_job_impact('job', 1)
            self.verify_resource_percent_capacity_remaining(ig)

    def test_project_updates_have_an_impact_of_one(self, factories, v2, tower_instance_group):
        project = factories.v2_project(scm_url='https://github.com/django/django.git', wait=False)
        project_update = project.related.current_job.get()
        utils.poll_until(lambda: project_update.get().execution_node, interval=1, timeout=30)
        instance = v2.instances.get(hostname=project_update.execution_node).results.pop()

        # project sources tower IG group since no IG explicitly assigned
        utils.poll_until(lambda: tower_instance_group.get().jobs_running == 1, interval=1, timeout=60)
        assert tower_instance_group.consumed_capacity == self.unified_job_impact('project_update')
        self.verify_resource_percent_capacity_remaining(tower_instance_group)

        utils.poll_until(lambda: instance.get().jobs_running == 1, interval=1, timeout=60)
        assert instance.consumed_capacity == self.unified_job_impact('project_update')
        self.verify_resource_percent_capacity_remaining(instance)

        project_update.wait_until_completed()
        self.assert_instance_reflects_zero_running_jobs(instance.get())
        self.assert_instance_group_reflects_zero_running_jobs(tower_instance_group.get())

    def test_inventory_updates_have_an_impact_of_one(self, factories, ig_with_single_instance):
        instance = ig_with_single_instance.related.instances.get().results.pop()
        aws_cred = factories.v2_credential(kind='aws')
        inv_source = factories.v2_inventory_source(source='ec2', credential=aws_cred)
        inv_source.ds.inventory.add_instance_group(ig_with_single_instance)

        inv_update = inv_source.update()

        utils.poll_until(lambda: instance.get().jobs_running == 1, interval=1, timeout=60)
        assert instance.consumed_capacity == self.unified_job_impact('inventory_update')
        self.verify_resource_percent_capacity_remaining(instance)

        utils.poll_until(lambda: ig_with_single_instance.get().jobs_running == 1, interval=1, timeout=60)
        assert ig_with_single_instance.consumed_capacity == self.unified_job_impact('inventory_update')
        self.verify_resource_percent_capacity_remaining(ig_with_single_instance)

        inv_update.wait_until_completed()
        self.assert_instance_reflects_zero_running_jobs(instance.get())
        self.assert_instance_group_reflects_zero_running_jobs(ig_with_single_instance.get())

    def test_system_jobs_have_an_impact_of_five(self, factories, v2, tower_instance_group,
                                                cleanup_activitystream_template):
        system_job = cleanup_activitystream_template.launch()
        utils.poll_until(lambda: system_job.get().execution_node, interval=1, timeout=5)  # job is short
        instance = v2.instances.get(hostname=system_job.execution_node).results.pop()

        utils.poll_until(lambda: instance.get().jobs_running == 1, interval=1, timeout=60)
        assert instance.consumed_capacity == self.unified_job_impact('system_job')
        self.verify_resource_percent_capacity_remaining(instance)

        # system job templates source the tower group
        utils.poll_until(lambda: tower_instance_group.get().jobs_running == 1, interval=1, timeout=60)
        assert tower_instance_group.consumed_capacity == self.unified_job_impact('system_job')
        self.verify_resource_percent_capacity_remaining(tower_instance_group)

        system_job.wait_until_completed()
        self.assert_instance_reflects_zero_running_jobs(instance.get())
        self.assert_instance_group_reflects_zero_running_jobs(tower_instance_group.get())

    def test_only_workflow_constituent_jobs_affect_capacity(self, factories, v2, tower_instance_group):
        host = factories.v2_host()
        wfjt = factories.v2_workflow_job_template()
        jt = factories.v2_job_template(inventory=host.ds.inventory, playbook='sleep.yml',
                                       extra_vars='{"sleep_interval": 30}')
        jt.add_instance_group(tower_instance_group)
        factories.v2_workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)

        wfj = wfjt.launch()

        utils.poll_until(lambda: jt.ds.project.related.project_updates.get(status='successful',
                         launch_type='sync').count == 1, interval=5, timeout=60)

        instance = v2.instances.get(hostname=jt.related.jobs.get().results.pop().execution_node).results.pop()
        utils.poll_until(lambda: instance.get().jobs_running == 1, interval=1, timeout=60)

        assert self.unified_job_impact('job', num_hosts=1) == instance.consumed_capacity
        self.verify_resource_percent_capacity_remaining(instance)

        assert tower_instance_group.get().consumed_capacity == self.unified_job_impact('job', num_hosts=1)
        self.verify_resource_percent_capacity_remaining(tower_instance_group)

        wfj.wait_until_completed()
        self.assert_instance_reflects_zero_running_jobs(instance.get())
        self.assert_instance_group_reflects_zero_running_jobs(tower_instance_group.get())
