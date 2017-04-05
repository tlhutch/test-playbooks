import pytest

import towerkit.exceptions
from tests.lib.helpers.rbac_utils import check_user_capabilities
from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.rbac
@pytest.mark.skip_selenium
class Test_System_Jobs_RBAC(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    @pytest.mark.fixture_args(days=1000, granularity='1y', older_than='1y')
    def test_get_detail_view_as_superuser(self, system_job):
        """Verify that a superuser account is able to GET a system_job resource."""
        system_job.get()

    @pytest.mark.fixture_args(days=1000, granularity='1y', older_than='1y')
    def test_get_list_view_as_non_superuser(self, non_superusers, user_password, api_system_jobs_pg):
        """Verify that non-superuser accounts are unable to access the top-level
        system jobs endpoint (/api/v1/system_jobs/).
        """
        for non_superuser in non_superusers:
            with self.current_user(non_superuser.username, user_password):
                with pytest.raises(towerkit.exceptions.Forbidden):
                    api_system_jobs_pg.get()

    @pytest.mark.fixture_args(days=1000, granularity='1y', older_than='1y')
    def test_get_detail_view_as_non_superuser(self, non_superusers, user_password, system_job):
        """Verify that non-superuser accounts are unable to access nested system
        job endpoints (/api/v1/system_jobs/N/).
        """
        for non_superuser in non_superusers:
            with self.current_user(non_superuser.username, user_password):
                with pytest.raises(towerkit.exceptions.Forbidden):
                    system_job.get()

    def test_user_capabilities_as_superuser(self, cleanup_jobs_with_status_completed, api_system_jobs_pg):
        """Verify 'user_capabilities' with a superuser."""
        check_user_capabilities(cleanup_jobs_with_status_completed.get(), "superuser")
        check_user_capabilities(api_system_jobs_pg.get(id=cleanup_jobs_with_status_completed.id).results.pop(), "superuser")

    def test_launch_as_auditor(self, factories, system_job_template):
        """Confirms that a system auditor cannot launch system jobs"""
        user = factories.user()
        user.is_system_auditor = True
        with self.current_user(user.username, user.password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                system_job_template.launch().wait_until_completed()
