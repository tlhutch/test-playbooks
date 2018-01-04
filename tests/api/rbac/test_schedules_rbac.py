import pytest

import towerkit.exceptions
from tests.api import Base_Api_Test
from tests.lib.helpers.rbac_utils import check_user_capabilities


@pytest.mark.api
@pytest.mark.rbac
@pytest.mark.skip_selenium
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class Test_Schedules_RBAC(Base_Api_Test):

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
            with pytest.raises(towerkit.exceptions.Forbidden):
                schedule.get()
            # test put/patch
            with pytest.raises(towerkit.exceptions.Forbidden):
                schedule.put()
            with pytest.raises(towerkit.exceptions.Forbidden):
                schedule.patch()
            # test post
            with pytest.raises(towerkit.exceptions.Forbidden):
                schedules.post()
            # test delete
            with pytest.raises(towerkit.exceptions.Forbidden):
                schedule.delete()

    def test_crud_as_org_user(self, org_user, resource_with_schedule):
        """Test schedules CRUD as an org_user against an inventory_source, project, and JT."""
        schedules = resource_with_schedule.related.schedules.get()
        schedule = schedules.results.pop()

        with self.current_user(org_user.username, org_user.password):
            # test get
            with pytest.raises(towerkit.exceptions.Forbidden):
                schedule.get()
            # test put/patch
            with pytest.raises(towerkit.exceptions.Forbidden):
                schedule.put()
            with pytest.raises(towerkit.exceptions.Forbidden):
                schedule.patch()
            # test create
            with pytest.raises(towerkit.exceptions.Forbidden):
                schedules.post()
            # test delete
            with pytest.raises(towerkit.exceptions.Forbidden):
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
            with pytest.raises(towerkit.exceptions.Forbidden):
                schedule.patch(unified_job_template=cleanup_jobs_template.id)

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
