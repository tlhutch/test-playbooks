import pytest
import httplib

import towerkit.exceptions
from tests.lib.helpers.rbac_utils import (
    assert_response_raised,
    check_read_access,
    check_user_capabilities,
    get_resource_roles,
    set_roles
)
from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.rbac
@pytest.mark.skip_selenium
class Test_Credential_RBAC(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_unprivileged_user(self, factories, user_password):
        """An unprivileged user/team should not be able to:
        * Make GETs to the credential detail page
        * Make GETs to all of the credential get_related
        * Edit the credential
        * Delete the credential
        """
        credential_pg = factories.credential()
        user_pg = factories.user(organization=credential_pg.get_related('organization'))

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(credential_pg, unprivileged=True)

            # check put/patch/delete
            assert_response_raised(credential_pg, httplib.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_admin_role(self, factories, set_test_roles, agent, user_password):
        """A user/team with credential 'admin' should be able to:
        * Make GETs to the credential detail page
        * Make GETs to all of the credential get_related
        * Edit the credential
        * Delete the credential
        """
        credential_pg = factories.credential()
        user_pg = factories.user(organization=credential_pg.get_related('organization'))

        # give agent admin_role
        set_test_roles(user_pg, credential_pg, agent, "admin")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(credential_pg)

            # check put/patch/delete
            assert_response_raised(credential_pg, httplib.OK)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_use_role(self, factories, set_test_roles, agent, user_password):
        """A user/team with credential 'use' should be able to:
        * Make GETs to the credential detail page
        * Make GETs to all of the credential get_related
        A user/team with credential 'use' should not be able to:
        * Edit the credential
        * Delete the credential
        """
        credential_pg = factories.credential()
        user_pg = factories.user(organization=credential_pg.get_related('organization'))

        # give agent use_role
        set_test_roles(user_pg, credential_pg, agent, "use")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(credential_pg, ['user'])

            # check put/patch/delete
            assert_response_raised(credential_pg, httplib.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_read_role(self, factories, set_test_roles, agent, user_password):
        """A user/team with credential 'read' should be able to:
        * Make GETs to the credential detail page
        * Make GETs to all of the credential get_related
        A user/team with credential 'read' should not be able to:
        * Edit the credential
        * Delete the credential
        """
        credential_pg = factories.credential()
        user_pg = factories.user(organization=credential_pg.get_related('organization'))

        # give agent read_role
        set_test_roles(user_pg, credential_pg, agent, "read")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(credential_pg, ['user'])

            # check put/patch/delete
            assert_response_raised(credential_pg, httplib.FORBIDDEN)

    @pytest.mark.parametrize('role', ['admin', 'use', 'read'])
    def test_user_capabilities(self, factories, user_password, api_credentials_pg, role):
        """Test user_capabilities given each credential role."""
        credential_pg = factories.credential()
        user_pg = factories.user(organization=credential_pg.get_related('organization'))

        # give test user target role privileges
        set_roles(user_pg, credential_pg, [role])

        with self.current_user(username=user_pg.username, password=user_password):
            check_user_capabilities(credential_pg.get(), role)
            check_user_capabilities(api_credentials_pg.get(id=credential_pg.id).results.pop(), role)

    def test_autopopulated_admin_role_with_user_credentials(self, factories):
        """Tests that when you create a credential with a value supplied for 'user'
        that your user is automatically given the admin role of your credential.
        """
        user_pg = factories.user()

        # assert newly created user has no roles
        assert not user_pg.get_related('roles').count, \
            "Newly created user created unexpectedly with roles - %s." % user_pg.get_related('roles')

        # assert user now has admin role after user credential creation
        credential_pg = factories.credential(user=user_pg, organization=None)
        admin_role_users_pg = credential_pg.get_object_role('admin_role').get_related('users')
        assert admin_role_users_pg.count == 1, \
            "Unexpected number of users with our credential admin role. Expected one, got %s." % admin_role_users_pg.count
        assert admin_role_users_pg.results[0].id == user_pg.id, \
            "Unexpected admin role user returned. Expected user with ID %s, but %s." % (user_pg.id, admin_role_users_pg.results[0].id)

    @pytest.mark.parametrize("agent_name", ["admin_user", "org_user"])
    def test_user_credential_role_assignment(self, request, factories, agent_name):
        """Tests that only superusers may grant user-credential roles to other users and that
        both superusers and regular users cannot grant user-credential roles to teams.
        """
        # create user credential
        user = factories.user()
        credential = factories.credential(user=user, organization=None)
        # create another user and team
        another_user = factories.user()
        team = factories.team()

        agent = request.getfuncargvalue(agent_name)
        role_names = get_resource_roles(credential)
        with self.current_user(agent.username, agent.password):
            for role_name in role_names:
                # superusers may assign credential roles to another user
                if agent_name == "admin_user":
                    credential.set_object_roles(another_user, role_name)
                # regular users may not assign credential roles to another user
                else:
                    with pytest.raises(towerkit.exceptions.Forbidden):
                        credential.set_object_roles(another_user, role_name)
                # superusers should receive 400
                if agent_name == "admin_user":
                    with pytest.raises(towerkit.exceptions.BadRequest):
                        credential.set_object_roles(team, role_name)
                # regular users should receive 403
                else:
                    with pytest.raises(towerkit.exceptions.Forbidden):
                        credential.set_object_roles(team, role_name)

    def test_invalid_organization_credential_role_assignment(self, factories):
        """Tests that organization credentials may not have their roles assigned to users
        and teams who exist outside of their organization.
        """
        # create an organization credential
        organization = factories.organization()
        credential = factories.credential(organization=organization)
        # user from another organization may not be assigned any of our credential roles
        another_organization = factories.organization()
        user = factories.user(organization=another_organization)
        role_names = get_resource_roles(credential)
        for role_name in role_names:
            with pytest.raises(towerkit.exceptions.BadRequest):
                credential.set_object_roles(user, role_name)
        # team from another organization may not be assigned any of our credential roles
        team = factories.team(organization=another_organization)
        for role_name in role_names:
            with pytest.raises(towerkit.exceptions.BadRequest):
                credential.set_object_roles(team, role_name)

    def test_valid_organization_credential_role_assignment(self, factories):
        """Tests that organization credentials may have their roles assigned to users
        and teams who exist within their own organization.
        """
        # create an organization credential
        organization = factories.organization()
        credential = factories.credential(organization=organization)
        # user from another organization may be assigned our credential roles
        user = factories.user(organization=organization)
        role_names = get_resource_roles(credential)
        for role_name in role_names:
            credential.set_object_roles(user, role_name)
        # team from another organization may be assigned our credential roles
        team = factories.team(organization=organization)
        for role_name in role_names:
            credential.set_object_roles(team, role_name)
