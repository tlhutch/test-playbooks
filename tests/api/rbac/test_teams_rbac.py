import pytest
import httplib

import towerkit.exceptions
from tests.lib.helpers.rbac_utils import (
    assert_response_raised,
    check_read_access,
    check_user_capabilities
)
from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.rbac
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class Test_Team_RBAC(Base_Api_Test):

    def test_unprivileged_user(self, factories):
        """An unprivileged user/team may not be able to:
        * Get the team details page
        * Get all of the team related pages
        * Edit the team
        * Delete the team
        """
        team = factories.team()
        user = factories.user()

        with self.current_user(username=user.username, password=user.password):
            # check GET as test user
            check_read_access(team, unprivileged=True)

            # check put/patch/delete
            assert_response_raised(team, httplib.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_admin_role(self, factories, set_test_roles, agent):
        """A user/team with team 'admin_role' should be able to:
        * Get the team details page
        * Get all of the team related pages
        * Edit the team
        * Delete the team
        """
        team = factories.team()
        user = factories.user()

        # give agent admin_role
        set_test_roles(user, team, agent, "admin")

        with self.current_user(username=user.username, password=user.password):
            # check GET as test user
            check_read_access(team, ['organization'])

            # check put/patch/delete
            assert_response_raised(team, httplib.OK)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_member_role(self, factories, set_test_roles, agent):
        """A user/team with team 'member_role' should be able to:
        * Get the team details page
        * Get all of the team related pages
        A user/team with team 'member_role' should not be able to:
        * Edit the team
        * Delete the team
        """
        team = factories.team()
        user = factories.user()

        # give agent member_role
        set_test_roles(user, team, agent, "member")

        with self.current_user(username=user.username, password=user.password):
            # check GET as test user
            check_read_access(team, ['organization'])

            # check put/patch/delete
            assert_response_raised(team, httplib.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_read_role(self, factories, set_test_roles, agent):
        """A user/team with team 'read_role' should be able to:
        * Get the team details page
        * Get all of the team related pages
        A user/team with team 'read_role' should not be able to:
        * Edit the team
        * Delete the team
        """
        team = factories.team()
        user = factories.user()

        # give agent read_role
        set_test_roles(user, team, agent, "read")

        with self.current_user(username=user.username, password=user.password):
            # check GET as test user
            check_read_access(team, ['organization'])

            # check put/patch/delete
            assert_response_raised(team, httplib.FORBIDDEN)

    @pytest.mark.parametrize('role', ['admin', 'member', 'read'])
    def test_user_capabilities(self, factories, api_teams_pg, role):
        """Test user_capabilities given each team role."""
        team = factories.team()
        user = factories.user()

        team.set_object_roles(user, role)

        with self.current_user(username=user.username, password=user.password):
            check_user_capabilities(team.get(), role)
            check_user_capabilities(api_teams_pg.get(id=team.id).results.pop(), role)

    def test_member_role_association(self, factories):
        """Tests that after a user is granted the member_role that he now shows
        up under /api/v1/teams/N/users/.
        """
        team = factories.team()
        user = factories.user()

        # team by default should have no users
        users = team.related.users.get()
        assert users.count == 0, "Users unexpectedly found for our team."

        # give test user member role privileges
        team.set_object_roles(user, "member")

        # assert that /teams/N/users/ now shows test user
        assert users.get().count == 1, "Expected one user under /teams/N/users/."
        assert users.results[0].id == user.id, \
            "Team user not our target user. Expected user with ID %s but received ID %s instead." % (user.id, users.results[0].id)

    def test_member_role_inheritance(self, factories):
        """Test that team-member gets included with team-admin permissions."""
        team = factories.team()
        user = factories.user()

        team.set_object_roles(user, "admin")

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
        roles = api_roles_pg.get(role_field='system_auditor')
        assert roles.count == 1, "Unexpected number of roles returned (expected 1)."
        auditor_role = roles.results[0]
        roles = api_roles_pg.get(role_field='system_administrator')
        assert roles.count == 1, "Unexpected number of roles returned (expected 1)."
        admin_role = roles.results[0]

        for role in [auditor_role, admin_role]:
            with pytest.raises(towerkit.exceptions.BadRequest):
                team.related.roles.post(dict(id=role.id))
