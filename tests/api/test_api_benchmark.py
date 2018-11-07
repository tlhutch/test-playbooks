import pytest
from tests.api import APITest
from towerkit.config import config


@pytest.mark.benchmark
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
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
        j.wait_until_completed()

    def multi_launch_and_wait(self, job_template, ct):
        jobs = []
        for _ in range(ct):
            jobs.append(job_template.launch())
        while True:
            for j in jobs:
                j.wait_until_completed()
            return jobs

    @pytest.mark.parametrize('endpoint', endpoints)
    @pytest.mark.mp_group('Benchmarking', 'isolated_serial')
    def test_benchmark_endpoint_response(self, v2, endpoint, benchmark):
        e = getattr(v2, endpoint)
        benchmark(self.get_endpoint, e)

    @pytest.mark.mp_group('Benchmarking', 'isolated_serial')
    def test_benchmark_org_creation(self, v2, benchmark):
        f = self.resource_creation_function(v2, 'organizations')
        benchmark(f)

    @pytest.mark.mp_group('Benchmarking', 'isolated_serial')
    def test_benchmark_user_creation(self, v2, factories, benchmark):
        f = self.resource_creation_function(v2, 'users')
        org = factories.v2_organization()
        benchmark(f, organization=org)

    @pytest.mark.mp_group('Benchmarking', 'isolated_serial')
    def test_benchmark_team_creation(self, v2, factories, benchmark):
        f = self.resource_creation_function(v2, 'teams')
        org = factories.v2_organization()
        benchmark(f, organization=org)

    @pytest.mark.mp_group('Benchmarking', 'isolated_serial')
    def test_benchmark_associate_user_with_org(self, factories, benchmark):
        # Need a setup function because we can't reuse the "user" value
        def setup():
            user = factories.v2_user()
            org = factories.v2_organization()
            return (org, user), {}

        def associate_user(org, user):
            org.related.users.post(user.payload())
        benchmark.pedantic(associate_user, setup=setup, rounds=15)

    @pytest.mark.mp_group('Benchmarking', 'isolated_serial')
    def test_benchmark_associate_user_with_team(self, factories, benchmark):
        def setup():
            user = factories.v2_user()
            org = factories.v2_organization()
            team = factories.v2_team(organization=org)
            return (team, user), {}

        def associate_user(team, user):
            team.related.users.post(user.payload())
        benchmark.pedantic(associate_user, setup=setup, rounds=15)

    @pytest.mark.mp_group('Benchmarking', 'isolated_serial')
    def test_benchmark_cloud_credential_creation(self, v2, factories, benchmark):
        f = self.resource_creation_function(v2, 'credentials')
        org = factories.v2_organization()
        benchmark(f, organization=org, kind='aws', username='foo', password='bar')

    @pytest.mark.mp_group('Benchmarking', 'isolated_serial')
    def test_benchmark_machine_credential_creation(self, v2, factories, benchmark):
        f = self.resource_creation_function(v2, 'credentials')
        org = factories.v2_organization()
        benchmark(f, organization=org, kind='ssh',
                  username='foo', password='bar', ssh_key_data=config.credentials.ssh.ssh_key_data)

    @pytest.mark.mp_group('Benchmarking', 'isolated_serial')
    def test_benchmark_project_creation(self, v2, factories, benchmark):
        f = self.resource_creation_function(v2, 'projects')
        org = factories.v2_organization()
        benchmark(f, organization=org, wait=False)

    @pytest.mark.mp_group('Benchmarking', 'isolated_serial')
    def test_benchmark_inventory_creation(self, v2, factories, benchmark):
        f = self.resource_creation_function(v2, 'inventory')
        org = factories.v2_organization()
        benchmark(f, organization=org)

    @pytest.mark.mp_group('Benchmarking', 'isolated_serial')
    def test_benchmark_job_template_creation(self, v2, factories, benchmark):
        org = factories.v2_organization()
        inventory = factories.v2_inventory(organization=org)
        project = factories.v2_project(organization=org)
        f = self.resource_creation_function(v2, 'job_templates')
        benchmark(f, organization=org, inventory=inventory, project=project)

    @pytest.mark.mp_group('Benchmarking', 'isolated_serial')
    def test_benchmark_job_template_slicing(self, v2, factories, benchmark):
        instances = v2.instances.get(
            rampart_groups__controller__isnull=True, page_size=200, capacity__gt=0).results
        ct = len(instances)
        host_count = ct * 20
        jt = factories.v2_job_template(
            job_slice_count=ct, forks=20, playbook='gather_facts.yml')
        for _ in range(host_count):
            jt.ds.inventory.add_host()
        benchmark(self.launch_and_wait, jt)

    @pytest.mark.mp_group('Benchmarking', 'isolated_serial')
    def test_benchmark_job_slicing_workaround(self, v2, factories, benchmark):
        instances = v2.instances.get(
            rampart_groups__controller__isnull=True, page_size=200, capacity__gt=0).results
        ct = len(instances)
        inventory = factories.v2_inventory()
        jt = factories.v2_job_template(
            forks=20, inventory=inventory, allow_simultaneous=True, playbook='gather_facts.yml')
        for _ in range(20):
            inventory.add_host()
        benchmark(self.multi_launch_and_wait, jt, ct)

    @pytest.mark.mp_group('Benchmarking', 'isolated_serial')
    def test_benchmark_single_job(self, v2, factories, benchmark):
        instances = v2.instances.get(
            rampart_groups__controller__isnull=True, page_size=200, capacity__gt=0).results
        ct = len(instances)
        job_size = ct * 20
        inventory = factories.v2_inventory()
        jt = factories.v2_job_template(
            forks=20, inventory=inventory, allow_simultaneous=True, playbook='gather_facts.yml')
        for _ in range(job_size):
            inventory.add_host()
        benchmark(self.launch_and_wait, jt)

    @pytest.mark.github('https://github.com/ansible/awx/issues/2252')
    @pytest.mark.mp_group('Benchmarking', 'isolated_serial')
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
