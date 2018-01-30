from towerkit import exceptions as exc
import pytest

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.rbac
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestJobsRBAC(Base_Api_Test):

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/7876')
    def test_v1_launch_as_superuser(self, job_template, api_jobs_pg):
        """Verify job creation via /api/v1/jobs/ and job start via /api/v2/jobs/N/start/."""
        job = api_jobs_pg.post(job_template.json)
        assert job.status == 'new'
        job.related.start.post()
        assert job.wait_until_completed().is_successful

    def test_v1_launch_as_non_superuser(self, job_template, non_superusers, api_jobs_pg):
        """Verify a non-superuser is unable to create a job via POST to the /api/v1/jobs/ endpoint."""
        for non_superuser in non_superusers:
            with self.current_user(non_superuser):
                with pytest.raises(exc.Forbidden):
                    api_jobs_pg.post(job_template.json)

    def test_v2_launch_as_all_users(self, factories, v2, all_users):
        """Creating jobs via post to /api/v2/jobs/ should raise 405."""
        for user in all_users:
            with self.current_user(user):
                with pytest.raises(exc.MethodNotAllowed):
                    v2.jobs.post()
