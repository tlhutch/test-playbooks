import pytest
import fauxfactory

import towerkit.exceptions
from tests.api import Base_Api_Test
from tests.lib.helpers.rbac_utils import check_user_capabilities


@pytest.mark.api
@pytest.mark.rbac
@pytest.mark.skip_selenium
class Test_Schedules_RBAC(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_crud_as_superuser(self, resource_with_schedule):
        """Tests schedule CRUD as superuser against all UJTs that support schedules.
        Create is tested upon fixture instantiation.
        """
        # test get
        # NOTE: additional filter so that we do not delete our prestocked system job schedule
        schedule_pg = resource_with_schedule.get_related('schedules', not__name='Cleanup Job Schedule').results[0]
        # test put/patch
        schedule_pg.put()
        schedule_pg.patch()
        # test delete
        schedule_pg.delete()

    def test_crud_as_org_admin(self, org_admin, user_password, schedulable_resource_as_org_admin):
        """Tests schedules CRUD as an org_admin against an inventory_source, project, and JT."""
        schedules_pg = schedulable_resource_as_org_admin.get_related('schedules')
        payload = dict(name="Schedule - %s" % fauxfactory.gen_utf8(),
                       rrule="DTSTART:20160926T040000Z RRULE:FREQ=HOURLY;INTERVAL=1")

        with self.current_user(org_admin.username, user_password):
            # test create
            schedule_pg = schedules_pg.post(payload)
            # test get
            schedule_pg.get()
            # test put/patch
            schedule_pg.put()
            schedule_pg.patch()
            # test delete
            schedule_pg.delete()

    def test_system_job_template_schedule_crud_as_org_admin(self, request, org_admin, user_password, cleanup_jobs_template):
        """Tests schedules CRUD as an org_admin against a system job template."""
        schedules_pg = cleanup_jobs_template.get_related('schedules')
        # Tower-3.0 comes with a prestocked cleanup_jobs schedule
        schedule_pg = cleanup_jobs_template.get_related('schedules').results[0]

        with self.current_user(org_admin.username, user_password):
            # test get
            with pytest.raises(towerkit.exceptions.Forbidden):
                schedule_pg.get()
            # test put/patch
            with pytest.raises(towerkit.exceptions.Forbidden):
                schedule_pg.put()
            with pytest.raises(towerkit.exceptions.Forbidden):
                schedule_pg.patch()
            # test post
            with pytest.raises(towerkit.exceptions.Forbidden):
                schedules_pg.post()
            # test delete
            with pytest.raises(towerkit.exceptions.Forbidden):
                schedule_pg.delete()

    def test_crud_as_org_user(self, request, org_user, user_password, resource_with_schedule):
        """Test schedules CRUD as an org_user against an inventory_source, project, and JT."""
        schedules_pg = resource_with_schedule.get_related('schedules')
        schedule_pg = resource_with_schedule.get_related('schedules').results[0]

        with self.current_user(org_user.username, user_password):
            # test get
            with pytest.raises(towerkit.exceptions.Forbidden):
                schedule_pg.get()
            # test put/patch
            with pytest.raises(towerkit.exceptions.Forbidden):
                schedule_pg.put()
            with pytest.raises(towerkit.exceptions.Forbidden):
                schedule_pg.patch()
            # test create
            with pytest.raises(towerkit.exceptions.Forbidden):
                schedules_pg.post()
            # test delete
            with pytest.raises(towerkit.exceptions.Forbidden):
                schedule_pg.delete()

    def test_user_capabilities_as_superuser(self, resource_with_schedule, api_schedules_pg):
        """Tests 'user_capabilities' against schedules of all types of UJT as superuser."""
        schedule_pg = resource_with_schedule.get_related('schedules').results[0]
        check_user_capabilities(schedule_pg.get(), 'superuser')
        check_user_capabilities(api_schedules_pg.get(id=schedule_pg.id).results.pop(), "superuser")

    @pytest.mark.github("https://github.com/ansible/ansible-tower/issues/5507")
    def test_user_capabilities_as_org_admin(self, org_admin, user_password, organization_resource_with_schedule, api_schedules_pg):
        """Tests 'user_capabilities' against schedules of all types of UJT as an org_admin."""
        schedule_pg = organization_resource_with_schedule.get_related('schedules').results[0]

        with self.current_user(org_admin.username, user_password):
            check_user_capabilities(schedule_pg.get(), 'org_admin')
            check_user_capabilities(api_schedules_pg.get(id=schedule_pg.id).results.pop(), "org_admin")
