from towerkit import exceptions as exc
import pytest

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.rbac
@pytest.mark.skip_selenium
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestJobsRBAC(Base_Api_Test):

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/7527')
    def test_v1_post_as_superuser(self, job_template, api_jobs_pg):
        """Verify a superuser is able to create a job via POST to the /api/v1/jobs/ endpoint."""
        job = api_jobs_pg.post(job_template.json)
        assert job.status == 'new'
        assert job.wait_until_completed().is_successful

    def test_v1_post_as_non_superuser(self, non_superusers, api_jobs_pg, job_template):
        """Verify a non-superuser is unable to create a job via POST to the /api/v1/jobs/ endpoint."""
        for non_superuser in non_superusers:
            with self.current_user(non_superuser):
                with pytest.raises(exc.Forbidden):
                    api_jobs_pg.post(job_template.json)

    def test_v2_post_as_all_users(self, factories, v2, all_users):
        """Creating jobs via post to /api/v2/jobs/ is not allowed."""
        for user in all_users:
            with self.current_user(user):
                with pytest.raises(exc.MethodNotAllowed):
                    v2.jobs.post()
