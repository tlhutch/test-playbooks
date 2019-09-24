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
        execution_node_result = []
        # Using this because we need to grab the hostname from the keys based on index
        for h in range(len(result.values())):
            if result.values()[h]['matched'] > 0:
                execution_node_result.append((result.values()[h], list(result.keys())[h]))
        if len(execution_node_result) > 1:
            raise Exception("Multiple nodes contain profiles for this job")
        elif len(execution_node_result) == 1:
            profile_found = True
            profile_result = execution_node_result[0]
        elif len(execution_node_result) == 0:
            profile_found = False
            profile_result = None
        return profile_found, profile_result

    def test_performance_stats_files_created(self, ansible_runner, skip_if_openshift, resource_profiling_enabled, factories):
        expected_files = ['memory',
                          'cpu',
                          'pids']
        jt = factories.job_template(playbook='sleep.yml', extra_vars='{"sleep_interval": 2}')
        factories.host(inventory=jt.ds.inventory)
        job = jt.launch().wait_until_completed()
        profile_found, profile_result = self.find_resource_profile(ansible_runner, job.id)
        assert profile_found, profile_result
        stat_files = profile_result[0]['files']
        filenames = [f['path'] for f in stat_files]
        for e in expected_files:
            assert any(e.lower() in f.lower() for f in filenames), filenames

    def test_performance_stats_not_created_when_disabled(self, ansible_runner, skip_if_openshift, factories):
        jt = factories.job_template(playbook='sleep.yml', extra_vars='{"sleep_interval": 2}')
        factories.host(inventory=jt.ds.inventory)
        job = jt.launch().wait_until_completed()
        profile_found, profile_result = self.find_resource_profile(ansible_runner, job.id)
        assert not profile_found, profile_result

    def test_performance_stats_intervals_are_applied(self, ansible_runner, ansible_adhoc, update_setting_pg, v2, factories, skip_if_openshift, resource_profiling_enabled):
        system_settings = v2.settings.get().get_endpoint('jobs')
        payload = {'AWX_RESOURCE_PROFILING_CPU_POLL_INTERVAL': '0.5',
                   'AWX_RESOURCE_PROFILING_MEMORY_POLL_INTERVAL': '0.5',
                   'AWX_RESOURCE_PROFILING_PID_POLL_INTERVAL': '0.5'}
        update_setting_pg(system_settings, payload)
        jt = factories.job_template(playbook='sleep.yml', extra_vars='{"sleep_interval": 10}')
        factories.host(inventory=jt.ds.inventory)
        job = jt.launch().wait_until_completed()
        profile_found, profile_result = self.find_resource_profile(ansible_runner, job.id)
        assert profile_found
        stat_files = profile_result[0]['files']
        hosts = ansible_adhoc()
        for f in stat_files:
            file_wc = hosts[profile_result[1]].command('wc {}'.format(f['path'])).values()[0]['stdout'].split()[0]
            assert 19 < int(file_wc) < 25, file_wc
