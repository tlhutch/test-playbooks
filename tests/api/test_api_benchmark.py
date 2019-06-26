import pytest
from tests.api import APITest
from towerkit.config import config


@pytest.mark.benchmark
@pytest.mark.serial
@pytest.mark.usefixtures('authtoken')
class TestApiPerformance(APITest):

    endpoints = ['job_templates',
                 'job_events',
                 'inventory_scripts',
                 'labels',
                 'schedules',
                 'workflow_job_nodes',
                 'instances',
                 'instance_groups',
                 'credential_types',
                 'teams',
                 'inventory_updates',
                 'system_jobs',
                 'workflow_jobs',
                 'ad_hoc_commands',
                 'project_updates',
                 'ping',
                 'inventory',
                 'config',
                 'inventory_sources',
                 'jobs',
                 'users',
                 'organizations',
                 'notification_templates',
                 'tokens',
                 'unified_jobs',
                 'applications',
                 'groups',
                 'unified_job_templates',
                 'credentials',
                 'workflow_job_template_nodes',
                 'projects',
                 'me',
                 'workflow_job_templates',
                 'roles',
                 'notifications',
                 'settings',
                 'system_job_templates',
                 'hosts',
                 'dashboard',
                 'activity_stream',
                ]

    def get_endpoint(self, endpoint):
        endpoint.get()

    def resource_creation_function(self, v2, resource_type):
        return getattr(v2, resource_type).create

    def launch_and_wait(self, job_template):
        j = job_template.launch()
        j.wait_until_completed(interval=0.25)

    def multi_launch_and_wait(self, job_template, ct):
        jobs = []
        for _ in range(ct):
            jobs.append(job_template.launch())
        while True:
            for j in jobs:
                j.wait_until_completed(interval=0.25)
            return jobs

    def wait_for_job_start(self, job_template):
        job_template.launch().wait_until_started(interval=0.25)

    def wait_for_workflow_node_start(self, wfjt):
        wfj = wfjt.launch()
        wfjn = wfj.related.workflow_nodes.get().results.pop()
        wfjn.wait_for_job(interval=0.25)
        job = wfjn.get_related('job')
        job.wait_until_started(interval=0.25)

    @pytest.mark.parametrize('endpoint', endpoints)
    def test_benchmark_endpoint_response(self, v2, endpoint, benchmark):
        e = getattr(v2, endpoint)
        benchmark(self.get_endpoint, e)

    def test_benchmark_org_creation(self, v2, benchmark):
        f = self.resource_creation_function(v2, 'organizations')
        benchmark(f)

    def test_benchmark_user_creation(self, v2, factories, benchmark):
        f = self.resource_creation_function(v2, 'users')
        org = factories.organization()
        benchmark(f, organization=org)

    def test_benchmark_team_creation(self, v2, factories, benchmark):
        f = self.resource_creation_function(v2, 'teams')
        org = factories.organization()
        benchmark(f, organization=org)

    def test_benchmark_associate_user_with_org(self, factories, benchmark):
        # Need a setup function because we can't reuse the "user" value
        def setup():
            user = factories.user()
            org = factories.organization()
            return (org, user), {}

        def associate_user(org, user):
            org.related.users.post(user.payload())
        benchmark.pedantic(associate_user, setup=setup, rounds=15)

    def test_benchmark_associate_user_with_team(self, factories, benchmark):
        def setup():
            user = factories.user()
            org = factories.organization()
            team = factories.team(organization=org)
            return (team, user), {}

        def associate_user(team, user):
            team.related.users.post(user.payload())
        benchmark.pedantic(associate_user, setup=setup, rounds=15)

    def test_benchmark_cloud_credential_creation(self, v2, factories, benchmark):
        f = self.resource_creation_function(v2, 'credentials')
        org = factories.organization()
        benchmark(f, organization=org, kind='aws', username='foo', password='bar')

    def test_benchmark_machine_credential_creation(self, v2, factories, benchmark):
        f = self.resource_creation_function(v2, 'credentials')
        org = factories.organization()
        benchmark(f, organization=org, kind='ssh',
                  username='foo', password='bar', ssh_key_data=config.credentials.ssh.ssh_key_data)

    def test_benchmark_project_creation(self, v2, factories, benchmark):
        f = self.resource_creation_function(v2, 'projects')
        org = factories.organization()
        benchmark(f, organization=org, wait=False)

    def test_benchmark_inventory_creation(self, v2, factories, benchmark):
        f = self.resource_creation_function(v2, 'inventory')
        org = factories.organization()
        benchmark(f, organization=org)

    def test_benchmark_inventory_group_creation(self, factories, benchmark):
        def create_group(inventory, org):
            factories.group(inventory=inventory, organization=org)
        org = factories.organization()
        inventory = factories.inventory(organization=org)
        benchmark(create_group, inventory, org)

    def test_benchmark_inventory_source_update(self, factories, benchmark):
        def update_source(source):
            source.update().wait_until_completed(interval=0.25)
        credential = factories.credential(kind='aws')
        source = factories.inventory_source(source='ec2', credential=credential)
        benchmark(update_source, source)

    def test_benchmark_job_template_start_time(self, factories, benchmark):
        jt = factories.job_template(allow_simultaneous=True)
        benchmark(self.wait_for_job_start, jt)

    def test_benchmark_workflow_node_start_time(self, factories, benchmark):
        jt = factories.job_template(
            playbook='ping.yml', allow_simultaneous=True)
        wfjt = factories.workflow_job_template(allow_simultaneous=True)
        factories.workflow_job_template_node(
            workflow_job_template=wfjt, unified_job_template=jt)
        benchmark(self.wait_for_workflow_node_start, wfjt)

    def test_benchmark_workflow_in_workflow_node_start_time(self, factories, benchmark):
        def wait_for_inner_workflow_node_start(wfjt):
            wfj = wfjt.launch()
            wfjn = wfj.related.workflow_nodes.get().results.pop()
            wfjn.wait_for_job(interval=0.25)
            job = wfjn.get_related('job')
            inner_wfjn = job.related.workflow_nodes.get().results.pop()
            inner_wfjn.wait_for_job(interval=0.25)
            inner_job = inner_wfjn.get_related('job')
            inner_job.wait_until_started(interval=0.25)

        wfjt_outer = factories.workflow_job_template(allow_simultaneous=True)
        wfjt_inner = factories.workflow_job_template(allow_simultaneous=True)
        jt = factories.job_template(allow_simultaneous=True)
        factories.workflow_job_template_node(
            workflow_job_template=wfjt_inner,
            unified_job_template=jt
        )
        node = factories.workflow_job_template_node(
            workflow_job_template=wfjt_outer)
        node.unified_job_template = wfjt_inner.id
        benchmark(wait_for_inner_workflow_node_start, wfjt_outer)

    def test_benchmark_job_template_creation(self, v2, factories, benchmark):
        org = factories.organization()
        inventory = factories.inventory(organization=org)
        project = factories.project(organization=org)
        f = self.resource_creation_function(v2, 'job_templates')
        benchmark(f, organization=org, inventory=inventory, project=project)

    def test_benchmark_job_template_slicing(self, v2, factories, benchmark):
        instances = v2.instances.get(
            rampart_groups__controller__isnull=True, page_size=200, capacity__gt=0).results
        ct = len(instances)
        host_count = ct * 20
        jt = factories.job_template(
            job_slice_count=ct, forks=20, playbook='gather_facts.yml')
        for _ in range(host_count):
            jt.ds.inventory.add_host()
        benchmark(self.launch_and_wait, jt)

    def test_benchmark_job_slicing_workaround(self, v2, factories, benchmark):
        instances = v2.instances.get(
            rampart_groups__controller__isnull=True, page_size=200, capacity__gt=0).results
        ct = len(instances)
        inventory = factories.inventory()
        jt = factories.job_template(
            forks=20, inventory=inventory, allow_simultaneous=True, playbook='gather_facts.yml')
        for _ in range(20):
            inventory.add_host()
        benchmark(self.multi_launch_and_wait, jt, ct)

    def test_benchmark_single_job(self, v2, factories, benchmark):
        instances = v2.instances.get(
            rampart_groups__controller__isnull=True, page_size=200, capacity__gt=0).results
        ct = len(instances)
        job_size = ct * 20
        inventory = factories.inventory()
        jt = factories.job_template(
            forks=20, inventory=inventory, allow_simultaneous=True, playbook='gather_facts.yml')
        for _ in range(job_size):
            inventory.add_host()
        benchmark(self.launch_and_wait, jt)

    def test_workflow_multiple_project_use(self, factories, benchmark):
        wfjt = factories.workflow_job_template()
        project = factories.project()
        for i in range(20):
            factories.workflow_job_template_node(
                workflow_job_template=wfjt,
                unified_job_template=factories.job_template(
                    allow_simultaneous=True,
                    project=project,
                    # need different inventory for each JT
                    # avoids task manager blocking inventory lock
                    inventory=factories.inventory()
                )
            )
        benchmark(self.launch_and_wait, wfjt)

    def test_benchmark_workflow_in_workflow(self, factories, benchmark):
        wfjt_outer = factories.workflow_job_template()
        wfjt_inner = factories.workflow_job_template()
        jt = factories.job_template()
        factories.workflow_job_template_node(
            workflow_job_template=wfjt_inner,
            unified_job_template=jt
        )
        node = factories.workflow_job_template_node(
            workflow_job_template=wfjt_outer)
        node.unified_job_template = wfjt_inner.id
        benchmark(self.launch_and_wait, wfjt_outer)

    def test_benchmark_nested_empty_workflows_in_workflow(self, factories, benchmark):
        wfjts = []
        for i in range(10):
            wfjt = factories.workflow_job_template()
            if wfjts:
                wfjts[-1].get_related('workflow_nodes').post(dict(
                    unified_job_template=wfjt.id
                ))
            wfjts.append(wfjt)
        benchmark(self.launch_and_wait, wfjts[0])
