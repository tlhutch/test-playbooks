import pytest
import http.client

import towerkit.exceptions
from tests.lib.helpers.rbac_utils import (
    assert_response_raised,
    check_read_access,
    check_user_capabilities
)
from tests.api import APITest


@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class Test_Project_RBAC(APITest):

    def test_unprivileged_user(self, factories):
        """An unprivileged user/team should not be able to:
        * GET our project detail page
        * GET all project related pages
        * Launch project updates
        * Edit our project
        * Delete our project
        """
        project = factories.project()
        user = factories.user()
        update = project.get_related('update')

        with self.current_user(username=user.username, password=user.password):
            # check GET as test user
            check_read_access(project, unprivileged=True)

            # check project update
            with pytest.raises(towerkit.exceptions.Forbidden):
                update.post()

            # check put/patch/delete
            assert_response_raised(project, http.client.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_admin_role(self, factories, set_test_roles, agent):
        """A user/team with project 'admin' should be able to:
        * GET our project detail page
        * GET all project related pages
        * Edit our project
        * Delete our project
        """
        project = factories.project()
        user = factories.user()

        # give agent admin_role
        set_test_roles(user, project, agent, "admin")

        with self.current_user(username=user.username, password=user.password):
            # check GET as test user
            check_read_access(project, ["organization"])

            # check put/patch/delete
            assert_response_raised(project, http.client.OK)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_update_role(self, factories, set_test_roles, agent):
        """A user/team with project 'update' should be able to:
        * GET our project detail page
        * GET all project related pages
        A user/team with project 'update' should not be able to:
        * Edit our project
        * Delete our project
        """
        project = factories.project()
        user = factories.user()

        # give agent update_role
        set_test_roles(user, project, agent, "update")

        with self.current_user(username=user.username, password=user.password):
            # check GET as test user
            check_read_access(project, ["organization"])

            # check put/patch/delete
            assert_response_raised(project, http.client.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_use_role(self, factories, set_test_roles, agent):
        """A user/team with project 'use' should be able to:
        * GET our project detail page
        * GET all project related pages
        A user/team with project 'use' should not be able to:
        * Edit our project
        * Delete our project
        """
        project = factories.project()
        user = factories.user()

        # give agent use_role
        set_test_roles(user, project, agent, "use")

        with self.current_user(username=user.username, password=user.password):
            # check GET as test user
            check_read_access(project, ["organization"])

            # check put/patch/delete
            assert_response_raised(project, http.client.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_read_role(self, factories, set_test_roles, agent):
        """A user/team with project 'read' should be able to:
        * GET our project detail page
        * GET all project related pages
        A user/team with project 'read' should not be able to:
        * Edit our project
        * Delete our project
        """
        project = factories.project()
        user = factories.user()

        # give agent read_role
        set_test_roles(user, project, agent, "read")

        with self.current_user(username=user.username, password=user.password):
            # check GET as test user
            check_read_access(project, ["organization"])

            # check put/patch/delete
            assert_response_raised(project, http.client.FORBIDDEN)

    @pytest.mark.parametrize('role', ['admin', 'update', 'use', 'read'])
    def test_user_capabilities(self, factories, api_projects_pg, role):
        """Test user_capabilities given each project role."""
        project = factories.project()
        user = factories.user()

        project.set_object_roles(user, role)

        with self.current_user(username=user.username, password=user.password):
            check_user_capabilities(project.get(), role)
            check_user_capabilities(api_projects_pg.get(id=project.id).results.pop(), role)

    @pytest.mark.parametrize('role', ['admin', 'update', 'use', 'read'])
    def test_launch_update(self, factories, role):
        """Tests ability to launch a project update."""
        ALLOWED_ROLES = ['admin', 'update']
        REJECTED_ROLES = ['use', 'read']

        project = factories.project()
        user = factories.user()

        project.set_object_roles(user, role)

        with self.current_user(username=user.username, password=user.password):
            if role in ALLOWED_ROLES:
                update = project.update().wait_until_completed()
                update.assert_successful()
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    project.update()
            else:
                raise ValueError("Received unhandled project role.")

    @pytest.mark.parametrize('role', ['admin', 'update', 'use', 'read'])
    def test_schedule_update(self, factories, role):
        """Tests ability to schedule a project update."""
        ALLOWED_ROLES = ['admin', 'update']
        REJECTED_ROLES = ['use', 'read']

        project = factories.project()
        user = factories.user()

        project.set_object_roles(user, role)

        with self.current_user(username=user.username, password=user.password):
            if role in ALLOWED_ROLES:
                schedule = project.add_schedule()
                assert_response_raised(schedule, methods=('get', 'put', 'patch', 'delete'))
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    project.related.schedules.post()
            else:
                raise ValueError("Received unhandled project role.")

    @pytest.mark.parametrize('role', ['admin', 'update', 'use', 'read'])
    def test_cancel_update(self, factories, project_ansible_git_nowait, role):
        """Tests project update cancellation. Project admins can cancel other people's projects."""
        ALLOWED_ROLES = ['admin']
        REJECTED_ROLES = ['update', 'use', 'read']

        user = factories.user()
        update = project_ansible_git_nowait.related.current_update.get()

        project_ansible_git_nowait.set_object_roles(user, role)

        with self.current_user(username=user.username, password=user.password):
            if role in ALLOWED_ROLES:
                update.cancel()
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    update.cancel()
            else:
                raise ValueError("Received unhandled project role.")

        # wait for project to finish to ensure clean teardown
        update.wait_until_completed()

    @pytest.mark.parametrize('role', ['admin', 'update', 'use', 'read'])
    def test_delete_update(self, factories, role):
        """Tests ability to delete a project update."""
        ALLOWED_ROLES = ['admin']
        REJECTED_ROLES = ['update', 'use', 'read']

        project = factories.project()
        user = factories.user()

        project.set_object_roles(user, role)

        update = project.update().wait_until_completed()

        with self.current_user(username=user.username, password=user.password):
            if role in ALLOWED_ROLES:
                update.delete()
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    update.delete()
            else:
                raise ValueError("Received unhandled project role.")

    @pytest.mark.parametrize('role', ['admin', 'update', 'use', 'read'])
    def test_update_user_capabilities(self, factories, api_project_updates_pg, role):
        """Test user_capabilities given each project role on spawned
        project_updates.
        """
        project = factories.project()
        user = factories.user()

        project.set_object_roles(user, role)

        update = project.update().wait_until_completed()

        with self.current_user(username=user.username, password=user.password):
            check_user_capabilities(update.get(), role)
            check_user_capabilities(api_project_updates_pg.get(id=update.id).results.pop(), role)
