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
class Test_Inventory_RBAC(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_unprivileged_user(self, host_local, aws_inventory_source, custom_group, factories):
        """An unprivileged user should not be able to:
        * Get the inventory detail
        * Get all of the inventory get_related
        * Update all groups that the inventory contains
        * Launch ad hoc commands against the inventory
        * Edit/delete the inventory
        * Create/edit/delete inventory groups and hosts
        """
        inventory = host_local.ds.inventory
        groups = inventory.related.groups.get()
        hosts = inventory.related.hosts.get()
        user = factories.user()

        commands = inventory.related.ad_hoc_commands.get()
        inv_source_update = aws_inventory_source.related.update.get()
        custom_group_update = custom_group.related.inventory_source.get().related.update()

        with self.current_user(username=user.username, password=user.password):
            # check GET as test user
            check_read_access(inventory, unprivileged=True)

            # update aws_group
            with pytest.raises(towerkit.exceptions.Forbidden):
                inv_source_update.post()

            # update custom group
            with pytest.raises(towerkit.exceptions.Forbidden):
                custom_group_update.post()

            # post command
            with pytest.raises(towerkit.exceptions.Forbidden):
                commands.post()

            # check ability to create group and host
            with pytest.raises(towerkit.exceptions.Forbidden):
                groups.post()
            with pytest.raises(towerkit.exceptions.Forbidden):
                hosts.post()

            # check put/patch/delete on inventory, custom_group, and host_local
            assert_response_raised(host_local, httplib.FORBIDDEN)
            assert_response_raised(custom_group, httplib.FORBIDDEN)
            assert_response_raised(inventory, httplib.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_admin_role(self, host_local, set_test_roles, agent, factories):
        """A user/team with inventory 'admin' should be able to:
        * Get the inventory detail
        * Get all of the inventory get_related
        * Edit/delete the inventory
        * Create/edit/delete inventory groups and hosts
        """
        inventory = host_local.get_related('inventory')
        groups = inventory.get_related('groups')
        hosts = inventory.get_related('hosts')
        group_payload = factories.group.payload(inventory=inventory)[0]
        host_payload = factories.host.payload(inventory=inventory)[0]

        group = factories.group(inventory=inventory)
        user = factories.user()

        # give agent admin_role
        set_test_roles(user, inventory, agent, "admin")

        with self.current_user(username=user.username, password=user.password):
            # check GET as test user
            check_read_access(inventory, ["organization"])

            # check ability to create group and host
            groups.post(group_payload)
            hosts.post(host_payload)

            # check put/patch/delete on inventory, custom_group, and host_local
            assert_response_raised(host_local, httplib.OK)
            assert_response_raised(group, httplib.OK)
            assert_response_raised(inventory, httplib.OK)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_use_role(self, host_local, set_test_roles, agent, factories):
        """A user/team with inventory 'use' should be able to:
        * Get the inventory detail
        * Get all of the inventory get_related
        A user/team with inventory 'use' should not be able to:
        * Edit/delete the inventory
        * Create/edit/delete inventory groups and hosts
        """
        inventory = host_local.get_related('inventory')
        groups = inventory.get_related('groups')
        hosts = inventory.get_related('hosts')
        group_payload = factories.group.payload(inventory=inventory)[0]
        host_payload = factories.host.payload(inventory=inventory)[0]

        group = factories.group(inventory=inventory)
        user = factories.user()

        # give agent use_role
        set_test_roles(user, inventory, agent, "use")

        with self.current_user(username=user.username, password=user.password):
            # check GET as test user
            check_read_access(inventory, ["organization"])

            # check ability to create group and host
            with pytest.raises(towerkit.exceptions.Forbidden):
                groups.post(group_payload)
            with pytest.raises(towerkit.exceptions.Forbidden):
                hosts.post(host_payload)

            # check put/patch/delete on inventory, custom_group, and host_local
            assert_response_raised(host_local, httplib.FORBIDDEN)
            assert_response_raised(group, httplib.FORBIDDEN)
            assert_response_raised(inventory, httplib.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_adhoc_role(self, host_local, set_test_roles, agent, factories):
        """A user/team with inventory 'adhoc' should be able to:
        * Get the inventory detail
        * Get all of the inventory get_related
        A user/team with inventory 'adhoc' should not be able to:
        * Edit/delete the inventory
        * Create/edit/delete inventory groups and hosts
        """
        inventory = host_local.get_related('inventory')
        groups = inventory.get_related('groups')
        hosts = inventory.get_related('hosts')
        group_payload = factories.group.payload(inventory=inventory)[0]
        host_payload = factories.host.payload(inventory=inventory)[0]

        group = factories.group(inventory=inventory)
        user = factories.user()

        # give agent adhoc_role
        set_test_roles(user, inventory, agent, "ad hoc")

        with self.current_user(username=user.username, password=user.password):
            # check GET as test user
            check_read_access(inventory, ["organization"])

            # check ability to create group and host
            with pytest.raises(towerkit.exceptions.Forbidden):
                groups.post(group_payload)
            with pytest.raises(towerkit.exceptions.Forbidden):
                hosts.post(host_payload)

            # check put/patch/delete on inventory, custom_group, and host_local
            assert_response_raised(host_local, httplib.FORBIDDEN)
            assert_response_raised(group, httplib.FORBIDDEN)
            assert_response_raised(inventory, httplib.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_update_role(self, host_local, set_test_roles, agent, factories):
        """A user/team with inventory 'update' should be able to:
        * Get the inventory detail
        * Get all of the inventory get_related
        A user/team with inventory 'update' should not be able to:
        * Edit/delete the inventory
        * Create/edit/delete inventory groups and hosts
        """
        inventory = host_local.get_related('inventory')
        groups = inventory.get_related('groups')
        hosts = inventory.get_related('hosts')
        group_payload = factories.group.payload(inventory=inventory)[0]
        host_payload = factories.host.payload(inventory=inventory)[0]

        group = factories.group(inventory=inventory)
        user = factories.user()

        # give agent update_role
        set_test_roles(user, inventory, agent, "update")

        with self.current_user(username=user.username, password=user.password):
            # check GET as test user
            check_read_access(inventory, ["organization"])

            # check ability to create group and host
            with pytest.raises(towerkit.exceptions.Forbidden):
                groups.post(group_payload)
            with pytest.raises(towerkit.exceptions.Forbidden):
                hosts.post(host_payload)

            # check put/patch/delete on inventory, custom_group, and host_local
            assert_response_raised(host_local, httplib.FORBIDDEN)
            assert_response_raised(group, httplib.FORBIDDEN)
            assert_response_raised(inventory, httplib.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_read_role(self, host_local, set_test_roles, agent, factories):
        """A user/team with inventory 'read' should be able to:
        * Get the inventory detail
        * Get all of the inventory get_related
        A user/team with inventory 'read' should not be able to:
        * Edit/delete the inventory
        * Create/edit/delete inventory groups and hosts
        """
        inventory = host_local.get_related('inventory')
        groups = inventory.get_related('groups')
        hosts = inventory.get_related('hosts')
        group_payload = factories.group.payload(inventory=inventory)[0]
        host_payload = factories.host.payload(inventory=inventory)[0]

        group = factories.group(inventory=inventory)
        user = factories.user()

        # give agent read_role
        set_test_roles(user, inventory, agent, "read")

        with self.current_user(username=user.username, password=user.password):
            # check GET as test user
            check_read_access(inventory, ["organization"])

            # check ability to create group and host
            with pytest.raises(towerkit.exceptions.Forbidden):
                groups.post(group_payload)
            with pytest.raises(towerkit.exceptions.Forbidden):
                hosts.post(host_payload)

            # check put/patch/delete on inventory, custom_group, and host_local
            assert_response_raised(host_local, httplib.FORBIDDEN)
            assert_response_raised(group, httplib.FORBIDDEN)
            assert_response_raised(inventory, httplib.FORBIDDEN)

    @pytest.mark.parametrize('agent', ['user', 'team'])
    @pytest.mark.parametrize('role', ['admin', 'use', 'ad hoc', 'update', 'read'])
    def test_user_capabilities(self, factories, api_inventories, set_test_roles, agent, role):
        """Test user_capabilities given each inventory role.
        Note: this test serves as a smokescreen test with user_capabilites and team credentials.
        This is the only place in tower-qa where we test user_capabilities with team credentials.
        """
        inventory = factories.inventory()
        factories.group(inventory=inventory)
        user = factories.user()

        # give agent target role privileges
        set_test_roles(user, inventory, agent, role)

        with self.current_user(username=user.username, password=user.password):
            check_user_capabilities(inventory.get(), role)
            check_user_capabilities(api_inventories.get(id=inventory.id).results.pop(), role)

    @pytest.mark.parametrize('role', ['admin', 'use', 'ad hoc', 'update', 'read'])
    def test_update_custom_group(self, factories, custom_inventory_source, role):
        """Test ability to update a custom group."""
        ALLOWED_ROLES = ['admin', 'update']
        REJECTED_ROLES = ['use', 'ad hoc', 'read']

        user = factories.user()

        # give test user target role privileges
        inventory = custom_inventory_source.related.inventory.get()
        inventory.set_object_roles(user, role)

        with self.current_user(username=user.username, password=user.password):
            if role in ALLOWED_ROLES:
                update = custom_inventory_source.update().wait_until_completed()
                assert update.is_successful, "Update unsuccessful - %s." % update
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    custom_inventory_source.update()
            else:
                raise ValueError("Received unhandled inventory role.")

    @pytest.mark.parametrize('role', ['admin', 'use', 'ad hoc', 'update', 'read'])
    def test_update_cloud_group(self, factories, aws_inventory_source, role):
        """Test ability to update a cloud group. Note: only tested on AWS to save time.
        Also, user should be able launch update even though cloud_credential is under
        admin user.
        """
        ALLOWED_ROLES = ['admin', 'update']
        REJECTED_ROLES = ['use', 'ad hoc', 'read']

        user = factories.user()

        # give agent target role privileges
        inventory = aws_inventory_source.related.inventory.get()
        inventory.set_object_roles(user, role)

        with self.current_user(username=user.username, password=user.password):
            if role in ALLOWED_ROLES:
                update = aws_inventory_source.update().wait_until_completed()
                assert update.is_successful, "Update unsuccessful - %s." % update
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    aws_inventory_source.update()
            else:
                raise ValueError("Received unhandled inventory role.")

    @pytest.mark.parametrize('role', ['admin', 'use', 'ad hoc', 'update', 'read'])
    def test_schedule_update(self, factories, custom_inventory_source, role):
        """Tests ability to schedule an inventory update."""
        ALLOWED_ROLES = ['admin', 'update']
        REJECTED_ROLES = ['use', 'ad hoc', 'read']

        user = factories.user()

        # give test user target role privileges
        inventory = custom_inventory_source.get_related('inventory')
        inventory.set_object_roles(user, role)

        with self.current_user(username=user.username, password=user.password):
            if role in ALLOWED_ROLES:
                schedule = custom_inventory_source.add_schedule()
                assert_response_raised(schedule, methods=('get', 'put', 'patch', 'delete'))
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    custom_inventory_source.add_schedule()
            else:
                raise ValueError("Received unhandled inventory role.")

    @pytest.mark.parametrize('role', ['admin', 'use', 'ad hoc', 'update', 'read'])
    def test_cancel_update(self, factories, aws_inventory_source, role):
        """Tests inventory update cancellation. Inventory admins can cancel other people's updates."""
        ALLOWED_ROLES = ['admin']
        REJECTED_ROLES = ['update', 'use', 'ad hoc', 'read']

        user = factories.user()

        # give test user target role privileges
        inventory = aws_inventory_source.get_related('inventory')
        inventory.set_object_roles(user, role)

        # launch inventory update
        update = aws_inventory_source.update()

        with self.current_user(username=user.username, password=user.password):
            if role in ALLOWED_ROLES:
                update.cancel()
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    update.cancel()
                # wait for inventory update to finish to ensure clean teardown
                update.wait_until_completed()
            else:
                raise ValueError("Received unhandled inventory role.")

    @pytest.mark.parametrize('role', ['admin', 'use', 'ad hoc', 'update', 'read'])
    def test_delete_update(self, factories, custom_inventory_source, role):
        """Tests ability to delete an inventory update."""
        ALLOWED_ROLES = ['admin']
        REJECTED_ROLES = ['use', 'ad hoc', 'update', 'read']

        user = factories.user()

        # give test user target role privileges
        inventory = custom_inventory_source.get_related('inventory')
        inventory.set_object_roles(user, role)

        # launch inventory update
        update = custom_inventory_source.update()

        with self.current_user(username=user.username, password=user.password):
            if role in ALLOWED_ROLES:
                update.delete()
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    update.delete()
                # wait for inventory update to finish to ensure clean teardown
                update.wait_until_completed()
            else:
                raise ValueError("Received unhandled inventory role.")

    @pytest.mark.parametrize('role', ['admin', 'update', 'use', 'read'])
    def test_update_user_capabilities(self, factories, custom_inventory_source, api_inventory_updates, role):
        """Test user_capabilities given each inventory role on spawned
        inventory_updates.
        """
        user = factories.user()

        # give test user target role privileges
        inventory = custom_inventory_source.get_related('inventory')
        inventory.set_object_roles(user, role)

        # launch inventory_update
        update = custom_inventory_source.update().wait_until_completed()

        with self.current_user(username=user.username, password=user.password):
            check_user_capabilities(update.get(), role)
            check_user_capabilities(api_inventory_updates.get(id=update.id).results.pop(), role)

    @pytest.mark.parametrize('role', ['admin', 'use', 'ad hoc', 'update', 'read'])
    def test_launch_command(self, factories, role):
        """Test ability to launch a command."""
        ALLOWED_ROLES = ['admin', 'ad hoc']
        REJECTED_ROLES = ['use', 'update', 'read']

        inventory = factories.inventory()
        user = factories.user()
        credential = factories.credential(user=user, organization=None)

        # create command fixtures
        ad_hoc_commands = inventory.get_related('ad_hoc_commands')
        payload = dict(inventory=inventory.id,
                       credential=credential.id,
                       module_name="ping")

        # give test user target role privileges
        inventory.set_object_roles(user, role)

        with self.current_user(username=user.username, password=user.password):
            if role in ALLOWED_ROLES:
                command = ad_hoc_commands.post(payload).wait_until_completed()
                assert command.is_successful, "Command unsuccessful - %s." % command
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    ad_hoc_commands.post(payload)
            else:
                raise ValueError("Received unhandled inventory role.")

    @pytest.mark.parametrize('role', ['admin', 'use', 'ad hoc', 'update', 'read'])
    def test_relaunch_command(self, factories, role):
        """Tests ability to relaunch a command."""
        ALLOWED_ROLES = ['admin', 'ad hoc']
        REJECTED_ROLES = ['use', 'update', 'read']

        inventory = factories.inventory()
        user = factories.user()
        credential = factories.credential(user=user, organization=None)

        # launch command
        payload = dict(inventory=inventory.id,
                       credential=credential.id,
                       module_name="ping")
        command = inventory.get_related('ad_hoc_commands').post(payload).wait_until_completed()
        assert command.is_successful, "Command unsuccessful - %s." % command

        # give test user target role privileges
        inventory.set_object_roles(user, role)

        with self.current_user(username=user.username, password=user.password):
            if role in ALLOWED_ROLES:
                relaunched_command = command.relaunch().wait_until_completed()
                assert relaunched_command.is_successful, "Command unsuccessful - %s." % command
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    command.relaunch()
            else:
                raise ValueError("Received unhandled inventory role.")

    @pytest.mark.parametrize('role', ['admin', 'use', 'ad hoc', 'update', 'read'])
    def test_cancel_command(self, factories, role):
        """Tests command cancellation. Inventory admins can cancel other people's commands."""
        ALLOWED_ROLES = ['admin']
        REJECTED_ROLES = ['ad hoc', 'use', 'update', 'read']

        inventory = factories.inventory()
        user = factories.user()
        credential = factories.credential(user=user, organization=None)

        # give test user target role privileges
        inventory.set_object_roles(user, role)

        # launch command
        payload = dict(inventory=inventory.id,
                       credential=credential.id,
                       module_args="sleep 10")
        command = inventory.get_related('ad_hoc_commands').post(payload)

        with self.current_user(username=user.username, password=user.password):
            if role in ALLOWED_ROLES:
                command.cancel()
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    command.cancel()
            else:
                raise ValueError("Received unhandled inventory role.")

    def test_delete_command_as_org_admin(self, factories):
        """Create two ad hoc commands and an org_admin for each of these commands.
        Then check that each org_admin may only delete his org's command.
        Note: command deletion is organization scoped. A command's inventory determines
        its organization.
        """
        # create items for command payloads
        inventory1 = factories.inventory()
        inventory2 = factories.inventory()
        inv_org1 = inventory1.get_related('organization')
        inv_org2 = inventory2.get_related('organization')
        credential1 = factories.credential(organization=inv_org1)
        credential2 = factories.credential(organization=inv_org2)

        # sanity check
        assert inv_org1.id != inv_org2, "Test inventories unexpectedly in the same organization."

        # create org_admins
        org_admin1 = factories.user()
        org_admin2 = factories.user()
        inv_org1.set_object_roles(org_admin1, 'admin')
        inv_org2.set_object_roles(org_admin2, 'admin')

        # launch both commands
        payload = dict(inventory=inventory1.id,
                       credential=credential1.id,
                       module_name="ping")
        command1 = inventory1.get_related('ad_hoc_commands').post(payload)
        payload = dict(inventory=inventory2.id,
                       credential=credential2.id,
                       module_name="ping")
        command2 = inventory2.get_related('ad_hoc_commands').post(payload)

        # assert that each org_admin cannot delete other organization's command
        with self.current_user(username=org_admin1.username, password=org_admin1.password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                command2.delete()
        with self.current_user(username=org_admin2.username, password=org_admin2.password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                command1.delete()

        # assert that each org_admin can delete his own organization's command
        with self.current_user(username=org_admin1.username, password=org_admin1.password):
            command1.delete()
        with self.current_user(username=org_admin2.username, password=org_admin2.password):
            command2.delete()

    def test_delete_command_as_org_user(self, factories):
        """Tests ability to delete an ad hoc command as a privileged org_user."""
        inventory = factories.inventory()
        user = factories.user()
        credential = factories.credential(user=user, organization=None)

        inventory.set_object_roles(user, "admin")

        # launch command
        payload = dict(inventory=inventory.id,
                       credential=credential.id,
                       module_name="ping")
        command = inventory.get_related('ad_hoc_commands').post(payload)

        with self.current_user(username=user.username, password=user.password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                command.delete()
            # wait for ad hoc command to finish to ensure clean teardown
            command.wait_until_completed()

    @pytest.mark.parametrize('role', ['admin', 'use', 'ad hoc', 'update', 'read'])
    def test_command_user_capabilities(self, factories, api_ad_hoc_commands_pg, role):
        """Test user_capabilities given each inventory role on spawned
        ad hoc commands.
        """
        inventory = factories.inventory()
        user = factories.user()
        credential = factories.credential(user=user, organization=None)

        inventory.set_object_roles(user, role)

        # launch command
        payload = dict(inventory=inventory.id,
                       credential=credential.id,
                       module_name="ping")
        command = inventory.get_related('ad_hoc_commands').post(payload).wait_until_completed()

        with self.current_user(username=user.username, password=user.password):
            check_user_capabilities(command.get(), role)
            check_user_capabilities(api_ad_hoc_commands_pg.get(id=command.id).results.pop(), role)

    def test_cloud_credential_reassignment(self, factories, openstack_v2_credential, admin_user):
        """Test that a user with inventory-admin may not patch an inventory source with another user's
        personal user credential.
        """
        inventory = factories.inventory()
        user = factories.user()

        inventory.set_object_roles(user, 'admin')

        with self.current_user(username=user.username, password=user.password):
            os_cred = factories.credential(kind='openstack',
                                           user=user,
                                           organization=None,
                                           password=self.credentials['cloud']['openstack_v2']['password'])
            os_group = factories.group(inventory=inventory, credential=os_cred)
            with pytest.raises(towerkit.exceptions.Forbidden):
                os_group.related.inventory_source.patch(credential=openstack_v2_credential.id)
