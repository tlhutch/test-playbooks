from tests.api import APITest
import pytest


@pytest.mark.usefixtures('authtoken')
class TestResourceProfiling(APITest):

    def toggle_resource_profiling(self, update_setting_pg, v2, state="false"):
        system_settings = v2.settings.get().get_endpoint('jobs')
        payload = {'AWX_RESOURCE_PROFILING_ENABLED': state}
        update_setting_pg(system_settings, payload)

    @pytest.fixture
    def resource_profiling_enabled(self, update_setting_pg, v2, request):
        self.toggle_resource_profiling(update_setting_pg, v2, state="true")
        request.addfinalizer(lambda: self.toggle_resource_profiling(update_setting_pg, v2, state="false"))

    # Attempt to simplify locating files in a cluster
    def find_resource_profile(self, ansible_runner, job_id):
        result = ansible_runner.find(paths='/var/log/tower/playbook_profiling/{}'.format(job_id), recurse=True)
        execution_node_result = [r for r in result.values() if r['matched'] > 0]
        if len(execution_node_result) != 1:
            raise Exception("execution node could not be determined")
        return execution_node_result[0]

    def test_performance_stats_files_created(self, ansible_runner, skip_if_openshift, resource_profiling_enabled, factories):
        expected_files = ['memory',
                          'cpu',
                          'pids']
        jt = factories.job_template(playbook='sleep.yml', extra_vars='{"sleep_interval": 2}')
        factories.host(inventory=jt.ds.inventory)
        job = jt.launch().wait_until_completed()
        result = self.find_resource_profile(ansible_runner, job.id)
        stat_files = result['files']
        filenames = [f['path'] for f in stat_files]
        for e in expected_files:
            assert any(e.lower() in f.lower() for f in filenames), filenames
