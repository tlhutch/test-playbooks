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

    @pytest.mark.parametrize('endpoint', endpoints)
    def test_endpoint_response_time(self, v2, endpoint, benchmark):
        e = getattr(v2, endpoint)
        benchmark(self.get_endpoint, e)
