import http.client

import towerkit.exceptions as exc
import pytest

from tests.lib.helpers.rbac_utils import assert_response_raised, check_read_access
from tests.api import APITest


@pytest.mark.api
@pytest.mark.rbac
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestSmartInventoryRBAC(APITest):

    def check_host_filter_edit(self, smart_inventory, allowed=False):
        new_filter = "name=new_host_filter"
        if allowed:
            smart_inventory.host_filter = new_filter
            assert smart_inventory.host_filter == new_filter
        else:
            with pytest.raises(exc.Forbidden):
                smart_inventory.host_filter = new_filter

    def test_unprivileged_user(self, factories):
        host = factories.host()
        inventory = factories.inventory(organization=host.ds.inventory.ds.organization, kind='smart',
                                           host_filter='name={0}'.format(host.name))
        user = factories.user()

        with self.current_user(username=user.username, password=user.password):
            check_read_access(inventory, unprivileged=True)

            with pytest.raises(exc.Forbidden):
                inventory.related.ad_hoc_commands.post()

            self.check_host_filter_edit(inventory, allowed=False)
            assert_response_raised(host, http.client.FORBIDDEN)
            assert_response_raised(inventory, http.client.FORBIDDEN)

    def test_organization_admin(self, factories):
        host = factories.host()
        inventory = factories.inventory(organization=host.ds.inventory.ds.organization, kind='smart',
                                           host_filter='name={0}'.format(host.name))
        user = factories.user()
        inventory.ds.organization.set_object_roles(user, "admin")

        with self.current_user(user):
            check_read_access(inventory)
            self.check_host_filter_edit(inventory, allowed=True)
            assert_response_raised(host, http.client.OK)
            assert_response_raised(inventory, http.client.OK)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_admin_role(self, set_test_roles, agent, factories):
        host = factories.host()
        inventory = factories.inventory(organization=host.ds.inventory.ds.organization, kind='smart',
                                           host_filter='name={0}'.format(host.name))
        user = factories.user()

        set_test_roles(user, inventory, agent, "admin")

        with self.current_user(username=user.username, password=user.password):
            check_read_access(inventory, ["organization"])
            self.check_host_filter_edit(inventory, allowed=False)
            assert_response_raised(host, http.client.FORBIDDEN)
            assert_response_raised(inventory, http.client.OK)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_use_role(self, set_test_roles, agent, factories):
        host = factories.host()
        inventory = factories.inventory(organization=host.ds.inventory.ds.organization, kind='smart',
                                           host_filter='name={0}'.format(host.name))
        user = factories.user()

        set_test_roles(user, inventory, agent, "use")

        with self.current_user(username=user.username, password=user.password):
            check_read_access(inventory, ["organization"])
            self.check_host_filter_edit(inventory, allowed=False)
            assert_response_raised(host, http.client.FORBIDDEN)
            assert_response_raised(inventory, http.client.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_adhoc_role(self, set_test_roles, agent, factories):
        host = factories.host()
        inventory = factories.inventory(organization=host.ds.inventory.ds.organization, kind='smart',
                                           host_filter='name=localhost')
        user = factories.user()

        set_test_roles(user, inventory, agent, "ad hoc")

        with self.current_user(username=user.username, password=user.password):
            check_read_access(inventory, ["organization"])
            self.check_host_filter_edit(inventory, allowed=False)
            assert_response_raised(host, http.client.FORBIDDEN)
            assert_response_raised(inventory, http.client.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_read_role(self, set_test_roles, agent, factories):
        host = factories.host()
        inventory = factories.inventory(organization=host.ds.inventory.ds.organization, kind='smart',
                                           host_filter='name={0}'.format(host.name))
        user = factories.user()

        set_test_roles(user, inventory, agent, "read")

        with self.current_user(username=user.username, password=user.password):
            check_read_access(inventory, ["organization"])
            self.check_host_filter_edit(inventory, allowed=False)
            assert_response_raised(host, http.client.FORBIDDEN)
            assert_response_raised(inventory, http.client.FORBIDDEN)

    @pytest.mark.parametrize('role', ['admin', 'use', 'ad hoc', 'read'])
    def test_launch_command_with_smart_inventory(self, factories, role):
        ALLOWED_ROLES = ['admin', 'ad hoc']
        REJECTED_ROLES = ['use', 'read']

        host = factories.host()
        inventory = factories.inventory(organization=host.ds.inventory.ds.organization, kind='smart',
                                           host_filter='name={0}'.format(host.name))
        user = factories.user()
        credential = factories.credential(user=user)

        inventory.set_object_roles(user, role)

        with self.current_user(username=user.username, password=user.password):
            if role in ALLOWED_ROLES:
                ahc = factories.ad_hoc_command(inventory=inventory,
                                                  credential=credential,
                                                  module_name="ping").wait_until_completed()
                ahc.assert_successful()
            elif role in REJECTED_ROLES:
                with pytest.raises(exc.Forbidden):
                    factories.ad_hoc_command(inventory=inventory,
                                                credential=credential,
                                                module_name="ping")
            else:
                raise ValueError("Received unhandled inventory role.")
