from tests.api import APITest
import pytest


@pytest.mark.serial
@pytest.mark.usefixtures('authtoken')
class TestResourceProfiling(APITest):

    expected_files = ['memory',
                      'cpu',
                      'pids']

    def toggle_resource_profiling(self, update_setting_pg, v2, state="false"):
        system_settings = v2.settings.get().get_endpoint('jobs')
        payload = {'AWX_RESOURCE_PROFILING_ENABLED': state}
        update_setting_pg(system_settings, payload)

    @pytest.fixture
    def global_resource_profiling_enabled(self, update_setting_pg, v2, request):
        self.toggle_resource_profiling(update_setting_pg, v2, state="true")

    def get_resource_profiles(self, ansible_adhoc, job_id, execution_node):
        hosts = ansible_adhoc()
        profile_paths = hosts[execution_node].find(paths='/var/log/tower/playbook_profiling/{}'.format(job_id), recurse=True).values()[0]['files']
        filenames = [f['path'] for f in profile_paths]
        return filenames

    def count_lines_in_files(self, ansible_adhoc, filenames, execution_node):
        hosts = ansible_adhoc()
        linecounts = {}
        for f in filenames:
            file_lc = hosts[execution_node].command('wc {}'.format(f)).values()[0]['stdout'].split()[0]
            linecounts[f] = int(file_lc)
        return linecounts

    def check_filenames(self, filenames):
        for e in self.expected_files:
            assert any(e.lower() in f.lower() for f in filenames), '{} not found'.format(e)

    def test_performance_stats_files_created(self, ansible_adhoc, skip_if_openshift, global_resource_profiling_enabled, factories):
        jt = factories.job_template(playbook='sleep.yml', extra_vars='{"sleep_interval": 2}')
        factories.host(inventory=jt.ds.inventory)
        job = jt.launch().wait_until_completed()
        profiles = self.get_resource_profiles(ansible_adhoc, job.id, job.execution_node)
        assert len(profiles) == len(self.expected_files)
        self.check_filenames(profiles)

    def test_performance_stats_enabled_by_verbosity_5(self, ansible_adhoc, skip_if_openshift, factories):
        jt = factories.job_template(playbook='sleep.yml', extra_vars='{"sleep_interval": 2}', verbosity=5)
        factories.host(inventory=jt.ds.inventory)
        job = jt.launch().wait_until_completed()
        profiles = self.get_resource_profiles(ansible_adhoc, job.id, job.execution_node)
        assert len(profiles) == len(self.expected_files)
        self.check_filenames(profiles)

    def test_performance_stats_not_created_when_disabled(self, ansible_adhoc, skip_if_openshift, factories):
        jt = factories.job_template(playbook='sleep.yml', extra_vars='{"sleep_interval": 2}')
        factories.host(inventory=jt.ds.inventory)
        job = jt.launch().wait_until_completed()
        profiles = self.get_resource_profiles(ansible_adhoc, job.id, job.execution_node)
        assert len(profiles) == 0

    def test_performance_stats_intervals_are_applied(self, ansible_adhoc, update_setting_pg, v2, factories, skip_if_openshift, global_resource_profiling_enabled):
        system_settings = v2.settings.get().get_endpoint('jobs')
        payload = {'AWX_RESOURCE_PROFILING_CPU_POLL_INTERVAL': '0.5',
                   'AWX_RESOURCE_PROFILING_MEMORY_POLL_INTERVAL': '0.5',
                   'AWX_RESOURCE_PROFILING_PID_POLL_INTERVAL': '0.5'}
        update_setting_pg(system_settings, payload)
        jt = factories.job_template(playbook='sleep.yml', extra_vars='{"sleep_interval": 10}')
        factories.host(inventory=jt.ds.inventory)
        job = jt.launch().wait_until_completed()
        profiles = self.get_resource_profiles(ansible_adhoc, job.id, job.execution_node)
        self.check_filenames(profiles)
        linecounts = self.count_lines_in_files(ansible_adhoc, profiles, job.execution_node)
        for f in profiles:
            assert 19 < linecounts[f] < 25, linecounts[f]

    def test_performance_stats_generated_on_isolated_nodes(self, ansible_adhoc, update_setting_pg, v2, factories, skip_if_openshift, skip_if_not_cluster, global_resource_profiling_enabled):
        ig = v2.instance_groups.get(name='protected').results.pop()
        jt = factories.job_template(playbook='sleep.yml', extra_vars='{"sleep_interval": 2}')
        jt.add_instance_group(ig)
        factories.host(inventory=jt.ds.inventory)
        job = jt.launch().wait_until_completed()
        profiles = self.get_resource_profiles(ansible_adhoc, job.id, job.execution_node)
        assert len(profiles) == len(self.expected_files)
        self.check_filenames(profiles)
