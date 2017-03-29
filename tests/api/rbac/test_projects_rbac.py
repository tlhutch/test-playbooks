import pytest
import httplib

import towerkit.exceptions
from tests.lib.helpers.rbac_utils import (
    assert_response_raised,
    check_read_access,
    check_user_capabilities,
    set_roles
)
from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.rbac
@pytest.mark.skip_selenium
class Test_Project_RBAC(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_unprivileged_user(self, factories, user_password):
        """An unprivileged user/team should not be able to:
        * GET our project detail page
        * GET all project related pages
        * Launch project updates
        * Edit our project
        * Delete our project
        """
        project_pg = factories.project()
        user_pg = factories.user()
        update_pg = project_pg.get_related('update')

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(project_pg, unprivileged=True)

            # check project update
            with pytest.raises(towerkit.exceptions.Forbidden):
                update_pg.post()

            # check put/patch/delete
            assert_response_raised(project_pg, httplib.FORBIDDEN)

    @pytest.mark.github("https://github.com/ansible/ansible-tower/issues/3930")
    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_admin_role(self, factories, set_test_roles, agent, user_password):
        """A user/team with project 'admin' should be able to:
        * GET our project detail page
        * GET all project related pages
        * Edit our project
        * Delete our project
        """
        project_pg = factories.project()
        user_pg = factories.user()

        # give agent admin_role
        set_test_roles(user_pg, project_pg, agent, "admin")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(project_pg, ["organization"])

            # check put/patch/delete
            assert_response_raised(project_pg, httplib.OK)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_update_role(self, factories, set_test_roles, agent, user_password):
        """A user/team with project 'update' should be able to:
        * GET our project detail page
        * GET all project related pages
        A user/team with project 'update' should not be able to:
        * Edit our project
        * Delete our project
        """
        project_pg = factories.project()
        user_pg = factories.user()

        # give agent update_role
        set_test_roles(user_pg, project_pg, agent, "update")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(project_pg, ["organization"])

            # check put/patch/delete
            assert_response_raised(project_pg, httplib.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_use_role(self, factories, set_test_roles, agent, user_password):
        """A user/team with project 'use' should be able to:
        * GET our project detail page
        * GET all project related pages
        A user/team with project 'use' should not be able to:
        * Edit our project
        * Delete our project
        """
        project_pg = factories.project()
        user_pg = factories.user()

        # give agent use_role
        set_test_roles(user_pg, project_pg, agent, "use")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(project_pg, ["organization"])

            # check put/patch/delete
            assert_response_raised(project_pg, httplib.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_read_role(self, factories, set_test_roles, agent, user_password):
        """A user/team with project 'read' should be able to:
        * GET our project detail page
        * GET all project related pages
        A user/team with project 'read' should not be able to:
        * Edit our project
        * Delete our project
        """
        project_pg = factories.project()
        user_pg = factories.user()

        # give agent read_role
        set_test_roles(user_pg, project_pg, agent, "read")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(project_pg, ["organization"])

            # check put/patch/delete
            assert_response_raised(project_pg, httplib.FORBIDDEN)

    @pytest.mark.parametrize('role', ['admin', 'update', 'use', 'read'])
    def test_user_capabilities(self, factories, user_password, api_projects_pg, role):
        """Test user_capabilities given each project role."""
        project_pg = factories.project()
        user_pg = factories.user()

        # give test user target role privileges
        set_roles(user_pg, project_pg, [role])

        with self.current_user(username=user_pg.username, password=user_password):
            check_user_capabilities(project_pg.get(), role)
            check_user_capabilities(api_projects_pg.get(id=project_pg.id).results.pop(), role)

    @pytest.mark.parametrize('role', ['admin', 'update', 'use', 'read'])
    def test_launch_update(self, factories, user_password, role):
        """Tests ability to launch a project update."""
        ALLOWED_ROLES = ['admin', 'update']
        REJECTED_ROLES = ['use', 'read']

        project_pg = factories.project()
        user_pg = factories.user()

        # give test user target role privileges
        set_roles(user_pg, project_pg, [role])

        with self.current_user(username=user_pg.username, password=user_password):
            if role in ALLOWED_ROLES:
                update_pg = project_pg.update().wait_until_completed()
                assert update_pg.is_successful, "Project update unsuccessful - %s." % update_pg
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    project_pg.update()
            else:
                raise ValueError("Received unhandled project role.")

    @pytest.mark.parametrize('role', ['admin', 'update', 'use', 'read'])
    def test_schedule_update(self, factories, role):
        """Tests ability to schedule a project update."""
        ALLOWED_ROLES = ['admin', 'update']
        REJECTED_ROLES = ['use', 'read']

        project_pg = factories.project()
        user_pg = factories.user()

        # give test user target role privileges
        set_roles(user_pg, project_pg, [role])

        with self.current_user(username=user_pg.username, password=user_pg.password):
            if role in ALLOWED_ROLES:
                schedule_pg = project_pg.add_schedule()
                assert_response_raised(schedule_pg, methods=('get', 'put', 'patch', 'delete'))
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    project_pg.related.schedules.post()
            else:
                raise ValueError("Received unhandled project role.")

    @pytest.mark.parametrize('role', ['admin', 'update', 'use', 'read'])
    def test_cancel_update(self, factories, project_ansible_git_nowait, user_password, role):
        """Tests project update cancellation. Project admins can cancel other people's projects."""
        ALLOWED_ROLES = ['admin']
        REJECTED_ROLES = ['update', 'use', 'read']

        user_pg = factories.user()
        update_pg = project_ansible_git_nowait.related.current_update.get()

        # give test user target role privileges
        set_roles(user_pg, project_ansible_git_nowait, [role])

        with self.current_user(username=user_pg.username, password=user_password):
            if role in ALLOWED_ROLES:
                update_pg.cancel()
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    update_pg.cancel()
                # wait for project to finish to ensure clean teardown
                update_pg.wait_until_completed()
            else:
                raise ValueError("Received unhandled project role.")

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/4181')
    @pytest.mark.parametrize('role', ['admin', 'update', 'use', 'read'])
    def test_delete_update(self, factories, user_password, role):
        """Tests ability to delete a project update."""
        ALLOWED_ROLES = ['admin']
        REJECTED_ROLES = ['update', 'use', 'read']

        project_pg = factories.project()
        user_pg = factories.user()

        # give test user target role privileges
        set_roles(user_pg, project_pg, [role])

        # launch project update
        update_pg = project_pg.update()

        with self.current_user(username=user_pg.username, password=user_password):
            if role in ALLOWED_ROLES:
                update_pg.delete()
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    update_pg.delete()
                # wait for project to finish to ensure clean teardown
                update_pg.wait_until_completed()
            else:
                raise ValueError("Received unhandled project role.")

    @pytest.mark.parametrize('role', ['admin', 'update', 'use', 'read'])
    def test_update_user_capabilities(self, factories, user_password, api_project_updates_pg, role):
        """Test user_capabilities given each project role on spawned
        project_updates.
        """
        project_pg = factories.project()
        user_pg = factories.user()

        # give test user target role privileges
        set_roles(user_pg, project_pg, [role])

        # launch project_update
        update_pg = project_pg.update().wait_until_completed()

        with self.current_user(username=user_pg.username, password=user_password):
            check_user_capabilities(update_pg.get(), role)
            check_user_capabilities(api_project_updates_pg.get(id=update_pg.id).results.pop(), role)

    @pytest.mark.parametrize('role', ['admin', 'update', 'use', 'read'])
    def test_change_project_org_affiliation(self, factories, role):
        """Confirm attempts to change project org to an unaffiliated one result in 403 for all project roles"""
        project = factories.project(wait=False)
        user = factories.user()
        another_org = factories.organization()

        project.set_object_roles(user, role)

        with self.current_user(username=user.username, password=user.password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                project.organization = another_org.id
