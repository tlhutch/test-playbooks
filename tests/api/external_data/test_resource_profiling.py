from tests.api import APITest
import pytest
from awxkit import utils
from awxkit.config import config
import awxkit.exceptions as exc

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


    @pytest.mark.ansible(host_pattern='tower[0]')
    def test_performance_stats_files_created(self, ansible_runner, skip_if_openshift, resource_profiling_enabled, factories):
        jt = factories.job_template()
        factories.host(inventory=jt.ds.inventory)
        job = jt.launch().wait_until_completed()
        result = ansible_runner.find(paths='/var/log/tower/playbook_profiling/{}'.format(job.id), recurse=True)
        assert result.values()[0]['matched'] > 0
