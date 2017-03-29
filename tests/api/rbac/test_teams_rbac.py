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
class Test_Team_RBAC(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_unprivileged_user(self, factories, user_password):
        """An unprivileged user/team may not be able to:
        * Get the team details page
        * Get all of the team related pages
        * Edit the team
        * Delete the team
        """
        team_pg = factories.team()
        user_pg = factories.user()

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(team_pg, unprivileged=True)

            # check put/patch/delete
            assert_response_raised(team_pg, httplib.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_admin_role(self, factories, set_test_roles, agent, user_password):
        """A user/team with team 'admin_role' should be able to:
        * Get the team details page
        * Get all of the team related pages
        * Edit the team
        * Delete the team
        """
        team_pg = factories.team()
        user_pg = factories.user()

        # give agent admin_role
        set_test_roles(user_pg, team_pg, agent, "admin")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(team_pg, ['organization'])

            # check put/patch/delete
            assert_response_raised(team_pg, httplib.OK)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_member_role(self, factories, set_test_roles, agent, user_password):
        """A user/team with team 'member_role' should be able to:
        * Get the team details page
        * Get all of the team related pages
        A user/team with team 'member_role' should not be able to:
        * Edit the team
        * Delete the team
        """
        team_pg = factories.team()
        user_pg = factories.user()

        # give agent member_role
        set_test_roles(user_pg, team_pg, agent, "member")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(team_pg, ['organization'])

            # check put/patch/delete
            assert_response_raised(team_pg, httplib.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_read_role(self, factories, set_test_roles, agent, user_password):
        """A user/team with team 'read_role' should be able to:
        * Get the team details page
        * Get all of the team related pages
        A user/team with team 'read_role' should not be able to:
        * Edit the team
        * Delete the team
        """
        team_pg = factories.team()
        user_pg = factories.user()

        # give agent read_role
        set_test_roles(user_pg, team_pg, agent, "read")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(team_pg, ['organization'])

            # check put/patch/delete
            assert_response_raised(team_pg, httplib.FORBIDDEN)

    @pytest.mark.parametrize('role', ['admin', 'member', 'read'])
    def test_user_capabilities(self, factories, user_password, api_teams_pg, role):
        """Test user_capabilities given each team role."""
        team_pg = factories.team()
        user_pg = factories.user()

        # give test user target role privileges
        set_roles(user_pg, team_pg, [role])

        with self.current_user(username=user_pg.username, password=user_password):
            check_user_capabilities(team_pg.get(), role)
            check_user_capabilities(api_teams_pg.get(id=team_pg.id).results.pop(), role)

    def test_member_role_association(self, factories, user_password):
        """Tests that after a user is granted member_role that he now shows
        up under teams/N/users.
        """
        team_pg = factories.team()
        user_pg = factories.user()

        # team by default should have no users
        users_pg = team_pg.get_related('users')
        assert users_pg.count == 0, "%s user[s] unexpectedly found for teams/%s." % (users_pg.count, team_pg.id)

        # give test user member role privileges
        role_pg = team_pg.get_object_role('member_role')
        with pytest.raises(towerkit.exceptions.NoContent):
            user_pg.get_related('roles').post(dict(id=role_pg.id))

        # assert that teams/N/users now shows test user
        assert users_pg.get().count == 1, "Expected one user for teams/%s/users/, got %s." % (team_pg.id, users_pg.count)
        assert users_pg.results[0].id == user_pg.id, \
            "Team user not our target user. Expected user with ID %s but got one with ID %s." % (user_pg.id, users_pg.results[0].id)

    def test_member_role_inheritance(self, factories):
        """Test that team-member gets included with team-admin permissions."""
        team = factories.team()
        user = factories.user()

        # give test user admin role privileges
        set_roles(user, team, ['admin'])

        # check that our team is listed under the /users/N/teams/ endpoint
        with self.current_user(username=user.username, password=user.password):
            teams = user.related.teams.get()
            assert teams.count == 1, "Target team not found under /api/v1/users/N/teams/."
            assert teams.results.pop().id == team.id, \
                "Unexpected team returned under /api/v1/users/N/teams/."

    def test_system_roles_forbidden(self, factories, api_roles_pg):
        """Teams are not allowed to be given the system admin and auditor roles."""
        team = factories.team()

        # find system admin and auditor roles
        roles_pg = api_roles_pg.get(role_field='system_auditor')
        assert roles_pg.count == 1, "Unexpected number of roles returned (expected 1)."
        auditor_role = roles_pg.results[0]
        roles_pg = api_roles_pg.get(role_field='system_administrator')
        assert roles_pg.count == 1, "Unexpected number of roles returned (expected 1)."
        admin_role = roles_pg.results[0]

        for role in [auditor_role, admin_role]:
            with pytest.raises(towerkit.exceptions.BadRequest):
                team.related.roles.post(dict(id=role.id))
