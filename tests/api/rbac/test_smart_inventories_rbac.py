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
@pytest.mark.skip_selenium
class TestSmartInventoryRBAC(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_unprivileged_user(self, factories):
        """An unprivileged user should not be able to:
        * Get the inventory detail page
        * Get all of the inventory related pages
        * Edit/delete the inventory
        * Edit/delete inventory host
        """
        host = factories.v2_host()
        inventory = factories.v2_inventory(kind='smart', host_filter='name={0}'.format(host.name))
        user = factories.user()

        with self.current_user(username=user.username, password=user.password):
            check_read_access(inventory, unprivileged=True)

            with pytest.raises(towerkit.exceptions.Forbidden):
                inventory.related.ad_hoc_commands.post()

            for resource in [host, inventory]:
                assert_response_raised(resource, httplib.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_admin_role(self, set_test_roles, agent, factories):
        host = factories.v2_host()
        inventory = factories.v2_inventory(kind='smart', host_filter='name={0}'.format(host.name))
        user = factories.user()

        set_test_roles(user, inventory, agent, "admin")

        with self.current_user(username=user.username, password=user.password):
            check_read_access(inventory, ["organization"])
            assert_response_raised(host, httplib.FORBIDDEN)
            assert_response_raised(inventory, httplib.OK)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_use_role(self, set_test_roles, agent, factories):
        host = factories.v2_host()
        inventory = factories.v2_inventory(kind='smart', host_filter='name={0}'.format(host.name))
        user = factories.user()

        set_test_roles(user, inventory, agent, "use")

        with self.current_user(username=user.username, password=user.password):
            check_read_access(inventory, ["organization"])
            assert_response_raised(host, httplib.FORBIDDEN)
            assert_response_raised(inventory, httplib.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_adhoc_role(self, set_test_roles, agent, factories):
        host = factories.v2_host()
        inventory = factories.v2_inventory(kind='smart', host_filter='name=localhost')
        user = factories.user()
        credential = factories.v2_credential(user=user)

        set_test_roles(user, inventory, agent, "ad hoc")

        with self.current_user(username=user.username, password=user.password):
            check_read_access(inventory, ["organization"])
            factories.v2_ad_hoc_command(inventory=inventory, credential=credential, module_name='shell',
                                        module_args='true').wait_until_completed()
            assert_response_raised(host, httplib.FORBIDDEN)
            assert_response_raised(inventory, httplib.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_read_role(self, set_test_roles, agent, factories):
        host = factories.v2_host()
        inventory = factories.v2_inventory(kind='smart', host_filter='name={0}'.format(host.name))
        user = factories.user()

        set_test_roles(user, inventory, agent, "read")

        with self.current_user(username=user.username, password=user.password):
            check_read_access(inventory, ["organization"])
            assert_response_raised(host, httplib.FORBIDDEN)
            assert_response_raised(inventory, httplib.FORBIDDEN)

    @pytest.mark.parametrize('role', ['admin', 'use', 'ad hoc', 'update', 'read'])
    def test_user_capabilities(self, factories, v2, role):
        host = factories.v2_host()
        inventory = factories.v2_inventory(kind='smart', host_filter='name={0}'.format(host.name))
        user = factories.user()

        inventory.set_object_roles(user, role)

        with self.current_user(username=user.username, password=user.password):
            check_user_capabilities(inventory.get(), role)
            check_user_capabilities(v2.inventory.get(id=inventory.id).results.pop(), role)
