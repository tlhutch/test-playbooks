from towerkit import exceptions as exc
import pytest

from tests.api import APITest


@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestJobsRBAC(APITest):

    def test_launch_as_all_users(self, factories, v2, all_users):
        """Creating jobs via post to /api/v2/jobs/ should raise 405."""
        for user in all_users:
            with self.current_user(user):
                with pytest.raises(exc.MethodNotAllowed):
                    v2.jobs.post()

    def test_relaunch_job_as_superuser(self, factories):
        jt = factories.job_template()
        job = jt.launch().wait_until_completed()
        job.assert_successful()

        relaunched_job = job.relaunch().wait_until_completed()
        relaunched_job.assert_successful()

    def test_relaunch_job_as_organization_admin(self, factories):
        jt1, jt2 = [factories.job_template() for _ in range(2)]
        user = factories.user()
        jt1.ds.inventory.ds.organization.set_object_roles(user, 'admin')

        job1 = jt1.launch().wait_until_completed()
        job2 = jt2.launch().wait_until_completed()
        for job in [job1, job2]:
            job.assert_successful()

        with self.current_user(user):
            relaunched_job = job1.relaunch().wait_until_completed()
            relaunched_job.assert_successful()

            with pytest.raises(exc.Forbidden):
                job2.relaunch()

    def test_relaunch_as_organization_user(self, factories):
        jt = factories.job_template()
        user = factories.user()
        jt.ds.inventory.ds.organization.set_object_roles(user, 'member')

        job = jt.launch().wait_until_completed()
        job.assert_successful()

        with self.current_user(user):
            with pytest.raises(exc.Forbidden):
                job.relaunch()

    def test_relaunch_job_as_system_auditor(self, factories, job_with_status_completed):
        user = factories.user(is_system_auditor=True)
        with self.current_user(user):
            with pytest.raises(exc.Forbidden):
                job_with_status_completed.relaunch().wait_until_completed()
