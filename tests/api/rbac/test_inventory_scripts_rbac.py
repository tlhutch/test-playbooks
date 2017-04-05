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
class Test_Inventory_Script_RBAC(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_unprivileged_user(self, factories, inventory_script):
        """An unprivileged user/team may not be able to:
        * Get your inventory_script detail page
        * Get all of your inventory_script get_related
        * Edit your inventory script
        * Delete your inventory script
        """
        user = factories.user()

        with self.current_user(username=user.username, password=user.password):
            # check GET as test user
            check_read_access(inventory_script, unprivileged=True)

            # check put/patch/delete
            assert_response_raised(inventory_script, httplib.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_admin_role(self, factories, inventory_script, set_test_roles, agent):
        """A user/team with inventory_script 'admin' should be able to:
        * Get your inventory_script detail page
        * Get all of your inventory_script get_related
        * Edit your inventory script
        * Delete your inventory script
        """
        user = factories.user()

        # assert value for 'script' present
        assert inventory_script.script
        script = inventory_script.script

        # give agent admin_role
        set_test_roles(user, inventory_script, agent, "admin")

        with self.current_user(username=user.username, password=user.password):
            # check GET as test user
            check_read_access(inventory_script, ["organization"])

            # check that value of 'script' viewable
            assert inventory_script.script == script, \
                "Unexpected value for 'script'; expected %s but got %s." % (script, inventory_script.script)

            # check put/patch/delete
            assert_response_raised(inventory_script, httplib.OK)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_read_role(self, factories, inventory_script, set_test_roles, agent):
        """A user/team with inventory_script 'read' should be able to:
        * Get your inventory_script detail page
        * Get all of your inventory_script get_related
        A user/team with inventory_script 'read' should not be able to:
        * Edit your inventory script
        * Delete your inventory script
        """
        user = factories.user()

        # assert value for 'script' present
        assert inventory_script.script

        # give agent read_role
        set_test_roles(user, inventory_script, agent, "read")

        with self.current_user(username=user.username, password=user.password):
            # check GET as test user
            check_read_access(inventory_script, ["organization"])

            # check that value of 'script' not viewable
            assert not inventory_script.script, \
                "Unexpected value for 'script'; expected null but got %s." % inventory_script.script

            # check put/patch/delete
            assert_response_raised(inventory_script, httplib.FORBIDDEN)

    @pytest.mark.parametrize('role', ['admin', 'read'])
    def test_user_capabilities(self, factories, inventory_script, api_inventory_scripts_pg, role):
        """Test user_capabilities given each inventory_script role."""
        user = factories.user()

        # give test user target role privileges
        set_roles(user, inventory_script, [role])

        with self.current_user(username=user.username, password=user.password):
            check_user_capabilities(inventory_script.get(), role)
            check_user_capabilities(api_inventory_scripts_pg.get(id=inventory_script.id).results.pop(), role)

    def test_able_to_assign_inventory_script_to_different_org(self, factories, inventory_script, organization,
                                                              another_organization):
        """Tests that org_admins can reassign an inventory_script to an organization for which they
        are an admin.
        """
        user = factories.user()
        set_roles(user, organization, ['admin'])
        set_roles(user, another_organization, ['admin'])

        # assert that org_admin can reassign label
        with self.current_user(username=user.username, password=user.password):
            inventory_script.patch(organization=another_organization.id)

    def test_unable_to_assign_inventory_script_to_different_org(self, factories, inventory_script, organization,
                                                                another_organization):
        """Tests that org_admins cannot reassign an inventory_script to an organization for which they
        are only a member.
        """
        user = factories.user()
        set_roles(user, organization, ['admin'])
        set_roles(user, another_organization, ['member'])

        # assert that org_admin cannot reassign label
        with self.current_user(username=user.username, password=user.password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                inventory_script.patch(organization=another_organization.id)
