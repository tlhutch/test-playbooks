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
class Test_Inventory_RBAC(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_unprivileged_user(self, host_local, aws_inventory_source, custom_group, user_password, factories):
        """An unprivileged user should not be able to:
        * Get the inventory detail
        * Get all of the inventory get_related
        * Update all groups that the inventory contains
        * Launch ad hoc commands against the inventory
        * Edit/delete the inventory
        * Create/edit/delete inventory groups and hosts
        """
        inventory_pg = host_local.get_related('inventory')
        groups_pg = inventory_pg.get_related('groups')
        hosts_pg = inventory_pg.get_related('hosts')
        user_pg = factories.user()

        commands_pg = inventory_pg.get_related('ad_hoc_commands')
        inv_source_update_pg = aws_inventory_source.get_related('update')
        custom_group_update_pg = custom_group.get_related('inventory_source').get_related('update')

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(inventory_pg, unprivileged=True)

            # update aws_group
            with pytest.raises(towerkit.exceptions.Forbidden):
                inv_source_update_pg.post()

            # update custom group
            with pytest.raises(towerkit.exceptions.Forbidden):
                custom_group_update_pg.post()

            # post command
            with pytest.raises(towerkit.exceptions.Forbidden):
                commands_pg.post()

            # check ability to create group and host
            with pytest.raises(towerkit.exceptions.Forbidden):
                groups_pg.post()
            with pytest.raises(towerkit.exceptions.Forbidden):
                hosts_pg.post()

            # check put/patch/delete on inventory, custom_group, and host_local
            assert_response_raised(host_local, httplib.FORBIDDEN)
            assert_response_raised(custom_group, httplib.FORBIDDEN)
            assert_response_raised(inventory_pg, httplib.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_admin_role(self, host_local, set_test_roles, agent, user_password, factories):
        """A user/team with inventory 'admin' should be able to:
        * Get the inventory detail
        * Get all of the inventory get_related
        * Edit/delete the inventory
        * Create/edit/delete inventory groups and hosts
        """
        inventory_pg = host_local.get_related('inventory')
        groups_pg = inventory_pg.get_related('groups')
        hosts_pg = inventory_pg.get_related('hosts')
        group_payload = factories.group.payload(inventory=inventory_pg)[0]
        host_payload = factories.host.payload(inventory=inventory_pg)[0]

        group_pg = factories.group(inventory=inventory_pg)
        user_pg = factories.user()

        # give agent admin_role
        set_test_roles(user_pg, inventory_pg, agent, "admin")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(inventory_pg, ["organization"])

            # check ability to create group and host
            groups_pg.post(group_payload)
            hosts_pg.post(host_payload)

            # check put/patch/delete on inventory, custom_group, and host_local
            assert_response_raised(host_local, httplib.OK)
            assert_response_raised(group_pg, httplib.OK)
            assert_response_raised(inventory_pg, httplib.OK)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_use_role(self, host_local, set_test_roles, agent, user_password, factories):
        """A user/team with inventory 'use' should be able to:
        * Get the inventory detail
        * Get all of the inventory get_related
        A user/team with inventory 'use' should not be able to:
        * Edit/delete the inventory
        * Create/edit/delete inventory groups and hosts
        """
        inventory_pg = host_local.get_related('inventory')
        groups_pg = inventory_pg.get_related('groups')
        hosts_pg = inventory_pg.get_related('hosts')
        group_payload = factories.group.payload(inventory=inventory_pg)[0]
        host_payload = factories.host.payload(inventory=inventory_pg)[0]

        group_pg = factories.group(inventory=inventory_pg)
        user_pg = factories.user()

        # give agent use_role
        set_test_roles(user_pg, inventory_pg, agent, "use")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(inventory_pg, ["organization"])

            # check ability to create group and host
            with pytest.raises(towerkit.exceptions.Forbidden):
                groups_pg.post(group_payload)
            with pytest.raises(towerkit.exceptions.Forbidden):
                hosts_pg.post(host_payload)

            # check put/patch/delete on inventory, custom_group, and host_local
            assert_response_raised(host_local, httplib.FORBIDDEN)
            assert_response_raised(group_pg, httplib.FORBIDDEN)
            assert_response_raised(inventory_pg, httplib.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_adhoc_role(self, host_local, set_test_roles, agent, user_password, factories):
        """A user/team with inventory 'adhoc' should be able to:
        * Get the inventory detail
        * Get all of the inventory get_related
        A user/team with inventory 'adhoc' should not be able to:
        * Edit/delete the inventory
        * Create/edit/delete inventory groups and hosts
        """
        inventory_pg = host_local.get_related('inventory')
        groups_pg = inventory_pg.get_related('groups')
        hosts_pg = inventory_pg.get_related('hosts')
        group_payload = factories.group.payload(inventory=inventory_pg)[0]
        host_payload = factories.host.payload(inventory=inventory_pg)[0]

        group_pg = factories.group(inventory=inventory_pg)
        user_pg = factories.user()

        # give agent adhoc_role
        set_test_roles(user_pg, inventory_pg, agent, "ad hoc")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(inventory_pg, ["organization"])

            # check ability to create group and host
            with pytest.raises(towerkit.exceptions.Forbidden):
                groups_pg.post(group_payload)
            with pytest.raises(towerkit.exceptions.Forbidden):
                hosts_pg.post(host_payload)

            # check put/patch/delete on inventory, custom_group, and host_local
            assert_response_raised(host_local, httplib.FORBIDDEN)
            assert_response_raised(group_pg, httplib.FORBIDDEN)
            assert_response_raised(inventory_pg, httplib.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_update_role(self, host_local, set_test_roles, agent, user_password, factories):
        """A user/team with inventory 'update' should be able to:
        * Get the inventory detail
        * Get all of the inventory get_related
        A user/team with inventory 'update' should not be able to:
        * Edit/delete the inventory
        * Create/edit/delete inventory groups and hosts
        """
        inventory_pg = host_local.get_related('inventory')
        groups_pg = inventory_pg.get_related('groups')
        hosts_pg = inventory_pg.get_related('hosts')
        group_payload = factories.group.payload(inventory=inventory_pg)[0]
        host_payload = factories.host.payload(inventory=inventory_pg)[0]

        group_pg = factories.group(inventory=inventory_pg)
        user_pg = factories.user()

        # give agent update_role
        set_test_roles(user_pg, inventory_pg, agent, "update")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(inventory_pg, ["organization"])

            # check ability to create group and host
            with pytest.raises(towerkit.exceptions.Forbidden):
                groups_pg.post(group_payload)
            with pytest.raises(towerkit.exceptions.Forbidden):
                hosts_pg.post(host_payload)

            # check put/patch/delete on inventory, custom_group, and host_local
            assert_response_raised(host_local, httplib.FORBIDDEN)
            assert_response_raised(group_pg, httplib.FORBIDDEN)
            assert_response_raised(inventory_pg, httplib.FORBIDDEN)

    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_read_role(self, host_local, set_test_roles, agent, user_password, factories):
        """A user/team with inventory 'read' should be able to:
        * Get the inventory detail
        * Get all of the inventory get_related
        A user/team with inventory 'read' should not be able to:
        * Edit/delete the inventory
        * Create/edit/delete inventory groups and hosts
        """
        inventory_pg = host_local.get_related('inventory')
        groups_pg = inventory_pg.get_related('groups')
        hosts_pg = inventory_pg.get_related('hosts')
        group_payload = factories.group.payload(inventory=inventory_pg)[0]
        host_payload = factories.host.payload(inventory=inventory_pg)[0]

        group_pg = factories.group(inventory=inventory_pg)
        user_pg = factories.user()

        # give agent read_role
        set_test_roles(user_pg, inventory_pg, agent, "read")

        with self.current_user(username=user_pg.username, password=user_password):
            # check GET as test user
            check_read_access(inventory_pg, ["organization"])

            # check ability to create group and host
            with pytest.raises(towerkit.exceptions.Forbidden):
                groups_pg.post(group_payload)
            with pytest.raises(towerkit.exceptions.Forbidden):
                hosts_pg.post(host_payload)

            # check put/patch/delete on inventory, custom_group, and host_local
            assert_response_raised(host_local, httplib.FORBIDDEN)
            assert_response_raised(group_pg, httplib.FORBIDDEN)
            assert_response_raised(inventory_pg, httplib.FORBIDDEN)

    @pytest.mark.parametrize('agent', ['user', 'team'])
    @pytest.mark.parametrize('role', ['admin', 'use', 'ad hoc', 'update', 'read'])
    def test_user_capabilities(self, factories, api_inventories_pg, set_test_roles, agent, role):
        """Test user_capabilities given each inventory role.
        Note: this test serves as a smokescreen test with user_capabilites and team credentials.
        This is the only place in tower-qa where we test user_capabilities with team credentials.
        """
        inventory_pg = factories.inventory()
        factories.group(inventory=inventory_pg)
        user_pg = factories.user()

        # give agent target role privileges
        set_test_roles(user_pg, inventory_pg, agent, role)

        with self.current_user(username=user_pg.username, password=user_pg.password):
            check_user_capabilities(inventory_pg.get(), role)
            check_user_capabilities(api_inventories_pg.get(id=inventory_pg.id).results.pop(), role)

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/4098')
    @pytest.mark.parametrize('role', ['admin', 'use', 'ad hoc', 'update', 'read'])
    def test_update_custom_group(self, factories, custom_inventory_source, user_password, role):
        """Test ability to update a custom group."""
        ALLOWED_ROLES = ['admin', 'update']
        REJECTED_ROLES = ['use', 'ad hoc', 'read']

        user_pg = factories.user()

        # give test user target role privileges
        inventory_pg = custom_inventory_source.get_related('inventory')
        set_roles(user_pg, inventory_pg, [role])

        with self.current_user(username=user_pg.username, password=user_password):
            if role in ALLOWED_ROLES:
                update_pg = custom_inventory_source.update().wait_until_completed()
                assert update_pg.is_successful, "Update unsuccessful - %s." % update_pg
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    custom_inventory_source.update()
            else:
                raise ValueError("Received unhandled inventory role.")

    @pytest.mark.parametrize('role', ['admin', 'use', 'ad hoc', 'update', 'read'])
    def test_update_cloud_group(self, factories, aws_inventory_source, user_password, role):
        """Test ability to update a cloud group. Note: only tested on AWS to save time.
        Also, user should be able launch update even though cloud_credential is under
        admin user.
        """
        ALLOWED_ROLES = ['admin', 'update']
        REJECTED_ROLES = ['use', 'ad hoc', 'read']

        user_pg = factories.user()

        # give agent target role privileges
        inventory_pg = aws_inventory_source.get_related('inventory')
        set_roles(user_pg, inventory_pg, [role])

        with self.current_user(username=user_pg.username, password=user_password):
            if role in ALLOWED_ROLES:
                update_pg = aws_inventory_source.update().wait_until_completed()
                assert update_pg.is_successful, "Update unsuccessful - %s." % update_pg
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

        user_pg = factories.user()

        # give test user target role privileges
        inventory_pg = custom_inventory_source.get_related('inventory')
        set_roles(user_pg, inventory_pg, [role])

        with self.current_user(username=user_pg.username, password=user_pg.password):
            if role in ALLOWED_ROLES:
                schedule_pg = custom_inventory_source.add_schedule()
                assert_response_raised(schedule_pg, methods=('get', 'put', 'patch', 'delete'))
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    custom_inventory_source.add_schedule()
            else:
                raise ValueError("Received unhandled inventory role.")

    @pytest.mark.parametrize('role', ['admin', 'use', 'ad hoc', 'update', 'read'])
    def test_cancel_update(self, factories, aws_inventory_source, user_password, role):
        """Tests inventory update cancellation. Inventory admins can cancel other people's updates."""
        ALLOWED_ROLES = ['admin']
        REJECTED_ROLES = ['update', 'use', 'ad hoc', 'read']

        user_pg = factories.user()

        # give test user target role privileges
        inventory_pg = aws_inventory_source.get_related('inventory')
        set_roles(user_pg, inventory_pg, [role])

        # launch inventory update
        update_pg = aws_inventory_source.update()

        with self.current_user(username=user_pg.username, password=user_password):
            if role in ALLOWED_ROLES:
                update_pg.cancel()
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    update_pg.cancel()
                # wait for inventory update to finish to ensure clean teardown
                update_pg.wait_until_completed()
            else:
                raise ValueError("Received unhandled inventory role.")

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/4182')
    @pytest.mark.parametrize('role', ['admin', 'use', 'ad hoc', 'update', 'read'])
    def test_delete_update(self, factories, custom_inventory_source, user_password, role):
        """Tests ability to delete an inventory update."""
        ALLOWED_ROLES = ['admin']
        REJECTED_ROLES = ['use', 'ad hoc', 'update', 'read']

        user_pg = factories.user()

        # give test user target role privileges
        inventory_pg = custom_inventory_source.get_related('inventory')
        set_roles(user_pg, inventory_pg, [role])

        # launch inventory update
        update_pg = custom_inventory_source.update()

        with self.current_user(username=user_pg.username, password=user_password):
            if role in ALLOWED_ROLES:
                update_pg.delete()
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    update_pg.delete()
                # wait for inventory update to finish to ensure clean teardown
                update_pg.wait_until_completed()
            else:
                raise ValueError("Received unhandled inventory role.")

    @pytest.mark.parametrize('role', ['admin', 'update', 'use', 'read'])
    def test_update_user_capabilities(self, factories, custom_inventory_source, user_password, api_inventory_updates_pg, role):
        """Test user_capabilities given each inventory role on spawned
        inventory_updates.
        """
        user_pg = factories.user()

        # give test user target role privileges
        inventory_pg = custom_inventory_source.get_related('inventory')
        set_roles(user_pg, inventory_pg, [role])

        # launch inventory_update
        update_pg = custom_inventory_source.update().wait_until_completed()

        with self.current_user(username=user_pg.username, password=user_password):
            check_user_capabilities(update_pg.get(), role)
            check_user_capabilities(api_inventory_updates_pg.get(id=update_pg.id).results.pop(), role)

    @pytest.mark.parametrize('role', ['admin', 'use', 'ad hoc', 'update', 'read'])
    def test_launch_command(self, factories, user_password, role):
        """Test ability to launch a command."""
        ALLOWED_ROLES = ['admin', 'ad hoc']
        REJECTED_ROLES = ['use', 'update', 'read']

        inventory_pg = factories.inventory()
        user_pg = factories.user()
        credential_pg = factories.credential(user=user_pg, organization=None)

        # create command fixtures
        ad_hoc_commands_pg = inventory_pg.get_related('ad_hoc_commands')
        payload = dict(inventory=inventory_pg.id,
                       credential=credential_pg.id,
                       module_name="ping")

        # give test user target role privileges
        set_roles(user_pg, inventory_pg, [role])

        with self.current_user(username=user_pg.username, password=user_password):
            if role in ALLOWED_ROLES:
                command_pg = ad_hoc_commands_pg.post(payload).wait_until_completed()
                assert command_pg.is_successful, "Command unsuccessful - %s." % command_pg
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    ad_hoc_commands_pg.post(payload)
            else:
                raise ValueError("Received unhandled inventory role.")

    @pytest.mark.parametrize('role', ['admin', 'use', 'ad hoc', 'update', 'read'])
    def test_relaunch_command(self, factories, user_password, role):
        """Tests ability to relaunch a command."""
        ALLOWED_ROLES = ['admin', 'ad hoc']
        REJECTED_ROLES = ['use', 'update', 'read']

        inventory_pg = factories.inventory()
        user_pg = factories.user()
        credential_pg = factories.credential(user=user_pg, organization=None)

        # launch command
        payload = dict(inventory=inventory_pg.id,
                       credential=credential_pg.id,
                       module_name="ping")
        command_pg = inventory_pg.get_related('ad_hoc_commands').post(payload).wait_until_completed()
        assert command_pg.is_successful, "Command unsuccessful - %s." % command_pg

        # give test user target role privileges
        set_roles(user_pg, inventory_pg, [role])

        with self.current_user(username=user_pg.username, password=user_password):
            if role in ALLOWED_ROLES:
                relaunched_command = command_pg.relaunch().wait_until_completed()
                assert relaunched_command.is_successful, "Command unsuccessful - %s." % command_pg
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    command_pg.relaunch()
            else:
                raise ValueError("Received unhandled inventory role.")

    @pytest.mark.parametrize('role', ['admin', 'use', 'ad hoc', 'update', 'read'])
    def test_cancel_command(self, factories, user_password, role):
        """Tests command cancellation. Inventory admins can cancel other people's commands."""
        ALLOWED_ROLES = ['admin']
        REJECTED_ROLES = ['ad hoc', 'use', 'update', 'read']

        inventory_pg = factories.inventory()
        user_pg = factories.user()
        credential_pg = factories.credential(user=user_pg, organization=None)

        # give test user target role privileges
        set_roles(user_pg, inventory_pg, [role])

        # launch command
        payload = dict(inventory=inventory_pg.id,
                       credential=credential_pg.id,
                       module_args="sleep 10")
        command_pg = inventory_pg.get_related('ad_hoc_commands').post(payload)

        with self.current_user(username=user_pg.username, password=user_password):
            if role in ALLOWED_ROLES:
                command_pg.cancel()
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    command_pg.cancel()
            else:
                raise ValueError("Received unhandled inventory role.")

    def test_delete_command_as_org_admin(self, factories, user_password):
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
        set_roles(org_admin1, inv_org1, ['admin'])
        set_roles(org_admin2, inv_org2, ['admin'])

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
        with self.current_user(username=org_admin1.username, password=user_password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                command2.delete()
        with self.current_user(username=org_admin2.username, password=user_password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                command1.delete()

        # assert that each org_admin can delete his own organization's command
        with self.current_user(username=org_admin1.username, password=user_password):
            command1.delete()
        with self.current_user(username=org_admin2.username, password=user_password):
            command2.delete()

    def test_delete_command_as_org_user(self, factories, user_password):
        """Tests ability to delete an ad hoc command as a privileged org_user."""
        inventory_pg = factories.inventory()
        user_pg = factories.user()
        credential_pg = factories.credential(user=user_pg, organization=None)

        # give test user target role privileges
        set_roles(user_pg, inventory_pg, ['admin'])

        # launch command
        payload = dict(inventory=inventory_pg.id,
                       credential=credential_pg.id,
                       module_name="ping")
        command_pg = inventory_pg.get_related('ad_hoc_commands').post(payload)

        with self.current_user(username=user_pg.username, password=user_password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                command_pg.delete()
            # wait for ad hoc command to finish to ensure clean teardown
            command_pg.wait_until_completed()

    @pytest.mark.parametrize('role', ['admin', 'use', 'ad hoc', 'update', 'read'])
    def test_command_user_capabilities(self, factories, user_password, api_ad_hoc_commands_pg, role):
        """Test user_capabilities given each inventory role on spawned
        ad hoc commands.
        """
        inventory_pg = factories.inventory()
        user_pg = factories.user()
        credential_pg = factories.credential(user=user_pg, organization=None)

        # give test user target role privileges
        set_roles(user_pg, inventory_pg, [role])

        # launch command
        payload = dict(inventory=inventory_pg.id,
                       credential=credential_pg.id,
                       module_name="ping")
        command_pg = inventory_pg.get_related('ad_hoc_commands').post(payload).wait_until_completed()

        with self.current_user(username=user_pg.username, password=user_password):
            check_user_capabilities(command_pg.get(), role)
            check_user_capabilities(api_ad_hoc_commands_pg.get(id=command_pg.id).results.pop(), role)

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
