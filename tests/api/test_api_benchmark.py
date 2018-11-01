import pytest
from tests.api import APITest


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

    @pytest.mark.parametrize('endpoint', endpoints)
    def test_benchmark_endpoint_response(self, v2, endpoint, benchmark):
        e = getattr(v2, endpoint)
        benchmark(self.get_endpoint, e)

    def test_benchmark_org_creation(self, v2, benchmark):
        f = self.resource_creation_function(v2, 'organizations')
        benchmark(f)

    def test_benchmark_user_creation(self, v2, factories, benchmark):
        f = self.resource_creation_function(v2, 'users')
        org = factories.v2_organization()
        benchmark(f, organization=org)

    def test_benchmark_cloud_credential_creation(self, v2, factories, benchmark):
        f = self.resource_creation_function(v2, 'credentials')
        org = factories.v2_organization()
        benchmark(f, organization=org, kind='aws', username='foo', password='bar')

    def test_benchmark_project_creation(self, v2, factories, benchmark):
        f = self.resource_creation_function(v2, 'projects')
        org = factories.v2_organization()
        benchmark(f, organization=org, wait=False)

    def test_benchmark_inventory_creation(self, v2, factories, benchmark):
        f = self.resource_creation_function(v2, 'inventory')
        org = factories.v2_organization()
        benchmark(f, organization=org)

    def test_job_template_creation(self, v2, factories, benchmark):
        org = factories.v2_organization()
        inventory = factories.v2_inventory(organization=org)
        project = factories.v2_project(organization=org)
        f = self.resource_creation_function(v2, 'job_templates')
        benchmark(f, organization=org, inventory=inventory, project=project)
