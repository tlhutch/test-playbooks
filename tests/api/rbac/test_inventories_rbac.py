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
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestInventoryRBAC(Base_Api_Test):

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/7321')
    def test_unprivileged_user(self, factories):
        """An unprivileged user should not be able to:
        * Get the inventory detail page
        * Get all of the inventory related pages
        * Update all groups that the inventory contains
        * Launch ad hoc commands against the inventory
        * Edit/delete the inventory
        * Create/edit/delete inventory groups, hosts, and sources
        """
        inventory = factories.v2_inventory()
        group = factories.v2_group(inventory=inventory)
        host = factories.v2_host(inventory=inventory)
        custom_inv_source = factories.v2_inventory_source(inventory=inventory)
        aws_inv_source = factories.v2_inventory_source(inventory=inventory, kind='ec2')
        user = factories.user()

        with self.current_user(username=user.username, password=user.password):
            # check GET as test user
            check_read_access(inventory, unprivileged=True)

            # update inventory sources
            with pytest.raises(towerkit.exceptions.Forbidden):
                aws_inv_source.related['update'].post()
            with pytest.raises(towerkit.exceptions.Forbidden):
                custom_inv_source.related['update'].post()

            # post command
            with pytest.raises(towerkit.exceptions.Forbidden):
                inventory.related.ad_hoc_commands.post()

            # check ability to create inventory resources
            with pytest.raises(towerkit.exceptions.Forbidden):
                inventory.related.groups.post()
            with pytest.raises(towerkit.exceptions.Forbidden):
                inventory.related.hosts.post()
            with pytest.raises(towerkit.exceptions.Forbidden):
                inventory.related.inventory_sources.post()

            # check put/patch/delete on inventory and inventory resources
            for resource in [host, group, aws_inv_source, inventory]:
                assert_response_raised(resource, httplib.FORBIDDEN)

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/7330')
    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_admin_role(self, set_test_roles, agent, factories):
        """A user/team with inventory 'admin' should be able to:
        * Get the inventory detail page
        * Get all of the inventory related pages
        * Edit/delete the inventory
        * Create/edit/delete inventory groups, hosts, and sources
        """
        inventory = factories.v2_inventory()
        inv_script = factories.v2_inventory_script(organization=inventory.ds.organization)
        user = factories.user()

        # give agent admin_role
        set_test_roles(user, inventory, agent, "admin")

        with self.current_user(username=user.username, password=user.password):
            # check GET as test user
            check_read_access(inventory, ["organization"])

            # check ability to create group and host
            group = factories.v2_group(inventory=inventory)
            host = factories.v2_host(inventory=inventory)
            inv_source = factories.v2_inventory_source(inventory=inventory, inventory_script=inv_script)

            # check put/patch/delete on inventory and inventory resources
            for resource in [host, group, inv_source, inventory]:
                assert_response_raised(resource, httplib.OK)

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/7329')
    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_use_role(self, set_test_roles, agent, factories):
        """A user/team with inventory 'use' should be able to:
        * Get the inventory detail page
        * Get all of the inventory related pages
        A user/team with inventory 'use' should not be able to:
        * Edit/delete the inventory
        * Create/edit/delete inventory groups, hosts, and sources
        """
        inventory = factories.v2_inventory()
        group = factories.v2_group(inventory=inventory)
        host = factories.v2_host(inventory=inventory)
        inv_source = factories.v2_inventory_source(inventory=inventory)
        inv_script = factories.v2_inventory_script(organization=inventory.ds.organization)
        user = factories.user()

        # give agent use_role
        set_test_roles(user, inventory, agent, "use")

        with self.current_user(username=user.username, password=user.password):
            # check GET as test user
            check_read_access(inventory, ["organization"])

            # check ability to create group and host
            with pytest.raises(towerkit.exceptions.Forbidden):
                factories.v2_group(inventory=inventory)
            with pytest.raises(towerkit.exceptions.Forbidden):
                factories.v2_host(inventory=inventory)
            with pytest.raises(towerkit.exceptions.Forbidden):
                factories.v2_inventory_source(inventory=inventory, inventory_script=inv_script)

            # check put/patch/delete on inventory and inventory resoures
            for resource in [host, group, inv_source, inventory]:
                assert_response_raised(resource, httplib.FORBIDDEN)

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/7329')
    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_adhoc_role(self, set_test_roles, agent, factories):
        """A user/team with inventory 'adhoc' should be able to:
        * Get the inventory detail
        * Get all of the inventory get_related
        A user/team with inventory 'adhoc' should not be able to:
        * Edit/delete the inventory
        * Create/edit/delete inventory groups, hosts, and sources
        """
        inventory = factories.v2_inventory()
        group = factories.v2_group(inventory=inventory)
        host = factories.v2_host(inventory=inventory)
        inv_source = factories.v2_inventory_source(inventory=inventory)
        inv_script = factories.v2_inventory_script(organization=inventory.ds.organization)
        user = factories.user()

        # give agent adhoc_role
        set_test_roles(user, inventory, agent, "ad hoc")

        with self.current_user(username=user.username, password=user.password):
            # check GET as test user
            check_read_access(inventory, ["organization"])

            # check ability to create group and host
            with pytest.raises(towerkit.exceptions.Forbidden):
                factories.v2_group(inventory=inventory)
            with pytest.raises(towerkit.exceptions.Forbidden):
                factories.v2_host(inventory=inventory)
            with pytest.raises(towerkit.exceptions.Forbidden):
                factories.v2_inventory_source(inventory=inventory, inventory_script=inv_script)

            # check put/patch/delete on inventory and inventory resources
            for resource in [host, group, inv_source, inventory]:
                assert_response_raised(resource, httplib.FORBIDDEN)

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/7329')
    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_update_role(self, set_test_roles, agent, factories):
        """A user/team with inventory 'update' should be able to:
        * Get the inventory detail
        * Get all of the inventory related pages
        A user/team with inventory 'update' should not be able to:
        * Edit/delete the inventory
        * Create/edit/delete inventory groups, hosts, and sources
        """
        inventory = factories.v2_inventory()
        group = factories.v2_group(inventory=inventory)
        host = factories.v2_host(inventory=inventory)
        inv_source = factories.v2_inventory_source(inventory=inventory)
        inv_script = factories.v2_inventory_script(organization=inventory.ds.organization)
        user = factories.user()

        # give agent update_role
        set_test_roles(user, inventory, agent, "update")

        with self.current_user(username=user.username, password=user.password):
            # check GET as test user
            check_read_access(inventory, ["organization"])

            # check ability to create group and host
            with pytest.raises(towerkit.exceptions.Forbidden):
                factories.v2_group(inventory=inventory)
            with pytest.raises(towerkit.exceptions.Forbidden):
                factories.v2_host(inventory=inventory)
            with pytest.raises(towerkit.exceptions.Forbidden):
                factories.v2_inventory_source(inventory=inventory, inventory_script=inv_script)

            # check put/patch/delete on inventory, group, and host
            for resource in [host, group, inv_source, inventory]:
                assert_response_raised(resource, httplib.FORBIDDEN)

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/7329')
    @pytest.mark.parametrize("agent", ["user", "team"])
    def test_read_role(self, set_test_roles, agent, factories):
        """A user/team with inventory 'read' should be able to:
        * Get the inventory detail page
        * Get all of the inventory related pages
        A user/team with inventory 'read' should not be able to:
        * Edit/delete the inventory
        * Create/edit/delete inventory groups, hosts, and sources
        """
        inventory = factories.v2_inventory()
        group = factories.v2_group(inventory=inventory)
        host = factories.v2_host(inventory=inventory)
        inv_source = factories.v2_inventory_source(inventory=inventory)
        inv_script = factories.v2_inventory_script(organization=inventory.ds.organization)
        user = factories.user()

        # give agent read_role
        set_test_roles(user, inventory, agent, "read")

        with self.current_user(username=user.username, password=user.password):
            # check GET as test user
            check_read_access(inventory, ["organization"])

            # check ability to create group and host
            with pytest.raises(towerkit.exceptions.Forbidden):
                factories.v2_group(inventory=inventory)
            with pytest.raises(towerkit.exceptions.Forbidden):
                factories.v2_host(inventory=inventory)
            with pytest.raises(towerkit.exceptions.Forbidden):
                factories.v2_inventory_source(inventory=inventory, inventory_script=inv_script)

            # check put/patch/delete on inventory, group, and host
            for resource in [host, group, inv_source, inventory]:
                assert_response_raised(resource, httplib.FORBIDDEN)

    @pytest.mark.parametrize('agent', ['user', 'team'])
    @pytest.mark.parametrize('role', ['admin', 'use', 'ad hoc', 'update', 'read'])
    def test_user_capabilities(self, factories, v2, set_test_roles, agent, role):
        """Test user_capabilities given each inventory role.
        Note: this test serves as a smoke test with user_capabilites and team credentials.
        This is the only place in tower-qa where we test user_capabilities with team credentials.
        """
        inventory = factories.v2_inventory()
        factories.v2_group(inventory=inventory)
        factories.v2_host(inventory=inventory)
        factories.v2_inventory_source(inventory=inventory)
        user = factories.user()

        # give agent target role privileges
        set_test_roles(user, inventory, agent, role)

        with self.current_user(username=user.username, password=user.password):
            check_user_capabilities(inventory.get(), role)
            check_user_capabilities(v2.inventory.get(id=inventory.id).results.pop(), role)

    @pytest.mark.parametrize('role', ['admin', 'use', 'ad hoc', 'update', 'read'])
    def test_update_custom_source(self, factories, role):
        """Test ability to update a custom source."""
        ALLOWED_ROLES = ['admin', 'update']
        REJECTED_ROLES = ['use', 'ad hoc', 'read']

        user = factories.user()

        inv_source = factories.v2_inventory_source()
        inv_source.ds.inventory.set_object_roles(user, role)

        with self.current_user(username=user.username, password=user.password):
            if role in ALLOWED_ROLES:
                update = inv_source.update().wait_until_completed()
                assert update.is_successful, "Update unsuccessful - %s." % update
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    inv_source.update()
            else:
                raise ValueError("Received unhandled inventory role.")

    @pytest.mark.parametrize('role', ['admin', 'use', 'ad hoc', 'update', 'read'])
    def test_update_cloud_source(self, factories, role):
        """Test ability to update a cloud source. Note: only tested on AWS to save time.
        Also, user should be able launch update even though cloud_credential is under
        admin user.
        """
        ALLOWED_ROLES = ['admin', 'update']
        REJECTED_ROLES = ['use', 'ad hoc', 'read']

        user = factories.user()

        aws_cred = factories.v2_credential(kind='aws')
        inv_source = factories.v2_inventory_source(kind='ec2', credential=aws_cred)
        inv_source.ds.inventory.set_object_roles(user, role)

        with self.current_user(username=user.username, password=user.password):
            if role in ALLOWED_ROLES:
                update = inv_source.update().wait_until_completed()
                assert update.is_successful, "Update unsuccessful - %s." % update
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    inv_source.update()
            else:
                raise ValueError("Received unhandled inventory role.")

    @pytest.mark.parametrize('role', ['admin', 'use', 'ad hoc', 'update', 'read'])
    def test_update_all_inventory_sources(self, factories, role):
        """Test ability to update all inventory sources. User should be able to
        launch update even though cloud_credential is owned by admin user.
        """
        ALLOWED_ROLES = ['admin', 'update']
        REJECTED_ROLES = ['use', 'ad hoc', 'read']

        inventory = factories.v2_inventory()
        gce_cred, aws_cred = [factories.v2_credential(kind=kind) for kind in ('gce', 'aws')]
        gce_source = factories.v2_inventory_source(inventory=inventory, source='gce', credential=gce_cred)
        ec2_source = factories.v2_inventory_source(inventory=inventory, source='ec2', credential=aws_cred)

        user = factories.user()
        inventory.set_object_roles(user, role)

        with self.current_user(user):
            if role in ALLOWED_ROLES:
                inv_updates = inventory.update_inventory_sources(wait=True)
                for update in inv_updates:
                    assert update.is_successful
                assert gce_source.get().is_successful and ec2_source.get().is_successful
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    inventory.update_inventory_sources()
            else:
                raise ValueError("Received unhandled inventory role.")

    @pytest.mark.parametrize('role', ['admin', 'use', 'ad hoc', 'update', 'read'])
    def test_schedule_update(self, factories, role):
        """Tests ability to schedule an inventory update."""
        ALLOWED_ROLES = ['admin', 'update']
        REJECTED_ROLES = ['use', 'ad hoc', 'read']

        user = factories.user()

        inv_source = factories.v2_inventory_source()
        inv_source.ds.inventory.set_object_roles(user, role)

        with self.current_user(username=user.username, password=user.password):
            if role in ALLOWED_ROLES:
                schedule = inv_source.add_schedule()
                assert_response_raised(schedule, methods=('get', 'put', 'patch', 'delete'))
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    inv_source.add_schedule()
            else:
                raise ValueError("Received unhandled inventory role.")

    @pytest.mark.parametrize('role', ['admin', 'use', 'ad hoc', 'update', 'read'])
    def test_cancel_update(self, factories, role):
        """Tests inventory update cancellation. Inventory admins can cancel other people's updates."""
        ALLOWED_ROLES = ['admin']
        REJECTED_ROLES = ['update', 'use', 'ad hoc', 'read']

        user = factories.user()

        aws_cred = factories.v2_credential(kind='aws')
        inv_source = factories.v2_inventory_source(kind='ec2', credential=aws_cred)
        inv_source.ds.inventory.set_object_roles(user, role)

        update = inv_source.update()

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
    def test_delete_update(self, factories, role):
        """Tests ability to delete an inventory update."""
        ALLOWED_ROLES = ['admin']
        REJECTED_ROLES = ['use', 'ad hoc', 'update', 'read']

        user = factories.user()

        inv_source = factories.v2_inventory_source()
        inv_source.ds.inventory.set_object_roles(user, role)

        update = inv_source.update().wait_until_completed()

        with self.current_user(username=user.username, password=user.password):
            if role in ALLOWED_ROLES:
                update.delete()
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    update.delete()
            else:
                raise ValueError("Received unhandled inventory role.")

    @pytest.mark.parametrize('role', ['admin', 'update', 'use', 'read'])
    def test_update_user_capabilities(self, factories, v2, role):
        """Test user_capabilities given each inventory role on spawned
        inventory_updates.
        """
        user = factories.user()

        inv_source = factories.v2_inventory_source()
        inv_source.ds.inventory.set_object_roles(user, role)

        # launch inventory_update
        update = inv_source.update().wait_until_completed()

        with self.current_user(username=user.username, password=user.password):
            check_user_capabilities(update.get(), role)
            check_user_capabilities(v2.inventory_updates.get(id=update.id).results.pop(), role)

    @pytest.mark.parametrize('role', ['admin', 'use', 'ad hoc', 'update', 'read'])
    def test_launch_command(self, factories, role):
        """Test ability to launch a command."""
        ALLOWED_ROLES = ['admin', 'ad hoc']
        REJECTED_ROLES = ['use', 'update', 'read']

        inventory = factories.v2_inventory()
        user = factories.user()
        credential = factories.v2_credential(user=user, organization=None)

        inventory.set_object_roles(user, role)

        with self.current_user(username=user.username, password=user.password):
            if role in ALLOWED_ROLES:
                ahc = factories.v2_ad_hoc_command(inventory=inventory,
                                                  credential=credential,
                                                  module_name="ping").wait_until_completed()
                assert ahc.is_successful, "Command unsuccessful - %s." % ahc
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    factories.v2_ad_hoc_command(inventory=inventory,
                                                credential=credential,
                                                module_name="ping")
            else:
                raise ValueError("Received unhandled inventory role.")

    @pytest.mark.parametrize('role', ['admin', 'use', 'ad hoc', 'update', 'read'])
    def test_relaunch_command(self, factories, role):
        """Tests ability to relaunch a command."""
        ALLOWED_ROLES = ['admin', 'ad hoc']
        REJECTED_ROLES = ['use', 'update', 'read']

        inventory = factories.v2_inventory()
        user = factories.user()
        credential = factories.v2_credential(user=user, organization=None)

        ahc = factories.v2_ad_hoc_command(inventory=inventory,
                                         credential=credential,
                                         module_name="ping").wait_until_completed()
        assert ahc.is_successful, "Command unsuccessful - %s." % ahc

        inventory.set_object_roles(user, role)

        with self.current_user(username=user.username, password=user.password):
            if role in ALLOWED_ROLES:
                relaunched_ahc = ahc.relaunch().wait_until_completed()
                assert relaunched_ahc.is_successful, "Command unsuccessful - %s." % relaunched_ahc
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    ahc.relaunch()
            else:
                raise ValueError("Received unhandled inventory role.")

    @pytest.mark.parametrize('role', ['admin', 'use', 'ad hoc', 'update', 'read'])
    def test_cancel_command(self, factories, role):
        """Tests command cancellation. Inventory admins can cancel other people's commands."""
        ALLOWED_ROLES = ['admin']
        REJECTED_ROLES = ['ad hoc', 'use', 'update', 'read']

        user = factories.user()

        ahc = factories.v2_ad_hoc_command(module_args="sleep 10")
        ahc.ds.inventory.set_object_roles(user, role)

        with self.current_user(username=user.username, password=user.password):
            if role in ALLOWED_ROLES:
                ahc.cancel()
            elif role in REJECTED_ROLES:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    ahc.cancel()
            else:
                raise ValueError("Received unhandled inventory role.")

    def test_delete_command_as_org_admin(self, factories):
        """Create two ad hoc commands and an org_admin for each of these commands.
        Then check that each org_admin may only delete his org's command.
        Note: command deletion is organization scoped. A command's inventory determines
        its organization.
        """
        # launch both commands
        ahc1, ahc2 = [factories.v2_ad_hoc_command(module_name="ping").wait_until_completed() for _ in range(2)]

        # create org admins
        org_admin1, org_admin2 = [factories.user() for _ in range(2)]
        ahc1.ds.inventory.ds.organization.add_admin(org_admin1)
        ahc2.ds.inventory.ds.organization.add_admin(org_admin2)

        # assert that each org_admin cannot delete other organization's command
        with self.current_user(username=org_admin1.username, password=org_admin1.password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                ahc2.delete()
        with self.current_user(username=org_admin2.username, password=org_admin2.password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                ahc1.delete()

        # assert that each org_admin can delete his own organization's command
        with self.current_user(username=org_admin1.username, password=org_admin1.password):
            ahc1.delete()
        with self.current_user(username=org_admin2.username, password=org_admin2.password):
            ahc2.delete()

    def test_delete_command_as_org_user(self, factories):
        """Tests ability to delete an ad hoc command as a privileged org_user."""
        user = factories.user()

        ahc = factories.v2_ad_hoc_command(module_name="ping").wait_until_completed()
        ahc.ds.inventory.set_object_roles(user, "admin")

        with self.current_user(username=user.username, password=user.password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                ahc.delete()

    @pytest.mark.parametrize('role', ['admin', 'use', 'ad hoc', 'update', 'read'])
    def test_command_user_capabilities(self, factories, v2, role):
        """Test user_capabilities given each inventory role on spawned
        ad hoc commands.
        """
        ahc = factories.v2_ad_hoc_command(module_name="ping").wait_until_completed()

        user = factories.user(organization=ahc.ds.credential.ds.organization)
        ahc.ds.inventory.set_object_roles(user, role)
        ahc.ds.credential.set_object_roles(user, "use")

        with self.current_user(username=user.username, password=user.password):
            check_user_capabilities(ahc.get(), role)
            check_user_capabilities(v2.ad_hoc_commands.get(id=ahc.id).results.pop(), role)

    def test_cloud_source_credential_reassignment(self, factories, openstack_v2_credential):
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
