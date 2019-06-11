from towerkit import exceptions as exc
import pytest

from tests.lib.helpers.rbac_utils import check_user_capabilities
from tests.api import APITest


@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestSystemJobRBAC(APITest):

    @pytest.mark.fixture_args(days=1000, granularity='1y', older_than='1y')
    def test_get_detail_view_as_superuser(self, system_job):
        system_job.get()

    @pytest.mark.fixture_args(days=1000, granularity='1y', older_than='1y')
    def test_get_list_view_as_non_superuser(self, non_superusers, api_system_jobs_pg):
        for non_superuser in non_superusers:
            with self.current_user(username=non_superuser.username, password=non_superuser.password):
                if non_superuser.is_system_auditor:
                    api_system_jobs_pg.get()
                else:
                    with pytest.raises(exc.Forbidden):
                        api_system_jobs_pg.get()

    @pytest.mark.fixture_args(days=1000, granularity='1y', older_than='1y')
    def test_get_detail_view_as_non_superuser(self, non_superusers, system_job):
        for non_superuser in non_superusers:
            with self.current_user(username=non_superuser.username, password=non_superuser.password):
                if non_superuser.is_system_auditor:
                    system_job.get()
                else:
                    with pytest.raises(exc.Forbidden):
                        system_job.get()

    def test_user_capabilities_as_superuser(self, cleanup_jobs_with_status_completed, api_system_jobs_pg):
        check_user_capabilities(cleanup_jobs_with_status_completed, "superuser")
        check_user_capabilities(api_system_jobs_pg.get(id=cleanup_jobs_with_status_completed.id).results.pop(), "superuser")

    def test_cannot_launch_as_system_auditor(self, factories, system_job_template):
        user = factories.user(is_system_auditor=True)
        with self.current_user(username=user.username, password=user.password):
            with pytest.raises(exc.Forbidden):
                system_job_template.launch().wait_until_completed()
