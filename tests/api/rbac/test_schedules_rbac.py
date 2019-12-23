import pytest

from awxkit import exceptions as exc

from tests.api import APITest
from tests.lib.helpers.rbac_utils import check_user_capabilities


@pytest.mark.usefixtures('authtoken')
class Test_Schedules_RBAC(APITest):

    def test_crud_as_superuser(self, resource_with_schedule):
        """Tests schedule CRUD as superuser against all UJTs that support schedules.
        Note: schedule creation is tested upon fixture instantiation.
        """
        # test get with additional filter so that we do not delete our prestocked system job schedule
        schedule = resource_with_schedule.related.schedules.get(not__name='Cleanup Job Schedule').results.pop()
        # test put/patch
        schedule.put()
        schedule.patch()
        # test delete
        schedule.delete()

    def test_crud_as_org_admin(self, org_admin, schedulable_resource_as_org_admin):
        """Tests schedules CRUD as an org_admin against an inventory_source, project, and JT."""

        with self.current_user(org_admin.username, org_admin.password):
            # test create
            schedule = schedulable_resource_as_org_admin.add_schedule()
            # test get
            schedule.get()
            # test put/patch
            schedule.put()
            schedule.patch()
            # test delete
            schedule.delete()

    def test_system_job_template_schedule_crud_as_org_admin(self, org_admin, cleanup_jobs_template):
        """Tests schedules CRUD as an org_admin against a SJT."""
        schedules = cleanup_jobs_template.related.schedules.get()
        # Tower-3.0 comes with a prestocked cleanup_jobs schedule
        schedule = schedules.results.pop()

        with self.current_user(org_admin.username, org_admin.password):
            # test get
            with pytest.raises(exc.Forbidden):
                schedule.get()
            # test put/patch
            with pytest.raises(exc.Forbidden):
                schedule.put()
            with pytest.raises(exc.Forbidden):
                schedule.patch()
            # test post
            with pytest.raises(exc.Forbidden):
                schedules.post()
            # test delete
            with pytest.raises(exc.Forbidden):
                schedule.delete()

    def test_crud_as_org_user(self, org_user, resource_with_schedule):
        """Test schedules CRUD as an org_user against an inventory_source, project, and JT."""
        schedules = resource_with_schedule.related.schedules.get()
        schedule = schedules.results.pop()

        with self.current_user(org_user.username, org_user.password):
            # test get
            with pytest.raises(exc.Forbidden):
                schedule.get()
            # test put/patch
            with pytest.raises(exc.Forbidden):
                schedule.put()
            with pytest.raises(exc.Forbidden):
                schedule.patch()
            # test create
            with pytest.raises(exc.Forbidden):
                schedules.post()
            # test delete
            with pytest.raises(exc.Forbidden):
                schedule.delete()

    def test_schedule_reassignment(self, org_user, schedulable_resource_as_org_admin, cleanup_jobs_template):
        """Tests that UJT-admins cannot patch their schedules to other UJTs."""
        # grant test user admin permissions to underlying Tower resource
        if schedulable_resource_as_org_admin.type != "inventory_source":
            schedulable_resource_as_org_admin.set_object_roles(org_user, "admin")
        else:
            inventory = schedulable_resource_as_org_admin.related.inventory.get()
            inventory.set_object_roles(org_user, "admin")

        schedule = schedulable_resource_as_org_admin.add_schedule()

        with self.current_user(username=org_user.username, password=org_user.password):
            with pytest.raises(exc.Forbidden):
                schedule.patch(unified_job_template=cleanup_jobs_template.id)

    @pytest.mark.parametrize('role', ['admin', 'execute', 'read'])
    def test_create_schedule_with_jt_job(self, factories, role):
        jt = factories.job_template()
        user = factories.user()
        jt.set_object_roles(user, role)

        job = jt.launch().wait_until_completed()
        job.assert_successful()

        with self.current_user(user):
            if role in ('admin', 'execute'):
                job.related.create_schedule.post()
                # https://github.com/ansible/awx/issues/4147 previously data that should have been
                # ignored via payload sanitization was causing 500 server error
                job.related.create_schedule.post({'credentials': ['aardvark']})
            else:
                with pytest.raises(exc.Forbidden):
                    job.related.create_schedule.post()

    @pytest.mark.parametrize('role', ['admin', 'execute', 'read'])
    def test_create_schedule_with_wfjtn_job(self, factories, role):
        jt = factories.job_template()
        wfjt = factories.workflow_job_template()
        factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)

        user = factories.user()
        jt.set_object_roles(user, role)

        wfj = wfjt.launch().wait_until_completed()
        wfj.assert_successful()

        create_schedule = jt.get().related.last_job.get().related.create_schedule.get()
        with self.current_user(user):
            if role in ('admin', 'execute'):
                create_schedule.post()
            else:
                with pytest.raises(exc.Forbidden):
                    create_schedule.post()

    def test_user_capabilities_as_superuser(self, resource_with_schedule, api_schedules_pg):
        """Tests 'user_capabilities' against schedules of all types of UJT as superuser."""
        schedule = resource_with_schedule.related.schedules.get().results.pop()
        check_user_capabilities(schedule, 'superuser')
        check_user_capabilities(api_schedules_pg.get(id=schedule.id).results.pop(), "superuser")

    def test_user_capabilities_as_org_admin(self, org_admin, organization_resource_with_schedule, api_schedules_pg):
        """Tests 'user_capabilities' against schedules of all types of UJT as an org_admin."""
        schedule = organization_resource_with_schedule.related.schedules.get().results.pop()

        with self.current_user(org_admin.username, org_admin.password):
            check_user_capabilities(schedule.get(), 'org_admin')
            check_user_capabilities(api_schedules_pg.get(id=schedule.id).results.pop(), "org_admin")
